"""
合同台账管理 - 存储模块
JSON 文件本地存储
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

STORAGE_DIR = Path(__file__).parent.parent / "data"
LEDGER_FILE = STORAGE_DIR / "contracts.json"


def init_storage():
    """初始化存储目录和文件"""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not LEDGER_FILE.exists():
        _write_ledger([])


def _read_ledger() -> list:
    """读取台账"""
    try:
        with open(LEDGER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_ledger(contracts: list):
    """写入台账"""
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(contracts, f, ensure_ascii=False, indent=2)


def add_contract(fields: dict) -> dict:
    """添加合同"""
    contracts = _read_ledger()
    contract = {
        "id": str(uuid.uuid4())[:8],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **fields,
        "reminders": []  # List of {days_before, enabled}
    }
    contracts.append(contract)
    _write_ledger(contracts)
    return contract


def get_contracts(
    status: Optional[str] = None,
    sort_by: str = "end_date",
    reverse: bool = True
) -> list:
    """获取合同列表"""
    contracts = _read_ledger()

    if status:
        contracts = [c for c in contracts if c.get("status") == status]

    # Sort
    contracts.sort(
        key=lambda x: x.get(sort_by, "" or "9999-12-31"),
        reverse=reverse
    )
    return contracts


def get_contract(contract_id: str) -> Optional[dict]:
    """获取单个合同"""
    contracts = _read_ledger()
    for c in contracts:
        if c.get("id") == contract_id:
            return c
    return None


def update_contract(contract_id: str, updates: dict) -> Optional[dict]:
    """更新合同"""
    contracts = _read_ledger()
    for i, c in enumerate(contracts):
        if c.get("id") == contract_id:
            contracts[i].update(updates)
            contracts[i]["updated_at"] = datetime.now().isoformat()
            _write_ledger(contracts)
            return contracts[i]
    return None


def delete_contract(contract_id: str) -> bool:
    """删除合同"""
    contracts = _read_ledger()
    original_len = len(contracts)
    contracts = [c for c in contracts if c.get("id") != contract_id]
    if len(contracts) < original_len:
        _write_ledger(contracts)
        return True
    return False


def add_reminder(contract_id: str, days_before: int, enabled: bool = True) -> bool:
    """添加提醒"""
    contract = get_contract(contract_id)
    if not contract:
        return False
    reminders = contract.get("reminders", [])
    reminders.append({"days_before": days_before, "enabled": enabled})
    update_contract(contract_id, {"reminders": reminders})
    return True


def remove_reminder(contract_id: str, index: int) -> bool:
    """移除提醒"""
    contract = get_contract(contract_id)
    if not contract:
        return False
    reminders = contract.get("reminders", [])
    if 0 <= index < len(reminders):
        reminders.pop(index)
        update_contract(contract_id, {"reminders": reminders})
        return True
    return False


def get_expiring_contracts(days: int = 7) -> list:
    """获取即将到期的合同"""
    contracts = _read_ledger()
    expiring = []
    now = datetime.now()
    for c in contracts:
        if c.get("status") == "已到期":
            continue
        end_date_str = c.get("end_date")
        if not end_date_str:
            continue
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            delta = (end_date - now).days
            if 0 <= delta <= days:
                c["days_until_expiry"] = delta
                expiring.append(c)
        except ValueError:
            continue
    return expiring


def count_contracts() -> int:
    """统计合同数量"""
    return len(_read_ledger())


def export_contracts(contracts: list, format: str = "csv") -> str:
    """导出合同数据"""
    if not contracts:
        return ""

    if format == "csv":
        return _export_csv(contracts)
    elif format == "json":
        return json.dumps(contracts, ensure_ascii=False, indent=2)
    else:
        return _export_csv(contracts)


def _export_csv(contracts: list) -> str:
    """导出为 CSV 格式"""
    if not contracts:
        return ""
    headers = ["id", "contract_name", "amount", "counterparty", "sign_date",
               "start_date", "end_date", "status", "key_nodes"]
    lines = [",".join(headers)]
    for c in contracts:
        row = [
            c.get("id", ""),
            c.get("contract_name", ""),
            str(c.get("amount", "")),
            c.get("counterparty", ""),
            c.get("sign_date", ""),
            c.get("start_date", ""),
            c.get("end_date", ""),
            c.get("status", ""),
            "|".join(c.get("key_nodes", []))
        ]
        lines.append(",".join(f'"{v}"' for v in row))
    return "\n".join(lines)


def _export_json(contracts: list) -> str:
    """导出为 JSON 格式"""
    return json.dumps(contracts, ensure_ascii=False, indent=2)
