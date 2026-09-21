#!/usr/bin/env python3
"""法律咨询口径度量引擎 — 确定性计算，禁止 LLM 手算。

指标：复用率 / 领域覆盖率 / 口径库增长率 / 响应时长 / 沉淀转化率 / 人均咨询量
"""

import argparse
import json
import os
import sys
from datetime import datetime, date


def pct(v, digits=1):
    """百分比格式化，None → '—'"""
    if v is None:
        return None
    return round(v * 100, digits)


def median(lst):
    if not lst:
        return None
    s = sorted(lst)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return round((s[n // 2 - 1] + s[n // 2]) / 2, 1)


def compute(ledger_records, corpus, today=None, window_start=None, window_end=None):
    """
    主度量函数。

    Parameters
    ----------
    ledger_records : list[dict]
        台账记录，每条含：
        - question_summary (str)
        - domain (str)
        - asker (str)
        - group (str)
        - ask_time (str, ISO date)
        - matched_corpus_id (str or None)
        - matched_similarity (float or None)
        - ai_draft (str)
        - final_reply (str)
        - is_reuse (bool)
        - is_deposited (bool)
        - reply_time (str, ISO date, optional)
    corpus : list[dict]
        口径库 consult_corpus.json
    today : date, optional
    window_start, window_end : date, optional
        本期窗口（用于 period 指标）
    """
    today = today or date.today()
    total = len(ledger_records)
    corpus_domains = set(c.get("法律领域", "") for c in corpus if c.get("法律领域"))
    if total == 0:
        r = _empty_result(today)
        r["corpus"]["total_entries"] = len(corpus)
        r["corpus"]["domains_covered"] = len(corpus_domains)
        return r

    # ── 累计指标 ──
    reuse_count = sum(1 for r in ledger_records if r.get("is_reuse"))
    deposit_count = sum(1 for r in ledger_records if r.get("is_deposited"))
    askers = set(r.get("asker", "") for r in ledger_records if r.get("asker"))

    # 响应时长：ask_time → reply_time（仅计算有 reply_time 的）
    durations = []
    for r in ledger_records:
        at = r.get("ask_time")
        rt = r.get("reply_time")
        if at and rt:
            try:
                d1 = datetime.fromisoformat(at).date() if "T" in str(at) else datetime.strptime(str(at)[:10], "%Y-%m-%d").date()
                d2 = datetime.fromisoformat(rt).date() if "T" in str(rt) else datetime.strptime(str(rt)[:10], "%Y-%m-%d").date()
                durations.append((d2 - d1).days)
            except (ValueError, TypeError):
                pass

    # ── 领域覆盖 ──
    all_domains = set()
    for r in ledger_records:
        d = r.get("domain", "")
        if d:
            all_domains.add(d)
    corpus_domains = set(c.get("法律领域", "") for c in corpus if c.get("法律领域"))
    covered_domains = all_domains & corpus_domains
    coverage = len(covered_domains) / len(all_domains) if all_domains else None

    # ── 本期窗口 ──
    period = {}
    if window_start and window_end:
        period_records = []
        for r in ledger_records:
            try:
                at_str = str(r.get("ask_time", ""))[:10]
                at = datetime.strptime(at_str, "%Y-%m-%d").date()
                if window_start <= at <= window_end:
                    period_records.append(r)
            except (ValueError, TypeError):
                pass
        pt = len(period_records)
        p_reuse = sum(1 for r in period_records if r.get("is_reuse"))
        period = {
            "new": pt,
            "reuse_count": p_reuse,
            "reuse_rate": pct(p_reuse / pt) if pt else None,
        }

    # ── 领域分布 ──
    domain_dist = {}
    for r in ledger_records:
        d = r.get("domain", "未分类")
        domain_dist[d] = domain_dist.get(d, 0) + 1

    # ── 提问人分布 ──
    asker_dist = {}
    for r in ledger_records:
        a = r.get("asker", "未知")
        asker_dist[a] = asker_dist.get(a, 0) + 1

    # ── 口径复用排行 ──
    corpus_reuse = {}
    for r in ledger_records:
        cid = r.get("matched_corpus_id")
        if cid:
            corpus_reuse[cid] = corpus_reuse.get(cid, 0) + 1

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": str(today),
        "window": {
            "start": str(window_start) if window_start else None,
            "end": str(window_end) if window_end else None,
        },
        "cumulative": {
            "total": total,
            "reuse_count": reuse_count,
            "reuse_rate": pct(reuse_count / total) if total else None,
            "deposit_count": deposit_count,
            "deposit_rate": pct(deposit_count / total) if total else None,
            "unique_askers": len(askers),
            "avg_consult_per_asker": round(total / len(askers), 1) if askers else None,
        },
        "corpus": {
            "total_entries": len(corpus),
            "domains_covered": len(corpus_domains),
            "domain_coverage": pct(coverage),
            "growth_rate": None,  # 需要历史快照才能算
        },
        "response_time": {
            "n": len(durations),
            "median": median(durations),
            "mean": round(sum(durations) / len(durations), 1) if durations else None,
            "max": max(durations) if durations else None,
        },
        "period": period,
        "dist": {
            "domain": domain_dist,
            "asker": dict(sorted(asker_dist.items(), key=lambda x: -x[1])[:10]),
            "corpus_reuse": dict(sorted(corpus_reuse.items(), key=lambda x: -x[1])[:10]),
        },
    }


def _empty_result(today):
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": str(today),
        "window": {"start": None, "end": None},
        "cumulative": {
            "total": 0, "reuse_count": 0, "reuse_rate": None,
            "deposit_count": 0, "deposit_rate": None,
            "unique_askers": 0, "avg_consult_per_asker": None,
        },
        "corpus": {"total_entries": 0, "domains_covered": 0, "domain_coverage": None, "growth_rate": None},
        "response_time": {"n": 0, "median": None, "mean": None, "max": None},
        "period": {},
        "dist": {"domain": {}, "asker": {}, "corpus_reuse": {}},
    }


def build_markdown(m):
    """生成 Markdown 格式的度量摘要。"""
    c = m["cumulative"]; co = m["corpus"]; rt = m["response_time"]
    lines = ["■ 法律咨询口径度量（确定性引擎 metrics.py）"]
    seg = f"累计 {c['total']}件｜复用 {c['reuse_count']}件({c['reuse_rate']}%)｜沉淀 {c['deposit_count']}件({c['deposit_rate']}%)"
    lines.append(seg)
    lines.append(f"口径库 {co['total_entries']}条｜覆盖 {co['domains_covered']}个领域({co['domain_coverage']}%)")
    if rt["n"]:
        lines.append(f"响应时长：中位 {rt['median']}天｜均值 {rt['mean']}天｜最长 {rt['max']}天（样本{rt['n']}件）")
    if c.get("unique_askers"):
        lines.append(f"提问人 {c['unique_askers']}人｜人均 {c['avg_consult_per_asker']}件")
    if m.get("period"):
        p = m["period"]
        lines.append(f"本期新增 {p['new']}｜复用率 {p['reuse_rate']}%")
    lines.append("（复用率=命中历史口径的咨询占比；覆盖率=口径库已覆盖的法律领域占比）")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="法律咨询口径度量引擎")
    ap.add_argument("--ledger", required=True, help="台账快照 JSON")
    ap.add_argument("--corpus", required=True, help="口径库 JSON")
    ap.add_argument("--today", default=None)
    ap.add_argument("--window-start", default=None)
    ap.add_argument("--window-end", default=None)
    ap.add_argument("--output", default=None, help="输出 JSON 路径（默认 stdout）")
    ap.add_argument("--md", action="store_true", help="输出 Markdown 格式")
    args = ap.parse_args()

    ledger = json.load(open(args.ledger, encoding="utf-8"))
    corpus = json.load(open(args.corpus, encoding="utf-8"))

    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else None
    ws = datetime.strptime(args.window_start, "%Y-%m-%d").date() if args.window_start else None
    we = datetime.strptime(args.window_end, "%Y-%m-%d").date() if args.window_end else None

    m = compute(ledger, corpus, today=today, window_start=ws, window_end=we)

    if args.md:
        text = build_markdown(m)
    else:
        text = json.dumps(m, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[metrics] → {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
