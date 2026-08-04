#!/usr/bin/env python3
"""Look up current PRC legal-authority cards for VC/PE agreement review."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "references" / "legal-authorities.json"


def load_data(path: Path = DATA) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("authorities"), list):
        raise ValueError("legal-authorities.json must contain an authorities list")
    return data


def searchable_text(item: dict) -> str:
    provisions = " ".join(
        f"{provision.get('article', '')} {provision.get('proposition', '')}" for provision in item.get("provisions", [])
    )
    return " ".join([
        str(item.get("id", "")),
        str(item.get("title", "")),
        str(item.get("authority_level", "")),
        str(item.get("status", "")),
        " ".join(str(alias) for alias in item.get("aliases", [])),
        " ".join(str(topic) for topic in item.get("topics", [])),
        provisions,
    ]).lower()


def filter_authorities(items: list[dict], query: list[str], match_all: bool, effective_only: bool) -> list[dict]:
    terms = [term.lower() for term in query]
    matches: list[tuple[int, str, dict]] = []
    for item in items:
        if effective_only and not str(item.get("status", "")).startswith("effective"):
            continue
        blob = searchable_text(item)
        hits = sum(term in blob for term in terms)
        if terms and (hits == len(terms) if match_all else hits > 0):
            score = hits * 10
            if " ".join(terms) == str(item.get("id", "")).lower():
                score += 500
            matches.append((score, str(item.get("id", "")), item))
    matches.sort(key=lambda entry: (-entry[0], entry[1]))
    return [item for _, _, item in matches]


def freshness_days(last_verified: str) -> int:
    verified = dt.date.fromisoformat(last_verified)
    return (dt.date.today() - verified).days


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query", nargs="+")
    ap.add_argument("--any", action="store_true", help="Match any query term instead of all terms.")
    ap.add_argument("--effective-only", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check-freshness", action="store_true", help="Fail if the authority registry is older than --max-age-days.")
    ap.add_argument("--max-age-days", type=int, default=90)
    args = ap.parse_args()

    if args.max_age_days < 1:
        print("--max-age-days must be positive", file=sys.stderr)
        return 2
    try:
        data = load_data()
        age_days = freshness_days(data["last_verified"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Could not load legal-authority data: {exc}", file=sys.stderr)
        return 2

    matches = filter_authorities(data["authorities"], args.query, not args.any, args.effective_only)
    payload = {
        "last_verified": data.get("last_verified"),
        "age_days": age_days,
        "freshness_rule": data.get("freshness_rule"),
        "matches": matches,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Authority registry verified: {data.get('last_verified')} ({age_days} day(s) ago)\n")
        for item in matches:
            print(f"## {item['title']}")
            print(f"ID: {item['id']}")
            print(f"Level/status: {item['authority_level']} / {item['status']}")
            print(f"Effective date: {item.get('effective_date') or 'not effective / not specified'}")
            print(f"Official source: {item['official_url']}")
            for provision in item.get("provisions", []):
                print(f"- Article/section {provision['article']}: {provision['proposition']}")
            print(f"Review use: {item['review_use']}")
            print(f"Caveat: {item['caveat']}\n")
    if not matches:
        print("No legal-authority match.", file=sys.stderr)
        return 1
    if args.check_freshness and age_days > args.max_age_days:
        print(
            f"Authority registry is stale ({age_days} days; maximum {args.max_age_days}); refresh official sources before relying on it.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
