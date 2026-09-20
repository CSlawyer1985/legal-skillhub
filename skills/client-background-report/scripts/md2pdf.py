#!/usr/bin/env python3
"""Markdown → PDF（附件汇编用，reportlab 内置中文字体 STSong-Light）。
用法: .venv/bin/python md2pdf.py 输入.md 输出.pdf
支持: #/##/### 标题、表格、- 列表、普通段落；**加粗** 标记会被去除。
"""
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

STYLES = {
    1: ParagraphStyle("h1", fontName="STSong-Light", fontSize=18, leading=26,
                      alignment=1, spaceAfter=10),
    2: ParagraphStyle("h2", fontName="STSong-Light", fontSize=14, leading=20,
                      spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1a3a6b")),
    3: ParagraphStyle("h3", fontName="STSong-Light", fontSize=12, leading=18,
                      spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="STSong-Light", fontSize=10.5,
                           leading=17, firstLineIndent=21, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="STSong-Light", fontSize=9, leading=13),
}


def clean(text):
    return text.replace("**", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("STSong-Light", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(A4[0] / 2, 12 * mm, f"— 第 {doc.page} 页 —")
    canvas.drawRightString(A4[0] - 22 * mm, 12 * mm, "信息来源汇编·客户背调附件")
    canvas.restoreState()


def main(src, dst):
    lines = open(src, encoding="utf-8").read().splitlines()
    story = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line.strip():
            continue
        if line.lstrip().startswith("|"):
            rows = []
            while True:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                    rows.append(cells)
                if i >= len(lines):
                    break
                line = lines[i].rstrip()
                i += 1
                if not line.lstrip().startswith("|"):
                    break
            if rows:
                ncol = max(len(r) for r in rows)
                data = [[Paragraph(clean(r[c]) if c < len(r) else "", STYLES["cell"])
                         for c in range(ncol)] for r in rows]
                tbl = Table(data, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story += [tbl, Spacer(1, 4 * mm)]
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = min(len(m.group(1)), 3)
            story.append(Paragraph(clean(m.group(2)), STYLES[level]))
            continue
        if line.lstrip().startswith(("- ", "* ")):
            story.append(Paragraph("• " + clean(line.lstrip()[2:]), STYLES["body"]))
            continue
        story.append(Paragraph(clean(line), STYLES["body"]))

    doc = SimpleDocTemplate(dst, pagesize=A4, leftMargin=22 * mm,
                            rightMargin=22 * mm, topMargin=25 * mm,
                            bottomMargin=20 * mm, title="信息来源汇编")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"OK -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
