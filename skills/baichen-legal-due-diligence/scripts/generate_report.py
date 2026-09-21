#!/usr/bin/env python3
"""
法律尽职调查报告 Word 文档生成脚本。

用法
  将此脚本复制到目标技能目录的 scripts/ 下，
  根据实际报告内容编写 generate_doc 函数体。

所需库python-docx
安装pip install python-docx

页面设置A4（21cm × 29.7cm），页边距上下 2.54cm、左右 3.18cm
正文字体楷体 小四，首行缩进两个字符，行距 1.5 倍
一级标题楷体 四号 加粗
二级标题楷体 小四 加粗
封面楷体 小二 加粗居中
表格Table Grid 样式，表头灰底加粗 小四
"""

from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document
from format_base import *

# ========== 初始化文档 ==========
# ── 委托 format_docx 处理 page_setup + Normal 样式 ──
doc = create_document([], output_path=None)


# ========== 辅助函数 ==========

def set_run_font(run, size=BODY_SIZE, bold=False, font_name=FONT_VARIANT, east_asian=FONT_VARIANT):
    run.font.size = _resolve_size(size)
    run.bold = bold
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asian)


def set_spacing(paragraph, line_spacing = LINE_SPACING, space_after=Pt(0), space_before=Pt(0),
                first_line_indent=None):
    pf = paragraph.paragraph_format
    pf.line_spacing = line_spacing
    pf.space_after = space_after
    pf.space_before = space_before
    if first_line_indent:
        pf.first_line_indent = first_line_indent


def add_cover_line(text, size=14, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER,
                   font_name=FONT_KAITI, ea=FONT_KAITI):
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, font_name=font_name, east_asian=ea)
    set_spacing(p, line_spacing = LINE_SPACING)
    return p


def add_separator():
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('_' * 50)
    run.font.size = Pt(10)
    set_spacing(p, line_spacing=1.0)
    return p


def add_blank_line(spacing=1.0):
    p = doc.add_paragraph()
    set_spacing(p, line_spacing=spacing)
    return p


def add_chapter_heading(text):
    """一级标题§1, §2 ... 楷体 四号 加粗"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=14, bold=True, font_name=FONT_KAITI, east_asian=FONT_KAITI)
    set_spacing(p, line_spacing = LINE_SPACING, space_before=BODY_SIZE)
    return p


def add_section_heading(text):
    """二级标题1.1, 2.1 ... 楷体 小四 加粗"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=BODY_SIZE, bold=True, font_name=FONT_KAITI, east_asian=FONT_KAITI)
    set_spacing(p, line_spacing = LINE_SPACING, space_before=Pt(6))
    return p


def add_preface_heading(text):
    """前言子标题（不参与编号）"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=BODY_SIZE, bold=True, font_name=FONT_KAITI, east_asian=FONT_KAITI)
    set_spacing(p, line_spacing = LINE_SPACING)
    return p


def add_body(text, indent=True):
    """正文段落楷体 小四，首行缩进两个字符"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=BODY_SIZE, bold=False, font_name=FONT_VARIANT, east_asian=FONT_VARIANT)
    if indent:
        set_spacing(p, line_spacing = LINE_SPACING, first_line_indent=Pt(24))
    else:
        set_spacing(p, line_spacing = LINE_SPACING)
    return p


def add_bold_body(text):
    """加粗正文段落（用于免责标注等）"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=BODY_SIZE, bold=True, font_name=FONT_VARIANT, east_asian=FONT_VARIANT)
    set_spacing(p, line_spacing = LINE_SPACING, first_line_indent=Pt(24))
    return p


def add_bullet(text):
    """列表项"""
    p = doc.add_paragraph()
    run = p.add_run(f'- {text}')
    set_run_font(run, size=BODY_SIZE, bold=False, font_name=FONT_VARIANT, east_asian=FONT_VARIANT)
    set_spacing(p, line_spacing = LINE_SPACING)
    return p


def add_numbered(text, num):
    """编号列表项"""
    p = doc.add_paragraph()
    run = p.add_run(f'{num}. {text}')
    set_run_font(run, size=BODY_SIZE, bold=False, font_name=FONT_VARIANT, east_asian=FONT_VARIANT)
    set_spacing(p, line_spacing = LINE_SPACING)
    return p


def add_table(headers, rows):
    """带边框表格Table Grid 样式，表头灰底加粗 小四"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(header)
        set_run_font(run, size=BODY_SIZE, bold=True, font_name=FONT_VARIANT, east_asian=FONT_VARIANT)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
        cell._element.get_or_add_tcPr().append(shading)

    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.rows[r + 1].cells[c]
            cell.text = ''
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            set_run_font(run, size=BODY_SIZE, bold=False, font_name=FONT_VARIANT, east_asian=FONT_VARIANT)

    add_blank_line(1.0)
    return table


def add_page_break():
    doc.add_page_break()


def write_cover(report_title, date_str, law_firm_cn, law_firm_en):
    """生成封面页"""
    add_blank_line(1.0)
    add_cover_line('严格保密', size=BODY_SIZE, bold=True)
    add_separator()
    add_blank_line(1.0)
    add_cover_line(report_title, size=18, bold=True, font_name=FONT_KAITI, ea=FONT_KAITI)
    add_blank_line(1.0)
    add_separator()
    add_blank_line(1.0)
    add_cover_line('本报告仅供项目有关人员参阅', size=11)
    add_blank_line(1.0)
    add_cover_line(_to_chinese_date(date_str), size=BODY_SIZE)
    add_blank_line(1.5)
    add_cover_line(law_firm_cn, size=14, bold=True, font_name=FONT_KAITI, ea=FONT_KAITI)
    add_cover_line(law_firm_en, size=BODY_SIZE)
    add_page_break()


def write_closing(date_str, law_firm_cn, law_firm_en):
    """注意律师版直接以附件收尾，不使用此函数。封面已有署名，结尾不重复落款。
    此函数保留仅为兼容历史上可能存在的特殊需求，新项目禁用。"""
    # 新项目不应调用此函数
    pass


# ========== 主入口 ==========

def generate_doc(output_path=None, report_title=None, date_str=None, law_firm_cn=None, law_firm_en=None):
    """
    主生成函数。在此函数中编排所有章节内容。
    调用 add_chapter_heading / add_section_heading / add_body / add_table 等
    构建完整报告。

    Args:
        output_path: 输出路径（可选；None 时自动生成）
    """
    write_cover(report_title, date_str, law_firm_cn, law_firm_en)

    # ===== 前言（不参与章编号）=====
    add_chapter_heading('前言')
    # add_body('...')
    # add_preface_heading('文件起草之目的')
    # ... 在此编写前言内容 ...

    # ===== §1 主要法律问题摘要 =====
    # add_chapter_heading('1. 主要法律问题摘要')
    # add_section_heading('1.1 资质证照')
    # ... 在此编写各节内容 ...

    # ===== §2-§11 正文各章 =====
    # 逐一编写 ...

    # ===== 附件 =====
    # add_chapter_heading('附件一苏州公司基本证照')
    # ...

    write_closing(date_str, law_firm_cn, law_firm_en)
    doc.save(output_path)
    print(f"报告已保存至: {output_path}")


# 脚本直接执行时调用
if __name__ == "__main__":
    generate_doc(
        output_path="/sandbox/workspace/outputs/法律尽职调查报告.docx",
        report_title="XX公司初步法律尽职调查报告",
        date_str="20XX年X月X日",
        law_firm_cn="百 宸 律 师 事 务 所",
        law_firm_en="PacGate Law Group",
    )
