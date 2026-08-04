#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多源核对（精准性铁律加强层 · 对应 SKILL.md「多源核对」原则）。

同一规范若存在多份官方副本（不同来源 / 版本 / PDF），逐字符比对同一条款，
**确定性地**报告差异，标记为 ⚠️，**绝不静默采纳任一方、绝不臆测填补**。
人工核对确认正字后，用 `term_memory.py add` 把结论沉淀进 skill 记忆。

用法：
  reconcile.py --a <来源A：文本/PDF> --b <来源B：文本/PDF> [--query 条款号]
    --a / --b  可为 .txt / .md（纯文本）或 .pdf（自动抽取文字层）
    --query    条款号（如 3.4.3），仅抽取该条款对比；省略则整篇比对
"""

import re
import sys
import os
import argparse
import difflib

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

CLAUSE_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)\b')


def read_source(path):
    if path.lower().endswith(".pdf"):
        if fitz is None:
            sys.exit("比对 PDF 需要 PyMuPDF：pip install pymupdf")
        doc = fitz.open(path)
        txt = "\n".join(p.get_text() for p in doc)
        doc.close()
        return txt
    with open(path, encoding="utf-8") as f:
        return f.read()


def clause_window(text, q):
    lines = text.splitlines()
    qnum = q.replace(" ", "")
    for i, ln in enumerate(lines):
        m = CLAUSE_RE.match(ln)
        if m and (m.group(1) == qnum or m.group(1).startswith(qnum)):
            window = []
            for j in range(i, min(i + 15, len(lines))):
                window.append(lines[j])
                if j > i and CLAUSE_RE.match(lines[j]):
                    break
            return "\n".join(window)
    return text  # 未定位到条款号，退回整篇


def normalize(text):
    return re.sub(r"\s+", "", text)


def main():
    ap = argparse.ArgumentParser(description="多源核对同一条款差异（确定性 diff）")
    ap.add_argument("--a", required=True, help="来源 A：文本文件或 PDF")
    ap.add_argument("--b", required=True, help="来源 B：文本文件或 PDF")
    ap.add_argument("--query", default="", help="条款号，仅抽取该条款对比")
    args = ap.parse_args()

    ta = read_source(args.a)
    tb = read_source(args.b)
    if args.query:
        ta = clause_window(ta, args.query)
        tb = clause_window(tb, args.query)

    na, nb = normalize(ta), normalize(tb)
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    print(f"[多源核对] A={os.path.basename(args.a)}  vs  B={os.path.basename(args.b)}")
    if args.query:
        print(f"  比对条款：{args.query}")
    print(f"  字符相似度（忽略空白）：{ratio:.3f}")

    if ratio >= 0.999:
        print("  ✅ 两份来源逐字符一致（空白忽略），可放心引用。")
        return

    sm = difflib.SequenceMatcher(None, na, nb)
    print("  ⚠️ 检测到差异，列举分歧点（勿静默采纳任一方，请人工核对）：")
    n = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        n += 1
        a_seg = na[i1:i2]
        b_seg = nb[j1:j2]
        # 上下文：取差异点前后若干字
        ctx_l, ctx_r = 8, 8
        a_ctx = na[max(0, i1 - ctx_l):i1] + "【" + a_seg + "】" + na[i2:i2 + ctx_r]
        b_ctx = nb[max(0, j1 - ctx_r):j1] + "【" + b_seg + "】" + nb[j2:j2 + ctx_r]
        print(f"  —— 分歧 #{n}")
        print(f"     A: …{a_ctx}…")
        print(f"     B: …{b_ctx}…")
    print("  提示：确认正字后，用 `python scripts/term_memory.py add --wrong <A段> --right <B段>` 沉淀。")


def _safe_main():
    """顶层异常兜底——防止文件不存在/读取失败时暴露 traceback。"""
    try:
        main()
    except FileNotFoundError as e:
        print(f"\n❌ 找不到文件：{e.filename}")
        print("   请检查 --a / --b 的路径是否正确（支持 .txt / .md / .pdf）。")
    except KeyboardInterrupt:
        print("\n\n操作已取消（按 Ctrl+C 可随时退出）。")
    except Exception as e:
        print(f"\n❌ 比对出错：{type(e).__name__} —— {e}")
        print("   请把上面的信息反馈给我们，或检查源文件是否正常。")


if __name__ == "__main__":
    _safe_main()
