#!/usr/bin/env python3
"""数据流图几何自检：解析生成的 data-flow-map.html，检测箭头 path 是否穿过节点矩形。

背景：正交路由（直线/垂直/elbow）曾出现穿过中间节点（同泳道跳格穿中间列节点、
同阶段跨泳道多格穿中间泳道节点、垂直段落点落列中心穿目标节点）与 accent label
压节点的缺陷；本脚本作为渲染后自动门禁，与 self_check.py（可访问性/安全契约）
互补：self_check 管 HTML 契约，本脚本管几何布局。

用法：
    python3 verify_geometry.py <data-flow-map.html>
退出码：0=通过；3=发现穿节点/标签压节点（列出明细，定位到 path 序号与节点标题）。

原理：从 HTML 提取 Connectors group 的 path（d 含 M/H/V/Q 命令）与 Nodes group 的
节点外框 rect（width=100 的单位宽），将 path 线性化后检测线段与节点矩形的相交
（含贴边容差：端点恰好落在节点边缘不计为穿过）。
"""
import re
import sys
from pathlib import Path


def parse_html(html: str):
    """返回 (箭头 path 列表, 节点矩形列表[(x0,y0,x1,y1,title)])。"""
    paths = []
    conn = re.search(r'<g aria-label="Connectors">(.*?)</g>', html, re.S)
    if conn:
        paths = [m for m in re.findall(r'<path d="([^"]+)"', conn.group(1)) if "L" not in m and "Z" not in m]
    node_rects = []
    nodes = re.search(r'<g aria-label="Nodes">(.*?)</g>', html, re.S)
    if nodes:
        for m in re.finditer(r'<rect x="(-?\d+)" y="(-?\d+)" width="(\d+)" height="(\d+)"', nodes.group(1)):
            x, y, w, h = (int(v) for v in m.groups())
            if w != 100 or h != 64:
                continue
            # 该 rect 后第一个 node-title 文本
            after = nodes.group(1)[m.end():]
            t = re.search(r'class="node-title"[^>]*>([^<]*)<', after)
            title = t.group(1) if t else "?"
            node_rects.append((x, y, x + w, y + h, title))
    return paths, node_rects


def path_segments(d: str):
    """将 M/H/V/Q path 线性化为线段列表。"""
    segs = []
    cx = cy = None
    for cmd, x, y in re.findall(r'([MHVQ])\s*(-?\d+(?:\.\d+)?)?\s*,?\s*(-?\d+(?:\.\d+)?)?', d):
        if cmd == "M":
            cx, cy = float(x), float(y)
        elif cmd == "H":
            segs.append(((cx, cy), (float(x), cy)))
            cx = float(x)
        elif cmd == "V":
            segs.append(((cx, cy), (cx, float(x))))
            cy = float(x)
        elif cmd == "Q":
            segs.append(((cx, cy), (float(x), float(y))))
            cx, cy = float(x), float(y)
    return segs


def seg_intersects_rect(seg, rect):
    """线段与矩形相交检测；端点贴边不计。rect=(x0,y0,x1,y1)。"""
    (x1, y1), (x2, y2) = seg
    rx0, ry0, rx1, ry1 = rect[:4]
    if min(x1, x2) >= rx1 or max(x1, x2) <= rx0 or min(y1, y2) >= ry1 or max(y1, y2) <= ry0:
        return False
    return True


def check(html: str):
    """返回 (问题列表, 节点矩形数, path 数)。"""
    paths, node_rects = parse_html(html)
    issues = []
    for i, d in enumerate(paths):
        for seg in path_segments(d):
            for r in node_rects:
                if seg_intersects_rect(seg, r):
                    issues.append(f"path#{i} {seg} 穿过节点「{r[4]}」({r[0]},{r[1]})-({r[2]},{r[3]})")
    # accent label rect（宽 >40 且高 ==12 的小 rect）与节点重叠检测
    label_re = re.compile(r'<rect x="(-?\d+)" y="(-?\d+)" width="(\d+)" height="12"')
    for m in label_re.finditer(html):
        x, y, w = (int(v) for v in m.groups())
        if w < 40 or w > 130:
            continue
        for r in node_rects:
            if x < r[2] and x + w > r[0] and y < r[3] and y + 12 > r[1]:
                issues.append(f"label rect ({x},{y},{w}x12) 压节点「{r[4]}」")
    return issues, len(node_rects), len(paths)


def main() -> None:
    if len(sys.argv) != 2:
        print("用法：verify_geometry.py <data-flow-map.html>", file=sys.stderr)
        sys.exit(2)
    html = Path(sys.argv[1]).read_text(encoding="utf-8")
    issues, n_nodes, n_paths = check(html)
    print(f"几何自检：{n_paths} 条箭头 × {n_nodes} 个节点")
    if issues:
        print(f"FAIL：发现 {len(issues)} 处几何问题：")
        for line in issues:
            print("  -", line)
        sys.exit(3)
    print("OK：无箭头穿节点、无 label 压节点")


if __name__ == "__main__":
    main()
