#!/usr/bin/env python3
"""generate_compliance.py — 合规审查文件 Word 文档生成工具

三段式结构（与同族 generate_datacompliance.py / generate_employment.py 一致）：
  1. build content_blocks（逐 section 组装，heading/body/table 三类）
  2. create_document(content_blocks, output_path=..., title=..., meta=...)
  3. __main__ 接收 JSON argv：{"meta": {...}, "sections": [...], "output": "..."}

⛔ 调用纪律（P0-9 新建·2026-08-30）：
  - attrs 必须显式以 dict 传入（block['attrs'] = dict(...)）；
    ⛔ 直接透传非 dict 的 attrs（字符串/元组/None 等）会导致渲染失败。
  - table 类 section 必须同时给出 rows 与 cols，否则该表不渲染。
  - output_path 缺省为 /sandbox/workspace/outputs/compliance.docx。
"""

import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document


def generate_compliance(meta, sections, output_path=None):
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
            block['attrs'] = dict(sec['attrs'])

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
    generate_compliance(data.get('meta', {}), data.get('sections', []),
                        data.get('output', '/sandbox/workspace/outputs/compliance.docx'))
