#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import math
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, datetime
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
TWELVE = Decimal("12")

POLICY_DATA_KEYS = ("policy_data", "policy")
INLINE_POLICY_FIELDS = (
    "social_avg_wage",
    "work_death_subsidy",
    "leaving_subsidy_standards",
    "sick_leave_period",
    "law_basis",
    "law_articles_text",
    "notes",
)
REGION_KEYS = ("region", "province", "city")
WHITESPACE_RE = re.compile(r"\s+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

DISABILITY_MONTHS = {1: 27, 2: 25, 3: 23, 4: 21, 5: 18, 6: 16, 7: 13, 8: 11, 9: 9, 10: 7}
ALLOWANCE_RATES = {
    1: Decimal("0.90"),
    2: Decimal("0.85"),
    3: Decimal("0.80"),
    4: Decimal("0.75"),
    5: Decimal("0.70"),
    6: Decimal("0.60"),
}
NURSING_RATES = {
    "完全不能自理": Decimal("0.50"),
    "大部分不能自理": Decimal("0.40"),
    "部分不能自理": Decimal("0.30"),
    "complete": Decimal("0.50"),
    "major": Decimal("0.40"),
    "partial": Decimal("0.30"),
}
LAW_BASIS = {
    "base_wage": "《工伤保险条例》第六十四条",
    "disability_subsidy": "《工伤保险条例》第三十五条、第三十六条、第三十七条",
    "disability_allowance": "《工伤保险条例》第三十五条、第三十六条",
    "suspension_wage": "《工伤保险条例》第三十三条",
    "nursing_fee": "《工伤保险条例》第三十四条",
    "death_benefits": "《工伤保险条例》第三十九条",
    "leaving_subsidies": "《工伤保险条例》第三十六条、第三十七条；各省工伤保险实施办法",
    "retirement_age": "《全国人民代表大会常务委员会关于实施渐进式延迟法定退休年龄的决定》",
}


class CalculationError(Exception):
    """Raised for invalid input or unsupported calculation requests."""


@dataclass
class DetailRow:
    item: str
    process: str
    amount: Decimal
    payer: str
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
    year = int(value)
    if year < 1900 or year > 2100:
        raise CalculationError("year 超出支持范围：1900-2100")
    return year


def parse_ym(value: Any, field_name: str) -> tuple[int, int]:
    if not value:
        raise CalculationError(f"{field_name}不能为空")
    text = str(value)
    match = re.match(r"^(\d{4})[-/年](\d{1,2})", text)
    if not match:
        raise CalculationError(f"{field_name}必须是 YYYY-MM 或 YYYY年M月 格式")
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        raise CalculationError(f"{field_name}月份必须在1-12之间")
    return year, month


def parse_date(value: Any, field_name: str) -> date:
    if not value:
        raise CalculationError(f"{field_name}不能为空")
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise CalculationError(f"{field_name}必须是 YYYY-MM-DD 格式") from exc


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
    if action in {"avg_wage_lookup", "work_death_subsidy_lookup", "death_benefits", "leaving_subsidies", "sick_leave_period_lookup"}:
        return True
    if action in {"base_wage", "nursing_fee"}:
        return payload.get("social_avg_monthly") in (None, "") and bool(first_payload_value(payload, REGION_KEYS))
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


def law_basis(payload: dict[str, Any], key: str) -> str:
    policy_data = policy_data_from_payload(payload)
    basis = policy_data.get("law_basis")
    if isinstance(basis, dict):
        value = basis.get(key)
        if value:
            return str(value)
    return LAW_BASIS.get(key, "")


def repair_mojibake(text: str) -> str:
    try:
        repaired = text.encode("gbk").decode("utf-8")
        if repaired and CJK_RE.search(repaired):
            return repaired
    except UnicodeError:
        pass
    return text


def normalize_region(region: str, *, full_name: bool = False) -> str:
    text = repair_mojibake(WHITESPACE_RE.sub("", str(region or "")))
    if not text:
        raise CalculationError("region 不能为空")
    if "深圳" in text:
        return "广东省" if full_name else "广东"
    municipalities = {"北京", "天津", "上海", "重庆"}
    autonomous = {
        "内蒙古": "内蒙古自治区",
        "广西": "广西壮族自治区",
        "宁夏": "宁夏回族自治区",
        "新疆": "新疆维吾尔自治区",
        "西藏": "西藏自治区",
    }
    short = text
    for item in ["省", "市", "自治区", "壮族", "回族", "维吾尔"]:
        short = short.replace(item, "")
    if full_name:
        if short in municipalities:
            return f"{short}市"
        if short in autonomous:
            return autonomous[short]
        return f"{short}省"
    return short


def avg_wage_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    policy_data = policy_data_for_calc(payload)
    raw_social_avg = policy_data.get("social_avg_wage")
    region_raw = first_payload_value(payload, REGION_KEYS)
    region = normalize_region(str(region_raw), full_name=True) if region_raw else ""
    if not isinstance(raw_social_avg, dict) or raw_social_avg.get("monthly_avg_wage") in (None, ""):
        return success(
            "avg_wage_lookup",
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
        "avg_wage_lookup",
        {
            "region": region,
            "year": raw_social_avg.get("year"),
            "found": True,
            "wage_caliber": raw_social_avg.get("wage_caliber_label") or raw_social_avg.get("wage_caliber") or wage_caliber_from_payload(payload),
            "annual_avg_wage": decimal_arg(raw_social_avg.get("annual_avg_wage"), "policy_data.social_avg_wage.annual_avg_wage"),
            "monthly_avg_wage": decimal_arg(raw_social_avg.get("monthly_avg_wage"), "policy_data.social_avg_wage.monthly_avg_wage"),
            "source": "policy_data.social_avg_wage",
        },
    )


def calculate_base_wage(payload: dict[str, Any]) -> dict[str, Any]:
    personal_wage = decimal_arg(payload.get("personal_monthly_wage"), "personal_monthly_wage")
    social_avg = social_avg_monthly_from_payload(payload)
    if social_avg <= 0:
        raise CalculationError("social_avg_monthly 不能为空，或通过 policy_data.social_avg_wage.monthly_avg_wage 提供")
    lower = social_avg * Decimal("0.6")
    upper = social_avg * Decimal("3")
    base = min(max(personal_wage, lower), upper)
    warnings: list[str] = []
    if personal_wage < lower:
        warnings.append("本人工资低于统筹地区上年度职工月平均工资60%，已按60%下限计算。")
    if personal_wage > upper:
        warnings.append("本人工资高于统筹地区上年度职工月平均工资300%，已按300%上限计算。")
    return success(
        "base_wage",
        {
            "personal_monthly_wage": personal_wage,
            "social_avg_monthly": social_avg,
            "lower_60_percent": money(lower),
            "upper_300_percent": money(upper),
            "calculation_base": money(base),
            "legal_basis": law_basis(payload, "base_wage"),
            "warnings": warnings,
        },
    )


def disability_subsidy(payload: dict[str, Any]) -> dict[str, Any]:
    level = int(decimal_arg(payload.get("disability_level"), "disability_level"))
    if level not in DISABILITY_MONTHS:
        raise CalculationError("disability_level 必须为1-10级")
    base = decimal_arg(payload.get("calculation_base"), "calculation_base")
    months = Decimal(DISABILITY_MONTHS[level])
    amount = money(base * months)
    row = DetailRow(
        item=f"{level}级一次性伤残补助金",
        process=f"{money_text(base)} × {months}个月 = {money_text(amount)}",
        amount=amount,
        payer="工伤保险基金",
        legal_basis=law_basis(payload, "disability_subsidy"),
        note="计算基数应适用本人工资60%-300%上下限。",
    )
    return success("disability_subsidy", {"disability_level": level, "months": months, "amount": amount, "detail_rows": [row]})


def disability_allowance(payload: dict[str, Any]) -> dict[str, Any]:
    level = int(decimal_arg(payload.get("disability_level"), "disability_level"))
    if level not in ALLOWANCE_RATES:
        raise CalculationError("伤残津贴仅适用于1-6级")
    base = decimal_arg(payload.get("calculation_base"), "calculation_base")
    rate = ALLOWANCE_RATES[level]
    amount = money(base * rate)
    payer = "工伤保险基金" if level <= 4 else "用人单位"
    note = "5-6级须在用人单位难以安排工作时才按月支付。" if level in {5, 6} else "1-4级保留劳动关系、退出工作岗位，按月支付。"
    row = DetailRow(
        item=f"{level}级伤残津贴（按月）",
        process=f"{money_text(base)} × {decimal_text(rate * 100)}% = {money_text(amount)}",
        amount=amount,
        payer=payer,
        legal_basis=law_basis(payload, "disability_allowance"),
        note=note,
    )
    return success("disability_allowance", {"disability_level": level, "monthly_amount": amount, "detail_rows": [row]})


def suspension_wage(payload: dict[str, Any]) -> dict[str, Any]:
    personal_wage = decimal_arg(payload.get("personal_monthly_wage"), "personal_monthly_wage")
    months = non_negative(decimal_arg(payload.get("months"), "months"), "months")
    amount = money(personal_wage * months)
    warnings = []
    if months > 12:
        warnings.append("停工留薪期一般不超过12个月；超过12个月须经设区的市级劳动能力鉴定委员会确认，延长最长不超过12个月。")
    row = DetailRow(
        item="停工留薪期工资",
        process=f"{money_text(personal_wage)} × {decimal_text(months)}个月 = {money_text(amount)}",
        amount=amount,
        payer="用人单位",
        legal_basis=law_basis(payload, "suspension_wage"),
        note="以劳动能力鉴定委员会确认的停工留薪期为准；未鉴定时仅为参考估算。",
    )
    return success("suspension_wage", {"months": months, "amount": amount, "detail_rows": [row], "warnings": warnings})


def nursing_fee(payload: dict[str, Any]) -> dict[str, Any]:
    social_avg = social_avg_monthly_from_payload(payload)
    if social_avg <= 0:
        raise CalculationError("social_avg_monthly 不能为空，或通过 policy_data.social_avg_wage.monthly_avg_wage 提供")
    level = repair_mojibake(str(payload.get("nursing_level") or payload.get("level") or ""))
    if level not in NURSING_RATES:
        raise CalculationError("nursing_level 仅支持 完全不能自理 / 大部分不能自理 / 部分不能自理")
    rate = NURSING_RATES[level]
    amount = money(social_avg * rate)
    row = DetailRow(
        item="评残后生活护理费（按月）",
        process=f"{money_text(social_avg)} × {decimal_text(rate * 100)}% = {money_text(amount)}",
        amount=amount,
        payer="工伤保险基金",
        legal_basis=law_basis(payload, "nursing_fee"),
        note="需经劳动能力鉴定委员会确认护理依赖等级。",
    )
    return success("nursing_fee", {"nursing_level": level, "monthly_amount": amount, "detail_rows": [row]})


def work_death_subsidy_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    death_year = parse_year(payload.get("death_year") or payload.get("year"))
    data_year = death_year - 1
    policy_data = policy_data_for_calc(payload)
    raw_work_death = policy_data.get("work_death_subsidy")
    if not isinstance(raw_work_death, dict) or raw_work_death.get("one_time_work_death_subsidy") in (None, ""):
        return success(
            "work_death_subsidy_lookup",
            {
                "death_year": death_year,
                "data_year": data_year,
                "found": False,
                "needs_web_search": True,
                "message": "政策数据 API 未返回 work_death_subsidy，建议进入最多两轮联网检索兜底。",
                "source": policy_api_url(),
            },
        )
    returned_data_year = int(raw_work_death.get("data_year") or data_year)
    if returned_data_year != data_year:
        return success(
            "work_death_subsidy_lookup",
            {
                "death_year": death_year,
                "data_year": data_year,
                "found": False,
                "needs_web_search": True,
                "message": f"政策数据 API 返回的是 {returned_data_year} 年数据，未覆盖死亡年份对应的 {data_year} 年数据。",
                "source": policy_api_url(),
            },
        )
    disposable_income = decimal_arg(raw_work_death.get("urban_disposable_income"), "policy_data.work_death_subsidy.urban_disposable_income")
    amount = decimal_arg(raw_work_death.get("one_time_work_death_subsidy"), "policy_data.work_death_subsidy.one_time_work_death_subsidy")
    return success(
        "work_death_subsidy_lookup",
        {
            "death_year": death_year,
            "data_year": data_year,
            "urban_disposable_income": disposable_income,
            "one_time_work_death_subsidy": amount,
            "formula": f"{money_text(disposable_income)} × 20 = {money_text(amount)}",
            "source": "policy_data.work_death_subsidy",
        },
    )


def death_benefits(payload: dict[str, Any]) -> dict[str, Any]:
    death_lookup = work_death_subsidy_lookup(payload)
    if death_lookup.get("needs_web_search"):
        return death_lookup
    personal_wage = decimal_arg(payload.get("personal_monthly_wage"), "personal_monthly_wage")
    social_avg = social_avg_monthly_from_payload(payload)
    if social_avg <= 0:
        raise CalculationError("social_avg_monthly 不能为空，或通过 policy_data.social_avg_wage.monthly_avg_wage 提供")
    spouse_count = int(optional_decimal(payload.get("spouse_count"), ZERO, "spouse_count"))
    other_count = int(optional_decimal(payload.get("other_dependents_count"), ZERO, "other_dependents_count"))
    orphan_elder_count = int(optional_decimal(payload.get("orphan_elder_count"), ZERO, "orphan_elder_count"))
    death_amount = Decimal(str(death_lookup["one_time_work_death_subsidy"]))
    funeral = money(social_avg * Decimal("6"))
    pension = personal_wage * (Decimal("0.4") * spouse_count + Decimal("0.3") * other_count + Decimal("0.1") * orphan_elder_count)
    capped_pension = min(money(pension), money(personal_wage))
    death_benefits_basis = law_basis(payload, "death_benefits")
    rows = [
        DetailRow("一次性工亡补助金", death_lookup["formula"], death_amount, "工伤保险基金", death_benefits_basis),
        DetailRow("丧葬补助金", f"{money_text(social_avg)} × 6个月 = {money_text(funeral)}", funeral, "工伤保险基金", death_benefits_basis),
        DetailRow("供养亲属抚恤金（按月）", f"本人工资 {money_text(personal_wage)} × 亲属比例合计，封顶不超过本人工资", capped_pension, "工伤保险基金", death_benefits_basis),
    ]
    return success(
        "death_benefits",
        {
            "one_time_work_death_subsidy": death_amount,
            "funeral_subsidy": funeral,
            "monthly_dependent_pension": capped_pension,
            "detail_rows": rows,
            "warnings": ["供养亲属抚恤金需符合供养亲属范围和无劳动能力等条件，且按月支付。"],
        },
    )


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    return total // 12, total % 12 + 1


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def retirement_age(payload: dict[str, Any]) -> dict[str, Any]:
    birth_year, birth_month = parse_ym(payload.get("birth_ym") or payload.get("birth_month"), "birth_ym")
    gender = repair_mojibake(str(payload.get("gender") or "")).lower()
    position = repair_mojibake(str(payload.get("female_position") or payload.get("position") or "worker")).lower()
    warnings: list[str] = []
    if gender in {"male", "男", "m"} or "男" in gender:
        base_age = 60
        if (birth_year, birth_month) < (1965, 1):
            delay = 0
        elif (birth_year, birth_month) > (1976, 8):
            delay = 36
        else:
            delay = ceil_div((birth_year + 60 - 2025) * 12 + birth_month, 4)
    elif gender in {"female", "女", "f", "濂�", "濂"} or "女" in gender or "濂" in gender:
        if position in {"manager", "management", "cadre", "管理岗", "干部", "技术岗"}:
            base_age = 55
            if (birth_year, birth_month) < (1970, 1):
                delay = 0
            elif (birth_year, birth_month) > (1981, 8):
                delay = 36
            else:
                delay = ceil_div((birth_year + 55 - 2025) * 12 + birth_month, 4)
        else:
            base_age = 50
            if not position or position in {"unknown", "不确定"}:
                warnings.append("女性岗位性质未明确，默认按女工人原50岁退休口径计算。")
            if (birth_year, birth_month) < (1975, 1):
                delay = 0
            elif (birth_year, birth_month) > (1984, 10):
                delay = 60
            else:
                delay = ceil_div((birth_year + 50 - 2025) * 12 + birth_month, 2)
    else:
        raise CalculationError("gender 仅支持 男/male 或 女/female")
    retire_year, retire_month = add_months(birth_year + base_age, birth_month, delay)
    return success(
        "retirement_age",
        {
            "birth_ym": f"{birth_year}-{birth_month:02d}",
            "base_age_years": base_age,
            "delay_months": delay,
            "retirement_ym": f"{retire_year}-{retire_month:02d}",
            "legal_basis": law_basis(payload, "retirement_age"),
            "warnings": warnings,
        },
    )


def remaining_years_to_retirement(retirement_ym: str, calc_ym: str) -> tuple[int, int]:
    ry, rm = parse_ym(retirement_ym, "retirement_ym")
    cy, cm = parse_ym(calc_ym, "calc_ym")
    months = (ry - cy) * 12 + (rm - cm)
    if months <= 0:
        return months, 0
    return months, math.ceil(months / 12)


def employment_discount_factor(payload: dict[str, Any]) -> tuple[Decimal, list[str]]:
    warnings: list[str] = []
    if payload.get("retirement_ym") and payload.get("calc_ym"):
        remaining_months, remaining_years = remaining_years_to_retirement(str(payload["retirement_ym"]), str(payload["calc_ym"]))
        if remaining_months <= 0 and not bool(payload.get("article_38_resignation")):
            return ZERO, ["已达或超过法定退休年龄，按多数省份规则就业补助金为0；劳动合同法第38条情形除外。"]
        if remaining_years >= 5:
            return Decimal("1"), warnings
        if remaining_years <= 1:
            return Decimal("0.1"), ["距退休不足1年，就业补助金按10%估算。"]
        return Decimal(remaining_years - 1) * Decimal("0.2"), [f"距退休不足5年，按剩余约{remaining_years}年折减就业补助金。"]
    return Decimal("1"), warnings


def parse_subsidy_value(value: str) -> tuple[Decimal, str]:
    value = value.strip()
    number_match = re.search(r"[\d.]+", value)
    if not number_match:
        raise CalculationError(f"补助金标准缺少可直接计算的数字：{value}；需联网核验地方规则或由用户提供具体计发月数。")
    if "每满一年" in value:
        return decimal_arg(number_match.group(0), value), "months_per_year"
    if "万元" in value:
        number = decimal_arg(number_match.group(0), value)
        return number * Decimal("10000"), "fixed"
    if "月" in value or "两项合并" in value or re.match(r"^[\d.]+(?:（.*）)?$", value):
        number = decimal_arg(number_match.group(0), value)
        return number, "months"
    raise CalculationError(f"暂不支持解析补助金标准：{value}")


def find_provincial_subsidy(payload: dict[str, Any], region: str, level: int) -> dict[str, Any]:
    policy_data = policy_data_for_calc(payload)
    standards = policy_data.get("leaving_subsidy_standards")
    if not isinstance(standards, list) or not standards:
        raise CalculationError("政策数据 API 未返回 leaving_subsidy_standards，建议进入最多两轮联网检索兜底")
    region_short = normalize_region(region, full_name=False)
    chosen = None
    for item in standards:
        if not isinstance(item, dict):
            continue
        item_region = normalize_region(str(item.get("normalized_region") or item.get("region") or ""), full_name=False)
        if item_region == region_short and int(decimal_arg(item.get("disability_level"), "policy_data.leaving_subsidy_standards[].disability_level")) == level:
            chosen = item
            break
    if chosen is None:
        raise CalculationError(f"未找到 {region} {level}级离职补助金标准")
    if chosen.get("combined_raw"):
        combined_value, value_type = parse_subsidy_value(str(chosen["combined_raw"]))
        return {
            "combined": combined_value,
            "value_type": value_type,
            "basis": chosen.get("basis", ""),
            "special": chosen.get("special", ""),
            "region": region_short,
        }
    if not chosen.get("medical_raw") or not chosen.get("employment_raw"):
        raise CalculationError(f"{region} {level}级补助金标准缺少医疗或就业补助金字段")
    medical_value, medical_type = parse_subsidy_value(str(chosen["medical_raw"]))
    employment_value, employment_type = parse_subsidy_value(str(chosen["employment_raw"]))
    return {
        "medical": medical_value,
        "employment": employment_value,
        "medical_type": medical_type,
        "employment_type": employment_type,
        "basis": chosen.get("basis", ""),
        "special": chosen.get("special", ""),
        "region": region_short,
    }


def leaving_subsidies(payload: dict[str, Any]) -> dict[str, Any]:
    level = int(decimal_arg(payload.get("disability_level"), "disability_level"))
    if level not in range(5, 11):
        raise CalculationError("离职两项补助金仅适用于5-10级")
    region = str(payload.get("region") or payload.get("province") or "")
    record = find_provincial_subsidy(payload, region, level)
    if payload.get("subsidy_base") not in (None, ""):
        base = decimal_arg(payload.get("subsidy_base"), "subsidy_base")
    elif "本人" in str(record.get("basis", "")):
        base = decimal_arg(payload.get("personal_monthly_wage"), "personal_monthly_wage")
    else:
        base = social_avg_monthly_from_payload(payload)
        if base <= 0 and record.get("value_type") != "fixed" and record.get("medical_type") != "fixed":
            raise CalculationError("subsidy_base 不能为空，或通过 policy_data.social_avg_wage.monthly_avg_wage 提供")
    personal_wage = optional_decimal(payload.get("personal_monthly_wage"), base, "personal_monthly_wage")
    occupational_disease = bool(payload.get("occupational_disease"))
    factor, factor_warnings = employment_discount_factor(payload)
    warnings = list(factor_warnings)
    rows: list[DetailRow] = []

    def amount_from(value: Decimal, value_type: str, item: str, payer: str, factor_value: Decimal = Decimal("1")) -> Decimal:
        if value_type == "fixed":
            amount = value * factor_value
            process = f"固定金额 {money_text(value)} × 折减系数 {decimal_text(factor_value)}"
        elif value_type == "months_per_year":
            raw_years = payload.get("subsidy_years") or payload.get("payment_years") or payload.get("remaining_years")
            if raw_years in (None, "") and payload.get("retirement_ym") and payload.get("calc_ym"):
                _, raw_years = remaining_years_to_retirement(str(payload["retirement_ym"]), str(payload["calc_ym"]))
            if raw_years in (None, ""):
                raise CalculationError("该地区标准按“每满一年发若干个月”计算，请提供 subsidy_years/payment_years，或提供 retirement_ym 与 calc_ym 供估算。")
            years = non_negative(decimal_arg(raw_years, "subsidy_years"), "subsidy_years")
            amount = base * value * years * factor_value
            process = f"{money_text(base)} × {decimal_text(value)}个月/年 × {decimal_text(years)}年 × 折减系数 {decimal_text(factor_value)}"
        else:
            amount = base * value * factor_value
            process = f"{money_text(base)} × {decimal_text(value)}个月 × 折减系数 {decimal_text(factor_value)}"
        amount = money(amount)
        rows.append(DetailRow(item, f"{process} = {money_text(amount)}", amount, payer, law_basis(payload, "leaving_subsidies"), record.get("basis", "")))
        return amount

    if "combined" in record:
        total = amount_from(record["combined"], record["value_type"], f"{level}级离职两项补助金（合并）", "按地方规定分担或用人单位/基金")
        medical = ZERO
        employment = total
        warnings.append("该省表格为两项合并口径，脚本未拆分医疗补助金和就业补助金支付主体。")
    else:
        medical_factor = Decimal("1")
        if occupational_disease:
            medical_factor = Decimal("1.2")
            warnings.append("职业病医疗补助金按通用+20%估算；各省特殊比例请结合特殊情形复核。")
        medical = amount_from(record["medical"], record["medical_type"], f"{level}级一次性工伤医疗补助金", "工伤保险基金", medical_factor)
        employment = amount_from(record["employment"], record["employment_type"], f"{level}级一次性伤残就业补助金", "用人单位", factor)
        total = money(medical + employment)
    if record.get("special"):
        warnings.append(record["special"])
    return success(
        "leaving_subsidies",
        {
            "region": record["region"],
            "disability_level": level,
            "subsidy_base": base,
            "medical_subsidy": medical,
            "employment_subsidy": employment,
            "total_amount": total,
            "detail_rows": rows,
            "warnings": warnings,
            "source": "policy_data.leaving_subsidy_standards",
        },
    )


def sick_leave_period_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    region = normalize_region(str(payload.get("region") or payload.get("province") or ""), full_name=False)
    injury_keyword = repair_mojibake(str(payload.get("injury_keyword") or payload.get("keyword") or "")).strip()
    policy_data = policy_data_for_calc(payload)
    sick_leave_policy = policy_data.get("sick_leave_period")
    if not isinstance(sick_leave_policy, dict):
        return success(
            "sick_leave_period_lookup",
            {
                "region": region,
                "found": False,
                "needs_web_search": True,
                "message": "政策数据 API 未返回 sick_leave_period，建议进入最多两轮联网检索兜底。",
                "source": policy_api_url(),
            },
        )
    collected = str(sick_leave_policy.get("collected_status") or "未确认完整收录")
    if not injury_keyword:
        return success(
            "sick_leave_period_lookup",
            {
                "region": region,
                "collected_status": collected,
                "found": False,
                "message": "请提供 injury_keyword 或以劳动能力鉴定委员会确认月数为准。",
                "source": "policy_data.sick_leave_period",
            },
        )
    best: Optional[dict[str, Any]] = None
    match_count = 0
    catalog = sick_leave_policy.get("catalog")
    if not isinstance(catalog, list):
        catalog = []
    for entry in catalog:
        if not isinstance(entry, dict):
            continue
        searchable = " ".join(str(entry.get(key) or "") for key in ("code", "injury", "period_text", "raw"))
        if injury_keyword not in searchable:
            continue
        month_value = optional_decimal(entry.get("suggested_months"), ZERO, "policy_data.sick_leave_period.catalog[].suggested_months")
        if month_value > 0:
            match_count += 1
            if best is None or month_value > best["months"]:
                best = {"raw": entry.get("raw") or searchable, "months": month_value, "entry": entry}
    if best is None:
        return success(
            "sick_leave_period_lookup",
            {
                "region": region,
                "collected_status": collected,
                "found": False,
                "needs_web_search": True,
                "message": "政策数据快照未匹配该伤情；建议进入最多两轮联网检索兜底，仍失败时咨询当地人社局12333或劳动能力鉴定委员会。",
                "source": "policy_data.sick_leave_period",
            },
        )
    warnings = []
    if sick_leave_policy.get("catalog_scope") == "generic":
        warnings.append("该地区未收录完整停工留薪期目录，当前结果来自通用参考标准，非当地官方标准。")
    return success(
        "sick_leave_period_lookup",
        {
            "region": region,
            "collected_status": collected,
            "found": True,
            "injury_keyword": injury_keyword,
            "suggested_months": best["months"],
            "match_count": match_count,
            "note": "多处伤以最严重损伤部位对应的最长期限为参考；最终以劳动能力鉴定委员会确认为准。",
            "source": "policy_data.sick_leave_period",
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
    headers = ["序号", "赔偿项目", "计算过程", "金额（元）", "支付主体", "备注/法依"]
    xml_rows = [
        '<row r="1">' + "".join(inline_string_cell(f"{excel_col(i)}1", h, 1) for i, h in enumerate(headers, 1)) + "</row>"
    ]
    for row_index, row in enumerate(rows, start=2):
        amount = amounts[row_index - 2] if amounts is not None else decimal_arg(row.get("amount", "0"), "rows[].amount")
        cells = [
            inline_string_cell(f"A{row_index}", row_index - 1),
            inline_string_cell(f"B{row_index}", row.get("item", "")),
            inline_string_cell(f"C{row_index}", row.get("process", "")),
            number_cell(f"D{row_index}", amount, 2),
            inline_string_cell(f"E{row_index}", row.get("payer", "")),
            inline_string_cell(f"F{row_index}", row.get("note") or row.get("legal_basis") or ""),
        ]
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    total_row = len(rows) + 2
    last_data_row = len(rows) + 1
    formula = f"SUM(D2:D{last_data_row})" if rows else "0"
    xml_rows.append(
        f'<row r="{total_row}">'
        + inline_string_cell(f"A{total_row}", "合计", 1)
        + inline_string_cell(f"B{total_row}", "")
        + inline_string_cell(f"C{total_row}", "")
        + number_cell(f"D{total_row}", ZERO, 3, formula=formula)
        + inline_string_cell(f"E{total_row}", "")
        + inline_string_cell(f"F{total_row}", "")
        + "</row>"
    )
    cols = (
        '<cols><col min="1" max="1" width="8" customWidth="1"/>'
        '<col min="2" max="2" width="28" customWidth="1"/>'
        '<col min="3" max="3" width="52" customWidth="1"/>'
        '<col min="4" max="4" width="14" customWidth="1"/>'
        '<col min="5" max="5" width="16" customWidth="1"/>'
        '<col min="6" max="6" width="42" customWidth="1"/></cols>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:F{total_row}"/>{cols}<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    )


def write_xlsx(path: Path, rows: list[dict[str, Any]], amounts: Optional[list[Decimal]] = None) -> None:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="工伤赔偿明细" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.00"/></numFmts>'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
        '<xf numFmtId="164" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyNumberFormat="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'
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
    normalized = []
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
    normalized, amounts = export_rows_and_amounts(payload, "export_to_excel 需要 rows 或 detail_rows 数组")
    output_path = export_output_path(payload, "work_injury_detail.xlsx")
    write_xlsx(output_path, normalized, amounts)
    total = sum(amounts, ZERO)
    return success("export_to_excel", {"output_path": output_path, "row_count": len(normalized), "total_amount": money(total)})


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if not action:
        raise CalculationError("缺少 action")
    handlers = {
        "avg_wage_lookup": avg_wage_lookup,
        "base_wage": calculate_base_wage,
        "disability_subsidy": disability_subsidy,
        "disability_allowance": disability_allowance,
        "suspension_wage": suspension_wage,
        "nursing_fee": nursing_fee,
        "work_death_subsidy_lookup": work_death_subsidy_lookup,
        "death_benefits": death_benefits,
        "retirement_age": retirement_age,
        "leaving_subsidies": leaving_subsidies,
        "sick_leave_period_lookup": sick_leave_period_lookup,
        "export_to_excel": export_to_excel,
        "export_excel": export_to_excel,
    }
    if action not in handlers:
        raise CalculationError(f"不支持的 action：{action}")
    return handlers[action](payload_with_policy_data(action, payload))


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
    "avg_wage_lookup",
    "calculate_base_wage",
    "disability_subsidy",
    "disability_allowance",
    "suspension_wage",
    "nursing_fee",
    "work_death_subsidy_lookup",
    "death_benefits",
    "retirement_age",
    "leaving_subsidies",
    "sick_leave_period_lookup",
    "export_to_excel",
    "dispatch",
]


if __name__ == "__main__":
    raise SystemExit(main())
