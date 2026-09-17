#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""
页码与分节自动配置 (Setup Pagination) — 合稿阶段必做动作的脚本化

来源：references/docx_engineering.md 第十一节。把原本内嵌在文档里的代码
抽成独立脚本，让合稿阶段直接调用，而不是每次临场复制粘贴。

三节结构与编号规则：
    ┌──────────┐  ┌──────────┐  ┌──────────────────┐
    │  节1 封面 │→│  节2 目录 │→│  节3 正文（及后续）│
    │  titlePg  │  │  独立序列  │  │  从1重新编号       │
    │  无页码    │  │  1,2,3…   │  │  1,2,3…           │
    └──────────┘  └──────────┘  └──────────────────┘

用法（CLI）:
    # 对已合稿的 docx 配置页码（原地修改或输出新文件）
    python setup_pagination.py 标书_v1.docx
    python setup_pagination.py 标书_v1.docx --output 标书_v1_paged.docx
    python setup_pagination.py 标书_v1.docx --dry-run    # 只报告节数与计划动作，不写文件

用法（Python API）:
    from setup_pagination import setup_page_numbers
    from docx import Document
    doc = Document("标书_v1.docx")
    setup_page_numbers(doc)
    doc.save("标书_v1.docx")

前提：doc 中已有分节符分隔封面/目录/正文（至少 2 个分节符 = 3 节）。
若不足 3 节，按实际节数降级处理并打印警告。
"""

import argparse
import sys

from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_page_field(paragraph):
    """在段落中插入 PAGE 域（当前页码），字体宋体小五居中。"""
    run = paragraph.add_run()
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = ' PAGE \\* MERGEFORMAT '
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    # 字体：宋体小五
    run.font.size = Pt(10.5)
    run.font.name = '宋体'
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), '宋体')
    rFonts.set(qn('w:ascii'), '宋体')
    rFonts.set(qn('w:hAnsi'), '宋体')


def setup_page_numbers(doc, verbose=True):
    """
    为投标文档配置三节式页码。合稿脚本末尾、保存前调用。

    参数：
        doc: python-docx Document 对象
        verbose: 是否打印处理过程

    前提：doc 中已有分节符分隔封面/目录/正文（至少 2 个分节符 = 3 节）。
    若不足 3 节，按实际节数降级处理并打印警告。
    """
    def _log(msg):
        if verbose:
            print(msg)

    sections = doc.sections
    n = len(sections)

    if n < 2:
        _log("⚠ 文档不足 2 个分节符，跳过页码配置。请先插入分节符分隔封面/目录/正文。")
        return False

    _log(f"▶ 文档共 {n} 节，开始配置页码")

    # ── 节1：封面 ──
    cover = sections[0]
    cover.different_first_page_header_footer = True  # titlePg，首页页脚留空

    # 封面默认页脚也清空（防止继承）
    cover.footer.is_linked_to_previous = False
    for p in cover.footer.paragraphs:
        for r in p.runs:
            r.text = ''
    _log("  ✓ 节1（封面）：titlePg 启用，页脚清空")

    # ── 节2：目录（若存在独立目录节） ──
    if n >= 3:
        _config_section_pages(sections[1], start=1, label="节2（目录）", verbose=verbose)
        # ── 节3+：正文 ──
        for i in range(2, n):
            _config_section_pages(sections[i], start=1 if i == 2 else None,
                                   label=f"节{i + 1}（正文）" if i == 2 else f"节{i + 1}",
                                   verbose=verbose)
    elif n == 2:
        # 只有封面 + 正文（无独立目录节）
        _config_section_pages(sections[1], start=1, label="节2（正文，无独立目录节）", verbose=verbose)

    _log("▶ 页码配置完成")
    return True


def _config_section_pages(section, start=None, label="", verbose=True):
    """配置某个节的页码：断开链接 → 页脚居中插 PAGE 域 → 设置起始页。"""
    def _log(msg):
        if verbose:
            print(msg)

    # 取消首页不同（防止继承封面的 titlePg）
    section.different_first_page_header_footer = False

    # 断开与上一节的页脚链接
    footer = section.footer
    footer.is_linked_to_previous = False

    # 清空已有页脚内容，插入居中 PAGE 域
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in para.runs:
        r.text = ''
    add_page_field(para)

    # 设置页码起始值
    if start is not None:
        sectPr = section._sectPr
        pgNumType = sectPr.find(qn('w:pgNumType'))
        if pgNumType is None:
            pgNumType = OxmlElement('w:pgNumType')
            sectPr.append(pgNumType)
        pgNumType.set(qn('w:start'), str(start))
        _log(f"  ✓ {label}：页脚 PAGE 域 + 起始页 {start}")
    else:
        _log(f"  ✓ {label}：页脚 PAGE 域（继承上一节编号）")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="为已合稿的 docx 配置三节式页码（合稿阶段必做）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("docx_path", help="待处理的 .docx 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径（默认原地修改）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只报告节数与计划动作，不写文件")
    args = parser.parse_args(argv)

    from docx import Document
    doc = Document(args.docx_path)

    if args.dry_run:
        sections = doc.sections
        print(f"▶ dry-run：文档共 {len(sections)} 节")
        print(f"  计划动作：")
        if len(sections) < 2:
            print("    ⚠ 节数不足 2，无法配置（需要封面/正文至少分节）")
        else:
            print("    - 节1（封面）：启用 titlePg，页脚清空")
            if len(sections) >= 3:
                print("    - 节2（目录）：断开链接，页脚插入 PAGE 域，start=1")
                print("    - 节3+（正文）：断开链接，页脚插入 PAGE 域，start=1")
            else:
                print("    - 节2（正文，无独立目录节）：断开链接，页脚插入 PAGE 域，start=1")
        print("▶ dry-run 完成，未写入文件")
        return 0

    ok = setup_page_numbers(doc)
    if ok:
        out_path = args.output or args.docx_path
        doc.save(out_path)
        print(f"▶ 已保存到：{out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
