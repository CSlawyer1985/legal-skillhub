#!/usr/bin/env python3
"""Deterministic regression tests for the element pleading runtime."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from element_pleading_tool import audit, load, resolve_dispute


BASE = Path(__file__).resolve().parents[1]
DATA = load(BASE / "references" / "element-pleading-claim-matrix.json")


def complete_case(dispute_query: str, claim_ids: list[str], role: str = "plaintiff") -> dict:
    dispute = resolve_dispute(DATA, dispute_query)
    claim_map = {item["claim_id"]: item for item in dispute["claims"]}
    case = {
        "dispute": dispute["element_node_id"],
        "role": role,
        "selected_claims": claim_ids,
        "answers": {},
        "evidence": {},
        "responses": {},
    }
    for claim_id in claim_ids:
        claim = claim_map[claim_id]
        for question in claim["fact_questions"]:
            case["answers"][question["question_id"]] = "已根据原始材料核实"
        for group in claim["evidence_groups"]:
            case["evidence"][group["evidence_id"]] = ["已核验证据"]
        if role == "defendant":
            case["responses"][claim_id] = {"position": "deny", "reason": "基于已核实事实提出异议"}
    return case


def run(case: dict) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory(prefix="element-pleading-test-") as directory:
        path = Path(directory) / "case.json"
        path.write_text(json.dumps(case, ensure_ascii=False), encoding="utf-8")
        return audit(DATA, path)


def main() -> None:
    assert resolve_dispute(DATA, "银行信用卡")["element_node_id"] == "ELM-006"
    missing = complete_case("民间借贷", ["PL-01"])
    missing["answers"]["PL-01-F01"] = "待核实"
    result, code = run(missing)
    assert code == 2 and result["status"] == "blocked"

    complete = complete_case("民间借贷", ["PL-01"])
    result, code = run(complete)
    assert code == 0 and result["status"] == "structure_ready"

    conflict = complete_case("买卖合同", ["SAL-05A", "SAL-05B"])
    result, code = run(conflict)
    assert code == 2 and any("救济冲突" in item for item in result["blocking"])

    defendant = complete_case("劳动争议", ["LAB-03"], role="defendant")
    defendant["responses"] = {}
    result, code = run(defendant)
    assert code == 2 and any("未作承认" in item for item in result["blocking"])
    print("PASS: alias routing; missing-fact block; complete-case readiness; relief-conflict block; defense-response block")


if __name__ == "__main__":
    main()
