#!/usr/bin/env python3
"""Validate bilingual issue-log completeness and source discipline."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from review_schema import canonical_risk, value_for


LEGAL_HINTS = re.compile(
    r"法律|效力|执行|公司法|民法典|仲裁|减资|出资|章程|司法解释|"
    r"\b(?:legal|law|validity|enforceability|arbitration|statute|regulation)\b",
    re.I,
)
BANNED_SOURCE = re.compile(r"(?!)")
DELETE_INSTRUCTION = re.compile(r"^(?:删除|删去|delete\b|remove\b)", re.I)

BASE_REQUIRED = ["issue", "position", "market", "risk", "proposed", "fallback"]


def load_rows(path: Path) -> tuple[list[str], list[dict]]:
    if path.suffix.lower() == ".json":
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, list):
            rows = obj
        elif isinstance(obj, dict) and isinstance(obj.get("issues"), list):
            rows = obj["issues"]
        else:
            raise ValueError("JSON must be a list or an object with an issues list")
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError("every JSON issue must be an object")
        headers = sorted({str(key) for row in rows for key in row})
        return headers, rows
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def has_location(row: dict) -> bool:
    return bool(value_for(row, "location") or (value_for(row, "file") and value_for(row, "clause")))


def complete_wording(value: str, minimum: int) -> bool:
    stripped = re.sub(r"\s+", "", value)
    return len(stripped) >= minimum or bool(DELETE_INSTRUCTION.search(value.strip()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("issue_log", type=Path)
    ap.add_argument("--allow-empty", action="store_true")
    ap.add_argument("--min-proposed-length", type=int, default=12)
    args = ap.parse_args()

    if args.min_proposed_length < 1:
        print("--min-proposed-length must be positive", file=sys.stderr)
        return 2
    try:
        headers, rows = load_rows(args.issue_log)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error) as exc:
        print(f"Could not read issue log: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if not headers:
        errors.append("missing header/schema")
    if not rows and not args.allow_empty:
        errors.append("no issues found")

    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        joined = " ".join(str(value or "") for key, value in row.items() if key is not None)
        if BANNED_SOURCE.search(joined):
            errors.append(f"row {index}: user-facing output names a banned benchmark source")
        if not has_location(row):
            errors.append(f"row {index}: missing file/clause location")
        for semantic in BASE_REQUIRED:
            if not value_for(row, semantic):
                errors.append(f"row {index}: missing {semantic}")

        risk = value_for(row, "risk")
        if risk and canonical_risk(risk) is None:
            errors.append(f"row {index}: unsupported risk label {risk!r}")

        legal_context = " ".join([value_for(row, "issue_type"), value_for(row, "issue")])
        if LEGAL_HINTS.search(legal_context):
            if not value_for(row, "legal_basis"):
                errors.append(f"row {index}: legal/enforcement issue lacks legal basis")
            if not value_for(row, "authority_status"):
                errors.append(f"row {index}: legal/enforcement issue lacks authority/verification status")

        proposed = value_for(row, "proposed")
        if proposed and not complete_wording(proposed, args.min_proposed_length):
            errors.append(f"row {index}: proposed wording appears too short to be complete")

        issue_id = value_for(row, "number")
        if issue_id:
            if issue_id in seen_ids:
                errors.append(f"row {index}: duplicate issue identifier {issue_id}")
            seen_ids.add(issue_id)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"FAILED: {len(errors)} validation issue(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(rows)} issue(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
