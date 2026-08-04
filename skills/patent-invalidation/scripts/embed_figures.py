#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
embed_figures.py — 将 report_data.json 中的本地附图路径内嵌为 base64 data-URI，
使生成的 HTML 自包含、可独立分享（无需依赖相对路径文件）。

适用场景（M1/M3/M11「可选应对」分支③ SVG 重构降级 的核心一步）：
  - 目标专利 / 对比文件官方 PDF 不可得，已用 SVG 框图重构并存于 figs/；
  - 用户上传的附图、或官方下载的 PNG，希望随 HTML 一并归档；
  - 任何希望"单文件 HTML"的场景。

用法：
  python scripts/embed_figures.py --data report_data.json \
      [--out report_data_embedded.json] [--inplace] [--base ./]

说明：
  - 仅处理形如 相对路径 的 src（不含 "data:" 前缀、不以 http 开头）；
  - 路径相对于 --base（缺省为 report_data.json 所在目录）解析；
  - MIME 由扩展名推断（svg→image/svg+xml，png/jpg→对应类型，其余→application/octet-stream）；
  - 已为 data-URI / 远程 URL 的 src 原样保留，不重复处理。
"""
import argparse
import base64
import json
import os
import sys

MIME = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}


def to_data_uri(path, base):
    full = path if os.path.isabs(path) else os.path.join(base, path)
    if not os.path.isfile(full):
        print(f"[跳过] 找不到文件: {full}")
        return None
    ext = os.path.splitext(full)[1].lower()
    mime = MIME.get(ext, "application/octet-stream")
    with open(full, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def walk(obj, base, stats):
    """递归遍历，将所有含 'src' 的字典的本地路径替换为 data-URI。"""
    if isinstance(obj, dict):
        if "src" in obj and isinstance(obj["src"], str):
            s = obj["src"]
            if s and not s.startswith("data:") and not s.startswith("http"):
                uri = to_data_uri(s, base)
                if uri:
                    obj["src"] = uri
                    stats["inlined"] += 1
                else:
                    stats["missing"] += 1
        for v in obj.values():
            walk(v, base, stats)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, base, stats)


def main():
    ap = argparse.ArgumentParser(description="附图内嵌为 data-URI（自包含 HTML）")
    ap.add_argument("--data", required=True, help="report_data.json 路径")
    ap.add_argument("--out", default=None, help="输出 JSON 路径；缺省为 <data>_embedded.json")
    ap.add_argument("--inplace", action="store_true", help="原地覆盖原文件")
    ap.add_argument("--base", default=None, help="附图路径基准目录；缺省为 data 所在目录")
    args = ap.parse_args()

    if not os.path.isfile(args.data):
        sys.exit(f"[错误] 找不到数据文件: {args.data}")
    base = args.base or os.path.dirname(os.path.abspath(args.data))
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {"inlined": 0, "missing": 0}
    walk(data, base, stats)

    if args.inplace:
        out = args.data
    else:
        out = args.out or (os.path.splitext(args.data)[0] + "_embedded.json")
    out = os.path.abspath(out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[完成] 内嵌 {stats['inlined']} 张附图；缺失 {stats['missing']} 张")
    print(f"[输出] {out}")
    if stats["inlined"]:
        print("[提示] 用 make_report_html.py --data 该文件生成的 HTML 即为自包含单文件。")


if __name__ == "__main__":
    main()
