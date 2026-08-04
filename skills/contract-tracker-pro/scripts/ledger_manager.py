"""
Contract Ledger Manager for Contract Tracker Pro
Manages local JSON-based contract ledger storage
"""

import json
import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Default ledger path (relative to skill directory, overridable via env)
DEFAULT_LEDGER_FILENAME = "contract_ledger.json"


def _get_ledger_path() -> Path:
    """Get the ledger file path."""
    # Allow override via environment variable
    env_path = os.environ.get("CONTRACT_TRACKER_LEDGER")
    if env_path:
        return Path(env_path)

    # Default: same directory as this script
    skill_dir = Path(__file__).parent.parent
    return skill_dir / DEFAULT_LEDGER_FILENAME


def _load_ledger() -> dict:
    """Load ledger from disk."""
    path = _get_ledger_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load ledger: {e}")
    return {"contracts": [], "metadata": {"version": "1.0", "created_at": _now_iso()}}


def _save_ledger(data: dict) -> None:
    """Save ledger to disk atomically."""
    path = _get_ledger_path()
    tmp_path = path.with_suffix(".tmp")

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Atomic rename
        tmp_path.replace(path)
        logger.debug(f"Ledger saved to {path}")

    except IOError as e:
        logger.error(f"Failed to save ledger: {e}")
        raise


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class LedgerManager:
    """
    Manages the contract ledger (CRUD operations on contracts and nodes).
    Thread-safe for single-process use.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        self._ledger_path = Path(ledger_path) if ledger_path else _get_ledger_path()

    # ─── Contract CRUD ─────────────────────────────────────────────────────────

    def add_contract(
        self,
        contract_name: str,
        nodes: list,
        contract_number: Optional[str] = None,
        sign_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        parties: Optional[dict] = None,
        penalty_clause: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Add a new contract to the ledger.

        Returns the created contract record.
        """
        ledger = _load_ledger()

        contract_id = str(uuid.uuid4())[:8]
        now = _now_iso()

        # Normalize nodes: ensure each has id and status
        normalized_nodes = []
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            node_id = node.get("id") or f"node-{i + 1}"
            normalized_nodes.append({
                "id": node_id,
                "type": node.get("type", "payment"),
                "description": node.get("description", ""),
                "amount": node.get("amount"),
                "due_date": node.get("due_date"),
                "status": "pending",  # pending / completed / overdue
                "completed_at": None,
                "raw_text": node.get("raw_text", ""),
            })

        contract = {
            "id": contract_id,
            "name": contract_name or "未命名合同",
            "number": contract_number,
            "sign_date": sign_date,
            "expiry_date": expiry_date,
            "parties": parties or {},
            "penalty_clause": penalty_clause,
            "summary": summary,
            "nodes": normalized_nodes,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
        }

        ledger["contracts"].append(contract)
        ledger["metadata"]["last_modified"] = now
        _save_ledger(ledger)

        logger.info(f"Contract added: {contract_id} ({contract_name})")
        return contract

    def get_contract(self, contract_id: str) -> Optional[dict]:
        """Get a contract by ID."""
        ledger = _load_ledger()
        for c in ledger.get("contracts", []):
            if c.get("id") == contract_id:
                return c
        return None

    def list_contracts(self, include_completed: bool = True) -> list:
        """
        List all contracts.
        Set include_completed=False to hide fully completed contracts.
        """
        ledger = _load_ledger()
        contracts = ledger.get("contracts", [])

        if not include_completed:
            contracts = [
                c for c in contracts
                if not all(n.get("status") == "completed" for n in c.get("nodes", []))
            ]

        return contracts

    def delete_contract(self, contract_id: str) -> bool:
        """Delete a contract. Returns True if deleted."""
        ledger = _load_ledger()
        original_len = len(ledger["contracts"])
        ledger["contracts"] = [c for c in ledger["contracts"] if c.get("id") != contract_id]

        if len(ledger["contracts"]) < original_len:
            ledger["metadata"]["last_modified"] = _now_iso()
            _save_ledger(ledger)
            logger.info(f"Contract deleted: {contract_id}")
            return True
        return False

    def update_contract(
        self,
        contract_id: str,
        updates: dict,
    ) -> Optional[dict]:
        """Update contract metadata (not nodes)."""
        ledger = _load_ledger()
        for c in ledger.get("contracts", []):
            if c.get("id") == contract_id:
                # Only update allowed fields
                allowed = ["name", "number", "sign_date", "expiry_date", "parties", "penalty_clause", "summary", "metadata"]
                for k, v in updates.items():
                    if k in allowed:
                        c[k] = v
                c["updated_at"] = _now_iso()
                ledger["metadata"]["last_modified"] = _now_iso()
                _save_ledger(ledger)
                return c
        return None

    # ─── Node Operations ───────────────────────────────────────────────────────

    def update_node_status(
        self,
        contract_id: str,
        node_id: str,
        status: str,  # pending / completed / overdue
    ) -> bool:
        """
        Update the status of a specific node.
        status: 'pending' | 'completed' | 'overdue'
        """
        if status not in {"pending", "completed", "overdue"}:
            raise ValueError(f"Invalid status: {status}")

        ledger = _load_ledger()
        for c in ledger.get("contracts", []):
            if c.get("id") == contract_id:
                for node in c.get("nodes", []):
                    if node.get("id") == node_id:
                        node["status"] = status
                        if status == "completed":
                            node["completed_at"] = _now_iso()
                        c["updated_at"] = _now_iso()
                        ledger["metadata"]["last_modified"] = _now_iso()
                        _save_ledger(ledger)
                        logger.info(f"Node {node_id} in contract {contract_id} set to {status}")
                        return True
        return False

    def mark_node_completed(self, contract_id: str, node_id: str) -> bool:
        """Convenience: mark a node as completed."""
        return self.update_node_status(contract_id, node_id, "completed")

    def get_node_status(
        self,
        contract_id: str,
        node_id: str,
    ) -> Optional[str]:
        """Get current status of a node."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None
        for node in contract.get("nodes", []):
            if node.get("id") == node_id:
                return node.get("status")
        return None

    # ─── Statistics ────────────────────────────────────────────────────────────

    def get_current_month_count(self) -> int:
        """Count contracts created this month."""
        ledger = _load_ledger()
        now = datetime.now(timezone.utc)
        year_month = (now.year, now.month)

        count = 0
        for c in ledger.get("contracts", []):
            created_at = c.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if (dt.year, dt.month) == year_month:
                        count += 1
                except (ValueError, TypeError):
                    pass
        return count

    def get_dashboard_stats(self) -> dict:
        """Get overall dashboard statistics."""
        ledger = _load_ledger()
        contracts = ledger.get("contracts", [])

        total_contracts = len(contracts)
        total_nodes = 0
        pending_nodes = 0
        completed_nodes = 0
        overdue_nodes = 0

        today = datetime.now(timezone.utc).date()

        for c in contracts:
            for node in c.get("nodes", []):
                total_nodes += 1
                status = node.get("status", "pending")
                if status == "completed":
                    completed_nodes += 1
                elif status == "overdue":
                    overdue_nodes += 1
                else:
                    pending_nodes += 1

        return {
            "total_contracts": total_contracts,
            "total_nodes": total_nodes,
            "pending_nodes": pending_nodes,
            "completed_nodes": completed_nodes,
            "overdue_nodes": overdue_nodes,
            "this_month_count": self.get_current_month_count(),
        }

    # ─── Export ────────────────────────────────────────────────────────────────

    def export_to_csv(self) -> str:
        """
        Export the full ledger to CSV format.
        Returns CSV string.
        """
        ledger = _load_ledger()
        lines = [
            "合同ID,合同名称,合同编号,节点ID,节点类型,节点描述,金额,截止日期,状态,完成时间,签署日期,到期日"
        ]

        for c in ledger.get("contracts", []):
            for node in c.get("nodes", []):
                amount = node.get("amount")
                amount_str = f"{amount:.2f}" if amount else ""
                lines.append(",".join([
                    _escape_csv(c.get("id", "")),
                    _escape_csv(c.get("name", "")),
                    _escape_csv(c.get("number", "") or ""),
                    _escape_csv(node.get("id", "")),
                    _escape_csv(node.get("type", "")),
                    _escape_csv(node.get("description", "")),
                    amount_str,
                    _escape_csv(node.get("due_date", "") or ""),
                    _escape_csv(node.get("status", "")),
                    _escape_csv(node.get("completed_at", "") or ""),
                    _escape_csv(c.get("sign_date", "") or ""),
                    _escape_csv(c.get("expiry_date", "") or ""),
                ]))

        return "\n".join(lines)


def _escape_csv(s: str) -> str:
    """Escape a string for CSV."""
    if s is None:
        return ""
    s = str(s)
    if "," in s or '"' in s or "\n" in s:
        return '"' + s.replace('"', '""') + '"'
    return s


# ─── Module-level convenience functions ──────────────────────────────────────

def add_contract(
    contract_name: str,
    nodes: list,
    **kwargs,
) -> dict:
    """Add a contract (module-level convenience)."""
    return LedgerManager().add_contract(contract_name, nodes, **kwargs)


def get_contract(contract_id: str) -> Optional[dict]:
    """Get a contract by ID."""
    return LedgerManager().get_contract(contract_id)


def list_contracts(include_completed: bool = True) -> list:
    """List all contracts."""
    return LedgerManager().list_contracts(include_completed)


def update_node_status(contract_id: str, node_id: str, status: str) -> bool:
    """Update node status."""
    return LedgerManager().update_node_status(contract_id, node_id, status)


def delete_contract(contract_id: str) -> bool:
    """Delete a contract."""
    return LedgerManager().delete_contract(contract_id)


def export_ledger_csv() -> str:
    """Export ledger to CSV string."""
    return LedgerManager().export_to_csv()
