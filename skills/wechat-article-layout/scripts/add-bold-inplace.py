#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号排版 · 就地补语义加粗 / 就地改文字（不重排版）

目的
----
只给已有 docx 补 run 级语义加粗、或改掉个别文字（如删图注序号），
**其余 XML 一字不动**——尤其是 word/styles.xml 与图片关系表必须原样保留。
重建整份文档会换掉 styles.xml 的 styleId 映射，标题识别会整体失效（见 SKILL.md 坑位 A），
所以「只补加粗 / 只改文字」这类最小变更一律走本脚本，不要用 python-docx 重建。

用法
----
    python3 add-bold-inplace.py <输入.docx> [--spec spec.json] [-o 输出.docx]
    python3 add-bold-inplace.py <输入.docx> --dump          # 只看现状：段落/加粗/图片落点

spec.json 结构（bold 与 replace 可只给其中一个）：
    {
      "bold": [
        {"para_starts_with": "段落开头的特征文字",
         "phrases": ["要被加粗的短语一", "要被加粗的短语二"]}
      ],
      "replace": [
        {"para_contains": "定位用片段",
         "old": "【配图 7｜DeepSeek 的翻译结果截图】",
         "new": "【DeepSeek 的翻译结果截图】"}
      ]
    }

为什么不能直接对 word/document.xml 做字符串替换
--------------------------------------------
Word 会把一段文字切成很多 run（中文按 rFonts hint 切、英文/数字单独切）。
例：「【配图 7｜DeepSeek 的翻译结果截图】」在 XML 里是
     <w:r>【配图</w:r><w:r> </w:r><w:r>7｜DeepSeek</w:r><w:r>的翻译结果截图】</w:r>
所以 `str.replace('【配图 7｜…】', '…')` 命中 0 次、静默什么都没改。
本脚本按「段落级重建」处理：把整段文字拼起来定位，再按原 run 的 rPr 逐段还原，
既能跨 run 命中，又能保留各 run 自己的字体属性。

自检（不过就不落盘）
--------------------
1. 每条 bold 短语、每条 replace 的 old，在本段内命中数必须**恰好为 1**；
2. 所有 bold/replace 目标段落必须**全部命中**（有落空即中止，防「改了但没生效」静默通过）；
3. 改后全文纯文本 == 原文纯文本 − replace 差异（逐字符比对），否则中止。

注意：本脚本不判断「哪句该加粗」——那是脑力活（读全文找结论/金句/关键数据），
由 AI 在 spec.json 里给出。脚本只负责把它准确、可验证地落进 XML。
"""

import argparse
import json
import os
import re
import shutil
import sys
import zipfile

# 段落 / run 的正则：都是非嵌套结构，非贪婪即可
P_RE = re.compile(r'<w:p(?: [^>]*)?>[\s\S]*?</w:p>')
R_RE = re.compile(r'<w:r(?: [^>]*)?>[\s\S]*?</w:r>')
T_RE = re.compile(r'<w:t[^>]*>([\s\S]*?)</w:t>')
RPR_RE = re.compile(r'<w:rPr>([\s\S]*?)</w:rPr>')


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def unesc(t):
    return (t.replace('&lt;', '<').replace('&gt;', '>')
             .replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&'))


def para_text(pxml):
    return unesc(''.join(T_RE.findall(pxml)))


def parse_runs(pxml):
    """-> [(run_xml, rPr_inner_or_None, text)]，只含带文本的 run 也一并返回顺序"""
    out = []
    for m in R_RE.finditer(pxml):
        rx = m.group(0)
        rpr = RPR_RE.search(rx)
        txt = unesc(''.join(T_RE.findall(rx)))
        out.append((rx, rpr.group(1) if rpr else None, txt))
    return out


def rpr_with_bold(rpr_inner):
    """把 <w:b/> 插到 schema 正确位置：rStyle -> rFonts -> b"""
    inner = rpr_inner or ''
    inner = re.sub(r'<w:b\s+w:val="(?:0|false)"\s*/>', '', inner)
    if re.search(r'<w:b\s*/>', inner):
        return inner
    for anchor in (r'</w:rStyle>', r'</w:rFonts>'):
        m = re.search(anchor, inner)
        if m:
            return inner[:m.end()] + '<w:b/>' + inner[m.end():]
    return '<w:b/>' + inner


def make_run(text, rpr_inner, bold):
    rpr = ''
    if rpr_inner is not None or bold:
        rpr = '<w:rPr>' + (rpr_with_bold(rpr_inner) if bold else rpr_inner) + '</w:rPr>'
    return '<w:r>' + rpr + '<w:t xml:space="preserve">' + esc(text) + '</w:t></w:r>'


def para_shell(pxml):
    """拆出 <w:p ...> 开始标签 / pPr / 内容 —— 只重建内容，pPr 原样搬回"""
    mp = re.match(r'<w:p(?: [^>]*)?>', pxml)
    inner = pxml[mp.end():-len('</w:p>')]
    ppr = re.search(r'<w:pPr>[\s\S]*?</w:pPr>', inner)
    return mp.group(0), (ppr.group(0) if ppr else ''), inner


def rebuild_with_bold(pxml, phrases):
    """按短语加粗重建整段：逐 run 按其原 rPr 切分，跨 run 短语可正确命中"""
    if '<w:drawing' in pxml or '<w:hyperlink' in pxml:
        raise ValueError('段落含图片/超链接，重建不安全，请改用段落内精确定位')
    start, head, _ = para_shell(pxml)
    runs = parse_runs(pxml)
    full = ''.join(r[2] for r in runs)

    spans = []
    for ph in phrases:
        n = full.count(ph)
        if n != 1:
            raise ValueError(f'加粗短语在本段命中 {n} 次（应为 1）: {ph!r}')
        i = full.index(ph)
        spans.append((i, i + len(ph)))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    def is_bold(pos):
        return any(s <= pos < e for s, e in merged)

    out, off = [], 0
    for rx, rpr, txt in runs:
        if not txt:
            out.append(rx)          # tab / br 等非文本 run 原样保留
            continue
        seg, cur_start, cur_bold = [], 0, is_bold(off)
        for j in range(1, len(txt)):
            b = is_bold(off + j)
            if b != cur_bold:
                seg.append((txt[cur_start:j], cur_bold))
                cur_start, cur_bold = j, b
        seg.append((txt[cur_start:], cur_bold))
        for s, b in seg:
            out.append(make_run(s, rpr, b))
        off += len(txt)

    return start + head + ''.join(out) + '</w:p>'


def rebuild_with_text(pxml, old, new):
    """整段替换文本，沿用首个 run 的 rPr（适用于格式统一的图注/说明段）"""
    start, head, _ = para_shell(pxml)
    runs = parse_runs(pxml)
    return start + head + make_run(new, (runs[0][1] if runs else None), False) + '</w:p>'


def dump(docxml):
    print('段落 / 加粗 / 图片落点：')
    for i, m in enumerate(P_RE.finditer(docxml)):
        px = m.group(0)
        segs = []
        for rx, rpr, txt in parse_runs(px):
            if not txt:
                continue
            segs.append('**' + txt + '**' if (rpr and re.search(r'<w:b\s*/>', rpr)) else txt)
        line = ''.join(segs)
        if line.strip():
            print(f'[{i}] {line}')
        if '<w:drawing' in px:
            print(f'[{i}] <IMG>')


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('src')
    ap.add_argument('--spec')
    ap.add_argument('-o', '--out')
    ap.add_argument('--dump', action='store_true')
    a = ap.parse_args()

    out = a.out or os.path.join(
        os.path.dirname(os.path.abspath(a.src)),
        os.path.splitext(os.path.basename(a.src))[0] + '_bold.docx')

    tmp = '/tmp/wx-inplace'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    with zipfile.ZipFile(a.src) as z:
        names = z.namelist()
        z.extractall(tmp)

    docxml_path = os.path.join(tmp, 'word/document.xml')
    xml = open(docxml_path, encoding='utf-8').read()

    if a.dump:
        dump(xml)
        shutil.rmtree(tmp, ignore_errors=True)
        return

    if not a.spec:
        print('✗ 未给 --spec（或改用 --dump 只看现状）'); sys.exit(1)
    spec = json.load(open(a.spec, encoding='utf-8'))
    orig_text = ''.join(unesc(t) for t in T_RE.findall(xml))

    print(f'段落数：{len(P_RE.findall(xml))}')

    paras = list(P_RE.finditer(xml))
    done_bold, done_repl = 0, 0
    used_b, used_r = set(), set()

    for idx in range(len(paras) - 1, -1, -1):   # 从后往前替换，避免位移
        p = paras[idx]
        ptxt = para_text(p.group(0))

        for k, r in enumerate(spec.get('replace', [])):
            if k in used_r or r['para_contains'] not in ptxt:
                continue
            if ptxt.count(r['old']) != 1:
                print(f'✗ 替换目标在本段命中 {ptxt.count(r["old"])} 次（应为 1）: {r["old"]!r}')
                sys.exit(1)
            xml = xml[:p.start()] + rebuild_with_text(p.group(0), r['old'], r['new']) + xml[p.end():]
            used_r.add(k); done_repl += 1
            print(f'  ~ 替换 | {r["old"][:26]} → {r["new"][:26]}')
            break

        for k, b in enumerate(spec.get('bold', [])):
            if k in used_b or not ptxt.startswith(b['para_starts_with']):
                continue
            try:
                newpx = rebuild_with_bold(p.group(0), b['phrases'])
            except ValueError as e:
                print(f'✗ {e}'); sys.exit(1)
            xml = xml[:p.start()] + newpx + xml[p.end():]
            used_b.add(k); done_bold += 1
            print(f'  + 加粗 {len(b["phrases"])} 处 | {b["para_starts_with"][:26]}')
            break

    # ── 自检：目标必须全部命中 ──
    for key, used, label in (('bold', used_b, '加粗'), ('replace', used_r, '替换')):
        miss = [spec[key][i]['para_starts_with' if key == 'bold' else 'para_contains']
                for i in range(len(spec.get(key, []))) if i not in used]
        if miss:
            print(f'✗ {label}目标段落未命中（定位串可能写错或文字有出入）：'); [print('   -', m) for m in miss]
            sys.exit(1)

    # ── 自检：正文一字未改（只允许 replace 的差异）──
    new_text = ''.join(unesc(t) for t in T_RE.findall(xml))
    expect = orig_text
    for r in spec.get('replace', []):
        expect = expect.replace(r['old'], r['new'])
    if new_text != expect:
        print('✗ 纯文本不一致，未落盘')
        for i in range(min(len(new_text), len(expect))):
            if new_text[i] != expect[i]:
                print(f'  char {i}: ...{expect[max(0,i-20):i+20]}... -> ...{new_text[max(0,i-20):i+20]}...')
                break
        sys.exit(1)

    open(docxml_path, 'w', encoding='utf-8').write(xml)
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(tmp, n), n)
    shutil.rmtree(tmp, ignore_errors=True)

    print(f'✓ 加粗 {done_bold} 段 / 替换 {done_repl} 处；原文一字未改（仅替换差异）')
    print('✓ 已保存：' + out)
    print('   下一步务必复核：cd ~/.workbuddy/skills/wechat-publisher/scripts && '
          f'node publish.js --check "{out}"')
    dump(zipfile.ZipFile(out).read('word/document.xml').decode('utf-8'))


if __name__ == '__main__':
    main()
