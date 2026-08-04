#!/usr/bin/env python3
"""
财富传承方案测算工具
—— 继承/赠与/信托三方案对比测算
输出：方案对比表 + 税务成本汇总 + 费用估算

用法：python wealth_calculator.py  --asset-type 不动产 --asset-value 1000 --asset-cost 300
"""
import argparse
import json
import sys
from typing import Dict, List, Tuple

# ---------- 配置参数 ----------

# 契税税率（不动产，各地差异）
DEED_TAX_RATE = {
    "first_house": 0.015,  # 首套房
    "second_house": 0.02,  # 二套房
    "third_plus": 0.03,    # 三套及以上/非住宅
}

# 个税税率表（财产转让）
INDIVIDUAL_TAX_RATE = 0.20  # 20%

# 增值税相关
VAT_RATE = 0.056  # 5.6%（不满2年）
VAT_EXEMPT_AFTER_YEARS = 2  # 满2年免征

# 信托费用估算
TRUST_SETUP_FEE_RATE = 0.01  # 设立费≈资产1%
TRUST_ANNUAL_FEE_RATE = 0.005  # 年管理费≈0.5%

# 保险金信托佣金参考（保费vs保额）
INSURANCE_LEVERAGE = 4  # 寿险杠杆率（1保费→4保额）


def calc_inheritance_tax(asset_value: float, deed_tax_rate: float) -> Dict:
    """方案一：法定继承税务成本测算"""
    deed_tax = round(asset_value * deed_tax_rate, 2)
    # 注：当前中国无遗产税，若有遗产税草案测算可在此加入
    return {
        "scheme": "法定继承",
        "deed_tax": deed_tax,
        "individual_tax": 0,
        "vat": 0,
        "other_fees": round(asset_value * 0.001, 2),  # 公证费约0.1%
        "total_tax": round(deed_tax + asset_value * 0.001, 2),
        "total_rate": round((deed_tax + asset_value * 0.001) / asset_value * 100, 2),
        "note": "无遗产税（现行法）；继承公证程序繁琐"
    }


def calc_gift_tax(asset_value: float, asset_cost: float,
                  deed_tax_rate: float, is_direct_line: bool = True) -> Dict:
    """方案二：赠与税务成本测算"""
    deed_tax = round(asset_value * deed_tax_rate, 2)

    # 直系亲属赠与免个税（部分城市）/非直系20%
    if is_direct_line:
        individual_tax = 0
        note = "直系亲属赠与免个税（大部分地区）"
    else:
        gain = asset_value - asset_cost
        individual_tax = round(max(0, gain) * INDIVIDUAL_TAX_RATE, 2)
        note = f"非直系亲属赠与个税20%（按差额）"

    total = round(deed_tax + individual_tax, 2)
    return {
        "scheme": "赠与",
        "deed_tax": deed_tax,
        "individual_tax": individual_tax,
        "vat": 0,
        "other_fees": round(asset_value * 0.005, 2),  # 评估费+公证≈0.5%
        "total_tax": round(total + asset_value * 0.005, 2),
        "total_rate": round((total + asset_value * 0.005) / asset_value * 100, 2),
        "note": note
    }


def calc_sale_tax(asset_value: float, asset_cost: float,
                  deed_tax_rate: float, hold_years: int = 3) -> Dict:
    """方案三：买卖过户税务成本测算"""
    deed_tax = round(asset_value * deed_tax_rate, 2)
    gain = max(0, asset_value - asset_cost)

    # 增值税（满2年免征）
    vat = 0
    if hold_years < VAT_EXEMPT_AFTER_YEARS:
        vat = round(asset_value * VAT_RATE, 2)

    # 个税（满五唯一免征，否则1%或差额20%，取较小者）
    individual_tax = round(min(gain * 0.20, asset_value * 0.01), 2)

    total = round(deed_tax + vat + individual_tax, 2)
    return {
        "scheme": "买卖过户",
        "deed_tax": deed_tax,
        "individual_tax": individual_tax,
        "vat": vat,
        "other_fees": round(asset_value * 0.005, 2),  # 中介+评估≈0.5%
        "total_tax": round(total + asset_value * 0.005, 2),
        "total_rate": round((total + asset_value * 0.005) / asset_value * 100, 2),
        "note": "满五唯一可免征个税；满2年免增值税"
    }


def calc_trust_tax(asset_value: float, deed_tax_rate: float) -> Dict:
    """方案四：信托架构税务成本（不动产为示例）"""
    deed_tax = round(asset_value * deed_tax_rate, 2)
    setup_fee = round(asset_value * TRUST_SETUP_FEE_RATE, 2)
    annual_fee = round(asset_value * TRUST_ANNUAL_FEE_RATE, 2)

    total_initial = round(deed_tax + setup_fee, 2)
    return {
        "scheme": "家族信托持有",
        "deed_tax": deed_tax,
        "individual_tax": 0,
        "vat": 0,
        "setup_fee": setup_fee,
        "annual_fee": annual_fee,
        "total_initial": total_initial,
        "total_rate": round(total_initial / asset_value * 100, 2),
        "note": "设立时税费较高但长期隔离保护最强；年管理费约0.5%"
    }


def calc_insurance_trust(premium: float) -> Dict:
    """保险金信托成本测算"""
    coverage = round(premium * INSURANCE_LEVERAGE, 2)
    setup_fee = round(min(max(coverage * 0.01, 30000), 80000), 2)
    annual_fee = round(coverage * 0.003, 2)

    return {
        "scheme": "保险金信托",
        "premium": premium,
        "coverage": coverage,
        "leverage": f"1:{INSURANCE_LEVERAGE}",
        "setup_fee": setup_fee,
        "annual_fee": annual_fee,
        "note": f"保费{premium/10000:.0f}万→保额{coverage/10000:.0f}万；杠杆{INSURANCE_LEVERAGE}倍"
    }


def display_comparison_table(results: List[Dict]):
    """输出方案对比表"""
    print("\n" + "=" * 80)
    print(" 📊 财富传承方案税务成本对比表")
    print("=" * 80)

    if "total_tax" in results[0]:
        print(f"\n{'方案':<16} {'契税':>10} {'个税':>10} {'增值税':>10} {'其他':>10} {'合计':>12} {'税率%':>8} {'说明'}")
        print("-" * 80)
        for r in results:
            print(f"{r['scheme']:<16} {r.get('deed_tax',0):>10,.0f} {r.get('individual_tax',0):>10,.0f} "
                  f"{r.get('vat',0):>10,.0f} {r.get('other_fees',0):>10,.0f} {r.get('total_tax',0):>12,.0f} "
                  f"{r.get('total_rate',0):>7.1f}% {r['note']}")
    elif "total_initial" in results[0]:
        print(f"\n{'方案':<16} {'契税':>10} {'设立费':>10} {'首年合计':>12} {'年管理费':>12} {'说明'}")
        print("-" * 80)
        r = results[0]
        print(f"{r['scheme']:<16} {r.get('deed_tax',0):>10,.0f} {r.get('setup_fee',0):>10,.0f} "
              f"{r.get('total_initial',0):>12,.0f} {r.get('annual_fee',0):>12,.0f} {r['note']}")
    elif "coverage" in results[0]:
        r = results[0]
        print(f"\n保险金信托测算：")
        print(f"  • 年缴保费：{r['premium']/10000:.0f}万元")
        print(f"  • 身故保额：{r['coverage']/10000:.0f}万元（杠杆{r['leverage']}）")
        print(f"  • 信托设立费：{r['setup_fee']/10000:.2f}万元")
        print(f"  • 年管理费：{r['annual_fee']/10000:.2f}万元")
        print(f"  • {r['note']}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="财富传承方案测算工具")
    parser.add_argument("--asset-type", default="不动产",
                        choices=["不动产", "股权", "金融资产", "保险"],
                        help="资产类型")
    parser.add_argument("--asset-value", type=float, required=True,
                        help="资产当前估值（万元）")
    parser.add_argument("--asset-cost", type=float, default=0,
                        help="资产原始取得成本（万元）")
    parser.add_argument("--hold-years", type=int, default=3,
                        help="持有年限（不动产买卖计算增值税用）")
    parser.add_argument("--is-direct-line", action="store_true", default=True,
                        help="是否为直系亲属赠予")
    parser.add_argument("--house-type", default="second_house",
                        choices=["first_house", "second_house", "third_plus"],
                        help="房屋类型（契税税率）")
    parser.add_argument("--premium", type=float, default=0,
                        help="保险年缴保费（万元，测算保险金信托用）")
    parser.add_argument("--output", choices=["table", "json"], default="table",
                        help="输出格式")

    args = parser.parse_args()

    deed_rate = DEED_TAX_RATE.get(args.house_type, 0.03)

    if args.asset_type == "不动产":
        inheritance = calc_inheritance_tax(args.asset_value, deed_rate)
        gift = calc_gift_tax(args.asset_value, args.asset_cost, deed_rate,
                             args.is_direct_line)
        sale = calc_sale_tax(args.asset_value, args.asset_cost, deed_rate,
                             args.hold_years)
        trust = calc_trust_tax(args.asset_value, deed_rate)

        if args.output == "table":
            display_comparison_table([inheritance, gift, sale, trust])
        else:
            print(json.dumps({
                "asset_type": args.asset_type,
                "asset_value": args.asset_value,
                "schemes": [inheritance, gift, sale, trust]
            }, ensure_ascii=False, indent=2))

    elif args.asset_type == "保险":
        if args.premium <= 0:
            print("请使用 --premium 指定年缴保费（万元）")
            sys.exit(1)
        result = calc_insurance_trust(args.premium)
        display_comparison_table([result])

    else:
        print(f"暂不支持「{args.asset_type}」类型测算（开发中）")
        sys.exit(1)


if __name__ == "__main__":
    main()
