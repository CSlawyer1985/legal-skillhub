"""交付包密钥、路径和系统杂项文件扫描回归测试。"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.create_legal_skill import create_skill
from scripts.validate_legal_skill import check


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_INTAKE = PACKAGE_ROOT / "tests" / "fixtures" / "golden-contract-review-intake.json"


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = json.loads(GOLDEN_INTAKE.read_text(encoding="utf-8"))

    def test_jwt_like_secret_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = create_skill(self.intake, Path(temporary_directory))
            (skill_dir / "references" / "leak.md").write_text(
                "token=" + "ey" + "Jabcdefghijk.abcdefghijk.abcdefghijk", encoding="utf-8"
            )

            errors, _ = check(skill_dir)

            self.assertIn("疑似密钥模式", " ".join(errors))

    def test_windows_user_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = create_skill(self.intake, Path(temporary_directory))
            windows_path = "C:" + "\\" + "Users" + "\\" + "Example" + "\\rules.md"
            (skill_dir / "references" / "path.md").write_text(windows_path, encoding="utf-8")

            errors, _ = check(skill_dir)

            self.assertIn("含用户绝对路径", " ".join(errors))

    def test_ds_store_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = create_skill(self.intake, Path(temporary_directory))
            (skill_dir / ".DS_Store").write_bytes(b"metadata")

            errors, _ = check(skill_dir)

            self.assertIn("系统杂项文件", " ".join(errors))

    def test_symlinked_maturity_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = create_skill(self.intake, Path(temporary_directory))
            external = Path(temporary_directory) / "external-ir.json"
            external.write_text("{}", encoding="utf-8")
            target = skill_dir / "reports" / "skill-ir.json"
            target.unlink()
            os.symlink(external, target)

            errors, _ = check(skill_dir)

            self.assertIn("不得经过软链接", " ".join(errors))

    def test_malformed_empty_description_is_friendly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            skill_dir = Path(temporary_directory) / "broken-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: broken-skill\ndescription:\nlicense: Apache-2.0\n---\n",
                encoding="utf-8",
            )

            errors, _ = check(skill_dir)

            self.assertTrue(errors)
            self.assertNotIn("Traceback", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
