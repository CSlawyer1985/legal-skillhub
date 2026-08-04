#!/usr/bin/env python3
"""Validate bilingual Major Issue List shape and negotiation state."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from review_schema import MAJOR_KEYS, canonical_major_row, statuses_in_text, value_for


BANNED_SOURCE = re.compile(r"(?!)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("major_issue_list", type=Path)
    ap.add_argument("--allow-empty", action="store_true")
    args = ap.parse_args()

    try:
        with args.major_issue_list.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            raw_rows = list(reader)
    except (OSError, csv.Error) as exc:
        print(f"Could not read Major Issue List: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if not headers:
        errors.append("missing header row")
    if len(headers) > 5:
        errors.append(f"too many columns: {len(headers)}; Major Issue List must not exceed 5 columns")
    if len(headers) < 5:
        errors.append(f"too few columns: {len(headers)}; Major Issue List requires exactly 5 columns")
    if any(None in row for row in raw_rows):
        errors.append("one or more rows contain values beyond the declared five columns")

    recognized = {key for key in MAJOR_KEYS if any(value_for({header: "x"}, key, major=True) for header in headers)}
    for key in MAJOR_KEYS:
        if key not in recognized:
            errors.append(f"missing required semantic column: {key}")

    if not raw_rows and not args.allow_empty:
        errors.append("no major issues found")

    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_rows, start=1):
        row = canonical_major_row(raw)
        joined = " ".join(str(value or "") for key, value in raw.items() if key is not None)
        if BANNED_SOURCE.search(joined):
            errors.append(f"row {index}: user-facing output names a banned benchmark source")
        for key in MAJOR_KEYS:
            if not row[key]:
                errors.append(f"row {index}: missing {key}")
        issue_id = row["issue_id"]
        if issue_id:
            if issue_id in seen_ids:
                errors.append(f"row {index}: duplicate Issue ID {issue_id}")
            seen_ids.add(issue_id)
        statuses = statuses_in_text(row["counterparty_status"])
        if len(statuses) != 1:
            errors.append(
                f"row {index}: Counterparty Position / Status must contain exactly one supported status; found {statuses or 'none'}"
            )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"FAILED: {len(errors)} validation issue(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(raw_rows)} major issue(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
