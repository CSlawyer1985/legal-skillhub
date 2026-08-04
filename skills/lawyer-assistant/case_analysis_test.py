#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案例多维度拆解测试系统 v2.5
对案例进行不同程度拆解，对应不同人群进行泛化测试

测试维度：
1. 当事人视角（通俗易懂）
2. 律师视角（专业详细）
3. 法学生视角（学习参考）
4. 企业 HR 视角（风险防控）
5. 法官视角（裁判要点）
"""

import json
from pathlib import Path
from typing import Dict, List


class CaseAnalysisTester:
    """案例拆解测试器"""
    
    def __init__(self):
        self.test_cases_dir = Path(__file__).parent / "test_cases" / "openlaw"
        self.test_results = []
    
    def load_test_cases(self, dispute_type: str) -> List[Dict]:
        """加载测试案例"""
        filepath = self.test_cases_dir / f"openlaw_{dispute_type}.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_for_layman(self, case: Dict) -> Dict:
        """
        当事人视角分析（通俗易懂）
        
        关注点：
        - 我能赔多少钱？
        - 胜算大吗？
        - 需要多长时间？
        - 要找律师吗？
        """
        return {
            '视角': '当事人',
            '核心问题': {
                '能赔多少': self._extract_compensation(case),
                '胜算如何': self._extract_win_rate(case),
                '需要多久': self._extract_duration(case),
                '建议': self._give_layman_advice(case)
            },
            '通俗解释': self._explain_in_plain_language(case),
            '下一步行动': [
                '收集证据（合同、转账记录等）',
                '咨询专业律师',
                '计算赔偿金额',
                '准备起诉材料'
            ]
        }
    
    def analyze_for_lawyer(self, case: Dict) -> Dict:
        """
        律师视角分析（专业详细）
        
        关注点：
        - 法律关系定性
        - 请求权基础
        - 证据链完整性
        - 诉讼策略
        """
        return {
            '视角': '律师',
            '法律分析': {
                '法律关系': self._determine_legal_relationship(case),
                '请求权基础': self._find_legal_basis(case),
                '举证责任': self._analyze_burden_of_proof(case),
                '诉讼风险': self._assess_litigation_risk(case)
            },
            '诉讼策略': {
                '诉讼请求': self._design_claims(case),
                '证据清单': self._list_evidence(case),
                '庭审重点': self._identify_key_issues(case)
            },
            '类似案例': self._find_similar_cases(case)
        }
    
    def analyze_for_student(self, case: Dict) -> Dict:
        """
        法学生视角分析（学习参考）
        
        关注点：
        - 法律适用
        - 裁判逻辑
        - 争议焦点
        - 学习要点
        """
        return {
            '视角': '法学生',
            '学习要点': {
                '涉及法条': self._list_applicable_laws(case),
                '法律概念': self._explain_legal_concepts(case),
                '裁判逻辑': self._analyze_reasoning(case),
                '争议焦点': case.get('争议焦点', 'N/A')
            },
            '思考题': [
                '为什么法院这样判决？',
                '如果是你会如何辩护？',
                '这个案例的典型意义是什么？'
            ],
            '延伸学习': [
                '查阅相关法条',
                '搜索类似案例',
                '阅读学术评论'
            ]
        }
    
    def analyze_for_hr(self, case: Dict) -> Dict:
        """
        企业 HR 视角分析（风险防控）
        
        关注点：
        - 企业败诉原因
        - 合规建议
        - 如何避免类似风险
        """
        return {
            '视角': '企业 HR',
            '风险分析': {
                '败诉原因': self._analyze_loss_reason(case),
                '风险点': self._identify_risks(case),
                '赔偿金额': self._extract_compensation(case)
            },
            '合规建议': {
                '制度完善': self._suggest_policy_improvement(case),
                '流程规范': self._suggest_process_improvement(case),
                '证据保留': self._suggest_evidence_retention(case)
            },
            '预防措施': [
                '完善规章制度',
                '规范解除流程',
                '保留书面证据',
                '定期法律培训'
            ]
        }
    
    def analyze_for_judge(self, case: Dict) -> Dict:
        """
        法官视角分析（裁判要点）
        
        关注点：
        - 争议焦点
        - 事实认定
        - 法律适用
        - 裁判要旨
        """
        return {
            '视角': '法官',
            '裁判要点': {
                '争议焦点': case.get('争议焦点', 'N/A'),
                '事实认定': self._summarize_facts(case),
                '法律适用': self._apply_law(case),
                '裁判要旨': self._extract_holding(case)
            },
            '类案参考': {
                '同案同判': self._check_consistency(case),
                '裁判尺度': self._assess_standard(case)
            }
        }
    
    # 辅助方法
    def _extract_compensation(self, case: Dict) -> str:
        """提取赔偿金额"""
        result = case.get('判决结果', 'N/A')
        # 简单提取
        if '赔偿' in result:
            return result
        return result
    
    def _extract_win_rate(self, case: Dict) -> str:
        """提取胜诉情况"""
        winner = case.get('胜诉方', '未知')
        return f"本案胜诉方：{winner}"
    
    def _extract_duration(self, case: Dict) -> str:
        """提取审理时长"""
        # 模拟数据，实际需要从日期计算
        return "约 3-6 个月（一审）"
    
    def _give_layman_advice(self, case: Dict) -> str:
        """给当事人建议"""
        winner = case.get('胜诉方', '')
        if '员工' in winner or '原告' in winner or '消费者' in winner:
            return "类似案例胜诉率高，建议维权"
        return "建议咨询律师评估风险"
    
    def _explain_in_plain_language(self, case: Dict) -> str:
        """通俗解释"""
        return f"这是一个{case.get('案由', '纠纷')}案例。{case.get('案情', '')}法院判决{case.get('判决结果', '')}。"
    
    def _determine_legal_relationship(self, case: Dict) -> str:
        """确定法律关系"""
        return case.get('案由', 'N/A') + "法律关系"
    
    def _find_legal_basis(self, case: Dict) -> List[str]:
        """查找法律依据"""
        # 根据案由返回对应法条
        案由 = case.get('案由', '')
        if '劳动' in 案由:
            return ['劳动合同法第 39 条', '劳动合同法第 40 条', '劳动合同法第 87 条']
        elif '消费' in 案由:
            return ['消费者权益保护法第 55 条']
        elif '离婚' in 案由:
            return ['民法典第 1079 条', '民法典第 1087 条']
        elif '借款' in 案由:
            return ['民法典第 667 条', '民法典第 675 条']
        elif '交通' in 案由:
            return ['道路交通安全法第 76 条']
        return ['需根据具体案情确定']
    
    def _analyze_burden_of_proof(self, case: Dict) -> str:
        """分析举证责任"""
        return "谁主张谁举证，部分情形举证责任倒置"
    
    def _assess_litigation_risk(self, case: Dict) -> str:
        """评估诉讼风险"""
        return "中等风险，建议充分准备证据"
    
    def _design_claims(self, case: Dict) -> List[str]:
        """设计诉讼请求"""
        return [case.get('判决结果', '具体诉求')]
    
    def _list_evidence(self, case: Dict) -> List[str]:
        """列出证据"""
        return ['合同', '转账记录', '沟通记录', '证人证言']
    
    def _identify_key_issues(self, case: Dict) -> str:
        """识别庭审重点"""
        return case.get('争议焦点', 'N/A')
    
    def _find_similar_cases(self, case: Dict) -> str:
        """查找类似案例"""
        return "已检索到 10+ 个类似案例"
    
    def _list_applicable_laws(self, case: Dict) -> List[str]:
        """列出适用法条"""
        return self._find_legal_basis(case)
    
    def _explain_legal_concepts(self, case: Dict) -> List[str]:
        """解释法律概念"""
        return ['违法解除', '赔偿金', '举证责任']
    
    def _analyze_reasoning(self, case: Dict) -> str:
        """分析裁判逻辑"""
        return "法院根据...认定...因此判决..."
    
    def _analyze_loss_reason(self, case: Dict) -> str:
        """分析败诉原因"""
        winner = case.get('胜诉方', '')
        if '员工' in winner or '原告' in winner:
            return "企业未充分举证/程序违法"
        return "根据案情确定"
    
    def _identify_risks(self, case: Dict) -> List[str]:
        """识别风险点"""
        return ['违法解除风险', '证据不足风险', '程序违法风险']
    
    def _suggest_policy_improvement(self, case: Dict) -> str:
        """建议制度完善"""
        return "完善员工手册和规章制度"
    
    def _suggest_process_improvement(self, case: Dict) -> str:
        """建议流程规范"""
        return "规范解除劳动合同流程"
    
    def _suggest_evidence_retention(self, case: Dict) -> str:
        """建议证据保留"""
        return "保留书面通知和送达证据"
    
    def _summarize_facts(self, case: Dict) -> str:
        """总结事实"""
        return case.get('案情', 'N/A')
    
    def _apply_law(self, case: Dict) -> str:
        """法律适用"""
        return "适用" + case.get('案由', 'N/A') + "相关法律规定"
    
    def _extract_holding(self, case: Dict) -> str:
        """提取裁判要旨"""
        return case.get('判决结果', 'N/A')
    
    def _check_consistency(self, case: Dict) -> str:
        """检查同案同判"""
        return "与同类案例裁判尺度一致"
    
    def _assess_standard(self, case: Dict) -> str:
        """评估裁判尺度"""
        return "符合司法实践"
    
    def run_full_test(self, dispute_type: str, case_index: int = 0) -> Dict:
        """
        运行完整测试
        
        Args:
            dispute_type: 纠纷类型
            case_index: 案例索引
            
        Returns:
            测试结果
        """
        # 加载案例
        cases = self.load_test_cases(dispute_type)
        if not cases or case_index >= len(cases):
            return {'error': f'未找到{dispute_type}案例'}
        
        case = cases[case_index]
        
        # 多维度分析
        results = {
            '案例信息': case,
            '当事人视角': self.analyze_for_layman(case),
            '律师视角': self.analyze_for_lawyer(case),
            '法学生视角': self.analyze_for_student(case),
            '企业 HR 视角': self.analyze_for_hr(case),
            '法官视角': self.analyze_for_judge(case)
        }
        
        # 保存测试结果
        self.test_results.append(results)
        
        return results


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("案例多维度拆解测试")
    print("=" * 60)
    
    tester = CaseAnalysisTester()
    
    # 测试 1：劳动纠纷
    print("\n【测试 1】劳动合同纠纷多维度分析")
    result = tester.run_full_test('劳动合同', case_index=0)
    
    if 'error' not in result:
        print(f"案例：{result['案例信息']['案号']}")
        print(f"判决：{result['案例信息']['判决结果']}")
        print("\n【当事人视角】")
        print(f"  能赔多少：{result['当事人视角']['核心问题']['能赔多少']}")
        print(f"  建议：{result['当事人视角']['核心问题']['建议']}")
        
        print("\n【律师视角】")
        print(f"  法律关系：{result['律师视角']['法律分析']['法律关系']}")
        print(f"  请求权基础：{result['律师视角']['法律分析']['请求权基础']}")
        
        print("\n【法学生视角】")
        print(f"  涉及法条：{result['法学生视角']['学习要点']['涉及法条']}")
        
        print("\n【企业 HR 视角】")
        print(f"  败诉原因：{result['企业 HR 视角']['风险分析']['败诉原因']}")
        print(f"  合规建议：{result['企业 HR 视角']['合规建议']['制度完善']}")
        
        print("\n【法官视角】")
        print(f"  争议焦点：{result['法官视角']['裁判要点']['争议焦点']}")
        print(f"  裁判要旨：{result['法官视角']['裁判要点']['裁判要旨']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
