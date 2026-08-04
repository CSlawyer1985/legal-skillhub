"""交付条款分析器"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeliveryFinding:
    """交付条款发现项"""
    severity: str
    location: str
    description: str
    suggestion: str


class DeliveryAnalyzer:
    """交付条款分析器"""
    
    def __init__(self):
        self.time_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})个月内',
            r'(\d{1,2})个工作日内',
            r'合同签订后(\d{1,2})天',
        ]
    
    def analyze(self, text: str) -> List[DeliveryFinding]:
        """分析交付条款"""
        findings = []
        
        findings.extend(self._check_delivery_time(text))
        findings.extend(self._check_acceptance_standard(text))
        findings.extend(self._check_delay_responsibility(text))
        findings.extend(self._check_deliverables(text))
        
        return findings
    
    def _check_delivery_time(self, text: str) -> List[DeliveryFinding]:
        """检查交付时间是否明确"""
        findings = []
        
        # 检查是否有交付时间描述
        delivery_keywords = ['交付', '完成', '验收', '上线', '实施完成']
        has_delivery = any(kw in text for kw in delivery_keywords)
        
        if not has_delivery:
            findings.append(DeliveryFinding(
                severity='high',
                location='交付时间',
                description='合同未明确约定交付时间',
                suggestion='必须明确约定交付时间，如：2024年6月30日前完成交付'
            ))
            return findings
        
        # 检查时间是否具体
        has_specific_date = any(re.search(p, text) for p in self.time_patterns)
        
        if not has_specific_date:
            findings.append(DeliveryFinding(
                severity='medium',
                location='交付时间',
                description='交付时间描述不够具体',
                suggestion='建议明确具体日期或期限，如：合同签订后30个工作日内完成交付'
            ))
        
        # 检查是否有分期交付
        if '阶段' in text or '分期' in text or '里程碑' in text:
            if not re.search(r'(第一阶段|第二阶段|第三期).{0,10}(\d{4}|\d{1,2}个月)', text):
                findings.append(DeliveryFinding(
                    severity='low',
                    location='分期交付',
                    description='提到分期/阶段交付，但未明确各阶段时间节点',
                    suggestion='建议明确各阶段交付时间和交付物'
                ))
        
        return findings
    
    def _check_acceptance_standard(self, text: str) -> List[DeliveryFinding]:
        """检查验收标准"""
        findings = []
        
        acceptance_keywords = ['验收', '验收标准', '验收条件', '验收通过']
        has_acceptance = any(kw in text for kw in acceptance_keywords)
        
        if not has_acceptance:
            findings.append(DeliveryFinding(
                severity='high',
                location='验收标准',
                description='合同未约定验收标准',
                suggestion='必须明确验收标准和验收流程，避免交付后争议'
            ))
            return findings
        
        # 检查验收标准是否可量化
        quantifiable_keywords = ['功能测试', '性能测试', '测试报告', '符合', '达到', '指标']
        is_quantifiable = any(kw in text for kw in quantifiable_keywords)
        
        if not is_quantifiable:
            findings.append(DeliveryFinding(
                severity='medium',
                location='验收标准',
                description='验收标准描述较模糊，缺乏可量化指标',
                suggestion='建议增加可量化的验收指标，如：系统响应时间<2秒，并发支持1000用户'
            ))
        
        # 检查验收期限
        if '验收' in text:
            if not re.search(r'(验收).{0,15}(\d{1,2}).{0,5}(工作日|天|日)', text):
                findings.append(DeliveryFinding(
                    severity='medium',
                    location='验收期限',
                    description='验收期限未明确约定',
                    suggestion='建议约定：甲方应在收到交付物后X个工作日内完成验收，逾期视为验收通过'
                ))
        
        return findings
    
    def _check_delay_responsibility(self, text: str) -> List[DeliveryFinding]:
        """检查延期责任"""
        findings = []
        
        # 检查是否有延期责任约定
        delay_keywords = ['延期', '逾期', '延迟交付']
        has_delay = any(kw in text for kw in delay_keywords)
        
        if not has_delay:
            findings.append(DeliveryFinding(
                severity='medium',
                location='延期责任',
                description='合同未约定延期交付的违约责任',
                suggestion='建议增加延期违约金条款，如：每延期一日按合同总额的万分之五支付违约金'
            ))
            return findings
        
        # 检查延期责任是否对等
        if '甲方原因' in text or '乙方原因' in text:
            # 检查是否区分双方责任
            if '甲方原因' in text and '乙方原因' not in text:
                findings.append(DeliveryFinding(
                    severity='low',
                    location='延期责任',
                    description='延期责任条款偏向甲方，未明确区分双方责任',
                    suggestion='建议明确区分：因甲方原因（如需求变更、资料延迟）导致的延期，乙方不承担责任'
                ))
        
        return findings
    
    def _check_deliverables(self, text: str) -> List[DeliveryFinding]:
        """检查交付物清单"""
        findings = []
        
        deliverable_keywords = ['交付物', '交付成果', '交付清单', '源代码', '文档']
        has_deliverables = any(kw in text for kw in deliverable_keywords)
        
        if not has_deliverables:
            findings.append(DeliveryFinding(
                severity='medium',
                location='交付物',
                description='合同未明确约定交付物清单',
                suggestion='建议列明交付物清单：软件安装包、源代码、技术文档、用户手册、测试报告等'
            ))
        
        # 检查知识产权归属
        ip_keywords = ['知识产权', '著作权', '版权', '所有权', '归属']
        has_ip = any(kw in text for kw in ip_keywords)
        
        if not has_ip:
            findings.append(DeliveryFinding(
                severity='high',
                location='知识产权',
                description='合同未约定知识产权归属',
                suggestion='必须明确约定：交付物的知识产权归属（通常归甲方或双方共有）'
            ))
        
        return findings


def analyze_delivery_terms(text: str) -> List[Dict[str, Any]]:
    """便捷函数：分析交付条款"""
    analyzer = DeliveryAnalyzer()
    findings = analyzer.analyze(text)
    return [
        {
            'severity': f.severity,
            'location': f.location,
            'description': f.description,
            'suggestion': f.suggestion
        }
        for f in findings
    ]


if __name__ == '__main__':
    # 测试
    test_text = """
    乙方应在合同签订后完成系统开发并交付甲方。
    甲方验收合格后支付尾款。
    """
    
    findings = analyze_delivery_terms(test_text)
    for f in findings:
        print(f"[{f['severity']}] {f['location']}: {f['description']}")
        print(f"  建议: {f['suggestion']}\n")
