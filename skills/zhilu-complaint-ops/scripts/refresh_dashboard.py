#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_dashboard.py — 台账快照 → 投影(含数据完整度) → 看板HTML 的单一刷新入口。
managed-DWS：脚本不能直调 dws；Agent 先 `dws aitable record query --format json` 落盘，
再把该文件喂给本脚本。它同时产出：
  1) dashboard_data.json —— 看板明细快照（含 miss 缺项）
  2) ledger_engine.json  —— step5 巡检投影
  3) 直接调用 dashboard_gen 生成 HTML
用法:
  python3 refresh_dashboard.py --ledger <台账dump.json>
        [--snap dashboard_data.json] [--engine ledger_engine.json]
        [--html 智录运营看板.html]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import completeness  # noqa: E402
import dashboard_gen  # noqa: E402
import metrics as metrics_engine  # noqa: E402
from ledger_io import FM, cell, load_records  # noqa: E402  (统一真源，避免 step5 与本脚本各存一份投影)


def main():
    default_dir = os.path.expanduser("~/.qwenworkcn/complaint-workflow-prod")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True, help="台账快照：dws query 原始响应或投影列表")
    ap.add_argument("--corpus", default=os.path.join(default_dir, "golden_corpus.json"),
                    help="口径库路径（用于知识资产指标）")
    ap.add_argument("--snap", default=os.path.join(default_dir, "dashboard_data.json"))
    ap.add_argument("--engine", default=os.path.join(default_dir, "ledger_engine.json"))
    ap.add_argument("--metrics", default=os.path.join(default_dir, "metrics.json"))
    ap.add_argument("--html", default=os.path.expanduser(
        "~/.qwenworkcn/workspace/msxzj93lzcuofavg/outputs/智录运营看板.html"))
    args = ap.parse_args()

    records = load_records(args.ledger)

    tickets, engine_rows = [], []
    for r in records:
        logical = {
            "投诉编号": cell(r, FM["no"]), "投诉人": cell(r, FM["person"]),
            "联系方式": cell(r, FM["contact"]), "被投诉主体": cell(r, FM["subject"]),
            "投诉类型": cell(r, FM["ctype"]), "投诉内容": cell(r, FM["content"]),
            "诉求金额": cell(r, FM["amount"]), "收到日期": cell(r, FM["recv"]),
            "截止日期": cell(r, FM["deadline"]), "处理状态": cell(r, FM["status"]),
            "跟进记录": cell(r, FM["follow"]),
        }
        engine_rows.append(logical)
        miss = completeness.missing_fields(logical)
        ctype = cell(r, FM["ctype"]) or "其他"
        case_type = cell(r, FM["case_type"])
        disp = case_type if case_type and case_type != "12315消费者投诉" else ctype
        tickets.append({
            "no": cell(r, FM["no"]) or "-", "person": cell(r, FM["person"]) or "匿名",
            "type": disp, "amount": cell(r, FM["amount"]),
            "date": cell(r, FM["recv"]), "status": cell(r, FM["status"]) or "-",
            "content": cell(r, FM["content"]), "risk": cell(r, FM["risk"]),
            "score": cell(r, FM["score"]) or 0, "miss": miss,
        })

    json.dump(tickets, open(args.snap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(engine_rows, open(args.engine, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    m = metrics_engine.compute(records)

    # 知识资产指标
    if args.corpus and os.path.exists(args.corpus):
        km = metrics_engine.compute_knowledge_metrics(args.corpus)
        if km:
            m["knowledge"] = km

    json.dump(m, open(args.metrics, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dashboard_gen.generate(tickets, args.html, metrics=m)

    res = completeness.analyze(engine_rows)
    cr = m['cumulative']['closure_rate']; rf = m['refund']['case_rate_pct']
    print(f"[refresh_dashboard] 快照{res['total']}件 未完结{res['pending']} "
          f"完整{res['complete']} 待补全{res['incomplete']} | 办结率{cr}% 退赔件率{rf}% → {args.html}")
    if m.get("knowledge"):
        k = m["knowledge"]
        print(f"  口径库{k['total_entries']}条 复用{k['total_reuse']}次 覆盖{len(k['type_coverage'])}类")


if __name__ == "__main__":
    main()
