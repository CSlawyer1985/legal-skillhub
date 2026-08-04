#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蚂蚁工资条 · 工伤待遇计算器 v1.0
==================================
中国工伤待遇精算引擎。
覆盖1-10级伤残补助 × 停工留薪期工资 × 伤残津贴 × 解除合同补助。

模式:
  默认模式    计算工伤待遇
  --list-levels  列出1-10级伤残待遇标准

依赖:
  - Python 3.10+

政策依据:
  - 《工伤保险条例》（国务院令第586号）
"""

import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP

# ============================================================
# Decimal helpers
# ============================================================

def R2(val):
    """Decimal 四舍五入到分"""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# ============================================================
# 伤残等级参数库
# ============================================================

# 一次性伤残补助金月数（1-10级）
DISABILITY_LUMP_SUM = {
    1: 27,   # 1级: 27个月
    2: 25,   # 2级: 25个月
    3: 23,   # 3级: 23个月
    4: 21,   # 4级: 21个月
    5: 18,   # 5级: 18个月
    6: 16,   # 6级: 16个月
    7: 13,   # 7级: 13个月
    8: 11,   # 8级: 11个月
    9: 9,    # 9级: 9个月
    10: 7,   # 10级: 7个月
}

# 伤残津贴比例（1-4级按月发放）
DISABILITY_PENSION_RATE = {
    1: Decimal("0.90"),   # 1级: 90%
    2: Decimal("0.85"),   # 2级: 85%
    3: Decimal("0.80"),   # 3级: 80%
    4: Decimal("0.75"),   # 4级: 75%
}

# 一次性工伤医疗补助金（5-10级，解除合同时，按各省统筹地区上年度月平工资倍数估算）
# 此处用全国通用参考值（月数）
MEDICAL_SUBSIDY_MONTHS = {
    5: 10,   # 5级: 约10个月
    6: 8,    # 6级: 约8个月
    7: 6,    # 7级: 约6个月
    8: 4,    # 8级: 约4个月
    9: 2,    # 9级: 约2个月
    10: 1,   # 10级: 约1个月
}

# 一次性伤残就业补助金（5-10级，解除合同时）
EMPLOYMENT_SUBSIDY_MONTHS = {
    5: 12,   # 5级: 约12个月
    6: 10,   # 6级: 约10个月
    7: 8,    # 7级: 约8个月
    8: 6,    # 8级: 约6个月
    9: 4,    # 9级: 约4个月
    10: 2,   # 10级: 约2个月
}

# 默认停工留薪期上限
MAX_SUSPEND_MONTHS = 12


# ============================================================
# 计算核心
# ============================================================

def calculate_work_injury(monthly_salary, disability_level, suspend_period, terminate):
    """
    计算工伤待遇
    """
    monthly_salary = Decimal(str(monthly_salary))
    level = int(disability_level)
    suspend = min(int(suspend_period), MAX_SUSPEND_MONTHS)

    # 停工留薪期工资
    suspend_pay = monthly_salary * Decimal(str(suspend))

    # 一次性伤残补助金
    lump_sum_months = DISABILITY_LUMP_SUM.get(level, 0)
    lump_sum = monthly_salary * Decimal(str(lump_sum_months))

    # 伤残津贴（仅1-4级）
    pension_rate = DISABILITY_PENSION_RATE.get(level)
    monthly_pension = monthly_salary * pension_rate if pension_rate else None

    # 一次性医疗/就业补助金（仅5-10级且解除合同）
    medical_subsidy = None
    employment_subsidy = None
    if level >= 5 and terminate:
        med_months = MEDICAL_SUBSIDY_MONTHS.get(level, 0)
        emp_months = EMPLOYMENT_SUBSIDY_MONTHS.get(level, 0)
        medical_subsidy = monthly_salary * Decimal(str(med_months))
        employment_subsidy = monthly_salary * Decimal(str(emp_months))

    # 合计
    total = suspend_pay + lump_sum
    if medical_subsidy:
        total += medical_subsidy
    if employment_subsidy:
        total += employment_subsidy

    return {
        "monthly_salary": monthly_salary,
        "level": level,
        "suspend_period": suspend,
        "actual_suspend": suspend,
        "terminate": terminate,
        "suspend_pay": R2(suspend_pay),
        "lump_sum_months": lump_sum_months,
        "lump_sum": R2(lump_sum),
        "pension_rate": pension_rate,
        "monthly_pension": R2(monthly_pension) if monthly_pension else None,
        "medical_subsidy": R2(medical_subsidy) if medical_subsidy else None,
        "employment_subsidy": R2(employment_subsidy) if employment_subsidy else None,
        "total": R2(total),
    }


# ============================================================
# 报告输出
# ============================================================

def format_report(result):
    """格式化报告输出"""
    lines = []
    lines.append("=" * 64)
    lines.append("  蚂蚁工资条 · 工伤待遇计算报告")
    lines.append(f"  伤残等级: {result['level']}级 | 工伤前月均工资: {result['monthly_salary']}元")
    lines.append("=" * 64)
    lines.append("")

    ms = result["monthly_salary"]
    lines.append("  📋 基本信息")
    lines.append(f"  工伤前12个月平均工资:     {ms} 元/月")
    lines.append(f"  伤残等级:                  {result['level']}级")
    lines.append(f"  停工留薪期:                {result['suspend_period']}个月")
    lines.append(f"  是否解除劳动关系:          {'是' if result['terminate'] else '否'}")
    lines.append("")

    # 停工留薪期工资
    lines.append("  📅 停工留薪期工资")
    lines.append(f"  计算标准:                  原工资福利待遇不变")
    lines.append(f"  月工资:                    {ms} 元/月")
    lines.append(f"  停工留薪期:                {result['actual_suspend']}个月")
    lines.append(f"  停工留薪期工资合计:        {result['suspend_pay']} 元")
    lines.append("")

    # 一次性伤残补助金
    lines.append("  💰 一次性伤残补助金")
    lines.append(f"  计算公式:                  本人工资 × 补助月数")
    lines.append(f"  伤残等级:                  {result['level']}级")
    lines.append(f"  补助月数:                  {result['lump_sum_months']}个月")
    lines.append(f"  一次性伤残补助金:          {result['lump_sum']} 元 (= {ms} × {result['lump_sum_months']})")
    lines.append("")

    # 伤残津贴
    lines.append("  📊 伤残津贴")
    if result["monthly_pension"]:
        rate_pct = int(result["pension_rate"] * 100)
        lines.append(f"  适用条件:                  1-4级伤残按月发放")
        lines.append(f"  伤残等级:                  {result['level']}级")
        lines.append(f"  发放比例:                  本人工资的{rate_pct}%")
        lines.append(f"  月伤残津贴:                {result['monthly_pension']} 元/月")
        lines.append(f"  年伤残津贴:                {R2(result['monthly_pension'] * 12)} 元/年")
    else:
        lines.append(f"  适用条件:                  1-4级伤残按月发放")
        lines.append(f"  当前等级:                  {result['level']}级（不适用伤残津贴）")
    lines.append("")

    # 一次性医疗/就业补助金
    lines.append("  📋 一次性医疗/就业补助金")
    if result["level"] <= 4:
        lines.append(f"  适用条件:                  5-10级解除劳动合同时发放")
        lines.append(f"  当前等级:                  {result['level']}级（1-4级保留劳动关系，不适用）")
    elif result["terminate"]:
        lines.append(f"  适用条件:                  5-10级解除劳动合同时发放")
        lines.append(f"  当前状态:                  已解除劳动关系")
        med_months = MEDICAL_SUBSIDY_MONTHS.get(result["level"], 0)
        emp_months = EMPLOYMENT_SUBSIDY_MONTHS.get(result["level"], 0)
        lines.append(f"  一次性工伤医疗补助金:      {result['medical_subsidy']} 元 (约{med_months}个月工资)")
        lines.append(f"  一次性伤残就业补助金:      {result['employment_subsidy']} 元 (约{emp_months}个月工资)")
        lines.append(f"  📌 一次性补助金按各省统筹地区上年度月平工资计发，此处按本人工资估算")
    else:
        lines.append(f"  适用条件:                  5-10级解除劳动合同时发放")
        lines.append(f"  当前状态:                  未解除劳动关系（不适用）")
        lines.append(f"  📌 若后续解除合同，可获得相应补助")
    lines.append("")

    # 汇总
    lines.append("  ✅ 汇总")
    lines.append(f"  停工留薪期工资:            {result['suspend_pay']} 元")
    lines.append(f"  一次性伤残补助金:          {result['lump_sum']} 元")
    if result["medical_subsidy"]:
        lines.append(f"  一次性工伤医疗补助金:      {result['medical_subsidy']} 元")
    if result["employment_subsidy"]:
        lines.append(f"  一次性伤残就业补助金:      {result['employment_subsidy']} 元")
    if result["monthly_pension"]:
        lines.append(f"  月伤残津贴(按月):          {result['monthly_pension']} 元/月")
    lines.append(f"  工伤待遇合计(一次性):      {result['total']} 元")
    lines.append("=" * 64)

    return "\n".join(lines)


def list_levels():
    """列出1-10级伤残待遇标准"""
    lines = []
    lines.append("=" * 64)
    lines.append("  蚂蚁工资条 · 工伤待遇计算器 — 伤残等级待遇标准")
    lines.append("=" * 64)
    lines.append("")
    lines.append(f"  {'等级':<8} {'一次性补助月数':<16} {'伤残津贴比例':<16} {'适用范围'}")
    lines.append(f"  {'----':<8} {'--------------':<16} {'------------':<16} {'--------'}")

    for level in range(1, 11):
        lump = DISABILITY_LUMP_SUM[level]
        if level <= 4:
            rate = f"{int(DISABILITY_PENSION_RATE[level] * 100)}%"
            scope = "伤残津贴(按月)"
        else:
            rate = "—"
            scope = "解除合同可领补助"
        lines.append(f"  {str(level)+'级':<8} {str(lump)+'个月':<16} {rate:<16} {scope}")

    lines.append("")
    lines.append("  说明:")
    lines.append("  - 1-4级: 保留劳动关系，按月发放伤残津贴")
    lines.append("  - 5-6级: 保留劳动关系，安排适当工作；难以安排的按月发津贴(70%/60%)")
    lines.append("  - 7-10级: 劳动合同期满或职工提出解除，可领一次性医疗+就业补助金")
    lines.append("  - 一次性医疗/就业补助金标准因省而异，以上为参考值")
    lines.append("=" * 64)
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="蚂蚁工资条 · 工伤待遇计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--monthly-salary", type=float, help="工伤前12个月平均月工资（元）")
    parser.add_argument("--disability-level", type=int, choices=range(1, 11), help="伤残等级（1-10）")
    parser.add_argument("--suspend-period", type=int, default=3, help="停工留薪期月数（默认3，最多12）")
    parser.add_argument("--terminate", action="store_true", help="是否解除劳动关系（仅5-10级适用）")
    parser.add_argument("--list-levels", action="store_true", help="列出1-10级伤残待遇标准")

    args = parser.parse_args()

    if args.list_levels:
        print(list_levels())
        return

    if not args.monthly_salary or not args.disability_level:
        print("错误: 计算 --monthly-salary 和 --disability-level 为必填参数")
        print("使用 --help 查看帮助")
        sys.exit(1)

    result = calculate_work_injury(
        args.monthly_salary, args.disability_level,
        args.suspend_period, args.terminate
    )
    print(format_report(result))


if __name__ == "__main__":
    main()
