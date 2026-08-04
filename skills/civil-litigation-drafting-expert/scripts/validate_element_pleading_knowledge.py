#!/usr/bin/env python3
"""Validate the element-based pleading knowledge base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "node_id",
    "version",
    "validation_status",
    "dispute_type",
    "book_model_name",
    "current_model_name",
    "source_locator",
    "book_model_status",
    "current_norm",
    "claim_matrix_ref",
    "change_record",
    "document_variants",
    "legal_basis",
    "burden_of_proof",
    "claim_elements",
    "fact_questions",
    "evidence_requirements",
    "court_review_focus",
    "calculation_rules",
    "logic_structure",
    "standard_format_rule",
    "ai_generation_flow",
    "automatic_checks",
    "common_omissions",
    "common_errors",
    "lawyer_writing_tips",
    "ai_generation_rules",
    "risk_analysis",
    "excellent_example_rule",
    "catalog_links",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="references/element-pleading-knowledge.json")
    parser.add_argument("--legal-index", default="references/legal-source-index.json")
    args = parser.parse_args()
    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    assert len(nodes) == 11, f"expected 11 nodes, got {len(nodes)}"
    assert "自愿选择" in data["policy"] and "强制" in data["policy"]
    ids: set[str] = set()
    links: list[str] = []
    for node in nodes:
        missing = REQUIRED - set(node)
        assert not missing, f"{node.get('node_id')}: missing {sorted(missing)}"
        assert node["node_id"] not in ids, f"duplicate {node['node_id']}"
        ids.add(node["node_id"])
        assert node["book_model_status"] == "superseded_methodology_retained"
        assert node["current_norm"] == "NORM-PLEADING-2025"
        assert node["claim_matrix_ref"] == "references/element-pleading-claim-matrix.json"
        assert node["validation_status"] == "verified_current_structure"
        assert len(node["document_variants"]) == 2
        assert {x["role"] for x in node["document_variants"]} == {"plaintiff", "defendant"}
        for key in REQUIRED - {"guiding_case_rule"}:
            assert node[key] not in (None, "", [], {}), f"{node['node_id']}: empty {key}"
        links.extend(node["catalog_links"])
    assert len(links) == 44 and len(set(links)) == 44
    assert set(links) == {f"APPX-{i:03d}" for i in range(1, 45)}
    credit = next(node for node in nodes if node["node_id"] == "ELM-006")
    assert credit["book_model_name"] == "银行信用卡纠纷"
    assert credit["current_model_name"] == "信用卡纠纷"
    legal_ids = {
        item["source_id"]
        for item in json.loads(Path(args.legal_index).read_text(encoding="utf-8"))["sources"]
    }
    referenced = {source_id for node in nodes for source_id in node["legal_basis"]}
    assert not referenced - legal_ids, f"missing legal source IDs: {sorted(referenced - legal_ids)}"
    print("PASS: 11 element-pleading nodes; 22 variants; 44 historical links; legal references resolved; current-policy guard active")


if __name__ == "__main__":
    main()
