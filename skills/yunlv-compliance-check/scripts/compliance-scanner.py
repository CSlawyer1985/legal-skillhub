#!/usr/bin/env python3
"""
云旅合规检查器 - Yunlv Compliance Scanner
进出口合规风险扫描、国家风险评级、合规报告生成

命令:
  scan          - 进出口合规风险扫描
  country-risk  - 国家风险评级
  report        - 合规报告生成
"""

import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ============ 数据模型 ============

@dataclass
class ComplianceRisk:
    """合规风险"""
    dimension: str
    level: str        # 低/中/高/极高
    score: float      # 0-100
    details: List[str]
    recommendations: List[str]

@dataclass
class CountryRisk:
    """国家风险"""
    country: str
    risk_level: str   # A/B/C/D/E
    score: float
    payment_risk: str
    logistics_risk: str
    political_risk: str

# ============ 内置数据 - 20个国家基础合规数据 ============

COUNTRY_DATA = {
    "美国": {
        "risk_level": "B",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "中",
        "certifications": ["FCC", "UL", "FDA", "CPSC"],
        "tariff_rate": "5-25%",
        "sanctions": "部分实体清单",
        "embargo": False,
        "restrictions": ["部分高科技产品出口管制", "知识产权保护严格"],
        "notes": "最大的出口市场，关税较高，需注意301条款"
    },
    "英国": {
        "risk_level": "B",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["UKCA", "CE"],
        "tariff_rate": "0-12%",
        "sanctions": "部分制裁",
        "embargo": False,
        "restrictions": ["UKCA认证要求", "VAT合规"],
        "notes": "脱欧后需单独认证，注意VAT申报"
    },
    "德国": {
        "risk_level": "A",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["CE", "GS", "TUV"],
        "tariff_rate": "0-12%",
        "sanctions": "遵守欧盟制裁",
        "embargo": False,
        "restrictions": ["环保法规严格", "产品安全标准高"],
        "notes": "欧洲核心市场，品质要求高"
    },
    "法国": {
        "risk_level": "A",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["CE", "NF"],
        "tariff_rate": "0-12%",
        "sanctions": "遵守欧盟制裁",
        "embargo": False,
        "restrictions": ["法语标注要求", "环保法规"],
        "notes": "需注意法语标签要求"
    },
    "日本": {
        "risk_level": "A",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["PSE", "JIS", "JQA"],
        "tariff_rate": "0-15%",
        "sanctions": "严格出口管制",
        "embargo": False,
        "restrictions": ["PSE认证", "日语标签", "Packaging Recycling"],
        "notes": "对品质要求极高，环保意识强"
    },
    "韩国": {
        "risk_level": "A",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "中",
        "certifications": ["KC"],
        "tariff_rate": "0-13%",
        "sanctions": "部分限制",
        "embargo": False,
        "restrictions": ["KC认证", "韩语标签"],
        "notes": "KC认证是必须的"
    },
    "澳大利亚": {
        "risk_level": "A",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["RCM", "ACMA"],
        "tariff_rate": "0-10%",
        "sanctions": "独立制裁",
        "embargo": False,
        "restrictions": ["RCM认证", "GST合规"],
        "notes": "距离远但市场规范"
    },
    "加拿大": {
        "risk_level": "A",
        "payment_risk": "低",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["CSA", "IC"],
        "tariff_rate": "0-25%",
        "sanctions": "配合美国",
        "embargo": False,
        "restrictions": ["英语法语双语", "CSA认证"],
        "notes": "北美市场一体性，关税随USMCA"
    },
    "巴西": {
        "risk_level": "C",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "中",
        "certifications": ["INMETRO", "ANATEL"],
        "tariff_rate": "20-60%",
        "sanctions": "独立政策",
        "embargo": False,
        "restrictions": ["INMETRO认证", "高关税", "复杂清关"],
        "notes": "市场大但准入门槛高，建议找本地代理"
    },
    "印度": {
        "risk_level": "C",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "中",
        "certifications": ["BIS", "WPC"],
        "tariff_rate": "10-50%",
        "sanctions": "独立政策",
        "embargo": False,
        "restrictions": ["BIS认证", "高关税", "本地化要求"],
        "notes": "潜力大但风险高，建议预付或LC"
    },
    "俄罗斯": {
        "risk_level": "D",
        "payment_risk": "高",
        "logistics_risk": "高",
        "political_risk": "极高",
        "certifications": ["EAC"],
        "tariff_rate": "变化大",
        "sanctions": "广泛制裁",
        "embargo": False,
        "restrictions": ["EAC认证", "制裁风险", "支付困难"],
        "notes": "制裁风险高，建议评估后决定"
    },
    "越南": {
        "risk_level": "B",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "低",
        "certifications": ["CR", "ICT"],
        "tariff_rate": "0-30%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["CR认证", "本地检验"],
        "notes": "制造业转移热门，RCEP优惠"
    },
    "印度尼西亚": {
        "risk_level": "C",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "中",
        "certifications": ["SNI"],
        "tariff_rate": "5-40%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["SNI认证强制", "清关较慢"],
        "notes": "人口大国，市场潜力大"
    },
    "墨西哥": {
        "risk_level": "B",
        "payment_risk": "中",
        "logistics_risk": "低",
        "political_risk": "中",
        "certifications": ["NOM"],
        "tariff_rate": "0-20%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["NOM认证", "西班牙语标签"],
        "notes": "USMCA优惠，需NOM认证"
    },
    "沙特阿拉伯": {
        "risk_level": "B",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "中",
        "certifications": ["SASO"],
        "tariff_rate": "5-15%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["SASO认证", "伊斯兰文化要求"],
        "notes": "GCC市场核心，注意文化合规"
    },
    "阿联酋": {
        "risk_level": "B",
        "payment_risk": "中",
        "logistics_risk": "低",
        "political_risk": "低",
        "certifications": ["ESMA"],
        "tariff_rate": "5%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["ESMA认证", "自由区政策"],
        "notes": "中东贸易枢纽，迪拜自由度高"
    },
    "土耳其": {
        "risk_level": "C",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "中",
        "certifications": ["CE", "TSE"],
        "tariff_rate": "0-25%",
        "sanctions": "部分制裁",
        "embargo": False,
        "restrictions": ["CE/TSE双认证", "里拉波动"],
        "notes": "地理位置好，但汇率风险大"
    },
    "南非": {
        "risk_level": "C",
        "payment_risk": "中",
        "logistics_risk": "中",
        "political_risk": "中",
        "certifications": ["SABS"],
        "tariff_rate": "0-30%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["SABS认证", "港口效率低"],
        "notes": "非洲最大市场，基础设施待改善"
    },
    "尼日利亚": {
        "risk_level": "D",
        "payment_risk": "高",
        "logistics_risk": "高",
        "political_risk": "高",
        "certifications": ["SON"],
        "tariff_rate": "10-50%",
        "sanctions": "部分",
        "embargo": False,
        "restrictions": ["SONCAP认证", "外汇管制"],
        "notes": "市场大但风险高，建议预付"
    },
    "埃及": {
        "risk_level": "D",
        "payment_risk": "高",
        "logistics_risk": "高",
        "political_risk": "高",
        "certifications": ["EOS"],
        "tariff_rate": "5-60%",
        "sanctions": "无",
        "embargo": False,
        "restrictions": ["EOS认证", "外汇管制", "清关复杂"],
        "notes": "清关难，外汇获取不易"
    }
}

# ============ 核心函数 ============

def scan_compliance_risk(
    product: str,
    country: str,
    hs_code: str = None
) -> Dict:
    """进出口合规风险扫描"""
    
    # 风险评估
    risks = []
    total_risk_score = 0
    
    # 1. 认证要求风险
    cert_risk = _evaluate_certification_risk(product, country)
    risks.append(cert_risk)
    total_risk_score += cert_risk["score"] * 0.30
    
    # 2. 关税风险
    tariff_risk = _evaluate_tariff_risk(product, country)
    risks.append(tariff_risk)
    total_risk_score += tariff_risk["score"] * 0.25
    
    # 3. 制裁风险
    sanctions_risk = _evaluate_sanctions_risk(country)
    risks.append(sanctions_risk)
    total_risk_score += sanctions_risk["score"] * 0.25
    
    # 4. 禁运风险
    embargo_risk = _evaluate_embargo_risk(country)
    risks.append(embargo_risk)
    total_risk_score += embargo_risk["score"] * 0.20
    
    # 综合评估
    overall_level = _get_risk_level(total_risk_score)
    
    return {
        "product": product,
        "country": country,
        "hs_code": hs_code,
        "overall_risk_level": overall_level,
        "overall_risk_score": round(total_risk_score, 1),
        "risk_dimensions": risks,
        "summary": _generate_risk_summary(risks, total_risk_score),
        "recommendations": _generate_compliance_recommendations(risks)
    }

def _evaluate_certification_risk(product: str, country: str) -> Dict:
    """评估认证要求风险"""
    country_info = COUNTRY_DATA.get(country, {})
    required_certs = country_info.get("certifications", [])
    
    # 基于产品类型估算认证复杂度
    high_cert_products = ["电子", "电器", "玩具", "食品", "医疗"]
    medium_cert_products = ["机械", "建材", "化工"]
    
    cert_complexity = "低"
    for kw in high_cert_products:
        if kw in product:
            cert_complexity = "高"
            break
    for kw in medium_cert_products:
        if kw in product:
            cert_complexity = "中"
            break
    
    risk_map = {"高": 80, "中": 50, "低": 25}
    score = risk_map.get(cert_complexity, 50) + len(required_certs) * 5
    
    return {
        "dimension": "认证要求",
        "level": cert_complexity,
        "score": min(100, score),
        "details": [
            f"目标市场: {country}",
            f"可能需要的认证: {', '.join(required_certs) if required_certs else '基础认证'}",
            f"认证复杂度: {cert_complexity}"
        ],
        "recommendations": _get_cert_recommendations(cert_complexity, required_certs)
    }

def _get_cert_recommendations(complexity: str, certs: List[str]) -> List[str]:
    """获取认证建议"""
    recommendations = []
    if complexity == "高":
        recommendations.append("建议提前6-12个月准备认证")
        recommendations.append("考虑使用认证机构预审服务")
    elif complexity == "中":
        recommendations.append("建议提前3-6个月准备认证")
        recommendations.append("可考虑使用本地代理协助认证")
    else:
        recommendations.append("认证要求相对简单")
        recommendations.append("准备基础合规文件即可")
    
    if certs:
        recommendations.append(f"重点关注: {certs[0]}认证")
    
    return recommendations

def _evaluate_tariff_risk(product: str, country: str) -> Dict:
    """评估关税风险"""
    country_info = COUNTRY_DATA.get(country, {})
    tariff_rate = country_info.get("tariff_rate", "未知")
    
    # 估算关税水平
    if "20%" in str(tariff_rate) or "25%" in str(tariff_rate) or "30%" in str(tariff_rate):
        level = "高"
        score = 75
    elif "10%" in str(tariff_rate) or "15%" in str(tariff_rate):
        level = "中"
        score = 50
    elif "0%" in str(tariff_rate):
        level = "低"
        score = 25
    else:
        level = "中"
        score = 50
    
    return {
        "dimension": "关税",
        "level": level,
        "score": score,
        "details": [
            f"目标市场: {country}",
            f"参考关税税率: {tariff_rate}",
            f"关税水平: {level}"
        ],
        "recommendations": _get_tariff_recommendations(level, country)
    }

def _get_tariff_recommendations(level: str, country: str) -> List[str]:
    """获取关税建议"""
    recommendations = []
    if level == "高":
        recommendations.append("高关税市场建议寻找贸易协定优惠")
        recommendations.append("考虑在第三国组装以降低关税")
    elif level == "中":
        recommendations.append("关注RCEP等区域贸易协定")
        recommendations.append("合理利用保税仓储降低成本")
    else:
        recommendations.append("关税优势明显，可积极拓展")
    
    return recommendations

def _evaluate_sanctions_risk(country: str) -> Dict:
    """评估制裁风险"""
    country_info = COUNTRY_DATA.get(country, {})
    sanctions = country_info.get("sanctions", "无")
    
    if "广泛" in sanctions or "严格" in sanctions:
        level = "极高"
        score = 100
    elif "部分" in sanctions or "独立" in sanctions:
        level = "中"
        score = 50
    else:
        level = "低"
        score = 20
    
    return {
        "dimension": "制裁",
        "level": level,
        "score": score,
        "details": [
            f"目标市场: {country}",
            f"制裁情况: {sanctions}"
        ],
        "recommendations": _get_sanctions_recommendations(level)
    }

def _get_sanctions_recommendations(level: str) -> List[str]:
    """获取制裁建议"""
    if level == "极高":
        return [
            "建议暂缓该市场业务",
            "如确需开展，建议进行专业法律评估",
            "考虑通过第三方合规渠道"
        ]
    elif level == "中":
        return [
            "建议定期关注制裁名单更新",
            "保持与专业合规机构的咨询",
            "确保交易对手不在制裁名单"
        ]
    else:
        return ["制裁风险较低，保持常规合规即可"]

def _evaluate_embargo_risk(country: str) -> Dict:
    """评估禁运风险"""
    country_info = COUNTRY_DATA.get(country, {})
    is_embargo = country_info.get("embargo", False)
    
    if is_embargo:
        level = "极高"
        score = 100
    else:
        level = "低"
        score = 10
    
    return {
        "dimension": "禁运",
        "level": level,
        "score": score,
        "details": [
            f"目标市场: {country}",
            f"禁运状态: {'是' if is_embargo else '否'}"
        ],
        "recommendations": ["该市场可正常开展贸易业务"] if not is_embargo else ["建议避免该市场业务"]
    }

def _get_risk_level(score: float) -> str:
    """获取风险等级"""
    if score <= 25:
        return "极低"
    elif score <= 45:
        return "低"
    elif score <= 60:
        return "中"
    elif score <= 80:
        return "高"
    else:
        return "极高"

def _generate_risk_summary(risks: List[Dict], total_score: float) -> str:
    """生成风险摘要"""
    high_risks = [r for r in risks if r["level"] in ["高", "极高"]]
    
    if not high_risks:
        return "综合风险较低，可以考虑开展业务"
    elif len(high_risks) == 1:
        return f"主要风险在于{high_risks[0]['dimension']}，需重点关注"
    else:
        risk_dims = "、".join([r["dimension"] for r in high_risks])
        return f"多项风险需关注：{risk_dims}"

def _generate_compliance_recommendations(risks: List[Dict]) -> List[str]:
    """生成合规建议"""
    recommendations = []
    
    for risk in risks:
        if risk["recommendations"]:
            recommendations.extend(risk["recommendations"][:2])
    
    if not recommendations:
        recommendations.append("建议进行正式合规评估后再开展业务")
    
    return list(dict.fromkeys(recommendations))[:5]  # 去重

def evaluate_country_risk(country: str) -> Dict:
    """国家风险评级"""
    
    if country not in COUNTRY_DATA:
        return {
            "error": f"未收录国家: {country}",
            "available_countries": list(COUNTRY_DATA.keys())
        }
    
    data = COUNTRY_DATA[country]
    
    # 计算综合风险分
    risk_scores = {
        "A": 20,
        "B": 45,
        "C": 65,
        "D": 85,
        "E": 100
    }
    
    payment_scores = {"低": 20, "中": 50, "高": 85}
    logistic_scores = {"低": 20, "中": 50, "高": 85}
    political_scores = {"低": 20, "中": 50, "高": 85, "极高": 100}
    
    total_score = (
        payment_scores.get(data["payment_risk"], 50) * 0.35 +
        logistic_scores.get(data["logistics_risk"], 50) * 0.25 +
        political_scores.get(data["political_risk"], 50) * 0.40
    )
    
    return {
        "country": country,
        "risk_level": data["risk_level"],
        "total_risk_score": round(total_score, 1),
        "risk_breakdown": {
            "payment_risk": data["payment_risk"],
            "logistics_risk": data["logistics_risk"],
            "political_risk": data["political_risk"]
        },
        "market_entry": {
            "tariff_rate": data["tariff_rate"],
            "required_certifications": data["certifications"],
            "sanctions_status": data["sanctions"],
            "embargo": data["embargo"],
            "special_restrictions": data.get("restrictions", [])
        },
        "notes": data["notes"],
        "recommendations": _get_country_recommendations(data)
    }

def _get_country_recommendations(data: Dict) -> List[str]:
    """获取国家建议"""
    recommendations = []
    risk = data["risk_level"]
    
    if risk == "A":
        recommendations.append("市场风险低，建议积极拓展")
        recommendations.append("注重产品品质和服务质量")
    elif risk == "B":
        recommendations.append("市场风险可控，可以开展业务")
        recommendations.append("建议选择安全付款方式")
    elif risk == "C":
        recommendations.append("市场存在一定风险，建议谨慎")
        recommendations.append("建议使用信用证或预付方式")
        recommendations.append("考虑投保出口信用保险")
    else:
        recommendations.append("市场风险较高，建议充分评估")
        recommendations.append("强烈建议使用预付或信用证")
        recommendations.append("必须投保出口信用保险")
    
    if data.get("required_certifications"):
        recommendations.append(f"注意获取{data['required_certifications'][0]}认证")
    
    return recommendations

def generate_compliance_report(
    products: List[str],
    countries: List[str]
) -> Dict:
    """生成合规报告"""
    
    scan_results = []
    
    for product in products:
        for country in countries:
            result = scan_compliance_risk(product, country)
            scan_results.append({
                "product": product,
                "country": country,
                "risk_level": result["overall_risk_level"],
                "risk_score": result["overall_risk_score"]
            })
    
    # 按风险排序
    scan_results.sort(key=lambda x: x["risk_score"], reverse=True)
    
    # 统计
    risk_distribution = {"极低": 0, "低": 0, "中": 0, "高": 0, "极高": 0}
    for r in scan_results:
        risk_distribution[r["risk_level"]] += 1
    
    return {
        "summary": {
            "total_combinations": len(scan_results),
            "risk_distribution": risk_distribution,
            "lowest_risk": scan_results[-1] if scan_results else None,
            "highest_risk": scan_results[0] if scan_results else None
        },
        "detailed_results": scan_results,
        "recommendations": _generate_report_recommendations(scan_results)
    }

def _generate_report_recommendations(results: List[Dict]) -> List[str]:
    """生成报告建议"""
    recommendations = []
    
    high_risk = [r for r in results if r["risk_level"] in ["高", "极高"]]
    low_risk = [r for r in results if r["risk_level"] in ["极低", "低"]]
    
    if high_risk:
        recommendations.append(f"建议暂缓{len(high_risk)}个高风险组合")
    
    if low_risk:
        recommendations.append(f"优先拓展{len(low_risk)}个低风险组合")
    
    recommendations.append("建议先小批量试单测试高风险市场")
    recommendations.append("所有市场均建议进行最终合规确认")
    
    return recommendations

# ============ CLI 入口 ============

def main():
    parser = argparse.ArgumentParser(
        description="云旅合规检查器 - 进出口合规风险评估工具"
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # scan命令
    p_scan = subparsers.add_parser('scan', help='进出口合规风险扫描')
    p_scan.add_argument('--product', required=True, help='产品名称')
    p_scan.add_argument('--country', required=True, help='目标国家')
    p_scan.add_argument('--hs-code', help='HS编码')
    
    # country-risk命令
    p_country = subparsers.add_parser('country-risk', help='国家风险评级')
    p_country.add_argument('--country', required=True, help='国家名称')
    
    # report命令
    p_report = subparsers.add_parser('report', help='合规报告生成')
    p_report.add_argument('--products', required=True, help='产品列表(逗号分隔)')
    p_report.add_argument('--countries', required=True, help='国家列表(逗号分隔)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'scan':
        result = scan_compliance_risk(
            product=args.product,
            country=args.country,
            hs_code=args.hs_code
        )
    elif args.command == 'country-risk':
        result = evaluate_country_risk(args.country)
    elif args.command == 'report':
        products = args.products.split(',')
        countries = args.countries.split(',')
        result = generate_compliance_report(products, countries)
    else:
        print(f"未知命令: {args.command}")
        return
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
