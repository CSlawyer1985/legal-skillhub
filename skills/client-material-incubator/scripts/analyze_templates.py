# -*- coding: utf-8 -*-
"""
analyze_templates.py — 模板分析（阶段1 步骤②）完整实现

读取律所投喂的 DOCX 模板，输出结构化分析供 AI 识别变量：
  1. 段落 + 表格 + 页眉页脚 全文提取（按序编号）
  2. 疑似变量候选自动提示（人名/金额/日期/案号/电话/身份证号正则）
  3. 脱敏检查——命中示范所/已知真实所名时告警
  4. --out json 输出结构化结果供 build_master 衔接

用法:
  python analyze_templates.py <模板.docx>                # 人类可读全文
  python analyze_templates.py <模板.docx> --out a.json   # JSON 结构化
  python analyze_templates.py <模板.docx> --candidates   # 只看疑似变量候选
  python analyze_templates.py <模板.docx> --sensitive-file <词表.txt>  # 指定脱敏词表
"""
import sys
import json
import re
import zipfile
import os
from pathlib import Path

# 脱敏检查词表——从外部配置文件读取，不再硬编码真实所名/地名
SENSITIVE_WORDS = []
_DEFAULT_WORDLIST = Path(__file__).resolve().parent.parent / "references" / "sensitive-words.txt"


def load_sensitive_words(filepath):
    """从外部配置文件读取脱敏词表（每行一个词，# 开头为注释，空行跳过）。"""
    words = []
    if not filepath.exists():
        return words
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line)
    return words

# 疑似变量候选的正则模式
CANDIDATE_PATTERNS = [
    ("案号", re.compile(r"[（(]\d{4}[）)]\S+?\d+号")),
    ("日期", re.compile(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日")),
    ("金额", re.compile(r"(?:人民币)?\s*[壹贰叁肆伍陆柒捌玖拾佰仟万亿]+\s*元|\d[\d,]*(?:\.\d+)?\s*元")),
    ("身份证号", re.compile(r"\d{17}[\dXx]")),
    ("律师执业证号", re.compile(r"\d{16,17}(?![\dXx])")) ,
    ("银行账号", re.compile(r"\d{16,19}")),
    ("手机号", re.compile(r"1[3-9]\d{9}")),
    ("不动产登记号", re.compile(r"\S{2,4}（\d{4}）\S+不动产权第\d+号")),
    ("统一社会信用代码", re.compile(r"[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}")),
    ("法院", re.compile(r"\S{2,15}人民法院")),
    ("律所", re.compile(r"\S{2,15}律师事务所")),
    ("百分比", re.compile(r"\d{1,2}\s*%")),
    ("勾选框", re.compile(r"[☑□√×✓✗]")),
    ("带字填空横线", re.compile(r"[＿_]{2,}[^＿_\s][^＿_]*[＿_]{2,}")),
    ("填空横线", re.compile(r"[＿_]{2,}")),
]

# 格式型下划线 run 检测（<w:u> 标记，文本可能为空或带字）
# 负向断言 (?!w:val="none") 排除显式无下划线标记 <w:u w:val="none"/>，避免 python-docx 生成的模板误报
UNDERLINE_RE = re.compile(
    r"<w:r[ >].*?<w:u(?:\s(?!w:val=\"none\")[^>]*)?/?>.*?<w:t[^>]*>([^<]*)</w:t>.*?</w:r>",
    re.DOTALL,
)


def extract_from_xml(xml_bytes):
    """从 word/*.xml 用正则提取段落文本（含表格单元格段落），不依赖 ElementTree——macOS Python 3.14 compat。"""
    text = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
    paras = []
    for p_match in re.finditer(r"<w:p[ >].*?</w:p>", text, re.DOTALL):
        para_xml = p_match.group(0)
        t_texts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", para_xml)
        joined = "".join(t_texts).strip()
        if joined:
            paras.append(joined)
    return paras


def extract_all(docx_path):
    """提取 document + 页眉页脚全部段落。"""
    result = {"document": [], "headers": [], "footers": []}
    with zipfile.ZipFile(docx_path) as z:
        names = z.namelist()
        if "word/document.xml" in names:
            result["document"] = extract_from_xml(z.read("word/document.xml"))
        for n in names:
            if re.match(r"word/header\d+\.xml$", n):
                result["headers"].extend(extract_from_xml(z.read(n)))
            elif re.match(r"word/footer\d+\.xml$", n):
                result["footers"].extend(extract_from_xml(z.read(n)))
    return result


def find_candidates(paras):
    """扫描疑似变量候选（长串优先 + 命中即止，避免证号被手机号/银行账号重复误报）。"""
    hits = []
    for idx, text in paras:
        used = []  # 已占用的字符区间（长串先匹配，短串跳过已占用区间）
        for label, pat in CANDIDATE_PATTERNS:
            for m in pat.finditer(text):
                # 命中即止：与已占用区间重叠则跳过
                if any(max(m.start(), s) < min(m.end(), e) for s, e in used):
                    continue
                used.append((m.start(), m.end()))
                hits.append({
                    "type": label,
                    "value": m.group(0).strip(),
                    "at": idx,
                    "context": text[max(0, m.start() - 10): m.end() + 10],
                })
    return hits


def find_underline_candidates(xml_bytes, doc_para_count):
    """
    扫描格式型下划线 run（<w:u> 标记）——它们也是变量位置的指示符。
    返回候选列表，类型为「下划线填空」。
    """
    text = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
    hits = []
    seen = set()
    for m in UNDERLINE_RE.finditer(text):
        content = m.group(1).strip()
        if content in seen:
            continue
        seen.add(content)
        hits.append({
            "type": "下划线填空",
            "value": content if content else "（空白下划线）",
            "at": "XML",
            "context": f"格式型下划线，内容[{content[:20] if content else '空'}]——变量位置指示符",
        })
    return hits


def find_empty_table_cells(xml_bytes):
    """
    扫描表格中的空白/占位符单元格——它们是需填写的变量位置（表格密集型文书易遗漏）。
    返回候选列表，类型为「空白单元格」。
    """
    text = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
    hits = []
    tc_idx = 0
    for tc in re.finditer(r"<w:tc[ >].*?</w:tc>", text, re.DOTALL):
        tc_idx += 1
        cell_text = "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", tc.group(0))).strip()
        # 空白、或仅由下划线/占位符/空格构成 → 变量候选
        if not cell_text or re.fullmatch(r"[＿_\-—·\s]*", cell_text):
            hits.append({
                "type": "空白单元格",
                "value": cell_text if cell_text else "（空）",
                "at": f"表格#{tc_idx}",
                "context": "表格空白/占位符单元格——需填写变量",
            })
    return hits


def check_sensitive(paras):
    """脱敏检查。"""
    hits = []
    for idx, text in paras:
        for w in SENSITIVE_WORDS:
            if w in text:
                hits.append({"word": w, "at": idx, "context": text[:40]})
    return hits


def detect_duplicate_sections(paras):
    """
    检测同一 DOCX 内的重复文书结构：同类文书标题出现 ≥2 次（如两份「授权委托书」，
    一份已填示例、一份空白手填），提示人工确认哪些套变量化、哪些保留原样。
    返回 {文书类型: 出现次数}。
    """
    markers = ["授权委托书", "委托代理合同", "律所函", "风险告知", "送达地址确认书"]
    from collections import Counter
    hits = []
    for idx, text in paras:
        for mk in markers:
            if mk in text:
                hits.append(mk)
    return {k: v for k, v in Counter(hits).items() if v >= 2}


def detect_layout(xml_text):
    """检测制表位分栏布局：统计含 <w:tab/> 的段落数（左右两栏抬头特征）。"""
    tab_paras = 0
    for p in re.finditer(r"<w:p[ >].*?</w:p>", xml_text, re.DOTALL):
        if "<w:tab/>" in p.group(0):
            tab_paras += 1
    return tab_paras


def suggest_alias_normalization(paras):
    """
    别名/简写归一提示：对命中的主体名称按尾缀归一，找出同一主体的多种写法
    （如「甲公司」「甲有限公司」），提示脱敏时归并为一条。
    返回 {主体简称: [多种写法]}。
    """
    from collections import defaultdict
    by_base = defaultdict(set)
    for idx, text in paras:
        for m in re.finditer(r"[\u4e00-\u9fa5]{2,8}(?:有限责任公司|有限公司|公司)", text):
            name = m.group(0)
            base = name.replace("有限责任公司", "").replace("有限公司", "").replace("公司", "")
            if base:
                by_base[base].add(name)
    return {b: sorted(names) for b, names in by_base.items() if len(names) > 1}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    mode_out = None
    show_candidates_only = "--candidates" in sys.argv
    if "--out" in sys.argv:
        i = sys.argv.index("--out")
        mode_out = sys.argv[i + 1]

    # 加载脱敏词表：优先 --sensitive-file 参数，否则默认读取 references/sensitive-words.txt
    sensitive_file = _DEFAULT_WORDLIST
    if "--sensitive-file" in sys.argv:
        i = sys.argv.index("--sensitive-file")
        sensitive_file = Path(sys.argv[i + 1])
    global SENSITIVE_WORDS
    SENSITIVE_WORDS = load_sensitive_words(sensitive_file)
    if not SENSITIVE_WORDS and sensitive_file == _DEFAULT_WORDLIST:
        # 配置文件不存在或无词——这是公开分发版本的正常状态
        pass

    data = extract_all(src)
    doc_paras = data["document"]
    numbered = [(f"{i+1:03d}", t) for i, t in enumerate(doc_paras)]
    numbered += [(f"H{i+1}", t) for i, t in enumerate(data["headers"])]
    numbered += [(f"F{i+1}", t) for i, t in enumerate(data["footers"])]

    candidates = find_candidates(numbered)
    # 格式型下划线 + 空白表格单元格检测（需要原始 XML，一次读取）
    with zipfile.ZipFile(src) as z:
        if "word/document.xml" in z.namelist():
            doc_xml_bytes = z.read("word/document.xml")
            underline_hits = find_underline_candidates(doc_xml_bytes, len(doc_paras))
            empty_cell_hits = find_empty_table_cells(doc_xml_bytes)
        else:
            underline_hits = []
            empty_cell_hits = []
    candidates.extend(underline_hits)
    candidates.extend(empty_cell_hits)
    sensitive = check_sensitive(numbered)
    dup_sections = detect_duplicate_sections(numbered)
    # 布局画像 + 别名归一（需要原始 XML）
    with zipfile.ZipFile(src) as z:
        doc_xml = z.read("word/document.xml").decode("utf-8") if "word/document.xml" in z.namelist() else ""
    tab_paras = detect_layout(doc_xml)
    alias_hints = suggest_alias_normalization(numbered)

    if mode_out:
        payload = {
            "file": src,
            "paragraph_count": len(doc_paras),
            "header_footer_count": len(data["headers"]) + len(data["footers"]),
            "paragraphs": [{"n": n, "text": t} for n, t in numbered],
            "candidates": candidates,
            "sensitive_hits": sensitive,
            "duplicate_sections": dup_sections,
            "tab_paragraph_count": tab_paras,
            "alias_hints": alias_hints,
        }
        with open(mode_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON -> {mode_out} (段落 {len(doc_paras)} / 候选 {len(candidates)} / 脱敏告警 {len(sensitive)})")
        return

    if not show_candidates_only:
        print(f"文件: {src}")
        print(f"正文段落 {len(doc_paras)} | 页眉 {len(data['headers'])} | 页脚 {len(data['footers'])}")
        print("=" * 70)
        for n, t in numbered:
            print(f"[{n}] {t}")
        print("=" * 70)

    print(f"\n--- 疑似变量候选 ({len(candidates)}) ---")
    seen = set()
    for c in candidates:
        key = (c["type"], c["value"])
        if key in seen:
            continue
        seen.add(key)
        print(f"  [{c['type']}] {c['value']}   @段落{c['at']}  上下文: …{c['context']}…")

    if sensitive:
        print(f"\n!!! 脱敏告警：命中 {len(sensitive)} 处敏感词，请确认已脱敏后再入库 !!!")
        for s in sensitive:
            print(f"  [{s['word']}] @段落{s['at']}: {s['context']}…")
    else:
        print("\n[OK] 脱敏检查通过（未命中已知敏感词）")

    if dup_sections:
        print(f"\n[!] 同文件多套文书检测：以下文书标题出现 ≥2 次，请确认哪些套变量化、哪些保留：")
        for k, v in dup_sections.items():
            print(f"  - 「{k}」出现 {v} 次")
    if tab_paras:
        print(f"\n[!] 布局画像：检测到 {tab_paras} 个段落含制表位（<w:tab/>），可能为左右两栏布局，替换时须保留 tab")
    if alias_hints:
        print(f"\n[!] 别名/简写归一提示：以下主体存在多种写法，脱敏时请归并为一条：")
        for base, names in alias_hints.items():
            print(f"  - {base}: {' / '.join(names)}")


if __name__ == "__main__":
    main()
