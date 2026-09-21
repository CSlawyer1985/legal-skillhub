#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_apply.py — 复核闭环·每日入库（经验固化层）

把当天"人工复核通过"的工单（复核状态=已复核待入库，或 处理状态=已完结且已填最终答复）
连同律师定稿口径追加进 golden_corpus.json，并产出把台账复核状态改"已入库"的更新载荷。
这是"用得越多、沉淀越多"的落库动作；也是次日 --redraft-open 能命中更优口径的前提。

设计：纯本地。默认 --dry 只预览不写；加 --apply 才真正追加 golden_corpus（写前先备份）。
写回台账状态由 Agent 顶层 dws 完成（读 updates.json）。

用法:
  python3 review_apply.py --data /tmp/ledger.json --corpus golden_corpus.json \
      [--apply] [--updates /tmp/updates.json]
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_io  # noqa: E402

ST_APPROVED = "已复核待入库"
ST_DEPOSITED = "已入库"
DONE = "已完结"


def _key(rec, *names):
    for n in names:
        if rec.get(n):
            return str(rec[n]).strip()
    return ""


def _classify_result(reply):
    """从定稿答复粗判处置结果（口径库分布用；判不准时留待核实，不硬编退款）。"""
    r = reply or ""
    if any(k in r for k in ["不支持退款", "不予退款", "无法退款", "不符合退款"]):
        return "不支持退款"
    if any(k in r for k in ["折算", "部分退"]):
        return "折算退款"
    if any(k in r for k in ["全额退款", "已退款", "退还全部", "原路退回"]):
        return "全额退款"
    if any(k in r for k in ["技术原因", "系统", "协议已有提示", "联系客服"]):
        return "技术说明+引导客服"
    return "待核实"


def _next_id(corpus):
    mx = 0
    for e in corpus:
        m = re.match(r"REAL-(\d+)", str(e.get("id", "")))
        if m:
            mx = max(mx, int(m.group(1)))
    return mx


def _already_in(corpus, case_content):
    cc = (case_content or "").strip()
    return any((e.get("case_content", "").strip() == cc) for e in corpus)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="台账快照 JSON")
    ap.add_argument("--corpus", default="golden_corpus.json")
    ap.add_argument("--updates", default="review_updates.json")
    ap.add_argument("--apply", action="store_true", help="真正追加口径库（默认只预览）")
    args = ap.parse_args()

    rows = ledger_io.to_engine(ledger_io.load_records(args.data))
    corpus = json.load(open(args.corpus, encoding="utf-8")) if os.path.exists(args.corpus) else []

    def approved(rec):
        rs = _key(rec, "复核状态", "review_status")
        final = _key(rec, "最终答复", "final", "Q587I0X")
        biz = _key(rec, "处理状态")
        return bool(final) and (rs == ST_APPROVED or (biz == DONE and rs != ST_DEPOSITED))

    picks = [r for r in rows if approved(r)]
    new_entries, updates, skipped = [], [], 0
    nid = _next_id(corpus)
    today = date.today().isoformat()
    for rec in picks:
        content = _key(rec, "投诉内容", "content")
        final = _key(rec, "最终答复", "final")
        if _already_in(corpus, content):
            skipped += 1
            continue
        nid += 1
        new_entries.append({
            "id": f"REAL-{nid:03d}",
            "投诉类型": _key(rec, "投诉类型", "ctype") or "其他",
            "case_content": content,
            "ai_suggestion": _key(rec, "AI建议", "suggestion"),
            "golden_reply": final,
            "处置结果": _classify_result(final),
            "口径要点": final[:60],
            "入库时间": today,
            "入库律师": _key(rec, "处理人", "handler") or "承办律师",
            "复用次数": 0,
            "关联工单数": 1,
            "质量评分": 5,
        })
        updates.append({"投诉编号": _key(rec, "投诉编号", "no"), "recordId": rec.get("recordId", ""),
                        "复核状态": ST_DEPOSITED})

    with open(args.updates, "w", encoding="utf-8") as f:
        json.dump(updates, f, ensure_ascii=False, indent=2)

    mode = "APPLY（已写库）" if args.apply else "DRY-RUN（预览，未写库）"
    print(f"复核入库[{mode}]：候选 {len(picks)} · 新入库 {len(new_entries)} · 去重跳过 {skipped}")
    for e in new_entries:
        print(f"  + {e['id']} {e['投诉类型']}｜处置:{e['处置结果']}｜{e['case_content'][:26]}")
    if args.apply and new_entries:
        shutil.copy2(args.corpus, args.corpus + ".bak-" + today)  # 写前备份
        corpus.extend(new_entries)
        with open(args.corpus, "w", encoding="utf-8") as f:
            json.dump(corpus, f, ensure_ascii=False, indent=2)
        print(f"  已追加 {len(new_entries)} 条 → {args.corpus}（原库已备份 .bak-{today}）")
    print(f"  台账更新载荷 → {args.updates}（Agent 用 dws record update 把复核状态改『已入库』）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
