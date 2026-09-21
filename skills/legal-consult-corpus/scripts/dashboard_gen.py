#!/usr/bin/env python3
"""看板生成器 — 输入台账快照+度量数据，输出单文件 HTML 看板。"""

import argparse
import json
import os
import sys
from collections import Counter


def generate(tickets, output_path, metrics=None):
    """
    生成单文件 HTML 看板。

    Parameters
    ----------
    tickets : list[dict]
        台账记录，每条含 question_summary/domain/asker/ask_time/status/matched_corpus_id 等
    output_path : str
        输出 HTML 路径
    metrics : dict, optional
        metrics.py 的输出
    """
    total = len(tickets)
    domains = Counter(t.get("domain", "未分类") for t in tickets)
    askers = Counter(t.get("asker", "未知") for t in tickets)
    statuses = Counter(t.get("status", "待回复") for t in tickets)

    # ── KPI 带 ──
    m = metrics or {}
    c = m.get("cumulative", {})
    co = m.get("corpus", {})
    rt = m.get("response_time", {})

    def _kpi(num, lbl):
        return f'<div class="mk"><div class="n">{num}</div><div class="l">{lbl}</div></div>'

    cards = "".join([
        _kpi(c.get("total", total), "总咨询数"),
        _kpi(f"{c.get('reuse_rate', '—')}%" if c.get("reuse_rate") is not None else "—", "复用率"),
        _kpi(co.get("total_entries", 0), "口径库规模"),
        _kpi(f"{co.get('domain_coverage', '—')}%" if co.get("domain_coverage") is not None else "—", "领域覆盖率"),
        _kpi(f"{rt.get('median', '—')}天" if rt.get("median") is not None else "—", "响应时长(中位)"),
        _kpi(c.get("unique_askers", len(askers)), "提问人数"),
    ])

    # ── 领域分布柱状图 ──
    max_domain = max(domains.values()) if domains else 1
    domain_bars = "".join(
        f'<div class="bar-row"><div class="lbl">{k}</div>'
        f'<div class="track"><div class="fill" style="width:{v/max_domain*100}%"></div></div>'
        f'<div class="val">{v}</div></div>'
        for k, v in sorted(domains.items(), key=lambda x: -x[1])
    )

    # ── 提问人 Top10 ──
    max_asker = max(askers.values()) if askers else 1
    asker_bars = "".join(
        f'<div class="bar-row"><div class="lbl">{k}</div>'
        f'<div class="track"><div class="fill" style="width:{v/max_asker*100}%"></div></div>'
        f'<div class="val">{v}</div></div>'
        for k, v in askers.most_common(10)
    )

    # ── 状态分布 ──
    status_items = "".join(
        f'<span class="tag">{k} <b>{v}</b></span>'
        for k, v in sorted(statuses.items(), key=lambda x: -x[1])
    )

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>法律咨询口径看板</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f6fa;color:#2d3436;padding:20px}}
h1{{font-size:22px;font-weight:600;margin-bottom:16px;color:#2d3436}}
h2{{font-size:15px;font-weight:600;color:#636e72;margin:16px 0 8px}}
.mband{{background:#fff;border-radius:12px;padding:16px 20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.mgrid{{display:flex;gap:16px;flex-wrap:wrap}}
.mk{{text-align:center;min-width:100px;flex:1}}
.mk .n{{font-size:28px;font-weight:700;color:#0984e3}}
.mk .l{{font-size:12px;color:#636e72;margin-top:2px}}
.panel{{background:#fff;border-radius:12px;padding:16px 20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.bar-row{{display:flex;align-items:center;margin:4px 0}}
.bar-row .lbl{{width:80px;font-size:13px;color:#636e72;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bar-row .track{{flex:1;height:20px;background:#f0f0f0;border-radius:4px;margin:0 8px;overflow:hidden}}
.bar-row .fill{{height:100%;background:linear-gradient(90deg,#0984e3,#74b9ff);border-radius:4px;transition:width .3s}}
.bar-row .val{{width:36px;font-size:13px;font-weight:600;text-align:right;flex-shrink:0}}
.tag{{display:inline-block;padding:4px 10px;background:#dfe6e9;border-radius:12px;font-size:12px;margin:2px 4px}}
.tag b{{margin-left:4px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:768px){{.grid2{{grid-template-columns:1fr}}}}
.footer{{text-align:center;color:#b2bec3;font-size:11px;margin-top:20px}}
</style>
</head>
<body>
<h1>法律咨询口径看板</h1>

<div class="mband">
<h2>核心指标</h2>
<div class="mgrid">{cards}</div>
</div>

<div class="grid2">
<div class="panel">
<h2>领域分布</h2>
{domain_bars if domain_bars else '<p style="color:#b2bec3">暂无数据</p>'}
</div>
<div class="panel">
<h2>提问人 Top10</h2>
{asker_bars if asker_bars else '<p style="color:#b2bec3">暂无数据</p>'}
</div>
</div>

<div class="panel">
<h2>状态分布</h2>
<div>{status_items if status_items else '<span style="color:#b2bec3">暂无数据</span>'}</div>
</div>

<div class="footer">法律咨询口径固化平台 · 数据更新 {m.get("generated_at", "—")[:10] if m.get("generated_at") else "—"}</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[dashboard_gen] {total}件 → {output_path}", file=sys.stderr)
    return output_path


def main():
    ap = argparse.ArgumentParser(description="法律咨询口径看板生成器")
    ap.add_argument("--snap", required=True, help="台账快照 JSON")
    ap.add_argument("--html", required=True, help="输出 HTML 路径")
    ap.add_argument("--metrics", default=None, help="metrics.json 路径")
    args = ap.parse_args()

    tickets = json.load(open(args.snap, encoding="utf-8"))
    metrics = json.load(open(args.metrics, encoding="utf-8")) if args.metrics else None

    generate(tickets, args.html, metrics=metrics)


if __name__ == "__main__":
    main()
