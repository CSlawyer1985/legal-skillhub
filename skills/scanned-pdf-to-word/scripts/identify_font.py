#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描件字体 / 字号识别 —— 像素级 IoU 网格搜索

问题：扫描件没有文本层，"看起来像楷体还是仿宋"目视不可靠、AI 猜测更不可靠。
本脚本把原件墨迹二值化，与候选字体渲染图做掩膜 IoU 比对，给出量化排名与字号估计。

原理：
  1. 从扫描件裁出一段文字行，Otsu 二值化成墨迹掩膜（参考图）
  2. 遍历候选字体：用 PIL 渲染同一串文字 → 同样二值化 → 裁到自身墨迹外接框
  3. 【字形分 shape】把候选掩膜缩放到与参考外接框同尺寸后算 IoU
     —— 缩放归零了尺寸差异，因此这一列**纯比字形**，不受字号误差干扰
  4. 【绝对分 abs】按估计字号原尺寸渲染候选，两张掩膜左上对齐后算 IoU
     —— 同时考验字形与字号；若 abs ≈ shape，说明字号也估对了
  5. **两侧同等膨胀**（默认半径 1px）后比对。扫描墨迹天然比矢量渲染粗，
     必须补偿；但**只膨胀原件会系统性偏袒粗笔字体**（黑体/榜书楷分数虚高）。
     实测：只膨胀原件时粗楷爬到第一，两侧同膨胀后真命字体以 0.807 vs 0.425 断层胜出。

字号估计：size_pt = 参考墨迹宽(pt) / 单位墨水宽(em)
  其中单位墨水宽 = 小尺寸探针渲染的墨迹像素宽 / em
  再用该字号原尺寸复渲染一次做字形比对（此时墨高已≈参考墨高，缩放接近恒等）

⚠️ IoU 绝对值因对称膨胀而整体抬高，**只有相对排名有意义**，不要拿 0.8 当"很好"。
  判定标准看**与次名的差距**：> 0.15 可下结论，< 0.08 须换一行交叉验证。

用法：
  # 先探出行带坐标（pt），挑一行有代表性的文字
  python3 identify_font.py --pdf scan.pdf --probe

  # 再指定该行的 rect（左,上,右,下，单位 pt）与文字内容
  python3 identify_font.py --pdf scan.pdf --text "授权委托事项：" --rect 76 466 173 484

注意：--text 必须与 rect 内的文字**完全一致**（含标点），多一字少一字都会毁掉结果。
  rect 内不能混入相邻行的笔画。
  结论要有三条以上独立样本交叉验证（不同字数、不同位置的行）。
"""
import argparse
import os
import re
import sys

import numpy as np
import fitz
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from fontTools.ttLib import TTFont
except ImportError:  # 只用文件名兜底
    TTFont = None

FONT_DIRS = [
    os.path.expanduser("~/Library/Fonts"),
    "/Library/Fonts",
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
]
EXTS = (".ttf", ".otf", ".ttc")
CJK = re.compile(r"[\u4e00-\u9fff]")


# ---------------------------------------------------------------- 工具


def otsu(gray):
    """灰度图 Otsu 阈值"""
    hist = np.bincount(gray.ravel(), minlength=256).astype(float)
    total = gray.size
    sum_all = float(np.dot(np.arange(256), hist))
    sum_b = w_b = 0.0
    best, thr = -1.0, 127
    for i in range(256):
        w_b += hist[i]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += i * hist[i]
        m_b, m_f = sum_b / w_b, (sum_all - sum_b) / w_f
        v = w_b * w_f * (m_b - m_f) ** 2
        if v > best:
            best, thr = v, i
    return thr


def crop_ink(m):
    """裁到墨迹外接框；无墨迹返回 None"""
    ys, xs = np.where(m)
    if ys.size == 0:
        return None
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def dilate(m, r):
    if r <= 0:
        return m
    im = Image.fromarray((m * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MaxFilter(2 * r + 1))
    return np.array(im) > 127


def resize_to(m, h, w):
    im = Image.fromarray((m * 255).astype(np.uint8))
    im = im.resize((w, h), Image.LANCZOS)
    return np.array(im) > 127


def iou(a, b):
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter) / union if union else 0.0


def render_mask(text, font_path, size_px, index=0):
    """渲染文字为墨迹掩膜（True = 墨）"""
    f = ImageFont.truetype(font_path, size=int(round(size_px)), index=index)
    pad = int(size_px) + 8
    w = int(f.getlength(text)) + pad * 2
    h = int(size_px * 2.2) + pad
    img = Image.new("L", (max(w, 8), max(h, 8)), 255)
    ImageDraw.Draw(img).text((pad, pad), text, font=f, fill=0)
    return np.array(img) < 128


def stem(name):
    """归并同一设计的变体：方正楷体简体 / 方正楷体繁体 / 方正楷体_GBK → 方正楷体

    否则"与次名的差距"会被自家变体吃掉，误报成"差距偏小"。
    """
    return re.sub(r"(简体|繁体|_?GBK|Regular|Normal|Unicode|Pro)$", "", name).strip() or name


def family_name(path):
    """取字体族名，优先中文名"""
    base = os.path.splitext(os.path.basename(path))[0]
    if TTFont is None:
        return base
    names = []
    try:
        t = TTFont(path, fontNumber=0, lazy=True)
        for rec in t["name"].names:
            if rec.nameID in (1, 4):
                try:
                    s = rec.toUnicode().strip()
                except Exception:
                    continue
                if s:
                    names.append(s)
        t.close()
    except Exception:
        return base
    for s in names:
        if CJK.search(s):
            return s
    return names[0] if names else base


def scan_fonts():
    out = []
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(EXTS):
                out.append(os.path.join(d, fn))
    return out


# ---------------------------------------------------------------- 测量


def probe_bands(page, z):
    """列出页面所有墨迹行带，单位为 pt"""
    pm = page.get_pixmap(matrix=fitz.Matrix(z, z))
    gray = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, 0]
    thr = otsu(gray)
    ink = gray < thr
    rows = ink.any(axis=1)
    bands, start = [], None
    for i, v in enumerate(rows):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= 3:
                bands.append((start, i - 1))
            start = None
    if start is not None:
        bands.append((start, len(rows) - 1))

    print(f"页面 {page.rect.width:.2f} x {page.rect.height:.2f} pt，缩放 {z:.4f} px/pt")
    print(f"{'#':>3} {'y0':>7} {'y1':>7} {'x0':>7} {'x1':>7}  {'高pt':>6}")
    for n, (a, b) in enumerate(bands):
        seg = ink[a:b + 1]
        xs = np.where(seg.any(axis=0))[0]
        print(f"{n:>3} {a / z:>7.2f} {b / z:>7.2f} {xs.min() / z:>7.2f} {xs.max() / z:>7.2f}"
              f"  {(b - a + 1) / z:>6.2f}")
    print("\n提示：取 rect = 左 上 右 下（pt），建议在选定行带上下各留 1pt，"
          "左右端手工收紧到该行文字的墨迹范围，确保 rect 内只有你要的那串字。")


def ref_mask(page, rect, z):
    x0, y0, x1, y1 = rect
    clip = fitz.Rect(x0, y0, x1, y1)
    pm = page.get_pixmap(matrix=fitz.Matrix(z, z), clip=clip)
    gray = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, 0]
    return gray < otsu(gray)


# ---------------------------------------------------------------- 主流程


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--probe", action="store_true", help="列出墨迹行带后退出")
    ap.add_argument("--text", help="rect 内的文字，须完全一致")
    ap.add_argument("--rect", nargs=4, type=float, metavar=("L", "T", "R", "B"))
    ap.add_argument("--zoom", type=float, default=6.0, help="渲染缩放 px/pt（默认 6≈432dpi）")
    ap.add_argument("--dilate", type=int, default=1, help="两侧同膨胀半径 px（默认 1）")
    ap.add_argument("--top", type=int, default=12, help="显示前 N 个候选")
    ap.add_argument("--filter", default=None, help="只测文件名含该串的字体，加速定位")
    ap.add_argument("-A", "--export-abs", action="store_true", help="导出绝对对齐比对图")
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    page = doc[a.page]
    z = a.zoom

    if a.probe:
        probe_bands(page, z)
        return
    if not (a.text and a.rect):
        ap.error("需要 --text 与 --rect（或使用 --probe）")

    ref = crop_ink(ref_mask(page, a.rect, z))
    if ref is None:
        sys.exit("rect 内无墨迹，请检查坐标")
    rh, rw = ref.shape
    ref_w_pt = rw / z
    ref_d = dilate(ref, a.dilate)
    fonts = scan_fonts()
    if a.filter:
        fonts = [f for f in fonts if a.filter.lower() in os.path.basename(f).lower()]
    if not fonts:
        sys.exit("没有找到候选字体")

    print(f"参考：{a.text!r}  墨迹 {rw}x{rh}px = {ref_w_pt:.2f}x{rh / z:.2f}pt  "
          f"（{len(fonts)} 个候选字体，膨胀半径 {a.dilate}px）\n")

    rows = []
    unit_px = 120.0            # 探针渲染的 em 像素（仅用于量比例，不必大）
    for fp in fonts:
        try:
            # 探针：量出单位墨水宽 / 高（em）
            probe = crop_ink(render_mask(a.text, fp, unit_px))
            if probe is None:
                continue
            unit_em = probe.shape[1] / unit_px       # 单位墨水宽（em）
            size_pt = ref_w_pt / unit_em             # 字号反推
            # 定型：按反推字号原尺寸渲染，此时墨高已 ≈ rh，缩放接近恒等
            near = crop_ink(render_mask(a.text, fp, size_pt * z))
            if near is None:
                continue
            shape = iou(ref_d, dilate(resize_to(near, rh, rw), a.dilate))
            # 绝对对齐（不复位缩放）→ 同时考验字形与字号
            near_d = dilate(near, a.dilate)
            H = max(rh, near_d.shape[0])
            W = max(rw, near_d.shape[1])
            c1 = np.zeros((H, W), bool); c1[:rh, :rw] = ref_d
            c2 = np.zeros((H, W), bool); c2[:near_d.shape[0], :near_d.shape[1]] = near_d
            rows.append((family_name(fp), shape, iou(c1, c2), size_pt, fp,
                         near.shape[1] / z))
        except Exception:
            continue

    if not rows:
        sys.exit("所有候选字体都渲染失败——检查 --text 里的字符是否被字体支持")

    # 同一字族可能有多个字体文件（斜体/不同版本），按字族取最高分，避免"次名是自己"
    best_of = {}
    for r in rows:
        if r[0] not in best_of or r[1] > best_of[r[0]][1]:
            best_of[r[0]] = r
    rows = sorted(best_of.values(), key=lambda r: -r[1])

    print(f"{'字族':<26}{'字形分':>8}{'绝对分':>8}{'估计字号':>10}{'试探墨宽pt':>11}")
    print("-" * 66)
    for name, shape, ab, sp, fp, wpt in rows[:a.top]:
        print(f"{name:<26}{shape:>8.3f}{ab:>8.3f}{sp:>9.2f}pt{wpt:>11.2f}")

    best = rows[0]
    # 简体/繁体/GBK 变体是同一设计的同一答案，不能算"次名"
    same = [r for r in rows if stem(r[0]) == stem(best[0])]
    others = [r for r in rows if stem(r[0]) != stem(best[0])]
    print(f"\n最佳匹配：{best[0]}  字形分 {best[1]:.3f}  估计字号 {best[3]:.2f}pt")
    if len(same) > 1:
        print("同设计变体（视为同一答案）："
              + ", ".join(f"{r[0]} {r[1]:.3f}" for r in same[1:6]))
    if others:
        gap = best[1] - others[0][1]
        ratio = best[1] / others[0][1] if others[0][1] else 99
        if gap >= 0.15:
            verdict = "断层优势，结论可靠"
        elif gap >= 0.08:
            verdict = "优势明显，建议再测一行确认"
        else:
            verdict = "差距偏小，必须换一行交叉验证"
        print(f"最佳异族（{others[0][0]} {others[0][1]:.3f}）相差 {gap:+.3f}"
              f"（{ratio:.2f} 倍）—— {verdict}")
    print(f"\nWord 字号精度为 0.5pt，取最近档：{round(best[3] * 2) / 2:.1f}pt")

    if a.export_abs:
        fp = best[4]
        em_px = best[3] * z
        near = crop_ink(render_mask(a.text, fp, em_px))
        a_m = dilate(ref, a.dilate)
        b_m = dilate(near, a.dilate)
        H = max(rh, b_m.shape[0]) + 8
        W = rw + b_m.shape[1] + 16
        canvas = np.full((H, W), 255, np.uint8)
        canvas[4:4 + rh, 4:4 + rw][a_m] = 0
        canvas[4:4 + b_m.shape[0], rw + 12:rw + 12 + b_m.shape[1]][b_m] = 0
        out = os.path.join(os.path.dirname(os.path.abspath(a.pdf)),
                           "identify_abs.png")
        Image.fromarray(canvas).save(out)
        print(f"绝对对齐比对图（左=原件 右=最佳候选，均为膨胀后掩膜）：{out}")


if __name__ == "__main__":
    main()
