#!/usr/bin/env python3
"""Validate the Gaotao litigation-visualization extension contract."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_litigation_visualization_handoff.py"
EXAMPLE_PATH = ROOT / "templates" / "litigation-visualization-handoff-v1.hold-example.json"
SCHEMA_PATH = ROOT / "templates" / "litigation-visualization-handoff-v1.schema.json"
ANCHOR_CONTRACT_PATH = ROOT / "templates" / "L2-05-ANCHOR-CONTRACT-v1.json"
ANCHOR_MAP_PATH = ROOT / "templates" / "L2-05-anchor-map.hold-example.json"
DRIFT_CASES_PATH = ROOT / "tests" / "fixtures" / "validator-drift-cases.json"
DOWNSTREAM_HOLD_PATH = ROOT / "tests" / "fixtures" / "projected-downstream-hold-spec.json"

EXPECTED_ANCHORS = [
    "parties_roles",
    "contract_chain",
    "performance_delivery_acceptance",
    "payment_balance",
    "notices_objections_termination_limitation",
    "claim_element_fact_evidence_matrix",
    "evidence_index",
    "litigation_stage_plan",
    "risk_hold_register",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("gaotao_handoff_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load handoff validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def set_path(document: Any, dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    cursor = document
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    final = parts[-1]
    if isinstance(cursor, list):
        cursor[int(final)] = value
    else:
        cursor[final] = value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    validator = load_validator()
    example = load_json(EXAMPLE_PATH)
    schema = load_json(SCHEMA_PATH)
    anchor_contract = load_json(ANCHOR_CONTRACT_PATH)
    anchor_map = load_json(ANCHOR_MAP_PATH)
    downstream_hold = load_json(DOWNSTREAM_HOLD_PATH)

    require(
        schema["properties"]["route"]["properties"]["output_profile"]["const"]
        == "professional_service.litigation_visualization",
        "output profile drifted",
    )
    require(example["route"]["trigger"] == "on_request", "trigger must default to on_request")
    require(example["route"]["capability_status"] == "hold", "capability must default to hold")
    require(example["write_back_allowed"] is False, "write-back must remain disabled")
    require(example["gates"]["render_allowed"] is False, "HOLD example must not render")
    require(downstream_hold["workflow_status"] == "hold", "downstream fixture must remain HOLD")

    contract_anchors = [item["anchor_id"] for item in anchor_contract["stable_anchors"]]
    map_anchors = [item["anchor_id"] for item in anchor_map["anchors"]]
    require(contract_anchors == EXPECTED_ANCHORS, "anchor contract must contain the exact nine anchors")
    require(map_anchors == EXPECTED_ANCHORS, "anchor map must contain the exact nine anchors")
    require(
        all(item["status"] == "empty_hold" for item in anchor_map["anchors"]),
        "synthetic anchor map must fail closed",
    )

    plan = example["upstream"]["litigation_plan"]
    require(
        plan["anchor_contract_sha256"] == sha256(ANCHOR_CONTRACT_PATH),
        "anchor contract hash binding failed",
    )
    require(plan["anchor_map_sha256"] == sha256(ANCHOR_MAP_PATH), "anchor map hash binding failed")

    baseline_errors = validator.validate_data(example)
    require(not baseline_errors, "baseline handoff invalid: " + "; ".join(baseline_errors))
    print("PASS baseline-hold-example")
    print("PASS nine-anchor-inheritance")
    print("PASS nested-output-profile-and-no-write-back")

    cases = load_json(DRIFT_CASES_PATH)
    for case in cases:
        mutated = copy.deepcopy(example)
        for dotted_path, value in case["mutations"].items():
            set_path(mutated, dotted_path, value)
        errors = validator.validate_data(mutated)
        expected = case["expected_error_code"] + ":"
        require(
            any(error.startswith(expected) for error in errors),
            f"{case['id']} did not produce {case['expected_error_code']}",
        )
        print(f"PASS {case['id']}")

    print(f"PASS validator-drift {len(cases)}/{len(cases)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL {exc}")
        raise SystemExit(1)
