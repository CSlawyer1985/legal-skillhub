#!/usr/bin/env python3
"""Contract Renewal Agent — manages the full contract renewal lifecycle."""

import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".openclaw" / "workspace" / "contract-renewal-agent" / "contracts.json"


def load_db() -> dict:
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return {"contracts": {}}
    with open(DB_PATH) as f:
        return json.load(f)


def save_db(db: dict) -> None:
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2, default=str)


def add_contract(name: str, counterparty: str, contract_type: str, start_date: str,
                 expiration_date: str, notice_window_days: int = 30, annual_value: float | None = None,
                 notes: str | None = None) -> dict:
    """Add a new contract."""
    db = load_db()
    contract_id = uuid.uuid4().hex[:8]

    today = datetime.now().date()
    try:
        exp_date = datetime.fromisoformat(expiration_date).date()
    except:
        return {"error": f"Invalid date format: {expiration_date}"}

    days_until = (exp_date - today).days

    if days_until < 0:
        status = "expired"
    elif days_until <= notice_window_days:
        status = "renewal_due"
    else:
        status = "active"

    contract = {
        "id": contract_id,
        "name": name,
        "counterparty": counterparty,
        "contract_type": contract_type,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "notice_window_days": notice_window_days,
        "annual_value": annual_value,
        "status": status,
        "days_until_expiry": days_until,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }

    db["contracts"][contract_id] = contract
    save_db(db)
    return contract


def list_contracts(status: str | None = None) -> list[dict]:
    """List contracts, optionally filtered by status."""
    db = load_db()
    contracts = list(db["contracts"].values())
    today = datetime.now().date()

    for c in contracts:
        try:
            exp_date = datetime.fromisoformat(c["expiration_date"]).date()
            c["days_until_expiry"] = (exp_date - today).days
        except:
            c["days_until_expiry"] = None

    if status:
        contracts = [c for c in contracts if c.get("status") == status]

    return sorted(contracts, key=lambda c: c.get("expiration_date", ""))


def get_contract(contract_id: str) -> dict:
    """Get a specific contract."""
    db = load_db()
    if contract_id not in db["contracts"]:
        return {"error": f"Contract {contract_id} not found"}
    return db["contracts"][contract_id]


def update_contract(contract_id: str, **updates) -> dict:
    """Update a contract."""
    db = load_db()
    if contract_id not in db["contracts"]:
        return {"error": f"Contract {contract_id} not found"}

    db["contracts"][contract_id].update(updates)
    db["contracts"][contract_id]["updated_at"] = datetime.now().isoformat()
    save_db(db)
    return db["contracts"][contract_id]


def delete_contract(contract_id: str) -> dict:
    """Delete a contract."""
    db = load_db()
    if contract_id not in db["contracts"]:
        return {"error": f"Contract {contract_id} not found"}

    contract = db["contracts"].pop(contract_id)
    save_db(db)
    return {"deleted": contract_id}


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "add":
        if len(args) < 5:
            print("Usage: add <name> <counterparty> <type> <start_date> <expiration_date> [annual_value] [notes]")
            return
        result = add_contract(
            name=args[0],
            counterparty=args[1],
            contract_type=args[2],
            start_date=args[3],
            expiration_date=args[4],
            annual_value=float(args[5]) if len(args) > 5 and args[5] != "-" else None,
            notes=args[6] if len(args) > 6 else None
        )
        print(json.dumps(result, indent=2, default=str))

    elif command == "list":
        status = args[0] if args else None
        contracts = list_contracts(status)
        print(json.dumps(contracts, indent=2, default=str))

    elif command == "get":
        if not args:
            print("Usage: get <contract_id>")
            return
        result = get_contract(args[0])
        print(json.dumps(result, indent=2, default=str))

    elif command == "update":
        if len(args) < 2:
            print("Usage: update <contract_id> <key=value> [key=value]...")
            return
        contract_id = args[0]
        updates = {}
        for arg in args[1:]:
            if "=" in arg:
                k, v = arg.split("=", 1)
                updates[k] = v
        result = update_contract(contract_id, **updates)
        print(json.dumps(result, indent=2, default=str))

    elif command == "delete":
        if not args:
            print("Usage: delete <contract_id>")
            return
        result = delete_contract(args[0])
        print(json.dumps(result, indent=2, default=str))

    elif command == "status":
        db = load_db()
        renewal_due = [c for c in db["contracts"].values() if c.get("status") == "renewal_due"]
        expired = [c for c in db["contracts"].values() if c.get("status") == "expired"]
        active = [c for c in db["contracts"].values() if c.get("status") == "active"]

        print(f"Contract Renewal Status:")
        print(f"  Active: {len(active)}")
        print(f"  Due for Renewal: {len(renewal_due)}")
        print(f"  Expired: {len(expired)}")

        if renewal_due:
            print(f"\n⚠️  Contracts due for renewal:")
            for c in renewal_due:
                print(f"  - {c['name']} ({c['counterparty']}) - expires {c['expiration_date']}")

    else:
        print(f"Unknown command: {command}")
        print_help()


def print_help():
    print("""Contract Renewal Agent

Commands:
  add <name> <counterparty> <type> <start> <expire> [value] [notes]
  list [status]
  get <id>
  update <id> <key=value> [key=value]...
  delete <id>
  status

Example:
  contract_renewal_agent.py add "Acme Contract" "Acme Corp" "Service" 2024-01-01 2025-12-31 50000 "Critical vendor"
  contract_renewal_agent.py list
  contract_renewal_agent.py status
""")


if __name__ == "__main__":
    main()
