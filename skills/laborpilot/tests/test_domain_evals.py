"""领域召回精度、复合争点和法律版本边界评测。"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
EVAL_RUNNER = SCRIPTS / "domain_eval.py"
EVALS_PATH = ROOT / "evals" / "evals.json"
LEGAL_VERSIONS_PATH = ROOT / "evals" / "legal-version-cases.json"
sys.path.insert(0, str(SCRIPTS))
import domain_eval as DOMAIN_EVAL  # noqa: E402
import issue_router as ROUTER  # noqa: E402


class DomainEvalsTest(unittest.TestCase):
    def test_versioned_eval_suite_passes_business_results(self):
        result = DOMAIN_EVAL.evaluate(EVALS_PATH, LEGAL_VERSIONS_PATH)
        self.assertEqual(result["status"], "pass", result["findings"])
        self.assertEqual(result["summary"], {
            "router_case_count": 14,
            "legal_version_case_count": 4,
            "passed_count": 18,
            "blocked_count": 0,
        })
        expected_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(result["package_version"], expected_version)

    def test_negative_context_and_out_of_domain_do_not_recall_excluded_issues(self):
        payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        selected = {
            item["id"]: item
            for item in payload["evals"]
            if item["case_type"] in {"negative_context", "out_of_domain"}
        }
        self.assertEqual(set(selected), {
            "negative-only-double-wage",
            "negative-voluntary-resignation-annual-leave",
            "out-of-domain-commercial-contract",
        })
        for eval_id, item in selected.items():
            with self.subTest(eval_id=eval_id):
                results = ROUTER.query_knowledge(item["prompt"])
                issue_text = "\n".join(result["issue"] for result in results)
                for term in item["forbidden_issue_terms"]:
                    self.assertNotIn(term, issue_text)
                minimum, maximum = item["expected_result_range"]
                self.assertTrue(minimum <= len(results) <= maximum)

    def test_legal_version_boundary_uses_effective_date_not_publication_date(self):
        payload = json.loads(LEGAL_VERSIONS_PATH.read_text(encoding="utf-8"))
        cases = DOMAIN_EVAL.validate_legal_dataset(payload)
        result, findings = DOMAIN_EVAL.evaluate_legal_versions(cases)
        self.assertFalse(findings)
        active = {item["id"]: item["active_version_ids"] for item in result}
        self.assertEqual(
            active["published-but-not-effective-2025-08-01"],
            ["interpretation-i-article-32p1"],
        )
        self.assertEqual(
            active["effective-boundary-2025-09-01"],
            ["interpretation-ii-2025-supersession-rule"],
        )

    def test_tampered_legal_version_expectation_is_detected(self):
        payload = json.loads(LEGAL_VERSIONS_PATH.read_text(encoding="utf-8"))
        cases = DOMAIN_EVAL.validate_legal_dataset(payload)
        changed = deepcopy(cases)
        changed[0]["expected_active_version_ids"] = ["interpretation-ii-2025-supersession-rule"]
        result, findings = DOMAIN_EVAL.evaluate_legal_versions(changed)
        self.assertEqual(result[0]["status"], "blocked")
        self.assertTrue(any("published-but-not-effective" in finding for finding in findings))

    def test_dataset_contract_requires_precision_and_all_case_types(self):
        payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        missing_forbidden = deepcopy(payload)
        target = next(
            item for item in missing_forbidden["evals"]
            if item["case_type"] == "negative_context"
        )
        target["forbidden_issue_terms"] = []
        with self.assertRaisesRegex(ValueError, "误召回禁止词"):
            DOMAIN_EVAL.validate_router_dataset(missing_forbidden)

        missing_type = deepcopy(payload)
        missing_type["evals"] = [
            item for item in missing_type["evals"] if item["case_type"] != "out_of_domain"
        ]
        with self.assertRaisesRegex(ValueError, "评测类型覆盖不完整"):
            DOMAIN_EVAL.validate_router_dataset(missing_type)

    def test_router_dataset_rejects_internal_card_and_gate_fields(self):
        payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        for field in ("expected_cards", "expected_gate"):
            with self.subTest(field=field):
                changed = deepcopy(payload)
                changed["evals"][0][field] = ["internal-id"]
                with self.assertRaisesRegex(ValueError, f"内部字段：{field}"):
                    DOMAIN_EVAL.validate_router_dataset(changed)

    def test_single_active_legal_timeline_rejects_overlap_and_gap(self):
        payload = json.loads(LEGAL_VERSIONS_PATH.read_text(encoding="utf-8"))

        overlap = deepcopy(payload)
        overlap["topics"][0]["versions"][0]["effective_to"] = "2025-09-01"
        with self.assertRaisesRegex(ValueError, "存在重叠"):
            DOMAIN_EVAL.validate_legal_dataset(overlap)

        gap = deepcopy(payload)
        gap["topics"][0]["versions"][0]["effective_to"] = "2025-08-30"
        with self.assertRaisesRegex(ValueError, "存在空档"):
            DOMAIN_EVAL.validate_legal_dataset(gap)

    def test_cli_report_does_not_expose_card_bodies_or_internal_ids(self):
        completed = subprocess.run(
            [sys.executable, str(EVAL_RUNNER)], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertNotIn("analysis_points", completed.stdout)
        self.assertNotIn("zhejiang_guidance", completed.stdout)
        self.assertNotIn("expected_cards", completed.stdout)
        self.assertNotRegex(completed.stdout, r'"[A-Z][0-9]{1,3}"')


if __name__ == "__main__":
    unittest.main()
