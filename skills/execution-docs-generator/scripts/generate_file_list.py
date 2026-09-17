# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""
执行文书文件清单及盖章指引生成脚本
读取 references/文件清单及盖章指引模板.md 中的表格（支持多个 ## 小节，每个小节一个表格），
生成 Word (.docx) 版文件清单。格式与执行文书一致：宋体标题、仿宋正文、A4 页面、实线表格。

份数规则（执行案件）：固定「交法院 1 份 + 自留 1 份」= 2 份；
授权委托书（律所备用版）仅自留 1 份；委托代理合同双方各执 1 份。
份数写死在模板 md 中，本脚本不按当事人人数浮动。

用法：
  python3 scripts/generate_file_list.py references/文件清单及盖章指引模板.md \
    "执行文书_[申请人简称]_[日期]/00-文件清单及盖章指引.docx" \
    --case "案件：[申请人]与[被执行人][案由]执行案"
"""
import re, sys, os, argparse
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


def parse_sections(md_path):
    """解析 markdown 为 [(小节标题, 表格rows), ...]；小节以 ## 开头，其后紧跟一个 | 表格"""
    sections = []
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    cur_title = ""
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("## "):
            cur_title = s[3:].strip()
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            sections.append((cur_title, rows))
            cur_title = ""
            continue
        i += 1
    return sections


def set_font(run, name, size, bold=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold


def set_solid_borders(table):
    """设置表格为实线边框（single），替代 python-docx 默认的虚线/无边框"""
    from docx.oxml import OxmlElement
    tbl = table._tbl
    tblPr = tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "8")      # 1pt
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def render(md_path, out_path, case_line=""):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(3), Cm(2.5)
    section.left_margin, section.right_margin = Cm(3), Cm(2.5)

    # 标题
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    set_font(p.add_run("文件清单（打印份数 + 盖章指引）"), "宋体", 18, bold=True)

    # 案件信息行（如有）
    if case_line:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.5
        set_font(p.add_run(case_line), "仿宋", 14)

    # 说明
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    set_font(p.add_run("打印时按本清单份数准备，备注列标「签章」的位置需签字/盖章。"
                       "自留规则：除委托代理合同双方各执一份外，其余全部材料一律按「交法院 1 份 + 自留 1 份」准备，"
                       "自留件用于卷宗存档与后续跟进。"), "仿宋", 14)

    # 各小节表格
    sections = parse_sections(md_path)
    for title, rows in sections:
        if title:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            set_font(p.add_run(title), "宋体", 14, bold=True)
        if not rows:
            continue
        table = doc.add_table(rows=len(rows), cols=len(rows[0]))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_solid_borders(table)
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                cell = table.cell(ri, ci)
                cell.text = ""
                para = cell.paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                is_header = (ri == 0)
                set_font(para.add_run(val), "宋体" if is_header else "仿宋", 12, bold=is_header)

    doc.save(out_path)
    print(f"✅ {out_path}")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("template", help="模板 .md 路径")
    ap.add_argument("output", help="输出 .docx 路径")
    ap.add_argument("--case", default="", help="案件信息行（可选）")
    args = ap.parse_args()
    render(args.template, args.output, args.case)
