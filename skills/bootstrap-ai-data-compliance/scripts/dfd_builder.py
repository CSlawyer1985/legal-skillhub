#!/usr/bin/env python3
"""数据流向图（DFD）模板引擎 v4——端口锁定 + 标签独立通道（归藏风版）。

修正要点：
  1. 端口强制为边中点：Left/Right/Top/Bottom-Center，禁止非中点出发
  2. 同层水平直连（y_center 相同）→ 笔直水平线；同列垂直直连 → 笔直垂直线
  3. 节点尺寸统一：高 60；宽按类型（external/process 140 / storage 160 / compliance 180 / vendor 160 / exit 130）
  4. 布局全部整数坐标（消除浮点中心偏差）
  5. 标签放水平段中点上方/下方（≥8px）；水平段 <60px 时放垂直段转弯处外侧
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# ============ 归藏风八色白名单 ============
WHITELIST = {
    "PAPER": "#FAFAF8", "MODULE": "#FFFFFF", "PERIOD": "#E0E0E0",
    "HAIR": "#D4D4D2", "LINE": "#BDBDBD", "GRAY": "#737373",
    "INK": "#333333", "KLEIN": "#002FA7",
}
PAPER, MODULE, PERIOD = WHITELIST["PAPER"], WHITELIST["MODULE"], WHITELIST["PERIOD"]
HAIR, LINE, GRAY, INK, KLEIN = WHITELIST["HAIR"], WHITELIST["LINE"], WHITELIST["GRAY"], WHITELIST["INK"], WHITELIST["KLEIN"]

# ============ 画布契约（不可变） ============
WIDTH, HEIGHT = 1600, 950
FONT = "-apple-system, 'PingFang SC', 'Segoe UI', sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, monospace"
NH = 60  # 所有节点统一高度
KIND_WIDTH = {
    "external": 140, "process": 140, "storage": 160,
    "compliance": 180, "human": 140, "vendor": 160, "exit": 130,
}
BOX = {"x": 40, "y": 80, "w": 1300, "h": 720}
DICT = {"x": 1360, "y": 80, "w": 200, "h": 720}
LEGEND_Y = 820
DECLARE_Y1, DECLARE_Y2 = 885, 910

# 层 → 列 x
LAYER_X = {
    "GOV": 280, "L0": 80, "L1": 280, "L2": 520, "L3": 820, "L4": 1100,
    "SUP": 520, "EXIT": 1100,
}
# 治理层 y（下移至 150，顶部留足空隙，避免贴框顶）
GOV_Y = 150
# 主流程层纵向范围（y 均分）
LAYER_Y_RANGE = (290, 430)

KIND_STYLE = {
    "external": (MODULE, HAIR, INK), "process": (MODULE, HAIR, INK),
    "storage": (MODULE, HAIR, INK), "compliance": (KLEIN, KLEIN, MODULE),
    "human": (MODULE, HAIR, INK), "vendor": (MODULE, HAIR, INK),
    "exit": (PERIOD, HAIR, INK),
}


def esc(value) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ============ 自动布局（整数坐标 + 统一尺寸） ============


def auto_layout(nodes: list[dict]) -> dict[str, dict]:
    by_layer: dict[str, list[dict]] = {}
    for node in nodes:
        by_layer.setdefault(node["layer"], []).append(node)
    pos = {}
    for layer, items in by_layer.items():
        x = LAYER_X.get(layer, 280)
        if layer in ("GOV", "SUP", "EXIT"):
            base_y = GOV_Y if layer == "GOV" else 640
            for i, node in enumerate(items):
                w = KIND_WIDTH.get(node["kind"], 140)
                # EXIT 层多节点横向错开（窄宽，右侧空间有限）；GOV/SUP 同列纵向
                if layer == "EXIT":
                    w = 100
                    pos[node["id"]] = {"x": round(x + i * (w + 40)), "y": base_y, "w": w, "h": NH, **node}
                else:
                    pos[node["id"]] = {"x": round(x + i * (w + 40)), "y": base_y, "w": w, "h": NH, **node}
        else:
            # 主流程层：同列纵向均分（每列最多 2 节点）
            n = len(items)
            span = LAYER_Y_RANGE[1] - LAYER_Y_RANGE[0] - NH
            ys = [round(LAYER_Y_RANGE[0] + i * span / max(n - 1, 1)) for i in range(n)]
            for node, y in zip(items, ys):
                w = KIND_WIDTH.get(node["kind"], 140)
                pos[node["id"]] = {"x": x, "y": y, "w": w, "h": NH, **node}
    return pos


def anchor(pos: dict, side: str) -> tuple[int, int]:
    """边中点端口（强制）：L/R/T/B = 对应边中点。"""
    x, y, w, h = pos["x"], pos["y"], pos["w"], pos["h"]
    return {
        "L": (x, y + h // 2), "R": (x + w, y + h // 2),
        "T": (x + w // 2, y), "B": (x + w // 2, y + h),
    }[side]


# ============ 自动路由（端口锁定 + 正交优先级） ============


def rects_list(pos: dict) -> list[tuple[str, int, int, int, int]]:
    return [(nid, p["x"], p["y"], p["w"], p["h"]) for nid, p in pos.items()]


def segment_hits_node(x1, y1, x2, y2, rects, exclude: set[str]) -> bool:
    """线段是否穿过或贴边节点（贴边也视为冲突，避免视觉贴线）。"""
    for nid, rx, ry, rw, rh in rects:
        if nid in exclude:
            continue
        if y1 == y2:
            # 水平段：y 在节点上下边之间（含贴边），x 范围重叠（含贴边）
            if ry <= y1 <= ry + rh and min(x1, x2) <= rx + rw and max(x1, x2) >= rx:
                return True
        else:
            # 垂直段：x 在节点左右边之间（含贴边），y 范围重叠（含贴边）
            if rx <= x1 <= rx + rw and min(y1, y2) <= ry + rh and max(y1, y2) >= ry:
                return True
    return False


def route_orthogonal(start, end, pos, exclude: set[str]) -> list[tuple[int, int]]:
    """正交路由（优先级：同层直连 > 同列直连 > 先水平后垂直 > 先垂直后水平）。"""
    x1, y1 = start
    x2, y2 = end
    rects = rects_list(pos)
    # 仅排除 from/to 两个端点节点；其余节点一律视为障碍
    exclude = set(exclude)
    # 1) 同 y（y_center 相同）→ 笔直水平线（Right-Center ↔ Left-Center）
    if y1 == y2 and not segment_hits_node(x1, y1, x2, y2, rects, exclude):
        return [(x1, y1), (x2, y2)]
    # 2) 同 x → 笔直垂直线（Bottom-Center ↔ Top-Center）
    if x1 == x2 and not segment_hits_node(x1, y1, x2, y2, rects, exclude):
        return [(x1, y1), (x2, y2)]
    # 3) 先水平后垂直：从起点水平出 → 垂直 → 水平入终点
    #    水平通道候选：起点/终点 x + 各列间隙 + 常用通道
    for mid_x in [x1, x2, (x1 + x2) // 2, 240, 360, 460, 480, 520, 650, 700, 1020, 1030]:
        path = [(x1, y1), (mid_x, y1), (mid_x, y2), (x2, y2)]
        if all(not segment_hits_node(*path[k], *path[k + 1], rects, exclude) for k in range(len(path) - 1)):
            return path
    # 4) 先垂直后水平：从起点垂直出 → 水平 → 垂直入终点
    #    垂直通道候选：治理层上方 100 / 治理-主流程 250 / 主流程下方 560 / 支撑上方 610 / 退出下方 730
    for mid_y in [y1, y2, 100, 250, 260, 560, 610, 730, 350, 580]:
        path = [(x1, y1), (x1, mid_y), (x2, mid_y), (x2, y2)]
        if all(not segment_hits_node(*path[k], *path[k + 1], rects, exclude) for k in range(len(path) - 1)):
            return path
    # 5) U 形：起点水平出列 → 垂直走通道 → 水平到终点列 → 垂直入终点
    #    起点先左/右脱离所在列（避开同列上下节点），再走顶部/底部通道
    exit_xs = sorted({x for x in (60, 240, 360, 460, 520, 700, 780, 1020, 1030, 1160)})
    channel_ys = [100, 250, 260, 560, 610, 730]
    for ex_x in exit_xs:
        for mid_y in channel_ys:
            path = [(x1, y1), (ex_x, y1), (ex_x, mid_y), (x2, mid_y), (x2, y2)]
            if all(not segment_hits_node(*path[k], *path[k + 1], rects, exclude) for k in range(len(path) - 1)):
                return path
    # 6) 兜底：报错标记（校验器将拒绝输出）
    return ["ROUTE_FAIL"]


# ============ 校验器 ============


def validate(pos: dict, flows: list[dict], routed: dict[str, list]) -> list[str]:
    issues = []
    for nid, p in pos.items():
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        if x < 0 or x + w > WIDTH or y < 0 or y + h > HEIGHT:
            issues.append(f"节点 {nid} 超出画布")
        if x < BOX["x"] or x + w > BOX["x"] + BOX["w"] or y < BOX["y"] or y + h > BOX["y"] + BOX["h"]:
            issues.append(f"节点 {nid} 超出虚线框")
    rects = rects_list(pos)
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, ax, ay, aw, ah = rects[i]
            b, bx, by, bw, bh = rects[j]
            if ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by:
                issues.append(f"节点重叠：{a}×{b}")
    for flow in flows:
        pts = routed.get(flow["id"], [])
        if not pts or pts[0] == "ROUTE_FAIL":
            issues.append(f"{flow['id']} 路由失败：无可用正交通道")
            continue
        for k in range(len(pts) - 1):
            x1, y1 = pts[k]
            x2, y2 = pts[k + 1]
            if x1 != x2 and y1 != y2:
                issues.append(f"{flow['id']} 含斜线段")
    return issues


# ============ 渲染 ============


def render_node(nid: str, p: dict) -> str:
    fill, stroke, text = KIND_STYLE[p["kind"]]
    return (
        f'<g class="dfd-node" data-node-id="{nid}">'
        f'<rect x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
        f'<text x="{p["x"] + p["w"] / 2}" y="{p["y"] + p["h"] / 2 - 3}" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="500" fill="{text}">{esc(p["label"])}</text>'
        f'<text x="{p["x"] + p["w"] / 2}" y="{p["y"] + p["h"] / 2 + 15}" text-anchor="middle" font-family="{FONT}" font-size="9" fill="{GRAY}">【系统名称 | 待核实】</text>'
        f'</g>'
    )


def overlaps_label(lx, ly, rects, w=44, h=18) -> bool:
    for _, rx, ry, rw, rh in rects:
        if lx < rx + rw and lx + w > rx and ly < ry + rh and ly + h > ry:
            return True
    return False


def render_flow(fid: str, pts: list, rects, dashed: bool, bidirectional: bool) -> str:
    # 找最长水平段
    best_h = None
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        if y1 == y2 and (best_h is None or abs(x2 - x1) > abs(best_h[1] - best_h[0])):
            best_h = (x1, x2, y1)
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    path_d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
    arrow = (
        f'<marker id="arr-{abs(hash(fid)) % 9999}" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto">'
        f'<path d="M0,0 L0,8 L9,4 z" fill="{LINE}"/></marker>'
    )
    extra = ""
    if bidirectional:
        rev = [(x + 8, y) for x, y in reversed(pts)]
        rev_d = "M " + " L ".join(f"{x},{y}" for x, y in rev)
        extra = f'<path d="{rev_d}" stroke="{LINE}" stroke-width="1.2" stroke-dasharray="3 4" fill="none" opacity="0.7"/>'

    # 标签定位（修正2：独立通道）
    if best_h and abs(best_h[1] - best_h[0]) >= 60:
        # 水平段足够长：标签放中点上方（优先）或下方
        lx = (best_h[0] + best_h[1]) / 2 - 22
        ly = best_h[2] - 24
        if overlaps_label(lx, ly, rects):
            ly = best_h[2] + 8  # 下方
            if overlaps_label(lx, ly, rects):
                ly = best_h[2] - 24
                lx += 40
                while overlaps_label(lx, ly, rects) and lx < DICT["x"] - 50:
                    lx += 40
    elif best_h:
        # 水平段 <60px：标签放垂直段转弯处外侧
        # 找最长的垂直段
        best_v = None
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            if x1 == x2 and (best_v is None or abs(y2 - y1) > abs(best_v[1] - best_v[0])):
                best_v = (y1, y2, x1)
        if best_v:
            vx = best_v[2]
            vy = (best_v[0] + best_v[1]) / 2
            # 放在垂直段左侧（如果左侧有空间）否则右侧
            lx = vx - 60
            ly = vy - 9
            if lx < BOX["x"] + 5 or overlaps_label(lx, ly, rects):
                lx = vx + 12
                if overlaps_label(lx, ly, rects):
                    lx = vx - 60
                    ly = vy - 30
        else:
            x1, y1 = pts[0]
            x2, y2 = pts[-1]
            lx, ly = (x1 + x2) / 2 - 22, (y1 + y2) / 2 - 9
    else:
        x1, y1 = pts[0]
        x2, y2 = pts[-1]
        lx, ly = (x1 + x2) / 2 - 22, (y1 + y2) / 2 - 9

    return (
        f'{arrow}'
        f'<path d="{path_d}" stroke="{LINE}" stroke-width="1.6" fill="none"{dash} marker-end="url(#arr-{abs(hash(fid)) % 9999})"/>'
        f'{extra}'
        f'<g class="dfd-flow" data-flow-label="{fid}">'
        f'<rect x="{lx}" y="{ly}" width="44" height="18" fill="{PAPER}" stroke="{PERIOD}"/>'
        f'<text x="{lx + 22}" y="{ly + 13}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{INK}">{esc(fid)}</text>'
        f'</g>'
    )


def build_svg(scene: dict, model: dict, pos: dict, routed: dict) -> str:
    industry = scene.get("industry") or (model.get("meta") or {}).get("industry", "AI产业")
    title = scene.get("title", f"{industry}数据流向图")
    data_objects = (model.get("dataFlowMap") or {}).get("dataObjects", [])
    dict_rows = ""
    for index, obj in enumerate(data_objects, 1):
        name = obj.get("name", "")
        sensitive = obj.get("classification") == "敏感个人信息"
        dict_rows += (
            f'<tr><td style="font-family:{MONO};padding:2px 4px;border-bottom:1px solid {HAIR};color:{INK}">D{index:02d}</td>'
            f'<td style="padding:2px 4px;border-bottom:1px solid {HAIR};color:{INK}">{esc(name)}</td>'
            f'<td style="text-align:right;padding:2px 4px;border-bottom:1px solid {HAIR};color:{"#333333" if sensitive else GRAY}">{"※敏感" if sensitive else "一般"}</td></tr>'
        )
    nodes_svg = "".join(render_node(nid, p) for nid, p in pos.items())
    rects = rects_list(pos)
    flows_svg = "".join(render_flow(f["id"], routed[f["id"]], rects, f.get("dashed", False), f.get("bidirectional", False)) for f in scene["flows"])
    gov_zone = (
        f'<g data-institution-zone="true">'
        f'<rect x="{BOX["x"]}" y="{BOX["y"]}" width="{BOX["w"]}" height="{BOX["h"]}" fill="none" stroke="{HAIR}" stroke-width="1.2" stroke-dasharray="8 6"/>'
        f'<text x="{BOX["x"] + 16}" y="{BOX["y"] + 24}" font-family="{FONT}" font-size="12" font-weight="500" fill="{GRAY}">外部输入与治理记录｜实际主体及系统待核实</text>'
        f'</g>'
    )
    dict_panel = (
        f'<rect x="{DICT["x"]}" y="{DICT["y"]}" width="{DICT["w"]}" height="{DICT["h"]}" fill="{MODULE}" stroke="{HAIR}" stroke-width="1.2"/>'
        f'<text x="{DICT["x"] + 12}" y="{DICT["y"] + 28}" font-family="{FONT}" font-size="15" font-weight="300" fill="{INK}">数据字典</text>'
        f'<foreignObject x="{DICT["x"] + 6}" y="{DICT["y"] + 40}" width="{DICT["w"] - 12}" height="{DICT["h"] - 56}">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-family:{FONT};font-size:11px">'
        f'<table style="width:100%;border-collapse:collapse;border-top:1px solid {HAIR}">'
        f'<tr style="border-bottom:1px solid {HAIR}"><th style="width:30px;text-align:left;padding:3px 4px;font-weight:500;color:{GRAY}">编号</th><th style="width:110px;text-align:left;padding:3px 4px;font-weight:500;color:{GRAY}">名称</th><th style="width:50px;text-align:right;padding:3px 4px;font-weight:500;color:{GRAY}">敏感</th></tr>'
        f'{dict_rows}'
        f'</table></div></foreignObject>'
    )
    legend_items = [("外部实体", MODULE), ("处理系统", MODULE), ("数据存储", MODULE), ("合规/伦理", KLEIN), ("人工介入", MODULE), ("归档/删除", PERIOD), ("外部供应商", MODULE)]
    legend_x = 50
    legend_svg = ""
    for label, color in legend_items:
        legend_svg += (
            f'<rect x="{legend_x}" y="{LEGEND_Y}" width="14" height="14" fill="{color}" stroke="{HAIR}" stroke-width="1"/>'
            f'<text x="{legend_x + 20}" y="{LEGEND_Y + 11}" font-family="{FONT}" font-size="11" fill="{GRAY}">{label}</text>'
        )
        legend_x += 42 + 4 * len(label) + 22
    separator = f'<line x1="50" y1="812" x2="1340" y2="812" stroke="{HAIR}" stroke-width="1" stroke-dasharray="2 4"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" data-view="DATAFLOW">
<style>
  .dfd-node{{cursor:pointer}} .dfd-node rect{{transition:stroke-width .12s}} .dfd-node:hover rect{{stroke-width:2.4}}
</style>
<rect width="100%" height="100%" fill="{PAPER}"/>
<text x="50" y="46" font-family="{FONT}" font-size="30" font-weight="300" fill="{INK}">{esc(title)}</text>
<text x="50" y="68" font-family="{FONT}" font-size="11" fill="{GRAY}">数据全生命周期 · 分层网格 · 治理/支撑/退出层 · 数据字典</text>
{gov_zone}
{nodes_svg}
{flows_svg}
{dict_panel}
{separator}
<text x="50" y="{LEGEND_Y - 6}" font-family="{FONT}" font-size="12" font-weight="500" fill="{INK}">图例</text>
{legend_svg}
<text x="50" y="{DECLARE_Y1}" font-family="{FONT}" font-size="11" fill="{GRAY}">所有实际系统名称均待核实。</text>
<text x="50" y="{DECLARE_Y2}" font-family="{FONT}" font-size="11" fill="{GRAY}">基于既有材料，法规版本及适用性待专项校验。</text>
</svg>"""


def main() -> None:
    scene_path = Path(sys.argv[1])
    model_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
    pos = auto_layout(scene["nodes"])
    routed = {}
    for flow in scene["flows"]:
        start = anchor(pos[flow["from"]], flow.get("side_from", "R"))
        end = anchor(pos[flow["to"]], flow.get("side_to", "L"))
        routed[flow["id"]] = route_orthogonal(start, end, pos, {flow["from"], flow["to"]})
    issues = validate(pos, scene["flows"], routed)
    if issues:
        print(json.dumps({"error": "模板契约校验失败", "issues": issues}, ensure_ascii=False))
        sys.exit(1)
    svg = build_svg(scene, model, pos, routed)
    output_path.write_text(svg, encoding="utf-8")
    print(json.dumps({"output": str(output_path), "bytes": len(svg), "validated": True, "nodes": len(pos), "flows": len(routed)}))


if __name__ == "__main__":
    main()
