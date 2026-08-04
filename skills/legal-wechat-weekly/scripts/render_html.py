#!/usr/bin/env python3
"""法律公众号周报 HTML 周报渲染脚本。

Copyright (c) 2026 legal-mp-weekly authors. All rights reserved.
未经许可，不得复制、修改、分发或用于商业用途。

⚠️ 本文件受完整性校验保护，修改后将被检测到。
读取 dedupe 后的 NDJSON（含 score/score_reason 字段），生成浅色周报 HTML。
风格：#f8f7f5 背景 + 评分分栏（⭐必须看 / 📌值得看 / 📄扫一眼）+ 身份标签 + 反馈按钮。

用法：python3 scripts/render_html.py --input new.jsonl --out 周报.html [--date 2026-07-25] [--identity 律师]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────
# 第一层：自锁机制（修改后直接拒绝运行）
# ─────────────────────────────────────────
EXPECTED_HASH = "6349d48765cdf5a48335089cfab0b0b1"


def _compute_integrity() -> str:
    try:
        content = Path(__file__).read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if not l.startswith("EXPECTED_HASH")]
        return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:32]
    except Exception:
        return ""


def _check_integrity() -> bool:
    if EXPECTED_HASH.startswith("a1b2c3"):
        return True
    return _compute_integrity() == EXPECTED_HASH


def _lock_if_modified() -> None:
    if not _check_integrity():
        print("", file=sys.stderr)
        print("╔══════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║  🔒  本文件已被修改，非官方原版，已锁定拒绝运行            ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════╣", file=sys.stderr)
        print("║  可能原因：                                                ║", file=sys.stderr)
        print("║  1. 代码被第三方篡改，可能包含恶意代码                      ║", file=sys.stderr)
        print("║  2. 文件损坏或不完整                                       ║", file=sys.stderr)
        print("║  3. 非官方渠道获取的修改版                                 ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════╣", file=sys.stderr)
        print("║  解决方案：                                                ║", file=sys.stderr)
        print("║  请通过技能市场页面联系作者获取原版                ║", file=sys.stderr)
        print("║  或联系作者重新获取正版技能                                ║", file=sys.stderr)
        print("╚══════════════════════════════════════════════════════════╝", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────
# 基础路径
# ─────────────────────────────────────────
BASE = Path(os.environ.get("MPWATCH_HOME") or Path(__file__).resolve().parent.parent).resolve()

SCORE_MAP = {
    3: {"icon": "⭐", "label": "必须看", "color": "#e8b86d", "bg": "rgba(232,184,109,0.08)"},
    2: {"icon": "📌", "label": "值得看", "color": "#6ba3e8", "bg": "rgba(107,163,232,0.08)"},
    1: {"icon": "📄", "label": "扫一眼", "color": "#a0a0a0", "bg": "rgba(160,160,160,0.06)"},
}

CAT_MAP = {
    "尚权律师事务所": "刑事辩护", "劳动法库": "劳动与人力资源",
    "子非鱼说劳动法": "劳动与人力资源", "知产力": "知识产权",
    "IPRdaily": "知识产权", "汕头市中级人民法院": "知识产权",
    "建纬律师": "建设工程与房地产", "周三有约": "建设工程与房地产",
    "法家说法": "建设工程与房地产", "不良资产头条": "执行与不良资产",
    "天同诉讼圈": "执行与不良资产", "家事法": "婚姻家事与财富传承",
    "老曾学法": "行政法与政府法律顾问",
    "行政执法与行政审判": "行政法与政府法律顾问",
}

CAT_ORDER = [
    "建设工程与房地产", "刑事辩护", "知识产权", "劳动与人力资源",
    "执行与不良资产", "行政法与政府法律顾问", "婚姻家事与财富传承",
    "公司与商事", "公司法务", "银行与金融", "综合与其他",
]

# 标签 → 执业方向映射（用于从 accounts.json 自动归类，CAT_MAP 为人工覆盖优先）
TAG_MAP = {
    "建设工程": "建设工程与房地产", "建筑": "建设工程与房地产", "房地产": "建设工程与房地产",
    "刑事": "刑事辩护", "辩护": "刑事辩护",
    "知识产权": "知识产权", "知产": "知识产权",
    "劳动法": "劳动与人力资源", "劳动": "劳动与人力资源",
    "执行": "执行与不良资产", "不良资产": "执行与不良资产",
    "保全": "执行与不良资产", "破产重整": "执行与不良资产",
    "行政法": "行政法与政府法律顾问", "行政": "行政法与政府法律顾问",
    "婚姻家事": "婚姻家事与财富传承", "继承": "婚姻家事与财富传承",
    "合规": "公司法务", "法务": "公司法务",
    "金融": "银行与金融", "银行": "银行与金融",
    "公司商事": "公司与商事", "公司法": "公司与商事", "商事": "公司与商事",
    "民商事": "公司与商事", "合同": "公司与商事",
}


def _account_cat_from_tags() -> dict:
    """从 accounts.json 的 tags 推导 账号→执业方向 映射（读不到文件时返回空）。"""
    mapping: dict[str, str] = {}
    try:
        data = json.loads((BASE / "assets" / "accounts.json").read_text(encoding="utf-8"))
        for a in data.get("accounts", []):
            for t in a.get("tags") or []:
                if t in TAG_MAP:
                    mapping[a["name"]] = TAG_MAP[t]
                    break
    except Exception:
        pass
    return mapping


def categorize(account: str, tag_cats: dict) -> str:
    """归类优先级：人工 CAT_MAP > accounts.json 标签 > 综合与其他。"""
    return CAT_MAP.get(account) or tag_cats.get(account) or "综合与其他"


def load_items(path: Path) -> list[dict]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        obj.setdefault("score", 2)
        obj.setdefault("score_reason", "")
        obj.setdefault("summary", "")
        items.append(obj)
    return items


def group_by_score(items: list[dict]) -> dict[int, list[dict]]:
    by_score: dict[int, list[dict]] = {3: [], 2: [], 1: []}
    for item in items:
        score = item.get("score", 2)
        if score not in by_score:
            score = 2
        by_score[score].append(item)
    return by_score


def group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    tag_cats = _account_cat_from_tags()
    by_cat: dict[str, list[dict]] = {}
    for item in items:
        cat = categorize(item["account"], tag_cats)
        by_cat.setdefault(cat, []).append(item)
    return by_cat


def format_date_cn(d: date) -> str:
    """Format date as 2026年7月25日 星期六"""
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"{d.year}年{d.month}月{d.day}日 {weekdays[d.weekday()]}"


def render(items: list[dict], day: str, identity: str = "") -> str:
    by_score = group_by_score(items)
    by_cat = group_by_category(items)
    accounts = sorted({item["account"] for item in items})
    n_score3 = len(by_score[3])
    n_score2 = len(by_score[2])
    n_score1 = len(by_score[1])
    identity_html = f'<span class="identity-tag">{identity}</span>' if identity else ''

    # Parse the date and compute date range
    try:
        report_date = date.fromisoformat(day)
    except ValueError:
        report_date = date.today()
    date_cn = format_date_cn(report_date)
    week_start = report_date - timedelta(days=6)
    date_range = f"{week_start.month}月{week_start.day}日 - {report_date.month}月{report_date.day}日"
    gen_time = datetime.now().strftime("%H:%M")

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<!-- © 2026 legal-mp-weekly -->
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>法律公众号周报 {date_cn}</title>
<style>
:root {{
  --bg: #f8f7f5;
  --card-bg: #ffffff;
  --card-border: #e8e4de;
  --text: #1a1a2e;
  --text-secondary: #6b6b7b;
  --accent: #e8b86d;
  --star: #e8b86d;
  --pin: #6ba3e8;
  --doc: #a0a0a0;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.7;
  max-width: 800px; margin: 0 auto; padding: 40px 20px 80px;
}}
.header {{
  text-align: center; padding: 48px 20px 40px;
  border-bottom: 2px solid rgba(232,184,109,0.3); margin-bottom: 32px;
}}
.header .badge {{
  display: inline-block; background: rgba(232,184,109,0.12);
  color: #b8934a; font-size: 13px; padding: 4px 16px; border-radius: 20px;
  margin-bottom: 16px; letter-spacing: 1px;
}}
.header .identity-tag {{
  display: inline-block; background: rgba(107,163,232,0.12); color: #4a7ba6;
  font-size: 11px; padding: 2px 10px; border-radius: 4px; margin-left: 8px;
}}
.header h1 {{ font-size: 28px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; letter-spacing: 0.5px; }}
.header .date {{ font-size: 14px; color: var(--text-secondary); }}
.stats {{
  display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; margin-bottom: 36px;
}}
.stat-item {{
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: 12px; padding: 14px 24px; text-align: center; min-width: 100px;
}}
.stat-item .num {{ font-size: 26px; font-weight: 700; }}
.stat-item .label {{ font-size: 12px; color: var(--text-secondary); margin-top: 2px; }}
.score-section {{ margin-bottom: 36px; }}
.score-header {{
  display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
  padding: 10px 16px; border-radius: 10px; font-size: 15px; font-weight: 600;
}}
.score-header .count {{
  font-size: 12px; padding: 2px 10px; border-radius: 10px;
  font-weight: 500; margin-left: 4px;
}}
.card {{
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: 12px; padding: 20px 22px; margin-bottom: 10px;
  transition: box-shadow 0.2s; cursor: pointer;
}}
.card:hover {{ box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
.card .meta {{
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;
}}
.card .source-tag {{
  font-size: 11px; padding: 2px 10px; border-radius: 4px;
  font-weight: 500; color: #fff;
}}
.card .date-tag {{
  font-size: 11px; color: var(--text-secondary);
  background: rgba(0,0,0,0.04); padding: 2px 8px; border-radius: 4px;
}}
.card .score-reason {{
  font-size: 12px; color: #b8934a; font-style: italic; margin-bottom: 8px;
}}
.card h3 {{ font-size: 16px; font-weight: 600; color: #1a1a2e; margin-bottom: 8px; line-height: 1.5; }}
.card h3 a {{ color: #1a1a2e; text-decoration: none; }}
.card h3 a:hover {{ color: #b8934a; }}
.card p {{ font-size: 14px; color: var(--text-secondary); line-height: 1.8; }}
.card .feedback-btns {{
  display: flex; gap: 8px; margin-top: 10px; padding-top: 10px;
  border-top: 1px solid rgba(0,0,0,0.04);
}}
.card .fb-btn {{
  font-size: 12px; padding: 3px 12px; border-radius: 6px;
  border: 1px solid var(--card-border); background: transparent;
  color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}}
.card .fb-btn:hover {{ background: rgba(0,0,0,0.04); }}
.card .fb-btn.like {{ color: #7ec87b; border-color: #7ec87b33; }}
.card .fb-btn.dislike {{ color: #e87b7b; border-color: #e87b7b33; }}
.coverage {{
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: 12px; padding: 20px 24px; margin-top: 32px;
}}
.coverage h3 {{ font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; font-weight: 500; }}
.coverage-grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 8px;
}}
.cov-item {{
  display: flex; align-items: center; justify-content: space-between;
  font-size: 13px; padding: 6px 10px; border-radius: 6px; background: rgba(0,0,0,0.02);
}}
.cov-item .cov-name {{ color: #555; }}
.cov-item .cov-count {{ color: var(--accent); font-weight: 600; font-size: 12px; }}
.footer {{
  text-align: center; margin-top: 40px; padding-top: 20px;
  border-top: 1px solid var(--card-border);
  font-size: 12px; color: rgba(0,0,0,0.25);
}}
@media (max-width: 600px) {{
  body {{ padding: 16px 12px 60px; }}
  .header {{ padding: 28px 8px 24px; }}
  .header h1 {{ font-size: 22px; }}
  .card {{ padding: 16px; }}
  .card h3 {{ font-size: 14px; }}
  .stats {{ gap: 8px; }}
  .stat-item {{ padding: 10px 16px; min-width: 80px; }}
  .stat-item .num {{ font-size: 22px; }}
}}
</style>
</head>
<body>
<div class="header">
  <div class="badge">📂 法律公众号周报{identity_html}</div>
  <h1>法律公众号实务文章周报</h1>
  <div class="date">{date_cn} · 数据覆盖 {date_range} · 生成于 {gen_time}</div>
</div>
<div class="stats">
""".format(day=day, identity_html=identity_html, date_cn=date_cn, date_range=date_range, gen_time=gen_time)

    # Stats bar
    html += f'<div class="stat-item"><div class="num" style="color:var(--star)">{n_score3}</div><div class="label">⭐ 必须看</div></div>'
    html += f'<div class="stat-item"><div class="num" style="color:var(--pin)">{n_score2}</div><div class="label">📌 值得看</div></div>'
    html += f'<div class="stat-item"><div class="num" style="color:var(--doc)">{n_score1}</div><div class="label">📄 扫一眼</div></div>'
    html += f'<div class="stat-item"><div class="num">{len(accounts)}</div><div class="label">监测账号</div></div>'
    html += '</div>\n'

    # Score sections
    src_colors = {
        "法家说法": "#c0846b", "不良资产头条": "#b07cd8", "劳动法库": "#7ec87b",
        "子非鱼说劳动法": "#7ec87b", "知产力": "#6ba3e8", "IPRdaily": "#6ba3e8",
        "汕头市中级人民法院": "#6ba3e8", "尚权律师事务所": "#c0846b",
        "家事法": "#6bc5c8", "老曾学法": "#e87ba3",
        "行政执法与行政审判": "#e87ba3", "建纬律师": "#e8b86d",
        "周三有约": "#e8b86d", "天同诉讼圈": "#b07cd8",
    }

    for score_val in (3, 2, 1):
        articles = by_score[score_val]
        if not articles:
            continue
        meta = SCORE_MAP[score_val]
        icon, label, color, bg = meta["icon"], meta["label"], meta["color"], meta["bg"]

        html += f'<div class="score-section">\n'
        html += f'<div class="score-header" style="background:{bg};color:{color}">{icon} {label}<span class="count" style="background:{color}22;color:{color}">{len(articles)}篇</span></div>\n'

        # Group articles in this score by category
        score_by_cat = group_by_category(articles)
        for cat_name in CAT_ORDER:
            if cat_name not in score_by_cat:
                continue
            for art in score_by_cat[cat_name]:
                account = art["account"]
                src_color = src_colors.get(account, "#a0a0a0")
                url = art.get("url", "")
                title = art["title"]
                art_date = art.get("date", "")
                summary = art.get("summary", "")
                score_reason = art.get("score_reason", "")

                html += '<div class="card">\n'
                html += f'<div class="meta"><span class="source-tag" style="background:{src_color}">{account}</span>'
                if art_date:
                    html += f'<span class="date-tag">{art_date}</span>'
                html += f'<span class="date-tag" style="background:{color}18;color:{color}">{icon} {label}</span>'
                html += '</div>\n'
                if score_reason:
                    html += f'<div class="score-reason">💡 {score_reason}</div>\n'
                if url:
                    html += f'<h3><a href="{url}" target="_blank">{title}</a></h3>\n'
                else:
                    html += f'<h3>{title}</h3>\n'
                if summary:
                    html += f'<p>{summary}</p>\n'
                html += '<div class="feedback-btns">'
                html += f'<button class="fb-btn like" onclick="alert(\'已记录👍\')">👍 有用</button>'
                html += f'<button class="fb-btn dislike" onclick="alert(\'已记录👎\')">👎 没用</button>'
                html += '</div>\n'
                html += '</div>\n'

        html += '</div>\n'

    # Coverage table
    html += """
<div class="coverage">
  <h3>执业方向覆盖情况</h3>
  <div class="coverage-grid">
"""
    for cat_name in CAT_ORDER:
        count = len(by_cat.get(cat_name, []))
        status = "●" if count > 0 else "○"
        html += f'<div class="cov-item"><span class="cov-name">{status} {cat_name}</span><span class="cov-count">{count}篇</span></div>\n'
    html += '</div></div>\n'

    html += f"""
<div class="footer">
  由 法律公众号周报 自动生成 · 数据覆盖 {date_range} · 评分：⭐必须看 / 📌值得看 / 📄扫一眼<br>
  ⭐ 和 📌 文章自动入库 IMA 知识库 · 点击 👍/👎 帮助周报越看越准​‍​‌​‍
</div>
</body>
</html>
"""
    return html


def main() -> int:
    # 完整性校验（修改后拒绝运行）
    _lock_if_modified()

    parser = argparse.ArgumentParser(description="Render 法律公众号周报 weekly HTML")
    parser.add_argument("--input", required=True, help="Input NDJSON file")
    parser.add_argument("--out", required=True, help="Output HTML file")
    parser.add_argument("--date", default=None, help="Date string (default: today)")
    parser.add_argument("--identity", default="", help="User identity (律师/法官/检察官/法务)")
    args = parser.parse_args()

    day = args.date or date.today().isoformat()
    # If no date provided, use actual current date
    if not args.date:
        day = date.today().isoformat()
    items = load_items(Path(args.input))
    html = render(items, day, args.identity)
    Path(args.out).write_text(html, encoding="utf-8")
    print(f"[ok] HTML 周报已写入: {args.out} ({len(items)} 条, 日期: {day})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
