#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""期限计算脚本（limit_calculator.py）。

支持类型：detention（拘留）/ bail（取保候审）/ residence（监视居住）/
investigation（侦查羁押）/ prosecution（审查起诉）/ trial（审判）。
内置多次/流窜/结伙判断逻辑与节假日顺延计算（节假日数据读取
assets/data/holiday_calendar.json；在押人员期限不顺延规则内置）。

调用方式：
  python scripts/limit_calculator.py --type detention --start_date 2026-08-01 \
      --subtype general|extended|multiple_offense|gang \
      --offense_count 4 --locations 2 --accomplices_total 2

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}，data含期限类型、
    起止日期、剩余天数、法律依据、预警节点及对应动作建议、三类日期
    （法定届满日/机关实际动作日/律师预警日）与顺延/前移提示（shift_notices）；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败；
  - 错误码：ERR_ARGS_MISSING / ERR_DATE_INVALID / ERR_TYPE_INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta

SCRIPT_NAME = "limit_calculator"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "data")

# 期限规则（与references/limit_knowledge.md规则表一致；本表为脚本计算依据）
DETECTION_RULES = {
    "general": {"label": "一般情形3+7", "days": 10,
                "basis": "刑事诉讼法第91条〔2018年修正〕：一般案件拘留后三日以内提请批捕，特殊情况可延长一至四日；检察院接到提请后七日以内作出是否批捕的决定",
                "article": "第91条"},
    "extended": {"label": "特殊情况延长7+7", "days": 14,
                 "basis": "刑事诉讼法第91条〔2018年修正〕：拘留后三日内提请批捕，特殊情况可延长一至四日；检察院七日以内决定",
                 "article": "第91条"},
    "multiple_offense": {"label": "多次/流窜/结伙作案30+7", "days": 37,
                         "basis": "刑事诉讼法第91条〔2018年修正〕＋《公安机关办理刑事案件程序规定》第129条第3款：多次作案、流窜作案、结伙作案的重大嫌疑分子提请批捕可延长至三十日；检察院七日以内决定（黄金37天）",
                         "article": "第91条"},
    "gang": {"label": "结伙作案30+7", "days": 37,
             "basis": "刑事诉讼法第91条〔2018年修正〕＋《公安机关办理刑事案件程序规定》第129条第3款：结伙作案提请批捕可延长至三十日；检察院七日以内决定（黄金37天）",
             "article": "第91条"},
}

OTHER_RULES = {
    "bail": {"label": "取保候审最长十二个月", "months": 12, "in_custody": False,
             "basis": "刑事诉讼法第79条〔2018年修正〕：取保候审最长不得超过十二个月", "article": "第79条"},
    "residence": {"label": "监视居住最长六个月", "months": 6, "in_custody": False,
                  "basis": "刑事诉讼法第79条〔2018年修正〕：监视居住最长不得超过六个月（指定居所监视居住折抵刑期见第76条）", "article": "第79条"},
    "investigation": {"label": "逮捕后侦查羁押期限二个月", "months": 2, "in_custody": True,
                      "basis": "刑事诉讼法第156条〔2018年修正〕：逮捕后侦查羁押期限不得超过二个月；案情复杂的经上一级检察院批准可延长一个月（第158、159条另有延长）", "article": "第156条"},
    "prosecution": {"label": "审查起诉一个月", "months": 1, "in_custody": True,
                    "basis": "刑事诉讼法第172条〔2018年修正〕：一个月以内作出决定，重大复杂的可延长十五日；速裁程序十日以内（可延至十五日）；退查规则见第175条", "article": "第172条"},
    "trial": {"label": "一审审限二个月（至迟三个月）", "months": 3, "in_custody": True,
              "basis": "刑事诉讼法第208条〔2018年修正〕：一审公诉案件二个月以内宣判、至迟不得超过三个月；可能判处死刑、附带民事诉讼及第158条情形可延长三个月", "article": "第208条"},
}

DETENTION_WARNINGS = [
    {"day": 5, "node": "第5日", "action": "一般案件提请批捕起点：确认是否已提捕"},
    {"day": 12, "node": "第12日", "action": "特殊情况延长后提请批捕截止：核对是否已报捕"},
    {"day": 27, "node": "第27日", "action": "多次/流窜/结伙案件提请批捕前3日：提交取保候审申请书（最后窗口）＋报捕前会见"},
    {"day": 33, "node": "第33日", "action": "30日延长案件提请批捕截止：核对是否已报捕"},
]


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_holidays():
    data = load_json(os.path.join(DATA_DIR, "holiday_calendar.json"))
    if not data:
        return {}, [], set()
    holidays, workdays = set(), set()
    covered_years = set()
    for year_key, arr in (data.get("years") or {}).items():
        try:
            covered_years.add(int(year_key))
        except (TypeError, ValueError):
            pass
        for item in arr:
            try:
                start = datetime.strptime(item["start"], "%Y-%m-%d").date()
                end = datetime.strptime(item["end"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            d = start
            while d <= end:
                holidays.add(d)
                d += timedelta(days=1)
            for wd in item.get("workdays", []):
                try:
                    workdays.add(datetime.strptime(wd, "%Y-%m-%d").date())
                except ValueError:
                    pass
    return holidays, workdays, covered_years


def is_rest_day(d, holidays, workdays):
    if d in workdays:
        return False
    if d in holidays:
        return True
    return d.weekday() >= 5


def next_workday(d, holidays, workdays):
    while is_rest_day(d, holidays, workdays):
        d += timedelta(days=1)
    return d


def prev_workday(d, holidays, workdays):
    d -= timedelta(days=1)
    while is_rest_day(d, holidays, workdays):
        d -= timedelta(days=1)
    return d


def add_months(start, months):
    """日历月计算（期限以月计算）。"""
    y, m = start.year, start.month + months
    while m > 12:
        m -= 12
        y += 1
    day = min(start.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def detect_subtype(args):
    """多次/流窜/结伙判断（《公安机关办理刑事案件程序规定》第129条第3款）。
    显式--subtype优先于自动判断；未提供subtype时按作案次数/地点/人数自动判断，
    案情参数提示的多次/流窜/结伙情形仍如实返回（供输出提示）。"""
    reasons = []
    if args.offense_count is not None and args.offense_count >= 3:
        reasons.append("多次作案（作案次数≥3）")
    if args.locations is not None and args.locations >= 2:
        reasons.append("流窜作案（跨市县连续作案）")
    if args.accomplices_total is not None and args.accomplices_total >= 2:
        reasons.append("结伙作案（共同作案总人数≥2，含本人）")
    if args.subtype:
        return args.subtype, reasons
    if reasons:
        return "multiple_offense", reasons
    return "general", reasons


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="刑事期限计算：detention/bail/residence/investigation/prosecution/trial六类型；"
                    "内置多次/流窜/结伙判断与节假日顺延（在押人员期限一律不顺延）。")
    parser.add_argument("--type", required=True,
                        choices=["detention", "bail", "residence", "investigation",
                                 "prosecution", "trial"],
                        help="期限类型")
    parser.add_argument("--start_date", required=True, help="起始日期（YYYY-MM-DD）")
    parser.add_argument("--subtype", choices=["general", "extended", "multiple_offense", "gang"],
                        help="拘留期限子类型（detention适用；缺省时按作案次数/地点/人数自动判断）")
    parser.add_argument("--offense_count", type=int, help="作案次数（≥3触发多次作案）")
    parser.add_argument("--locations", type=int, help="跨市县数（≥2触发流窜作案）")
    parser.add_argument("--accomplices_total", type=int, help="共同作案总人数含本人（≥2触发结伙作案）")
    parser.add_argument("--alert_lead", type=int, default=3,
                        help="律师预警日在机关实际动作日前前推的自然日数（默认3）")
    args = parser.parse_args()
    trace_id = make_trace_id()

    try:
        start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    except ValueError:
        print(json.dumps(envelope("error", "ERR_DATE_INVALID",
                                  "日期格式非法：%s（须YYYY-MM-DD）" % args.start_date, None),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    holidays, workdays, covered_years = load_holidays()
    holiday_note = ("节假日数据未配置或缺失，本次计算未适用节假日顺延【待核实：请补充assets/data/holiday_calendar.json】"
                    if not holidays else "节假日数据源：assets/data/holiday_calendar.json")

    if args.type == "detention":
        subtype, trigger_reasons = detect_subtype(args)
        rule = DETECTION_RULES[subtype]
        # 期间开始的日不算在期间以内（刑诉法第105条）：第N日＝start＋N天
        end = start + timedelta(days=rule["days"])
        natural_end = end
        in_custody = True
        postpone_note = "在押人员期限一律计算至期满之日为止，不顺延（刑诉法第105条）"
    else:
        rule = OTHER_RULES[args.type]
        subtype = None
        trigger_reasons = []
        end = add_months(start, rule["months"])
        natural_end = end
        in_custody = rule["in_custody"]
        if in_custody:
            postpone_note = "在押人员期限一律计算至期满之日为止，不顺延（刑诉法第105条）"
        else:
            postpone_note = "期限届满日为法定节假日的，顺延至节假日后的第一个工作日（刑诉法第105条）"
            if holidays and end.year not in covered_years:
                postpone_note += ("；注意：节假日数据未覆盖%d年，该年度顺延仅按周末判断"
                                  "【待核实：请更新assets/data/holiday_calendar.json】" % end.year)
            adjusted = next_workday(end, holidays, workdays)
            if adjusted != end:
                postpone_note += "；本次届满日%s逢休息日，已顺延至%s" % (end.isoformat(), adjusted.isoformat())
                end = adjusted

    # 三类日期与顺延/前移提示（大纲 5.3 第 1 项双轨口径）
    shift_notices = []
    if in_custody:
        # 法定届满日＝自然日连续计算至期满之日（不顺延）
        legal_expiry = natural_end
        # 机关实际动作日：届满日落在休息日的，按节前最后一个工作日
        if is_rest_day(natural_end, holidays, workdays):
            authority_action_day = prev_workday(natural_end, holidays, workdays)
            shift_notices.append({
                "kind": "前移", "original_day": natural_end.isoformat(),
                "adjusted_day": authority_action_day.isoformat(),
                "reason": "法定届满日%s逢休息日，机关须在此前最后一个工作日完成动作" % natural_end.isoformat()})
        else:
            authority_action_day = natural_end
        # 律师预警日：在机关实际动作日前前推，遇休息日再前移
        lawyer_alert_day = authority_action_day - timedelta(days=args.alert_lead)
        while is_rest_day(lawyer_alert_day, holidays, workdays):
            lawyer_alert_day -= timedelta(days=1)
    else:
        # 一般期间轨：最后一日为节假日的顺延至节后第一个工作日，顺延后为法定届满日；无机关动作日概念
        legal_expiry = end
        authority_action_day = end
        if end != natural_end:
            shift_notices.append({
                "kind": "顺延", "original_day": natural_end.isoformat(),
                "adjusted_day": end.isoformat(),
                "reason": "届满日逢休息日，顺延至节假日后的第一个工作日"})
        lawyer_alert_day = end - timedelta(days=args.alert_lead)
        while is_rest_day(lawyer_alert_day, holidays, workdays):
            lawyer_alert_day -= timedelta(days=1)

    # 预警节点（在押期限节点不顺延；超出本案期限类型的节点不输出，如10日/14日案件不含第27/33日节点）
    warnings = []
    if args.type == "detention":
        for w in DETENTION_WARNINGS:
            if w["day"] > rule["days"]:
                continue
            d = start + timedelta(days=w["day"])
            if d >= date.today():
                warnings.append({"date": d.isoformat(), "node": w["node"],
                                 "action": w["action"], "status": "待执行"})
    else:
        warn_date = end - timedelta(days=7)
        if warn_date < date.today():
            warn_date = date.today()
        warnings.append({"date": warn_date.isoformat(), "node": "届满前7日",
                         "action": "强制措施期限届满前7日：依刑诉法第117条第1款第1项预备申诉控告",
                         "status": "待执行"})

    days_remaining = (end - date.today()).days

    data = {
        "trace_id": trace_id,
        "type": args.type,
        "subtype": subtype,
        "label": rule["label"],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days_remaining": days_remaining,
        "in_custody": in_custody,
        "holiday_postpone_rule": postpone_note,
        "three_dates": {
            "legal_expiry": natural_end.isoformat(),
            "authority_action_day": authority_action_day.isoformat(),
            "lawyer_alert_day": lawyer_alert_day.isoformat(),
        },
        "shift_notices": shift_notices,
        "legal_basis": {"name": "中华人民共和国刑事诉讼法", "article": rule["article"],
                        "basis": rule["basis"], "amendment": "2018年修正",
                        "status": "现行有效"},
        "warnings": warnings,
        "notes": [holiday_note],
    }
    if args.type == "detention":
        data["trigger_reasons"] = trigger_reasons or ["无多次/流窜/结伙情形"]
        # subtype来源说明：消除"显式指定30+7而trigger_reasons显示无情形"的表面矛盾
        data["subtype_source"] = ("显式指定（--subtype=%s，期限类型以该参数为准）" % args.subtype
                                  if args.subtype else "按作案次数/跨市县数/同案人数自动判断（未传--subtype）")
        if args.subtype in ("multiple_offense", "gang") and not trigger_reasons:
            data["notes"].append("已按显式--subtype=%s计算；trigger_reasons显示\"无\"仅指未提供作案次数／跨市县数／同案人数参数供自动判断，并非否定多次/流窜/结伙情形，请核实事实依据后引用" % args.subtype)
        data["notes"].append("预警节点系实务惯例提前预警（经验值，非刑诉法第91条法定期限）；法定期限以legal_basis与本输出end_date为准（检察院决定截止：一般十日／延长后十四日／30日案件三十七日），对外文书引用法定期限")
        if trigger_reasons and args.subtype and args.subtype not in ("multiple_offense", "gang"):
            data["notes"].append("已按显式--subtype=%s计算；注意：案情参数提示%s，或适用30+7（37日），请核实"
                                 % (args.subtype, "、".join(trigger_reasons)))
        if not trigger_reasons and args.subtype is None:
            data["notes"].append("作案次数/地点/同案人数未提供完全时，30+7可能适用【待核实：请补充作案次数、是否跨市县、共同作案人数】")
    print(json.dumps(envelope("ok", None, "计算成功", data), ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
