#!/usr/bin/env python3
"""
generate_letter.py — 律师函 Word 文档生成工具

用法（由 Agent 调用）
    from generate_letter import generate_letter

    sections = [
        {"type": "title", "text": "律 师 函"},
        {"type": "info", "lines": ["地址...", "电话..."]},
        {"type": "h2", "text": "据委托人陈述及提供的资料表明"},
        {"type": "body", "text": "正文内容..."},
        {"type": "signature", "law_firm": "律所名", "lawyers": 2, "date": "日期", "contact": {"address": "...", "contact_person": "...", "phone": "..."}},
    ]

    generate_letter(sections, output_path)

支持的 section type
- title: 居中大标题 (22pt 黑体加粗)
- info: 律所/函件信息块 (12pt 仿宋，info 无缩进，多个 lines)
- h2: 二级标题 (14pt 黑体加粗，段前段后)
- h3: 三级标题 (12pt 仿宋加粗)
- body: 正文段落 (12pt 仿宋，首行缩进2字符)
- body_no_indent: 正文无缩进
- bold: 加粗段落 (12pt 仿宋加粗)
- list_item: 列表项 (带 • 缩进)
- center: 居中文本 (12pt 仿宋)
- right: 右对齐文本 (12pt 仿宋)
- blank: 空行
- signature: 落款签署区 (含律所、律师签字行、日期、联系方式附件)

⛔ 调用前**必须**已执行交付前质量自检与用户确认；⚠️/⛔ 状态法条**不得**传入正文 sections。
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from docx.shared import Pt
from format_docx import create_document
from format_base import *


def generate_letter(sections, output_path=None):
    """
    Generate a Word document from structured section data.

    Args:
        sections: List of dicts, each with 'type' and content keys
        output_path: Path to save the .docx file (None = auto-generate)

    Returns:
        Document object
    """
    content_blocks = []

    for sec in sections:
        sec_type = sec.get('type', 'body')

        if sec_type == 'title':
            content_blocks.append({
                'type': 'title',
                'text': sec['text']
            })

        elif sec_type == 'info':
            content_blocks.append({
                'type': 'info',
                'attrs': {'lines': sec.get('lines', [])}
            })

        elif sec_type == 'h2':
            content_blocks.append({
                'type': 'h2',
                'text': sec['text']
            })

        elif sec_type == 'h3':
            content_blocks.append({
                'type': 'h3',
                'text': sec['text']
            })

        elif sec_type == 'body':
            content_blocks.append({
                'type': 'body',
                'text': sec['text']
            })

        elif sec_type == 'body_no_indent':
            content_blocks.append({
                'type': 'body_ni',
                'text': sec['text']
            })

        elif sec_type == 'bold':
            content_blocks.append({
                'type': 'bold',
                'text': sec['text']
            })

        elif sec_type == 'list_item':
            content_blocks.append({
                'type': 'list_item',
                'text': sec['text']
            })

        elif sec_type == 'center':
            content_blocks.append({
                'type': 'center',
                'text': sec['text']
            })

        elif sec_type == 'right':
            content_blocks.append({
                'type': 'right',
                'text': sec['text']
            })

        elif sec_type == 'blank':
            content_blocks.append({'type': 'blank'})

        elif sec_type == 'signature':
            _build_signature_blocks(content_blocks, sec)

        else:
            content_blocks.append({
                'type': 'body',
                'text': sec.get('text', '')
            })

    # Build meta for footer and filename
    meta = {}
    for sec in sections:
        if sec.get('type') == 'signature':
            law_firm = sec.get('law_firm', '')
            meta['party'] = law_firm
            meta['doc_type'] = '律师函'
            meta['matter'] = ''
            # 2026-09-13 修复：不再向 meta 写入 date。落款日期已由 _build_signature_blocks 渲染为
            # right 块；若同时传 meta['date']，create_document 会因 content_blocks 中不存在
            # 'signature' 类型块而触发兜底逻辑，重复追加一次落款日期（勿回退）。
            break

    create_document(content_blocks, output_path=output_path, meta=meta)
    return output_path


def _build_signature_blocks(blocks, sec):
    """Build signature content blocks for lawyer letter."""
    # Spacing before signature block
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'blank'})

    # Law firm name
    law_firm = sec.get('law_firm', '')
    blocks.append({
        'type': 'right',
        'text': law_firm,
        'attrs': {'bold': True}
    })

    # (盖章) hint
    blocks.append({
        'type': 'right',
        'text': '（盖章）'
    })

    # Lawyer signature lines
    lawyers = sec.get('lawyers', 2)
    lawyer_name = sec.get('lawyer_name', '')
    for i in range(lawyers):
        if lawyer_name and i == 0:
            blocks.append({
                'type': 'right',
                'text': f'{lawyer_name} 律师'
            })
        else:
            blocks.append({
                'type': 'right',
                'text': '律师_________________'
            })

    # Lawyer phone
    phone = sec.get('phone', '')
    if phone:
        blocks.append({
            'type': 'right',
            'text': f'电话：{phone}'
        })

    # Date
    date_text = sec.get('date', '')
    if date_text:
        blocks.append({
            'type': 'right',
            'text': _to_chinese_date(date_text),
            'attrs': {'space_before': Pt(6)}
        })

    # Contact attachment
    contact = sec.get('contact')
    if contact:
        blocks.append({'type': 'blank'})
        blocks.append({'type': 'blank'})
        blocks.append({
            'type': 'bold',
            'text': '附联系方式'
        })
        if contact.get('address'):
            blocks.append({
                'type': 'body_ni',
                'text': f"地址：{contact['address']}"
            })
        if contact.get('contact_person'):
            blocks.append({
                'type': 'body_ni',
                'text': f"联系人：{contact['contact_person']}"
            })
        if contact.get('phone'):
            blocks.append({
                'type': 'body_ni',
                'text': f"电话：{contact['phone']}"
            })


if __name__ == '__main__':
    import json, sys

    if len(sys.argv) < 2:
        print("用法: python3 generate_letter.py <output_path>", file=sys.stderr)
        print("  sections JSON 从 stdin 读取", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    generate_letter(data, output_path)
