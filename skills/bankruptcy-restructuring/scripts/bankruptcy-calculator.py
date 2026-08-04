#!/usr/bin/env python3
"""
破产分配测算工具
—— 债权比例/清偿率/分配金额测算
用法：python bankruptcy_calculator.py --total-assets 500 --priority-claims 80 --tax-claims 50 --ordinary-claims 2000
"""
import argparse
import json
import sys
from typing import Dict, List


def calc_distribution(
    total_assets: float,
    bankruptcy_expenses: float,
    common_benefit_debts: float,
    employee_claims: float,
    tax_claims: float,
    ordinary_claims: float,
    secured_claims_value: float = 0,
    secured_assets_value: float = 0,
    subordinate_claims: float = 0,
) -> Dict:
    """
    破产分配测算
    分配顺序：破产费用+共益债务 → 职工债权 → 税款债权 → 普通债权 → 劣后债权
    """
    remaining = total_assets
    results = {}

    # 破产费用+共益债务（随时清偿）
    expenses_total = bankruptcy_expenses + common_benefit_debts
    if expenses_total > 0:
        if remaining >= expenses_total:
            results["破产费用与共益债务"] = {
                "claim": expenses_total,
                "distributed": expenses_total,
                "ratio": 100.0,
                "remaining_after": remaining - expenses_total
            }
            remaining -= expenses_total
        else:
            # 不足时按比例分配（所有未付部分成为普通股权的劣后部分）
            results["破产费用与共益债务"] = {
                "claim": expenses_total,
                "distributed": remaining,
                "ratio": round(remaining / expenses_total * 100, 2),
                "remaining_after": 0,
                "note": "⚠️ 破产费用不足，按比例分配"
            }
            remaining = 0

    # 有财产担保债权（别除权，担保物价值范围内优先）
    if secured_claims_value > 0 and secured_assets_value > 0:
        secured_recovery = min(secured_claims_value, secured_assets_value)
        secured_shortfall = max(0, secured_claims_value - secured_assets_value)
        results["有财产担保债权（别除权）"] = {
            "claim": secured_claims_value,
            "distributed": secured_recovery,
            "ratio": round(secured_recovery / secured_claims_value * 100, 2),
            "shortfall_as_ordinary": secured_shortfall,
            "note": f"担保物价值{secured_assets_value:.0f}万，不足部分{secured_shortfall:.0f}万转为普通债权"
        }

    # 第一顺位：职工债权
    if employee_claims > 0 and remaining > 0:
        if remaining >= employee_claims:
            results["职工债权（第一顺位）"] = {
                "claim": employee_claims,
                "distributed": employee_claims,
                "ratio": 100.0,
                "remaining_after": remaining - employee_claims
            }
            remaining -= employee_claims
        else:
            results["职工债权（第一顺位）"] = {
                "claim": employee_claims,
                "distributed": remaining,
                "ratio": round(remaining / employee_claims * 100, 2),
                "remaining_after": 0,
                "note": "⚠️ 资产不足以全额清偿职工债权"
            }
            remaining = 0

    # 第二顺位：税款债权
    if tax_claims > 0 and remaining > 0:
        if remaining >= tax_claims:
            results["税款债权（第二顺位）"] = {
                "claim": tax_claims,
                "distributed": tax_claims,
                "ratio": 100.0,
                "remaining_after": remaining - tax_claims
            }
            remaining -= tax_claims
        else:
            results["税款债权（第二顺位）"] = {
                "claim": tax_claims,
                "distributed": remaining,
                "ratio": round(remaining / tax_claims * 100, 2),
                "remaining_after": 0,
                "note": "⚠️ 资产不足以全额清偿税款债权"
            }
            remaining = 0

    # 第三顺位：普通债权（含担保不足转为普通的部分）
    total_ordinary = ordinary_claims
    if secured_claims_value > 0 and secured_assets_value > 0:
        secured_shortfall = max(0, secured_claims_value - secured_assets_value)
        total_ordinary += secured_shortfall

    if total_ordinary > 0 and remaining > 0:
        ordinary_ratio = round(remaining / total_ordinary * 100, 2)
        results["普通债权（第三顺位）"] = {
            "original_ordinary": ordinary_claims,
            "secured_shortfall": max(0, secured_claims_value - secured_assets_value) if secured_claims_value > 0 else 0,
            "total_ordinary": total_ordinary,
            "distributed": remaining,
            "ratio": ordinary_ratio,
            "remaining_after": 0
        }
        remaining = 0
    elif total_ordinary > 0:
        results["普通债权（第三顺位）"] = {
            "total_ordinary": total_ordinary,
            "distributed": 0,
            "ratio": 0,
            "remaining_after": 0,
            "note": "⚠️ 无可分配资产"
        }

    # 劣后债权
    if subordinate_claims > 0:
        if remaining > 0:
            results["劣后债权"] = {
                "claim": subordinate_claims,
                "distributed": remaining,
                "ratio": round(remaining / subordinate_claims * 100, 2),
            }
        else:
            results["劣后债权"] = {
                "claim": subordinate_claims,
                "distributed": 0,
                "ratio": 0,
                "note": "⚠️ 无可分配资产"
            }

    # 汇总
    total_claims = expenses_total + employee_claims + tax_claims + total_ordinary + subordinate_claims
    total_distributed = sum(
        r.get("distributed", 0) for r in results.values()
    )

    results["_summary"] = {
        "total_assets": total_assets,
        "total_claims": total_claims,
        "total_distributed": total_distributed,
        "overall_recovery_rate": round(total_distributed / total_claims * 100, 2) if total_claims > 0 else 0,
        "unsecured_debt_remaining": round(max(0, total_claims - total_distributed), 2)
    }

    return results


def display_table(results: Dict):
    summary = results.pop("_summary", {})

    print("\n" + "=" * 80)
    print(" 📊 破产分配测算结果")
    print("=" * 80)
    print(f"\n破产财产总额：{summary['total_assets']:>10,.0f} 万元")
    print(f"债权总额：    {summary['total_claims']:>10,.0f} 万元")
    print(f"分配总额：    {summary['total_distributed']:>10,.0f} 万元")
    print(f"综合清偿率：  {summary['overall_recovery_rate']:>7.2f}%")
    print(f"未受偿额：    {summary['unsecured_debt_remaining']:>10,.0f} 万元")
    print("-" * 80)

    for group_name, data in results.items():
        claim = data.get("claim", data.get("total_ordinary", 0))
        distributed = data.get("distributed", 0)
        ratio = data.get("ratio", 0)
        note = data.get("note", "")

        print(f"\n{group_name}")
        print(f"  债权金额：{claim:>10,.0f} 万元")
        print(f"  分配金额：{distributed:>10,.0f} 万元")
        print(f"  清偿率：  {ratio:>7.2f}%")
        if note:
            print(f"  ⚠️ {note}")

        # 有担保债权的不足部分转为普通
        shortfall = data.get("shortfall_as_ordinary", 0)
        if shortfall > 0:
            print(f"  不足部分转为普通债权：{shortfall:,.0f} 万元")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="破产分配测算工具")
    parser.add_argument("--total-assets", type=float, required=True,
                        help="破产财产总额（万元）")
    parser.add_argument("--bankruptcy-expenses", type=float, default=0,
                        help="破产费用（万元）")
    parser.add_argument("--common-benefit-debts", type=float, default=0,
                        help="共益债务（万元）")
    parser.add_argument("--employee-claims", type=float, default=0,
                        help="职工债权总额（万元）")
    parser.add_argument("--tax-claims", type=float, default=0,
                        help="税款债权总额（万元）")
    parser.add_argument("--ordinary-claims", type=float, default=0,
                        help="普通债权总额（万元）")
    parser.add_argument("--secured-claims-value", type=float, default=0,
                        help="有财产担保债权总额（万元）")
    parser.add_argument("--secured-assets-value", type=float, default=0,
                        help="担保物价值（万元）")
    parser.add_argument("--subordinate-claims", type=float, default=0,
                        help="劣后债权总额（万元）")
    parser.add_argument("--output", choices=["table", "json"], default="table",
                        help="输出格式")

    args = parser.parse_args()

    result = calc_distribution(
        total_assets=args.total_assets,
        bankruptcy_expenses=args.bankruptcy_expenses,
        common_benefit_debts=args.common_benefit_debts,
        employee_claims=args.employee_claims,
        tax_claims=args.tax_claims,
        ordinary_claims=args.ordinary_claims,
        secured_claims_value=args.secured_claims_value,
        secured_assets_value=args.secured_assets_value,
        subordinate_claims=args.subordinate_claims,
    )

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        display_table(result)


if __name__ == "__main__":
    main()
