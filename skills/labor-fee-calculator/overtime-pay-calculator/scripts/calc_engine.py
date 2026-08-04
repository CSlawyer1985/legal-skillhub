#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any, Optional
from xml.sax.saxutils import escape

from policy_data import PolicyDataError, get_policy_data, policy_api_url

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

getcontext().prec = 28

BASE_DIR = Path(__file__).resolve().parent.parent

ZERO = Decimal("0")
MONTHLY_PAID_DAYS = Decimal("21.75")
HOURS_PER_DAY = Decimal("8")
MULTIPLIER_WEEKDAY = Decimal("1.5")
MULTIPLIER_RESTDAY = Decimal("2")
MULTIPLIER_HOLIDAY = Decimal("3")

POLICY_DATA_KEYS = ("policy_data", "policy")
INLINE_POLICY_FIELDS = ("min_wage", "worktime_params", "statutory_holiday_rules")
REGION_KEYS = ("region", "province", "city")
WAGE_COMPONENT_KEYS = (
    "base",
    "basic",
    "contract_wage",
    "bonus",
    "allowance",
    "subsidy",
    "overtime",
)
RESTDAY_COMPENSATION_KEYS = ("restday_compensated", "restday_compensatory_leave", "arranged_rest")
REGION_NORMALIZATION_TERMS = ("省", "市", "自治区", "壮族", "回族", "维吾尔", "特别行政区")
DIRECT_REGION_ALIASES = {"北京", "天津", "上海", "重庆", "内蒙古", "广西", "宁夏", "新疆", "西藏"}
SHEET_HEADERS = ("序号", "加班类型", "加班时长", "计算过程", "金额（元）", "法条依据")
WHITESPACE_RE = re.compile(r"\s+")

STANDARD_CYCLE_HOURS = {
    "week": Decimal("40"),
    "weekly": Decimal("40"),
    "周": Decimal("40"),
    "月": Decimal("165.33"),
    "month": Decimal("165.33"),
    "monthly": Decimal("165.33"),
    "季": Decimal("496"),
    "quarter": Decimal("496"),
    "quarterly": Decimal("496"),
    "年": Decimal("1984"),
    "year": Decimal("1984"),
    "yearly": Decimal("1984"),
}

CYCLE_ALIASES = {
    "week": "week",
    "weekly": "week",
    "周": "week",
    "month": "month",
    "monthly": "month",
    "月": "month",
    "quarter": "quarter",
    "quarterly": "quarter",
    "季": "quarter",
    "year": "year",
    "yearly": "year",
    "年": "year",
}

LAW_BASIS = {
    "wage_conversion": "人社部发〔2025〕2号",
    "weekday": "《劳动法》第四十四条第（一）项；《工资支付暂行规定》第十三条第（一）项",
    "restday": "《劳动法》第四十四条第（二）项；《工资支付暂行规定》第十三条第（二）项",
    "holiday": "《劳动法》第四十四条第（三）项；《工资支付暂行规定》第十三条第（三）项",
    "comprehensive": "《工资支付暂行规定》第十三条第二款",
    "irregular": "《工资支付暂行规定》第十三条第四款",
    "piece_rate": "《工资支付暂行规定》第十三条第三款",
    "minimum_wage": "《劳动法》第四十八条",
}


class CalculationError(Exception):
    """Raised for invalid input or unsupported calculation requests."""


@dataclass
class DetailRow:
    overtime_type: str
    quantity: str
    rate: str
    formula: str
    amount: Decimal
    legal_basis: str
    note: str = ""


def decimal_arg(value: Any, field_name: str = "数值") -> Decimal:
    if value is None or value == "":
        raise CalculationError(f"{field_name}不能为空")
    try:
        result = Decimal(str(value).replace(",", ""))
    except Exception as exc:
        raise CalculationError(f"{field_name}不是有效数字：{value}") from exc
    return result


def optional_decimal(value: Any, default: Decimal = ZERO, field_name: str = "数值") -> Decimal:
    if value is None or value == "":
        return default
    return decimal_arg(value, field_name)


def non_negative(value: Decimal, field_name: str) -> Decimal:
    if value < 0:
        raise CalculationError(f"{field_name}不得为负数")
    return value


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_text(value: Decimal, places: str = "0.00") -> str:
    return str(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def money_text(value: Decimal) -> str:
    return decimal_text(money(value))


def rate_text(rate: Decimal) -> str:
    value = (rate * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    text = format(value, "f").rstrip("0").rstrip(".")
    return f"{text}%"


def json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return money_text(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, DetailRow):
        return json_ready(asdict(value))
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    return value


def success(action: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "action": action, **data}


def response_envelope(success_value: bool, body: dict[str, Any]) -> dict[str, Any]:
    return {"success": success_value, "msg": "", "body": body}


def cli_response(result: dict[str, Any]) -> dict[str, Any]:
    body = dict(result)
    success_value = bool(body.pop("ok", True))
    return response_envelope(success_value, body)


def policy_data_for_calc(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return get_policy_data(payload)
    except PolicyDataError as exc:
        raise CalculationError(str(exc)) from exc


def first_payload_value(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    return next((payload[key] for key in keys if payload.get(key)), "")


def has_inline_policy_data(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in POLICY_DATA_KEYS + INLINE_POLICY_FIELDS)


def payload_with_policy_data(payload: dict[str, Any]) -> dict[str, Any]:
    if has_inline_policy_data(payload):
        return payload
    if not first_payload_value(payload, REGION_KEYS):
        return payload

    prepared = dict(payload)
    prepared["policy_data"] = policy_data_for_calc(payload)
    return prepared


def policy_decimal(value: Any, default: Decimal, field_name: str) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise CalculationError(f"{field_name} 不是有效数字：{value}") from exc


def worktime_params(payload: dict[str, Any]) -> dict[str, Any]:
    policy_data = policy_data_for_calc(payload)
    raw = policy_data.get("worktime_params")
    return raw if isinstance(raw, dict) else {}


def monthly_paid_days_from_payload(payload: dict[str, Any]) -> Decimal:
    params = worktime_params(payload)
    return policy_decimal(params.get("monthly_paid_days"), MONTHLY_PAID_DAYS, "policy_data.worktime_params.monthly_paid_days")


def hours_per_day_from_payload(payload: dict[str, Any]) -> Decimal:
    params = worktime_params(payload)
    return policy_decimal(params.get("hours_per_day"), HOURS_PER_DAY, "policy_data.worktime_params.hours_per_day")


def law_basis(payload: dict[str, Any], key: str) -> str:
    policy_data = policy_data_for_calc(payload)
    basis = policy_data.get("law_basis")
    if isinstance(basis, dict):
        value = basis.get(key)
        if value:
            return str(value)
    return LAW_BASIS.get(key, "")


def resolve_monthly_wage(payload: dict[str, Any]) -> tuple[Decimal, str]:
    if "monthly_wage" in payload:
        monthly_wage = decimal_arg(payload["monthly_wage"], "monthly_wage")
        return monthly_wage, "monthly_wage"

    if "annual_salary" in payload:
        annual_salary = decimal_arg(payload["annual_salary"], "annual_salary")
        return annual_salary / Decimal("12"), "annual_salary / 12"

    if "monthly_wages" in payload:
        raw_items = payload["monthly_wages"]
        if not isinstance(raw_items, list) or not raw_items:
            raise CalculationError("monthly_wages 必须是非空数组")
        wages = [decimal_arg(item, "monthly_wages[]") for item in raw_items]
        return sum(wages, ZERO) / Decimal(len(wages)), "average(monthly_wages)"

    if "wage_components" in payload:
        raw_components = payload["wage_components"]
        if not isinstance(raw_components, dict):
            raise CalculationError("wage_components 必须是对象")
        total = sum(
            (
                optional_decimal(raw_components.get(key), ZERO, f"wage_components.{key}")
                for key in WAGE_COMPONENT_KEYS
            ),
            ZERO,
        )
        return total, "sum(wage_components included items)"

    raise CalculationError("缺少 monthly_wage、annual_salary、monthly_wages 或 wage_components")


def resolve_hourly_wage(payload: dict[str, Any]) -> tuple[Decimal, list[str]]:
    if "hourly_wage" in payload:
        hourly_wage = decimal_arg(payload["hourly_wage"], "hourly_wage")
        if hourly_wage <= 0:
            raise CalculationError("hourly_wage 必须大于0")
        return hourly_wage, []

    monthly_wage, source = resolve_monthly_wage(payload)
    if monthly_wage <= 0:
        raise CalculationError(f"{source} 得出的月工资基数必须大于0")
    converted = wage_conversion({"monthly_wage": monthly_wage, "policy_data": policy_data_for_calc(payload)})
    hourly = Decimal(converted["hourly_wage"])
    return hourly, [f"未提供 hourly_wage，已按 {source} 折算小时工资。"]


def hours_from_payload(payload: dict[str, Any], prefix: str) -> Decimal:
    hours = optional_decimal(payload.get(f"{prefix}_hours"), ZERO, f"{prefix}_hours")
    days = optional_decimal(payload.get(f"{prefix}_days"), ZERO, f"{prefix}_days")
    return non_negative(hours + days * hours_per_day_from_payload(payload), prefix)


def wage_conversion(payload: dict[str, Any]) -> dict[str, Any]:
    monthly_wage, source = resolve_monthly_wage(payload)
    if monthly_wage <= 0:
        raise CalculationError("月工资基数必须大于0")

    monthly_paid_days = monthly_paid_days_from_payload(payload)
    hours_per_day = hours_per_day_from_payload(payload)
    monthly_paid_hours = monthly_paid_days * hours_per_day
    daily_wage = monthly_wage / monthly_paid_days
    hourly_wage = daily_wage / hours_per_day
    return {
        "monthly_wage": monthly_wage,
        "monthly_wage_source": source,
        "monthly_paid_days": monthly_paid_days,
        "monthly_paid_hours": monthly_paid_hours,
        "daily_wage": money(daily_wage),
        "hourly_wage": money(hourly_wage),
        "formula": f"日工资 = 月工资基数 ÷ {monthly_paid_days}；小时工资 = 日工资 ÷ {hours_per_day}",
        "legal_basis": law_basis(payload, "wage_conversion"),
    }


def calculate_amount(base: Decimal, quantity: Decimal, multiplier: Decimal) -> Decimal:
    if base <= 0:
        raise CalculationError("计算基数必须大于0")
    if quantity < 0:
        raise CalculationError("数量不得为负数")
    return money(base * quantity * multiplier)


def build_overtime_row(
    *,
    overtime_type: str,
    base_label: str,
    base_value: Decimal,
    quantity: Decimal,
    quantity_unit: str,
    multiplier: Decimal,
    legal_basis: str,
    note: str = "",
) -> DetailRow:
    amount = calculate_amount(base_value, quantity, multiplier)
    return DetailRow(
        overtime_type=overtime_type,
        quantity=f"{decimal_text(quantity)}{quantity_unit}",
        rate=rate_text(multiplier),
        formula=f"{base_label}{money_text(base_value)} × {decimal_text(quantity)}{quantity_unit} × {rate_text(multiplier)}",
        amount=amount,
        legal_basis=legal_basis,
        note=note,
    )


def standard_overtime(payload: dict[str, Any]) -> dict[str, Any]:
    hourly_wage, assumptions = resolve_hourly_wage(payload)
    weekday_hours = hours_from_payload(payload, "weekday")
    restday_hours = hours_from_payload(payload, "restday")
    holiday_hours = hours_from_payload(payload, "holiday")
    restday_compensated = any(payload.get(key) for key in RESTDAY_COMPENSATION_KEYS)

    rows: list[DetailRow] = []
    if weekday_hours:
        rows.append(
            build_overtime_row(
                overtime_type="工作日延长工作时间",
                base_label="小时工资",
                base_value=hourly_wage,
                quantity=weekday_hours,
                quantity_unit="小时",
                multiplier=MULTIPLIER_WEEKDAY,
                legal_basis=law_basis(payload, "weekday"),
                note="工作日加班不可用补休替代。",
            )
        )

    if restday_hours:
        if restday_compensated:
            rows.append(
                DetailRow(
                    overtime_type="休息日加班",
                    quantity=f"{decimal_text(restday_hours)}小时",
                    rate="200%",
                    formula="已安排补休，休息日加班费按0元列示",
                    amount=ZERO,
                    legal_basis=law_basis(payload, "restday"),
                    note="休息日加班已安排补休的，可不另行支付200%加班费。",
                )
            )
        else:
            rows.append(
                build_overtime_row(
                    overtime_type="休息日加班",
                    base_label="小时工资",
                    base_value=hourly_wage,
                    quantity=restday_hours,
                    quantity_unit="小时",
                    multiplier=MULTIPLIER_RESTDAY,
                    legal_basis=law_basis(payload, "restday"),
                    note="未安排补休时支付200%加班费。",
                )
            )

    if holiday_hours:
        rows.append(
            build_overtime_row(
                overtime_type="法定节假日加班",
                base_label="小时工资",
                base_value=hourly_wage,
                quantity=holiday_hours,
                quantity_unit="小时",
                multiplier=MULTIPLIER_HOLIDAY,
                legal_basis=law_basis(payload, "holiday"),
                note="法定节假日加班不得以补休替代。",
            )
        )

    return overtime_result(
        action="standard_overtime",
        hourly_wage=hourly_wage,
        rows=rows,
        assumptions=assumptions,
        warnings=[],
        meta={"work_time_system": "标准工时制"},
    )


def resolve_cycle_hours(payload: dict[str, Any]) -> tuple[Decimal, str]:
    if "cycle_hours" in payload:
        cycle_hours = decimal_arg(payload["cycle_hours"], "cycle_hours")
        if cycle_hours <= 0:
            raise CalculationError("cycle_hours 必须大于0")
        return cycle_hours, "payload.cycle_hours"

    cycle = str(payload.get("cycle") or payload.get("cycle_type") or "").strip().lower()
    if not cycle:
        raise CalculationError("缺少 cycle_hours；也可传 cycle=week/month/quarter/year")
    canonical_cycle = CYCLE_ALIASES.get(cycle)
    if not canonical_cycle:
        raise CalculationError("cycle 仅支持 week/month/quarter/year 或 周/月/季/年")

    params = worktime_params(payload)
    cycle_hours = params.get("cycle_standard_hours") if isinstance(params.get("cycle_standard_hours"), dict) else {}
    if canonical_cycle in cycle_hours:
        return (
            policy_decimal(
                cycle_hours[canonical_cycle],
                STANDARD_CYCLE_HOURS[canonical_cycle],
                f"policy_data.worktime_params.cycle_standard_hours.{canonical_cycle}",
            ),
            f"policy_data.worktime_params.cycle_standard_hours.{canonical_cycle}",
        )
    return STANDARD_CYCLE_HOURS[canonical_cycle], f"2025年起{canonical_cycle}周期法定标准工时"


def comprehensive_overtime(payload: dict[str, Any]) -> dict[str, Any]:
    hourly_wage, assumptions = resolve_hourly_wage(payload)
    cycle_hours, cycle_source = resolve_cycle_hours(payload)
    actual_hours = non_negative(decimal_arg(payload.get("actual_hours"), "actual_hours"), "actual_hours")
    holiday_hours = hours_from_payload(payload, "holiday")
    if holiday_hours > actual_hours:
        raise CalculationError("holiday_hours 不应大于 actual_hours")

    excess_hours = max(actual_hours - cycle_hours, ZERO)
    rows: list[DetailRow] = []
    if excess_hours:
        rows.append(
            build_overtime_row(
                overtime_type="综合周期超出法定标准工时",
                base_label="小时工资",
                base_value=hourly_wage,
                quantity=excess_hours,
                quantity_unit="小时",
                multiplier=MULTIPLIER_WEEKDAY,
                legal_basis=law_basis(payload, "comprehensive"),
                note="休息日工作已纳入综合周期总工时，不单独计算。",
            )
        )
    if holiday_hours:
        rows.append(
            build_overtime_row(
                overtime_type="综合工时制法定节假日加班",
                base_label="小时工资",
                base_value=hourly_wage,
                quantity=holiday_hours,
                quantity_unit="小时",
                multiplier=MULTIPLIER_HOLIDAY,
                legal_basis=law_basis(payload, "holiday"),
                note="法定节假日工作时间同时计入周期总工时。",
            )
        )

    return overtime_result(
        action="comprehensive_overtime",
        hourly_wage=hourly_wage,
        rows=rows,
        assumptions=assumptions,
        warnings=[],
        meta={
            "work_time_system": "综合计算工时制",
            "cycle_hours": cycle_hours,
            "cycle_hours_source": cycle_source,
            "actual_hours": actual_hours,
            "excess_hours": excess_hours,
        },
    )


def irregular_overtime(payload: dict[str, Any]) -> dict[str, Any]:
    hourly_wage, assumptions = resolve_hourly_wage(payload)
    holiday_hours = hours_from_payload(payload, "holiday")
    rows: list[DetailRow] = []
    if holiday_hours:
        rows.append(
            build_overtime_row(
                overtime_type="不定时工时制法定节假日加班",
                base_label="小时工资",
                base_value=hourly_wage,
                quantity=holiday_hours,
                quantity_unit="小时",
                multiplier=MULTIPLIER_HOLIDAY,
                legal_basis=law_basis(payload, "holiday"),
                note="不定时工时制通常仅计算法定节假日加班；地方特殊规定需另行核验。",
            )
        )
    return overtime_result(
        action="irregular_overtime",
        hourly_wage=hourly_wage,
        rows=rows,
        assumptions=assumptions,
        warnings=["不定时工时制须经劳动行政部门批准；上海、深圳等地特殊规则需结合当地规定复核。"],
        meta={"work_time_system": "不定时工时制"},
    )


def piece_rate_overtime(payload: dict[str, Any]) -> dict[str, Any]:
    piece_price = decimal_arg(payload.get("piece_price"), "piece_price")
    if piece_price <= 0:
        raise CalculationError("piece_price 必须大于0")

    quota_completed = payload.get("quota_completed", True)
    if quota_completed is False:
        return overtime_result(
            action="piece_rate_overtime",
            hourly_wage=ZERO,
            rows=[],
            assumptions=[],
            warnings=["计件加班费以劳动者已完成计件定额任务为前提；当前 quota_completed=false，脚本不计算倍率加班费。"],
            meta={"work_time_system": "计件工资制", "piece_price": piece_price},
        )

    quantities = {
        "weekday": non_negative(optional_decimal(payload.get("weekday_qty"), ZERO, "weekday_qty"), "weekday_qty"),
        "restday": non_negative(optional_decimal(payload.get("restday_qty"), ZERO, "restday_qty"), "restday_qty"),
        "holiday": non_negative(optional_decimal(payload.get("holiday_qty"), ZERO, "holiday_qty"), "holiday_qty"),
    }
    row_specs = [
        ("weekday", "计件工资制工作日加班", MULTIPLIER_WEEKDAY, law_basis(payload, "piece_rate")),
        ("restday", "计件工资制休息日加班", MULTIPLIER_RESTDAY, law_basis(payload, "piece_rate")),
        ("holiday", "计件工资制法定节假日加班", MULTIPLIER_HOLIDAY, law_basis(payload, "piece_rate")),
    ]
    rows = [
        build_overtime_row(
            overtime_type=label,
            base_label="计件单价",
            base_value=piece_price,
            quantity=quantities[key],
            quantity_unit="件",
            multiplier=multiplier,
            legal_basis=basis,
            note="仅对完成定额任务后的加班产量按倍率计算。",
        )
        for key, label, multiplier, basis in row_specs
        if quantities[key]
    ]
    return overtime_result(
        action="piece_rate_overtime",
        hourly_wage=ZERO,
        rows=rows,
        assumptions=[],
        warnings=[],
        meta={"work_time_system": "计件工资制", "piece_price": piece_price},
    )


def overtime_result(
    *,
    action: str,
    hourly_wage: Decimal,
    rows: list[DetailRow],
    assumptions: list[str],
    warnings: list[str],
    meta: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    total = money(sum((row.amount for row in rows), ZERO))
    result = {
        "hourly_wage": hourly_wage if hourly_wage else None,
        "detail_rows": rows,
        "total_overtime_pay": total,
        "assumptions": assumptions,
        "warnings": warnings,
    }
    if meta:
        result.update(meta)
    return success(action, result)


def normalize_region(region: str) -> str:
    text = WHITESPACE_RE.sub("", str(region or ""))
    if not text:
        raise CalculationError("region 不能为空")
    if "深圳" in text:
        return "深圳"

    normalized = text
    for item in REGION_NORMALIZATION_TERMS:
        normalized = normalized.replace(item, "")

    if normalized in DIRECT_REGION_ALIASES:
        return normalized
    return normalized


def min_wage_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        lookup = min_wage_lookup_from_policy(payload)
    except CalculationError as exc:
        region_raw = first_payload_value(payload, REGION_KEYS)
        return success(
            "min_wage_lookup",
            {
                "region": normalize_region(str(region_raw)) if region_raw else "",
                "found": False,
                "needs_web_search": True,
                "message": f"政策数据 API 未返回可用最低工资数据：{exc}",
                "source": policy_api_url(),
            },
        )
    if lookup:
        return lookup
    return success(
        "min_wage_lookup",
        {
            "region": "",
            "found": False,
            "needs_web_search": True,
            "message": "政策数据 API 未返回 min_wage，建议进入最多两轮联网检索兜底。",
            "source": policy_api_url(),
        },
    )


def min_wage_lookup_from_policy(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    policy_data = policy_data_for_calc(payload)
    raw_min_wage = policy_data.get("min_wage")
    if not isinstance(raw_min_wage, dict) or raw_min_wage.get("monthly_min_wage") in (None, ""):
        return None

    region_raw = first_payload_value(payload, REGION_KEYS)
    region = normalize_region(str(region_raw)) if region_raw else ""
    return success(
        "min_wage_lookup",
        {
            "region": region,
            "found": True,
            "period": raw_min_wage.get("period", ""),
            "period_date": raw_min_wage.get("period_date"),
            "monthly_min_wage": decimal_arg(raw_min_wage["monthly_min_wage"], "policy_data.min_wage.monthly_min_wage"),
            "hourly_min_wage": (
                optional_decimal(raw_min_wage.get("hourly_min_wage"), ZERO, "policy_data.min_wage.hourly_min_wage")
                if raw_min_wage.get("hourly_min_wage") not in (None, "")
                else None
            ),
            "source": "policy_data.min_wage",
            "scope_note": "最低工资数据来自政策数据 API/快照；具体城市/区县档次仍需按当地最新文件复核。",
        },
    )


def minimum_wage_check(payload: dict[str, Any]) -> dict[str, Any]:
    monthly_wage, wage_source = resolve_monthly_wage(payload)
    lookup = min_wage_lookup(payload)
    if not lookup.get("found"):
        lookup_data = {key: value for key, value in lookup.items() if key not in {"ok", "action"}}
        lookup_data.update({"monthly_wage": monthly_wage, "monthly_wage_source": wage_source})
        return success("minimum_wage_check", lookup_data)

    min_wage = Decimal(str(lookup["monthly_min_wage"]))
    below = monthly_wage < min_wage
    warning = ""
    if below:
        warning = "月工资基数低于本地参考最低工资标准，可能涉及最低工资违法；加班费仍按实际工资基数计算并在结论中注明风险。"

    return success(
        "minimum_wage_check",
        {
            "region": lookup["region"],
            "period": lookup["period"],
            "monthly_wage": monthly_wage,
            "monthly_wage_source": wage_source,
            "monthly_min_wage": min_wage,
            "hourly_min_wage": lookup.get("hourly_min_wage"),
            "below_minimum_wage": below,
            "warning": warning,
            "legal_basis": law_basis(payload, "minimum_wage"),
            "source": lookup["source"],
            "scope_note": lookup["scope_note"],
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
    xml_rows: list[str] = []
    header_cells = [
        inline_string_cell(f"{excel_col(index)}1", header, 1)
        for index, header in enumerate(SHEET_HEADERS, start=1)
    ]
    xml_rows.append(f'<row r="1">{"".join(header_cells)}</row>')

    for row_index, row in enumerate(rows, start=2):
        amount = Decimal(str(row.get("amount", "0")).replace(",", ""))
        cells = [
            inline_string_cell(f"A{row_index}", row_index - 1),
            inline_string_cell(f"B{row_index}", row.get("overtime_type", "")),
            inline_string_cell(f"C{row_index}", row.get("quantity", "")),
            inline_string_cell(f"D{row_index}", row.get("formula", "")),
            number_cell(f"E{row_index}", amount, 2),
            inline_string_cell(f"F{row_index}", row.get("legal_basis", "")),
        ]
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    total_row = len(rows) + 2
    last_data_row = len(rows) + 1
    formula = f"SUM(E2:E{last_data_row})" if rows else "0"
    total_cells = [
        inline_string_cell(f"A{total_row}", "合计", 1),
        inline_string_cell(f"B{total_row}", ""),
        inline_string_cell(f"C{total_row}", ""),
        inline_string_cell(f"D{total_row}", ""),
        number_cell(f"E{total_row}", ZERO, 3, formula=formula),
        inline_string_cell(f"F{total_row}", ""),
    ]
    xml_rows.append(f'<row r="{total_row}">{"".join(total_cells)}</row>')

    cols = (
        '<cols>'
        '<col min="1" max="1" width="8" customWidth="1"/>'
        '<col min="2" max="2" width="24" customWidth="1"/>'
        '<col min="3" max="3" width="16" customWidth="1"/>'
        '<col min="4" max="4" width="44" customWidth="1"/>'
        '<col min="5" max="5" width="14" customWidth="1"/>'
        '<col min="6" max="6" width="34" customWidth="1"/>'
        '</cols>'
    )
    dimension = f"A1:F{total_row}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        f"{cols}"
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def write_xlsx(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    xlsx_parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="加班费明细" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>'
        ),
        "xl/styles.xml": (
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
        ),
        "xl/worksheets/sheet1.xml": build_sheet_xml(rows),
    }

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_path, content in xlsx_parts.items():
            archive.writestr(archive_path, content)


def export_rows(payload: dict[str, Any], missing_message: str) -> list[dict[str, Any]]:
    rows = payload.get("rows") or payload.get("detail_rows")
    if not isinstance(rows, list):
        raise CalculationError(missing_message)
    normalized_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            raise CalculationError("rows 中的每一项都必须是对象")
        normalized_rows.append(item)
    return normalized_rows


def export_output_path(payload: dict[str, Any], default_name: str) -> Path:
    output_path = Path(str(payload.get("output_path") or default_name))
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    return output_path


def export_to_excel(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_rows = export_rows(payload, "export_to_excel 需要 rows 或 detail_rows 数组")
    output_path = export_output_path(payload, "overtime_pay_detail.xlsx")
    write_xlsx(output_path, normalized_rows)
    total = sum((decimal_arg(row.get("amount", "0"), "rows[].amount") for row in normalized_rows), ZERO)
    return success(
        "export_to_excel",
        {
            "output_path": output_path,
            "row_count": len(normalized_rows),
            "total_overtime_pay": money(total),
            "style_note": "表头和合计行仅加粗；金额列使用 #,##0.00；合计行使用 SUM 公式。",
        },
    )


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if not action:
        raise CalculationError("缺少 action")

    handlers = {
        "wage_conversion": lambda data: success("wage_conversion", wage_conversion(data)),
        "standard_overtime": standard_overtime,
        "comprehensive_overtime": comprehensive_overtime,
        "irregular_overtime": irregular_overtime,
        "irregular_working_hours_overtime": irregular_overtime,
        "piece_rate_overtime": piece_rate_overtime,
        "min_wage_lookup": min_wage_lookup,
        "minimum_wage_check": minimum_wage_check,
        "export_to_excel": export_to_excel,
    }
    if action not in handlers:
        raise CalculationError(f"不支持的 action：{action}")
    calculation_payload = payload if action == "export_to_excel" else payload_with_policy_data(payload)
    return handlers[action](calculation_payload)


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
        print(json.dumps(response_envelope(False, {"error": str(exc)}), ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(json_ready(cli_response(result)), ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "wage_conversion",
    "standard_overtime",
    "comprehensive_overtime",
    "irregular_overtime",
    "piece_rate_overtime",
    "min_wage_lookup",
    "minimum_wage_check",
    "export_to_excel",
    "dispatch",
]

if __name__ == "__main__":
    raise SystemExit(main())
