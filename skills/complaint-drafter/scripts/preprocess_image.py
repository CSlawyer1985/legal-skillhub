#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preprocess_image.py — 起诉状图片预处理（可选步骤）

作用：把用户上传的起诉状照片/扫描件归一化，提升 Read 工具的视觉识别（OCR）准确率。
- 按 EXIF 自动校正方向（手机竖拍照片常见）
- 缩放至最长边 <= max_size，保留文字清晰度又不至于过大
- 统一另存为 PNG（无损、便于多模态模型读取）

用法：
    python preprocess_image.py <图片1> [图片2 ...] [--outdir DIR] [--max-size 2200]
输出：打印一行 JSON，列出归一化后的图片绝对路径；失败项单独列出。
"""
import sys
import os
import json
from PIL import Image, ImageOps

MAX_SIZE = 2200


def normalize_one(src, outdir, max_size):
    try:
        img = Image.open(src)
        # 按 EXIF 方向校正（手机照片常见横竖颠倒）
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        # 转 RGB（避免 RGBA/P 调色板导致的读取异常）
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / float(max(w, h))
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        base = os.path.splitext(os.path.basename(src))[0]
        # 文件名安全化
        safe = "".join(ch if ch not in '\\/:*?"<>|\t' else "_" for ch in base).strip()
        out = os.path.join(outdir, safe + ".png")
        img.save(out, "PNG")
        return {"src": src, "out": out, "ok": True}
    except Exception as e:
        return {"src": src, "out": None, "ok": False, "error": str(e)}


def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "未提供图片路径"}))
        sys.exit(1)
    outdir = "."
    max_size = MAX_SIZE
    imgs = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--outdir":
            outdir = args[i + 1]
            i += 2
            continue
        if a == "--max-size":
            max_size = int(args[i + 1])
            i += 2
            continue
        imgs.append(a)
        i += 1

    os.makedirs(outdir, exist_ok=True)
    results = [normalize_one(p, outdir, max_size) for p in imgs]
    print(json.dumps({"normalized": [r["out"] for r in results if r["ok"]],
                      "failed": [r for r in results if not r["ok"]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
