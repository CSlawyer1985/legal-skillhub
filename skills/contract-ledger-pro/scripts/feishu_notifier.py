"""
合同台账管理 - 飞书通知模块
使用飞书 IM 工具推送到期提醒
"""
from datetime import datetime, timedelta
from typing import Optional

# Feishu card template for expiry reminders
FEISHU_REMINDER_CARD = {
    "config": {"wide_screen_mode": True},
    "elements": [
        {
            "tag": "markdown",
            "content": "**🔔 合同到期提醒**"
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "fields": [
                {"is_short": True, "text": {"tag": "lark_md", "content": "**合同名称**"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "{contract_name}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "**对方**"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "{counterparty}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "**到期日期**"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "{end_date}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "**剩余天数**"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "{days_left} 天"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "**合同金额**"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": "{amount}"}},
            ]
        },
        {"tag": "hr"},
        {
            "tag": "note",
            "elements": [
                {"tag": "lark_md", "content": "来自合同台账管理系统"}
            ]
        }
    ],
    "header": {
        "title": {"tag": "plain_text", "content": "📄 合同到期提醒"},
        "template": "orange"
    }
}


def build_reminder_card(contract: dict, days_until_expiry: int) -> dict:
    """构建提醒卡片"""
    fields = [
        {"is_short": True, "text": {"tag": "lark_md", "content": "**合同名称**"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": f"{contract.get('contract_name', '未知')}"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": "**对方**"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": f"{contract.get('counterparty', '未知')}"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": "**到期日期**"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": f"{contract.get('end_date', '未知')}"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": "**剩余天数**"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": f"{days_until_expiry} 天"}},
    ]

    # Add amount if available
    amount = contract.get("amount")
    if amount:
        fields.extend([
            {"is_short": True, "text": {"tag": "lark_md", "content": "**合同金额**"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"¥{amount:,.2f}"}},
        ])

    card = {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "markdown",
                "content": "**🔔 合同即将到期**"
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "fields": fields
            },
            {"tag": "hr"},
            {
                "tag": "markdown",
                "content": "来自合同台账管理系统"
            }
        ],
        "header": {
            "title": {"tag": "plain_text", "content": "📄 合同到期提醒"},
            "template": "orange"
        }
    }

    return card


def format_reminder_message(contract: dict, days_until_expiry: int) -> str:
    """格式化提醒消息（纯文本备选）"""
    name = contract.get("contract_name", "未知")
    counterparty = contract.get("counterparty", "未知")
    end_date = contract.get("end_date", "未知")
    amount = contract.get("amount")

    msg = f"🔔 合同即将到期\n\n"
    msg += f"📄 {name}\n"
    msg += f"👤 对方：{counterparty}\n"
    msg += f"📅 到期：{end_date}\n"
    msg += f"⏰ 剩余：{days_until_expiry} 天\n"
    if amount:
        msg += f"💰 金额：¥{amount:,.2f}\n"
    return msg
