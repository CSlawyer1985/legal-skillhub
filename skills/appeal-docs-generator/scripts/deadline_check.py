#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""上诉期限计算器 —— 二审第一个也是唯一一个不可逆的闸门。

法律依据
--------
- 民诉法第171条：不服一审判决，判决书送达之日起 15 日内上诉；不服一审裁定，裁定书送达
  之日起 10 日内上诉。
- 民诉法第85条：期间开始的时和日不计算在期间内；期间届满的最后一日是法定休假日的，以
  法定休假日后的第一日为期间届满的日期；期间不包括在途时间，诉讼文书在期满前交邮的，
  不算过期。

因此计算规则是：起算日 = 送达日 + 1 天；届满日 = 起算日 + N - 1 天；若届满日落在周末，
顺延至下一个工作日；法定节假日需另行核对（见下）。

⚠️ 法定节假日
------------
脚本只自动处理周六周日。**法定节假日（春节、国庆等）与调休安排必须人工核对**——
请以国务院办公厅当年发布的节假日安排通知为准，用 `--holidays 2026-10-01,2026-10-02`
传入后脚本会照样顺延。交付时必须提示律师复核这一项。

用法
----
    python3 deadline_check.py --served 2026-09-10 --type 判决
    python3 deadline_check.py --served 2026-09-10 --type 判决 --today 2026-09-16 --json

输出：届满日、剩余天数、风险等级（充足 / 紧张 / 紧急 / 已过）、缴费提示。
紧急模式（剩余 ≤3 天）时另打印处置建议。
"""

import argparse
import json
from datetime import date, datetime, timedelta

PERIOD = {"判决": 15, "裁定": 10}

RISK = [
    (None, "已过期", "❌ 上诉期已过，不得再上诉。请评估再审/申诉路径（本技能不生成再审文书）。"),
    (3, "紧急", "🚨 进入紧急模式：先出上诉状保期限，其余材料在期限内后补。"),
    (7, "紧张", "⚠️ 时间偏紧：先定上诉请求并落定上诉状，其余材料并行准备。"),
    (9999, "充足", "✅ 时间充足：按常规四道闸门推进。"),
]


def next_workday(d, holidays):
    while d.weekday() >= 5 or d.isoformat() in holidays:
        d += timedelta(days=1)
    return d


def compute(served, kind, today=None, holidays=()):
    served = datetime.strptime(served, "%Y-%m-%d").date()
    today = datetime.strptime(today, "%Y-%m-%d").date() if today else date.today()
    n = PERIOD[kind]

    start = served + timedelta(days=1)              # 期间开始的日不计入
    due = start + timedelta(days=n - 1)             # 第 n 日
    rolled = next_workday(due, set(holidays))       # 末日在休假日则顺延

    remain = (rolled - today).days
    level, advice = "充足", ""
    for th, lv, ad in RISK:
        if th is None:
            if remain < 0:
                level, advice = lv, ad
                break
        elif remain <= th:
            level, advice = lv, ad
            break

    return {
        "裁判类型": kind,
        "法定期间": f"{n} 日",
        "送达日": served.isoformat(),
        "起算日（送达次日）": start.isoformat(),
        "届满日": rolled.isoformat(),
        "是否顺延": rolled != due,
        "原始届满日": due.isoformat(),
        "计算基准日": today.isoformat(),
        "剩余天数": remain,
        "风险等级": level,
        "处置建议": advice,
        "缴费提示": "上诉案件受理费应在提交上诉状时预交；上诉期内未预交的，法院通知后 7 日内预交，逾期视为撤回上诉（诉讼费用交纳办法第22条第2款）。",
        "复核提示": "法定节假日与调休未自动识别，请以国务院办公厅当年节假日安排通知为准复核；期间不包括在途时间，文书在期满前交邮的不算过期（民诉法第85条）。",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--served", required=True, help="送达日期 YYYY-MM-DD")
    ap.add_argument("--type", default="判决", choices=["判决", "裁定"])
    ap.add_argument("--today", default=None, help="计算基准日 YYYY-MM-DD，默认今天")
    ap.add_argument("--holidays", default="", help="法定节假日，逗号分隔 YYYY-MM-DD")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    holidays = [h.strip() for h in a.holidays.split(",") if h.strip()]
    r = compute(a.served, a.type, a.today, holidays)

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    print(f"裁判类型：{r['裁判类型']}　法定期间：{r['法定期间']}")
    print(f"送达日：{r['送达日']}　起算日：{r['起算日（送达次日）']}")
    print(f"届满日：{r['届满日']}" + (f"（原 {r['原始届满日']}，因休假日顺延）" if r['是否顺延'] else ""))
    print(f"基准日：{r['计算基准日']}　剩余：{r['剩余天数']} 天　风险等级：{r['风险等级']}")
    print(f"\n▶ {r['处置建议']}")
    print(f"▶ {r['缴费提示']}")
    print(f"▶ {r['复核提示']}")


if __name__ == "__main__":
    main()
