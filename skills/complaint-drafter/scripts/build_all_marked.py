#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量把官方 67 类要素式模板（references/templates/*.txt）渲染为带占位符的
标记版 .docx，并导出字段映射 JSON，存入 references/marked/。

用法：
  python build_all_marked.py
"""
import os, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # skills/complaint-drafter
TEMPLATES = os.path.join(ROOT, 'references', 'templates')
OUT = os.path.join(ROOT, 'references', 'marked')

sys.path.insert(0, HERE)
import generate_complaint_docx as g

os.makedirs(OUT, exist_ok=True)

txts = sorted(glob.glob(os.path.join(TEMPLATES, '*.txt')))
print(f'发现模板 {len(txts)} 个')
ok, fail = 0, 0
for txt in txts:
    name = os.path.splitext(os.path.basename(txt))[0]
    docx = os.path.join(OUT, name + '.docx')
    js = os.path.join(OUT, name + '.fields.json')
    try:
        g.render_marked(txt, docx, js)
        ok += 1
    except Exception as e:
        fail += 1
        print(f'  [FAIL] {name}: {e}')
print(f'完成：成功 {ok}，失败 {fail}')
print(f'输出目录：{OUT}')
