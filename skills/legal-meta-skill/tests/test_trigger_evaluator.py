"""静态触发覆盖与可选 provider-backed 路由证据回归测试。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE_ROOT / "scripts" / "evaluate_trigger_cases.py"


class TriggerEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.skill_dir = Path(temporary_directory.name) / "legal-meta-skill"
        (self.skill_dir / "evals").mkdir(parents=True)
        shutil.copyfile(PACKAGE_ROOT / "SKILL.md", self.skill_dir / "SKILL.md")
        shutil.copyfile(
            PACKAGE_ROOT / "evals" / "trigger_cases.json",
            self.skill_dir / "evals" / "trigger_cases.json",
        )

    def observed_document(self) -> dict:
        cases = json.loads((PACKAGE_ROOT / "evals/trigger_cases.json").read_text(encoding="utf-8"))["cases"]
        return {
            "provider": "synthetic-provider-harness",
            "model": "synthetic-route-model",
            "run_at": "2026-08-12T12:00:00+08:00",
            "cases": [
                {
                    "id": case["id"],
                    "triggered": case["kind"] == "should-trigger",
                    "selected_skill": "legal-meta-skill" if case["kind"] == "should-trigger" else None,
                }
                for case in cases
            ],
        }

    def run_evaluator(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.skill_dir), *extra_args],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_with_observed(self, observed: dict) -> tuple[subprocess.CompletedProcess[str], dict]:
        observed_path = self.skill_dir / "reports" / "observed.json"
        output_path = self.skill_dir / "reports" / "report.json"
        observed_path.parent.mkdir(parents=True, exist_ok=True)
        observed_path.write_text(json.dumps(observed, ensure_ascii=False), encoding="utf-8")
        completed = self.run_evaluator(
            "--cases",
            "evals/trigger_cases.json",
            "--observed-results",
            "reports/observed.json",
            "--output",
            "reports/report.json",
        )
        return completed, json.loads(output_path.read_text(encoding="utf-8"))

    def test_complete_observations_are_recorded_as_provider_backed(self) -> None:
        completed, report = self.run_with_observed(self.observed_document())

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["evidence_kind"], "provider_passed")
        self.assertFalse(report["not_model_trigger_rate"])
        self.assertEqual(report["observed_results"]["passed"], report["observed_results"]["total"])
        self.assertNotIn("provider-backed 模型触发运行", report["missing_evidence"])

    def test_incomplete_observations_fail_without_upgrading_evidence(self) -> None:
        observed = self.observed_document()
        observed["cases"].pop()

        completed, report = self.run_with_observed(observed)

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["evidence_kind"], "provider_failed")
        self.assertIn("provider-backed 模型触发运行", report["missing_evidence"])

    def test_route_mismatch_is_provider_failed_not_provider_passed(self) -> None:
        observed = self.observed_document()
        observed["cases"][0]["selected_skill"] = "another-skill"

        completed, report = self.run_with_observed(observed)

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["evidence_kind"], "provider_failed")
        self.assertTrue(report["not_model_trigger_rate"])

    def test_audit_mode_can_write_outside_without_writing_skill(self) -> None:
        before = sorted(
            (path.relative_to(self.skill_dir), path.stat().st_mtime_ns)
            for path in self.skill_dir.rglob("*")
            if path.is_file()
        )
        outside = Path(self.skill_dir.parent) / "audit-outside.json"

        completed = self.run_evaluator(
            "--cases",
            "evals/trigger_cases.json",
            "--output",
            str(outside),
            "--audit-mode",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(outside.is_file())
        after = sorted(
            (path.relative_to(self.skill_dir), path.stat().st_mtime_ns)
            for path in self.skill_dir.rglob("*")
            if path.is_file()
        )
        self.assertEqual(before, after)

    def test_malformed_cases_json_fails_with_friendly_error(self) -> None:
        (self.skill_dir / "evals" / "broken.json").write_text("{not json", encoding="utf-8")

        completed = self.run_evaluator("--cases", "evals/broken.json", "--output", "reports/report.json")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("错误", completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_missing_cases_file_fails_with_friendly_error(self) -> None:
        completed = self.run_evaluator("--cases", "evals/absent.json", "--output", "reports/report.json")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("错误", completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cases_document_without_list_fails_with_friendly_error(self) -> None:
        (self.skill_dir / "evals" / "scalar.json").write_text('"只是字符串"', encoding="utf-8")

        completed = self.run_evaluator("--cases", "evals/scalar.json", "--output", "reports/report.json")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("必须为数组或含 cases 数组的对象", completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_non_object_case_element_is_reported_not_crashing(self) -> None:
        cases = json.loads((self.skill_dir / "evals/trigger_cases.json").read_text(encoding="utf-8"))
        cases["cases"].append("not-a-dict")
        (self.skill_dir / "evals/trigger_cases.json").write_text(
            json.dumps(cases, ensure_ascii=False), encoding="utf-8"
        )

        completed = self.run_evaluator("--cases", "evals/trigger_cases.json", "--output", "reports/report.json")

        self.assertEqual(completed.returncode, 1)
        self.assertNotIn("Traceback", completed.stderr)
        report = json.loads((self.skill_dir / "reports/report.json").read_text(encoding="utf-8"))
        self.assertIn("必须为对象", " ".join(report["errors"]))

    def test_output_path_outside_skill_dir_is_rejected(self) -> None:
        outside = Path(self.skill_dir.parent) / "escaped-report.json"

        completed = self.run_evaluator(
            "--cases", "evals/trigger_cases.json", "--output", str(outside)
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("必须位于 Skill 目录内", completed.stdout + completed.stderr)
        self.assertFalse(outside.exists())

    def test_observed_results_path_escape_is_rejected(self) -> None:
        completed = self.run_evaluator(
            "--cases",
            "evals/trigger_cases.json",
            "--observed-results",
            "../observed.json",
            "--output",
            "reports/report.json",
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("必须位于 Skill 目录内", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
