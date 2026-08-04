#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同智囊 · 反馈闭环（持久化学习）

将律师对审核结论的「采纳 / 部分采纳 / 驳回」落盘为 feedback_stats，
供同类合同下次审查时调整默认置信度与优先级。

三种用法：
  classify      对比 原台账(ledger) 与 定稿(final docx / 或 --changes-json)，
                逐条判定采纳状态，输出 feedback-<contract>.json
  update-stats  汇总 feedback-*.json，累加进 references/feedback/feedback_stats.jsonl
  report        打印当前反馈统计摘要

依赖：python-docx + lxml（仅 classify 解析 docx 时需要；可用 --changes-json 跳过）
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
FEEDBACK_DIR = SKILL_ROOT / "references" / "feedback"
STATS_FILE = FEEDBACK_DIR / "feedback_stats.jsonl"


def _norm(s):
    if not s:
        return ""
    return re.sub(r"\s+", "", str(s))


def extract_changes(docx_path):
    """从 docx 提取 Track Changes 文本：返回 (ins_list, del_list)"""
    try:
        from docx import Document
        from lxml import etree  # noqa: F401
    except Exception as e:  # pragma: no cover
        print(f"[feedback_loop] 需要 python-docx+lxml 才能解析 docx：{e}", file=sys.stderr)
        sys.exit(2)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    doc = Document(docx_path)
    body = doc.element.body
    ins, dele = [], []
    for el in body.findall(".//w:ins", ns):
        t = "".join(n.text or "" for n in el.findall(".//w:t", ns))
        if t.strip():
            ins.append(t)
    for el in body.findall(".//w:del", ns):
        t = "".join(n.text or "" for n in el.findall(".//w:delText", ns))
        if t.strip():
            dele.append(t)
    return ins, dele


def classify(ledger_path, ins, dele):
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    del_norm = [_norm(d) for d in dele]
    ins_norm = [_norm(i) for i in ins]
    # 拼接全文：Word 的 Track Changes 常把一段删除/新增拆成多个 run，
    # 只比对单个 run 会漏匹配→误判为「驳回」，故同时比对拼接全文。
    ins_all = "".join(ins_norm)
    del_all = "".join(del_norm)
    results = []
    user_added = []
    matched_ins = set()
    for issue in ledger.get("issues", []):
        orig = _norm(issue.get("original_text", ""))
        simple = _norm(issue.get("model_clause_simple", ""))
        full = _norm(issue.get("model_clause_full", ""))
        orig_deleted = bool(orig) and (any(orig in d for d in del_norm) or orig in del_all)
        simple_in = bool(simple) and (any(simple in i for i in ins_norm) or simple in ins_all)
        full_in = bool(full) and (any(full in i for i in ins_norm) or full in ins_all)
        if orig_deleted and (simple_in or full_in):
            status = "accepted"
        elif orig_deleted:
            # 删了原文但示范条款未明显进入，视为部分采纳
            status = "partial"
        else:
            # 原文保留 = 未采纳
            status = "rejected"
        for idx, i in enumerate(ins_norm):
            if (simple and simple in i) or (full and full in i):
                matched_ins.add(idx)
        results.append({
            "id": issue.get("id"),
            "section": issue.get("section"),
            "risk_level": issue.get("risk_level"),
            "status": status,
        })
    for idx, i in enumerate(ins_norm):
        if idx not in matched_ins and len(i) >= 6:
            user_added.append(i[:80])
    return {
        "document": ledger.get("document"),
        "contract_type": ledger.get("contract_type"),
        "issues": results,
        "user_added_clauses": user_added,
    }


def update_stats(feedback_dir, out_file):
    feedback_dir = Path(feedback_dir)
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    agg = {}
    for f in sorted(feedback_dir.glob("feedback-*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        ctype = data.get("contract_type", "未知")
        for it in data.get("issues", []):
            sig = f"{ctype}|{it.get('section', '')}"
            d = agg.setdefault(sig, {
                "accepted": 0, "partial": 0, "rejected": 0,
                "contract_type": ctype, "section": it.get("section", ""),
            })
            st = it.get("status")
            if st in d:
                d[st] += 1
    lines = []
    for sig, d in sorted(agg.items()):
        d2 = dict(d)
        d2["signature"] = sig
        lines.append(json.dumps(d2, ensure_ascii=False))
    out_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def report(stats_file):
    stats_file = Path(stats_file)
    if not stats_file.exists():
        print("暂无反馈统计。")
        return
    total_a = total_p = total_r = 0
    print(f"{'合同类型|章节':<42}{'采纳':>6}{'部分':>6}{'驳回':>6}")
    for line in stats_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        a, p, r = d.get("accepted", 0), d.get("partial", 0), d.get("rejected", 0)
        total_a += a; total_p += p; total_r += r
        print(f"{d.get('signature', ''):<42}{a:>6}{p:>6}{r:>6}")
    print("-" * 62)
    print(f"{'合计':<42}{total_a:>6}{total_p:>6}{total_r:>6}")
    denom = total_a + total_r
    if denom:
        print(f"误报率（驳回/(采纳+驳回)）≈ {total_r / denom * 100:.1f}%")


def main():
    ap = argparse.ArgumentParser(description="合同智囊反馈闭环")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("classify")
    p1.add_argument("--ledger", required=True)
    p1.add_argument("--final", help="定稿 docx 路径")
    p1.add_argument("--changes-json", help="预提取的 {ins:[],del:[]} JSON，用于测试/无 docx 环境")
    p1.add_argument("--out", help="输出 feedback-*.json 路径")
    p2 = sub.add_parser("update-stats")
    p2.add_argument("--feedback-dir", default=str(FEEDBACK_DIR))
    p2.add_argument("--out", default=str(STATS_FILE))
    p3 = sub.add_parser("report")
    p3.add_argument("--stats", default=str(STATS_FILE))
    args = ap.parse_args()

    if args.cmd == "classify":
        if args.changes_json:
            ch = json.loads(Path(args.changes_json).read_text(encoding="utf-8"))
            ins, dele = ch.get("ins", []), ch.get("del", [])
        elif args.final:
            ins, dele = extract_changes(args.final)
            if not ins and not dele:
                print(
                    "[feedback_loop] 定稿中未检测到任何修订痕迹（Track Changes）。\n"
                    "  可能原因：定稿前已『接受所有修订』，痕迹已被抹除。\n"
                    "  此时无法判定采纳/驳回，继续统计会把所有条目误判为『驳回』并污染误报率。\n"
                    "  解决：改用『保留修订痕迹』的定稿版本，或用 --changes-json 手动提供 {ins:[],del:[]}。",
                    file=sys.stderr,
                )
                sys.exit(3)
        else:
            print("classify 需要 --final 或 --changes-json", file=sys.stderr)
            sys.exit(1)
        out = classify(args.ledger, ins, dele)
        out_path = args.out or (FEEDBACK_DIR / f"feedback-{Path(args.ledger).stem}.json")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[feedback_loop] 已输出 {out_path}：采纳/部分/驳回 共 {len(out['issues'])} 条")
    elif args.cmd == "update-stats":
        n = update_stats(args.feedback_dir, args.out)
        print(f"[feedback_loop] 已更新统计：{n} 个签名写入 {args.out}")
    elif args.cmd == "report":
        report(args.stats)


if __name__ == "__main__":
    main()
