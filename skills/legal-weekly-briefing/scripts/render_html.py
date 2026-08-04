#!/usr/bin/env python3
"""周报 HTML 渲染器 —— 将评分流水线产出的数据渲染为可交互的 HTML 周报页面。

用法:
    # 方式 A：从 pipeline 输出的 JSON 渲染
    python3 scripts/render_html.py run-report.json

    # 方式 B：从 demo.py 输出的周报 MD 渲染（提取标题和 URL）
    python3 scripts/render_html.py 周报_demo_2026-07-11.md

    # 方式 C：管道模式（从 stdin 读 JSON）
    cat scored_data.json | python3 scripts/render_html.py --stdin

输入数据格式（JSON 数组）:
[
  {
    "title": "文章标题",
    "url": "https://mp.weixin.qq.com/s/...",
    "category": "legal",            // "legal" 或 "ai-legal"
    "source": "山东高法",
    "source_category": "法院·以案说法",
    "date": "2026.07",
    "score": 9.0,
    "tags": ["婚姻家事", "夫妻债务"],
    "abstract": "文章摘要...",
    "recommend": "推荐理由..."
  },
  ...
]

输出: 周报_<日期>.html —— 独立可打开的 HTML 文件（含内联 CSS/JS）
"""
import json
import sys
import os
import re
import html as _html
from datetime import date
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>法律周报 · {report_date}</title>
<style>
  :root {{
    --bg: #f8f7f5;
    --header-bg: #1a1a2e;
    --header-text: rgba(255,255,255,0.92);
    --card-bg: #ffffff;
    --text: #2d2d3a;
    --text-secondary: #5f5f6e;
    --text-tertiary: #8b8b9a;
    --accent-legal: #7c5e3e;
    --accent-ai: #3b6cb4;
    --score-high-bg: #e8f0e8;
    --score-high-text: #2d5a27;
    --score-mid-bg: #f4efe8;
    --score-mid-text: #8b6914;
    --tag-bg: #f0f0f5;
    --tag-text: #58586e;
    --border: #e8e8ec;
    --favorite-outline: #c0c0cc;
    --favorite-active: #d1523f;
    --divider: #e8e8ec;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.75;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
  }}
  .header {{
    background: var(--header-bg);
    padding: 48px 24px 40px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}
  .header .week-label {{
    font-size: 12px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
    margin-bottom: 12px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    color: var(--header-text);
    letter-spacing: 0.02em;
    margin-bottom: 6px;
  }}
  .header .date-range {{
    font-size: 14px;
    color: rgba(255,255,255,0.55);
    font-weight: 400;
  }}
  .header .stats-row {{
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-top: 24px;
    flex-wrap: wrap;
  }}
  .header .stat {{ text-align: center; }}
  .header .stat-num {{
    font-size: 22px;
    font-weight: 700;
    color: rgba(255,255,255,0.9);
    font-variant-numeric: tabular-nums;
  }}
  .header .stat-label {{
    font-size: 11px;
    color: rgba(255,255,255,0.4);
    letter-spacing: 0.08em;
    margin-top: 2px;
  }}
  .container {{
    max-width: 760px;
    margin: 0 auto;
    padding: 40px 24px 60px;
  }}
  .section {{ margin-bottom: 48px; }}
  .section-head {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--divider);
  }}
  .section-head.ai {{ border-color: var(--accent-ai); }}
  .section-head.legal {{ border-color: var(--accent-legal); }}
  .section-head .section-num {{
    font-size: 22px;
    font-weight: 700;
    color: var(--text-tertiary);
    font-variant-numeric: tabular-nums;
  }}
  .section-head .section-title {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
  }}
  .section-head.radar {{ border-color: var(--divider); }}
  .section-head .section-en {{
    font-size: 12px;
    color: var(--text-tertiary);
    margin-left: auto;
  }}
  /* 雷达区（其他领域速览）：轻量列表，不抢精读区视觉权重 */
  .radar-list {{ list-style: none; padding: 0; margin: 0; }}
  .radar-item {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 10px 4px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
  }}
  .radar-item:last-child {{ border-bottom: none; }}
  .radar-score {{
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: var(--text-tertiary);
    font-size: 13px;
    min-width: 30px;
  }}
  .radar-title a {{ color: var(--text); text-decoration: none; }}
  .radar-title a:hover {{ color: var(--accent-legal); }}
  .radar-source {{ margin-left: auto; flex-shrink: 0; font-size: 12px; color: var(--text-tertiary); }}
  .radar-note {{ font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px; }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 16px;
    transition: border-color 0.15s ease;
    position: relative;
  }}
  .card:hover {{ border-color: #c8c8d4; }}
  .card-top {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 10px;
  }}
  .score-badge {{
    flex-shrink: 0;
    min-width: 48px;
    text-align: center;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 700;
    line-height: 1.3;
    font-variant-numeric: tabular-nums;
  }}
  .score-high {{ background: var(--score-high-bg); color: var(--score-high-text); }}
  .score-mid  {{ background: var(--score-mid-bg); color: var(--score-mid-text); }}
  .card-title {{
    flex: 1;
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.5;
  }}
  .card-title a {{
    color: inherit;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.15s;
  }}
  .card-title a:hover {{ border-color: var(--accent-ai); }}
  .fav-btn {{
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border: 1.5px solid var(--favorite-outline);
    border-radius: 50%;
    background: transparent;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: var(--favorite-outline);
    transition: all 0.2s;
    margin-top: 2px;
  }}
  .fav-btn:hover {{ border-color: var(--favorite-active); color: var(--favorite-active); }}
  .fav-btn.active {{ border-color: var(--favorite-active); background: var(--favorite-active); color: #fff; }}
  .source-line {{
    font-size: 12px;
    color: var(--text-tertiary);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .source-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-legal);
    flex-shrink: 0;
  }}
  .source-dot.ai {{ background: var(--accent-ai); }}
  .source-category {{
    font-weight: 500;
    color: var(--text-secondary);
  }}
  .source-name {{ color: var(--text-tertiary); }}
  .tags-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }}
  .tag {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    background: var(--tag-bg);
    color: var(--tag-text);
    letter-spacing: 0.02em;
  }}
  .abstract {{
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.8;
    margin-bottom: 12px;
  }}
  .recommend {{
    background: #f9f8f6;
    border-left: 3px solid var(--accent-legal);
    padding: 10px 14px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.65;
    margin-bottom: 12px;
    border-radius: 0 4px 4px 0;
  }}
  .recommend.ai {{ border-color: var(--accent-ai); }}
  .recommend-label {{
    font-size: 11px;
    font-weight: 600;
    color: var(--accent-legal);
    letter-spacing: 0.06em;
    margin-bottom: 4px;
  }}
  .recommend.ai .recommend-label {{ color: var(--accent-ai); }}
  .card-link {{
    font-size: 12px;
    color: var(--accent-ai);
    text-decoration: none;
    word-break: break-all;
    transition: opacity 0.15s;
  }}
  .card-link:hover {{ opacity: 0.7; }}
  .card-link .link-icon {{
    display: inline-block;
    margin-right: 4px;
  }}
  .footer {{
    max-width: 760px;
    margin: 0 auto;
    padding: 32px 24px 48px;
    text-align: center;
    border-top: 1px solid var(--divider);
  }}
  .footer .vol {{
    font-size: 12px;
    letter-spacing: 0.2em;
    color: var(--text-tertiary);
    margin-bottom: 4px;
  }}
  .footer .engine-info {{
    font-size: 12px;
    color: var(--text-tertiary);
    margin-top: 8px;
  }}
  .footer .engine-info span {{ margin: 0 8px; }}
  .footer .disclaimer {{
    font-size: 11px;
    color: var(--text-tertiary);
    margin-top: 12px;
    opacity: 0.7;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="week-label">Weekly Briefing</div>
  <h1>法律周报</h1>
  <div class="date-range">{report_date}</div>
  <div class="stats-row">
    <div class="stat"><div class="stat-num">{total_count}</div><div class="stat-label">精选</div></div>
    <div class="stat"><div class="stat-num">{ai_count}</div><div class="stat-label">AI+法律</div></div>
    <div class="stat"><div class="stat-num">{legal_count}</div><div class="stat-label">公众号精选</div></div>
  </div>
</div>

<div class="container">

  <div class="section">
    <div class="section-head ai">
      <span class="section-num">01</span>
      <span class="section-title">AI + 法律</span>
      <span class="section-en">Legal Tech</span>
    </div>
    {ai_cards}
  </div>

  <div class="section">
    <div class="section-head legal">
      <span class="section-num">02</span>
      <span class="section-title">公众号精选</span>
      <span class="section-en">Court Accounts</span>
    </div>
    {legal_cards}
  </div>

  <div class="section">
    <div class="section-head radar">
      <span class="section-num">03</span>
      <span class="section-title">其他领域速览</span>
      <span class="section-en">Radar</span>
    </div>
    <div class="radar-note">执业圈外的立法与其他领域动态——不进精读，但值得知道发生了什么。</div>
    <ul class="radar-list">
{radar_items}
    </ul>
  </div>

</div>

<div class="footer">
  <div class="vol">VOL.{vol_date} &middot; {total_count} STORIES &middot; WEEKLY BRIEFING</div>
  <div class="engine-info">
    legal-weekly-briefing
    <span>|</span>
    k-NN 评分引擎 v2.1
    <span>|</span>
    双管道分流（周报 + IMA 知识库）
  </div>
  <div class="disclaimer">
    本报告由 AI 驱动的评分引擎自动生成，仅供参考。具体的法律判断请以现行法律法规和裁判文书为准。
  </div>
</div>

<script>
function toggleFav(btn) {{
  btn.classList.toggle('active');
}}
</script>

</body>
</html>"""

CARD_TEMPLATE = """    <div class="card">
      <div class="card-top">
        <span class="score-badge {score_class}">{score}</span>
        <span class="card-title"><a href="{url}" target="_blank">{title}</a></span>
        <button class="fav-btn" onclick="toggleFav(this)" title="收藏">&#9733;</button>
      </div>
      <div class="source-line">
        <span class="source-dot{ai_class}"></span>
        <span class="source-category">{source_category}</span>
        <span class="source-name">{source_name}</span>
        <span style="color:#c0c0cc;">&middot;</span>
        <span>{date}</span>
      </div>
      <div class="tags-row">
        {tags_html}
      </div>
      <div class="abstract">
        {abstract}
      </div>
      <div class="recommend{ai_rec}">
        <div class="recommend-label">推荐理由</div>
        {recommend}
      </div>
      <a class="card-link" href="{url}" target="_blank"><span class="link-icon">&nearr;</span>{link_text}</a>
    </div>"""


def load_articles(source_path: str) -> list[dict]:
    """从多种数据源加载文章数据。"""
    from pathlib import Path as _Path
    source = _Path(source_path)
    content = source.read_text(encoding='utf-8')

    # JSON 数据
    if source.suffix == '.json':
        data = json.loads(content)
        # run-report.json 格式
        if isinstance(data, dict):
            if 'articles' in data:
                return data['articles']
            if 'report' in data and 'articles' in data['report']:
                return data['report']['articles']
            # 尝试找第一个列表字段（排除 stages/counts/errors 等日志型字段）
            for k, v in data.items():
                if k in {"stages", "counts", "errors", "self_check"}:
                    continue
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    return v
        return data if isinstance(data, list) else []

    # JSONL 格式
    if source.suffix == '.jsonl':
        return [json.loads(line) for line in content.strip().split('\n') if line.strip()]

    # MD 格式（从周报 MD 中提取标题和 URL）
    if source.suffix == '.md':
        articles = []
        lines = content.split('\n')
        category = 'legal'
        current = None
        for line in lines:
            if 'AI + 法律' in line:
                category = 'ai-legal'
            elif '纯法律' in line or '公众号精选' in line or '裁判实务' in line:
                category = 'legal'
            # 匹配标题行: ### 标题
            m = re.match(r'^### (.+)', line)
            if m:
                if current:
                    articles.append(current)
                current = {
                    'title': m.group(1).strip(),
                    'category': category,
                    'source': '',
                    'source_category': '',
                    'date': '',
                    'score': 0,
                    'tags': [],
                    'abstract': '',
                    'recommend': ''
                }
                continue
            # URL 行
            if current and (line.startswith('http://') or line.startswith('https://')):
                current['url'] = line.strip()
                continue
            # 预览行
            if current and line.strip() and not line.startswith('#') and not line.startswith('【'):
                if not current['abstract']:
                    current['abstract'] = line.strip()
        if current:
            articles.append(current)
        return articles

    raise ValueError(f"不支持的文件格式: {source.suffix}")


def render_card(article: dict) -> str:
    """渲染单张文章卡片。"""
    is_ai = article.get('category') == 'ai-legal'
    score = article.get('score', 0)
    esc = _html.escape  # 抓取数据不可信，一律转义防 HTML 注入

    return CARD_TEMPLATE.format(
        score_class='score-high' if score >= 8.5 else 'score-mid',
        score=f"{score:.1f}" if isinstance(score, (int, float)) else str(score),
        url=esc(article.get('url', '#')),
        title=esc(article.get('title', '(无标题)')),
        ai_class=' ai' if is_ai else '',
        source_category=esc(article.get('source_category', '')),
        source_name=esc(article.get('source', '')),
        date=esc(article.get('date', '')),
        tags_html='\n        '.join(f'<span class="tag">{esc(t)}</span>' for t in article.get('tags', [])),
        abstract=esc(article.get('abstract', '')),
        ai_rec=' ai' if is_ai else '',
        recommend=esc(article.get('recommend', '')),
        link_text=esc(article.get('url', ''))[:80].replace('http://', '').replace('https://', ''),
    )


def render_radar_item(article: dict) -> str:
    """渲染雷达区单条（轻量列表项）。"""
    score = article.get('score', 0)
    score_str = f"{score:.1f}" if isinstance(score, (int, float)) else str(score)
    source = article.get('source') or article.get('source_name', '')
    esc = _html.escape
    return (
        '      <li class="radar-item">'
        f'<span class="radar-score">{score_str}</span>'
        f'<span class="radar-title"><a href="{esc(article.get("url", "#"))}" target="_blank">'
        f'{esc(article.get("title", "(无标题)"))}</a></span>'
        f'<span class="radar-source">{esc(source)}</span>'
        '</li>'
    )


# 雷达区分流阈值：低于此分的条目在雷达区做低调视觉标记（判据8·执业视野提醒）
# 值从 settings.yaml 的 output.radar_score_ceiling 读取，不再硬编码
_RADAR_SCORE_CEILING_DEFAULT = 7.0


def _get_radar_score_ceiling() -> float:
    """从 settings.yaml 读取 radar_score_ceiling，缺失时回退默认值。"""
    try:
        import yaml
        from pathlib import Path
        settings_path = Path(__file__).resolve().parent.parent / "assets" / "config" / "settings.yaml"
        if settings_path.exists():
            cfg = yaml.safe_load(open(settings_path)) or {}
            return float(cfg.get("output", {}).get("radar_score_ceiling", _RADAR_SCORE_CEILING_DEFAULT))
    except Exception:
        pass
    return _RADAR_SCORE_CEILING_DEFAULT


def render_html(articles: list[dict], report_date: str = None) -> str:
    """渲染完整 HTML。"""
    if report_date is None:
        report_date = date.today().strftime('%Y.%m.%d')

    ai_articles = [a for a in articles if a.get('category') == 'ai-legal']
    legal_articles = [a for a in articles if a.get('category') != 'ai-legal']

    ai_cards = '\n'.join(render_card(a) for a in ai_articles[:3])
    legal_cards = '\n'.join(render_card(a) for a in legal_articles[:7])

    # 雷达区（判据8·执业视野提醒）：legal 类中未进精读前7的 + 分数低于精选最低分的条目
    # 2026-08-01 修复：雷达区评分必须低于精选（"低分≠消失"设计）——同源均衡挤掉的高分落选条
    # 不进雷达区（分数高于精选会制造"雷达区比精选分高"的违和），只收分数低于精选最低分的低分条
    featured_urls = {a.get('url') for a in legal_articles[:7]}
    featured_scores = [a.get('score', 10) for a in legal_articles[:7]]
    radar_ceiling = min(featured_scores) if featured_scores else _get_radar_score_ceiling()
    radar_pool = []
    for a in legal_articles:
        s = a.get('score', 10)
        # 未进精读区 且 分数低于精选最低分 → 雷达区（评分天然不如精选）
        if a.get('url') not in featured_urls and s < radar_ceiling and a not in radar_pool:
            radar_pool.append(a)
    radar_items = '\n'.join(render_radar_item(a) for a in radar_pool[:8])
    if not radar_items:
        radar_items = '      <li class="radar-item"><span class="radar-title" style="color:var(--text-tertiary);">本期无其他领域动态</span></li>'

    vol_date = date.today().strftime('%Y.%m.%d')

    return TEMPLATE.format(
        report_date=report_date,
        total_count=len(ai_articles[:3]) + len(legal_articles[:7]),
        ai_count=len(ai_articles[:3]),
        legal_count=len(legal_articles[:7]),
        ai_cards=ai_cards,
        legal_cards=legal_cards,
        radar_items=radar_items,
        vol_date=vol_date,
    )


def main():
    if '--stdin' in sys.argv:
        data = json.load(sys.stdin)
        articles = data if isinstance(data, list) else data.get('articles', [])
    else:
        if len(sys.argv) < 2:
            print("用法: python3 render_html.py <data.json|data.jsonl|周报.md>", file=sys.stderr)
            sys.exit(1)
        articles = load_articles(sys.argv[1])

    report_date = date.today().strftime('%Y年%m月%d日')
    html = render_html(articles, report_date)

    out_path = Path.cwd() / f"周报_{date.today().strftime('%Y-%m-%d')}.html"
    out_path.write_text(html, encoding='utf-8')
    print(f"HTML 周报已生成: {out_path}")


if __name__ == '__main__':
    main()
