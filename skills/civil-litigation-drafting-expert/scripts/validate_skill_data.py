#!/usr/bin/env python3
"""Validate the party-filing snapshot or cumulative Parts 2-4 catalog."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


REQUIRED = {
    "document_id", "document_name", "canonical_name", "document_role",
    "document_function", "applicable_cases", "applicable_procedure",
    "start_conditions", "applicant_or_maker", "counterparty_or_recipient",
    "competent_court", "book_original_basis", "current_legal_basis",
    "legal_update_note", "judicial_interpretations", "case_authorities",
    "court_focus", "submission_or_making_time", "burden_of_proof",
    "evidence_requirements", "risk_analysis", "logical_structure",
    "smart_template_fields", "court_review_logic", "lawyer_writing_tips",
    "ai_generation_flow", "automatic_validation_rules", "common_errors",
    "excellent_example_policy", "source_locator", "validation_status",
    "version", "effective_from", "supersedes",
}
SNAPSHOT_IDS = {"PARTY-L2-JUR-001", "PARTY-L2-JUR-002", "PARTY-L2-REC-001"}
SNAPSHOT_CHAPTERS = {"管辖": 2, "回避": 1}
CUMULATIVE_88_CHAPTERS = {
    "管辖": 2, "回避": 2, "诉讼参加人": 6, "证据": 9,
    "期间、送达": 1, "调解": 1, "保全和先予执行": 9,
    "对妨害民事诉讼的强制措施": 2, "诉讼费用": 1,
    "第一审普通程序": 17, "简易程序": 1,
    "简易程序中的小额诉讼": 1, "公益诉讼": 4,
    "第三人撤销之诉": 1, "执行异议之诉": 2,
    "第二审程序": 1, "非讼程序": 28,
}
CUMULATIVE_149_CHAPTERS = {
    **CUMULATIVE_88_CHAPTERS,
    "审判监督程序": 1,
    "督促程序": 4,
    "公示催告程序": 3,
    "执行程序": 8,
    "涉外民事诉讼程序的特别规定": 1,
    "附录：部分案件民事起诉状、答辩状示范文本（试行）": 44,
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_skill_data.py <party-catalog.json>")
    data = json.loads(Path(sys.argv[1]).read_text())
    documents = data.get("documents")
    if not isinstance(documents, list):
        fail("documents must be a list")
    if data.get("document_count") != len(documents):
        fail("document_count does not match documents length")
    if len(documents) not in {3, 88, 149}:
        fail(f"expected 3 snapshot, 88 intermediate, or 149 complete nodes, got {len(documents)}")
    ids = [doc.get("document_id") for doc in documents]
    if len(ids) != len(set(ids)):
        fail("duplicate document_id")
    if len(documents) == 3 and set(ids) != SNAPSHOT_IDS:
        fail(f"snapshot IDs mismatch: {ids}")
    expected_chapters = (
        SNAPSHOT_CHAPTERS if len(documents) == 3
        else CUMULATIVE_88_CHAPTERS if len(documents) == 88
        else CUMULATIVE_149_CHAPTERS
    )
    chapters = Counter(doc["source_locator"].get("chapter") for doc in documents)
    if dict(chapters) != expected_chapters:
        fail(f"chapter counts mismatch: {dict(chapters)}")
    for doc in documents:
        missing = REQUIRED - set(doc)
        if missing:
            fail(f"{doc.get('document_id')} missing fields: {sorted(missing)}")
        if doc["document_role"] != "party_filing":
            fail(f"{doc['document_id']} is not a party filing")
        if doc["validation_status"] not in {"ocr_lead", "book_verified", "verified_current", "superseded", "needs_review"}:
            fail(f"{doc['document_id']} has invalid validation_status")
        locator = doc["source_locator"]
        part = locator.get("source_file_part")
        page = locator.get("pdf_file_page", 0)
        if part == 2 and page < 196:
            fail(f"{doc['document_id']} improperly imports excluded court-document pages")
        if part == 3 and not 1 <= page <= 203:
            fail(f"{doc['document_id']} has invalid Part 3 page")
        if part == 4 and not 1 <= page <= 204:
            fail(f"{doc['document_id']} has invalid Part 4 page")
        if part not in {2, 3, 4}:
            fail(f"{doc['document_id']} has unexpected source part {part}")
        for key in REQUIRED - {"effective_from", "supersedes"}:
            if doc[key] in (None, "", []):
                fail(f"{doc['document_id']} has empty required value: {key}")
    if len(documents) == 88:
        if set(doc["source_locator"]["source_file_part"] for doc in documents) != {2, 3}:
            fail("cumulative catalog must contain source parts 2 and 3")
        if "审判监督程序" in chapters:
            fail("Chapter 18 title page must not create a document node")
        arbitration = next(doc for doc in documents if doc["document_id"] == "PARTY-L3-NSP-021")
        if not any("2025年修订" in basis for basis in arbitration["current_legal_basis"]):
            fail("arbitration node must use the 2025 revised Arbitration Law")
    if len(documents) == 149:
        if set(doc["source_locator"]["source_file_part"] for doc in documents) != {2, 3, 4}:
            fail("complete catalog must contain source parts 2, 3 and 4")
        appendix = [doc for doc in documents if doc["document_id"].startswith("PARTY-L4-APPX-")]
        if len(appendix) != 44 or any(doc["validation_status"] != "superseded" for doc in appendix):
            fail("all 44 appendix nodes must be retained and marked superseded")
        if any("法〔2025〕82号" not in " ".join(doc["current_legal_basis"]) for doc in appendix):
            fail("every superseded appendix node must route to 法〔2025〕82号")
        active_part4 = [doc for doc in documents if doc["document_id"].startswith("PARTY-L4-") and not doc["document_id"].startswith("PARTY-L4-APPX-")]
        if len(active_part4) != 17 or any(doc["validation_status"] != "book_verified" for doc in active_part4):
            fail("Part 4 must contain 17 book-verified active chapter nodes")
        if data.get("active_document_count") != 105 or data.get("historical_superseded_count") != 44:
            fail("complete catalog active/historical counts mismatch")
    print(f"PASS: {len(documents)} party filings; chapters {dict(chapters)}; court-document pages excluded")


if __name__ == "__main__":
    main()
