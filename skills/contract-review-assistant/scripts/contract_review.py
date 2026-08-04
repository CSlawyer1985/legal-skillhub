#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同审查辅助系统核心模块
支持条款提取、风险识别、差异比对、意见生成
"""

import re
import difflib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    HIGH = "高风险"
    MEDIUM = "中风险"
    LOW = "低风险"


@dataclass
class Clause:
    """合同条款"""
    clause_type: str  # 条款类型
    content: str      # 条款内容
    risk_level: RiskLevel
    suggestion: str   # 修改建议


@dataclass
class ReviewResult:
    """审查结果"""
    contract_type: str
    parties: List[str]
    clauses: List[Clause]
    risks: List[str]
    suggestions: List[str]
    diff_highlights: Optional[str] = None


class ContractReviewer:
    """合同审查器"""
    
    # 常见风险关键词
    RISK_KEYWORDS = {
        RiskLevel.HIGH: [
            "无条件退款", "放弃追偿", "无限责任", "自动续约",
            "单方解除", "不可撤销", "永久有效"
        ],
        RiskLevel.MEDIUM: [
            "违约金过高", "期限不明确", "管辖权不利", "保密义务过重",
            "知识产权归属不明"
        ],
        RiskLevel.LOW: [
            "表述模糊", "条款冗长", "引用不规范"
        ]
    }
    
    # 核心条款类型
    CLAUSE_TYPES = [
        "当事人信息", "标的物", "价款/报酬", "履行期限", "履行地点",
        "质量标准", "违约责任", "争议解决", "保密条款", "知识产权",
        "终止条件", "不可抗力"
    ]
    
    def __init__(self):
        self.contract_text = ""
        self.result = None
    
    def load_contract(self, text: str):
        """加载合同文本"""
        self.contract_text = text
        return self
    
    def extract_parties(self) -> List[str]:
        """提取合同当事人"""
        parties = []
        
        # 匹配常见的当事人表述
        patterns = [
            r"(甲方|乙方|卖方|买方|出租方|承租方|委托方|受托方)[：:]\s*([^\n，。]+)",
            r"(甲方|乙方|卖方|买方|出租方|承租方|委托方|受托方)\s*[:：]\s*([^，。\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, self.contract_text)
            for match in matches:
                party = match.group(2).strip()
                if party and party not in parties:
                    parties.append(party)
        
        return parties if parties else ["未识别到当事人信息"]
    
    def extract_clauses(self) -> List[Clause]:
        """提取核心条款"""
        clauses = []
        
        # 简化的条款提取逻辑（实际应用中可使用NLP模型）
        for clause_type in self.CLAUSE_TYPES:
            # 查找条款内容
            pattern = rf"{clause_type}[：:]?\s*([^\n]{{10,200}})"
            match = re.search(pattern, self.contract_text)
            
            if match:
                content = match.group(1).strip()
                risk_level = self._assess_risk(content)
                suggestion = self._generate_suggestion(clause_type, content, risk_level)
                
                clauses.append(Clause(
                    clause_type=clause_type,
                    content=content,
                    risk_level=risk_level,
                    suggestion=suggestion
                ))
        
        return clauses
    
    def _assess_risk(self, text: str) -> RiskLevel:
        """评估文本风险等级"""
        for level, keywords in self.RISK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return level
        return RiskLevel.LOW
    
    def _generate_suggestion(self, clause_type: str, content: str, risk_level: RiskLevel) -> str:
        """生成修改建议"""
        suggestions = {
            "违约责任": "建议明确违约金计算方式，避免过高违约金条款",
            "争议解决": "建议约定明确的管辖法院或仲裁机构",
            "价款/报酬": "建议明确支付时间、方式和条件",
            "履行期限": "建议明确起止时间，避免模糊表述",
        }
        
        if risk_level == RiskLevel.HIGH:
            return f"【高风险】{suggestions.get(clause_type, '建议请法务专员复核此条款')}"
        elif risk_level == RiskLevel.MEDIUM:
            return f"【中风险】{suggestions.get(clause_type, '建议进一步明确此条款')}"
        else:
            return f"【低风险】{suggestions.get(clause_type, '条款基本合规')}"
    
    def compare_versions(self, old_text: str, new_text: str) -> str:
        """对比合同版本差异"""
        diff = difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile='原版本',
            tofile='新版本',
            lineterm=''
        )
        return '\n'.join(diff)
    
    def generate_review_opinion(self, clauses: List[Clause]) -> Tuple[List[str], List[str]]:
        """生成审查意见"""
        risks = []
        suggestions = []
        
        # 统计风险
        high_risks = [c for c in clauses if c.risk_level == RiskLevel.HIGH]
        medium_risks = [c for c in clauses if c.risk_level == RiskLevel.MEDIUM]
        
        if high_risks:
            risks.append(f"发现 {len(high_risks)} 个高风险条款，需要重点关注")
            suggestions.append("建议与对方协商修改高风险条款")
        
        if medium_risks:
            risks.append(f"发现 {len(medium_risks)} 个中风险条款，建议进一步明确")
        
        # 生成总体建议
        suggestions.append("建议合同双方权利义务对等")
        suggestions.append("建议明确合同解除和终止条件")
        suggestions.append("建议增加不可抗力条款")
        
        return risks, suggestions
    
    def review(self, contract_text: str) -> ReviewResult:
        """执行完整审查流程"""
        self.load_contract(contract_text)
        
        # 提取当事人
        parties = self.extract_parties()
        
        # 提取条款
        clauses = self.extract_clauses()
        
        # 生成审查意见
        risks, suggestions = self.generate_review_opinion(clauses)
        
        # 判断合同类型（简化逻辑）
        contract_type = "服务合同" if "服务" in contract_text else "买卖合同"
        
        self.result = ReviewResult(
            contract_type=contract_type,
            parties=parties,
            clauses=clauses,
            risks=risks,
            suggestions=suggestions
        )
        
        return self.result
    
    
    def format_result(self) -> str:
        """格式化审查结果"""
        if not self.result:
            return "请先执行审查"
        
        output = []
        output.append(f"# {self.result.contract_type}审查报告\n")
        output.append(f"## 当事人信息")
        for i, party in enumerate(self.result.parties, 1):
            output.append(f"{i}. {party}")
        
        output.append(f"\n## 条款审查")
        for clause in self.result.clauses:
            output.append(f"\n### {clause.clause_type} ({clause.risk_level.value})")
            output.append(f"内容：{clause.content[:100]}...")
            output.append(f"建议：{clause.suggestion}")
        
        output.append(f"\n## 风险摘要")
        for risk in self.result.risks:
            output.append(f"- {risk}")
        
        output.append(f"\n## 审查建议")
        for suggestion in self.result.suggestions:
            output.append(f"- {suggestion}")
        
        return '\n'.join(output)


if __name__ == "__main__":
    # 示例用法
    sample_contract = """
    甲方：深圳某某科技有限公司
    乙方：北京某某技术服务公司
    
    标的物：软件开发服务
    价款：人民币100万元
    履行期限：合同签订后6个月内
    违约责任：任何一方违约，需支付合同总价30%的违约金
    争议解决：双方协商解决，协商不成提交甲方所在地法院诉讼
    """
    
    reviewer = ContractReviewer()
    result = reviewer.review(sample_contract)
    print(reviewer.format_result())
