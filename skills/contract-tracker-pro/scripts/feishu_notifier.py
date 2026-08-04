"""
Feishu Notifier for Contract Tracker Pro
Sends reminder notifications via Feishu interactive cards
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def build_reminder_card(reminder: dict) -> dict:
    """
    Build a Feishu interactive card for a single reminder.

    Args:
        reminder: Dict from reminder_checker.check_reminders

    Returns:
        Feishu card JSON element (dict)
    """
    contract_name = reminder.get("contract_name", "未知合同")
    contract_number = reminder.get("contract_number", "")
    node_desc = reminder.get("description", "未描述")
    amount = reminder.get("amount")
    due_date = reminder.get("due_date", "未知")
    days = reminder.get("days_until_due", 0)
    reminder_type = reminder.get("reminder_type", "")
    node_type = reminder.get("node_type", "")

    # Status emoji and label
    if reminder_type == "overdue":
        emoji = "🔴"
        status_label = f"已逾期 {abs(days)} 天"
        header_color = "red"
    elif reminder_type == "today":
        emoji = "🟠"
        status_label = "今天是截止日期！"
        header_color = "orange"
    else:
        emoji = "🟡"
        status_label = f"距截止还有 {days} 天"
        header_color = "yellow"

    # Type label
    type_labels = {
        "payment": "💰 付款",
        "delivery": "📦 交付",
        "expiry": "📅 到期",
        "acceptance": "✅ 验收",
        "warranty": "🛡 质保",
    }
    type_label = type_labels.get(node_type, node_type)

    # Amount
    amount_str = f"¥{amount:,.2f}" if amount else "—"

    # Header title
    title = f"{emoji} 合同履约提醒"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": header_color,
        },
        "elements": [
            {
                "tag": "markdown",
                "content": f"**合同名称**：{contract_name}",
            },
            {
                "tag": "markdown",
                "content": f"**合同编号**：{contract_number or '—'}",
            },
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": f"**节点类型**：{type_label}",
            },
            {
                "tag": "markdown",
                "content": f"**节点描述**：{node_desc}",
            },
            {
                "tag": "markdown",
                "content": f"**金额**：{amount_str}",
            },
            {
                "tag": "markdown",
                "content": f"**截止日期**：{due_date}",
            },
            {
                "tag": "markdown",
                "content": f"**状态**：{emoji} {status_label}",
            },
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": "_请及时处理，或在系统中标记完成。_",
            },
        ],
    }

    return card


def build_reminder_summary_card(reminders: list) -> dict:
    """
    Build a Feishu card summarizing multiple reminders.

    Args:
        reminders: List of reminder dicts from check_reminders

    Returns:
        Feishu card dict
    """
    if not reminders:
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "✅ 合同履约提醒"},
                "template": "grey",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": "暂无需要提醒的履约节点。",
                }
            ],
        }

    overdue = [r for r in reminders if r.get("reminder_type") == "overdue"]
    today = [r for r in reminders if r.get("reminder_type") == "today"]
    advance = [r for r in reminders if r.get("reminder_type") == "advance_3day"]

    # Count
    overdue_count = len(overdue)
    today_count = len(today)
    advance_count = len(advance)

    lines = []

    if overdue:
        lines.append(f"🔴 **已逾期**（{overdue_count} 项）")
        for r in overdue[:5]:
            days = r.get("days_until_due", 0)
            lines.append(f"- {r.get('contract_name')}：{r.get('description')}（逾期 {abs(days)} 天）")
        if overdue_count > 5:
            lines.append(f"- ...还有 {overdue_count - 5} 项逾期")
        lines.append("")

    if today:
        lines.append(f"🟠 **今日到期**（{today_count} 项）")
        for r in today:
            lines.append(f"- {r.get('contract_name')}：{r.get('description')}")
        lines.append("")

    if advance:
        lines.append(f"🟡 **即将到期（3天内）**（{advance_count} 项）")
        for r in advance[:5]:
            days = r.get("days_until_due", 0)
            lines.append(f"- {r.get('contract_name')}：{r.get('description')}（{days} 天）")
        if advance_count > 5:
            lines.append(f"- ...还有 {advance_count - 5} 项即将到期")

    content_md = "\n".join(lines)

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📋 合同履约提醒（{len(reminders)} 项）"},
            "template": "red" if overdue else "orange" if today else "yellow",
        },
        "elements": [
            {"tag": "markdown", "content": content_md},
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": "_请及时处理，或在系统中标记完成。_",
            },
        ],
    }

    return card


def prepare_reminder_notification(
    reminder: dict,
    for_card: bool = True,
) -> dict:
    """
    Prepare Feishu notification data for the agent to send.

    Args:
        reminder: Single reminder dict from check_reminders
        for_card: If True, return interactive card; else text

    Returns:
        Dict with:
        - card: Feishu card as dict
        - card_json: JSON string of card (for feishu_im_user_message content)
        - text: Plain text fallback message
        - reminder_message: Short text for the notification
    """
    if for_card:
        card = build_reminder_card(reminder)
        return {
            "card": card,
            "card_json": json.dumps(card, ensure_ascii=False),
            "text": None,
        }
    else:
        from .reminder_checker import build_reminder_message
        text = build_reminder_message(reminder)
        return {
            "card": None,
            "card_json": None,
            "text": text,
        }


def prepare_summary_notification(
    reminders: list,
    for_card: bool = True,
) -> dict:
    """
    Prepare Feishu summary notification for multiple reminders.

    Args:
        reminders: List of reminder dicts
        for_card: If True, return interactive card

    Returns:
        Dict with card/text data
    """
    if for_card:
        card = build_reminder_summary_card(reminders)
        return {
            "card": card,
            "card_json": json.dumps(card, ensure_ascii=False),
            "text": None,
        }
    else:
        from .reminder_checker import format_reminders_batch
        text = format_reminders_batch(reminders)
        return {
            "card": None,
            "card_json": None,
            "text": text,
        }
