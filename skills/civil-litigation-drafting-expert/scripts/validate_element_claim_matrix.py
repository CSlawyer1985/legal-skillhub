#!/usr/bin/env python3
"""Validate request-level element pleading matrices."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


EXPECTED = {
    "ELM-001": 5,
    "ELM-002": 8,
    "ELM-003": 8,
    "ELM-004": 5,
    "ELM-005": 3,
    "ELM-006": 4,
    "ELM-007": 10,
    "ELM-008": 7,
    "ELM-009": 7,
    "ELM-010": 3,
    "ELM-011": 3,
}
CLAIM_REQUIRED = {
    "claim_id",
    "request_name",
    "relief_type",
    "branch",
    "elements",
    "fact_questions",
    "evidence_groups",
    "defense_paths",
    "court_review_checks",
    "calculation_rule",
    "conflicts_with",
    "drafting_rule",
    "element_node_id",
    "dispute_type",
    "current_norm",
    "legal_route_ids",
    "source_guide_pages",
    "article_verification_required",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="references/element-pleading-claim-matrix.json")
    parser.add_argument("--element-catalog", default="references/element-pleading-knowledge.json")
    parser.add_argument("--legal-index", default="references/legal-source-index.json")
    args = parser.parse_args()

    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    assert data["skill_version"] == "1.4.0"
    assert data["as_of"] == "2026-07-25"
    assert data["source_book"] == "《民事起诉状、答辩状示范文本及适用指南（图解版）》"
    assert data["source_pdf_sha256"] == "1a9864e9236d322ef7217174a23d38ca225da436a5d110d6d2727736db391580"
    assert "尊重选择" in data["policy"]
    disputes = data["disputes"]
    assert len(disputes) == 11
    counts = Counter(item["element_node_id"] for item in disputes for _ in item["claims"])
    assert counts == Counter(EXPECTED), f"claim counts mismatch: {counts}"

    element_ids = {
        item["node_id"]
        for item in json.loads(Path(args.element_catalog).read_text(encoding="utf-8"))["nodes"]
    }
    legal_ids = {
        item["source_id"]
        for item in json.loads(Path(args.legal_index).read_text(encoding="utf-8"))["sources"]
    }
    assert data["current_norm_source_id"] == "NORM-PLEADING-2025"
    assert data["current_practice_source_id"] == "PRACTICE-PLEADING-CASES-2026-4"
    assert data["current_norm_source_id"] in legal_ids
    assert data["current_practice_source_id"] in legal_ids
    claim_ids: set[str] = set()
    question_ids: set[str] = set()
    evidence_ids: set[str] = set()
    all_claims: list[dict] = []
    for dispute in disputes:
        assert dispute["element_node_id"] in element_ids
        assert dispute["aliases"] and dispute["source_guide_pages"]
        for claim in dispute["claims"]:
            all_claims.append(claim)
            missing = CLAIM_REQUIRED - set(claim)
            assert not missing, f"{claim.get('claim_id')}: missing {sorted(missing)}"
            assert claim["claim_id"] not in claim_ids
            claim_ids.add(claim["claim_id"])
            assert claim["element_node_id"] == dispute["element_node_id"]
            assert claim["dispute_type"] == dispute["dispute_type"]
            assert claim["current_norm"] == "NORM-PLEADING-2025"
            assert "NORM-PLEADING-2024-TRIAL" not in claim["legal_route_ids"]
            assert not set(claim["legal_route_ids"]) - legal_ids
            assert claim["article_verification_required"] is True
            for key in ("elements", "fact_questions", "evidence_groups", "defense_paths"):
                assert len(claim[key]) >= 2, f"{claim['claim_id']}: insufficient {key}"
            assert claim["court_review_checks"], f"{claim['claim_id']}: missing court review checks"
            for question in claim["fact_questions"]:
                assert question["question_id"] not in question_ids
                question_ids.add(question["question_id"])
                assert question["prompt"] and question["blocking"] is True
            for group in claim["evidence_groups"]:
                assert group["evidence_id"] not in evidence_ids
                evidence_ids.add(group["evidence_id"])
                assert group["group"] and group["required_or_explain_absence"] is True
    assert data["claim_count"] == len(all_claims) == 63
    for claim in all_claims:
        assert not set(claim["conflicts_with"]) - claim_ids
    assert len(question_ids) >= 190
    assert len(evidence_ids) >= 150
    print(
        "PASS: 11 disputes; 63 request modules; "
        f"{len(question_ids)} blocking fact questions; "
        f"{len(evidence_ids)} evidence groups; current-law routes resolved"
    )


if __name__ == "__main__":
    main()
