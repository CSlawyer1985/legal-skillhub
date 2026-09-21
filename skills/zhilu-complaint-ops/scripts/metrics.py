#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metrics.py — 智录·工商投诉运营度量引擎（P1，确定性计算，单一真源）。

设计原则：
  - 周月报和看板都 import 本模块或直接跑本 CLI，绝不再让大模型手算指标（那是 周报 error 的根因之一）。
  - 输入可以是 raw dws {data:{records:[{cells}]} }、hook 包裹、或已投影中文键——用 ledger_io 归一，pick() 双取，绝不崩。

指标口径（已与初二确认）：
  - 办结时长 = 收到日期 → 定稿答复时点。定稿时点无独立字段，用"跟进记录里最后一个可解析日期"做近似代理，标 approx。
  - 办结率   = 已完结/已归档 件数 / 总件数（另给本期 cohort 完结率）。
  - 退赔率   = 件数占比 + 金额占比（关键词近似识别"退款/已退/到账/折算"，标 approx）。
  - 二次投诉率 = 同手机号(无则同人)跨件重复 + 跟进含"二次/再次/重复" 的近似识别，标 approx。
  - 趋势     = 按 ISO 周（近 8 周）或自然月的 新增/完结 序列。

CLI:
  python3 metrics.py --data <台账快照.json> [--today YYYY-MM-DD]
                     [--window-start YYYY-MM-DD --window-end YYYY-MM-DD]
                     [--out metrics.json] [--md]
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_io  # noqa: E402
from ledger_io import FM, cell  # noqa: E402

DONE = ("已完结", "已归档")
_DT = re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:[\sT]+(\d{1,2}):(\d{2}))?")
_YUAN = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*元")
_PHONE = re.compile(r"1[3-9]\d{9}")


# ---------- 字段抽取（raw 与投影双兼容）----------
def pick(rec, fid, *aliases):
    c = rec.get("cells", rec) if isinstance(rec, dict) else {}
    v = c.get(fid, "")
    if isinstance(v, dict):
        v = v.get("name", "")
    if not v:
        for a in aliases:
            w = c.get(a, "")
            if isinstance(w, dict):
                w = w.get("name", "")
            if w:
                v = w
                break
    return str(v).strip() if v else ""


def to_amt(s):
    if not s:
        return None
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)", str(s).replace(",", ""))
    return float(m.group(1)) if m else None


def to_date(s):
    if not s:
        return None
    m = _DT.search(str(s))
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def follow_dates(text):
    out = []
    for m in _DT.finditer(text or ""):
        try:
            out.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            continue
    return out


def norm_person(p):
    p = re.sub(r"[0-9\s]", "", (p or "").strip())
    return p if p and p != "匿名" else ""


# ---------- 分类 ----------
def classify_outcome(text):
    t = text or ""
    if any(k in t for k in ("全额退", "如数退", "全部退", "全额退款")):
        return "全额退款"
    if any(k in t for k in ("折算", "部分退", "按比例", "退剩余", "未使用部分")):
        return "折算退款"
    if any(k in t for k in ("不支持退", "不予退", "无法退", "不符合退", "维持", "拒绝退", "未退")):
        return "不支持退款"
    if any(k in t for k in ("技术", "超时", "截断", "模型", "上下文")) and "退" not in t:
        return "技术说明"
    if any(k in t for k in ("产品", "自定义", "设计", "功能", "版本")) and "退" not in t:
        return "产品说明"
    if any(k in t for k in ("退款", "已退", "退还", "到账", "退回")):
        return "折算退款"
    return "其他"


def amount_bucket(a):
    if a is None:
        return "未填"
    if a >= 5000:
        return "大额≥5000"
    if a >= 500:
        return "中额500-5000"
    return "小额<500"


# ---------- 知识资产指标 ----------
def compute_knowledge_metrics(corpus_path):
    """计算知识资产指标：口径库增长/复用/覆盖率/律师工作量"""
    import json
    from datetime import datetime

    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    if not corpus:
        return None

    # 基础统计
    total = len(corpus)

    # 按投诉类型覆盖
    type_coverage = {}
    for entry in corpus:
        t = entry.get('投诉类型', '其他')
        type_coverage[t] = type_coverage.get(t, 0) + 1

    # 复用统计
    total_reuse = sum(e.get('复用次数', 0) for e in corpus)
    avg_reuse = round(total_reuse / total, 1) if total else 0

    # 关联工单统计
    total_cases = sum(e.get('关联工单数', 0) for e in corpus)

    # 律师工作量（按入库律师分组）
    lawyer_workload = {}
    for entry in corpus:
        lawyer = entry.get('入库律师', '未知')
        if lawyer not in lawyer_workload:
            lawyer_workload[lawyer] = {'入库数': 0, '总复用': 0, '总关联': 0}
        lawyer_workload[lawyer]['入库数'] += 1
        lawyer_workload[lawyer]['总复用'] += entry.get('复用次数', 0)
        lawyer_workload[lawyer]['总关联'] += entry.get('关联工单数', 0)

    # 质量评分（有评分的条目）
    rated = [e for e in corpus if e.get('质量评分', 0) > 0]
    avg_quality = round(sum(e.get('质量评分', 0) for e in rated) / len(rated), 1) if rated else None

    return {
        'total_entries': total,
        'type_coverage': type_coverage,
        'total_reuse': total_reuse,
        'avg_reuse': avg_reuse,
        'total_cases_linked': total_cases,
        'lawyer_workload': lawyer_workload,
        'avg_quality': avg_quality,
        'rated_count': len(rated),
    }


# ---------- 主计算 ----------
def compute(records, today=None, window_start=None, window_end=None):
    today = today or date.today()

    def pct(v):
        return round(v * 100, 1) if v is not None else None

    def median(a):
        return a[len(a) // 2] if a else None

    rich = []
    for r in records:
        follow = pick(r, FM["follow"], "跟进记录")
        final = pick(r, FM["final"], "最终答复")
        fdates = follow_dates(follow)
        recv = to_date(pick(r, FM["recv"], "收到日期"))
        res = max(fdates) if fdates else None
        amt = to_amt(pick(r, FM["amount"], "诉求金额"))
        status = pick(r, FM["status"], "处理状态")
        outcome_text = final + " " + follow
        refund_explicit = [float(x.replace(",", "")) for x in _YUAN.findall(outcome_text)]
        rich.append({
            "no": pick(r, FM["no"], "投诉编号"),
            "person": norm_person(pick(r, FM["person"], "投诉人")),
            "phones": set(_PHONE.findall(pick(r, FM["contact"], "联系方式") + " " + pick(r, FM["ctype"], ""))),
            "ctype": pick(r, FM["ctype"], "投诉类型") or "其他",
            "amount": amt, "recv": recv, "deadline": to_date(pick(r, FM["deadline"], "截止日期")),
            "status": status, "closed": status in DONE,
            "res_date": res, "first_follow": min(fdates) if fdates else None,
            "outcome": classify_outcome(outcome_text),
            "refund_amt": (max(refund_explicit) if refund_explicit else None),
            "repeat_kw": any(k in outcome_text for k in ("二次来件", "再次投诉", "重复投诉", "二次投诉", "再次来件")),
        })

    total = len(rich)
    closed = sum(1 for x in rich if x["closed"])
    open_ = total - closed
    total_amt = sum(x["amount"] or 0 for x in rich if x["amount"])

    # 办结时长（收到→定稿近似）：已完结 + 两个日期都有
    dur = []
    for x in rich:
        if x["closed"] and x["recv"] and x["res_date"] and x["res_date"] >= x["recv"]:
            dur.append((x["res_date"] - x["recv"]).days)
    dur.sort()

    # 退赔：件数占比 + 金额占比（近似）
    denom = [x for x in rich if x["closed"] and x["amount"]]        # 有诉求金额的完结件
    refund_cases = [x for x in denom if x["outcome"] in ("全额退款", "折算退款")]
    refund_case_rate = (len(refund_cases) / len(denom)) if denom else None
    # 金额：能解析出退款额的用之，全额但无额按诉求，折算但无额不猜(排除)
    num_amt, den_amt = 0.0, 0.0
    for x in denom:
        den_amt += x["amount"]
        if x["outcome"] == "全额退款":
            num_amt += x["refund_amt"] or x["amount"]
        elif x["outcome"] == "折算退款" and x["refund_amt"]:
            num_amt += x["refund_amt"]
    refund_amt_rate = (num_amt / den_amt) if den_amt else None

    # 二次投诉率（近似）：同手机/同人跨件重复的"额外件" + 关键词件
    key2cnt = {}
    for x in rich:
        k = ("ph", tuple(sorted(x["phones"]))) if x["phones"] else (("pn", x["person"]) if x["person"] else None)
        if k:
            key2cnt[k] = key2cnt.get(k, 0) + 1
    dup_extra = sum(c - 1 for c in key2cnt.values() if c > 1)
    kw_only = sum(1 for x in rich if x["repeat_kw"])
    repeat_cases = max(dup_extra, kw_only)  # 保守取两者较大，避免重复计
    repeat_rate = (repeat_cases / total) if total else None

    # 本期窗口
    period = None
    if window_start or window_end:
        ws = to_date(window_start) if isinstance(window_start, str) else window_start
        we = to_date(window_end) if isinstance(window_end, str) else window_end
        new_p = [x for x in rich if x["recv"] and (not ws or x["recv"] >= ws) and (not we or x["recv"] <= we)]
        closed_p = [x for x in new_p if x["closed"]]
        period = {"new": len(new_p), "closed": len(closed_p),
                  "closure_rate": pct(len(closed_p) / len(new_p)) if new_p else None,
                  "amount": round(sum(x["amount"] or 0 for x in new_p))}

    # 趋势：按周（recv 落在的近 8 周）
    def week_bucket(d):
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    trend = {}
    for x in rich:
        if x["recv"]:
            b = week_bucket(x["recv"])
            t = trend.setdefault(b, {"bucket": b, "new": 0, "closed": 0})
            t["new"] += 1
            if x["closed"]:
                t["closed"] += 1
    trend_series = [trend[k] for k in sorted(trend)][-8:]

    # 分布
    def cnt(field):
        d = {}
        for x in rich:
            k = x[field] if field != "bucket" else amount_bucket(x["amount"])
            d[k] = d.get(k, 0) + 1
        return d
    dist = {"type": cnt("ctype"), "amount_bucket": cnt("bucket"), "outcome": cnt("outcome")}

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": str(today),
        "window": {"start": str(window_start) if window_start else None,
                   "end": str(window_end) if window_end else None},
        "cumulative": {"total": total, "closed": closed, "open": open_,
                       "closure_rate": pct(closed / total) if total else None,
                       "total_amt": round(total_amt)},
        "period": period,
        "resolution_days": {"n": len(dur), "median": median(dur),
                            "mean": round(sum(dur) / len(dur), 1) if dur else None,
                            "p90": dur[int(len(dur) * 0.9)] if dur else None,
                            "max": dur[-1] if dur else None, "approx": True},
        "refund": {"refund_cases": len(refund_cases), "denom_cases": len(denom),
                   "case_rate_pct": pct(refund_case_rate),
                   "refund_amount": round(num_amt), "amount_denom": round(den_amt),
                   "amount_rate_pct": pct(refund_amt_rate), "approx": True},
        "repeat": {"repeat_cases": repeat_cases, "rate_pct": pct(repeat_rate),
                   "dup_extra": dup_extra, "kw_only": kw_only, "approx": True},
        "trend_weekly": trend_series,
        "dist": dist,
    }


def build_markdown(m):
    c = m["cumulative"]; rd = m["resolution_days"]; rf = m["refund"]; rp = m["repeat"]
    lines = ["■ 运营度量（确定性引擎 metrics.py）"]
    seg = f"累计 {c['total']}件｜已完结 {c['closed']}｜待办 {c['open']}｜总办结率 {c['closure_rate']}%"
    if m.get("period"):
        p = m["period"]
        seg += f"　本期新增 {p['new']}｜本期完结率 {p['closure_rate']}%"
    lines.append(seg)
    if rd["n"]:
        lines.append(f"办结时长(收到→定稿,近似)：中位 {rd['median']}天｜均值 {rd['mean']}天｜P90 {rd['p90']}天｜样本 {rd['n']}件")
    if rf["denom_cases"]:
        lines.append(f"退赔率(近似)：件数 {rf['case_rate_pct']}%（{rf['refund_cases']}/{rf['denom_cases']}）｜金额 {rf['amount_rate_pct']}%（¥{rf['refund_amount']}/¥{rf['amount_denom']}）")
    lines.append(f"二次投诉率(近似)：{rp['rate_pct']}%（{rp['repeat_cases']}件，含同手机/同人跨件重复+关键词）")
    tr = m["trend_weekly"]
    if tr:
        lines.append("近周趋势(新增/完结)：" + "，".join(f"{t['bucket']}:{t['new']}/{t['closed']}" for t in tr[-6:]))

    # 知识资产指标
    if m.get("knowledge"):
        k = m["knowledge"]
        lines.append("")
        lines.append("■ 知识资产（golden_corpus）")
        lines.append(f"口径库 {k['total_entries']}条｜总复用 {k['total_reuse']}次｜平均复用 {k['avg_reuse']}次/条")
        lines.append(f"覆盖投诉类型：{', '.join(f'{t}({n}条)' for t, n in sorted(k['type_coverage'].items(), key=lambda x:-x[1]))}")
        if k.get('lawyer_workload'):
            for lawyer, stats in k['lawyer_workload'].items():
                lines.append(f"  {lawyer}：入库{stats['入库数']}条 复用{stats['总复用']}次 关联{stats['总关联']}件")
        if k.get('avg_quality'):
            lines.append(f"平均质量评分：{k['avg_quality']}（{k['rated_count']}条有评分）")

    lines.append("（办结时长/退赔率/二次投诉率均为台账近似口径，定稿答复无独立时间字段，取跟进末次日期做代理）")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="台账快照：raw dws / hook / 投影列表")
    ap.add_argument("--corpus", help="口径库路径（可选，用于知识资产指标）")
    ap.add_argument("--today")
    ap.add_argument("--window-start")
    ap.add_argument("--window-end")
    ap.add_argument("--out", default="metrics.json")
    ap.add_argument("--md", action="store_true", help="额外打印可嵌周月报的中文摘要")
    args = ap.parse_args()

    records = ledger_io.load_records(args.data)
    today = to_date(args.today) if args.today else date.today()
    m = compute(records, today=today, window_start=args.window_start, window_end=args.window_end)

    # 知识资产指标
    if args.corpus:
        km = compute_knowledge_metrics(args.corpus)
        if km:
            m["knowledge"] = km

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print(f"[metrics] 已写 {args.out}")
    print(f"  累计{m['cumulative']['total']} 办结率{m['cumulative']['closure_rate']}% "
          f"办结时长中位{m['resolution_days']['median']}天 "
          f"退赔件{m['refund']['case_rate_pct']}%/额{m['refund']['amount_rate_pct']}% "
          f"二次{m['repeat']['rate_pct']}%")
    if m.get("knowledge"):
        k = m["knowledge"]
        print(f"  口径库{k['total_entries']}条 复用{k['total_reuse']}次 覆盖{len(k['type_coverage'])}类")
    if args.md:
        print("---")
        print(build_markdown(m))


if __name__ == "__main__":
    main()
