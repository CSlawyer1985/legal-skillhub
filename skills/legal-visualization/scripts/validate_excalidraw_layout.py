#!/usr/bin/env python3
"""Approximate Excalidraw layout validator for legal diagrams."""

from __future__ import annotations

import argparse
import json
import sys
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

    def expanded(self, margin: float) -> "Box":
        return Box(self.id, self.label, self.x - margin, self.y - margin, self.w + 2 * margin, self.h + 2 * margin)


def segment_intersects_box(a: tuple[float, float], b: tuple[float, float], box: Box) -> bool:
    x1, y1 = a
    x2, y2 = b
    left, right = box.x, box.x + box.w
    top, bottom = box.y, box.y + box.h
    if max(x1, x2) < left or min(x1, x2) > right or max(y1, y2) < top or min(y1, y2) > bottom:
        return False
    if y1 == y2:
        return top <= y1 <= bottom and max(min(x1, x2), left) <= min(max(x1, x2), right)
    if x1 == x2:
        return left <= x1 <= right and max(min(y1, y2), top) <= min(max(y1, y2), bottom)
    for i in range(25):
        t = i / 24
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if left <= x <= right and top <= y <= bottom:
            return True
    return False


def extract_label(elements: list[dict], box: Box) -> str:
    labels: list[str] = []
    for el in elements:
        if el.get("type") != "text" or el.get("isDeleted"):
            continue
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        if box.x - 20 <= x <= box.x + box.w + 20 and box.y - 20 <= y <= box.y + box.h + 20:
            text = str(el.get("text", "")).replace("\n", " ")
            if text:
                labels.append(text[:40])
    return " / ".join(labels[:2])


def validate(path: Path, margin: float) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    elements = [el for el in data.get("elements", []) if not el.get("isDeleted")]
    boxes: list[Box] = []
    warnings: list[str] = []

    for el in elements:
        if el.get("type") not in {"rectangle", "diamond", "ellipse"}:
            continue
        box = Box(
            str(el.get("id", "")),
            "",
            float(el.get("x", 0)),
            float(el.get("y", 0)),
            abs(float(el.get("width", 0))),
            abs(float(el.get("height", 0))),
        )
        box.label = extract_label(elements, box)
        boxes.append(box)

        fill = el.get("fillStyle")
        if fill in {"hachure", "cross-hatch"}:
            warnings.append(f"WARN node {box.id!r} ({box.label}) uses noisy fillStyle={fill!r}; use solid for legal diagrams")
        roughness = float(el.get("roughness", 0) or 0)
        if roughness > 1:
            warnings.append(f"WARN node {box.id!r} ({box.label}) has roughness={roughness}; use 0 or 1 for legal diagrams")

    for el in elements:
        if el.get("type") != "arrow":
            continue
        eid = str(el.get("id", ""))
        base_x = float(el.get("x", 0))
        base_y = float(el.get("y", 0))
        points = [(base_x + float(p[0]), base_y + float(p[1])) for p in el.get("points", [])]
        if len(points) < 2:
            continue
        for a, b in zip(points, points[1:]):
            for box in boxes:
                if segment_intersects_box(a, b, box.expanded(margin)):
                    warnings.append(f"WARN arrow {eid!r} crosses node {box.id!r} ({box.label})")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Excalidraw legal diagram layout.")
    parser.add_argument("excalidraw_file", type=Path)
    parser.add_argument("--margin", type=float, default=4.0)
    args = parser.parse_args()
    warnings = validate(args.excalidraw_file, args.margin)
    if warnings:
        print("\n".join(warnings))
        return 1
    print(f"PASS {args.excalidraw_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
