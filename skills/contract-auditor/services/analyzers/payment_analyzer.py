"""金额条款分析器"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PaymentFinding:
    """金额条款发现项"""
    severity: str  # critical/high/medium/low
    location: str
    description: str
    suggestion: str


class PaymentAnalyzer:
    """金额条款分析器"""
    
    # 中文数字映射
    CN_NUMBERS = {
        '零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4,
        '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
        '拾': 10, '佰': 100, '仟': 1000, '万': 10000,
        '亿': 100000000
    }
    
    def __init__(self):
        self.patterns = {
            'amount_cn': r'[壹贰叁肆伍陆柒捌玖拾佰仟万亿]+元',
            'amount_num': r'\d{1,3}(,\d{3})*\.?\d*\s*[万元]',
            'payment_node': r'((首付|预付款|定金|首款).{0,10}(\d+%|百分之[一二三四五六七八九十]+))',
            'penalty': r'(违约金|滞纳金|逾期).{0,20}(\d+%|千分之[一二三四五六七八九十]+)',
        }
    
    def analyze(self, text: str) -> List[PaymentFinding]:
        """分析金额条款"""
        findings = []
        
        # 1. 检查金额一致性
        findings.extend(self._check_amount_consistency(text))
        
        # 2. 检查付款节点
        findings.extend(self._check_payment_nodes(text))
        
        # 3. 检查违约金条款
        findings.extend(self._check_penalty(text))
        
        # 4. 检查发票条款
        findings.extend(self._check_invoice(text))
        
        return findings
    
    def _check_amount_consistency(self, text: str) -> List[PaymentFinding]:
        """检查大写小写金额一致性"""
        findings = []
        
        # 提取中文大写金额
        cn_amounts = re.findall(r'(人民币)?([壹贰叁肆伍陆柒捌玖拾佰仟万亿]+元[整]?)', text)
        # 提取数字金额
        num_amounts = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*[万元]', text)
        
        if cn_amounts and not num_amounts:
            findings.append(PaymentFinding(
                severity='medium',
                location='金额条款',
                description='合同仅有中文大写金额，缺少阿拉伯数字金额对照',
                suggestion='建议同时标注阿拉伯数字金额，如：人民币壹拾万元整（¥100,000.00）'
            ))
        
        if num_amounts and not cn_amounts:
            findings.append(PaymentFinding(
                severity='high',
                location='金额条款',
                description='合同仅有阿拉伯数字金额，缺少中文大写金额',
                suggestion='必须添加中文大写金额，防止篡改。格式：人民币壹拾万元整（¥100,000.00）'
            ))
        
        return findings
    
    def _check_payment_nodes(self, text: str) -> List[PaymentFinding]:
        """检查付款节点是否明确"""
        findings = []
        
        # 检查是否有付款节点描述
        payment_keywords = ['首付', '预付款', '定金', '首款', '进度款', '尾款', '验收款']
        found_keywords = [k for k in payment_keywords if k in text]
        
        if not found_keywords:
            findings.append(PaymentFinding(
                severity='high',
                location='付款条款',
                description='合同未明确约定付款节点',
                suggestion='建议明确约定：预付款比例、进度款支付条件、尾款支付时间'
            ))
        
        # 检查付款比例是否明确
        if '首付' in text or '预付款' in text:
            if not re.search(r'(首付|预付款).{0,15}(\d+%|百分之)', text):
                findings.append(PaymentFinding(
                    severity='medium',
                    location='预付款条款',
                    description='预付款/首付比例未明确',
                    suggestion='明确约定预付款比例，如：合同签订后5个工作日内支付30%预付款'
                ))
        
        return findings
    
    def _check_penalty(self, text: str) -> List[PaymentFinding]:
        """检查违约金条款"""
        findings = []
        
        # 检查是否有违约金条款
        if '违约金' not in text and '滞纳金' not in text:
            findings.append(PaymentFinding(
                severity='medium',
                location='违约责任',
                description='合同未约定违约金条款',
                suggestion='建议增加违约金条款，明确逾期付款/交付的违约责任'
            ))
            return findings
        
        # 检查违约金比例是否过高
        penalty_patterns = [
            r'(违约金|滞纳金).{0,10}(\d{2,3})%',
            r'(违约金|滞纳金).{0,10}日\s*(\d+)',
        ]
        
        for pattern in penalty_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    rate_str = match[-1]
                    try:
                        rate = int(rate_str)
                        # 日违约金超过千分之五或年违约金超过24%都过高
                        if '日' in pattern and rate >= 5:
                            findings.append(PaymentFinding(
                                severity='high',
                                location='违约金条款',
                                description=f'违约金比例过高（日{rate}‰），可能不被法院支持',
                                suggestion='建议调整为日万分之五（年化约18%）或以下'
                            ))
                    except ValueError:
                        pass
        
        return findings
    
    def _check_invoice(self, text: str) -> List[PaymentFinding]:
        """检查发票条款"""
        findings = []
        
        invoice_keywords = ['发票', '增值税专用发票', '增值税普通发票']
        if not any(kw in text for kw in invoice_keywords):
            findings.append(PaymentFinding(
                severity='medium',
                location='发票条款',
                description='合同未明确约定发票类型',
                suggestion='建议明确发票类型：增值税专用发票/普通发票，以及税率（如6%、13%）'
            ))
        
        # 检查开票时间
        if '发票' in text:
            if not re.search(r'(收到款项后|付款后|验收后).{0,10}开票', text):
                findings.append(PaymentFinding(
                    severity='low',
                    location='发票条款',
                    description='开票时间未明确约定',
                    suggestion='建议约定：收到款项后X个工作日内开具发票'
                ))
        
        return findings


def analyze_payment_terms(text: str) -> List[Dict[str, Any]]:
    """便捷函数：分析金额条款"""
    analyzer = PaymentAnalyzer()
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
    合同金额：人民币壹拾万元整
    付款方式：合同签订后支付预付款，验收合格后支付尾款。
    """
    
    findings = analyze_payment_terms(test_text)
    for f in findings:
        print(f"[{f['severity']}] {f['location']}: {f['description']}")
        print(f"  建议: {f['suggestion']}\n")
