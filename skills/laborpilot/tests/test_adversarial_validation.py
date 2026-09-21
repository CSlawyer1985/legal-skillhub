"""实质性对抗验证报告与防伪门禁回归。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from adversarial_validation import (  # noqa: E402
    VALIDATOR_ID,
    adversarial_report_errors,
    build_adversarial_report,
    business_state_digest,
)
from workflow_graph import validation_report_is_valid  # noqa: E402
from case_state import procedure_digest  # noqa: E402


WORKFLOW = SCRIPTS / "workflow_graph.py"
VALIDATE = SCRIPTS / "validate_case.py"


class AdversarialValidationTest(unittest.TestCase):
    def run_cli(self, script: Path, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(script), *arguments], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(
            result.returncode, expected,
            f"命令退出码异常：{result.args}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        return result

    def prepared_state(self, case_root: Path) -> Path:
        # 复用金额专项已验证的完整争点、证据、法源和请求状态，但不导入其测试类到模块全局。
        from tests.test_claims_executor import CALCULATE, PROCEDURE, ClaimsExecutorTest

        helper = ClaimsExecutorTest()
        state_path = helper.prepare_claims_node(case_root)
        input_path = case_root / "calculation.json"
        helper.write_input(input_path, [helper.calculation_input()])
        helper.run_cli(CALCULATE, "--state", str(state_path), "--input", str(input_path))
        procedure_path = case_root / "procedure.json"
        procedure_path.write_text(
            json.dumps(helper.procedure_input(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        helper.run_cli(PROCEDURE, "--state", str(state_path), "--input", str(procedure_path))
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["current_node"] = "validation"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return state_path

    def test_report_contains_recomputable_business_results_and_can_be_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepared_state(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            report = build_adversarial_report(state)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                [item["check_id"] for item in report["checks"]],
                [
                    "opponent_case", "failure_boundaries", "fact_layering",
                    "fact_conflicts", "citation_consistency", "procedure_completeness",
                ],
            )
            self.assertTrue(report["procedure_matrix"])
            self.assertEqual(report["fact_conflict_matrix"], [])
            challenge = report["challenge_matrix"][0]
            self.assertEqual(challenge["issue_id"], "issue-compensation")
            self.assertTrue(challenge["opponent_strongest_argument"])
            self.assertTrue(challenge["failure_boundary"])
            self.assertFalse(adversarial_report_errors(report, state))

            report_path = case_root / "adversarial.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.run_cli(
                WORKFLOW, "record-validation", "--state", str(state_path),
                "--kind", "adversarial", "--validator", VALIDATOR_ID,
                "--report", str(report_path),
            )
            updated = json.loads(state_path.read_text(encoding="utf-8"))
            record = updated["validations"][-1]
            self.assertEqual(record["report_sha256"], hashlib.sha256(report_path.read_bytes()).hexdigest())
            self.assertTrue(validation_report_is_valid(record, updated))

    def test_arbitrary_or_stale_adversarial_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepared_state(case_root)
            fake_path = case_root / "fake.json"
            fake_path.write_text(json.dumps({"status": "pass", "findings": []}), encoding="utf-8")
            fake = self.run_cli(
                WORKFLOW, "record-validation", "--state", str(state_path),
                "--kind", "adversarial", "--validator", VALIDATOR_ID,
                "--report", str(fake_path), expected=2,
            )
            self.assertIn("重新计算校验", fake.stderr)

            state = json.loads(state_path.read_text(encoding="utf-8"))
            report = build_adversarial_report(state)
            report_path = case_root / "stale.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            state["issues"][0]["failure_consequence"] = "若解除性质或工资口径不能证明，当前请求金额可能减少或不获支持。"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            stale = self.run_cli(
                WORKFLOW, "record-validation", "--state", str(state_path),
                "--kind", "adversarial", "--validator", VALIDATOR_ID,
                "--report", str(report_path), expected=2,
            )
            self.assertIn("state_digest", stale.stderr)

    def test_fact_layering_and_ungrounded_opponent_case_return_for_rework(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path = self.prepared_state(Path(temporary))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            issue = state["issues"][0]
            issue["our_position"]["elements"][0]["status"] = "supported"
            issue["our_position"]["elements"][0]["gaps"] = []
            issue["opponent_position"]["uncertainties"] = []
            report = build_adversarial_report(state)
            self.assertEqual(report["status"], "return")
            codes = {item["code"] for item in report["findings"]}
            self.assertIn("SUPPORTED_ELEMENT_WITHOUT_SUPPORTED_FACT", codes)
            self.assertIn("OPPONENT_CASE_UNGROUNDED", codes)

    def test_fact_conflicts_block_silent_certainty_and_one_way_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path = self.prepared_state(Path(temporary))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["facts"] = [
                {
                    "fact_id": "fact-client-dismissal",
                    "statement": "劳动者陈述公司口头解除劳动合同。",
                    "status": "supported", "sources": [],
                    "conflicts_with_fact_ids": ["fact-employer-resignation"],
                    "conflict_status": "unresolved",
                    "conflict_explanation": "双方对劳动关系终止原因存在直接矛盾。",
                    "conflict_next_action": "核对解除通知、辞职申请及完整聊天记录。",
                },
                {
                    "fact_id": "fact-employer-resignation",
                    "statement": "用人单位主张劳动者自行辞职。",
                    "status": "opponent_allegation", "sources": [],
                    "conflicts_with_fact_ids": ["fact-client-dismissal"],
                    "conflict_status": "unresolved",
                    "conflict_explanation": "双方对劳动关系终止原因存在直接矛盾。",
                    "conflict_next_action": "核对解除通知、辞职申请及完整聊天记录。",
                },
            ]
            report = build_adversarial_report(state)
            codes = {item["code"] for item in report["findings"]}
            self.assertEqual(report["status"], "blocked")
            self.assertIn("FACT_CONFLICT_STRUCTURE", codes)
            self.assertIn("UNRESOLVED_FACT_CONFLICT", codes)
            self.assertIn("不得标记为 supported", "\n".join(
                item["message"] for item in report["findings"]
            ))
            state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
            deterministic = json.loads(self.run_cli(
                VALIDATE, "--state", str(state_path), expected=1,
            ).stdout)
            self.assertIn(
                "FACT_CONFLICT",
                {item["code"] for item in deterministic["findings"]},
            )
            malformed = json.loads(json.dumps(state, ensure_ascii=False))
            malformed["facts"][0]["conflict_status"] = []
            malformed_report = build_adversarial_report(malformed)
            self.assertEqual(malformed_report["status"], "blocked")
            self.assertIn(
                "FACT_CONFLICT_STRUCTURE",
                {item["code"] for item in malformed_report["findings"]},
            )

            state["facts"][0]["status"] = "client_statement"
            state["facts"][1]["conflicts_with_fact_ids"] = []
            state["facts"][1]["conflict_status"] = "none"
            state["facts"][1]["conflict_explanation"] = None
            state["facts"][1]["conflict_next_action"] = None
            one_way = build_adversarial_report(state)
            self.assertIn(
                "事实冲突关系必须双向一致",
                "\n".join(item["message"] for item in one_way["findings"]),
            )

    def test_procedure_omission_tampering_and_change_invalidate_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path = self.prepared_state(Path(temporary))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            baseline = build_adversarial_report(state)
            baseline_digest = business_state_digest(state)
            self.assertEqual(baseline["status"], "pass")

            missing = json.loads(json.dumps(state, ensure_ascii=False))
            missing["procedural_assessments"] = []
            missing_report = build_adversarial_report(missing)
            self.assertEqual(missing_report["status"], "blocked")
            self.assertIn(
                "PROCEDURE_INCOMPLETE",
                {item["code"] for item in missing_report["findings"]},
            )

            tampered = json.loads(json.dumps(state, ensure_ascii=False))
            tampered["procedural_assessments"][0]["remedy_paths"] = []
            tampered_report = build_adversarial_report(tampered)
            self.assertEqual(tampered_report["status"], "blocked")
            self.assertIn(
                "procedure_digest 与程序分析内容不一致",
                "\n".join(item["message"] for item in tampered_report["findings"]),
            )

            changed = json.loads(json.dumps(state, ensure_ascii=False))
            assessment = changed["procedural_assessments"][0]
            assessment["risk"] = "若请求类型或金额口径变化，应重新复核一裁终局和后续救济路径。"
            assessment["procedure_digest"] = procedure_digest(assessment)
            self.assertNotEqual(baseline_digest, business_state_digest(changed))
            stale_errors = adversarial_report_errors(baseline, changed)
            self.assertTrue(any("state_digest" in message for message in stale_errors))
            self.assertTrue(any("procedure_matrix" in message for message in stale_errors))

    def test_empty_challenge_matrix_is_blocked_and_report_tampering_breaks_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepared_state(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            empty_state = dict(state)
            empty_state["issues"] = []
            empty_report = build_adversarial_report(empty_state)
            self.assertEqual(empty_report["status"], "blocked")
            self.assertIn("NO_REVIEWED_ISSUES", {item["code"] for item in empty_report["findings"]})

            report = build_adversarial_report(state)
            report_path = case_root / "adversarial.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            record = {
                "kind": "adversarial", "status": "pass", "report_path": str(report_path),
                "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            }
            self.assertTrue(validation_report_is_valid(record, state))
            report_path.write_text(json.dumps({**report, "challenge_matrix": []}, ensure_ascii=False), encoding="utf-8")
            self.assertFalse(validation_report_is_valid(record, state))


if __name__ == "__main__":
    unittest.main()
