"""专业金额计算器、参数包和金额门禁的业务行为回归。"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from claims_engine import calculate_formula  # noqa: E402


CASE_STATE = SCRIPTS / "case_state.py"
WORKFLOW = SCRIPTS / "workflow_graph.py"
VALIDATE = SCRIPTS / "validate_case.py"
CALCULATE = SCRIPTS / "calculate_claims.py"
PROCEDURE = SCRIPTS / "analyze_procedure.py"


class ClaimsExecutorTest(unittest.TestCase):
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

    def valid_issue(self) -> dict:
        return {
            "issue_id": "issue-compensation",
            "issue": "用人单位解除劳动合同是否应支付补偿或赔偿",
            "issue_type": "claim",
            "analysis_status": "reviewed",
            "representation": "employee",
            "our_position": {
                "position": "我方主张应根据解除性质、工资基数和工作年限确定补偿或赔偿金额。",
                "elements": [{
                    "element_id": "element-compensation",
                    "description": "解除性质及补偿工资基数、计发年限均已确定",
                    "status": "to_verify",
                    "fact_ids": [],
                    "evidence_ids": ["evidence-compensation-gap"],
                    "rule_ids": ["rule-compensation"],
                    "gaps": ["本测试以经用户确认的数值口径作为金额输入"],
                }],
                "conclusion": "实体请求与数值口径经复核后方可形成确定金额。",
            },
            "opponent_position": {
                "strongest_argument": "用人单位可能对解除性质、工资基数或工作年限提出异议。",
                "fact_ids": [], "evidence_ids": [], "rule_ids": [],
                "response": "逐项保留数值来源、计算口径和备选金额供律师复核。",
                "uncertainties": ["实体请求能否获得支持不由金额脚本判断"],
            },
            "alternative_paths": [{
                "path": "违法解除赔偿金与经济补偿作为互斥或备选路径分别计算",
                "trigger": "解除性质经审查后发生变化",
                "consequence": "公式由2N切换为N或N＋1并重新计算",
            }],
            "failure_consequence": "解除性质、工资基数或工作年限未获支持时，金额请求可能相应减少或不获支持。",
        }

    def valid_evidence(self) -> dict:
        return {
            "evidence_id": "evidence-compensation-gap",
            "analysis_status": "reviewed",
            "issue_id": "issue-compensation",
            "element_ids": ["element-compensation"],
            "proposition": "解除性质、工资基数和计发年限均有足够材料支持",
            "orientation": "gap_only",
            "fact_ids": [],
            "burden": {
                "primary_party": "employee", "control_party": "both", "rule": "shared",
                "shifted_to": "both",
                "rationale": "双方分别对各自主张的工资、年限和解除性质提供材料。",
                "initial_showing": "劳动者先提交工资支付和劳动关系存续期间的初步材料。",
                "shift_condition": "完成初步举证后，用人单位对其掌握的工资台账和解除依据举证。",
                "adverse_consequence": "不能证明相应数值或解除性质的一方承担金额主张不被采纳的风险。",
            },
            "items": [{
                "evidence_item_id": "item-compensation-inputs",
                "name": "工资基数与工作年限材料",
                "status": "missing", "material_ids": [],
                "purpose": "证明补偿或赔偿的工资基数和计发月数。",
                "authenticity_status": "not_applicable", "source_locator": None,
            }],
            "assessment": {
                "status": "insufficient",
                "reasoning": "本测试仅验证经用户确认的金额输入，未提供真实案件材料。",
                "gaps": ["缺少真实工资和工作年限材料"],
                "actions": ["真实案件中应补充工资流水、工资台账和劳动关系起止材料"],
            },
        }

    def valid_rule(self) -> dict:
        text = "测试规则全文：补偿或赔偿金额应依据经核实的工资基数、计发年限和解除性质计算。"
        return {
            "rule_id": "rule-compensation", "analysis_status": "reviewed",
            "issue_id": "issue-compensation", "element_ids": ["element-compensation"],
            "proposition": "补偿或赔偿应以经核实的工资基数和计发年限计算",
            "orientation": "supports_our_position", "adoption_status": "adopted",
            "document_id": "document-compensation", "document_title": "测试用金额计算规则",
            "document_number": "测试文号〔2026〕2号", "issuing_authority": "测试用规则制定机关",
            "authority_level": "law", "article_id": "article-compensation-1", "article_number": "第一条",
            "article_text": text, "article_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "verification_status": "verified", "validity_status": "effective",
            "effective_from": "2020-01-01", "effective_to": None,
            "territory_scope": "national", "applicable_jurisdictions": ["全国"],
            "case_jurisdiction": "浙江省", "analysis_date": "2026-08-24",
            "relevant_date": "2025-06-15",
            "temporal_basis": "以解除劳动合同发生日期作为金额实体规则的相关日期。",
            "applicability_status": "applicable",
            "applicability_reasoning": "测试规则在解除日期已经生效且全国适用范围覆盖本案。",
            "source_type": "official", "source_name": "测试用官方来源",
            "source_url": "https://example.invalid/official/compensation-rule",
            "retrieved_at": "2026-08-24T10:00:00+08:00", "warning": None,
            "created_by": "test", "created_at": "2026-08-24T10:00:00+08:00",
        }

    def prepare_claims_node(self, case_root: Path) -> Path:
        state_path = case_root / ".casework" / "case_state.json"
        self.run_cli(CASE_STATE, "init", "--output", str(state_path), "--analysis-date", "2026-08-24")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({
            "representation": "employee", "stage": "arbitration", "jurisdiction": "浙江省",
            "current_node": "claims_procedure", "pending_nodes": [],
            "task_context": {
                "user_request": "核算解除劳动合同补偿或赔偿金额",
                "requested_outputs": ["金额计算台账"], "constraints": [],
                "confirmed_by": "user", "confirmed_at": "2026-08-24T10:00:00+08:00",
            },
            "issues": [self.valid_issue()], "evidence": [self.valid_evidence()],
            "rules": [self.valid_rule()],
            "decisions": [
                {
                    "decision_id": "decision-monthly-wage", "decision": "本测试月工资基数采用10000元。",
                    "confirmed_on": "2026-08-24", "confirmed_by": "user",
                },
                {
                    "decision_id": "decision-service-months", "decision": "本测试补偿计发月数采用3.5个月。",
                    "confirmed_on": "2026-08-24", "confirmed_by": "user",
                },
                {
                    "decision_id": "decision-cap", "decision": "本测试确认三倍社平工资封顶不适用。",
                    "confirmed_on": "2026-08-24", "confirmed_by": "user",
                },
                {
                    "decision_id": "decision-overtime-hours", "decision": "本测试平日加班时长采用10小时。",
                    "confirmed_on": "2026-08-24", "confirmed_by": "user",
                },
            ],
            "node_requirement_waivers": [
                {
                    "waiver_id": "waiver-material", "node": "material_ingestion",
                    "requirement_id": "traceable_material", "status": "approved",
                    "reason": "用户确认本轮只验证金额公式，不提供真实案件材料。",
                    "confirmed_by": "user", "confirmed_at": "2026-08-24T10:00:00+08:00",
                },
                {
                    "waiver_id": "waiver-fact", "node": "intake",
                    "requirement_id": "structured_fact", "status": "approved",
                    "reason": "用户确认本轮以已确认数值测试金额公式，不建立事实时间轴。",
                    "confirmed_by": "user", "confirmed_at": "2026-08-24T10:00:00+08:00",
                },
            ],
        })
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return state_path

    def calculation_input(self, *, formula_type: str = "unlawful_termination_compensation") -> dict:
        return {
            "calculation_id": "calc-main", "claim_id": "claim-main",
            "name": "违法解除劳动合同赔偿金", "formula_type": formula_type,
            "issue_ids": ["issue-compensation"], "rule_ids": ["rule-compensation"],
            "relevant_date": "2025-06-15",
            "inputs": {
                "monthly_wage": {"value": "10000", "source_ids": ["decision-monthly-wage"]},
                "compensation_months": {"value": "3.5", "source_ids": ["decision-service-months"]},
                "cap_applies": {"value": "0", "source_ids": ["decision-cap"]},
            },
            "parameter_refs": {},
            "assumptions": ["本测试已经确认工资基数和补偿计发月数，仅验证算术与追溯。"],
            "pending_inputs": [],
            "risk": "解除性质、工资基数或计发月数变化时必须重新计算。",
            "alternative": False,
        }

    def procedure_input(self, *, status: str = "reviewed") -> dict:
        pending_items = [] if status == "reviewed" else ["需继续核对仲裁时效是否发生中断。"]
        return {
            "schema_version": "1.0",
            "procedural_assessments": [{
                "assessment_id": "procedure-compensation",
                "issue_id": "issue-compensation",
                "claim_ids": ["claim-main"],
                "analysis_status": status,
                "case_jurisdiction": "浙江省",
                "analysis_date": "2026-08-24",
                "limitation": {
                    "status": "in_time",
                    "trigger_date": "2026-01-01",
                    "deadline_date": "2027-01-01",
                    "basis_rule_ids": ["rule-compensation"],
                    "analysis": "以已核对的请求权起算日为基础，至分析日尚未超过仲裁时效。",
                },
                "jurisdiction": {
                    "status": "proper",
                    "forum": "浙江省某劳动人事争议仲裁委员会",
                    "case_jurisdiction": "浙江省",
                    "basis_rule_ids": ["rule-compensation"],
                    "analysis": "根据已核对的劳动合同履行地和案件管辖地确定当前仲裁委员会有管辖权。",
                },
                "final_award": {
                    "status": "not_applicable",
                    "basis_rule_ids": [],
                    "analysis": "本测试请求不符合已核对的一裁终局适用条件。",
                },
                "interim_relief": {
                    "status": "not_applicable",
                    "basis_rule_ids": [],
                    "analysis": "当前已确认事实不满足先予执行或其他临时救济条件。",
                },
                "remedy_paths": ["仲裁裁决作出后，按裁决类型在法定期限内起诉或申请执行。"],
                "pending_items": pending_items,
                "risk": "时效中断、实际履行地或请求金额发生变化时，程序结论必须重新复核。",
            }],
        }

    def write_input(self, path: Path, calculations: list[dict]) -> None:
        path.write_text(json.dumps({"calculations": calculations}, ensure_ascii=False), encoding="utf-8")

    def test_professional_formula_results(self):
        numeric = lambda value: {"value": str(value), "source_ids": ["source"]}
        cap_parameters = {"monthly_wage_cap": {"value": "15000"}}
        overtime_parameters = {
            "monthly_paid_days": {"value": "21.75"}, "daily_hours": {"value": "8"},
        }
        injury_parameters = {"benefit_unit_amount": {"value": "5000"}}
        cases = [
            ("economic_compensation", {
                "monthly_wage": numeric(20000), "compensation_months": numeric(4), "cap_applies": numeric(1),
            }, cap_parameters, "60000"),
            ("n_plus_one", {
                "monthly_wage": numeric(10000), "compensation_months": numeric(3.5),
                "notice_pay_base": numeric(10000), "notice_months": numeric(1), "cap_applies": numeric(0),
            }, {}, "45000.0"),
            ("unlawful_termination_compensation", {
                "monthly_wage": numeric(10000), "compensation_months": numeric(3.5), "cap_applies": numeric(0),
            }, {}, "70000.0"),
            ("overtime_workday", {"monthly_wage": numeric(21750), "overtime_hours": numeric(10)}, overtime_parameters, "1875.0"),
            ("overtime_rest_day", {"monthly_wage": numeric(21750), "overtime_hours": numeric(10)}, overtime_parameters, "2500"),
            ("overtime_statutory_holiday", {"monthly_wage": numeric(21750), "overtime_hours": numeric(10)}, overtime_parameters, "3750"),
            ("work_injury_lump_sum_disability", {"monthly_wage": numeric(6000), "benefit_months": numeric(7)}, {}, "42000"),
            ("work_injury_disability_allowance", {
                "monthly_wage": numeric(6000), "allowance_rate": numeric("0.6"), "payment_months": numeric(12),
            }, {}, "43200.0"),
            ("work_injury_regional_benefit", {"benefit_units": numeric(6)}, injury_parameters, "30000"),
            ("non_compete_compensation", {
                "monthly_compensation": numeric(3000), "payment_months": numeric(6),
            }, {}, "18000"),
        ]
        for formula, inputs, resolved, expected in cases:
            with self.subTest(formula=formula):
                raw, expression, steps = calculate_formula(formula, inputs, resolved)
                self.assertEqual(raw, Decimal(expected))
                self.assertTrue(expression)
                self.assertTrue(steps)
        raw, _, _ = calculate_formula(
            "work_injury_three_lump_sums", {"component_ids": ["a", "b", "c"]}, {},
            {"a": Decimal("42000"), "b": Decimal("30000"), "c": Decimal("18000")},
        )
        self.assertEqual(raw, Decimal("90000"))

    def test_stateful_calculation_is_traceable_and_unlocks_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            input_path = case_root / "calculation.json"
            self.write_input(input_path, [self.calculation_input()])
            result = json.loads(self.run_cli(
                CALCULATE, "--state", str(state_path), "--input", str(input_path),
            ).stdout)
            self.assertEqual(result["calculated_count"], 1)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            calculation = state["calculations"][0]
            claim = state["claims"][0]
            self.assertEqual(calculation["amount"], "70000.00")
            self.assertEqual(claim["amount"], "70000.00")
            self.assertEqual(claim["calculation_id"], calculation["calculation_id"])
            self.assertEqual(
                calculation["input_source_ids"],
                ["decision-monthly-wage", "decision-service-months", "decision-cap"],
            )
            self.assertEqual(len(calculation["calculation_digest"]), 64)
            ledger = Path(result["ledger"])
            self.assertTrue(ledger.is_file())
            artifact = next(item for item in state["artifacts"] if item["kind"] == "calculation_ledger")
            self.assertEqual(artifact["sha256"], hashlib.sha256(ledger.read_bytes()).hexdigest())
            procedure_path = case_root / "procedure.json"
            procedure_path.write_text(
                json.dumps(self.procedure_input(), ensure_ascii=False), encoding="utf-8"
            )
            self.run_cli(
                PROCEDURE, "--state", str(state_path), "--input", str(procedure_path),
            )
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test",
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["current_node"], "strategy_approval"
            )

    def test_official_parameter_package_is_resolved_by_date_and_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            item = self.calculation_input(formula_type="overtime_workday")
            item.update(name="平日延时加班工资")
            item["inputs"] = {
                "monthly_wage": {"value": "21750", "source_ids": ["decision-monthly-wage"]},
                "overtime_hours": {"value": "10", "source_ids": ["decision-overtime-hours"]},
            }
            item["parameter_refs"] = {
                "monthly_paid_days": {
                    "package_id": "cn-wage-conversion-2025", "parameter_key": "monthly_paid_days",
                },
                "daily_hours": {
                    "package_id": "cn-wage-conversion-2025", "parameter_key": "daily_hours",
                },
            }
            input_path = case_root / "overtime.json"
            self.write_input(input_path, [item])
            self.run_cli(CALCULATE, "--state", str(state_path), "--input", str(input_path))
            calculation = json.loads(state_path.read_text(encoding="utf-8"))["calculations"][0]
            self.assertEqual(calculation["amount"], "1875.00")
            paid_days = calculation["resolved_parameters"]["monthly_paid_days"]
            self.assertEqual(paid_days["package_version"], "2025.1")
            self.assertEqual(paid_days["source"]["document_number"], "人社部发〔2025〕2号")
            self.assertEqual(len(paid_days["package_sha256"]), 64)

    def test_external_social_average_wage_package_applies_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["decisions"][0]["decision"] = "本测试月工资基数采用20000元。"
            state["decisions"][1]["decision"] = "本测试补偿计发月数采用4个月。"
            state["decisions"][2]["decision"] = "本测试确认三倍社平工资封顶适用。"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            package_path = case_root / "social-average-wage-package.json"
            package_path.write_text(json.dumps({
                "schema_version": "1.0", "package_id": "test-social-average-wage-2025",
                "version": "2025.1", "jurisdiction_scope": "national",
                "applicable_jurisdictions": ["中华人民共和国境内"],
                "effective_from": "2025-01-01", "effective_to": None,
                "published_at": "2025-06-01",
                "source": {
                    "title": "测试用年度社会平均工资参数通知", "issuer": "测试用官方机关",
                    "document_number": "测试参数〔2025〕1号",
                    "url": "https://example.invalid/official/social-average-wage",
                    "retrieved_at": "2026-08-24T10:00:00+08:00",
                },
                "values": {
                    "monthly_average_wage_cap": {
                        "value": "15000", "unit": "CNY/month",
                        "effective_from": "2025-01-01", "effective_to": None,
                        "source_locator": "第一条三倍社平工资封顶数值",
                    }
                },
            }, ensure_ascii=False), encoding="utf-8")
            item = self.calculation_input(formula_type="economic_compensation")
            item["name"] = "经济补偿金"
            item["inputs"]["monthly_wage"]["value"] = "20000"
            item["inputs"]["compensation_months"]["value"] = "4"
            item["inputs"]["cap_applies"]["value"] = "1"
            item["parameter_refs"] = {
                "monthly_wage_cap": {
                    "package_id": "test-social-average-wage-2025",
                    "parameter_key": "monthly_average_wage_cap",
                }
            }
            input_path = case_root / "capped-compensation.json"
            self.write_input(input_path, [item])
            self.run_cli(
                CALCULATE, "--state", str(state_path), "--input", str(input_path),
                "--parameter-package", str(package_path),
            )
            calculation = json.loads(state_path.read_text(encoding="utf-8"))["calculations"][0]
            self.assertEqual(calculation["amount"], "60000.00")
            self.assertEqual(
                calculation["resolved_parameters"]["monthly_wage_cap"]["parameter_key"],
                "monthly_average_wage_cap",
            )

    def test_pending_inputs_never_produce_final_amount_or_unlock_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            item = self.calculation_input()
            item["inputs"].pop("monthly_wage")
            item["pending_inputs"] = ["尚未核对补偿或赔偿工资基数"]
            input_path = case_root / "pending.json"
            self.write_input(input_path, [item])
            result = json.loads(self.run_cli(
                CALCULATE, "--state", str(state_path), "--input", str(input_path),
            ).stdout)
            self.assertEqual(result["needs_confirmation_count"], 1)
            calculation = json.loads(state_path.read_text(encoding="utf-8"))["calculations"][0]
            self.assertIsNone(calculation["amount"])
            self.assertIsNone(calculation["expression"])
            self.assertEqual(calculation["steps"], [])
            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test",
                expected=2,
            )
            self.assertIn("不得存在待确认输入", blocked.stderr)
            waiver = self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", "structured_claim", "--reason", "用户暂时无法确认工资基数。",
                "--confirmed-by", "user", expected=2,
            )
            self.assertIn("不允许豁免", waiver.stderr)
            report = json.loads(self.run_cli(VALIDATE, "--state", str(state_path), expected=1).stdout)
            self.assertTrue(any(item["code"] == "CALCULATION_PENDING" for item in report["findings"]))

    def test_invalid_parameter_date_and_tampered_amount_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            item = self.calculation_input(formula_type="overtime_workday")
            item["relevant_date"] = "2024-06-15"
            item["inputs"] = {
                "monthly_wage": {"value": "21750", "source_ids": ["decision-monthly-wage"]},
                "overtime_hours": {"value": "10", "source_ids": ["decision-overtime-hours"]},
            }
            item["parameter_refs"] = {
                "monthly_paid_days": {
                    "package_id": "cn-wage-conversion-2025", "parameter_key": "monthly_paid_days",
                },
                "daily_hours": {
                    "package_id": "cn-wage-conversion-2025", "parameter_key": "daily_hours",
                },
            }
            input_path = case_root / "invalid-date.json"
            self.write_input(input_path, [item])
            original = state_path.read_bytes()
            invalid = self.run_cli(
                CALCULATE, "--state", str(state_path), "--input", str(input_path), expected=2,
            )
            self.assertIn("不覆盖本案相关日期", invalid.stderr)
            self.assertEqual(state_path.read_bytes(), original)

            valid_path = case_root / "valid.json"
            self.write_input(valid_path, [self.calculation_input()])
            self.run_cli(CALCULATE, "--state", str(state_path), "--input", str(valid_path))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["calculations"][0]["amount"] = "999999.99"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = json.loads(self.run_cli(VALIDATE, "--state", str(state_path), expected=1).stdout)
            messages = "\n".join(item["message"] for item in report["findings"])
            self.assertIn("重新计算结果不一致", messages)
            self.assertTrue(any(item["code"] == "CALCULATION_LEDGER" for item in report["findings"]))

    def test_cap_decision_and_exact_input_contract_are_mandatory(self):
        cases = [
            (lambda item: item["inputs"].pop("cap_applies"), "缺少公式输入：cap_applies"),
            (lambda item: item["inputs"].update(typo_months={
                "value": "3.5", "source_ids": ["decision-service-months"],
            }), "存在公式未使用的输入：typo_months"),
        ]
        for mutate, expected_message in cases:
            with self.subTest(expected_message=expected_message), tempfile.TemporaryDirectory() as temporary:
                case_root = Path(temporary)
                state_path = self.prepare_claims_node(case_root)
                item = self.calculation_input()
                mutate(item)
                input_path = case_root / "invalid-contract.json"
                self.write_input(input_path, [item])
                result = self.run_cli(
                    CALCULATE, "--state", str(state_path), "--input", str(input_path), expected=2,
                )
                self.assertIn(expected_message, result.stderr)

    def test_reviewed_procedure_analysis_is_required_and_traceable(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            calculation_path = case_root / "calculation.json"
            self.write_input(calculation_path, [self.calculation_input()])
            self.run_cli(CALCULATE, "--state", str(state_path), "--input", str(calculation_path))

            missing = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("reviewed_procedure_path", missing.stderr)

            scaffold = json.loads(self.run_cli(
                PROCEDURE, "--state", str(state_path), "--scaffold",
            ).stdout)
            self.assertEqual(scaffold["status"], "to_review")
            self.assertTrue(Path(scaffold["output"]).is_file())
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["procedural_assessments"],
                [],
            )

            procedure_path = case_root / "procedure.json"
            procedure_path.write_text(
                json.dumps(self.procedure_input(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = json.loads(self.run_cli(
                PROCEDURE, "--state", str(state_path), "--input", str(procedure_path),
            ).stdout)
            self.assertEqual(result["status"], "reviewed")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            assessment = state["procedural_assessments"][0]
            self.assertEqual(assessment["limitation"]["status"], "in_time")
            self.assertEqual(assessment["jurisdiction"]["status"], "proper")
            self.assertRegex(assessment["procedure_digest"], r"^[a-f0-9]{64}$")
            self.assertTrue((case_root / ".casework" / "procedure" / "analysis.json").is_file())
            self.assertTrue((case_root / ".casework" / "procedure" / "analysis.md").is_file())

            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["current_node"],
                "strategy_approval",
            )

    def test_invalid_or_pending_procedure_analysis_cannot_unlock_node(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            calculation_path = case_root / "calculation.json"
            self.write_input(calculation_path, [self.calculation_input()])
            self.run_cli(CALCULATE, "--state", str(state_path), "--input", str(calculation_path))

            invalid_payload = self.procedure_input()
            invalid_payload["procedural_assessments"][0]["limitation"]["deadline_date"] = "2025-01-01"
            invalid_path = case_root / "invalid-procedure.json"
            invalid_path.write_text(json.dumps(invalid_payload, ensure_ascii=False), encoding="utf-8")
            original = state_path.read_bytes()
            invalid = self.run_cli(
                PROCEDURE, "--state", str(state_path), "--input", str(invalid_path), expected=2,
            )
            self.assertIn("标记 in_time 但截止日已早于分析日", invalid.stderr)
            self.assertEqual(state_path.read_bytes(), original)

            pending_path = case_root / "pending-procedure.json"
            pending_path.write_text(
                json.dumps(self.procedure_input(status="needs_confirmation"), ensure_ascii=False),
                encoding="utf-8",
            )
            pending = json.loads(self.run_cli(
                PROCEDURE, "--state", str(state_path), "--input", str(pending_path),
            ).stdout)
            self.assertEqual(pending["status"], "needs_confirmation")
            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("reviewed_procedure_path", blocked.stderr)
            waiver = self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", "reviewed_procedure_path",
                "--reason", "用户尚未确认程序信息。", "--confirmed-by", "user", expected=2,
            )
            self.assertIn("不允许豁免", waiver.stderr)
            report = json.loads(self.run_cli(VALIDATE, "--state", str(state_path), expected=1).stdout)
            self.assertTrue(any(item["code"] == "PROCEDURE_PENDING" for item in report["findings"]))

    def test_legacy_claim_requires_explicit_replacement_and_keeps_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_claims_node(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["claims"] = [{"claim_id": "legacy-placeholder", "amount": 1}]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            input_path = case_root / "replacement.json"
            self.write_input(input_path, [self.calculation_input()])
            blocked = self.run_cli(
                CALCULATE, "--state", str(state_path), "--input", str(input_path), expected=2,
            )
            self.assertIn("--replace-existing-calculations", blocked.stderr)
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["claims"][0]["claim_id"], "legacy-placeholder")
            self.run_cli(
                CALCULATE, "--state", str(state_path), "--input", str(input_path),
                "--replace-existing-calculations",
            )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            previous = json.loads(Path(state["previous_state"]).read_text(encoding="utf-8"))
            self.assertEqual(previous["claims"], [{"claim_id": "legacy-placeholder", "amount": 1}])
            self.assertEqual(state["claims"][0]["claim_id"], "claim-main")


if __name__ == "__main__":
    unittest.main()
