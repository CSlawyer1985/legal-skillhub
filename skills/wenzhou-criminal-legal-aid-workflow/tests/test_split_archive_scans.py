"""split_archive_scans.py 回归测试：按页码规则切割扫描件并核对输出。"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
SPLITTER = ROOT / "scripts" / "split_archive_scans.py"


def make_pdf(path: Path, pages: int) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=841)
    with open(path, "wb") as handle:
        writer.write(handle)


class SplitArchiveScansTests(unittest.TestCase):
    def test_split_extracts_pdf_files_by_rule(self) -> None:
        temp = Path(tempfile.mkdtemp(prefix="legal-aid-split-"))
        source = temp / "归档扫描材料.pdf"
        make_pdf(source, 5)
        spec = temp / "切割规则.json"
        spec.write_text(
            json.dumps(
                [
                    {"name": "01-指派通知书", "from": 1, "to": 1},
                    {"name": "02-委托协议、授权委托书", "from": 2, "to": 3},
                    {"name": "03-会见笔录", "from": 4, "to": 5},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        out = temp / "归档PDF"
        result = subprocess.run(
            [sys.executable, str(SPLITTER), "--input", str(source), "--spec", str(spec), "--output-dir", str(out)],
            capture_output=True,
            text=True,
            check=True,
        )
        files = sorted(p.name for p in out.glob("*.pdf"))
        self.assertEqual(files, ["01-指派通知书.pdf", "02-委托协议、授权委托书.pdf", "03-会见笔录.pdf"])
        self.assertEqual(len(PdfReader(str(out / "01-指派通知书.pdf")).pages), 1)
        self.assertEqual(len(PdfReader(str(out / "02-委托协议、授权委托书.pdf")).pages), 2)
        self.assertEqual(len(PdfReader(str(out / "03-会见笔录.pdf")).pages), 2)
        # 全部页码均已分配，不应出现未分配提示
        self.assertNotIn("未分配", result.stdout)

    def test_split_rejects_out_of_range_pages(self) -> None:
        temp = Path(tempfile.mkdtemp(prefix="legal-aid-split-bad-"))
        source = temp / "归档扫描材料.pdf"
        make_pdf(source, 3)
        spec = temp / "切割规则.json"
        spec.write_text(json.dumps([{"name": "超范围", "from": 1, "to": 9}], ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SPLITTER), "--input", str(source), "--spec", str(spec), "--output-dir", str(temp / "out")],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("超出范围", result.stderr)


if __name__ == "__main__":
    unittest.main()

