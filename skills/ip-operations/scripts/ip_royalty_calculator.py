#!/usr/bin/env python3
"""
IP许可费率计算器
IP Royalty Calculator

功能：基于25%法则/增量法/市场比较法计算知识产权许可费率
来源：LES国际许可从业者协会 + 国知局统计
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RoyaltyRateResult:
    """许可费率计算结果"""
    method: str
    formula: str
    parameters: Dict
    rate: float
    description: str
    source: str


class IPRoyaltyCalculator:
    """知识产权许可费率计算器"""
    
    # 25%法则基础参数
    PROFIT_SHARING_RATE = 0.25  # 利润分成率（经验值）
    
    # 行业基准费率（来源：LES协会统计 + 国知局报告）
    INDUSTRY_BASE_RATES = {
        "电子/半导体": {
            "芯片设计": (0.02, 0.10, 0.05),
            "半导体制造": (0.03, 0.12, 0.06),
            "电子元器件": (0.01, 0.08, 0.025),
        },
        "软件/IT": {
            "基础软件": (0.05, 0.20, 0.12),
            "应用软件": (0.08, 0.25, 0.15),
            "算法/AI": (0.10, 0.30, 0.18),
        },
        "医药": {
            "化学药品": (0.05, 0.15, 0.08),
            "生物制药": (0.08, 0.25, 0.15),
            "医疗器械": (0.03, 0.12, 0.06),
        },
        "机械/制造": {
            "通用设备": (0.01, 0.06, 0.03),
            "专用设备": (0.02, 0.08, 0.04),
            "汽车制造": (0.02, 0.08, 0.04),
        },
        "化工": {
            "催化剂": (0.03, 0.10, 0.05),
            "材料配方": (0.02, 0.08, 0.04),
            "精细化工": (0.03, 0.12, 0.06),
        },
        "通信": {
            "通信设备": (0.01, 0.08, 0.03),
            "通信标准必要专利": (0.005, 0.05, 0.01),
            "网络技术": (0.02, 0.10, 0.05),
        },
        "新能源": {
            "电池技术": (0.05, 0.15, 0.08),
            "光伏技术": (0.03, 0.12, 0.06),
            "储能技术": (0.04, 0.15, 0.08),
        },
    }
    
    # 技术贡献率（来源：国知局）
    TECH_CONTRIBUTION_RATES = {
        "制造业": (0.15, 0.30, 0.20),
        "IT": (0.25, 0.40, 0.30),
        "软件": (0.25, 0.40, 0.30),
        "生物医药": (0.30, 0.50, 0.40),
        "电子通信": (0.20, 0.35, 0.25),
        "新能源": (0.25, 0.40, 0.30),
        "化工": (0.20, 0.35, 0.25),
    }
    
    # 许可模式调整系数
    LICENSE_TYPE_ADJUSTMENTS = {
        "独占许可": 1.5,    # 排他性强，价值高
        "排他许可": 1.25,   # 双方共享
        "普通许可": 0.75,   # 多方共享
        "分许可权": 0.50,   # 需原始许可方同意
    }
    
    def __init__(self):
        self.calculation_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    def method_25_percent_rule(
        self,
        tech_contribution_rate: float,
        product_profit_rate: float
    ) -> RoyaltyRateResult:
        """
        25%法则计算许可费率
        
        公式: 许可费率 = 25% × 技术贡献率 / 产品利润率
        
        参数:
            tech_contribution_rate: 技术贡献率 (0-1)
            product_profit_rate: 产品利润率 (0-1)
        
        返回:
            许可费率计算结果
        """
        rate = self.PROFIT_SHARING_RATE * tech_contribution_rate / product_profit_rate
        
        return RoyaltyRateResult(
            method="25%法则",
            formula="许可费率 = 利润分成率 × 技术贡献率 / 产品利润率",
            parameters={
                "利润分成率": {
                    "value": self.PROFIT_SHARING_RATE,
                    "description": "经验值，许可方应获得的利润比例",
                    "source": "行业惯例"
                },
                "技术贡献率": {
                    "value": tech_contribution_rate,
                    "description": "技术对产品利润的贡献比例",
                    "source": "国知局行业基准"
                },
                "产品利润率": {
                    "value": product_profit_rate,
                    "description": "产品的销售利润率",
                    "source": "企业财务数据"
                }
            },
            rate=min(rate, 0.30),  # 上限30%
            description="基于25%法则计算的许可费率",
            source="知识产权领域经典经验法则"
        )
    
    def method_incremental(
        self,
        revenue_with_tech: float,
        revenue_without_tech: float,
        tech_contribution_coefficient: float = 0.35
    ) -> RoyaltyRateResult:
        """
        增量法计算许可费
        
        公式: 许可费 = 增量收益 × 技术贡献系数
        增量收益 = 使用技术后收益 - 不使用技术收益
        
        参数:
            revenue_with_tech: 使用技术后的年收益（万元）
            revenue_without_tech: 不使用技术的基准年收益（万元）
            tech_contribution_coefficient: 技术贡献系数 (0-1)，默认35%
        
        返回:
            年许可费计算结果
        """
        incremental_revenue = revenue_with_tech - revenue_without_tech
        annual_royalty = incremental_revenue * tech_contribution_coefficient
        
        # 计算等效许可费率（假设产品利润率25%）
        implied_rate = annual_royalty / revenue_with_tech if revenue_with_tech > 0 else 0
        
        return RoyaltyRateResult(
            method="增量法",
            formula="许可费 = (使用技术后收益 - 不使用技术收益) × 技术贡献系数",
            parameters={
                "使用技术后收益": {
                    "value": revenue_with_tech,
                    "unit": "万元/年",
                    "description": "采用专利技术后的年收益"
                },
                "不使用技术收益": {
                    "value": revenue_without_tech,
                    "unit": "万元/年",
                    "description": "不采用技术的基准年收益"
                },
                "增量收益": {
                    "value": incremental_revenue,
                    "unit": "万元/年",
                    "description": "技术带来的收益增量"
                },
                "技术贡献系数": {
                    "value": tech_contribution_coefficient,
                    "description": "技术对增量的贡献比例",
                    "source": "国知局标准 25%-50%"
                }
            },
            rate=implied_rate,
            description=f"年许可费: {annual_royalty:.2f}万元",
            source="国知局《专利价值分析指标体系操作手册》"
        )
    
    def method_market_comparison(
        self,
        industry: str,
        sub_industry: Optional[str] = None,
        license_type: str = "普通许可",
        adjustment_factors: Optional[Dict[str, float]] = None
    ) -> RoyaltyRateResult:
        """
        市场比较法计算许可费率
        
        公式: 许可费率 = 可比交易费率 × 调整系数
        
        参数:
            industry: 行业名称
            sub_industry: 子行业名称
            license_type: 许可类型
            adjustment_factors: 调整因素 {
                "创新性": 调整值(-0.2~0.2),
                "实用性": 调整值,
                "独占性": 调整值,
                "市场": 调整值,
                "合同条款": 调整值
            }
        
        返回:
            许可费率计算结果
        """
        # 获取行业基准费率
        if sub_industry and industry in self.INDUSTRY_BASE_RATES:
            rates = self.INDUSTRY_BASE_RATES[industry].get(
                sub_industry, 
                (0.05, 0.10, 0.07)
            )
        elif industry in self.INDUSTRY_BASE_RATES:
            rates = (0.03, 0.12, 0.07)
        else:
            rates = (0.03, 0.15, 0.08)  # 默认
        
        base_rate = rates[2]  # 中位数作为基准
        
        # 许可类型调整
        type_adjustment = self.LICENSE_TYPE_ADJUSTMENTS.get(license_type, 1.0)
        
        # 五维度调整
        if adjustment_factors is None:
            adjustment_factors = {
                "创新性": 0,
                "实用性": 0,
                "独占性": 0,
                "市场": 0,
                "合同条款": 0
            }
        
        dimension_adjustment = sum(adjustment_factors.values()) * 0.05  # 每维度±5%
        
        # 最终费率
        rate = base_rate * type_adjustment * (1 + dimension_adjustment)
        rate = max(0.001, min(rate, 0.50))  # 限制在0.1%-50%
        
        return RoyaltyRateResult(
            method="市场比较法",
            formula="许可费率 = 行业基准费率 × 许可类型调整 × 维度调整系数",
            parameters={
                "行业基准费率": {
                    "value": base_rate,
                    "description": f"{industry}/{sub_industry or '通用'}",
                    "source": "LES协会统计 + 国知局报告"
                },
                "许可类型调整": {
                    "value": type_adjustment,
                    "description": license_type,
                    "detail": {
                        "独占许可": "×1.5",
                        "排他许可": "×1.25",
                        "普通许可": "×0.75",
                        "分许可权": "×0.5"
                    }
                },
                "维度调整": {
                    "value": 1 + dimension_adjustment,
                    "factors": adjustment_factors,
                    "description": "五维度调整（创新性/实用性/独占性/市场/合同条款）"
                }
            },
            rate=rate,
            description=f"基于{industry}行业市场数据计算",
            source="LES国际许可从业者协会 + 中国技术交易所数据"
        )
    
    def calculate_comprehensive(
        self,
        industry: str,
        sub_industry: Optional[str] = None,
        sales: Optional[float] = None,
        profit: Optional[float] = None,
        tech_contribution_rate: Optional[float] = None,
        license_type: str = "普通许可",
        revenue_with_tech: Optional[float] = None,
        revenue_without_tech: Optional[float] = None
    ) -> Dict:
        """
        综合计算许可费率
        
        参数:
            industry: 行业
            sub_industry: 子行业
            sales: 年销售额（万元）
            profit: 年利润（万元）
            tech_contribution_rate: 技术贡献率
            license_type: 许可类型
            revenue_with_tech: 使用技术后收益（万元）
            revenue_without_tech: 不使用技术收益（万元）
        
        返回:
            综合计算结果
        """
        results = {
            "calculation_time": self.calculation_time,
            "industry": industry,
            "sub_industry": sub_industry,
            "methods": {},
            "recommended_range": {}
        }
        
        # 25%法则
        if profit and sales and tech_contribution_rate:
            product_profit_rate = profit / sales if sales > 0 else 0.20
            rule_result = self.method_25_percent_rule(tech_contribution_rate, product_profit_rate)
            results["methods"]["25%法则"] = {
                "rate": rule_result.rate,
                "formula": rule_result.formula,
                "parameters": rule_result.parameters,
                "description": rule_result.description,
                "annual_royalty": sales * rule_result.rate if sales else 0
            }
        
        # 增量法
        if revenue_with_tech and revenue_without_tech:
            incremental_result = self.method_incremental(revenue_with_tech, revenue_without_tech)
            results["methods"]["增量法"] = {
                "rate": incremental_result.rate,
                "formula": incremental_result.formula,
                "parameters": incremental_result.parameters,
                "description": incremental_result.description,
                "annual_royalty": incremental_result.parameters["技术贡献系数"]["value"] * \
                                (revenue_with_tech - revenue_without_tech)
            }
        
        # 市场比较法
        market_result = self.method_market_comparison(industry, sub_industry, license_type)
        results["methods"]["市场比较法"] = {
            "rate": market_result.rate,
            "formula": market_result.formula,
            "parameters": market_result.parameters,
            "description": market_result.description,
            "annual_royalty": sales * market_result.rate if sales else 0
        }
        
        # 推荐区间
        rates = [m["rate"] for m in results["methods"].values() if m["rate"] > 0]
        if rates:
            results["recommended_range"] = {
                "conservative": min(rates) * 0.9,
                "neutral": sum(rates) / len(rates),
                "optimistic": max(rates) * 1.1
            }
            
            # 年许可费估算
            if sales:
                results["recommended_annual_royalty"] = {
                    "conservative": sales * results["recommended_range"]["conservative"],
                    "neutral": sales * results["recommended_range"]["neutral"],
                    "optimistic": sales * results["recommended_range"]["optimistic"]
                }
        
        return results
    
    def generate_report(self, calc_result: Dict) -> str:
        """生成许可费率计算报告"""
        lines = [
            "=" * 70,
            "知识产权许可费率计算报告",
            "=" * 70,
            f"计算时间: {calc_result.get('calculation_time', 'N/A')}",
            f"行业: {calc_result.get('industry', 'N/A')}",
            f"子行业: {calc_result.get('sub_industry', 'N/A')}",
            "",
        ]
        
        lines.append("-" * 70)
        lines.append("各方法计算结果")
        lines.append("-" * 70)
        
        for method, data in calc_result.get("methods", {}).items():
            rate = data["rate"]
            annual = data.get("annual_royalty", 0)
            
            lines.append(f"\n【{method}】")
            lines.append(f"  许可费率: {rate*100:.2f}%")
            if annual > 0:
                lines.append(f"  年许可费估算: {annual:.2f}万元")
            lines.append(f"  公式: {data['formula']}")
        
        if "recommended_range" in calc_result:
            rr = calc_result["recommended_range"]
            lines.append("")
            lines.append("-" * 70)
            lines.append("推荐费率区间")
            lines.append("-" * 70)
            lines.append(f"  保守: {rr['conservative']*100:.2f}%")
            lines.append(f"  中性: {rr['neutral']*100:.2f}%")
            lines.append(f"  乐观: {rr['optimistic']*100:.2f}%")
            
            if "recommended_annual_royalty" in calc_result:
                rar = calc_result["recommended_annual_royalty"]
                lines.append("")
                lines.append("  年许可费估算:")
                lines.append(f"    保守: {rar['conservative']:.2f}万元")
                lines.append(f"    中性: {rar['neutral']:.2f}万元")
                lines.append(f"    乐观: {rar['optimistic']:.2f}万元")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def main():
    """主函数 - 示例使用"""
    calculator = IPRoyaltyCalculator()
    
    print("\n" + "=" * 70)
    print("示例：某AI软件专利许可费率计算")
    print("=" * 70)
    
    # 综合计算
    result = calculator.calculate_comprehensive(
        industry="软件/IT",
        sub_industry="算法/AI",
        sales=1000,  # 年销售额1000万
        profit=200,  # 年利润200万
        tech_contribution_rate=0.30,  # 技术贡献率30%
        license_type="普通许可",
        revenue_with_tech=300,  # 使用技术后收益
        revenue_without_tech=150   # 不使用技术收益
    )
    
    # 生成报告
    report = calculator.generate_report(result)
    print(report)
    
    # 输出行业基准费率
    print("\n" + "=" * 70)
    print("行业基准费率参考")
    print("=" * 70)
    
    for industry, sub_industries in calculator.INDUSTRY_BASE_RATES.items():
        print(f"\n【{industry}】")
        for sub, rates in sub_industries.items():
            print(f"  {sub}: {rates[0]*100:.1f}% - {rates[1]*100:.1f}% (典型: {rates[2]*100:.1f}%)")


if __name__ == "__main__":
    main()
