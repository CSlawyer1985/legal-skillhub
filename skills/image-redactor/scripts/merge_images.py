#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多张图拼接成一张（横排/竖排），带逐像素校验。

用途：多张截图脱敏后拼成一张——公众号/课件配图、流程对比图。
横排省纵向长度、竖排省横向宽度，按发布场景选。

规则（P0）：
  · 画布边长取各图对应边的最大值，间隙默认 24px 纯白；一律输出 PNG（无损，
    不要把 JPEG 再压一遍——黑块的「纯黑」会在压缩中漂移）。
  · 拼接后必须逐像素校验：粘贴区 == 源图、接缝带纯白。防止缩放/偏移悄悄发生。
  · 同内容不同分辨率的副本（剪贴板 jpg vs 目录原 png）取原 png。

CLI：
  python3 merge_images.py out.png a.png b.png c.png --direction h --gap 24
  python3 merge_images.py out.png a.png b.png --direction v --reverse   # 逆序（右图放左）
  python3 merge_images.py out.png a.png b.png --dry-run                 # 只打印尺寸不落盘
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image


def plan(paths, direction="h", gap=24):
    """算画布尺寸与每张图的粘贴坐标。返回 (canvas_w, canvas_h, [(path, x, y), ...])。"""
    sizes = [Image.open(p).size for p in paths]
    if direction == "h":
        w = sum(s[0] for s in sizes) + gap * (len(sizes) - 1)
        h = max(s[1] for s in sizes)
        pos, x = [], 0
        for p, (pw, _) in zip(paths, sizes):
            pos.append((p, x, 0)); x += pw + gap
    elif direction == "v":
        w = max(s[0] for s in sizes)
        h = sum(s[1] for s in sizes) + gap * (len(sizes) - 1)
        pos, y = [], 0
        for p, (_, ph) in zip(paths, sizes):
            pos.append((p, 0, y)); y += ph + gap
    else:
        raise ValueError("direction 须为 h / v")
    return w, h, pos


def merge_images(paths, out, direction="h", gap=24, bg=(255, 255, 255), verify=True):
    """拼接并（可选）逐像素校验。

    Returns: (out_path, report:list[str], ok:bool)
    """
    w, h, pos = plan(paths, direction, gap)
    canvas = Image.new("RGB", (w, h), bg)
    srcs = []
    for p, x, y in pos:
        im = Image.open(p).convert("RGB")
        canvas.paste(im, (x, y))
        srcs.append(((x, y, im.width, im.height), im))
    canvas.save(out, optimize=True)

    report = [f"方向={'横排' if direction == 'h' else '竖排'}  间隙={gap}px  画布={w}x{h}"]
    if not verify:
        return out, report, True

    arr = np.array(Image.open(out).convert("RGB")).astype(int)
    ok = True
    for i, ((x, y, iw, ih), im) in enumerate(srcs, 1):
        same = bool((arr[y:y + ih, x:x + iw] == np.array(im).astype(int)).all())
        ok &= same
        report.append(f"  图{i} 粘贴区 ({x},{y})-({x + iw - 1},{y + ih - 1}) 逐像素一致={same}")
    # 接缝带纯白
    for i in range(len(srcs) - 1):
        if direction == "h":
            x0 = srcs[i][0][0] + srcs[i][0][2]
            seam = arr[:, x0:x0 + gap]
        else:
            y0 = srcs[i][0][1] + srcs[i][0][3]
            seam = arr[y0:y0 + gap, :]
        white = bool((seam == np.array(bg)).all())
        ok &= white
        report.append(f"  接缝{i + 1} 纯背景色={white}")
    report.append(f"尺寸 {Image.open(out).size}  大小 {round(os.path.getsize(out) / 1024)} KB")
    report.append("拼接校验: " + ("✅ 通过" if ok else "❌ 存在偏差，勿交付"))
    return out, report, ok


def main():
    ap = argparse.ArgumentParser(description="多图横排/竖排拼接 + 逐像素校验")
    ap.add_argument("out")
    ap.add_argument("images", nargs="+", help="按拼接顺序给出（左→右 或 上→下）")
    ap.add_argument("--direction", choices=["h", "v"], default="h")
    ap.add_argument("--gap", type=int, default=24)
    ap.add_argument("--reverse", action="store_true", help="逆序（例：把右图放到左边）")
    ap.add_argument("--dry-run", action="store_true", help="只打印尺寸与位置，不落盘")
    a = ap.parse_args()

    paths = list(reversed(a.images)) if a.reverse else a.images
    for p in paths:
        if not os.path.exists(p):
            sys.exit(f"找不到文件：{p}")
    if a.dry_run:
        w, h, pos = plan(paths, a.direction, a.gap)
        print(f"画布 {w}x{h}")
        for p, x, y in pos:
            print(f"  {p} → ({x},{y})")
        return 0
    _, report, ok = merge_images(paths, a.out, a.direction, a.gap)
    print("\n".join(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

# 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）
