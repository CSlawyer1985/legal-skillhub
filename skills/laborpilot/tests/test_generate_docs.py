"""文书生成器在缺少 Pandoc 时给出可执行提示，而不是原始异常。"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generate_docs


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "tests" / "fixtures" / "docx-case.json"


class GenerateDocsPandocTest(unittest.TestCase):
    def test_md_to_docx_reports_missing_binary(self):
        with patch("generate_docs.subprocess.run", side_effect=FileNotFoundError):
            ok, err = generate_docs.md_to_docx(Path("draft.md"), Path("draft.docx"))
        self.assertFalse(ok)
        self.assertIn("未找到 Pandoc", err)
        self.assertIn("https://pandoc.org", err)

    def test_cli_exits_with_install_hint_when_pandoc_absent(self):
        env = os.environ.copy()
        env["PATH"] = ""
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_docs.py"),
                    "--case",
                    str(CASE),
                    "--output",
                    temporary,
                    "--types",
                    "仲裁申请书",
                    "--delivery-status",
                    "lawyer_review_draft",
                    "--strict",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("未找到 Pandoc", result.stderr)
        self.assertNotIn("FileNotFoundError", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
