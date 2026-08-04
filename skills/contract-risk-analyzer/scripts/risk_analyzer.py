"""
Risk Analyzer for Contract Risk Analyzer
Annotates contract text with risk levels based on industry risk checklist
"""

import re
from typing import Any

# Risk checklist by level
RISK_CHECKLIST = {
    "🔴": [
        {
            "id": "R001",
            "name": "金额不明确或留空",
            "keywords": ["金额", "合同金额", "总价款", "总费用", "报酬"],
            "pattern": r"(金额|合同金额|总价款|总费用|报酬)\s*[为是为]?\s*[：:]\s*[^\d\s]",
            "severity": "high"
        },
        {
            "id": "R002",
            "name": "违约责任严重不对等",
            "keywords": ["违约责任", "违约金", "赔偿责任"],
            "pattern": r"(甲方|乙方).{0,20}(违约|赔偿).{0,50}(甲方|乙方).{0,20}(违约|赔偿)",
            "severity": "high"
        },
        {
            "id": "R003",
            "name": "违约金比例过高",
            "keywords": ["违约金", "赔偿", "损失"],
            "pattern": r"违约金\s*[为是为]?\s*([2-9]\d|[1-9]\d{2,})%",
            "severity": "high"
        },
        {
            "id": "R004",
            "name": "管辖法院在外地且对我方不利",
            "keywords": ["管辖", "仲裁", "诉讼"],
            "pattern": r"(管辖|仲裁|诉讼).{0,30}(甲方所在地|乙方所在地|对方)",
            "severity": "high"
        },
        {
            "id": "R005",
            "name": "无解除条款",
            "keywords": ["解除", "终止", "撤销"],
            "pattern": r"(?!.*(解除|终止|撤销)).{100,}",
            "severity": "high",
            "negate_match": True
        },
        {
            "id": "R006",
            "name": "无限连带责任",
            "keywords": ["连带", "连带责任", "无限责任"],
            "pattern": r"无限连带",
            "severity": "high"
        },
        {
            "id": "R007",
            "name": "格式条款未明示",
            "keywords": ["格式条款", "格式合同", "标准化条款"],
            "pattern": r"(?!.*(格式条款.*确认|已阅读|同意)).{200,}",
            "severity": "high",
            "negate_match": True
        },
    ],
    "🟠": [
        {
            "id": "Y001",
            "name": "付款方式无明确时间节点",
            "keywords": ["付款", "支付", "结算"],
            "pattern": r"付款.{0,20}(后|内|前|时)",
            "severity": "medium"
        },
        {
            "id": "Y002",
            "name": "保密期限超过2年",
            "keywords": ["保密期限", "保密期", "保密义务期限"],
            "pattern": r"保密.{0,10}(期限|期).{0,10}([2-9]|[1-9]\d)年|自.{0,10}起\s*[2-9]年",
            "severity": "medium"
        },
        {
            "id": "Y003",
            "name": "竞业限制范围过宽",
            "keywords": ["竞业", "竞争", "同业"],
            "pattern": r"竞业.{0,20}(全部|所有|任何|一切|全部业务)",
            "severity": "medium"
        },
        {
            "id": "Y004",
            "name": "知识产权归属模糊",
            "keywords": ["知识产权", "版权", "专利", "著作权", "成果"],
            "pattern": r"(知识产权|版权|专利).{0,30}(归属|所有|享有)",
            "severity": "medium"
        },
        {
            "id": "Y005",
            "name": "不可抗力条款过于宽松",
            "keywords": ["不可抗力"],
            "pattern": r"不可抗力.{0,30}(不包括|排除|不含)",
            "severity": "medium"
        },
        {
            "id": "Y006",
            "name": "争议解决方式不利于维权",
            "keywords": ["仲裁", "诉讼", "管辖"],
            "pattern": r"(仲裁|诉讼|管辖).{0,50}(国际|境外|外国|国外)",
            "severity": "medium"
        },
        {
            "id": "Y007",
            "name": "单方面变更权",
            "keywords": ["变更", "修改", "调整"],
            "pattern": r"(甲方|委托方|买方).{0,20}(变更|修改|调整).{0,30}(无需|不必|不需要)",
            "severity": "medium"
        },
    ],
    "🟡": [
        {
            "id": "G001",
            "name": "通知方式未明确",
            "keywords": ["通知", "送达"],
            "pattern": r"(?!.*(书面通知|邮件通知|电子通知|书面形式)).{150,}",
            "severity": "low",
            "negate_match": True
        },
        {
            "id": "G002",
            "name": "合同份数未约定",
            "keywords": ["合同份数", "正本", "副本"],
            "pattern": r"(?!.*(合同份数|一式|正本|副本)).{150,}",
            "severity": "low",
            "negate_match": True
        },
        {
            "id": "G003",
            "name": "附件与正文不一致风险",
            "keywords": ["附件", "附录"],
            "pattern": r"附件与本合同具有同等法律效力",
            "severity": "low"
        },
        {
            "id": "G004",
            "name": "语言版本冲突未说明",
            "keywords": ["语言", "中文", "英文"],
            "pattern": r"(?!.*(中英文|双语|语言版本)).{150,}",
            "severity": "low",
            "negate_match": True
        },
        {
            "id": "G005",
            "name": "合同生效条件模糊",
            "keywords": ["生效", "有效"],
            "pattern": r"本合同.{0,30}生效",
            "severity": "low"
        },
    ]
}


def annotate_risks(
    text: str,
    fields: dict = None,
) -> list:
    """
    Analyze contract text and annotate risks based on checklist.

    Args:
        text: Contract text content
        fields: Optional extracted fields dict

    Returns:
        List of risk items with level, name, suggestion
    """
    risks = []
    text_lower = text.lower()

    # Check each risk level
    for level, checklist in RISK_CHECKLIST.items():
        for item in checklist:
            risk_found = False

            # Keyword-based quick check
            keywords_found = sum(1 for kw in item["keywords"] if kw.lower() in text_lower)

            if keywords_found > 0:
                # Pattern-based verification
                try:
                    if "pattern" in item:
                        pattern_match = re.search(item["pattern"], text, re.IGNORECASE)
                        if item.get("negate_match"):
                            risk_found = pattern_match is None
                        else:
                            risk_found = pattern_match is not None
                    else:
                        risk_found = keywords_found >= 1
                except re.error as e:
                    # Invalid regex, fall back to keyword
                    risk_found = keywords_found >= 2

            if risk_found:
                risks.append({
                    "level": level,
                    "item": item["name"],
                    "id": item["id"],
                    "suggestion": _get_suggestion(item["name"], level),
                    "severity": item["severity"]
                })

    # Sort by severity: 🔴 first, then 🟠, then 🟡
    severity_order = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return risks


def _get_suggestion(risk_name: str, level: str) -> str:
    """Get suggestion text for a risk item."""
    suggestions = {
        "金额不明确或留空": "建议在合同中明确填写具体金额或计算方式，避免履行时产生争议。",
        "违约责任严重不对等": "建议要求双方违约责任对等，避免单方面承担过重责任。",
        "违约金比例过高": "建议将违约金比例控制在损失金额的30%以内，避免显失公平。",
        "管辖法院在外地且对我方不利": "建议约定为本地法院管辖，或选择双方认可的第三方仲裁机构。",
        "无解除条款": "建议添加明确的合同解除条件和程序，保护双方权益。",
        "无限连带责任": "建议要求改为有限连带责任，或要求对方提供相应担保。",
        "格式条款未明示": "建议将格式条款加粗显示，并要求对方确认已阅读理解。",
        "付款方式无明确时间节点": "建议明确约定付款的具体日期或期限，如'签约后15个工作日内'。",
        "保密期限超过2年": "建议将保密期限控制在2年以内，合理的保密期限通常为1-2年。",
        "竞业限制范围过宽": "建议缩小竞业限制的行业范围和地域范围，并明确补偿标准。",
        "知识产权归属模糊": "建议明确约定知识产权归属，建议归委托方或双方共有。",
        "不可抗力条款过于宽松": "建议明确不可抗力的定义和范围，平衡双方风险。",
        "争议解决方式不利于维权": "建议选择我方所在地的仲裁机构或法院管辖。",
        "单方面变更权": "建议修改为双方协商一致后方可变更，或设置合理的变更条件。",
        "通知方式未明确": "建议明确约定通知方式和送达地址，如书面邮寄或电子邮件。",
        "合同份数未约定": "建议明确合同份数及各自用途，如'本合同一式两份，甲乙双方各执一份'。",
        "附件与正文不一致风险": "建议明确附件的法律效力，并在正文注明冲突时的优先顺序。",
        "语言版本冲突未说明": "建议明确约定以中文版本为准，或提供准确的双语版本。",
        "合同生效条件模糊": "建议明确约定合同生效条件，如'本合同自双方签字盖章之日起生效'。",
    }

    base_suggestion = suggestions.get(risk_name, "建议咨询专业法律人士。")

    if level == "🔴":
        return f"【高风险】{base_suggestion}"
    elif level == "🟠":
        return f"【中风险】{base_suggestion}"
    else:
        return f"【低风险】{base_suggestion}"


def get_risk_summary(risks: list) -> dict:
    """Get a summary count of risks by level."""
    summary = {"🔴": 0, "🟠": 0, "🟡": 0}
    for risk in risks:
        level = risk.get("level", "🟡")
        if level in summary:
            summary[level] += 1
    return summary
