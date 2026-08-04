# HTML审查报告模板

本模板用于生成食品标签合规审查的HTML报告。使用Jinja2模板引擎渲染审查数据。

## 使用方式

1. 智能体完成审查后，生成结构化JSON数据
2. 使用Jinja2加载本模板
3. 渲染生成HTML文件

## 数据结构

```json
{
  "report_time": "2025-01-15 14:30:00",
  "summary": {
    "total": 58,
    "compliant": 45,
    "non_compliant": 13
  },
  "categories": [
    {
      "name": "基本信息",
      "items": [
        {
          "id": "01",
          "name": "生产许可证编号",
          "status": "non_compliant",
          "error_location": "标签正面底部",
          "error_reason": "未标注生产许可证编号，仅标SC图标",
          "suggestion": "标注完整SC编号，如SC10631011800012",
          "consequence": "依据《食品安全法》第125条，罚款5000元（沪市监松处〔2024〕123号）",
          "standard": "《食品安全法》第六十七条，必须标注完整SC编号，不得仅标SC图标"
        }
      ]
    }
  ]
}
```

## Jinja2模板代码

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>食品标签合规审查报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}
        .summary-card .number {{ font-size: 36px; font-weight: bold; margin-bottom: 5px; }}
        .summary-card .label {{ color: #666; font-size: 14px; }}
        .summary-card.total .number {{ color: #667eea; }}
        .summary-card.compliant .number {{ color: #10b981; }}
        .summary-card.non-compliant .number {{ color: #ef4444; }}
        .main-layout {{ display: grid; grid-template-columns: 320px 1fr; gap: 20px; min-height: 600px; }}
        .left-nav {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            padding: 20px;
            max-height: 800px;
            overflow-y: auto;
        }}
        .nav-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .filter {{ display: flex; gap: 10px; margin-bottom: 15px; }}
        .filter-btn {{
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s;
        }}
        .filter-btn:hover {{ background: #f0f0f0; }}
        .filter-btn.active {{ background: #667eea; color: white; border-color: #667eea; }}
        .category-group {{ margin-bottom: 15px; }}
        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
        }}
        .category-header:hover {{ background: #e9ecef; }}
        .category-toggle {{ font-size: 12px; color: #666; }}
        .category-items {{ padding-left: 10px; margin-top: 8px; }}
        .review-item {{
            display: flex;
            align-items: center;
            padding: 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s;
            margin-bottom: 5px;
        }}
        .review-item:hover {{ background: #f0f0f0; }}
        .review-item.active {{ background: #667eea; color: white; }}
        .item-icon {{ margin-right: 8px; font-size: 16px; }}
        .item-name {{ flex: 1; }}
        .status-compliant {{ color: #10b981; }}
        .status-non-compliant {{ color: #ef4444; }}
        .status-unknown {{ color: #9ca3af; }}
        .right-content {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            padding: 30px;
            max-height: 800px;
            overflow-y: auto;
        }}
        .empty-state {{ text-align: center; color: #999; padding: 100px 0; font-size: 16px; }}
        .item-detail {{ animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .item-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 20px;
        }}
        .item-title {{ font-size: 24px; font-weight: bold; color: #333; }}
        .status-badge {{ padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .badge-compliant {{ background: #d1fae5; color: #10b981; }}
        .badge-non-compliant {{ background: #fee2e2; color: #ef4444; }}
        .badge-unknown {{ background: #f3f4f6; color: #9ca3af; }}
        .item-content {{ font-size: 14px; line-height: 1.8; }}
        .detail-row {{ display: flex; margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; }}
        .detail-label {{ font-weight: bold; color: #666; min-width: 120px; flex-shrink: 0; }}
        .detail-value {{ color: #333; flex: 1; word-break: break-word; }}
        .error-section {{ border-left: 4px solid #ef4444; background: #fef2f2; }}
        .suggestion-section {{ border-left: 4px solid #667eea; background: #f0f4ff; }}
        .consequence-section {{ border-left: 4px solid #f59e0b; background: #fef3c7; }}
        @media (max-width: 768px) {{
            .main-layout {{ grid-template-columns: 1fr; }}
            .left-nav {{ max-height: 300px; }}
            .summary {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>食品标签合规审查报告</h1>
            <div class="meta">审查时间：{{ report_time }}</div>
        </div>

        <div class="summary">
            <div class="summary-card total">
                <div class="number">{{ summary.total }}</div>
                <div class="label">总计审查点</div>
            </div>
            <div class="summary-card compliant">
                <div class="number">{{ summary.compliant }}</div>
                <div class="label">合规</div>
            </div>
            <div class="summary-card non-compliant">
                <div class="number">{{ summary.non_compliant }}</div>
                <div class="label">不合规</div>
            </div>
        </div>

        <div class="main-layout">
            <div class="left-nav">
                <div class="nav-title">审查点导航</div>
                <div class="filter">
                    <button class="filter-btn active" onclick="filterItems('all')">全部</button>
                    <button class="filter-btn" onclick="filterItems('non_compliant')">不合规</button>
                    <button class="filter-btn" onclick="filterItems('compliant')">合规</button>
                </div>
                {% for category in categories %}
                {% set cat_id = 'cat_' + loop.index|string %}
                <div class="category-group">
                    <div class="category-header" onclick="toggleCategory('{{ cat_id }}')">
                        <span class="category-name">{{ category.name }}</span>
                        <span class="category-toggle">▼</span>
                    </div>
                    <div class="category-items" id="{{ cat_id }}">
                        {% for item in category.items %}
                        {% set icon = '✅' if item.status == 'compliant' else '❌' if item.status == 'non_compliant' else '⚪' %}
                        {% set status_class = 'status-compliant' if item.status == 'compliant' else 'status-non-compliant' if item.status == 'non_compliant' else 'status-unknown' %}
                        <div class="review-item {{ status_class }}" id="nav_{{ item.id }}" onclick="showItem('{{ item.id }}')">
                            <span class="item-icon">{{ icon }}</span>
                            <span class="item-name">{{ item.name }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>

            <div class="right-content" id="rightContent">
                <div class="empty-state">
                    点击左侧审查点查看详情
                </div>
                {% for category in categories %}
                {% for item in category.items %}
                {% set status_text = '✅ 合规' if item.status == 'compliant' else '❌ 不合规' if item.status == 'non_compliant' else '⚪ 未检查' %}
                {% set status_class = 'badge-compliant' if item.status == 'compliant' else 'badge-non-compliant' if item.status == 'non_compliant' else 'badge-unknown' %}
                <div class="item-detail" id="detail_{{ item.id }}" style="display: none;">
                    <div class="item-header">
                        <h2 class="item-title">{{ item.name }}</h2>
                        <span class="status-badge {{ status_class }}">{{ status_text }}</span>
                    </div>
                    <div class="item-content">
                        {% if item.status == 'compliant' %}
                        <div class="detail-row">
                            <span class="detail-label">合规说明：</span>
                            <span class="detail-value">符合相关标准要求</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">合规标准：</span>
                            <span class="detail-value">{{ item.standard }}</span>
                        </div>
                        {% elif item.status == 'non_compliant' %}
                        <div class="detail-row error-section">
                            <span class="detail-label">错误位置：</span>
                            <span class="detail-value">{{ item.error_location }}</span>
                        </div>
                        <div class="detail-row error-section">
                            <span class="detail-label">错误原因：</span>
                            <span class="detail-value">{{ item.error_reason }}</span>
                        </div>
                        <div class="detail-row suggestion-section">
                            <span class="detail-label">修改建议：</span>
                            <span class="detail-value">{{ item.suggestion }}</span>
                        </div>
                        <div class="detail-row consequence-section">
                            <span class="detail-label">处罚案例：</span>
                            <span class="detail-value">{{ item.consequence }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">合规标准：</span>
                            <span class="detail-value">{{ item.standard }}</span>
                        </div>
                        {% else %}
                        <div class="detail-row">
                            <span class="detail-label">合规标准：</span>
                            <span class="detail-value">{{ item.standard }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function showItem(itemId) {{
            const allDetails = document.querySelectorAll('.item-detail');
            allDetails.forEach(detail => {{ detail.style.display = 'none'; }});

            const allItems = document.querySelectorAll('.review-item');
            allItems.forEach(item => {{ item.classList.remove('active'); }});

            const selectedDetail = document.getElementById('detail_' + itemId);
            if (selectedDetail) {{ selectedDetail.style.display = 'block'; }}

            const selectedItem = document.getElementById('nav_' + itemId);
            if (selectedItem) {{ selectedItem.classList.add('active'); }}
        }}

        function toggleCategory(categoryId) {{
            const category = document.getElementById(categoryId);
            if (category) {{
                if (category.style.display === 'none') {{
                    category.style.display = 'block';
                }} else {{
                    category.style.display = 'none';
                }}
            }}
        }}

        function filterItems(filterType) {{
            const allItems = document.querySelectorAll('.review-item');
            const allButtons = document.querySelectorAll('.filter-btn');

            allButtons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            allItems.forEach(item => {{
                if (filterType === 'all') {{
                    item.style.display = 'flex';
                }} else if (filterType === 'non_compliant') {{
                    if (item.classList.contains('status-non-compliant')) {{
                        item.style.display = 'flex';
                    }} else {{
                        item.style.display = 'none';
                    }}
                }} else if (filterType === 'compliant') {{
                    if (item.classList.contains('status-compliant')) {{
                        item.style.display = 'flex';
                    }} else {{
                        item.style.display = 'none';
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>
```

## 渲染示例（Python代码）

```python
from jinja2 import Template
import json

# 读取模板
with open('html-template.md', 'r', encoding='utf-8') as f:
    template_content = f.read()

# 提取Jinja2代码部分（从```html到```）
import re
match = re.search(r'```html\n(.*?)\n```', template_content, re.DOTALL)
if match:
    jinja_template = Template(match.group(1))

    # 加载审查数据
    with open('review_data.json', 'r', encoding='utf-8') as f:
        review_data = json.load(f)

    # 渲染HTML
    html_output = jinja_template.render(**review_data)

    # 保存文件
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
```

## 功能特性

- 左侧抽屉式导航，支持分类折叠/展开
- 右侧内容区显示审查点详情
- 筛选功能：全部/合规/不合规
- 不合规项高亮显示（红色）
- 响应式设计，支持移动端
- 单文件输出，内嵌CSS和JavaScript
