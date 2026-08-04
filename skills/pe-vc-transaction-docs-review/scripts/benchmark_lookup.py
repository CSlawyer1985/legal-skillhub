#!/usr/bin/env python3
"""Look up internal VC/PE market benchmarks without exposing source names."""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "references" / "benchmark-data.json"
PERCENTAGE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)%")


def load_data(path: Path = DATA) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("benchmarks"), list):
        raise ValueError("benchmark-data.json must contain a benchmarks list")
    return data


def rank_matches(items: list[dict], query: str, all_terms: bool = False, exact: bool = False) -> list[dict]:
    normalized = query.strip().lower()
    terms = [term for term in normalized.split() if term]
    scored: list[tuple[int, str, dict]] = []
    for item in items:
        labels = [str(item.get("id", "")), *(str(alias) for alias in item.get("aliases", []))]
        labels_lower = [label.lower() for label in labels]
        haystack = " ".join(labels_lower)
        if exact:
            matched = normalized in labels_lower
            score = 1000 if matched else 0
        else:
            hits = sum(term in haystack for term in terms)
            matched = bool(terms) and (hits == len(terms) if all_terms else hits > 0)
            score = hits * 10
            if normalized in labels_lower:
                score += 500
            elif normalized and normalized in haystack:
                score += 100
        if matched:
            scored.append((score, str(item.get("id", "")), item))
    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    return [item for _, _, item in scored]


def approximate_percentages(text: str) -> str:
    """Round user-facing percentages while retaining exact source data internally."""

    def replace(match: re.Match[str]) -> str:
        value = Decimal(match.group(1))
        if Decimal("0") < value < Decimal("1"):
            return "less than 1%"
        rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"about {rounded}%"

    return PERCENTAGE.sub(replace, text)


def public_match(item: dict) -> dict:
    result = {
        key: item.get(key)
        for key in ("id", "aliases", "benchmark", "review_use")
        if key in item
    }
    for key in ("benchmark", "review_use"):
        if isinstance(result.get(key), str):
            result[key] = approximate_percentages(result[key])
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all-terms", action="store_true", help="Require every query term to match an ID or alias.")
    ap.add_argument("--exact", action="store_true", help="Match an exact benchmark ID or alias.")
    ap.add_argument("--internal", action="store_true", help="Include internal provenance for source verification.")
    args = ap.parse_args()

    try:
        data = load_data()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not load benchmark data: {exc}", file=sys.stderr)
        return 2

    query = " ".join(args.query)
    matches = rank_matches(data["benchmarks"], query, args.all_terms, args.exact)
    display_matches = matches if args.internal else [public_match(item) for item in matches]
    payload = {
        "benchmark_period": data.get("benchmark_period"),
        "last_verified": data.get("last_verified"),
        "source_label_for_outputs": data.get("source_label_for_outputs"),
        "do_not_name_source_in_user_outputs": data.get("do_not_name_source_in_user_outputs"),
        "default_method": data.get("default_method"),
        "matches": display_matches,
    }
    if args.internal:
        payload["source_registry"] = data.get("source_registry")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if matches else 1
    if not matches:
        print(
            "No benchmark match. Try redemption, anti-dilution, liquidation preference, ROFR, co-sale, 信息权, 回购, or 注册资本.",
            file=sys.stderr,
        )
        return 1

    print(f"Benchmark period: {data.get('benchmark_period', 'not specified')}")
    print(f"Method: {data.get('default_method', 'not specified')}\n")
    if args.internal:
        source_ids = sorted({citation.get("source_id") for item in matches for citation in item.get("citations", [])})
        print(f"Internal source IDs: {', '.join(source_ids) or 'not specified'}")
        print(f"Verified: {data.get('last_verified', 'not specified')}\n")
    for item in display_matches:
        print(f"## {item['id']}")
        print(f"Benchmark: {item['benchmark']}")
        print(f"Review use: {item['review_use']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
