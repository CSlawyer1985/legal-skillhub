#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_draft.py — 复核闭环·批量起草（自动化层→智能化层的衔接）

采集入库后，对"待起草/未起草"的工单批量检索相似口径 + AI 起草答复初稿，
打上"已起草待复核"，交人工在工作台/台账复核。次日 --redraft-open 会用更新后的
口径库对仍未完结的工单重新起草（越攒越准）。

设计：纯本地、只读快照、不写生产台账。LLM 有 key 则真跑、无 key 降级模板。
写回台账由 Agent 顶层 dws 完成（读 outputs 里的 AI建议 + 复核状态）。

用法:
  python3 batch_draft.py --data /tmp/ledger.json --corpus golden_corpus.json \
      --out /tmp/drafts.json [--redraft-open] [--limit 20]
  可选环境变量 LLM_API_KEY（有则调 step4.draft_with_llm 真跑，无则模板）。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_io  # noqa: E402
import step4_draft_reply as s4  # noqa: E402

# 复核状态生命周期
ST_TODO = "待起草"
ST_TO_REVIEW = "已起草待复核"
DONE = "已完结"


def _key(rec, *names):
    for n in names:
        if rec.get(n):
            return str(rec[n]).strip()
    return ""


def _needs_draft(rec, redraft_open):
    status = _key(rec, "复核状态", "review_status")
    biz = _key(rec, "处理状态")
    if biz == DONE:
        return False
    if not status or status == ST_TODO:
        return True
    if redraft_open and status == ST_TO_REVIEW:
        return True  # 用更新后的口径库重新起草
    return False


def draft_one(rec, corpus, api_key):
    content = _key(rec, "投诉内容", "content")
    refs = s4.retrieve_similar(corpus, content, top_k=3)
    if api_key:
        try:
            reply = s4.draft_with_llm(api_key, rec, refs)
        except Exception:
            reply = s4.draft_template(rec)
    else:
        reply = s4.draft_template(rec)
    return reply, [r.get("id") for r in refs[:3]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="台账快照 JSON（raw 或投影，ledger_io 自动归一）")
    ap.add_argument("--corpus", default="golden_corpus.json")
    ap.add_argument("--out", default="drafts.json")
    ap.add_argument("--redraft-open", action="store_true", help="对未完结工单按最新口径库重新起草")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    rows = ledger_io.to_engine(ledger_io.load_records(args.data))
    corpus = s4.load_corpus(args.corpus)
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    engine = "本地千问/DashScope" if api_key else "模板引擎（无 LLM_API_KEY，降级）"

    targets = [r for r in rows if _needs_draft(r, args.redraft_open)][:args.limit]
    outputs = []
    for rec in targets:
        reply, hit = draft_one(rec, corpus, api_key)
        outputs.append({
            "投诉编号": _key(rec, "投诉编号", "no"),
            "recordId": rec.get("recordId", ""),
            "投诉类型": _key(rec, "投诉类型", "ctype"),
            "AI建议": reply,
            "复核状态": ST_TO_REVIEW,
            "命中口径": hit,
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"engine": engine, "drafted": len(outputs), "items": outputs},
                  f, ensure_ascii=False, indent=2)
    print(f"批量起草：目标 {len(targets)} 条，已起草 {len(outputs)} 条 → {args.out}（起草引擎：{engine}）")
    print("下一步：Agent 用 dws record update 把每条的 AI建议(ev6l0q6) + 复核状态 写回台账，进人工复核队列。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
