#!/usr/bin/env python3
"""Regression tests for the lawyer distillation candidate package."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_package.py"
SPEC = importlib.util.spec_from_file_location("validate_package", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def load_json(relative: str) -> dict:
    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class PackageTests(unittest.TestCase):
    def test_static_validator(self) -> None:
        self.assertEqual([], VALIDATOR.validate_package(ROOT))

    def test_manifest_keeps_release_closed(self) -> None:
        manifest = load_json("manifest.json")
        self.assertEqual("candidate-local-only", manifest["status"])
        self.assertEqual(0, manifest["privacy"]["case_payload_files"])
        self.assertFalse(manifest["privacy"]["answer_key_included"])
        self.assertFalse(manifest["publication"]["formal_skill_install_authorized"])
        self.assertFalse(manifest["publication"]["external_publish_authorized"])

    def test_three_zones_are_explicit_and_distinct(self) -> None:
        manifest = load_json("manifest.json")
        self.assertEqual(
            ["private-evidence", "verified-knowledge", "public-projection"],
            manifest["privacy"]["architecture"],
        )
        plan = load_json("templates/distillation-plan.example.json")
        self.assertEqual(4, len(set(plan["zones"].values())))

    def test_atomic_schema_has_legal_and_public_gates(self) -> None:
        schema = load_json("templates/atomic-knowledge-record.schema.json")
        required = set(schema["required"])
        for field in (
            "source_locator",
            "source_hash",
            "legal_authority",
            "privacy_class",
            "rights_status",
            "failure_modes",
            "public_projection",
        ):
            self.assertIn(field, required)
        self.assertTrue(schema["allOf"])

    def test_atomic_example_has_every_required_field(self) -> None:
        schema = load_json("templates/atomic-knowledge-record.schema.json")
        example = load_json("templates/atomic-knowledge-record.example.json")
        self.assertEqual(set(), set(schema["required"]) - set(example))
        self.assertFalse(example["public_projection"]["allowed"])
        self.assertNotEqual("public", example["privacy_class"])

    def test_prompt_coverage(self) -> None:
        cases = load_json("templates/test-prompts.json")["cases"]
        counts = {
            kind: sum(case["type"] == kind for case in cases)
            for kind in ("should_trigger", "should_not_trigger", "edge_case")
        }
        self.assertGreaterEqual(counts["should_trigger"], 3)
        self.assertGreaterEqual(counts["should_not_trigger"], 3)
        self.assertGreaterEqual(counts["edge_case"], 2)

    def test_prompt_suite_has_legal_safety_baits(self) -> None:
        text = json.dumps(load_json("templates/test-prompts.json"), ensure_ascii=False)
        for marker in (
            "HOLD-PRIVACY",
            "HOLD-LEGAL",
            "HOLD-ANSWER-KEY",
            "HOLD-GEO-FIDELITY",
            "HOLD-BASELINE-INHERITANCE",
            "HOLD-OUTPUT-CONTRACT",
            "HOLD-COURT-TEXT",
            "HOLD-RENDER",
            "HOLD-E2E",
        ):
            self.assertIn(marker, text)

    def test_georank_operations_do_not_trigger(self) -> None:
        cases = load_json("templates/test-prompts.json")["cases"]
        api_case = next(case for case in cases if case["id"] == "no-trigger-georank-api-01")
        self.assertEqual("should_not_trigger", api_case["type"])
        self.assertIn("不操作平台 API", api_case["expected_behavior"])

    def test_geo_measurement_avoids_single_score(self) -> None:
        geo = load_json("templates/geo-query-set.example.json")
        measurement = geo["measurement"]
        self.assertFalse(measurement["ranking_guarantee"])
        self.assertEqual({"control", "treatment"}, set(measurement["branches"]))
        self.assertIn("citation_selection", measurement["metrics"])
        self.assertIn("citation_absorption", measurement["metrics"])
        self.assertIn("citation_fidelity", measurement["metrics"])

    def test_sublation_matrix_uses_all_decisions(self) -> None:
        matrix = (ROOT / "templates/Sublation比较矩阵.md").read_text(encoding="utf-8")
        for donor in ("原创基底", "仓颉", "GEORank"):
            self.assertIn(donor, matrix)
        for decision in ("保留", "强化", "替换", "组合", "舍弃"):
            self.assertIn(f"| {decision} |", matrix)

    def test_package_contains_no_symlinks(self) -> None:
        symlinks = [path.relative_to(ROOT) for path in ROOT.rglob("*") if path.is_symlink()]
        self.assertEqual([], symlinks)

    def test_checksum_manifest_is_complete(self) -> None:
        errors: list[str] = []
        VALIDATOR.check_checksums(ROOT, errors)
        self.assertEqual([], errors)

    def test_validation_report_preserves_independent_review_boundary(self) -> None:
        report = load_json("VALIDATION-REPORT.json")
        self.assertEqual("PASS", report["static_validator"]["status"])
        self.assertEqual("pending-independent-review", report["privacy_review"])
        self.assertEqual("pending-independent-review", report["legal_review"])
        self.assertFalse(report["human_final_acceptance"])

    def test_manifest_separates_deployment_observation_from_authorization(self) -> None:
        manifest = load_json("manifest.json")
        deployment = manifest["deployment_observation"]
        self.assertTrue(deployment["physical_install_observed"])
        self.assertEqual("1.0.0-rc.1", deployment["observed_installed_version"])
        self.assertEqual("missing", deployment["install_authorization_receipt"])
        self.assertFalse(deployment["candidate_version_installed"])
        self.assertFalse(deployment["production_promotion_authorized"])

    def test_manifest_has_new_holds(self) -> None:
        holds = set(load_json("manifest.json")["required_holds"])
        for hold in (
            "HOLD-BASELINE-INHERITANCE",
            "HOLD-OUTPUT-CONTRACT",
            "HOLD-COURT-TEXT",
            "HOLD-RENDER",
            "HOLD-E2E",
        ):
            self.assertIn(hold, holds)

    def test_domain_baseline_inventory_exactly_matches_decisions(self) -> None:
        payload = load_json("templates/domain-baseline-inheritance.example.json")
        required = {
            (donor["donor_id"], gate_id)
            for donor in payload["donor_inventories"]
            for gate_id in donor["required_gate_ids"]
        }
        decisions = [
            (decision["donor_id"], decision["gate_id"])
            for decision in payload["decisions"]
        ]
        self.assertEqual(required, set(decisions))
        self.assertEqual(len(decisions), len(set(decisions)))
        self.assertEqual([], payload["coverage"]["missing_gate_ids"])
        self.assertEqual([], payload["coverage"]["duplicate_gate_ids"])

    def test_output_contracts_are_closed_and_read_only(self) -> None:
        contracts = load_json("templates/output-contract.example.json")["contracts"]
        self.assertEqual(
            {"court_submission", "professional_service"},
            {contract["artifact_class"] for contract in contracts},
        )
        self.assertEqual(2, len(contracts))
        for contract in contracts:
            self.assertFalse(contract["write_back"])
            self.assertFalse(contract["redaction_policy"]["private_case_payload"])
            self.assertFalse(contract["redaction_policy"]["absolute_paths"])
            self.assertFalse(contract["redaction_policy"]["governance_metadata_visible"])

    def test_output_contract_schema_requires_contracts(self) -> None:
        schema = load_json("templates/output-contract.schema.json")
        self.assertEqual({"schema_version", "contracts"}, set(schema["required"]))
        item_required = set(schema["properties"]["contracts"]["items"]["required"])
        for field in (
            "artifact_class",
            "source_ssot",
            "allowed_fields",
            "redaction_policy",
            "write_back",
            "promotion_gate",
            "render_gate",
            "failure_state",
        ):
            self.assertIn(field, item_required)

    def test_promotion_evidence_has_two_independent_e2e_roles(self) -> None:
        payload = load_json("templates/promotion-evidence.example.json")
        cases = payload["e2e_cases"]
        self.assertEqual(
            {"complete-nine-document", "hold-case"},
            {case["role"] for case in cases},
        )
        complete = next(case for case in cases if case["role"] == "complete-nine-document")
        hold = next(case for case in cases if case["role"] == "hold-case")
        self.assertEqual(9, complete["document_count"])
        self.assertTrue(hold["hold_triggered"])
        self.assertNotEqual(payload["seats"]["builder"], payload["seats"]["acceptance"])

    def test_rc3_scope_excludes_deferred_donor(self) -> None:
        forbidden = ("derived" + "_view", "case-knowledge" + "-graph")
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in VALIDATOR.TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in forbidden:
                self.assertNotIn(marker, text, str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()
