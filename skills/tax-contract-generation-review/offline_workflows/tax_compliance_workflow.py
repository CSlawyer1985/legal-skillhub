"""
合同涉税合规工作流。

提供合同涉税风险识别、审核清单生成、风险指标检查等功能。
"""

import json
from typing import Dict, Any, List, Optional

# ---- 合同涉税五大风险条款 ----
RISK_CATEGORIES = {
    "混合销售与兼营": {
        "risk_level": "high",
        "description": "同一合同含货物+服务，未分别注明金额从高适用税率",
        "check_items": [
            "合同是否含货物销售+安装/运输/服务",
            "是否分别注明各自金额",
            "是否刻意拆分合同降税率",
        ],
        "policy_refs": ["财税〔2016〕36号第三十九条、第四十条"],
    },
    "价外费用": {
        "risk_level": "high",
        "description": "违约金、赔偿金、滞纳金等未纳入计税依据",
        "check_items": [
            "违约金条款是否明确'开票缴税'",
            "赔偿金是否属价外费用",
            "代垫运费是否满足双条件",
        ],
        "policy_refs": ["增值税暂行条例第六条", "实施细则第十二条"],
    },
    "阴阳合同与拆分": {
        "risk_level": "critical",
        "description": "做低申报价、通过多份合同拆分收入",
        "check_items": [
            "合同价与备案价/市场价是否一致",
            "是否存在多份合同拆分同一笔交易",
            "是否存在私户/多账户收款",
        ],
        "policy_refs": ["税收征管法第六十三条", "发票管理办法第二十一条"],
    },
    "关联交易定价": {
        "risk_level": "medium",
        "description": "关联方交易定价偏离独立交易原则",
        "check_items": [
            "费率是否与承担功能匹配",
            "是否准备转让定价同期资料",
            "是否存在高进低出",
        ],
        "policy_refs": ["企业所得税法第四十一条"],
    },
    "政采与工程合同": {
        "risk_level": "medium",
        "description": "补充合同超10%上限、规避招标",
        "check_items": [
            "补充合同金额是否超原合同10%",
            "是否存在化整为零规避招标",
            "是否存在违法分包转包",
            "是否存在超进度付款",
        ],
        "policy_refs": ["审计署年度第1号公告"],
    },
}

# ---- 21项合同涉税风险指标 ----
RISK_INDICATORS = {
    "C01": {"name": "混合销售/兼营税率适用错误", "level": "high", "category": "混合销售与兼营"},
    "C02": {"name": "价外费用未纳入计税依据", "level": "high", "category": "价外费用"},
    "C03": {"name": "纳税义务发生时间错位", "level": "medium", "category": "混合销售与兼营"},
    "C05": {"name": "阴阳合同做低申报价", "level": "critical", "category": "阴阳合同与拆分"},
    "C06": {"name": "虚假服务合同虚开", "level": "critical", "category": "阴阳合同与拆分"},
    "C07": {"name": "合同拆分隐匿收入", "level": "critical", "category": "阴阳合同与拆分"},
    "C08": {"name": "关联交易定价偏离独立交易原则", "level": "medium", "category": "关联交易定价"},
    "C12": {"name": "政采补充合同超10%上限", "level": "medium", "category": "政采与工程合同"},
    "C13": {"name": "规避公开招标", "level": "medium", "category": "政采与工程合同"},
    "C14": {"name": "违法分包转包", "level": "medium", "category": "政采与工程合同"},
    "C15": {"name": "超进度付款", "level": "low", "category": "政采与工程合同"},
    "C16": {"name": "虚假验收", "level": "medium", "category": "政采与工程合同"},
    "C17": {"name": "发票正负面清单违规", "level": "critical", "category": "价外费用"},
    "C18": {"name": "预收款纳税义务时间错位", "level": "medium", "category": "混合销售与兼营"},
    "C19": {"name": "发票正负面清单违规", "level": "critical", "category": "价外费用"},
    "C20": {"name": "用工合同社保条款无效", "level": "medium", "category": "价外费用"},
    "C21": {"name": "小规模纳税人起征点违规", "level": "low", "category": "价外费用"},
}


def get_risk_categories() -> Dict[str, Any]:
    """Get all risk categories."""
    return RISK_CATEGORIES


def get_risk_indicators() -> Dict[str, Any]:
    """Get all risk indicators."""
    return RISK_INDICATORS


def check_risk(contract_text: str, indicators: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Check contract text against risk indicators.

    Args:
        contract_text: Contract text to check
        indicators: Specific indicators to check (None = all)

    Returns:
        List of risk findings
    """
    findings = []
    text_lower = contract_text.lower()

    # Risk keyword mapping
    risk_keywords = {
        "C01": ["分别核算", "混合销售", "兼营"],
        "C02": ["违约金", "赔偿金", "滞纳金", "价外费用"],
        "C03": ["纳税义务", "收款时间", "开票时间"],
        "C05": ["阴阳合同", "做低", "申报价", "备案价"],
        "C06": ["虚假", "虚开", "无真实"],
        "C07": ["拆分", "多份合同", "隐匿收入"],
        "C08": ["关联方", "转让定价", "独立交易"],
        "C12": ["补充合同", "超过", "10%"],
        "C13": ["规避招标", "化整为零"],
        "C14": ["分包", "转包"],
        "C15": ["超进度", "提前付款"],
        "C16": ["虚假验收", "未完工"],
        "C17": ["发票", "虚开", "代开"],
        "C18": ["预收", "预付款", "收款"],
        "C19": ["发票", "正负面"],
        "C20": ["社保", "用工", "事实劳动"],
        "C21": ["小规模", "起征点", "月10万"],
    }

    for code, keywords in risk_keywords.items():
        if indicators and code not in indicators:
            continue
        for kw in keywords:
            if kw in text_lower:
                indicator = RISK_INDICATORS.get(code, {})
                findings.append({
                    "indicator_code": code,
                    "indicator_name": indicator.get("name", ""),
                    "risk_level": indicator.get("level", "unknown"),
                    "matched_keyword": kw,
                })
                break  # One match per indicator

    return findings


def generate_review_checklist(contract_type: str) -> List[Dict[str, Any]]:
    """Generate review checklist for a contract type.

    Args:
        contract_type: Contract type name

    Returns:
        List of checklist items
    """
    checklist = []

    # General checklist
    checklist.extend([
        {"category": "法务", "item": "合同主体资格是否合法", "required": True},
        {"category": "法务", "item": "合同条款是否完整", "required": True},
        {"category": "法务", "item": "违约责任是否合理", "required": True},
        {"category": "财务", "item": "价格条款是否明确（含税/不含税）", "required": True},
        {"category": "财务", "item": "付款方式是否符合公司制度", "required": True},
        {"category": "税务", "item": "税率适用是否正确", "required": True},
        {"category": "税务", "item": "价外费用是否纳入计税依据", "required": True},
        {"category": "税务", "item": "印花税缴纳义务是否明确", "required": True},
    ])

    # Type-specific checklist
    if "租赁" in contract_type:
        checklist.extend([
            {"category": "税务", "item": "房产税缴纳义务是否明确", "required": True},
            {"category": "税务", "item": "干租/湿租税率是否区分正确", "required": False},
        ])
    elif "转让" in contract_type or "股权" in contract_type:
        checklist.extend([
            {"category": "税务", "item": "股权转让个税/企业所得税是否正确", "required": True},
            {"category": "税务", "item": "印花税按产权转移书据缴纳", "required": True},
        ])
    elif "技术" in contract_type:
        checklist.extend([
            {"category": "税务", "item": "技术转让是否经认定免税", "required": False},
            {"category": "税务", "item": "委托研发80%加计扣除条件是否满足", "required": False},
        ])
    elif "关联" in contract_type:
        checklist.extend([
            {"category": "税务", "item": "是否符合独立交易原则", "required": True},
            {"category": "税务", "item": "是否准备转让定价同期资料", "required": True},
        ])

    return checklist


def generate_review_report(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a review report from findings.

    Args:
        findings: List of risk findings

    Returns:
        Structured review report
    """
    critical = [f for f in findings if f.get("risk_level") == "critical"]
    high = [f for f in findings if f.get("risk_level") == "high"]
    medium = [f for f in findings if f.get("risk_level") == "medium"]
    low = [f for f in findings if f.get("risk_level") == "low"]

    if critical:
        conclusion = "不通过 - 存在重大风险，需立即整改"
    elif high:
        conclusion = "有条件通过 - 存在高风险，需整改后复审"
    elif medium:
        conclusion = "通过 - 存在中等风险，建议关注"
    else:
        conclusion = "通过 - 未发现重大风险"

    return {
        "conclusion": conclusion,
        "risk_summary": {
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
        },
        "findings": findings,
    }


if __name__ == "__main__":
    # Test
    sample_contract = "本合同约定违约金10万元，如乙方迟延交货，甲方有权解除合同并要求乙方赔偿损失。双方约定本合同价款为100万元（含税），乙方应向甲方开具增值税专用发票。"
    findings = check_risk(sample_contract)
    report = generate_review_report(findings)
    print(json.dumps(report, ensure_ascii=False, indent=2))
