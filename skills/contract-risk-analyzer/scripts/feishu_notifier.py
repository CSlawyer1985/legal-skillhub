"""

import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def build_feishu_card(
    contract_name: str,
    contract_type: str,
    summary: str,
    risk_summary: dict,
    top_risks: list,
    report_url: Optional[str] = None,
) -> dict:
    """
    Build Feishu interactive card payload for risk report.

    Args:
        contract_name: Name of the contract
        contract_type: Type of contract
        summary: Contract summary
        risk_summary: Dict with risk counts by level
        top_risks: Top 3 risks to highlight
        report_url: Optional URL to full report

    Returns:
        Feishu card JSON element (dict)
    """
    # Build risk summary text
    risk_text = f"🔴 高风险：{risk_summary.get('🔴', 0)} 项 | 🟠 中风险：{risk_summary.get('🟠', 0)} 项 | 🟡 低风险：{risk_summary.get('🟡', 0)} 项"

    # Truncate summary
    display_summary = summary[:300] + "..." if len(summary) > 300 else summary

    # Build top risks section
    risk_md_parts = []
    for risk in top_risks[:5]:
        level_emoji = risk.get("level", "🟡")
        risk_md_parts.append(f"{level_emoji} **{risk.get('item', '')}**")

    risk_md = "\n".join(risk_md_parts) if risk_md_parts else "未发现明显风险点"

    # Build card
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "markdown",
                "content": f"# 📋 合同风险审查报告\n**{contract_name}**\n\n类型：{contract_type} | {risk_text}"
            },
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": f"### 📝 合同摘要\n{display_summary}"
            },
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": f"### ⚠️ 主要风险点\n\n{risk_md}"
            },
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": "⚠️ _本报告由AI自动生成，仅供参考，不构成法律建议。_"
            }
        ]
    }

    return card


def build_feishu_text_message(
    contract_name: str,
    contract_type: str,
    summary: str,
    risk_summary: dict,
) -> str:
    """
    Build a plain text Feishu message (fallback when card fails).

    Args:
        contract_name: Name of contract
        contract_type: Type of contract
        summary: Contract summary
        risk_summary: Dict with risk counts

    Returns:
        Plain text message
    """
    # Truncate summary for text
    display_summary = summary[:500] + "..." if len(summary) > 500 else summary

    lines = [
        f"📋 合同风险审查报告已完成",
        f"",
        f"合同名称：{contract_name}",
        f"合同类型：{contract_type}",
        f"",
        f"摘要：{display_summary}",
        f"",
        f"风险统计：",
        f"  🔴 高风险：{risk_summary.get('🔴', 0)} 项",
        f"  🟠 中风险：{risk_summary.get('🟠', 0)} 项",
        f"  🟡 低风险：{risk_summary.get('🟡', 0)} 项",
        f"",
        f"⚠️ 本报告仅供参考，不构成法律建议。",
    ]

    return "\n".join(lines)


def prepare_feishu_notification(
    open_id: str,
    report_markdown: str,
    contract_type: str,
    contract_name: str = "合同",
    risk_summary: Optional[dict] = None,
    top_risks: Optional[list] = None,
) -> dict:
    """
    Prepare Feishu notification data for sending.

    This function returns the necessary data that the agent should use
    to send via the feishu_im_user_message tool.

    Args:
        open_id: User's Feishu open_id
        report_markdown: Full report in markdown
        contract_type: Type of contract
        contract_name: Name of contract
        risk_summary: Dict with risk counts
        top_risks: Top risks list

    Returns:
        Dict with:
        - open_id: User's open_id
        - card: Feishu card payload (dict)
        - text_fallback: Plain text fallback message
    """
    # Default risk summary
    if risk_summary is None:
        risk_summary = {"🔴": 0, "🟠": 0, "🟡": 0}
    if top_risks is None:
        top_risks = []

    # Extract summary from markdown
    summary = ""
    if "## 一、合同摘要" in report_markdown:
        parts = report_markdown.split("## 一、合同摘要")
        if len(parts) > 1:
            summary_part = parts[1].split("---")[0]
            summary = summary_part.strip()

    # Build card
    card = build_feishu_card(
        contract_name=contract_name,
        contract_type=contract_type,
        summary=summary,
        risk_summary=risk_summary,
        top_risks=top_risks
    )

    # Build text fallback
    text_fallback = build_feishu_text_message(
        contract_name=contract_name,
        contract_type=contract_type,
        summary=summary,
        risk_summary=risk_summary
    )

    return {
        "open_id": open_id,
        "card": card,
        "text_fallback": text_fallback,
    }


def send_feishu_notification(
    open_id: str,
    report_markdown: str,
    contract_type: str,
    contract_name: str = "合同",
    risk_summary: Optional[dict] = None,
    top_risks: Optional[list] = None,
) -> dict:
    """
    Prepare Feishu notification data for agent to send via feishu_im_user_message tool.

    IMPORTANT: This function only PREPARES the notification data.
    The agent must actually send it using OpenClaw's feishu_im_user_message tool:

        # After calling send_feishu_notification():
        notification = send_feishu_notification(...)
        if notification["ready"]:
            feishu_im_user_message(
                action="send",
                receive_id_type="open_id",
                receive_id=notification["open_id"],
                msg_type="interactive",
                content=notification["card_json"],
            )

    For graceful degradation when Feishu auth is unavailable:
    - If feishu_im_user_message fails, log the error but continue
    - The report_markdown is already available as local output
    - Do NOT crash or abort - just skip the notification

    Args:
        open_id: User's Feishu open_id
        report_markdown: Full report in markdown
        contract_type: Type of contract
        contract_name: Name of contract
        risk_summary: Dict with risk counts (e.g., {"🔴": 2, "🟠": 1, "🟡": 0})
        top_risks: List of top risk dicts (e.g., [{"level": "🔴", "item": "风险项"}])

    Returns:
        Dict with:
        - ready: bool, True if data prepared successfully
        - open_id: User's open_id
        - card: Feishu card as dict
        - card_json: Feishu card as JSON string (for feishu_im_user_message content)
        - text_fallback: Plain text message (fallback if interactive card fails)
    """
    notification_data = prepare_feishu_notification(
        open_id=open_id,
        report_markdown=report_markdown,
        contract_type=contract_type,
        contract_name=contract_name,
        risk_summary=risk_summary,
        top_risks=top_risks,
    )

    return {
        "ready": True,
        "open_id": notification_data["open_id"],
        "card": notification_data["card"],
        "card_json": json.dumps(notification_data["card"], ensure_ascii=False),
        "text_fallback": notification_data["text_fallback"],
    }
