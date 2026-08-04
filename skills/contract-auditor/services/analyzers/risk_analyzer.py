"""风险提示分析器"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class RiskFinding:
    """风险发现项"""
    severity: str
    location: str
    description: str
    suggestion: str


class RiskAnalyzer:
    """风险提示分析器"""
    
    def __init__(self):
        # 模糊表述词汇
        self.vague_terms = [
            ('合理', '合理时间、合理费用等表述主观性强'),
            ('尽力', '"尽力完成"缺乏约束力'),
            ('适当', '"适当调整"标准不明确'),
            ('及时', '"及时交付"时间界定模糊'),
            ('重大', '"重大变更"缺乏量化标准'),
            ('必要时', '"必要时"触发条件不明确'),
            ('视情况', '"视情况而定"过于随意'),
            ('约', '"约XX元"金额不精确'),
            ('左右', '"XX左右"范围不明确'),
            ('等相关', '"XX等相关"范围无限扩大'),
        ]
        
        # 不利条款模式
        self.unfavorable_patterns = [
            (r'(甲方|乙方).{0,5}(有权|可以).{0,10}(单方|单方面).{0,5}(解除|终止|变更)',
             '单方解除权', 'high'),
            (r'(无限|连带).{0,5}责任',
             '无限连带责任', 'critical'),
            (r'(放弃|免除).{0,10}(追偿|索赔|诉讼)',
             '放弃追偿权', 'high'),
            (r'(自动|默认).{0,5}(同意|认可|接受)',
             '默认同意条款', 'medium'),
            (r'(最终|唯一).{0,5}解释.{0,5}权',
             '单方解释权', 'medium'),
        ]
    
    def analyze(self, text: str) -> List[RiskFinding]:
        """分析风险点"""
        findings = []
        
        findings.extend(self._check_vague_terms(text))
        findings.extend(self._check_unfavorable_clauses(text))
        findings.extend(self._check_imbalanced_terms(text))
        findings.extend(self._check_dispute_resolution(text))
        
        return findings
    
    def _check_vague_terms(self, text: str) -> List[RiskFinding]:
        """检查模糊表述"""
        findings = []
        
        for term, description in self.vague_terms:
            if term in text:
                # 找到上下文
                pattern = f'.{{0,20}}{term}.{{0,20}}'
                matches = re.findall(pattern, text)
                context = matches[0] if matches else term
                
                findings.append(RiskFinding(
                    severity='medium',
                    location='模糊表述',
                    description=f'发现模糊表述"{term}"：{description}。上下文："...{context}..."',
                    suggestion=f'建议将"{term}"替换为具体可量化的标准，如具体日期、金额、数量等'
                ))
        
        return findings
    
    def _check_unfavorable_clauses(self, text: str) -> List[RiskFinding]:
        """检查不利条款"""
        findings = []
        
        for pattern, clause_type, severity in self.unfavorable_patterns:
            matches = re.findall(pattern, text)
            if matches:
                context_pattern = f'.{{0,30}}{pattern}.{{0,30}}'
                contexts = re.findall(context_pattern, text, re.DOTALL)
                context = contexts[0] if contexts else '...'
                
                suggestions = {
                    '单方解除权': '建议限制单方解除权的行使条件，如需提前30日书面通知并支付违约金',
                    '无限连带责任': '强烈建议删除，改为"以合同金额为限承担违约责任"',
                    '放弃追偿权': '建议删除，保留合法的追偿和诉讼权利',
                    '默认同意条款': '建议改为"逾期未提出书面异议视为同意"，并明确异议期限',
                    '单方解释权': '建议删除或改为"双方协商解释，协商不成按通常理解"',
                }
                
                findings.append(RiskFinding(
                    severity=severity,
                    location=f'不利条款：{clause_type}',
                    description=f'发现{clause_type}条款。上下文："...{context}..."',
                    suggestion=suggestions.get(clause_type, '建议审慎评估该条款的合理性')
                ))
        
        return findings
    
    def _check_imbalanced_terms(self, text: str) -> List[RiskFinding]:
        """检查权利义务不对等"""
        findings = []
        
        # 检查甲方权利 vs 乙方权利
        party_a_rights = len(re.findall(r'甲方.{0,10}(有权|可以)', text))
        party_b_rights = len(re.findall(r'乙方.{0,10}(有权|可以)', text))
        
        if party_a_rights > party_b_rights * 2 and party_b_rights > 0:
            findings.append(RiskFinding(
                severity='medium',
                location='权利义务平衡',
                description=f'甲方权利条款（{party_a_rights}处）明显多于乙方（{party_b_rights}处），权利义务可能不对等',
                suggestion='建议审查双方权利义务是否平衡，避免显失公平的条款'
            ))
        
        # 检查单方违约责任
        if '甲方违约' in text and '乙方违约' not in text:
            findings.append(RiskFinding(
                severity='medium',
                location='违约责任对等',
                description='合同仅约定甲方违约责任，未约定乙方违约责任',
                suggestion='建议明确双方的违约责任，保持对等性'
            ))
        
        if '乙方违约' in text and '甲方违约' not in text:
            findings.append(RiskFinding(
                severity='medium',
                location='违约责任对等',
                description='合同仅约定乙方违约责任，未约定甲方违约责任',
                suggestion='建议明确双方的违约责任，保持对等性'
            ))
        
        return findings
    
    def _check_dispute_resolution(self, text: str) -> List[RiskFinding]:
        """检查争议解决条款偏向性"""
        findings = []
        
        # 检查仲裁地点偏向
        if '仲裁' in text:
            # 检查是否指定特定仲裁机构
            if re.search(r'(北京|上海|深圳|广州).{0,10}仲裁委员会', text):
                findings.append(RiskFinding(
                    severity='low',
                    location='争议解决',
                    description='仲裁条款指定了具体仲裁机构和地点',
                    suggestion='建议确认仲裁地点是否便利，或约定"被告所在地"或"合同履行地"仲裁机构'
                ))
        
        # 检查诉讼管辖偏向
        if '诉讼' in text or '法院' in text:
            if re.search(r'(甲方|乙方).{0,10}所在地.{0,10}(法院|人民法院)', text):
                party = '甲方' if '甲方所在地' in text else '乙方'
                findings.append(RiskFinding(
                    severity='low',
                    location='争议解决',
                    description=f'诉讼管辖约定在{party}所在地法院',
                    suggestion=f'注意：约定在{party}所在地法院可能增加另一方的诉讼成本，建议协商确定中立地点或按法定管辖'
                ))
        
        return findings


def analyze_risks(text: str) -> List[Dict[str, Any]]:
    """便捷函数：分析风险"""
    analyzer = RiskAnalyzer()
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
    技术服务合同
    
    甲方有权单方解除合同。
    乙方应在合理时间内完成交付。
    如发生争议，提交甲方所在地人民法院诉讼。
    
    乙方违约应支付违约金，甲方违约按实际情况处理。
    """
    
    findings = analyze_risks(test_text)
    for f in findings:
        print(f"[{f['severity']}] {f['location']}: {f['description']}")
        print(f"  建议: {f['suggestion']}\n")
