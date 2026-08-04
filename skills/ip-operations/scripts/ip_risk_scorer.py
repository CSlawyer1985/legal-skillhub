#!/usr/bin/env python3
"""
IP风险评分器
IP Risk Scorer

功能：基于四维20项指标评分卡进行知识产权尽职调查和风险评估
来源：国知局《专利价值分析指标体系操作手册》+ 学术研究
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class IndicatorScore:
    """指标评分结果"""
    indicator: str
    weight: float
    score: float
    max_score: float = 10.0
    weighted_score: float = 0.0
    source: str = ""


class IPRiskScorer:
    """知识产权风险评分器"""
    
    # 四维权重体系
    DIMENSION_WEIGHTS = {
        "权属清晰度": 0.30,
        "有效性评估": 0.25,
        "侵权风险": 0.25,
        "价值评估": 0.20
    }
    
    # 20项指标定义
    INDICATORS = {
        "权属清晰度": [
            {"name": "权属链条完整性", "weight": 0.08, "source": "国知局《专利价值分析指标体系操作手册》"},
            {"name": "发明人身份确认", "weight": 0.05, "source": "专利法实施细则"},
            {"name": "职务发明认定", "weight": 0.05, "source": "专利法第六条"},
            {"name": "共有协议完整性", "weight": 0.05, "source": "专利法第十五条"},
            {"name": "质押/许可负担", "weight": 0.07, "source": "国知局质押登记办法"},
        ],
        "有效性评估": [
            {"name": "授权状态", "weight": 0.05, "source": "专利法"},
            {"name": "缴费状态", "weight": 0.05, "source": "专利法实施细则"},
            {"name": "无效宣告风险", "weight": 0.05, "source": "AHP层次分析法"},
            {"name": "保护范围宽度", "weight": 0.05, "source": "Smolka专利研究"},
            {"name": "等同原则适用性", "weight": 0.05, "source": "最高法司法解释"},
        ],
        "侵权风险": [
            {"name": "FTO自由实施分析", "weight": 0.07, "source": "技术尽职调查标准"},
            {"name": "侵权概率", "weight": 0.06, "source": "诉讼统计分析"},
            {"name": "潜在侵权方数量", "weight": 0.04, "source": "市场分析方法"},
            {"name": "规避设计难度", "weight": 0.04, "source": "技术评估方法"},
            {"name": "诉讼成本预估", "weight": 0.04, "source": "律师协会统计"},
        ],
        "价值评估": [
            {"name": "技术成熟度TRL", "weight": 0.05, "source": "NASA TRL标准"},
            {"name": "市场覆盖度", "weight": 0.05, "source": "《专利价值分析指标体系操作手册》"},
            {"name": "替代技术数量", "weight": 0.04, "source": "Park Y研究"},
            {"name": "剩余保护期", "weight": 0.03, "source": "专利法"},
            {"name": "年化收益预估", "weight": 0.03, "source": "《专利价值分析指标体系操作手册》"},
        ]
    }
    
    # 风险等级阈值
    RISK_LEVELS = {
        "A": {"min": 80, "max": 100, "recommendation": "优先推进", "description": "可直接进入成果转化"},
        "B": {"min": 60, "max": 79, "recommendation": "积极推进", "description": "需补充1-2项尽调"},
        "C": {"min": 40, "max": 59, "recommendation": "补强后推进", "description": "需解决关键风险点"},
        "D": {"min": 0, "max": 39, "recommendation": "暂缓", "description": "建议完善IP布局后再评估"},
    }
    
    # TRL评分映射
    TRL_SCORE_MAP = {
        9: 10, 8: 9, 7: 8, 6: 7, 5: 6, 4: 5, 3: 4, 2: 3, 1: 2
    }
    
    def __init__(self):
        self.scoring_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    def calculate_dimension_score(
        self, 
        dimension: str, 
        scores: Dict[str, float]
    ) -> Dict:
        """
        计算单一维度的得分
        
        参数:
            dimension: 维度名称
            scores: 该维度下各指标得分 {指标名: 得分(1-10)}
        
        返回:
            维度得分结果
        """
        indicators = self.INDICATORS.get(dimension, [])
        dimension_weight = self.DIMENSION_WEIGHTS.get(dimension, 0)
        
        indicator_results = []
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for indicator in indicators:
            name = indicator["name"]
            weight = indicator["weight"]
            source = indicator["source"]
            
            score = scores.get(name, 5)  # 默认5分
            
            # 计算维度内加权得分（维度权重×该指标在维度内的相对权重×得分）
            # 维度内归一化权重
            dim_total_weight = sum(ind["weight"] for ind in indicators)
            normalized_weight = weight / dim_total_weight if dim_total_weight > 0 else 0
            
            # 维度得分 = Σ(指标得分×指标权重占比) × 10（满分10分）
            weighted_score = score * normalized_weight
            
            indicator_results.append({
                "indicator": name,
                "weight": weight,
                "score": score,
                "normalized_weight": normalized_weight,
                "weighted_score": weighted_score,
                "source": source
            })
            
            total_weighted_score += weighted_score
            total_weight += weight
        
        # 维度得分（10分制）
        dimension_score = total_weighted_score  # 已经是0-10的得分
        
        return {
            "dimension": dimension,
            "dimension_weight": dimension_weight,
            "indicators": indicator_results,
            "dimension_score": dimension_score,
            "max_score": 10.0
        }
    
    def calculate_comprehensive_score(
        self, 
        all_scores: Dict[str, Dict[str, float]]
    ) -> Dict:
        """
        计算综合评分
        
        参数:
            all_scores: 所有维度得分 {
                "权属清晰度": {"指标名": 得分, ...},
                "有效性评估": {...},
                ...
            }
        
        返回:
            综合评分结果
        """
        dimension_results = []
        weighted_total_score = 0.0  # 用于综合评分
        
        for dimension, scores in all_scores.items():
            result = self.calculate_dimension_score(dimension, scores)
            dimension_results.append(result)
            # 综合评分 = Σ(维度得分×维度权重)，得分已归一化到0-10
            weighted_total_score += result["dimension_score"] * self.DIMENSION_WEIGHTS[dimension]
        
        # 确定风险等级（综合评分已经是在权重下的加权得分，范围约0-10）
        # 转换为0-100分制
        total_score = weighted_total_score * 10
        risk_level = self._determine_risk_level(total_score)
        
        return {
            "scoring_time": self.scoring_time,
            "dimensions": dimension_results,
            "comprehensive_score": total_score,
            "risk_level": risk_level
        }
    
    def _determine_risk_level(self, score: float) -> Dict:
        """确定风险等级"""
        for level, info in self.RISK_LEVELS.items():
            if info["min"] <= score <= info["max"]:
                return {
                    "level": level,
                    "recommendation": info["recommendation"],
                    "description": info["description"]
                }
        return {"level": "D", "recommendation": "暂缓", "description": "评分异常"}
    
    def generate_risk_report(self, score_result: Dict) -> str:
        """生成风险评估报告"""
        lines = [
            "=" * 70,
            "知识产权尽职调查风险评估报告",
            "=" * 70,
            f"评估时间: {score_result.get('scoring_time', 'N/A')}",
            "",
        ]
        
        # 各维度得分
        lines.append("-" * 70)
        lines.append("各维度评估结果")
        lines.append("-" * 70)
        
        for dim_result in score_result["dimensions"]:
            dim_name = dim_result["dimension"]
            dim_weight = dim_result["dimension_weight"]
            dim_score = dim_result["dimension_score"]
            
            lines.append(f"\n【{dim_name}】(权重{float(dim_weight)*100:.0f}%)")
            lines.append(f"  维度得分: {dim_score:.2f}/10")
            
            for ind in dim_result["indicators"]:
                indicator = ind["indicator"]
                weight = ind["weight"]
                score = ind["score"]
                source = ind["source"]
                
                lines.append(
                    f"    • {indicator}: {score:.0f}/10 "
                    f"(权重{float(weight)*100:.0f}%) "
                    f"[来源: {source}]"
                )
        
        # 综合评分
        lines.append("")
        lines.append("-" * 70)
        lines.append("综合评分")
        lines.append("-" * 70)
        
        comp_score = score_result["comprehensive_score"]
        risk = score_result["risk_level"]
        
        lines.append(f"\n  综合评分: {comp_score:.2f}/100")
        lines.append(f"  风险等级: {risk['level']}级")
        lines.append(f"  建议: {risk['recommendation']}")
        lines.append(f"  说明: {risk['description']}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def validate_input_scores(self, scores: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        验证输入得分是否有效
        
        参数:
            scores: 指标得分
        
        返回:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        for indicator, score in scores.items():
            if not isinstance(score, (int, float)):
                errors.append(f"{indicator}: 得分必须为数字")
            elif score < 1 or score > 10:
                errors.append(f"{indicator}: 得分必须在1-10之间")
        
        return len(errors) == 0, errors


def main():
    """主函数 - 示例使用"""
    scorer = IPRiskScorer()
    
    print("\n" + "=" * 70)
    print("示例：某发明专利尽职调查评分")
    print("=" * 70)
    
    # 所有20项指标的得分 (1-10分)
    all_scores = {
        "权属清晰度": {
            "权属链条完整性": 9,      # 权属链条完整
            "发明人身份确认": 9,      # 身份明确
            "职务发明认定": 8,       # 有协议约定
            "共有协议完整性": 10,     # 无共有
            "质押/许可负担": 9,       # 无负担
        },
        "有效性评估": {
            "授权状态": 10,           # 已授权
            "缴费状态": 10,          # 已缴清
            "无效宣告风险": 7,       # 有一定风险
            "保护范围宽度": 8,       # 范围较宽
            "等同原则适用性": 8,      # 等同特征明显
        },
        "侵权风险": {
            "FTO自由实施分析": 8,    # 基本自由
            "侵权概率": 6,           # 有一定侵权风险
            "潜在侵权方数量": 7,      # 3-5家
            "规避设计难度": 7,        # 较难规避
            "诉讼成本预估": 6,        # 成本适中
        },
        "价值评估": {
            "技术成熟度TRL": 7,       # TRL 6-7
            "市场覆盖度": 8,          # 多国覆盖
            "替代技术数量": 7,        # 替代性较弱
            "剩余保护期": 8,          # 剩余10-12年
            "年化收益预估": 7,        # 500-1000万
        }
    }
    
    # 计算综合评分
    result = scorer.calculate_comprehensive_score(all_scores)
    
    # 生成报告
    report = scorer.generate_risk_report(result)
    print(report)
    
    # 输出权重来源
    print("\n" + "=" * 70)
    print("指标权重来源汇总")
    print("=" * 70)
    
    for dimension, indicators in scorer.INDICATORS.items():
        weight = scorer.DIMENSION_WEIGHTS[dimension]
        print(f"\n【{dimension}】(权重: {weight*100:.0f}%)")
        for ind in indicators:
            print(f"  {ind['name']}: {ind['weight']*100:.0f}% [来源: {ind['source']}]")


if __name__ == "__main__":
    main()
