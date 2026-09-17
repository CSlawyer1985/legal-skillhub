#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正式文书排版转换脚本（md2docx_formal.py）。

功能：把 Markdown 母版按附录 A 排版参数生成 .docx，与母版同名输出——
  · 正文：仿宋、三号（16pt）、行距固定值 28 磅、两端对齐、首行缩进 2 字符、
    段前段后 0、纯黑不加粗；
  · 西文（含数字）：Times New Roman；中文字体：仿宋（东亚字体）；
  · 标题：一级黑体、二级楷体、三级四级字号同正文（三号），统一纯黑不加粗；
  · 页面边距：上下 25.4mm、左右 31.8mm；表格为实线边框。

依赖 python-docx（本脚本为例外，允许第三方依赖）。缺失时报错并给出安装指引，
**禁止静默降级为纯文本输出**。

调用方式：
  python scripts/md2docx_formal.py --md 03_正式文书/xxx_辩护人.md
  python scripts/md2docx_formal.py --md 03_正式文书/ --out 04_正式文书（word版）/

统一接口规范：
  - 支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2路径缺失 / 3转换失败；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO / ERR_DEP_MISSING。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "md2docx_formal"

INSTALL_GUIDE = ("未安装 python-docx，本脚本不可用。安装：pip install python-docx "
                 "（或 python -m pip install python-docx）。依赖缺失时禁止静默降级。")

# 附录 A 排版参数
BODY_FONT_CN = "仿宋"
BODY_FONT_EN = "Times New Roman"
BODY_SIZE_PT = 16          # 三号
LINE_SPACING_PT = 28       # 固定行距 28 磅
MARGIN_TOP_BOTTOM_MM = 25.4
MARGIN_LEFT_RIGHT_MM = 31.8
HEAD_FONTS = {1: "黑体", 2: "楷体", 3: BODY_FONT_CN, 4: BODY_FONT_CN}


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def require_docx(tid):
    try:
        import docx  # noqa: F401
    except ImportError:
        emit(envelope("error", "ERR_DEP_MISSING", INSTALL_GUIDE,
                      {"trace_id": tid, "dependency": "python-docx"}), 3)
    try:
        import docx
        from docx.shared import Pt
        _ = Pt(12)
        return docx
    except Exception as exc:
        emit(envelope("error", "ERR_DEP_MISSING",
                      "python-docx 导入异常：%s。%s" % (exc, INSTALL_GUIDE),
                      {"trace_id": tid}), 3)


def parse_md(text):
    """极简 Markdown 解析：标题／段落／无序列表／有序列表／引用／表格／分隔线。"""
    blocks, table = [], []
    for raw in text.split("\n"):
        line = raw.rstrip()
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        if table:
            blocks.append(("table", table)); table = []
        if not line.strip():
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            blocks.append(("heading", (len(m.group(1)), m.group(2).strip())))
            continue
        if re.match(r"^\s*([-*+])\s+", line):
            blocks.append(("list", (False, re.sub(r"^\s*[-*+]\s+", "", line))))
            continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            blocks.append(("list", (True, re.sub(r"^\s*\d+[.)]\s+", "", line))))
            continue
        if line.lstrip().startswith(">"):
            blocks.append(("quote", line.lstrip()[1:].strip()))
            continue
        if re.match(r"^(-{3,}|\*{3,})$", line.strip()):
            blocks.append(("hr", ""))
            continue
        blocks.append(("para", line.strip()))
    if table:
        blocks.append(("table", table))
    return blocks


def strip_inline(s):
    """去除 Markdown 行内标记（**粗体**、*斜体*、`代码`）。"""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s.strip()


def convert(md_path, out_path, docx, tid):
    from docx.shared import Pt, Mm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml.ns import qn

    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    blocks = parse_md(text)

    doc = docx.Document()
    sec = doc.sections[0]
    sec.top_margin = Mm(MARGIN_TOP_BOTTOM_MM)
    sec.bottom_margin = Mm(MARGIN_TOP_BOTTOM_MM)
    sec.left_margin = Mm(MARGIN_LEFT_RIGHT_MM)
    sec.right_margin = Mm(MARGIN_LEFT_RIGHT_MM)

    style = doc.styles["Normal"]
    style.font.name = BODY_FONT_EN
    style.font.size = Pt(BODY_SIZE_PT)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.font.bold = False
    style.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT_CN)

    def fmt_run(run, font_cn=BODY_FONT_CN, size=BODY_SIZE_PT):
        run.font.name = BODY_FONT_EN
        run.font.size = Pt(size)
        run.font.bold = False
        run.font.color.rgb = RGBColor(0, 0, 0)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), font_cn)

    def set_para(p, indent=True, spacing=LINE_SPACING_PT):
        pf = p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(spacing)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        if indent:
            pf.first_line_indent = Pt(BODY_SIZE_PT * 2)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    n_para = n_head = n_table = 0
    for kind, payload in blocks:
        if kind == "heading":
            level, txt = payload
            p = doc.add_paragraph()
            set_para(p, indent=False)
            r = p.add_run(strip_inline(txt))
            fmt_run(r, font_cn=HEAD_FONTS.get(min(level, 4), BODY_FONT_CN))
            n_head += 1
        elif kind in ("para", "quote", "list"):
            txt = payload[1] if kind == "list" else payload
            if kind == "list":
                ordered, txt = payload
                txt = ("　　" if not ordered else "　　") + txt
            p = doc.add_paragraph()
            set_para(p)
            r = p.add_run(strip_inline(txt))
            fmt_run(r)
            n_para += 1
        elif kind == "table":
            rows = payload
            if not rows:
                continue
            ncols = max(len(r) for r in rows)
            t = doc.add_table(rows=0, cols=ncols)
            t.style = "Table Grid"
            for ri, row in enumerate(rows):
                cells = t.add_row().cells
                for ci in range(ncols):
                    val = row[ci] if ci < len(row) else ""
                    if ri == 1 and re.match(r"^[-: ]+$", val or ""):
                        continue
                    cells[ci].text = ""
                    p = cells[ci].paragraphs[0]
                    r = p.add_run(strip_inline(val))
                    fmt_run(r, size=14)
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
            n_table += 1

    doc.save(out_path)
    return {"paragraphs": n_para, "headings": n_head, "tables": n_table}


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="Markdown → 正式排版 docx（附录 A 参数）。")
    ap.add_argument("--md", required=True, help="md 母版文件或目录")
    ap.add_argument("--out", help="输出目录（缺省为母版同目录）")
    args = ap.parse_args()
    tid = make_trace_id()

    docx = require_docx(tid)

    if not os.path.exists(args.md):
        emit(envelope("error", "NOT_FOUND", "母版路径缺失：%s" % args.md,
                      {"trace_id": tid}), 2)

    if os.path.isfile(args.md):
        md_files = [args.md]
        out_dir = args.out or os.path.dirname(os.path.abspath(args.md))
    else:
        md_files = sorted(os.path.join(dp, fn)
                          for dp, _, fns in os.walk(args.md)
                          for fn in fns if fn.lower().endswith(".md"))
        out_dir = args.out or os.path.abspath(args.md)
        if not md_files:
            emit(envelope("error", "NOT_FOUND", "目录下无 .md 母版：%s" % args.md,
                          {"trace_id": tid}), 2)
    os.makedirs(out_dir, exist_ok=True)

    done, errors = [], []
    for md in md_files:
        out = os.path.join(out_dir, os.path.splitext(os.path.basename(md))[0] + ".docx")
        try:
            stats = convert(md, out, docx, tid)
        except Exception as exc:
            errors.append({"md": md, "error": str(exc)})
            continue
        done.append({"md": md, "docx": out, "size": os.path.getsize(out), **stats})

    if errors and not done:
        emit(envelope("error", "ERR_IO", "转换全部失败", {"trace_id": tid, "errors": errors}), 3)

    emit(envelope("ok" if not errors else "error", None if not errors else "INVALID",
                  "转换完成 %d 个，失败 %d 个" % (len(done), len(errors)),
                  {"trace_id": tid, "out_dir": out_dir, "converted": done, "errors": errors,
                   "typography": {"正文字体": BODY_FONT_CN, "字号pt": BODY_SIZE_PT,
                                  "行距pt": LINE_SPACING_PT,
                                  "边距mm": [MARGIN_TOP_BOTTOM_MM, MARGIN_LEFT_RIGHT_MM],
                                  "西文字体": BODY_FONT_EN, "表格": "Table Grid 实线"},
                   "note": "母版修改后须重新生成本 docx，防止母版与交付版脱节"}),
         0 if not errors else 1)


if __name__ == "__main__":
    main()
