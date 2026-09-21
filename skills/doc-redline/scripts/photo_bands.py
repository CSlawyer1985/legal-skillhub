#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: WorkBuddy (agent_created)
"""把手机拍摄的文书照片切成「可逐行读清的横条」，并把纸张区域先框出来。

为什么不能直接 Read 整张照片：
  手机拍 A4 是 2160×3840 竖图，整图读进来后单字只有几个像素，正文糊成一片。
  而 Read 工具对图像有分辨率上限，喂原图等于白喂——必须裁细再放大。

三条参数上的「为什么」（都是实测调出来的，不要凭感觉改）：
  1) 先出一张 30% 缩略图（`*_overview.png`）：**先看版式，再抠细节**。
     “某一段整段消失”这类问题在缩略图上最显眼，逐条读反而容易迷路。
  2) `--band` 必须大于 `--step`（默认 560 > 470，重叠 90px）：
     否则行会被切在条与条之间，**上下各少半行，读出来的句子是残的**——
     这种错会伪装成“原稿少了几个字”，比切不干净危险得多。
  3) 所有条统一缩放到同一宽度（默认 1500px）：
     不同页纸张定位的宽窄不同，不统一的话每次读到的字号大小不一样，
     容易把“这页字小”误判成“这页内容不同”。

用法:
  python3 photo_bands.py 1.jpg 2.jpg 3.jpg            # 切到与图同级的 _bands/
  python3 photo_bands.py ./照片/ -o /tmp/bands         # 整目录
  python3 photo_bands.py 1.jpg --band 700 --step 560   # 行更密的文书（小五号）
  python3 photo_bands.py 1.jpg --overview 0.20         # 想看更粗的版式

产出:
  <out>/<stem>_overview.png   缩略图，先看这个
  <out>/<stem>_b1.png ...     横条，按 --step 依次向下，条号即阅读顺序
  每条会打印 y 区间，便于与照片对位回溯
"""
import argparse
import os
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError as e:  # numpy/PIL 缺失时说清楚装什么，别抛裸异常
    sys.exit("缺依赖（%s）。请装：python3 -m pip install numpy pillow" % e)

EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")
# HEIC 单独提示：iPhone 直出格式，PIL 默认解不了，需先转 jpg
HEIC = (".heic", ".heif")


def locate_paper(img):
    """用行/列灰度均值的相对阈值定位纸张。返回 (x0, y0, x1, y1)。

    为什么用“最大值 × 比例”而不是绝对亮度：拍摄环境光差异极大，
    绝对阈值换个场地就废；纸张是画面里最大片的亮区，取相对值才稳。
    为什么行用 --paper-thresh、列用 --col-thresh 两个参数：
    纸张上下有桌面、左右有背景，两者的对比度经常不一样，
    共用一个系数会把桌面也算进纸张里。
    """
    g = np.asarray(img.convert("L")).astype(np.float32)
    rowm = g.mean(axis=1)
    colm = g.mean(axis=0)
    rows = np.where(rowm > rowm.max() * args.paper_thresh)[0]
    cols = np.where(colm > rowm.max() * args.col_thresh)[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def bands_of(path, outdir):
    im = Image.open(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    w, h = im.size

    if w > h:
        print("  ⚠️ %s 是横向图（%d×%d）。本脚本按竖版 A4 设计，"
              "请先确认方向或用 -o 手工裁。" % (stem, w, h))

    ov_scale = args.overview
    ov = im.resize((max(1, int(w * ov_scale)), max(1, int(h * ov_scale))), Image.LANCZOS)
    ov_path = os.path.join(outdir, "%s_overview.png" % stem)
    ov.save(ov_path)
    print("  %-22s %d×%d → 缩略图 %s" % (os.path.basename(path), w, h, os.path.basename(ov_path)))

    box = locate_paper(im)
    if box is None:
        print("  ⚠️ 定位纸张失败，退回整图切条")
        x0, y0, x1, y1 = 0, 0, w, h
    else:
        x0, y0, x1, y1 = box
        # 防呆：定位结果太小说明阈值把纸也算成背景了，宁可用整图也不要给错框
        if (y1 - y0) < h * 0.30 or (x1 - x0) < w * 0.30:
            print("  ⚠️ 纸张区域过小（y %d-%d, x %d-%d），退回整图切条"
                  % (y0, y1, x0, x1))
            x0, y0, x1, y1 = 0, 0, w, h
        else:
            print("  %-22s 纸张 y %d-%d（高 %d）x %d-%d（宽 %d）"
                  % ("", y0, y1, y1 - y0, x0, x1, x1 - x0))

    rgb = im.convert("RGB")
    n, y = 0, y0
    while y < y1:
        yb = min(y + args.band, y1)
        crop = rgb.crop((x0, y, x1, yb))
        factor = float(args.width) / crop.width
        crop = crop.resize(
            (int(crop.width * factor), int(crop.height * factor)), Image.LANCZOS
        )
        n += 1
        crop.save(os.path.join(outdir, "%s_b%d.png" % (stem, n)))
        print("     b%-2d y=%d-%d  %d×%d" % (n, y, yb, crop.width, crop.height))
        if yb >= y1:
            break          # 已到纸张下缘：再切只会得到被本条完全包含的重复条，
                           # 那种残条读起来像"多了一段"，纯噪声
        y += args.step
    return n


def main():
    paths = []
    for p in args.images:
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.lower().endswith(EXTS):
                    paths.append(os.path.join(p, f))
                elif f.lower().endswith(HEIC):
                    print("⏭  跳过 HEIC：%s（先转 jpg：`sips -s format jpeg` 或预览导出）" % f)
        elif p.lower().endswith(HEIC):
            print("⏭  跳过 HEIC：%s（先转 jpg）" % p)
        elif os.path.exists(p):
            paths.append(p)
        else:
            print("⚠️ 找不到：%s" % p)

    if not paths:
        sys.exit("没有可处理的图片。")

    outdir = args.out or os.path.join(os.path.dirname(os.path.abspath(paths[0])), "_bands")
    os.makedirs(outdir, exist_ok=True)
    print("输出目录：%s\n" % outdir)

    total = 0
    for p in paths:
        total += bands_of(p, outdir) or 0

    print("\n共 %d 张 → %d 条。**先看缩略图定版式，再按条号逐条读。**\n"
          "读的时候：条与条重叠区的内容要接起来读，不要把重叠当成重复行。" % (len(paths), total))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="把文书照片切成可逐行读清的横条")
    ap.add_argument("images", nargs="+", help="图片路径或目录（可多个）")
    ap.add_argument("-o", "--out", help="输出目录（默认 <图片目录>/_bands）")
    ap.add_argument("--width", type=int, default=1500, help="统一缩放宽（默认 1500）")
    ap.add_argument("--band", type=int, default=560, help="单条高度像素（默认 560）")
    ap.add_argument("--step", type=int, default=470, help="向下步长（默认 470，须 < band 以重叠）")
    ap.add_argument("--overview", type=float, default=0.30, help="缩略图比例（默认 0.30）")
    ap.add_argument("--paper-thresh", type=float, default=0.58, help="纸张行阈值系数（默认 0.58）")
    ap.add_argument("--col-thresh", type=float, default=0.45, help="纸张列阈值系数（默认 0.45）")
    args = ap.parse_args()

    if args.step >= args.band:
        sys.exit("--step 必须小于 --band（默认 470 < 560）。否则行会被切断，读出来是残句。")
    main()
