# -*- coding: utf-8 -*-
"""交付前参数审计：把"逐段核对 + 数量校验 + 一致性检查"变成可执行的东西。

为什么要有它：2026-09-12 的复盘结论是**验收指标不完备**——我列的 6 个指标里
0 个管字体/字号/元素归属/文档网格，于是 21 项错有 17 项落在"未被指标覆盖"的区域。
本脚本把"原件的属性清单"逐项打印出来，让每一个属性都有归属，不给盲区留位置。

用法：
    python3 audit_docx.py out.docx                    # 打印全表 + 计数 + 一致性检查
    python3 audit_docx.py out.docx --spec spec.json   # 再与 spec 逐项比对（理想：零差异）

退出码：0 = 没有问题；1 = 有 FAIL 项（**不许交付**）。
"""
import argparse
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
# Word 常见整档字号（用于"是否已取整档"检查）
STD_SIZES = {5, 5.5, 6.5, 7.5, 8, 9, 10, 10.5, 11, 12, 14, 15, 16, 18, 20, 21, 22, 24, 26, 28,
             32, 36, 42, 44, 48, 54, 60, 72}

FAIL, WARN = [], []


def q(t):
    return W + t


def at(e):
    return {k.replace(W, ''): v for k, v in e.attrib.items()} if e is not None else None


def load(path):
    if not os.path.exists(path):
        sys.exit(f'找不到文件：{path}（检查路径；别忘了先 cd 到产物目录）')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
        parts = {}
        for n in names:
            if re.match(r'word/(footer|header)\d*\.xml$', n):
                parts[n] = ET.fromstring(z.read(n).decode('utf-8'))
        styles = ET.fromstring(z.read('word/styles.xml').decode('utf-8'))
    return root, parts, styles


def run_fmt(r):
    rpr = r.find(q('rPr'))
    if rpr is None:
        return {}
    rf, sz, sc = rpr.find(q('rFonts')), rpr.find(q('sz')), rpr.find(q('w'))
    d = {}
    if rf is not None:
        d['ea'] = rf.get(q('eastAsia')) or '-'
        d['ascii'] = rf.get(q('ascii')) or '-'
    if sz is not None:
        d['size'] = int(sz.get(q('val'))) / 2
    if sc is not None:
        d['scale'] = int(sc.get(q('val')))
    return d


def par_fmt(p):
    pPr = p.find(q('pPr'))
    d = {}
    if pPr is None:
        return d
    for t in ('jc', 'spacing', 'ind', 'docGrid'):
        e = pPr.find(q(t))
        if e is not None:
            d[t] = at(e)
    for t in ('kinsoku', 'wordWrap', 'autoSpaceDE', 'autoSpaceDN'):
        if pPr.find(q(t)) is not None:
            d[t] = pPr.find(q(t)).get(q('val'))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('--spec')
    a = ap.parse_args()
    root, parts, styles = load(a.docx)
    body = root.find(q('body'))
    sect = body.find(q('sectPr'))
    pg, mar = sect.find(q('pgSz')), sect.find(q('pgMar'))
    dg = sect.find(q('docGrid'))

    pw, ph = int(pg.get(q('w'))) / 20, int(pg.get(q('h'))) / 20
    lm, rm = int(mar.get(q('left'))) / 20, int(mar.get(q('right'))) / 20
    tm, bm = int(mar.get(q('top'))) / 20, int(mar.get(q('bottom'))) / 20
    text_w = pw - lm - rm

    print('=' * 84)
    print(f'【第 1 项  页面与节】{a.docx}')
    print('=' * 84)
    print(f'  页 {pw:.1f}×{ph:.1f}pt | 边距 上{tm} 右{rm} 下{bm} 左{lm} | '
          f'页脚{int(mar.get(q("footer")))/20 if mar.get(q("footer")) else "-"} | 文本列宽 {text_w:.1f}pt')
    print(f'  文档网格 docGrid: {at(dg) if dg is not None else "★ 无（请确认原件是否也没有）"}')
    if dg is None:
        WARN.append('无 docGrid：若原件有网格，版面会整体位移（本案 36.5pt）')

    print()
    print('=' * 84)
    print('【第 2 项  段落参数】')
    print('=' * 84)
    paras = [p for p in body.findall(q('p'))]
    for i, p in enumerate(paras):
        t = ''.join(x.text or '' for x in p.iter(q('t')))
        runs = [r for r in p.findall(q('r'))
                if ''.join(x.text or '' for x in r.iter(q('t')))]
        f = run_fmt(runs[0]) if runs else {}
        pf = par_fmt(p)
        sp = pf.get('spacing', {})
        line = sp.get('line')
        tag = f"line={line}({sp.get('lineRule', '-')})" if line else 'line=继承'
        scale = f' 缩放{f["scale"]}%' if f.get('scale') else ''
        print(f'  [{i:>2}] {t[:34]!r}')
        print(f'        {f.get("ea", "-")}/{f.get("ascii", "-")} {f.get("size", "-")}pt{scale}'
              f' | {tag} before={sp.get("before", "-")} after={sp.get("after", "-")}'
              f' | jc={pf.get("jc", {}).get("val", "-")} ind={pf.get("ind", "-")}')
        if f.get('size') and f['size'] not in STD_SIZES:
            print(f'        ↳ 提示：{f["size"]}pt 不是常见整档，确认是否已过"取整档"闸门')
        if f.get('scale') and f['scale'] != 100:
            print(f'        ↳ 提示：字符缩放 {f["scale"]}% —— 必须已过三道闸门（≥3 样本一致等）')
        if not runs and t.strip() == '':
            WARN.append(f'第 {i} 段为空段，确认是否与原件一致（多了/少了都算差异）')

    print()
    print('=' * 84)
    print('【第 3 项  表格参数】')
    print('=' * 84)
    tbls = body.findall(q('tbl'))
    for ti, tb in enumerate(tbls):
        tp = tb.find(q('tblPr'))
        grid = tb.find(q('tblGrid'))
        cols = [int(c.get(q('w'))) for c in grid.findall(q('gridCol'))]
        bd = tp.find(q('tblBorders'))
        mar2 = tp.find(q('tblCellMar'))
        print(f'  表{ti + 1}: {len(tb.findall(q("tr")))} 行 × {len(cols)} 列')
        print(f'       tblW={at(tp.find(q("tblW")))} jc={at(tp.find(q("jc")))} '
              f'ind={at(tp.find(q("tblInd")))} layout={at(tp.find(q("tblLayout")))}')
        print(f'       列宽(twips)={cols}  合计={sum(cols)}twips = {sum(cols)/20:.1f}pt'
              f'   文本列宽={text_w:.1f}pt  → 溢出 {(sum(cols)/20 - text_w):+.1f}pt')
        if bd is not None:
            print(f'       边框 sz={ {c.tag.replace(W, ""): c.get(q("sz")) for c in bd} }'
                  f'   (sz 单位 1/8pt；4=0.5pt, 6=0.75pt)')
        print(f'       单元格边距={at(mar2.find(q("left"))) if mar2 is not None else "默认108(5.4pt)"}')
        rows = tb.findall(q('tr'))
        hs = [(at(r.find(q('trPr') + '/' + q('trHeight'))) or {}).get('val') for r in rows]
        print(f'       行高(twips)={hs}  合计={sum(int(x) for x in hs if x)}twips'
              f' = {sum(int(x) for x in hs if x) / 20:.1f}pt')
        # 表头首格 + 单元格文字归属
        hdr = [' '.join(''.join(x.text or '' for x in tc.iter(q('t'))).split())
               for tc in rows[0].findall(q('tc'))]
        print(f'       表头={hdr}')
        hdr_run = rows[0].findall(q('tc'))[0].find(q('p') + '/' + q('r'))
        if hdr_run is not None:
            print(f'       表头字体={run_fmt(hdr_run)}')

    print()
    print('=' * 84)
    print('【第 4 项  计数（进出条目比对）】')
    print('=' * 84)
    texts = [''.join(x.text or '' for x in p.iter(q('t'))) for p in paras]
    body_txt = ''.join(texts)
    tbl_txt = ''
    for tb in tbls:
        for tc in tb.iter(q('tc')):
            tbl_txt += ''.join(x.text or '' for x in tc.iter(q('t')))
    print(f'  段落总数 {len(paras)}（非空 {sum(1 for t in texts if t.strip())}）')
    if tbls:
        cells = [sum(len(tr.findall(q('tc'))) for tr in tb.findall(q('tr'))) for tb in tbls]
        print(f'  表格 {len(tbls)} 个；每表格数 {cells}（合计 {sum(cells)}）')
    else:
        print('  表格 0 个')
    print(f'  正文下划线字符数 {body_txt.count("_")}  单元格内 {tbl_txt.count("_")}')
    print(f'  页眉/页脚部件 {len(parts)} 个：{list(parts) or "无"}')
    for n, r in parts.items():
        for i, p in enumerate(r.iter(q('p'))):
            t = ''.join(x.text or '' for x in p.iter(q('t')))
            if t.strip():
                print(f'     {n} 段落[{i}] {t!r}')
    # 全角/半角数字检查
    fw = re.findall(r'[\uff10-\uff19]', body_txt)
    if fw:
        print(f'  ⚠ 正文含全角数字 {fw}（与半角不可混用，确认原件是哪一种）')

    print()
    print('=' * 84)
    print('【第 5 项  内部一致性】')
    print('=' * 84)
    for ti, tb in enumerate(tbls):
        cols = [int(c.get(q('w'))) for c in tb.find(q('tblGrid')).findall(q('gridCol'))]
        tw = int(tb.find(q('tblPr') + '/' + q('tblW')).get(q('w')))
        ok = abs(sum(cols) - tw) <= 20
        print(f'  {"✔" if ok else "✘"} 表{ti + 1} 列宽合计 {sum(cols)} == tblW {tw}'
              f'（容差 20 twips = 1pt）')
        if not ok:
            FAIL.append(f'表{ti + 1} 列宽合计与 tblW 不一致')
    if dg is None and any((par_fmt(p).get('spacing') or {}).get('line') is None
                          for p in paras if ''.join(x.text or '' for x in p.iter(q('t'))).strip()):
        FAIL.append('无 docGrid 且存在"没有显式行距"的段落 —— 版面必然与带网格的原件不一致')
        print('  ✘ 无网格 + 有段落未设显式行距（最坏组合，见第 3 步第 6 条）')

    if a.spec:
        print()
        print('=' * 84)
        print('【第 6 项  与 spec 比对（理想：零差异）】')
        print('=' * 84)
        sp = json.load(open(a.spec, encoding='utf-8'))
        srcs = sp.get('_sources')
        if srcs:
            print('  【参数来源清单】')
            for k, v in srcs.items():
                if k.startswith('_'):
                    continue
                print(f'     {k}: {v}')
            levels = {v for k, v in srcs.items() if not k.startswith('_')}
            if levels == {'原件'}:
                print('     → 全部来自原件声明值：可直接照抄，属"原件级"交付')
            elif '反推' in levels or '实测' in levels:
                print('     → 含实测/反推项：交付说明必须写明这是**反推件**与误差范围')
        else:
            print('  ⚠ spec 缺 _sources 字段 —— 无法判断每个参数的来源等级')
            WARN.append('spec 缺 _sources：参数来源未标注，交付说明容易写成"都是原件值"')
        pgs = sp.get('page', {})
        def cmp(name, got, want):
            def norm(v):
                if isinstance(v, dict):
                    # 以 _ 开头的键是注释（_note/_说明/_sources 内层），不参与比对
                    return {k: norm(x) for k, x in v.items() if not k.startswith('_')}
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return v
            ok = norm(got) == norm(want)
            print(f'  {"✔" if ok else "✘"} {name}: 文档={got}  spec={want}')
            if not ok:
                FAIL.append(f'{name} 与 spec 不一致：{got} vs {want}')
        cmp('页宽', round(pw, 1), pgs.get('w'))
        cmp('页高', round(ph, 1), pgs.get('h'))
        for k, v in (pgs.get('margin') or {}).items():
            cmp(f'边距 {k}', {'top': tm, 'right': rm, 'bottom': bm, 'left': lm}[k], v)
        if sp.get('doc_grid') is not None:
            cmp('docGrid', at(dg) or None, sp['doc_grid'])
        # 段落逐项
        body_items = [x for x in sp.get('body', []) if x['kind'] == 'p']
        got_ps = [p for p in paras if ''.join(x.text or '' for x in p.iter(q('t'))).strip()
                  or True]
        for i, item in enumerate(body_items):
            if i >= len(got_ps):
                FAIL.append(f'spec 段落[{i}] 在文档中不存在')
                continue
            runs = [r for r in got_ps[i].findall(q('r'))
                    if ''.join(x.text or '' for x in r.iter(q('t')))]
            f = run_fmt(runs[0]) if runs else {}
            cmp(f'段落[{i}] 字号', f.get('size'), item.get('size'))
            cmp(f'段落[{i}] 中文字体', f.get('ea'), (item.get('font') or {}).get('ea'))
        # ★ 双向条目比对（进出条目比对）：多出的段落 / 缺的段落都要报。
        #   最严重的那处错误（把发文通知的版记+页码复刻进附件）就是靠这条抓的：
        #   单看每个参数都对，只有"文档里多了两段"这一个信号。
        want = [''.join(x.get('text', '')).strip() for x in sp.get('body', [])
                if x['kind'] == 'p']
        want = [x for x in want if x]
        got_ps = [''.join(x.text or '' for x in p.iter(q('t'))).strip()
                  for p in paras]
        got = [x for x in got_ps if x]
        extra = [x for x in got if x not in want]
        miss = [x for x in want if x not in got]
        print('  【双向条目比对】spec 段落 %d 条 / 文档非空段落 %d 条'
              % (len(want), len(got)))
        if extra:
            for x in extra:
                print(f'     ✘ 文档多出：{x[:40]!r}')
            FAIL.append(f'文档比 spec 多出 {len(extra)} 个非空段落（多复刻了内容？）')
        if miss:
            for x in miss:
                print(f'     ✘ 文档缺少：{x[:40]!r}')
            FAIL.append(f'文档比 spec 少 {len(miss)} 个非空段落（漏了内容？）')
        if not extra and not miss:
            print('     ✔ 非空段落集合一致')

        for ti, item in enumerate([x for x in sp.get('body', []) if x['kind'] == 'table']):
            if ti >= len(tbls):
                FAIL.append(f'spec 表{ti + 1} 在文档中不存在')
                continue
            tb = tbls[ti]
            cols = [int(c.get(q('w'))) for c in tb.find(q('tblGrid')).findall(q('gridCol'))]
            cmp(f'表{ti + 1} 列宽', cols, item['cols'])
            tp = tb.find(q('tblPr'))
            cmp(f'表{ti + 1} 对齐', (at(tp.find(q('jc'))) or {}).get('val'),
                item.get('align', 'center'))
            bd = tp.find(q('tblBorders'))
            if bd is not None and 'border_sz' in item:
                cmp(f'表{ti + 1} 边框粗细', int(bd.find(q('top')).get(q('sz'))),
                    item['border_sz'])
            mar3 = tp.find(q('tblCellMar'))
            got_cm = int(mar3.find(q('left')).get(q('w'))) if mar3 is not None else 108
            if 'cell_margin' in item:
                cmp(f'表{ti + 1} 单元格边距', got_cm, item['cell_margin'])
            hs_got = [(at(r.find(q('trPr') + '/' + q('trHeight'))) or {}).get('val')
                      for r in tb.findall(q('tr'))]
            hs_want = [str(r['h']) for r in item.get('rows', [])]
            if hs_want:
                cmp(f'表{ti + 1} 行高', hs_got, hs_want)

    print()
    print('=' * 84)
    print('【结论】')
    print('=' * 84)
    for f in FAIL:
        print(f'  ✘ FAIL: {f}')
    for w in WARN:
        print(f'  ⚠ WARN: {w}')
    if not FAIL:
        print('  ✔ 无 FAIL 项。注意：本脚本只检验"与给定参数一致"，'
              '**参数本身对不对要有外部真源（原件）才算验收**。')
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
