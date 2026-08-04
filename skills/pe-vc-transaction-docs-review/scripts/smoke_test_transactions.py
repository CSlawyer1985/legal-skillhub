#!/usr/bin/env python3
"""Smoke-test extraction and routing against transaction-project folders."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_DISCOVERY_LIMIT = 12


def import_script(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_document_map = import_script("build_document_map")
extract_contract_text = import_script("extract_contract_text")

CORE_TERMS = {
    "redemption": ["回购", "赎回", "redemption", "repurchase"],
    "liquidation_preference": ["清算优先", "优先分配", "liquidation preference"],
    "anti_dilution": ["反稀释", "anti-dilution", "anti dilution"],
    "drag": ["领售", "拖售", "drag-along", "drag along"],
    "rofr": ["优先购买", "right of first refusal", "rofr"],
    "co_sale": ["共同出售", "co-sale", "co sale", "tag-along", "tag along"],
    "preemptive": ["优先认购", "preemptive"],
    "protective": ["保护性条款", "保留事项", "protective provisions", "reserved matters"],
    "board": ["董事", "board", "director"],
    "information": ["信息权", "检查权", "知情权", "information right", "inspection right"],
    "indemnity": ["赔偿", "indemnity", "indemnification"],
    "registered_capital": ["注册资本", "认缴", "实缴", "出资期限", "registered capital"],
    "esop": ["股权激励", "期权池", "持股平台", "esop", "option pool"],
    "investor_transfer": ["投资人转让", "竞争对手", "investor transfer", "competitor"],
    "mfn": ["最优惠", "most favored", "mfn"],
    "founder_restrictions": ["创始股东", "限制性股权", "founder", "restricted shares"],
    "governing_law": ["适用法律", "争议解决", "仲裁", "governing law", "arbitration"],
}


def discover_project_names(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))


def project_label(path: Path, anonymize: bool) -> str:
    if not anonymize:
        return str(path)
    return "project-redacted"


def display_file(path: Path, anonymize: bool) -> str:
    return "redacted" if anonymize else path.name


def pick_representative(docs: list[dict]) -> Path | None:
    priority = [
        "shareholders agreement",
        "investment/subscription agreement",
        "articles/charter",
        "convertible loan / note",
        "side letter / supplemental",
    ]
    for doc_type in priority:
        for document in docs:
            if document["type"] == doc_type:
                return Path(document["path"])
    return Path(docs[0]["path"]) if docs else None


def extract(path: Path, scope: str = "full") -> dict:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return extract_contract_text.extract_docx(path, scope)
    if suffix == ".pdf":
        result = extract_contract_text.extract_pdf(path)
        if scope == "track-changes":
            extract_contract_text._add_warning(
                result,
                "PDF Track Changes cannot be structurally extracted; inspect the redline manually or compare versions.",
            )
        return result
    return extract_contract_text.extract_doc_or_other(path)


def hit_terms(text: str) -> list[str]:
    lowered = text.lower()
    return [group for group, terms in CORE_TERMS.items() if any(term.lower() in lowered for term in terms)]


def project_result(path: Path, anonymize: bool = False) -> dict:
    document_map = build_document_map.build_map([path])
    docs = document_map["documents"]
    representative = pick_representative(docs)
    representative_extraction: dict = {}
    extraction_summary = {
        "files_attempted": 0,
        "text_success": 0,
        "empty_or_failed": 0,
        "methods": {},
        "warnings": [],
        "errors": [],
    }
    aggregate_text: list[str] = []
    track_changes = {
        "docx_files": 0,
        "files_with_revision_markers": 0,
        "changed_files": 0,
        "revision_markers": 0,
        "total_changes": 0,
        "changed_paragraphs": 0,
        "warnings": [],
    }

    for document in docs:
        file_path = Path(document["path"])
        extracted = extract(file_path)
        extraction_summary["files_attempted"] += 1
        paragraphs = extracted.get("paragraphs", [])
        if paragraphs:
            extraction_summary["text_success"] += 1
            aggregate_text.append("\n".join(item["text"] for item in paragraphs))
        else:
            extraction_summary["empty_or_failed"] += 1
        method = extracted.get("method")
        if method:
            extraction_summary["methods"][method] = extraction_summary["methods"].get(method, 0) + 1
        file_name = display_file(file_path, anonymize)
        for warning in extracted.get("warnings", []):
            extraction_summary["warnings"].append(f"{file_name}: {warning}")
        if extracted.get("error"):
            extraction_summary["errors"].append(f"{file_name}: {extracted['error']}")
        if representative and file_path == representative:
            representative_extraction = extracted

        if document["suffix"] == ".docx":
            track_changes["docx_files"] += 1
            tracked = extract(file_path, "track-changes")
            marker_count = int(tracked.get("revision_marker_count") or 0)
            change_count = int(tracked.get("change_count") or 0)
            if marker_count:
                track_changes["files_with_revision_markers"] += 1
                track_changes["revision_markers"] += marker_count
            if change_count:
                track_changes["changed_files"] += 1
                track_changes["total_changes"] += change_count
                track_changes["changed_paragraphs"] += int(tracked.get("changed_paragraph_count") or 0)
            for warning in tracked.get("warnings", []):
                track_changes["warnings"].append(f"{file_name}: {warning}")
            if tracked.get("error"):
                track_changes["warnings"].append(f"{file_name}: {tracked['error']}")

    critical_failures: list[str] = []
    attempted = extraction_summary["files_attempted"]
    if not docs:
        critical_failures.append("no supported transaction documents found")
    elif attempted and extraction_summary["text_success"] == 0:
        critical_failures.append("no document text was extractable; OCR/manual review is required")
    if document_map["input_errors"]:
        critical_failures.extend(document_map["input_errors"])

    if critical_failures:
        readiness = "not review-ready"
    elif extraction_summary["empty_or_failed"]:
        readiness = "partially review-ready"
    else:
        readiness = "review-ready"

    return {
        "project": project_label(path, anonymize),
        "document_count": len(docs),
        "package_type_hint": document_map["package_type_hint"],
        "inferred_structure": document_map["inferred_structure"],
        "structure_assessment": document_map["structure_assessment"],
        "filename_language_hint": document_map["filename_language_hint"],
        "document_types": sorted({document["type"] for document in docs}),
        "missing_common_documents": document_map["missing_common_documents"],
        "representative_file": display_file(representative, anonymize) if representative else None,
        "representative_extraction": {
            "paragraph_count": representative_extraction.get("paragraph_count"),
            "page_count": representative_extraction.get("page_count"),
            "method": representative_extraction.get("method"),
            "error": representative_extraction.get("error"),
            "warnings": representative_extraction.get("warnings", []),
        },
        "extraction_summary": extraction_summary,
        "core_clause_hits": hit_terms("\n".join(aggregate_text)),
        "track_changes": track_changes,
        "review_readiness": readiness,
        "critical_failures": critical_failures,
    }


def summary_for(results: list[dict], require_all_extractable: bool = False) -> dict:
    critical = sum(bool(result["critical_failures"]) for result in results)
    partial = sum(result["extraction_summary"]["empty_or_failed"] > 0 for result in results)
    strict_failures = critical + (partial if require_all_extractable else 0)
    return {
        "project_count": len(results),
        "document_count": sum(result["document_count"] for result in results),
        "review_ready_projects": sum(result["review_readiness"] == "review-ready" for result in results),
        "projects_with_critical_failures": critical,
        "projects_with_partial_extraction": partial,
        "projects_with_track_changes": sum(bool(result["track_changes"]["total_changes"]) for result in results),
        "projects_with_revision_markers": sum(bool(result["track_changes"]["revision_markers"]) for result in results),
        "strict_pass": strict_failures == 0,
    }


def md_escape(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def as_markdown(results: list[dict], require_all_extractable: bool = False) -> str:
    summary = summary_for(results, require_all_extractable)
    ocr_candidates = [
        Path(result["project"]).name
        for result in results
        if "no document text was extractable; OCR/manual review is required" in result["critical_failures"]
    ]
    lines = [
        "# VC/PE Skill Smoke Test Report",
        "",
        f"- Strict result: {'PASS' if summary['strict_pass'] else 'FAIL'}",
        f"- Projects tested: {summary['project_count']}",
        f"- Documents scanned: {summary['document_count']}",
        f"- Review-ready projects: {summary['review_ready_projects']}/{summary['project_count']}",
        f"- Projects with critical failures: {summary['projects_with_critical_failures']}",
        f"- Projects with structural Track Changes detected: {summary['projects_with_track_changes']}/{summary['project_count']}",
        f"- OCR/manual-review candidates: {', '.join(ocr_candidates) if ocr_candidates else '-'}",
        "",
        "| # | Project | Docs | Readiness | Structure | Missing core docs | Extraction | Track Changes | Core clause hits |",
        "|---:|---|---:|---|---|---|---|---|---|",
    ]
    for index, result in enumerate(results, start=1):
        name = Path(result["project"]).name
        missing = ", ".join(result["missing_common_documents"]) or "-"
        extraction = result["extraction_summary"]
        methods = ",".join(f"{key}:{value}" for key, value in sorted(extraction["methods"].items())) or "-"
        extraction_text = (
            f"{extraction['text_success']}/{extraction['files_attempted']} text ok; "
            f"empty/failed {extraction['empty_or_failed']}; {methods}"
        )
        if extraction["warnings"] or extraction["errors"]:
            extraction_text += f"; warnings/errors {len(extraction['warnings']) + len(extraction['errors'])}"
        tracked = result["track_changes"]
        tracked_text = (
            f"{tracked['changed_files']}/{tracked['docx_files']} files, {tracked['revision_markers']} markers, "
            f"{tracked['total_changes']} text changes, {tracked['changed_paragraphs']} changed paragraphs"
        )
        if tracked["warnings"]:
            tracked_text += f"; warnings {len(tracked['warnings'])}"
        hits = ", ".join(result["core_clause_hits"]) or "-"
        lines.append(
            f"| {index} | {md_escape(name)} | {result['document_count']} | {md_escape(result['review_readiness'])} "
            f"| {md_escape(result['inferred_structure'])} | {md_escape(missing)} | {md_escape(extraction_text)} "
            f"| {md_escape(tracked_text)} | {md_escape(hits)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--project", action="append", help="Relative project folder. May be repeated.")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--strict", action="store_true", help="Return non-zero when a project has a critical failure.")
    ap.add_argument("--require-all-extractable", action="store_true", help="With --strict, fail when any file needs OCR/manual review.")
    ap.add_argument(
        "--anonymize",
        action="store_true",
        help="Replace project labels with per-run sequence IDs and redact filenames in the report.",
    )
    args = ap.parse_args()

    if args.limit < 0:
        print("--limit must be zero or greater", file=sys.stderr)
        return 2
    root = args.root.expanduser()
    if not root.is_dir():
        print(f"Root folder not found: {root}", file=sys.stderr)
        return 2
    names = args.project or discover_project_names(root)
    if args.limit:
        names = names[: args.limit]
    elif not args.project:
        names = names[:DEFAULT_DISCOVERY_LIMIT]
    if not names:
        print("No project folders found.", file=sys.stderr)
        return 2

    projects = [root / name for name in names]
    missing = [project for project in projects if not project.is_dir()]
    if missing:
        print("Missing project folder(s):", file=sys.stderr)
        for project in missing:
            print(f"- {project}", file=sys.stderr)
        return 2

    results = []
    for index, project in enumerate(projects, start=1):
        result = project_result(project, anonymize=args.anonymize)
        if args.anonymize:
            result["project"] = f"project-{index:03d}"
        results.append(result)
    summary = summary_for(results, args.require_all_extractable)
    if args.format == "md":
        print(as_markdown(results, args.require_all_extractable))
    else:
        print(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2))
    if args.strict and not summary["strict_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
