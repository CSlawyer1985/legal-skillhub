#!/usr/bin/env python3
"""Deterministic Decimal and date calculations for policy-oriented skills."""

from __future__ import annotations

import argparse
import calendar
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 40
CENTS = Decimal("0.01")
HUNDRED = Decimal("100")


def dec(value: object) -> Decimal:
    return Decimal(str(value).replace(",", "").strip())


def q(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def text(value: Decimal) -> str:
    return f"{q(value):.2f}"


def component_mode(payload: dict) -> dict:
    rows = []
    total = Decimal("0")
    for item in payload["items"]:
        base = dec(item.get("base", "0"))
        rate = dec(item.get("rate", "0"))
        fixed = dec(item.get("fixed", "0"))
        amount = q(base * rate + fixed)
        rows.append(
            {
                "label": item.get("label", ""),
                "base": str(base),
                "rate": str(rate),
                "fixed": str(fixed),
                "amount": text(amount),
            }
        )
        total += amount
    return {"mode": "components", "items": rows, "total": text(total)}


def gross_net_mode(payload: dict) -> dict:
    amount = dec(payload["amount"])
    rate = dec(payload["rate"])
    direction = payload.get("direction", "gross-to-net")
    if amount < 0 or rate < 0:
        raise ValueError("amount and rate cannot be negative")
    if direction == "gross-to-net":
        gross = amount
        net = gross / (Decimal("1") + rate)
    elif direction == "net-to-gross":
        net = amount
        gross = net * (Decimal("1") + rate)
    else:
        raise ValueError("direction must be gross-to-net or net-to-gross")
    return {
        "mode": "gross-net",
        "direction": direction,
        "rate": str(rate),
        "gross": text(gross),
        "net": text(net),
        "difference": text(gross - net),
    }


def scenario_sum_mode(payload: dict) -> dict:
    scenarios = []
    for scenario in payload["scenarios"]:
        values = [dec(item["value"]) for item in scenario["items"]]
        scenarios.append(
            {
                "label": scenario.get("label", ""),
                "items": scenario["items"],
                "total": text(sum(values, Decimal("0"))),
            }
        )
    return {"mode": "scenario-sum", "scenarios": scenarios}


def annuity_mode(payload: dict) -> dict:
    principal = dec(payload["principal"])
    annual_rate = dec(payload["annual_rate_percent"]) / HUNDRED
    months = int(payload["months"])
    if principal <= 0 or months <= 0 or annual_rate < 0:
        raise ValueError("principal and months must be positive; rate cannot be negative")
    monthly_rate = annual_rate / Decimal("12")
    if monthly_rate == 0:
        payment = principal / months
    else:
        factor = (Decimal("1") + monthly_rate) ** months
        payment = principal * monthly_rate * factor / (factor - Decimal("1"))
    payment = q(payment)
    total_payment = q(payment * months)
    return {
        "mode": "annuity",
        "principal": text(principal),
        "annual_rate_percent": str(dec(payload["annual_rate_percent"])),
        "months": months,
        "monthly_payment": text(payment),
        "total_payment": text(total_payment),
        "total_interest": text(total_payment - principal),
    }


def equal_principal_mode(payload: dict) -> dict:
    principal = dec(payload["principal"])
    annual_rate = dec(payload["annual_rate_percent"]) / HUNDRED
    months = int(payload["months"])
    if principal <= 0 or months <= 0 or annual_rate < 0:
        raise ValueError("principal and months must be positive; rate cannot be negative")
    monthly_rate = annual_rate / Decimal("12")
    principal_part = principal / months
    balance = principal
    schedule = []
    for month in range(1, months + 1):
        interest = q(balance * monthly_rate)
        principal_paid = q(principal_part if month < months else balance)
        payment = q(principal_paid + interest)
        balance = q(balance - principal_paid)
        schedule.append(
            {
                "month": month,
                "principal": text(principal_paid),
                "interest": text(interest),
                "payment": text(payment),
                "remaining": text(max(balance, Decimal("0"))),
            }
        )
    total_payment = sum((dec(row["payment"]) for row in schedule), Decimal("0"))
    return {
        "mode": "equal-principal",
        "principal": text(principal),
        "annual_rate_percent": str(dec(payload["annual_rate_percent"])),
        "months": months,
        "first_payment": schedule[0]["payment"],
        "last_payment": schedule[-1]["payment"],
        "total_payment": text(total_payment),
        "total_interest": text(total_payment - principal),
        "schedule": schedule,
    }


def progressive_tax_mode(payload: dict) -> dict:
    taxable = dec(payload["taxable_amount"])
    if taxable <= 0:
        return {"mode": "progressive-tax", "taxable_amount": text(taxable), "tax": "0.00"}
    matched = None
    for bracket in payload["brackets"]:
        upper = bracket.get("upper")
        if upper is None or taxable <= dec(upper):
            matched = bracket
            break
    if matched is None:
        raise ValueError("no tax bracket matches taxable_amount")
    rate = dec(matched["rate"])
    quick = dec(matched.get("quick_deduction", "0"))
    tax = q(taxable * rate - quick)
    return {
        "mode": "progressive-tax",
        "taxable_amount": text(taxable),
        "matched_rate": str(rate),
        "quick_deduction": str(quick),
        "tax": text(max(tax, Decimal("0"))),
    }


def add_months_mode(payload: dict) -> dict:
    start = date.fromisoformat(payload["date"])
    months = int(payload["months"])
    absolute_month = start.year * 12 + start.month - 1 + months
    year, month_zero = divmod(absolute_month, 12)
    month = month_zero + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    result = date(year, month, day)
    return {
        "mode": "add-months",
        "input_date": start.isoformat(),
        "months": months,
        "result_date": result.isoformat(),
        "note": "The month increment must come from the currently applicable official rule.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=[
            "components",
            "gross-net",
            "scenario-sum",
            "annuity",
            "equal-principal",
            "progressive-tax",
            "add-months",
        ],
    )
    parser.add_argument("--input", type=Path, required=True, help="JSON input file")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    handlers = {
        "components": component_mode,
        "gross-net": gross_net_mode,
        "scenario-sum": scenario_sum_mode,
        "annuity": annuity_mode,
        "equal-principal": equal_principal_mode,
        "progressive-tax": progressive_tax_mode,
        "add-months": add_months_mode,
    }
    print(json.dumps(handlers[args.mode](payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
