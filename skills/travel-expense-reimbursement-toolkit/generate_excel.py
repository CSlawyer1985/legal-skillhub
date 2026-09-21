# -*- coding: utf-8 -*-
"""为每个案件生成Excel报销明细表"""
import json
import os
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
from openpyxl.utils import get_column_letter

DATA_PATH = r".\expense_data.json"
OUT_DIR = r"."

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 自动校正每个案件的total和item_count，避免手动算错
corrected = False
for case in data:
    actual_total = round(sum(item["amount"] for item in case["items"]), 2)
    actual_count = len(case["items"])
    if case.get("total") != actual_total or case.get("item_count") != actual_count:
        print(f"[校正] {case['case_name']}: total {case.get('total')} -> {actual_total}, count {case.get('item_count')} -> {actual_count}")
        case["total"] = actual_total
        case["item_count"] = actual_count
        corrected = True
if corrected:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 样式定义
title_font = Font(name="微软雅黑", size=14, bold=True)
header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
total_font = Font(name="微软雅黑", size=11, bold=True)
total_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
normal_font = Font(name="微软雅黑", size=11)
thin_border = Border(
    left=Side(style="thin", color="999999"),
    right=Side(style="thin", color="999999"),
    top=Side(style="thin", color="999999"),
    bottom=Side(style="thin", color="999999"),
)
center_align = Alignment(horizontal="center", vertical="center")
left_align = Alignment(horizontal="left", vertical="center")
right_align = Alignment(horizontal="right", vertical="center")

HEADERS = ["序号", "日期", "时间", "事项摘要", "起点", "终点", "金额(元)", "备注"]
COL_WIDTHS = [6, 14, 10, 28, 20, 20, 12, 30]


def generate_excel(case):
    case_name = case["case_name"]
    total = case["total"]
    items = case["items"]

    wb = Workbook()
    ws = wb.active
    ws.title = case_name[:31]  # Excel sheet name max 31 chars

    # 标题行
    ws.merge_cells("A1:H1")
    ws["A1"] = f"{case_name} - 差旅费报销明细表"
    ws["A1"].font = title_font
    ws["A1"].alignment = center_align
    ws.row_dimensions[1].height = 30

    # 总金额行（含预支/补交/退还信息，按时间逻辑顺序表述）
    ws.merge_cells("A2:H2")
    if case.get("prepayment"):
        prep = case["prepayment"]
        diff = round(total - prep["amount"], 2)
        if diff > 0:
            ws["A2"] = f"当事人已预支：{prep['amount']:.2f} 元    实际发生报销：{total:.2f} 元（共{len(items)}条）    当事人尚需补交：{diff:.2f} 元    待向当事人退还：0.00 元"
        elif diff < 0:
            ws["A2"] = f"当事人已预支：{prep['amount']:.2f} 元    实际发生报销：{total:.2f} 元（共{len(items)}条）    当事人尚需补交：0.00 元    待向当事人退还：{abs(diff):.2f} 元"
        else:
            ws["A2"] = f"当事人已预支：{prep['amount']:.2f} 元    实际发生报销：{total:.2f} 元（共{len(items)}条）    费用两清"
    else:
        ws["A2"] = f"当事人未预支    实际发生报销：{total:.2f} 元（共{len(items)}条）    当事人尚需补交：{total:.2f} 元    待向当事人退还：0.00 元"
    ws["A2"].font = Font(name="微软雅黑", size=11, bold=True, color="CC0000")
    ws["A2"].alignment = center_align
    ws.row_dimensions[2].height = 22

    # 空行
    ws.row_dimensions[3].height = 8

    # 表头
    header_row = 4
    for col_idx, header in enumerate(HEADERS, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    ws.row_dimensions[header_row].height = 24

    # 数据行
    for i, item in enumerate(items):
        row = header_row + 1 + i
        # Date: red if from dialog, red+(推测) if inferred
        date_val = item["date"]
        date_font = normal_font
        date_fill = None
        if item.get("date_source") == "dialog":
            date_font = Font(name="微软雅黑", size=11, bold=True, color="CC0000")
            date_fill = PatternFill(start_color="FFF3E0", end_color="FFF3E0", fill_type="solid")
        elif item.get("date_source") == "inferred":
            date_val = f"{item['date']}（推测）"
            date_font = Font(name="微软雅黑", size=11, bold=True, color="CC0000")
            date_fill = PatternFill(start_color="FFF3E0", end_color="FFF3E0", fill_type="solid")

        values = [
            item["seq"],
            date_val,
            item.get("time", "") or "—",
            item["type"],
            item.get("from", "") or "—",
            item.get("to", "") or "—",
            item["amount"],
            item.get("note", "") or "",
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.font = normal_font
            cell.border = thin_border
            # 日期列特殊处理
            if col_idx == 2:
                cell.font = date_font
                if date_fill:
                    cell.fill = date_fill
            # 金额列右对齐+数字格式
            if col_idx == 7:
                cell.alignment = right_align
                cell.number_format = "0.00"
            elif col_idx in (1, 2, 3):
                cell.alignment = center_align
            else:
                cell.alignment = left_align
        ws.row_dimensions[row].height = 20

    # 合计行
    total_row = header_row + 1 + len(items)
    ws.merge_cells(f"A{total_row}:F{total_row}")
    total_cell = ws.cell(row=total_row, column=1, value="合计")
    total_cell.font = total_font
    total_cell.fill = total_fill
    total_cell.alignment = center_align
    total_cell.border = thin_border

    amount_cell = ws.cell(row=total_row, column=7, value=total)
    amount_cell.font = total_font
    amount_cell.fill = total_fill
    amount_cell.alignment = right_align
    amount_cell.number_format = "0.00"
    amount_cell.border = thin_border

    note_cell = ws.cell(row=total_row, column=8, value="")
    note_cell.fill = total_fill
    note_cell.border = thin_border
    ws.row_dimensions[total_row].height = 24

    # ===== 预支费用结算区（所有案件都显示）=====
    current_row = total_row + 1

    # 空行
    ws.row_dimensions[current_row].height = 8
    current_row += 1

    # 结算标题
    ws.merge_cells(f"A{current_row}:H{current_row}")
    title = ws.cell(row=current_row, column=1, value="【费用结算】")
    title.font = Font(name="微软雅黑", size=12, bold=True, color="333333")
    title.alignment = Alignment(horizontal="left", vertical="center")
    title.fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
    ws.row_dimensions[current_row].height = 26
    current_row += 1

    if case.get("prepayment"):
        prep = case["prepayment"]
        diff = round(total - prep["amount"], 2)
        refund = abs(diff) if diff < 0 else 0
        supplement = diff if diff > 0 else 0

        # 四行结算数据
        rows_data = [
            ("实际发生差旅费总额", total, "FFF2CC", False, "333333"),
            ("当事人已预支差旅费", prep["amount"], "E8F5E9", False, "333333"),
            ("当事人尚需补交", supplement, "FFEBEE", True, "CC0000"),
            ("待向当事人退还", refund, "E3F2FD", True, "CC0000"),
        ]
        for label, val, fill_color, is_bold, text_color in rows_data:
            ws.merge_cells(f"A{current_row}:F{current_row}")
            label_cell = ws.cell(row=current_row, column=1, value=label)
            label_cell.font = Font(name="微软雅黑", size=11, bold=is_bold, color=text_color)
            label_cell.alignment = Alignment(horizontal="right", vertical="center")
            label_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            label_cell.border = thin_border

            val_cell = ws.cell(row=current_row, column=7, value=val)
            val_cell.font = Font(name="微软雅黑", size=11, bold=True, color=text_color)
            val_cell.alignment = right_align
            val_cell.number_format = "0.00"
            val_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            val_cell.border = thin_border

            unit_cell = ws.cell(row=current_row, column=8, value="元")
            unit_cell.font = Font(name="微软雅黑", size=11, color="666666")
            unit_cell.alignment = Alignment(horizontal="left", vertical="center")
            unit_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            unit_cell.border = thin_border
            ws.row_dimensions[current_row].height = 24
            current_row += 1

        # 预支说明
        ws.merge_cells(f"A{current_row}:H{current_row}")
        if diff > 0:
            note_text = f"注：当事人于 {prep['date']} 预支差旅费 {prep['amount']:.2f} 元，实际发生 {total:.2f} 元，尚需补交 {diff:.2f} 元。"
        elif diff < 0:
            note_text = f"注：当事人于 {prep['date']} 预支差旅费 {prep['amount']:.2f} 元，实际发生 {total:.2f} 元，需向当事人退还 {abs(diff):.2f} 元。"
        else:
            note_text = f"注：当事人于 {prep['date']} 预支差旅费 {prep['amount']:.2f} 元，实际发生 {total:.2f} 元，费用两清。"
        note = ws.cell(row=current_row, column=1, value=note_text)
        note.font = Font(name="微软雅黑", size=10, italic=True, color="666666")
        note.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[current_row].height = 20
    else:
        # 无预支费用的情况
        rows_data = [
            ("实际发生差旅费总额", total, "FFF2CC", False, "333333"),
            ("当事人已预支差旅费", 0, "E8F5E9", False, "999999"),
            ("当事人尚需补交", total, "FFEBEE", True, "CC0000"),
            ("待向当事人退还", 0, "E3F2FD", False, "999999"),
        ]
        for label, val, fill_color, is_bold, text_color in rows_data:
            ws.merge_cells(f"A{current_row}:F{current_row}")
            label_cell = ws.cell(row=current_row, column=1, value=label)
            label_cell.font = Font(name="微软雅黑", size=11, bold=is_bold, color=text_color)
            label_cell.alignment = Alignment(horizontal="right", vertical="center")
            label_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            label_cell.border = thin_border

            val_cell = ws.cell(row=current_row, column=7, value=val)
            val_cell.font = Font(name="微软雅黑", size=11, bold=True, color=text_color)
            val_cell.alignment = right_align
            val_cell.number_format = "0.00"
            val_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            val_cell.border = thin_border

            unit_cell = ws.cell(row=current_row, column=8, value="元")
            unit_cell.font = Font(name="微软雅黑", size=11, color="666666")
            unit_cell.alignment = Alignment(horizontal="left", vertical="center")
            unit_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
            unit_cell.border = thin_border
            ws.row_dimensions[current_row].height = 24
            current_row += 1

        ws.merge_cells(f"A{current_row}:H{current_row}")
        note = ws.cell(row=current_row, column=1, value=f"注：本案件当事人未预支差旅费，实际发生 {total:.2f} 元，需向当事人报销 {total:.2f} 元。")
        note.font = Font(name="微软雅黑", size=10, italic=True, color="666666")
        note.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[current_row].height = 20

    # 设置列宽
    for col_idx, width in enumerate(COL_WIDTHS, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # 冻结表头
    ws.freeze_panes = f"A{header_row + 1}"

    # 保存（文件名包含核心数据：预支/实际/补交或退还）
    if case.get("prepayment"):
        prep = case["prepayment"]
        diff = round(total - prep["amount"], 2)
        if diff > 0:
            filename = f"{case_name}报销明细_预支{prep['amount']:.2f}_实际{total:.2f}_补交{diff:.2f}.xlsx"
        elif diff < 0:
            filename = f"{case_name}报销明细_预支{prep['amount']:.2f}_实际{total:.2f}_退还{abs(diff):.2f}.xlsx"
        else:
            filename = f"{case_name}报销明细_预支{prep['amount']:.2f}_实际{total:.2f}_两清.xlsx"
    else:
        filename = f"{case_name}报销明细_未预支_实际{total:.2f}_补交{total:.2f}.xlsx"
    out_path = os.path.join(OUT_DIR, filename)
    wb.save(out_path)
    print(f"Generated: {out_path}")
    return out_path


# 生成前：按截图分组复核（防止同图多日期误套首日期，与 generate_docs.js 保持一致）
print("=== 按截图分组复核（请确认每条日期与截图日期表头一致）===")
for case in data:
    img_groups = defaultdict(list)
    for item in case["items"]:
        img_name = item.get("img", "")
        if img_name and img_name != "__no_image__":
            img_groups[img_name].append(item)
    for img_name, group_items in img_groups.items():
        dates = sorted(set(it["date"] for it in group_items))
        seqs = ",".join(str(it["seq"]) for it in group_items)
        multi = f"  ⚠ 含{len(dates)}个日期: {', '.join(dates)}" if len(dates) > 1 else ""
        print(f"  {img_name}: 序号{seqs}{multi}")
print("")

# 生成所有Excel
for case in data:
    generate_excel(case)

print(f"\n全部 {len(data)} 份Excel已生成完成！")
