#!/usr/bin/env python3
"""Markdown → 规范排版 Word（客户背调报告专用）。
用法: python3 md2docx.py 输入.md 输出.docx
支持的 Markdown 子集: #/##/### 标题、**加粗** 行(副标题)、表格、- 列表、普通段落。
排版: 标题黑体居中; 一级标题黑体三号; 二级标题楷体四号加粗; 正文仿宋_GB2312 四号、
首行缩进2字符、1.5倍行距; 表格仿宋小四。页面 A4。
"""
import os
import re
import sys
from xml.sax.saxutils import escape as html_escape

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def set_font(run, name, size, bold=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.bold = bold


def add_runs(p, text, font, size, base_bold=False):
    # 处理行内 **加粗**
    for seg in re.split(r"(\*\*.*?\*\*)", text):
        if not seg:
            continue
        if seg.startswith("**") and seg.endswith("**"):
            r = p.add_run(seg[2:-2])
            set_font(r, font, size, True)
        else:
            r = p.add_run(seg)
            set_font(r, font, size, base_bold)


def body_para(doc, text, indent=True):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if indent:
        p.paragraph_format.first_line_indent = Pt(28)  # 四号14pt × 2字符
    add_runs(p, text, "仿宋_GB2312", 14)
    return p


def add_page_number(paragraph):
    fld = parse_xml(
        '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        ' w:instr=" PAGE "><w:r><w:rPr><w:rFonts w:eastAsia="仿宋_GB2312"/>'
        '<w:sz w:val="18"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>')
    paragraph._p.append(fld)


def setup_header_footer(doc):
    """页眉：天驰君泰 logo（scripts/tctl_logo.jpeg）；页脚：居中页码。"""
    logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tctl_logo.jpeg")
    for sec in doc.sections:
        hp = sec.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if os.path.exists(logo):
            hp.add_run().add_picture(logo, width=Cm(6.5))
        fp = sec.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run("— ")
        r.font.size = Pt(9)
        add_page_number(fp)
        r2 = fp.add_run(" —")
        r2.font.size = Pt(9)


def main(src, dst):
    lines = open(src, encoding="utf-8").read().splitlines()
    doc = Document()
    for sec in doc.sections:
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.8)
        sec.top_margin, sec.bottom_margin = Cm(3.0), Cm(2.5)
    setup_header_footer(doc)

    # 封面信息：标题（首个 # 行）与副标题（其后首个 ** 行）先写，随后插目录页
    title_idx = sub_idx = None
    for k, l in enumerate(lines):
        s = l.strip()
        if title_idx is None and s.startswith("# "):
            title_idx = k
        elif title_idx is not None and sub_idx is None and s.startswith("**") and s.endswith("**"):
            sub_idx = k
            break
    if title_idx is not None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, lines[title_idx].strip()[2:], "黑体", 22, True)
    if sub_idx is not None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, lines[sub_idx].strip(), "楷体_GB2312", 15)
    # 目录页（TOC 域：预填章节条目作为缓存结果，Word 中"更新域"后自动生成带页码目录）
    toc_entries = [l.strip()[3:] for l in lines
                   if l.strip().startswith("## ")][:40]
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = tp.add_run("目　　录")
    set_font(tr, "黑体", 16, True)
    toc_p = doc.add_paragraph()
    cached = "".join(
        f'<w:r><w:rPr><w:rFonts w:eastAsia="仿宋_GB2312"/><w:sz w:val="24"/></w:rPr>'
        f'<w:t xml:space="preserve">{html_escape(t)}</w:t></w:r><w:r><w:br/></w:r>'
        for t in toc_entries)
    toc_p._p.append(parse_xml(
        '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        ' w:instr=" TOC \\o &quot;1-2&quot; \\h \\z \\u ">' + cached + '</w:fldSimple>'))
    doc.add_page_break()

    title_done = True
    seen_heading = False
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line.strip():
            continue
        # 表格
        if line.lstrip().startswith("|"):
            rows = []
            while i <= len(lines) and line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                    rows.append(cells)
                if i >= len(lines):
                    break
                line = lines[i].rstrip()
                i += 1
            if rows:
                ncol = max(len(r) for r in rows)
                tbl = doc.add_table(rows=len(rows), cols=ncol)
                tbl.style = "Table Grid"
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                for ri, r in enumerate(rows):
                    for ci in range(ncol):
                        cell = tbl.cell(ri, ci)
                        cell.paragraphs[0].text = ""
                        add_runs(cell.paragraphs[0], r[ci] if ci < len(r) else "",
                                 "仿宋_GB2312", 12, base_bold=(ri == 0))
            continue
        # 图片：![说明](相对底稿目录的路径)
        mi = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", line.strip())
        if mi:
            img = mi.group(2)
            if not os.path.isabs(img):
                img = os.path.join(os.path.dirname(src), img)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(img, width=Cm(15.5))
            if mi.group(1):
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(cap, mi.group(1), "楷体_GB2312", 12)
            continue
        # 跳过已提前写入封面/目录的标题与副标题行
        if i - 1 in (title_idx, sub_idx):
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level, text = len(m.group(1)), m.group(2)
            if level >= 2:
                seen_heading = True
            p = doc.add_paragraph(style=f"Heading {min(level, 3)}")
            if level == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(p, text, "黑体", 16, True)
            elif level == 2:
                add_runs(p, text, "黑体", 15, True)
            else:
                add_runs(p, text, "楷体_GB2312", 14, True)
            continue
        if line.lstrip().startswith(("- ", "* ")):
            body_para(doc, "• " + line.lstrip()[2:], indent=False)
            continue
        if not seen_heading and line.strip().startswith("**") and line.strip().endswith("**"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(p, line.strip(), "楷体_GB2312", 15)
            continue
        body_para(doc, line)

    doc.save(dst)
    # 读回验证
    d2 = Document(dst)
    w, h = d2.sections[0].page_width, d2.sections[0].page_height
    assert abs(w.cm - 21) < 0.1 and abs(h.cm - 29.7) < 0.1, "页面非A4"
    print(f"OK 段落数={len(d2.paragraphs)} 表格数={len(d2.tables)} A4={w.cm:.1f}x{h.cm:.1f}cm -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
