"""LaborPilot 整包版本同步机制的回归测试。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "sync_version.py"
SPEC = importlib.util.spec_from_file_location("laborpilot_version_sync_test", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"无法加载版本同步脚本：{SCRIPT_PATH}")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


def _write_fixture(root: Path) -> None:
    (root / ".codex-plugin").mkdir(parents=True)
    (root / "data").mkdir(parents=True)
    (root / "evals").mkdir(parents=True)
    (root / "skills" / "sample").mkdir(parents=True)
    (root / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (root / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": "Fixture", "version": "0.1.0"}, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "data" / "knowledge-build-stats.json").write_text(
        json.dumps({"manifest_version": "1.0.0", "package_version": "0.1.0"}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (root / "evals" / "evals.json").write_text(
        json.dumps({"schema_version": "2.0", "package_version": "0.1.0"}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# Fixture\n\n"
        "[![Version](https://img.shields.io/badge/version-v0.1.0-brightgreen.svg)]"
        "(./CHANGELOG.md)\n",
        encoding="utf-8",
    )
    skill_text = (
        "---\n"
        "name: fixture\n"
        'version: "0.1.0"\n'
        "---\n\n"
        "正文中的 version: 示例不得被替换。\n"
    )
    (root / "SKILL.md").write_text(skill_text, encoding="utf-8")
    (root / "skills" / "sample" / "SKILL.md").write_text(skill_text, encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "# 更新日志\n\n## [0.1.0] - 2026-08-22\n",
        encoding="utf-8",
    )


class VersionSyncTest(unittest.TestCase):
    def test_repository_versions_are_consistent(self):
        self.assertEqual(SYNC.consistency_issues(ROOT), [])

    def test_set_version_updates_all_machine_readable_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_fixture(root)

            changed = SYNC.set_version(root, "1.2.3")

            self.assertEqual(len(changed), 7)
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "1.2.3\n")
            manifest = json.loads(
                (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], "1.2.3")
            knowledge_stats = json.loads(
                (root / "data" / "knowledge-build-stats.json").read_text(encoding="utf-8")
            )
            self.assertEqual(knowledge_stats["package_version"], "1.2.3")
            evals = json.loads(
                (root / "evals" / "evals.json").read_text(encoding="utf-8")
            )
            self.assertEqual(evals["package_version"], "1.2.3")
            self.assertIn(
                "version-v1.2.3-brightgreen.svg",
                (root / "README.md").read_text(encoding="utf-8"),
            )
            for path in SYNC.skill_files(root):
                text = path.read_text(encoding="utf-8")
                self.assertIn('version: "1.2.3"', text)
                self.assertIn("正文中的 version: 示例不得被替换。", text)

            issues = SYNC.consistency_issues(root)
            self.assertEqual(len(issues), 1)
            self.assertIn("CHANGELOG.md", issues[0])

            (root / "CHANGELOG.md").write_text(
                "# 更新日志\n\n## [1.2.3] - 2026-08-22\n",
                encoding="utf-8",
            )
            self.assertEqual(SYNC.consistency_issues(root), [])

    def test_readme_version_is_checked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_fixture(root)
            (root / "README.md").write_text(
                "# Fixture\n\n"
                "[![Version](https://img.shields.io/badge/version-v9.9.9-brightgreen.svg)]"
                "(./CHANGELOG.md)\n",
                encoding="utf-8",
            )

            issues = SYNC.consistency_issues(root)

            self.assertEqual(len(issues), 1)
            self.assertIn("README.md", issues[0])
            self.assertIn("9.9.9", issues[0])

    def test_eval_dataset_version_drift_is_checked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_fixture(root)
            evals_path = root / "evals" / "evals.json"
            evals = json.loads(evals_path.read_text(encoding="utf-8"))
            evals["package_version"] = "9.9.9"
            evals_path.write_text(json.dumps(evals, indent=2) + "\n", encoding="utf-8")

            issues = SYNC.consistency_issues(root)

            self.assertEqual(len(issues), 1)
            self.assertIn("evals/evals.json", issues[0])
            self.assertIn("9.9.9", issues[0])

    def test_invalid_version_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_fixture(root)

            with self.assertRaises(ValueError):
                SYNC.set_version(root, "1.2")

            self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "0.1.0\n")

    def test_invalid_target_is_rejected_before_any_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_fixture(root)
            (root / ".codex-plugin" / "plugin.json").write_text(
                "{invalid json}\n",
                encoding="utf-8",
            )

            with self.assertRaises(json.JSONDecodeError):
                SYNC.set_version(root, "1.2.3")

            self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "0.1.0\n")
            for path in SYNC.skill_files(root):
                self.assertIn(
                    'version: "0.1.0"',
                    path.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
