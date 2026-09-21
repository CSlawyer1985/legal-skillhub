"""证据链与举证责任执行器的业务行为回归。"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE_STATE = ROOT / "scripts" / "case_state.py"
WORKFLOW = ROOT / "scripts" / "workflow_graph.py"
VALIDATE = ROOT / "scripts" / "validate_case.py"
INGEST_MATERIALS = ROOT / "scripts" / "ingest_materials.py"
BUILD_TIMELINE = ROOT / "scripts" / "build_timeline.py"
BUILD_ISSUES = ROOT / "scripts" / "build_issue_matrix.py"
BUILD_EVIDENCE = ROOT / "scripts" / "build_evidence_chain.py"


class EvidenceChainExecutorTest(unittest.TestCase):
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

    def valid_issue(self) -> dict:
        return {
            "issue_id": "issue-unlawful-dismissal",
            "issue": "用人单位解除劳动合同是否构成违法解除",
            "issue_type": "claim",
            "analysis_status": "reviewed",
            "our_position": {
                "position": "我方主张用人单位已单方解除劳动合同，且应证明解除事由与程序合法。",
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
                        "gaps": ["尚未取得违纪事实与规章制度材料"],
                    },
                ],
                "conclusion": "解除行为已有材料支持，违法性仍取决于用人单位的解除依据。",
            },
            "opponent_position": {
                "strongest_argument": "用人单位可能主张劳动者严重违纪，规章制度有效且解除程序完成。",
                "fact_ids": [],
                "evidence_ids": [],
                "rule_ids": [],
                "response": "应逐项核对违纪事实、规章制度效力、公示与解除程序。",
                "uncertainties": ["对方尚未提交具体违纪证据与规章制度文本"],
            },
            "alternative_paths": [{
                "path": "若不构成违法解除，继续审查是否应支付经济补偿",
                "trigger": "解除事由或程序被认定合法，但解除类型仍需支付补偿",
                "consequence": "请求项目由违法解除赔偿金转为经济补偿",
            }],
            "failure_consequence": "若用人单位完成解除事由、制度效力和程序的举证，赔偿金请求可能不获支持。",
        }

    def valid_chains(self, material_id: str) -> list[dict]:
        return [
            {
                "evidence_id": "evidence-dismissal-notice",
                "issue_id": "issue-unlawful-dismissal",
                "element_ids": ["element-dismissal-act"],
                "proposition": "用人单位已经作出并送达解除劳动合同的意思表示",
                "orientation": "supports_our_position",
                "fact_ids": ["fact-dismissal-notice"],
                "burden": {
                    "primary_party": "employee",
                    "control_party": "employee",
                    "rule": "general",
                    "shifted_to": None,
                    "rationale": "劳动者先对用人单位已作出解除表示承担初步举证责任。",
                    "initial_showing": "劳动者提交载明解除意思表示的通知即可完成初步举证。",
                    "shift_condition": "劳动者完成初步举证后，再审查用人单位的解除根据。",
                    "adverse_consequence": "劳动者不能证明解除行为发生时，相应赔偿请求可能不获支持。",
                },
                "items": [{
                    "evidence_item_id": "item-dismissal-notice",
                    "name": "解除劳动合同通知",
                    "status": "available",
                    "material_ids": [material_id],
                    "purpose": "证明用人单位已经向劳动者作出解除劳动合同的意思表示。",
                    "authenticity_status": "original",
                    "source_locator": {"material_id": material_id, "line": 1},
                }],
                "assessment": {
                    "status": "sufficient",
                    "reasoning": "现有解除通知可以证明解除行为本身已经发生。",
                    "gaps": [],
                    "actions": [],
                },
            },
            {
                "evidence_id": "evidence-dismissal-ground-gap",
                "issue_id": "issue-unlawful-dismissal",
                "element_ids": ["element-dismissal-ground"],
                "proposition": "用人单位主张的违纪事实、制度依据与解除程序均成立",
                "orientation": "supports_opponent_position",
                "fact_ids": [],
                "burden": {
                    "primary_party": "employee",
                    "control_party": "employer",
                    "rule": "employer_controlled",
                    "shifted_to": "employer",
                    "rationale": "解除决定、规章制度与违纪调查材料通常由用人单位掌握。",
                    "initial_showing": "劳动者先证明用人单位已作出解除表示并对合法性提出争议。",
                    "shift_condition": "劳动者完成解除事实的初步举证后，由用人单位证明解除合法。",
                    "adverse_consequence": "用人单位无法提交由其掌握的解除依据时，应承担举证不能的不利后果。",
                },
                "items": [{
                    "evidence_item_id": "item-employer-rules",
                    "name": "规章制度及违纪调查材料",
                    "status": "opponent_controlled",
                    "material_ids": [],
                    "purpose": "证明解除事由具有事实依据且规章制度已合法制定并公示。",
                    "authenticity_status": "to_verify",
                    "source_locator": None,
                }],
                "assessment": {
                    "status": "insufficient",
                    "reasoning": "当前没有取得用人单位掌握的解除依据与程序材料。",
                    "gaps": ["缺少违纪事实证据、规章制度文本与公示证据"],
                    "actions": ["要求用人单位提交解除决定所依据的全部事实、制度与程序材料"],
                },
            },
        ]

    def prepare_evidence_node(self, case_root: Path) -> tuple[Path, str]:
        state_path = case_root / ".casework" / "case_state.json"
        material_path = case_root / "解除通知.txt"
        material_path.write_text("2025年6月15日公司向劳动者送达解除通知。", encoding="utf-8")
        self.run_cli(CASE_STATE, "init", "--output", str(state_path))
        self.run_cli(
            CASE_STATE, "set-task", "--input", str(state_path),
            "--representation", "employee", "--stage", "arbitration",
            "--user-request", "分析违法解除请求的证据链与举证责任",
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
        issues_path = case_root / "issues.json"
        issues_path.write_text(json.dumps({"issues": [self.valid_issue()]}, ensure_ascii=False), encoding="utf-8")
        self.run_cli(BUILD_ISSUES, "--state", str(state_path), "--input", str(issues_path))
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        return state_path, material_id

    def write_chains(self, path: Path, records: list[dict]) -> None:
        path.write_text(json.dumps({"evidence": records}, ensure_ascii=False), encoding="utf-8")

    def test_scaffold_is_review_only_and_does_not_unlock_node(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, _ = self.prepare_evidence_node(case_root)
            result = json.loads(self.run_cli(
                BUILD_EVIDENCE, "--state", str(state_path), "--scaffold",
            ).stdout)
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(result["candidate_count"], 2)
            scaffold = json.loads(Path(result["scaffold"]).read_text(encoding="utf-8"))
            self.assertEqual(
                {item["element_ids"][0] for item in scaffold["candidates"]},
                {"element-dismissal-act", "element-dismissal-ground"},
            )
            self.assertTrue(all(item["analysis_status"] == "to_review" for item in scaffold["candidates"]))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["evidence"], [])
            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("structured_evidence", blocked.stderr)
            waiver = self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", "structured_evidence",
                "--reason", "当前尚未取得任何可用证据材料。",
                "--confirmed-by", "user", expected=2,
            )
            self.assertIn("不允许豁免", waiver.stderr)

    def test_reviewed_chains_cover_elements_and_write_bidirectional_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, material_id = self.prepare_evidence_node(case_root)
            input_path = case_root / "evidence.json"
            self.write_chains(input_path, self.valid_chains(material_id))
            result = json.loads(self.run_cli(
                BUILD_EVIDENCE, "--state", str(state_path), "--input", str(input_path),
            ).stdout)
            self.assertEqual(result["evidence_chain_count"], 2)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            issue = state["issues"][0]
            elements = {item["element_id"]: item for item in issue["our_position"]["elements"]}
            self.assertEqual(elements["element-dismissal-act"]["evidence_ids"], ["evidence-dismissal-notice"])
            self.assertEqual(elements["element-dismissal-ground"]["evidence_ids"], ["evidence-dismissal-ground-gap"])
            self.assertEqual(issue["opponent_position"]["evidence_ids"], ["evidence-dismissal-ground-gap"])
            burden = next(
                item["burden"] for item in state["evidence"]
                if item["evidence_id"] == "evidence-dismissal-ground-gap"
            )
            self.assertEqual(burden["control_party"], "employer")
            self.assertEqual(burden["shifted_to"], "employer")
            self.assertIn("不利后果", burden["adverse_consequence"])
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_node"], "authority_research")

    def test_invalid_chains_are_rejected_without_mutating_state(self):
        cases = []
        cases.append(("available 无材料", lambda chains: chains[0]["items"][0].update(material_ids=[]), "必须关联 material_id"))
        cases.append(("不存在的 fact_id", lambda chains: chains[0].update(fact_ids=["fact-missing"]), "引用不存在的 ID"))
        cases.append(("不存在的 material_id", lambda chains: chains[0]["items"][0].update(material_ids=["material-missing"]), "引用不存在的 ID"))
        cases.append(("非充分证据缺少行动", lambda chains: chains[1]["assessment"].update(actions=[]), "必须同时列明 gaps 和 actions"))
        cases.append(("gap_only 含已有证据", lambda chains: chains[0].update(orientation="gap_only"), "不得包含 available"))
        cases.append(("employer_controlled 控制方错误", lambda chains: chains[1]["burden"].update(control_party="employee"), "control_party=employer"))
        cases.append((
            "sufficient 没有已核实证据",
            lambda chains: chains[0]["items"][0].update(
                status="to_verify", material_ids=[], authenticity_status="to_verify", source_locator=None,
            ),
            "证据评估为 sufficient 时至少需要",
        ))
        cases.append(("构成要件没有证据链", lambda chains: chains.pop(), "尚未建立证据链或缺口链"))

        for label, mutate, expected_message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                case_root = Path(temporary)
                state_path, material_id = self.prepare_evidence_node(case_root)
                original = state_path.read_bytes()
                records = deepcopy(self.valid_chains(material_id))
                mutate(records)
                input_path = case_root / "invalid-evidence.json"
                self.write_chains(input_path, records)
                result = self.run_cli(
                    BUILD_EVIDENCE, "--state", str(state_path), "--input", str(input_path), expected=2,
                )
                self.assertIn(expected_message, result.stderr)
                self.assertEqual(state_path.read_bytes(), original)

    def test_tampered_reverse_link_is_blocked_by_independent_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, material_id = self.prepare_evidence_node(case_root)
            input_path = case_root / "evidence.json"
            self.write_chains(input_path, self.valid_chains(material_id))
            self.run_cli(BUILD_EVIDENCE, "--state", str(state_path), "--input", str(input_path))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["issues"][0]["our_position"]["elements"][0]["evidence_ids"] = []
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = self.run_cli(VALIDATE, "--state", str(state_path), expected=1)
            payload = json.loads(result.stdout)
            messages = "\n".join(item["message"] for item in payload["findings"])
            self.assertIn("双向链接不一致", messages)
            self.assertTrue(any(item["code"] == "EVIDENCE_CHAIN" for item in payload["findings"]))

    def test_legacy_placeholder_requires_explicit_replacement_and_keeps_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path, material_id = self.prepare_evidence_node(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["evidence"] = [{"evidence_id": "legacy-placeholder"}]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("structured_evidence", blocked.stderr)
            input_path = case_root / "replacement-evidence.json"
            self.write_chains(input_path, self.valid_chains(material_id))
            needs_replace = self.run_cli(
                BUILD_EVIDENCE, "--state", str(state_path), "--input", str(input_path), expected=2,
            )
            self.assertIn("--replace-existing-evidence", needs_replace.stderr)
            unchanged = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged["evidence"], [{"evidence_id": "legacy-placeholder"}])

            result = json.loads(self.run_cli(
                BUILD_EVIDENCE, "--state", str(state_path), "--input", str(input_path),
                "--replace-existing-evidence",
            ).stdout)
            self.assertEqual(result["replaced_previous_count"], 1)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(state["evidence"]), 2)
            previous = json.loads(Path(state["previous_state"]).read_text(encoding="utf-8"))
            self.assertEqual(previous["evidence"], [{"evidence_id": "legacy-placeholder"}])


if __name__ == "__main__":
    unittest.main()
