#!/usr/bin/env python3
"""
报告格式化工具 - 格式化PIPL合规报告
"""

import json
import csv
import html
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class ReportFormatter:
    """报告格式化工具类"""
    
    @staticmethod
    def format_json_report(report_data: Dict[str, Any], pretty: bool = True) -> str:
        """
        格式化JSON报告
        
        Args:
            report_data: 报告数据
            pretty: 是否美化输出
        
        Returns:
            str: 格式化后的JSON字符串
        """
        try:
            if pretty:
                return json.dumps(report_data, indent=2, ensure_ascii=False, default=str)
            else:
                return json.dumps(report_data, ensure_ascii=False, default=str)
        except Exception as e:
            raise ValueError(f"JSON格式化失败: {e}")
    
    @staticmethod
    def format_html_report(report_data: Dict[str, Any], template: str = None) -> str:
        """
        格式化HTML报告
        
        Args:
            report_data: 报告数据
            template: HTML模板（可选）
        
        Returns:
            str: 格式化后的HTML字符串
        """
        if template:
            html_content = template
        else:
            html_content = ReportFormatter._get_default_html_template()
        
        # 替换变量
        variables = ReportFormatter._extract_report_variables(report_data)
        for key, value in variables.items():
            placeholder = '{' + key + '}'
            html_content = html_content.replace(placeholder, html.escape(str(value)))
        
        # 格式化表格内容
        if 'checklist' in report_data:
            table_html = ReportFormatter._format_checklist_table(report_data['checklist'])
            html_content = html_content.replace('{checklist_table}', table_html)
        
        if 'risk_assessment' in report_data:
            risk_html = ReportFormatter._format_risk_assessment(report_data['risk_assessment'])
            html_content = html_content.replace('{risk_assessment}', risk_html)
        
        return html_content
    
    @staticmethod
    def format_csv_report(report_data: Dict[str, Any], 
                          include_checklist: bool = True) -> str:
        """
        格式化CSV报告
        
        Args:
            report_data: 报告数据
            include_checklist: 是否包含检查清单
        
        Returns:
            str: 格式化后的CSV字符串
        """
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入报告头信息
        writer.writerow(['PIPL合规检查报告'])
        writer.writerow(['报告编号', report_data.get('report_id', 'N/A')])
        writer.writerow(['企业名称', report_data.get('company_name', 'N/A')])
        writer.writerow(['检查日期', report_data.get('check_date', 'N/A')])
        writer.writerow(['总体得分', report_data.get('overall_score', 'N/A')])
        writer.writerow(['合规等级', report_data.get('compliance_level', 'N/A')])
        writer.writerow([])
        
        # 写入检查清单
        if include_checklist and 'checklist' in report_data:
            writer.writerow(['检查清单'])
            writer.writerow(['ID', '类别', '要求', '状态', '得分', '重要性', '备注'])
            
            for item in report_data['checklist']:
                writer.writerow([
                    item.get('id', ''),
                    item.get('category', ''),
                    item.get('requirement', ''),
                    item.get('status', ''),
                    item.get('score', ''),
                    item.get('importance', ''),
                    item.get('notes', '')
                ])
            
            writer.writerow([])
        
        # 写入风险评估
        if 'risk_assessment' in report_data:
            risk_data = report_data['risk_assessment']
            writer.writerow(['风险评估'])
            writer.writerow(['总体风险等级', risk_data.get('overall_risk_level', 'N/A')])
            writer.writerow(['高风险数量', risk_data.get('high_risk_count', 0)])
            writer.writerow(['中风险数量', risk_data.get('medium_risk_count', 0)])
            writer.writerow(['低风险数量', risk_data.get('low_risk_count', 0)])
            writer.writerow([])
            
            # 写入风险项
            if 'risks' in risk_data:
                writer.writerow(['风险详情'])
                writer.writerow(['风险项', '风险等级', '影响程度', '可能性', '建议措施'])
                
                for risk in risk_data['risks']:
                    writer.writerow([
                        risk.get('item', ''),
                        risk.get('level', ''),
                        risk.get('impact', ''),
                        risk.get('likelihood', ''),
                        risk.get('recommendation', '')
                    ])
        
        return output.getvalue()
    
    @staticmethod
    def format_text_report(report_data: Dict[str, Any]) -> str:
        """
        格式化文本报告
        
        Args:
            report_data: 报告数据
        
        Returns:
            str: 格式化后的文本字符串
        """
        lines = []
        
        # 报告头
        lines.append("=" * 60)
        lines.append("PIPL合规检查报告")
        lines.append("=" * 60)
        lines.append(f"报告编号: {report_data.get('report_id', 'N/A')}")
        lines.append(f"企业名称: {report_data.get('company_name', 'N/A')}")
        lines.append(f"检查日期: {report_data.get('check_date', 'N/A')}")
        lines.append(f"报告生成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 执行摘要
        lines.append("一、执行摘要")
        lines.append("-" * 40)
        lines.append(f"总体合规得分: {report_data.get('overall_score', 'N/A')}/100")
        lines.append(f"合规等级: {report_data.get('compliance_level', 'N/A')}")
        lines.append("")
        
        if 'key_findings' in report_data:
            lines.append("关键发现:")
            for finding in report_data['key_findings']:
                lines.append(f"  • {finding}")
            lines.append("")
        
        if 'improvement_suggestions' in report_data:
            lines.append("改进建议:")
            for suggestion in report_data['improvement_suggestions']:
                lines.append(f"  • {suggestion}")
            lines.append("")
        
        # 检查清单
        if 'checklist' in report_data:
            lines.append("二、详细检查结果")
            lines.append("-" * 40)
            
            completed = sum(1 for item in report_data['checklist'] if item.get('status') == 'completed')
            total = len(report_data['checklist'])
            
            lines.append(f"检查项完成情况: {completed}/{total} ({completed/total*100:.1f}%)")
            lines.append("")
            
            # 按类别分组显示
            categories = {}
            for item in report_data['checklist']:
                category = item.get('category', '其他')
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
            
            for category, items in categories.items():
                lines.append(f"{category}:")
                for item in items:
                    status_symbol = "✅" if item.get('status') == 'completed' else "❌"
                    lines.append(f"  {status_symbol} {item.get('requirement', '')} ({item.get('score', 0)}分)")
                lines.append("")
        
        # 风险评估
        if 'risk_assessment' in report_data:
            risk_data = report_data['risk_assessment']
            lines.append("三、风险评估")
            lines.append("-" * 40)
            lines.append(f"总体风险等级: {risk_data.get('overall_risk_level', 'N/A')}")
            lines.append("")
            
            if 'risks' in risk_data:
                lines.append("高风险项:")
                for risk in [r for r in risk_data['risks'] if r.get('level') == 'high']:
                    lines.append(f"  ⚠️  {risk.get('item', '')}")
                    lines.append(f"     建议: {risk.get('recommendation', '')}")
                lines.append("")
        
        # 结论
        lines.append("四、结论")
        lines.append("-" * 40)
        lines.append(report_data.get('conclusion', '检查完成。'))
        lines.append("")
        
        lines.append("=" * 60)
        lines.append("报告结束")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_markdown_report(report_data: Dict[str, Any]) -> str:
        """
        格式化Markdown报告
        
        Args:
            report_data: 报告数据
        
        Returns:
            str: 格式化后的Markdown字符串
        """
        lines = []
        
        # 报告头
        lines.append(f"# PIPL合规检查报告")
        lines.append("")
        lines.append(f"**报告编号**: {report_data.get('report_id', 'N/A')}  ")
        lines.append(f"**企业名称**: {report_data.get('company_name', 'N/A')}  ")
        lines.append(f"**检查日期**: {report_data.get('check_date', 'N/A')}  ")
        lines.append(f"**报告生成**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append("")
        
        # 执行摘要
        lines.append("## 一、执行摘要")
        lines.append("")
        lines.append(f"**总体合规得分**: {report_data.get('overall_score', 'N/A')}/100  ")
        lines.append(f"**合规等级**: {report_data.get('compliance_level', 'N/A')}  ")
        lines.append("")
        
        if 'key_findings' in report_data:
            lines.append("**关键发现**:")
            lines.append("")
            for finding in report_data['key_findings']:
                lines.append(f"- {finding}")
            lines.append("")
        
        if 'improvement_suggestions' in report_data:
            lines.append("**改进建议**:")
            lines.append("")
            for suggestion in report_data['improvement_suggestions']:
                lines.append(f"- {suggestion}")
            lines.append("")
        
        # 检查清单
        if 'checklist' in report_data:
            lines.append("## 二、详细检查结果")
            lines.append("")
            
            completed = sum(1 for item in report_data['checklist'] if item.get('status') == 'completed')
            total = len(report_data['checklist'])
            completion_rate = completed/total*100 if total > 0 else 0
            
            lines.append(f"**检查项完成情况**: {completed}/{total} ({completion_rate:.1f}%)")
            lines.append("")
            
            # 创建表格
            lines.append("| 检查项 | 类别 | 状态 | 得分 | 重要性 | 备注 |")
            lines.append("|--------|------|------|------|--------|------|")
            
            for item in report_data['checklist']:
                status_emoji = "✅" if item.get('status') == 'completed' else "❌"
                lines.append(f"| {item.get('requirement', '')} | {item.get('category', '')} | {status_emoji} | {item.get('score', 0)} | {item.get('importance', '')} | {item.get('notes', '')} |")
            
            lines.append("")
        
        # 风险评估
        if 'risk_assessment' in report_data:
            risk_data = report_data['risk_assessment']
            lines.append("## 三、风险评估")
            lines.append("")
            lines.append(f"**总体风险等级**: {risk_data.get('overall_risk_level', 'N/A')}  ")
            lines.append("")
            
            if 'risks' in risk_data:
                lines.append("### 高风险项")
                lines.append("")
                for risk in [r for r in risk_data['risks'] if r.get('level') == 'high']:
                    lines.append(f"**{risk.get('item', '')}**  ")
                    lines.append(f"风险等级: ⚠️ 高风险  ")
                    lines.append(f"建议措施: {risk.get('recommendation', '')}  ")
                    lines.append("")
        
        # 结论
        lines.append("## 四、结论")
        lines.append("")
        lines.append(report_data.get('conclusion', '检查完成。'))
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_default_html_template() -> str:
        """获取默认HTML模板"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PIPL合规检查报告 - {company_name}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; }
        .section { margin-bottom: 30px; }
        .section-title { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f4f4f4; }
        .score { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .completed { color: green; }
        .failed { color: red; }
        .risk-high { color: red; font-weight: bold; }
        .risk-medium { color: orange; }
        .risk-low { color: green; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PIPL合规检查报告</h1>
        <p><strong>报告编号</strong>: {report_id}</p>
        <p><strong>企业名称</strong>: {company_name}</p>
        <p><strong>检查日期</strong>: {check_date}</p>
        <p><strong>报告生成</strong>: {report_date}</p>
    </div>
    
    <div class="section">
        <h2 class="section-title">执行摘要</h2>
        <p><strong>总体合规得分</strong>: <span class="score">{overall_score}/100</span></p>
        <p><strong>合规等级</strong>: {compliance_level}</p>
        
        <h3>关键发现</h3>
        <ul>
            <li>示例关键发现1</li>
            <li>示例关键发现2</li>
        </ul>
        
        <h3>改进建议</h3>
        <ul>
            <li>示例改进建议1</li>
            <li>示例改进建议2</li>
        </ul>
    </div>
    
    <div class="section">
        <h2 class="section-title">详细检查结果</h2>
        {checklist_table}
    </div>
    
    <div class="section">
        <h2 class="section-title">风险评估</h2>
        {risk_assessment}
    </div>
    
    <div class="section">
        <h2 class="section-title">结论</h2>
        <p>{conclusion}</p>
    </div>
</body>
</html>"""
    
    @staticmethod
    def _extract_report_variables(report_data: Dict[str, Any]) -> Dict[str, Any]:
        """从报告数据中提取模板变量"""
        variables = {
            'report_id': report_data.get('report_id', 'N/A'),
            'company_name': report_data.get('company_name', 'N/A'),
            'check_date': report_data.get('check_date', 'N/A'),
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': report_data.get('overall_score', 'N/A'),
            'compliance_level': report_data.get('compliance_level', 'N/A'),
            'conclusion': report_data.get('conclusion', '检查完成。')
        }
        
        # 处理关键发现
        if 'key_findings' in report_data:
            findings_html = '<ul>' + ''.join(f'<li>{html.escape(f)}</li>' for f in report_data['key_findings']) + '</ul>'
            variables['key_findings'] = findings_html
        
        # 处理改进建议
        if 'improvement_suggestions' in report_data:
            suggestions_html = '<ul>' + ''.join(f'<li>{html.escape(s)}</li>' for s in report_data['improvement_suggestions']) + '</ul>'
            variables['improvement_suggestions'] = suggestions_html
        
        return variables
    
    @staticmethod
    def _format_checklist_table(checklist_data: List[Dict[str, Any]]) -> str:
        """格式化检查清单表格"""
        if not checklist_data:
            return '<p>无检查数据</p>'
        
        completed = sum(1 for item in checklist_data if item.get('status') == 'completed')
        total = len(checklist_data)
        
        summary = f'<p><strong>检查项完成情况</strong>: {completed}/{total} ({completed/total*100:.1f}%)</p>'
        
        table = '<table>\n<thead>\n<tr>\n'
        table += '<th>检查项</th>\n<th>类别</th>\n<th>状态</th>\n<th>得分</th>\n<th>重要性</th>\n<th>备注</th>\n'
