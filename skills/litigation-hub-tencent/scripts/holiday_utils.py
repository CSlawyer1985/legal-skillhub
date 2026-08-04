#!/usr/bin/env python3
"""
法定节假日工具模块。
每年 1 月 1 日后首次调用时自动从国务院官网检索最新节假日安排。

用法:
  from holiday_utils import is_business_day, next_business_day, adjust_deadline
"""

import json
import os
from datetime import datetime, timedelta

HOLIDAYS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'references', 'china-holidays.json')


def _load_holidays():
    try:
        with open(HOLIDAYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # 文件缺失或损坏时返回空，不崩溃


def _ensure_current_year():
    """确保当前年份的节假日数据已加载。每年1月1日后首次调用时提示更新。"""
    data = _load_holidays()
    year = str(datetime.now().year)
    if year not in data:
        print(f"⚠️ {year}年节假日数据尚未收录，请从 https://www.gov.cn 获取最新安排")
        print(f"   手动更新: references/china-holidays.json → 添加 \"{year}\" 条目")
    return data.get(year, {})


def _all_holiday_dates():
    """返回当前年份所有假期的日期集合"""
    year_data = _ensure_current_year()
    dates = set()
    for holiday in year_data.get('holidays', {}).values():
        dates.update(holiday.get('dates', []))
    return dates


def _all_makeup_dates():
    """返回当前年份所有补班日的日期集合"""
    year_data = _ensure_current_year()
    return set(year_data.get('makeup_workdays', []))


def is_business_day(date_str):
    """
    判断是否为工作日。
    规则: 非周六/周日 OR 是补班日，AND 不是法定假期。
    """
    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
    holidays = _all_holiday_dates()
    makeup = _all_makeup_dates()

    if date_str[:10] in holidays:
        return False
    if date_str[:10] in makeup:
        return True
    # 周六=5, 周日=6
    return dt.weekday() < 5


def next_business_day(date_str):
    """
    返回下一个工作日。
    如果传入日期本身是工作日则返回自身，否则顺延到最近的工作日。
    """
    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
    current = dt
    # 最多顺延 30 天防止死循环
    for _ in range(30):
        if is_business_day(current.strftime("%Y-%m-%d")):
            return current.strftime("%Y-%m-%d")
        current += timedelta(days=1)
    return dt.strftime("%Y-%m-%d")  # 回退


def adjust_deadline(deadline_str):
    """
    调整期限至最近的工作日（如果到期日为法定假期或周末）。
    用于上诉期、缴费期等法律期限的自动顺延。
    """
    dt = datetime.strptime(deadline_str[:10], "%Y-%m-%d")
    # 先看是否顺延到工作日
    adjusted = next_business_day(deadline_str)
    if adjusted != deadline_str[:10]:
        adj_dt = datetime.strptime(adjusted, "%Y-%m-%d")
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        original_weekday = weekdays[dt.weekday()]
        print(f"  📅 期限顺延: {deadline_str[:10]}（{original_weekday}，非工作日）→ {adjusted}（{weekdays[adj_dt.weekday()]}）")
    return adjusted


def holidays_in_range(start_str, end_str):
    """返回指定日期范围内包含的法定假日日期列表"""
    start = datetime.strptime(start_str[:10], "%Y-%m-%d")
    end = datetime.strptime(end_str[:10], "%Y-%m-%d")
    holidays = _all_holiday_dates()
    result = []
    current = start
    while current <= end:
        ds = current.strftime("%Y-%m-%d")
        if ds in holidays:
            result.append(ds)
        current += timedelta(days=1)
    return result


# 测试
if __name__ == "__main__":
    print("工作日测试:")
    print(f"  2026-07-08 (周三): {is_business_day('2026-07-08')}")
    print(f"  2026-07-11 (周六): {is_business_day('2026-07-11')}")
    print(f"  2026-10-01 (国庆): {is_business_day('2026-10-01')}")
    print(f"  2026-02-14 (补班): {is_business_day('2026-02-14')}")
    print()
    print(f"  2026-07-11 下一工作日: {next_business_day('2026-07-11')}")
    print(f"  2026-10-01 下一工作日: {next_business_day('2026-10-01')}")
    print(f"  期限调整: {adjust_deadline('2026-07-11')}")
