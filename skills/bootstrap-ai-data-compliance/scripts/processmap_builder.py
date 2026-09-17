#!/usr/bin/env python3
"""三层流程渲染器：industry-model.json → 自包含 HTML（diagram-design Swimlane 类型）。

结构映射（与 vendor/diagram-design/references/type-swimlane.md 一致）：
- 泳道（横）：业务层 BUSINESS / 技术层 TECHNOLOGY / 数据层 DATA（模型三层节点）
- 阶段（列）：模型 stages（S01..）
- 节点：每泳道×阶段格一个（title=节点名，sub=事实状态）
- 层间链接：业务→技术 同列垂直；业务→数据 链式化为 技术→数据（避免垂直线穿过技术层节点）
- 全部 muted 实线；图例说明链式映射语义

用法：
    python3 processmap_builder.py <model.json> <output.html>
"""
import json
import sys
from pathlib import Path

# 与 dataflow_builder 相同的 token 与布局常量（默认皮肤）
TOKENS = {
    "paper": "#f5f5f5", "ink": "#2d3142", "muted": "#4f5d75", "soft": "#7a8399",
    "accent": "#eb6c36", "accent_tint": "rgba(235,108,54,0.08)", "link": "#2e5aa8",
}
LABEL_COL_W = 140
STEP_SLOT_W = 112
RIGHT_PAD = 28
HEADER_H = 36
LANE_H = 80
LEGEND_H = 80
LANES = [
    {"key": "BIZ", "name": ["业务层", "BUSINESS"]},
    {"key": "TEC", "name": ["技术层", "TECHNOLOGY"]},
    {"key": "DAT", "name": ["数据层", "DATA"]},
]
LAYER_NODE_KEY = {"businessNodes": "BIZ", "technologyNodes": "TEC", "dataNodes": "DAT"}


class ProcessMapError(Exception):
    pass


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProcessMapError(f"模型 JSON 读取失败：{exc}") from exc


def validate(model: dict) -> None:
    stages = model.get("stages", [])
    if not (1 <= len(stages) <= 6):
        raise ProcessMapError(f"阶段数量必须为 1..6，当前 {len(stages)}")
    stage_ids = {s["id"] for s in stages}
    for layer_key, lane_key in LAYER_NODE_KEY.items():
        seen = set()
        for n in model.get(layer_key, []):
            if n.get("stageId") not in stage_ids:
                raise ProcessMapError(f"{lane_key} 节点 {n.get('name')} 引用了不存在的阶段 {n.get('stageId')}")
            cell = (lane_key, n.get("stageId"))
            if cell in seen:
                raise ProcessMapError(f"泳道×阶段格重复：{lane_key}/{n.get('stageId')}（{n.get('name')}）")
            seen.add(cell)
    for link in model.get("layerLinks", []):
        if link.get("from") not in stage_ids and not any(
            n["id"] == link.get("from") for lk in LAYER_NODE_KEY for n in model.get(lk, [])
        ):
            raise ProcessMapError(f"层间链接 from 引用不存在：{link.get('from')}")


def render(model: dict) -> str:
    stages = model["stages"]
    t = TOKENS
    slug = "process-map"

    n_steps, n_lanes = len(stages), 3
    viewbox_w = LABEL_COL_W + n_steps * STEP_SLOT_W + RIGHT_PAD
    viewbox_h = HEADER_H + n_lanes * LANE_H + LEGEND_H
    legend_top = HEADER_H + n_lanes * LANE_H

    def step_cx(j):
        return LABEL_COL_W + j * STEP_SLOT_W + STEP_SLOT_W // 2

    def node_rect(lane_idx, step_idx):
        return step_cx(step_idx) - 50, HEADER_H + lane_idx * LANE_H + 8

    lane_idx_of = {l["key"]: i for i, l in enumerate(LANES)}
    # 泳道 → (stageId -> node)
    grid = {k: {} for k in LAYER_NODE_KEY}
    for layer_key, lane_key in LAYER_NODE_KEY.items():
        for n in model.get(layer_key, []):
            grid[layer_key][n["stageId"]] = n
    step_index = {s["id"]: i for i, s in enumerate(stages)}
    stage_name = {s["id"]: s["name"] for s in stages}

    ink_rgb = t["ink"][1:]
    def ink_alpha(a):
        return f"rgba({int(ink_rgb[0:2],16)},{int(ink_rgb[2:4],16)},{int(ink_rgb[4:6],16)},{a})"

    # ---------------- 层间链接（链式渲染） ----------------
    svg_arrows = []
    link_count = 0
    for link in model.get("layerLinks", []):
        f, to = link["from"], link["to"]
        src = next((n for lk in LAYER_NODE_KEY for n in model.get(lk, []) if n["id"] == f), None)
        dst = next((n for lk in LAYER_NODE_KEY for n in model.get(lk, []) if n["id"] == to), None)
        if src is None or dst is None:
            continue
        src_layer = next(lk for lk in LAYER_NODE_KEY if src in grid[lk].values())
        dst_layer = next(lk for lk in LAYER_NODE_KEY if dst in grid[lk].values())
        # 同阶段优先垂直；B→D 链式化为 TN→D
        chain = []
        if src_layer == "businessNodes" and dst_layer == "dataNodes":
            tn = grid["technologyNodes"].get(dst["stageId"])
            if tn is not None:
                chain = [("businessNodes", tn["stageId"]), ("technologyNodes", dst["stageId"])]
            else:
                chain = [("businessNodes", dst["stageId"])]
        else:
            chain = [(src_layer, dst["stageId"])]
        prev_layer = src_layer
        for layer_key, stage_id in chain:
            li, lj = lane_idx_of[LAYER_NODE_KEY[prev_layer]], step_index[stage_id]
            ki, kj = lane_idx_of[LAYER_NODE_KEY[layer_key]], step_index[stage_id]
            fx, fy = node_rect(li, lj)
            tx, ty = node_rect(ki, kj)
            if kj == lj and ki != li:
                cx = step_cx(lj)
                if ki > li:
                    d = f"M {cx} {fy+64} V {ty}"
                else:
                    d = f"M {cx} {fy} V {ty+64}"
            else:
                cx_to = step_cx(kj)
                mid_a = HEADER_H + li * LANE_H + LANE_H // 2
                if ki > li:
                    d = f"M {fx+100} {mid_a} H {cx_to-8} Q {cx_to} {mid_a} {cx_to} {mid_a+8} V {ty}"
                else:
                    d = f"M {fx+100} {mid_a} H {cx_to-8} Q {cx_to} {mid_a} {cx_to} {mid_a-8} V {ty+64}"
            svg_arrows.append(
                f'<path d="{d}" fill="none" stroke="{t["muted"]}" marker-end="url(#arr-muted)"/>'
            )
            prev_layer = layer_key
            link_count += 1

    # ---------------- 节点 ----------------
    svg_nodes = []
    for layer_key, lane_key in LAYER_NODE_KEY.items():
        li = lane_idx_of[lane_key]
        for n in model.get(layer_key, []):
            si = step_index[n["stageId"]]
            x, y = node_rect(li, si)
            cx = x + 50
            status = n.get("factStatus", "")
            # "待核实"为生成器占位（全图无差异时无信息量），不显示；有真实事实状态才显示
            sub = f"{stage_name.get(n['stageId'], '')}" if not status or status == "待核实" else f"{status}"
            svg_nodes.append(
                f'<rect x="{x}" y="{y}" width="100" height="64" rx="6" fill="{t["paper"]}" stroke="{ink_alpha(0.25)}"/>'
                f'<rect x="{x+4}" y="{y+4}" width="18" height="10" rx="3" fill="{ink_alpha(0.12)}"/><text x="{x+13}" y="{y+9}" class="role-text">{lane_key}</text>'
                f'<text x="{cx}" y="{y+23}" class="node-title">{n["name"]}</text>'
                f'<text x="{cx}" y="{y+35}" class="node-sub">{sub}</text>'
                f'<text x="{cx}" y="{y+47}" class="node-tool">{n.get("phaseId", "")}</text>'
            )

    # ---------------- 列头 / 泳道标签 ----------------
    step_chips = []
    for j, s in enumerate(stages):
        cx = step_cx(j)
        step_chips.append(
            f'<rect x="{cx-16}" y="6" width="32" height="16" rx="8" fill="{ink_alpha(0.12)}"/>'
            f'<text x="{cx}" y="14" class="step-number">{s["index"]:02d}</text>'
            f'<text x="{cx}" y="29" class="step-label">{s["name"]}</text>'
        )
    lane_labels = []
    for k, l in enumerate(LANES):
        mid = HEADER_H + k * LANE_H + LANE_H // 2
        for i, line in enumerate(l["name"]):
            lane_labels.append(f'<text x="{LABEL_COL_W//2}" y="{mid - 4 + i*12}" class="lane-label">{line}</text>')

    # ---------------- 图例 ----------------
    row = legend_top + 16
    legend = [
        f'<text x="{LABEL_COL_W+24}" y="{row}" class="legend-label">FLOW</text>',
        f'<line x1="180" y1="{row-3}" x2="204" y2="{row-3}" stroke="{t["muted"]}" marker-end="url(#arr-muted)"/><text x="212" y="{row}" class="legend-text">层间映射</text>',
        f'<text x="316" y="{row}" class="legend-text">业务 → 技术 → 数据（链式落地；数据经技术层写入/读取）</text>',
    ]

    # ---------------- 页面 ----------------
    title_text = f"{model.get('meta', {}).get('industry', '产业')} · 三层流程图"
    desc_text = "业务层、技术层、数据层三层的流程阶段映射图：每个业务环节映射到支撑技术系统与数据资产，数据经技术层落地。"
    arrows_defs = (
        f'<marker id="arr-muted" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="{t["muted"]}"/></marker>'
    )
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
      --paper: {t["paper"]}; --paper-2: #ececec; --ink: {t["ink"]}; --muted: {t["muted"]};
      --soft: {t["soft"]}; --rule: {ink_alpha(0.12)}; --accent: {t["accent"]};
      --accent-tint: {t["accent_tint"]}; --link: {t["link"]};
      --sans: {css_sans}; --serif: {css_serif}; --mono: {css_mono};
    }}
    body {{ min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 3rem 2rem; background: var(--paper); color: var(--ink); font-family: var(--sans); }}
    .frame {{ width: 100%; max-width: 1400px; }}
    .eyebrow {{ margin-bottom: 0.5rem; color: var(--muted); font: 500 0.66rem var(--mono); letter-spacing: 0.18em; text-transform: uppercase; }}
    h1 {{ margin-bottom: 1.5rem; color: var(--ink); font: 400 clamp(1.5rem, 2.4vw + 0.75rem, 2rem)/1.15 var(--serif); letter-spacing: -0.02em; }}
    svg {{ display: block; width: 100%; min-width: {viewbox_w}px; }}
    .step-number, .step-label, .lane-label, .role-text, .legend-label {{ font-family: var(--mono); text-anchor: middle; }}
    .step-number {{ fill: var(--ink); font-size: 7px; font-weight: 600; }}
    .step-label {{ fill: var(--muted); font-size: 7px; font-weight: 500; letter-spacing: 0.12em; }}
    .lane-label {{ fill: var(--muted); font-size: 8px; font-weight: 500; letter-spacing: 0.14em; }}
    .role-text {{ fill: var(--ink); font-size: 6px; font-weight: 600; }}
    .node-title {{ fill: var(--ink); font: 600 9px var(--sans); text-anchor: middle; }}
    .node-sub {{ fill: var(--muted); font: 400 6.5px var(--mono); text-anchor: middle; }}
    .node-tool {{ fill: var(--soft); font: 400 6.5px var(--mono); text-anchor: middle; }}
    .legend-label {{ fill: var(--muted); font-size: 7px; font-weight: 500; letter-spacing: 0.12em; text-anchor: end; }}
    .legend-text {{ fill: var(--muted); font: 400 7px var(--sans); }}
  </style>
</head>
<body>
  <main class="frame">
    <p class="eyebrow">Process map · Swimlane · Diagram Design</p>
    <h1>{title_text}</h1>

    <svg viewBox="0 0 {viewbox_w} {viewbox_h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">
      <title id="{slug}-title">{title_text}</title>
      <desc id="{slug}-desc">{desc_text}</desc>
      <defs>
        <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="11" cy="11" r="0.8" fill="{ink_alpha(0.10)}"/></pattern>
        {arrows_defs}
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


def main() -> None:
    if len(sys.argv) != 3:
        print("用法：processmap_builder.py <model.json> <output.html>", file=sys.stderr)
        sys.exit(2)
    model_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    model = read_json(model_path)
    try:
        validate(model)
    except ProcessMapError as exc:
        print(f"模型校验失败：{exc}", file=sys.stderr)
        sys.exit(3)
    html = render(model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    stages = len(model.get("stages", []))
    nodes = sum(len(model.get(lk, [])) for lk in ("businessNodes", "technologyNodes", "dataNodes"))
    links = len(model.get("layerLinks", []))
    print(json.dumps({"ok": True, "model": str(model_path), "output": str(out_path),
                      "stages": stages, "nodes": nodes, "layer_links": links}, ensure_ascii=False))


if __name__ == "__main__":
    main()
