"""法律 Skill IR v0.3 导出器的升级回归测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import export_legal_skill_ir
from scripts.validate_legal_profile import REQUIRED_MODULES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTER = PROJECT_ROOT / "scripts" / "export_legal_skill_ir.py"
PROFILE_TEMPLATE = PROJECT_ROOT / "assets" / "templates" / "legal-capability-profile.json"


def complete_profile() -> dict[str, object]:
    profile = json.loads(PROFILE_TEMPLATE.read_text(encoding="utf-8"))
    profile["modules"] = {
        module: profile["modules"][module] for module in reversed(REQUIRED_MODULES)
    }
    return profile


class ExportLegalSkillIrTests(unittest.TestCase):
    def create_skill(
        self, temporary_directory: str, legal_profile: dict[str, object]
    ) -> Path:
        skill_dir = Path(temporary_directory) / "synthetic-legal-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: synthetic-legal-skill\ndescription: |\n  合成测试 Skill\n---\n",
            encoding="utf-8",
        )
        (skill_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "name": "synthetic-legal-skill",
                    "version": "0.6.0",
                    "legal_profile": legal_profile,
                    "skill_contract": {
                        "job": "审查中国大陆采购合同并形成逐条风险与修改建议",
                        "decision": {
                            "goal": "支持业务决定是否签署或修改合同",
                            "owner": "合同负责人",
                            "supported_action": "提出修改与谈判建议"
                        },
                        "target_users": ["律师"],
                        "inputs": ["采购合同"],
                        "outputs": ["合同审查报告"],
                        "exclusions": ["替代律师签发"],
                        "workflow": ["识别交易", "逐条审查"],
                        "decision_points": ["风险是否可接受"],
                        "failure_modes": ["关键附件缺失"]
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return skill_dir

    def test_build_ir_exports_new_profile_with_stable_summary_and_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.create_skill(temporary_directory, complete_profile())
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "z.md").write_text("z", encoding="utf-8")
            (skill_dir / "references" / "a.md").write_text("a", encoding="utf-8")
            (skill_dir / "references" / ".hidden").mkdir()
            (skill_dir / "references" / ".hidden" / "secret.md").write_text(
                "hidden", encoding="utf-8"
            )
            (skill_dir / "scripts" / "__pycache__").mkdir(parents=True)
            (skill_dir / "scripts" / "__pycache__" / "cached.pyc").write_bytes(b"")

            first = export_legal_skill_ir.build_ir(skill_dir, generated_at="2026-01-02")
            second = export_legal_skill_ir.build_ir(skill_dir, generated_at="2026-01-02")

            self.assertEqual(first, second)
            self.assertEqual(first["schema_version"], "legal-skill-ir/v0.3")
            self.assertEqual(first["generated_at"], "2026-01-02")
            self.assertEqual(first["description"], "合成测试 Skill")
            self.assertEqual(first["job"], "审查中国大陆采购合同并形成逐条风险与修改建议")
            self.assertNotIn("把可复用的中国大陆法律工作流设计", json.dumps(first, ensure_ascii=False))
            self.assertEqual(list(first["legal_profile"]["modules"]), list(REQUIRED_MODULES))
            self.assertEqual(
                first["capability_summary"],
                {"total": 12, "active": 12, "not_applicable": 0, "blocked": 0},
            )
            self.assertEqual(
                list(first["capability_summary"]),
                ["total", "active", "not_applicable", "blocked"],
            )
            self.assertEqual(first["migration_warnings"], [])
            self.assertEqual(first["resources"]["references"], ["references/a.md", "references/z.md"])
            self.assertEqual(first["resources"]["scripts"], [])
            self.assertNotIn(str(skill_dir.resolve()), json.dumps(first, ensure_ascii=False))

    def test_build_ir_preserves_legacy_profile_without_fabricating_modules(self) -> None:
        legacy_profile = {
            "jurisdiction_default": "中国大陆",
            "verification": "具体法条、司法解释、时效和案例独立核验",
            "fact_evidence_model": ["材料", "事实", "法律评价", "程序"],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.create_skill(temporary_directory, legacy_profile)

            ir = export_legal_skill_ir.build_ir(skill_dir, generated_at="2026-01-02")

            self.assertEqual(ir["legal_profile"], legacy_profile)
            self.assertNotIn("modules", ir["legal_profile"])
            self.assertEqual(
                ir["capability_summary"],
                {"total": 0, "active": 0, "not_applicable": 0, "blocked": 0},
            )
            self.assertEqual(len(ir["migration_warnings"]), 1)
            self.assertIn("尚未迁移", ir["migration_warnings"][0])

    def test_missing_skill_contract_stays_empty_instead_of_using_meta_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.create_skill(temporary_directory, complete_profile())
            manifest_path = skill_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["skill_contract"]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

            ir = export_legal_skill_ir.build_ir(skill_dir, generated_at="2026-01-02")

            self.assertEqual(ir["job"], "")
            self.assertEqual(ir["workflow"], [])
            self.assertIn("skill_contract", " ".join(ir["migration_warnings"]))

    def test_cli_keeps_relative_output_compatible_and_writes_parseable_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.create_skill(temporary_directory, complete_profile())

            completed = subprocess.run(
                [sys.executable, str(EXPORTER), ".", "--output", "reports/skill-ir.json"],
                cwd=skill_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            output_path = skill_dir / "reports" / "skill-ir.json"
            self.assertTrue(output_path.is_file())
            ir = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(ir["schema_version"], "legal-skill-ir/v0.3")
            self.assertNotIn(str(skill_dir.resolve()), json.dumps(ir, ensure_ascii=False))


    def run_cli(self, skill_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(EXPORTER), str(skill_dir), "--output", "reports/skill-ir.json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_reports_missing_skill_md_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = Path(temporary_directory) / "empty-skill"
            skill_dir.mkdir()

            completed = self.run_cli(skill_dir)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("SKILL.md", completed.stdout + completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_cli_rejects_non_object_manifest_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.create_skill(temporary_directory, complete_profile())
            (skill_dir / "manifest.json").write_text('["不是对象"]', encoding="utf-8")

            completed = self.run_cli(skill_dir)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("manifest.json 必须为 JSON 对象", completed.stdout + completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_cli_rejects_trigger_case_without_prompt_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = self.create_skill(temporary_directory, complete_profile())
            (skill_dir / "evals").mkdir()
            (skill_dir / "evals" / "trigger_cases.json").write_text(
                json.dumps({"cases": [{"id": "c1", "kind": "should-trigger"}]}, ensure_ascii=False),
                encoding="utf-8",
            )

            completed = self.run_cli(skill_dir)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("prompt", completed.stdout + completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
