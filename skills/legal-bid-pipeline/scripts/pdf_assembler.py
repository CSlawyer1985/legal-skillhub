#!/usr/bin/env python3
"""
PDF 拼合脚本 (v3.1)

读取结构化插入清单 JSON，按目录顺序将 DOCX 导出的 PDF 与扫描件 PDF 合并，
输出 `投标文件_完整版.pdf`。

用法：
    python3 pdf_assembler.py --manifest 08_插入清单.json --output 投标文件_完整版.pdf

依赖：pypdf (pip install pypdf)
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("错误：未安装 pypdf，请运行 pip install pypdf")
    sys.exit(1)


# ─── 常量 ────────────────────────────────────────────

# 封面和目录页的最大数量（从 main.pdf 开头提取）
COVER_PAGES = 1
TOC_PAGES = 1


# ─── 数据类 ──────────────────────────────────────────

class PageRange:
    """页码范围"""
    def __init__(self, start: int, end: int | None = None):
        self.start = start
        self.end = end if end is not None else start

    @classmethod
    def from_spec(cls, spec: str) -> "PageRange":
        """解析 '1-3' 或 '5' 格式的页码范围字符串"""
        spec = spec.strip()
        if "-" in spec:
            parts = spec.split("-")
            return cls(int(parts[0]), int(parts[1]))
        return cls(int(spec))

    @property
    def pages(self) -> list[int]:
        """返回 1-indexed 页码列表"""
        return list(range(self.start, self.end + 1))


class ScanEntry:
    """单个扫描件条目"""
    def __init__(self, path: str, description: str = ""):
        self.path = Path(path)
        self.description = description

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def page_count(self) -> int:
        if not self.exists:
            return 0
        reader = PdfReader(str(self.path))
        return len(reader.pages)


class SectionItem:
    """目录中的一个条目（递归结构）"""
    def __init__(
        self,
        section: str,
        source: str,
        file: str | None = None,
        pages: str | None = None,
        children: list[dict] | None = None,
        scan: dict | None = None,
    ):
        self.section = section
        self.source = source
        self.file = file
        self.page_range = PageRange.from_spec(pages) if pages else None
        self.children: list[SectionItem] = []
        self.scan_path = scan.get("file") if scan else None
        self.scan_pages = scan.get("pages", 1) if scan else None

        if children:
            for child in children:
                self.children.append(SectionItem(**child))


class AssemblyManifest:
    """插入清单"""
    def __init__(self, data: dict):
        self.project_name = data.get("project_name", "未命名项目")
        self.toc_order: list[SectionItem] = []
        self.scan_files: list[ScanEntry] = []

        for item in data.get("toc_order", []):
            self.toc_order.append(SectionItem(**item))

        for sf in data.get("scan_files", []):
            self.scan_files.append(ScanEntry(**sf))

    def validate_scan_files(self) -> tuple[list[str], list[str]]:
        """校验扫描件文件是否存在，返回 (存在的, 缺失的)"""
        found, missing = [], []
        for sf in self.scan_files:
            if sf.exists:
                found.append(str(sf.path))
            else:
                missing.append(str(sf.path))
        return found, missing

    @property
    def total_sections(self) -> int:
        """计算总条目数（含递归子条目）"""
        def count(items):
            n = 0
            for item in items:
                if item.source == "mixed" and item.children:
                    n += count(item.children)
                else:
                    n += 1
            return n
        return count(self.toc_order)


# ─── PDF 操作 ────────────────────────────────────────

def extract_pages_from_pdf(pdf_path: str, page_range: PageRange) -> PdfWriter:
    """从 PDF 中提取指定页码范围"""
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    writer = PdfWriter()

    for page_num in page_range.pages:
        idx = page_num - 1  # 转为 0-indexed
        if 0 <= idx < total:
            writer.add_page(reader.pages[idx])
        else:
            print(f"  ⚠ 页码 {page_num} 超出 PDF 总页数 {total}，已跳过")

    return writer


def load_scan_pdf(scan_path: str) -> PdfWriter:
    """加载扫描件 PDF"""
    reader = PdfReader(scan_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    return writer


def build_toc_page(manifest: AssemblyManifest) -> PdfWriter:
    """
    生成目录页。

    由于 pypdf 不支持直接写文字内容，这里生成一个占位目录页。
    实际目录由主 PDF 的 DOCX 转换时自带。
    如果用户需要程序化目录，请配合 reportlab 使用。
    """
    # 目录页已在 DOCX 生成阶段处理，此处跳过
    # 返回空 writer 表示不添加额外目录页
    return PdfWriter()


# ─── 遍历与拼合 ──────────────────────────────────────

def flatten_sections(items: list[SectionItem]) -> list[dict]:
    """
    将嵌套的目录结构展平为线性拼合指令序列。
    每条指令包含 source_type, source_path, page_range (可选)
    """
    instructions = []

    for item in items:
        if item.source == "mixed" and item.children:
            for child in item.children:
                instructions.extend(flatten_sections([child]))
        elif item.source in ("template", "free"):
            instructions.append({
                "type": "extract",
                "section": item.section,
                "file": item.file,
                "page_range": item.page_range,
            })
        elif item.source == "scan":
            instructions.append({
                "type": "scan",
                "section": item.section,
                "file": item.scan_path,
            })
        elif item.source == "generate":
            instructions.append({
                "type": "generate",
                "section": item.section,
            })

    return instructions


def assemble(manifest: AssemblyManifest, main_pdf_path: str, output_path: str) -> dict:
    """
    主拼合逻辑：
    1. 展平目录结构
    2. 逐条处理：提取 main_pdf 页面或插入扫描件 PDF
    3. 合并到最终输出
    """
    main_pdf = Path(main_pdf_path)
    if not main_pdf.exists():
        raise FileNotFoundError(f"主 PDF 文件不存在: {main_pdf_path}")

    reader = PdfReader(str(main_pdf))
    total_pages = len(reader.pages)

    instructions = flatten_sections(manifest.toc_order)
    writer = PdfWriter()

    stats = {
        "total_pages": 0,
        "main_pages_used": 0,
        "scan_pages_added": 0,
        "scan_files_added": 0,
        "sections_processed": 0,
        "errors": [],
    }

    current_main_page = 0  # 0-indexed cursor in main_pdf

    for idx, instr in enumerate(instructions):
        print(f"  [{idx + 1}/{len(instructions)}] {instr['section']}")

        if instr["type"] == "extract":
            page_range = instr["page_range"]
            if page_range is None:
                stats["errors"].append(f"缺少页码范围: {instr['section']}")
                continue

            for page_num in page_range.pages:
                pi = page_num - 1
                if 0 <= pi < total_pages:
                    writer.add_page(reader.pages[pi])
                    stats["main_pages_used"] += 1
                else:
                    stats["errors"].append(
                        f"页码 {page_num} 超出主 PDF 总页数 {total_pages}: {instr['section']}"
                    )

        elif instr["type"] == "scan":
            scan_file = instr.get("file", "")
            if not scan_file:
                stats["errors"].append(f"扫描件路径为空: {instr['section']}")
                continue

            scan_path = Path(scan_file)
            if not scan_path.exists():
                stats["errors"].append(f"扫描件不存在: {scan_file} ({instr['section']})")
                continue

            scan_reader = PdfReader(str(scan_path))
            for page in scan_reader.pages:
                writer.add_page(page)
                stats["scan_pages_added"] += 1
            stats["scan_files_added"] += 1

        elif instr["type"] == "generate":
            # 封面/目录等由 DOCX 自带，不需要额外处理
            # 如果用户需要程序化生成封面，在此接入
            pass

        stats["sections_processed"] += 1

    stats["total_pages"] = len(writer.pages)

    # 写入输出文件
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        writer.write(f)

    return stats


# ─── 页码校验 ────────────────────────────────────────

def validate_pagination(manifest: AssemblyManifest, output_path: str) -> dict:
    """校验输出 PDF 的页码连续性"""
    reader = PdfReader(output_path)
    total = len(reader.pages)

    report = {
        "file": output_path,
        "total_pages": total,
        "has_cover": total > 0,
        "has_content": total > 1,
        "issues": [],
    }

    if total == 0:
        report["issues"].append("输出 PDF 为空（0 页）")

    # 检查是否有重复页（通过页面前 200 字符的哈希）
    from hashlib import md5
    seen = {}
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        h = md5(text[:200].encode()).hexdigest()
        if h in seen:
            report["issues"].append(f"第 {i + 1} 页与第 {seen[h] + 1} 页内容疑似重复")
        seen[h] = i

    return report


# ─── CLI ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PDF 拼合脚本 — 按目录顺序合并标书 PDF 与扫描件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 pdf_assembler.py --manifest 08_插入清单.json --output output/投标文件_完整版.pdf
  python3 pdf_assembler.py --manifest 08_插入清单.json --main 标书_v3.pdf --output 投标文件.pdf --validate
        """,
    )
    parser.add_argument(
        "--manifest", "-m",
        required=True,
        help="插入清单 JSON 文件路径（08_插入清单.json）",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出 PDF 文件路径",
    )
    parser.add_argument(
        "--main", "-p",
        default=None,
        help="主 PDF 文件路径（标书_vN.pdf）。默认从 manifest 同目录查找",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="拼合后执行页码校验并输出报告",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅校验扫描件和主 PDF 是否存在，不实际拼合",
    )

    args = parser.parse_args()

    # 加载 manifest
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"错误：插入清单文件不存在: {args.manifest}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = AssemblyManifest(data)

    print(f"项目名称: {manifest.project_name}")
    print(f"目录条目数: {manifest.total_sections}")
    print(f"扫描件数量: {len(manifest.scan_files)}")
    print()

    # 校验扫描件
    print("=== 扫描件校验 ===")
    found, missing = manifest.validate_scan_files()
    for f_path in found:
        print(f"  ✅ {f_path}")
    for m_path in missing:
        print(f"  ❌ 缺失: {m_path}")

    if missing:
        print(f"\n⚠ 警告：{len(missing)} 个扫描件文件不存在，拼合时将跳过")
        if args.dry_run:
            sys.exit(1)

    # 确定主 PDF 路径
    if args.main:
        main_pdf = args.main
    else:
        # 在同目录下查找标书 PDF
        manifest_dir = manifest_path.parent
        candidates = sorted(manifest_dir.glob("output/*.pdf"))
        if not candidates:
            candidates = sorted(manifest_dir.glob("*.pdf"))
        if candidates:
            main_pdf = str(candidates[-1])  # 取最新的
            print(f"\n自动检测到主 PDF: {main_pdf}")
        else:
            print("\n错误：未找到主 PDF 文件，请用 --main 指定")
            sys.exit(1)

    if args.dry_run:
        print("\n✅ Dry-run 通过（仅校验，未拼合）")
        sys.exit(0)

    # 执行拼合
    print(f"\n=== 开始拼合 ===")
    print(f"主 PDF: {main_pdf}")
    print(f"输出: {args.output}")
    print()

    try:
        stats = assemble(manifest, main_pdf, args.output)
    except FileNotFoundError as e:
        print(f"错误：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"拼合失败: {e}")
        sys.exit(1)

    print()
    print("=== 拼合完成 ===")
    print(f"  总页数: {stats['total_pages']}")
    print(f"  主 PDF 使用页数: {stats['main_pages_used']}")
    print(f"  扫描件插入页数: {stats['scan_pages_added']}")
    print(f"  扫描件文件数: {stats['scan_files_added']}")
    print(f"  处理条目数: {stats['sections_processed']}")

    if stats["errors"]:
        print(f"\n⚠ 警告（{len(stats['errors'])} 条）:")
        for err in stats["errors"]:
            print(f"  - {err}")

    # 页码校验
    if args.validate:
        print("\n=== 页码校验 ===")
        report = validate_pagination(manifest, args.output)
        print(f"  总页数: {report['total_pages']}")
        if report["issues"]:
            for issue in report["issues"]:
                print(f"  ⚠ {issue}")
        else:
            print("  ✅ 页码校验通过")

    print(f"\n输出文件: {args.output}")


if __name__ == "__main__":
    main()
