#!/usr/bin/env python3
"""Validate this Skill's Markdown output against its output contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SKILL_ROOT / "references" / "output-contract.json"


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def section_text(text: str, heading: str, headings: list[str]) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    later = [text.find(item, start + len(heading)) for item in headings]
    later = [position for position in later if position >= 0]
    return text[start : min(later) if later else len(text)]


def table_line_count(block: str) -> int:
    count = 0
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        count += 1
    return count


def validate(text: str, contract: dict) -> list[str]:
    errors: list[str] = []
    minimum = int(contract["minimum_characters"])
    if len(text.strip()) < minimum:
        errors.append(f"内容过短：至少 {minimum} 个字符")

    headings = contract["required_headings"]
    positions = [text.find(heading) for heading in headings]
    for heading, position in zip(headings, positions):
        if position < 0:
            errors.append(f"缺少标题：{heading}")
    present_positions = [position for position in positions if position >= 0]
    if present_positions != sorted(present_positions):
        errors.append("章节顺序不符合输出契约")

    for heading, minimum_rows in contract["section_requirements"].items():
        block = section_text(text, heading, headings)
        if block and table_line_count(block) < int(minimum_rows):
            errors.append(f"{heading} 的表格内容不足，至少需要 {minimum_rows} 行")

    for term in contract["required_terms"]:
        if term not in text:
            errors.append(f"缺少必要字段：{term}")

    for pattern in contract["forbidden_patterns"]:
        if pattern in text:
            errors.append(f"包含禁止表达：{pattern}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-output", required=True, type=Path)
    args = parser.parse_args()
    output_path = args.check_output.expanduser().resolve()

    if not output_path.is_file():
        print(f"FAIL: 输出文件不存在：{output_path}", file=sys.stderr)
        return 2
    try:
        text = output_path.read_text(encoding="utf-8")
        contract = load_contract()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: 无法读取输出或契约：{exc}", file=sys.stderr)
        return 2

    errors = validate(text, contract)
    if errors:
        print("FAIL: 输出未通过校验", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"PASS: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
