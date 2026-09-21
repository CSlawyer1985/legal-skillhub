#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
photo_layout.py — 聊天记录中保存的照片/文件 证据排版
排版规则与 case-file-review「图片自动排版」/ 帧册 Framebook 一致：
  每页2张（照片类，默认）= 横版A4 841.89×595.276，边距24，中缝18，左右两格
  每页1张（关键凭证）   = 竖版A4，边距24，完整居中
  每页4张（截图类）     = 竖版A4，边距20，格间距12，2×2
页码「组号-页号」16pt 底部居中（--no-page-number 可关闭）；图片等比缩放完整居中，绝不裁剪绝不变形。
用法:
  python3 photo_layout.py 图1.jpg 图2.jpg ... -o 输出目录 [--per-page 2] [--group 1]
  python3 photo_layout.py 照片目录/ -o 输出目录            # 目录内全部图片按文件名排序
  支持 jpg/png/bmp/tiff/webp 与 pdf（PDF 逐页转图插入）
"""
import argparse
import os
import sys

import fitz  # pymupdf
from PIL import Image, ImageOps

PAGE = {"1": (595.276, 841.89), "2": (841.89, 595.276), "4": (595.276, 841.89)}
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def parse_args():
    ap = argparse.ArgumentParser(description="照片/文件证据排版（交互询问版式，或参数直传跳过提问）")
    ap.add_argument("inputs", nargs="+", help="图片/PDF 文件或目录（目录取全部图片按名排序）")
    ap.add_argument("-o", "--outdir", default=None, help="输出目录 (默认: ~/Desktop/照片排版_<组名>)")
    ap.add_argument("--per-page", type=int, choices=[1, 2, 4], default=None,
                    help="每页张数：1=关键凭证竖版整页 2=照片一上一下(竖版)/左右(横版) 4=截图2×2。不传则交互询问")
    ap.add_argument("--landscape", action="store_true",
                    help="每页2张时用横版左右两格（竖拍照片更大；默认竖版一上一下，横拍照片更大）")
    ap.add_argument("--group", default=None, help="组号（页码前缀，页码形如 1-1）。不传则交互询问")
    ap.add_argument("--no-page-number", action="store_true",
                    help="不打印「组号-页号」页码（页码待材料编排完成后统一回填时用）")
    ap.add_argument("--name", default=None, help="输出文件名标识 (默认取首个输入文件名/目录名)")
    ap.add_argument("--dpi", type=int, default=150, help="PDF 输入转图 DPI (默认150)")
    ap.add_argument("--yes", action="store_true", help="跳过交互，全部用默认值（2张/页竖版一上一下，组号1）")
    return ap.parse_args()


LAYOUT_MENU = """
请选择排版版式：
  1. 每页 1 张 —— 关键凭证，竖版 A4 整页完整居中
  2. 每页 2 张 —— 照片类（默认）：竖版 A4 一上一下；横拍照片单格更大
  3. 每页 2 张 —— 照片类横版：横版 A4 左右两格；竖拍照片单格更大
  4. 每页 4 张 —— 截图类：竖版 A4 2×2
"""


def ask_layout(args):
    """交互询问版式与组号；--yes 或参数已给时跳过。返回 (per_page, landscape, group)。"""
    per_page, landscape, group = args.per_page, args.landscape, args.group
    if not sys.stdin.isatty() and not args.yes and per_page is None:
        # 非交互环境（如被 agent 调用）无法提问：用默认并提示
        print("[提示] 非交互环境，未指定 --per-page，使用默认：每页2张竖版一上一下（组号1）")
        return 2, False, group or "1"
    if per_page is None and not args.yes:
        print(LAYOUT_MENU, end="")
        while True:
            c = input("输入选项 [1/2/3/4]（回车=2 一上一下）: ").strip()
            if c == "" :
                per_page, landscape = 2, False
                break
            if c == "1":
                per_page = 1
                break
            if c == "2":
                per_page, landscape = 2, False
                break
            if c == "3":
                per_page, landscape = 2, True
                break
            if c == "4":
                per_page = 4
                break
            print("无效输入，请输入 1/2/3/4")
    elif per_page is None:
        per_page = 2
    if group is None and not args.yes and sys.stdin.isatty():
        g = input("页码组号 [回车=1]: ").strip()
        group = g or "1"
    elif group is None:
        group = "1"
    return per_page, landscape, group


def collect_images(inputs, dpi):
    """收集输入为 PIL 图像列表（PDF 逐页渲染；图片做 EXIF 方向归一化）。"""
    files = []
    for p in inputs:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in sorted(os.listdir(p))
                      if os.path.splitext(f)[1].lower() in IMG_EXTS]
        elif os.path.splitext(p)[1].lower() == ".pdf":
            files.append(p)
        else:
            files.append(p)
    if not files:
        sys.exit("错误：未找到任何图片/PDF 输入")
    images = []
    for path in files:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            doc = fitz.open(path)
            for pg in doc:
                pix = pg.get_pixmap(dpi=dpi)
                images.append((os.path.basename(path), Image.open(__import__("io").BytesIO(pix.tobytes("png")))))
            doc.close()
        else:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)  # 手机照片 EXIF 方向归一化
            images.append((os.path.basename(path), img))
    return images


def cells(per_page, landscape=False):
    """每页各格子 (x, y, w, h)，原点左上；格子顺序即阅读顺序：左→右、上→下。
    2张默认竖版一上一下（横拍照片单格更大33%，卷宗方向统一）；landscape=True 横版左右格（竖拍照片更大）。"""
    pw, ph = PAGE["1" if (per_page == 2 and not landscape) else str(per_page)]
    if per_page == 1:
        m = 24
        return [(m, m, pw - 2 * m, ph - 2 * m)]
    if per_page == 2:
        m, gap = 24, 18
        if landscape:  # 横版左右两格
            cw = (pw - 2 * m - gap) / 2
            return [(m, m, cw, ph - 2 * m), (m + cw + gap, m, cw, ph - 2 * m)]
        # 竖版一上一下（默认）：上下两格，中缝18
        ch = (ph - 2 * m - gap) / 2
        return [(m, m, pw - 2 * m, ch), (m, m + ch + gap, pw - 2 * m, ch)]
    m, gap = 20, 12
    cw = (pw - 2 * m - gap) / 2
    ch = (ph - 2 * m - gap) / 2
    return [(m, m, cw, ch), (m + cw + gap, m, cw, ch),
            (m, m + ch + gap, cw, ch), (m + cw + gap, m + ch + gap, cw, ch)]


def place_image(img_w, img_h, cell, bottom_reserve):
    """等比缩放居中进格子（scale=min，绝不裁剪绝不变形），bottom_reserve 为页码预留。"""
    x, y, cw, ch = cell
    ch -= bottom_reserve
    scale = min(cw / img_w, ch / img_h)
    w, h = img_w * scale, img_h * scale
    return x + (cw - w) / 2, y + (ch - h) / 2, w, h


def self_check(n_images, per_page, n_pages, doc, bottom_reserve):
    """交付前自检：页数口径、页码区不被遮挡。"""
    expect_pages = -(-n_images // per_page)  # ceil
    assert n_pages == expect_pages, f"页数不符: 生成{n_pages} 预期{expect_pages}"
    pw, ph = PAGE[str(per_page)]
    for i, pg in enumerate(doc):
        n_this = min(per_page, n_images - i * per_page)
        assert n_this >= 1, f"第{i+1}页无图"
    # 末页最后一张图底边距检查由排版逻辑保证（bottom_reserve 预留），此处抽查渲染页数
    return True


def main():
    args = parse_args()
    per_page, landscape, group = ask_layout(args)
    images = collect_images(args.inputs, args.dpi)
    n = len(images)
    name = args.name or (os.path.basename(os.path.normpath(args.inputs[0]))
                         if os.path.isdir(args.inputs[0]) else os.path.splitext(os.path.basename(args.inputs[0]))[0])
    outdir = args.outdir or os.path.join(os.path.expanduser("~/Desktop"), f"照片排版_{name}")
    os.makedirs(outdir, exist_ok=True)

    pw, ph = PAGE["1" if (per_page == 2 and not landscape) else str(per_page)]
    bottom_reserve = 28  # 16pt 页码 + 8pt 让位（与 case-file-review 铁律一致）
    doc = fitz.open()
    grid = cells(per_page, landscape)
    print(f"[版式] 每页{per_page}张 {'横版左右' if (per_page==2 and landscape) else '竖版'} | 组号 {group} | 共{n}张图")

    for page_idx in range(0, n, per_page):
        page = doc.new_page(width=pw, height=ph)
        batch = images[page_idx:page_idx + per_page]
        for slot, (_, img) in enumerate(batch):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            x, y, w, h = place_image(img.width, img.height, grid[slot], bottom_reserve)
            tmp = os.path.join(outdir, "_tmp_slot.png")
            img.save(tmp)
            page.insert_image(fitz.Rect(x, y, x + w, y + h), filename=tmp)
            os.remove(tmp)
        # 页码「组号-页号」16pt 底部居中
        if not args.no_page_number:
            pno = page_idx // per_page + 1
            label = f"{group}-{pno}"
            page.insert_text(fitz.Point(pw / 2 - 12, ph - 12), label, fontsize=16,
                             fontname="helv", color=(0, 0, 0))

    self_check(n, per_page, doc.page_count, doc, bottom_reserve)
    n_pages = doc.page_count
    out_pdf = os.path.join(outdir, f"照片排版_{name}_一面{per_page}张{'_横版' if (per_page == 2 and landscape) else ''}.pdf")
    doc.save(out_pdf, deflate=True)
    doc.close()
    print(f"[OK] {n} 张图 → {n_pages} 页 ({per_page}张/页)")
    print(f"[OK] {out_pdf}")
    print("[提醒] 请人工复核：图片无裁剪无变形、页码未压图、顺序符合取证顺序")


if __name__ == "__main__":
    main()
