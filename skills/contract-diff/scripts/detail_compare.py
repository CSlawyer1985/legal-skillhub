#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import difflib
import re
from docx import Document
import fitz

# Extract template
doc = Document('input/合作协议模板.docx')
template = '\n'.join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

# Extract scanned
doc2 = fitz.open('input/合作协议_盖章版.pdf')
scanned = ''
for page in doc2:
    scanned += page.get_text()

template_sents = [s.strip() for s in re.split(r'[。\n]', template) if s.strip()]
scanned_sents = [s.strip() for s in re.split(r'[。\n]', scanned) if s.strip()]

# Classify differences
only_template = []
only_scanned = []
similar = []

for t in template_sents:
    if len(t) < 5:
        continue
    best_match = None
    best_ratio = 0
    for s in scanned_sents:
        ratio = difflib.SequenceMatcher(None, t, s).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = s
    if best_ratio > 0.85:
        pass  # Similar enough, ignore
    elif best_ratio > 0.5:
        similar.append({'template': t, 'scanned': best_match, 'ratio': round(best_ratio, 2)})
    else:
        only_template.append(t)

for s in scanned_sents:
    if len(s) < 5:
        continue
    found = False
    for t in template_sents:
        if difflib.SequenceMatcher(None, t, s).ratio() > 0.85:
            found = True
            break
    if not found:
        only_scanned.append(s)

print('='*60)
print('[DIFF STATS]')
print(f'Only in template: {len(only_template)}')
print(f'Only in scanned: {len(only_scanned)}')
print(f'Similar: {len(similar)}')
print()

print('='*60)
print('[ONLY IN TEMPLATE - First 25]')
for i, t in enumerate(only_template[:25]):
    print(f'{i+1}. {t}')
print()

print('='*60)
print('[ONLY IN SCANNED - First 25]')
for i, s in enumerate(only_scanned[:25]):
    print(f'{i+1}. {s}')
print()

print('='*60)
print('[SIMILAR WITH MODIFICATIONS]')
for i, item in enumerate(similar[:15]):
    print(f'{i+1}. Ratio: {item["ratio"]}')
    print(f'   Template: {item["template"][:100]}')
    print(f'   Scanned: {item["scanned"][:100]}')
    print()