#!/usr/bin/env python3
"""generate_consultation.py — 客户法律咨询答复 Word 文档生成工具。

调用: generate_consultation(meta, sections, output_path)
  - meta: dict with 'date', 'client', 'topic', 'law_firm', 'lawyer'
  - sections: List of dicts, each with 'type' and relevant content keys
  - output_path: Path to save the .docx file

支持的 section type
- title:       居中大标题（黑体加粗）
- conclusion:  结论先行段（加粗强调）
- body:        正文段落（仿宋_GB2312 12pt, 首行缩进2字符）
- list_item:   带编号的列表项（仿宋_GB2312 12pt）
- signature:   落款（右对齐律所/律师/中文大写日期）
- blank:       空行
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document
from format_base import _to_chinese_date


def fix_quotes(text):
    """将「」替换为中文双引号"""
    return text.replace('\u300c', '\u201c').replace('\u300d', '\u201d')


def generate_consultation(meta, sections, output_path=None):
    """
    Generate a Word document for a client consultation reply from structured section data.

    Args:
        meta: dict with 'date', 'client', 'topic', 'law_firm', 'lawyer'
        sections: List of dicts, each with 'type' and relevant content keys
        output_path: Path to save the .docx file

    Returns:
        Document object
    """
    content_blocks = []

    for sec in sections:
        sec_type = sec.get('type', 'body')

        # ── title ──────────────────────────────────────────────
        if sec_type == 'title':
            content_blocks.append({
                'type': 'title',
                'text': fix_quotes(sec.get('text', '法律咨询答复'))
            })

        # ── conclusion ─────────────────────────────────────────
        elif sec_type == 'conclusion':
            content_blocks.append({
                'type': 'bold',
                'text': fix_quotes(sec.get('text', ''))
            })

        # ── body ───────────────────────────────────────────────
        elif sec_type == 'body':
            content_blocks.append({
                'type': 'body',
                'text': fix_quotes(sec.get('text', ''))
            })

        # ── list_item ──────────────────────────────────────────
        elif sec_type == 'list_item':
            content_blocks.append({
                'type': 'body',
                'text': fix_quotes(sec.get('text', ''))
            })

        # ── signature ──────────────────────────────────────────
        elif sec_type == 'signature':
            lines = [fix_quotes(sec.get('text', ''))]
            lawyer = meta.get('lawyer', '')
            if lawyer:
                lines.append(f'律师：{lawyer}')
            date_raw = meta.get('date', '')
            lines.append(_to_chinese_date(date_raw) if date_raw else '')
            content_blocks.append({
                'type': 'signature',
                'attrs': {
                    'lines': [l for l in lines if l],
                    'date': ''
                }
            })

        # ── blank ──────────────────────────────────────────────
        elif sec_type == 'blank':
            content_blocks.append({'type': 'blank'})

        # ── fallback: unknown type → body ──────────────────────
        else:
            content_blocks.append({
                'type': 'body',
                'text': fix_quotes(sec.get('text', ''))
            })

    create_document(content_blocks, output_path=output_path, meta=meta)
    return output_path


if __name__ == '__main__':
    import json

    if len(sys.argv) < 2:
        print('用法: python3 generate_consultation.py <output_path>', file=sys.stderr)
        print('  JSON 从 stdin 读取，格式: {"meta": {...}, "sections": [...]}', file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(f'Error: Invalid JSON input: {e}', file=sys.stderr)
        sys.exit(1)

    meta = data.get('meta', {})
    sections = data.get('sections', [])
    generate_consultation(meta, sections, output_path)
