"""
Report Generator for Contract Risk Analyzer
Generates structured risk report in Markdown format
"""

from datetime import datetime
from typing import Any, Optional

from .risk_analyzer import get_risk_summary


def generate_report(
    contract_type: str,
    summary: str,
    key_terms: list,
    risks: list,
    contract_name: str = "未命名合同",
) -> str:
    """
    Generate a complete risk report in Markdown format.

    Args:
        contract_type: Type of contract
        summary: Contract summary text
        key_terms: List of key term dicts with category, content, risk
        risks: List of risk dicts with level, item, suggestion
        contract_name: Optional contract name

    Returns:
        Markdown formatted report
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build report sections
    report = f"""# 合同风险审查报告

**合同名称：** {contract_name}
**合同类型：** {contract_type}
**审查时间：** {now}
**免责声明：** 本报告由AI自动生成，仅供参考，不构成法律建议。如有法律问题请咨询专业律师。

---

## 一、合同摘要

{summary if summary else '暂无摘要信息'}

---

## 二、关键条款

"""

    # Key terms table
    if key_terms:
        report += "| 条款类别 | 原文摘要 | 风险提示 |\n"
        report += "|---------|---------|---------|\n"
        for term in key_terms:
            category = term.get("category", "")
            content = term.get("content", "")
            risk = term.get("risk", "")
            # Truncate long content
            if len(content) > 50:
                content = content[:47] + "..."
            report += f"| {category} | {content} | {risk} |\n"
    else:
        report += "*暂无关键条款信息*\n"

    report += "\n---\n\n## 三、风险点列表\n\n"

    # Group risks by level
    risks_by_level = {"🔴": [], "🟠": [], "🟡": []}
    for risk in risks:
        level = risk.get("level", "🟡")
        if level in risks_by_level:
            risks_by_level[level].append(risk)

    # High risk
    if risks_by_level["🔴"]:
        report += "### 🔴 高风险（需特别注意，可能对我方不利）\n\n"
        for i, risk in enumerate(risks_by_level["🔴"], 1):
            report += f"{i}. **{risk['item']}**：{risk.get('suggestion', '')}\n"
        report += "\n"

    # Medium risk
    if risks_by_level["🟠"]:
        report += "### 🟠 中风险（建议要求修改或添加补充条款）\n\n"
        for i, risk in enumerate(risks_by_level["🟠"], 1):
            report += f"{i}. **{risk['item']}**：{risk.get('suggestion', '')}\n"
        report += "\n"

    # Low risk
    if risks_by_level["🟡"]:
        report += "### 🟡 低风险（需要注意，但影响较小）\n\n"
        for i, risk in enumerate(risks_by_level["🟡"], 1):
            report += f"{i}. **{risk['item']}**：{risk.get('suggestion', '')}\n"
        report += "\n"

    # Risk summary
    summary_counts = get_risk_summary(risks)
    report += "---\n\n"
    report += f"## 四、风险统计\n\n"
    report += f"- 🔴 高风险：{summary_counts['🔴']} 项\n"
    report += f"- 🟠 中风险：{summary_counts['🟠']} 项\n"
    report += f"- 🟡 低风险：{summary_counts['🟡']} 项\n"
    report += f"- **总计**：{len(risks)} 项风险\n\n"

    # Overall assessment
    total_risks = len(risks)
    if total_risks == 0:
        assessment = "✅ 本合同未发现明显风险条款，建议继续履行。"
    elif summary_counts["🔴"] >= 2:
        assessment = "⚠️ 本合同存在较多高风险条款，建议修改后再签署。"
    elif summary_counts["🔴"] >= 1:
        assessment = "⚠️ 本合同存在高风险条款，请特别关注并要求修改。"
    elif summary_counts["🟠"] >= 3:
        assessment = "📋 本合同存在中等风险条款，建议要求添加补充条款。"
    else:
        assessment = "✅ 本合同风险可控，个别条款建议关注。"

    report += f"**总体评估**：{assessment}\n\n"
    report += "---\n\n*本报告由合同风险智能审查工具自动生成*\n"

    return report


def generate_compact_report(
    contract_type: str,
    summary: str,
    key_terms: list,
    risks: list,
    contract_name: str = "未命名合同",
) -> str:
    """
    Generate a compact version of the risk report (for Feishu card).

    Args:
        contract_type: Type of contract
        summary: Contract summary text
        key_terms: List of key term dicts
        risks: List of risk dicts
        contract_name: Optional contract name

    Returns:
        Compact Markdown formatted report
    """
    now = datetime.now().strftime("%Y-%m-%d")

    # Truncate summary
    if len(summary) > 300:
        summary = summary[:297] + "..."

    report = f"""📋 **合同风险审查报告**

**{contract_name}**
类型：{contract_type} | {now}

---

**摘要：** {summary}

---

"""

    # Group risks
    risks_by_level = {"🔴": [], "🟠": [], "🟡": []}
    for risk in risks:
        level = risk.get("level", "🟡")
        if level in risks_by_level:
            risks_by_level[level].append(risk)

    if risks_by_level["🔴"]:
        report += "🔴 **高风险**\n"
        for risk in risks_by_level["🔴"]:
            report += f"• {risk['item']}\n"
        report += "\n"

    if risks_by_level["🟠"]:
        report += "🟠 **中风险**\n"
        for risk in risks_by_level["🟠"]:
            report += f"• {risk['item']}\n"
        report += "\n"

    if risks_by_level["🟡"]:
        report += "🟡 **低风险**\n"
        for risk in risks_by_level["🟡"]:
            report += f"• {risk['item']}\n"
        report += "\n"

    # Summary
    summary_counts = get_risk_summary(risks)
    report += f"📊 风险统计：🔴{summary_counts['🔴']} 🟠{summary_counts['🟠']} 🟡{summary_counts['🟡']}\n"
    report += f"\n⚠️ 本报告仅供参考，不构成法律建议。"

    return report


def generate_excel_report(
    contract_type: str,
    summary: str,
    key_terms: list,
    risks: list,
) -> list:
    """
    Generate data for Excel report output.

    Returns:
        List of dicts suitable for Excel/CSV export
    """
    rows = []

    # Key terms
    for term in key_terms:
        rows.append({
            "类别": "关键条款",
            "项目": term.get("category", ""),
            "内容": term.get("content", ""),
            "风险提示": term.get("risk", ""),
            "风险等级": ""
        })

    # Risks
    for risk in risks:
        rows.append({
            "类别": "风险点",
            "项目": risk.get("item", ""),
            "内容": risk.get("suggestion", ""),
            "风险提示": "",
            "风险等级": risk.get("level", "")
        })

    return rows
