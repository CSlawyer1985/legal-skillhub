#!/usr/bin/env python3
"""
广告公司 AI 合规审查 —— 批量合规风险报告生成器（零依赖，纯标准库）

用法：
  python generate_report.py --client <客户目录> --docs <历史文案目录/文件> \
      --name "客户名" --out report.html [--no-line-mode] [--top 10]

功能：
  - 扫描客户历史文案（默认每行一条；--no-line-mode 则整文件为一条）
  - 复用 review.py 的 load_client_terms / scan 做命中扫描
  - 汇总风险分布、违规类型、高频违规词
  - 生成自包含 HTML 报告（内联 CSS + SVG 图表 + 打印/另存 PDF 按钮）
  - 报告可直接邮件发给客户，或浏览器打开后「打印 → 另存为 PDF」
"""
import os
import sys
import html
import math
import argparse
from datetime import datetime
from pathlib import Path

# 复用审查核心
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review import load_client_terms, scan, validate_client_dir  # noqa: E402

SEV_COLOR = {"高": "#E24B4A", "中": "#EF9F27", "低": "#639922", "通过": "#9AA7B8", "异常": "#B8860B"}
CAT_COLOR = ["#378ADD", "#1D9E75", "#BA7517", "#993556", "#534AB7", "#0F6E56"]


def read_docs(docs_path, line_mode):
    docs = []  # (source, text)
    p = Path(docs_path)
    files = [p] if p.is_file() else sorted(p.glob("*.txt")) + sorted(p.glob("*.md"))
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if line_mode:
            for ln in text.splitlines():
                ln = ln.strip()
                if ln:
                    docs.append((f.name, ln))
        else:
            t = text.strip()
            if t:
                docs.append((f.name, t))
    return docs


def analyze(docs, terms):
    results = []
    level_count = {"高": 0, "中": 0, "低": 0, "通过": 0, "异常": 0}
    cat_count = {}
    term_count = {}
    for src, text in docs:
        # 单条文案数据异常（编码/超长/意外字符）不应拖垮整份报告
        try:
            vios, level = scan(text, terms)
        except Exception as e:
            results.append({"src": src, "text": text, "level": "异常",
                            "vios": [], "error": f"该条文案解析失败：{esc(str(e))[:160]}"})
            level_count["异常"] += 1
            continue
        level_count[level] = level_count.get(level, 0) + 1
        for v in vios:
            cat_count[v["category"]] = cat_count.get(v["category"], 0) + 1
            term_count[v["term"]] = term_count.get(v["term"], 0) + 1
        results.append({"src": src, "text": text, "level": level, "vios": vios})
    return results, level_count, cat_count, term_count


def esc(s):
    return html.escape(str(s))


def pie_chart(level_count):
    total = sum(level_count.values())
    if total == 0:
        return "<p>暂无数据</p>"
    order = ["高", "中", "低", "通过", "异常"]
    slices = [(lv, level_count[lv]) for lv in order if level_count[lv] > 0]
    cx, cy, r = 90, 90, 70
    parts = []
    start = -90.0
    for lv, val in slices:
        frac = val / total
        end = start + frac * 360
        large = 1 if (end - start) > 180 else 0
        x1 = cx + r * math.cos(math.radians(start))
        y1 = cy + r * math.sin(math.radians(start))
        x2 = cx + r * math.cos(math.radians(end))
        y2 = cy + r * math.sin(math.radians(end))
        d = f"M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} Z"
        parts.append(f'<path d="{d}" fill="{SEV_COLOR[lv]}" stroke="#fff" stroke-width="1"/>')
        mid = math.radians((start + end) / 2)
        lx = cx + (r + 18) * math.cos(mid)
        ly = cy + (r + 18) * math.sin(mid)
        parts.append(f'<text x="{lx:.0f}" y="{ly:.0f}" font-size="11" fill="{SEV_COLOR[lv]}" '
                     f'text-anchor="middle" dominant-baseline="central">{esc(lv)} {val/total*100:.0f}%</text>')
        start = end
    return (f'<svg viewBox="0 0 200 185" width="200" height="185" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "</svg>")


def bar_chart(cat_count, top=6):
    items = sorted(cat_count.items(), key=lambda x: -x[1])[:top]
    if not items:
        return "<p style='color:#5f5e5a;'>未检出具体违规类型</p>"
    maxv = max(v for _, v in items)
    rows = []
    for i, (cat, val) in enumerate(items):
        w = val / maxv * 100
        color = CAT_COLOR[i % len(CAT_COLOR)]
        rows.append(
            f'<div style="display:flex;align-items:center;margin:7px 0;">'
            f'<div style="width:130px;font-size:12px;color:#36506e;">{esc(cat)}</div>'
            f'<div style="flex:1;background:#eef1f5;border-radius:4px;height:16px;overflow:hidden;">'
            f'<div style="width:{w:.0f}%;background:{color};height:16px;border-radius:4px;"></div></div>'
            f'<div style="width:34px;text-align:right;font-size:12px;color:#5f5e5a;">{val}</div>'
            f'</div>'
        )
    return "<div>" + "".join(rows) + "</div>"


def build_html(name, results, level_count, cat_count, term_count, top):
    total = len(results)
    hit = sum(1 for r in results if r["level"] != "通过")
    hit_rate = f"{hit / total * 100:.0f}%" if total else "0%"
    high = level_count.get("高", 0)
    today = datetime.now().strftime("%Y-%m-%d")
    top_terms = sorted(term_count.items(), key=lambda x: -x[1])[:top]
    anomaly = level_count.get("异常", 0)
    anomaly_banner = (
        f'<div style="padding:8px 36px 0;">'
        f'<p style="background:#fbf3e2;border-left:4px solid #B8860B;padding:10px 14px;border-radius:6px;'
        f'font-size:13px;color:#7a5b16;margin:0;">'
        f'⚠️ 有 {anomaly} 条文案因内容异常（如编码损坏、长度超限）未能完成扫描，已在下方明细中标注，'
        f'建议单独复核或重新提交这部分文案。</p></div>'
    ) if anomaly else ""
    top_html = " ".join(
        f'<span style="display:inline-block;background:#fcebeb;color:#a32d2d;border:1px solid #f7c1c1;'
        f'border-radius:12px;padding:3px 10px;margin:3px;font-size:12px;">{esc(t)} ×{c}</span>'
        for t, c in top_terms
    ) or "<span style='color:#5f5e5a;'>无</span>"

    rows = []
    for r in results:
        preview = r["text"][:64] + ("…" if len(r["text"]) > 64 else "")
        if r.get("error"):
            vlist = f'<span style="color:#B8860B;">{esc(r["error"])}</span>'
        else:
            vlist = "、".join(f'{v["term"]}({v["category"]})' for v in r["vios"]) or "—"
        rows.append(
            f'<tr>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;color:#5f5e5a;font-size:12px;white-space:nowrap;">{esc(r["src"])}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;">{esc(preview)}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;white-space:nowrap;">'
            f'<span style="color:{SEV_COLOR[r["level"]]};font-weight:600;">{r["level"]}</span></td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;color:#5f5e5a;font-size:12px;">{vlist}</td>'
            f'</tr>'
        )
    rows_html = "".join(rows)

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(name)} · 广告文案合规风险体检报告</title></head>
<body style="margin:0;background:#f4f6f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1f2d3d;">
<div style="max-width:860px;margin:0 auto;background:#fff;">
  <div style="height:8px;background:linear-gradient(90deg,#378ADD,#1D9E75);"></div>
  <div style="padding:28px 36px 8px;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
      <div>
        <div style="font-size:13px;color:#378ADD;font-weight:600;">AI 合规体检 · COMPLIANCE CHECK</div>
        <h1 style="margin:6px 0 2px;font-size:22px;">广告文案合规风险体检报告</h1>
        <div style="color:#5f5e5a;font-size:13px;">客户：{esc(name)}　|　生成日期：{today}</div>
      </div>
      <button onclick="window.print()" style="border:1px solid #378ADD;background:#378ADD;color:#fff;
        border-radius:8px;padding:9px 16px;font-size:13px;cursor:pointer;">打印 / 另存为 PDF</button>
    </div>
  </div>

  <div style="padding:8px 36px 4px;">
    <p style="background:#eef4fd;border-left:4px solid #378ADD;padding:10px 14px;border-radius:6px;
      font-size:13px;color:#36506e;margin:14px 0;">
      本报告基于《广告法》通用红线与贵司品牌调性，对历史文案做自动体检，旨在帮助团队在对外发布前
      识别合规风险、降低被处罚 / 被下架的概率。AI 辅助审查不替代人工终审。
    </p>
  </div>

  {anomaly_banner}
  <div style="padding:10px 36px;display:flex;gap:14px;flex-wrap:wrap;">
    <div style="flex:1;min-width:150px;background:#f7f9fc;border:1px solid #e6ebf2;border-radius:12px;padding:16px;">
      <div style="font-size:12px;color:#5f5e5a;">扫描文案</div>
      <div style="font-size:26px;font-weight:700;">{total}</div>
      <div style="font-size:12px;color:#5f5e5a;">条</div>
    </div>
    <div style="flex:1;min-width:150px;background:#f7f9fc;border:1px solid #e6ebf2;border-radius:12px;padding:16px;">
      <div style="font-size:12px;color:#5f5e5a;">命中风险</div>
      <div style="font-size:26px;font-weight:700;color:#E24B4A;">{hit}</div>
      <div style="font-size:12px;color:#5f5e5a;">占比 {hit_rate}</div>
    </div>
    <div style="flex:1;min-width:150px;background:#f7f9fc;border:1px solid #e6ebf2;border-radius:12px;padding:16px;">
      <div style="font-size:12px;color:#5f5e5a;">高风险项</div>
      <div style="font-size:26px;font-weight:700;color:#E24B4A;">{high}</div>
      <div style="font-size:12px;color:#5f5e5a;">需优先处理</div>
    </div>
  </div>

  <div style="padding:10px 36px;display:flex;gap:24px;flex-wrap:wrap;align-items:center;">
    <div style="flex:0 0 200px;">{pie_chart(level_count)}</div>
    <div style="flex:1;min-width:280px;">
      <div style="font-size:14px;font-weight:600;margin-bottom:4px;">违规类型分布</div>
      {bar_chart(cat_count)}
    </div>
  </div>

  <div style="padding:10px 36px;">
    <div style="font-size:14px;font-weight:600;margin:10px 0 6px;">高频违规词 Top {len(top_terms)}</div>
    <div>{top_html}</div>
  </div>

  <div style="padding:10px 36px 20px;">
    <div style="font-size:14px;font-weight:600;margin:12px 0 8px;">文案明细</div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead><tr style="background:#f7f9fc;text-align:left;color:#36506e;">
        <th style="padding:8px;border-bottom:2px solid #e6ebf2;">来源</th>
        <th style="padding:8px;border-bottom:2px solid #e6ebf2;">文案（节选）</th>
        <th style="padding:8px;border-bottom:2px solid #e6ebf2;">风险</th>
        <th style="padding:8px;border-bottom:2px solid #e6ebf2;">主要违规</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>

  <div style="padding:14px 36px 30px;background:#f7f9fc;border-top:1px solid #e6ebf2;">
    <div style="font-size:14px;font-weight:600;margin-bottom:6px;">下一步建议</div>
    <ul style="margin:6px 0;padding-left:20px;font-size:13px;color:#36506e;line-height:1.8;">
      <li>优先清理高风险文案（绝对化用语、医疗功效暗示），避免上线后被处罚或下架。</li>
      <li>将本次检出的高频违规词沉淀为贵司专属违禁词库，供团队日常自查。</li>
      <li>可接入「AI 合规闸」——发布前自动比对品牌红线与广告法，把风险挡在上线之前。</li>
    </ul>
    <div style="font-size:11px;color:#9aa7b8;margin-top:10px;">
      本报告由 AI 合规体检工具自动生成 · 仅供内部参考，不构成法律意见。
    </div>
  </div>
</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="广告合规风险报告生成器")
    ap.add_argument("--client", required=True, help="客户资料目录（含 banned_words.md / brand.md）")
    ap.add_argument("--docs", required=True, help="历史文案目录或文件（默认每行一条）")
    ap.add_argument("--name", default="贵司", help="客户名称（用于报告抬头）")
    ap.add_argument("--out", default="report.html", help="输出 HTML 路径")
    ap.add_argument("--no-line-mode", action="store_true", help="整文件作为一条文案（默认按行拆分）")
    ap.add_argument("--top", type=int, default=10, help="高频违规词显示条数")
    args = ap.parse_args()

    ok, msg = validate_client_dir(args.client)
    if not ok:
        print("【错误】" + msg, file=sys.stderr)
        sys.exit(2)
    if msg:
        print(msg, file=sys.stderr)
    terms = load_client_terms(args.client)
    docs = read_docs(args.docs, not args.no_line_mode)
    if not docs:
        print("未读取到任何文案，请检查 --docs 路径。")
        sys.exit(1)
    results, level_count, cat_count, term_count = analyze(docs, terms)

    html_out = build_html(args.name, results, level_count, cat_count, term_count, args.top)
    Path(args.out).write_text(html_out, encoding="utf-8")

    total = len(results)
    hit = sum(1 for r in results if r["level"] != "通过")
    print(f"扫描 {total} 条文案，命中风险 {hit} 条，高风险 {level_count.get('高', 0)} 条")
    print(f"报告已生成：{args.out}")


if __name__ == "__main__":
    main()
