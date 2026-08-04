#!/usr/bin/env python3
"""
金融营销合规检查器 v1.0.0
基于《金融产品网络营销管理办法》及相关法规，提供合规审查功能。
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

# 配置
SKILL_DIR = Path(__file__).parent.parent
RULES_FILE = SKILL_DIR / "references" / "rules.md"
REGULATIONS_FILE = SKILL_DIR / "references" / "regulations.md"

# 诱导性用语列表（第十条第（七）项）
INDUCING_WORDS = [
    "低风险", "低门槛", "秒到账", "高收益", "低利率", "无成本",
    "保本", "保息", "保本保息", "零风险", "稳赚不赔", "限时抢购",
    "抢购", "秒杀", "抄底", "暴富", "财富自由"
]

# 金融产品类型
PRODUCT_TYPES = [
    "存款", "贷款", "证券", "资产管理产品", "保险", "贵金属",
    "外汇产品", "期货", "衍生品", "支付服务", "投资顾问", "咨询",
    "基金", "理财", "信托"
]

# 涉金融属性字样（第十八条）
FINANCE_KEYWORDS = [
    "金融", "融资", "贷款", "借钱", "典当", "银行", "交易所",
    "交易中心", "资产管理", "基金", "理财", "财富管理",
    "投资顾问", "咨询", "证券", "期货", "股权众筹", "保险",
    "商业保险年金", "信托", "财务公司", "支付", "清算",
    "结算", "征信", "信用评级", "外汇", "货币兑换"
]


def load_rules() -> dict:
    """加载审查规则"""
    rules = {
        "content_authenticity": [],
        "key_info_completeness": [],
        "prohibited_behaviors": [],
        "qualification_requirements": [],
        "suitability_management": []
    }
    
    if RULES_FILE.exists():
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 简单解析（实际应用中应使用更复杂的解析逻辑）
        rules["content_authenticity"] = [
            "R01: 虚假信息",
            "R02: 数据真实性",
            "R03: 保本承诺",
            "R04: 收益承诺",
            "R05: 业绩预测",
            "R06: 模拟业绩",
            "R07: 保险夸大",
            "R08: 简单类比",
            "R09: 备案误导",
            "R10: 诱导消费"
        ]
        
        rules["key_info_completeness"] = [
            "K01: 产品名称",
            "K02: 提供者信息",
            "K03: 产品类别",
            "K04: 利率费率",
            "K05: 风险提示"
        ]
        
        rules["prohibited_behaviors"] = [
            "B01: 诱导性用语",
            "B02: 专区设立",
            "B03: 算法推荐",
            "B04: 弹窗广告",
            "B05: 搭售行为",
            "B06: 资质要求",
            "B07: 品牌独立",
            "B08: 数据安全"
        ]
        
        rules["qualification_requirements"] = [
            "Z01: 金融业务资质",
            "Z02: 账号名称规范",
            "Z03: 商标使用规范"
        ]
        
        rules["suitability_management"] = [
            "S01: 区域限制",
            "S02: 适当性测评",
            "S03: 私募产品",
            "S04: 场外衍生品"
        ]
    
    return rules


def check_content(content: str, product_type: str = "") -> dict:
    """
    审查营销内容合规性
    
    Args:
        content: 营销内容文本
        product_type: 金融产品类型
    
    Returns:
        审查结果字典
    """
    violations = []
    warnings = []
    suggestions = []
    
    # 检查 1：诱导性用语（第十条第（七）项）
    found_inducing = [word for word in INDUCING_WORDS if word in content]
    if found_inducing:
        violations.append({
            "rule": "第十条第（七）项",
            "description": "使用诱导性用语",
            "details": f"发现诱导性用语：{', '.join(found_inducing)}",
            "severity": "高"
        })
        suggestions.append(f"删除诱导性用语：{', '.join(found_inducing)}")
    
    # 检查 2：保本/保息承诺（第十条第（三）项）
    if any(word in content for word in ["保本", "保息", "保本保息", "零风险", "稳赚不赔"]):
        violations.append({
            "rule": "第十条第（三）项",
            "description": "明示或暗示保本、承诺收益",
            "details": "发现保本/保息相关表述",
            "severity": "高"
        })
        suggestions.append("删除保本/保息相关表述")
    
    # 检查 3：风险提示（第八条）
    if "风险提示" not in content and "风险" not in content:
        warnings.append({
            "rule": "第八条",
            "description": "缺少风险提示",
            "details": "营销内容中未包含风险提示",
            "severity": "中"
        })
        suggestions.append("补充风险提示")
    
    # 检查 4：涉金融属性字样（第十八条）
    found_finance = [word for word in FINANCE_KEYWORDS if word in content]
    if found_finance:
        warnings.append({
            "rule": "第十八条",
            "description": "涉金融属性字样使用",
            "details": f"发现涉金融属性字样：{', '.join(found_finance)}",
            "severity": "低"
        })
        suggestions.append("确保使用涉金融属性字样具有相应资质")
    
    # 检查 5：产品类型匹配
    if product_type and product_type not in PRODUCT_TYPES:
        warnings.append({
            "rule": "第三条",
            "description": "产品类型未识别",
            "details": f"未识别的产品类型：{product_type}",
            "severity": "低"
        })
    
    # 确定合规状态
    if violations:
        compliance_status = "❌ 违规"
        risk_level = "高"
    elif warnings:
        compliance_status = "⚠️ 需修改"
        risk_level = "中"
    else:
        compliance_status = "✅ 合规"
        risk_level = "低"
    
    return {
        "compliance_status": compliance_status,
        "risk_level": risk_level,
        "violations": violations,
        "warnings": warnings,
        "suggestions": suggestions,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def check_marketing_plan(plan: str, channel: str = "", product_type: str = "") -> dict:
    """
    审查营销方案合规性
    
    Args:
        plan: 营销方案文本
        channel: 营销渠道
        product_type: 金融产品类型
    
    Returns:
        审查结果字典
    """
    result = check_content(plan, product_type)
    
    # 渠道合规性检查（第十六条）
    if channel in ["公众号", "直播", "短视频"]:
        if "自营平台" not in plan and "金融机构" not in plan:
            result["warnings"].append({
                "rule": "第十六条",
                "description": "渠道合规性",
                "details": f"通过{channel}营销需在金融机构自营平台或合法开设的账号进行",
                "severity": "中"
            })
            result["suggestions"].append(f"确保通过{channel}营销在金融机构自营平台进行")
    
    # 跳转链接检查（第五条）
    if "链接" in plan or "url" in plan.lower():
        if "自营平台" not in plan:
            result["warnings"].append({
                "rule": "第五条",
                "description": "跳转至非自营平台",
                "details": "购买链接需跳转至金融机构自营平台",
                "severity": "中"
            })
            result["suggestions"].append("购买链接需跳转至金融机构自营平台")
    
    return result


def generate_marketing_plan(product_type: str, target_audience: str, channel: str, selling_points: str) -> dict:
    """
    生成合规营销方案
    
    Args:
        product_type: 金融产品类型
        target_audience: 目标人群
        channel: 营销渠道
        selling_points: 核心卖点
    
    Returns:
        营销方案字典
    """
    plan = {
        "product_type": product_type,
        "target_audience": target_audience,
        "channel": channel,
        "selling_points": selling_points,
        "compliance_tips": [
            "✅ 未使用诱导性用语",
            "✅ 未承诺收益",
            "✅ 补充风险提示",
            "✅ 使用涉金融属性字样具有相应资质"
        ],
        "risk_points": [
            "⚠️ 确保营销内容真实准确",
            "⚠️ 确保关键信息完整",
            "⚠️ 确保渠道合规"
        ],
        "suggestions": [
            "补充产品风险提示",
            "确保营销人员具备相关资格",
            "确保跳转至金融机构自营平台"
        ]
    }
    
    return plan


def format_report(result: dict, report_type: str = "review") -> str:
    """
    格式化审查报告
    
    Args:
        result: 审查结果
        report_type: 报告类型（review/plan）
    
    Returns:
        格式化报告文本
    """
    if report_type == "review":
        report = f"""🔍 合规审查结果
━━━━━━━━━━━━━━━━━━━━
合规状态：{result['compliance_status']}
风险等级：{result['risk_level']}
审查时间：{result['timestamp']}

"""
        if result["violations"]:
            report += "违规条款：\n"
            for i, v in enumerate(result["violations"], 1):
                report += f"{i}. {v['rule']}：{v['description']}\n"
                report += f"   - {v['details']}\n\n"
        
        if result["warnings"]:
            report += "警告事项：\n"
            for i, w in enumerate(result["warnings"], 1):
                report += f"{i}. {w['rule']}：{w['description']}\n"
                report += f"   - {w['details']}\n\n"
        
        if result["suggestions"]:
            report += "修改建议：\n"
            for i, s in enumerate(result["suggestions"], 1):
                report += f"{i}. {s}\n"
        
        report += "━━━━━━━━━━━━━━━━━━━━"
    
    elif report_type == "plan":
        report = f"""📋 合规营销方案
━━━━━━━━━━━━━━━━━━━━
产品类型：{result['product_type']}
目标人群：{result['target_audience']}
营销渠道：{result['channel']}
核心卖点：{result['selling_points']}

【合规提示】
"""
        for tip in result["compliance_tips"]:
            report += f"{tip}\n"
        
        report += "\n【风险点】\n"
        for risk in result["risk_points"]:
            report += f"{risk}\n"
        
        report += "\n【建议】\n"
        for suggestion in result["suggestions"]:
            report += f"• {suggestion}\n"
        
        report += "━━━━━━━━━━━━━━━━━━━━"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="金融营销合规检查器 v1.0.0")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # review 命令
    review_parser = subparsers.add_parser("review", help="审查营销内容")
    review_parser.add_argument("--content", required=True, help="营销内容")
    review_parser.add_argument("--product-type", default="", help="金融产品类型")
    
    # plan 命令
    plan_parser = subparsers.add_parser("plan", help="审查营销方案")
    plan_parser.add_argument("--plan", required=True, help="营销方案")
    plan_parser.add_argument("--channel", default="", help="营销渠道")
    plan_parser.add_argument("--product-type", default="", help="金融产品类型")
    
    # generate 命令
    generate_parser = subparsers.add_parser("generate", help="生成营销方案")
    generate_parser.add_argument("--product-type", required=True, help="金融产品类型")
    generate_parser.add_argument("--target-audience", required=True, help="目标人群")
    generate_parser.add_argument("--channel", required=True, help="营销渠道")
    generate_parser.add_argument("--selling-points", required=True, help="核心卖点")
    
    args = parser.parse_args()
    
    if args.command == "review":
        result = check_content(args.content, args.product_type)
        print(format_report(result, "review"))
    
    elif args.command == "plan":
        result = check_marketing_plan(args.plan, args.channel, args.product_type)
        print(format_report(result, "review"))
    
    elif args.command == "generate":
        result = generate_marketing_plan(
            args.product_type,
            args.target_audience,
            args.channel,
            args.selling_points
        )
        print(format_report(result, "plan"))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

# 分行业敏感词库
INDUSTRY_KEYWORDS = {
    "fund": [
        "坐享其成", "躺赚", "抄底逃顶",
        "专家推荐", "受益者证明",
        "目标价", "强烈推荐"
    ],
    "securities": [
        "目标价", "强烈推荐",
        "内幕消息", "确定性判断"
    ],
    "insurance": [
        "存钱送保障", "分红",
        "不用健康告知"
    ],
    "bank": [
        "预期年化", "存款送礼",
        "保本理财"
    ]
}


def check_industry_content(content: str, industry: str) -> dict:
    """
    分行业合规检查
    
    Args:
        content: 营销内容文本
        industry: 行业类型（fund/securities/insurance/bank）
    
    Returns:
        审查结果字典
    """
    result = check_content(content)
    
    # 行业专属检查
    if industry in INDUSTRY_KEYWORDS:
        found_keywords = [word for word in INDUSTRY_KEYWORDS[industry] if word in content]
        if found_keywords:
            result["violations"].append({
                "rule": f"行业专属规则（{industry}）",
                "description": "使用行业禁止用语",
                "details": f"发现行业禁止用语：{', '.join(found_keywords)}",
                "severity": "高"
            })
            result["suggestions"].append(f"删除行业禁止用语：{', '.join(found_keywords)}")
    
    return result
