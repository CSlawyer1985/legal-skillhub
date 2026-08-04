#!/usr/bin/env python3
"""Convert a bilingual CSV issue log into a comment-plan CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from review_schema import COMMENT_HEADERS, normalize_language, value_for


LABELS = {
    "en": {
        "issue": "Issue",
        "position": "Our position",
        "market": "Market context",
        "legal": "Legal basis",
        "authority": "Authority / verification status",
        "proposed": "Proposed revised wording",
        "fallback": "Fallback",
        "question": "Client/counterparty question",
    },
    "zh": {
        "issue": "问题",
        "position": "我方立场",
        "market": "市场数据",
        "legal": "法律依据",
        "authority": "事实/法律依据核验状态",
        "proposed": "建议修改",
        "fallback": "Fallback",
        "question": "需客户/对方确认",
    },
}


def output_values(row: dict, language: str) -> list[str]:
    issue = value_for(row, "issue")
    position = value_for(row, "position")
    market = value_for(row, "market")
    legal = value_for(row, "legal_basis")
    authority = value_for(row, "authority_status")
    proposed = value_for(row, "proposed")
    fallback = value_for(row, "fallback")
    needs_input = value_for(row, "needs_client_input")
    labels = LABELS[language]

    comment_parts = []
    for key, value in [
        ("issue", issue),
        ("position", position),
        ("market", market),
        ("legal", legal),
        ("authority", authority),
        ("proposed", proposed),
        ("fallback", fallback),
        ("question", needs_input),
    ]:
        if value:
            comment_parts.append(f"{labels[key]}: {value}")

    file_ = value_for(row, "file")
    location = value_for(row, "clause") or value_for(row, "location")
    return [
        file_,
        location,
        value_for(row, "current_text"),
        value_for(row, "risk"),
        value_for(row, "issue_type"),
        "\n".join(comment_parts),
        proposed,
        fallback,
        needs_input,
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("issue_log", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    args = ap.parse_args()

    try:
        with args.issue_log.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        print(f"Could not read issue log: {exc}", file=sys.stderr)
        return 2

    if not headers:
        print("Issue log has no header row.", file=sys.stderr)
        return 2
    if not rows:
        print("Issue log contains no issues.", file=sys.stderr)
        return 1

    language = normalize_language(args.language, headers, rows)
    fieldnames = COMMENT_HEADERS[language]
    out = None
    close = False
    try:
        if args.output:
            out = args.output.open("w", newline="", encoding="utf-8-sig")
            close = True
        else:
            out = sys.stdout
        writer = csv.writer(out)
        writer.writerow(fieldnames)
        for row in rows:
            writer.writerow(output_values(row, language))
    except OSError as exc:
        print(f"Could not write comment plan: {exc}", file=sys.stderr)
        return 2
    finally:
        if close and out is not None:
            out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
