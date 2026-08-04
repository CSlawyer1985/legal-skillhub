#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户纠错 / 评分回流（模式七）。

把用户对某条 golden / seed / 离线索引结论的「纠错」或「评分」追加写入
references/golden/feedback.log（JSONL），并支持标记处理状态，进入「模式三」复核队列。

用法：
  python scripts/feedback.py add --anchor "GB 55037 第 3.2.1 条" --type correct \
      --content "此处疏散宽度应为 4.0m，原文误为 4m"
  python scripts/feedback.py add --anchor "seed#123" --type rating --score 4 \
      --content "答得准，但出处应补 GB 50016"
  python scripts/feedback.py list [--type correct|rating] [--pending]
  python scripts/feedback.py resolve --id <id> [--note "已核实并 confirm 进 golden"]
  python scripts/feedback.py stats

纪律：
  - 纠错/评分只记录「信号」，机器不据此自动改写金标准；
  - 进入复核队列后，由 agent 用「模式一」联网核实，再决定 golden.py confirm / abolish / 修正。
"""

import os
import sys
import json
import argparse
import uuid
from datetime import datetime, timezone

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG = os.path.join(_BASE, "references", "golden", "feedback.log")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load():
    if not os.path.exists(_LOG):
        return []
    rows = []
    with open(_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _save(rows):
    os.makedirs(os.path.dirname(_LOG), exist_ok=True)
    with open(_LOG, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def add(anchor, ftype, content, score):
    if ftype == "rating" and score is None:
        score = 3
    row = {
        "id": uuid.uuid4().hex[:8],
        "ts": _now(),
        "anchor": anchor,
        "type": ftype,
        "content": content,
        "score": score if ftype == "rating" else None,
        "resolved": False,
        "resolve_note": "",
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    print(f"已记录 {ftype} 反馈 → id={row['id']} anchor={anchor}")
    return row


def list_rows(ftype=None, pending_only=False):
    rows = _load()
    if ftype:
        rows = [r for r in rows if r.get("type") == ftype]
    if pending_only:
        rows = [r for r in rows if not r.get("resolved")]
    if not rows:
        print("（无反馈记录）")
        return
    for r in rows:
        mark = "✅" if r.get("resolved") else "⏳"
        extra = f" score={r['score']}" if r.get("type") == "rating" else ""
        note = f"  ← {r['resolve_note']}" if r.get("resolve_note") else ""
        print(f"[{mark}] {r['id']} {r['type']} | {r['anchor']}{extra}\n    {r['content']}{note}")


def resolve(rid, note):
    rows = _load()
    hit = False
    for r in rows:
        if r.get("id") == rid:
            r["resolved"] = True
            r["resolve_note"] = note or "已处理"
            hit = True
            break
    if not hit:
        print(f"❌ 找不到编号为「{rid}」的反馈记录")
        print("\n你可以用以下命令查看所有记录：")
        print("  python scripts/feedback.py list")
        sys.exit(0)
    _save(rows)
    print(f"已标记处理：{rid}（进入模式三复核闭环）")


def stats():
    rows = _load()
    total = len(rows)
    pending = sum(1 for r in rows if not r.get("resolved"))
    correct = sum(1 for r in rows if r.get("type") == "correct")
    ratings = [r["score"] for r in rows if r.get("type") == "rating" and r.get("score") is not None]
    avg = sum(ratings) / len(ratings) if ratings else None
    print(f"总反馈：{total}  | 待处理：{pending}  | 纠错：{correct}  | 评分：{len(ratings)}"
          + (f"  | 平均分：{avg:.2f}" if avg is not None else ""))


def main():
    ap = argparse.ArgumentParser(description="用户纠错/评分回流（模式七）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="新增一条反馈")
    a.add_argument("--anchor", required=True, help="条目锚点，如 'GB 55037 第 3.2.1 条' 或 'seed#123'")
    a.add_argument("--type", required=True, choices=["correct", "rating"], help="correct=纠错 / rating=评分")
    a.add_argument("--content", required=True, help="反馈内容")
    a.add_argument("--score", type=int, choices=range(1, 6), help="rating 时 1-5 分")

    l = sub.add_parser("list", help="列出反馈")
    l.add_argument("--type", choices=["correct", "rating"])
    l.add_argument("--pending", action="store_true", help="仅待处理")

    r = sub.add_parser("resolve", help="标记已处理（进入模式三复核）")
    r.add_argument("--id", required=True)
    r.add_argument("--note", default="")

    s = sub.add_parser("stats", help="统计")

    args = ap.parse_args()
    if args.cmd == "add":
        add(args.anchor, args.type, args.content, getattr(args, "score", None))
    elif args.cmd == "list":
        list_rows(getattr(args, "type", None), args.pending)
    elif args.cmd == "resolve":
        resolve(args.id, args.note)
    elif args.cmd == "stats":
        stats()


def _safe_main():
    """顶层异常兜底。"""
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消。")
    except Exception as e:
        print(f"\n❌ 出了点问题：{type(e).__name__} —— {e}")
        print("如果反复出现，请把这条信息反馈给技术支持。")


if __name__ == "__main__":
    _safe_main()
