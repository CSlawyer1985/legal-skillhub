#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""New-firm onboarding for case-archiver V3.

The V3 detector deduplicates merged cells and prefers explicit markers,
content controls, and label-relative selectors. Generated mappings are a
reviewable starting point; low-confidence empty-cell guesses are marked with
``review_required``.
"""
import json
import os
import re
import sys
from pathlib import Path

from docx import Document

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_ROOT = os.path.abspath(os.path.join(os.path.expanduser("~"), ".workbuddy", "case-archiver"))
sys.path.insert(0, HERE)

import fill_docx


MARKER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}|\[\[\s*([^\[\]]+?)\s*\]\]")
PLACEHOLDER = re.compile(r"(_{2,}|（\s*）|\(\s*\)|【\s*】|\.{3,}|…{2,})")


def _norm(text):
    return re.sub(r"[\s\u3000:：_（）()【】\[\]]+", "", str(text or ""))


def _clean_label(text):
    return PLACEHOLDER.sub("", str(text or "")).strip().rstrip("：:")


def _looks_like_label(text):
    label = _clean_label(text)
    if not label or len(_norm(label)) > 18:
        return False
    if re.search(r"[。！？!?；;]", label):
        return False
    if re.search(r"[□☐☑☒○◯]", label):
        return False
    return True


def _unique_cells(row):
    result = []
    seen = set()
    for grid_col, cell in enumerate(row.cells):
        key = cell._tc
        if key in seen:
            continue
        seen.add(key)
        result.append((grid_col, cell))
    return result


def _add_field(fields, seen, field):
    key = json.dumps(
        {
            "marker": field.get("marker"),
            "control_tag": field.get("control_tag"),
            "selector": field.get("selector"),
            "loc": field.get("loc"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    if key in seen:
        return
    seen.add(key)
    fields.append(field)


def detect_fields(docx_path):
    doc = Document(docx_path)
    fields = []
    seen = set()

    for para in fill_docx.iter_all_paragraphs(doc):
        for match in MARKER.finditer(para.text):
            name = next(value for value in match.groups() if value is not None).strip()
            _add_field(
                fields,
                seen,
                {
                    "name": name,
                    "marker": match.group(0),
                    "source": "agent",
                    "confidence": "high",
                },
            )

    inspection = fill_docx.inspect_template(docx_path)
    for tag in inspection.get("content_controls", []):
        _add_field(
            fields,
            seen,
            {
                "name": tag,
                "control_tag": tag,
                "source": "agent",
                "confidence": "high",
            },
        )

    for ti, table in enumerate(doc.tables):
        occurrences = {}
        for ri, row in enumerate(table.rows):
            unique = _unique_cells(row)
            for ui, (grid_col, cell) in enumerate(unique):
                text = cell.text.strip()
                if MARKER.search(text):
                    continue
                previous = unique[ui - 1][1] if ui > 0 else None
                previous_label = _clean_label(previous.text) if previous is not None else ""

                field = None
                if PLACEHOLDER.search(text):
                    same_label = _clean_label(text)
                    if _looks_like_label(same_label):
                        field = {
                            "name": same_label,
                            "selector": {
                                "type": "cell_anchor",
                                "table": ti,
                                "label": same_label,
                                "direction": "same",
                                "match": "contains",
                            },
                            "loc": [ti, ri, grid_col],
                            "mode": "after_label",
                            "source": "agent",
                            "confidence": "medium",
                            "review_required": True,
                        }
                    elif _looks_like_label(previous_label):
                        field = {
                            "name": previous_label,
                            "selector": {
                                "type": "cell_anchor",
                                "table": ti,
                                "label": previous_label,
                                "direction": "right",
                                "match": "contains",
                            },
                            "loc": [ti, ri, grid_col],
                            "mode": "replace",
                            "source": "agent",
                            "confidence": "medium",
                            "review_required": True,
                        }
                elif not text and _looks_like_label(previous_label):
                    field = {
                        "name": previous_label,
                        "selector": {
                            "type": "cell_anchor",
                            "table": ti,
                            "label": previous_label,
                            "direction": "right",
                            "match": "contains",
                        },
                        "loc": [ti, ri, grid_col],
                        "mode": "replace",
                        "source": "agent",
                        "confidence": "low",
                        "review_required": True,
                    }

                if field:
                    selector = field["selector"]
                    occurrence_key = (ti, _norm(selector["label"]))
                    occurrence = occurrences.get(occurrence_key, 0)
                    occurrences[occurrence_key] = occurrence + 1
                    if occurrence:
                        selector["occurrence"] = occurrence
                    _add_field(fields, seen, field)

    return {"kind": "docx_form_v3", "strict": True, "fields": fields}


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    print("=== 案件归档 SKILL V3 · 律所接入向导 ===")
    firm = input("律所英文标识(如 tongjing): ").strip() or "myfirm"
    firm_name = input("律所全称: ").strip() or firm
    template_dir = input("模板目录(绝对路径): ").strip()
    output_base = input("归档输出目录: ").strip()
    source_base = input("源案卷目录: ").strip()
    directory_template = input("归档目录模板文件名(如 归档目录.doc): ").strip()

    base = os.path.join(CONFIG_ROOT, "firm_config", firm)
    os.makedirs(base, exist_ok=True)

    _write_json(
        os.path.join(base, "paths.json"),
        {
            "firm_name": firm_name,
            "template_dir": template_dir,
            "output_base": output_base,
            "source_base": source_base,
            "directory_template": directory_template,
        },
    )

    field_map = {"schema_version": 3, "templates": {}}
    print("\n依次提供需填写的 DOCX 模板（留空结束）：")
    while True:
        raw = input("  填写模板 docx 路径(或回车结束): ").strip()
        if not raw:
            break
        if not os.path.exists(raw):
            print("    路径不存在，请重试")
            continue
        name = os.path.splitext(os.path.basename(raw))[0]
        spec = detect_fields(raw)
        spec["file"] = os.path.basename(raw)
        field_map["templates"][name] = spec
        review_count = sum(1 for item in spec["fields"] if item.get("review_required"))
        print(f"    侦测到 {len(spec['fields'])} 个字段，其中 {review_count} 个需人工确认")

    if not field_map["templates"]:
        field_map["templates"] = {
            "审批表": {"file": "审批表.docx", "kind": "docx_form_v3", "strict": True, "fields": []}
        }
    _write_json(os.path.join(base, "field_map.json"), field_map)

    _write_json(
        os.path.join(base, "archive_plan.json"),
        {
            "order": [
                {"seq": index, "name": f"目录项{index}", "type": "copy", "match": ["*"], "out": f"{index}.材料"}
                for index in range(1, 21)
            ],
            "directory_template_out": "0.归档卷宗目录.doc",
        },
    )
    _write_json(
        os.path.join(base, "preferences.json"),
        {"merge_pdf": "ask", "auto_number_folders": True, "leave_blank_not_placeholder": True},
    )
    _write_json(os.path.join(CONFIG_ROOT, "settings.json"), {"default_firm": firm})

    print(f"\n已生成配置: {base}")
    print("请先审阅 field_map.json 中 review_required=true 的映射，再进行正式归档。")


if __name__ == "__main__":
    main()
