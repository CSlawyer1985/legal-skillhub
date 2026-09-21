"""工作图业务节点完成条件的反例与完整流程回归。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
CASE_STATE = ROOT / "scripts" / "case_state.py"
WORKFLOW = ROOT / "scripts" / "workflow_graph.py"
VALIDATE = ROOT / "scripts" / "validate_case.py"
ADVERSARIAL_VALIDATE = ROOT / "scripts" / "adversarial_validation.py"
INGEST_MATERIALS = ROOT / "scripts" / "ingest_materials.py"
BUILD_TIMELINE = ROOT / "scripts" / "build_timeline.py"


class WorkflowRequirementsTest(unittest.TestCase):
    @staticmethod
    def canonical_digest(payload: object) -> str:
        rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(rendered.encode("utf-8")).hexdigest()

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

    def initialize_confirmed_case(self, state_path: Path) -> None:
        self.run_cli(CASE_STATE, "init", "--output", str(state_path))
        self.run_cli(
            CASE_STATE,
            "set-task",
            "--input", str(state_path),
            "--representation", "employee",
            "--stage", "arbitration",
            "--user-request", "分析劳动争议并起草仲裁申请书",
            "--requested-output", "仲裁申请书",
            "--confirmed-by", "user",
        )
        self.run_cli(
            WORKFLOW,
            "transition",
            "--state", str(state_path),
            "--event", "pass",
            "--actor", "test",
        )

    def structured_evidence(self, material_id: str) -> dict:
        return {
            "evidence_id": "evidence-1",
            "analysis_status": "reviewed",
            "issue_id": "issue-1",
            "element_ids": ["element-1"],
            "proposition": "解除通知能够证明用人单位已经作出解除劳动合同的意思表示",
            "orientation": "supports_our_position",
            "fact_ids": ["fact-1"],
            "burden": {
                "primary_party": "employee",
                "control_party": "employee",
                "rule": "general",
                "shifted_to": None,
                "rationale": "劳动者先就解除行为已经发生承担初步举证责任。",
                "initial_showing": "劳动者提交载明解除意思表示的解除通知即可完成初步举证。",
                "shift_condition": "劳动者完成初步举证后，再审查用人单位主张的解除依据。",
                "adverse_consequence": "劳动者不能证明解除行为发生时，相应赔偿请求可能不获支持。",
            },
            "items": [{
                "evidence_item_id": "evidence-item-1",
                "name": "解除劳动合同通知",
                "status": "available",
                "material_ids": [material_id],
                "purpose": "证明用人单位已经向劳动者作出解除劳动合同的意思表示。",
                "authenticity_status": "original",
                "source_locator": {"material_id": material_id, "line": 1},
            }],
            "assessment": {
                "status": "sufficient",
                "reasoning": "现有解除通知能够证明解除行为本身已经发生。",
                "gaps": [],
                "actions": [],
            },
            "created_by": "test",
            "created_at": "2026-08-24T10:00:00+08:00",
        }

    def structured_authority(self, state: dict) -> dict:
        article_text = "测试用规则：用人单位解除劳动合同时，应当依法证明解除事由和程序。"
        return {
            "rule_id": "rule-1",
            "analysis_status": "reviewed",
            "issue_id": "issue-1",
            "element_ids": ["element-1"],
            "proposition": "用人单位应当对解除事由和程序的合法性承担证明责任",
            "orientation": "supports_our_position",
            "adoption_status": "adopted",
            "document_id": "document-test-rule",
            "document_title": "测试用劳动合同规则",
            "document_number": "测试文号〔2026〕1号",
            "issuing_authority": "测试用规则制定机关",
            "authority_level": "law",
            "article_id": "article-test-rule-1",
            "article_number": "第一条",
            "article_text": article_text,
            "article_text_sha256": hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
            "verification_status": "verified",
            "validity_status": "effective",
            "effective_from": "2020-01-01",
            "effective_to": None,
            "territory_scope": "national",
            "applicable_jurisdictions": ["全国"],
            "case_jurisdiction": state["jurisdiction"],
            "analysis_date": state["analysis_date"],
            "relevant_date": "2025-06-15",
            "temporal_basis": "以用人单位作出解除决定的日期作为实体规则适用日期。",
            "applicability_status": "applicable",
            "applicability_reasoning": "该测试规则在相关日期已生效，且地域范围覆盖本案管辖地。",
            "source_type": "official",
            "source_name": "测试用官方来源",
            "source_url": "https://example.invalid/official/test-rule",
            "retrieved_at": "2026-08-24T10:00:00+08:00",
            "warning": None,
            "created_by": "test",
            "created_at": "2026-08-24T10:00:00+08:00",
        }

    def structured_procedure(self, state: dict) -> dict:
        record = {
            "assessment_id": "procedure-1",
            "issue_id": "issue-1",
            "claim_ids": ["claim-1"],
            "analysis_status": "reviewed",
            "case_jurisdiction": state["jurisdiction"],
            "analysis_date": state["analysis_date"],
            "limitation": {
                "status": "in_time", "trigger_date": "2026-01-01", "deadline_date": "2027-01-01",
                "basis_rule_ids": ["rule-1"],
                "analysis": "以已核对的请求权起算日为基础，分析日尚未超过仲裁时效。",
            },
            "jurisdiction": {
                "status": "proper", "forum": "测试劳动人事争议仲裁委员会",
                "case_jurisdiction": state["jurisdiction"], "basis_rule_ids": ["rule-1"],
                "analysis": "以已核对的劳动合同履行地和用人单位所在地判断当前管辖。",
            },
            "final_award": {
                "status": "not_applicable", "basis_rule_ids": [],
                "analysis": "本测试请求不符合已核对的一裁终局适用条件。",
            },
            "interim_relief": {
                "status": "not_applicable", "basis_rule_ids": [],
                "analysis": "当前已确认事实不满足先予执行或其他临时救济条件。",
            },
            "remedy_paths": ["仲裁裁决后按裁决类型在法定期限内起诉或申请执行。"],
            "pending_items": [],
            "risk": "时效中断、实际履行地或请求金额变化时必须重新复核。",
            "created_by": "test", "created_at": "2026-08-24T10:00:00+08:00",
        }
        digest_fields = (
            "assessment_id", "issue_id", "claim_ids", "analysis_status",
            "case_jurisdiction", "analysis_date", "limitation", "jurisdiction",
            "final_award", "interim_relief", "remedy_paths", "pending_items", "risk",
        )
        record["procedure_digest"] = self.canonical_digest({field: record.get(field) for field in digest_fields})
        return record

    def test_empty_business_state_is_blocked_but_confirmed_waiver_is_structured(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "case_state.json"
            self.initialize_confirmed_case(state_path)

            blocked = self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "pass",
                "--actor", "test",
                expected=2,
            )
            self.assertIn("traceable_material", blocked.stderr)

            self.run_cli(
                WORKFLOW,
                "record-waiver",
                "--state", str(state_path),
                "--requirement", "traceable_material",
                "--reason", "用户确认本轮仅基于对话文本分析，不提供文件材料。",
                "--confirmed-by", "user",
            )
            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "pass",
                "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_node"], "intake")
            self.assertEqual(state["node_requirement_waivers"][0]["requirement_id"], "traceable_material")

    def test_manual_empty_stage_close_is_rejected_by_independent_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "case_state.json"
            self.initialize_confirmed_case(state_path)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_node"] = "stage_close"
            state["pending_nodes"] = []
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_cli(VALIDATE, "--state", str(state_path), expected=1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "blocked")
            messages = "\n".join(item["message"] for item in payload["findings"])
            self.assertIn("traceable_material", messages)
            self.assertIn("draft_artifact", messages)
            self.assertIn("report_backed_validations", messages)

    def test_valid_fixture_reaches_stage_close_and_validation_pass_requires_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / "case_state.json"
            material_path = case_root / "material.txt"
            draft_path = case_root / "draft.md"
            material_path.write_text("劳动合同与解除通知", encoding="utf-8")
            draft_path.write_text("# 仲裁申请书初稿", encoding="utf-8")
            self.initialize_confirmed_case(state_path)

            self.run_cli(
                INGEST_MATERIALS,
                "--state", str(state_path),
                "--source", str(material_path),
                "--original-or-copy", "copy",
            )
            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "pass",
                "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            material_id = state["materials"][0]["material_id"]
            fact_input = case_root / "facts.json"
            fact_input.write_text(json.dumps({"facts": [{
                "fact_id": "fact-1",
                "statement": "解除通知记载用人单位解除劳动合同。",
                "status": "supported",
                "sources": [material_id],
            }]}, ensure_ascii=False), encoding="utf-8")
            self.run_cli(BUILD_TIMELINE, "--state", str(state_path), "--input", str(fact_input))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["issues"] = [{
                "issue_id": "issue-1",
                "issue": "用人单位解除劳动合同是否合法",
                "issue_type": "claim",
                "analysis_status": "reviewed",
                "representation": "employee",
                "our_position": {
                    "position": "我方主张用人单位解除劳动合同缺乏合法依据。",
                    "elements": [{
                        "element_id": "element-1",
                        "description": "用人单位已作出解除劳动合同的意思表示",
                        "status": "supported",
                        "fact_ids": ["fact-1"],
                        "evidence_ids": ["evidence-1"],
                        "rule_ids": ["rule-1"],
                        "gaps": [],
                    }],
                    "conclusion": "当前材料可以证明解除事实，解除理由仍需继续审查。",
                },
                "opponent_position": {
                    "strongest_argument": "用人单位可能主张劳动者存在严重违纪且解除程序已完成。",
                    "fact_ids": [],
                    "evidence_ids": [],
                    "rule_ids": [],
                    "response": "需要核对规章制度、违纪事实、送达和工会程序材料。",
                    "uncertainties": ["用人单位尚未提交完整解除依据"],
                },
                "alternative_paths": [],
                "no_alternative_reason": "当前测试只验证主请求路径，不设其他备选请求。",
                "failure_consequence": "若用人单位证明解除事由与程序均合法，赔偿金请求可能不获支持。",
            }]
            state["evidence"] = [self.structured_evidence(material_id)]
            state["rules"] = [self.structured_authority(state)]
            state["claims"] = [{
                "claim_id": "claim-1",
                "name": "确认用人单位违法解除劳动合同",
                "claim_type": "non_monetary",
                "analysis_status": "reviewed",
                "calculation_status": None,
                "amount": None,
                "currency": None,
                "calculation_id": None,
                "issue_ids": ["issue-1"],
                "rule_ids": ["rule-1"],
                "pending_inputs": [],
                "risk": "本测试只验证工作流门禁，不评价实体请求能否获得支持。",
                "alternative": False,
            }]
            state["procedural_assessments"] = [self.structured_procedure(state)]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            for expected_node in ("issue_analysis", "evidence_analysis", "authority_research", "claims_procedure"):
                self.run_cli(
                    WORKFLOW,
                    "transition",
                    "--state", str(state_path),
                    "--event", "pass",
                    "--actor", "test",
                )
                state = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertEqual(state["current_node"], expected_node)

            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "pass",
                "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_node"], "strategy_approval")

            for gate, scopes in (
                (
                    "strategy_approval",
                    ["representation", "stage", "requested_document", "provisional_strategy"],
                ),
            ):
                arguments = [
                    "approve", "--state", str(state_path), "--gate", gate,
                    "--status", "approved", "--approved-by", "user",
                ]
                for scope in scopes:
                    arguments.extend(["--scope", scope])
                self.run_cli(WORKFLOW, *arguments)
            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "approved",
                "--actor", "test",
            )

            self.run_cli(
                WORKFLOW,
                "register-artifact",
                "--state", str(state_path),
                "--path", str(draft_path),
                "--kind", "legal_draft",
                "--version", "v1",
                "--delivery-status", "lawyer_review_draft",
                "--generator", "test-fixture",
                "--source-ref", "facts:fact-1",
                "--created-by", "test",
                "--artifact-id", "draft-1",
            )
            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "pass",
                "--actor", "test",
                "--output-artifact", "draft-1",
            )

            missing_report = self.run_cli(
                WORKFLOW,
                "record-validation",
                "--state", str(state_path),
                "--kind", "deterministic",
                "--validator", "test",
                "--status", "pass",
                expected=2,
            )
            self.assertIn("必须提供", missing_report.stderr)

            missing_escalation_reports = self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "escalate",
                "--actor", "test",
                expected=2,
            )
            self.assertIn("report_backed_validations", missing_escalation_reports.stderr)

            incomplete_report_path = case_root / "missing-status.json"
            incomplete_report_path.write_text(
                json.dumps({"findings": []}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            incomplete_report = self.run_cli(
                WORKFLOW,
                "record-validation",
                "--state", str(state_path),
                "--kind", "deterministic",
                "--validator", "test",
                "--status", "pass",
                "--report", str(incomplete_report_path),
                expected=2,
            )
            self.assertIn("status 和 findings", incomplete_report.stderr)

            deterministic_report = case_root / "deterministic.json"
            deterministic_report.write_text(
                json.dumps({"status": "pass", "findings": []}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            deterministic_record = json.loads(self.run_cli(
                WORKFLOW,
                "record-validation",
                "--state", str(state_path),
                "--kind", "deterministic",
                "--validator", "test",
                "--report", str(deterministic_report),
                "--artifact-id", "draft-1",
            ).stdout)
            adversarial_report = case_root / "adversarial.json"
            self.run_cli(
                ADVERSARIAL_VALIDATE,
                "--state", str(state_path),
                "--output", str(adversarial_report),
            )
            adversarial_record = json.loads(self.run_cli(
                WORKFLOW,
                "record-validation",
                "--state", str(state_path),
                "--kind", "adversarial",
                "--validator", "laborpilot-adversarial-validator",
                "--report", str(adversarial_report),
                "--artifact-id", "draft-1",
            ).stdout)
            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "pass",
                "--actor", "test",
            )

            arguments = [
                "approve", "--state", str(state_path), "--gate", "lawyer_approval",
                "--status", "approved", "--approved-by", "user",
            ]
            for scope in ("validated_draft", "residual_risks", "submission_decision"):
                arguments.extend(["--scope", scope])
            arguments.extend(["--artifact-id", "draft-1"])
            arguments.extend(["--validation-id", deterministic_record["validation_id"]])
            arguments.extend(["--validation-id", adversarial_record["validation_id"]])
            self.run_cli(WORKFLOW, *arguments)
            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "approved",
                "--actor", "test",
            )

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_node"], "stage_close")
            validation = self.run_cli(VALIDATE, "--state", str(state_path))
            self.assertEqual(json.loads(validation.stdout)["status"], "pass")

    def test_report_backed_validation_escalation_reaches_lawyer_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / "case_state.json"
            draft_path = case_root / "draft.md"
            material_path = case_root / "material.txt"
            draft_path.write_text("# 律师复核初稿", encoding="utf-8")
            material_path.write_text("2025年6月15日解除劳动合同。", encoding="utf-8")
            self.initialize_confirmed_case(state_path)

            self.run_cli(INGEST_MATERIALS, "--state", str(state_path), "--source", str(material_path))
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            material_id = state["materials"][0]["material_id"]
            fact_input = case_root / "facts.json"
            fact_input.write_text(json.dumps({"facts": [{
                "fact_id": "fact-1", "statement": "材料记载解除劳动合同。",
                "status": "supported", "sources": [material_id],
            }]}, ensure_ascii=False), encoding="utf-8")
            self.run_cli(BUILD_TIMELINE, "--state", str(state_path), "--input", str(fact_input))

            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_node"] = "validation"
            state["issues"] = [{
                "issue_id": "issue-1",
                "issue": "用人单位解除劳动合同是否合法",
                "issue_type": "claim",
                "analysis_status": "reviewed",
                "representation": "employee",
                "our_position": {
                    "position": "我方主张用人单位已解除劳动合同且应证明解除合法性。",
                    "elements": [{
                        "element_id": "element-1",
                        "description": "用人单位已作出解除劳动合同的意思表示",
                        "status": "supported",
                        "fact_ids": ["fact-1"],
                        "evidence_ids": ["evidence-1"],
                        "rule_ids": ["rule-1"],
                        "gaps": [],
                    }],
                    "conclusion": "解除事实已有材料支持，解除合法性仍待核对。",
                },
                "opponent_position": {
                    "strongest_argument": "用人单位可能主张劳动者严重违纪且解除程序合法。",
                    "fact_ids": [],
                    "evidence_ids": [],
                    "rule_ids": [],
                    "response": "应核对违纪事实、规章制度效力与解除程序材料。",
                    "uncertainties": ["对方尚未提交具体解除依据"],
                },
                "alternative_paths": [],
                "no_alternative_reason": "本测试只验证验证报告升级路径，不展开备选请求。",
                "failure_consequence": "若对方证明解除事由与程序均合法，赔偿金请求可能失败。",
            }]
            state["evidence"] = [self.structured_evidence(material_id)]
            state["rules"] = [self.structured_authority(state)]
            state["claims"] = [{
                "claim_id": "claim-1",
                "name": "确认用人单位违法解除劳动合同",
                "claim_type": "non_monetary",
                "analysis_status": "reviewed",
                "calculation_status": None,
                "issue_ids": ["issue-1"],
                "rule_ids": ["rule-1"],
                "amount": None,
                "currency": None,
                "calculation_id": None,
                "pending_inputs": [],
                "risk": "本测试只验证验证报告升级路径，不评价实体请求能否获得支持。",
                "alternative": False,
            }]
            state["procedural_assessments"] = [self.structured_procedure(state)]
            state["approvals"] = [{
                "approval_id": "approval-strategy", "gate": "strategy_approval",
                "status": "approved", "approved_by": "user",
            }]
            state["artifacts"] = [{
                "artifact_id": "draft-1", "kind": "legal_draft",
                "delivery_status": "lawyer_review_draft", "path": str(draft_path),
                "version": "v1", "generator": "test-fixture", "producer_version": VERSION,
                "created_by": "test", "created_at": "2026-08-24T10:00:00+08:00",
                "sha256": hashlib.sha256(draft_path.read_bytes()).hexdigest(),
                "derived_from": [],
                "source_refs": [{
                    "collection": "facts", "record_id": "fact-1",
                    "sha256": self.canonical_digest(state["facts"][0]),
                }],
            }]
            for node in (
                "intake", "issue_analysis", "evidence_analysis",
                "authority_research", "claims_procedure", "drafting",
            ):
                state["node_runs"].append({
                    "run_id": f"run-{node}", "node": node, "status": "passed",
                    "output_artifact_ids": ["draft-1"] if node == "drafting" else [],
                })
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            deterministic_report = case_root / "deterministic.json"
            deterministic_report.write_text(
                json.dumps({"status": "escalate", "findings": []}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.run_cli(
                WORKFLOW,
                "record-validation",
                "--state", str(state_path),
                "--kind", "deterministic",
                "--validator", "test",
                "--report", str(deterministic_report),
                "--artifact-id", "draft-1",
            )
            adversarial_report = case_root / "adversarial.json"
            self.run_cli(
                ADVERSARIAL_VALIDATE,
                "--state", str(state_path),
                "--output", str(adversarial_report),
            )
            self.run_cli(
                WORKFLOW,
                "record-validation",
                "--state", str(state_path),
                "--kind", "adversarial",
                "--validator", "laborpilot-adversarial-validator",
                "--report", str(adversarial_report),
                "--artifact-id", "draft-1",
            )

            self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "escalate",
                "--actor", "test",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_node"], "lawyer_approval")
            route = self.run_cli(WORKFLOW, "route", "--state", str(state_path))
            self.assertEqual(json.loads(route.stdout)["status"], "ready")

            missing_approval = self.run_cli(
                WORKFLOW,
                "transition",
                "--state", str(state_path),
                "--event", "approved",
                "--actor", "test",
                expected=2,
            )
            self.assertIn("lawyer_approval", missing_approval.stderr)


if __name__ == "__main__":
    unittest.main()
