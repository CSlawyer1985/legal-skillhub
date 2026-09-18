"""从完整 intake 到自包含下游法律 Skill 的端到端回归测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.create_legal_skill import create_skill, validate_intake
from scripts.validate_legal_skill import check


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_INTAKE = PACKAGE_ROOT / "tests" / "fixtures" / "golden-contract-review-intake.json"
INTAKE_TEMPLATE = PACKAGE_ROOT / "assets" / "templates" / "legal-skill-intake.json"


class CreateLegalSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = json.loads(GOLDEN_INTAKE.read_text(encoding="utf-8"))

    def test_golden_intake_is_complete(self) -> None:
        self.assertEqual(validate_intake(self.intake), [])

    def test_template_cannot_be_generated_without_completion(self) -> None:
        template = json.loads(INTAKE_TEMPLATE.read_text(encoding="utf-8"))

        errors = validate_intake(template)

        joined = " ".join(errors)
        self.assertIn("仍是模板", joined)
        self.assertIn("占位内容", joined)

    def test_downstream_package_templates_are_bundled_as_assets(self) -> None:
        for filename in (
            "downstream-skill.template.md",
            "downstream-manifest.template.json",
            "downstream-interface.template.yaml",
            "downstream-trigger-cases.template.json",
            "downstream-output-assertions.json",
            "downstream-creation-handoff.template.md",
        ):
            self.assertTrue((PACKAGE_ROOT / "assets" / "templates" / filename).is_file(), filename)

    def test_end_to_end_generation_produces_valid_self_contained_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = create_skill(self.intake, Path(temporary_directory))

            errors, warnings = check(target)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertEqual(list(target.rglob("SKILL.md")), [target / "SKILL.md"])
            for relative in (
                "manifest.json",
                "LICENSE",
                "NOTICE",
                "agents/interface.yaml",
                "assets/legal-skill-output-contract.md",
                "evals/trigger_cases.json",
                "evals/output_assertions.json",
                "evals/universal_legal_cases.json",
                "reports/skill-ir.json",
                "reports/prior-art.md",
                "reports/trust-review.md",
                "scripts/validate_legal_skill.py",
                "references/universal-legal-capability-model.md",
            ):
                self.assertTrue((target / relative).is_file(), relative)

            ir = json.loads((target / "reports/skill-ir.json").read_text(encoding="utf-8"))
            self.assertEqual(ir["name"], "mainland-procurement-contract-review")
            self.assertIn("采购合同", ir["job"])
            self.assertNotIn("把可复用的中国大陆法律工作流设计", json.dumps(ir, ensure_ascii=False))
            package_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in target.rglob("*")
                if path.is_file() and path.suffix in {".md", ".json", ".yaml", ".py"}
            )
            self.assertNotIn("/" + "Users/", package_text)
            self.assertNotIn("/" + "home/", package_text)

    def test_generation_refuses_to_overwrite_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            create_skill(self.intake, Path(temporary_directory))

            with self.assertRaises(FileExistsError):
                create_skill(self.intake, Path(temporary_directory))

    def test_unknown_scenario_archetype_is_rejected(self) -> None:
        intake = deepcopy(self.intake)
        intake["scenario_archetype"] = "general_contract"

        errors = validate_intake(intake)

        self.assertIn("scenario_archetype", " ".join(errors))

    def test_missing_scenario_archetype_is_rejected(self) -> None:
        intake = deepcopy(self.intake)
        intake.pop("scenario_archetype")

        errors = validate_intake(intake)

        self.assertIn("scenario_archetype", " ".join(errors))

    def test_intent_canvas_missing_keys_are_rejected(self) -> None:
        intake = deepcopy(self.intake)
        for key in ("jurisdiction_bundle", "human_control"):
            intake["intent_canvas_coverage"].pop(key)

        errors = validate_intake(intake)

        joined = " ".join(errors)
        self.assertIn("jurisdiction_bundle", joined)
        self.assertIn("human_control", joined)

    def test_vague_intent_canvas_answer_is_rejected(self) -> None:
        for vague in ("按需", "略"):
            intake = deepcopy(self.intake)
            intake["intent_canvas_coverage"]["success"] = vague

            errors = validate_intake(intake)

            self.assertIn("intent_canvas_coverage.success", " ".join(errors))

    def test_each_scenario_archetype_generates_valid_package(self) -> None:
        archetypes = (
            "dispute_resolution",
            "contract_review",
            "document_drafting",
            "legal_research",
            "compliance_regulatory",
            "legal_retrieval",
            "evidence_files",
            "document_review_redline",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            for archetype in archetypes:
                with self.subTest(archetype=archetype):
                    intake = deepcopy(self.intake)
                    intake["name"] = "archetype-" + archetype.replace("_", "-")
                    intake["scenario_archetype"] = archetype

                    target = create_skill(intake, Path(temporary_directory))

                    errors, warnings = check(target)
                    self.assertEqual(errors, [])
                    self.assertEqual(warnings, [])
                    self.assertTrue((target / "references" / f"{archetype}.md").is_file())
                    self.assertTrue((target / "references" / "legal-method-core.md").is_file())
                    self.assertTrue((target / "references" / "legal-scenario-archetypes.md").is_file())
                    self.assertTrue((target / "references" / "legal-skill-ir.md").is_file())
                    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
                    self.assertEqual(manifest["scenario_archetype"], archetype)

    def test_library_intake_requires_seven_evaluation_cases(self) -> None:
        intake = deepcopy(self.intake)
        intake["evaluation_cases"] = intake["evaluation_cases"][:1]

        errors = validate_intake(intake)

        self.assertIn("至少需要 7 个", " ".join(errors))

    def governed_intake(self) -> dict:
        intake = deepcopy(self.intake)
        intake["name"] = "governed-procurement-contract-review"
        intake["maturity"] = "governed"
        intake["evidence_boundary"]["present"].append("2026-08-12 承办律师合成用例人工复核记录")
        intake["governance_evidence"] = {
            "fixture_index": [
                {
                    "id": "synthetic-contract-01",
                    "filename": "synthetic-contract-01.md",
                    "content": "# 合成采购合同\n\n仅用于评测，不含真实客户信息。",
                    "authorization": "synthetic",
                    "expected_boundary": "不得把合成条款外的信息补成事实",
                }
            ],
            "permission_policy": "只读处理合成夹具；联网、外传、签署、发信和提交均不授权。",
            "rollback_plan": "保留生成前版本；治理规则变更失败时恢复上一版本并重新运行全部门禁。",
            "human_review_records": [
                {
                    "reviewer": "承办律师",
                    "reviewed_at": "2026-08-12",
                    "case_id": "synthetic-contract-01",
                    "outcome": "通过并要求保留依据缺失停止路径",
                    "confidence": "中",
                    "reason": "合成用例输出能够区分材料、事实、法律评价和程序状态",
                }
            ],
        }
        return intake

    def test_governed_generation_requires_and_packages_real_evidence_records(self) -> None:
        intake = self.governed_intake()

        with tempfile.TemporaryDirectory() as temporary_directory:
            target = create_skill(intake, Path(temporary_directory))
            errors, warnings = check(target)

            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertTrue((target / "evals/fixtures/synthetic-contract-01.md").is_file())
            self.assertTrue((target / "reports/human-review-evidence.json").is_file())
            ir = json.loads((target / "reports/skill-ir.json").read_text(encoding="utf-8"))
            self.assertIn("evals/fixtures/synthetic-contract-01.md", ir["resources"]["evals"])

    def test_governed_intake_rejects_unreal_review_date(self) -> None:
        for bad_date in ("9999-99-99", "0000-00-00", "2099-01-01"):
            with self.subTest(bad_date=bad_date):
                intake = self.governed_intake()
                intake["governance_evidence"]["human_review_records"][0]["reviewed_at"] = bad_date

                errors = validate_intake(intake)

                self.assertIn("日期格式无效", " ".join(errors))

    def test_governed_intake_rejects_windows_fixture_filename_escape(self) -> None:
        for bad_name in ("..\\..\\evil", "../evil", "/abs/evil"):
            with self.subTest(bad_name=bad_name):
                intake = self.governed_intake()
                intake["governance_evidence"]["fixture_index"][0]["filename"] = bad_name

                errors = validate_intake(intake)

                self.assertIn("filename 必须为单个安全文件名", " ".join(errors))

    def test_governed_package_rejects_unreal_review_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = create_skill(self.governed_intake(), Path(temporary_directory))
            evidence_path = target / "reports" / "human-review-evidence.json"
            records = json.loads(evidence_path.read_text(encoding="utf-8"))
            records[0]["reviewed_at"] = "9999-99-99"
            evidence_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

            errors, _ = check(target)

            self.assertIn("日期格式无效", " ".join(errors))

    def test_failed_generation_leaves_no_partial_package(self) -> None:
        intake = deepcopy(self.intake)
        intake["evaluation_cases"][0]["assertion_ids"] = ["unknown-assertion"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(RuntimeError):
                create_skill(intake, Path(temporary_directory))

            self.assertEqual(list(Path(temporary_directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
