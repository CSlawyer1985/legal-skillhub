"""简易批注生成器

生成带批注标记的文本版本（不依赖 python-docx）
"""

from typing import List, Dict, Any
from pathlib import Path


class SimpleAnnotator:
    """简易批注器 - 生成 Markdown 格式的批注文档"""
    
    def __init__(self):
        self.severity_markers = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
        }
    
    def create_annotated_text(self, original_text: str, findings: List[Dict[str, Any]]) -> str:
        """
        创建带批注的文本
        
        在原文中插入批注标记，并生成批注列表
        """
        lines = original_text.split('\n')
        annotated_lines = []
        line_findings = {}  # 行号 -> findings 映射
        
        # 将 findings 映射到行
        for finding in findings:
            line_idx = self._find_relevant_line(lines, finding)
            if line_idx >= 0:
                if line_idx not in line_findings:
                    line_findings[line_idx] = []
                line_findings[line_idx].append(finding)
        
        # 生成带批注的文本
        for idx, line in enumerate(lines):
            annotated_lines.append(line)
            
            if idx in line_findings:
                # 在该行后添加批注
                for finding in line_findings[idx]:
                    marker = self.severity_markers.get(finding.get('severity', 'low'), '⚪')
                    comment = f"  {marker} [{finding.get('severity', 'UNKNOWN').upper()}] {finding.get('location', '')}: {finding.get('description', '')}"
                    annotated_lines.append(comment)
        
        return '\n'.join(annotated_lines)
    
    def create_annotated_markdown(self, original_text: str, findings: List[Dict[str, Any]], 
                                   contract_name: str = "合同") -> str:
        """创建 Markdown 格式的批注文档"""
        lines = [
            f"# 带批注的合同：{contract_name}",
            "",
            "> **说明**：本文档为合同审计后的批注版本，标注了发现的问题和风险点",
            "",
            "---",
            "",
            "## 批注图例",
            "",
            "- 🔴 CRITICAL: 严重问题，必须修改",
            "- 🟠 HIGH: 高风险，强烈建议修改",
            "- 🟡 MEDIUM: 中风险，建议修改",
            "- 🟢 LOW: 低风险，可选修改",
            "",
            "---",
            "",
            "## 合同正文（带批注）",
            "",
            "```",
        ]
        
        # 添加带批注的正文
        original_lines = original_text.split('\n')
        line_findings = {}
        
        for finding in findings:
            line_idx = self._find_relevant_line(original_lines, finding)
            if line_idx >= 0:
                if line_idx not in line_findings:
                    line_findings[line_idx] = []
                line_findings[line_idx].append(finding)
        
        for idx, line in enumerate(original_lines):
            lines.append(line)
            
            if idx in line_findings:
                for finding in line_findings[idx]:
                    marker = self.severity_markers.get(finding.get('severity', 'low'), '⚪')
                    comment = f">>> {marker} [{finding.get('severity', 'UNKNOWN').upper()}] {finding.get('location', '')}"
                    lines.append(comment)
                    lines.append(f">>>   问题：{finding.get('description', '')}")
                    lines.append(f">>>   建议：{finding.get('suggestion', '')}")
        
        lines.extend([
            "```",
            "",
            "---",
            "",
            "## 审计摘要",
            "",
        ])
        
        # 添加摘要
        total = len(findings)
        by_severity = {}
        for f in findings:
            sev = f.get('severity', 'unknown')
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        lines.append(f"**发现问题总数**：{total} 项")
        lines.append("")
        
        if by_severity:
            lines.append("**严重程度分布**：")
            severity_order = ['critical', 'high', 'medium', 'low']
            for sev in severity_order:
                count = by_severity.get(sev, 0)
                if count > 0:
                    marker = self.severity_markers.get(sev, '⚪')
                    lines.append(f"- {marker} {sev.upper()}: {count} 项")
            lines.append("")
        
        # 添加问题清单
        lines.extend([
            "## 问题清单",
            "",
        ])
        
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.get('severity', 'low'), 4))
        
        for i, f in enumerate(sorted_findings, 1):
            marker = self.severity_markers.get(f.get('severity', 'low'), '⚪')
            lines.append(f"### {i}. {marker} [{f.get('severity', 'UNKNOWN').upper()}] {f.get('location', '')}")
            lines.append(f"- **类别**：{f.get('category', '未分类')}")
            lines.append(f"- **问题**：{f.get('description', '')}")
            lines.append(f"- **建议**：{f.get('suggestion', '')}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _find_relevant_line(self, lines: List[str], finding: Dict[str, Any]) -> int:
        """查找与 finding 相关的行号"""
        # 从 location 和 description 中提取关键词
        keywords = self._extract_keywords(finding.get('location', '') + ' ' + finding.get('description', ''))
        
        best_match_idx = -1
        best_match_score = 0
        
        for idx, line in enumerate(lines):
            line_text = line.strip()
            if not line_text:
                continue
            
            score = 0
            for kw in keywords:
                if kw in line_text:
                    score += 1
            
            if score > best_match_score:
                best_match_score = score
                best_match_idx = idx
        
        return best_match_idx
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re
        # 提取中文关键词（2-6个字的词组）
        words = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
        # 去重并返回
        seen = set()
        result = []
        for w in words:
            if w not in seen and len(w) >= 2:
                seen.add(w)
                result.append(w)
        return result[:10]


def create_annotated_markdown(original_text: str, findings: List[Dict[str, Any]], 
                               contract_name: str = "合同") -> str:
    """便捷函数：创建带批注的 Markdown 文档"""
    annotator = SimpleAnnotator()
    return annotator.create_annotated_markdown(original_text, findings, contract_name)


if __name__ == '__main__':
    # 测试
    test_text = """技术服务合同

第一条 合同金额
本合同总金额为人民币壹拾万元整。

第二条 交付时间
乙方应在合理时间内完成交付。
"""
    
    test_findings = [
        {
            'category': '金额条款',
            'severity': 'medium',
            'location': '金额条款',
            'description': '合同仅有中文大写金额，缺少阿拉伯数字金额对照',
            'suggestion': '建议同时标注阿拉伯数字金额'
        },
        {
            'category': '交付条款',
            'severity': 'medium',
            'location': '交付时间',
            'description': '交付时间描述不够具体',
            'suggestion': '建议明确具体日期或期限'
        }
    ]
    
    annotator = SimpleAnnotator()
    result = annotator.create_annotated_markdown(test_text, test_findings, "测试合同")
    print(result)
