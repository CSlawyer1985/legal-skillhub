#!/usr/bin/env python3
"""Approximate draw.io layout validator for legal diagrams.

Flags edges whose orthogonal/polyline segments pass through non-endpoint
vertex bounding boxes. This catches the most common "line crosses text/node"
problem in generated legal diagrams.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Box:
    id: str
    label: str
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def expanded(self, margin: float) -> "Box":
        return Box(self.id, self.label, self.x - margin, self.y - margin, self.w + 2 * margin, self.h + 2 * margin)


@dataclass
class Edge:
    id: str
    label: str
    source: str | None
    target: str | None
    points: list[tuple[float, float]]


def clean_label(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("&#xa;", " ").replace("\n", " ").strip()


def parse_drawio(path: Path) -> tuple[dict[str, Box], list[Edge]]:
    root = ET.parse(path).getroot()
    boxes: dict[str, Box] = {}
    edges: list[Edge] = []

    for cell in root.iter("mxCell"):
        cid = cell.attrib.get("id", "")
        geom = cell.find("mxGeometry")
        if not cid or geom is None:
            continue

        if cell.attrib.get("vertex") == "1":
            label = clean_label(cell.attrib.get("value"))
            style = cell.attrib.get("style", "")
            # Ignore decorative background bands and pure text labels. They are
            # allowed to be crossed and otherwise create noisy false positives.
            if not label or style.startswith("text;") or "strokeColor=none" in style:
                continue
            try:
                x = float(geom.attrib.get("x", "0"))
                y = float(geom.attrib.get("y", "0"))
                w = float(geom.attrib.get("width", "0"))
                h = float(geom.attrib.get("height", "0"))
            except ValueError:
                continue
            if w > 0 and h > 0:
                boxes[cid] = Box(cid, label, x, y, w, h)

        if cell.attrib.get("edge") == "1":
            pts: list[tuple[float, float]] = []
            arr = geom.find("Array")
            if arr is not None:
                for pt in arr.findall("mxPoint"):
                    try:
                        pts.append((float(pt.attrib["x"]), float(pt.attrib["y"])))
                    except (KeyError, ValueError):
                        pass
            edges.append(
                Edge(
                    cid,
                    clean_label(cell.attrib.get("value")),
                    cell.attrib.get("source"),
                    cell.attrib.get("target"),
                    pts,
                )
            )
    return boxes, edges


def segment_intersects_box(a: tuple[float, float], b: tuple[float, float], box: Box) -> bool:
    x1, y1 = a
    x2, y2 = b
    left, right = box.x, box.x + box.w
    top, bottom = box.y, box.y + box.h

    # Fast reject by bounding boxes.
    if max(x1, x2) < left or min(x1, x2) > right or max(y1, y2) < top or min(y1, y2) > bottom:
        return False

    # Horizontal/vertical segments are the normal draw.io orthogonal case.
    if y1 == y2:
        return top <= y1 <= bottom and max(min(x1, x2), left) <= min(max(x1, x2), right)
    if x1 == x2:
        return left <= x1 <= right and max(min(y1, y2), top) <= min(max(y1, y2), bottom)

    # Conservative fallback: sample the line.
    steps = 24
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if left <= x <= right and top <= y <= bottom:
            return True
    return False


def edge_polyline(edge: Edge, boxes: dict[str, Box]) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    if edge.source in boxes:
        src = boxes[edge.source]
        pts.append((src.cx, src.cy))
    pts.extend(edge.points)
    if edge.target in boxes:
        dst = boxes[edge.target]
        pts.append((dst.cx, dst.cy))
    return pts


def validate(path: Path, margin: float) -> list[str]:
    boxes, edges = parse_drawio(path)
    warnings: list[str] = []

    for edge in edges:
        pts = edge_polyline(edge, boxes)
        if len(pts) < 2:
            continue
        endpoints = {edge.source, edge.target}
        for a, b in zip(pts, pts[1:]):
            for box in boxes.values():
                if box.id in endpoints:
                    continue
                # Ignore tiny text-only title boxes by requiring a meaningful area.
                if box.w * box.h < 1200:
                    continue
                if segment_intersects_box(a, b, box.expanded(margin)):
                    warnings.append(
                        f"WARN edge {edge.id!r} ({edge.label or 'no label'}) crosses node {box.id!r} ({box.label[:40]})"
                    )
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate draw.io legal diagram layout.")
    parser.add_argument("drawio_file", type=Path)
    parser.add_argument("--margin", type=float, default=4.0, help="box expansion margin for collision checks")
    args = parser.parse_args()

    warnings = validate(args.drawio_file, args.margin)
    if warnings:
        print("\n".join(warnings))
        return 1
    print(f"PASS {args.drawio_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
