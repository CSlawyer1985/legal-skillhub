# -*- coding: utf-8 -*-
"""参数驱动的 Word 表格构建器（扫描件复刻用）。

设计立场：**本脚本不猜任何参数。** 字体/字号/列宽/行高/边距一律由调用方（JSON spec）
给出——参数从哪来（原件，还是像素反推）由人决定，脚本只负责"把给定参数正确地写进 OOXML"。

这样拆开是因为 2026-09-12 的教训：律协《附件3》一案，**构建环节零缺陷，
20 项错 16 项全部出自"参数获取与判断"**。所以技能该把力气花在参数验证上，构建交本脚本。

用法：
    python3 build_table_docx.py spec.json [-o out.docx]

spec 结构见 references/table-spec-律协附件3.json（唯一经原件核对的样例）。

═══ OOXML 子元素顺序（ECMA-376 强制，写错会被渲染器静默忽略）═══
本脚本按规范顺序插入，**不要改成无序 append 图省事**：
  w:tblPr : tblW → jc → tblCellSpacing → tblInd → tblBorders → shd
            → tblLayout → tblCellMar → tblLook
  w:pPr   : tabs → kinsoku → wordWrap → autoSpaceDE → autoSpaceDN
            → spacing → ind → jc → rPr
  w:rPr   : rFonts → w(字符缩放) → sz
  w:tcPr  : tcW → noWrap → vAlign → textDirection → tcFitText
"""
import argparse
import json
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

TBL_ALIGN = {"left": WD_TABLE_ALIGNMENT.LEFT,
             "center": WD_TABLE_ALIGNMENT.CENTER,
             "right": WD_TABLE_ALIGNMENT.RIGHT}


def el(tag, attrs=None):
    e = OxmlElement(tag)
    for k, v in (attrs or {}).items():
        e.set(qn(f"w:{k}"), str(v))
    return e


def tw(pt):
    """pt → twips（OOXML 里的 1/20 pt）"""
    return int(round(pt * 20))


# ── run：rPr 顺序 rFonts → w → sz ──────────────────────────────────────────
def set_run(run, spec):
    rPr = run._element.get_or_add_rPr()
    f = spec.get("font", {})
    asc = f.get("ascii") or f.get("ea", "")
    rPr.append(el("w:rFonts", {"ascii": asc, "hAnsi": asc,
                               "eastAsia": f.get("ea", ""), "cs": f.get("ea", "")}))
    if spec.get("scale") and spec["scale"] != 100:
        rPr.append(el("w:w", {"val": spec["scale"]}))
    if spec.get("size"):
        half = int(round(spec["size"] * 2))
        rPr.append(el("w:sz", {"val": half}))
        rPr.append(el("w:szCs", {"val": half}))
    return run


# ── 段落：pPr 顺序 tabs → kinsoku/wordWrap/autoSpace → spacing → ind → jc ──
def set_par(p, spec):
    pPr = p._element.get_or_add_pPr()
    for c in list(pPr):
        pPr.remove(c)
    if spec.get("tab_right"):
        tabs = el("w:tabs")
        tabs.append(el("w:tab", {"val": "right", "pos": tw(spec["tab_right"])}))
        pPr.append(tabs)
    for tag in ("w:kinsoku", "w:wordWrap", "w:autoSpaceDE", "w:autoSpaceDN"):
        pPr.append(el(tag, {"val": 0}))
    line = spec.get("line")
    pPr.append(el("w:spacing", {
        "before": tw(spec.get("before", 0) or 0),
        "after": tw(spec.get("after", 0) or 0),
        "line": int(line) if line else 240,
        "lineRule": "exact" if line else "auto"}))
    ind = {}
    if spec.get("left"):
        ind["left"] = tw(spec["left"])
    if spec.get("right"):
        ind["right"] = tw(spec["right"])
    if spec.get("first_line"):
        ind["firstLine"] = tw(spec["first_line"])
    if ind:
        pPr.append(el("w:ind", ind))
    if spec.get("align"):
        pPr.append(el("w:jc", {"val": spec["align"]}))
    return p


def add_par(container, spec, is_footer=False):
    p = (container.paragraphs[0] if is_footer else container.add_paragraph())
    set_par(p, spec)
    set_run(p.add_run(spec.get("text", "")), spec)
    return p


# ── 表格 ───────────────────────────────────────────────────────────────────
def build_table(doc, spec):
    row_specs, cols = spec["rows"], spec["cols"]
    tb = doc.add_table(rows=len(row_specs), cols=len(cols))
    tb.autofit = False

    tblPr = tb._tbl.tblPr
    for c in list(tblPr):
        tblPr.remove(c)
    tblPr.append(el("w:tblW", {"w": sum(cols), "type": "dxa"}))
    tblPr.append(el("w:jc", {"val": spec.get("align", "center")}))
    if spec.get("indent_twips"):
        tblPr.append(el("w:tblInd", {"w": spec["indent_twips"], "type": "dxa"}))
    bd = el("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        bd.append(el(f"w:{edge}", {"val": "single",
                                   "sz": spec.get("border_sz", 4),
                                   "space": 0, "color": "auto"}))
    tblPr.append(bd)
    tblPr.append(el("w:tblLayout", {"type": "fixed"}))
    mar = el("w:tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        w = spec.get("cell_margin", 108) if side in ("left", "right") else 0
        mar.append(el(f"w:{side}", {"w": w, "type": "dxa"}))
    tblPr.append(mar)
    tblPr.append(el("w:tblLook", {"val": "04A0", "firstRow": 1, "lastRow": 0,
                                 "firstColumn": 1, "lastColumn": 0,
                                 "noHBand": 0, "noVBand": 1}))

    grid = tb._tbl.find(qn("w:tblGrid"))
    for gc, w in zip(grid.findall(qn("w:gridCol")), cols):
        gc.set(qn("w:w"), str(w))

    for ri, row in enumerate(tb.rows):
        rs = row_specs[ri]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(el("w:trHeight", {"val": rs["h"],
                                      "hRule": rs.get("rule", "exact")}))
        trPr.append(el("w:jc", {"val": rs.get("align", "center")}))
        cells = rs.get("cells") or [{} for _ in cols]
        for ci, cell in enumerate(row.cells):
            cs = cells[ci] if ci < len(cells) else {}
            tcPr = cell._tc.get_or_add_tcPr()
            tcPr.append(el("w:tcW", {"w": cols[ci], "type": "dxa"}))
            tcPr.append(el("w:noWrap", {"val": 0}))
            tcPr.append(el("w:vAlign", {"val": cs.get("valign", "center")}))
            set_par(cell.paragraphs[0], {"align": cs.get("align", "center"),
                                         "line": cs.get("line", 240)})
            set_run(cell.paragraphs[0].add_run(cs.get("text", "")), cs)
    return tb


# ── 文档 ───────────────────────────────────────────────────────────────────
def build(spec, out):
    doc = Document()
    d = spec.get("default_font", {})
    st = doc.styles["Normal"]
    st.font.name = d.get("ascii", "Times New Roman")
    st.font.size = Pt(d.get("size", 14))
    st._element.rPr.rFonts.set(qn("w:eastAsia"), d.get("ea", "宋体"))

    s = doc.sections[0]
    pg, mg = spec["page"], spec["page"]["margin"]
    s.page_width, s.page_height = Pt(pg["w"]), Pt(pg["h"])
    s.top_margin, s.bottom_margin = Pt(mg["top"]), Pt(mg["bottom"])
    s.left_margin, s.right_margin = Pt(mg["left"]), Pt(mg["right"])
    if pg.get("footer"):
        s.footer_distance = Pt(pg["footer"])
    # 文档网格：**照抄原件，别删**。
    # 2026-09-12 反证实测：原件 docGrid linePitch=312（15.6pt），我按旧规则删掉后，
    # 没有显式行距的段落（如标题）行高变了，表格整体上移 36.5pt。
    # 正确规则：①有原件就照抄 docGrid；②否则给**每一段**都设显式 line+lineRule=exact
    # （exact 覆盖网格，删不删都一样）；③绝不能"删网格 + 留几段没有显式行距"。
    for g in s._sectPr.findall(qn("w:docGrid")):
        s._sectPr.remove(g)
    dg = spec.get("doc_grid") or pg.get("doc_grid")   # 兼容两种放法
    if dg:
        s._sectPr.append(el("w:docGrid", {"type": dg.get("type", "lines"),
                                          "linePitch": dg.get("linePitch", 312),
                                          "charSpace": dg.get("charSpace", 0)}))

    for item in spec.get("body", []):
        if item["kind"] == "p":
            add_par(doc, item)
        elif item["kind"] == "table":
            build_table(doc, item)
        else:
            sys.exit(f"未知 body.kind: {item['kind']}")

    for fp in spec.get("footer_paras", []):
        add_par(doc.sections[0].footer, fp, is_footer=True)

    doc.save(out)
    print(f"✔ 已生成 {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    build(spec, a.out or spec.get("out", "out.docx"))
