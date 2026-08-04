#!/usr/bin/env python3
"""
AI法律数据库检索 - HTML报告生成器
生成交互式HTML可视化法律分析报告
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"


def load_template():
    """加载基础HTML模板"""
    template_path = TEMPLATE_DIR / "report_base.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return None


def generate_report(
    input_data: dict,
    output_path: str = None,
    title: str = "法律检索分析报告"
) -> str:
    """
    生成交互式HTML法律分析报告

    Args:
        input_data: 结构化法律数据
            {
                "query": "检索词",
                "source": "数据源名称",
                "laws": [...],       # 法规列表
                "cases": [...],      # 案例列表
                "analysis": {...},   # 分析结果
                "similar_cases": [...] # 类案对比
            }
        output_path: 输出路径（默认当前目录）
        title: 报告标题

    Returns:
        报告文件路径
    """

    laws = input_data.get("laws", [])
    cases = input_data.get("cases", [])
    analysis = input_data.get("analysis", {})
    similar_cases = input_data.get("similar_cases", [])
    query = input_data.get("query", "")
    source = input_data.get("source", "法律数据库")

    # 统计
    law_count = len(laws)
    case_count = len(cases)
    similar_count = len(similar_cases)

    # 生成法规HTML
    laws_html = _render_laws(laws)

    # 生成案例HTML
    cases_html = _render_cases(cases)

    # 生成类案对比HTML
    similar_html = _render_similar_cases(similar_cases)

    # 生成分析建议HTML
    analysis_html = _render_analysis(analysis)

    # 统计数据
    stats_html = _render_stats(law_count, case_count, similar_count, source)

    # 模板变量
    template = load_template()
    if template is None:
        template = _get_default_template()

    html = template.format(
        title=title,
        query=query,
        source=source,
        generate_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        stats=stats_html,
        laws_section=laws_html if laws_html else "<p class='empty'>未检索到相关法规</p>",
        cases_section=cases_html if cases_html else "<p class='empty'>未检索到相关案例</p>",
        similar_section=similar_html if similar_html else "<p class='empty'>未检索到类案</p>",
        analysis_section=analysis_html if analysis_html else "<p class='empty'>暂无分析建议</p>",
    )

    # 输出
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"legal_report_{ts}.html"

    Path(output_path).write_text(html, encoding="utf-8")
    return os.path.abspath(output_path)


def _render_laws(laws: list) -> str:
    """渲染法规列表HTML"""
    if not laws:
        return ""

    items = []
    for law in laws:
        # 时效性标签颜色
        sxx = law.get("sxx", "")
        sxx_class = {
            "现行有效": "tag-valid",
            "失效": "tag-invalid",
            "已被修改": "tag-modified",
            "部分失效": "tag-partial",
            "尚未生效": "tag-pending",
        }.get(sxx, "tag-default")

        # 效力级别
        effect = law.get("effect1", "") or law.get("effect_level", "")

        title = law.get("fgtitle", "") or law.get("title", "")
        if isinstance(title, list):
            title = "、".join(title)

        num = law.get("num", "") or law.get("article_num", "")
        content = law.get("content", "")

        items.append(f"""
        <div class="law-card">
            <div class="law-header">
                <span class="law-title">{title}</span>
                <span class="law-num">{num}</span>
            </div>
            <div class="law-meta">
                <span class="tag {sxx_class}">{sxx}</span>
                <span class="tag tag-effect">{effect}</span>
            </div>
            <div class="law-content">{content}</div>
        </div>
        """)

    return f"""
    <div class="section" id="laws">
        <h2>📜 相关法律法规 ({len(laws)}条)</h2>
        <div class="law-list">{''.join(items)}</div>
    </div>
    """


def _render_cases(cases: list) -> str:
    """渲染案例列表HTML"""
    if not cases:
        return ""

    items = []
    for case in cases:
        case_num = case.get("case_num", "") or case.get("caseno", "")
        court = case.get("court", "") or case.get("court_name", "")
        date = case.get("judgment_date", "") or case.get("date", "")
        title = case.get("title", "") or case.get("case_title", "")
        summary = case.get("summary", "") or case.get("content", "")[:500]
        result = case.get("result", "") or case.get("judgment_result", "")
        procedure = case.get("procedure", "") or case.get("trial_procedure", "")

        items.append(f"""
        <div class="case-card">
            <div class="case-header">
                <span class="case-title">{title or case_num}</span>
                <span class="case-num">{case_num}</span>
            </div>
            <div class="case-meta">
                <span class="case-court">🏛️ {court}</span>
                <span class="case-date">📅 {date}</span>
                <span class="case-procedure">📋 {procedure}</span>
            </div>
            <div class="case-summary">{summary}</div>
            {f'<div class="case-result"><strong>判决结果：</strong>{result}</div>' if result else ''}
        </div>
        """)

    return f"""
    <div class="section" id="cases">
        <h2>⚖️ 相关案例 ({len(cases)}件)</h2>
        <div class="case-list">{''.join(items)}</div>
    </div>
    """


def _render_similar_cases(similar_cases: list) -> str:
    """渲染类案对比表HTML"""
    if not similar_cases:
        return ""

    # 表头
    headers = ["案号", "法院", "裁判日期", "争议焦点", "裁判观点", "判决结果"]

    rows = []
    for sc in similar_cases:
        rows.append(f"""
        <tr>
            <td>{sc.get('case_num', '')}</td>
            <td>{sc.get('court', '')}</td>
            <td>{sc.get('date', '')}</td>
            <td>{sc.get('dispute_focus', '')}</td>
            <td>{sc.get('opinion', '')}</td>
            <td><span class="result-badge">{sc.get('result', '')}</span></td>
        </tr>
        """)

    # 对比洞察
    insights = _extract_insights(similar_cases)

    return f"""
    <div class="section" id="similar">
        <h2>📊 类案对比分析 ({len(similar_cases)}件)</h2>

        <div class="insight-box">
            <h3>💡 裁判观点提炼</h3>
            {insights}
        </div>

        <div class="table-wrapper">
            <table class="compare-table">
                <thead>
                    <tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </div>
    """


def _extract_insights(similar_cases: list) -> str:
    """从类案中提取共性洞察"""
    results = [c.get("result", "") for c in similar_cases]
    courts = [c.get("court", "") for c in similar_cases]

    # 统计结果倾向
    support_count = sum(1 for r in results if any(kw in r for kw in ["支持", "胜诉", "维持"]))
    reject_count = sum(1 for r in results if any(kw in r for kw in ["驳回", "不予支持", "撤销"]))
    total = len(results)

    parts = []

    if total > 0:
        parts.append(f"<p>📈 共检索到 <strong>{total}</strong> 件类案：</p>")
        parts.append("<ul>")

        if support_count > 0:
            parts.append(
                f"<li>支持/胜诉类案件 <strong>{support_count}</strong> 件（{support_count*100//total}%），"
                f"法院通常基于...做出支持判决</li>"
            )
        if reject_count > 0:
            parts.append(
                f"<li>驳回/不支持类案件 <strong>{reject_count}</strong> 件（{reject_count*100//total}%），"
                f"主要原因为证据不足或法律适用错误</li>"
            )

        parts.append("</ul>")

    # 法院层级分布
    high_courts = [c for c in courts if any(x in c for x in ["高级", "中级", "最高"])]
    if high_courts:
        parts.append(f"<p>🏛️ 涉及 <strong>{len(high_courts)}</strong> 个较高级别法院的裁判观点</p>")

    return "".join(parts)


def _render_analysis(analysis: dict) -> str:
    """渲染分析建议HTML"""
    if not analysis:
        return ""

    parts = []

    # 法律适用分析
    if "legal_basis" in analysis:
        parts.append(f"""
        <div class="analysis-block">
            <h3>⚖️ 法律适用分析</h3>
            <p>{analysis['legal_basis']}</p>
        </div>
        """)

    # 风险提示
    if "risks" in analysis:
        risks = analysis["risks"]
        if isinstance(risks, str):
            risks = [risks]
        risk_items = "".join(f"<li>{r}</li>" for r in risks)
        parts.append(f"""
        <div class="analysis-block warning">
            <h3>⚠️ 风险提示</h3>
            <ul>{risk_items}</ul>
        </div>
        """)

    # 建议
    if "suggestions" in analysis:
        suggestions = analysis["suggestions"]
        if isinstance(suggestions, str):
            suggestions = [suggestions]
        sug_items = "".join(f"<li>{s}</li>" for s in suggestions)
        parts.append(f"""
        <div class="analysis-block">
            <h3>💡 实务建议</h3>
            <ul>{sug_items}</ul>
        </div>
        """)

    # 关键证据要求
    if "evidence" in analysis:
        parts.append(f"""
        <div class="analysis-block">
            <h3>📋 关键证据要求</h3>
            <p>{analysis['evidence']}</p>
        </div>
        """)

    return f"""
    <div class="section" id="analysis">
        <h2>📝 综合分析建议</h2>
        {''.join(parts)}
    </div>
    """


def _render_stats(law_count: int, case_count: int, similar_count: int, source: str) -> str:
    """渲染统计卡片"""
    return f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{law_count}</div>
            <div class="stat-label">相关法规</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{case_count}</div>
            <div class="stat-label">相关案例</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{similar_count}</div>
            <div class="stat-label">类案对比</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">数据源</div>
            <div class="stat-source">{source}</div>
        </div>
    </div>
    """


def _get_default_template() -> str:
    """默认HTML模板（内置，无需外部文件）"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.8;
        }}
        .header {{
            background: linear-gradient(135deg, #1a365d 0%, #2d5a8e 50%, #3d7bc9 100%);
            color: white;
            padding: 40px 60px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ color: #bcd0f0; font-size: 14px; }}
        .query-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.15);
            padding: 4px 14px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 14px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 30px 40px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: 700;
            color: #1a365d;
            margin-bottom: 4px;
        }}
        .stat-label {{ color: #666; font-size: 14px; }}
        .stat-source {{ color: #3d7bc9; font-size: 14px; font-weight: 500; }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px 35px;
            margin-bottom: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}
        .section h2 {{
            font-size: 20px;
            color: #1a365d;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e8edf3;
        }}
        .law-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            transition: box-shadow 0.2s;
        }}
        .law-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.08); }}
        .law-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .law-title {{ font-size: 16px; font-weight: 600; color: #1a365d; }}
        .law-num {{ color: #3d7bc9; font-weight: 600; }}
        .law-meta {{ margin-bottom: 12px; }}
        .law-content {{
            color: #555;
            font-size: 15px;
            line-height: 2;
            text-indent: 2em;
        }}
        .tag {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 8px;
        }}
        .tag-valid {{ background: #e6fffa; color: #00a372; }}
        .tag-invalid {{ background: #fff5f5; color: #e53e3e; }}
        .tag-modified {{ background: #fffaf0; color: #dd6b20; }}
        .tag-partial {{ background: #fff5f5; color: #c53030; }}
        .tag-pending {{ background: #ebf8ff; color: #3182ce; }}
        .tag-default {{ background: #f7fafc; color: #718096; }}
        .tag-effect {{ background: #f0f0ff; color: #5a6acf; }}
        .case-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        .case-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        .case-title {{ font-weight: 600; color: #1a365d; }}
        .case-num {{ color: #718096; font-size: 13px; }}
        .case-meta {{
            display: flex;
            gap: 20px;
            margin-bottom: 12px;
            font-size: 14px;
            color: #666;
        }}
        .case-summary {{ color: #555; margin-bottom: 10px; }}
        .case-result {{ color: #2d5a8e; font-size: 14px; }}
        .compare-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .compare-table th {{
            background: #1a365d;
            color: white;
            padding: 12px 14px;
            text-align: left;
            font-weight: 500;
        }}
        .compare-table td {{
            padding: 12px 14px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }}
        .compare-table tr:hover {{ background: #f7fafc; }}
        .result-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 4px;
            font-size: 12px;
            background: #e6fffa;
            color: #00a372;
            white-space: nowrap;
        }}
        .table-wrapper {{ overflow-x: auto; }}
        .insight-box {{
            background: #f0f7ff;
            border-left: 4px solid #3d7bc9;
            padding: 20px;
            margin-bottom: 24px;
            border-radius: 0 8px 8px 0;
        }}
        .insight-box h3 {{ margin-bottom: 12px; color: #1a365d; }}
        .insight-box ul {{ padding-left: 20px; }}
        .insight-box li {{ margin-bottom: 6px; }}
        .analysis-block {{
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e8edf3;
        }}
        .analysis-block:last-child {{ border-bottom: none; }}
        .analysis-block h3 {{ margin-bottom: 10px; color: #1a365d; }}
        .analysis-block.warning {{
            background: #fffdf5;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 16px;
        }}
        .analysis-block ul {{ padding-left: 20px; }}
        .analysis-block li {{ margin-bottom: 6px; }}
        .empty {{ color: #999; text-align: center; padding: 30px; }}
        .toc {{
            background: #f7fafc;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .toc h3 {{ margin-bottom: 12px; color: #1a365d; }}
        .toc a {{
            display: block;
            padding: 4px 0;
            color: #3d7bc9;
            text-decoration: none;
            font-size: 15px;
        }}
        .toc a:hover {{ text-decoration: underline; }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 13px;
            padding: 30px 0;
        }}
        .footer a {{ color: #3d7bc9; }}
        @media (max-width: 768px) {{
            .container {{ padding: 20px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .header {{ padding: 24px; }}
            .section {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚖️ {title}</h1>
        <div class="meta">
            生成时间：{generate_time} | 数据源：{source}
        </div>
        <div class="query-badge">检索词：{query}</div>
    </div>

    <div class="container">
        {stats}

        <div class="toc">
            <h3>📑 报告目录</h3>
            <a href="#laws">📜 相关法律法规</a>
            <a href="#cases">⚖️ 相关案例</a>
            <a href="#similar">📊 类案对比分析</a>
            <a href="#analysis">📝 综合分析建议</a>
        </div>

        {laws_section}
        {cases_section}
        {similar_section}
        {analysis_section}

        <div class="footer">
            <p>本报告由 AI法律数据库检索助手 自动生成</p>
            <p>数据来源：{source} | 报告仅供参考，不构成法律意见</p>
            <p>AI Legal Search Report | Powered by WorkBuddy</p>
        </div>
    </div>
</body>
</html>"""


if __name__ == "__main__":
    # 命令行入口
    import argparse

    parser = argparse.ArgumentParser(description="法律报告生成器")
    parser.add_argument("--input", "-i", help="输入JSON文件路径")
    parser.add_argument("--output", "-o", help="输出HTML文件路径")
    parser.add_argument("--title", "-t", default="法律检索分析报告", help="报告标题")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    if args.input:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        # 从stdin读取
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
        else:
            print("请通过 --input 参数指定输入文件，或通过管道传入JSON数据", file=sys.stderr)
            sys.exit(1)

    output_path = generate_report(
        input_data=data,
        output_path=args.output,
        title=args.title,
    )

    print(f"✅ 报告已生成: {output_path}")
    if args.debug:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
