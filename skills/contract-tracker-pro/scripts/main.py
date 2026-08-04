"""
Contract Tracker Pro — Main Entry Point
Unified interface for all contract tracking operations.
"""

import logging
from typing import Optional

from .token_validator import TokenValidator, verify_token, TierConfig
from .pdf_extractor import extract_text, get_page_count
from .ai_extractor import extract_contract_nodes, extract_contract_nodes_from_pdf
from .ledger_manager import (
    LedgerManager,
    add_contract,
    get_contract,
    list_contracts,
    update_node_status,
    delete_contract,
    export_ledger_csv,
)
from .reminder_checker import (
    check_reminders,
    get_pending_reminders,
    build_reminder_message,
    format_reminders_batch,
    compute_status,
)
from .feishu_notifier import (
    build_reminder_card,
    build_reminder_summary_card,
    prepare_reminder_notification,
    prepare_summary_notification,
)

logger = logging.getLogger(__name__)


# ─── Core User-Facing Functions ───────────────────────────────────────────────


def add_contract_from_pdf(
    pdf_path: str,
    api_key: str,
    ai_api_key: str,
    ai_base_url: str = "https://api.openai.com/v1",
    ai_model: str = "gpt-4o-mini",
) -> dict:
    """
    Add a contract from a PDF file: extract nodes via AI, store in ledger.

    Args:
        pdf_path: Path to contract PDF
        api_key: CONT-TRACK-* token for tier validation
        ai_api_key: User's AI model API key
        ai_base_url: AI API base URL
        ai_model: AI model name

    Returns:
        Result dict with:
        - success: bool
        - contract: contract record (if success)
        - tier_config: TierConfig used
        - error: error message (if failed)
    """
    # Step 1: Token validation + tier limit check
    tier_config = verify_token(api_key)
    from .ledger_manager import LedgerManager
    lm = LedgerManager()
    count = lm.get_current_month_count()
    limit = tier_config.contracts_per_month
    if count >= limit:
        return {
            "success": False,
            "error": f"已达当月合同上限（{limit}个），请下月重试或升级套餐",
            "tier_config": tier_config,
            "contract": None,
        }

    # Step 2: Extract text from PDF
    text = extract_text(pdf_path)
    page_count = get_page_count(pdf_path)
    logger.info(f"PDF extracted: {len(text)} chars, {page_count} pages")

    # Step 3: AI extract nodes
    extracted = extract_contract_nodes(
        contract_text=text,
        api_key=ai_api_key,
        base_url=ai_base_url,
        model=ai_model,
    )

    # Step 4: Add to ledger
    contract = add_contract(
        contract_name=extracted.get("contract_name") or pdf_path.split("/")[-1].replace(".pdf", ""),
        contract_number=extracted.get("contract_number"),
        sign_date=extracted.get("sign_date"),
        expiry_date=extracted.get("expiry_date"),
        parties=extracted.get("parties"),
        penalty_clause=extracted.get("penalty_clause"),
        summary=extracted.get("summary"),
        nodes=extracted.get("nodes", []),
        metadata={
            "source": "pdf",
            "pdf_path": pdf_path,
            "page_count": page_count,
            "text_length": len(text),
            "tier": tier_config.tier,
        },
    )

    return {
        "success": True,
        "contract": contract,
        "tier_config": tier_config,
        "extracted": extracted,
        "page_count": page_count,
        "text_length": len(text),
    }


def add_contract_from_text(
    contract_text: str,
    contract_name: str,
    api_key: str,
    ai_api_key: str,
    ai_base_url: str = "https://api.openai.com/v1",
    ai_model: str = "gpt-4o-mini",
    sign_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    parties: Optional[dict] = None,
    manual_nodes: Optional[list] = None,
) -> dict:
    """
    Add a contract from raw text (or with manually provided nodes).

    Args:
        contract_text: Full or partial contract text
        contract_name: Name/title for the contract
        api_key: CONT-TRACK-* token
        ai_api_key: AI API key
        ai_base_url: AI API base URL
        ai_model: AI model
        sign_date: Override sign date
        expiry_date: Override expiry date
        parties: Override parties dict
        manual_nodes: If provided, skip AI extraction and use these nodes directly

    Returns:
        Same as add_contract_from_pdf
    """
    # Token validation
    tier_config = verify_token(api_key)

    if manual_nodes is not None:
        # Use manually provided nodes (skip AI extraction)
        nodes = manual_nodes
        extracted = {"nodes": nodes, "summary": "手动录入"}
    else:
        # AI extraction
        extracted = extract_contract_nodes(
            contract_text=contract_text,
            api_key=ai_api_key,
            base_url=ai_base_url,
            model=ai_model,
        )
        nodes = extracted.get("nodes", [])

    contract = add_contract(
        contract_name=contract_name,
        contract_number=None,
        sign_date=sign_date or extracted.get("sign_date"),
        expiry_date=expiry_date or extracted.get("expiry_date"),
        parties=parties or extracted.get("parties"),
        penalty_clause=extracted.get("penalty_clause"),
        summary=extracted.get("summary"),
        nodes=nodes,
        metadata={
            "source": "text",
            "text_length": len(contract_text),
            "tier": tier_config.tier,
        },
    )

    return {
        "success": True,
        "contract": contract,
        "tier_config": tier_config,
        "extracted": extracted,
    }


def check_and_notify(
    api_key: str,
    feishu_webhook: Optional[str] = None,
    contract_id: Optional[str] = None,
) -> dict:
    """
    Check pending reminders and optionally send Feishu notification.

    This function prepares the notification data — the agent must actually
    send it via feishu_im_user_message tool.

    Args:
        api_key: CONT-TRACK-* token
        feishu_webhook: Optional Feishu webhook URL
        contract_id: Optional, check specific contract only

    Returns:
        dict with:
        - reminders: list of reminder dicts
        - summary_text: formatted summary
        - notifications: list of prepared notification dicts (card + text)
        - should_notify: bool
    """
    # Refresh token validation (verify cached)
    tier_config = verify_token(api_key)

    reminders = check_reminders(contract_id=contract_id)

    notifications = []
    for r in reminders:
        notifications.append(prepare_reminder_notification(r))

    summary_text = format_reminders_batch(reminders)

    return {
        "reminders": reminders,
        "reminder_count": len(reminders),
        "summary_text": summary_text,
        "notifications": notifications,
        "should_notify": len(reminders) > 0,
        "tier_config": tier_config,
        "tier_display": tier_config.tier,
    }


def get_contract_status(contract_id: str) -> dict:
    """
    Get full status of a contract and its nodes.

    Returns:
        dict with contract info, nodes with computed status, and stats
    """
    contract = get_contract(contract_id)
    if not contract:
        return {"error": f"Contract {contract_id} not found"}

    today = __import__("datetime").date

    updated_nodes = []
    for node in contract.get("nodes", []):
        effective = compute_status(node.get("due_date", ""), node.get("status", "pending"))
        updated_nodes.append({**node, "effective_status": effective})

    return {
        "contract": {**contract, "nodes": updated_nodes},
        "stats": {
            "total": len(updated_nodes),
            "completed": len([n for n in updated_nodes if n.get("effective_status") == "completed"]),
            "overdue": len([n for n in updated_nodes if n.get("effective_status") == "overdue"]),
            "pending": len([n for n in updated_nodes if n.get("effective_status") == "pending"]),
        },
    }


def mark_node_done(contract_id: str, node_id: str) -> dict:
    """Mark a node as completed."""
    success = update_node_status(contract_id, node_id, "completed")
    if success:
        contract = get_contract(contract_id)
        node = next((n for n in contract.get("nodes", []) if n.get("id") == node_id), None)
        return {"success": True, "contract": contract, "node": node}
    return {"success": False, "error": "Node not found or already completed"}


def export_contracts(api_key: str, format: str = "csv") -> dict:
    """
    Export contract ledger.

    Args:
        api_key: CONT-TRACK-* token (validates tier)
        format: 'csv' or 'json'

    Returns:
        dict with:
        - success: bool
        - data: exported data as string
        - tier: user tier
        - stats: dashboard stats
    """
    tier_config = verify_token(api_key)

    lm = LedgerManager()
    stats = lm.get_dashboard_stats()

    if format == "csv":
        data = export_ledger_csv()
    else:
        import json
        contracts = lm.list_contracts()
        data = json.dumps({"contracts": contracts, "stats": stats}, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "data": data,
        "format": format,
        "tier": tier_config.tier,
        "tier_display": tier_config.tier,
        "stats": stats,
    }
