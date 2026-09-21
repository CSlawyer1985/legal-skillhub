#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""二审上诉案件受理费测算器。

法律依据
--------
- 诉讼费用交纳办法第17条：对财产案件提起上诉的，按照不服一审判决部分的上诉请求数额交纳
  案件受理费。→ 所以本脚本的入参是"不服部分的金额"，不是全案金额，也不是一审判决金额。
- 诉讼费用交纳办法第13条：财产案件受理费按下列比例分段累计交纳——
    不超过 1 万元                每件 50 元
    超过 1 万至 10 万的部分      2.5%
    超过 10 万至 20 万的部分     2%
    超过 20 万至 50 万的部分     1.5%
    超过 50 万至 100 万的部分    1%
    超过 100 万至 200 万的部分   0.9%
    超过 200 万至 500 万的部分   0.8%
    超过 500 万至 1000 万的部分  0.7%
    超过 1000 万至 2000 万的部分 0.6%
    超过 2000 万的部分           0.5%
  非财产案件：离婚 50–300 元/件；人格权 100–500 元/件；其他非财产案件 50–100 元/件；
  劳动争议 10 元/件。
- 诉讼费用交纳办法第22条第2款：上诉案件受理费由上诉人向法院提交上诉状时预交；上诉期内
  未预交的，法院应当通知其在 7 日内预交（逾期视为撤回上诉）。
- 诉讼费用交纳办法第15条：以调解方式结案或者当事人申请撤诉的，减半交纳。
- 民诉法第173条：上诉状按对方当事人人数提出副本。

用法
----
    # 财产案件：不服部分金额 800,000 元
    python3 appeal_fee_calc.py --amount 800000
    # 多段不服金额（如对两项判项分别不服）
    python3 appeal_fee_calc.py --amount 300000 --amount 500000
    # 非财产案件
    python3 appeal_fee_calc.py --non-property 其他
    python3 appeal_fee_calc.py --non-property 劳动争议
    # 输出 JSON 供其它环节消费
    python3 appeal_fee_calc.py --amount 800000 --json

⚠️ 适用范围
----------
本脚本只算**案件受理费**。申请费（保全费等）、鉴定评估费不在其列。诉讼费用交纳办法第13条
第（二）(三)(六)项设有幅度区间，具体标准由省、自治区、直辖市人民政府制定，故非财产案件
只能给出区间，须由律师按受诉地标准核定。
"""

import argparse
import json

# （上限金额, 费率）
BRACKETS = [
    (10_000, None),          # 不超过 1 万：每件 50 元（单独处理）
    (100_000, 0.025),
    (200_000, 0.02),
    (500_000, 0.015),
    (1_000_000, 0.01),
    (2_000_000, 0.009),
    (5_000_000, 0.008),
    (10_000_000, 0.007),
    (20_000_000, 0.006),
    (float("inf"), 0.005),
]

NON_PROPERTY = {
    "离婚": ("50 元至 300 元/件（涉及财产分割的，财产总额不超过 20 万元不另行交纳，"
             "超过部分按 0.5% 交纳）"),
    "人格权": ("100 元至 500 元/件（涉及损害赔偿的，赔偿金额不超过 5 万元不另行交纳；"
               "超过 5 万至 10 万的部分按 1% 交纳；超过 10 万的部分按 0.5% 交纳）"),
    "知识产权": "无争议金额 500–1000 元/件；有争议金额按财产案件标准交纳",
    "劳动争议": "10 元/件",
    "其他": "50 元至 100 元/件",
}


def calc_property(amount):
    """财产案件受理费：分段累计。"""
    if amount <= 0:
        return 0.0
    if amount <= BRACKETS[0][0]:
        return 50.0
    fee = 50.0
    lower = BRACKETS[0][0]
    for upper, rate in BRACKETS[1:]:
        if amount <= lower:
            break
        seg = min(amount, upper) - lower
        fee += seg * rate
        lower = upper
    return fee


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", type=float, action="append", default=[],
                    help="不服一审判决部分的金额（元）。可多次传入，逐段计费后相加")
    ap.add_argument("--non-property", default=None,
                    choices=list(NON_PROPERTY.keys()), help="非财产案件类型")
    ap.add_argument("--counterparties", type=int, default=1, help="对方当事人人数（算副本份数）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    out = {"依据": "《诉讼费用交纳办法》第17条、第13条、第15条、第22条第2款", "明细": []}
    total = 0.0

    if a.non_property:
        out["类型"] = f"非财产案件（{a.non_property}）"
        out["区间说明"] = NON_PROPERTY[a.non_property]
        out["提示"] = "幅度区间内的具体标准由省级人民政府制定，请按受诉地标准核定。"
    elif a.amount:
        out["类型"] = "财产案件"
        for i, amt in enumerate(a.amount, 1):
            fee = calc_property(amt)
            total += fee
            out["明细"].append({"第": i, "不服部分金额": amt, "受理费": round(fee, 2)})
        out["合计受理费"] = round(total, 2)
        out["减半（调解结案或撤诉）"] = round(total / 2, 2)
    else:
        out["类型"] = "未指定"
        out["提示"] = "请用 --amount 传不服部分金额（财产案件），或用 --non-property 指定非财产案件类型。"

    out["副本份数"] = a.counterparties + 2
    out["副本依据"] = "民诉法第173条：上诉状按对方当事人或代表人的人数提出副本（我方1+对方N+法院1）"
    out["预交提示"] = "提交上诉状时预交；上诉期内未预交的，法院通知后 7 日内预交，逾期视为撤回上诉"

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"类型：{out['类型']}　（{out['依据']}）")
    for d in out.get("明细", []):
        print(f"  第{d['第']}项　不服 {d['不服部分金额']:,.2f} 元　→　受理费 {d['受理费']:,.2f} 元")
    if "合计受理费" in out:
        print(f"\n合计预交受理费：{out['合计受理费']:,.2f} 元")
        print(f"（如以调解方式结案或撤回上诉，减半交纳：{out['减半（调解结案或撤诉）']:,.2f} 元）")
    if "区间说明" in out:
        print(f"标准区间：{out['区间说明']}")
        print(f"⚠️ {out['提示']}")
    print(f"\n上诉状副本份数：{out['副本份数']} 份　（{out['副本依据']}）")
    print(f"▶ {out['预交提示']}")


if __name__ == "__main__":
    main()
