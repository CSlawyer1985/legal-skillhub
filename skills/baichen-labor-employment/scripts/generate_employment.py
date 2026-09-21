#!/usr/bin/env python3
"""generate_employment.py — 劳动人事文件 Word 文档生成工具"""

import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document


def generate_employment(meta, sections, output_path=None):
    content_blocks = []
    for sec in sections:
        sec_type = sec.get('type', 'body')
        text = sec.get('text', '')
        block = {'type': sec_type, 'text': text}

        if sec_type == 'heading':
            block['type'] = 'heading'

        if sec_type == 'table':
            rows = sec.get('rows', [])
            cols = sec.get('cols', [])
            if rows or cols:
                block['attrs'] = {'rows': rows, 'cols': cols}
        elif sec.get('attrs'):
            block['attrs'] = sec['attrs']

        content_blocks.append(block)

    create_document(
        content_blocks,
        output_path=output_path,
        title=meta.get('title'),
        meta=meta
    )
    return output_path


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error: Invalid JSON argument: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        data = {'meta': {}, 'sections': []}
    generate_employment(data.get('meta', {}), data.get('sections', []),
                        data.get('output', '/sandbox/workspace/outputs/employment.docx'))
