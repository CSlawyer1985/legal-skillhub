"""四级成熟度门禁的回归测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.create_legal_skill import create_skill
from scripts.validate_legal_skill import check


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_INTAKE = PACKAGE_ROOT / "tests" / "fixtures" / "golden-contract-review-intake.json"


class MaturityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = json.loads(GOLDEN_INTAKE.read_text(encoding="utf-8"))

    def generated_skill(self, temporary_directory: str) -> Path:
        return create_skill(self.intake, Path(temporary_directory))

    def update_manifest(self, skill_dir: Path, transform) -> None:
        path = skill_dir / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        transform(manifest)
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_official_minimum_skill_is_auditable_without_false_production_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = Path(temporary_directory) / "minimal-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: minimal-skill\ndescription: 最小结构示例，仅用于官方格式审计。\n---\n",
                encoding="utf-8",
            )

            errors, warnings = check(skill_dir)

            self.assertEqual(errors, [])
            self.assertIn("不能确认法律成熟度", " ".join(warnings))

    def test_library_claim_requires_prior_art_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "reports" / "prior-art.md").unlink()

            errors, _ = check(skill_dir)

            self.assertIn("成熟度证据不存在", " ".join(errors))

    def test_library_claim_requires_skill_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            self.update_manifest(skill_dir, lambda manifest: manifest.pop("skill_contract"))

            errors, _ = check(skill_dir)

            self.assertIn("manifest.skill_contract", " ".join(errors))

    def test_governed_claim_requires_governance_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)

            def promote(manifest: dict) -> None:
                manifest["maturity_tier"] = "governed"
                manifest["maturity_label_zh"] = "高风险治理级"

            self.update_manifest(skill_dir, promote)

            errors, _ = check(skill_dir)

            joined = " ".join(errors)
            self.assertIn("quality_evidence.fixture_index", joined)
            self.assertIn("quality_evidence.human_review_evidence", joined)

    def test_production_claim_requires_scenario_archetype(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            self.update_manifest(skill_dir, lambda manifest: manifest.pop("scenario_archetype"))

            errors, _ = check(skill_dir)

            self.assertIn("scenario_archetype", " ".join(errors))

    def test_production_claim_rejects_unknown_scenario_archetype(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            self.update_manifest(
                skill_dir, lambda manifest: manifest.update({"scenario_archetype": "general_contract"})
            )

            errors, _ = check(skill_dir)

            self.assertIn("scenario_archetype", " ".join(errors))

    def test_non_meta_production_claim_requires_maturity_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = Path(temporary_directory) / "external-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: external-skill\ndescription: 外部工具生成的法律 Skill，声明治理级。\n---\n",
                encoding="utf-8",
            )
            (skill_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "external-skill",
                        "version": "1.0.0",
                        "maturity_tier": "governed",
                        "maturity_label_zh": "高风险治理级",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            errors, warnings = check(skill_dir)

            self.assertIn("无法证明成熟度", " ".join(errors))
            self.assertIn("未经生成器背书", " ".join(warnings))

    def test_empty_evidence_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "reports" / "prior-art.md").write_text("", encoding="utf-8")

            errors, _ = check(skill_dir)

            self.assertIn("成熟度证据为空文件", " ".join(errors))

    def test_placeholder_evidence_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "reports" / "prior-art.md").write_text(
                "# 同类方案取舍\n\n【填写来源与理由】\n", encoding="utf-8"
            )

            errors, _ = check(skill_dir)

            self.assertIn("成熟度证据仍含占位内容", " ".join(errors))

    def test_unparseable_json_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "reports" / "skill-ir.json").write_text("{not json", encoding="utf-8")

            errors, _ = check(skill_dir)

            self.assertIn("成熟度证据 JSON 无法解析", " ".join(errors))

    def test_governed_evidence_paths_must_be_safe_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)

            def promote_with_escape(manifest: dict) -> None:
                manifest["maturity_tier"] = "governed"
                manifest["maturity_label_zh"] = "高风险治理级"
                manifest["quality_evidence"]["fixture_index"] = "/etc/passwd"
                manifest["quality_evidence"]["human_review_evidence"] = "../human.json"

            self.update_manifest(skill_dir, promote_with_escape)

            errors, _ = check(skill_dir)

            joined = " ".join(errors)
            self.assertIn("quality_evidence.fixture_index 必须为包内安全相对路径", joined)
            self.assertIn("quality_evidence.human_review_evidence 必须为包内安全相对路径", joined)

    def test_production_claim_requires_method_core_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "references" / "legal-method-core.md").unlink()

            errors, _ = check(skill_dir)

            self.assertIn("缺少 references/legal-method-core.md", " ".join(errors))

    def test_production_claim_requires_archetype_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "references" / "contract_review.md").unlink()

            errors, _ = check(skill_dir)

            self.assertIn("缺少场景检查清单 references/contract_review.md", " ".join(errors))

    def test_references_dead_markdown_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            target = skill_dir / "references" / "legal-core-rules.md"
            target.write_text(
                target.read_text(encoding="utf-8") + "\n见 [缺失规则](missing-rule.md)。\n",
                encoding="utf-8",
            )

            errors, _ = check(skill_dir)

            self.assertIn("references/legal-core-rules.md 引用的资源不存在：missing-rule.md", " ".join(errors))

    def test_references_plain_text_mention_is_not_misjudged_as_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            target = skill_dir / "references" / "legal-core-rules.md"
            target.write_text(
                target.read_text(encoding="utf-8")
                + "\n纯文本提及 references/skill-research-sources.md，不是链接。\n",
                encoding="utf-8",
            )

            errors, warnings = check(skill_dir)

            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_production_claim_cannot_omit_output_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.generated_skill(temporary_directory)
            (skill_dir / "evals" / "output_assertions.json").unlink()
            (skill_dir / "evals" / "universal_legal_cases.json").unlink()

            def lower_to_production(manifest: dict) -> None:
                manifest["maturity_tier"] = "production"
                manifest["maturity_label_zh"] = "专业复用级"
                for key in ("skill_ir", "prior_art", "trust_review", "creation_handoff"):
                    manifest["quality_evidence"].pop(key, None)

            self.update_manifest(skill_dir, lower_to_production)

            errors, _ = check(skill_dir)

            self.assertIn("专业复用级以上缺少法律输出断言", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
