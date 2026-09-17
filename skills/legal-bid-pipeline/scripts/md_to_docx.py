#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""
Markdown → DOCX 转换器 — v3.8.0 新增

轨道B 自由章节 Markdown→DOCX 转换的脚本化实现。
pandoc 做结构性转换 + python-docx 做后处理（宋体小四、1.5 倍行距、标题层级）。

用法：
    python md_to_docx.py chapter.md [chapter2.md ...] [选项]

    单文件：
    python md_to_docx.py 章节1_服务方案.md

    批量：
    python md_to_docx.py 章节1.md 章节2.md 章节3.md --output-dir ./output/

    自定义字体：
    python md_to_docx.py chapter.md --font "PingFang SC" --font-size 14

依赖：
    - pandoc (brew install pandoc)
    - python-docx (pip install python-docx)

选项：
    --output-dir, -d   输出目录（默认当前目录）
    --font             正文字体（默认：宋体）
    --font-size        正文字号 pt（默认：12，即小四）
    --line-spacing     行距倍数（默认：1.5）
"""

import argparse
import subprocess
import sys
import tempfile
import os
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt
    from docx.oxml.ns import qn
except ImportError:
    print("错误：需要 python-docx。pip install python-docx", file=sys.stderr)
    sys.exit(1)

FONT_NAME = "宋体"
FONT_SIZE = Pt(12)  # 小四
LINE_SPACING = 1.5


def _find_pandoc() -> str:
    """查找 pandoc 可执行文件。"""
    paths = [
        "/opt/homebrew/bin/pandoc",
        "/usr/local/bin/pandoc",
        "/usr/bin/pandoc",
    ]
    for p in paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    # 最后试 PATH
    try:
        result = subprocess.run(
            ["which", "pandoc"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _set_run_font(run, font_name, font_size):
    """设置 run 的中文字体（包含 eastAsia 属性）。"""
    run.font.name = font_name
    run.font.size = font_size
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        from docx.oxml import OxmlElement
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), font_name)
    rfonts.set(qn("w:ascii"), font_name)
    rfonts.set(qn("w:hAnsi"), font_name)


def post_process_docx(docx_path: str, font_name: str, font_size,
                      line_spacing: float):
    """对 pandoc 生成的 docx 进行中文排版后处理。"""
    doc = Document(docx_path)

    for para in doc.paragraphs:
        # 行距
        pf = para.paragraph_format
        if pf.line_spacing != line_spacing:
            pf.line_spacing = line_spacing

        # 字体
        for run in para.runs:
            _set_run_font(run, font_name, font_size)

    # 处理表格
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        _set_run_font(run, font_name, font_size)

    doc.save(docx_path)


def convert_one(md_path: str, output_dir: str, font_name: str,
                font_size, line_spacing: float) -> bool:
    """转换单个 markdown 文件。"""
    md_path = Path(md_path)
    if not md_path.exists():
        print(f"✗ 文件不存在：{md_path}", file=sys.stderr)
        return False
    if md_path.suffix.lower() != ".md":
        print(f"⚠ 非 .md 文件，跳过：{md_path}", file=sys.stderr)
        return False

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{md_path.stem}.docx"

    pandoc = _find_pandoc()
    if not pandoc:
        print("✗ pandoc 未安装。brew install pandoc", file=sys.stderr)
        return False

    # Step 1：pandoc 转换
    print(f"  📝 {md_path.name} → {output_path.name}")
    try:
        subprocess.run(
            [pandoc, str(md_path), "-o", str(output_path),
             "--from", "markdown", "--to", "docx"],
            check=True, capture_output=True, text=True, timeout=60,
        )
    except subprocess.CalledProcessError as e:
        print(f"✗ pandoc 转换失败：{e.stderr}", file=sys.stderr)
        return False

    # Step 2：python-docx 后处理
    try:
        post_process_docx(str(output_path), font_name, font_size, line_spacing)
        print(f"  ✅ {output_path}（{font_name} {font_size.pt}pt, "
              f"{line_spacing}× 行距）")
        return True
    except Exception as e:
        print(f"✗ 后处理失败：{e}", file=sys.stderr)
        return False


def self_check():
    """用样例 markdown 测试转换。"""
    import tempfile

    print("=== md_to_docx 自检 ===")

    pandoc = _find_pandoc()
    if not pandoc:
        print("  ❌ pandoc 未安装，无法自检")
        return False

    with tempfile.TemporaryDirectory() as d:
        md_path = os.path.join(d, "test.md")
        with open(md_path, "w") as f:
            f.write("# 测试标题\n\n这是正文。\n\n## 第二节\n\n表格测试：\n\n")
            f.write("| 列1 | 列2 |\n|-----|-----|\n| A | B |\n")

        ok = convert_one(md_path, d, "宋体", Pt(12), 1.5)
        if ok:
            docx_path = os.path.join(d, "test.docx")
            if os.path.exists(docx_path):
                doc = Document(docx_path)
                paras = len(doc.paragraphs)
                print(f"  ✅ 转换成功：{paras} 段，文件 {os.path.getsize(docx_path)} 字节")
                return True
        print("  ❌ 转换失败")
        return False


def main():
    if "--self-check" in sys.argv:
        ok = self_check()
        sys.exit(0 if ok else 1)

    parser = argparse.ArgumentParser(description="Markdown → DOCX 转换器")
    parser.add_argument("files", nargs="+", help="Markdown 文件路径（可多个）")
    parser.add_argument("--output-dir", "-d", default=".", help="输出目录")
    parser.add_argument("--font", default=FONT_NAME, help="正文字体")
    parser.add_argument("--font-size", type=float, default=12.0,
                        help="正文字号 pt（默认 12 = 小四）")
    parser.add_argument("--line-spacing", type=float, default=1.5,
                        help="行距倍数（默认 1.5）")

    args = parser.parse_args()

    font_size = Pt(args.font_size)
    success = 0
    fail = 0

    print(f"📄 Markdown → DOCX（{args.font} {args.font_size}pt, "
          f"{args.line_spacing}× 行距）")
    print("")

    for f in args.files:
        if convert_one(f, args.output_dir, args.font, font_size,
                       args.line_spacing):
            success += 1
        else:
            fail += 1

    print(f"\n完成：{success} 成功 · {fail} 失败")


if __name__ == "__main__":
    main()
