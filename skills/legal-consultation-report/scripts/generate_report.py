#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律咨询报告生成脚本
根据案情数据生成精美的HTML咨询报告
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 报告HTML模板
REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Microsoft YaHei", "PingFang SC", "SimSun", sans-serif;
        }}
        body {{
            background-color: #f7f8fa;
            color: #333333;
            line-height: 1.8;
            padding: 30px 20px;
        }}
        .container {{
            max-width: 1140px;
            margin: 0 auto;
            background: #ffffff;
            padding: 60px;
            border-radius: 6px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
        }}
        .download-wrap {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .download-btn {{
            display: inline-block;
            padding: 12px 36px;
            background: #1a4996;
            color: #fff;
            font-size: 16px;
            font-weight: 500;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s ease;
        }}
        .download-btn:hover {{
            background: #0f387d;
        }}
        .main-title {{
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            color: #1a4996;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e5eaf3;
        }}
        .subtitle {{
            text-align: center;
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
        }}
        .to-info {{
            text-align: right;
            font-size: 15px;
            color: #666;
            margin-bottom: 30px;
        }}
        .intro {{
            font-size: 15px;
            margin-bottom: 25px;
            text-align: justify;
            color: #444;
        }}
        h2 {{
            font-size: 20px;
            color: #1a4996;
            margin: 40px 0 20px;
            padding-left: 12px;
            border-left: 4px solid #1a4996;
            font-weight: 600;
        }}
        h3 {{
            font-size: 17px;
            color: #333;
            margin: 25px 0 15px;
            font-weight: 600;
        }}
        p {{
            font-size: 15px;
            margin-bottom: 15px;
            text-align: justify;
        }}
        .requirement-item {{
            background: #f8f9fc;
            padding: 15px 20px;
            margin-bottom: 12px;
            border-radius: 4px;
            border-left: 3px solid #1a4996;
        }}
        .requirement-item strong {{
            color: #1a4996;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0 30px;
            font-size: 14px;
            page-break-inside: avoid;
        }}
        table th {{
            background: #e5eaf3;
            color: #1a4996;
            font-weight: 600;
            text-align: left;
            padding: 12px 15px;
            border: 1px solid #d6dce7;
        }}
        table td {{
            padding: 12px 15px;
            border: 1px solid #d6dce7;
            vertical-align: top;
        }}
        table tr:nth-child(even) {{
            background-color: #fafbfc;
        }}
        .risk-high {{
            color: #c9302c;
            font-weight: 600;
        }}
        .risk-medium {{
            color: #ec971f;
            font-weight: 600;
        }}
        .risk-low {{
            color: #5cb85c;
            font-weight: 600;
        }}
        .solution-item {{
            margin-bottom: 20px;
            padding: 15px;
            background: #fafbfd;
            border-radius: 4px;
        }}
        .solution-title {{
            font-weight: 600;
            color: #1a4996;
            margin-bottom: 8px;
        }}
        ul {{
            margin: 0 0 20px 25px;
        }}
        ul li {{
            margin-bottom: 8px;
            font-size: 15px;
        }}
        .package-card {{
            background: linear-gradient(135deg, #f8f9fc 0%, #e8ecf4 100%);
            border: 1px solid #d6dce7;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }}
        .package-name {{
            font-size: 18px;
            font-weight: 600;
            color: #1a4996;
            margin-bottom: 10px;
        }}
        .package-price {{
            font-size: 28px;
            font-weight: 700;
            color: #1a4996;
            margin-bottom: 15px;
        }}
        .package-features {{
            margin-top: 15px;
        }}
        .cta-box {{
            background: linear-gradient(135deg, #1a4996 0%, #2d5bb8 100%);
            color: #fff;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            margin: 40px 0;
        }}
        .cta-box h3 {{
            color: #fff;
            font-size: 20px;
            margin-bottom: 15px;
        }}
        .cta-box p {{
            color: #e0e6f0;
            text-align: center;
        }}
        .footer-info {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e5eaf3;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
        .footer-info p {{
            margin-bottom: 5px;
            text-align: center;
        }}
        .contact-item {{
            display: inline-block;
            margin: 0 15px;
        }}
        @media print {{
            body {{ background: #fff; }}
            .container {{ box-shadow: none; }}
            .download-wrap {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="download-wrap">
            <button class="download-btn" onclick="saveReport()">📄 一键下载本报告</button>
        </div>

        <h1 class="main-title">{title}</h1>
        {subtitle_html}
        <div class="to-info">
            致：{client_name}{contacts_html}
        </div>

        <div class="intro">
            {intro_text}
        </div>

        <h2>一、客户需求</h2>
        <p>结合{client_name}的实际情况与法律服务需求，本次咨询聚焦以下核心诉求：</p>
        {requirements_html}

        <h2>二、核心事实梳理</h2>
        <p>基于本次咨询沟通，我方对相关事实要点梳理如下：</p>
        {facts_html}

        <h2>三、法律关系分析</h2>
        <p>针对上述事实，我方对涉及的法律关系进行如下分析：</p>
        {relations_html}

        <h2>四、潜在风险提示</h2>
        <p>结合现行法律规定及司法实践，本次咨询涉及的主要法律风险如下：</p>
        {risks_html}

        <h2>五、解决方案建议</h2>
        <p>针对上述风险，我方提出以下专业解决方案：</p>
        {solutions_html}

        {packages_html}

        <div class="cta-box">
            <h3>立即行动 · 守护您的合法权益</h3>
            <p>上述法律风险不容忽视，及时专业介入是保护您权益的关键。</p>
            <p style="margin-top:15px;">我们建议您尽快与我们取得联系，让我们为您的案件提供全程专业法律服务。</p>
        </div>

        <p>{closing_text}</p>

        <div class="footer-info">
            <p><strong>咨询律师：{lawyer_name}</strong></p>
            {team_html}
            {advantages_html}
            {validity_html}
        </div>
    </div>

    <script>
        function saveReport() {{
            const htmlContent = document.documentElement.outerHTML;
            const blob = new Blob([htmlContent], {{ type: 'text/html;charset=utf-8' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = '{download_filename}';
            link.click();
            URL.revokeObjectURL(link.href);
        }}
    </script>
</body>
</html>"""


def build_requirements_html(requirements):
    """构建客户需求HTML"""
    html = ""
    for i, req in enumerate(requirements, 1):
        if isinstance(req, dict):
            html += f'''<div class="requirement-item">
                <strong>{i}. {req.get('title', '需求项')}</strong><br>
                {req.get('description', '')}
            </div>'''
        else:
            html += f'<div class="requirement-item"><strong>{i}.</strong> {req}</div>'
    return html


def build_facts_html(facts):
    """构建核心事实HTML"""
    html = '<table><thead><tr><th>序号</th><th>事实要点</th><th>法律意义</th></tr></thead><tbody>'
    for i, fact in enumerate(facts, 1):
        if isinstance(fact, dict):
            html += f'<tr><td>{i}</td><td>{fact.get("fact", "")}</td><td>{fact.get("legal_significance", "-")}</td></tr>'
        else:
            html += f'<tr><td>{i}</td><td>{fact}</td><td>-</td></tr>'
    html += '</tbody></table>'
    return html


def build_relations_html(relations):
    """构建法律关系HTML"""
    html = ""
    for i, rel in enumerate(relations, 1):
        if isinstance(rel, dict):
            html += f'''<div class="requirement-item">
                <strong>{i}. {rel.get('title', '法律关系')}</strong><br>
                主体：{rel.get('parties', '-')}；<br>
                性质：{rel.get('nature', '-')}；<br>
                说明：{rel.get('description', '-')}
            </div>'''
        else:
            html += f'<div class="requirement-item"><strong>{i}.</strong> {rel}</div>'
    return html


def build_risks_html(risks):
    """构建风险提示HTML"""
    html = '<table><thead><tr><th>风险等级</th><th>风险事项</th><th>潜在后果</th><th>建议优先级</th></tr></thead><tbody>'
    risk_level_map = {'高': ('risk-high', '高'), '中': ('risk-medium', '中'), '低': ('risk-low', '低')}
    
    for risk in risks:
        if isinstance(risk, dict):
            level = risk.get('level', '中')
            level_class, level_text = risk_level_map.get(level, ('risk-medium', level))
            html += f'''<tr>
                <td><span class="{level_class}">{level_text}</span></td>
                <td>{risk.get('item', '')}</td>
                <td>{risk.get('consequence', '-')}</td>
                <td>{risk.get('priority', '-')}</td>
            </tr>'''
        else:
            html += f'<tr><td><span class="risk-medium">中</span></td><td>{risk}</td><td>-</td><td>-</td></tr>'
    html += '</tbody></table>'
    return html


def build_solutions_html(solutions):
    """构建解决方案HTML"""
    html = ""
    for i, sol in enumerate(solutions, 1):
        if isinstance(sol, dict):
            html += f'''<div class="solution-item">
                <div class="solution-title">{i}. {sol.get('title', '建议')}</div>
                <div>{sol.get('description', sol)}</div>
                {f'<div style="margin-top:10px;"><strong>预期效果：</strong>{sol.get("effect", "")}</div>' if sol.get('effect') else ''}
            </div>'''
        else:
            html += f'<div class="solution-item"><div class="solution-title">{i}.</div><div>{sol}</div></div>'
    return html


def build_packages_html(packages):
    """构建服务方案HTML"""
    if not packages:
        return ""
    
    html = '<h2>六、服务方案与报价</h2><p>我方根据贵方需求，设计以下服务方案供选择：</p>'
    
    for pkg in packages:
        html += f'''<div class="package-card">
            <div class="package-name">{pkg.get('name', '基础服务包')}</div>
            <div class="package-price">{pkg.get('price', '面议')}</div>
            <p>{pkg.get('description', '')}</p>
            <div class="package-features">
                <strong>服务内容包括：</strong>
                <ul>
    '''
        for feature in pkg.get('features', []):
            html += f'<li>{feature}</li>'
        html += '''
                </ul>
            </div>
        </div>'''
    
    html += f'<p><strong>报价有效期：</strong>{packages[0].get("validity", "自报价之日起15个自然日")}</p>'
    return html


def generate_report(data):
    """生成完整HTML报告"""
    # 构建各部分HTML
    subtitle_html = f'<div class="subtitle">{data.get("report_subtitle", "")}</div>' if data.get("report_subtitle") else ''
    contacts_html = f'（{data["client_contacts"]}）' if data.get("client_contacts") else ''
    
    # 构建介绍文本
    intro_parts = [
        f"我方（{data.get('lawyer_name', '咨询律师')}）立足贵方的实际情况与法律服务需求，"
        f"依托专业法律知识与丰富实践经验，结合现行法律规定及司法实践，"
    ]
    if data.get('core_advantages'):
        intro_parts.append(f"发挥{data['core_advantages']}的核心优势，")
    intro_parts.append("特出具本专项咨询报告。")
    intro_text = ''.join(intro_parts)
    
    team_html = f'<p>服务团队：{data["lawyer_team"]}</p>' if data.get("lawyer_team") else ''
    advantages_html = f'<p>核心优势：{data["core_advantages"]}</p>' if data.get("core_advantages") else ''
    validity_html = f'<p>报价有效期：{data.get("validity_period", "自报价之日起15个自然日")}</p>' if data.get("validity_period") else ''
    
    # 生成下载文件名
    download_filename = f'{data["client_name"]}法律风险咨询报告.html'
    
    # 填充模板
    html = REPORT_TEMPLATE.format(
        title=data.get('report_title', f'{data["client_name"]}法律风险咨询报告'),
        subtitle_html=subtitle_html,
        client_name=data['client_name'],
        contacts_html=contacts_html,
        intro_text=data.get('consultation_background', intro_text),
        requirements_html=build_requirements_html(data.get('core_requirements', [])),
        facts_html=build_facts_html(data.get('key_facts', [])),
        relations_html=build_relations_html(data.get('legal_relations', [])),
        risks_html=build_risks_html(data.get('risk_items', [])),
        solutions_html=build_solutions_html(data.get('solutions', [])),
        packages_html=build_packages_html(data.get('service_packages', [])),
        closing_text=data.get('closing_message', '我方将持续关注贵方法律服务需求，期待与贵方达成合作，以专业服务为贵方权益保驾护航。'),
        lawyer_name=data.get('lawyer_name', '咨询律师'),
        team_html=team_html,
        advantages_html=advantages_html,
        validity_html=validity_html,
        download_filename=download_filename
    )
    
    return html


def main():
    parser = argparse.ArgumentParser(description='生成法律咨询报告HTML')
    parser.add_argument('--case_data', type=str, help='JSON格式的案情数据')
    parser.add_argument('--case_file', type=str, help='包含案情数据的JSON文件路径')
    parser.add_argument('--output', type=str, help='输出HTML文件路径')
    
    args = parser.parse_args()
    
    # 读取数据
    if args.case_file:
        with open(args.case_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif args.case_data:
        data = json.loads(args.case_data)
    else:
        print(json.dumps({'status': 'error', 'message': '请提供 --case_data 或 --case_file 参数'}))
        sys.exit(1)
    
    # 生成报告
    html_content = generate_report(data)
    
    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html_content)
        result = {'status': 'success', 'output': args.output, 'message': f'报告已生成: {args.output}'}
    else:
        # 输出到stdout
        print(html_content)
        result = {'status': 'success', 'message': '报告已输出'}
    
    # 返回JSON结果
    if not args.output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
