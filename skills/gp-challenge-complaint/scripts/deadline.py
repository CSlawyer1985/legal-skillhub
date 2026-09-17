#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""政府采购工作日日历。只计算确认的触发日期。"""

import argparse
import datetime as dt
import sys

# ---------------------------------------------------------------------------
# 法定节假日与调休安排
#   holidays  : 放假的日期（含调休放假）
#   workdays  : 因调休而需要上班的周末
# 数据来源：国务院办公厅关于部分节假日安排的通知
# ---------------------------------------------------------------------------

HOLIDAY_DATA = {
    2025: {
        # 国办发明电〔2024〕7号
        "holidays": [
            "2025-01-01",
            # 春节 1/28(除夕)-2/4
            "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
            "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04",
            # 清明 4/4-4/6
            "2025-04-04", "2025-04-05", "2025-04-06",
            # 劳动节 5/1-5/5
            "2025-05-01", "2025-05-02", "2025-05-03", "2025-05-04", "2025-05-05",
            # 端午 5/31-6/2
            "2025-05-31", "2025-06-01", "2025-06-02",
            # 国庆中秋 10/1-10/8
            "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-04",
            "2025-10-05", "2025-10-06", "2025-10-07", "2025-10-08",
        ],
        "workdays": [
            "2025-01-26", "2025-02-08",   # 春节调休
            "2025-04-27",                 # 劳动节调休
            "2025-09-28", "2025-10-11",   # 国庆调休
        ],
    },
    2026: {
        # 国办发明电〔2025〕7号
        "holidays": [
            # 元旦 1/1-1/3
            "2026-01-01", "2026-01-02", "2026-01-03",
            # 春节 2/15(腊月廿八)-2/23(正月初七)
            "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19",
            "2026-02-20", "2026-02-21", "2026-02-22", "2026-02-23",
            # 清明 4/4-4/6（不调休）
            "2026-04-04", "2026-04-05", "2026-04-06",
            # 劳动节 5/1-5/5
            "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05",
            # 端午 6/19-6/21（不调休）
            "2026-06-19", "2026-06-20", "2026-06-21",
            # 中秋 9/25-9/27（不调休）
            "2026-09-25", "2026-09-26", "2026-09-27",
            # 国庆 10/1-10/7
            "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",
            "2026-10-05", "2026-10-06", "2026-10-07",
        ],
        "workdays": [
            "2026-01-04",                 # 元旦调休
            "2026-02-14", "2026-02-28",   # 春节调休
            "2026-05-09",                 # 劳动节调休
            "2026-09-20", "2026-10-10",   # 国庆调休
        ],
    },
}

HOLIDAYS = set()
EXTRA_WORKDAYS = set()
COVERED_YEARS = set()
for _y, _d in HOLIDAY_DATA.items():
    COVERED_YEARS.add(_y)
    HOLIDAYS.update(dt.date.fromisoformat(x) for x in _d["holidays"])
    EXTRA_WORKDAYS.update(dt.date.fromisoformat(x) for x in _d["workdays"])


def ensure_covered(d: dt.date):
    if d.year not in COVERED_YEARS:
        sys.exit(
            f"错误：{d.year} 年的法定节假日安排尚未收录，无法准确计算工作日。\n"
            f"当前已收录年份：{sorted(COVERED_YEARS)}\n"
            f"请查询《国务院办公厅关于 {d.year} 年部分节假日安排的通知》"
            f"（gov.cn 或中国政府网发布），补充到本脚本的 HOLIDAY_DATA 后重试。\n"
            f"法定期限不容许估算，脚本拒绝按周末近似推算。"
        )


def is_workday(d: dt.date) -> bool:
    ensure_covered(d)
    if d in EXTRA_WORKDAYS:
        return True
    if d in HOLIDAYS:
        return False
    return d.weekday() < 5


def day_label(d: dt.date) -> str:
    wk = "一二三四五六日"[d.weekday()]
    if d in EXTRA_WORKDAYS:
        note = "（调休上班）"
    elif d in HOLIDAYS:
        note = "（法定假日）"
    elif d.weekday() >= 5:
        note = "（休息日）"
    else:
        note = ""
    return f"{d.isoformat()} 周{wk}{note}"


def add_workdays(start: dt.date, n: int):
    """自 start 的次日起算，返回第 n 个工作日（即期限届满日）及经过的日历天数。"""
    ensure_covered(start)
    d = start
    count = 0
    guard = 0
    while count < n:
        d += dt.timedelta(days=1)
        guard += 1
        if guard > 400:
            sys.exit("错误：计算超出 400 天，请检查输入。")
        ensure_covered(d)
        if is_workday(d):
            count += 1
    return d, (d - start).days


def countdown(deadline: dt.date, today: dt.date = None):
    today = today or dt.date.today()
    cal = (deadline - today).days
    if cal < 0:
        return f"已超期 {-cal} 个日历日"
    # 剩余工作日
    d, n = today, 0
    while d < deadline:
        d += dt.timedelta(days=1)
        if d.year in COVERED_YEARS and is_workday(d):
            n += 1
    return f"剩余 {cal} 个日历日 / 约 {n} 个工作日"


def cmd_from(start: dt.date, days: int):
    end, cal = add_workdays(start, days)
    print(f"\n起算日：{day_label(start)}（当日不计入，自次日起算）")
    print(f"期限：{days} 个工作日")
    print(f"届满日：{day_label(end)}")
    print(f"跨越 {cal} 个日历日")
    print(f"倒计时：{countdown(end)}")
    print("\n逐日明细：")
    d, c = start, 0
    while d < end:
        d += dt.timedelta(days=1)
        if is_workday(d):
            c += 1
            print(f"  第 {c:>2} 个工作日  {day_label(d)}")
        else:
            print(f"  {'':>13} {day_label(d)}")



def main():
    import json
    from pathlib import Path
    config = json.loads((Path(__file__).resolve().parents[1] / "region.json").read_text(encoding="utf-8"))
    p = argparse.ArgumentParser(description="按真实触发事件计算，不猜测送达或受理日期")
    p.add_argument("--jurisdiction", default="zhejiang")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--event", choices=["challenge", "reply", "complaint", "review", "decision"])
    p.add_argument("--from", dest="start")
    p.add_argument("--check")
    a = p.parse_args()
    if a.jurisdiction not in config["allowed"]:
        p.error("本包不支持该地区")
    if a.jurisdiction == "shenzhen" and not a.demo:
        p.error("深圳仅支持演示，需同时提供 --demo")
    try:
        if a.check:
            d = dt.date.fromisoformat(a.check)
            print(f"{day_label(d)}：{'工作日' if is_workday(d) else '非工作日'}")
            return
        if not a.event or not a.start:
            p.error("必须提供 --event 和 --from，日期必须是该事件已核实的触发日期")
        sz = a.jurisdiction == "shenzhen"
        rules = {
          "challenge": (7, "知道或应知权益受损日", "深圳条例第41条、实施细则第61条" if sz else "政府采购法第52条、实施条例第53条"),
          "reply": (7, "被质疑人实际收到书面质疑日", "深圳条例第41条" if sz else "政府采购法第53条、94号令第13条"),
          "complaint": (15, "法定答复期届满日", "深圳条例第42条" if sz else "政府采购法第55条、94号令第17条"),
          "review": (5, "主管部门实际收到投诉日", "深圳条例第43条" if sz else "94号令第21条"),
          "decision": (30, "实际受理投诉日" if sz else "实际收到投诉日", "深圳条例第44条" if sz else "政府采购法第56条、94号令第26条")
        }
        n, trigger, basis = rules[a.event]
        start = dt.date.fromisoformat(a.start)
        end, _ = add_workdays(start, n)
        print(json.dumps({"地区": a.jurisdiction, "模式": "虚构演示" if a.demo else "案件辅助",
          "事件": a.event, "触发事件": trigger, "触发日": str(start), "工作日数": n,
          "截止日": str(end), "依据": basis,
          "假设": "起算当日不计；未计依法扣除、补正等特殊期间；送达及窗口时间另核",
          "提示": "不判断起算事实；提交日不等于收到日，审查截止日不等于受理日"},
          ensure_ascii=False, indent=2))
        if sz:
            print("深圳应知日：文件公布日；程序环节结束日；结果公示日。适用冲突应列示复核。")
    except ValueError as exc:
        p.error(str(exc))

if __name__ == "__main__":
    main()
