#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import math
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any, Optional
from xml.sax.saxutils import escape

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

getcontext().prec = 28

BASE_DIR = Path(__file__).resolve().parent.parent
ZERO = Decimal("0")
MONTHLY_PAID_DAYS = Decimal("21.75")
CALENDAR_YEAR_DAYS = Decimal("365")

LAW_BASIS = {
    "annual_days": "《职工带薪年休假条例》第三条；《企业职工带薪年休假实施办法》第四条",
    "new_employee": "《企业职工带薪年休假实施办法》第五条",
    "resignation": "《企业职工带薪年休假实施办法》第十二条",
    "daily_wage": "《企业职工带薪年休假实施办法》第十一条",
    "compensation": "《职工带薪年休假条例》第五条；《企业职工带薪年休假实施办法》第十条",
    "exceptions": "《职工带薪年休假条例》第四条；《企业职工带薪年休假实施办法》第七条、第八条",
}


class CalculationError(Exception):
    """Raised for invalid input or unsupported calculation requests."""


@dataclass
class DetailRow:
    item: str
    process: str
    amount: Decimal
    legal_basis: str
    note: str = ""


def decimal_arg(value: Any, field_name: str = "数值") -> Decimal:
    if value is None or value == "":
        raise CalculationError(f"{field_name}不能为空")
    try:
        return Decimal(str(value).replace(",", ""))
    except Exception as exc:
        raise CalculationError(f"{field_name}不是有效数字：{value}") from exc


def optional_decimal(value: Any, default: Decimal = ZERO, field_name: str = "数值") -> Decimal:
    if value is None or value == "":
        return default
    return decimal_arg(value, field_name)


def non_negative(value: Decimal, field_name: str) -> Decimal:
    if value < 0:
        raise CalculationError(f"{field_name}不得为负数")
    return value


def parse_date(value: Any, field_name: str) -> date:
    if not value:
        raise CalculationError(f"{field_name}不能为空")
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise CalculationError(f"{field_name}必须是 YYYY-MM-DD 格式") from exc


def parse_year(value: Any) -> int:
    if value is None or value == "":
        raise CalculationError("year 不能为空")
    try:
        year = int(value)
    except Exception as exc:
        raise CalculationError(f"year 不是有效年份：{value}") from exc
    if year < 1900 or year > 2100:
        raise CalculationError("year 超出支持范围：1900-2100")
    return year


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_text(value: Decimal) -> str:
    return format(money(value), "f")


def decimal_text(value: Decimal, places: str = "0.00") -> str:
    return format(value.quantize(Decimal(places), rounding=ROUND_HALF_UP), "f")


def int_days(value: Decimal) -> int:
    return int(math.floor(float(value)))


def json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return money_text(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, DetailRow):
        return json_ready(asdict(value))
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    return value


def success(action: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "action": action, **data}


def annual_leave_days_by_years(cumulative_years: Decimal) -> int:
    if cumulative_years < 0:
        raise CalculationError("cumulative_years 不得为负数")
    if cumulative_years < Decimal("1"):
        return 0
    if cumulative_years < Decimal("10"):
        return 5
    if cumulative_years < Decimal("20"):
        return 10
    return 15


def resolve_annual_leave_days(payload: dict[str, Any]) -> tuple[int, str]:
    if "annual_leave_days" in payload:
        days = decimal_arg(payload["annual_leave_days"], "annual_leave_days")
        if days < 0:
            raise CalculationError("annual_leave_days 不得为负数")
        return int_days(days), "payload.annual_leave_days"

    cumulative_years = decimal_arg(payload.get("cumulative_years"), "cumulative_years")
    days = annual_leave_days_by_years(cumulative_years)
    return days, f"累计工作年限 {decimal_text(cumulative_years)} 年对应法定年休假天数"


def daily_wage(payload: dict[str, Any]) -> dict[str, Any]:
    monthly_wage = decimal_arg(payload.get("monthly_wage"), "monthly_wage")
    if monthly_wage <= 0:
        raise CalculationError("monthly_wage 必须大于0")
    daily = monthly_wage / MONTHLY_PAID_DAYS
    return {
        "monthly_wage": monthly_wage,
        "monthly_paid_days": MONTHLY_PAID_DAYS,
        "daily_wage": money(daily),
        "formula": "日工资 = 剔除加班工资后的月平均工资 ÷ 21.75",
        "legal_basis": LAW_BASIS["daily_wage"],
        "note": "月工资应为支付未休年休假工资报酬前12个月剔除加班工资后的月平均工资；不满12个月的按实际月份平均。",
    }


def days_inclusive(start: date, end: date) -> int:
    if end < start:
        raise CalculationError("结束日期不得早于开始日期")
    return (end - start).days + 1


def validate_date_in_year(value: date, year: int, field_name: str) -> None:
    if value.year != year:
        raise CalculationError(f"{field_name} 必须落在 year={year} 的公历年度内")


def calc_compensation(
    *,
    unused_days: int,
    daily_wage_value: Decimal,
    employee_reason_written_waiver: bool = False,
) -> tuple[list[DetailRow], Decimal, Decimal]:
    if unused_days <= 0:
        return [], ZERO, ZERO

    normal_wage = money(daily_wage_value * Decimal(unused_days))
    total_300 = money(daily_wage_value * Decimal(unused_days) * Decimal("3"))
    extra_200 = money(daily_wage_value * Decimal(unused_days) * Decimal("2"))

    if employee_reason_written_waiver:
        rows = [
            DetailRow(
                item="未休年休假正常工资收入",
                process=f"日工资 {money_text(daily_wage_value)} × 未休 {unused_days} 天 × 100%",
                amount=normal_wage,
                legal_basis=LAW_BASIS["compensation"],
                note="职工因本人原因且书面提出不休年休假的，用人单位可以只支付正常工作期间工资收入。",
            )
        ]
        return rows, normal_wage, ZERO

    rows = [
        DetailRow(
            item="未休年休假工资报酬（300%口径）",
            process=f"日工资 {money_text(daily_wage_value)} × 未休 {unused_days} 天 × 300%",
            amount=total_300,
            legal_basis=LAW_BASIS["compensation"],
            note="300%包含正常工作期间工资收入100%和额外补偿200%。",
        ),
        DetailRow(
            item="其中：额外应补发部分（200%口径）",
            process=f"日工资 {money_text(daily_wage_value)} × 未休 {unused_days} 天 × 200%",
            amount=extra_200,
            legal_basis=LAW_BASIS["compensation"],
            note="若正常工资已发，通常重点主张该200%差额。",
        ),
    ]
    return rows, total_300, extra_200


def new_employee(payload: dict[str, Any]) -> dict[str, Any]:
    year = parse_year(payload.get("year"))
    entry_date = parse_date(payload.get("entry_date"), "entry_date")
    validate_date_in_year(entry_date, year, "entry_date")
    annual_days, annual_source = resolve_annual_leave_days(payload)

    year_end = date(year, 12, 31)
    remaining_calendar_days = days_inclusive(entry_date, year_end)
    raw_days = Decimal(remaining_calendar_days) / CALENDAR_YEAR_DAYS * Decimal(annual_days)
    converted_days = int_days(raw_days)

    warnings: list[str] = []
    if annual_days == 0:
        warnings.append("累计工作年限未满1年时，通常不享受当年带薪年休假。")

    return success(
        "new_employee",
        {
            "scenario": "新员工入职当年折算",
            "year": year,
            "entry_date": entry_date,
            "annual_leave_days": annual_days,
            "annual_leave_days_source": annual_source,
            "remaining_calendar_days": remaining_calendar_days,
            "raw_converted_days": raw_days,
            "converted_leave_days": converted_days,
            "formula": f"({remaining_calendar_days} ÷ 365) × {annual_days} = {decimal_text(raw_days)}，不足1整天部分不计入",
            "legal_basis": LAW_BASIS["new_employee"],
            "warnings": warnings,
        },
    )


def resignation(payload: dict[str, Any]) -> dict[str, Any]:
    year = parse_year(payload.get("year"))
    resignation_date = parse_date(payload.get("resignation_date"), "resignation_date")
    validate_date_in_year(resignation_date, year, "resignation_date")
    annual_days, annual_source = resolve_annual_leave_days(payload)
    already_taken = non_negative(
        optional_decimal(payload.get("already_taken_days", payload.get("taken_days")), ZERO, "already_taken_days"),
        "already_taken_days",
    )

    elapsed_calendar_days = days_inclusive(date(year, 1, 1), resignation_date)
    raw_prorated_days = Decimal(elapsed_calendar_days) / CALENDAR_YEAR_DAYS * Decimal(annual_days)
    prorated_days = int_days(raw_prorated_days)
    unused_days = max(0, prorated_days - int_days(already_taken))
    more_taken_days = max(0, int_days(already_taken) - prorated_days)

    rows: list[DetailRow] = []
    total_compensation = ZERO
    extra_compensation = ZERO
    daily: Optional[Decimal] = None
    if "monthly_wage" in payload and unused_days > 0:
        wage_info = daily_wage(payload)
        daily = Decimal(str(wage_info["daily_wage"]))
        rows, total_compensation, extra_compensation = calc_compensation(
            unused_days=unused_days,
            daily_wage_value=daily,
            employee_reason_written_waiver=bool(payload.get("employee_reason_written_waiver")),
        )

    warnings: list[str] = []
    if annual_days == 0:
        warnings.append("累计工作年限未满1年时，通常不享受当年带薪年休假。")
    if more_taken_days:
        warnings.append("当年已安排年休假多于折算应休天数的，多出部分不再扣回。")
    if unused_days > 0 and "monthly_wage" not in payload:
        warnings.append("未提供 monthly_wage，仅计算未休天数，未计算补偿金额。")

    return success(
        "resignation",
        {
            "scenario": "离职员工年休假折算与补偿",
            "year": year,
            "resignation_date": resignation_date,
            "annual_leave_days": annual_days,
            "annual_leave_days_source": annual_source,
            "elapsed_calendar_days": elapsed_calendar_days,
            "raw_prorated_days": raw_prorated_days,
            "prorated_leave_days": prorated_days,
            "already_taken_days": already_taken,
            "unused_leave_days": unused_days,
            "more_taken_days_no_deduction": more_taken_days,
            "daily_wage": daily,
            "detail_rows": rows,
            "total_300_percent_compensation": total_compensation,
            "extra_200_percent_compensation": extra_compensation,
            "formula": f"({elapsed_calendar_days} ÷ 365) × {annual_days} = {decimal_text(raw_prorated_days)}，取整后 {prorated_days} 天；未休天数 = max(0, {prorated_days} - {int_days(already_taken)}) = {unused_days} 天",
            "legal_basis": LAW_BASIS["resignation"],
            "warnings": warnings,
        },
    )


def in_service(payload: dict[str, Any]) -> dict[str, Any]:
    year = parse_year(payload.get("year"))
    annual_days, annual_source = resolve_annual_leave_days(payload)
    taken_days = non_negative(optional_decimal(payload.get("taken_days"), ZERO, "taken_days"), "taken_days")
    arranged_days = non_negative(
        optional_decimal(payload.get("arranged_days", payload.get("scheduled_days")), Decimal(annual_days), "arranged_days"),
        "arranged_days",
    )
    unused_days = max(0, annual_days - int_days(taken_days))

    wage_info = daily_wage(payload)
    daily = Decimal(str(wage_info["daily_wage"]))
    rows, total_compensation, extra_compensation = calc_compensation(
        unused_days=unused_days,
        daily_wage_value=daily,
        employee_reason_written_waiver=bool(payload.get("employee_reason_written_waiver")),
    )

    warnings: list[str] = []
    if annual_days == 0:
        warnings.append("累计工作年限未满1年时，通常不享受当年带薪年休假。")
    if arranged_days < Decimal(annual_days):
        warnings.append("用人单位安排年休假天数少于法定应休天数时，对应未休天数应支付未休年休假工资报酬。")
    if taken_days > Decimal(annual_days):
        warnings.append("已休天数超过法定应休天数，脚本按未休0天处理；超休是否扣回需结合单位制度和证据另行判断。")

    return success(
        "in_service",
        {
            "scenario": "在职员工未休年休假补偿",
            "year": year,
            "annual_leave_days": annual_days,
            "annual_leave_days_source": annual_source,
            "arranged_days": arranged_days,
            "taken_days": taken_days,
            "unused_leave_days": unused_days,
            "daily_wage": daily,
            "detail_rows": rows,
            "total_300_percent_compensation": total_compensation,
            "extra_200_percent_compensation": extra_compensation,
            "formula": f"未休天数 = max(0, {annual_days} - {int_days(taken_days)}) = {unused_days} 天",
            "legal_basis": LAW_BASIS["compensation"],
            "warnings": warnings,
        },
    )


def eligibility_check(payload: dict[str, Any]) -> dict[str, Any]:
    cumulative_years = decimal_arg(payload.get("cumulative_years"), "cumulative_years")
    annual_days = annual_leave_days_by_years(cumulative_years)
    warning_items: list[str] = []

    summer_winter_leave_days = optional_decimal(payload.get("summer_winter_leave_days"), ZERO, "summer_winter_leave_days")
    personal_leave_days = optional_decimal(payload.get("personal_leave_days"), ZERO, "personal_leave_days")
    sick_leave_months = optional_decimal(payload.get("sick_leave_months"), ZERO, "sick_leave_months")

    disqualified = False
    if annual_days == 0:
        disqualified = True
        warning_items.append("连续工作未满12个月，通常不享受带薪年休假。")
    if summer_winter_leave_days > Decimal(annual_days):
        disqualified = True
        warning_items.append("依法享受寒暑假且休假天数多于年休假天数的，不享受当年年休假。")
    if personal_leave_days >= Decimal("20") and bool(payload.get("personal_leave_paid", True)):
        disqualified = True
        warning_items.append("请事假累计20天以上且单位按照规定不扣工资的，不享受当年年休假。")
    if Decimal("1") <= cumulative_years < Decimal("10") and sick_leave_months >= Decimal("2"):
        disqualified = True
        warning_items.append("累计工作满1年不满10年，请病假累计2个月以上的，不享受当年年休假。")
    if Decimal("10") <= cumulative_years < Decimal("20") and sick_leave_months >= Decimal("3"):
        disqualified = True
        warning_items.append("累计工作满10年不满20年，请病假累计3个月以上的，不享受当年年休假。")
    if cumulative_years >= Decimal("20") and sick_leave_months >= Decimal("4"):
        disqualified = True
        warning_items.append("累计工作满20年以上，请病假累计4个月以上的，不享受当年年休假。")

    return success(
        "eligibility_check",
        {
            "cumulative_years": cumulative_years,
            "annual_leave_days": annual_days,
            "disqualified_current_year": disqualified,
            "warnings": warning_items,
            "legal_basis": LAW_BASIS["exceptions"],
        },
    )


def excel_col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def safe_xml_text(value: Any) -> str:
    return str(value).encode("utf-8", errors="replace").decode("utf-8")


def inline_string_cell(ref: str, value: Any, style: int = 0) -> str:
    style_attr = f' s="{style}"' if style else ""
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{escape(safe_xml_text(value))}</t></is></c>'


def number_cell(ref: str, value: Decimal, style: int = 0, formula: Optional[str] = None) -> str:
    style_attr = f' s="{style}"' if style else ""
    if formula:
        return f'<c r="{ref}"{style_attr}><f>{escape(formula)}</f></c>'
    return f'<c r="{ref}"{style_attr}><v>{money_text(value)}</v></c>'


def build_sheet_xml(rows: list[dict[str, Any]]) -> str:
    headers = ["序号", "项目", "计算基数与过程", "金额（元）", "备注/法律依据"]
    xml_rows: list[str] = []
    header_cells = [
        inline_string_cell(f"{excel_col(index)}1", header, 1)
        for index, header in enumerate(headers, start=1)
    ]
    xml_rows.append(f'<row r="1">{"".join(header_cells)}</row>')

    for row_index, row in enumerate(rows, start=2):
        amount = decimal_arg(row.get("amount", "0"), "rows[].amount")
        note = row.get("note") or row.get("legal_basis") or ""
        process = row.get("process") or row.get("formula") or ""
        cells = [
            inline_string_cell(f"A{row_index}", row_index - 1),
            inline_string_cell(f"B{row_index}", row.get("item", "")),
            inline_string_cell(f"C{row_index}", process),
            number_cell(f"D{row_index}", amount, 2),
            inline_string_cell(f"E{row_index}", note),
        ]
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    total_row = len(rows) + 2
    last_data_row = len(rows) + 1
    formula = f"SUM(D2:D{last_data_row})" if rows else "0"
    total_cells = [
        inline_string_cell(f"A{total_row}", "合计", 1),
        inline_string_cell(f"B{total_row}", ""),
        inline_string_cell(f"C{total_row}", ""),
        number_cell(f"D{total_row}", ZERO, 3, formula=formula),
        inline_string_cell(f"E{total_row}", ""),
    ]
    xml_rows.append(f'<row r="{total_row}">{"".join(total_cells)}</row>')

    cols = (
        '<cols>'
        '<col min="1" max="1" width="8" customWidth="1"/>'
        '<col min="2" max="2" width="28" customWidth="1"/>'
        '<col min="3" max="3" width="52" customWidth="1"/>'
        '<col min="4" max="4" width="14" customWidth="1"/>'
        '<col min="5" max="5" width="42" customWidth="1"/>'
        '</cols>'
    )
    dimension = f"A1:E{total_row}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        f"{cols}"
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def write_xlsx(path: Path, rows: list[dict[str, Any]]) -> None:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="未休年休假明细" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.00"/></numFmts>'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="4">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
        '<xf numFmtId="164" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyNumberFormat="1"/>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", styles)
        archive.writestr("xl/worksheets/sheet1.xml", build_sheet_xml(rows))


def export_to_excel(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") or payload.get("detail_rows")
    if not isinstance(rows, list):
        raise CalculationError("export_to_excel 需要 rows 或 detail_rows 数组")

    output_path = Path(str(payload.get("output_path") or "unused_annual_leave_detail.xlsx"))
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    normalized_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            raise CalculationError("rows 中的每一项都必须是对象")
        normalized_rows.append(item)

    write_xlsx(output_path, normalized_rows)
    total = sum((decimal_arg(row.get("amount", "0"), "rows[].amount") for row in normalized_rows), ZERO)
    return success(
        "export_to_excel",
        {
            "output_path": output_path,
            "row_count": len(normalized_rows),
            "total_amount": money(total),
            "style_note": "表头和合计行仅加粗；金额列使用 #,##0.00；合计行使用 SUM 公式。",
        },
    )


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if not action:
        raise CalculationError("缺少 action")

    handlers = {
        "annual_leave_days": lambda data: success(
            "annual_leave_days",
            {
                "annual_leave_days": resolve_annual_leave_days(data)[0],
                "annual_leave_days_source": resolve_annual_leave_days(data)[1],
                "legal_basis": LAW_BASIS["annual_days"],
            },
        ),
        "daily_wage": lambda data: success("daily_wage", daily_wage(data)),
        "new_employee": new_employee,
        "resignation": resignation,
        "in_service": in_service,
        "eligibility_check": eligibility_check,
        "export_to_excel": export_to_excel,
    }
    if action not in handlers:
        raise CalculationError(f"不支持的 action：{action}")
    return handlers[action](payload)


def load_payload(argv: list[str]) -> dict[str, Any]:
    if len(argv) >= 2:
        raw = argv[1]
        if raw.startswith("@"):
            raw = Path(raw[1:]).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        raise CalculationError("请通过命令行参数或 stdin 传入 JSON")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CalculationError(f"JSON 解析失败：{exc}") from exc
    if not isinstance(payload, dict):
        raise CalculationError("顶层 JSON 必须是对象")
    return payload


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv
    try:
        payload = load_payload(argv)
        result = dispatch(payload)
    except CalculationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(json_ready(result), ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "annual_leave_days_by_years",
    "daily_wage",
    "new_employee",
    "resignation",
    "in_service",
    "eligibility_check",
    "export_to_excel",
    "dispatch",
]


if __name__ == "__main__":
    raise SystemExit(main())
