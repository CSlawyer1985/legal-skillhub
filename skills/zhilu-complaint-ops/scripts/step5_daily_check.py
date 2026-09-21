#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step5 每日巡检：扫描台账，找出今日无跟进、临期（3天内）、已逾期的未完结案件并预警
用法:
  Phase 1仅支持本地模式：python3 step5_daily_check.py --data data/sample_complaints.json
  在线读取和--push已禁用；由Agent顶层通过DWS读取及发送。
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import completeness  # noqa: E402
import ledger_io  # noqa: E402

TODAY = date.today()


def extract_latest_date(text):
    """从跟进记录文本中提取最近一次操作日期"""
    if not text:
        return None
    dates = re.findall(r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}", text)
    latest = None
    for d_str in dates:
        try:
            d = datetime.strptime(d_str.replace("/", "-"), "%Y-%m-%d").date()
            if latest is None or d > latest:
                latest = d
        except ValueError:
            continue
    return latest


def parse_deadline(val):
    if not val:
        return None
    try:
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def run_check(records):
    no_update, due_soon, overdue, incomplete = [], [], [], []
    for rec in records:
        if rec.get("处理状态") in ("已完结", "已归档"):
            continue
        miss = completeness.missing_fields(rec)
        if miss:
            rec["_miss"] = miss
            incomplete.append(rec)
        latest = extract_latest_date(rec.get("跟进记录", ""))
        if latest is None or latest < TODAY:
            no_update.append(rec)
        # 截止日期：有则用，无则用收到日期+15天做默认（避免巡检盲区）
        deadline = parse_deadline(rec.get("截止日期", ""))
        if deadline is None:
            recv = parse_deadline(rec.get("收到日期", ""))
            if recv:
                from datetime import timedelta
                deadline = recv + timedelta(days=15)
        if deadline:
            days_left = (deadline - TODAY).days
            if days_left < 0:
                overdue.append(rec)
            elif days_left <= 3:
                due_soon.append(rec)
    return no_update, due_soon, overdue, incomplete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="本地JSON数据文件")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--push", action="store_true", help="推送到IM（需config.yaml）")
    args = parser.parse_args()

    if not args.data:
        print("在线模式已禁用：请由Agent顶层用DWS导出JSON，再传 --data 本地巡检", file=sys.stderr)
        return 2
    # 统一经 ledger_io 归一：raw dws 单元格格式 / hook 包裹 / 已投影中文键，都能吃，绝不崩。
    records = ledger_io.load_engine(args.data)

    no_update, due_soon, overdue, incomplete = run_check(records)

    print(f"巡检日期: {TODAY}  未完结: {len([r for r in records if r.get('处理状态') not in ('已完结','已归档')])} 件")
    print("=" * 60)
    print(f"\n【今日无跟进】{len(no_update)} 件")
    for r in no_update:
        print(f"  - {r.get('投诉编号','?')} {r.get('投诉人','?')}（{r.get('投诉类型','?')}）")
    print(f"\n【3天内到期】{len(due_soon)} 件")
    for r in due_soon:
        print(f"  - {r.get('投诉编号','?')} 截止 {r.get('截止日期')}")
    print(f"\n【已逾期】{len(overdue)} 件")
    for r in overdue:
        print(f"  - {r.get('投诉编号','?')} 截止 {r.get('截止日期')} ⚠️")
    print(f"\n【数据待补全】{len(incomplete)} 件（缺联系方式/截止日期，回填后才好答复与盯办）")
    for r in incomplete:
        print(f"  - {r.get('投诉编号','?')} {r.get('投诉人','?')} → 缺 {'+ '.join(r.get('_miss', []))}")

    if args.push:
        print("--push 已禁用：请由Agent顶层读取本地巡检结果后使用DWS发送", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
