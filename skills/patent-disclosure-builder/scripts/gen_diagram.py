#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_diagram.py — 依据技术方案描述，自动生成交底书用【架构图】或【流程图】示意图(PNG)。

用途:
    当发明人给不出图、或提供的图不符合要求时，由本脚本按结构化描述生成"示意图"，
    供发明人核对修改，再用 [[IMG:路径|图注]] 插进 build_docx 生成的 docx。
    ⚠️ 生成的是"AI 依据口述整理的示意图"，属发明人需核对的草图，不臆造技术细节。

用法:
    python gen_diagram.py spec.json out.png
    # spec.json 单张图；若传目录则批量：见 batch 模式说明。

spec.json 结构:
{
  "type": "arch" | "flow",          # 架构图 / 流程图
  "title": "外卖智能调度系统架构",   # 图内标题(可空)

  # ---- type=arch(架构图) ----
  "nodes": [
    {"id":"in","text":"订单接入模块\n(3秒滚动窗口)","col":0,"row":0,"accent":"blue"},
    {"id":"eng","text":"调度决策引擎","col":1,"row":1,"accent":"red"}
    # col 从0起(左→右列)，row 从0起(上→下行)；accent: blue/red/amber/green/gray(默认blue)
  ],
  "edges": [ {"from":"in","to":"eng","label":"订单流"} ],   # label 可空

  # ---- type=flow(流程图) ----
  "steps": [
    {"text":"攒批：3秒窗口聚合","kind":"start"},          # kind: start/process/decision/end
    {"text":"构建成本矩阵\nC=α·空驶+β·延误+γ·顺路","kind":"process","accent":"red"},
    {"text":"2秒内算完?","kind":"decision","branch":"否→分区贪心兜底"}  # decision 可带 branch 支路说明
  ]
}

设计:
- 纯 PIL 绘制，无 matplotlib 重依赖。中文字体多候选自适配(macOS/通用)。
- 输出 150dpi PNG，宽度自适应，build_docx 会等比缩放到正文宽内。
- 配色走浅底深框(适配浅色主题打印)，高亮节点用红/琥珀区分核心/兜底。
"""
import os, sys, json, math

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("需要 Pillow：pip install pillow", file=sys.stderr)
    sys.exit(1)

# ---- 中文字体多候选 ----
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
_FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.isfile(p)), None)


def font(sz):
    if _FONT_PATH:
        try:
            return ImageFont.truetype(_FONT_PATH, sz)
        except Exception:
            pass
    return ImageFont.load_default()


# 配色: (填充, 描边)
PALETTE = {
    "blue":  ("#EAF2FB", "#2F6FB0"),
    "red":   ("#FDECEC", "#C0504D"),
    "amber": ("#FFF6E5", "#E0A800"),
    "green": ("#E7F5E9", "#3C9D4E"),
    "gray":  ("#F0F0F0", "#888888"),
}
TEXT_COLOR = "#1A1A1A"
TITLE_COLOR = "#1A1A1A"
ARROW_COLOR = "#555555"


def _accent(name):
    return PALETTE.get(name or "blue", PALETTE["blue"])


def mtext(d, cx, cy, text, f, fill=TEXT_COLOR):
    """多行文字，以 (cx,cy) 为中心绘制。"""
    lines = text.split("\n")
    metas = []
    total_h = 0
    for ln in lines:
        tb = d.textbbox((0, 0), ln, font=f)
        h = tb[3] - tb[1]
        metas.append((ln, tb, h))
        total_h += h + 4
    y = cy - total_h / 2
    for ln, tb, h in metas:
        w = tb[2] - tb[0]
        d.text((cx - w / 2, y - tb[1]), ln, fill=fill, font=f)
        y += h + 4


def box(d, xy, text, f, accent="blue", radius=10):
    fill, outline = _accent(accent)
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=2)
    x0, y0, x1, y1 = xy
    mtext(d, (x0 + x1) / 2, (y0 + y1) / 2, text, f)


def diamond(d, cx, cy, hw, hh, text, f, accent="amber"):
    fill, outline = _accent(accent)
    d.polygon([(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)],
              fill=fill, outline=outline, width=2)
    mtext(d, cx, cy, text, f)


def arrow(d, p1, p2, color=ARROW_COLOR, label=None, f=None):
    d.line([p1, p2], fill=color, width=2)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    L = 10
    for da in (math.radians(150), math.radians(-150)):
        d.line([p2, (p2[0] + L * math.cos(ang + da), p2[1] + L * math.sin(ang + da))],
               fill=color, width=2)
    if label and f:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        tb = d.textbbox((0, 0), label, font=f)
        d.text((mx - (tb[2] - tb[0]) / 2, my - (tb[3] - tb[1]) - 6), label,
               fill="#777", font=f)


# ===================== 架构图 =====================
def render_arch(spec, out_path):
    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    title = spec.get("title", "")
    if not nodes:
        raise ValueError("arch 图需要 nodes")

    # 网格：按 col/row 分布
    cols = max(n.get("col", 0) for n in nodes) + 1
    rows = max(n.get("row", 0) for n in nodes) + 1

    BOX_W, BOX_H = 230, 92
    GAP_X, GAP_Y = 120, 70
    MARGIN = 50
    TITLE_H = 60 if title else 20

    W = MARGIN * 2 + cols * BOX_W + (cols - 1) * GAP_X
    H = MARGIN * 2 + TITLE_H + rows * BOX_H + (rows - 1) * GAP_Y

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    if title:
        mtext(d, W / 2, MARGIN + 16, title, font(30), fill=TITLE_COLOR)

    # 计算每个节点矩形
    rect = {}
    for n in nodes:
        col, row = n.get("col", 0), n.get("row", 0)
        x0 = MARGIN + col * (BOX_W + GAP_X)
        y0 = MARGIN + TITLE_H + row * (BOX_H + GAP_Y)
        rect[n["id"]] = (x0, y0, x0 + BOX_W, y0 + BOX_H)

    # 先画边(在框下面)
    fLabel = font(17)
    for e in edges:
        a, b = rect.get(e["from"]), rect.get(e["to"])
        if not a or not b:
            continue
        # 取两框中心，落点收缩到框边缘
        ca = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
        cb = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        p1 = _edge_point(a, ca, cb)
        p2 = _edge_point(b, cb, ca)
        arrow(d, p1, p2, label=e.get("label"), f=fLabel)

    # 再画框
    fBox = font(21)
    for n in nodes:
        box(d, rect[n["id"]], n.get("text", n["id"]), fBox, accent=n.get("accent", "blue"))

    img.save(out_path, dpi=(150, 150))
    return img.size


def _edge_point(rect, c_self, c_other):
    """从矩形中心朝对方方向，求与矩形边框的交点，作为箭头端点。"""
    x0, y0, x1, y1 = rect
    cx, cy = c_self
    dx, dy = c_other[0] - cx, c_other[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
    # 缩放系数，使点落在边框上
    sx = hw / abs(dx) if dx != 0 else float("inf")
    sy = hh / abs(dy) if dy != 0 else float("inf")
    s = min(sx, sy)
    return (cx + dx * s, cy + dy * s)


# ===================== 流程图 =====================
def render_flow(spec, out_path):
    steps = spec.get("steps", [])
    title = spec.get("title", "")
    if not steps:
        raise ValueError("flow 图需要 steps")

    BOX_W = 460
    MARGIN = 50
    TITLE_H = 60 if title else 20
    GAP_Y = 52

    # 预估高度
    def step_h(s):
        return 92

    W = BOX_W + MARGIN * 2 + 220  # 右侧留支路标注空间
    H = MARGIN * 2 + TITLE_H + sum(step_h(s) + GAP_Y for s in steps)

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    cx = MARGIN + BOX_W / 2
    if title:
        mtext(d, cx, MARGIN + 16, title, font(28), fill=TITLE_COLOR)

    fStep = font(21)
    fBranch = font(17)
    y = MARGIN + TITLE_H
    centers = []
    for s in steps:
        h = step_h(s)
        kind = s.get("kind", "process")
        accent = s.get("accent")
        if kind == "decision":
            hw, hh = 200, h / 2
            diamond(d, cx, y + h / 2, hw, hh, s.get("text", ""), fStep,
                    accent=accent or "amber")
            if s.get("branch"):
                d.text((cx + hw + 10, y + h / 2 - 10), s["branch"], fill="#C00000", font=fBranch)
        else:
            if kind == "start":
                acc = accent or "blue"
                box(d, (cx - BOX_W / 2, y, cx + BOX_W / 2, y + h), s.get("text", ""), fStep,
                    accent=acc, radius=40)  # 圆角胶囊表示起点
            elif kind == "end":
                acc = accent or "green"
                box(d, (cx - BOX_W / 2, y, cx + BOX_W / 2, y + h), s.get("text", ""), fStep,
                    accent=acc, radius=40)
            else:
                acc = accent or "blue"
                box(d, (cx - BOX_W / 2, y, cx + BOX_W / 2, y + h), s.get("text", ""), fStep,
                    accent=acc)
        centers.append((y, y + h))
        y += h + GAP_Y

    # 连线
    for i in range(len(centers) - 1):
        arrow(d, (cx, centers[i][1]), (cx, centers[i + 1][0]))

    img.save(out_path, dpi=(150, 150))
    return img.size


def render(spec, out_path):
    t = spec.get("type", "arch")
    if t == "arch":
        return render_arch(spec, out_path)
    elif t == "flow":
        return render_flow(spec, out_path)
    else:
        raise ValueError(f"未知图类型: {t}（应为 arch/flow）")


def main():
    if len(sys.argv) < 3:
        print("用法: python gen_diagram.py spec.json out.png")
        sys.exit(1)
    spec_path, out_path = sys.argv[1], sys.argv[2]
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    size = render(spec, out_path)
    print(f"OK -> {out_path}  {size}")


if __name__ == "__main__":
    main()
