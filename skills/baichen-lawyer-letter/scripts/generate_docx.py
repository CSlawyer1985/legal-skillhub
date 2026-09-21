#!/usr/bin/env python3
"""将律师函 Markdown 内容直接生成格式化的 Word 文档（.docx）。

⛔ 本脚本仅用于律师函草稿定稿后的格式转换：生成前**必须**完成 `../baichen-ndr-standard/references/ndr-standards.md` §15.4 普检与用户确认，**不得**将未经质量自检的草稿直接生成交付件。"""

import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document
from format_base import *


def parse_and_generate(markdown_text, output_path=None):
    """解析 Markdown 内容并生成 Word 文档。"""
    content_blocks = []

    lines = markdown_text.split('\n')
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]

        # 跳过 YAML frontmatter
        if line.strip() == '---' and i == 0:
            i += 1
            while i < len(lines) and lines[i].strip() != '---':
                i += 1
            i += 1
            continue

        # 代码块
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # 水平线
        if stripped == '---' or stripped == '***':
            content_blocks.append({'type': 'blank'})
            i += 1
            continue

        # 标题
        if stripped.startswith('# '):
            text = stripped[2:]
            content_blocks.append({'type': 'title', 'text': text})
            i += 1
            continue

        if stripped.startswith('## '):
            text = stripped[3:]
            content_blocks.append({'type': 'h2', 'text': text})
            i += 1
            continue

        if stripped.startswith('### '):
            text = stripped[4:]
            content_blocks.append({'type': 'h3', 'text': text})
            i += 1
            continue

        # 带编号的项目列表
        if re.match(r'^\d+\.\s', stripped):
            content_blocks.append({'type': 'list_item', 'text': stripped})
            i += 1
            continue

        # 项目符号列表
        if stripped.startswith('- ') or stripped.startswith('* '):
            text = stripped[2:]
            content_blocks.append({'type': 'list_item', 'text': text})
            i += 1
            continue

        # 引用块
        if stripped.startswith('> '):
            text = stripped[2:]
            content_blocks.append({'type': 'body', 'text': text})
            i += 1
            continue

        # 表格行
        if stripped.startswith('|') and stripped.endswith('|'):
            # 跳过表头分隔行
            if re.match(r'^\|[\s\-:]+\|', stripped):
                i += 1
                continue
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            text = '\u3000\u3000'.join(cells)
            content_blocks.append({'type': 'body', 'text': text})
            i += 1
            continue

        # 加粗的独立行（**xxx**）
        if stripped.startswith('**') and stripped.endswith('**'):
            text = stripped[2:-2]
            content_blocks.append({'type': 'bold', 'text': text})
            i += 1
            continue

        # 普通段落
        content_blocks.append({'type': 'body', 'text': stripped})
        i += 1

    create_document(content_blocks, output_path=output_path)
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 generate_docx.py <output_path>", file=sys.stderr)
        print("  Markdown 内容从 stdin 读取", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    markdown_content = sys.stdin.read()
    parse_and_generate(markdown_content, output_path)
