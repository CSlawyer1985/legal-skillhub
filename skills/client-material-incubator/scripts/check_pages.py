# -*- coding: utf-8 -*-
"""
check_pages.py — 页数估算与分页风险提示

背景：Word 的分页是「软分页」，由内容长度 + 页面设置（页边距/纸张/字体/行距）在渲染时
动态决定，DOCX 的 XML 里没有「页数」这个静态属性。变量替换（{{变量}}→真实值）后，
若真实值比占位符长，内容变长，可能把「刚好一页」的文书撑到第二页——这是 T9 格式
零改动校验（比对格式属性）覆盖不到的盲区。

本脚本做三件事，均为「估算 + 提示」，不替代 Word 打开后的人工核对：
  1. 检测手动分页符 <w:br w:type="page"/>（替换前后不变，准确）
  2. 检测 <w:lastRenderedPageBreak/>（Word 上次渲染的自动分页快照，反映母版基准页数）
  3. 分析映射表，找出「new 比 old 长」的变量（分页风险源）

用法:
  python check_pages.py <docx>                        # 输出该文件的页数估算
  python check_pages.py --vars <映射.json>            # 分析映射变量长度变化，提示分页风险
  python check_pages.py --check <母版.docx> <映射.json>  # 基准页数 + 分页风险 联合提示
"""
import sys
import re
import json
import zipfile

MANUAL_BREAK_RE = re.compile(r'<w:br[^>]*w:type="page"[^>]*/?>')


def read_document_xml(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("不是有效的 DOCX（缺少 word/document.xml）")
            return z.read("word/document.xml").decode("utf-8")
    except zipfile.BadZipFile:
        print(f"[X] 文件不是有效的 DOCX（非 zip 格式）: {docx_path}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"[X] 文件不存在: {docx_path}")
        sys.exit(1)


def count_breaks(xml):
    """返回 (手动分页符数, 自动分页快照数)。"""
    manual = len(MANUAL_BREAK_RE.findall(xml))
    auto = xml.count("<w:lastRenderedPageBreak/>")
    return manual, auto


def estimate_pages(xml):
    """估算页数：手动分页符数 + 自动分页快照数 + 1。无任何标记时返回 None。"""
    manual, auto = count_breaks(xml)
    if manual == 0 and auto == 0:
        return None, manual, auto
    return manual + auto + 1, manual, auto


def analyze_var_growth(mapping):
    """分析映射表，返回「new 比 old 长」的变量列表（分页风险源）。"""
    risks = []
    for m in mapping:
        old, new = m["old"], m["new"]
        if len(new) > len(old):
            risks.append((old, new, len(new) - len(old)))
    risks.sort(key=lambda r: -r[2])
    return risks


def show_docx(docx_path):
    xml = read_document_xml(docx_path)
    pages, manual, auto = estimate_pages(xml)
    print(f"文件: {docx_path}")
    print(f"  手动分页符: {manual} 处")
    print(f"  自动分页快照(lastRenderedPageBreak): {auto} 处")
    if pages is not None:
        print(f"  估算页数: {pages} 页（≈ 手动分页 {manual+1} + 自动分页快照 {auto}）")
    else:
        print(f"  估算页数: 无法判断（无分页标记，可能由程序生成、未经 Word 渲染）")
    print(f"  ⚠️ 提示：实际页数以 Word 打开渲染为准；若变量替换后内容变长，页数可能增加。")


def show_vars(mapping_path):
    with open(mapping_path, encoding="utf-8") as f:
        mapping = json.load(f)
    risks = analyze_var_growth(mapping)
    print(f"映射规则 {len(mapping)} 条，其中「替换后变长」{len(risks)} 条（分页风险源）：")
    if not risks:
        print("  无——所有变量替换后长度不变或变短，分页风险低。")
        return
    for old, new, d in risks:
        print(f"  [变长 +{d} 字符] {old!r} → {new!r}")
    print("\n⚠️ 以上变量替换后内容变长，若母版原本「接近一页满」，可能被撑到下一页。")
    print("  建议：生成后核对成品页数，必要时微调行距/页边距（保留客户决策权）。")


def check(master_path, mapping_path):
    xml = read_document_xml(master_path)
    pages, manual, auto = estimate_pages(xml)
    print(f"母版基准: {master_path}")
    if pages is not None:
        print(f"  基准页数: {pages} 页（手动分页 {manual} + 自动分页快照 {auto}）")
    else:
        print(f"  基准页数: 无法判断（无分页标记）——请人工确认母版页数并记录")
    print()
    show_vars(mapping_path)
    print("\n核对流程：生成成品后，用 Word 打开确认实际页数 ≤ 母版基准页数；若超页，")
    print("  优先排查上述「变长变量」，再考虑微调行距/页边距。")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--vars":
        if len(args) < 2:
            print("[X] 用法: python check_pages.py --vars <映射.json>")
            sys.exit(1)
        show_vars(args[1])
    elif args[0] == "--check":
        if len(args) < 3:
            print("[X] 用法: python check_pages.py --check <母版.docx> <映射.json>")
            sys.exit(1)
        check(args[1], args[2])
    else:
        show_docx(args[0])


if __name__ == "__main__":
    main()
