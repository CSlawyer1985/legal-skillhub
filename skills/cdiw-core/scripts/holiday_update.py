#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节假日日历年度更新脚本（holiday_update.py）。

数据源说明：国务院办公厅每年约11月发布下一年度部分节假日安排通知，
本Skill不联网抓取，由维护者按通知原文录入（update_rule见
assets/data/holiday_calendar.json）。本脚本提供三项辅助：

  1. --check               覆盖状态检查（当年必须齐备；下一年度自当年10月起要求）；
  2. --template 年度        输出该年度的录入模板（七个法定节假日骨架，供按通知填写）；
  3. --add-year 年度 --holidays '[...]'  录入新年度数据（JSON数组），
     自动校验字段齐备、日期格式、起止逻辑后写入并更新_updated_at。

调用方式：
  python scripts/holiday_update.py --check
  python scripts/holiday_update.py --template 2027
  python scripts/holiday_update.py --add-year 2027 --holidays '[{"festival":"元旦","start":"2027-01-01","end":"2027-01-03","workdays":["2027-01-02"]}]'

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3校验失败；
  - 录入完成后须在CHANGELOG.md记入更新条目（脚本输出中提示）。
"""

import argparse
import json
import os
import sys
from datetime import date, datetime

SCRIPT_NAME = "holiday_update"
CAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "data", "holiday_calendar.json")

FESTIVALS = ["元旦", "春节", "清明节", "劳动节", "端午节", "中秋节", "国庆节"]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code, "message": message, "data": data}


def fail(error_code, message, code=3):
    print(json.dumps(envelope("error", error_code, message, None),
                     ensure_ascii=False, indent=2))
    sys.exit(code)


def load_calendar():
    if not os.path.exists(CAL_PATH):
        fail("ERR_IO", "holiday_calendar.json不存在：%s" % CAL_PATH, 2)
    try:
        with open(CAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        fail("ERR_IO", "holiday_calendar.json解析失败：%s" % exc, 2)


def valid_date(s, year):
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
    if d.year != year:
        return None
    return d


def check(data):
    years = set(data.get("years", {}).keys())
    today = date.today()
    problems, warnings = [], []
    if str(today.year) not in years:
        problems.append("缺少%d年度数据——当年期限顺延计算将降级，请立即录入" % today.year)
    elif str(today.year + 1) not in years:
        if today.month >= 10:
            problems.append("缺少%d年度数据（国务院通知已发布窗口期），请录入" % (today.year + 1))
        else:
            warnings.append("%d年度数据尚未录入（正常：国务院通知通常%d年11月发布，届时录入）"
                            % (today.year + 1, today.year))
    return {"已覆盖年度": sorted(years),
            "问题": problems or None,
            "提示": warnings or None,
            "更新规则": data.get("update_rule")}


def make_template(year):
    skeleton = []
    for i, f in enumerate(FESTIVALS, 1):
        skeleton.append({"festival": f,
                         "start": "%d-XX-XX" % year if i > 1 else "%d-01-01" % year,
                         "end": "%d-XX-XX" % year,
                         "workdays": []})
    return {"festival": "按国务院办公厅《关于%d年部分节假日安排的通知》逐项填写："
                       "festival节日名、start放假首日、end放假末日（YYYY-MM-DD）、"
                       "workdays调休上班日列表（无调休填空数组）" % year,
            "entries": skeleton,
            "提醒": "除夕是否纳入春节假期、调休上班日务必录入——期限顺延判断依赖workdays"}


def add_year(data, year, holidays):
    problems = []
    seen = set()
    for i, item in enumerate(holidays, 1):
        fest = item.get("festival")
        if not fest:
            problems.append("第%d条缺festival" % i)
            continue
        if fest in seen:
            problems.append("节日%s重复录入" % fest)
        seen.add(fest)
        ds = valid_date(item.get("start"), year)
        de = valid_date(item.get("end"), year)
        if ds is None:
            problems.append("%s：start缺失或非%d年合法日期（YYYY-MM-DD）" % (fest, year))
        if de is None:
            problems.append("%s：end缺失或非%d年合法日期" % (fest, year))
        if ds and de and ds > de:
            problems.append("%s：start晚于end" % fest)
        for w in item.get("workdays", []):
            if valid_date(w, year) is None:
                problems.append("%s：调休上班日%s非%d年合法日期" % (fest, w, year))
    if problems:
        fail("ERR_ARGS_MISSING", "录入数据校验未通过（未写入）：%s" % "；".join(problems), 1)
    data.setdefault("years", {})[str(year)] = holidays
    data["_updated_at"] = date.today().isoformat()
    try:
        with open(CAL_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        fail("ERR_IO", "写入失败：%s" % exc, 2)
    return {"已录入年度": year,
            "节日数": len(holidays),
            "写入路径": os.path.relpath(CAL_PATH),
            "后续动作": ["在CHANGELOG.md记入：节假日日历新增%d年度数据（来源：国务院办公厅通知文号）" % year,
                         "运行python scripts/self_check.py确认日历覆盖检查通过"]}


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="节假日日历年度更新：--check覆盖检查／--template模板生成／--add-year录入。",
        epilog=("调用示例：\n"
                "  python scripts/holiday_update.py --check\n"
                "  python scripts/holiday_update.py --template 2027\n"
                "  python scripts/holiday_update.py --add-year 2027 --holidays "
                "'[{\"festival\":\"元旦\",\"start\":\"2027-01-01\",\"end\":\"2027-01-03\","
                "\"workdays\":[\"2027-01-02\"]}]'\n\n"
                "数据源：国务院办公厅《关于XXXX年部分节假日安排的通知》（每年约11月发布）；"
                "录入后须在CHANGELOG.md记入条目。"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="覆盖状态检查")
    parser.add_argument("--template", type=int, metavar="年度", help="输出该年度录入模板")
    parser.add_argument("--add-year", type=int, metavar="年度", help="录入新年度数据")
    parser.add_argument("--holidays", help="年度数据JSON数组（与--add-year配合）")
    args = parser.parse_args()

    if not (args.check or args.template or args.add_year):
        fail("ERR_ARGS_MISSING", "--check、--template、--add-year至少提供一个", 1)

    data = load_calendar()

    if args.check:
        result = check(data)
        print(json.dumps(envelope("ok", None, "检查完成", result),
                         ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.template:
        print(json.dumps(envelope("ok", None, "模板已生成（未写入文件）",
                                  make_template(args.template)),
                         ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.add_year:
        if not args.holidays:
            fail("ERR_ARGS_MISSING", "--add-year须配合--holidays提供JSON数组", 1)
        try:
            holidays = json.loads(args.holidays)
        except ValueError:
            fail("ERR_ARGS_MISSING", "--holidays不是合法JSON", 1)
        if not isinstance(holidays, list) or not holidays:
            fail("ERR_ARGS_MISSING", "--holidays须为非空JSON数组", 1)
        if str(args.add_year) in data.get("years", {}):
            fail("ERR_ARGS_MISSING",
                 "%d年度数据已存在（共%d条）；如需修正请先人工编辑%s"
                 % (args.add_year, len(data["years"][str(args.add_year)]),
                    os.path.relpath(CAL_PATH)), 1)
        result = add_year(data, args.add_year, holidays)
        print(json.dumps(envelope("ok", None, "年度数据已录入", result),
                         ensure_ascii=False, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
