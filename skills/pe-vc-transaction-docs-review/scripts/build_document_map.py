#!/usr/bin/env python3
"""Build an evidence-bearing map of a VC/PE transaction document package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SUPPORTED_SUFFIXES = {".docx", ".doc", ".pdf", ".rtf", ".txt", ".md"}
IGNORED_PREFIXES = ("~$", "._")

# Higher weights represent more specific filename evidence. The highest-scoring
# document family wins, so an investment supplemental agreement remains an
# investment agreement instead of being swallowed by generic "supplemental".
DOC_TYPE_RULES: list[tuple[str, list[tuple[str, int, bool]]]] = [
    ("management rights", [("management rights", 120, False), ("管理权利", 120, False), ("管理权", 90, False)]),
    ("term sheet", [("term sheet", 120, False), ("条款清单", 120, False), ("投资条款", 80, False), ("ts", 50, True)]),
    ("shareholders agreement", [
        ("shareholders agreement", 120, False), ("shareholder agreement", 120, False),
        ("股东协议", 120, False), ("合资经营合同", 120, False), ("joint venture", 100, False), ("sha", 80, True),
    ]),
    ("articles/charter", [
        ("memorandum and articles", 140, False), ("articles of association", 130, False),
        ("公司章程", 130, False), ("章程", 110, False), ("memorandum", 100, False),
        ("articles", 90, False), ("m&aa", 90, True), ("maa", 80, True), ("m&a", 70, True), ("ma", 45, True),
    ]),
    ("convertible loan / note", [
        ("convertible loan", 130, False), ("convertible note", 130, False),
        ("可转债协议", 130, False), ("可转债", 110, False), ("借款协议", 90, False),
    ]),
    ("investment/subscription agreement", [
        ("投资补充协议", 150, False), ("增资协议补充协议", 150, False),
        ("share subscription agreement", 140, False), ("share purchase agreement", 140, False),
        ("股份认购协议", 140, False), ("增资及转股", 135, False), ("增资协议", 130, False),
        ("投资协议", 130, False), ("股权转让协议", 125, False), ("转股协议", 110, False),
        ("认购协议", 120, False), ("subscription agreement", 120, False),
        ("share subscription", 115, False), ("share purchase", 115, False),
        ("ssa", 80, True), ("spa", 80, True),
    ]),
    ("disclosure", [("disclosure schedule", 130, False), ("disclosure letter", 130, False), ("披露函", 130, False), ("披露", 90, False)]),
    ("esop / incentive", [("esop", 120, True), ("option plan", 120, False), ("股权激励", 120, False), ("期权计划", 120, False), ("期权", 70, False)]),
    ("vie / control", [
        ("exclusive business cooperation", 130, False), ("equity pledge", 120, False),
        ("power of attorney", 110, False), ("控制协议", 130, False), ("独家业务合作", 130, False),
        ("股权质押", 110, False), ("授权委托", 100, False), ("vie", 100, True),
    ]),
    ("board/shareholder approval", [
        ("board resolution", 120, False), ("shareholder resolution", 120, False),
        ("written consent", 100, False), ("董事会决议", 120, False), ("股东会决议", 120, False),
        ("resolution", 70, False), ("minutes", 60, False), ("决议", 70, False),
    ]),
    ("closing deliverable", [
        ("closing certificate", 120, False), ("closing deliverable", 120, False),
        ("交割证明", 120, False), ("交割文件", 110, False), ("交割", 70, False), ("certificate", 55, False),
    ]),
    ("indemnity / restriction", [
        ("indemnification agreement", 120, False), ("restriction agreement", 120, False),
        ("赔偿协议", 110, False), ("限制协议", 100, False), ("indemnification", 80, False),
    ]),
    ("side letter / supplemental", [
        ("side letter", 130, False), ("补充协议", 45, False), ("supplemental", 45, False),
        ("amendment", 40, False), ("修订协议", 45, False),
    ]),
]

RMB_TERMS = [
    ("有限公司", 5), ("增资", 5), ("合资经营", 5), ("人民币", 5), ("股东协议", 3),
    ("投资协议", 3), ("公司章程", 3), ("股权转让", 3), ("中外合资", 4),
]
OFFSHORE_TERMS = [
    ("cayman", 6), ("开曼", 6), ("bvi", 5), ("wfoe", 5), ("美元", 4),
    ("preferred shares", 4), ("preference shares", 4), ("memorandum", 3),
    ("subscription agreement", 3), ("articles", 2), ("shareholders agreement", 2),
    ("sha", 1), ("spa", 1), ("ssa", 1), ("series", 1),
]
VIE_TERMS = [
    ("vie", 7), ("wfoe", 7), ("控制协议", 6), ("独家业务合作", 6),
    ("exclusive business cooperation", 6), ("股权质押", 4), ("授权委托", 3),
]


def _token_match(name: str, token: str) -> bool:
    return bool(re.search(rf"(^|[^a-z0-9]){re.escape(token.lower())}([^a-z0-9]|$)", name))


def classify_with_evidence(path: Path) -> dict[str, object]:
    name = path.name.lower()
    scored: list[tuple[int, int, str, list[str]]] = []
    for priority, (doc_type, rules) in enumerate(DOC_TYPE_RULES):
        score = 0
        evidence: list[str] = []
        for term, weight, token_only in rules:
            matched = _token_match(name, term) if token_only else term.lower() in name
            if matched:
                score += weight
                evidence.append(term)
        if score:
            scored.append((score, -priority, doc_type, evidence))
    if not scored:
        return {"type": "other", "score": 0, "evidence": []}
    score, _, doc_type, evidence = max(scored)
    return {"type": doc_type, "score": score, "evidence": evidence}


def classify(path: Path) -> str:
    return str(classify_with_evidence(path)["type"])


def _score_terms(blob: str, terms: list[tuple[str, int]], *, token_terms: set[str] | None = None) -> tuple[int, list[str]]:
    score = 0
    evidence: list[str] = []
    token_terms = token_terms or set()
    for term, weight in terms:
        matched = _token_match(blob, term) if term in token_terms else term in blob
        if matched:
            score += weight
            evidence.append(term)
    return score, evidence


def structure_assessment(paths: list[Path]) -> dict[str, object]:
    blob = " ".join(path.name.lower() for path in paths)
    token_terms = {"vie", "wfoe", "bvi", "sha", "spa", "ssa"}
    rmb_score, rmb_evidence = _score_terms(blob, RMB_TERMS)
    offshore_score, offshore_evidence = _score_terms(blob, OFFSHORE_TERMS, token_terms=token_terms)
    vie_score, vie_evidence = _score_terms(blob, VIE_TERMS, token_terms={"vie", "wfoe"})

    if vie_score >= 6:
        label = "offshore USD - VIE likely"
        confidence = "high" if vie_score >= 10 else "medium"
    elif rmb_score >= offshore_score + 2:
        label = "RMB onshore likely"
        confidence = "high" if rmb_score >= 8 and rmb_score - offshore_score >= 4 else "medium"
    elif offshore_score >= rmb_score + 2:
        label = "offshore USD - direct/VIE to confirm"
        confidence = "high" if offshore_score >= 8 and offshore_score - rmb_score >= 4 else "medium"
    elif rmb_score or offshore_score:
        label = "ambiguous - confirm from operative documents"
        confidence = "low"
    else:
        label = "unknown"
        confidence = "low"

    return {
        "label": label,
        "confidence": confidence,
        "filename_only": True,
        "scores": {"rmb_onshore": rmb_score, "offshore": offshore_score, "vie": vie_score},
        "evidence": {"rmb_onshore": rmb_evidence, "offshore": offshore_evidence, "vie": vie_evidence},
    }


def infer_structure(paths: list[Path]) -> str:
    return str(structure_assessment(paths)["label"])


def language_hint(paths: list[Path]) -> dict[str, object]:
    names = " ".join(path.stem for path in paths)
    cjk_count = len(re.findall(r"[\u3400-\u9fff]", names))
    latin_count = len(re.findall(r"[A-Za-z]", names))
    if not cjk_count and not latin_count:
        label = "unknown"
        confidence = "low"
    elif cjk_count and latin_count and min(cjk_count, latin_count) >= 6:
        label = "mixed"
        confidence = "low"
    elif cjk_count:
        label = "zh"
        confidence = "medium" if cjk_count >= 6 else "low"
    else:
        label = "en"
        confidence = "medium" if latin_count >= 10 else "low"
    return {
        "label": label,
        "confidence": confidence,
        "filename_only": True,
        "counts": {"cjk": cjk_count, "latin": latin_count},
    }


def version_signals(path: Path) -> list[str]:
    name = path.name.lower()
    signals: list[str] = []
    groups = {
        "redline_or_comparison": ["redline", "markup", "track changes", "对比", "比较版", "修订", "修改版"],
        "clean": ["clean", "干净版", "清洁版"],
        "signed_or_executed": ["executed", "signed", "签署版", "签署稿", "盖章版"],
        "final": ["final", "定稿", "最终版"],
        "draft": ["draft", "草稿", "送审稿", "讨论稿"],
    }
    for label, terms in groups.items():
        if any(term in name for term in terms):
            signals.append(label)
    if re.search(r"(?:^|[^a-z0-9])v\d+(?:[^a-z0-9]|$)", name):
        signals.append("numbered_version")
    if re.search(r"第[一二三四五六七八九十\d]+稿", name):
        signals.append("numbered_draft_round")
    if re.search(r"(?:20\d{2})[-_.]?(?:0?[1-9]|1[0-2])[-_.]?(?:0?[1-9]|[12]\d|3[01])", name):
        signals.append("date_in_filename")
    return signals


def collect_with_diagnostics(inputs: list[Path]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    seen: set[Path] = set()
    for raw_item in inputs:
        item = raw_item.expanduser()
        if not item.exists():
            errors.append(f"input not found: {item}")
            continue
        candidates = item.rglob("*") if item.is_dir() else [item]
        for candidate in candidates:
            if not candidate.is_file() or candidate.name.startswith(IGNORED_PREFIXES):
                continue
            if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
                if not item.is_dir():
                    errors.append(f"unsupported file type: {candidate}")
                continue
            identity = candidate.resolve()
            if identity not in seen:
                seen.add(identity)
                files.append(candidate)
    return sorted(files, key=lambda path: str(path).lower()), errors


def collect(inputs: list[Path]) -> list[Path]:
    return collect_with_diagnostics(inputs)[0]


def package_type_hint(types: set[str]) -> str:
    core = {"investment/subscription agreement", "shareholders agreement", "articles/charter"}
    if types & core:
        return "transaction-document package"
    if "term sheet" in types:
        return "term-sheet-only or early package"
    if "convertible loan / note" in types:
        return "convertible financing package"
    return "unknown"


def build_map(inputs: list[Path]) -> dict[str, object]:
    files, input_errors = collect_with_diagnostics(inputs)
    documents = []
    for path in files:
        classification = classify_with_evidence(path)
        documents.append({
            "path": str(path),
            "name": path.name,
            "type": classification["type"],
            "classification_score": classification["score"],
            "classification_evidence": classification["evidence"],
            "suffix": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "version_signals": version_signals(path),
        })
    types = {str(document["type"]) for document in documents}
    expected = ["investment/subscription agreement", "shareholders agreement", "articles/charter"]
    missing = [doc_type for doc_type in expected if doc_type not in types]
    structure = structure_assessment(files)
    return {
        "document_count": len(documents),
        "package_type_hint": package_type_hint(types),
        "inferred_structure": structure["label"],
        "structure_assessment": structure,
        "filename_language_hint": language_hint(files),
        "documents": documents,
        "missing_common_documents": missing,
        "input_errors": input_errors,
        "limitations": [
            "Document type, structure, language, and version signals are filename-based intake hints only.",
            "Confirm structure, governing law, language, and document version from operative text before substantive review.",
        ],
    }


def md_escape(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--format", choices=["json", "md"], default="json")
    args = ap.parse_args()

    result = build_map(args.inputs)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        assessment = result["structure_assessment"]
        language = result["filename_language_hint"]
        print("# Document Map")
        print(f"\n- Package hint: {result['package_type_hint']}")
        print(f"- Structure hint: {assessment['label']} ({assessment['confidence']} confidence; filename only)")
        print(f"- Language hint: {language['label']} ({language['confidence']} confidence; filename only)")
        print(f"- Document count: {result['document_count']}")
        if result["missing_common_documents"]:
            print(f"- Potentially missing common documents: {', '.join(result['missing_common_documents'])}")
        if result["input_errors"]:
            print(f"- Input errors: {'; '.join(result['input_errors'])}")
        print("\n| Type | Version signals | File | Classification evidence |")
        print("|---|---|---|---|")
        for document in result["documents"]:
            print(
                f"| {md_escape(document['type'])} | {md_escape(', '.join(document['version_signals']) or '-')} "
                f"| {md_escape(document['path'])} | {md_escape(', '.join(document['classification_evidence']) or '-')} |"
            )
    return 0 if result["document_count"] and not result["input_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
