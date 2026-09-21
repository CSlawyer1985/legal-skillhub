#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
completeness.py — 智录工单"数据完整度"单一判定（派生式，不落易过期的字段）

规则：对【未完结】工单，缺以下关键字段即视为"待补全"：
  - 联系方式（Ohw9pvL）：无联系方式 → 无法回填结果/无法核实身份
  - 截止日期（Ctv7j2o）：无截止日期 → 巡检盲区（虽有"收到+15天"兜底，但应回填真实值）
诉求金额可合法为 0，不计缺失；被投诉主体为可选软项（默认"钉钉（中国）信息技术有限公司"）。

被 step5 巡检、dashboard_gen 看板、dedup_upsert/采集 三处共用，保证口径一致。

CLI: python3 completeness.py --data <台账投影.json> [--all]
     --all 时连已完结一起看；默认只统计未完结的待补全。
"""
import argparse
import json
import sys

# 关键字段别名：兼容 投影中文名 / 字段ID / 看板ticket键
_KEY_ALIASES = {
    "contact": ("联系方式", "contact", "Ohw9pvL", "phone"),
    "deadline": ("截止日期", "deadline", "Ctv7j2o", "deadline_raw"),
    "status": ("处理状态", "status", "BIi8AY4"),
    "no": ("投诉编号", "no", "01ZM8y7", "case_no"),
    "person": ("投诉人", "person", "wh1fk4j", "complainant"),
}
DONE_STATUSES = ("已完结", "已归档")


def _get(rec, logical):
    for k in _KEY_ALIASES.get(logical, ()):
        if k in rec and rec[k] not in (None, ""):
            v = rec[k]
            # singleSelect 归一
            if isinstance(v, dict):
                v = v.get("name", "")
            return str(v).strip()
    return ""


def missing_fields(rec):
    """返回缺失的关键字段标签列表（空=完整）"""
    miss = []
    if not _get(rec, "contact"):
        miss.append("联系方式")
    if not _get(rec, "deadline"):
        miss.append("截止日期")
    return miss


def is_done(rec):
    return _get(rec, "status") in DONE_STATUSES


def completeness_level(rec):
    """返回 '完整' / '缺联系方式' / '缺截止日期' / '缺联系方式+截止日期'"""
    miss = missing_fields(rec)
    if not miss:
        return "完整"
    return "缺" + "+".join(miss)


def analyze(records, include_done=False):
    """扫描记录，返回 {total, done, pending_total, complete, incomplete, rows:[{no,person,miss,level,status}]}"""
    rows = []
    complete = incomplete = 0
    done = pending = 0
    for rec in records:
        if is_done(rec):
            done += 1
            if not include_done:
                continue
        else:
            pending += 1
        miss = missing_fields(rec)
        if miss:
            incomplete += 1
            rows.append({
                "no": _get(rec, "no") or "?",
                "person": _get(rec, "person") or "匿名",
                "miss": miss,
                "level": completeness_level(rec),
                "status": _get(rec, "status") or "?",
            })
        else:
            complete += 1
    return {
        "total": len(records), "done": done, "pending": pending,
        "complete": complete, "incomplete": incomplete,
        "rows": sorted(rows, key=lambda r: (len(r["miss"]), r["no"]), reverse=True),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="台账投影JSON（列表）")
    ap.add_argument("--all", action="store_true", help="含已完结一起看")
    ap.add_argument("--out", help="可选：把结果写到JSON")
    args = ap.parse_args()
    records = json.load(open(args.data, encoding="utf-8"))
    if isinstance(records, dict):
        records = records.get("data", {}).get("records", records.get("records", []))
    res = analyze(records, include_done=args.all)
    line = f"[completeness] 扫描{res['total']}件(未完结{res['pending']}) 完整{res['complete']} 待补全{res['incomplete']}"
    print(line)
    for r in res["rows"]:
        print(f"  待补全 {r['no']} {r['person']}（{r['status']}）→ 缺：{'+'.join(r['miss'])}")
    if args.out:
        json.dump(res, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
