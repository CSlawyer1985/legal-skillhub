#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
figure_compare.py —— G7 特征对照图自动生成工具
====================================================

本脚本把"特征比对与附图标引"规范（v1.0.3 新增 G7）从手工 Photoshop 升级为
一键自动生成。输入两张附图（涉案 + 对比）+ 标注 JSON（每特征的同色位置
+ 标签），自动：
  1. 左右并排合成"特征对照图"
  2. 相同特征用同色叠加色块 + 引线 + 特征号
  3. 顶部加标题、底部加色板图例
  4. 输出 PNG（默认）/ PDF

为什么需要它：
    手工贴色块、引线、编号极易错位、耗时；G7 要求"全案同色对应"，
    多张图工作量 × 特征数。脚本化后可批量、可重做、可追溯 JSON。

输入格式（标注 JSON）:
    {
      "target_label": "涉案专利 CN118658342A",
      "compare_label": "对比文件 US10234567B2",
      "features": [
        {
          "name": "散热器",
          "color": "#E63946",          // 必填，HEX 颜色
          "target_xy": [[120, 80]],     // 可选，多点；坐标 (x, y) 单位像素
          "compare_xy": [[100, 90]]
        },
        {
          "name": "压缩机",
          "color": "#1D6FB8",
          "target_xy": [[200, 150]],
          "compare_xy": [[180, 160]]
        }
      ]
    }

    - 颜色可填 HEX（#RRGGBB）或本技能预设的 7 种色板关键词（见 PALETTE）
    - target_xy / compare_xy 留空 = 该图不标注该特征（仅在一张图上出现）

使用前提：
    - 依赖 Python `Pillow`（PIL）。可选 `reportlab`（PDF 输出，不装也能输出 PNG）。
    - 附图来源：可用 `foreign_patent_fetch.py figures` 或 `cnipa_epub.py` 取。

子命令:
    single    1张图标注（如涉案专利附图，按色板打点）
    compare   2张图同色对比（核心：左涉案 + 右对比）
    from-json 通用入口（从 JSON 文件读所有配置）
"""
import argparse
import json
import os
import sys
from typing import List, Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
except ImportError:
    print("错误: 需要安装 Pillow。请运行: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# ── 预设色板（G7 规范，全案统一）─────────────────────────

PALETTE = {
    "红-散热器":   "#E63946",
    "蓝-压缩机":   "#1D6FB8",
    "绿-送风":     "#2A9D4A",
    "紫-旋转轴":   "#7B4FB5",
    "橙-分隔部":   "#E08A1E",
    "灰-安装面":   "#6B7280",
    "青-气流":     "#0FA3B1",
    "黑":         "#000000",
    "白":         "#FFFFFF",
}

DEFAULT_COLORS = [
    "#E63946", "#1D6FB8", "#2A9D4A", "#7B4FB5",
    "#E08A1E", "#6B7280", "#0FA3B1",
]


def resolve_color(c: str) -> str:
    """颜色归一化：HEX 直接返回；色板名称查表；否则按字面意思处理。"""
    s = c.strip()
    if s.startswith("#") and len(s) == 7:
        return s.upper()
    if s in PALETTE:
        return PALETTE[s]
    # 容错：不在色板里但已是 HEX
    return s.upper()


# ── 字体加载（中文友好）──────────────────────────────────

def _load_font(size: int = 20) -> ImageFont.FreeTypeFont:
    """跨平台找一个支持中文的字体；找不到就退回默认。"""
    candidates = [
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── 单图标注（无对比）────────────────────────────────────

def annotate_single(
    fig_path: str,
    features: List[dict],
    out_path: str,
    title: str = "",
    label: str = "",
) -> str:
    """在单张附图上叠加色块 + 引线 + 特征号。"""
    img = Image.open(fig_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(20)
    font_small = _load_font(14)

    for i, feat in enumerate(features, 1):
        color = resolve_color(feat.get("color", DEFAULT_COLORS[(i - 1) % len(DEFAULT_COLORS)]))
        name = feat.get("name", f"特征{i}")
        xys = feat.get("xy", [])
        for (x, y) in xys:
            _draw_marker(draw, x, y, color, str(i))
        # 标号引线（在最右下角点附近放标签）
        if xys:
            lx, ly = xys[-1]
            draw.text((lx + 16, ly - 10), f"{i}.{name}", fill=color, font=font_small)

    # 合成
    result = Image.alpha_composite(img, overlay)
    # 加标题 / 标签栏
    if title or label:
        result = _add_title_bar(result, title, label)

    # 保存
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    result.convert("RGB").save(out_path)
    return out_path


def _draw_marker(draw: ImageDraw.ImageDraw, x: int, y: int, color: str, label: str) -> None:
    """画一个圆形色块 + 引线（指向 (x, y)）+ 编号小圆。"""
    r = 18
    # 半透明填充圆
    fill_color = color + "B0"  # 加 70% alpha（HEX8）
    outline_color = color
    draw.ellipse([x - r, y - r, x + r, y + r], fill=fill_color, outline=outline_color, width=3)
    # 中心编号
    try:
        font = _load_font(16)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw / 2 - bbox[0], y - th / 2 - bbox[1]), label, fill="white", font=font)
    except Exception:
        pass


def _add_title_bar(img: Image.Image, title: str, label: str) -> Image.Image:
    """给图加顶部标题栏 + 标签栏。"""
    W, H = img.size
    bar_h = 60
    new_img = Image.new("RGBA", (W, H + bar_h), (255, 255, 255, 255))
    new_img.paste(img, (0, bar_h))
    d = ImageDraw.Draw(new_img)
    f = _load_font(20)
    if title:
        d.text((10, 8), title, fill="black", font=f)
    if label:
        d.text((10, 32), label, fill="#444", font=_load_font(16))
    return new_img


# ── 并排对比 ─────────────────────────────────────────────

def compare_two(
    target_path: str,
    compare_path: str,
    features: List[dict],
    out_path: str,
    target_label: str = "涉案专利",
    compare_label: str = "对比文件",
    title: str = "特征对照图",
) -> str:
    """生成左右并排的"特征对照图"，相同特征同色叠加。"""
    t_img = Image.open(target_path).convert("RGBA")
    c_img = Image.open(compare_path).convert("RGBA")

    # 缩放到相同高度
    target_h = 800
    t_img = _resize_to_height(t_img, target_h)
    c_img = _resize_to_height(c_img, target_h)

    # 对每张图叠加标注
    t_overlay = Image.new("RGBA", t_img.size, (0, 0, 0, 0))
    c_overlay = Image.new("RGBA", c_img.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(t_overlay)
    cd = ImageDraw.Draw(c_overlay)
    font_small = _load_font(14)
    font_legend = _load_font(18)

    legend_items = []  # [(idx, name, color)]

    for i, feat in enumerate(features, 1):
        color = resolve_color(feat.get("color", DEFAULT_COLORS[(i - 1) % len(DEFAULT_COLORS)]))
        name = feat.get("name", f"特征{i}")
        legend_items.append((i, name, color))

        # 涉案图
        for (x, y) in feat.get("target_xy", []):
            _draw_marker(td, x, y, color, str(i))
        # 对比图
        for (x, y) in feat.get("compare_xy", []):
            _draw_marker(cd, x, y, color, str(i))

    # 在两张图右下角放特征号小标签
    for i, feat in enumerate(features, 1):
        color = resolve_color(feat.get("color", DEFAULT_COLORS[(i - 1) % len(DEFAULT_COLORS)]))
        name = feat.get("name", f"特征{i}")
        if feat.get("target_xy"):
            x, y = feat["target_xy"][-1]
            td.text((x + 16, y - 10), f"{i}.{name}", fill=color, font=font_small)
        if feat.get("compare_xy"):
            x, y = feat["compare_xy"][-1]
            cd.text((x + 16, y - 10), f"{i}.{name}", fill=color, font=font_small)

    # 合成叠加
    t_comp = Image.alpha_composite(t_img, t_overlay)
    c_comp = Image.alpha_composite(c_img, c_overlay)

    # 并排：每张图加子标题栏
    label_h = 40
    t_labeled = _add_label_bar(t_comp, target_label)
    c_labeled = _add_label_bar(c_comp, compare_label)

    # 拼合
    W = t_labeled.width + c_labeled.width + 20
    H = max(t_labeled.height, c_labeled.height)
    combined = Image.new("RGB", (W, H), (255, 255, 255))
    combined.paste(t_labeled, (0, 0))
    combined.paste(c_labeled, (t_labeled.width + 20, 0))

    # 加总标题 + 图例
    final = _add_combined_title_and_legend(combined, title, legend_items)

    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    final.save(out_path)
    return out_path


def _resize_to_height(img: Image.Image, h: int) -> Image.Image:
    """按高度等比缩放。"""
    w, oh = img.size
    if oh == h:
        return img
    new_w = int(w * h / oh)
    return img.resize((new_w, h), Image.LANCZOS)


def _add_label_bar(img: Image.Image, label: str) -> Image.Image:
    """给单图加底部标签栏。"""
    W, H = img.size
    bar_h = 40
    new_img = Image.new("RGBA", (W, H + bar_h), (240, 240, 240, 255))
    new_img.paste(img, (0, 0))
    d = ImageDraw.Draw(new_img)
    f = _load_font(18)
    # 居中
    try:
        bbox = d.textbbox((0, 0), label, font=f)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = len(label) * 10
    d.text(((W - tw) / 2, H + 8), label, fill="black", font=f)
    return new_img


def _add_combined_title_and_legend(
    img: Image.Image, title: str, legend: List[Tuple[int, str, str]]
) -> Image.Image:
    """给并排图加顶部总标题 + 底部色板图例。"""
    W, H = img.size
    title_h = 50
    legend_h = max(50, 20 + 24 * ((len(legend) + 5) // 6))  # 6 个一行
    new_img = Image.new("RGB", (W, H + title_h + legend_h), (255, 255, 255))
    new_img.paste(img, (0, title_h))
    d = ImageDraw.Draw(new_img)
    f_title = _load_font(24)
    f_legend = _load_font(16)
    d.text((20, 12), title, fill="black", font=f_title)

    # 图例（6 个一行）
    x0, y0 = 20, H + title_h + 10
    col_w = (W - 40) // 6
    for i, (idx, name, color) in enumerate(legend):
        col = i % 6
        row = i // 6
        cx = x0 + col * col_w
        cy = y0 + row * 24
        # 色块
        d.rectangle([cx, cy, cx + 18, cy + 18], fill=color, outline="black")
        # 编号 + 名称
        d.text((cx + 24, cy), f"{idx}.{name}", fill="black", font=f_legend)
    return new_img


# ── 子命令入口 ───────────────────────────────────────────


def cmd_single(args) -> int:
    features = json.loads(args.annotations) if args.annotations else []
    out = annotate_single(args.fig, features, args.out, args.title or "", args.label or "")
    print(f"[OK] 标注图: {out}")
    return 0


def cmd_compare(args) -> int:
    features = json.loads(args.annotations) if args.annotations else []
    out = compare_two(
        args.target, args.compare, features, args.out,
        target_label=args.target_label,
        compare_label=args.compare_label,
        title=args.title or "特征对照图",
    )
    print(f"[OK] 对照图: {out}")
    return 0


def cmd_from_json(args) -> int:
    """从 JSON 文件一次性读全部配置。"""
    with open(args.json, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    target = cfg.get("target")
    compare = cfg.get("compare")
    out = cfg.get("out", "feature_comparison.png")
    if target and compare:
        out_path = compare_two(
            target, compare, cfg.get("features", []), out,
            target_label=cfg.get("target_label", "涉案专利"),
            compare_label=cfg.get("compare_label", "对比文件"),
            title=cfg.get("title", "特征对照图"),
        )
    elif target:
        out_path = annotate_single(
            target, cfg.get("features", []), out,
            title=cfg.get("title", ""), label=cfg.get("target_label", ""),
        )
    else:
        print("错误: JSON 至少需含 target 字段", file=sys.stderr)
        return 1
    print(f"[OK] 生成: {out_path}")
    return 0


# ── CLI 入口 ────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(
        description="G7 特征对照图自动生成（涉案图 vs 对比文件附图，同色叠加）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
色板（与 references/特征比对与附图标引.md 一致）:
  红-散热器   #E63946    蓝-压缩机   #1D6FB8
  绿-送风     #2A9D4A    紫-旋转轴   #7B4FB5
  橙-分隔部   #E08A1E    灰-安装面   #6B7280
  青-气流     #0FA3B1

示例 (命令行内联 JSON):
  python figure_compare.py compare \\
      --target ./target/fig-002.png \\
      --compare ./compare/fig-005.png \\
      --annotations '[
        {"name":"散热器","color":"红-散热器","target_xy":[[120,80]],"compare_xy":[[100,90]]},
        {"name":"压缩机","color":"蓝-压缩机","target_xy":[[200,150]],"compare_xy":[[180,160]]}
      ]' \\
      --target-label "涉案专利 CN118658342A" \\
      --compare-label "对比文件 US10234567B2" \\
      --out ./compare/feature_compare.png

示例 (JSON 文件):
  python figure_compare.py from-json config.json

config.json 格式见脚本 docstring 顶部。
        """,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_s = sub.add_parser("single", help="单图标注（无对比）")
    p_s.add_argument("fig", help="附图路径 PNG/JPG")
    p_s.add_argument("--out", default="annotated.png", help="输出路径")
    p_s.add_argument("--annotations", help="标注 JSON 字符串（每项含 name/color/xy）")
    p_s.add_argument("--title", default="", help="总标题")
    p_s.add_argument("--label", default="", help="图标签")

    p_c = sub.add_parser("compare", help="左右并排同色对比（核心命令）")
    p_c.add_argument("--target", required=True, help="涉案专利附图路径")
    p_c.add_argument("--compare", required=True, help="对比文件附图路径")
    p_c.add_argument("--out", default="feature_comparison.png", help="输出路径")
    p_c.add_argument("--annotations", help="标注 JSON 字符串（每项含 name/color/target_xy/compare_xy）")
    p_c.add_argument("--target-label", default="涉案专利", help="左图标签")
    p_c.add_argument("--compare-label", default="对比文件", help="右图标签")
    p_c.add_argument("--title", default="特征对照图", help="总标题")

    p_j = sub.add_parser("from-json", help="从 JSON 文件读全部配置")
    p_j.add_argument("json", help="配置文件路径")

    args = ap.parse_args()
    if args.cmd == "single":
        return cmd_single(args)
    elif args.cmd == "compare":
        return cmd_compare(args)
    elif args.cmd == "from-json":
        return cmd_from_json(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
