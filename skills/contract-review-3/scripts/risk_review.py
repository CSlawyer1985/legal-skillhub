#!/usr/bin/env python3
"""
合同风险审核引擎 - Phase 2
功能：识别合同中的高/中/低风险条款
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path


class RiskLevel(Enum):
    """风险等级"""
    HIGH = "🔴 高风险"      # 必须修改
    MEDIUM = "🟡 中风险"     # 建议修改
    LOW = "🟢 低风险"        # 可保留
    INFO = "ℹ️ 提示"         # 信息性


@dataclass
class RiskItem:
    """风险条目"""
    level: RiskLevel
    clause_type: str       # 条款类型
    title: str             # 风险标题
    description: str       # 风险描述
    suggestion: str        # 修改建议
    location: str          # 位置（条款编号等）
    reference: str         # 参考依据


class RiskPatterns:
    """风险模式库"""
    
    # 高风险模式
    HIGH_RISK_PATTERNS = [
        {
            'pattern': r'任由.{0,10}决定|单方.{0,6}决定权|无条件',
            'title': '单方决定权条款',
            'description': '赋予一方单方面决定重要事项的权利，可能显失公平',
            'suggestion': '建议修改为双方协商或设定明确标准',
        },
        {
            'pattern': r'放弃.{0,10}权利|无权.{0,10}抗辩|不得.{0,10}异议',
            'title': '权利放弃条款',
            'description': '要求一方放弃法定权利，可能被认定为无效',
            'suggestion': '删除或修改为对等条款',
        },
        {
            'pattern': r'违约金.{0,5}[\d]+%|滞纳金.{0,5}[\d]+%',
            'title': '过高违约金/滞纳金',
            'description': '违约金/滞纳金比例过高，可能被法院调减',
            'suggestion': '建议将比例调整至实际损失的30%以内',
        },
        {
            'pattern': r'不得起诉|放弃诉讼|仲裁条款.{0,10}无效',
            'title': '限制诉权条款',
            'description': '限制当事人诉权可能违反法律规定',
            'suggestion': '删除此类条款',
        },
        {
            'pattern': r'转账.{0,5}[^\u4e00-\u9fa5]{0,10}[账号]|收款人.{0,5}[^\u4e00-\u9fa5]{0,10}账号',
            'title': '付款账号不明确',
            'description': '付款条款未明确收款账户信息',
            'suggestion': '明确付款账户信息，包括户名、开户行、账号',
        },
    ]
    
    # 中风险模式
    MEDIUM_RISK_PATTERNS = [
        {
            'pattern': r'合理.{0,6}内|若干.{0,6}|适当.{0,6}|必要时',
            'title': '模糊表述条款',
            'description': '条款中使用"合理"、"若干"等模糊词汇，可能引发争议',
            'suggestion': '将模糊表述修改为具体标准或范围',
        },
        {
            'pattern': r'不可抗力.{0,30}除外|免责.{0,10}范围',
            'title': '不可抗力条款不完整',
            'description': '不可抗力条款未明确通知义务和证明材料要求',
            'suggestion': '补充不可抗力的定义、通知义务和证明材料要求',
        },
        {
            'pattern': r'变更.{0,10}通知|地址.{0,10}变更',
            'title': '通知条款不完善',
            'description': '未约定变更地址时的通知义务',
            'suggestion': '增加地址/联系方式变更的通知义务',
        },
        {
            'pattern': r'争议.{0,10}解决|管辖.{0,10}法院',
            'title': '争议解决条款缺失',
            'description': '合同未约定争议解决方式',
            'suggestion': '建议明确约定仲裁或管辖法院',
        },
        {
            'pattern': r'保密.{0,10}期限|保密.{0,10}范围',
            'title': '保密条款不完整',
            'description': '保密条款未明确期限和具体范围',
            'suggestion': '补充保密期限（一般不少于2年）和保密范围定义',
        },
    ]
    
    # 低风险/提示模式
    LOW_RISK_PATTERNS = [
        {
            'pattern': r'双方盖章|签字生效|签署之日起',
            'title': '生效条件提示',
            'description': '合同生效条件已明确',
            'suggestion': '确认双方已完成盖章/签字',
        },
        {
            'pattern': r'份.{0,3}各执|一式',
            'title': '合同份数',
            'description': '合同份数已明确',
            'suggestion': '确认各方持有的份数',
        },
    ]
    
    # 缺失条款检查
    MISSING_CLAUSE_CHECKS = [
        {
            'name': '付款条款',
            'keywords': ['付款', '支付', '价款', '报酬', '费用'],
            'risk': RiskLevel.MEDIUM,
            'suggestion': '建议明确付款时间、方式、账户信息',
        },
        {
            'name': '违约条款',
            'keywords': ['违约', '违约金', '责任'],
            'risk': RiskLevel.HIGH,
            'suggestion': '建议明确违约情形和违约责任',
        },
        {
            'name': '争议解决条款',
            'keywords': ['争议', '仲裁', '诉讼', '管辖'],
            'risk': RiskLevel.MEDIUM,
            'suggestion': '建议明确争议解决方式（仲裁或诉讼）及管辖法院',
        },
        {
            'name': '保密条款',
            'keywords': ['保密', '机密'],
            'risk': RiskLevel.LOW,
            'suggestion': '涉及商业秘密的建议增加保密条款',
        },
        {
            'name': '终止条款',
            'keywords': ['终止', '解除', '期满'],
            'risk': RiskLevel.MEDIUM,
            'suggestion': '建议明确合同终止条件和程序',
        },
        {
            'name': '不可抗力条款',
            'keywords': ['不可抗力'],
            'risk': RiskLevel.MEDIUM,
            'suggestion': '建议增加不可抗力条款',
        },
    ]


class RiskReviewEngine:
    """风险审核引擎"""
    
    def __init__(self, text: str, contract_type: str = None):
        """
        初始化审核引擎
        
        Args:
            text: 合同文本内容
            contract_type: 合同类型
        """
        self.text = text
        self.text_lower = text.lower()
        self.contract_type = contract_type
        self.risks: List[RiskItem] = []
        
        # 加载该合同类型的法律规则（如存在）
        self._legal_rules = self._load_type_rules()
        
    def _load_type_rules(self) -> Optional[dict]:
        """加载合同类型对应的 legal_rules.json"""
        if not self.contract_type:
            return None
        try:
            skill_dir = Path(__file__).parent.parent
            rules_dir = skill_dir / "references" / "rule-packs"
            rule_path = rules_dir / self.contract_type / "legal_rules.json"
            if not rule_path.exists():
                # 模糊匹配
                for child in rules_dir.iterdir():
                    if child.is_dir() and self.contract_type in child.name:
                        rule_path = child / "legal_rules.json"
                        break
            if rule_path.exists():
                with open(rule_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
        
    def review(self) -> Dict:
        """
        执行完整风险审核
        
        Returns:
            包含审核结果的字典
        """
        # 清空之前的风险
        self.risks = []
        
        # 执行各项检查
        self._check_high_risk_patterns()
        self._check_medium_risk_patterns()
        self._check_low_risk_patterns()
        self._check_missing_clauses()
        self._check_legal_compliance()
        self._check_type_specific_rules()  # 新增：基于 legal_rules.json 的专项检查
        
        # 按风险等级分组
        grouped = self._group_by_level()
        
        return {
            'summary': self._generate_summary(grouped),
            'risks': grouped,
            'all_items': [self._risk_to_dict(r) for r in self.risks],
            'risk_score': self._calculate_score(grouped),
        }
    
    def _check_high_risk_patterns(self):
        """检查高风险模式"""
        for pattern in RiskPatterns.HIGH_RISK_PATTERNS:
            matches = list(re.finditer(pattern['pattern'], self.text))
            for match in matches:
                # 获取上下文
                start = max(0, match.start() - 20)
                end = min(len(self.text), match.end() + 50)
                context = self.text[start:end]
                
                self.risks.append(RiskItem(
                    level=RiskLevel.HIGH,
                    clause_type='格式条款/权利义务',
                    title=pattern['title'],
                    description=pattern['description'],
                    suggestion=pattern['suggestion'],
                    location=f'位置: {match.start()}-{match.end()}',
                    reference='《民法典》第497条（格式条款无效情形）',
                ))
    
    def _check_medium_risk_patterns(self):
        """检查中风险模式"""
        for pattern in RiskPatterns.MEDIUM_RISK_PATTERNS:
            matches = list(re.finditer(pattern['pattern'], self.text))
            for match in matches:
                self.risks.append(RiskItem(
                    level=RiskLevel.MEDIUM,
                    clause_type='条款表述',
                    title=pattern['title'],
                    description=pattern['description'],
                    suggestion=pattern['suggestion'],
                    location=f'位置: {match.start()}-{match.end()}',
                    reference='合同条款完备性要求',
                ))
    
    def _check_low_risk_patterns(self):
        """检查低风险/提示模式"""
        for pattern in RiskPatterns.LOW_RISK_PATTERNS:
            matches = list(re.finditer(pattern['pattern'], self.text))
            for match in matches:
                self.risks.append(RiskItem(
                    level=RiskLevel.LOW,
                    clause_type='条款完整性',
                    title=pattern['title'],
                    description=pattern['description'],
                    suggestion=pattern['suggestion'],
                    location=f'位置: {match.start()}-{match.end()}',
                    reference='',
                ))
    
    def _check_missing_clauses(self):
        """检查缺失条款"""
        for check in RiskPatterns.MISSING_CLAUSE_CHECKS:
            found = any(kw in self.text_lower for kw in check['keywords'])
            if not found:
                self.risks.append(RiskItem(
                    level=check['risk'],
                    clause_type='条款缺失',
                    title=f'缺少"{check["name"]}"',
                    description=f'合同中未发现"{check["name"]}"相关内容',
                    suggestion=check['suggestion'],
                    location='全文',
                    reference=f'建议参考{self.contract_type or "一般合同"}标准模板',
                ))
    
    def _check_legal_compliance(self):
        """检查法律合规性（基于 legal_rules.json + 通用规则）"""
        # 1. 通用合规检查
        if '无效' in self.text and '特别约定' in self.text:
            self.risks.append(RiskItem(
                level=RiskLevel.HIGH,
                clause_type='法律合规',
                title='可能导致合同无效的条款',
                description='合同约定与法律强制性规定冲突可能导致部分或全部无效',
                suggestion='删除违法条款，或调整为符合法律规定的表述',
                location='特别约定章节',
                reference='《民法典》第153条（违反强制性规定无效）',
            ))

        # 2. 基于 legal_rules.json 的违约金/定金检查
        if self._legal_rules and 'penalty_provisions' in self._legal_rules:
            penalties = self._legal_rules['penalty_provisions']
            
            # 违约金上限检查
            if '违约金上限' in penalties:
                rule = penalties['违约金上限']
                penalty_match = re.search(r'违约金[^\d]*(\d+(?:\.\d+)?)\s*%', self.text)
                if penalty_match:
                    ratio = float(penalty_match.group(1))
                    if ratio > 30:
                        self.risks.append(RiskItem(
                            level=RiskLevel.HIGH,
                            clause_type='惩罚性条款',
                            title=f'违约金比例过高（{ratio}%）',
                            description=f'合同约定违约金为{ratio}%，可能被法院认定为"过分高于造成的损失"',
                            suggestion='建议将违约金比例调整至30%以内',
                            location='违约责任条款',
                            reference=rule.get('legal_basis', '《民法典》第585条'),
                        ))

            # 定金上限检查
            if '定金规则' in penalties:
                rule = penalties['定金规则']
                deposit_match = re.search(r'定金[^\d]*(\d+(?:\.\d+)?)\s*%', self.text)
                if deposit_match:
                    ratio = float(deposit_match.group(1))
                    if ratio > 20:
                        self.risks.append(RiskItem(
                            level=RiskLevel.HIGH,
                            clause_type='惩罚性条款',
                            title=f'定金比例超过法定上限（{ratio}%）',
                            description=f'《民法典》第586条规定定金不得超过主合同标的额的20%',
                            suggestion='建议将定金比例调整至20%以内',
                            location='定金条款',
                            reference=rule.get('legal_basis', '《民法典》第586条'),
                        ))

        # 3. 民间借贷利率检查
        if self.contract_type and '借款' in self.contract_type:
            rate_match = re.search(r'(?:年)?利率\s*[为是]?\s*(\d+(?:\.\d+)?)\s*%', self.text)
            if rate_match:
                rate = float(rate_match.group(1))
                if rate > 14.8:
                    self.risks.append(RiskItem(
                        level=RiskLevel.HIGH,
                        clause_type='法律合规',
                        title=f'年利率{rate}%可能超过司法保护上限',
                        description='根据《民间借贷司法解释》第25条，超过合同成立时一年期LPR四倍的利率部分不受法律保护',
                        suggestion='建议将利率调整至法定保护范围内，或明确该借款不属于民间借贷范畴',
                        location='利率条款',
                        reference='《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第25条',
                    ))

    def _check_type_specific_rules(self):
        """基于 legal_rules.json 的合同类型专项检查"""
        if not self._legal_rules:
            return

        # 检查必要条款
        essential = self._legal_rules.get('essential_clauses', {})
        for clause_name, rule in essential.items():
            keywords = rule.get('keywords', [])
            if not any(kw in self.text for kw in keywords):
                self.risks.append(RiskItem(
                    level=RiskLevel.MEDIUM,
                    clause_type='条款缺失',
                    title=f'缺少{clause_name}',
                    description=f'合同中未发现{clause_name}相关内容（{rule.get("requirement", "")[:60]}...）',
                    suggestion=f'建议补充{clause_name}，明确{rule.get("requirement", "")[:80]}',
                    location='全文',
                    reference=rule.get('legal_basis', ''),
                ))

        # 检查常见问题
        common_gaps = self._legal_rules.get('common_gaps', [])
        for gap in common_gaps:
            issue_keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', gap.get('issue', ''))
            if issue_keywords and not any(kw in self.text for kw in issue_keywords[:3]):
                self.risks.append(RiskItem(
                    level=RiskLevel.MEDIUM,
                    clause_type='条款缺失',
                    title=gap.get('issue', '常见缺失'),
                    description=gap.get('risk', ''),
                    suggestion=gap.get('suggestion', ''),
                    location='全文',
                    reference='实务经验总结',
                ))
    
    def _group_by_level(self) -> Dict:
        """按风险等级分组"""
        grouped = {
            RiskLevel.HIGH: [],
            RiskLevel.MEDIUM: [],
            RiskLevel.LOW: [],
            RiskLevel.INFO: [],
        }
        for risk in self.risks:
            grouped[risk.level].append(self._risk_to_dict(risk))
        return grouped
    
    def _risk_to_dict(self, risk: RiskItem) -> Dict:
        """将风险对象转为字典"""
        return {
            'level': risk.level.value,
            'type': risk.clause_type,
            'title': risk.title,
            'description': risk.description,
            'suggestion': risk.suggestion,
            'location': risk.location,
            'reference': risk.reference,
        }
    
    def _generate_summary(self, grouped: Dict) -> Dict:
        """生成审核摘要"""
        return {
            'total_issues': len(self.risks),
            'high_risk_count': len(grouped[RiskLevel.HIGH]),
            'medium_risk_count': len(grouped[RiskLevel.MEDIUM]),
            'low_risk_count': len(grouped[RiskLevel.LOW]),
            'overall_assessment': self._get_assessment_text(grouped),
        }
    
    def _get_assessment_text(self, grouped: Dict) -> str:
        """生成总体评估文字"""
        high = len(grouped[RiskLevel.HIGH])
        medium = len(grouped[RiskLevel.MEDIUM])
        
        if high > 0:
            return f'合同存在{high}项高风险问题，必须修改后签署'
        elif medium > 2:
            return f'合同存在{medium}项中风险问题，建议修改'
        elif medium > 0:
            return f'合同存在{medium}项中风险问题，可根据情况决定是否修改'
        else:
            return '合同整体风险较低，建议完善个别条款'
    
    def _calculate_score(self, grouped: Dict) -> float:
        """计算风险评分（满分100，越高风险越低）"""
        score = 100
        score -= len(grouped[RiskLevel.HIGH]) * 20
        score -= len(grouped[RiskLevel.MEDIUM]) * 5
        score -= len(grouped[RiskLevel.LOW]) * 1
        return max(0, min(100, score))


def main(text: str, contract_type: str = None) -> Dict:
    """
    主入口函数
    
    Args:
        text: 合同文本内容
        contract_type: 可选的合同类型
        
    Returns:
        审核结果字典
    """
    engine = RiskReviewEngine(text, contract_type)
    return engine.review()


if __name__ == '__main__':
    # 测试
    sample = """
    咨询服务合同
    
    甲方（委托方）：某公司
    乙方（受托方）：某律所
    
    第一条 服务内容
    乙方为甲方提供法律咨询服务。
    
    第二条 服务费用
    咨询服务费共计人民币100万元整。
    
    第三条 特别约定
    甲方同意乙方在任何情况下不得就服务提出异议。
    违约金按合同总价的50%计算。
    
    第四条 合同份数
    本合同一式四份，各方各执两份。
    """
    
    result = main(sample, '委托合同')
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
