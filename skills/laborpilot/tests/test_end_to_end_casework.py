"""虚构案件从任务确认到律师审批的公开包端到端回归。"""

from __future__ import annotations

from copy import deepcopy
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
SCRIPTS = ROOT / "scripts"
CASE_STATE = SCRIPTS / "case_state.py"
WORKFLOW = SCRIPTS / "workflow_graph.py"
INGEST = SCRIPTS / "ingest_materials.py"
TIMELINE = SCRIPTS / "build_timeline.py"
ISSUES = SCRIPTS / "build_issue_matrix.py"
EVIDENCE = SCRIPTS / "build_evidence_chain.py"
AUTHORITIES = SCRIPTS / "build_authorities.py"
CALCULATE = SCRIPTS / "calculate_claims.py"
PROCEDURE = SCRIPTS / "analyze_procedure.py"
GENERATE_DOCS = SCRIPTS / "generate_docs.py"
DETERMINISTIC = SCRIPTS / "validate_case.py"
ADVERSARIAL = SCRIPTS / "adversarial_validation.py"


class EndToEndCaseworkTest(unittest.TestCase):
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

    @staticmethod
    def write_json(path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def transition(self, state_path: Path, event: str, *extra: str) -> None:
        self.run_cli(
            WORKFLOW, "transition", "--state", str(state_path),
            "--event", event, "--actor", "e2e-test", *extra,
        )

    def test_fictional_case_reaches_stage_close_with_real_docx_and_validations(self):
        self.assertIsNotNone(shutil.which("pandoc"), "端到端文书门禁需要安装 Pandoc。")
        from tests.test_authority_executor import AuthorityExecutorTest
        from tests.test_claims_executor import ClaimsExecutorTest
        from tests.test_evidence_chain_executor import EvidenceChainExecutorTest

        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            internal = case_root / ".casework"
            state_path = internal / "case_state.json"
            material_path = case_root / "虚构解除通知.txt"
            material_path.write_text(
                "本材料为自动测试虚构材料。2025年6月15日，测试用人单位向测试劳动者送达解除通知。",
                encoding="utf-8",
            )

            self.run_cli(
                CASE_STATE, "init", "--output", str(state_path),
                "--analysis-date", "2026-08-24", "--case-id", "case-public-e2e-fictional",
            )
            self.run_cli(
                CASE_STATE, "set-task", "--input", str(state_path),
                "--representation", "employee", "--stage", "arbitration",
                "--jurisdiction", "浙江省",
                "--user-request", "分析虚构违法解除争议并生成劳动仲裁申请书",
                "--requested-output", "劳动仲裁申请书", "--confirmed-by", "fictional-user",
            )
            self.transition(state_path, "pass")

            self.run_cli(
                INGEST, "--state", str(state_path), "--source", str(material_path),
                "--original-or-copy", "original",
            )
            self.transition(state_path, "pass")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            material_id = state["materials"][0]["material_id"]
            facts_path = case_root / "facts.json"
            self.write_json(facts_path, {"facts": [{
                "fact_id": "fact-dismissal-notice",
                "statement": "测试用人单位于2025年6月15日向测试劳动者送达解除通知。",
                "status": "supported",
                "sources": [material_id],
                "occurred_on": "2025-06-15",
                "source_locators": [{"material_id": material_id, "line": 1}],
            }]})
            self.run_cli(TIMELINE, "--state", str(state_path), "--input", str(facts_path))
            self.transition(state_path, "pass")

            evidence_helper = EvidenceChainExecutorTest()
            issues_path = case_root / "issues.json"
            self.write_json(issues_path, {"issues": [evidence_helper.valid_issue()]})
            self.run_cli(ISSUES, "--state", str(state_path), "--input", str(issues_path))
            self.transition(state_path, "pass")

            evidence_path = case_root / "evidence.json"
            self.write_json(evidence_path, {"evidence": evidence_helper.valid_chains(material_id)})
            self.run_cli(EVIDENCE, "--state", str(state_path), "--input", str(evidence_path))
            self.transition(state_path, "pass")

            authority_helper = AuthorityExecutorTest()
            state = json.loads(state_path.read_text(encoding="utf-8"))
            authority = deepcopy(authority_helper.valid_authority(state))
            authority.update({
                "issue_id": "issue-unlawful-dismissal",
                "element_ids": ["element-dismissal-act", "element-dismissal-ground"],
            })
            authority_path = case_root / "authorities.json"
            self.write_json(authority_path, {"rules": [authority]})
            self.run_cli(AUTHORITIES, "--state", str(state_path), "--input", str(authority_path))
            self.transition(state_path, "pass")

            for decision_id, decision in (
                ("decision-monthly-wage", "经虚构用户确认，月工资基数采用10000元。"),
                ("decision-service-months", "经虚构用户确认，赔偿金计发月数采用3.5个月。"),
                ("decision-cap", "经虚构用户确认，三倍社平工资封顶不适用。"),
            ):
                self.run_cli(
                    CASE_STATE, "record-decision", "--input", str(state_path),
                    "--decision-id", decision_id, "--decision", decision,
                    "--confirmed-on", "2026-08-24", "--confirmed-by", "fictional-user",
                )
            calculation_path = case_root / "calculation.json"
            self.write_json(calculation_path, {"calculations": [{
                "calculation_id": "calc-e2e-2n",
                "claim_id": "claim-e2e-2n",
                "name": "违法解除劳动合同赔偿金",
                "formula_type": "unlawful_termination_compensation",
                "issue_ids": ["issue-unlawful-dismissal"],
                "rule_ids": ["rule-dismissal-test"],
                "relevant_date": "2025-06-15",
                "inputs": {
                    "monthly_wage": {"value": "10000", "source_ids": ["decision-monthly-wage"]},
                    "compensation_months": {"value": "3.5", "source_ids": ["decision-service-months"]},
                    "cap_applies": {"value": "0", "source_ids": ["decision-cap"]},
                },
                "parameter_refs": {},
                "assumptions": ["本回归仅使用虚构且已经确认的工资基数和计发月数。"],
                "pending_inputs": [],
                "risk": "解除合法性获得支持时，违法解除赔偿金请求可能不获支持。",
                "alternative": False,
            }]})
            self.run_cli(CALCULATE, "--state", str(state_path), "--input", str(calculation_path))
            procedure_payload = ClaimsExecutorTest().procedure_input()
            procedure_record = procedure_payload["procedural_assessments"][0]
            procedure_record.update({
                "assessment_id": "procedure-e2e-dismissal",
                "issue_id": "issue-unlawful-dismissal",
                "claim_ids": ["claim-e2e-2n"],
            })
            for section_name in ("limitation", "jurisdiction"):
                procedure_record[section_name]["basis_rule_ids"] = ["rule-dismissal-test"]
            procedure_path = case_root / "procedure.json"
            self.write_json(procedure_path, procedure_payload)
            self.run_cli(PROCEDURE, "--state", str(state_path), "--input", str(procedure_path))
            self.transition(state_path, "pass")

            approve_strategy = [
                "approve", "--state", str(state_path), "--gate", "strategy_approval",
                "--status", "approved", "--approved-by", "fictional-lawyer",
            ]
            for scope in ("representation", "stage", "requested_document", "provisional_strategy"):
                approve_strategy.extend(["--scope", scope])
            self.run_cli(WORKFLOW, *approve_strategy)
            self.transition(state_path, "approved")

            drafting_input = case_root / "drafting-input.json"
            self.write_json(drafting_input, {
                "case": {
                    "申请人": "测试劳动者（虚构）", "性别": "女", "出生年月": "1990年1月1日",
                    "民族": "汉族", "户籍地址": "虚构地址", "身份证号": "【虚构信息】",
                    "电话": "【虚构信息】", "被申请人": "测试用人单位（虚构）",
                    "被申请人地址": "虚构地址", "案由": "违法解除劳动合同争议",
                    "仲裁委": "测试劳动人事争议仲裁委员会",
                    "事实与理由": "2025年6月15日，测试用人单位向测试劳动者送达解除通知。现有材料可以证明解除行为，解除事由和程序仍应由用人单位依法举证。",
                },
                "claims": [{
                    "事项": "违法解除劳动合同赔偿金", "金额": 70000.00,
                    "计算式": "10000元/月×3.5个月×2",
                }],
                "evidence": [], "actions": {},
            })
            drafting_work = internal / "drafting"
            self.run_cli(
                GENERATE_DOCS, "--case", str(drafting_input), "--output", str(case_root),
                "--work-dir", str(drafting_work), "--types", "仲裁申请书", "--strict",
            )
            stem = "02_劳动仲裁申请书_律师复核初稿_v1"
            docx_path = case_root / "01_律师复核初稿" / f"{stem}.docx"
            self.assertTrue(docx_path.is_file())
            self.assertFalse((case_root / f"{stem}.md").exists())
            self.assertTrue((drafting_work / f"{stem}.md").is_file())
            self.assertTrue((drafting_work / f"{stem}_版式验证.json").is_file())
            with zipfile.ZipFile(docx_path) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            self.assertIn("测试劳动者（虚构）", document_xml)
            self.assertIn("70,000.00", document_xml)

            source_refs = [
                f"materials:{material_id}",
                "facts:fact-dismissal-notice",
                "issues:issue-unlawful-dismissal",
                "evidence:evidence-dismissal-notice",
                "evidence:evidence-dismissal-ground-gap",
                "rules:rule-dismissal-test",
                "calculations:calc-e2e-2n",
                "claims:claim-e2e-2n",
                "decisions:decision-monthly-wage",
                "decisions:decision-service-months",
                "decisions:decision-cap",
            ]
            register_input = [
                "register-artifact", "--state", str(state_path),
                "--path", str(drafting_input), "--kind", "drafting_input", "--version", "1",
                "--delivery-status", "internal_work_product",
                "--generator", "tests/test_end_to_end_casework.py",
                "--created-by", "e2e-test", "--artifact-id", "artifact-drafting-input-e2e",
            ]
            for source_ref in source_refs:
                register_input.extend(["--source-ref", source_ref])
            self.run_cli(WORKFLOW, *register_input)

            register_draft = [
                "register-artifact", "--state", str(state_path),
                "--path", str(docx_path), "--kind", "arbitration_application", "--version", "1",
                "--delivery-status", "lawyer_review_draft", "--generator", "scripts/generate_docs.py",
                "--created-by", "e2e-test", "--artifact-id", "artifact-draft-e2e",
                "--derived-from", "artifact-drafting-input-e2e",
            ]
            for source_ref in source_refs:
                register_draft.extend(["--source-ref", source_ref])
            self.run_cli(
                WORKFLOW, *register_draft,
            )
            self.transition(state_path, "pass", "--output-artifact", "artifact-draft-e2e")

            validation_dir = internal / "validation"
            deterministic_path = validation_dir / "deterministic.json"
            self.run_cli(DETERMINISTIC, "--state", str(state_path), "--output", str(deterministic_path))
            deterministic_record = json.loads(self.run_cli(
                WORKFLOW, "record-validation", "--state", str(state_path),
                "--kind", "deterministic", "--validator", "laborpilot-deterministic-validator",
                "--report", str(deterministic_path), "--artifact-id", "artifact-draft-e2e",
            ).stdout)
            adversarial_path = validation_dir / "adversarial.json"
            self.run_cli(ADVERSARIAL, "--state", str(state_path), "--output", str(adversarial_path))
            adversarial_record = json.loads(self.run_cli(
                WORKFLOW, "record-validation", "--state", str(state_path),
                "--kind", "adversarial", "--validator", "laborpilot-adversarial-validator",
                "--report", str(adversarial_path), "--artifact-id", "artifact-draft-e2e",
            ).stdout)
            self.transition(state_path, "pass")

            approve_lawyer = [
                "approve", "--state", str(state_path), "--gate", "lawyer_approval",
                "--status", "approved", "--approved-by", "fictional-lawyer",
            ]
            for scope in ("validated_draft", "residual_risks", "submission_decision"):
                approve_lawyer.extend(["--scope", scope])
            missing_binding = self.run_cli(WORKFLOW, *approve_lawyer, expected=2)
            self.assertIn("正式产物", missing_binding.stderr)
            approve_lawyer.extend(["--artifact-id", "artifact-draft-e2e"])
            approve_lawyer.extend(["--validation-id", deterministic_record["validation_id"]])
            approve_lawyer.extend(["--validation-id", adversarial_record["validation_id"]])
            self.run_cli(WORKFLOW, *approve_lawyer)
            self.transition(state_path, "approved")

            final_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(final_state["current_node"], "stage_close")
            self.assertEqual(final_state["claims"][0]["amount"], "70000.00")
            self.assertEqual({item["kind"] for item in final_state["validations"]}, {"deterministic", "adversarial"})
            self.assertEqual({item["gate"] for item in final_state["approvals"]}, {"strategy_approval", "lawyer_approval"})
            draft = next(item for item in final_state["artifacts"] if item["artifact_id"] == "artifact-draft-e2e")
            self.assertEqual(draft["delivery_status"], "lawyer_review_draft")
            self.assertEqual(draft["producer_version"], VERSION)
            self.assertEqual(draft["generator"], "scripts/generate_docs.py")
            self.assertEqual(draft["sha256"], hashlib.sha256(docx_path.read_bytes()).hexdigest())
            self.assertEqual(draft["derived_from"], ["artifact-drafting-input-e2e"])
            self.assertEqual(len(draft["source_refs"]), len(source_refs))
            lawyer_approval = next(item for item in final_state["approvals"] if item["gate"] == "lawyer_approval")
            self.assertEqual(lawyer_approval["artifact_ids"], ["artifact-draft-e2e"])
            self.assertEqual(
                set(lawyer_approval["validation_ids"]),
                {deterministic_record["validation_id"], adversarial_record["validation_id"]},
            )
            completed_nodes = {item["node"] for item in final_state["node_runs"]}
            self.assertTrue({
                "task_intake", "material_ingestion", "intake", "issue_analysis",
                "evidence_analysis", "authority_research", "claims_procedure",
                "strategy_approval", "drafting", "validation", "lawyer_approval",
            }.issubset(completed_nodes))
            final_validation = json.loads(self.run_cli(DETERMINISTIC, "--state", str(state_path)).stdout)
            self.assertEqual(final_validation["status"], "pass")
            trace = json.loads(self.run_cli(
                WORKFLOW, "trace-artifact", "--state", str(state_path),
                "--artifact-id", "artifact-draft-e2e",
            ).stdout)
            self.assertEqual(trace["status"], "pass")
            self.assertEqual(trace["artifact_id"], "artifact-draft-e2e")
            self.assertEqual(
                set(trace["validation_ids"]),
                {deterministic_record["validation_id"], adversarial_record["validation_id"]},
            )
            self.assertEqual(trace["approval_id"], lawyer_approval["approval_id"])

            deterministic_original = deterministic_path.read_bytes()
            deterministic_path.write_text('{"status":"pass","findings":[{"tampered":true}]}\n', encoding="utf-8")
            changed_report = self.run_cli(
                WORKFLOW, "trace-artifact", "--state", str(state_path),
                "--artifact-id", "artifact-draft-e2e", expected=1,
            )
            changed_report_errors = "\n".join(json.loads(changed_report.stdout)["errors"])
            self.assertIn("报告当前无效", changed_report_errors)
            deterministic_path.write_bytes(deterministic_original)

            docx_path.write_bytes(docx_path.read_bytes() + b"tampered")
            tampered = self.run_cli(
                WORKFLOW, "trace-artifact", "--state", str(state_path),
                "--artifact-id", "artifact-draft-e2e", expected=1,
            )
            self.assertEqual(json.loads(tampered.stdout)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
