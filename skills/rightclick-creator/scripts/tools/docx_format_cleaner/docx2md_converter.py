#!/usr/bin/env python3
"""
Word 文档转 Markdown 工具
- 支持修订模式：自动接受所有修订，提取最终文本
- 输出 MD 文件到同一文件夹
- 通用版：动态探测 pandoc 路径，不依赖任何硬编码
"""

import sys
import os
import subprocess
import shutil
import tempfile
from pathlib import Path


def _find_pandoc() -> str:
    """动态探测 pandoc 路径，兼容 Apple Silicon 和 Intel Mac"""
    candidates = [
        "/opt/homebrew/bin/pandoc",                    # Apple Silicon Homebrew
        "/usr/local/bin/pandoc",                        # Intel Mac Homebrew
        str(Path.home() / ".rightclick-creator" / "bin" / "pandoc"),  # 技能本地安装
        "/usr/bin/pandoc",                              # 系统自带（极少见）
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    # 尝试 PATH 中的 pandoc
    found = shutil.which("pandoc")
    if found:
        return found
    raise RuntimeError(
        "未找到 pandoc。请先安装：brew install pandoc"
    )


def accept_revisions_and_convert(docx_path: str) -> str:
    """
    接受 Word 文档中的所有修订，并转换为 Markdown。
    返回输出的 MD 文件路径。
    """
    src = Path(docx_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"文件不存在: {src}")

    out_md = src.with_suffix(".md")
    pandoc = _find_pandoc()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_docx = Path(tmpdir) / src.name
        shutil.copy2(str(src), str(tmp_docx))

        # 用 python-docx + lxml 接受所有修订
        _accept_all_revisions(str(tmp_docx))

        result = subprocess.run(
            [
                pandoc,
                str(tmp_docx),
                "-f", "docx",
                "-t", "markdown-simple_tables-grid_tables-multiline_tables",
                "--wrap=none",
                "-o", str(out_md),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"pandoc 转换失败:\n{result.stderr}")

    return str(out_md)


def _accept_all_revisions(docx_path: str):
    """
    通过直接操作 XML，接受 docx 中的所有修订（插入/删除/格式变更）。
      - w:ins  → 保留其内部文本，移除标签本身
      - w:del  → 整体删除（包括内部文本）
      - w:rPrChange / w:pPrChange → 移除（保留当前格式）
    """
    from docx import Document

    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    doc = Document(docx_path)
    body = doc.element.body

    for ins in body.findall(f".//{{{W}}}ins"):
        parent = ins.getparent()
        if parent is None:
            continue
        idx = list(parent).index(ins)
        for child in list(ins):
            parent.insert(idx, child)
            idx += 1
        parent.remove(ins)

    for del_elem in body.findall(f".//{{{W}}}del"):
        parent = del_elem.getparent()
        if parent is not None:
            parent.remove(del_elem)

    for tag in ["rPrChange", "pPrChange"]:
        for elem in body.findall(f".//{{{W}}}{tag}"):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    doc.save(docx_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 docx2md_converter.py <文件1.docx> [文件2.docx ...]")
        sys.exit(1)

    for path in sys.argv[1:]:
        try:
            out = accept_revisions_and_convert(path)
            print(f"✅ 已生成: {out}")
        except Exception as e:
            print(f"❌ 处理失败 [{path}]: {e}", file=sys.stderr)
            sys.exit(1)
