"""
Contract Smart Compare - CLI Entry Point.

Compares two or more contract documents and generates diff reports.

Usage:
    python -m src.main compare <file_a> <file_b> [--output report.md]
    python -m src.main multi <files...> --labels <labels...> --output report.md
    python -m src.main risk <diff_file> [--model gpt-4o]

Commands:
    compare     Compare two contract files (FREE+)
    multi       Compare 3+ versions with timeline (PRO)
    parse       Parse a file and print extracted text
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.config import (
    TIER_FREE,
    TIER_STANDARD,
    TIER_PRO,
    LIMITS,
    TEMP_DIR,
    FREE_TOTAL_USES,
)
from src.billing import (
    charge_user,
    get_tier,
    is_dev_mode,
    get_free_usage_count,
)
from src.parsers import (
    parse_contract,
    ParseError,
    sanitize_path,
)
from src.diff_engine import (
    extract_clauses,
    compare_clauses,
    assess_risk,
    summarize_key_clauses,
    DiffError,
)
from src.report import (
    render_diff_report,
    render_multi_version_report,
)
from src.excel_exporter import (
    export_diff_to_excel,
    export_risk_report,
    export_multi_version_timeline,
    ExcelExportError,
)


def main():
    parser = argparse.ArgumentParser(
        description="Contract Smart Compare - AI-powered contract comparison tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two contract files")
    compare_parser.add_argument("file_a", help="Path to the first contract file")
    compare_parser.add_argument("file_b", help="Path to the second contract file")
    compare_parser.add_argument(
        "--label-a", default="合同A", help="Label for contract A"
    )
    compare_parser.add_argument(
        "--label-b", default="合同B", help="Label for contract B"
    )
    compare_parser.add_argument(
        "--output", "-o", default=None, help="Output Markdown file path"
    )
    compare_parser.add_argument(
        "--excel", action="store_true", help="Also export Excel diff list (STANDARD+)"
    )
    compare_parser.add_argument(
        "--include-same", action="store_true", help="Include unchanged clauses in report"
    )
    compare_parser.add_argument(
        "--model", default=None, help="AI model to use"
    )
    compare_parser.add_argument(
        "--user-id", default="anonymous", help="User ID for usage tracking"
    )
    compare_parser.add_argument(
        "--tier", default=None, help="Subscription tier override"
    )

    # multi command
    multi_parser = subparsers.add_parser("multi", help="Compare 3+ contract versions (PRO)")
    multi_parser.add_argument("files", nargs="+", help="Paths to contract files")
    multi_parser.add_argument(
        "--labels", nargs="+", default=None, help="Version labels"
    )
    multi_parser.add_argument(
        "--dates", nargs="+", default=None, help="Version dates (YYYY-MM-DD)"
    )
    multi_parser.add_argument(
        "--output", "-o", default=None, help="Output Markdown file path"
    )
    multi_parser.add_argument(
        "--excel", action="store_true", help="Also export Excel timeline"
    )
    multi_parser.add_argument(
        "--model", default=None, help="AI model to use"
    )
    multi_parser.add_argument(
        "--user-id", default="anonymous", help="User ID for usage tracking"
    )

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse a contract file and print text")
    parse_parser.add_argument("file", help="Path to the contract file")
    parse_parser.add_argument(
        "--max-chars", type=int, default=5000, help="Max characters to print"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "compare":
        cmd_compare(args)
    elif args.command == "multi":
        cmd_multi(args)
    elif args.command == "parse":
        cmd_parse(args)


def get_api_key() -> str:
    """Get API key from environment."""
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or ""


def cmd_compare(args):
    """Compare two contract files."""
    # Determine tier
    if args.tier:
        tier = args.tier
    else:
        tier, _ = get_tier()

    # Check tier limits
    if tier == TIER_FREE:
        limits = LIMITS[TIER_FREE]
        usage_count = get_free_usage_count(args.user_id)
        if usage_count >= FREE_TOTAL_USES:
            print(f"Error: FREE tier limit reached ({FREE_TOTAL_USES} uses/month)", file=sys.stderr)
            print(f"Upgrade to STANDARD or PRO at https://yk-global.com", file=sys.stderr)
            sys.exit(1)
    elif tier not in (TIER_STANDARD, TIER_PRO):
        tier = TIER_FREE

    limits = LIMITS.get(tier, LIMITS[TIER_FREE])

    # Validate file types
    ext_a = os.path.splitext(args.file_a)[1].lower().lstrip(".")
    ext_b = os.path.splitext(args.file_b)[1].lower().lstrip(".")

    allowed_types = limits.get("file_types", ["txt", "docx"])
    if ext_a not in allowed_types:
        print(f"Error: File type '.{ext_a}' not supported in {tier} tier", file=sys.stderr)
        print(f"Supported: {', '.join(allowed_types)}", file=sys.stderr)
        sys.exit(1)
    if ext_b not in allowed_types:
        print(f"Error: File type '.{ext_b}' not supported in {tier} tier", file=sys.stderr)
        print(f"Supported: {', '.join(allowed_types)}", file=sys.stderr)
        sys.exit(1)

    # Record usage (FREE tier)
    if tier == TIER_FREE:
        result = charge_user(args.user_id, tier)
        if not result["ok"]:
            print(f"Error: {result['message']}", file=sys.stderr)
            sys.exit(1)

    # Parse files
    print(f"Parsing {args.file_a}...", file=sys.stderr)
    try:
        text_a = parse_contract(args.file_a)
    except ParseError as e:
        print(f"Error parsing {args.file_a}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {args.file_b}...", file=sys.stderr)
    try:
        text_b = parse_contract(args.file_b)
    except ParseError as e:
        print(f"Error parsing {args.file_b}: {e}", file=sys.stderr)
        sys.exit(1)

    if not text_a or not text_b:
        print("Error: One or both files have no extractable text", file=sys.stderr)
        sys.exit(1)

    # Extract clauses
    api_key = get_api_key()
    model = args.model

    print("Extracting clauses from contract A...", file=sys.stderr)
    clauses_a = extract_clauses(text_a, api_key, model)

    print("Extracting clauses from contract B...", file=sys.stderr)
    clauses_b = extract_clauses(text_b, api_key, model)

    # Compare
    print("Comparing clauses...", file=sys.stderr)
    diff_items = compare_clauses(clauses_a, clauses_b, api_key, model)

    # Render report
    report = render_diff_report(
        diff_items,
        file_a_name=args.label_a,
        file_b_name=args.label_b,
        tier=tier,
        include_same=args.include_same,
    )

    # Excel export (STANDARD+)
    excel_path = None
    if args.excel and tier in (TIER_STANDARD, TIER_PRO):
        print("Exporting Excel report...", file=sys.stderr)
        try:
            excel_path = export_diff_to_excel(diff_items)
            print(f"Excel report: {excel_path}", file=sys.stderr)
        except ExcelExportError as e:
            print(f"Warning: Excel export failed: {e}", file=sys.stderr)

    # Output
    if args.output:
        os.makedirs(os.path.dirname(args.output) or "/tmp", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {args.output}", file=sys.stderr)
        if excel_path:
            # Copy excel to output dir
            import shutil
            excel_output = os.path.join(
                os.path.dirname(args.output) or "/tmp",
                os.path.basename(excel_path)
            )
            shutil.copy(excel_path, excel_output)
            print(f"Excel report copied to {excel_output}", file=sys.stderr)
    else:
        print(report)

    # Usage info for FREE tier
    if tier == TIER_FREE and not is_dev_mode():
        remaining = FREE_TOTAL_USES - get_free_usage_count(args.user_id)
        print(f"\n[INFO] FREE tier: {remaining}/{FREE_TOTAL_USES} uses remaining this month", file=sys.stderr)


def cmd_multi(args):
    """Compare 3+ contract versions (PRO tier only)."""
    tier, limits = get_tier()

    if not limits.get("multi_version", False):
        print("Error: Multi-version comparison requires PRO tier", file=sys.stderr)
        print("Visit https://yk-global.com to upgrade", file=sys.stderr)
        sys.exit(1)

    files = args.files
    if len(files) < 3:
        print("Error: Multi-version comparison requires at least 3 files", file=sys.stderr)
        sys.exit(1)

    labels = args.labels or [f"版本{i+1}" for i in range(len(files))]
    dates = args.dates or [datetime.now().strftime("%Y-%m-%d")] * len(files)

    file_info = [
        {"filename": f, "version_label": labels[i], "date": dates[i]}
        for i, f in enumerate(files)
    ]

    api_key = get_api_key()
    model = args.model

    # Parse all files
    all_texts = []
    all_clauses = []
    print(f"Parsing {len(files)} contract files...", file=sys.stderr)
    for f in files:
        print(f"  Parsing {f}...", file=sys.stderr)
        try:
            text = parse_contract(f)
            all_texts.append(text)
        except ParseError as e:
            print(f"Error parsing {f}: {e}", file=sys.stderr)
            sys.exit(1)

        clauses = extract_clauses(text, api_key, model)
        all_clauses.append(clauses)

    # Compare consecutive versions
    diff_results = []
    print("Comparing versions...", file=sys.stderr)
    for i in range(len(files) - 1):
        print(f"  Comparing version {i+1} vs {i+2}...", file=sys.stderr)
        diff = compare_clauses(all_clauses[i], all_clauses[i+1], api_key, model)
        diff_results.append(diff)

    # Risk assessment
    risk_items = []
    all_changed = []
    for dr in diff_results:
        all_changed.extend([d for d in dr if d["type"] in ("new", "modified", "deleted")])

    if all_changed:
        print("Assessing risk...", file=sys.stderr)
        risk_items = assess_risk(all_changed, api_key, model)

    # Key clause summaries
    key_summaries = {}
    print("Generating key clause summaries...", file=sys.stderr)
    for text, info in zip(all_texts, file_info):
        clauses = extract_clauses(text, api_key, model)
        summary = summarize_key_clauses(clauses, api_key, model)
        key_summaries[info["filename"]] = summary

    # Render report
    report = render_multi_version_report(
        all_clauses=all_clauses,
        file_info=file_info,
        diff_results=diff_results,
        key_summaries=key_summaries,
        risk_items=risk_items,
    )

    # Excel timeline (if requested)
    if args.excel:
        print("Exporting Excel timeline...", file=sys.stderr)
        try:
            excel_path = export_multi_version_timeline(file_info)
            print(f"Excel timeline: {excel_path}", file=sys.stderr)
        except ExcelExportError as e:
            print(f"Warning: Excel export failed: {e}", file=sys.stderr)

        if risk_items:
            try:
                risk_path = export_risk_report(risk_items)
                print(f"Risk report: {risk_path}", file=sys.stderr)
            except ExcelExportError as e:
                print(f"Warning: Risk report export failed: {e}", file=sys.stderr)

    # Output
    if args.output:
        os.makedirs(os.path.dirname(args.output) or "/tmp", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(report)


def cmd_parse(args):
    """Parse and print contract text."""
    print(f"Parsing {args.file}...", file=sys.stderr)
    try:
        text = parse_contract(args.file)
        print(text[: args.max_chars])
        if len(text) > args.max_chars:
            print(f"\n... (truncated, total {len(text)} chars)", file=sys.stderr)
    except ParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
