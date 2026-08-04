#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利预审自检 - 机械检查脚本（确定性规则）
对专利申请文本做形式类确定性检查，输出 JSON，供 SKILL.md 步骤 3 调用。

用法:
  python mechanical_checks.py --claim "<权利要求文本>" --spec "<说明书文本>" \
      --abstract "<摘要文本>" --title "<发明名称>" --type invention
  python mechanical_checks.py --file application.txt --type utility

说明:
  - 权利要求文本建议为「权利要求书」整段；脚本按 "数字. " 或 "数字、" 切分各项。
  - 附图标记双向一致性为启发式检查（提取正文括号标记与附图说明标记对比），
    深度语义核对交由 LLM 完成。
"""
import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

# 章节标题（用于终止权利要求区抽取，避免把后续说明书/摘要误并入最后一项权利要求）
_SECTION_RE = re.compile(
    r'^(说明书|摘要|附图说明|权利要求书|技术领域|背景技术|发明内容|'
    r'具体实施方式|发明名称|申请人|代理人|权利要求)')


def split_claims(claim_text):
    """按 'N.' 或 'N、' 切分为各项权利要求，返回 (编号列表, 各项文本列表)。
    编号锚定到行首（claims 块中每项独占一行），避免化学式 'C66.'、小数 '1.0' 等
    行内数字被误判为权利要求序号（真实案件含大量化学式/参数，旧正则会切碎权利要求）。"""
    if not claim_text:
        return [], []
    # 主路径：行首锚定（re.M），仅匹配每段起始的序号
    pattern = re.compile(r'(?:^|\n)\s*(\d{1,3})\s*[\.、]', re.M)
    matches = list(pattern.finditer(claim_text))
    if not matches:
        # 退路：无换行的合并文本，退回宽松匹配（仍排除 CJK/数字前导，避免 '权利要求1'）
        pattern2 = re.compile(r'(?<![\u4e00-\u9fff\d])(\d{1,3})\s*[\.、]')
        matches = list(pattern2.finditer(claim_text))
        if not matches:
            return [], [claim_text]
    nums = [int(m.group(1)) for m in matches]
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(claim_text)
        blocks.append(claim_text[start:end])
    return nums, blocks


def _check_claims(nums, blocks):
    """对 (编号列表, 各项文本列表) 做连续性 + 句号规范性检查。"""
    issues = []
    if not nums:
        issues.append({"check": "权利要求编号", "level": "严重",
                       "msg": "未识别到任何权利要求编号（应为 '1. ' 形式）"})
        return issues
    expected = list(range(1, len(nums) + 1))
    if nums != expected:
        issues.append({"check": "编号连续性", "level": "严重",
                       "msg": f"权利要求编号不连续：识别到 {nums}，应为 1..{len(nums)}"})
    for i, blk in enumerate(blocks, 1):
        periods = blk.count('。')
        if periods != 1:
            issues.append({"check": "句号规范性", "level": "中等",
                           "msg": f"权利要求 {i} 含 {periods} 个句号，应恰好 1 个（结尾句号）"})
    return issues


def check_claim_numbering(claim_text):
    nums, blocks = split_claims(claim_text)
    return _check_claims(nums, blocks)


def check_abstract(abstract):
    if not abstract:
        return []
    n = len(abstract.strip())
    if n > 300:
        return [{"check": "摘要字数", "level": "严重",
                 "msg": f"摘要 {n} 字（含标点），超过 300 字上限（细则第 26 条）"}]
    return []


def check_title(title):
    if not title:
        return []
    n = len(title.strip())
    if n > 25:
        return [{"check": "发明名称长度", "level": "中等",
                 "msg": f"发明名称 {n} 字，超过 25 字上限"}]
    return []


def check_figure_markers(spec_text):
    """启发式：提取说明书正文括号中的附图标记（兼容半角/全角括号），与「附图说明」段中
    列出的标记做一致性比对（细则第21条：附图说明应说明各标记含义）。
    标记形式支持 (10)(10a)（10）（10a）以及「10-基板」式列举。"""
    issues = []
    if not spec_text:
        return issues
    # 正文括号标记，兼容半角()与全角（）
    body_markers = set(re.findall(r'[\(（](\d{1,3}[a-z]?)[\)）]', spec_text))
    # 附图说明段
    m = re.search(r'附图说明[^\n]*\n(.*?)(?:具体实施方式|$)', spec_text, re.S)
    ref_markers = set()
    if m:
        seg = m.group(1)
        # 括号内标记（半角/全角）
        ref_markers |= set(re.findall(r'[\(（](\d{1,3}[a-z]?)[\)）]', seg))
        # 「10-基板」式列举
        ref_markers |= set(re.findall(r'(?<!\d)(\d{1,3})(?=\s*[-—])', seg))
    if body_markers and not ref_markers:
        issues.append({"check": "附图标记一致性", "level": "中等",
                       "msg": f"正文出现附图标记 {sorted(body_markers)[:10]} 但附图说明未对应列出（细则第21条：附图说明应说明各标记含义）"})
    elif body_markers and ref_markers:
        only_body = body_markers - ref_markers
        if only_body:
            issues.append({"check": "附图标记一致性", "level": "中等",
                           "msg": f"正文出现但附图说明未对应的标记（示例）：{sorted(only_body)[:10]}；请核对双向一致（细则第21条）"})
    return issues


def check_invention_options(claim_text, type_):
    """示例占位：发明的预审专项勾选（早日公布/实质审查/放弃主动修改）来自请求书文本，
    由调用方将请求书文本传入 --request 后在此校验。"""
    return []


def _zh_num(n):
    """简体中文数字（计数用），支持 1-9999。"""
    if n <= 0:
        return str(n)
    digits = "零一二三四五六七八九"
    units = ["", "十", "百", "千"]
    s = ""
    str_n = str(n)
    length = len(str_n)
    for i, ch in enumerate(str_n):
        d = int(ch)
        pos = length - i - 1
        if d == 0:
            if s and not s.endswith("零"):
                s += "零"
        else:
            s += digits[d] + units[pos]
    s = s.replace("零零", "零").strip("零")
    if s.startswith("一十"):  # 口语：10->十, 11->十一
        s = s[1:]
    return s


def _alpha(n):
    """1->a, 26->z, 27->aa ..."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(ord('a') + r) + s
    return s


def _roman(n):
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
            (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
            (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for v, sym in vals:
        while n >= v:
            s += sym
            n -= v
    return s


def _render_number(numFmt, n):
    nf = numFmt or "decimal"
    if nf in ("decimal", "decimalFullWidth", "decimalEnclosedCircle", "ideographTraditional"):
        return str(n)
    if nf == "decimalZero":
        return f"{n:02d}" if n < 100 else str(n)
    if nf in ("chineseCounting", "chineseLegalSimplified", "chineseCountingThousand"):
        return _zh_num(n)
    if nf == "lowerLetter":
        return _alpha(n)
    if nf == "upperLetter":
        return _alpha(n).upper()
    if nf == "lowerRoman":
        return _roman(n).lower()
    if nf == "upperRoman":
        return _roman(n).upper()
    if nf in ("none", "bullet"):
        return ""
    return str(n)


def _load_numbering(z):
    """读取 word/numbering.xml。返回 (num2abs, abs_map)：
    num2abs: numId -> abstractNumId；abs_map: abstractNumId -> {ilvl:(numFmt,lvlText,start)}。"""
    try:
        data = z.read("word/numbering.xml")
    except KeyError:
        return {}, {}
    try:
        nroot = ET.fromstring(data)
    except ET.ParseError:
        return {}, {}
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    abs_map = {}
    for an in nroot.iter(ns + "abstractNum"):
        aid = an.get(ns + "abstractNumId")
        levels = {}
        for lvl in an.findall(ns + "lvl"):
            il = int(lvl.get(ns + "ilvl"))
            fmt = lvl.find(ns + "numFmt")
            txt = lvl.find(ns + "lvlText")
            start = lvl.find(ns + "start")
            levels[il] = (
                fmt.get(ns + "val") if fmt is not None else "decimal",
                txt.get(ns + "val") if txt is not None else "%1.",
                int(start.get(ns + "val")) if start is not None else 1,
            )
        abs_map[aid] = levels
    num2abs = {}
    for nm in nroot.iter(ns + "num"):
        nid = nm.get(ns + "numId")
        a = nm.find(ns + "abstractNumId")
        if a is not None:
            num2abs[nid] = a.get(ns + "val")
    return num2abs, abs_map


def _read_docx_paras(path):
    """解析 .docx 为段落列表 [(ilvl, text), ...]。
    ilvl：Word 自动编号层级（无编号为 0）；text 已带还原的序号前缀（如 '1.' '一、'）。
    无第三方依赖（zipfile + xml）。表格单元格文字同样位于 <w:p> 中会被提取。"""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        num2abs, abs_map = _load_numbering(z)
    counters = {}  # numId -> {ilvl: 当前计数}
    out = []
    for p in root.iter(ns + "p"):
        numId = None
        ilvl = 0
        ppr = p.find(ns + "pPr")
        if ppr is not None:
            numPr = ppr.find(ns + "numPr")
            if numPr is not None:
                nid = numPr.find(ns + "numId")
                ilv = numPr.find(ns + "ilvl")
                if nid is not None:
                    numId = nid.get(ns + "val")
                if ilv is not None:
                    ilvl = int(ilv.get(ns + "val"))
        texts = "".join(t.text for t in p.iter(ns + "t") if t.text)
        prefix = ""
        if numId is not None and numId in num2abs:
            aid = num2abs[numId]
            levels = abs_map.get(aid, {})
            if ilvl in levels:
                fmt, lvlText, start = levels[ilvl]
                cdict = counters.setdefault(numId, {})
                for k in [k for k in list(cdict.keys()) if k > ilvl]:
                    del cdict[k]
                cdict[ilvl] = cdict.get(ilvl, start - 1) + 1
                nums = []
                for i in range(ilvl + 1):
                    f, t, s = levels.get(i, ("decimal", "%1.", 1))
                    nums.append(_render_number(f, cdict.get(i, s)))
                rendered = lvlText
                for idx, num in enumerate(nums, start=1):
                    rendered = rendered.replace(f"%{idx}", num)
                prefix = rendered
        out.append((ilvl, prefix + texts))
    return out


def read_docx(path):
    """从 .docx 提取纯文本（按段落，保留段落边界），无第三方依赖。
    关键增强：解析 Word 自动编号（numbering.xml 的 numPr），将列表序号还原为
    '1.' '一、' 等形式前缀，避免代理所排版文档丢失权利要求序号导致误报。"""
    return "\n".join(t for _, t in _read_docx_paras(path))


def extract_claims(paras):
    """从 (ilvl, line) 段落列表抽取权利要求。
    仅将【顶层 ilvl==0】且序号连续 1,2,3... 的段落视为独立权利要求；
    权利要求正文常跨多个段落（仅首段带 'N.'，后续为无编号续行），这些续行
    （ilvl==0 或 ilvl>0 嵌套步骤）均归入当前权利要求；遇到序号不再连续的最顶层
    编号段落即判定权利要求区结束（其后的 '1.' 多为说明书步骤，不再计入）。
    返回 [(num, claim_text), ...]。"""
    start = None
    for i, (ilvl, line) in enumerate(paras):
        if ilvl == 0 and re.match(r'^\s*1[\.、]', line):
            start = i
            break
    if start is None:
        return []
    claims = []
    current = None
    expected = 1
    i = start
    n = len(paras)
    while i < n:
        ilvl, line = paras[i]
        m = re.match(r'^\s*(\d{1,3})[\.、]', line)
        if ilvl == 0 and m:
            num = int(m.group(1))
            if num == expected:
                if current is not None:
                    claims.append(current)
                current = (num, line)
                expected = num + 1
            else:
                # 序号不再连续 -> 权利要求区结束（后续可能是说明书步骤等）
                break
        elif current is not None:
            # 遇到章节标题（说明书/摘要/...）即判定权利要求区结束，停止并入
            if _SECTION_RE.match(line.strip()):
                break
            # 续行（无编号的 ilvl==0 续写，或 ilvl>0 嵌套步骤）归入当前权利要求
            current = (current[0], current[1] + "\n" + line)
        i += 1
    if current is not None:
        claims.append(current)
    return claims


def _detect_claim_block(text):
    """退路（主要用于无层级信息的 .txt）：按行首连续编号 '1.'/'1、' 识别权利要求块。"""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*(\d{1,3})[\.、]', line):
            start = i
            break
    if start is None:
        return ""
    collected = [lines[start]]
    expected = 2
    for i in range(start + 1, len(lines)):
        line = lines[i]
        m = re.match(r'^\s*(\d{1,3})[\.、]', line)
        if m and int(m.group(1)) == expected:
            collected.append(line)
            expected += 1
        elif line.strip() == "":
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            nm = re.match(r'^\s*(\d{1,3})[\.、]', nxt)
            if nm and int(nm.group(1)) == expected:
                continue
            break
        else:
            break
    return "\n".join(collected)


def main():
    ap = argparse.ArgumentParser(description="专利预审自检 - 机械检查")
    ap.add_argument("--claim", help="权利要求书文本")
    ap.add_argument("--spec", help="说明书文本")
    ap.add_argument("--abstract", help="摘要文本")
    ap.add_argument("--title", help="发明名称")
    ap.add_argument("--request", help="请求书文本（用于勾选项校验）")
    ap.add_argument("--type", default="invention", choices=["invention", "utility"])
    ap.add_argument("--file", help="合并申请文本文件（utf-8）")
    args = ap.parse_args()

    claim = args.claim or ""
    spec = args.spec or ""
    abstract = args.abstract or ""
    title = args.title or ""

    paras = None  # (ilvl, line) 列表，仅 .docx 时可用
    if args.file:
        try:
            if args.file.lower().endswith(".docx"):
                paras = _read_docx_paras(args.file)
                text = "\n".join(t for _, t in paras)
            else:
                text = open(args.file, encoding="utf-8").read()
        except Exception as e:
            print(json.dumps({"error": f"读取文件失败: {e}"}, ensure_ascii=False))
            sys.exit(1)
        # 简易分块：先尝试标准标题词，再尝试同义/常见写法，最后用编号序列兜底
        cm = (re.search(r'权利要求书(.*?)(?:说明书|$)', text, re.S)
              or re.search(r'权利要求[^\n：:]*[：:]\s*(.*?)(?:说明书|$)', text, re.S))
        sm = (re.search(r'说明书(.*?)(?:摘要|$)', text, re.S)
              or re.search(r'说明书[^\n：:]*[：:]\s*(.*?)(?:摘要|$)', text, re.S))
        am = re.search(r'摘\s*要[^\n：:]*[：:]\s*(.*?)(?:\n\n|$)', text, re.S)
        tm = (re.search(r'发明名称[^\n：:]*[：:]\s*([^\n]+)', text)
              or re.search(r'名\s*称[^\n：:]*[：:]\s*([^\n]+)', text))
        if cm:
            claim = cm.group(1)
        else:
            claim = _detect_claim_block(text)  # 退路：连续编号序列识别
        if sm:
            spec = sm.group(1)
        if am:
            abstract = am.group(1).strip()
        if tm:
            title = tm.group(1).strip()
        else:
            # 标题退路：用文件名（去扩展名）作为发明名称候选
            title = os.path.splitext(os.path.basename(args.file))[0]

    issues = []
    if paras is not None:
        # .docx：用 ilvl 感知的权利要求抽取（顶层序号=权利要求，嵌套步骤不误判）
        claims = extract_claims(paras)
        if claims:
            issues += _check_claims([c[0] for c in claims], [c[1] for c in claims])
        else:
            issues += check_claim_numbering(claim)
    else:
        issues += check_claim_numbering(claim)
    issues += check_abstract(abstract)
    issues += check_title(title)
    issues += check_figure_markers(spec)

    # 发明勾选项校验（基于请求书文本）
    if args.type == "invention" and args.request:
        req = args.request
        for label, kw in [("请求早日公布", "早日公布"),
                          ("请求实质审查", "实质审查"),
                          ("放弃主动修改", "放弃主动修改")]:
            if kw not in req:
                issues.append({"check": "预审专项勾选", "level": "严重",
                               "msg": f"发明请求书未检出勾选项：{label}（细则第 57 条）"})

    summary = {
        "issues": issues,
        "count": len(issues),
        "severe": sum(1 for i in issues if i["level"] == "严重"),
        "medium": sum(1 for i in issues if i["level"] == "中等"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
