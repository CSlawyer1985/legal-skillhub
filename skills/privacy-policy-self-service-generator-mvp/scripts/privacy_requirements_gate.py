#!/usr/bin/env python3
"""Create and validate the hard gate for original privacy agreement requirements."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIREMENTS = [
    ("P6", "编制程序"),
    ("P7.2", "发布主体和适用范围"),
    ("P7.3", "摘要"),
    ("P7.4", "收集使用个人信息规则"),
    ("P7.5", "个人信息安全规则"),
    ("P7.6", "个人信息主体权利规则"),
    ("P7.7", "个人信息跨境流动规则"),
    ("P7.8", "隐私协议更新规则"),
    ("P7.9", "联系方式和外部争议解决"),
    ("P8", "发布和可视化"),
    ("P9", "隐私协议修订"),
    ("P10", "争议纠纷处理"),
]

FAIL_STATUSES = {"未覆盖", "缺失", "不通过"}
WARN_STATUSES = {"部分覆盖", "事实需确认", "需企业确认", "需法务复核"}

HEADERS = ["要求ID", "要求名称", "覆盖状态", "协议位置", "企业事实", "问题或补充项"]


def make_template() -> str:
    lines = [
        "# 隐私协议要求覆盖矩阵",
        "",
        "| " + " | ".join(HEADERS) + " |",
        "| " + " | ".join(["---"] * len(HEADERS)) + " |",
    ]
    for req_id, name in REQUIREMENTS:
        lines.append(f"| {req_id} | {name} | 已覆盖 | 企业填写 | 企业填写 | 企业填写 |")
    return "\n".join(lines) + "\n"


def parse_rows(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    valid_ids = {req_id for req_id, _ in REQUIREMENTS}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        req_id = cells[0]
        if req_id in valid_ids:
            rows[req_id] = cells
    return rows


def validate(path: Path) -> tuple[bool, list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    rows = parse_rows(text)
    issues: list[str] = []
    warnings: list[str] = []
    for req_id, name in REQUIREMENTS:
        row = rows.get(req_id)
        if not row:
            issues.append(f"{req_id} missing: {name}")
            continue
        status = row[2]
        if any(term in status for term in FAIL_STATUSES):
            issues.append(f"{req_id} not covered: {name} ({status})")
        elif any(term in status for term in WARN_STATUSES):
            warnings.append(f"{req_id} needs attention: {name} ({status})")
        elif not re.search(r"已覆盖|不适用", status):
            warnings.append(f"{req_id} has unclear status: {name} ({status})")
    return not issues, issues, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or validate privacy agreement requirement coverage.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--make-template", metavar="OUT", help="Write a Markdown coverage matrix.")
    group.add_argument("--validate", metavar="FILE", help="Validate coverage matrix.")
    args = parser.parse_args()

    if args.make_template:
        out = Path(args.make_template)
        out.write_text(make_template(), encoding="utf-8")
        print(f"Wrote privacy requirements matrix template: {out}")
        return 0

    path = Path(args.validate)
    if not path.exists():
        print(f"Matrix file does not exist: {path}", file=sys.stderr)
        return 2

    ok, issues, warnings = validate(path)
    for warning in warnings:
        print(f"WARN: {warning}")
    if ok:
        print(f"PASS: matrix covers {len(REQUIREMENTS)} original privacy agreement requirements.")
        return 0
    print("FAIL: original privacy agreement requirements are not fully covered.", file=sys.stderr)
    for issue in issues:
        print(f"- {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
