#!/usr/bin/env python3
"""
IP估值计算器
IP Valuation Calculator

功能：基于五维度权重体系，使用成本法/收益法/市场法对知识产权进行估值
来源：国知局+中国技术交易所《专利价值分析指标体系操作手册》
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class WeightSource:
    """权重来源标注"""
    dimension: str
    sub_indicator: str
    weight: float
    source_type: str  # 国知局/学术/行业
    source_detail: str


class IPValuationCalculator:
    """知识产权估值计算器"""
    
    # 五维度权重体系（来源：国知局+中国技术交易所《专利价值分析指标体系操作手册》）
    DIMENSION_WEIGHTS = {
        "创新性": 0.25,
        "实用性": 0.20,
        "独占性": 0.20,
        "战略赛道": 0.15,
        "未来市场": 0.20
    }
    
    # 子指标权重
    SUB_INDICATOR_WEIGHTS = {
        "创新性": {"新颖性": 0.10, "创造性": 0.10, "技术先进性": 0.05},
        "实用性": {"可实施性": 0.08, "解决实际问题": 0.07, "TRL": 0.05},
        "独占性": {"保护范围": 0.08, "权利要求数量": 0.05, "同族覆盖": 0.04, "排他性": 0.03},
        "战略赛道": {"国家战略": 0.05, "产业政策": 0.05, "赛道热度": 0.05},
        "未来市场": {"市场规模": 0.08, "增长趋势": 0.07, "商业化路径": 0.05}
    }
    
    # 权重来源标注
    WEIGHT_SOURCES = {
        "创新性-新颖性": WeightSource("创新性", "新颖性", 0.10, "国知局", "《专利价值分析指标体系操作手册》"),
        "创新性-创造性": WeightSource("创新性", "创造性", 0.10, "学术", "Park Y技术价值评估体系"),
        "创新性-技术先进性": WeightSource("创新性", "技术先进性", 0.05, "国知局", "《专利价值分析指标体系操作手册》"),
        "实用性-可实施性": WeightSource("实用性", "可实施性", 0.08, "国知局", "《专利价值分析指标体系操作手册》"),
        "实用性-解决实际问题": WeightSource("实用性", "解决实际问题", 0.07, "国知局", "《专利价值分析指标体系操作手册》"),
        "实用性-TRL": WeightSource("实用性", "TRL", 0.05, "行业", "NASA TRL标准"),
        "独占性-保护范围": WeightSource("独占性", "保护范围", 0.08, "学术", "Smolka专利保护范围研究"),
        "独占性-权利要求数量": WeightSource("独占性", "权利要求数量", 0.05, "国知局", "《专利价值分析指标体系操作手册》"),
        "独占性-同族覆盖": WeightSource("独占性", "同族覆盖", 0.04, "WIPO", "WIPO专利家族分析指南"),
        "独占性-排他性": WeightSource("独占性", "排他性", 0.03, "国知局", "《专利价值分析指标体系操作手册》"),
        "战略赛道-国家战略": WeightSource("战略赛道", "国家战略", 0.05, "政策", "《知识产权强国建设纲要》"),
        "战略赛道-产业政策": WeightSource("战略赛道", "产业政策", 0.05, "政策", "工信部产业目录"),
        "战略赛道-赛道热度": WeightSource("战略赛道", "赛道热度", 0.05, "行业", "Gartner技术成熟度曲线"),
        "未来市场-市场规模": WeightSource("未来市场", "市场规模", 0.08, "国知局", "《专利价值分析指标体系操作手册》"),
        "未来市场-增长趋势": WeightSource("未来市场", "增长趋势", 0.07, "OECD", "OECD知识产权估值指南"),
        "未来市场-商业化路径": WeightSource("未来市场", "商业化路径", 0.05, "国知局", "《专利价值分析指标体系操作手册》"),
    }
    
    # 技术生命周期（年）
    TECH_LIFECYCLES = {
        "软件": (2, 5),
        "IT": (2, 5),
        "电子": (5, 8),
        "通信": (5, 8),
        "机械": (8, 15),
        "制造": (8, 15),
        "生物医药": (10, 20),
        "材料": (10, 15),
        "化工": (8, 12),
        "新能源": (8, 15),
        "默认": (5, 10)
    }
    
    # 行业技术贡献率基准（来源：国知局）
    TECH_CONTRIBUTION_RATES = {
        "制造业": (0.15, 0.30, 0.20),
        "IT": (0.25, 0.40, 0.30),
        "软件": (0.25, 0.40, 0.30),
        "生物医药": (0.30, 0.50, 0.40),
        "电子通信": (0.20, 0.35, 0.25),
        "新能源": (0.25, 0.40, 0.30),
        "化工": (0.20, 0.35, 0.25),
        "默认": (0.20, 0.35, 0.28)
    }
    
    def __init__(self):
        self.valuation_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    def calculate_dimension_score(self, scores: Dict[str, float]) -> Tuple[Dict[str, float], float]:
        """
        计算五维度得分和综合得分
        
        参数:
            scores: 各维度得分 {维度名: 得分(1-10)}
        
        返回:
            (维度加权得分, 综合得分)
        """
        dimension_scores = {}
        weighted_total = 0.0
        
        for dimension, weight in self.DIMENSION_WEIGHTS.items():
            score = scores.get(dimension, 0)
            weighted_score = score * weight
            dimension_scores[dimension] = {
                "score": score,
                "weight": weight,
                "weighted_score": weighted_score,
                "source": "国知局+中技所《专利价值分析指标体系操作手册》"
            }
            weighted_total += weighted_score
        
        return dimension_scores, weighted_total
    
    def cost_method(
        self,
        rd_cost: float,
        profit_margin: float = 0.30,
        tech_domain: str = "默认",
        years_used: int = 0
    ) -> Dict:
        """
        成本法估值
        
        公式: V = C研发 × (1 + 合理利润率) × 技术贬值系数
        
        参数:
            rd_cost: 研发成本（万元）
            profit_margin: 合理利润率 (0-1)，默认30%
            tech_domain: 技术领域
            years_used: 已使用年限
        
        返回:
            成本法估值结果
        """
        # 获取技术生命周期
        lifecycle_range = self.TECH_LIFECYCLES.get(tech_domain, self.TECH_LIFECYCLES["默认"])
        lifecycle = sum(lifecycle_range) / 2  # 取中间值
        
        # 计算贬值系数
        depreciation_rate = min(years_used / lifecycle, 1.0)
        depreciation_factor = 1 - depreciation_rate
        
        # 计算估值
        value = rd_cost * (1 + profit_margin) * depreciation_factor
        
        return {
            "method": "成本法",
            "formula": "V = C研发 × (1 + 合理利润率) × 技术贬值系数",
            "parameters": {
                "C研发": {"value": rd_cost, "unit": "万元", "source": "研发费用核算"},
                "合理利润率": {"value": profit_margin, "source": "技术交易所实践"},
                "技术贬值系数": {
                    "value": depreciation_factor,
                    "calculation": f"1 - {years_used}/{lifecycle:.1f}年"
                }
            },
            "result": {"value": value, "unit": "万元"},
            "source": "国知局+中技所《专利价值分析指标体系操作手册》",
            "assumption": f"技术生命周期{lifecycle:.1f}年（{tech_domain}领域）"
        }
    
    def income_method(
        self,
        annual_revenue: Dict[str, float],
        tech_domain: str = "默认",
        discount_rate: float = 0.12,
        ip_risk_premium: float = 0.05,
        years: int = 5
    ) -> Dict:
        """
        收益法估值
        
        公式: V = Σ [ Ci × 技术贡献率 / (1 + r)^i ]
        
        参数:
            annual_revenue: 年收益预测 {"保守": x, "中性": x, "乐观": x}（万元）
            tech_domain: 技术领域
            discount_rate: WACC折现率 (0-1)
            ip_risk_premium: IP风险溢价 (0-1)，默认5%
            years: 收益年限
        
        返回:
            收益法三情景估值结果
        """
        # 获取技术贡献率
        contrib_range = self.TECH_CONTRIBUTION_RATES.get(tech_domain, self.TECH_CONTRIBUTION_RATES["默认"])
        
        # 计算综合折现率
        r = discount_rate + ip_risk_premium
        
        results = {}
        scenario_descriptions = {
            "保守": "采用最低技术贡献率和收益预测",
            "中性": "采用中等技术贡献率和收益预测",
            "乐观": "采用最高技术贡献率和收益预测"
        }
        
        for scenario, revenue in annual_revenue.items():
            # 选择技术贡献率
            if scenario == "保守":
                tech_contrib = contrib_range[0]  # 下限
            elif scenario == "中性":
                tech_contrib = contrib_range[2]  # 典型值
            else:  # 乐观
                tech_contrib = contrib_range[1]  # 上限
            
            # 计算各年现值
            total_value = 0.0
            year_values = []
            
            for i in range(1, years + 1):
                discounted_cash_flow = (revenue * tech_contrib) / ((1 + r) ** i)
                total_value += discounted_cash_flow
                year_values.append({
                    "year": i,
                    "annual_royalty": revenue * tech_contrib,
                    "discount_factor": 1 / ((1 + r) ** i),
                    "present_value": discounted_cash_flow
                })
            
            results[scenario] = {
                "description": scenario_descriptions[scenario],
                "parameters": {
                    "年收益预测": {"value": revenue, "unit": "万元"},
                    "技术贡献率": {"value": tech_contrib, "source": f"国知局{tech_domain}行业基准"},
                    "折现率": {"value": r, "calculation": f"{discount_rate} + {ip_risk_premium}"},
                    "收益年限": {"value": years, "unit": "年"}
                },
                "year_values": year_values,
                "result": {"value": total_value, "unit": "万元"}
            }
        
        return {
            "method": "收益法",
            "formula": "V = Σ [ Ci × 技术贡献率 / (1 + r)^i ]",
            "scenarios": results,
            "source": "国知局+中技所《专利价值分析指标体系操作手册》"
        }
    
    def market_method(
        self,
        comparable_price: float,
        dimension_scores: Dict[str, float],
        comparable_scores: Dict[str, float] = None
    ) -> Dict:
        """
        市场法估值
        
        公式: V = 可比交易价格 × 调整系数
        
        参数:
            comparable_price: 可比交易价格（万元）
            dimension_scores: 目标专利五维度得分
            comparable_scores: 可比专利五维度得分，默认全8分
        
        返回:
            市场法估值结果
        """
        if comparable_scores is None:
            comparable_scores = {dim: 8.0 for dim in self.DIMENSION_WEIGHTS.keys()}
        
        # 计算调整系数
        adjustment = 0.0
        adjustment_details = []
        
        for dimension, weight in self.DIMENSION_WEIGHTS.items():
            target_score = dimension_scores.get(dimension, 5)
            comparable_score = comparable_scores.get(dimension, 8)
            diff = (target_score - comparable_score) / 10
            dim_adjustment = diff * weight
            adjustment += dim_adjustment
            adjustment_details.append({
                "dimension": dimension,
                "weight": weight,
                "target_score": target_score,
                "comparable_score": comparable_score,
                "adjustment": dim_adjustment
            })
        
        adjustment_factor = 1.0 + adjustment
        value = comparable_price * adjustment_factor
        
        return {
            "method": "市场法",
            "formula": "V = 可比交易价格 × 调整系数",
            "parameters": {
                "可比交易价格": {"value": comparable_price, "unit": "万元", "source": "智慧芽/技术交易所"},
                "调整系数": {
                    "value": adjustment_factor,
                    "calculation": f"1.0 + {adjustment:.4f}"
                }
            },
            "adjustment_details": adjustment_details,
            "result": {"value": value, "unit": "万元"},
            "source": "国知局+中技所《专利价值分析指标体系操作手册》"
        }
    
    def comprehensive_valuation(
        self,
        rd_cost: Optional[float] = None,
        annual_revenue: Optional[Dict[str, float]] = None,
        comparable_price: Optional[float] = None,
        tech_domain: str = "默认",
        dimension_scores: Optional[Dict[str, float]] = None,
        method_weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        综合估值
        
        参数:
            rd_cost: 研发成本（万元）
            annual_revenue: 年收益预测 {"保守": x, "中性": x, "乐观": x}
            comparable_price: 可比交易价格
            tech_domain: 技术领域
            dimension_scores: 五维度得分
            method_weights: 三种方法的权重 {"成本法": x, "收益法": x, "市场法": x}
        
        返回:
            综合估值结果
        """
        # 默认方法权重
        if method_weights is None:
            method_weights = {"成本法": 0.20, "收益法": 0.50, "市场法": 0.30}
        
        # 默认五维度得分
        if dimension_scores is None:
            dimension_scores = {dim: 7.0 for dim in self.DIMENSION_WEIGHTS.keys()}
        
        results = {
            "valuation_time": self.valuation_time,
            "tech_domain": tech_domain,
            "dimension_scores": {},
            "methods": {},
            "recommended_range": {}
        }
        
        # 计算维度得分
        dim_scores, comprehensive_dim_score = self.calculate_dimension_score(dimension_scores)
        results["dimension_scores"] = dim_scores
        results["comprehensive_dimension_score"] = comprehensive_dim_score
        
        # 成本法
        if rd_cost is not None:
            results["methods"]["成本法"] = self.cost_method(rd_cost, tech_domain=tech_domain)
        
        # 收益法
        if annual_revenue is not None:
            results["methods"]["收益法"] = self.income_method(
                annual_revenue, 
                tech_domain=tech_domain
            )
        
        # 市场法
        if comparable_price is not None:
            results["methods"]["市场法"] = self.market_method(
                comparable_price, 
                dimension_scores
            )
        
        # 计算综合估值
        if len(results["methods"]) >= 2:
            total_weight = sum(method_weights.values())
            
            # 中性情景收益法估值
            income_value = None
            if "收益法" in results["methods"]:
                income_value = results["methods"]["收益法"]["scenarios"]["中性"]["result"]["value"]
            
            values = {
                "成本法": results["methods"].get("成本法", {}).get("result", {}).get("value", 0),
                "收益法": income_value or 0,
                "市场法": results["methods"].get("市场法", {}).get("result", {}).get("value", 0)
            }
            
            weighted_sum = sum(
                values.get(method, 0) * method_weights.get(method, 0)
                for method in method_weights.keys()
            )
            
            comprehensive_value = weighted_sum / total_weight
            
            # 计算推荐区间
            valid_values = [v for v in values.values() if v > 0]
            if valid_values:
                conservative = min(valid_values) * 0.85
                optimistic = max(valid_values) * 1.15
            else:
                conservative = optimistic = 0
            
            results["recommended_range"] = {
                "conservative": {"value": conservative, "unit": "万元"},
                "neutral": {"value": comprehensive_value, "unit": "万元"},
                "optimistic": {"value": optimistic, "unit": "万元"}
            }
            results["comprehensive_value"] = {"value": comprehensive_value, "unit": "万元"}
            results["method_weights"] = method_weights
        
        return results
    
    def generate_report(self, valuation_result: Dict) -> str:
        """生成估值报告"""
        report_lines = [
            "=" * 60,
            "知识产权估值报告",
            "=" * 60,
            f"估值时间: {valuation_result.get('valuation_time', 'N/A')}",
            f"技术领域: {valuation_result.get('tech_domain', 'N/A')}",
            "",
            "-" * 60,
            "五维度评分",
            "-" * 60
        ]
        
        for dim, data in valuation_result.get("dimension_scores", {}).items():
            report_lines.append(
                f"  {dim}: {data['score']:.1f}/10 "
                f"(权重{data['weight']*100:.0f}%, "
                f"加权{data['weighted_score']:.2f})"
            )
        
        report_lines.append(
            f"\n综合维度得分: {valuation_result.get('comprehensive_dimension_score', 0):.2f}/10"
        )
        
        if "methods" in valuation_result:
            report_lines.append("")
            report_lines.append("-" * 60)
            report_lines.append("各方法估值结果")
            report_lines.append("-" * 60)
            
            for method, result in valuation_result["methods"].items():
                if method == "成本法":
                    report_lines.append(
                        f"  {method}: {result['result']['value']:.2f}万元"
                    )
                elif method == "收益法":
                    for scenario, data in result["scenarios"].items():
                        report_lines.append(
                            f"    {scenario}: {data['result']['value']:.2f}万元"
                        )
                elif method == "市场法":
                    report_lines.append(
                        f"  {method}: {result['result']['value']:.2f}万元"
                    )
        
        if "recommended_range" in valuation_result:
            rr = valuation_result["recommended_range"]
            report_lines.append("")
            report_lines.append("-" * 60)
            report_lines.append("推荐估值区间")
            report_lines.append("-" * 60)
            report_lines.append(f"  保守估计: {rr['conservative']['value']:.2f}万元")
            report_lines.append(f"  中性估计: {rr['neutral']['value']:.2f}万元")
            report_lines.append(f"  乐观估计: {rr['optimistic']['value']:.2f}万元")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


def main():
    """主函数 - 示例使用"""
    calculator = IPValuationCalculator()
    
    # 示例：某人工智能专利估值
    print("\n" + "=" * 60)
    print("示例：人工智能专利估值")
    print("=" * 60)
    
    # 五维度得分
    dimension_scores = {
        "创新性": 8.5,
        "实用性": 7.0,
        "独占性": 7.5,
        "战略赛道": 8.0,
        "未来市场": 8.0
    }
    
    # 年收益预测（万元）
    annual_revenue = {
        "保守": 80,
        "中性": 120,
        "乐观": 180
    }
    
    # 综合估值
    result = calculator.comprehensive_valuation(
        rd_cost=300,  # 研发成本300万
        annual_revenue=annual_revenue,
        comparable_price=400,  # 可比交易价格400万
        tech_domain="IT",
        dimension_scores=dimension_scores
    )
    
    # 生成报告
    report = calculator.generate_report(result)
    print(report)
    
    # 输出权重来源
    print("\n" + "=" * 60)
    print("权重来源标注")
    print("=" * 60)
    
    for key, source in calculator.WEIGHT_SOURCES.items():
        print(f"\n{key}:")
        print(f"  权重: {source.weight*100:.0f}%")
        print(f"  来源类型: {source.source_type}")
        print(f"  来源依据: {source.source_detail}")


if __name__ == "__main__":
    main()
