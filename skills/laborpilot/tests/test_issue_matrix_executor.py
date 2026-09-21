"""请求／抗辩矩阵执行器的业务行为回归。"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE_STATE = ROOT / "scripts" / "case_state.py"
WORKFLOW = ROOT / "scripts" / "workflow_graph.py"
INGEST_MATERIALS = ROOT / "scripts" / "ingest_materials.py"
BUILD_TIMELINE = ROOT / "scripts" / "build_timeline.py"
BUILD_ISSUES = ROOT / "scripts" / "build_issue_matrix.py"


class IssueMatrixExecutorTest(unittest.TestCase):
    def run_cli(self, script: Path, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            f"命令退出码异常：{result.args}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        return result

    def prepare_issue_node(self, case_root: Path) -> tuple[Path, str]:
        state_path = case_root / ".casework" / "case_state.json"
        material_path = case_root / "解除通知.txt"
        material_path.write_text("2025年6月15日公司向劳动者送达解除通知。", encoding="utf-8")
        self.run_cli(CASE_STATE, "init", "--output", str(state_path))
        self.run_cli(
            CASE_STATE, "set-task", "--input", str(state_path),
            "--representation", "employee", "--stage", "arbitration",
            "--user-request", "分析违法解除赔偿金请求并审查对方抗辩",
            "--requested-output", "案件研判报告", "--confirmed-by", "user",
        )
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        self.run_cli(INGEST_MATERIALS, "--state", str(state_path), "--source", str(material_path))
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        material_id = state["materials"][0]["material_id"]
        facts_path = case_root / "facts.json"
        facts_path.write_text(json.dumps({"facts": [{
            "fact_id": "fact-dismissal-notice",
            "statement": "用人单位于2025年6月15日向劳动者送达解除通知。",
            "status": "supported",
            "sources": [material_id],
            "occurred_on": "2025-06-15",
            "source_locators": [{"material_id": material_id, "line": 1}],
        }]}, ensure_ascii=False), encoding="utf-8")
        self.run_cli(BUILD_TIMELINE, "--state", str(state_path), "--input", str(facts_path))
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        return state_path, material_id

    def valid_issue(self) -> dict:
        return {
            "issue_id": "issue-unlawful-dismissal",
            "issue": "用人单位解除劳动合同是否构成违法解除",
            "issue_type": "claim",
            "analysis_status": "reviewed",
            "our_position": {
                "position": "我方主张用人单位已单方解除劳动合同，且应对解除事由与程序合法性承担举证责任。",
                "elements": [
                    {
                        "element_id": "element-dismissal-act",
                        "description": "用人单位已作出并送达解除劳动合同的意思表示",
                        "status": "supported",
                        "fact_ids": ["fact-dismissal-notice"],
                        "evidence_ids": [],
                        "rule_ids": [],
                        "gaps": [],
                    },
                    {
                        "element_id": "element-dismissal-ground",
                        "description": "用人单位主张的解除事由具有事实与制度依据",
                        "status": "to_verify",
                        "fact_ids": [],
                        "evidence_ids": [],
                        "rule_ids": [],
                        "gaps": ["尚未取得用人单位主张的违纪事实与规章制度材料"],
                    },
                ],
                "conclusion": "解除行为已有材料支持，但违法性结论仍取决于用人单位后续提交的解除依据。",
            },
            "opponent_position": {
                "strongest_argument": "用人单位可能主张劳动者存在严重违纪，规章制度已履行民主制定与公示程序，解除具有事实和制度依据。",
                "fact_ids": [],
                "evidence_ids": [],
                "rule_ids": [],
                "response": "应逐项核对违纪事实、规章制度效力、公示与解除程序，不得仅以解除通知中的定性表述作为证明。",
                "uncertainties": ["对方尚未提交具体违纪证据与规章制度文本"],
            },
            "alternative_paths": [{
                "path": "若不构成违法解除，继续审查是否存在应支付经济补偿的情形",
                "trigger": "解除事由或程序被认定合法，但具体解除类型仍需支付补偿",
                "consequence": "请求项目由违法解除赔偿金转为经济补偿，金额和请求权基础随之改变",
            }],
            "failure_consequence": "若用人单位完成解除事由、制度效力和解除程序的举证，违法解除赔偿金请求可能不获支持。",
        }

    def test_discovery_is_review_only_and_reviewed_matrix_passes_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, _ = self.prepare_issue_node(case_root)

            discovery = json.loads(self.run_cli(
                BUILD_ISSUES, "--state", str(state_path), "--discover",
                "--query", "公司以严重违纪为由解除劳动合同，劳动者主张2N赔偿金",
            ).stdout)
            self.assertEqual(discovery["status"], "review_required")
            self.assertGreater(discovery["candidate_count"], 0)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["issues"], [])
            discovery_payload = json.loads(Path(discovery["discovery"]).read_text(encoding="utf-8"))
            self.assertTrue(all(item["analysis_status"] == "to_review" for item in discovery_payload["candidates"]))
            self.assertTrue(all(set(item) == {
                "candidate_id", "issue", "analysis_status", "analysis_points",
                "zhejiang_guidance", "required_completion",
            } for item in discovery_payload["candidates"]))
            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("structured_issue", blocked.stderr)

            matrix_input = case_root / "issue-matrix.json"
            matrix_input.write_text(json.dumps({"issues": [self.valid_issue()]}, ensure_ascii=False), encoding="utf-8")
            result = json.loads(self.run_cli(
                BUILD_ISSUES, "--state", str(state_path), "--input", str(matrix_input),
            ).stdout)
            self.assertEqual(result["issue_count"], 1)
            self.assertTrue(Path(result["matrix"]).is_file())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["issues"][0]["analysis_status"], "reviewed")
            self.assertEqual(
                state["issues"][0]["opponent_position"]["strongest_argument"],
                self.valid_issue()["opponent_position"]["strongest_argument"],
            )
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_node"], "evidence_analysis")

    def test_matrix_rejects_missing_provenance_and_empty_opponent_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, _ = self.prepare_issue_node(case_root)
            invalid = self.valid_issue()
            invalid["our_position"]["elements"][0]["fact_ids"] = ["fact-does-not-exist"]
            invalid_path = case_root / "invalid-matrix.json"
            invalid_path.write_text(json.dumps({"issues": [invalid]}, ensure_ascii=False), encoding="utf-8")
            missing = self.run_cli(
                BUILD_ISSUES, "--state", str(state_path), "--input", str(invalid_path), expected=2,
            )
            self.assertIn("引用不存在的 ID", missing.stderr)

            invalid = self.valid_issue()
            invalid["opponent_position"]["strongest_argument"] = ""
            invalid_path.write_text(json.dumps({"issues": [invalid]}, ensure_ascii=False), encoding="utf-8")
            no_opponent = self.run_cli(
                BUILD_ISSUES, "--state", str(state_path), "--input", str(invalid_path), expected=2,
            )
            self.assertIn("opponent_position.strongest_argument", no_opponent.stderr)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["issues"], [])

    def test_legacy_placeholder_issue_can_be_replaced_with_history_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, _ = self.prepare_issue_node(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["issues"] = [{"issue_id": "legacy-placeholder"}]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("structured_issue", blocked.stderr)

            matrix_input = case_root / "replacement-matrix.json"
            matrix_input.write_text(json.dumps({"issues": [self.valid_issue()]}, ensure_ascii=False), encoding="utf-8")
            needs_explicit_replace = self.run_cli(
                BUILD_ISSUES,
                "--state", str(state_path),
                "--input", str(matrix_input),
                expected=2,
            )
            self.assertIn("--replace-existing-issues", needs_explicit_replace.stderr)
            unchanged = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["issues"], [{"issue_id": "legacy-placeholder"}])
            result = json.loads(self.run_cli(
                BUILD_ISSUES,
                "--state", str(state_path),
                "--input", str(matrix_input),
                "--replace-existing-issues",
            ).stdout)
            self.assertEqual(result["replaced_previous_count"], 1)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual([item["issue_id"] for item in state["issues"]], ["issue-unlawful-dismissal"])
            previous_state = Path(state["previous_state"])
            self.assertTrue(previous_state.is_file())
            previous = json.loads(previous_state.read_text(encoding="utf-8"))
            self.assertEqual(previous["issues"], [{"issue_id": "legacy-placeholder"}])


if __name__ == "__main__":
    unittest.main()
