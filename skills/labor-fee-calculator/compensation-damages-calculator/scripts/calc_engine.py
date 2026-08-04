#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import date
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
ONE = Decimal("1")
THREE = Decimal("3")
TWELVE = Decimal("12")

POLICY_DATA_KEYS = ("policy_data", "policy")
INLINE_POLICY_FIELDS = ("min_wage", "social_avg_wage", "law_basis", "law_articles_text", "notes")
REGION_KEYS = ("region", "province", "city")
REGION_NORMALIZATION_TERMS = ("省", "市", "自治区", "壮族", "回族", "维吾尔", "特别行政区")
DIRECT_REGION_ALIASES = {"北京", "天津", "上海", "重庆", "内蒙古", "广西", "宁夏", "新疆", "西藏"}
WHITESPACE_RE = re.compile(r"\s+")

LAW_BASIS = {
    "no_contract": "《劳动合同法》第十条、第八十二条；《劳动合同法实施条例》第六条、第七条；法释〔2025〕12号第六条、第七条、第九条",
    "calc_s": "《劳动合同法》第四十七条；《劳动合同法实施条例》第二十七条",
    "calc_n": "《劳动合同法》第四十七条",
    "compensation_n": "《劳动合同法》第四十六条、第四十七条",
    "n_plus_1": "《劳动合同法》第四十条、第四十六条、第四十七条；《劳动合同法实施条例》第二十条",
    "illegal_2n": "《劳动合同法》第八十七条；《劳动合同法实施条例》第二十五条",
    "non_compete": "《劳动合同法》第二十三条、第二十四条；劳动争议司法解释四第六条、第九条；法释〔2025〕12号第十三条、第十四条、第十五条",
    "min_wage": "《劳动法》第四十八条；《劳动合同法实施条例》第二十七条",
    "social_avg": "《劳动合同法》第四十七条第二款",
}


class CalculationError(Exception):
    """Raised for invalid input or unsupported calculation requests."""


@dataclass
class DetailRow:
    category: str
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


def parse_ym(year: Any, month: Any, prefix: str) -> tuple[int, int]:
    if year is None or month is None:
        raise CalculationError(f"缺少 {prefix}_year 或 {prefix}_month")
    y = int(year)
    m = int(month)
    if not 1 <= m <= 12:
        raise CalculationError(f"{prefix}_month 必须在1-12之间")
    return y, m


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_text(value: Decimal) -> str:
    return format(money(value), "f")


def decimal_text(value: Decimal, places: str = "0.00") -> str:
    return format(value.quantize(Decimal(places), rounding=ROUND_HALF_UP), "f")


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


def response_envelope(success_value: bool, body: dict[str, Any]) -> dict[str, Any]:
    return {"success": success_value, "msg": "", "body": body}


def cli_response(result: dict[str, Any]) -> dict[str, Any]:
    body = dict(result)
    success_value = bool(body.pop("ok", True))
    return response_envelope(success_value, body)


def first_payload_value(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    return next((payload[key] for key in keys if payload.get(key)), "")


def policy_data_for_calc(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return get_policy_data(payload)
    except PolicyDataError as exc:
        raise CalculationError(str(exc)) from exc


def policy_data_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("policy_data") or payload.get("policy")
    if isinstance(raw, dict):
        return raw
    if any(key in payload for key in INLINE_POLICY_FIELDS):
        return payload
    return {}


def has_inline_policy_data(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in POLICY_DATA_KEYS + INLINE_POLICY_FIELDS)


def payload_needs_policy_data(action: str, payload: dict[str, Any]) -> bool:
    if has_inline_policy_data(payload):
        return False
    if not first_payload_value(payload, REGION_KEYS):
        return False
    if action in {"min_wage_lookup", "social_avg_wage_lookup"}:
        return True
    if action in {"calc_s", "no_contract", "non_compete"}:
        return payload.get("local_min_wage") in (None, "")
    if action in {"compensation_n", "n_plus_1"}:
        return payload.get("social_avg_monthly") in (None, "")
    return False


def payload_with_policy_data(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not payload_needs_policy_data(action, payload):
        return payload
    prepared = dict(payload)
    prepared["policy_data"] = policy_data_for_calc(payload)
    return prepared


def policy_decimal(value: Any, default: Decimal, field_name: str) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value).replace(",", ""))
    except Exception as exc:
        raise CalculationError(f"{field_name} 不是有效数字：{value}") from exc


def law_basis(payload: dict[str, Any], key: str) -> str:
    policy_data = policy_data_from_payload(payload)
    basis = policy_data.get("law_basis")
    if isinstance(basis, dict):
        value = basis.get(key)
        if value:
            return str(value)
    return LAW_BASIS.get(key, "")


def local_min_wage_from_payload(payload: dict[str, Any]) -> Decimal:
    if payload.get("local_min_wage") not in (None, ""):
        return decimal_arg(payload.get("local_min_wage"), "local_min_wage")
    policy_data = policy_data_from_payload(payload)
    min_wage = policy_data.get("min_wage")
    if isinstance(min_wage, dict):
        return policy_decimal(min_wage.get("monthly_min_wage"), ZERO, "policy_data.min_wage.monthly_min_wage")
    return ZERO


def social_avg_monthly_from_payload(payload: dict[str, Any]) -> Decimal:
    if payload.get("social_avg_monthly") not in (None, ""):
        return decimal_arg(payload.get("social_avg_monthly"), "social_avg_monthly")
    policy_data = policy_data_from_payload(payload)
    social_avg = policy_data.get("social_avg_wage")
    if isinstance(social_avg, dict):
        return policy_decimal(social_avg.get("monthly_avg_wage"), ZERO, "policy_data.social_avg_wage.monthly_avg_wage")
    return ZERO


def wage_caliber_from_payload(payload: dict[str, Any]) -> str:
    if payload.get("wage_caliber"):
        return repair_mojibake(str(payload.get("wage_caliber")))
    policy_data = policy_data_from_payload(payload)
    social_avg = policy_data.get("social_avg_wage")
    if isinstance(social_avg, dict):
        return str(social_avg.get("wage_caliber_label") or social_avg.get("wage_caliber") or "未提供")
    return "未提供"


def repair_mojibake(text: str) -> str:
    try:
        repaired = text.encode("gbk").decode("utf-8")
        if repaired:
            return repaired
    except UnicodeError:
        pass
    return text


def normalize_region(region: str) -> str:
    text = repair_mojibake(WHITESPACE_RE.sub("", str(region or "")))
    if not text:
        raise CalculationError("region 不能为空")
    if "深圳" in text:
        return "深圳"
    normalized = text
    for item in REGION_NORMALIZATION_TERMS:
        normalized = normalized.replace(item, "")
    return normalized if normalized not in DIRECT_REGION_ALIASES else normalized


def min_wage_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    policy_data = policy_data_for_calc(payload)
    raw_min_wage = policy_data.get("min_wage")
    region_raw = first_payload_value(payload, REGION_KEYS)
    region = normalize_region(str(region_raw)) if region_raw else ""
    if not isinstance(raw_min_wage, dict) or raw_min_wage.get("monthly_min_wage") in (None, ""):
        return success(
            "min_wage_lookup",
            {
                "region": region,
                "found": False,
                "needs_web_search": True,
                "message": "政策数据 API 未返回 min_wage，建议进入最多两轮联网检索兜底。",
                "source": policy_api_url(),
            },
        )
    notes = policy_data.get("notes")
    scope_note = ""
    if isinstance(notes, dict):
        scope_note = str(notes.get("min_wage_scope_note") or "")
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
            "scope_note": scope_note or "最低工资数据来自政策数据 API/快照；具体城市/区县档次仍需按当地最新文件复核。",
        },
    )


def social_avg_wage_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    policy_data = policy_data_for_calc(payload)
    raw_social_avg = policy_data.get("social_avg_wage")
    region_raw = first_payload_value(payload, REGION_KEYS)
    region = normalize_region(str(region_raw)) if region_raw else ""
    if not isinstance(raw_social_avg, dict) or raw_social_avg.get("monthly_avg_wage") in (None, ""):
        return success(
            "social_avg_wage_lookup",
            {
                "region": region,
                "year": payload.get("social_avg_year") or payload.get("year"),
                "found": False,
                "needs_web_search": True,
                "message": "政策数据 API 未返回 social_avg_wage，建议进入最多两轮联网检索兜底。",
                "source": policy_api_url(),
            },
        )
    return success(
        "social_avg_wage_lookup",
        {
            "region": region,
            "year": raw_social_avg.get("year"),
            "found": True,
            "wage_caliber": raw_social_avg.get("wage_caliber_label") or raw_social_avg.get("wage_caliber"),
            "annual_avg_wage": decimal_arg(raw_social_avg.get("annual_avg_wage"), "policy_data.social_avg_wage.annual_avg_wage"),
            "monthly_avg_wage": decimal_arg(raw_social_avg.get("monthly_avg_wage"), "policy_data.social_avg_wage.monthly_avg_wage"),
            "triple_monthly_cap": decimal_arg(raw_social_avg.get("triple_monthly_cap"), "policy_data.social_avg_wage.triple_monthly_cap"),
            "source": "policy_data.social_avg_wage",
        },
    )


def calc_s(payload: dict[str, Any]) -> dict[str, Any]:
    if "monthly_wages" in payload:
        raw = payload["monthly_wages"]
        if not isinstance(raw, list) or not raw:
            raise CalculationError("monthly_wages 必须是非空数组")
        wages = [decimal_arg(item, "monthly_wages[]") for item in raw]
        actual_months = Decimal(len(wages))
        total_income = sum(wages, ZERO)
    else:
        total_income = decimal_arg(payload.get("total_income_12m"), "total_income_12m")
        actual_months = optional_decimal(payload.get("actual_months"), TWELVE, "actual_months")
    if total_income < 0:
        raise CalculationError("total_income_12m 不得为负数")
    if actual_months <= 0 or actual_months > 12:
        raise CalculationError("actual_months 必须大于0且不超过12")

    local_min = local_min_wage_from_payload(payload)
    avg = total_income / actual_months
    adjusted = max(avg, local_min)
    warnings: list[str] = []
    if local_min and avg < local_min:
        warnings.append("月均工资低于当地最低工资标准，已按最低工资标准作为S。")
    return success(
        "calc_s",
        {
            "total_income": total_income,
            "actual_months": actual_months,
            "raw_s": money(avg),
            "local_min_wage": local_min if local_min else None,
            "s": money(adjusted),
            "formula": f"S = {money_text(total_income)} ÷ {decimal_text(actual_months)} = {money_text(avg)}",
            "legal_basis": law_basis(payload, "calc_s"),
            "warnings": warnings,
        },
    )


def calc_n_value_by_months(total_months: int) -> Decimal:
    if total_months <= 0:
        raise CalculationError("工作期间必须大于0个月")
    full_years = total_months // 12
    remain = total_months % 12
    n = Decimal(full_years)
    if remain >= 6:
        n += ONE
    elif remain > 0:
        n += Decimal("0.5")
    return n


def calc_n(payload: dict[str, Any]) -> dict[str, Any]:
    if "months" in payload:
        total_months = int(decimal_arg(payload["months"], "months"))
        source = "payload.months"
    else:
        sy, sm = parse_ym(payload.get("start_year"), payload.get("start_month"), "start")
        ey, em = parse_ym(payload.get("end_year"), payload.get("end_month"), "end")
        total_months = (ey - sy) * 12 + (em - sm) + 1
        source = f"{sy}-{sm:02d} 至 {ey}-{em:02d}（按月份含首尾月估算）"
    n = calc_n_value_by_months(total_months)
    return success(
        "calc_n",
        {
            "service_months": total_months,
            "n": n,
            "source": source,
            "formula": "满1年计1个月；满6个月不满1年计1个月；不满6个月计0.5个月",
            "legal_basis": law_basis(payload, "calc_n"),
        },
    )


def apply_triple_cap(s: Decimal, n: Decimal, social_avg_monthly: Optional[Decimal]) -> tuple[Decimal, Decimal, bool, list[str]]:
    warnings: list[str] = []
    if social_avg_monthly is None or social_avg_monthly <= 0:
        return s, n, False, warnings
    cap = social_avg_monthly * THREE
    if s > cap:
        warnings.append("S高于当地上年度职工月平均工资三倍，经济补偿金适用三倍封顶且补偿年限最高12年。")
        return money(cap), min(n, Decimal("12")), True, warnings
    return s, n, False, warnings


def compensation_n(payload: dict[str, Any]) -> dict[str, Any]:
    s = decimal_arg(payload.get("s"), "s")
    n = decimal_arg(payload.get("n"), "n")
    social = social_avg_monthly_from_payload(payload)
    base, capped_n, cap_applied, warnings = apply_triple_cap(s, n, social if social else None)
    amount = money(base * capped_n)
    row = DetailRow(
        category="离职补偿",
        item="经济补偿金（N）",
        process=f"{money_text(base)} × {decimal_text(capped_n)} = {money_text(amount)}",
        amount=amount,
        legal_basis=law_basis(payload, "compensation_n"),
        note="三倍封顶仅适用于经济补偿金；如未提供 social_avg_monthly，则未进行高收入封顶判断。",
    )
    return success(
        "compensation_n",
        {
            "s": s,
            "n": n,
            "calculation_base": base,
            "calculation_n": capped_n,
            "social_avg_monthly": social if social else None,
            "triple_cap_applied": cap_applied,
            "amount": amount,
            "detail_rows": [row],
            "warnings": warnings,
            "wage_caliber": wage_caliber_from_payload(payload),
        },
    )


def n_plus_1(payload: dict[str, Any]) -> dict[str, Any]:
    base_result = compensation_n(payload)
    last_month_wage = decimal_arg(payload.get("last_month_wage"), "last_month_wage")
    compensation_amount = Decimal(str(base_result["amount"]))
    total = money(compensation_amount + last_month_wage)
    rows = list(base_result["detail_rows"])
    rows.append(
        DetailRow(
            category="离职补偿",
            item="代通知金",
            process=f"上一个月工资 {money_text(last_month_wage)}",
            amount=money(last_month_wage),
            legal_basis=law_basis(payload, "n_plus_1"),
            note="第40条非过失性辞退且未提前30天书面通知时适用。",
        )
    )
    return success(
        "n_plus_1",
        {
            "compensation_n_amount": compensation_amount,
            "notice_pay": money(last_month_wage),
            "total_amount": total,
            "detail_rows": rows,
            "warnings": base_result.get("warnings", []),
            "wage_caliber": wage_caliber_from_payload(payload),
        },
    )


def illegal_2n(payload: dict[str, Any]) -> dict[str, Any]:
    s = decimal_arg(payload.get("s"), "s")
    n = decimal_arg(payload.get("n"), "n")
    amount = money(s * n * Decimal("2"))
    row = DetailRow(
        category="赔偿金",
        item="违法解除/终止赔偿金（2N）",
        process=f"{money_text(s)} × {decimal_text(n)} × 2 = {money_text(amount)}",
        amount=amount,
        legal_basis=law_basis(payload, "illegal_2n"),
        note="2N赔偿金不适用三倍封顶；已支付2N的，不再另付经济补偿金N。",
    )
    return success(
        "illegal_2n",
        {
            "s": s,
            "n": n,
            "amount": amount,
            "detail_rows": [row],
            "warnings": ["2N赔偿金与继续履行期间工资通常需择一路径，不能重复主张。"],
        },
    )


def no_contract(payload: dict[str, Any]) -> dict[str, Any]:
    avg_wage = decimal_arg(payload.get("avg_monthly_wage"), "avg_monthly_wage")
    local_min = local_min_wage_from_payload(payload)
    months = non_negative(decimal_arg(payload.get("months"), "months"), "months")
    cap_months = Decimal("11")
    warnings: list[str] = []
    if months > cap_months and not bool(payload.get("allow_over_11_months")):
        months = cap_months
        warnings.append("未签书面劳动合同二倍工资常规赔偿期最多11个月，已按11个月封顶；满1年后视为无固定期限合同。")
    base = max(avg_wage, local_min)
    if local_min and avg_wage < local_min:
        warnings.append("月工资低于当地最低工资标准，已按最低工资作为赔偿基数。")
    amount = money(base * months)

    partial_amount = ZERO
    if payload.get("partial_month_actual_workdays") is not None or payload.get("partial_month_workdays") is not None:
        actual = non_negative(decimal_arg(payload.get("partial_month_actual_workdays"), "partial_month_actual_workdays"), "partial_month_actual_workdays")
        workdays = decimal_arg(payload.get("partial_month_workdays"), "partial_month_workdays")
        if workdays <= 0:
            raise CalculationError("partial_month_workdays 必须大于0")
        partial_amount = money(base / workdays * actual)
        amount = money(amount + partial_amount)
        warnings.append("不满整月部分已按该月实际工作日折算，请核实当月应工作日与实际工作日。")

    row = DetailRow(
        category="未签合同赔偿",
        item="二倍工资额外一倍赔偿",
        process=f"{money_text(base)} × {decimal_text(months)}个月" + (f" + 不满整月折算 {money_text(partial_amount)}" if partial_amount else ""),
        amount=amount,
        legal_basis=law_basis(payload, "no_contract"),
        note="本项为额外多出的1倍；正常工资1倍不作为赔偿金重复计算。",
    )
    return success(
        "no_contract",
        {
            "monthly_base": base,
            "months": months,
            "partial_month_amount": partial_amount,
            "amount": amount,
            "detail_rows": [row],
            "warnings": warnings,
        },
    )


def non_compete(payload: dict[str, Any]) -> dict[str, Any]:
    avg_wage = decimal_arg(payload.get("avg_monthly_wage"), "avg_monthly_wage")
    months = non_negative(decimal_arg(payload.get("non_compete_months"), "non_compete_months"), "non_compete_months")
    local_min = local_min_wage_from_payload(payload)
    if months > Decimal("24"):
        months = Decimal("24")
        capped = True
    else:
        capped = False

    in_service_restriction = bool(payload.get("in_service_restriction"))
    warnings: list[str] = []
    if in_service_restriction:
        warnings.append("在职期间竞业限制条款通常无需支付经济补偿；本脚本仍可用于离职后竞业限制补偿测算。")

    if payload.get("agreed_monthly_amount") is not None:
        monthly_amount = decimal_arg(payload.get("agreed_monthly_amount"), "agreed_monthly_amount")
        rate = monthly_amount / avg_wage if avg_wage else ZERO
        source = "agreed_monthly_amount"
    else:
        rate = optional_decimal(payload.get("agreed_rate"), Decimal("0.3"), "agreed_rate")
        monthly_amount = avg_wage * rate
        source = "agreed_rate/default_30_percent"
    if months > Decimal("12") and rate < Decimal("0.5"):
        warnings.append("竞业限制期限超过1年，实务中建议补偿比例不低于50%；当前仍按输入/默认比例计算。")
    if local_min and monthly_amount < local_min:
        monthly_amount = local_min
        warnings.append("月竞业限制补偿低于当地最低工资标准，已按最低工资作为月补偿。")
    if capped:
        warnings.append("竞业限制期限最长不得超过2年，已按24个月封顶。")
    total = money(monthly_amount * months)
    row = DetailRow(
        category="竞业限制补偿",
        item="竞业限制经济补偿金",
        process=f"月补偿 {money_text(monthly_amount)} × {decimal_text(months)}个月 = {money_text(total)}",
        amount=total,
        legal_basis=law_basis(payload, "non_compete"),
        note="离职后竞业限制补偿通常不低于离职前12个月平均工资30%，且不低于当地最低工资标准。",
    )
    return success(
        "non_compete",
        {
            "avg_monthly_wage": avg_wage,
            "rate": rate,
            "rate_source": source,
            "monthly_compensation": money(monthly_amount),
            "non_compete_months": months,
            "total_amount": total,
            "detail_rows": [row],
            "warnings": warnings,
        },
    )


def safe_xml_text(value: Any) -> str:
    return str(value).encode("utf-8", errors="replace").decode("utf-8")


def excel_col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def inline_string_cell(ref: str, value: Any, style: int = 0) -> str:
    style_attr = f' s="{style}"' if style else ""
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{escape(safe_xml_text(value))}</t></is></c>'


def number_cell(ref: str, value: Decimal, style: int = 0, formula: Optional[str] = None) -> str:
    style_attr = f' s="{style}"' if style else ""
    if formula:
        return f'<c r="{ref}"{style_attr}><f>{escape(formula)}</f></c>'
    return f'<c r="{ref}"{style_attr}><v>{money_text(value)}</v></c>'


def build_sheet_xml(rows: list[dict[str, Any]], amounts: Optional[list[Decimal]] = None) -> str:
    headers = ["序号", "类别", "项目", "计算过程", "金额（元）", "法条依据"]
    xml_rows: list[str] = []
    xml_rows.append(
        '<row r="1">' + "".join(inline_string_cell(f"{excel_col(i)}1", h, 1) for i, h in enumerate(headers, 1)) + "</row>"
    )
    for row_index, row in enumerate(rows, start=2):
        amount = amounts[row_index - 2] if amounts is not None else decimal_arg(row.get("amount", "0"), "rows[].amount")
        cells = [
            inline_string_cell(f"A{row_index}", row_index - 1),
            inline_string_cell(f"B{row_index}", row.get("category", "")),
            inline_string_cell(f"C{row_index}", row.get("item", "")),
            inline_string_cell(f"D{row_index}", row.get("process") or row.get("formula") or ""),
            number_cell(f"E{row_index}", amount, 2),
            inline_string_cell(f"F{row_index}", row.get("legal_basis", "")),
        ]
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    total_row = len(rows) + 2
    last_data_row = len(rows) + 1
    formula = f"SUM(E2:E{last_data_row})" if rows else "0"
    xml_rows.append(
        f'<row r="{total_row}">'
        + inline_string_cell(f"A{total_row}", "合计", 1)
        + inline_string_cell(f"B{total_row}", "")
        + inline_string_cell(f"C{total_row}", "")
        + inline_string_cell(f"D{total_row}", "")
        + number_cell(f"E{total_row}", ZERO, 3, formula=formula)
        + inline_string_cell(f"F{total_row}", "")
        + "</row>"
    )
    cols = (
        '<cols>'
        '<col min="1" max="1" width="8" customWidth="1"/>'
        '<col min="2" max="2" width="18" customWidth="1"/>'
        '<col min="3" max="3" width="26" customWidth="1"/>'
        '<col min="4" max="4" width="48" customWidth="1"/>'
        '<col min="5" max="5" width="14" customWidth="1"/>'
        '<col min="6" max="6" width="42" customWidth="1"/>'
        '</cols>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:F{total_row}"/>'
        f"{cols}"
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def write_xlsx(path: Path, rows: list[dict[str, Any]], amounts: Optional[list[Decimal]] = None) -> None:
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
        '<sheets><sheet name="补偿赔偿明细" sheetId="1" r:id="rId1"/></sheets>'
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
    xlsx_parts = {
        "[Content_Types].xml": content_types,
        "_rels/.rels": root_rels,
        "xl/workbook.xml": workbook,
        "xl/_rels/workbook.xml.rels": workbook_rels,
        "xl/styles.xml": styles,
        "xl/worksheets/sheet1.xml": build_sheet_xml(rows, amounts),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_path, content in xlsx_parts.items():
            archive.writestr(archive_path, content)


def export_rows_and_amounts(payload: dict[str, Any], missing_message: str) -> tuple[list[dict[str, Any]], list[Decimal]]:
    rows = payload.get("rows") or payload.get("detail_rows")
    if not isinstance(rows, list):
        raise CalculationError(missing_message)
    normalized: list[dict[str, Any]] = []
    amounts: list[Decimal] = []
    for row in rows:
        if not isinstance(row, dict):
            raise CalculationError("rows 中的每一项都必须是对象")
        normalized.append(row)
        amounts.append(decimal_arg(row.get("amount", "0"), "rows[].amount"))
    return normalized, amounts


def export_output_path(payload: dict[str, Any], default_name: str) -> Path:
    output_path = Path(str(payload.get("output_path") or default_name))
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    return output_path


def export_to_excel(payload: dict[str, Any]) -> dict[str, Any]:
    normalized, amounts = export_rows_and_amounts(payload, "export_excel 需要 rows 或 detail_rows 数组")
    output_path = export_output_path(payload, "compensation_damages_detail.xlsx")
    write_xlsx(output_path, normalized, amounts)
    total = sum(amounts, ZERO)
    return success(
        "export_excel",
        {
            "output_path": output_path,
            "row_count": len(normalized),
            "total_amount": money(total),
            "style_note": "表头和合计行仅加粗；金额列使用 #,##0.00；合计行使用 SUM 公式。",
        },
    )


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if not action:
        raise CalculationError("缺少 action")
    handlers = {
        "calc_s": calc_s,
        "calc_n": calc_n,
        "no_contract": no_contract,
        "compensation_n": compensation_n,
        "n_plus_1": n_plus_1,
        "illegal_2n": illegal_2n,
        "non_compete": non_compete,
        "min_wage_lookup": min_wage_lookup,
        "social_avg_wage_lookup": social_avg_wage_lookup,
        "export_excel": export_to_excel,
        "export_to_excel": export_to_excel,
    }
    if action not in handlers:
        raise CalculationError(f"不支持的 action：{action}")
    calculation_payload = payload if action in {"export_excel", "export_to_excel"} else payload_with_policy_data(action, payload)
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
    "calc_s",
    "calc_n",
    "no_contract",
    "compensation_n",
    "n_plus_1",
    "illegal_2n",
    "non_compete",
    "min_wage_lookup",
    "social_avg_wage_lookup",
    "export_to_excel",
    "dispatch",
]


if __name__ == "__main__":
    raise SystemExit(main())
