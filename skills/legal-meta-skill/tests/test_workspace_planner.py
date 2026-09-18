from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.plan_legal_workspace import plan


class WorkspacePlannerTests(unittest.TestCase):
    def test_plan_only_does_not_create_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "案件"
            result = plan("case_analysis_v2", root)
            self.assertTrue(result["plan_only"])
            self.assertFalse(root.exists())
            self.assertNotIn("input", json.dumps(result, ensure_ascii=False))

    def test_initialize_creates_chinese_profile_and_guide(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "尽调"
            result = plan("due_diligence", root, initialize=True)
            self.assertFalse(result["plan_only"])
            self.assertTrue((root / "文件夹使用说明.md").is_file())
            self.assertTrue((root / "原始底稿").is_dir())
            self.assertFalse((root / "input").exists())
            self.assertFalse((root / "scratch").exists())
            self.assertFalse((root / "output").exists())

    def test_legacy_directories_are_reported_without_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "input").mkdir()
            result = plan("legal_research", root)
            self.assertEqual(result["legacy_directories"], ["input"])
            self.assertTrue((root / "input").is_dir())


if __name__ == "__main__":
    unittest.main()
