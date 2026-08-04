#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
劳动纠纷证据对抗流程脚本
用于辅助生成证据质证意见和对抗策略
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple


class EvidenceBattle:
    """证据对抗处理器"""
    
    def __init__(self, case_info: Dict):
        self.case_info = case_info
        self.evidence_rules = {
            "真实性": {
                "认可": "对该证据的真实性予以认可",
                "不认可": "对该证据的真实性不予认可，理由：{reason}",
                "无法确认": "对该证据的真实性无法确认"
            },
            "合法性": {
                "认可": "对该证据的合法性予以认可",
                "不认可": "对该证据的合法性不予认可，该证据系通过{method}取得，属于非法证据"
            },
            "关联性": {
                "认可": "对该证据的关联性予以认可",
                "不认可": "对该证据的关联性不予认可，该证据与{focus}无关"
            },
            "证明力": {
                "充分": "该证据足以证明{fact}",
                "不充分": "该证据不能证明{fact}，理由：{reason}",
                "需佐证": "该证据需要结合其他证据综合认定"
            }
        }
    
    def analyze_evidence_strength(self, evidence_type: str, party: str) -> Dict:
        """分析证据强弱
        
        Args:
            evidence_type: 证据类型
            party: 'employee' 或 'company'
            
        Returns:
            证据强度分析结果
        """
        strength_map = {
            "劳动合同": {"employee": 90, "company": 90},
            "工资流水": {"employee": 95, "company": 85},
            "考勤记录": {"employee": 80, "company": 70},
            "解除通知": {"employee": 85, "company": 80},
            "聊天记录": {"employee": 70, "company": 65},
            "录音": {"employee": 75, "company": 60},
            "证人证言": {"employee": 60, "company": 55},
            "规章制度": {"employee": 50, "company": 85},
            "绩效考核": {"employee": 55, "company": 80}
        }
        
        return {
            "evidence_type": evidence_type,
            "strength": strength_map.get(evidence_type, {}).get(party, 50),
            "party": "员工方" if party == "employee" else "公司方"
        }
    
    def generate_cross_examination(self, evidence: Dict, opponent_party: str) -> str:
        """生成质证意见
        
        Args:
            evidence: 证据信息
            opponent_party: 对方当事人 ('employee' 或 'company')
            
        Returns:
            质证意见文本
        """
        evidence_type = evidence.get("type", "")
        
        # 根据证据类型和对方身份生成质证策略
        strategies = {
            "劳动合同": {
                "company": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "认可",
                    "证明力": "需佐证",
                    "comment": "但强调合同约定的工资标准和岗位内容"
                },
                "employee": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "认可",
                    "证明力": "充分",
                    "comment": "注意核对合同条款与实际履行是否一致"
                }
            },
            "考勤记录": {
                "company": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "不认可",
                    "证明力": "不充分",
                    "comment": "打卡记录不能证明实际加班，员工可能在公司做私事"
                },
                "employee": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "认可",
                    "证明力": "充分",
                    "comment": "打卡记录客观反映了员工的出勤和加班情况"
                }
            },
            "工资流水": {
                "company": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "认可",
                    "证明力": "充分",
                    "comment": "恰恰证明公司已足额支付工资"
                },
                "employee": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "认可",
                    "证明力": "充分",
                    "comment": "证明工资标准和发放情况"
                }
            },
            "解除通知": {
                "company": {
                    "真实性": "认可",
                    "合法性": "认可",
                    "关联性": "认可",
                    "证明力": "充分",
                    "comment": "解除理由合法、程序合规"
                },
                "employee": {
                    "真实性": "认可",
                    "合法性": "不认可",
                    "关联性": "认可",
                    "证明力": "不充分",
                    "comment": "解除理由缺乏事实和法律依据"
                }
            }
        }
        
        strategy = strategies.get(evidence_type, {}).get(opponent_party, {})
        
        if not strategy:
            return "对该证据的真实性、合法性、关联性均予以认可，但对证明目的有异议。"
        
        # 生成质证意见
        opinions = []
        
        for dimension in ["真实性", "合法性", "关联性", "证明力"]:
            if dimension in strategy:
                result = strategy[dimension]
                template = self.evidence_rules[dimension].get(result, "")
                
                # 填充模板变量
                if "{reason}" in template:
                    if evidence_type == "考勤记录" and opponent_party == "company":
                        template = template.format(reason="打卡不等于实际工作")
                    elif evidence_type == "解除通知" and opponent_party == "employee":
                        template = template.format(reason="解除理由缺乏事实和法律依据")
                    else:
                        template = template.format(reason="证据不足以证明待证事实")
                
                if "{method}" in template:
                    template = template.format(method="非法手段")
                
                if "{focus}" in template:
                    template = template.format(focus="本案争议焦点")
                
                if "{fact}" in template:
                    template = template.format(fact="待证事实", reason="证据不足")
                
                opinions.append(f"**{dimension}**：{template}")
        
        if strategy.get("comment"):
            opinions.append(f"\n**补充意见**：{strategy['comment']}")
        
        return "\n".join(opinions)
    
    def calculate_win_rate(self, evidence_list: List[Dict], dispute_type: str) -> Dict:
        """计算胜诉率
        
        Args:
            evidence_list: 证据列表
            dispute_type: 争议类型
            
        Returns:
            胜诉率分析结果
        """
        # 不同争议类型的基础胜率
        base_rates = {
            "违法解除": {"employee": 65, "company": 35},
            "拖欠工资": {"employee": 80, "company": 20},
            "加班费": {"employee": 55, "company": 45},
            "年假工资": {"employee": 70, "company": 30},
            "社保公积金": {"employee": 60, "company": 40}
        }
        
        base = base_rates.get(dispute_type, {"employee": 50, "company": 50})
        
        # 根据证据情况调整
        employee_evidence_score = 0
        company_evidence_score = 0
        
        for evidence in evidence_list:
            party = evidence.get("party", "")
            strength = evidence.get("strength", 50)
            
            if party == "employee":
                employee_evidence_score += strength
            else:
                company_evidence_score += strength
        
        # 计算调整后的胜率
        total_score = employee_evidence_score + company_evidence_score
        if total_score > 0:
            employee_adjustment = (employee_evidence_score / total_score - 0.5) * 20
        else:
            employee_adjustment = 0
        
        employee_rate = min(95, max(5, base["employee"] + employee_adjustment))
        company_rate = 100 - employee_rate
        
        return {
            "dispute_type": dispute_type,
            "employee_win_rate": round(employee_rate, 1),
            "company_win_rate": round(company_rate, 1),
            "analysis": self._generate_win_rate_analysis(employee_rate, dispute_type)
        }
    
    def _generate_win_rate_analysis(self, win_rate: float, dispute_type: str) -> str:
        """生成胜率分析说明"""
        if win_rate >= 80:
            return f"员工方在{dispute_type}争议中证据充分，胜诉概率较高。建议积极主张权利。"
        elif win_rate >= 60:
            return f"员工方在{dispute_type}争议中有一定优势，但存在部分证据瑕疵。建议补充相关证据。"
        elif win_rate >= 40:
            return f"双方证据势均力敌，{dispute_type}争议结果存在不确定性。建议做好充分准备。"
        else:
            return f"员工方在{dispute_type}争议中处于劣势，证据不足。建议重新评估诉讼策略或寻求和解。"
    
    def generate_battle_report(self) -> str:
        """生成证据对抗报告"""
        report = []
        report.append("# 证据对抗分析报告")
        report.append(f"\n生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        report.append(f"\n案件类型：{self.case_info.get('dispute_type', '劳动争议')}")
        report.append(f"争议焦点：{self.case_info.get('focus', '待定')}")
        
        report.append("\n## 一、证据强度分析\n")
        
        evidence_list = self.case_info.get("evidence", [])
        for evidence in evidence_list:
            ev_type = evidence.get("type", "")
            party = evidence.get("party", "")
            strength = self.analyze_evidence_strength(ev_type, party)
            report.append(f"- **{ev_type}**（{strength['party']}）：强度 {strength['strength']}/100")
        
        report.append("\n## 二、质证意见\n")
        
        for evidence in evidence_list:
            ev_type = evidence.get("type", "")
            party = evidence.get("party", "")
            opponent = "company" if party == "employee" else "employee"
            
            report.append(f"\n### 针对 {ev_type} 的质证意见\n")
            cross_exam = self.generate_cross_examination(evidence, opponent)
            report.append(cross_exam)
        
        report.append("\n## 三、胜诉率评估\n")
        
        win_rate = self.calculate_win_rate(evidence_list, self.case_info.get("dispute_type", "其他"))
        report.append(f"\n**员工方胜诉概率**：{win_rate['employee_win_rate']}%")
        report.append(f"**公司方胜诉概率**：{win_rate['company_win_rate']}%")
        report.append(f"\n**分析意见**：{win_rate['analysis']}")
        
        return "\n".join(report)


def main():
    """主函数 - 示例用法"""
    
    # 示例案件信息
    case_info = {
        "dispute_type": "违法解除",
        "focus": "公司解除劳动合同是否合法",
        "evidence": [
            {"type": "劳动合同", "party": "employee", "strength": 90},
            {"type": "工资流水", "party": "employee", "strength": 95},
            {"type": "考勤记录", "party": "employee", "strength": 80},
            {"type": "解除通知", "party": "employee", "strength": 85},
            {"type": "规章制度", "party": "company", "strength": 85},
            {"type": "绩效考核", "party": "company", "strength": 80}
        ]
    }
    
    battle = EvidenceBattle(case_info)
    report = battle.generate_battle_report()
    print(report)


if __name__ == "__main__":
    main()
