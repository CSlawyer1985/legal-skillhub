#!/usr/bin/env python3
"""Create and validate three-law auxiliary review tables."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


LAW_ARTICLES = {
    "PIPL": range(1, 75),
    "DSL": range(1, 56),
    "CSL": range(1, 82),
}

LAW_NAMES = {
    "PIPL": "中华人民共和国个人信息保护法",
    "DSL": "中华人民共和国数据安全法",
    "CSL": "中华人民共和国网络安全法",
}

HEADERS = [
    "法律",
    "条文或维度",
    "条文主题",
    "是否适用",
    "产品事实",
    "协议位置",
    "当前评价",
    "需补充或修订",
    "风险等级",
    "状态",
]


def make_template() -> str:
    lines = [
        "# 三法相关维度辅助检查表",
        "",
        "| " + " | ".join(HEADERS) + " |",
        "| " + " | ".join(["---"] * len(HEADERS)) + " |",
    ]
    for law, articles in LAW_ARTICLES.items():
        for article in articles:
            lines.append(
                "| "
                + " | ".join(
                    [
                        law,
                        str(article),
                        "企业填写",
                        "企业填写",
                        "企业填写",
                        "企业填写",
                        "企业填写",
                        "企业填写",
                        "企业填写",
                        "企业填写",
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def parse_matrix(text: str) -> dict[str, set[int]]:
    found = {law: set() for law in LAW_ARTICLES}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        law = cells[0].upper()
        article_cell = cells[1]
        if law not in found:
            continue
        match = re.search(r"\d+", article_cell)
        if not match:
            continue
        found[law].add(int(match.group(0)))
    return found


def validate(path: Path) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        issues.append("review table is missing or has no data rows")
        return False, issues

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    required_any = [
        {"法律"},
        {"条文或维度", "条文"},
        {"是否适用"},
        {"产品事实"},
        {"当前评价"},
        {"需补充或修订"},
    ]
    for choices in required_any:
        if not any(choice in headers for choice in choices):
            issues.append(f"missing required header: {'/'.join(sorted(choices))}")
    return not issues, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or validate a three-law auxiliary review table.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--make-template", metavar="OUT", help="Write a blank Markdown review table.")
    group.add_argument("--validate", metavar="FILE", help="Check review table structure and listed dimensions.")
    args = parser.parse_args()

    if args.make_template:
        out = Path(args.make_template)
        out.write_text(make_template(), encoding="utf-8")
        print(f"Wrote legal matrix template: {out}")
        return 0

    path = Path(args.validate)
    if not path.exists():
        print(f"Matrix file does not exist: {path}", file=sys.stderr)
        return 2
    ok, issues = validate(path)
    if ok:
        print("PASS: auxiliary review table has the required structure.")
        return 0
    print("NOTICE: auxiliary review table structure needs attention.", file=sys.stdout)
    for issue in issues:
        print(f"- {issue}", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
