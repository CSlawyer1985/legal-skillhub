#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_to_text.py - 将 .docx 文件转换为 Markdown 纯文本

仅依赖 Python 标准库（zipfile + xml.etree），无需 pip 安装任何包。
按文档顺序提取段落与表格：段落输出为文本行，表格输出为 Markdown 表格，
标题样式（Heading 1-4 / 标题 1-4）自动转换为 Markdown 标题层级。

用法：
    python docx_to_text.py <input.docx> [-o <output.md>]

省略 -o 时输出到 stdout（Windows 下建议始终使用 -o 写文件，避免控制台编码问题）。
"""
import argparse
import sys
import zipfile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def para_text(p):
    """提取段落文本，保留 tab 与换行。"""
    parts = []
    for node in p.iter():
        if node.tag == W + 't':
            parts.append(node.text or '')
        elif node.tag == W + 'tab':
            parts.append(' ')
        elif node.tag == W + 'br':
            parts.append('\n')
    return ''.join(parts).strip()


def para_heading_level(p):
    """识别标题样式，返回 Markdown 标题层级（1-4），非标题返回 0。"""
    ppr = p.find(W + 'pPr')
    if ppr is None:
        return 0
    pstyle = ppr.find(W + 'pStyle')
    if pstyle is None:
        return 0
    val = (pstyle.get(W + 'val') or '').lower()
    for i in range(1, 5):
        if val in ('heading%d' % i, 'heading %d' % i, '%d' % i) or val.endswith('heading%d' % i):
            return i
    # 中文样式名常见写法：1 / 2 / 3 级标题对应的 val 常为 "1"、"2"... 或 "a3" 等，已尽力覆盖
    return 0


def table_to_md(tbl):
    """将 w:tbl 转为 Markdown 表格，第一行作为表头。"""
    rows = []
    for tr in tbl.findall(W + 'tr'):
        cells = []
        for tc in tr.findall(W + 'tc'):
            cell_paras = [para_text(p) for p in tc.findall(W + 'p')]
            cell = ' '.join(t for t in cell_paras if t)
            cells.append(cell.replace('|', '\\|').replace('\n', ' '))
        if cells:
            rows.append(cells)
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [''] * (width - len(r)) for r in rows]
    lines = ['| ' + ' | '.join(rows[0]) + ' |',
             '|' + '---|' * width]
    for r in rows[1:]:
        lines.append('| ' + ' | '.join(r) + ' |')
    return lines


def convert(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml_bytes = z.read('word/document.xml')
    root = ET.fromstring(xml_bytes)
    body = root.find(W + 'body')
    if body is None:
        raise ValueError('未找到 word/document.xml 的 body 节点，文件可能损坏或不是标准 docx。')

    out = []
    for child in body:
        if child.tag == W + 'p':
            text = para_text(child)
            if not text:
                continue
            level = para_heading_level(child)
            out.append(('#' * level + ' ' + text) if level else text)
        elif child.tag == W + 'tbl':
            out.extend(table_to_md(child))
            out.append('')
    return '\n\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description='将 .docx 转换为 Markdown 纯文本')
    ap.add_argument('input', help='输入 .docx 文件路径')
    ap.add_argument('-o', '--output', help='输出 .md 文件路径（省略则打印到 stdout）')
    args = ap.parse_args()

    text = convert(args.input)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
        print('已写出: %s（%d 字符）' % (args.output, len(text)))
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
