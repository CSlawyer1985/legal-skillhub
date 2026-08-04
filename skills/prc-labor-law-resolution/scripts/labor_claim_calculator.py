#!/usr/bin/env python3
"""中国劳动争议请求金额透明暂算工具。

只执行可复核的算术，不替代法律适用判断。所有地方标准、费率、倍率、
基数、封顶值和请求成立条件均需结合争议发生时间与官方现行规则核验。
"""

from __future__ import annotations

import argparse
import calendar
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


class FriendlyParser(argparse.ArgumentParser):
    """把 argparse 的技术报错转换为用户可理解的中文修正指南。"""

    def error(self, message: str) -> None:
        payload = {
            "status": "error",
            "error_code": "INVALID_ARGUMENT",
            "problem": "输入参数不完整或格式不正确。",
            "details": message,
            "how_to_fix": [
                "先运行：python scripts/labor_claim_calculator.py guide",
                "日期统一填写为 YYYY-MM-DD，例如 2026-08-01。",
                "金额只填写数字，例如 8000 或 8000.50，不要带“元”。",
                "再运行对应命令并补齐标记为必填的参数。",
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"日期“{value}”无法识别；请改成 YYYY-MM-DD，例如 2026-08-01"
        ) from exc


def decimal_value(value: Any, field: str, allow_zero: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field}必须是数字，例如 8000 或 0.8") from exc
    minimum_ok = number >= 0 if allow_zero else number > 0
    if not number.is_finite() or not minimum_ok:
        condition = "大于或等于0" if allow_zero else "大于0"
        raise ValueError(f"{field}必须是{condition}的有限数字")
    return number


def positive_decimal(value: str) -> Decimal:
    try:
        return decimal_value(value, "金额")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def nonnegative_decimal(value: str) -> Decimal:
    try:
        return decimal_value(value, "金额", allow_zero=True)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"“{value}”不是整数") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("数量必须大于0")
    return number


def service_months(start: date, end: date) -> int:
    if end < start:
        raise ValueError(
            f"结束日期 {end.isoformat()} 早于开始日期 {start.isoformat()}；"
            "请检查是否填反，或修正其中一个日期"
        )
    months = (end.year - start.year) * 12 + end.month - start.month
    anniversary_day = min(start.day, calendar.monthrange(end.year, end.month)[1])
    if end.day >= anniversary_day:
        months += 1
    return max(months, 1)


def statutory_years(months: int) -> Decimal:
    """按常见的不足半年0.5、超过半年1个月工资模型折算N。"""
    full_years, remainder = divmod(months, 12)
    years = Decimal(full_years)
    if remainder == 0:
        return years
    return years + (Decimal("0.5") if remainder < 6 else Decimal("1"))


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def common_output(calculation: str, result: Decimal, formula: str) -> dict[str, Any]:
    return {
        "status": "success",
        "calculation": calculation,
        "estimated_amount": money(result),
        "formula": formula,
        "legal_status": "算术暂算，是否有权主张及最终金额须依据现行有效规则和证据核验",
    }


def compensation(args: argparse.Namespace) -> dict[str, Any]:
    months = service_months(args.start, args.end)
    n_value = statutory_years(months)
    wage_used = args.monthly_wage
    warnings = []

    if args.local_monthly_cap is not None and wage_used > args.local_monthly_cap:
        wage_used = args.local_monthly_cap
        warnings.append("已按用户提供的当地月工资封顶值暂算；须核验数值、年份和适用条件。")
    if args.max_years is not None and n_value > Decimal(args.max_years):
        n_value = Decimal(args.max_years)
        warnings.append("已按用户提供的最高计发年限暂算；须核验是否适用于本案。")

    multiplier = Decimal("2") if args.mode == "unlawful" else Decimal("1")
    result = wage_used * n_value * multiplier
    output = common_output(
        "compensation",
        result,
        f"{money(wage_used)} × {n_value} × {multiplier}",
    )
    output.update(
        {
            "mode": args.mode,
            "service_start": args.start.isoformat(),
            "service_end": args.end.isoformat(),
            "service_months_model": months,
            "n_years_model": str(n_value),
            "monthly_wage_input": money(args.monthly_wage),
            "monthly_wage_used": money(wage_used),
            "multiplier": str(multiplier),
            "warnings": [
                "不得仅凭本结果断言应支付N或2N；先核验解除性质、法律要件和证据。",
                "如涉及2008年前工龄或不同规则分段，请改用 segmented-compensation。",
                *warnings,
            ],
            "next_steps": [
                "核对入职、解除或终止日期及工资基数证据。",
                "核验当地封顶标准、适用年度和是否需要分段。",
                "把计算结果连同成立条件写入请求事项，不要只写总金额。",
            ],
        }
    )
    return output


def segmented_compensation(args: argparse.Namespace) -> dict[str, Any]:
    try:
        raw_segments = json.loads(args.segments_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "分段JSON无法解析。请使用双引号包住字段名，并参考 guide 中的完整示例；"
            f"错误位置：第{exc.lineno}行第{exc.colno}列"
        ) from exc
    if not isinstance(raw_segments, list) or not raw_segments:
        raise ValueError("segments-json 必须是至少包含一个分段对象的数组")

    details = []
    total = Decimal("0")
    previous_end: date | None = None
    for index, item in enumerate(raw_segments, 1):
        if not isinstance(item, dict):
            raise ValueError(f"第{index}段必须是JSON对象")
        missing = [key for key in ("label", "start", "end", "monthly_wage", "multiplier") if key not in item]
        if missing:
            raise ValueError(f"第{index}段缺少字段：{', '.join(missing)}")
        try:
            start = parse_date(str(item["start"]))
            end = parse_date(str(item["end"]))
        except argparse.ArgumentTypeError as exc:
            raise ValueError(f"第{index}段：{exc}") from exc
        if previous_end is not None and start <= previous_end:
            raise ValueError(
                f"第{index}段与前一段日期重叠或顺序错误；请保证后一段开始日期晚于前一段结束日期"
            )
        months = service_months(start, end)
        n_value = statutory_years(months)
        wage = decimal_value(item["monthly_wage"], f"第{index}段月工资")
        multiplier = decimal_value(item["multiplier"], f"第{index}段倍率")
        cap = None
        if item.get("monthly_cap") is not None:
            cap = decimal_value(item["monthly_cap"], f"第{index}段月工资封顶值")
            wage = min(wage, cap)
        if item.get("max_years") is not None:
            max_years = decimal_value(item["max_years"], f"第{index}段最高年限")
            n_value = min(n_value, max_years)
        amount = wage * n_value * multiplier
        total += amount
        details.append(
            {
                "label": str(item["label"]),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "service_months_model": months,
                "n_years_model": str(n_value),
                "monthly_wage_used": money(wage),
                "multiplier": str(multiplier),
                "monthly_cap_input": money(cap) if cap is not None else None,
                "amount": money(amount),
                "formula": f"{money(wage)} × {n_value} × {multiplier}",
            }
        )
        previous_end = end

    output = common_output(
        "segmented_compensation",
        total,
        "各分段金额相加，详见 segments",
    )
    output.update(
        {
            "segments": details,
            "warnings": [
                "各段起止日、工资基数、倍率、封顶值和最高年限均由用户提供，必须逐段核验法律依据。",
                "不得用本工具自行判断2008年前后分别适用何种规则。",
            ],
            "next_steps": [
                "为每一分段注明规范名称、适用时间和计算理由。",
                "检查分段是否遗漏、重叠或错误使用同一工资基数。",
            ],
        }
    )
    return output


def arrears(args: argparse.Namespace) -> dict[str, Any]:
    total = args.monthly_wage * Decimal(args.months) - args.already_paid
    if total < 0:
        raise ValueError(
            f"已支付金额 {money(args.already_paid)} 高于暂算应付总额 "
            f"{money(args.monthly_wage * Decimal(args.months))}；请核对月数、月工资或已付金额"
        )
    output = common_output(
        "wage_arrears",
        total,
        f"{money(args.monthly_wage)} × {args.months} - {money(args.already_paid)}",
    )
    output.update(
        {
            "monthly_wage": money(args.monthly_wage),
            "months": args.months,
            "already_paid": money(args.already_paid),
            "warnings": [
                "本结果不自动处理提成、奖金、加班费、扣款合法性或税费争议。",
                "须用合同、工资流水、工资条和考勤等材料核验基数与期间。",
            ],
            "next_steps": ["按月份制作应付、实付和差额明细表。", "分别列明固定工资、浮动工资和其他请求。"],
        }
    )
    return output


def overtime(args: argparse.Namespace) -> dict[str, Any]:
    base = args.hourly_base
    weekday = base * args.weekday_hours * args.weekday_multiplier
    rest = base * args.rest_hours * args.rest_multiplier
    holiday = base * args.holiday_hours * args.holiday_multiplier
    total = weekday + rest + holiday - args.already_paid
    if total < 0:
        raise ValueError("已支付加班费高于当前参数暂算总额；请核对小时、基数、倍率或已付金额")
    output = common_output(
        "overtime",
        total,
        "工作日 + 休息日 + 法定节假日加班费 - 已支付金额",
    )
    output.update(
        {
            "breakdown": {
                "weekday": money(weekday),
                "rest_day": money(rest),
                "statutory_holiday": money(holiday),
                "already_paid": money(args.already_paid),
            },
            "inputs": {
                "hourly_base": money(base),
                "weekday_hours": str(args.weekday_hours),
                "weekday_multiplier": str(args.weekday_multiplier),
                "rest_hours": str(args.rest_hours),
                "rest_multiplier": str(args.rest_multiplier),
                "holiday_hours": str(args.holiday_hours),
                "holiday_multiplier": str(args.holiday_multiplier),
            },
            "warnings": [
                "倍率由用户明确提供，须先核验工时制度、加班类型、调休及现行规则。",
                "不得仅以工作时长推定全部加班成立；还需分析安排、审批、控制和证据。",
            ],
            "next_steps": ["按日期制作加班明细。", "关联考勤、排班、审批、聊天和工作成果。"],
        }
    )
    return output


def rate_based(args: argparse.Namespace) -> dict[str, Any]:
    gross = args.daily_base * Decimal(args.days) * args.rate
    total = gross - args.already_paid
    if total < 0:
        raise ValueError("已支付金额高于当前参数暂算额；请核对天数、日基数、比例或已付金额")
    output = common_output(
        args.command.replace("-", "_"),
        total,
        f"{money(args.daily_base)} × {args.days}天 × {args.rate} - {money(args.already_paid)}",
    )
    output.update(
        {
            "daily_base": money(args.daily_base),
            "days": args.days,
            "rate": str(args.rate),
            "already_paid": money(args.already_paid),
            "warnings": [
                "日基数、天数和比例均由用户提供，须根据所在地、争议时间和具体制度核验。",
                "本工具不判断休假资格、医疗期、应休天数或单位已支付项目。",
            ],
            "next_steps": ["保存当地官方标准或单位合法制度。", "按日期和已付项目制作明细。"],
        }
    )
    return output


def guide(_: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": "success",
        "title": "劳动请求金额暂算向导",
        "how_to_use": "也可在对话中直接说“请使用 prc-labor-law-resolution 技能，帮我计算……”，无需自己运行命令。",
        "choose_one": [
            {"scenario": "经济补偿或违法解除赔偿", "command": "compensation"},
            {"scenario": "2008年前后或其他复杂分段", "command": "segmented-compensation"},
            {"scenario": "固定工资欠付", "command": "wage-arrears"},
            {"scenario": "加班费", "command": "overtime"},
            {"scenario": "按日基数×天数×比例暂算病假工资", "command": "sick-leave"},
            {"scenario": "按日基数×天数×比例暂算未休年假工资", "command": "annual-leave"},
        ],
        "examples": [
            "python scripts/labor_claim_calculator.py compensation --start 2021-04-01 --end 2026-08-01 --monthly-wage 8000 --mode economic",
            "python scripts/labor_claim_calculator.py overtime --hourly-base 50 --weekday-hours 10 --weekday-multiplier 1.5 --rest-hours 8 --rest-multiplier 2 --holiday-hours 0 --holiday-multiplier 3",
            "python scripts/labor_claim_calculator.py sick-leave --daily-base 300 --days 5 --rate 0.8",
            "python scripts/labor_claim_calculator.py annual-leave --daily-base 368 --days 5 --rate 2",
        ],
        "segmented_example": [
            {"label": "2008年前段", "start": "2005-01-01", "end": "2007-12-31", "monthly_wage": 8000, "multiplier": 1},
            {"label": "2008年后段", "start": "2008-01-01", "end": "2026-08-01", "monthly_wage": 10000, "multiplier": 1, "monthly_cap": 30000, "max_years": 12},
        ],
        "important": [
            "先核验请求是否成立，再使用计算结果。",
            "地方标准、比例、倍率和封顶值必须来自争议发生时有效的官方规则。",
            "不会填参数时直接描述事实，由技能逐项追问，不需要学习命令行。",
        ],
    }


def add_rate_parser(subparsers: Any, command: str, help_text: str) -> None:
    parser = subparsers.add_parser(command, help=help_text)
    parser.add_argument("--daily-base", type=positive_decimal, required=True, help="已核验的日计算基数")
    parser.add_argument("--days", type=positive_int, required=True, help="已核验的天数")
    parser.add_argument("--rate", type=nonnegative_decimal, required=True, help="已核验的支付比例，如0.8或2")
    parser.add_argument("--already-paid", type=nonnegative_decimal, default=Decimal("0"))
    parser.set_defaults(handler=rate_based)


def build_parser() -> FriendlyParser:
    parser = FriendlyParser(description="中国劳动争议请求金额透明暂算工具")
    subparsers = parser.add_subparsers(dest="command", required=True, parser_class=FriendlyParser)

    guide_parser = subparsers.add_parser("guide", help="查看中文选择向导和示例")
    guide_parser.set_defaults(handler=guide)

    comp = subparsers.add_parser("compensation", help="暂算单一规则下的N或2N")
    comp.add_argument("--start", type=parse_date, required=True, help="用工开始日期 YYYY-MM-DD")
    comp.add_argument("--end", type=parse_date, required=True, help="用工结束日期 YYYY-MM-DD")
    comp.add_argument("--monthly-wage", type=positive_decimal, required=True, help="月工资基数")
    comp.add_argument("--mode", choices=("economic", "unlawful"), required=True, help="economic=N，unlawful=2N")
    comp.add_argument("--local-monthly-cap", type=positive_decimal, help="已核验的当地月工资封顶值")
    comp.add_argument("--max-years", type=int, choices=range(1, 101), metavar="1-100", help="已核验的最高计发年限")
    comp.set_defaults(handler=compensation)

    segmented = subparsers.add_parser("segmented-compensation", help="按用户提供规则处理复杂分段工龄")
    segmented.add_argument("--segments-json", required=True, help="JSON数组；运行guide查看示例结构")
    segmented.set_defaults(handler=segmented_compensation)

    wages = subparsers.add_parser("wage-arrears", help="暂算固定月工资欠付")
    wages.add_argument("--monthly-wage", type=positive_decimal, required=True)
    wages.add_argument("--months", type=positive_int, required=True)
    wages.add_argument("--already-paid", type=nonnegative_decimal, default=Decimal("0"))
    wages.set_defaults(handler=arrears)

    overtime_parser = subparsers.add_parser("overtime", help="按用户核验的基数和倍率暂算加班费")
    overtime_parser.add_argument("--hourly-base", type=positive_decimal, required=True)
    overtime_parser.add_argument("--weekday-hours", type=nonnegative_decimal, required=True)
    overtime_parser.add_argument("--weekday-multiplier", type=nonnegative_decimal, required=True)
    overtime_parser.add_argument("--rest-hours", type=nonnegative_decimal, required=True)
    overtime_parser.add_argument("--rest-multiplier", type=nonnegative_decimal, required=True)
    overtime_parser.add_argument("--holiday-hours", type=nonnegative_decimal, required=True)
    overtime_parser.add_argument("--holiday-multiplier", type=nonnegative_decimal, required=True)
    overtime_parser.add_argument("--already-paid", type=nonnegative_decimal, default=Decimal("0"))
    overtime_parser.set_defaults(handler=overtime)

    add_rate_parser(subparsers, "sick-leave", "按用户核验的日基数、天数和比例暂算病假工资")
    add_rate_parser(subparsers, "annual-leave", "按用户核验的日基数、天数和比例暂算未休年假工资")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        output = args.handler(args)
    except (ValueError, TypeError) as exc:
        payload = {
            "status": "error",
            "error_code": "CALCULATION_INPUT_ERROR",
            "problem": str(exc),
            "how_to_fix": [
                "根据上面的具体原因修改输入。",
                "运行 guide 查看对应场景的完整示例。",
                "仍不确定时，不要猜数值；在对话中提供事实和材料，由技能逐项追问。",
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
