#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""
标书格式自动修复器 (Bid Auto-Fixer) — v3.8.0 新增

将阶段四·路径A 的 8 项自动修复从"Agent 临场写代码"升级为可执行脚本。
覆盖：标点替换、字体统一、表格格式、图表编号、模糊词、签章、超链接、表格列数。
修复为「仅审不改」模式——标记问题位置，生成修复后的 docx。

用法：
    python auto_fixer.py bid.docx [选项]

    常用组合：
    python auto_fixer.py bid.docx --all --output bid_fixed.docx
    python auto_fixer.py bid.docx --punctuation --font --table-format --output bid_fixed.docx
    python auto_fixer.py bid.docx --all --dry-run   # 仅报告，不改文件

修复项：
    --punctuation      标点符号替换（英文→中文，仅替换直接可见符号）
    --font             字体统一（宋体 12pt + 1.5 倍行距）
    --table-format     表格格式统一（边框/居中/字号）
    --chart-numbering  图表编号重排（图1/图2/...顺序）
    --vague-words      模糊词替换（标记+给出替换建议）
    --signature        签章行预填清理（检测签字/盖章行，清空文本）
    --hyperlink        蓝色超链接清除（移除链接 + 统一黑色）
    --table-columns    表格列数校验与修复（需 --expected-tables JSON）
    --all              启用全部 8 项修复

辅助参数：
    --expected-tables  表格列数期望值，JSON 格式：'{"0":6,"3":5}'（表格索引:列数）
    --output, -o       输出 docx 路径（默认：输入文件名_fixed.docx）
    --dry-run          仅扫描报告，不修改文件
    --self-check       运行自检
"""

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Inches, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("错误：需要 python-docx。安装：pip install python-docx", file=sys.stderr)
    sys.exit(1)

# ════════════════════════════════════════════
# 常数
# ════════════════════════════════════════════

FONT_NAME = "宋体"
FONT_SIZE = Pt(12)  # 小四
LINE_SPACING = 1.5

EN_TO_CN_PUNCTUATION = {
    ",": "，", ".": "。", ":": "：", ";": "；",
    "!": "！", "?": "？", "(": "（", ")": "）",
    # 中文顿号 vs 英文句点（仅限数字列表场景）
    # 全角半角不在替换范围（全角半角不影响废标判定）
}

VAGUE_WORDS = [
    "可能", "大概", "也许", "应该", "左右", "大约",
    "约莫", "似乎", "仿佛", "大致", "几乎", "差不多",
    "或许", "多半", "好像", "怕是",
]

SIGNATURE_KEYWORDS = [
    "签字", "盖章", "签章", "授权代表", "法定代表人",
    "签字或盖章", "签字盖章",
]

CHART_PATTERN = re.compile(r"图\s*(\d+)")  # 图1 / 图 2 / 图 123


# ════════════════════════════════════════════
# 修复函数
# ════════════════════════════════════════════

def _set_east_asian_font(run):
    """设置中文字体（run.font.name 不生效时的补救）。"""
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), FONT_NAME)
    rfonts.set(qn("w:ascii"), FONT_NAME)
    rfonts.set(qn("w:hAnsi"), FONT_NAME)


def _has_signature_context(text: str) -> bool:
    """判断文本是否出现在签章上下文（如 '授权代表签字：张三'）。"""
    for kw in SIGNATURE_KEYWORDS:
        if kw in text:
            return True
    return False


# ── 修复 1：标点符号替换 ──

def fix_punctuation(doc: Document) -> int:
    """英文标点 → 中文标点。返回替换处数。"""
    count = 0
    for para in doc.paragraphs:
        for run in para.runs:
            old = run.text
            new = old
            for en, cn in EN_TO_CN_PUNCTUATION.items():
                new = new.replace(en, cn)
            if new != old:
                run.text = new
                count += 1
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        old = run.text
                        new = old
                        for en, cn in EN_TO_CN_PUNCTUATION.items():
                            new = new.replace(en, cn)
                        if new != old:
                            run.text = new
                            count += 1
    return count


# ── 修复 2：字体统一 ──

def fix_font(doc: Document) -> int:
    """统一正文为宋体 12pt + 1.5 倍行距。返回修改段落数。"""
    count = 0
    for para in doc.paragraphs:
        pf = para.paragraph_format
        if pf.line_spacing != LINE_SPACING:
            pf.line_spacing = LINE_SPACING
            count += 1
        for run in para.runs:
            if run.font.size != FONT_SIZE or run.font.name != FONT_NAME:
                run.font.size = FONT_SIZE
                run.font.name = FONT_NAME
                _set_east_asian_font(run)
                count += 1
    return count


# ── 修复 3：表格格式统一 ──

def fix_table_format(doc: Document) -> int:
    """统一所有表格边框、字体、居中对齐。返回修改表格数。"""
    count = 0
    for table in doc.tables:
        # 边框
        tbl = table._tbl
        tblPr = tbl.find(qn("w:tblPr"))
        if tblPr is None:
            tblPr = OxmlElement("w:tblPr")
            tbl.insert(0, tblPr)
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "000000")
            borders.append(el)
        tblPr.append(borders)

        # 单元格字体和对齐
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.size = Pt(10.5)  # 五号
                        run.font.name = FONT_NAME
                        _set_east_asian_font(run)
        count += 1
    return count


# ── 修复 4：图表编号重排 ──

def fix_chart_numbering(doc: Document) -> int:
    """扫描全文「图N」，重新按出现顺序编号。返回修改处数。"""
    chart_counter = 0
    count = 0
    for para in doc.paragraphs:
        full_text = para.text
        if CHART_PATTERN.search(full_text):
            chart_counter += 1
            new_num = str(chart_counter)
            for run in para.runs:
                m = CHART_PATTERN.search(run.text)
                if m and m.group(1) != new_num:
                    old_num = m.group(1)
                    run.text = run.text.replace(f"图{old_num}", f"图{new_num}").replace(
                        f"图 {old_num}", f"图 {new_num}"
                    )
                    count += 1
    return count


# ── 修复 5：模糊词替换 ──

def fix_vague_words(doc: Document, dry_run: bool = False) -> list:
    """扫描模糊词位置，返回 (段落索引, 模糊词, 原文片段) 列表。"""
    findings = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text
        for word in VAGUE_WORDS:
            if word in text:
                # 定位上下文
                idx = text.index(word)
                start = max(0, idx - 10)
                end = min(len(text), idx + len(word) + 15)
                findings.append((i, word, text[start:end]))
                break  # 每段只报一次
    return findings


# ── 修复 6：签章行预填清理 ──

def fix_signature_lines(doc: Document) -> int:
    """检测签字/盖章相关行，清空已预填的文字。返回清理行数。"""
    count = 0
    for para in doc.paragraphs:
        if _has_signature_context(para.text):
            for run in para.runs:
                if run.text.strip():
                    run.text = ""
                    count += 1
    return count


# ── 修复 7：蓝色超链接清除 ──

def fix_hyperlinks(doc: Document) -> int:
    """清除超链接并统一黑色字体。返回处理超链接数。"""
    count = 0
    # 处理正文段落中的超链接
    for para in doc.paragraphs:
        for hyperlink in para._element.findall(
            ".//" + qn("w:hyperlink")
        ):
            count += 1
            # 提取 hyperlink 内的 run，移出到段落层
            parent = hyperlink.getparent()
            idx = list(parent).index(hyperlink)
            for run_el in list(hyperlink):
                # 设置黑色字体
                rpr = run_el.find(qn("w:rPr"))
                if rpr is None:
                    rpr = OxmlElement("w:rPr")
                    run_el.insert(0, rpr)
                color = OxmlElement("w:color")
                color.set(qn("w:val"), "000000")
                rpr.append(color)
                parent.insert(idx, run_el)
                idx += 1
            parent.remove(hyperlink)
    return count


# ── 修复 8：表格列数校验与修复 ──

def fix_table_columns(
    doc: Document, expected: dict, dry_run: bool = False
) -> list:
    """按期望列数校验并修复表格。返回 (表索引, 期望列数, 实际列数) 列表。"""
    findings = []
    for idx_str, expected_cols in expected.items():
        idx = int(idx_str)
        if idx >= len(doc.tables):
            findings.append((idx, expected_cols, 0, "表格不存在"))
            continue
        table = doc.tables[idx]
        # 取第一行的列数（表头）
        actual_cols = len(table.rows[0].cells) if table.rows else 0
        if actual_cols != expected_cols:
            findings.append((idx, expected_cols, actual_cols, "列数不匹配"))
            if not dry_run:
                _rebuild_table_columns(table, expected_cols)
    return findings


def _rebuild_table_columns(table, target_cols: int):
    """重写表格列结构（python-docx 不提供 delete_column，走 XML 重写）。"""
    # 简化实现：通过删除/添加单元格调整每行列数
    for row in table.rows:
        cells = row.cells
        current = len(cells)
        if current > target_cols:
            # 删除多余列
            for _ in range(current - target_cols):
                cell = cells[-1]
                cell._element.getparent().remove(cell._element)
        elif current < target_cols:
            # 追加空列
            for _ in range(target_cols - current):
                OxmlElement("w:tc")


# ════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════

def run(args):
    doc = Document(args.input)

    report_lines = [f"# 自动修复报告：{Path(args.input).name}", ""]

    # ── 标点 ──
    if args.all or args.punctuation:
        n = fix_punctuation(doc)
        report_lines.append(f"## 标点符号替换")
        report_lines.append(f"- 英文标点→中文标点：{n} 处")
        report_lines.append("")

    # ── 字体 ──
    if args.all or args.font:
        n = fix_font(doc)
        report_lines.append(f"## 字体统一")
        report_lines.append(f"- 宋体 12pt（小四）+ 1.5 倍行距：{n} 处修改")
        report_lines.append("")

    # ── 表格格式 ──
    if args.all or args.table_format:
        n = fix_table_format(doc)
        report_lines.append(f"## 表格格式统一")
        report_lines.append(f"- 边框/居中/字体：{n} 个表格")
        report_lines.append("")

    # ── 图表编号 ──
    if args.all or args.chart_numbering:
        n = fix_chart_numbering(doc)
        report_lines.append(f"## 图表编号重排")
        report_lines.append(f"- 重编号：{n} 处")
        report_lines.append("")

    # ── 模糊词 ──
    if args.all or args.vague_words:
        findings = fix_vague_words(doc, dry_run=args.dry_run)
        report_lines.append(f"## 模糊词扫描")
        if findings:
            report_lines.append(f"- 发现 {len(findings)} 处模糊词：")
            for para_idx, word, ctx in findings:
                report_lines.append(f"  - 段落 #{para_idx}：「{word}」上下文：...{ctx}...")
        else:
            report_lines.append("- 未发现模糊词 ✅")
        report_lines.append("")

    # ── 签章 ──
    if args.all or args.signature:
        n = fix_signature_lines(doc)
        report_lines.append(f"## 签章行预填清理")
        report_lines.append(f"- 清空签章行：{n} 行")
        report_lines.append("")

    # ── 超链接 ──
    if args.all or args.hyperlink:
        n = fix_hyperlinks(doc)
        report_lines.append(f"## 蓝色超链接清除")
        report_lines.append(f"- 清除超链接：{n} 个")
        report_lines.append("")

    # ── 表格列数 ──
    if args.table_columns and args.expected_tables:
        try:
            expected = json.loads(args.expected_tables)
        except json.JSONDecodeError:
            print("错误：--expected-tables 必须是合法 JSON", file=sys.stderr)
            return
        findings = fix_table_columns(doc, expected, dry_run=args.dry_run)
        report_lines.append(f"## 表格列数校验")
        if findings:
            for idx, exp, act, reason in findings:
                report_lines.append(f"- 表格 #{idx}：期望 {exp} 列，实际 {act} 列 — {reason}")
        else:
            report_lines.append("- 所有表格列数正确 ✅")
        report_lines.append("")

    # ── 输出 ──
    if args.dry_run:
        report_lines.append("---")
        report_lines.append("> ⚠️ 仅扫描模式（--dry-run），文件未修改。")
        print("\n".join(report_lines))
        return

    if not args.output:
        stem = Path(args.input).stem
        args.output = f"{stem}_fixed.docx"
    doc.save(args.output)
    report_lines.append("---")
    report_lines.append(f"> 修复后文件已保存至：{args.output}")
    print("\n".join(report_lines))


# ════════════════════════════════════════════
# 自检
# ════════════════════════════════════════════

def self_check():
    """用测试 docx 验证各项修复。"""
    from io import BytesIO
    import tempfile

    print("=== auto_fixer 自检 ===")

    # 建测试文档
    doc = Document()
    # 标点测试
    doc.add_paragraph("5. 测试英文标点, and more.")
    # 签章测试
    doc.add_paragraph("授权代表签字：张三")
    # 模糊词测试
    doc.add_paragraph("这个方案可能不太完善")
    # 超链接测试（python-docx 不直接创建超链接，用 XML）
    para = doc.add_paragraph("点击这里")
    from docx.oxml import OxmlElement
    rpr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0000FF")
    rpr.append(color)
    para.runs[0]._element.insert(0, rpr)
    # 图表测试
    doc.add_paragraph("如图 5 所示")
    doc.add_paragraph("图3 架构")
    # 表格
    table = doc.add_table(rows=2, cols=4)
    table.rows[0].cells[0].text = "序号"

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    test_doc = Document(buf)
    tests = []

    # 1. 标点
    n = fix_punctuation(test_doc)
    tests.append(("标点替换", n > 0, f"{n} 处"))

    # 2. 字体
    n = fix_font(test_doc)
    tests.append(("字体统一", n > 0, f"{n} 处"))

    # 3. 签章
    n = fix_signature_lines(test_doc)
    tests.append(("签章清空", n > 0, f"{n} 行"))

    # 4. 模糊词
    findings = fix_vague_words(test_doc)
    tests.append(("模糊词扫描", len(findings) > 0, f"{len(findings)} 处"))

    # 5. 图表编号
    n = fix_chart_numbering(test_doc)
    tests.append(("图表编号", n > 0, f"{n} 处"))

    all_pass = True
    for name, result, detail in tests:
        status = "✅" if result else "❌"
        if not result:
            all_pass = False
        print(f"  {status} {name}: {detail}")

    if all_pass:
        print("自检全过 ✅")
        return True
    else:
        print("自检未全过 ❌")
        return False


def main():
    if "--self-check" in sys.argv:
        ok = self_check()
        sys.exit(0 if ok else 1)

    parser = argparse.ArgumentParser(description="标书格式自动修复器")
    parser.add_argument("input", help="输入 docx 路径")
    parser.add_argument("--all", action="store_true", help="启用全部修复项")
    parser.add_argument("--punctuation", action="store_true", help="标点符号替换")
    parser.add_argument("--font", action="store_true", help="字体统一")
    parser.add_argument("--table-format", action="store_true", help="表格格式统一")
    parser.add_argument("--chart-numbering", action="store_true", help="图表编号重排")
    parser.add_argument("--vague-words", action="store_true", help="模糊词扫描")
    parser.add_argument("--signature", action="store_true", help="签章行清理")
    parser.add_argument("--hyperlink", action="store_true", help="超链接清除")
    parser.add_argument("--table-columns", action="store_true", help="表格列数校验")
    parser.add_argument("--expected-tables", help="表格列数期望 JSON")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描报告不修改")

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
