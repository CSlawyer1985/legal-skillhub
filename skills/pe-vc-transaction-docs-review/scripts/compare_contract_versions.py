#!/usr/bin/env python3
"""Compare clean transaction-document versions at clause and paragraph level."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import extract_contract_text
import contract_clause_model


def extract_file(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return extract_contract_text.extract_docx(path, "full")
    if suffix == ".pdf":
        return extract_contract_text.extract_pdf(path)
    return extract_contract_text.extract_doc_or_other(path)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def location(paragraph: dict) -> str:
    if paragraph.get("page"):
        return f"page {paragraph['page']}, block {paragraph.get('page_block', paragraph['paragraph'])}"
    if paragraph.get("source_part"):
        return f"{paragraph['source_part']}, paragraph {paragraph.get('part_paragraph', paragraph['paragraph'])}"
    return f"paragraph {paragraph['paragraph']}"


def paragraph_record(paragraph: dict) -> dict[str, object]:
    return {
        "paragraph": paragraph.get("paragraph"),
        "location": location(paragraph),
        "text": paragraph.get("text", ""),
    }


def compare_documents(prior: Path, current: Path, high_volume_threshold: int = 500) -> dict:
    prior_result = extract_file(prior)
    current_result = extract_file(current)
    errors = []
    if prior_result.get("error"):
        errors.append(f"prior: {prior_result['error']}")
    if current_result.get("error"):
        errors.append(f"current: {current_result['error']}")
    prior_paragraphs = prior_result.get("paragraphs", [])
    current_paragraphs = current_result.get("paragraphs", [])
    if not prior_paragraphs:
        errors.append("prior: no extractable text")
    if not current_paragraphs:
        errors.append("current: no extractable text")
    if errors:
        return {
            "prior_file": str(prior),
            "current_file": str(current),
            "errors": errors,
            "change_blocks": [],
            "change_block_count": 0,
        }

    prior_normalized = [normalize_text(str(paragraph.get("text", ""))) for paragraph in prior_paragraphs]
    current_normalized = [normalize_text(str(paragraph.get("text", ""))) for paragraph in current_paragraphs]
    matcher = difflib.SequenceMatcher(None, prior_normalized, current_normalized, autojunk=False)
    changes: list[dict] = []
    unchanged_count = 0
    changed_prior_count = 0
    changed_current_count = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            unchanged_count += i2 - i1
            continue
        before = [paragraph_record(paragraph) for paragraph in prior_paragraphs[i1:i2]]
        after = [paragraph_record(paragraph) for paragraph in current_paragraphs[j1:j2]]
        changed_prior_count += len(before)
        changed_current_count += len(after)
        changes.append({
            "type": tag,
            "prior_range": [i1 + 1, i2] if i2 > i1 else None,
            "current_range": [j1 + 1, j2] if j2 > j1 else None,
            "prior": before,
            "current": after,
        })

    prior_clauses = contract_clause_model.build_clauses(prior_paragraphs)
    current_clauses = contract_clause_model.build_clauses(current_paragraphs)
    clause_alignment = contract_clause_model.align_clauses(prior_clauses, current_clauses)
    clause_changes = [item for item in clause_alignment if item["type"] != "unchanged"]
    clause_change_counts: dict[str, int] = {}
    for item in clause_changes:
        clause_change_counts[item["type"]] = clause_change_counts.get(item["type"], 0) + 1

    result = {
        "prior_file": str(prior),
        "current_file": str(current),
        "scope": "clean-version clause and paragraph comparison",
        "method": "explicit clause labels, exact-content alignment, split/merge detection, fuzzy fallback, plus paragraph SequenceMatcher",
        "prior_extraction_method": prior_result.get("method"),
        "current_extraction_method": current_result.get("method"),
        "prior_paragraph_count": len(prior_paragraphs),
        "current_paragraph_count": len(current_paragraphs),
        "unchanged_paragraph_count": unchanged_count,
        "changed_prior_paragraph_count": changed_prior_count,
        "changed_current_paragraph_count": changed_current_count,
        "change_blocks": changes,
        "change_block_count": len(changes),
        "similarity_ratio": round(matcher.ratio(), 6),
        "prior_clause_count": len(prior_clauses),
        "current_clause_count": len(current_clauses),
        "clause_changes": clause_changes,
        "clause_change_count": len(clause_changes),
        "clause_change_counts": clause_change_counts,
        "clause_alignment": clause_alignment,
        "limitations": [
            "Clause alignment isolates textual deltas but does not determine whether a prior legal position was accepted or rejected.",
            "Low-confidence fuzzy, split, merge, table, exhibit, and formatting-only results require manual confirmation.",
            "Clause identity is strongest for explicit article/section/decimal labels; unnumbered prose uses paragraph fallback records.",
        ],
    }
    if changed_prior_count + changed_current_count > high_volume_threshold or len(clause_changes) > high_volume_threshold:
        extract_contract_text._add_warning(
            result,
            "High-volume clean-version differences detected; batch by clause family or Major Issue List before substantive review.",
        )
    return result


def truncate_result(result: dict, limit: int) -> dict:
    output = dict(result)
    changes = list(result.get("change_blocks", []))
    if limit > 0 and len(changes) > limit:
        output["change_blocks"] = changes[:limit]
        output["truncated"] = True
        output["returned_change_blocks"] = limit
    else:
        output["truncated"] = False
        output["returned_change_blocks"] = len(changes)
    clause_changes = list(result.get("clause_changes", []))
    if limit > 0 and len(clause_changes) > limit:
        output["clause_changes"] = clause_changes[:limit]
        output["clause_changes_truncated"] = True
        output["returned_clause_changes"] = limit
    else:
        output["clause_changes_truncated"] = False
        output["returned_clause_changes"] = len(clause_changes)
    return output


def md_escape(value: object) -> str:
    return str(value or "").replace("|", "/").replace("\n", "<br>")


def block_text(paragraphs: list[dict]) -> str:
    return "<br><br>".join(f"[{paragraph['location']}] {paragraph['text']}" for paragraph in paragraphs) or "-"


def as_markdown(result: dict) -> str:
    if result.get("errors"):
        lines = ["# Clean Version Comparison", "", "## Errors", ""]
        lines.extend(f"- {error}" for error in result["errors"])
        return "\n".join(lines) + "\n"
    lines = [
        "# Clause-Aware Clean Version Comparison",
        "",
        f"- Prior paragraphs: {result['prior_paragraph_count']}",
        f"- Current paragraphs: {result['current_paragraph_count']}",
        f"- Change blocks: {result['change_block_count']}",
        f"- Changed prior/current paragraphs: {result['changed_prior_paragraph_count']}/{result['changed_current_paragraph_count']}",
        f"- Similarity ratio: {result['similarity_ratio']}",
        f"- Prior/current clauses: {result['prior_clause_count']}/{result['current_clause_count']}",
        f"- Clause changes: {result['clause_change_count']}",
        f"- Truncated: {'yes' if result.get('truncated') else 'no'}",
    ]
    for warning in result.get("warnings", []):
        lines.append(f"- Warning: {warning}")
    lines.extend([
        "",
        "| Change | Confidence | Prior clause/location | Current clause/location |",
        "|---|---|---|---|",
    ])
    for change in result.get("clause_changes", []):
        prior = "<br>".join(
            f"{label} [{location}]" for label, location in zip(change["prior_labels"], change["prior_locations"])
        ) or "-"
        current = "<br>".join(
            f"{label} [{location}]" for label, location in zip(change["current_labels"], change["current_locations"])
        ) or "-"
        lines.append(
            f"| {md_escape(change['type'])} | {md_escape(change['confidence'])} | {md_escape(prior)} | {md_escape(current)} |"
        )
    lines.extend(["", "## Paragraph Delta Appendix", "", "| Change | Prior | Current |", "|---|---|---|"])
    for change in result.get("change_blocks", []):
        lines.append(
            f"| {md_escape(change['type'])} | {md_escape(block_text(change['prior']))} | {md_escape(block_text(change['current']))} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prior", type=Path)
    ap.add_argument("current", type=Path)
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--limit", type=int, default=200, help="Maximum change blocks to print; 0 means all.")
    ap.add_argument("--high-volume-threshold", type=int, default=500)
    args = ap.parse_args()

    if args.limit < 0 or args.high_volume_threshold < 0:
        print("--limit and --high-volume-threshold must be zero or greater", file=sys.stderr)
        return 2
    prior = args.prior.expanduser()
    current = args.current.expanduser()
    if not prior.is_file() or not current.is_file():
        print("Both prior and current inputs must be existing files.", file=sys.stderr)
        return 2

    try:
        result = truncate_result(compare_documents(prior, current, args.high_volume_threshold), args.limit)
    except Exception as exc:
        print(f"Unexpected comparison failure: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(as_markdown(result))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
