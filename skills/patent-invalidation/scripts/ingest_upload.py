#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_upload.py — 处理「用户手动上传的全文 / 附图」的落地助手（M1/M3「可选应对」分支②）

当用户选择上传某篇专利的官方 PDF 或附图图片时，本脚本把上传件规范化为
report_data.json 可直接引用的条目：
  - 图片(PNG/JPG)：复制到工作目录 figs/，归一化文件名，输出相对路径 + JSON 片段
  - PDF：用 PyMuPDF 提取指定绘图页为 PNG（图像型 PDF 仍建议用 contact sheet 核对绘图页），
         输出各页相对路径；未装 PyMuPDF 时退化为仅复制 PDF 并给出提示

用法：
  # 图片直接落地
  python scripts/ingest_upload.py --file /path/to/CN107084577A_fig.png \
      --label CN107084577A --out-dir ./output_xxx

  # PDF 提取第 11、12 页（绘图页）为 PNG
  python scripts/ingest_upload.py --file /path/to/CN105042985A.pdf \
      --label CN105042985A --out-dir ./output_xxx --pages 11,12

输出：打印一段可直接粘入 report_data.json / figure_compare 的 JSON（source 默认 user_upload）。
"""
import argparse
import json
import os
import shutil
import sys

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
PDF_EXT = {".pdf"}


def norm_label(label):
    # 去掉空格/斜杠，保留字母数字与连字符
    return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in (label or "upload"))


def ingest_image(src, out_dir, label):
    ext = os.path.splitext(src)[1].lower()
    figs_dir = os.path.join(out_dir, "figs")
    os.makedirs(figs_dir, exist_ok=True)
    dst = os.path.join(figs_dir, f"{norm_label(label)}_upload{ext}")
    shutil.copy2(src, dst)
    rel = os.path.relpath(dst, out_dir).replace("\\", "/")
    return [{
        "src": rel,
        "source": "user_upload",
        "caption": f"用户上传：{label}（官方附图）",
    }]


def ingest_pdf(src, out_dir, label, pages):
    figs_dir = os.path.join(out_dir, "figs")
    os.makedirs(figs_dir, exist_ok=True)
    try:
        import fitz  # PyMuPDF
    except Exception:
        # 退化：仅复制 PDF，提示人工提取
        dst = os.path.join(figs_dir, f"{norm_label(label)}_upload.pdf")
        shutil.copy2(src, dst)
        rel = os.path.relpath(dst, out_dir).replace("\\", "/")
        print("[警告] 未安装 PyMuPDF（pip install PyMuPDF），已复制 PDF 但未提取绘图页。")
        print("[提示] 可用 PyMuPDF / figure_compare.py 自行提取绘图页后，再粘入下列条目：")
        print(json.dumps([{"src": rel, "source": "user_upload",
                            "caption": f"用户上传：{label}（官方 PDF，待提取附图）"}],
                          ensure_ascii=False, indent=2))
        return
    doc = fitz.open(src)
    entries = []
    total = doc.page_count
    if pages:
        idxs = []
        for p in pages.split(","):
            p = p.strip()
            if p.isdigit():
                idxs.append(int(p) - 1)
    else:
        idxs = list(range(total))
    for i in idxs:
        if i < 0 or i >= total:
            print(f"[跳过] 页 {i+1} 超出范围(共 {total} 页)")
            continue
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
        out = os.path.join(figs_dir, f"{norm_label(label)}_upload_p{i+1}.png")
        pix.save(out)
        rel = os.path.relpath(out, out_dir).replace("\\", "/")
        entries.append({
            "src": rel,
            "source": "user_upload",
            "caption": f"用户上传：{label} 第 {i+1} 页（官方附图）",
        })
    doc.close()
    return entries


def main():
    ap = argparse.ArgumentParser(description="用户上传件落地助手")
    ap.add_argument("--file", required=True, help="用户上传的文件路径（图片或 PDF）")
    ap.add_argument("--label", required=True, help="专利号或名称，用于归一化文件名")
    ap.add_argument("--out-dir", required=True, help="工作目录（report_data.json 所在目录）")
    ap.add_argument("--pages", default="", help="PDF 时指定要提取的页（逗号分隔，如 11,12）；缺省提取全部")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"[错误] 找不到上传文件: {args.file}")
    os.makedirs(args.out_dir, exist_ok=True)
    ext = os.path.splitext(args.file)[1].lower()

    if ext in IMAGE_EXT:
        entries = ingest_image(args.file, args.out_dir, args.label)
    elif ext in PDF_EXT:
        entries = ingest_pdf(args.file, args.out_dir, args.label, args.pages)
    else:
        sys.exit(f"[错误] 不支持的文件类型: {ext}（仅支持图片/PNG/JPG 或 PDF）")

    print("\n=== 粘入 report_data.json 的 figure_compare 条目（source=user_upload）===")
    print(json.dumps(entries, ensure_ascii=False, indent=2))
    print(f"\n[完成] 共落地 {len(entries)} 张附图到 {os.path.join(args.out_dir, 'figs')}")


if __name__ == "__main__":
    main()
