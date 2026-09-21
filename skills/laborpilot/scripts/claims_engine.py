#!/usr/bin/env python3
"""劳动争议专业金额公式的纯计算核心。

本模块只执行已经选定的公式，不判断请求权基础是否成立。调用方必须先
完成事实、证据和法源核验，并把每个输入的来源写入计算记录。
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any


FORMULA_VERSION = "1.0.0"
FORMULA_TYPES = {
    "economic_compensation",
    "n_plus_one",
    "unlawful_termination_compensation",
    "overtime_workday",
    "overtime_rest_day",
    "overtime_statutory_holiday",
    "work_injury_lump_sum_disability",
    "work_injury_disability_allowance",
    "work_injury_regional_benefit",
    "work_injury_three_lump_sums",
    "non_compete_compensation",
    "sum",
}
FORMULA_INPUT_KEYS = {
    "economic_compensation": {"monthly_wage", "compensation_months", "cap_applies"},
    "n_plus_one": {"monthly_wage", "compensation_months", "notice_pay_base", "notice_months", "cap_applies"},
    "unlawful_termination_compensation": {"monthly_wage", "compensation_months", "cap_applies"},
    "overtime_workday": {"monthly_wage", "overtime_hours"},
    "overtime_rest_day": {"monthly_wage", "overtime_hours"},
    "overtime_statutory_holiday": {"monthly_wage", "overtime_hours"},
    "work_injury_lump_sum_disability": {"monthly_wage", "benefit_months"},
    "work_injury_disability_allowance": {"monthly_wage", "allowance_rate", "payment_months"},
    "work_injury_regional_benefit": {"benefit_units"},
    "work_injury_three_lump_sums": {"component_ids"},
    "non_compete_compensation": {"monthly_compensation", "payment_months"},
    "sum": {"component_ids"},
}
FORMULA_REQUIRED_PARAMETERS = {
    "overtime_workday": {"monthly_paid_days", "daily_hours"},
    "overtime_rest_day": {"monthly_paid_days", "daily_hours"},
    "overtime_statutory_holiday": {"monthly_paid_days", "daily_hours"},
    "work_injury_regional_benefit": {"benefit_unit_amount"},
}


class CalculationError(ValueError):
    """计算合同或数值不合法。"""


def decimal_value(value: Any, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CalculationError(f"{field} 不是合法数值：{value}") from exc
    if not result.is_finite():
        raise CalculationError(f"{field} 必须是有限数值。")
    return result


def _input(inputs: dict[str, Any], key: str, *, positive: bool = False) -> Decimal:
    record = inputs.get(key)
    if not isinstance(record, dict) or "value" not in record:
        raise CalculationError(f"缺少数值输入 inputs.{key}。")
    result = decimal_value(record["value"], f"inputs.{key}.value")
    if positive and result <= 0:
        raise CalculationError(f"inputs.{key}.value 必须大于 0。")
    if not positive and result < 0:
        raise CalculationError(f"inputs.{key}.value 不得小于 0。")
    return result


def _parameter(parameters: dict[str, Any], key: str, *, positive: bool = True) -> Decimal:
    record = parameters.get(key)
    if not isinstance(record, dict) or "value" not in record:
        raise CalculationError(f"缺少已解析参数 resolved_parameters.{key}。")
    result = decimal_value(record["value"], f"resolved_parameters.{key}.value")
    if positive and result <= 0:
        raise CalculationError(f"resolved_parameters.{key}.value 必须大于 0。")
    return result


def _step(label: str, expression: str, raw: Decimal) -> dict[str, str]:
    return {"label": label, "expression": expression, "raw_result": format(raw, "f")}


def calculate_formula(
    formula_type: str,
    inputs: dict[str, Any],
    resolved_parameters: dict[str, Any],
    prior_amounts: dict[str, Decimal] | None = None,
) -> tuple[Decimal, str, list[dict[str, str]]]:
    """返回未舍入金额、总算式及可复核中间步骤。"""
    if formula_type not in FORMULA_TYPES:
        raise CalculationError(f"不支持的专业公式：{formula_type}")
    expected_inputs = FORMULA_INPUT_KEYS[formula_type]
    missing_inputs = sorted(expected_inputs - set(inputs))
    unexpected_inputs = sorted(set(inputs) - expected_inputs)
    if missing_inputs:
        raise CalculationError(f"缺少公式输入：{', '.join(missing_inputs)}")
    if unexpected_inputs:
        raise CalculationError(f"存在公式未使用的输入：{', '.join(unexpected_inputs)}")
    required_parameters = FORMULA_REQUIRED_PARAMETERS.get(formula_type, set())
    allowed_parameters = set(required_parameters)
    if formula_type in {"economic_compensation", "n_plus_one", "unlawful_termination_compensation"}:
        cap_applies = _input(inputs, "cap_applies")
        if cap_applies not in {Decimal("0"), Decimal("1")}:
            raise CalculationError("inputs.cap_applies.value 必须为 0 或 1。")
        if cap_applies == 1:
            required_parameters.add("monthly_wage_cap")
        allowed_parameters.add("monthly_wage_cap")
        if cap_applies == 0 and "monthly_wage_cap" in resolved_parameters:
            raise CalculationError("封顶不适用时不得传入 monthly_wage_cap。")
    missing_parameters = sorted(required_parameters - set(resolved_parameters))
    unexpected_parameters = sorted(set(resolved_parameters) - allowed_parameters)
    if missing_parameters:
        raise CalculationError(f"缺少公式参数：{', '.join(missing_parameters)}")
    if unexpected_parameters:
        raise CalculationError(f"存在公式未使用的参数：{', '.join(unexpected_parameters)}")
    prior_amounts = prior_amounts or {}
    steps: list[dict[str, str]] = []

    if formula_type == "economic_compensation":
        wage = _input(inputs, "monthly_wage", positive=True)
        months = _input(inputs, "compensation_months")
        applied_wage = wage
        if "monthly_wage_cap" in resolved_parameters:
            cap = _parameter(resolved_parameters, "monthly_wage_cap")
            applied_wage = min(wage, cap)
            steps.append(_step("补偿工资基数封顶", f"min({wage}, {cap})", applied_wage))
        raw = applied_wage * months
        expression = f"{applied_wage} × {months}"
        steps.append(_step("经济补偿 N", expression, raw))

    elif formula_type == "n_plus_one":
        wage = _input(inputs, "monthly_wage", positive=True)
        months = _input(inputs, "compensation_months")
        notice_base = _input(inputs, "notice_pay_base", positive=True)
        notice_months = _input(inputs, "notice_months", positive=True)
        applied_wage = wage
        if "monthly_wage_cap" in resolved_parameters:
            cap = _parameter(resolved_parameters, "monthly_wage_cap")
            applied_wage = min(wage, cap)
            steps.append(_step("补偿工资基数封顶", f"min({wage}, {cap})", applied_wage))
        compensation = applied_wage * months
        notice = notice_base * notice_months
        raw = compensation + notice
        steps.append(_step("经济补偿 N", f"{applied_wage} × {months}", compensation))
        steps.append(_step("代通知金", f"{notice_base} × {notice_months}", notice))
        expression = f"({applied_wage} × {months}) + ({notice_base} × {notice_months})"
        steps.append(_step("N＋1 合计", expression, raw))

    elif formula_type == "unlawful_termination_compensation":
        wage = _input(inputs, "monthly_wage", positive=True)
        months = _input(inputs, "compensation_months")
        applied_wage = wage
        if "monthly_wage_cap" in resolved_parameters:
            cap = _parameter(resolved_parameters, "monthly_wage_cap")
            applied_wage = min(wage, cap)
            steps.append(_step("赔偿金工资基数封顶", f"min({wage}, {cap})", applied_wage))
        raw = applied_wage * months * Decimal("2")
        expression = f"{applied_wage} × {months} × 2"
        steps.append(_step("违法解除赔偿金 2N", expression, raw))

    elif formula_type in {"overtime_workday", "overtime_rest_day", "overtime_statutory_holiday"}:
        wage = _input(inputs, "monthly_wage", positive=True)
        hours = _input(inputs, "overtime_hours")
        paid_days = _parameter(resolved_parameters, "monthly_paid_days")
        daily_hours = _parameter(resolved_parameters, "daily_hours")
        multiplier = {
            "overtime_workday": Decimal("1.5"),
            "overtime_rest_day": Decimal("2"),
            "overtime_statutory_holiday": Decimal("3"),
        }[formula_type]
        hourly_rate = wage / paid_days / daily_hours
        raw = hourly_rate * hours * multiplier
        steps.append(_step("小时工资折算", f"{wage} ÷ {paid_days} ÷ {daily_hours}", hourly_rate))
        expression = f"({wage} ÷ {paid_days} ÷ {daily_hours}) × {hours} × {multiplier}"
        steps.append(_step("加班工资", expression, raw))

    elif formula_type == "work_injury_lump_sum_disability":
        wage = _input(inputs, "monthly_wage", positive=True)
        months = _input(inputs, "benefit_months")
        raw = wage * months
        expression = f"{wage} × {months}"
        steps.append(_step("一次性伤残补助金", expression, raw))

    elif formula_type == "work_injury_disability_allowance":
        wage = _input(inputs, "monthly_wage", positive=True)
        rate = _input(inputs, "allowance_rate")
        months = _input(inputs, "payment_months", positive=True)
        if rate > 1:
            raise CalculationError("inputs.allowance_rate.value 应使用 0—1 的比例。")
        raw = wage * rate * months
        expression = f"{wage} × {rate} × {months}"
        steps.append(_step("伤残津贴", expression, raw))

    elif formula_type == "work_injury_regional_benefit":
        units = _input(inputs, "benefit_units")
        unit_amount = _parameter(resolved_parameters, "benefit_unit_amount")
        raw = unit_amount * units
        expression = f"{unit_amount} × {units}"
        steps.append(_step("地域工伤待遇", expression, raw))

    elif formula_type in {"work_injury_three_lump_sums", "sum"}:
        component_ids = inputs.get("component_ids")
        if not isinstance(component_ids, list) or not component_ids or not all(
            isinstance(item, str) and item for item in component_ids
        ):
            raise CalculationError("inputs.component_ids 必须是非空计算 ID 数组。")
        if formula_type == "work_injury_three_lump_sums" and len(component_ids) != 3:
            raise CalculationError("三笔一次性待遇必须且只能关联 3 个计算项。")
        missing = [item for item in component_ids if item not in prior_amounts]
        if missing:
            raise CalculationError(f"引用了尚未完成的计算项：{', '.join(missing)}")
        raw = sum((prior_amounts[item] for item in component_ids), Decimal("0"))
        expression = " + ".join(component_ids)
        label = "工伤三笔一次性待遇合计" if formula_type == "work_injury_three_lump_sums" else "金额合计"
        steps.append(_step(label, expression, raw))

    elif formula_type == "non_compete_compensation":
        monthly = _input(inputs, "monthly_compensation", positive=True)
        months = _input(inputs, "payment_months")
        raw = monthly * months
        expression = f"{monthly} × {months}"
        steps.append(_step("竞业限制补偿", expression, raw))

    else:  # pragma: no cover - FORMULA_TYPES 与分支应同步
        raise CalculationError(f"未实现的专业公式：{formula_type}")

    if raw < 0:
        raise CalculationError("计算结果不得为负数。")
    return raw, expression, steps


def canonical_digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def calculation_digest(record: dict[str, Any]) -> str:
    """计算记录的业务摘要；创建／更新时间不影响同一计算的内容哈希。"""
    excluded = {"calculation_digest", "created_by", "created_at", "updated_by", "updated_at"}
    return canonical_digest({key: value for key, value in record.items() if key not in excluded})
