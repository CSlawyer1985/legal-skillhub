#!/usr/bin/env python3
"""劳动解除成本的确定性算术计算器。

这个脚本只计算用户已经提供并标记为可用的数字，不判断解除是否合法、是否应支付
N/2N，也不检索法律。无法确认的输入会进入 blocked 或 needs_human_review，避免把
算术结果包装成法律结论。
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


CENT = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    try:
        return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"金额不是可计算数字：{value!r}") from exc


def json_money(value: Decimal) -> float:
    return float(money(value))


def as_decimal(data: dict[str, Any], key: str, *, required: bool = False) -> Decimal | None:
    value = data.get(key)
    if value is None or value == "":
        if required:
            raise ValueError(f"缺少必需数字字段：{key}")
        return None
    return money(value)


def n_units_from_service_months(service_months: int) -> Decimal:
    if service_months < 0:
        raise ValueError("service_months 不能为负数")
    years, remainder = divmod(service_months, 12)
    if remainder == 0:
        return Decimal(years)
    if remainder < 6:
        return Decimal(years) + Decimal("0.5")
    return Decimal(years + 1)


def derive_service_months(employment: dict[str, Any]) -> tuple[int | None, list[str]]:
    warnings: list[str] = []
    if employment.get("service_months") is not None:
        months = int(employment["service_months"])
        if months < 0:
            raise ValueError("service_months 不能为负数")
        return months, warnings

    start = employment.get("service_start")
    end = employment.get("termination_date")
    if not start or not end:
        return None, ["未提供 service_months 或完整的 service_start/termination_date"]

    try:
        start_year, start_month, start_day = [int(part) for part in str(start).split("-")]
        end_year, end_month, end_day = [int(part) for part in str(end).split("-")]
    except (TypeError, ValueError) as exc:
        raise ValueError("日期必须使用 YYYY-MM-DD") from exc
    months = (end_year - start_year) * 12 + end_month - start_month
    if end_day < start_day:
        months -= 1
    if months < 0:
        raise ValueError("termination_date 不能早于 service_start")
    warnings.append("工龄由日期暂算为完整月数；连续工龄、起止日口径和地方实践仍需人工复核")
    return months, warnings


def wage_base(employment: dict[str, Any], jurisdiction: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    blocked: list[str] = []
    avg = as_decimal(employment, "monthly_average_wage_12m", required=True)
    last = as_decimal(employment, "last_month_wage")
    local_avg = as_decimal(jurisdiction, "local_average_monthly_wage")
    base = avg
    cap_applied = False
    cap_value: Decimal | None = None
    high_wage_possible = bool(employment.get("high_wage_cap_possible", False))
    cap_verified = employment.get("high_wage_cap_verified") is True
    multiplier = money(jurisdiction.get("high_wage_multiplier", 3))

    if high_wage_possible or (local_avg is not None and avg > local_avg * multiplier):
        if local_avg is None or not cap_verified:
            blocked.append("可能触发高工资三倍上限，但地方年度工资数据或适用规则未完成核验")
            warnings.append("同时需要输出未封顶与封顶情景，不得选择唯一工资基数")
        else:
            cap_value = money(local_avg * multiplier)
            if avg > cap_value:
                base = cap_value
                cap_applied = True

    if employment.get("wage_base_verified") is not True:
        warnings.append("月工资基数尚未由律师按工资构成和适用规范完成核验")

    return {
        "monthly_average_wage_12m": json_money(avg),
        "last_month_wage": json_money(last) if last is not None else None,
        "local_average_monthly_wage": json_money(local_avg) if local_avg is not None else None,
        "high_wage_multiplier": json_money(multiplier),
        "cap_value": json_money(cap_value) if cap_value is not None else None,
        "base_used_for_N": json_money(base),
        "cap_applied": cap_applied,
        "warnings": warnings,
        "blocked": blocked,
    }


def addon_items(addons: dict[str, Any]) -> tuple[list[dict[str, Any]], Decimal, list[str]]:
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    total = Decimal("0")
    for key, raw in addons.items():
        if raw is None or raw == "":
            continue
        if isinstance(raw, dict):
            value = raw.get("amount")
            status = raw.get("status", "user_provided_pending_legal_review")
            formula = raw.get("formula", "用户输入金额；需独立核验")
        else:
            value = raw
            status = "user_provided_pending_legal_review"
            formula = "用户输入金额；需独立核验"
        amount = money(value)
        total += amount
        items.append({"id": key, "amount": json_money(amount), "status": status, "formula": formula})
        if status not in {"verified", "已核验"}:
            warnings.append(f"附随项目 {key} 尚未标记为已核验")
    return items, money(total), warnings


def option_result(option: str, n_amount: Decimal, last_month_wage: Decimal | None) -> dict[str, Any]:
    if option == "N":
        return {"option": option, "label": "经济补偿金（N）", "legal_base": json_money(n_amount), "formula": "月工资基数 × N月数"}
    if option == "N+1":
        if last_month_wage is None:
            return {"option": option, "label": "经济补偿金加代通知金（N+1）", "status": "blocked", "gap": "缺少上月工资或代通知金口径", "formula": "N + 一个核验后的月额"}
        total = money(n_amount + last_month_wage)
        return {"option": option, "label": "经济补偿金加代通知金（N+1）", "legal_base": json_money(total), "formula": "N + 上月工资/核验后的一个月代通知金额"}
    if option == "2N":
        total = money(n_amount * 2)
        return {"option": option, "label": "违法解除或终止赔偿金（2N情景）", "legal_base": json_money(total), "formula": "N × 2", "status": "conditional_on_unlawful_termination"}
    if option == "0_claimed":
        return {"option": option, "label": "过失性解除的理论法定补偿基数", "legal_base": 0.0, "formula": "不以N作为法定补偿；合法性和证据另行判断", "status": "high_dispute_exposure"}
    if option == "reinstatement":
        return {"option": option, "label": "继续履行情景", "legal_base": None, "formula": "期间工资和福利按可继续履行及裁判/仲裁状态另行核验", "status": "not_fixed_by_this_calculator"}
    if option == "negotiated":
        return {"option": option, "label": "协商解除", "legal_base": json_money(n_amount), "formula": "默认以N作为比较基线；实际协商金额需用户输入", "status": "negotiated_baseline"}
    raise ValueError(f"不支持的方案：{option}")


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    employment = payload.get("employment") or {}
    jurisdiction = payload.get("jurisdiction") or {}
    addons = payload.get("addons") or {}
    options = payload.get("options") or ["negotiated", "N", "N+1", "2N", "reinstatement"]
    warnings: list[str] = []
    blocked: list[str] = []

    service_months, service_warnings = derive_service_months(employment)
    warnings.extend(service_warnings)
    if service_months is None:
        blocked.append("缺少可计算的工作年限")
        n_months = None
    else:
        n_months = n_units_from_service_months(service_months)

    wage = wage_base(employment, jurisdiction)
    warnings.extend(wage["warnings"])
    blocked.extend(wage["blocked"])

    n_amount: Decimal | None = None
    if n_months is not None and not wage["blocked"]:
        effective_months = n_months
        if wage["cap_applied"]:
            max_years = int(employment.get("high_wage_tenure_cap_years", 12))
            effective_months = min(effective_months, Decimal(max_years))
        n_amount = money(Decimal(str(wage["base_used_for_N"])) * effective_months)
    elif n_months is not None:
        warnings.append("N 仅能生成条件计算；工资封顶或适用规则未完成核验")

    addon_rows, addon_total, addon_warnings = addon_items(addons)
    warnings.extend(addon_warnings)
    result_options: list[dict[str, Any]] = []
    if n_amount is not None:
        last = money(wage["last_month_wage"]) if wage["last_month_wage"] is not None else None
        result_options = [option_result(option, n_amount, last) for option in options]
        for item in result_options:
            if item.get("legal_base") is not None:
                item["with_user_provided_addons"] = json_money(Decimal(str(item["legal_base"])) + addon_total)
    else:
        result_options = [{"option": option, "status": "blocked", "gap": "N 的核心输入尚未完成核验"} for option in options]

    status = "blocked" if blocked else ("needs_human_review" if warnings else "calculated")
    return {
        "schema_version": "labor-termination-calculation/v0.1",
        "status": status,
        "as_of_date": payload.get("as_of_date"),
        "input_echo": {"employment": employment, "jurisdiction": jurisdiction, "options": options, "addons": addons},
        "service_months": service_months,
        "n_months": float(n_months) if n_months is not None else None,
        "wage": wage,
        "addons": {"items": addon_rows, "total": json_money(addon_total)},
        "options": result_options,
        "warnings": warnings,
        "blocked": blocked,
        "disclaimer": "本文件只提供算术和条件化情景，不判断解除是否合法，不替代律师对事实、法源、程序和正式交付的复核。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="劳动解除 N、N+1、2N 条件化算术计算器")
    parser.add_argument("--input-json", required=True, help="项目内计算输入 JSON")
    parser.add_argument("--output-json", help="可选：项目内计算输出 JSON")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        result = calculate(payload)
        serialized = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output_json:
            Path(args.output_json).write_text(serialized + "\n", encoding="utf-8")
        else:
            print(serialized)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"计算失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
