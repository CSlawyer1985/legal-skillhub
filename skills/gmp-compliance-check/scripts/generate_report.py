#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GMP 合规体检报告生成器（零依赖，输出可打印 HTML）

用法:
  python generate_report.py --client <基线目录> --docs <待检资料...> --name "某药企" --out report.html
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review import parse_baseline, load_corpus, evaluate, ChineseArgumentParser  # noqa: E402


def _bar_color(pct):
    if pct >= 75:
        return "#2e7d32"
    if pct >= 50:
        return "#f9a825"
    return "#c62828"


def _risk_color(r):
    return {"高": "#c62828", "中": "#f9a825", "低": "#2e7d32"}.get(r, "#555")


def build_html(result, client_name):
    today = datetime.date.today().isoformat()
    overall = result["overall_score"]
    risk = result["overall_risk"]

    domain_rows = []
    for d in result["domains"]:
        pct = int(d["score"] * 100)
        domain_rows.append(
            f'<div class="domain">'
            f'<div class="domain-head"><span>{d["name"]}</span><span>{pct}%</span></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{_bar_color(pct)}"></div></div>'
            f"</div>"
        )

    rows = []
    for d in result["domains"]:
        for i in d["items"]:
            if i["status"] in ("缺失", "部分覆盖"):
                rows.append(
                    f"<tr><td>{d['name']}</td><td>{i['name']}</td>"
                    f'<td class="risk-{i["risk"]}">{i["risk"]}</td>'
                    f'<td>{i["status"]}</td><td>{i["advice"] or "—"}</td></tr>'
                )
    if not rows:
        rows.append('<tr><td colspan="5" class="ok">未发现缺失/部分覆盖项，合规覆盖良好。</td></tr>')

    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>GMP合规体检报告 - {client_name}</title>
<style>
  body {{ font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif; color:#222; max-width:920px; margin:24px auto; padding:0 20px; }}
  h1 {{ font-size:22px; margin-bottom:4px; }}
  h2 {{ font-size:17px; margin-top:28px; border-left:4px solid #1565c0; padding-left:8px; }}
  .meta {{ color:#666; font-size:13px; }}
  .score-box {{ display:flex; gap:28px; align-items:center; margin:18px 0; padding:18px 22px; background:#f5f7fa; border-radius:10px; }}
  .score-num {{ font-size:46px; font-weight:700; line-height:1; }}
  .badge {{ display:inline-block; padding:5px 14px; border-radius:20px; color:#fff; font-weight:600; font-size:14px; }}
  .domain {{ margin:12px 0; }}
  .domain-head {{ display:flex; justify-content:space-between; font-size:14px; margin-bottom:5px; }}
  .bar-track {{ background:#eee; border-radius:6px; height:14px; overflow:hidden; }}
  .bar-fill {{ height:100%; }}
  table {{ width:100%; border-collapse:collapse; margin-top:8px; font-size:13px; }}
  th, td {{ border:1px solid #ddd; padding:8px 10px; text-align:left; vertical-align:top; }}
  th {{ background:#f0f2f5; }}
  .risk-高 {{ color:#c62828; font-weight:700; }}
  .risk-中 {{ color:#f9a825; font-weight:700; }}
  .risk-低 {{ color:#2e7d32; }}
  .ok {{ text-align:center; color:#2e7d32; }}
  .btn {{ margin-top:22px; padding:10px 18px; background:#1565c0; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:14px; }}
  @media print {{ .no-print {{ display:none; }} body {{ margin:0; }} }}
</style></head>
<body>
  <h1>GMP 合规体检报告</h1>
  <div class="meta">对象：{client_name} ｜ 生成日期：{today}</div>
  <div class="score-box">
    <div><div class="score-num">{overall}</div><div class="meta">综合合规覆盖度（满分100）</div></div>
    <div><span class="badge" style="background:{_risk_color(risk)}">整体风险：{risk}</span></div>
  </div>
  <h2>各合规域覆盖度</h2>
  {''.join(domain_rows)}
  <h2>待整改项明细</h2>
  <table>
    <tr><th>合规域</th><th>检查项</th><th>风险</th><th>状态</th><th>整改建议</th></tr>
    {''.join(rows)}
  </table>
  <button class="btn no-print" onclick="window.print()">打印 / 另存为 PDF</button>
</body></html>"""
    return html


def main():
    ap = ChineseArgumentParser(description="GMP 合规体检报告生成器")
    ap.add_argument("--client", required=True, help="含 gmp_requirements.md 的基线目录")
    ap.add_argument("--docs", nargs="+", required=True, help="待检文档/目录")
    ap.add_argument("--name", default="客户", help="报告抬头名称")
    ap.add_argument("--out", default="gmp_report.html", help="输出 HTML 路径")
    args = ap.parse_args()

    client_dir = args.client
    if not os.path.isdir(client_dir):
        print(
            f"错误：基线目录不存在：{client_dir}\n"
            f"请确认 --client 指向一个【文件夹】，且其中包含 gmp_requirements.md。",
            file=sys.stderr,
        )
        sys.exit(2)
    baseline_path = os.path.join(client_dir, "gmp_requirements.md")
    if not os.path.isfile(baseline_path):
        print(f"错误：基线目录 {client_dir} 中未找到 gmp_requirements.md。", file=sys.stderr)
        sys.exit(2)
    try:
        domains = parse_baseline(baseline_path)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(2)

    missing_docs = [p for p in args.docs if not os.path.exists(p)]
    if missing_docs:
        print(f"提示：以下待检路径不存在，已忽略：{', '.join(missing_docs)}", file=sys.stderr)
    corpus = load_corpus(args.docs)
    if not corpus.strip():
        print("错误：待检资料为空（仅支持 .txt/.md；Word/PDF 需先导出纯文本）", file=sys.stderr)
        sys.exit(2)

    result = evaluate(domains, corpus)
    html = build_html(result, args.name)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"报告已生成：{args.out}（综合覆盖度 {result['overall_score']}，风险 {result['overall_risk']}）")


if __name__ == "__main__":
    main()
