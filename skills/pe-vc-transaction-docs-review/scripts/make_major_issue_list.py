#!/usr/bin/env python3
"""Seed a bilingual Major Issue List from a VC/PE issue-log CSV."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from review_schema import (
    MAJOR_HEADERS,
    canonical_risk,
    localized_major_row,
    localized_status,
    normalize_language,
    truthy,
    value_for,
)


MAJOR_TERMS = {
    "redemption", "repurchase", "回购", "赎回", "liquidation", "清算", "anti-dilution",
    "anti dilution", "反稀释", "drag", "领售", "拖售", "rofr", "优先购买", "co-sale",
    "共同出售", "preemptive", "优先认购", "reserved matters", "protective", "保留事项",
    "保护性", "board", "董事", "information", "信息权", "inspection", "检查权", "mfn",
    "最优惠", "founder", "创始", "vesting", "限制性股权", "closing", "交割", "indemnity",
    "赔偿", "registered capital", "出资", "失权", "governing law", "适用法律", "arbitration",
    "仲裁", "章程", "articles", "maa", "m&a", "vie", "控制协议",
}

MINOR_TERMS = {"typo", "format", "formatting", "numbering", "punctuation", "错别字", "格式", "编号", "标点"}


def is_major(row: dict) -> bool:
    explicit = value_for(row, "major")
    if explicit:
        return truthy(explicit)

    risk = canonical_risk(value_for(row, "risk"))
    issue_type = value_for(row, "issue_type").lower()
    issue = value_for(row, "issue").lower()
    clause = (value_for(row, "clause") or value_for(row, "location")).lower()
    joined = " ".join([issue_type, issue, clause])
    if any(term in joined for term in MINOR_TERMS):
        return False
    if risk == "high":
        return True
    return risk == "medium" and any(term in joined for term in MAJOR_TERMS)


def build_row(row: dict, issue_id: str, language: str, round_name: str, owner: str) -> dict[str, str]:
    file_ = value_for(row, "file")
    clause = value_for(row, "clause") or value_for(row, "location")
    location = " - ".join(part for part in [file_, clause] if part)
    issue = value_for(row, "issue")
    risk = value_for(row, "risk") or ("中" if language == "zh" else "Medium")
    proposed = value_for(row, "proposed")
    fallback = value_for(row, "fallback")
    major_issue = f"{location}: {issue}" if location else issue

    if language == "zh":
        status = f"状态：{localized_status('open', language)}；对方立场：待确认；优先级：{risk}；轮次：{round_name}"
        next_parts = ["发送对方并在下一轮修订中持续跟踪"]
        if proposed:
            next_parts.append(f"建议文本：{proposed}")
        if fallback:
            next_parts.append(f"Fallback：{fallback}")
        if owner:
            next_parts.append(f"负责人：{owner}")
    else:
        status = f"Status: {localized_status('open', language)}; counterparty position: TBC; priority: {risk}; round: {round_name}"
        next_parts = ["Send to counterparty and track in the next markup"]
        if proposed:
            next_parts.append(f"proposed wording: {proposed}")
        if fallback:
            next_parts.append(f"fallback: {fallback}")
        if owner:
            next_parts.append(f"owner: {owner}")

    separator = "；" if language == "zh" else "; "
    canonical = {
        "issue_id": issue_id,
        "major_issue": major_issue,
        "position": value_for(row, "position"),
        "counterparty_status": status,
        "next_step": separator.join(next_parts),
    }
    return localized_major_row(canonical, language)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("issue_log", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--round")
    ap.add_argument("--owner", default="")
    ap.add_argument("--id-prefix", default="M")
    ap.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", args.id_prefix):
        print("--id-prefix must start with a letter and contain only letters, digits, '_' or '-'.", file=sys.stderr)
        return 2

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
    round_name = args.round or ("第一轮" if language == "zh" else "Round 1")
    selected = [row for row in rows if is_major(row)]
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
        for index, row in enumerate(selected, start=1):
            writer.writerow(build_row(row, f"{args.id_prefix}-{index:03d}", language, round_name, args.owner))
    except OSError as exc:
        print(f"Could not write Major Issue List: {exc}", file=sys.stderr)
        return 2
    finally:
        if close and out is not None:
            out.close()

    if not selected:
        print("No issues met the Major Issue criteria; wrote a header-only list.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
