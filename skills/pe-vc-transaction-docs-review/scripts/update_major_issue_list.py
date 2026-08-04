#!/usr/bin/env python3
"""Merge later-round updates into a Major Issue List while preserving Issue IDs."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from review_schema import (
    MAJOR_HEADERS,
    canonical_major_row,
    detect_language,
    localized_major_row,
    normalize_language,
)


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        return headers, [canonical_major_row(row) for row in reader]


def validate_ids(rows: list[dict[str, str]], label: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        issue_id = row["issue_id"]
        if not issue_id:
            errors.append(f"{label} row {index}: missing Issue ID")
        elif issue_id in seen:
            errors.append(f"{label} row {index}: duplicate Issue ID {issue_id}")
        seen.add(issue_id)
    return errors


def merge_rows(existing: list[dict[str, str]], updates: list[dict[str, str]], allow_new: bool) -> list[dict[str, str]]:
    by_id = {row["issue_id"]: dict(row) for row in existing}
    order = [row["issue_id"] for row in existing]
    for update in updates:
        issue_id = update["issue_id"]
        if issue_id not in by_id:
            if not allow_new:
                raise ValueError(f"Update contains unknown Issue ID {issue_id}; use --allow-new to append it")
            if any(not update[key] for key in update):
                raise ValueError(f"New Issue ID {issue_id} must provide all five Major Issue List fields")
            by_id[issue_id] = dict(update)
            order.append(issue_id)
            continue
        for key, value in update.items():
            if key != "issue_id" and value:
                by_id[issue_id][key] = value
    return [by_id[issue_id] for issue_id in order]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("existing", type=Path, help="Existing Major Issue List CSV.")
    ap.add_argument("updates", type=Path, help="CSV with the same Issue IDs and only fields that changed.")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--allow-new", action="store_true", help="Append fully populated new Issue IDs.")
    ap.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    args = ap.parse_args()

    try:
        existing_headers, existing = read_rows(args.existing)
        update_headers, updates = read_rows(args.updates)
    except (OSError, csv.Error) as exc:
        print(f"Could not read Major Issue List: {exc}", file=sys.stderr)
        return 2

    errors = validate_ids(existing, "existing") + validate_ids(updates, "updates")
    if not existing:
        errors.append("existing Major Issue List is empty")
    if not updates:
        errors.append("updates file is empty")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    language = normalize_language(args.language, existing_headers, [])
    if args.language == "auto" and detect_language(update_headers) != language:
        print("Warning: update headers use a different language; output follows the existing list.", file=sys.stderr)
    try:
        merged = merge_rows(existing, updates, args.allow_new)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out = None
    close = False
    try:
        if args.output:
            out = args.output.open("w", newline="", encoding="utf-8-sig")
            close = True
        else:
            out = sys.stdout
        writer = csv.DictWriter(out, fieldnames=MAJOR_HEADERS[language])
        writer.writeheader()
        for row in merged:
            writer.writerow(localized_major_row(row, language))
    except OSError as exc:
        print(f"Could not write updated Major Issue List: {exc}", file=sys.stderr)
        return 2
    finally:
        if close and out is not None:
            out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
