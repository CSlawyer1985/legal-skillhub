#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《律师使用AI指南 2024》按需检索脚本（仅依赖 Python 标准库）。

用法：
  python search_guide.py "关键词"           检索原文片段（支持多个词，空格分隔）
  python search_guide.py --list             列出全书章节目录
  python search_guide.py --chapter "第二章"  提取整章原文（取前 8000 字）

说明：全文已提取至 ../references/guide_full.md（约 19 万字）。
检索按需返回相关片段与页码，避免一次性将全书读入上下文。
"""
import sys
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.join(HERE, "..", "references", "guide_full.md")

# 全书章节索引（标题, 起始页）—— 用于 --list 与 --chapter
CHAPTERS = [
    ("第一章 AI技术在律师工作中的实际应用", 20),
    ("第二章 法律研究与文书准备", 28),
    ("第三章 日常办公与效率提升", 102),
    ("第四章 客户服务与咨询沟通", 208),
    ("第五章 专业发展与能力提升", 270),
    ("第六章 规范和自我约束（含《律师行业人工智能技术应用管理规范》）", 324),
]


def load_pages():
    with open(GUIDE, encoding="utf-8") as f:
        text = f.read()
    chunks = re.split(r"<!-- page (\d+) -->", text)
    pages = {}
    for i in range(1, len(chunks), 2):
        pnum = int(chunks[i])
        body = chunks[i + 1] if i + 1 < len(chunks) else ""
        pages[pnum] = body
    return pages


def search(query, top=15):
    pages = load_pages()
    kws = [k.strip() for k in re.split(r"[\s+,，、]", query) if k.strip()]
    if not kws:
        print("请提供检索关键词，例如：python search_guide.py \"合同审查 提示词\"")
        return
    results = []
    for p, body in pages.items():
        paras = re.split(r"\n\s*\n", body)
        for para in paras:
            low = para.lower()
            hits = sum(1 for k in kws if k.lower() in low)
            if hits > 0:
                results.append((hits, p, para.strip()))
    results.sort(key=lambda x: (-x[0], x[1]))
    results = results[:top]
    if not results:
        print(f"未找到与「{query}」相关的内容。")
        return
    print(f"=== 检索「{query}」 命中 {len(results)} 条（取相关度最高的 {len(results)} 条）===\n")
    for hits, p, para in results:
        snippet = para[:400] + ("…" if len(para) > 400 else "")
        print(f"[p{p} | 命中{hits}] {snippet}\n")


def list_chapters():
    print("=== 《律师使用AI指南 2024》目录 ===\n")
    for title, p in CHAPTERS:
        print(f"  p{p}: {title}")
    print("\n（正文约 p20–p340；附录《律师行业人工智能技术应用管理规范》约 p306 起）")


def extract_chapter(num):
    pages = load_pages()
    starts = [(p, title) for title, p in CHAPTERS if title.startswith(f"第{num}")]
    if not starts:
        print(f"未找到第{num}章，可用 --list 查看目录。")
        return
    start_page = starts[0][0]
    all_starts = sorted([p for _, p in CHAPTERS])
    idx = all_starts.index(start_page)
    end_page = all_starts[idx + 1] if idx + 1 < len(all_starts) else max(pages.keys()) + 1
    out = []
    for p in range(start_page, end_page):
        if p in pages:
            out.append(f"\n<!-- page {p} -->\n" + pages[p])
    text = "".join(out)
    print(f"=== 第{num}章（p{start_page}–p{end_page - 1}）===\n")
    if len(text) > 8000:
        print(text[:8000])
        print("\n…（内容较长，已截断显示前 8000 字；可用关键词检索定位更多片段）")
    else:
        print(text)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--list":
        list_chapters()
        return
    if args[0] == "--chapter":
        num = args[1] if len(args) > 1 else ""
        extract_chapter(num)
        return
    query = " ".join(args)
    search(query)


if __name__ == "__main__":
    main()
