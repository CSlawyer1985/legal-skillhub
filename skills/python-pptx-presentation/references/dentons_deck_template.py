"""Dentons/Dacheng editable PPTX starter for python-pptx.

Copy this file into the workspace and adapt SLIDE_DATA before running.
It intentionally uses native PowerPoint text boxes, shapes, tables, and lines.
No logos or full-slide screenshots are used.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


WIDE_W = Inches(13.333)
WIDE_H = Inches(7.5)

PURPLE = RGBColor(0x6B, 0x2D, 0x8B)
BRIGHT_PURPLE = RGBColor(0x8B, 0x2F, 0xC9)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GOLD = RGBColor(0xF5, 0xE6, 0xC8)
LIGHT_GOLD = RGBColor(0xFF, 0xF7, 0xE6)
LAVENDER = RGBColor(0xF5, 0xED, 0xFC)
DARK_GRAY = RGBColor(0x40, 0x40, 0x40)
MEDIUM_GRAY = RGBColor(0x80, 0x80, 0x80)
LIGHT_GRAY = RGBColor(0xE0, 0xE0, 0xE0)
ULTRA_LIGHT = RGBColor(0xF8, 0xF8, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

TITLE_FONT = "Source Han Serif CN"
BODY_FONT = "Source Han Sans CN"
FOOTER_TEXT = "大成律师事务所"


def add_solid_rect(slide, x, y, w, h, fill, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
    return shape


def add_text(slide, text, x, y, w, h, *, size, color=BLACK, font=BODY_FONT, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(x, y, w, h)
    box.text_frame.clear()
    box.text_frame.word_wrap = True
    box.text_frame.vertical_anchor = valign
    box.text_frame.margin_left = Inches(0.02)
    box.text_frame.margin_right = Inches(0.02)
    box.text_frame.margin_top = Inches(0.02)
    box.text_frame.margin_bottom = Inches(0.02)
    paragraph = box.text_frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_multiline(slide, lines, x, y, w, h, *, size=16, color=BLACK, bullet=False):
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.06)
    frame.margin_right = Inches(0.06)
    frame.margin_top = Inches(0.04)
    frame.margin_bottom = Inches(0.04)
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.level = 0
        paragraph.space_after = Pt(8)
        paragraph.alignment = PP_ALIGN.LEFT
        if bullet:
            paragraph.text = f"• {line}"
            for run in paragraph.runs:
                run.font.name = BODY_FONT
                run.font.size = Pt(size)
                run.font.color.rgb = color
        else:
            run = paragraph.add_run()
            run.text = line
            run.font.name = BODY_FONT
            run.font.size = Pt(size)
            run.font.color.rgb = color
    return box


def add_title_bar(slide, title, page_no):
    add_text(slide, title, Inches(0.83), Inches(0.42), Inches(11.67), Inches(0.75),
             size=24, color=PURPLE, font=TITLE_FONT, bold=True)
    line = slide.shapes.add_connector(1, Inches(0.83), Inches(1.25), Inches(12.5), Inches(1.25))
    line.line.color.rgb = LIGHT_GRAY
    line.line.width = Pt(1)
    add_footer(slide, page_no)


def add_footer(slide, page_no):
    add_text(slide, FOOTER_TEXT, Inches(0.83), Inches(7.05), Inches(5.5), Inches(0.3),
             size=11, color=MEDIUM_GRAY)
    add_text(slide, str(page_no), Inches(7.0), Inches(7.05), Inches(5.5), Inches(0.3),
             size=11, color=MEDIUM_GRAY, align=PP_ALIGN.RIGHT)


def add_cover(prs, title, subtitle_en, info):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, BLACK)
    add_solid_rect(slide, Inches(0.85), Inches(0.72), Inches(0.04), Inches(5.9), GOLD)
    add_text(slide, title, Inches(1.18), Inches(2.0), Inches(10.9), Inches(1.25),
             size=44, color=WHITE, font=TITLE_FONT, bold=True)
    add_text(slide, subtitle_en, Inches(1.2), Inches(3.25), Inches(10.2), Inches(0.5),
             size=16, color=GOLD)
    add_text(slide, info, Inches(1.2), Inches(5.78), Inches(10.2), Inches(0.38),
             size=14, color=WHITE)


def add_toc(prs, items):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, WHITE)
    add_solid_rect(slide, 0, 0, Inches(3.45), WIDE_H, PURPLE)
    add_text(slide, "CONTENTS", Inches(0.6), Inches(0.86), Inches(2.3), Inches(0.55),
             size=30, color=WHITE, font=TITLE_FONT, bold=True, align=PP_ALIGN.CENTER)
    for index, item in enumerate(items, start=1):
        y = Inches(1.45 + (index - 1) * 1.05)
        add_text(slide, f"{index:02d}", Inches(4.1), y, Inches(0.72), Inches(0.45),
                 size=20, color=PURPLE, font=TITLE_FONT, bold=True)
        add_text(slide, item["title"], Inches(5.0), y - Inches(0.03), Inches(6.8), Inches(0.42),
                 size=20, color=BLACK, font=TITLE_FONT, bold=True)
        add_text(slide, item.get("subtitle", ""), Inches(5.0), y + Inches(0.42), Inches(6.8), Inches(0.32),
                 size=13, color=DARK_GRAY)


def add_transition(prs, number, title, desc):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, ULTRA_LIGHT)
    add_text(slide, number, Inches(0.9), Inches(1.15), Inches(2.8), Inches(1.1),
             size=80, color=GOLD, font=TITLE_FONT, bold=True)
    add_text(slide, title, Inches(3.8), Inches(2.4), Inches(7.8), Inches(0.95),
             size=56, color=PURPLE, font=TITLE_FONT, bold=True)
    add_text(slide, desc, Inches(3.86), Inches(3.55), Inches(7.2), Inches(0.5),
             size=20, color=DARK_GRAY)


def add_content(prs, title, bullets, page_no):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, WHITE)
    add_title_bar(slide, title, page_no)
    add_multiline(slide, bullets, Inches(1.05), Inches(1.72), Inches(10.95), Inches(4.85),
                  size=16, color=BLACK, bullet=True)


def add_cards(prs, title, cards, page_no, columns=3):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, WHITE)
    add_title_bar(slide, title, page_no)
    gap = Inches(0.28)
    left = Inches(0.83)
    top = Inches(1.65)
    width = (Inches(11.67) - gap * (columns - 1)) / columns
    height = Inches(4.65)
    body_size = 16 if columns <= 3 else 14
    for index, card in enumerate(cards[:columns]):
        x = left + (width + gap) * index
        add_solid_rect(slide, x, top, width, height, LAVENDER, line=LIGHT_GRAY)
        add_text(slide, card["title"], x + Inches(0.24), top + Inches(0.24), width - Inches(0.48), Inches(0.48),
                 size=18, color=PURPLE, font=TITLE_FONT, bold=True)
        add_text(slide, card["body"], x + Inches(0.24), top + Inches(0.95), width - Inches(0.48), height - Inches(1.2),
                 size=body_size, color=BLACK)


def add_table_slide(prs, title, headers, rows, page_no):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, WHITE)
    add_title_bar(slide, title, page_no)
    table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(0.95), Inches(1.55),
                                         Inches(11.4), Inches(4.95))
    table = table_shape.table
    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = PURPLE
        cell.text = header
        paragraph = cell.text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        for run in paragraph.runs:
            run.font.name = BODY_FONT
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = WHITE
    for row_index, row in enumerate(rows, start=1):
        for col, value in enumerate(row):
            cell = table.cell(row_index, col)
            cell.fill.solid()
            cell.fill.fore_color.rgb = ULTRA_LIGHT if row_index % 2 == 0 else WHITE
            cell.text = str(value)
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.name = BODY_FONT
                    run.font.size = Pt(12)
                    run.font.color.rgb = BLACK


def add_quote(prs, title, body, page_no):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, WHITE)
    add_title_bar(slide, title, page_no)
    add_solid_rect(slide, Inches(1.08), Inches(1.75), Inches(0.09), Inches(4.35), PURPLE)
    add_text(slide, body, Inches(1.48), Inches(1.9), Inches(10.3), Inches(3.9),
             size=23, color=BLACK, font=TITLE_FONT)


def add_ending(prs, title="谢谢！", slogan="全球资源 本土智慧"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_solid_rect(slide, 0, 0, WIDE_W, WIDE_H, PURPLE)
    add_text(slide, title, Inches(0.85), Inches(2.55), Inches(11.65), Inches(0.95),
             size=44, color=WHITE, font=TITLE_FONT, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, slogan, Inches(0.85), Inches(3.68), Inches(11.65), Inches(0.45),
             size=18, color=GOLD, align=PP_ALIGN.CENTER)


def build_deck(out_path: str | Path) -> None:
    prs = Presentation()
    prs.slide_width = WIDE_W
    prs.slide_height = WIDE_H

    add_cover(prs, "公共数据资源授权运营合规要点", "Compliance Briefing on Public Data Resource Operation", "大成律师事务所 · 2026")
    add_toc(prs, [
        {"title": "监管背景", "subtitle": "政策框架与关键口径"},
        {"title": "定价逻辑", "subtitle": "范围、成本、收益与程序"},
        {"title": "合规建议", "subtitle": "合同、内控与信息披露"},
    ])
    add_transition(prs, "01", "监管背景", "从政策目标到运营边界")
    add_content(prs, "监管背景与适用场景", [
        "公共数据授权运营强调依法依规、分类分级、授权可追溯。",
        "运营方案通常需要明确数据范围、使用目的、授权期限、收益分配和安全责任。",
        "律师审查时应同步关注价格依据、个人信息保护、数据安全和国资监管要求。",
    ], 4)
    add_cards(prs, "重点审查维度", [
        {"title": "授权边界", "body": "核对数据目录、授权主体、使用目的、再授权限制和退出机制，避免泛化授权。"},
        {"title": "价格机制", "body": "关注成本归集、准许收益、调价程序和公开透明要求，保留可审计依据。"},
        {"title": "安全责任", "body": "落实数据分级分类、访问控制、日志留存、事件报告和第三方管理责任。"},
    ], 5)
    add_table_slide(prs, "合同条款清单", ["模块", "审查重点", "建议"], [
        ["标的范围", "数据目录、字段、更新频率", "附件化并设变更流程"],
        ["费用条款", "计费口径、调价、税费", "绑定价格依据和审计权"],
        ["合规义务", "个人信息、数据安全、保密", "设置违约责任与整改期限"],
        ["终止退出", "数据返还、删除、留痕", "明确交接证明和后评估"],
    ], 6)
    add_quote(prs, "示例引用页", "涉及具体条文或政策依据时，应在答案中列明原文、法名、条号或章节、效力以及本库版本日期。", 7)
    add_ending(prs)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)


if __name__ == "__main__":
    build_deck(Path("output/dacheng_public_data_compliance.pptx"))
