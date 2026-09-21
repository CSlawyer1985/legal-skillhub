#!/usr/bin/env python3
"""LaborPilot DOCX 的 JLS 版式修正与独立结构校验。

仅使用 Python 标准库修改 Pandoc 生成的 OOXML，不读取或输出知识卡数据。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tempfile
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from xml_safe import UnsafeXMLError, fromstring as safe_fromstring


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
NAMESPACES = {
    "w": W_NS,
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "cp": CP_NS,
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


PROFILE_ID = "jls-legal-docx-2026-08-06"
DELIVERY_STATUSES = {"lawyer_review_draft", "final_submission"}
DOCUMENT_TYPES = {"仲裁申请书", "证据清单", "行动清单"}
FONT_EAST_ASIA = "仿宋_GB2312"
FONT_RENDER_FALLBACK = "STFangsong"
FONT_LATIN = "Times New Roman"
LINE_TWIPS = "500"  # 25pt
BODY_SIZE = "28"  # 14pt
TITLE_SIZE = "36"  # 18pt
HEADING_SIZE = "30"  # 15pt
SMALL_SIZE = "24"  # 12pt
BODY_FIRST_LINE = "480"  # 24pt
SIGNATURE_START = "4080"  # 204pt
DATE_START = "4920"  # 246pt
PAGE_WIDTH = "11907"  # A4
PAGE_HEIGHT = "16839"
PAGE_MARGIN = "1440"
TABLE_WIDTH = 9000
FINAL_BLOCKED_MARKERS = ("【", "】", "待确认", "待核实", "待补充", "内部工作备注")


def w(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def ensure(parent: ET.Element, local: str, *, first: bool = False) -> ET.Element:
    element = parent.find(w(local))
    if element is None:
        element = ET.Element(w(local))
        if first:
            parent.insert(0, element)
        else:
            parent.append(element)
    return element


def set_w(element: ET.Element, key: str, value: str) -> None:
    element.set(w(key), value)


def remove_children(parent: ET.Element, *locals_: str) -> None:
    tags = {w(local) for local in locals_}
    for child in list(parent):
        if child.tag in tags:
            parent.remove(child)


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(w("t"))).strip()


def text_runs(paragraph: ET.Element) -> list[ET.Element]:
    return [
        run for run in paragraph.iter(w("r"))
        if any((node.text or "") for node in run.iter(w("t")))
    ]


def set_run_properties(rpr: ET.Element, size: str, *, bold: bool | None = None) -> None:
    fonts = ensure(rpr, "rFonts", first=True)
    fonts.attrib.clear()
    for key, value in (
        ("ascii", FONT_LATIN), ("hAnsi", FONT_LATIN),
        ("eastAsia", FONT_EAST_ASIA), ("cs", FONT_LATIN),
    ):
        set_w(fonts, key, value)
    for local in ("sz", "szCs"):
        set_w(ensure(rpr, local), "val", size)
    if bold is True:
        set_w(ensure(rpr, "b"), "val", "1")
        set_w(ensure(rpr, "bCs"), "val", "1")
    elif bold is False:
        remove_children(rpr, "b", "bCs")


def set_run_style(run: ET.Element, size: str, *, bold: bool | None = None) -> None:
    set_run_properties(ensure(run, "rPr", first=True), size, bold=bold)


def set_paragraph_style(paragraph: ET.Element, role: str) -> None:
    ppr = ensure(paragraph, "pPr", first=True)
    remove_children(ppr, "spacing", "ind", "jc", "keepNext", "contextualSpacing")
    spacing = ensure(ppr, "spacing")
    for key, value in (("before", "0"), ("after", "0"), ("line", LINE_TWIPS), ("lineRule", "exact")):
        set_w(spacing, key, value)

    size = BODY_SIZE
    bold: bool | None = None
    alignment = "both"
    indent: tuple[str, str] | None = ("firstLine", BODY_FIRST_LINE)
    if role == "title":
        size, bold, alignment, indent = TITLE_SIZE, True, "center", None
        ensure(ppr, "keepNext")
    elif role == "heading":
        size, bold, alignment, indent = HEADING_SIZE, True, "center", None
        ensure(ppr, "keepNext")
    elif role in {"caption", "no_indent"}:
        alignment, indent = ("center" if role == "caption" else "left"), None
    elif role == "signature":
        alignment, indent = "left", ("start", SIGNATURE_START)
    elif role == "date":
        alignment, indent = "left", ("start", DATE_START)
    elif role in {"evidence_signature", "evidence_date"}:
        # 证据目录的提交信息按整段右对齐处理，不能沿用申请书落款的固定缩进，
        # 否则较长姓名或中文日期会因可用行宽过窄而被迫换行。
        alignment, indent = "right", None
    elif role in {"table", "table_left", "table_header"}:
        size, bold, alignment, indent = (
            SMALL_SIZE, role == "table_header", "left" if role == "table_left" else "center", None
        )
    elif role == "attachment":
        size, alignment, indent = SMALL_SIZE, "left", None

    set_w(ensure(ppr, "jc"), "val", alignment)
    if indent is not None:
        key, value = indent
        set_w(ensure(ppr, "ind"), key, value)
    for run in text_runs(paragraph):
        set_run_style(run, size, bold=bold)


def direct_body_paragraphs(document: ET.Element) -> list[ET.Element]:
    body = document.find(w("body"))
    if body is None:
        return []
    return [child for child in list(body) if child.tag == w("p")]


def remove_blank_body_paragraphs(document: ET.Element) -> None:
    body = document.find(w("body"))
    if body is None:
        return
    for child in list(body):
        if child.tag != w("p") or paragraph_text(child):
            continue
        protected = any(child.find(f".//{w(local)}") is not None for local in ("drawing", "fldChar", "br"))
        if not protected:
            body.remove(child)


def classify_body(paragraphs: list[ET.Element], document_type: str) -> dict[int, str]:
    roles: dict[int, str] = {}
    after_salutation = False
    recipient_seen = False
    attachment_mode = False
    for paragraph in paragraphs:
        text = paragraph_text(paragraph)
        role = "body"
        if document_type == "仲裁申请书":
            if text == "劳动仲裁申请书":
                role = "title"
            elif text in {"仲裁请求：", "事实与理由："}:
                role = "heading"
            elif text == "此致":
                role, after_salutation = "no_indent", True
            elif after_salutation and not recipient_seen:
                role, recipient_seen = "no_indent", True
            elif after_salutation and text.startswith("申请人："):
                role = "signature"
            elif after_salutation and re.fullmatch(r"[〇一二三四五六七八九十]{4}年.+月.+日", text):
                role = "date"
            elif text == "附：":
                role, attachment_mode = "attachment", True
            elif attachment_mode and re.match(r"^\d+、", text):
                role = "attachment"
        elif document_type == "证据清单":
            if text == "证据目录":
                role = "title"
            elif text.startswith("提交人："):
                role = "evidence_signature"
            elif text.startswith("提交时间："):
                role = "evidence_date"
            else:
                role = "caption"
        elif document_type == "行动清单":
            if text == "待补材料与行动清单":
                role = "title"
            elif re.match(r"^[一二三四五六七八九十]+、", text):
                role = "heading"
        roles[id(paragraph)] = role
    return roles


def table_widths(document_type: str, columns: int) -> list[int]:
    if document_type == "证据清单" and columns == 5:
        return [720, 1600, 1100, 800, 4780]
    if document_type == "行动清单" and columns == 5:
        return [900, 2400, 1700, 2800, 1200]
    if document_type == "行动清单" and columns == 4:
        return [1000, 3600, 2800, 1600]
    base, remainder = divmod(TABLE_WIDTH, max(columns, 1))
    return [base + (1 if index < remainder else 0) for index in range(columns)]


def patch_tables(document: ET.Element, document_type: str) -> None:
    for table in document.iter(w("tbl")):
        rows = table.findall(w("tr"))
        if not rows:
            continue
        columns = max(len(row.findall(w("tc"))) for row in rows)
        widths = table_widths(document_type, columns)
        tbl_pr = ensure(table, "tblPr", first=True)
        tbl_w = ensure(tbl_pr, "tblW")
        set_w(tbl_w, "type", "dxa")
        set_w(tbl_w, "w", str(sum(widths)))
        tbl_ind = ensure(tbl_pr, "tblInd")
        set_w(tbl_ind, "type", "dxa")
        set_w(tbl_ind, "w", "0")
        set_w(ensure(tbl_pr, "tblLayout"), "type", "fixed")
        margins = ensure(tbl_pr, "tblCellMar")
        for side, value in (("top", "100"), ("left", "120"), ("bottom", "100"), ("right", "120")):
            edge = ensure(margins, side)
            set_w(edge, "w", value)
            set_w(edge, "type", "dxa")
        borders = ensure(tbl_pr, "tblBorders")
        for edge_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
            edge = ensure(borders, edge_name)
            set_w(edge, "val", "single")
            set_w(edge, "sz", "4")
            set_w(edge, "space", "0")
            set_w(edge, "color", "666666")

        grid = ensure(table, "tblGrid")
        for child in list(grid):
            grid.remove(child)
        for width in widths:
            set_w(ET.SubElement(grid, w("gridCol")), "w", str(width))

        for row_index, row in enumerate(rows):
            cells = row.findall(w("tc"))
            if row_index == 0:
                set_w(ensure(ensure(row, "trPr", first=True), "tblHeader"), "val", "1")
            for column_index, cell in enumerate(cells):
                tc_pr = ensure(cell, "tcPr", first=True)
                tc_w = ensure(tc_pr, "tcW")
                set_w(tc_w, "type", "dxa")
                set_w(tc_w, "w", str(widths[min(column_index, len(widths) - 1)]))
                set_w(ensure(tc_pr, "vAlign"), "val", "center")
                for paragraph in cell.iter(w("p")):
                    role = "table_header" if row_index == 0 else ("table" if column_index == 0 else "table_left")
                    set_paragraph_style(paragraph, role)


def patch_styles(styles: ET.Element) -> None:
    defaults = ensure(styles, "docDefaults", first=True)
    rpr_default = ensure(defaults, "rPrDefault", first=True)
    rpr = ensure(rpr_default, "rPr", first=True)
    set_run_properties(rpr, BODY_SIZE)
    ppr_default = ensure(defaults, "pPrDefault")
    ppr = ensure(ppr_default, "pPr", first=True)
    spacing = ensure(ppr, "spacing")
    for key, value in (("before", "0"), ("after", "0"), ("line", LINE_TWIPS), ("lineRule", "exact")):
        set_w(spacing, key, value)

    for style in styles.findall(w("style")):
        name = style.find(w("name"))
        if name is None or name.get(w("val")) != "Normal":
            continue
        style_rpr = ensure(style, "rPr")
        set_run_properties(style_rpr, BODY_SIZE)
        style_ppr = ensure(style, "pPr")
        style_spacing = ensure(style_ppr, "spacing")
        for key, value in (("before", "0"), ("after", "0"), ("line", LINE_TWIPS), ("lineRule", "exact")):
            set_w(style_spacing, key, value)


def patch_font_table(font_table: ET.Element) -> None:
    target = next(
        (font for font in font_table.findall(w("font")) if font.get(w("name")) == FONT_EAST_ASIA),
        None,
    )
    if target is None:
        target = ET.SubElement(font_table, w("font"))
        set_w(target, "name", FONT_EAST_ASIA)
    set_w(ensure(target, "altName"), "val", FONT_RENDER_FALLBACK)
    set_w(ensure(target, "family"), "val", "roman")
    set_w(ensure(target, "pitch"), "val", "variable")


def patch_page(document: ET.Element) -> None:
    sect_pr = document.find(f".//{w('sectPr')}")
    if sect_pr is None:
        body = document.find(w("body"))
        if body is None:
            raise ValueError("DOCX 缺少 word/body。")
        sect_pr = ET.SubElement(body, w("sectPr"))
    pg_sz = ensure(sect_pr, "pgSz")
    set_w(pg_sz, "w", PAGE_WIDTH)
    set_w(pg_sz, "h", PAGE_HEIGHT)
    pg_mar = ensure(sect_pr, "pgMar")
    for key, value in (
        ("top", PAGE_MARGIN), ("right", PAGE_MARGIN), ("bottom", PAGE_MARGIN),
        ("left", PAGE_MARGIN), ("header", "720"), ("footer", "720"), ("gutter", "0"),
    ):
        set_w(pg_mar, key, value)


def add_profile_metadata(files: dict[str, bytes], delivery_status: str) -> None:
    core_name = "docProps/core.xml"
    if core_name not in files:
        return
    core = safe_fromstring(files[core_name])
    keywords = core.find(f"{{{CP_NS}}}keywords")
    if keywords is None:
        keywords = ET.SubElement(core, f"{{{CP_NS}}}keywords")
    keywords.text = f"LaborPilot;{PROFILE_ID};delivery={delivery_status}"
    files[core_name] = ET.tostring(core, encoding="utf-8", xml_declaration=True)


def apply_jls_style(path: Path, document_type: str, delivery_status: str) -> None:
    """就地修正一份新生成 DOCX，并在写回后执行独立结构校验。"""
    if document_type not in DOCUMENT_TYPES:
        raise ValueError(f"不支持的文书类型：{document_type}")
    if delivery_status not in DELIVERY_STATUSES:
        raise ValueError(f"不支持的交付层级：{delivery_status}")
    if document_type == "行动清单" and delivery_status == "final_submission":
        raise ValueError("行动清单属于内部工作文件，不得标记为最终提交版。")
    with ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    if any(name not in files for name in ("word/document.xml", "word/styles.xml", "word/fontTable.xml")):
        raise ValueError("DOCX 缺少 document.xml、styles.xml 或 fontTable.xml。")
    document = safe_fromstring(files["word/document.xml"])
    styles = safe_fromstring(files["word/styles.xml"])
    font_table = safe_fromstring(files["word/fontTable.xml"])

    remove_blank_body_paragraphs(document)
    paragraphs = direct_body_paragraphs(document)
    roles = classify_body(paragraphs, document_type)
    for paragraph in paragraphs:
        set_paragraph_style(paragraph, roles[id(paragraph)])
    patch_tables(document, document_type)
    patch_page(document)
    patch_styles(styles)
    patch_font_table(font_table)
    files["word/document.xml"] = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    files["word/styles.xml"] = ET.tostring(styles, encoding="utf-8", xml_declaration=True)
    files["word/fontTable.xml"] = ET.tostring(font_table, encoding="utf-8", xml_declaration=True)
    add_profile_metadata(files, delivery_status)

    with tempfile.NamedTemporaryFile(prefix="laborpilot-docx-", suffix=".docx", delete=False, dir=path.parent) as stream:
        temporary = Path(stream.name)
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
    findings = validate_jls_docx(path, document_type, delivery_status)
    if findings:
        raise ValueError("JLS DOCX 版式校验失败：\n" + "\n".join(findings))


def role_expectations(role: str) -> tuple[str, str, str | None, str | None, bool]:
    size, alignment, indent_key, indent_value, bold = BODY_SIZE, "both", "firstLine", BODY_FIRST_LINE, False
    if role == "title":
        return TITLE_SIZE, "center", None, None, True
    if role == "heading":
        return HEADING_SIZE, "center", None, None, True
    if role == "caption":
        return BODY_SIZE, "center", None, None, False
    if role == "no_indent":
        return BODY_SIZE, "left", None, None, False
    if role == "signature":
        return BODY_SIZE, "left", "start", SIGNATURE_START, False
    if role == "date":
        return BODY_SIZE, "left", "start", DATE_START, False
    if role in {"evidence_signature", "evidence_date"}:
        return BODY_SIZE, "right", None, None, False
    if role == "attachment":
        return SMALL_SIZE, "left", None, None, False
    if role in {"table", "table_left", "table_header"}:
        return SMALL_SIZE, "left" if role == "table_left" else "center", None, None, role == "table_header"
    return size, alignment, indent_key, indent_value, bold


def detect_document_type(document: ET.Element) -> str | None:
    texts = {paragraph_text(paragraph) for paragraph in direct_body_paragraphs(document)}
    if "劳动仲裁申请书" in texts:
        return "仲裁申请书"
    if "证据目录" in texts:
        return "证据清单"
    if "待补材料与行动清单" in texts:
        return "行动清单"
    return None


def validate_paragraph(paragraph: ET.Element, role: str, label: str, findings: list[str]) -> None:
    size, alignment, indent_key, indent_value, bold_required = role_expectations(role)
    ppr = paragraph.find(w("pPr"))
    if ppr is None:
        findings.append(f"{label}缺少段落属性。")
        return
    spacing = ppr.find(w("spacing"))
    expected_spacing = {"before": "0", "after": "0", "line": LINE_TWIPS, "lineRule": "exact"}
    if spacing is None or any(spacing.get(w(key)) != value for key, value in expected_spacing.items()):
        findings.append(f"{label}不是段前后 0、固定值 25 磅行距。")
    jc = ppr.find(w("jc"))
    if jc is None or jc.get(w("val")) != alignment:
        findings.append(f"{label}对齐方式不是 {alignment}。")
    ind = ppr.find(w("ind"))
    if indent_key is None:
        if ind is not None and any(ind.get(w(key)) not in {None, "0"} for key in ("firstLine", "start", "left")):
            findings.append(f"{label}存在不应有的缩进。")
    elif ind is None or ind.get(w(indent_key)) != indent_value:
        findings.append(f"{label}缺少规定缩进 {indent_key}={indent_value}。")
    for run_index, run in enumerate(text_runs(paragraph), 1):
        rpr = run.find(w("rPr"))
        fonts = rpr.find(w("rFonts")) if rpr is not None else None
        if fonts is None or any(fonts.get(w(key)) != value for key, value in (
            ("ascii", FONT_LATIN), ("hAnsi", FONT_LATIN), ("eastAsia", FONT_EAST_ASIA),
        )):
            findings.append(f"{label}第 {run_index} 个文本运行未使用规定中英文字体。")
        sz = rpr.find(w("sz")) if rpr is not None else None
        if sz is None or sz.get(w("val")) != size:
            findings.append(f"{label}第 {run_index} 个文本运行字号不符合角色 {role}。")
        if bold_required:
            bold = rpr.find(w("b")) if rpr is not None else None
            if bold is None or bold.get(w("val"), "1") not in {"1", "true"}:
                findings.append(f"{label}第 {run_index} 个文本运行未加粗。")


def validate_table(table: ET.Element, index: int, document_type: str, findings: list[str]) -> None:
    rows = table.findall(w("tr"))
    if not rows:
        findings.append(f"表格 {index} 没有数据行。")
        return
    columns = max(len(row.findall(w("tc"))) for row in rows)
    expected_widths = table_widths(document_type, columns)
    tbl_pr = table.find(w("tblPr"))
    tbl_w = tbl_pr.find(w("tblW")) if tbl_pr is not None else None
    layout = tbl_pr.find(w("tblLayout")) if tbl_pr is not None else None
    if tbl_w is None or tbl_w.get(w("w")) != str(sum(expected_widths)) or tbl_w.get(w("type")) != "dxa":
        findings.append(f"表格 {index} 总宽度不是确定的 DXA 几何。")
    if layout is None or layout.get(w("type")) != "fixed":
        findings.append(f"表格 {index} 未使用固定布局。")
    borders = tbl_pr.find(w("tblBorders")) if tbl_pr is not None else None
    if borders is None or any(
        borders.find(w(edge_name)) is None
        or borders.find(w(edge_name)).get(w("val")) != "single"
        for edge_name in ("top", "left", "bottom", "right", "insideH", "insideV")
    ):
        findings.append(f"表格 {index} 缺少完整、确定的边框。")
    grid = table.find(w("tblGrid"))
    actual_grid = [item.get(w("w")) for item in grid.findall(w("gridCol"))] if grid is not None else []
    if actual_grid != [str(value) for value in expected_widths]:
        findings.append(f"表格 {index} 的 tblGrid 与预定列宽不一致。")
    for row_index, row in enumerate(rows):
        for column_index, cell in enumerate(row.findall(w("tc"))):
            tc_pr = cell.find(w("tcPr"))
            tc_w = tc_pr.find(w("tcW")) if tc_pr is not None else None
            expected = str(expected_widths[min(column_index, len(expected_widths) - 1)])
            if tc_w is None or tc_w.get(w("w")) != expected or tc_w.get(w("type")) != "dxa":
                findings.append(f"表格 {index} 第 {row_index + 1} 行第 {column_index + 1} 列宽度不一致。")
            for paragraph_index, paragraph in enumerate(cell.iter(w("p")), 1):
                role = "table_header" if row_index == 0 else ("table" if column_index == 0 else "table_left")
                validate_paragraph(
                    paragraph, role,
                    f"表格 {index} 第 {row_index + 1} 行第 {column_index + 1} 列第 {paragraph_index} 段",
                    findings,
                )


def validate_jls_docx(
    path: Path,
    document_type: str | None = None,
    delivery_status: str = "lawyer_review_draft",
) -> list[str]:
    """返回 DOCX 版式问题；空列表表示结构校验通过。"""
    findings: list[str] = []
    if delivery_status not in DELIVERY_STATUSES:
        return [f"不支持的交付层级：{delivery_status}"]
    try:
        with ZipFile(path) as archive:
            document = safe_fromstring(archive.read("word/document.xml"))
            font_table = safe_fromstring(archive.read("word/fontTable.xml"))
            core = safe_fromstring(archive.read("docProps/core.xml")) if "docProps/core.xml" in archive.namelist() else None
    except (OSError, KeyError, BadZipFile, ET.ParseError, UnsafeXMLError) as exc:
        return [f"DOCX 无法解析：{exc}"]
    detected = detect_document_type(document)
    if document_type is None:
        document_type = detected
    if document_type not in DOCUMENT_TYPES or detected != document_type:
        findings.append(f"无法确认文书类型：声明={document_type!r}，识别={detected!r}。")
        return findings
    if document_type == "行动清单" and delivery_status == "final_submission":
        findings.append("行动清单属于内部工作文件，不得作为最终提交版。")

    configured_font = next(
        (font for font in font_table.findall(w("font")) if font.get(w("name")) == FONT_EAST_ASIA),
        None,
    )
    alt_name = configured_font.find(w("altName")) if configured_font is not None else None
    if alt_name is None or alt_name.get(w("val")) != FONT_RENDER_FALLBACK:
        findings.append("仿宋_GB2312 未配置可视渲染回退字体 STFangsong。")

    if core is not None:
        keywords = core.find(f"{{{CP_NS}}}keywords")
        expected = f"LaborPilot;{PROFILE_ID};delivery={delivery_status}"
        if keywords is None or keywords.text != expected:
            findings.append("DOCX 元数据未绑定当前 JLS 版式配置和交付层级。")

    paragraphs = direct_body_paragraphs(document)
    roles = classify_body(paragraphs, document_type)
    for index, paragraph in enumerate(paragraphs, 1):
        text = paragraph_text(paragraph)
        if not text:
            findings.append(f"正文第 {index} 段为空白段落。")
            continue
        validate_paragraph(paragraph, roles[id(paragraph)], f"正文第 {index} 段“{text[:24]}”", findings)

    expected_title = {"仲裁申请书": "劳动仲裁申请书", "证据清单": "证据目录", "行动清单": "待补材料与行动清单"}[document_type]
    if sum(paragraph_text(paragraph) == expected_title for paragraph in paragraphs) != 1:
        findings.append(f"文书必须且只能包含一个标题“{expected_title}”。")
    tables = list(document.iter(w("tbl")))
    for index, table in enumerate(tables, 1):
        validate_table(table, index, document_type, findings)
    if document_type in {"证据清单", "行动清单"} and not tables:
        findings.append(f"{document_type}缺少应有表格。")

    sect_pr = document.find(f".//{w('sectPr')}")
    pg_sz = sect_pr.find(w("pgSz")) if sect_pr is not None else None
    pg_mar = sect_pr.find(w("pgMar")) if sect_pr is not None else None
    if pg_sz is None or pg_sz.get(w("w")) != PAGE_WIDTH or pg_sz.get(w("h")) != PAGE_HEIGHT:
        findings.append("页面尺寸不是 A4。")
    if pg_mar is None or any(pg_mar.get(w(key)) != PAGE_MARGIN for key in ("top", "right", "bottom", "left")):
        findings.append("页面四边距不是 1 英寸。")

    all_text = "\n".join(paragraph_text(paragraph) for paragraph in document.iter(w("p")))
    if delivery_status == "final_submission":
        for marker in FINAL_BLOCKED_MARKERS:
            if marker in all_text:
                findings.append(f"最终提交版仍含内部占位或待办标记：{marker}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="应用或校验 LaborPilot 的 JLS DOCX 版式")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("apply", "check"):
        item = sub.add_parser(command)
        item.add_argument("--input", required=True)
        item.add_argument("--document-type", choices=sorted(DOCUMENT_TYPES))
        item.add_argument("--delivery-status", choices=sorted(DELIVERY_STATUSES), default="lawyer_review_draft")
    args = parser.parse_args()
    path = Path(args.input)
    try:
        if args.command == "apply":
            if not args.document_type:
                raise ValueError("apply 必须指定 --document-type。")
            apply_jls_style(path, args.document_type, args.delivery_status)
        findings = validate_jls_docx(path, args.document_type, args.delivery_status)
    except (OSError, ValueError, BadZipFile, ET.ParseError) as exc:
        findings = [str(exc)]
    result: dict[str, Any] = {
        "status": "pass" if not findings else "blocked",
        "profile": PROFILE_ID,
        "path": str(path.resolve()),
        "delivery_status": args.delivery_status,
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
