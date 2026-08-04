"""
Reminder Checker for Contract Tracker Pro
Checks pending reminders based on today's date
Reminder rules:
  - 3 days before due date → advance reminder
  - On due date → today reminder
  - Overdue → daily reminder (until marked completed)
"""

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "pending": "🟡待执行",
    "completed": "🟢已完成",
    "overdue": "🔴已逾期",
}


def compute_status(due_date_str: str, current_status: str) -> str:
    """
    Compute the effective status based on due date and current status.
    If already completed, stays completed.
    If overdue (past due date), returns 'overdue'.
    Otherwise returns current status (usually 'pending').
    """
    if current_status == "completed":
        return "completed"

    if not due_date_str:
        return current_status  # cannot determine

    try:
        due = date.fromisoformat(due_date_str)
        today = date.today()

        if today > due:
            return "overdue"
        return "pending"
    except (ValueError, TypeError):
        return current_status


def check_reminders(
    contract_id: Optional[str] = None,
    ledger_manager=None,
) -> list:
    """
    Check all contracts and nodes that need reminders today.

    Returns a list of reminder dicts, each containing:
      - contract_id, contract_name
      - node_id, node_type, description, amount, due_date
      - reminder_type: 'advance_3day' | 'today' | 'overdue'
      - days_until_due: negative if overdue
      - current_status

    Args:
        contract_id: If provided, only check this contract
        ledger_manager: LedgerManager instance (creates one if None)
    """
    if ledger_manager is None:
        from .ledger_manager import LedgerManager
        ledger_manager = LedgerManager()

    contracts = ledger_manager.list_contracts(include_completed=False)
    if contract_id:
        contracts = [c for c in contracts if c.get("id") == contract_id]

    reminders = []
    today = date.today()
    advance_days = 3

    for contract in contracts:
        for node in contract.get("nodes", []):
            due_date_str = node.get("due_date")
            current_status = node.get("status", "pending")

            # Skip completed nodes
            if current_status == "completed":
                continue

            # Compute effective status based on due date
            effective_status = compute_status(due_date_str, current_status)

            # Update node status if overdue
            if effective_status == "overdue" and current_status != "overdue":
                ledger_manager.update_node_status(
                    contract["id"], node["id"], "overdue"
                )
                node["status"] = "overdue"

            # Determine if reminder should fire
            reminder_type = None
            if not due_date_str:
                continue

            try:
                due = date.fromisoformat(due_date_str)
                days_until = (due - today).days

                if days_until == 0:
                    reminder_type = "today"
                elif days_until == advance_days:
                    reminder_type = "advance_3day"
                elif days_until < 0:
                    reminder_type = "overdue"
                # else: not yet time

            except (ValueError, TypeError):
                logger.warning(f"Invalid due_date format: {due_date_str}")
                continue

            if reminder_type:
                reminders.append({
                    "contract_id": contract.get("id"),
                    "contract_name": contract.get("name"),
                    "contract_number": contract.get("number"),
                    "node_id": node.get("id"),
                    "node_type": node.get("type"),
                    "description": node.get("description", ""),
                    "amount": node.get("amount"),
                    "due_date": due_date_str,
                    "effective_status": effective_status,
                    "reminder_type": reminder_type,
                    "days_until_due": (date.fromisoformat(due_date_str) - today).days if due_date_str else 0,
                })

    logger.info(f"Found {len(reminders)} reminders")
    return reminders


def get_pending_reminders(
    contract_id: Optional[str] = None,
) -> list:
    """
    Get all pending reminders without updating statuses.
    Convenience wrapper for check_reminders.
    """
    return check_reminders(contract_id=contract_id)


def build_reminder_message(reminder: dict) -> str:
    """
    Build a human-readable reminder message for a single reminder.

    Args:
        reminder: Dict from check_reminders

    Returns:
        Formatted text message
    """
    contract_name = reminder.get("contract_name", "未知合同")
    contract_number = reminder.get("contract_number", "")
    node_desc = reminder.get("description", "未描述")
    amount = reminder.get("amount")
    due_date = reminder.get("due_date", "未知")
    days = reminder.get("days_until_due", 0)
    reminder_type = reminder.get("reminder_type", "")
    node_type = reminder.get("node_type", "")

    # Type labels
    type_labels = {
        "payment": "付款",
        "delivery": "交付",
        "expiry": "到期",
        "acceptance": "验收",
        "warranty": "质保",
    }
    type_label = type_labels.get(node_type, node_type)

    # Status
    if reminder_type == "overdue":
        status_label = f"🔴已逾期 {abs(days)} 天"
    elif reminder_type == "today":
        status_label = "🟠今天是截止日期！"
    else:
        status_label = f"🟡距截止还有 {days} 天"

    # Amount
    amount_str = f"¥{amount:,.2f}" if amount else ""

    lines = [
        f"📋 合同履约提醒",
        f"",
        f"合同：{contract_name}",
        f"编号：{contract_number or '—'}",
        f"节点：{type_label} - {node_desc}",
    ]

    if amount_str:
        lines.append(f"金额：{amount_str}")

    lines.extend([
        f"截止日期：{due_date}",
        f"状态：{status_label}",
    ])

    return "\n".join(lines)


def format_reminders_batch(reminders: list) -> str:
    """
    Format multiple reminders into a single summary message.
    """
    if not reminders:
        return "✅ 暂无需要提醒的履约节点"

    # Group by reminder type
    today_reminders = [r for r in reminders if r.get("reminder_type") == "today"]
    advance_reminders = [r for r in reminders if r.get("reminder_type") == "advance_3day"]
    overdue_reminders = [r for r in reminders if r.get("reminder_type") == "overdue"]

    parts = []

    if overdue_reminders:
        parts.append(f"🔴 **已逾期**（{len(overdue_reminders)} 项）")
        for r in overdue_reminders[:5]:
            parts.append(f"  • {r.get('contract_name')}：{r.get('description')}（逾期 {abs(r.get('days_until_due',0))} 天）")
        if len(overdue_reminders) > 5:
            parts.append(f"  • ...还有 {len(overdue_reminders) - 5} 项逾期")

    if today_reminders:
        parts.append(f"🟠 **今日到期**（{len(today_reminders)} 项）")
        for r in today_reminders:
            parts.append(f"  • {r.get('contract_name')}：{r.get('description')}")

    if advance_reminders:
        parts.append(f"🟡 **即将到期（3天内）**（{len(advance_reminders)} 项）")
        for r in advance_reminders[:5]:
            parts.append(f"  • {r.get('contract_name')}：{r.get('description')}（{r.get('days_until_due')} 天）")

    return "\n".join(parts) if parts else "✅ 暂无需要提醒的履约节点"
