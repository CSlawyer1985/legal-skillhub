#!/usr/bin/env python3
"""Validate cross-file contracts inside the VC/PE review skill package."""

from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

from refresh_legal_authorities import validate_registry as validate_legal_registry
from review_schema import COMMENT_HEADERS, ISSUE_HEADERS, MAJOR_HEADERS


ROOT = Path(__file__).resolve().parents[1]
RESOURCE_LINK = re.compile(r"(?<![A-Za-z0-9_.-])((?:references|scripts|assets)/[A-Za-z0-9_./&:-]+(?:\.md|\.json|\.py|\.swift|\.csv))")
USER_ABSOLUTE_PATH = re.compile("/" + "Users/" + r"[^/\s]+/")
EXPECTED_BENCHMARK_IDS = {
    "transaction_structure", "preemptive_right", "rofr", "co_sale", "redemption",
    "redemption_obligors", "redemption_price", "anti_dilution", "drag_along",
    "preferred_dividend", "protective_provisions", "board_seat", "esop",
    "liquidation_preference", "founder_restrictions", "founder_secondary_sale",
    "information_rights", "rw_survival", "indemnity", "investor_transfer_restrictions",
    "mfn", "registered_capital_contribution", "governing_law_dispute",
}


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path.relative_to(ROOT)}: top-level JSON must be an object")
        return {}
    return data


def validate_data_registry(path: Path, list_key: str, required: set[str], errors: list[str]) -> None:
    data = load_json(path, errors)
    items = data.get(list_key)
    if not isinstance(items, list) or not items:
        errors.append(f"{path.relative_to(ROOT)}: {list_key} must be a non-empty list")
        return
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path.relative_to(ROOT)} row {index}: item must be an object")
            continue
        missing = required - set(item)
        if missing:
            errors.append(f"{path.relative_to(ROOT)} row {index}: missing {sorted(missing)}")
        identifier = str(item.get("id", ""))
        if not identifier:
            errors.append(f"{path.relative_to(ROOT)} row {index}: empty id")
        elif identifier in seen:
            errors.append(f"{path.relative_to(ROOT)} row {index}: duplicate id {identifier}")
        seen.add(identifier)


def csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle), [])


def validate_templates(errors: list[str]) -> None:
    expected = {
        ROOT / "assets" / "issue-log-template.csv": ISSUE_HEADERS["en"],
        ROOT / "assets" / "issue-log-template-zh.csv": ISSUE_HEADERS["zh"],
        ROOT / "assets" / "comment-plan-template.csv": COMMENT_HEADERS["en"],
        ROOT / "assets" / "comment-plan-template-zh.csv": COMMENT_HEADERS["zh"],
        ROOT / "assets" / "major-issue-list-template.csv": MAJOR_HEADERS["en"],
        ROOT / "assets" / "major-issue-list-template-zh.csv": MAJOR_HEADERS["zh"],
    }
    for path, header in expected.items():
        try:
            actual = csv_header(path)
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: could not read: {exc}")
            continue
        if actual != header:
            errors.append(f"{path.relative_to(ROOT)}: header does not match shared schema")


def parse_date(value: object, label: str, errors: list[str]) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label}: invalid or missing ISO date {value!r}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-authority-age-days", type=int, default=180)
    args = ap.parse_args()
    if args.max_authority_age_days < 1:
        print("[ERROR][CONSISTENCY-INPUT-001] --max-authority-age-days must be positive", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    skill_path = ROOT / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    if len(skill_text.splitlines()) > 500:
        errors.append("SKILL.md exceeds the 500-line progressive-disclosure limit")

    markdown_files = [skill_path, *sorted((ROOT / "references").glob("*.md"))]
    all_links: set[str] = set()
    for markdown in markdown_files:
        text = markdown.read_text(encoding="utf-8")
        for relative in RESOURCE_LINK.findall(text):
            all_links.add(relative)
            if not (ROOT / relative).exists():
                errors.append(f"{markdown.relative_to(ROOT)}: broken resource link {relative}")

    for reference in sorted((ROOT / "references").iterdir()):
        if reference.suffix not in {".md", ".json"}:
            continue
        relative = f"references/{reference.name}"
        if relative not in skill_text:
            errors.append(f"SKILL.md does not directly route to {relative}")

    for forbidden in ["README.md", "INSTALLATION_GUIDE.md", "CHANGELOG.md"]:
        if (ROOT / forbidden).exists():
            errors.append(f"extraneous skill-root documentation found: {forbidden}")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".md", ".py", ".json", ".yaml", ".yml", ".csv", ".swift"}:
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeError:
                continue
            if USER_ABSOLUTE_PATH.search(text):
                errors.append(f"{path.relative_to(ROOT)}: contains a user-specific absolute path")

    for script in sorted((ROOT / "scripts").glob("*.py")):
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except (OSError, SyntaxError) as exc:
            errors.append(f"{script.relative_to(ROOT)}: Python syntax error: {exc}")

    validate_data_registry(
        ROOT / "references" / "benchmark-data.json",
        "benchmarks",
        {"id", "aliases", "benchmark", "review_use"},
        errors,
    )
    validate_data_registry(
        ROOT / "references" / "legal-authorities.json",
        "authorities",
        {"id", "title", "authority_level", "status", "official_url", "aliases", "topics", "review_use", "caveat"},
        errors,
    )

    legal_data = load_json(ROOT / "references" / "legal-authorities.json", errors)
    legal_report = validate_legal_registry(legal_data)
    errors.extend(f"legal-authorities.json: {error}" for error in legal_report["errors"])
    verified = parse_date(legal_data.get("last_verified"), "legal-authorities.json last_verified", errors)
    if verified:
        age = (dt.date.today() - verified).days
        if age > args.max_authority_age_days:
            errors.append(f"legal-authorities.json is stale: {age} days old")
        elif age > 90:
            warnings.append(f"legal-authorities.json is {age} days old; refresh before high-stakes reliance")

    benchmark_data = load_json(ROOT / "references" / "benchmark-data.json", errors)
    parse_date(benchmark_data.get("last_verified"), "benchmark-data.json last_verified", errors)
    benchmark_rows = benchmark_data.get("benchmarks", [])
    benchmark_ids = {
        item.get("id") for item in benchmark_rows
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(benchmark_rows, list) else set()
    if len(benchmark_rows) != len(EXPECTED_BENCHMARK_IDS) or benchmark_ids != EXPECTED_BENCHMARK_IDS:
        missing = sorted(EXPECTED_BENCHMARK_IDS - benchmark_ids)
        unexpected = sorted(benchmark_ids - EXPECTED_BENCHMARK_IDS)
        errors.append(
            "benchmark-data.json must contain exactly 23 expected unique topics "
            f"(missing={missing}, unexpected={unexpected}, rows={len(benchmark_rows) if isinstance(benchmark_rows, list) else 'invalid'})"
        )
    for index, item in enumerate(benchmark_rows if isinstance(benchmark_rows, list) else [], start=1):
        if not isinstance(item, dict) or any(not item.get(field) for field in ("id", "aliases", "benchmark", "review_use")):
            errors.append(f"benchmark-data.json row {index}: incomplete required fields")
    if benchmark_data.get("do_not_name_source_in_user_outputs") is not True:
        errors.append("benchmark-data.json must keep do_not_name_source_in_user_outputs=true")
    if benchmark_data.get("distribution_profile") == "public":
        if "source_registry" in benchmark_data:
            errors.append("public benchmark-data.json must not contain source_registry")
        for item in benchmark_data.get("benchmarks", []):
            if isinstance(item, dict) and "citations" in item:
                errors.append(f"public benchmark {item.get('id', '<unknown>')} must not contain citations")
    else:
        from audit_benchmark_provenance import validate_data as validate_benchmark_provenance

        benchmark_report = validate_benchmark_provenance(benchmark_data, verify_source_text=False)
        errors.extend(f"benchmark-data.json: {error}" for error in benchmark_report["errors"])

    validate_templates(errors)

    agent_text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if f"$${ROOT.name}" in agent_text:
        errors.append("agents/openai.yaml contains a malformed skill invocation")
    if f"${ROOT.name}" not in agent_text:
        errors.append("agents/openai.yaml default_prompt must mention the skill with $skill-name")

    for warning in warnings:
        print(f"[WARNING][CONSISTENCY-WARNING] {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"[ERROR][CONSISTENCY-BLOCKING] {error}", file=sys.stderr)
        print(
            f"[FAILED][CONSISTENCY-BLOCKING] {len(errors)} blocking error(s). "
            "Next step: fix every listed file or resource error, then rerun this validator before delivery.",
            file=sys.stderr,
        )
        return 1
    print(
        f"OK: skill consistency validated ({len(markdown_files)} markdown files, "
        f"{len(list((ROOT / 'scripts').glob('*.py')))} Python scripts, {len(all_links)} resource links, "
        f"{len(benchmark_rows) if isinstance(benchmark_rows, list) else 0} complete benchmark topics)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
