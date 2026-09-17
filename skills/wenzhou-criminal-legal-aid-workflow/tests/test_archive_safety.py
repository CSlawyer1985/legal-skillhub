"""归档提取边界测试；仅使用合成页面，不包含真实案件。"""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("archive_splitter", ROOT / "scripts/split_archive_scans.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ArchiveSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "原件.pdf"
        writer = PdfWriter()
        for width in (101, 202, 303):
            writer.add_blank_page(width=width, height=400)
        writer.write(str(self.src))
        self.original = self.src.read_bytes()

    def run_split(self, rules, out=None, **kw):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.split(self.src, rules, out or self.root / "输出", **kw)
        self.assertEqual(self.original, self.src.read_bytes())
        return buf.getvalue()

    def test_noncontiguous_order_and_source_directory_allowed(self):
        message = self.run_split([{"name": "会见材料", "pages": [3, 1]}], self.root)
        pages = PdfReader(self.root / "会见材料.pdf").pages
        self.assertEqual([float(p.mediabox.width) for p in pages], [303, 101])
        self.assertIn("未分配页码：[2]", message)

    def test_existing_source_and_target_never_overwritten(self):
        for name in ("原件", "旧文件"):
            old = self.root / (name + ".pdf")
            if name == "旧文件":
                old.write_bytes(b"existing")
            before = old.read_bytes()
            with self.assertRaises(ValueError):
                self.run_split([{"name": name, "pages": [1]}], self.root)
            self.assertEqual(old.read_bytes(), before)

    def test_invalid_later_rule_produces_no_partial_outputs(self):
        for bad in ([4], [True], [1.5], [], "1"):
            with self.assertRaises(ValueError):
                self.run_split([{"name": "合法", "pages": [1]}, {"name": "错误", "pages": bad}])
            self.assertFalse((self.root / "输出").exists())

    def test_sanitized_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            self.run_split([{"name": "a/b", "pages": [1]}, {"name": "a:b", "pages": [2]}])
        self.assertFalse((self.root / "输出").exists())

    def test_overlap_requires_explicit_permission(self):
        rules = [{"name": "甲", "pages": [1]}, {"name": "乙", "pages": [1]}]
        with self.assertRaises(ValueError):
            self.run_split(rules)
        self.assertIn("已显式允许重复", self.run_split(rules, allow_overlap=True))

    def test_commit_failure_rolls_back_only_current_outputs(self):
        out = self.root / "输出"
        out.mkdir()
        old = out / "已有材料.pdf"
        old.write_bytes(b"keep")
        link = os.link
        calls = []
        def failing_link(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise OSError("模拟交付失败")
            return link(source, target)
        with patch.object(mod.os, "link", side_effect=failing_link):
            with self.assertRaises(OSError):
                self.run_split([{"name": "甲", "pages": [1]}, {"name": "乙", "pages": [2]}], out)
        self.assertEqual([p.name for p in out.iterdir()], ["已有材料.pdf"])
        self.assertEqual(old.read_bytes(), b"keep")

    def test_render_failure_leaves_no_partial_outputs(self):
        with patch.object(mod.PdfWriter, "write", side_effect=OSError("模拟磁盘失败")):
            with self.assertRaises(OSError):
                self.run_split([{"name": "甲", "pages": [1]}])
        self.assertFalse((self.root / "输出").exists())

    def test_encrypted_input_has_actionable_error(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt("synthetic-password")
        writer.write(str(self.src))
        with self.assertRaisesRegex(ValueError, "已加密"):
            mod.split(self.src, [{"name": "甲", "pages": [1]}], self.root / "输出")
        self.assertFalse((self.root / "输出").exists())


if __name__ == "__main__":
    unittest.main()
