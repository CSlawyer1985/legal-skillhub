#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同智囊 · 质控指标看板

--log      追加一条审查记录到 metrics_log.jsonl
--report   聚合 metrics_log + feedback_stats，输出质控看板(md)

记录字段：contract_type, num_issues, high, mid, low, duration_sec, mode, external
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
METRICS_FILE = SKILL_ROOT / "references" / "metrics" / "metrics_log.jsonl"
STATS_FILE = SKILL_ROOT / "references" / "feedback" / "feedback_stats.jsonl"


def log(record_json, metrics_file):
    metrics_file = Path(metrics_file)
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    rec = json.loads(record_json)
    with metrics_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[metrics] 已记录：{rec.get('contract_type')} / {rec.get('num_issues')} 个问题")


def report(metrics_file, stats_file):
    metrics_file = Path(metrics_file)
    if not metrics_file.exists():
        print("暂无指标数据。", file=sys.stderr)
        sys.exit(1)
    recs = [json.loads(l) for l in metrics_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    n = len(recs)
    total_issues = sum(r.get("num_issues", 0) for r in recs)
    high = sum(r.get("high", 0) for r in recs)
    mid = sum(r.get("mid", 0) for r in recs)
    low = sum(r.get("low", 0) for r in recs)
    dur = [r.get("duration_sec", 0) for r in recs if r.get("duration_sec")]
    avg_dur = sum(dur) / len(dur) if dur else 0
    type_cnt = defaultdict(int)
    for r in recs:
        type_cnt[r.get("contract_type", "?")] += 1
    mis_rate = "N/A"
    if Path(stats_file).exists():
        a = p = rr = 0
        for l in Path(stats_file).read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            d = json.loads(l)
            a += d.get("accepted", 0); p += d.get("partial", 0); rr += d.get("rejected", 0)
        if a + rr:
            mis_rate = f"{rr / (a + rr) * 100:.1f}%"
    L = []
    L.append("# 合同智囊 · 质控指标看板\n")
    L.append(f"> 累计审查：**{n}** 次 ｜ 发现问题：**{total_issues}** 条"
             f"｜ 平均耗时：**{avg_dur:.1f}s** ｜ 误报率：**{mis_rate}**\n")
    L.append("## 风险分布\n")
    L.append(f"🔴 高 {high} ｜ 🟡 中 {mid} ｜ 🟢 低 {low}（合计 {total_issues}）\n")
    L.append("## 合同类型覆盖\n")
    L.append("| 类型 | 审查次数 |")
    L.append("|------|---------|")
    for t, c in sorted(type_cnt.items(), key=lambda x: -x[1]):
        L.append(f"| {t} | {c} |")
    L.append("\n---\n*由 `scripts/metrics_report.py` 生成。"
             "误报率来自反馈闭环统计（驳回/(采纳+驳回)）。*")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description="质控指标看板")
    ap.add_argument("--log", help="JSON 字符串审查记录")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--metrics-file", default=str(METRICS_FILE))
    ap.add_argument("--stats-file", default=str(STATS_FILE))
    args = ap.parse_args()
    if args.log:
        log(args.log, args.metrics_file)
    elif args.report:
        report(args.metrics_file, args.stats_file)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
