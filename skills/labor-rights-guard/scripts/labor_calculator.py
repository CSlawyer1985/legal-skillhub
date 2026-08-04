#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
劳动维权费用计算工具

功能：
  1. 加班费计算（延时加班/休息日加班/法定节假日加班）
  2. 经济补偿金计算（N）
  3. 违法解雇赔偿金计算（2N）
  4. 未签劳动合同双倍工资计算

用法：
  python labor_calculator.py --type overtime --monthly-salary 10000 --overtime-hours 8 --overtime-category holiday
  python labor_calculator.py --type compensation --monthly-salary 10000 --years 3 --months 5
  python labor_calculator.py --type double-salary --monthly-salary 10000 --uncontracted-months 10
"""

import argparse
import sys

# 月计薪天数
MONTHLY_PAID_DAYS = 21.75
# 每日工作小时数
DAILY_WORK_HOURS = 8

# 加班倍率
OVERTIME_RATES = {
    "extended": 1.5,    # 延时加班
    "restday": 2.0,     # 休息日加班
    "holiday": 3.0,     # 法定节假日加班
}

OVERTIME_LABELS = {
    "extended": "工作日延时加班",
    "restday": "休息日加班",
    "holiday": "法定节假日加班",
}


def calc_daily_wage(monthly_salary: float) -> float:
    """计算日工资"""
    return round(monthly_salary / MONTHLY_PAID_DAYS, 2)


def calc_hourly_wage(monthly_salary: float) -> float:
    """计算小时工资"""
    daily = calc_daily_wage(monthly_salary)
    return round(daily / DAILY_WORK_HOURS, 2)


def calc_overtime_pay(monthly_salary: float, overtime_hours: float, category: str) -> dict:
    """
    计算加班费

    参数:
      monthly_salary: 月工资标准
      overtime_hours: 加班小时数
      category: 加班类别 (extended/restday/holiday)
    """
    if category not in OVERTIME_RATES:
        raise ValueError(f"无效的加班类别: {category}，可选: extended/restday/holiday")

    hourly_wage = calc_hourly_wage(monthly_salary)
    daily_wage = calc_daily_wage(monthly_salary)
    rate = OVERTIME_RATES[category]
    label = OVERTIME_LABELS[category]

    if category == "extended":
        # 延时加班按小时计算
        overtime_pay = round(hourly_wage * rate * overtime_hours, 2)
        detail = f"小时工资 {hourly_wage} 元 × {rate} 倍 × {overtime_hours} 小时"
    else:
        # 休息日和节假日加班，输入小时数折算天数
        overtime_days = overtime_hours / DAILY_WORK_HOURS
        overtime_pay = round(daily_wage * rate * overtime_days, 2)
        detail = f"日工资 {daily_wage} 元 × {rate} 倍 × {overtime_days:.2f} 天"

    result = {
        "加班类型": label,
        "月工资标准": f"{monthly_salary} 元",
        "日工资": f"{daily_wage} 元",
        "小时工资": f"{hourly_wage} 元",
        "加班时长": f"{overtime_hours} 小时",
        "加班倍率": f"{rate} 倍",
        "加班费": f"{overtime_pay} 元",
        "计算过程": detail,
    }

    if category == "holiday":
        result["特别说明"] = "法定节假日加班三倍工资为额外支付，加上当日正常工资，实际应得4倍日工资"

    return result


def calc_compensation(monthly_salary: float, years: float, months: float = 0, illegal: bool = False) -> dict:
    """
    计算经济补偿金或违法解雇赔偿金

    参数:
      monthly_salary: 月工资（解除合同前12个月平均工资）
      years: 工作年限（整数年）
      months: 零头月份
      illegal: 是否违法解雇（True则计算2N赔偿金）
    """
    total_years = years + months / 12.0

    # 计算N
    if months >= 6:
        n = years + 1
    elif months > 0:
        n = years + 0.5
    else:
        n = years

    if n < 0.5:
        n = 0.5

    compensation = round(monthly_salary * n, 2)

    if illegal:
        # 违法解雇 2N
        total = round(compensation * 2, 2)
        result = {
            "类型": "违法解雇赔偿金（2N）",
            "月工资标准": f"{monthly_salary} 元",
            "工作年限": f"{int(years)}年{int(months)}个月",
            "N值": f"{n} 个月工资",
            "经济补偿金（N）": f"{compensation} 元",
            "赔偿金（2N）": f"{total} 元",
            "计算过程": f"{monthly_salary} × {n} × 2 = {total} 元",
        }
    else:
        result = {
            "类型": "经济补偿金（N）",
            "月工资标准": f"{monthly_salary} 元",
            "工作年限": f"{int(years)}年{int(months)}个月",
            "N值": f"{n} 个月工资",
            "经济补偿金": f"{compensation} 元",
            "计算过程": f"{monthly_salary} × {n} = {compensation} 元",
            "说明": "每满1年支付1个月工资；6个月以上不满1年按1年算；不满6个月支付半个月工资",
        }

    return result


def calc_double_salary(monthly_salary: float, uncontracted_months: int) -> dict:
    """
    计算未签劳动合同双倍工资

    参数:
      monthly_salary: 月工资标准
      uncontracted_months: 未签合同的月数（超过1个月的部分，最多11个月）
    """
    # 双倍工资从用工第2个月起算，最多11个月
    payable_months = min(uncontracted_months, 11)

    if payable_months <= 0:
        return {
            "类型": "未签劳动合同双倍工资",
            "结果": "未超过1个月，无需支付双倍工资",
            "说明": "用人单位自用工之日起1个月内签订合同即可，超过1个月才需支付双倍工资",
        }

    extra_pay = round(monthly_salary * payable_months, 2)
    total = round(monthly_salary * payable_months + monthly_salary * payable_months, 2)

    result = {
        "类型": "未签劳动合同双倍工资",
        "月工资标准": f"{monthly_salary} 元",
        "未签合同月数": f"{uncontracted_months} 个月",
        "应支付双倍工资月数": f"{payable_months} 个月",
        "额外支付金额": f"{extra_pay} 元",
        "计算过程": f"额外支付 = {monthly_salary} × {payable_months} = {extra_pay} 元",
        "说明": "双倍工资即正常工资+额外一倍工资，此处显示额外需支付部分",
    }

    if uncontracted_months >= 12:
        result["特别说明"] = "满1年未签合同视为已订立无固定期限合同，双倍工资最多支付11个月"

    return result


def format_result(result: dict) -> str:
    """格式化输出结果"""
    lines = []
    for key, value in result.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="劳动维权费用计算工具")
    subparsers = parser.add_subparsers(dest="type", help="计算类型")

    # 加班费计算
    overtime_parser = subparsers.add_parser("overtime", help="加班费计算")
    overtime_parser.add_argument("--monthly-salary", type=float, required=True, help="月工资标准（元）")
    overtime_parser.add_argument("--overtime-hours", type=float, required=True, help="加班小时数")
    overtime_parser.add_argument(
        "--category", choices=["extended", "restday", "holiday"], required=True,
        help="加班类别: extended=延时加班, restday=休息日加班, holiday=法定节假日加班"
    )

    # 经济补偿金/赔偿金计算
    comp_parser = subparsers.add_parser("compensation", help="经济补偿金/赔偿金计算")
    comp_parser.add_argument("--monthly-salary", type=float, required=True, help="月工资标准（元）")
    comp_parser.add_argument("--years", type=int, required=True, help="工作年限（整数）")
    comp_parser.add_argument("--months", type=int, default=0, help="零头月份")
    comp_parser.add_argument("--illegal", action="store_true", help="是否违法解雇（计算2N赔偿金）")

    # 双倍工资计算
    double_parser = subparsers.add_parser("double-salary", help="未签劳动合同双倍工资计算")
    double_parser.add_argument("--monthly-salary", type=float, required=True, help="月工资标准（元）")
    double_parser.add_argument("--uncontracted-months", type=int, required=True, help="未签合同月数")

    args = parser.parse_args()

    if not args.type:
        parser.print_help()
        sys.exit(1)

    if args.type == "overtime":
        result = calc_overtime_pay(args.monthly_salary, args.overtime_hours, args.category)
    elif args.type == "compensation":
        result = calc_compensation(args.monthly_salary, args.years, args.months, args.illegal)
    elif args.type == "double-salary":
        result = calc_double_salary(args.monthly_salary, args.uncontracted_months)
    else:
        print(f"未知计算类型: {args.type}")
        sys.exit(1)

    print("=== 计算结果 ===")
    print(format_result(result))


if __name__ == "__main__":
    main()
