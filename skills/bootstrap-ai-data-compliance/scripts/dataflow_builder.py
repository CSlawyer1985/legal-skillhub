#!/usr/bin/env python3
"""Data flow 渲染器：场景视图 JSON → 自包含 HTML（diagram-design Data flow 类型）。

依据 vendor/diagram-design/references/type-data-flow.md 的确定性公式实现：
- 角色泳道 × 阶段列参数化网格（≤4 泳道、≤6 阶段、≤12 流）
- 唯一 focal（1 个 focal 阶段 + 1 个 focal 节点 + 1 条 accent 流）
- 4px 网格、同输入必同输出、fail-fast 校验

用法：
    python3 dataflow_builder.py <view.json> <output.html>
"""
import json
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Token（默认皮肤，style-guide.md；dark 模式翻转见 §6）
# --------------------------------------------------------------------------
TOKENS_LIGHT = {
    "paper": "#f5f5f5", "ink": "#2d3142", "muted": "#4f5d75", "soft": "#7a8399",
    "accent": "#eb6c36", "accent_tint": "rgba(235,108,54,0.08)", "link": "#2e5aa8",
}
TOKENS_DARK = {
    "paper": "#2d3142", "ink": "#f5f5f5", "muted": "#bfc0c0", "soft": "#8e98ac",
    "accent": "#f08a59", "accent_tint": "rgba(240,138,89,0.10)", "link": "#6a95d8",
}
CHIP_COLORS = {"WB": "#6e6479", "DB": "#5e7a9b", "TB": "#b8915a", "FL": "#9c6b50", "LS": "#4a7c59"}
ARROW_STYLES = {
    "muted":  {"stroke": None, "width": "1.0", "dash": None, "marker": "arr-muted"},
    "trigger": {"stroke": None, "width": "1.0", "dash": "4,3", "marker": "arr-muted"},
    "accent": {"stroke": None, "width": "1.2", "dash": None, "marker": "arr-accent"},
    "link":   {"stroke": None, "width": "1.0", "dash": None, "marker": "arr-link"},
}
FLOW_LEGEND = [
    ("muted", "标准移交"),
    ("trigger", "治理/审核触发"),
    ("accent", "关键移交"),
    ("link", "对外交付"),
]

# 布局常量（§2，不可变）
LABEL_COL_W = 140
STEP_SLOT_W = 112
RIGHT_PAD = 28
HEADER_H = 36
LANE_H = 80
LEGEND_H_PLAIN = 80
LEGEND_H_COLOR = 100


class DataFlowError(Exception):
    pass


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataFlowError(f"视图 JSON 读取失败：{exc}") from exc


def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def validate(view: dict) -> None:
    lanes, steps = view.get("lanes", []), view.get("steps", [])
    nodes, arrows = view.get("nodes", []), view.get("arrows", [])
    if not (1 <= len(lanes) <= 4):
        raise DataFlowError(f"泳道数量必须为 1..4，当前 {len(lanes)}")
    if not (1 <= len(steps) <= 6):
        raise DataFlowError(f"阶段数量必须为 1..6，当前 {len(steps)}")
    if not lanes or not steps:
        raise DataFlowError("视图缺少 lanes 或 steps")
    lane_keys = {l["key"] for l in lanes}
    guide = "参考模板：assets/dfd-scenes/retail-ecommerce-dataflow.json"
    n_focal_step = sum(1 for s in steps if s.get("focal"))
    if n_focal_step != 1:
        raise DataFlowError(f"focal 阶段必须恰好 1 个，当前 {n_focal_step}（在步骤 label 上加 \"focal\": true）。{guide}")
    n_focal_node = sum(1 for n in nodes if n.get("focal"))
    if n_focal_node != 1:
        raise DataFlowError(f"focal 节点必须恰好 1 个，当前 {n_focal_node}（在节点上加 \"focal\": true）。{guide}")
    n_accent = sum(1 for a in arrows if a.get("style") == "accent")
    if n_accent != 1:
        raise DataFlowError(f"accent（关键移交）流必须恰好 1 条，当前 {n_accent}。{guide}")
    if len(arrows) > 12:
        raise DataFlowError(f"流数量超过预算（≤12），当前 {len(arrows)}。{guide}")
    for n in nodes:
        if n["lane"] not in lane_keys:
            raise DataFlowError(f"节点 {n.get('title')} 引用了不存在的泳道 {n['lane']}；可用泳道：{list(lane_keys)}。{guide}")
        if not (0 <= n["step"] < len(steps)):
            raise DataFlowError(f"节点 {n.get('title')} 的阶段越界：{n['step']}（0..{len(steps)-1}）。{guide}")
        for side in ("in", "out"):
            code = n.get("chips", {}).get(side)
            if code and code not in CHIP_COLORS:
                raise DataFlowError(f"节点 {n.get('title')} 的数据类型码非法：{code}")
    for a in arrows:
        for end in ("from", "to"):
            ref = a[end]
            if ref["lane"] not in lane_keys or not (0 <= ref["step"] < len(steps)):
                raise DataFlowError(f"流 {a} 引用了不存在的节点坐标")
        if a.get("style") not in ARROW_STYLES:
            raise DataFlowError(f"流的样式非法：{a.get('style')}")


def render(view: dict) -> str:
    """返回自包含 HTML。"""
    lanes, steps = view["lanes"], view["steps"]
    nodes, arrows = view.get("nodes", []), view.get("arrows", [])
    dark = bool(view.get("dark"))
    t = TOKENS_DARK if dark else TOKENS_LIGHT
    slug = view.get("slug", "data-flow")

    n_steps, n_lanes = len(steps), len(lanes)
    has_color = any(n.get("color") for n in nodes)
    legend_h = LEGEND_H_COLOR if has_color else LEGEND_H_PLAIN
    viewbox_w = LABEL_COL_W + n_steps * STEP_SLOT_W + RIGHT_PAD
    viewbox_h = HEADER_H + n_lanes * LANE_H + legend_h
    legend_top = HEADER_H + n_lanes * LANE_H

    def step_cx(j):
        return LABEL_COL_W + j * STEP_SLOT_W + STEP_SLOT_W // 2

    def node_rect(lane_idx, step_idx):
        x = step_cx(step_idx) - 50
        y = HEADER_H + lane_idx * LANE_H + 8
        return x, y

    idx_of = {l["key"]: i for i, l in enumerate(lanes)}
    node_map = {}  # (lane, step) -> node dict（校验唯一）
    for n in nodes:
        key = (n["lane"], n["step"])
        if key in node_map:
            raise DataFlowError(f"泳道×阶段格重复：{key}")
        node_map[key] = n
    n_lanes_total = len(lanes)

    def node_occupies(lane_idx, step_idx):
        """该泳道×阶段格是否被节点占用（路由避让用）。"""
        return (lanes[lane_idx]["key"], step_idx) in node_map

    def route_path(fi, fj, ti, tj):
        """正交路由：优先直线/垂直，路径上有节点时绕行，避免箭头贯穿节点。

        四种情况：
        1) 同泳道（fi==ti）：水平直线；中间列有节点 → 绕行 lane 外侧（上优先，下备选）
        2) 同阶段跨泳道（fj==tj）：垂直直线；中间泳道有节点 → 走列间隙（cx+56）
        3) 跨泳道跨阶段：elbow；水平段或垂直段被堵 → 组合绕行（lane 外水平 + 列间隙垂直）
        4) 反向（tj<fj / ti<fi）对称处理
        """
        fx, fy = node_rect(fi, fj)
        tx, ty = node_rect(ti, tj)
        if fi == ti:
            mid = HEADER_H + fi * LANE_H + LANE_H // 2
            between = list(range(min(fj, tj) + 1, max(fj, tj)))
            if not between or not any(node_occupies(fi, j) for j in between):
                # 直线（无中间节点）
                if tj > fj:
                    return f"M {fx+100} {mid} H {tx}"
                return f"M {fx} {mid} H {tx+100}"
            # 中间列有节点：绕行 lane 外侧（优先上方，其次下方；全堵退化节点上方空隙）
            cols = list(range(min(fj, tj), max(fj, tj) + 1))
            y0 = None
            if fi - 1 >= 0 and not any(node_occupies(fi - 1, j) for j in cols):
                y0 = HEADER_H + fi * LANE_H - 8
            elif fi + 1 < n_lanes_total and not any(node_occupies(fi + 1, j) for j in cols):
                y0 = HEADER_H + (fi + 1) * LANE_H + 8
            else:
                y0 = HEADER_H + fi * LANE_H + 4
            # 垂直段落点用目标节点左/右缘（tx / tx+100），不能落列中心——会穿过目标节点
            if tj > fj:
                return f"M {fx+100} {mid} V {y0} H {tx} V {mid}"
            return f"M {fx} {mid} V {y0} H {tx+100} V {mid}"
        if fj == tj:
            cx = step_cx(fj)
            between_lanes = list(range(min(fi, ti) + 1, max(fi, ti)))
            if not between_lanes or not any(node_occupies(l, fj) for l in between_lanes):
                # 垂直直线（相邻泳道或中间泳道无节点）
                if ti > fi:
                    return f"M {cx} {fy+64} V {ty}"
                return f"M {cx} {fy} V {ty+64}"
            # 中间泳道有节点：走列间隙（cx+56 恒在节点矩形外，节点宽 100 居中于列中心）
            gx = cx + 56
            if ti > fi:
                return f"M {cx} {fy+64} H {gx} V {ty-4} H {cx} V {ty}"
            return f"M {cx} {fy} H {gx} V {ty+68} H {cx} V {ty+64}"
        # 跨泳道跨阶段：elbow（水平段在起点泳道中线）
        mid = HEADER_H + fi * LANE_H + LANE_H // 2
        cx_to = step_cx(tj)
        hcols = list(range(min(fj, tj), max(fj, tj) + 1))
        vlanes = list(range(min(fi, ti) + 1, max(fi, ti)))
        h_blocked = any(node_occupies(fi, j) for j in hcols if j != fj)
        v_blocked = any(node_occupies(l, tj) for l in vlanes)
        if not h_blocked and not v_blocked:
            if ti > fi:
                return f"M {fx+100} {mid} H {cx_to-8} Q {cx_to} {mid} {cx_to} {mid+8} V {ty}"
            return f"M {fx+100} {mid} H {cx_to-8} Q {cx_to} {mid} {cx_to} {mid-8} V {ty+64}"
        # 组合绕行：水平段走 lane 外侧（选无节点方向），垂直段走目标列间隙
        y0 = None
        if fi - 1 >= 0 and not any(node_occupies(fi - 1, j) for j in hcols):
            y0 = HEADER_H + fi * LANE_H - 8
        elif fi + 1 < n_lanes_total and not any(node_occupies(fi + 1, j) for j in hcols):
            y0 = HEADER_H + (fi + 1) * LANE_H + 8
        else:
            y0 = HEADER_H + fi * LANE_H + 4
        gx = cx_to + 56
        if ti > fi:
            return f"M {fx+100} {mid} V {y0} H {gx} V {ty-4} H {cx_to} V {ty}"
        return f"M {fx+100} {mid} V {y0} H {gx} V {ty+68} H {cx_to} V {ty+64}"

    ink_rgb = t["ink"][1:]  # hex without #
    def ink_alpha(a):
        return f"rgba({int(ink_rgb[0:2],16)},{int(ink_rgb[2:4],16)},{int(ink_rgb[4:6],16)},{a})"

    # ---------------- 线段 ---------------
    svg_arrows = []
    for a in arrows:
        style = ARROW_STYLES[a["style"]]
        stroke = style["stroke"] or t["muted"] if a["style"] in ("muted", "trigger") else (
            t["accent"] if a["style"] == "accent" else t["link"])
        fi, ti = idx_of[a["from"]["lane"]], idx_of[a["to"]["lane"]]
        fj, tj = a["from"]["step"], a["to"]["step"]
        fx, fy = node_rect(fi, fj)
        tx, ty = node_rect(ti, tj)
        attrs = f'fill="none" stroke="{stroke}"'
        if style["width"] != "1.0":
            attrs += f' stroke-width="{style["width"]}"'
        if style["dash"]:
            attrs += f' stroke-dasharray="{style["dash"]}"'
        attrs += f' marker-end="url(#{style["marker"]})"'

        d = route_path(fi, fj, ti, tj)
        svg_arrows.append(f'<path d="{d}" {attrs}/>')

        # focal 标签（唯一 accent）：放在流线上的空隙处，不压节点
        #  - 同泳道/elbow：水平段中点上方；水平段所在列无节点时才安全（路由已避让）
        #  - 垂直流（fj==tj）：起终点节点之间的空隙中点
        if a["style"] == "accent":
            label = a.get("label") or "关键移交"
            label_w = max(48, len(label) * 8 + 16)  # 8px 等宽字体，中文约 8px/字
            if fj == tj:
                # 垂直流：标签在起终点节点之间的空隙
                mid_x = step_cx(fj)
                if ti > fi:
                    gap_y = (fy + 64 + ty) // 2
                else:
                    gap_y = (fy + ty + 64) // 2
                label_y = gap_y - 6
            else:
                # 水平流/elbow：标签在水平段上方 20px（所在列无节点，路由已避让）
                mid = HEADER_H + fi * LANE_H + LANE_H // 2
                if fi == ti:
                    mid_x = (fx + 100 + tx) // 2 if tj > fj else (fx + tx + 100) // 2
                else:
                    mid_x = (fx + 100 + step_cx(tj) - 8) // 2
                label_y = mid - 20
            svg_arrows.append(
                f'<rect x="{mid_x - label_w//2}" y="{label_y}" width="{label_w}" height="12" rx="2" fill="{t["paper"]}"/>'
                f'<text x="{mid_x}" y="{label_y+9}" fill="{t["accent"]}" font-size="8" '
                f'font-family="\'Geist Mono\', monospace" text-anchor="middle" '
                f'letter-spacing="0.06em">{label}</text>'
            )

    # ---------------- 节点 ---------------
    svg_nodes = []
    for n in nodes:
        x, y = node_rect(idx_of[n["lane"]], n["step"])
        focal = bool(n.get("focal"))
        color = n.get("color")
        if focal:
            fill, stroke, sw = t["accent_tint"], t["accent"], ' stroke-width="1.2"'
            chip_fill, chip_text = _hex_rgba(t["accent"], 0.20), t["accent"]
            title_fill = t["ink"]
        elif color:
            fill, stroke, sw = _hex_rgba(color, 0.06), _hex_rgba(color, 0.35), ""
            chip_fill, chip_text = _hex_rgba(color, 0.18), color
            title_fill = color
        else:
            fill, stroke, sw = t["paper"], ink_alpha(0.25), ""
            chip_fill, chip_text = ink_alpha(0.12), t["ink"]
            title_fill = t["ink"]
        cx = x + 50
        chips = n.get("chips", {})
        chip_in = f'<rect x="{x+4}" y="{y+54}" width="16" height="8" rx="3" fill="{CHIP_COLORS[chips["in"]]}"/><text x="{x+12}" y="{y+60}" class="chip-text">{chips["in"]}</text>' if chips.get("in") else ""
        chip_out = f'<rect x="{x+80}" y="{y+54}" width="16" height="8" rx="3" fill="{CHIP_COLORS[chips["out"]]}"/><text x="{x+88}" y="{y+60}" class="chip-text">{chips["out"]}</text>' if chips.get("out") else ""
        if focal:
            role_attr = 'class="role-text focal-text"'
        elif color:
            role_attr = f'class="role-text" fill="{chip_text}"'
        else:
            role_attr = 'class="role-text"'
        title_attr = f' fill="{title_fill}"' if title_fill != t["ink"] else ""
        svg_nodes.append(
            f'<rect x="{x}" y="{y}" width="100" height="64" rx="6" fill="{fill}" stroke="{stroke}"{sw}/>'
            f'<rect x="{x+4}" y="{y+4}" width="18" height="10" rx="3" fill="{chip_fill}"/><text x="{x+13}" y="{y+9}" {role_attr}>{n["lane"]}</text>'
            f'<text x="{cx}" y="{y+23}" class="node-title"{title_attr}>{n["title"]}</text>'
            f'<text x="{cx}" y="{y+35}" class="node-sub">{n.get("sub", "")}</text>'
            f'<text x="{cx}" y="{y+47}" class="node-tool">{n.get("tool", "")}</text>'
            f'{chip_in}{chip_out}'
        )

    # ---------------- Header / 泳道 ---------------
    step_chips = []
    for j, s in enumerate(steps):
        cx = step_cx(j)
        if s.get("focal"):
            fill, txt_cls = f"rgba({int(t['accent'][1:3],16)},{int(t['accent'][3:5],16)},{int(t['accent'][5:7],16)},0.20)", 'class="step-number focal-text"'
            lab_cls = 'class="step-label focal-text"'
        else:
            fill, txt_cls, lab_cls = ink_alpha(0.12), 'class="step-number"', 'class="step-label"'
        step_chips.append(
            f'<rect x="{cx-16}" y="6" width="32" height="16" rx="8" fill="{fill}"/>'
            f'<text x="{cx}" y="14" {txt_cls}>{s["number"]}</text>'
            f'<text x="{cx}" y="29" {lab_cls}>{s["label"]}</text>'
        )
    lane_labels = []
    for k, l in enumerate(lanes):
        mid = HEADER_H + k * LANE_H + LANE_H // 2
        lines = l["name"] if isinstance(l["name"], list) else [l["name"]]
        for i, line in enumerate(lines):
            lane_labels.append(f'<text x="{LABEL_COL_W//2}" y="{mid - 4 + i*12}" class="lane-label">{line}</text>')

    # ---------------- 图例 ---------------
    rows = [legend_top + 16, legend_top + 37, legend_top + 58]
    if has_color:
        rows.append(legend_top + 79)
    def legend_row_label(y, text):
        return f'<text x="{LABEL_COL_W+24}" y="{y}" class="legend-label">{text}</text>'
    legend = [legend_row_label(rows[0], "STEPS")]
    for j, s in enumerate(steps):
        cx = step_cx(j)
        if s.get("focal"):
            fill, num_cls = f"rgba({int(t['accent'][1:3],16)},{int(t['accent'][3:5],16)},{int(t['accent'][5:7],16)},0.20)", 'class="step-number focal-text"'
        else:
            fill, num_cls = ink_alpha(0.12), 'class="step-number"'
        legend.append(f'<rect x="{cx-16}" y="{rows[0]-9}" width="24" height="12" rx="6" fill="{fill}"/><text x="{cx-4}" y="{rows[0]-1}" {num_cls}>{s["number"]}</text><text x="{cx+16}" y="{rows[0]}" class="legend-text">{s["label"]}</text>')

    # 文字基线上移 2px（视觉中心对齐 8px 高色块；STEPS 行 12px chip 保持原基准）
    label_off = 2
    used_chips = sorted({c for n in nodes for c in n.get("chips", {}).values()})
    legend.append(legend_row_label(rows[1] - label_off, "DATA TYPE"))
    chip_x = 180
    for code in used_chips:
        legend.append(f'<rect x="{chip_x}" y="{rows[1]-8}" width="16" height="8" rx="3" fill="{CHIP_COLORS[code]}"/><text x="{chip_x+8}" y="{rows[1]-2}" class="chip-text">{code}</text><text x="{chip_x+22}" y="{rows[1]-label_off}" class="legend-text">{CHIP_MEAN[code]}</text>')
        chip_x += 84
    legend.append(f'<text x="{chip_x+22}" y="{rows[1]-label_off}" class="legend-text">left chip = input · right chip = output</text>')

    if has_color:
        legend.append(legend_row_label(rows[2] - label_off, "CONCERN"))
        cx0 = 180
        colors_seen = []
        for n in nodes:
            c = n.get("color")
            if c and c not in colors_seen:
                colors_seen.append(c)
                legend.append(f'<rect x="{cx0}" y="{rows[2]-8}" width="16" height="8" rx="3" fill="{c}"/><text x="{cx0+24}" y="{rows[2]-label_off}" class="legend-text">{n.get("title", "")}</text>')
                cx0 += 132
        legend.append(f'<rect x="{cx0}" y="{rows[2]-8}" width="16" height="8" rx="3" fill="{t["accent"]}"/><text x="{cx0+24}" y="{rows[2]-label_off}" class="legend-text focal-text">关键移交</text>')

    flow_row = rows[3] if has_color else rows[2]
    legend.append(legend_row_label(flow_row - label_off, "FLOW"))
    seg_x = 180
    for style_key, label in FLOW_LEGEND:
        st = ARROW_STYLES[style_key]
        stroke = t["muted"] if style_key in ("muted", "trigger") else (t["accent"] if style_key == "accent" else t["link"])
        extra = f' stroke-width="{st["width"]}"' if st["width"] != "1.0" else ""
        dash = f' stroke-dasharray="{st["dash"]}"' if st["dash"] else ""
        legend.append(f'<line x1="{seg_x}" y1="{flow_row-3}" x2="{seg_x+24}" y2="{flow_row-3}" stroke="{stroke}"{dash}{extra} marker-end="url(#{st["marker"]})"/><text x="{seg_x+32}" y="{flow_row-label_off}" class="legend-text">{label}</text>')
        seg_x += 176

    # ---------------- 页面 ---------------
    title_text = view.get("title", "数据流向图")
    desc_text = view.get("desc", "")
    eyebrow = view.get("eyebrow", "DATA FLOW · DIAGRAM DESIGN")
    arrows_defs = []
    for key, color in (("muted", t["muted"]), ("accent", t["accent"]), ("link", t["link"])):
        arrows_defs.append(f'<marker id="arr-{key}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="{color}"/></marker>')
    lane_tint = "".join(
        f'<rect x="0" y="{HEADER_H + k * LANE_H}" width="{viewbox_w}" height="{LANE_H}" fill="{ink_alpha(0.018)}"/>'
        for k in range(n_lanes) if k % 2 == 0
    )
    dividers = "".join(
        f'<line x1="0" y1="{HEADER_H + k * LANE_H}" x2="{viewbox_w}" y2="{HEADER_H + k * LANE_H}" stroke="{ink_alpha(0.12)}" stroke-width="0.8"/>'
        for k in range(n_lanes + 1)
    )
    dividers += f'<line x1="{LABEL_COL_W}" y1="{HEADER_H}" x2="{LABEL_COL_W}" y2="{legend_top}" stroke="{ink_alpha(0.12)}" stroke-width="0.8"/>'

    css_sans = "'Geist', 'PingFang SC', system-ui, sans-serif"
    css_serif = "'Instrument Serif', 'Songti SC', serif"
    css_mono = "'Geist Mono', 'PingFang SC', ui-monospace, monospace"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_text}</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&amp;family=Geist:wght@400;500;600&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --paper: {t["paper"]}; --paper-2: {"#393e53" if dark else "#ececec"}; --ink: {t["ink"]}; --muted: {t["muted"]};
      --soft: {t["soft"]}; --rule: {ink_alpha(0.12)}; --accent: {t["accent"]};
      --accent-tint: {t["accent_tint"]}; --link: {t["link"]};
      --sans: {css_sans}; --serif: {css_serif}; --mono: {css_mono};
    }}
    body {{ min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 3rem 2rem; background: var(--paper); color: var(--ink); font-family: var(--sans); }}
    .frame {{ width: 100%; max-width: 1400px; }}
    .eyebrow {{ margin-bottom: 0.5rem; color: var(--muted); font: 500 0.66rem var(--mono); letter-spacing: 0.18em; text-transform: uppercase; }}
    h1 {{ margin-bottom: 1.5rem; color: var(--ink); font: 400 clamp(1.5rem, 2.4vw + 0.75rem, 2rem)/1.15 var(--serif); letter-spacing: -0.02em; }}
    svg {{ display: block; width: 100%; min-width: {viewbox_w}px; }}
    .step-number, .step-label, .lane-label, .role-text, .chip-text, .legend-label {{ font-family: var(--mono); text-anchor: middle; }}
    .step-number {{ fill: var(--ink); font-size: 7px; font-weight: 600; }}
    .step-label {{ fill: var(--muted); font-size: 7px; font-weight: 500; letter-spacing: 0.12em; }}
    .lane-label {{ fill: var(--muted); font-size: 8px; font-weight: 500; letter-spacing: 0.14em; }}
    .role-text {{ fill: var(--ink); font-size: 6px; font-weight: 600; }}
    .node-title {{ fill: var(--ink); font: 600 9px var(--sans); text-anchor: middle; }}
    .node-sub {{ fill: var(--muted); font: 400 6.5px var(--mono); text-anchor: middle; }}
    .node-tool {{ fill: var(--soft); font: 400 6.5px var(--mono); text-anchor: middle; }}
    .chip-text {{ fill: #fff; font-size: 5px; font-weight: 700; }}
    .focal-text {{ fill: var(--accent); }}
    .legend-label {{ fill: var(--muted); font-size: 7px; font-weight: 500; letter-spacing: 0.12em; text-anchor: end; }}
    .legend-text {{ fill: var(--muted); font: 400 7px var(--sans); }}
  </style>
</head>
<body>
  <main class="frame">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title_text}</h1>

    <svg viewBox="0 0 {viewbox_w} {viewbox_h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">{title_text}</title>
      <desc id="{slug}-desc">{desc_text}</desc>
      <defs>
        <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="11" cy="11" r="0.8" fill="{ink_alpha(0.10)}"/></pattern>
        {''.join(arrows_defs)}
      </defs>
      <rect width="{viewbox_w}" height="{viewbox_h}" fill="{t["paper"]}"/>
      <rect width="{viewbox_w}" height="{viewbox_h}" fill="url(#dots)"/>
      {lane_tint}
      {dividers}
      <g aria-label="Pipeline steps">
        {''.join(step_chips)}
      </g>
      <g aria-label="Role lanes">
        {''.join(lane_labels)}
      </g>
      <g aria-label="Connectors">
        {''.join(svg_arrows)}
      </g>
      <g aria-label="Nodes">
        {''.join(svg_nodes)}
      </g>
      <g aria-label="Legend">
        {''.join(legend)}
      </g>
    </svg>
  </main>
</body>
</html>
"""
    return html


CHIP_MEAN = {"WB": "Web数据", "DB": "数据集", "TB": "分析就绪表", "FL": "文件/报告", "LS": "日志流"}


def main() -> None:
    if len(sys.argv) != 3:
        print("用法：dataflow_builder.py <view.json> <output.html>", file=sys.stderr)
        sys.exit(2)
    view_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    view = read_json(view_path)
    try:
        validate(view)
    except DataFlowError as exc:
        print(f"视图校验失败：{exc}", file=sys.stderr)
        sys.exit(3)
    html = render(view)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(json.dumps({"ok": True, "view": str(view_path), "output": str(out_path),
                      "nodes": len(view["nodes"]), "flows": len(view.get("arrows", [])),
                      "lanes": len(view["lanes"]), "steps": len(view["steps"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
