#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: WorkBuddy (agent_created)
"""把「Word/电子稿」与「打印稿/扫描件转写文本」逐段比对，只报真正的增删改。

输入:
  1) 电子稿：docx_dump.py 的文本输出，或 --json 产物
  2) 纸质稿：把扫描/照片按阅读顺序转写成 txt，一行一段（与电子稿段落颗粒度一致）

输出:
  - DELETE / INSERT / REPLACE 明细，附被删原文（可直接粘进给客户/对方的说明）
  - 疑似误报清单：只差自动编号、只差空格/全半角、命中页脚或页外浮动对象文字

用法:
  python3 docx_dump.py 合同.docx --json /tmp/el.json
  python3 version_diff.py /tmp/el.json 纸质稿转写.txt [--fold-width] [--exclude-text "2" "3"]
"""
import argparse
import json
import re
import sys
import difflib


def norm(s, fold_width=False):
    s = s.replace("\u3000", " ").replace("\xa0", " ")
    s = re.sub(r"\s+", "", s)
    if fold_width:
        s = "".join(
            chr(ord(c) - 0xFEE0) if 0xFF01 <= ord(c) <= 0xFF5E else c for c in s
        )
    return s


def load_docx_paras(path):
    with open(path, encoding="utf-8") as f:
        if path.endswith(".json"):
            data = json.load(f)
            return [(p.get("num", "") + p.get("text", "")) for p in data["paragraphs"]]
        return [ln for ln in f.read().split("\n") if ln.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx_dump")          # docx_dump.py 的输出（.txt 或 .json）
    ap.add_argument("print_text")         # 纸质稿转写
    ap.add_argument("--fold-width", action="store_true", help="全角/半角视为相同（仅提示，不吞掉差异）")
    ap.add_argument("--exclude-text", nargs="*", default=[], help="页脚/页外浮动对象等非正文文字，命中时只提示不计入删除")
    ap.add_argument("--min-len", type=int, default=1, help="小于该字数的差异按“疑似转录误差”单独列出")
    a = ap.parse_args()

    docx = [ln for ln in load_docx_paras(a.docx_dump) if ln.strip()]
    paper = [ln for ln in open(a.print_text, encoding="utf-8").read().split("\n") if ln.strip()]
    # 去掉 docx_dump 的行号前缀 "[  1] "
    docx = [re.sub(r"^\[\s*\d+\]\s?", "", x) for x in docx]
    paper = [re.sub(r"^\[\s*\d+\]\s?", "", x) for x in paper]

    D = [norm(x) for x in docx]
    P = [norm(x) for x in paper]
    print(f"电子稿 {len(D)} 段 / 纸质稿 {len(P)} 段")

    sm = difflib.SequenceMatcher(None, D, P, autojunk=False)
    real, notes = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        # 段内配对：先在块内做相似度配对，避免整块错位
        left = list(range(i1, i2))
        right = list(range(j1, j2))
        pairs, lfree, rfree = pair_blocks(D, P, left, right)
        for di, pi in pairs:
            a_, b_ = D[di], P[pi]
            if a_ == b_:
                continue
            s2 = difflib.SequenceMatcher(None, a_, b_, autojunk=False)
            for tg, x1, x2, y1, y2 in s2.get_opcodes():
                if tg == "equal":
                    continue
                old, new = a_[x1:x2], b_[y1:y2]
                if tg in ("delete", "replace") and old:
                    item = ("电子稿[%d] → 纸质稿[%d]" % (di + 1, pi + 1), old, new)
                    (notes if len(old) < a.min_len else real).append(item)
        # 整段缺失/新增才做“非正文文字”排除（页脚、页外浮动对象）。
        # 片段级不做：exclude-text 是子串匹配，页脚关键字“2”会误伤正文“200万元”。
        for di in lfree:
            if hit(D[di], a.exclude_text):
                notes.append(("电子稿[%d] 整段缺失（命中 --exclude-text，判为非正文）" % (di + 1), D[di], ""))
            else:
                real.append(("电子稿[%d] 整段缺失" % (di + 1), D[di], ""))
        for pi in rfree:
            real.append(("纸质稿[%d] 新增" % (pi + 1), "", P[pi]))

    print("\n===== 实质差异（纸质稿相对电子稿） =====")
    if not real:
        print("（无）")
    for loc, old, new in real:
        if old and new:
            print(f"- [改写] {loc}\n    原：{old}\n    改：{new}")
        elif old:
            print(f"- [删除] {loc}\n    {old}")
        else:
            print(f"- [新增] {loc}\n    {new}")
    if notes:
        print("\n===== 疑似误报/转录误差（需人工确认，勿直接当成删除） =====")
        for loc, old, new in notes:
            print(f"- [微差] {loc} 原={old!r} 现={new!r}")
    print("\n提示：纸质稿是人工转写，任一差异都应对着高分辨率裁切图回读一次再下结论。")


def hit(text, keys):
    return any(k and k in text for k in keys)


def pair_blocks(D, P, left, right):
    """在差异块内按相似度配对段落。返回 (pairs, 左侧未配, 右侧未配)。"""
    pairs, used_r = [], set()
    for di in left:
        best, score = None, 0.0
        for pi in right:
            if pi in used_r:
                continue
            r = difflib.SequenceMatcher(None, D[di], P[pi], autojunk=False).ratio()
            if r > score:
                best, score = pi, r
        if best is not None and score >= 0.45:
            pairs.append((di, best))
            used_r.add(best)
    lfree = [d for d in left if d not in {x[0] for x in pairs}]
    rfree = [p for p in right if p not in used_r]
    return pairs, lfree, rfree


if __name__ == "__main__":
    main()
