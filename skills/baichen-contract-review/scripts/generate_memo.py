#!/usr/bin/env python3
"""
generate_memo.py — 合同审查意见书（法律备忘录）Word 文档生成工具

用法: generate_memo(meta, sections, output_path)

支持的 section type:
- greeting: 致辞段落
- body_title: 正文标题
- section_title: 节标题
- body: 正文段落 (楷体 12pt, 首行缩进2字符)
- bold_body: 加粗正文
- body_no_indent: 无缩进正文
- risk_item: 风险条款卡片
- closing: 结语段落
- signature: 落款
- blank: 空行
"""

from docx import Document
import os
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
import os, sys

# ── 格式底座（page_setup / Normal 样式委托给 create_document）──
_sys_path = os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references')
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)
from format_docx import create_document
from format_base import *

# _docx_base 保留 set_font 自定义内容辅助
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../_shared'))
from _docx_base import set_font


def _add_multiline(doc, text, indent_cm=0.85, no_indent_prefix=None):
    """将多行文本拆分为多个段落，每段使用楷体12pt，可指定首行缩进。"""
    for para_text in text.strip().split('\n'):
        para_text = para_text.strip()
        if not para_text:
            continue
        p = doc.add_paragraph()
        run = p.add_run(para_text)
        set_font(run, FONT_VARIANT, 12)
        if no_indent_prefix and para_text.startswith(no_indent_prefix):
            p.paragraph_format.first_line_indent = Cm(0)
        else:
            p.paragraph_format.first_line_indent = Cm(indent_cm)


def _add_risk_field(doc, label, text):
    """添加"标签内容"格式的风险项段落，标签加粗，内容正常。"""
    p = doc.add_paragraph()
    run = p.add_run(label)
    set_font(run, FONT_VARIANT, 12, bold=True)
    run2 = p.add_run(text)
    set_font(run2, FONT_VARIANT, 12)
    p.paragraph_format.first_line_indent = Cm(0.85)


def _add_page_header(doc, text):
    """Add '保密文件' page header."""
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(text)
        set_font(run, FONT_VARIANT, 10)


def _add_header_table(doc, meta):
    """Add title area as a table: date, recipient, sender, subject."""
    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    # Set table borders
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')

    rows_data = [
        ('日  期', _to_chinese_date(meta.get('date', ''))),
        ('收件人', meta.get('recipient', '')),
        ('发件人', meta.get('sender', '')),
        ('事  由', meta.get('subject', '')),
        ('', ''),
        ('', ''),
    ]

    for i, (label, value) in enumerate(rows_data):
        row = table.rows[i]

        # Label cell
        cell_label = row.cells[0]
        cell_label.width = Cm(3)
        p = cell_label.paragraphs[0]
        run = p.add_run(label)
        set_font(run, FONT_VARIANT, 12, bold=True)

        # Value cell
        cell_value = row.cells[1]
        cell_value.width = Cm(13)
        p = cell_value.paragraphs[0]
        run = p.add_run(value)
        set_font(run, FONT_VARIANT, 12)


def generate_memo(meta, sections, output_path=None):
    """
    Generate a legal memo Word document from structured data.

    Args:
        meta: Dict with page_header, date, recipient, sender, subject
        sections: List of section dicts
        output_path: Path to save .docx (optional; auto-generated if None)

    Returns:
        str: output_path
    """
    # ── 委托 format_docx 处理 page_setup + Normal 样式 ──
    doc = create_document([], output_path=None)

    # Page header
    _add_page_header(doc, meta.get('page_header', '保密文件'))

    # Header table
    _add_header_table(doc, meta)

    # Spacing after table
    doc.add_paragraph()

    # Process sections
    for sec in sections:
        sec_type = sec.get('type', 'body')

        if sec_type == 'greeting':
            _add_multiline(doc, sec['text'], indent_cm=0.85, no_indent_prefix='敬启者')

        elif sec_type == 'body_title':
            doc.add_paragraph()  # spacing before
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(sec['text'])
            set_font(run, TITLE_FONT, 14, bold=True)
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            doc.add_paragraph()  # spacing after

        elif sec_type == 'section_title':
            p = doc.add_paragraph()
            run = p.add_run(sec['text'])
            set_font(run, TITLE_FONT, 12, bold=True)
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = BODY_SIZE
            p.paragraph_format.space_after = Pt(3)

        elif sec_type == 'body':
            _add_multiline(doc, sec['text'], indent_cm=0.85)

        elif sec_type == 'bold_body':
            p = doc.add_paragraph()
            run = p.add_run(sec['text'])
            set_font(run, FONT_VARIANT, 12, bold=True)
            p.paragraph_format.first_line_indent = Cm(0.85)

        elif sec_type == 'body_no_indent':
            _add_multiline(doc, sec['text'], indent_cm=0)

        elif sec_type == 'risk_item':
            # Risk label line: "条款X | 主题 | 风险等级"
            label = sec.get('label', '')
            topic = sec.get('topic', '')
            risk = sec.get('risk', '')

            doc.add_paragraph()  # spacing
            p = doc.add_paragraph()
            run = p.add_run(f"**{label}** | {topic} | **{risk}**")
            set_font(run, FONT_VARIANT, 12, bold=True)
            p.paragraph_format.first_line_indent = Cm(0)

            # Contract original text
            if sec.get('contract_text'):
                _add_risk_field(doc, '合同原文', sec['contract_text'])

            # Risk analysis
            if sec.get('analysis'):
                _add_risk_field(doc, '风险分析', sec['analysis'])

            # Modification suggestion
            if sec.get('suggestion'):
                _add_risk_field(doc, '修改建议', sec['suggestion'])

            # Consequence difference
            if sec.get('consequence'):
                _add_risk_field(doc, '后果差异', sec['consequence'])

        elif sec_type == 'closing':
            doc.add_paragraph()  # spacing
            _add_multiline(doc, sec['text'], indent_cm=0.85)

        elif sec_type == 'signature':
            for _ in range(3):
                doc.add_paragraph()

            # Firm name
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(sec.get('firm', '北京市百宸（上海）律师事务所'))
            set_font(run, FONT_VARIANT, 12, bold=True)
            p.paragraph_format.first_line_indent = Cm(0)

            # Date
            if sec.get('date'):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = p.add_run(_to_chinese_date(sec['date']))
                set_font(run, FONT_VARIANT, 12)
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.space_before = Pt(6)

        elif sec_type == 'blank':
            doc.add_paragraph()

        else:
            # Unknown type, treat as body
            p = doc.add_paragraph()
            run = p.add_run(sec.get('text', ''))
            set_font(run, FONT_VARIANT, 12)
            p.paragraph_format.first_line_indent = Cm(0.85)

    if output_path is None:
        output_path = build_filename('memo', meta.get('recipient', 'recipient'), meta.get('subject', 'subject'))
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    doc.save(output_path)
    print(f"审查意见书已生成: {output_path}")


if __name__ == '__main__':
    import json, sys

    if len(sys.argv) < 2:
        print("用法: python3 generate_memo.py <output_path>", file=sys.stderr)
        print("  JSON 从 stdin 读取，格式: {\"meta\": {...}, \"sections\": [...]}", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    generate_memo(data['meta'], data['sections'], output_path)
