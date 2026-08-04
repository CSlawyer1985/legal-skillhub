#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版合同审查模块 - 支持LLM API
使用AI模型生成更专业的审查意见
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import requests
from typing import Dict, List, Optional

# 导入基础审查模块
from scripts.contract_review import ContractReviewer, RiskLevel, Clause, ReviewResult


class EnhancedContractReviewer(ContractReviewer):
    """增强版合同审查器 - 支持LLM"""
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        """
        初始化增强版审查器
        
        Args:
            use_llm: 是否使用LLM API
            api_key: LLM API密钥（如需使用）
        """
        super().__init__()
        self.use_llm = use_llm
        self.api_key = api_key
        self.llm_provider = None  # 'openai', 'claude', 'local'
        
        # 扩展的风险关键词库
        self.RISK_KEY_WORDS = {
            RiskLevel.HIGH: [
                "无条件退款", "放弃追偿", "无限责任", "自动续约",
                "单方解除", "不可撤销", "永久有效", "无限授权",
                "放弃诉讼时效", "放弃抗辩权", "连带责任", "惩罚性赔偿"
            ],
            RiskLevel.MEDIUM: [
                "违约金过高", "期限不明确", "管辖权不利", "保密义务过重",
                "知识产权归属不明", "验收标准模糊", "付款条件不清",
                "违约责任不对等", "争议解决条款不利"
            ],
            RiskLevel.LOW: [
                "表述模糊", "条款冗长", "引用不规范", "定义不清晰"
            ]
        }
        
        # 标准条款模板库
        self.STANDARD_CLAUSES = {
            "违约责任": "违约责任应当公平对等，违约金一般不超过合同标的额的20%",
            "争议解决": "建议约定明确的管辖法院或仲裁机构，通常选择对原告有利的机构",
            "价款支付": "应当明确付款时间、方式、条件，以及逾期付款的违约责任",
            "不可抗力": "应当明确不可抗力的范围、通知义务和后果分担"
        }
    
    def setup_llm(self, provider: str, api_key: str):
        """
        配置LLM提供商
        
        Args:
            provider: 'openai', 'claude', 'local'
            api_key: API密钥
        """
        self.llm_provider = provider
        self.api_key = api_key
        self.use_llm = True
        print(f"✓ LLM已配置：{provider}")
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM API
        
        Args:
            prompt: 提示词
        
        Returns:
            LLM生成的文本
        """
        if not self.use_llm or not self.api_key:
            return self._fallback_analysis(prompt)
        
        try:
            if self.llm_provider == 'openai':
                return self._call_openai(prompt)
            elif self.llm_provider == 'claude':
                return self._call_claude(prompt)
            elif self.llm_provider == 'local':
                return self._call_local_llm(prompt)
            else:
                return self._fallback_analysis(prompt)
        except Exception as e:
            print(f"LLM调用失败：{e}")
            return self._fallback_analysis(prompt)
    
    def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
        # 这里需要安装openai库：pip install openai
        try:
            import openai
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content
        except:
            # 如果openai库未安装或调用失败，返回模拟响应
            return self._simulate_llm_response(prompt)
    
    def _call_claude(self, prompt: str) -> str:
        """调用Claude API"""
        # 这里需要安装anthropic库：pip install anthropic
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except:
            return self._simulate_llm_response(prompt)
    
    def _call_local_llm(self, prompt: str) -> str:
        """调用本地LLM（如Ollama）"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama2", "prompt": prompt, "stream": False}
            )
            return response.json().get("response", "")
        except:
            return self._simulate_llm_response(prompt)
    
    def _simulate_llm_response(self, prompt: str) -> str:
        """模拟LLM响应（用于演示）"""
        if "风险" in prompt:
            return "该条款存在一定风险，建议进一步明确双方权利义务，避免模糊表述。"
        elif "建议" in prompt:
            return "建议：1) 明确条款具体内容；2) 确保权利义务对等；3) 添加违约责任条款。"
        else:
            return "根据合同审查经验，该条款需要进一步完善。"
    
    def _fallback_analysis(self, prompt: str) -> str:
        """降级分析（不使用LLM时）"""
        return "基于规则分析：该条款需要提供更多信息以便准确评估。"
    
    def enhanced_review(self, contract_text: str, contract_type: Optional[str] = None) -> ReviewResult:
        """
        增强版审查（使用LLM）
        
        Args:
            contract_text: 合同文本
            contract_type: 合同类型（可选）
        
        Returns:
            审查结果
        """
        print("正在进行增强版合同审查...")
        
        # 先执行基础审查
        result = self.review(contract_text)
        
        # 使用LLM增强审查意见
        if self.use_llm:
            print("正在使用AI增强审查意见...")
            result = self._enhance_with_llm(result, contract_text)
        
        # 与标准模板比对
        result = self._compare_with_standard_clauses(result)
        
        print("✓ 增强版审查完成")
        return result
    
    def _enhance_with_llm(self, result: ReviewResult, contract_text: str) -> ReviewResult:
        """使用LLM增强审查意见"""
        
        # 为每个条款生成LLM审查意见
        for i, clause in enumerate(result.clauses):
            prompt = f"""
作为专业的法务顾问，请审查以下合同条款：

条款类型：{clause.clause_type}
条款内容：{clause.content}

请从以下方面进行分析：
1. 法律风险（高/中/低）
2. 可能存在的不利点
3. 修改建议

请提供专业、简洁的审查意见。
"""
            
            llm_opinion = self._call_llm(prompt)
            
            # 更新建议
            result.clauses[i].suggestion = f"{clause.suggestion}\n\nAI专业意见：{llm_opinion}"
        
        # 生成总体审查意见
        overall_prompt = f"""
请作为专业法务，对以下合同生成总体审查意见：

合同类型：{result.contract_type}
当事人：{', '.join(result.parties)}

已识别风险：
{chr(10).join(['- ' + risk for risk in result.risks])}

请提供：
1. 总体风险评估
2. 重点注意事项
3. 谈判建议
"""
        
        overall_opinion = self._call_llm(overall_prompt)
        result.suggestions.append(f"\nAI总体意见：\n{overall_opinion}")
        
        return result
    
    def _compare_with_standard_clauses(self, result: ReviewResult) -> ReviewResult:
        """与标准条款模板比对"""
        
        for i, clause in enumerate(result.clauses):
            if clause.clause_type in self.STANDARD_CLAUSES:
                standard = self.STANDARD_CLAUSES[clause.clause_type]
                result.clauses[i].suggestion += f"\n\n标准条款参考：{standard}"
        
        return result
    
    def batch_review(self, contract_texts: List[str]) -> List[ReviewResult]:
        """
        批量审查合同
        
        Args:
            contract_texts: 合同文本列表
        
        Returns:
            审查结果列表
        """
        results = []
        
        for i, text in enumerate(contract_texts, 1):
            print(f"\n正在审查第 {i}/{len(contract_texts)} 份合同...")
            result = self.enhanced_review(text)
            results.append(result)
        
        print(f"\n✓ 批量审查完成，共审查 {len(results)} 份合同")
        return results
    
    def generate_detailed_report(self, result: ReviewResult) -> Dict:
        """
        生成详细审查报告数据
        
        Args:
            result: 审查结果
        
        Returns:
            详细的报告数据字典
        """
        report = {
            "summary": {
                "contract_type": result.contract_type,
                "parties_count": len(result.parties),
                "clauses_reviewed": len(result.clauses),
                "high_risks": len([c for c in result.clauses if c.risk_level == RiskLevel.HIGH]),
                "medium_risks": len([c for c in result.clauses if c.risk_level == RiskLevel.MEDIUM]),
                "low_risks": len([c for c in result.clauses if c.risk_level == RiskLevel.LOW])
            },
            "parties": result.parties,
            "clauses": [
                {
                    "type": c.clause_type,
                    "content": c.content,
                    "risk_level": c.risk_level.value,
                    "suggestion": c.suggestion
                }
                for c in result.clauses
            ],
            "risks": result.risks,
            "suggestions": result.suggestions
        }
        
        return report


# 测试代码
if __name__ == "__main__":
    # 创建增强版审查器
    reviewer = EnhancedContractReviewer(use_llm=False)  # 先不使用LLM
    
    # 测试合同
    test_contract = """
    甲方：深圳某某科技有限公司
    乙方：北京某某技术服务公司
    
    第一条 项目内容
    乙方为甲方开发一套管理软件系统。
    
    第二条 合同价款
    合同总价款为人民币100万元，分三期支付。
    
    第三条 履行期限
    乙方应在合同签订后6个月内完成系统开发。
    
    第四条 违约责任
    任何一方违约，需向守约方支付合同总价30%的违约金。
    
    第五条 争议解决
    双方因本合同发生争议，应友好协商解决；协商不成的，提交甲方所在地人民法院诉讼解决。
    """
    
    # 执行增强版审查
    result = reviewer.enhanced_review(test_contract)
    
    # 打印结果
    print("\n" + "="*60)
    print("增强版审查结果")
    print("="*60)
    print(f"合同类型：{result.contract_type}")
    print(f"当事人：{', '.join(result.parties)}")
    print(f"\n条款审查：")
    for clause in result.clauses:
        print(f"  - {clause.clause_type} ({clause.risk_level.value})")
        print(f"    建议：{clause.suggestion[:100]}...")
    
    print(f"\n风险摘要：{len(result.risks)} 项")
    print(f"审查建议：{len(result.suggestions)} 条")
    print("="*60)
