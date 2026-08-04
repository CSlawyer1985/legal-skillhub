# -*- coding: utf-8 -*-
"""
analyze_rejection.py —— 驳回决定解构工具

从驳回决定(PDF/DOCX)抽取结构化信息，辅助生成"驳回决定深度分析"清单：
  - 收文日/决定日（用于倒排3个月时限）
  - 涉及权利要求
  - 引用法条（法22.3/22.2/26.4/33…）
  - 对比文件及标号
  - 审查员关键认定句（不具备创造性/常规/公知/启示/区别/技术问题）

依赖：pip install python-docx PyMuPDF

用法：python analyze_rejection.py --decision 驳回决定.pdf --out 驳回决定分析.md
"""
import argparse
import os
import re
import zipfile

try:
    import fitz
except ImportError:
    fitz = None


def read_text(path):
    if path.lower().endswith('.pdf'):
        if fitz is None:
            raise RuntimeError('需安装 PyMuPDF: pip install PyMuPDF')
        doc = fitz.open(path)
        txt = '\n'.join(p.get_text() for p in doc)
        doc.close()
        return txt
    elif path.lower().endswith('.docx'):
        from docx import Document
        d = Document(path)
        return '\n'.join(p.text for p in d.paragraphs)
    else:
        with open(path, encoding='utf-8', errors='ignore') as f:
            return f.read()


def analyze(text):
    res = {}
    # 决定日 / 收文日
    m = re.search(r'(?:决定日|发文日)[：:]\s*(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})', text)
    res['决定日'] = '-'.join(m.groups()) if m else '未识别'
    m2 = re.search(r'(?:收到|收文)[日日期]*[：:]\s*(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})', text)
    res['收文日(若载明)'] = '-'.join(m2.groups()) if m2 else '未载明（以实际收到日为准）'

    # 权利要求
    claims = set(re.findall(r'权利要求\s*([0-9]+[-‑–至~和、,，\s]*)', text))
    res['涉及权利要求(初筛)'] = sorted(claims, key=lambda x: int(re.sub(r'\D', '', x) or 0))[:20]

    # 法条
    laws = set(re.findall(r'专利法(?:实施细则)?\s*第?\s*([0-9]+)\s*[条\.、]?\s*(?:第?\s*([0-9]+)\s*[款\.、项]?)?', text))
    res['引用法条(初筛)'] = [f'法{l[0]}' + (f'.{l[1]}' if l[1] else '') for l in laws if l[0]]

    # 对比文件
    refs = set(re.findall(r'对比文件\s*([0-9]+)', text))
    res['对比文件'] = sorted(refs, key=int)

    # 关键认定句
    keys = ['不具备创造性', '不具备新颖性', '不清楚', '不支持', '缺少必要技术特征',
            '常规技术', '惯用', '公知常识', '技术启示', '区别技术特征', '实际解决的技术问题',
            '最接近', '修改超出', '放弃', '陈述意见', '显而易见']
    sentences = []
    for ln in re.split(r'[\n。；;]', text):
        if any(k in ln for k in keys) and 8 < len(ln) < 200:
            sentences.append(ln.strip())
    res['关键认定句'] = sentences[:40]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--decision', required=True, help='驳回决定 PDF/DOCX 路径')
    ap.add_argument('--out', default='驳回决定分析.md', help='输出 markdown 路径')
    args = ap.parse_args()

    text = read_text(args.decision)
    res = analyze(text)
    lines = ['# 驳回决定深度分析（自动解构，请人工复核）', '']
    lines.append(f'- 决定日：{res["决定日"]}')
    lines.append(f'- 收文日：{res["收文日(若载明)"]}（请按实际收到日倒排 **3个月** 复审时限）')
    lines.append(f'- 涉及权利要求（初筛）：{", ".join(res["涉及权利要求(初筛)"]) or "未识别"}')
    lines.append(f'- 引用法条（初筛）：{", ".join(res["引用法条(初筛)"]) or "未识别"}')
    lines.append(f'- 对比文件：{", ".join("对比文件"+r for r in res["对比文件"]) or "未识别"}')
    lines.append('')
    lines.append('## 审查员关键认定句（供 M3–M8  rebuttal 索引）')
    for s in res['关键认定句']:
        lines.append(f'- {s}')
    lines.append('')
    lines.append('> 提示：本解构为初筛，须人工核对原文并补全"技术起点/区别特征归纳/可能偏差点"。')
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('分析完成 ->', args.out)
    print('决定日:', res['决定日'], '| 对比文件:', res['对比文件'], '| 关键句:', len(res['关键认定句']))


if __name__ == '__main__':
    main()
