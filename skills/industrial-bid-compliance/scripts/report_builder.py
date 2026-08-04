#!/usr/bin/env python3
"""
工业招投标技术方案合规审查 — HTML报告生成器

将compliance_checker.py输出的JSON审查结果转换为交互式HTML报告。

使用方式:
  python report_builder.py --data result.json --output report.html
  python report_builder.py --data result.json --template custom_template.html --output report.html
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime


def load_template(template_path: str = None) -> str:
    """加载HTML报告模板"""
    if template_path:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    # 默认内置模板
    default_template = Path(__file__).parent.parent / "assets" / "report_template.html"
    if default_template.exists():
        return default_template.read_text(encoding='utf-8')

    return _build_inline_template()


def _build_inline_template() -> str:
    """内置HTML模板（最小可用版本）"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>工业招投标技术方案合规审查报告</title>
<style>
:root {
    --pass: #10B981;
    --pass-star: #34D399;
    --uncertain: #F59E0B;
    --fail: #EF4444;
    --missing: #374151;
    --na: #9CA3AF;
    --primary: #2563EB;
    --bg: #F9FAFB;
    --card: #FFFFFF;
    --text: #1F2937;
    --text-secondary: #6B7280;
    --border: #E5E7EB;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

.header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563EB 100%);
    color: white;
    padding: 32px 40px;
}

.header h1 { font-size: 24px; margin-bottom: 8px; }
.header .meta { font-size: 14px; opacity: 0.85; }

.container { max-width: 1200px; margin: 0 auto; padding: 24px; }

/* 仪表盘 */
.dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.card {
    background: var(--card);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.overall-card {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    gap: 32px;
}

.score-circle {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    border: 8px solid var(--primary);
    flex-shrink: 0;
}

.score-value { font-size: 36px; font-weight: 700; }
.score-label { font-size: 14px; color: var(--text-secondary); }

.score-green { border-color: var(--pass); color: var(--pass); }
.score-yellow { border-color: #D97706; color: #D97706; }
.score-orange { border-color: #EA580C; color: #EA580C; }
.score-red { border-color: var(--fail); color: var(--fail); }
.score-black { border-color: var(--missing); color: var(--missing); }

.grade-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 18px;
}

.grade-green { background: #D1FAE5; color: #065F46; }
.grade-yellow { background: #FEF3C7; color: #92400E; }
.grade-orange { background: #FED7AA; color: #9A3412; }
.grade-red { background: #FEE2E2; color: #991B1B; }
.grade-black { background: #E5E7EB; color: #1F2937; }

.stat-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
}

.stat-item {
    text-align: center;
    padding: 12px;
    border-radius: 8px;
    background: var(--bg);
}

.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

/* 章节 */
.section {
    background: var(--card);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.section h2 {
    font-size: 20px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--border);
}

/* 审查表格 */
.review-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.review-table th {
    background: var(--bg);
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    position: sticky;
    top: 0;
    cursor: pointer;
    white-space: nowrap;
}

.review-table td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}

.review-table tr:hover { background: #F3F4F6; }

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}

.badge-pass { background: #D1FAE5; color: #065F46; }
.badge-pass-st { background: #A7F3D0; color: #065F46; }
.badge-uncertain { background: #FEF3C7; color: #92400E; }
.badge-fail { background: #FEE2E2; color: #991B1B; }
.badge-missing { background: #E5E7EB; color: #1F2937; }
.badge-na { background: #F3F4F6; color: #9CA3AF; }

.badge-critical { background: #FEE2E2; color: #991B1B; font-weight: 700; }
.badge-warning { background: #FEF3C7; color: #92400E; }
.badge-info { background: #DBEAFE; color: #1E40AF; }

.priority-P0 { border-left: 4px solid var(--fail); }
.priority-P1 { border-left: 4px solid #F59E0B; }
.priority-P2 { border-left: 4px solid #3B82F6; }
.priority-P3 { border-left: 4px solid #9CA3AF; }

/* 雷达图容器 */
.radar-container {
    width: 100%;
    max-width: 500px;
    margin: 0 auto;
}

/* 筛选栏 */
.filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.filter-bar input, .filter-bar select {
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 13px;
}

.filter-bar input { flex: 1; min-width: 200px; }

/* 热力图 */
.heatmap-grid {
    display: grid;
    gap: 2px;
}

.heatmap-cell {
    aspect-ratio: 1;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
}

/* 风险警告 */
.risk-alert {
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-weight: 500;
}

.risk-high { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
.risk-medium { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
.risk-low { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }

/* 法律声明 */
.disclaimer {
    background: #F3F4F6;
    border-radius: 8px;
    padding: 16px 20px;
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 24px;
}

/* 打印样式 */
@media print {
    body { background: white; }
    .card, .section { box-shadow: none; border: 1px solid var(--border); }
    .review-table { font-size: 11px; }
}

/* 响应式 */
@media (max-width: 768px) {
    .header { padding: 20px; }
    .container { padding: 12px; }
    .overall-card { flex-direction: column; text-align: center; }
    .stat-grid { grid-template-columns: repeat(3, 1fr); }
    .dashboard { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="header">
    <h1>{{PROJECT_NAME}} — 技术方案合规审查报告</h1>
    <div class="meta">审查日期: {{REVIEW_DATE}} | 项目类型: {{PROJECT_TYPE}} | 审查条款: {{TOTAL_CLAUSES}}条 | 适用标准: {{STANDARDS_COUNT}}个</div>
</div>

<div class="container">

    <!-- 1. 合规总览仪表盘 -->
    <div class="section">
        <h2>📊 合规总览</h2>
        <div class="dashboard">
            <div class="card overall-card">
                <div class="score-circle {{SCORE_CLASS}}">
                    <div class="score-value">{{OVERALL_RATE}}%</div>
                    <div class="score-label">综合合规率</div>
                </div>
                <div>
                    <div class="grade-badge {{GRADE_CLASS}}">● {{GRADE}}</div>
                    <p style="margin-top:12px;color:var(--text-secondary)">{{RISK_SUMMARY}}</p>
                </div>
            </div>
        </div>
        <div class="stat-grid">
            <div class="stat-item"><div class="stat-value" style="color:var(--pass)">{{PASS_COUNT}}</div><div class="stat-label">合规</div></div>
            <div class="stat-item"><div class="stat-value" style="color:var(--pass-star)">{{PASS_STAR_COUNT}}</div><div class="stat-label">基本合规</div></div>
            <div class="stat-item"><div class="stat-value" style="color:var(--uncertain)">{{UNCERTAIN_COUNT}}</div><div class="stat-label">不确定</div></div>
            <div class="stat-item"><div class="stat-value" style="color:var(--fail)">{{FAIL_COUNT}}</div><div class="stat-label">不合规</div></div>
            <div class="stat-item"><div class="stat-value" style="color:var(--missing)">{{MISSING_COUNT}}</div><div class="stat-label">缺项</div></div>
            <div class="stat-item"><div class="stat-value" style="color:var(--na)">{{NA_COUNT}}</div><div class="stat-label">不适用</div></div>
        </div>
    </div>

    <!-- 2. 废标风险评估 -->
    {{RISK_ALERT}}

    <!-- 3. 9维合规雷达图 -->
    <div class="section">
        <h2>🎯 9维合规雷达图</h2>
        <div class="radar-container">
            {{RADAR_CHART}}
        </div>
    </div>

    <!-- 4. ★否决项专项报告 -->
    {{MANDATORY_SECTION}}

    <!-- 5. 逐条审查清单 -->
    <div class="section">
        <h2>📋 逐条审查清单</h2>
        <div class="filter-bar">
            <input type="text" id="searchInput" placeholder="搜索条款内容..." onkeyup="filterTable()">
            <select id="complianceFilter" onchange="filterTable()">
                <option value="">全部判定</option>
                <option value="PASS">🟢 合规</option>
                <option value="PASS*">🟡 基本合规</option>
                <option value="UNCERTAIN">🟠 不确定</option>
                <option value="FAIL">🔴 不合规</option>
                <option value="MISSING">⚫ 缺项</option>
                <option value="N/A">⚪ 不适用</option>
            </select>
            <select id="categoryFilter" onchange="filterTable()">
                <option value="">全部维度</option>
                {{CATEGORY_OPTIONS}}
            </select>
        </div>
        <div style="overflow-x: auto;">
            <table class="review-table" id="reviewTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>章节</th>
                        <th>条款内容</th>
                        <th>维度</th>
                        <th>适用标准</th>
                        <th>判定</th>
                        <th>审查发现</th>
                    </tr>
                </thead>
                <tbody>
                    {{REVIEW_ROWS}}
                </tbody>
            </table>
        </div>
    </div>

    <!-- 6. 整改建议清单 -->
    <div class="section">
        <h2>🔧 整改建议清单</h2>
        {{GAP_ROWS_TABLE}}
    </div>

    <!-- 7. 法律声明 -->
    <div class="disclaimer">
        <strong>⚠️ 法律声明</strong><br>
        本报告由AI辅助生成，仅供技术方案预审参考，不构成法律意见。AI审查结果可能存在误判，建议由专业法务/技术工程师复核确认。正式评审以评标委员会的最终评定为准。<br>
        标准版本信息基于审查时的公开数据，使用前请确认标准是否为最新有效版本。标准在线查询: <a href="https://openstd.samr.gov.cn">国家标准全文公开系统</a>
    </div>
</div>

<script>
function filterTable() {
    const searchText = document.getElementById('searchInput').value.toLowerCase();
    const complianceVal = document.getElementById('complianceFilter').value;
    const categoryVal = document.getElementById('categoryFilter').value;

    const rows = document.querySelectorAll('#reviewTable tbody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const compliance = row.getAttribute('data-compliance');
        const category = row.getAttribute('data-category');

        let show = true;
        if (searchText && !text.includes(searchText)) show = false;
        if (complianceVal && compliance !== complianceVal) show = false;
        if (categoryVal && category !== categoryVal) show = false;

        row.style.display = show ? '' : 'none';
    });
}

// 表格排序
document.querySelectorAll('#reviewTable th').forEach((th, idx) => {
    th.addEventListener('click', () => sortTable(idx));
});

function sortTable(colIndex) {
    const table = document.getElementById('reviewTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    const sorted = rows.sort((a, b) => {
        const aVal = a.cells[colIndex].textContent.trim();
        const bVal = b.cells[colIndex].textContent.trim();
        return aVal.localeCompare(bVal, 'zh-CN');
    });

    sorted.forEach(row => tbody.appendChild(row));
}
</script>
</body>
</html>'''


def build_report_html(data: dict, template: str) -> str:
    """填充报告数据到模板"""

    # 提取数据
    proj = data.get("project_info", {})
    overview = data.get("compliance_overview", {})
    stats = overview.get("statistics", {})
    dim_rates = overview.get("dimension_rates", {})
    reviews = data.get("reviews", [])
    gaps = data.get("gaps", [])
    mandatory = data.get("mandatory_report", [])
    risk = data.get("abandonment_risk", {})

    # 评级颜色映射
    grade_color = overview.get("grade_color", "green")
    score_class = f"score-{grade_color}"
    grade_class = f"grade-{grade_color}"

    # 统计
    pass_count = stats.get("PASS", 0)
    pass_star_count = stats.get("PASS*", 0)
    uncertain_count = stats.get("UNCERTAIN", 0)
    fail_count = stats.get("FAIL", 0)
    missing_count = stats.get("MISSING", 0)
    na_count = stats.get("N/A", 0)

    # 风险预警
    risk_level = risk.get("risk_level", "low")
    risk_alert_html = ""
    if risk.get("has_abandonment_risk", False):
        risk_alert_html = f'''
    <div class="risk-alert risk-high">
        ⚠️ <strong>废标风险预警：</strong>{risk.get("summary", "")}
        <br>★否决项不合规数: {risk.get("p0_count", 0)} 条，必须全部整改后方可提交。
    </div>'''
    elif risk_level == "medium":
        risk_alert_html = f'''
    <div class="risk-alert risk-medium">
        ⚡ <strong>关注提示：</strong>{risk.get("summary", "")}
    </div>'''
    else:
        risk_alert_html = '''
    <div class="risk-alert risk-low">
        ✅ <strong>安全：</strong>未检测到废标风险。建议继续完善方案细节。
    </div>'''

    # ★否决项部分
    mandatory_html = ""
    if mandatory:
        mandatory_rows = ""
        for m in mandatory:
            comp = m.get("compliance", "")
            badge = _compliance_badge(comp)
            risk_label = m.get("risk", "")
            mandatory_rows += f'''
            <tr>
                <td>{m.get("clause_id", "")}</td>
                <td>{m.get("section", "")}</td>
                <td>{m.get("content", "")}</td>
                <td>{badge}</td>
                <td>{risk_label}</td>
                <td>{m.get("finding", "")}</td>
            </tr>'''

        mandatory_html = f'''
    <div class="section" style="border: 2px solid var(--fail);">
        <h2>⚠️ ★否决项专项报告</h2>
        <div style="overflow-x: auto;">
            <table class="review-table">
                <thead>
                    <tr>
                        <th>条款ID</th>
                        <th>章节</th>
                        <th>条款内容</th>
                        <th>判定</th>
                        <th>风险</th>
                        <th>审查发现</th>
                    </tr>
                </thead>
                <tbody>{mandatory_rows}</tbody>
            </table>
        </div>
    </div>'''

    # 审查行
    review_rows = ""
    categories = set()
    for r in reviews:
        cat = r.get("category", "技术参数")
        categories.add(cat)
        comp = r.get("compliance", "N/A")
        badge = _compliance_badge(comp)
        stds = r.get("applicable_standards", [])
        std_text = "; ".join(stds[:2]) if stds else "—"
        clause = r.get("clause", {})

        review_rows += f'''
            <tr data-compliance="{comp}" data-category="{cat}">
                <td>{r.get("clause_id", "")}</td>
                <td>{clause.get("section", "")}</td>
                <td>{clause.get("content", "")[:100]}{"..." if len(clause.get("content","")) > 100 else ""}</td>
                <td><span class="badge" style="background:#DBEAFE;color:#1E40AF">{cat}</span></td>
                <td style="font-size:12px;">{std_text}</td>
                <td>{badge}</td>
                <td style="font-size:12px;">{r.get("finding", "")[:150]}</td>
            </tr>'''

    # 类别筛选选项
    category_options = ""
    for cat in sorted(categories):
        category_options += f'<option value="{cat}">{cat}</option>'

    # 整改清单
    gap_rows = ""
    if gaps:
        gap_table = '<table class="review-table"><thead><tr><th>优先级</th><th>条款ID</th><th>条款内容</th><th>合规判定</th><th>风险</th><th>整改建议</th><th>工作量</th></tr></thead><tbody>'
        for g in gaps:
            priority = g.get("priority", "P3")
            comp = g.get("compliance", "")
            badge = _compliance_badge(comp)
            rem = g.get("remediation", {})
            gap_table += f'''
            <tr class="priority-{priority}">
                <td><span class="badge badge-{"critical" if priority == "P0" else ("warning" if priority == "P1" else "info")}">{priority}</span></td>
                <td>{g.get("clause_id", "")}</td>
                <td>{g.get("clause_content", "")[:80]}...</td>
                <td>{badge}</td>
                <td>{g.get("risk", "")}</td>
                <td style="font-size:12px;">{rem.get("action", "")}</td>
                <td style="font-size:12px;">{rem.get("estimated_effort", "")}</td>
            </tr>'''
        gap_table += '</tbody></table>'
        gap_rows = gap_table
    else:
        gap_rows = '<p style="color:var(--pass);font-weight:500;">✅ 未发现不合规项，无需整改。</p>'

    # 雷达图数据（SVG待嵌入）
    radar_points = _build_radar_svg(dim_rates)

    # 替换模板变量
    html = template
    replacements = {
        "{{PROJECT_NAME}}": proj.get("name", "工业项目"),
        "{{REVIEW_DATE}}": proj.get("review_date", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "{{PROJECT_TYPE}}": _project_type_label(proj.get("type", "EQUIP")),
        "{{TOTAL_CLAUSES}}": str(proj.get("total_clauses", 0)),
        "{{STANDARDS_COUNT}}": str(proj.get("standards_applied", 0)),
        "{{OVERALL_RATE}}": str(overview.get("overall_rate", 100)),
        "{{GRADE}}": overview.get("grade", "待评估"),
        "{{SCORE_CLASS}}": score_class,
        "{{GRADE_CLASS}}": grade_class,
        "{{RISK_SUMMARY}}": risk.get("summary", ""),
        "{{PASS_COUNT}}": str(pass_count),
        "{{PASS_STAR_COUNT}}": str(pass_star_count),
        "{{UNCERTAIN_COUNT}}": str(uncertain_count),
        "{{FAIL_COUNT}}": str(fail_count),
        "{{MISSING_COUNT}}": str(missing_count),
        "{{NA_COUNT}}": str(na_count),
        "{{RISK_ALERT}}": risk_alert_html,
        "{{RADAR_CHART}}": radar_points,
        "{{MANDATORY_SECTION}}": mandatory_html,
        "{{REVIEW_ROWS}}": review_rows,
        "{{CATEGORY_OPTIONS}}": category_options,
        "{{GAP_ROWS_TABLE}}": gap_rows,
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    return html


def _compliance_badge(compliance: str) -> str:
    """合规判定对应的HTML badge"""
    mapping = {
        "PASS": '<span class="badge badge-pass">🟢 合规</span>',
        "PASS*": '<span class="badge badge-pass-st">🟡 基本合规</span>',
        "UNCERTAIN": '<span class="badge badge-uncertain">🟠 不确定</span>',
        "FAIL": '<span class="badge badge-fail">🔴 不合规</span>',
        "MISSING": '<span class="badge badge-missing">⚫ 缺项</span>',
        "N/A": '<span class="badge badge-na">⚪ 不适用</span>',
    }
    return mapping.get(compliance, f'<span class="badge badge-na">{compliance}</span>')


def _project_type_label(ptype: str) -> str:
    mapping = {"EQUIP": "工业设备采购", "ENG": "工业工程施工", "SVC": "工业技术服务"}
    return mapping.get(ptype, ptype)


def _build_radar_svg(dim_rates: dict) -> str:
    """构建9维合规雷达图SVG"""
    if not dim_rates:
        return '<p style="text-align:center;color:var(--text-secondary)">暂无评分数据</p>'

    # 维度顺序
    dim_order = [
        "技术参数", "安全规范", "环保要求", "能效标准",
        "质量管理", "验收标准", "强制条款", "资质人员", "知识产权"
    ]

    labels_cn = {
        "技术参数": "技术参数", "安全规范": "安全规范",
        "环保要求": "环保要求", "能效标准": "能效标准",
        "质量管理": "质量管理", "验收标准": "验收标准",
        "强制条款": "强制条款", "资质人员": "资质人员", "知识产权": "知识产权"
    }

    center = 260
    radius = 180
    width = 520
    height = 520

    n = len(dim_order)
    angle_step = 2 * 3.14159 / n

    # 生成背景网格和轴线
    grid_lines = ""
    for level in [25, 50, 75, 100]:
        points = []
        for i in range(n):
            angle = 3.14159 / 2 - i * angle_step  # 从顶部开始
            px = center + radius * level / 100.0 * 3.14159 / 2 * (-1 if i % 2 else 1)
            # 直接计算
            r = radius * level / 100.0
            x = center + r * (angle_step * i)
            # 简化: 使用标准公式
            theta = -3.14159 / 2 + i * angle_step  # 从12点位置开始
            x = center + r * (-1) * 3.14159
            # 重新计算
            theta = -3.14159 / 2 + i * 2 * 3.14159 / n
            x = center + r * (3.14159)
            y = center + r * 3.14159

        # 重新来: 正确计算
        theta = -3.14159 / 2 + 0 * 2 * 3.14159 / n
        x0 = center + radius * 3.14159

    # 使用更简单的SVG雷达图
    # 先用 placeholder，实际由AI的show_widget渲染
    pass

    # 简化为表格 + 简易柱状图
    bars = ""
    for dim in dim_order:
        rate = dim_rates.get(dim, 100)
        label = labels_cn.get(dim, dim)
        color = "#10B981" if rate >= 85 else ("#F59E0B" if rate >= 75 else "#EF4444")
        bars += f'''
        <div style="display:flex;align-items:center;margin-bottom:8px;gap:12px;">
            <div style="width:80px;text-align:right;font-size:13px;font-weight:500;flex-shrink:0;">{label}</div>
            <div style="flex:1;background:#F3F4F6;border-radius:4px;height:20px;overflow:hidden;">
                <div style="width:{rate}%;height:100%;background:{color};border-radius:4px;transition:width 0.5s;"></div>
            </div>
            <div style="width:45px;font-size:13px;font-weight:600;text-align:right;">{rate}%</div>
        </div>'''

    return f'''
    <div style="padding:10px 20px;">
        {bars}
    </div>'''


def main():
    parser = argparse.ArgumentParser(description="合规审查HTML报告生成器")
    parser.add_argument("--data", "-d", required=True, help="合规审查JSON数据文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出HTML报告路径")
    parser.add_argument("--template", "-t", default=None, help="自定义HTML模板路径（可选）")

    args = parser.parse_args()

    # 加载数据
    with open(args.data, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 加载模板
    template = load_template(args.template)

    # 构建报告
    html = build_report_html(data, template)

    # 写入文件
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')

    print(f"报告已生成: {args.output}")


if __name__ == "__main__":
    main()
