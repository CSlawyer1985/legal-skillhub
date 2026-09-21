"""法源核验结果适配器的业务行为回归。"""

from __future__ import annotations

from copy import deepcopy
import hashlib
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
BUILD_ISSUES = ROOT / "scripts" / "build_issue_matrix.py"
BUILD_EVIDENCE = ROOT / "scripts" / "build_evidence_chain.py"
BUILD_AUTHORITIES = ROOT / "scripts" / "build_authorities.py"


class AuthorityExecutorTest(unittest.TestCase):
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
            "issue_id": "issue-dismissal",
            "issue": "用人单位解除劳动合同是否合法",
            "issue_type": "claim",
            "analysis_status": "reviewed",
            "our_position": {
                "position": "我方主张用人单位应对解除事由和解除程序的合法性承担证明责任。",
                "elements": [
                    {
                        "element_id": "element-ground",
                        "description": "用人单位主张的解除事由具有法律和事实依据",
                        "status": "to_verify", "fact_ids": [], "evidence_ids": [], "rule_ids": [],
                        "gaps": ["尚未核对解除事由及所依据的法律规则"],
                    },
                    {
                        "element_id": "element-procedure",
                        "description": "用人单位解除劳动合同已履行必要的法定程序",
                        "status": "to_verify", "fact_ids": [], "evidence_ids": [], "rule_ids": [],
                        "gaps": ["尚未核对解除程序材料与适用的法律规则"],
                    },
                ],
                "conclusion": "解除事由和程序均须结合已核验法源与证据后再作判断。",
            },
            "opponent_position": {
                "strongest_argument": "用人单位可能主张解除事由符合法定情形且已履行全部程序。",
                "fact_ids": [], "evidence_ids": [], "rule_ids": [],
                "response": "应对照已核验的实体规则和程序规则逐项审查。",
                "uncertainties": ["尚未获取完整解除依据与程序材料"],
            },
            "alternative_paths": [{
                "path": "若解除合法，继续审查是否存在经济补偿请求",
                "trigger": "解除事由和程序经审查均符合适用规则",
                "consequence": "请求基础可能由违法解除赔偿转为经济补偿",
            }],
            "failure_consequence": "若对方完成解除事由和程序合法性的举证，赔偿请求可能不获支持。",
        }

    def gap_chain(self, element_id: str, evidence_id: str, orientation: str) -> dict:
        return {
            "evidence_id": evidence_id,
            "issue_id": "issue-dismissal",
            "element_ids": [element_id],
            "proposition": "当前尚无证据证明该解除构成要件已经实际满足",
            "orientation": orientation,
            "fact_ids": [],
            "burden": {
                "primary_party": "employer", "control_party": "employer", "rule": "general",
                "shifted_to": None,
                "rationale": "解除事由和程序材料由用人单位提出并掌握。",
                "initial_showing": "劳动者先对用人单位已作出解除表示提出具体主张。",
                "shift_condition": "劳动者完成解除事实的初步说明后由用人单位举证。",
                "adverse_consequence": "用人单位不能提交解除依据时可能承担相应不利后果。",
            },
            "items": [{
                "evidence_item_id": f"item-{element_id}",
                "name": "解除事由及程序材料",
                "status": "missing", "material_ids": [],
                "purpose": "证明用人单位主张的解除事由和必要程序均已成立。",
                "authenticity_status": "not_applicable", "source_locator": None,
            }],
            "assessment": {
                "status": "insufficient", "reasoning": "当前没有可供核对的解除依据与程序材料。",
                "gaps": ["缺少解除事由和程序材料"],
                "actions": ["要求用人单位提交完整解除依据和程序记录"],
            },
        }

    def valid_authority(self, state: dict) -> dict:
        article_text = "测试规则全文：用人单位解除劳动合同时，应当依法证明解除事由成立并履行必要程序。"
        return {
            "rule_id": "rule-dismissal-test",
            "issue_id": "issue-dismissal",
            "element_ids": ["element-ground", "element-procedure"],
            "proposition": "用人单位应对解除事由成立与解除程序合法承担证明责任",
            "orientation": "cuts_both_ways", "adoption_status": "adopted",
            "document_id": "document-dismissal-test", "document_title": "测试用劳动合同规则",
            "document_number": "测试文号〔2026〕1号", "issuing_authority": "测试用规则制定机关",
            "authority_level": "law", "article_id": "article-dismissal-test-1", "article_number": "第一条",
            "article_text": article_text,
            "verification_status": "verified", "validity_status": "effective",
            "effective_from": "2020-01-01", "effective_to": None,
            "territory_scope": "national", "applicable_jurisdictions": ["全国"],
            "relevant_date": "2025-06-15",
            "temporal_basis": "以用人单位作出解除决定的日期作为实体规则适用日期。",
            "applicability_status": "applicable",
            "applicability_reasoning": "该测试规则在解除日期已生效，且全国适用范围覆盖本案管辖地。",
            "source_type": "official", "source_name": "测试用官方来源",
            "source_url": "https://example.invalid/official/test-rule",
            "retrieved_at": "2026-08-24T10:00:00+08:00", "warning": None,
        }

    def prepare_authority_node(self, case_root: Path) -> Path:
        state_path = case_root / ".casework" / "case_state.json"
        self.run_cli(CASE_STATE, "init", "--output", str(state_path), "--analysis-date", "2026-08-24")
        self.run_cli(
            CASE_STATE, "set-task", "--input", str(state_path),
            "--representation", "employee", "--stage", "arbitration", "--jurisdiction", "浙江省",
            "--user-request", "核验违法解除争点的法源适用性",
            "--requested-output", "案件研判报告", "--confirmed-by", "user",
        )
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        for requirement, reason in (
            ("traceable_material", "用户确认本轮只完成法源适用性核验，不提供案件文件。"),
            ("structured_fact", "用户确认本轮只完成法源适用性核验，不建立事实时间轴。"),
        ):
            self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", requirement, "--reason", reason, "--confirmed-by", "user",
            )
            self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")

        issue_path = case_root / "issues.json"
        issue_path.write_text(json.dumps({"issues": [self.valid_issue()]}, ensure_ascii=False), encoding="utf-8")
        self.run_cli(BUILD_ISSUES, "--state", str(state_path), "--input", str(issue_path))
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        evidence_path = case_root / "evidence.json"
        evidence_path.write_text(json.dumps({"evidence": [
            self.gap_chain("element-ground", "evidence-ground-gap", "supports_opponent_position"),
            self.gap_chain("element-procedure", "evidence-procedure-gap", "gap_only"),
        ]}, ensure_ascii=False), encoding="utf-8")
        self.run_cli(BUILD_EVIDENCE, "--state", str(state_path), "--input", str(evidence_path))
        self.run_cli(WORKFLOW, "transition", "--state", str(state_path), "--event", "pass", "--actor", "test")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["current_node"], "authority_research")
        return state_path

    def write_authorities(self, path: Path, records: list[dict]) -> None:
        path.write_text(json.dumps({"rules": records}, ensure_ascii=False), encoding="utf-8")

    def test_scaffold_is_review_only_and_authority_cannot_be_waived(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_authority_node(case_root)
            result = json.loads(self.run_cli(
                BUILD_AUTHORITIES, "--state", str(state_path), "--scaffold",
            ).stdout)
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(result["candidate_count"], 2)
            scaffold = json.loads(Path(result["scaffold"]).read_text(encoding="utf-8"))
            self.assertTrue(all(item["analysis_status"] == "to_review" for item in scaffold["candidates"]))
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["rules"], [])
            blocked = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("verified_authority", blocked.stderr)
            waiver = self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", "verified_authority", "--reason", "本轮暂无外部法律数据库。",
                "--confirmed-by", "user", expected=2,
            )
            self.assertIn("不允许豁免", waiver.stderr)

    def test_verified_authority_links_elements_and_preserves_source_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_authority_node(case_root)
            state_before = json.loads(state_path.read_text(encoding="utf-8"))
            record = self.valid_authority(state_before)
            input_path = case_root / "authorities.json"
            self.write_authorities(input_path, [record])
            result = json.loads(self.run_cli(
                BUILD_AUTHORITIES, "--state", str(state_path), "--input", str(input_path),
            ).stdout)
            self.assertEqual(result["authority_count"], 1)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            stored = state["rules"][0]
            self.assertEqual(
                stored["article_text_sha256"], hashlib.sha256(record["article_text"].encode("utf-8")).hexdigest()
            )
            self.assertEqual(stored["case_jurisdiction"], "浙江省")
            self.assertEqual(stored["analysis_date"], "2026-08-24")
            elements = state["issues"][0]["our_position"]["elements"]
            self.assertTrue(all(item["rule_ids"] == ["rule-dismissal-test"] for item in elements))
            self.assertEqual(state["issues"][0]["opponent_position"]["rule_ids"], ["rule-dismissal-test"])
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["current_node"], "claims_procedure")

    def test_invalid_authorities_are_rejected_without_mutating_state(self):
        cases = [
            ("内部知识冒充权威来源", lambda item: item.update(source_type="internal_knowledge"), "source_type 无效"),
            ("来源 URL 无效", lambda item: item.update(source_url="not-a-url"), "source_url"),
            ("条文哈希不符", lambda item: item.update(article_text_sha256="0" * 64), "article_text_sha256"),
            ("地方口径地域错配", lambda item: item.update(
                territory_scope="local", applicable_jurisdictions=["上海市"]
            ), "地域范围与案件管辖地不匹配"),
            ("相关日期早于生效日", lambda item: item.update(effective_from="2026-01-01"), "早于法源生效日"),
            ("待核验法源被正式采用", lambda item: item.update(verification_status="conflict"), "正式采用的法源必须已核验"),
            ("废止法源无警示", lambda item: item.update(
                validity_status="repealed", effective_to="2025-12-31", warning=None
            ), "必须写明 warning"),
            ("旧索引冒充现行解答五", lambda item: item.update(
                document_id="ZJLAC-LABOR-132", validity_status="effective"
            ), "已列入浙江2026-08-25废止目录"),
            ("废止解答借旧日期正式采用", lambda item: item.update(
                document_title="浙江高院解答（三）", validity_status="repealed",
                warning="本文件已废止，但试图以早期事实日期继续正式采用。"
            ), "仅可 reference_only 或 excluded"),
            ("未覆盖全部要件", lambda item: item.update(element_ids=["element-ground"]), "尚未关联已核验且适用的法源"),
        ]
        for label, mutate, expected_message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                case_root = Path(temporary)
                state_path = self.prepare_authority_node(case_root)
                state = json.loads(state_path.read_text(encoding="utf-8"))
                original = state_path.read_bytes()
                record = deepcopy(self.valid_authority(state))
                mutate(record)
                input_path = case_root / "invalid-authority.json"
                self.write_authorities(input_path, [record])
                result = self.run_cli(
                    BUILD_AUTHORITIES, "--state", str(state_path), "--input", str(input_path), expected=2,
                )
                self.assertIn(expected_message, result.stderr)
                self.assertEqual(state_path.read_bytes(), original)

    def test_tampered_rule_link_is_blocked_by_independent_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_authority_node(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            input_path = case_root / "authority.json"
            self.write_authorities(input_path, [self.valid_authority(state)])
            self.run_cli(BUILD_AUTHORITIES, "--state", str(state_path), "--input", str(input_path))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["issues"][0]["our_position"]["elements"][0]["rule_ids"] = []
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = self.run_cli(VALIDATE, "--state", str(state_path), expected=1)
            payload = json.loads(result.stdout)
            self.assertTrue(any(item["code"] == "AUTHORITY_MATRIX" for item in payload["findings"]))
            self.assertIn("双向链接不一致", "\n".join(item["message"] for item in payload["findings"]))

    def test_legacy_placeholder_requires_explicit_replacement_and_keeps_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = self.prepare_authority_node(case_root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["rules"] = [{"rule_id": "legacy-placeholder"}]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            input_path = case_root / "authority.json"
            self.write_authorities(input_path, [self.valid_authority(state)])
            blocked = self.run_cli(
                BUILD_AUTHORITIES, "--state", str(state_path), "--input", str(input_path), expected=2,
            )
            self.assertIn("--replace-existing-rules", blocked.stderr)
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["rules"],
                [{"rule_id": "legacy-placeholder"}],
            )
            result = json.loads(self.run_cli(
                BUILD_AUTHORITIES, "--state", str(state_path), "--input", str(input_path),
                "--replace-existing-rules",
            ).stdout)
            self.assertEqual(result["replaced_previous_count"], 1)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            previous = json.loads(Path(state["previous_state"]).read_text(encoding="utf-8"))
            self.assertEqual(previous["rules"], [{"rule_id": "legacy-placeholder"}])


if __name__ == "__main__":
    unittest.main()
