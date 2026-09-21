#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""横排一行的「行内子串」打码边界定位（纯像素列投影，不依赖 OCR 的字符框）。

为什么不能直接用 OCR 的逐字符 bbox：Vision 给的是**推进宽度、首尾相接**
（实测「燕」止于 278.8、「B」起于 282.1，比真实墨迹宽 10~20px；把矩形按
bbox+padding 打码，必然啃到相邻字）。所以行内子串的边界一律以本脚本实测为准。

四步：
  1) 切墨迹段：min_px=1、gap=0，尽量切碎（横笔画字会被拆成多段）
  2) 按「同字」合并：相邻段间距 <= gap 且 合并后跨度 <= 行高*1.05（CJK 字宽≈行高）
     —— 这是「第几个字」的唯一正确依据，不能直接数段
     gap 取值实测：横排 CJK+拉丁混排 **3**（自己拿本行三档阈值互校确认）；
     取 6 会把窄拉丁字母（B+I）并成一个"字"，取 2 会把 CJK 字拆成两半
  3) 目标字区间向左右各取「相邻空隙的中点」，天然避让相邻字
  4) 与该行墨迹上下界合成矩形，直接喂 image_redact.redact()

CLI：
  python3 row_substr.py 图.png --y 195,265 --x 30,700 --target 1-3
  # 输出：三档阈值一致性 / 每字区间 / 目标矩形 / 相邻字未动校验命令
"""
import argparse
import sys

import numpy as np
from PIL import Image


def load_gray(path):
    return np.array(Image.open(path).convert("L")).astype(int)


def ink_vspan(gray, y0, y1, x0, x1, thr=220):
    """行内墨迹的上下边界（阈值放宽到 220 才抓得住抗锯齿边缘）。"""
    rows = (gray[y0:y1, x0:x1] < thr).sum(axis=1)
    ys = [i + y0 for i, v in enumerate(rows) if v > 0]
    return (min(ys), max(ys)) if ys else (None, None)


def row_cells(gray, y0, y1, x0, x1, thr=180, gap=3, min_px=1, min_w=2):
    """列投影切出「每字」的 x 区间。返回 [(x0, x1), ...]，长度 = 字数。"""
    cols = (gray[y0:y1, x0:x1] < thr).sum(axis=0)
    runs, s = [], None
    for i, v in enumerate(cols):
        if v >= min_px and s is None:
            s = i
        elif v < min_px and s is not None:
            runs.append([s + x0, i - 1 + x0])
            s = None
    if s is not None:
        runs.append([s + x0, x1 - 1])

    top, bot = ink_vspan(gray, y0, y1, x0, x1, thr=220)
    cell_h = (bot - top + 1) if top is not None else (y1 - y0)

    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] <= gap and (r[1] - merged[-1][0] + 1) <= cell_h * 1.05:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a, b) for a, b in merged if b - a + 1 >= min_w]


def stable_cells(gray, y0, y1, x0, x1, thrs=(140, 180, 220), gap=3):
    """三档阈值互校：返回 (以中档为准的 cells, 是否一致, 各档段数)。"""
    per = [(t, row_cells(gray, y0, y1, x0, x1, thr=t, gap=gap)) for t in thrs]
    counts = [len(c) for _, c in per]
    base = dict(per).get(thrs[len(thrs) // 2], per[0][1]) if per else []
    return base, len(set(counts)) == 1, counts


def substr_rect(gray, y0, y1, x0, x1, i_from, i_to, pad=2, thrs=(140, 180, 220),
                gap=3, vpad=3, cells=None):
    """第 i_from..i_to 个字（1-based，含两端）的安全矩形。

    Returns: dict(cells, consistent, counts, box, target, neighbors)
    """
    if cells is None:
        cells, consistent, counts = stable_cells(gray, y0, y1, x0, x1, thrs, gap)
    else:
        consistent, counts = True, [len(cells)]
    n = len(cells)
    if not (1 <= i_from <= i_to <= n):
        raise ValueError(f"target {i_from}-{i_to} 超出范围（本行切出 {n} 个字）")

    left = cells[i_from - 1][0]
    right = cells[i_to - 1][1]
    left_src = "字左缘"
    right_src = "字右缘"
    if i_from > 1:                      # 与左邻字的空隙中点
        prev_end = cells[i_from - 2][1]
        left = (prev_end + left) // 2
        left_src = f"空隙中点（左邻字止于 {prev_end}）"
    else:
        left = max(0, left - pad)
    if i_to < n:                        # 与右邻字的空隙中点
        nxt = cells[i_to][0]
        right = (right + nxt) // 2
        right_src = f"空隙中点（右邻字起于 {nxt}）"
    else:
        right = min(gray.shape[1] - 1, right + pad)

    top, bot = ink_vspan(gray, y0, y1, left, right + 1, thr=max(thrs))
    if top is None:
        top, bot = y0, y1
    box = (left, max(0, top - vpad), right, min(gray.shape[0] - 1, bot + vpad))
    return {
        "cells": cells, "consistent": consistent, "counts": counts, "box": box,
        "target": (cells[i_from - 1][0], cells[i_to - 1][1]),
        "left_rule": left_src, "right_rule": right_src,
        "neighbors": {"left": cells[i_from - 2] if i_from > 1 else None,
                      "right": cells[i_to] if i_to < n else None},
    }


def main():
    ap = argparse.ArgumentParser(description="横排行内子串打码边界定位")
    ap.add_argument("image")
    ap.add_argument("--y", required=True, help="行带的 y0,y1")
    ap.add_argument("--x", default=None, help="x 窗口 x0,x1（默认整宽）")
    ap.add_argument("--target", required=True, help="要盖第几个字，如 1-3")
    ap.add_argument("--thrs", default="140,180,220")
    ap.add_argument("--gap", type=int, default=3, help="同字合并的字间距上限，横排 CJK+拉丁取 3")
    ap.add_argument("--pad", type=int, default=2)
    a = ap.parse_args()

    gray = load_gray(a.image)
    y0, y1 = (int(v) for v in a.y.split(","))
    x0, x1 = (int(v) for v in a.x.split(",")) if a.x else (0, gray.shape[1])
    i_from, i_to = (int(v) for v in a.target.split("-"))
    thrs = tuple(int(v) for v in a.thrs.split(","))

    r = substr_rect(gray, y0, y1, x0, x1, i_from, i_to, pad=a.pad, thrs=thrs, gap=a.gap)
    print(f"行带 y {y0}-{y1}  x 窗口 {x0}-{x1}")
    print(f"三档阈值段数 {r['counts']} → {'✅ 一致' if r['consistent'] else '⚠️ 不一致，需人工核对'}")
    print(f"切出 {len(r['cells'])} 个字：")
    for i, (s, e) in enumerate(r["cells"], 1):
        tag = " ← 目标" if i_from <= i <= i_to else ""
        print(f"  #{i}: x {s}-{e} (w={e - s + 1}){tag}")
    top, bot = ink_vspan(gray, y0, y1, x0, x1, thr=max(thrs))
    cell_h = (bot - top + 1) if top is not None else (y1 - y0)
    thin = [i for i, (s2, e2) in enumerate(r["cells"], 1) if (e2 - s2 + 1) < 0.5 * cell_h]
    if thin:
        print(f"⚠️ 窄段 {thin}（宽度 < 行高一半，多为 I/1/i 等窄字符）：段数可能少于字符数，"
              f"请按上面的 x 区间核对后再定 --target")
    print(f"目标字墨迹 x {r['target'][0]}-{r['target'][1]}")
    print(f"左界：{r['left_rule']}；右界：{r['right_rule']}")
    print(f"→ 打码矩形 (x1,y1,x2,y2) = {r['box']}")
    print(f"  redact(图, out, [{r['box']}])")
    print("  校验：输出图在目标框外逐像素不变；相邻字区段全等（见 SKILL.md 工作流第四步）")


if __name__ == "__main__":
    sys.exit(main())

# 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）
