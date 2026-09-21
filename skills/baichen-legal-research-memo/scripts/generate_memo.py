#!/usr/bin/env python3
"""法律备忘录 Word 文档生成脚本（python-docx）。

接收 meta（元信息）、part_one（事实部分）、part_two（分析部分）和 closing_summary（总结），
生成符合百宸律所备忘录格式的 .docx。

用法: cat input.json | python3 generate_memo.py
输出至 /sandbox/workspace/outputs/legal_memo_{timestamp}.docx。
"""

import json
import sys
import os
from datetime import datetime
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from docx.shared import Pt
from format_docx import create_document
from format_base import *


def _num_to_chinese(n):
    """数字转中文序号。"""
    mapping = {1: '\u4e00', 2: '\u4e8c', 3: '\u4e09', 4: '\u56db', 5: '\u4e94',
               6: '\u516d', 7: '\u4e03', 8: '\u516b', 9: '\u4e5d', 10: '\u5341'}
    return mapping.get(n, str(n))


def generate_memo(meta, part_one, part_two, closing_summary, output_dir="/sandbox/workspace/outputs"):
    """生成法律备忘录 Word 文档。

    Args:
        meta: dict，包含
            - date: str                    日期（YYYY年MM月DD日）
            - recipient: str               收件人/客户名称
            - recipient_short: str         客户简称（用于"下称"定义）
            - law_firm: str                律所名称
            - law_firm_short: str          律所简称（用于"下称"定义）
            - matter: str                  事由
            - definitions: list[dict]      术语定义列表，每项 {full, short}
            - thanks_text: str             感谢段落
            - opening_text: str            引言段（含"根据贵司……出具本法律备忘录"）
            - caveat_text: str             保留声明段
            - contact_line: str            联系方式行
            - confidentiality: str         保密标注

        part_one: dict，包含
            - title: str                   第一部分标题（"第一部分  本案主要事实"）
            - body: str                    事实叙述（含"鉴于"体）

        part_two: dict，包含
            - title: str                   第二部分标题
            - intro: str                   序言段（"我们建议贵司……关注以下问题"）
            - brief_answer: str            简短回答（"我们的初步判断是：……"3-5句）
            - sections: list[dict]         子问题列表，每项
                - heading: str             子标题（"一、……"）
                - body: str                完整叙事段落（不拆分标签，自然段落）

        closing_summary: dict，包含
            - summary_text: str            "综上所述"总结段
            - closing_caveat: str          结尾保留声明
            - closing_remark: str          结尾敬语

        output_dir: str                    输出目录

    Returns:
        str: 生成的文件路径
    """
    content_blocks = []

    # ====== 保密文件 ======
    confidentiality = meta.get('confidentiality', '')
    if confidentiality:
        content_blocks.append({
            'type': 'center',
            'text': confidentiality,
            'attrs': {'font_name': TITLE_FONT, 'size': Pt(14), 'bold': True}
        })
        content_blocks.append({'type': 'blank'})

    # ====== 抬头信息（替代原表格）======
    date_str = _to_chinese_date(meta.get('date', ''))
    content_blocks.append({'type': 'bold', 'text': f'日  期：{date_str}'})
    content_blocks.append({'type': 'bold', 'text': f'收件人：{meta.get("recipient", "")}'})
    content_blocks.append({'type': 'bold', 'text': f'发件人：{meta.get("law_firm", "")}'})
    content_blocks.append({'type': 'bold', 'text': f'事  由：{meta.get("matter", "")}'})
    content_blocks.append({'type': 'blank'})

    # ====== 敬启者 + 感谢 + 术语定义 ======
    content_blocks.append({'type': 'bold', 'text': '\u656c\u542f\u8005\uff1a'})
    content_blocks.append({'type': 'blank'})

    thanks_text = meta.get('thanks_text', '')
    if thanks_text:
        content_blocks.append({'type': 'body', 'text': thanks_text})

    # 术语定义段
    definitions = meta.get('definitions', [])
    if definitions:
        def_parts = []
        for d in definitions:
            def_parts.append(f"{d['full']}\uff08\u4e0b\u79f0\u201c{d['short']}\u201d\uff09")
        def_text = '\u3000\u3000' + '\uff1b'.join(def_parts) + '\u3002'
        content_blocks.append({'type': 'body', 'text': def_text})

    # ====== 引言段 ======
    opening_text = meta.get('opening_text', '')
    if opening_text:
        content_blocks.append({'type': 'body', 'text': opening_text})

    # ====== 保留声明 ======
    caveat_text = meta.get('caveat_text', '')
    if caveat_text:
        content_blocks.append({'type': 'body', 'text': caveat_text})

    # ====== 联系方式 ======
    contact_line = meta.get('contact_line', '')
    if contact_line:
        content_blocks.append({'type': 'body', 'text': contact_line})

    # ====== 第一部分：本案主要事实 ======
    content_blocks.append({
        'type': 'h2',
        'text': part_one.get('title', '\u7b2c\u4e00\u90e8\u5206  \u672c\u6848\u4e3b\u8981\u4e8b\u5b9e')
    })
    content_blocks.append({'type': 'body', 'text': part_one.get('body', '')})

    # ====== 第二部分：法律分析 ======
    content_blocks.append({
        'type': 'h2',
        'text': part_two.get('title', '\u7b2c\u4e8c\u90e8\u5206  \u6cd5\u5f8b\u5206\u6790')
    })

    intro = part_two.get('intro', '')
    if intro:
        content_blocks.append({'type': 'body', 'text': intro})

    brief_answer = part_two.get('brief_answer', '')
    if brief_answer:
        content_blocks.append({'type': 'bold', 'text': brief_answer})
        content_blocks.append({'type': 'blank'})

    sections = part_two.get('sections', [])
    for sec in sections:
        heading = sec.get('heading', '')
        if heading:
            content_blocks.append({'type': 'bold', 'text': heading})
        body = sec.get('body', '')
        if body:
            # 将 body 按双换行拆分为多个自然段落
            paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
            if not paragraphs:
                paragraphs = [body]
            for para_text in paragraphs:
                content_blocks.append({'type': 'body', 'text': para_text})

    # ====== 综上所述 ======
    summary_text = closing_summary.get('summary_text', '')
    if summary_text:
        content_blocks.append({'type': 'body', 'text': summary_text})

    # ====== 结尾保留声明 ======
    closing_caveat = closing_summary.get('closing_caveat', '')
    if closing_caveat:
        content_blocks.append({'type': 'body', 'text': closing_caveat})

    # ====== 结尾敬语 ======
    closing_remark = closing_summary.get('closing_remark', '')
    if closing_remark:
        content_blocks.append({'type': 'body', 'text': closing_remark})

    # ====== 落款 ======
    content_blocks.append({'type': 'blank'})
    content_blocks.append({
        'type': 'right',
        'text': meta.get('law_firm', ''),
        'attrs': {'font_name': TITLE_FONT, 'bold': True}
    })
    content_blocks.append({
        'type': 'right',
        'text': _to_chinese_date(meta.get('date', ''))
    })

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    filename = build_filename('备忘录', meta.get('recipient_short', ''), meta.get('matter', ''))
    filepath = os.path.join(output_dir, filename)
    create_document(content_blocks, output_path=filepath)
    return filepath


if __name__ == '__main__':
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    meta = input_data.get('meta', {})
    part_one = input_data.get('part_one', {})
    part_two = input_data.get('part_two', {})
    closing_summary = input_data.get('closing_summary', {})
    output_dir = input_data.get('output_dir', '/sandbox/workspace/outputs')
    filepath = generate_memo(meta, part_one, part_two, closing_summary, output_dir)
    print(json.dumps({'status': 'ok', 'filepath': filepath}))
