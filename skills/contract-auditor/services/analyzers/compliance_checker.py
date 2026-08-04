"""合规性检查器"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ComplianceFinding:
    """合规性发现项"""
    severity: str
    location: str
    description: str
    suggestion: str


class ComplianceChecker:
    """合规性检查器"""
    
    def __init__(self):
        self.required_clauses = [
            ('合同主体', r'(甲方|乙方).{0,5}(名称|单位)'),
            ('签署日期', r'(签署|签订).{0,5}(日期|时间)'),
            ('生效条件', r'(生效|自.{0,10}起)'),
            ('争议解决', r'(争议|纠纷).{0,10}(解决|仲裁|诉讼)'),
        ]
    
    def analyze(self, text: str) -> List[ComplianceFinding]:
        """分析合规性"""
        findings = []
        
        findings.extend(self._check_signatures(text))
        findings.extend(self._check_dates(text))
        findings.extend(self._check_parties(text))
        findings.extend(self._check_required_clauses(text))
        
        return findings
    
    def _check_signatures(self, text: str) -> List[ComplianceFinding]:
        """检查签章信息"""
        findings = []
        
        # 检查是否有签章位置
        signature_keywords = ['签章', '签字', '盖章', '法定代表人', '授权代表']
        has_signature = any(kw in text for kw in signature_keywords)
        
        if not has_signature:
            findings.append(ComplianceFinding(
                severity='high',
                location='签章条款',
                description='合同未约定签章位置和方式',
                suggestion='必须明确签章条款：双方签字盖章位置、法定代表人或授权代表签字'
            ))
        
        # 检查是否有双方签章
        if '甲方' in text and '乙方' in text:
            if not re.search(r'(甲方|乙方).{0,10}(签章|盖章|签字)', text):
                findings.append(ComplianceFinding(
                    severity='medium',
                    location='签章条款',
                    description='合同未明确甲乙双方的签章位置',
                    suggestion='建议分别列明甲方签章处和乙方签章处，包括：单位盖章、法定代表人/授权代表签字、日期'
                ))
        
        return findings
    
    def _check_dates(self, text: str) -> List[ComplianceFinding]:
        """检查日期完整性"""
        findings = []
        
        # 检查签署日期
        date_patterns = [
            r'(签署日期|签订日期).{0,5}(\d{4})',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日.{0,5}(签署|签订)',
        ]
        
        has_sign_date = any(re.search(p, text) for p in date_patterns)
        
        if not has_sign_date:
            findings.append(ComplianceFinding(
                severity='high',
                location='签署日期',
                description='合同未明确约定签署日期',
                suggestion='必须填写合同签署日期，格式：2024年3月17日'
            ))
        
        # 检查生效日期
        if '生效' in text:
            if not re.search(r'(自|从).{0,10}(\d{4}|签署之日|签订之日).{0,5}生效', text):
                findings.append(ComplianceFinding(
                    severity='medium',
                    location='生效日期',
                    description='生效日期不够明确',
                    suggestion='建议明确生效日期，如：本合同自双方签字盖章之日起生效，或自2024年X月X日起生效'
                ))
        
        # 检查合同期限
        duration_keywords = ['有效期', '合同期限', '服务期限', '至.*止']
        has_duration = any(re.search(kw, text) for kw in duration_keywords)
        
        if not has_duration:
            findings.append(ComplianceFinding(
                severity='medium',
                location='合同期限',
                description='合同未明确约定有效期或期限',
                suggestion='建议明确合同有效期，如：本合同有效期自2024年3月1日至2025年2月28日'
            ))
        
        return findings
    
    def _check_parties(self, text: str) -> List[ComplianceFinding]:
        """检查合同主体"""
        findings = []
        
        # 检查是否有甲乙双方
        if '甲方' not in text or '乙方' not in text:
            findings.append(ComplianceFinding(
                severity='critical',
                location='合同主体',
                description='合同未明确约定甲乙双方（合同主体）',
                suggestion='必须明确合同双方：甲方（委托方/采购方）和乙方（服务方/供应方）的完整名称'
            ))
            return findings
        
        # 检查是否有主体信息
        party_info_patterns = [
            r'(甲方|乙方).{0,10}(名称|单位名称)',
            r'(甲方|乙方).{0,10}(地址|住所)',
            r'(甲方|乙方).{0,10}(法定代表人|联系人)',
        ]
        
        for pattern in party_info_patterns:
            if not re.search(pattern, text):
                findings.append(ComplianceFinding(
                    severity='medium',
                    location='合同主体信息',
                    description='合同主体信息不完整，缺少名称、地址或联系人信息',
                    suggestion='建议补充完整的主体信息：单位全称、统一社会信用代码、地址、法定代表人、联系人、联系方式'
                ))
                break
        
        return findings
    
    def _check_required_clauses(self, text: str) -> List[ComplianceFinding]:
        """检查关键条款缺失"""
        findings = []
        
        # 检查争议解决条款
        if not re.search(r'(争议|纠纷).{0,15}(协商|调解|仲裁|诉讼)', text):
            findings.append(ComplianceFinding(
                severity='high',
                location='争议解决',
                description='合同未约定争议解决方式',
                suggestion='必须增加争议解决条款，如：协商解决，协商不成提交甲方所在地人民法院诉讼'
            ))
        
        # 检查法律适用
        if '法律' not in text or '法规' not in text:
            findings.append(ComplianceFinding(
                severity='low',
                location='法律适用',
                description='合同未明确适用法律',
                suggestion='建议增加：本合同的订立、效力、解释、履行和争议解决均适用中华人民共和国法律'
            ))
        
        # 检查不可抗力
        if '不可抗力' not in text:
            findings.append(ComplianceFinding(
                severity='medium',
                location='不可抗力',
                description='合同未约定不可抗力条款',
                suggestion='建议增加不可抗力条款，明确不可抗力的定义、通知义务和责任免除'
            ))
        
        # 检查保密条款（如涉及商业信息）
        confidential_keywords = ['保密', '商业秘密', '机密信息']
        has_confidential = any(kw in text for kw in confidential_keywords)
        
        if not has_confidential:
            findings.append(ComplianceFinding(
                severity='low',
                location='保密条款',
                description='合同未约定保密条款',
                suggestion='如涉及商业秘密，建议增加保密条款，约定保密义务和期限'
            ))
        
        # 检查变更解除条款
        if '变更' not in text or '解除' not in text:
            findings.append(ComplianceFinding(
                severity='medium',
                location='变更解除',
                description='合同未明确约定变更和解除条件',
                suggestion='建议增加：合同变更需双方书面同意；一方违约时另一方可解除合同'
            ))
        
        return findings


def analyze_compliance(text: str) -> List[Dict[str, Any]]:
    """便捷函数：分析合规性"""
    checker = ComplianceChecker()
    findings = checker.analyze(text)
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
    技术服务合同
    
    甲方：某某科技有限公司
    乙方：某某软件公司
    
    第一条 服务内容
    乙方为甲方提供软件开发服务。
    
    第二条 合同金额
    合同金额人民币壹拾万元整。
    """
    
    findings = analyze_compliance(test_text)
    for f in findings:
        print(f"[{f['severity']}] {f['location']}: {f['description']}")
        print(f"  建议: {f['suggestion']}\n")
