"""法律能力配置校验器的升级回归测试。"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


REQUIRED_MODULES = (
    "task_context",
    "jurisdiction",
    "temporal",
    "actors",
    "matter",
    "claims_and_elements",
    "authority_and_interpretation",
    "proof",
    "procedure",
    "outcomes_and_enforcement",
    "strategy_and_uncertainty",
    "governance",
)

MODULE_LABELS = {
    "task_context": "任务目的与受众",
    "jurisdiction": "法域",
    "temporal": "时间",
    "actors": "主体角色",
    "matter": "法律事项",
    "claims_and_elements": "请求与要件",
    "authority_and_interpretation": "法源与解释",
    "proof": "证明",
    "procedure": "程序",
    "outcomes_and_enforcement": "结果与执行",
    "strategy_and_uncertainty": "策略与不确定性",
    "governance": "职业治理",
}

PROFILE_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "templates"
    / "legal-capability-profile.json"
)
SKILL_ROOT = Path(__file__).resolve().parents[1]


def complete_manifest() -> dict[str, object]:
    """返回一个具有完整十二模块配置的合成 manifest。"""
    profile = json.loads(PROFILE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return {
        "name": "synthetic-legal-skill",
        "version": "0.6.0",
        "legal_profile": deepcopy(profile),
    }


class ValidateLegalProfileTests(unittest.TestCase):
    def test_profile_template_matches_required_modules(self) -> None:
        self.assertTrue(
            PROFILE_TEMPLATE_PATH.is_file(),
            f"法律能力配置模板不存在：{PROFILE_TEMPLATE_PATH}",
        )
        profile = json.loads(PROFILE_TEMPLATE_PATH.read_text(encoding="utf-8"))
        modules = profile["modules"]

        self.assertEqual(set(modules), set(REQUIRED_MODULES))
        self.assertEqual(len(modules), 12)
        for module_id, module in modules.items():
            with self.subTest(module_id=module_id):
                label = module.get("label_zh")
                self.assertIsInstance(label, str)
                self.assertRegex(label, r"[\u4e00-\u9fff]")
                required_outputs = module.get("required_outputs")
                self.assertIsInstance(required_outputs, list)
                self.assertTrue(required_outputs)

    def write_manifest(self, manifest: dict[str, object]) -> dict[str, object]:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        manifest_path = Path(temporary_directory.name) / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def validate(
        self, manifest: dict[str, object], *, strict: bool = False
    ) -> tuple[list[str], list[str]]:
        persisted_manifest = self.write_manifest(manifest)
        try:
            from scripts.validate_legal_profile import validate_profile
        except ModuleNotFoundError as exc:
            self.fail(f"尚未实现法律能力配置校验器：{exc}")
        return validate_profile(persisted_manifest, strict=strict)

    def clone_skill_package(self, name: str = "legal-meta-skill") -> Path:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        skill_dir = Path(temporary_directory.name) / name
        shutil.copytree(
            SKILL_ROOT,
            skill_dir,
            ignore=shutil.ignore_patterns(
                ".git", ".superpowers", "__pycache__", ".pytest_cache"
            ),
        )
        if name != "legal-meta-skill":
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "name: legal-meta-skill", f"name: {name}", 1
                ),
                encoding="utf-8",
            )
            manifest = json.loads((skill_dir / "manifest.json").read_text(encoding="utf-8"))
            manifest["name"] = name
            (skill_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return skill_dir

    def read_skill_manifest(self, skill_dir: Path) -> dict[str, object]:
        return json.loads((skill_dir / "manifest.json").read_text(encoding="utf-8"))

    def write_skill_manifest(self, skill_dir: Path, manifest: dict[str, object]) -> None:
        (skill_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def check_skill(self, skill_dir: Path) -> tuple[list[str], list[str]]:
        from scripts.validate_legal_skill import check

        return check(skill_dir)

    def test_complete_twelve_module_profile_passes(self) -> None:
        errors, warnings = self.validate(complete_manifest())

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_module_fails(self) -> None:
        manifest = complete_manifest()
        modules = manifest["legal_profile"]["modules"]
        del modules[REQUIRED_MODULES[-1]]

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_unknown_module_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"]["invented_module"] = {
            "label_zh": "虚构模块",
            "status": "active",
            "reason": "不应被校验器接受",
            "required_outputs": ["minimum_output"],
        }

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_unknown_status_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["status"] = "unknown-status"

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_not_applicable_without_reason_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]] = {
            "status": "not_applicable"
        }

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_blocked_without_gap_or_fallback_fails(self) -> None:
        with self.subTest("missing gap"):
            manifest = complete_manifest()
            manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]] = {
                "status": "blocked",
                "fallback": "人工复核",
            }

            errors, _ = self.validate(manifest)

            self.assertNotEqual(errors, [])

        with self.subTest("missing fallback"):
            manifest = complete_manifest()
            manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]] = {
                "status": "blocked",
                "gap": "缺少经核验的模型能力",
            }

            errors, _ = self.validate(manifest)

            self.assertNotEqual(errors, [])

    def test_blocked_with_placeholder_gap_and_fallback_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]] = {
            "label_zh": "任务目的与受众",
            "status": "blocked",
            "gap": "无",
            "fallback": "略",
        }

        errors, _ = self.validate(manifest)

        joined = " ".join(errors)
        self.assertIn("缺少输入或依据缺口", joined)
        self.assertIn("缺少停止或降级路径", joined)

    def test_legacy_profile_without_model_only_warns(self) -> None:
        manifest = complete_manifest()
        del manifest["legal_profile"]["schema_version"]
        del manifest["legal_profile"]["activation_policy"]

        errors, warnings = self.validate(manifest)

        self.assertEqual(errors, [])
        self.assertIn("旧版法律能力配置", " ".join(warnings))

    def test_legacy_profile_without_model_fails_in_strict_mode(self) -> None:
        manifest = complete_manifest()
        del manifest["legal_profile"]["schema_version"]

        errors, warnings = self.validate(manifest, strict=True)

        self.assertIn("缺少通用法律能力模型", " ".join(errors))
        self.assertEqual(warnings, [])

    def test_wrong_schema_version_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["schema_version"] = "universal-legal-core/v0.2"

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_wrong_activation_policy_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["activation_policy"] = "optional"

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_active_module_without_required_outputs_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["required_outputs"] = []

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_active_module_without_specific_reason_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["reason"] = ""

        errors, _ = self.validate(manifest)

        self.assertIn("具体理由", " ".join(errors))

    def test_active_module_with_incomplete_minimum_outputs_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["required_outputs"] = [
            "task_type"
        ]

        errors, _ = self.validate(manifest)

        self.assertIn("缺少通用最低输出", " ".join(errors))

    def test_module_without_chinese_label_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["label_zh"] = ""

        errors, _ = self.validate(manifest)

        self.assertNotEqual(errors, [])

    def test_module_with_english_only_label_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["label_zh"] = "Task context"

        errors, _ = self.validate(manifest)

        self.assertIn("中文标签必须为", " ".join(errors))

    def test_module_with_wrong_chinese_label_fails(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]]["label_zh"] = "其他中文"

        errors, _ = self.validate(manifest)

        self.assertIn("中文标签必须为", " ".join(errors))

    def test_not_applicable_with_placeholder_reason_fails(self) -> None:
        for reason in ("按需", " 无， ", "略。", "否", "不适用", "。！？"):
            with self.subTest(reason=reason):
                manifest = complete_manifest()
                manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]].update(
                    {"status": "not_applicable", "reason": reason}
                )

                errors, _ = self.validate(manifest)

                self.assertIn("缺少具体理由", " ".join(errors))

    def test_not_applicable_with_concrete_reason_passes(self) -> None:
        manifest = complete_manifest()
        manifest["legal_profile"]["modules"][REQUIRED_MODULES[0]].update(
            {
                "status": "not_applicable",
                "reason": "该轻量法条核验工具不比较诉讼策略，但保留人工复核触发条件。",
                "required_outputs": [],
            }
        )

        errors, warnings = self.validate(manifest)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_creator_version_0_10_0_requires_strict_validation(self) -> None:
        try:
            from scripts.validate_legal_skill import requires_strict_profile
        except ImportError as exc:
            self.fail(f"尚未实现严格模式判定：{exc}")

        self.assertTrue(
            requires_strict_profile(
                {
                    "name": "downstream-skill",
                    "creator": {
                        "created_with": "legal-meta-skill",
                        "created_with_version": "0.10.0",
                    },
                }
            )
        )

    def test_check_rejects_meta_skill_with_missing_module(self) -> None:
        skill_dir = self.clone_skill_package()
        manifest = self.read_skill_manifest(skill_dir)
        del manifest["legal_profile"]["modules"][REQUIRED_MODULES[-1]]
        self.write_skill_manifest(skill_dir, manifest)

        errors, _ = self.check_skill(skill_dir)

        self.assertIn("法律能力模型缺少模块", " ".join(errors))

    def test_check_rejects_explicit_new_model_with_missing_module(self) -> None:
        skill_dir = self.clone_skill_package("synthetic-new-model")
        manifest = self.read_skill_manifest(skill_dir)
        del manifest["legal_profile"]["modules"][REQUIRED_MODULES[-1]]
        self.write_skill_manifest(skill_dir, manifest)

        errors, _ = self.check_skill(skill_dir)

        self.assertIn("法律能力模型缺少模块", " ".join(errors))

    def test_check_warns_for_ordinary_legacy_downstream_skill(self) -> None:
        skill_dir = self.clone_skill_package("legacy-downstream-skill")
        manifest = self.read_skill_manifest(skill_dir)
        manifest["legal_profile"] = {"jurisdiction_default": "中国大陆"}
        manifest["creator"]["created_with"] = "other-skill"
        manifest["creator"].pop("created_with_version")
        self.write_skill_manifest(skill_dir, manifest)

        errors, warnings = self.check_skill(skill_dir)

        self.assertEqual(errors, [])
        self.assertIn("旧版法律能力配置", " ".join(warnings))

    def test_check_requires_strict_profile_for_creator_version_0_10_0(self) -> None:
        skill_dir = self.clone_skill_package("newer-downstream-skill")
        manifest = self.read_skill_manifest(skill_dir)
        manifest["legal_profile"] = {"jurisdiction_default": "中国大陆"}
        manifest["creator"]["created_with"] = "legal-meta-skill"
        manifest["creator"]["created_with_version"] = "0.10.0"
        self.write_skill_manifest(skill_dir, manifest)

        errors, warnings = self.check_skill(skill_dir)

        self.assertIn("缺少通用法律能力模型", " ".join(errors))
        self.assertEqual(warnings, [])

    def test_check_rejects_non_hidden_nested_skill_file(self) -> None:
        skill_dir = self.clone_skill_package()
        nested_skill = skill_dir / "references" / "ordinary-nested" / "SKILL.md"
        nested_skill.parent.mkdir()
        nested_skill.write_text("name: nested\n", encoding="utf-8")

        errors, _ = self.check_skill(skill_dir)

        self.assertIn("references/ordinary-nested/SKILL.md", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
