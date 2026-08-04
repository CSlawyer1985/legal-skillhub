#!/usr/bin/env python3
"""Search party filings and the 11-dispute element-pleading layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="document name, procedure keyword, or document ID")
    parser.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parents[1] / "references" / "party-document-catalog.json")
    parser.add_argument("--element-catalog", type=Path, default=Path(__file__).resolve().parents[1] / "references" / "element-pleading-knowledge.json")
    parser.add_argument("--claim-catalog", type=Path, default=Path(__file__).resolve().parents[1] / "references" / "element-pleading-claim-matrix.json")
    parser.add_argument("--full", action="store_true", help="print full matching nodes")
    args = parser.parse_args()
    data = json.loads(args.catalog.read_text())
    q = args.query.casefold()
    matches = []
    for doc in data["documents"]:
        haystack = " ".join([
            doc["document_id"], doc["document_name"], doc["canonical_name"], doc["document_function"],
            *doc["applicable_cases"], *doc["applicable_procedure"],
        ]).casefold()
        if q in haystack:
            matches.append(("party", doc))
    if args.element_catalog.exists():
        element_data = json.loads(args.element_catalog.read_text())
        for node in element_data["nodes"]:
            haystack = " ".join([
                node["node_id"],
                node["dispute_type"],
                node["book_model_name"],
                node["current_model_name"],
                *[item["document_name"] for item in node["document_variants"]],
                *node["claim_elements"],
                *node["fact_questions"],
            ]).casefold()
            if q in haystack:
                matches.append(("element", node))
    if args.claim_catalog.exists():
        claim_data = json.loads(args.claim_catalog.read_text())
        for dispute in claim_data["disputes"]:
            for claim in dispute["claims"]:
                haystack = " ".join([
                    claim["claim_id"],
                    dispute["dispute_type"],
                    *dispute["aliases"],
                    claim["request_name"],
                    *claim["elements"],
                    *claim["defense_paths"],
                ]).casefold()
                if q in haystack:
                    matches.append(("claim", claim))
    priority = {
        "claim": 0,
        "element": 1,
        "party_active": 2,
        "party_superseded": 9,
    }
    matches.sort(
        key=lambda item: priority[
            f"party_{'superseded' if item[1].get('validation_status') == 'superseded' else 'active'}"
            if item[0] == "party"
            else item[0]
        ]
    )
    if args.full:
        print(json.dumps([node for _, node in matches], ensure_ascii=False, indent=2))
    else:
        for kind, node in matches:
            if kind == "party":
                locator = node["source_locator"]
                print(f"{node['document_id']}\t{node['canonical_name']}\t{node['validation_status']}\t下册第{locator['source_file_part']}文件 PDF页{locator['pdf_file_page']}／书页{locator['printed_book_page']}")
            elif kind == "element":
                locator = node["source_locator"]
                print(f"{node['node_id']}\t{node['current_model_name']}起诉／答辩\t{node['validation_status']}\t专项教材指南书页{locator['application_guide_printed_pages']}／PDF页{locator['application_guide_pdf_file_pages']}")
            else:
                print(f"{node['claim_id']}\t{node['dispute_type']}｜{node['request_name']}\trequest_matrix\t{node['source_guide_pages']}")
    if not matches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
