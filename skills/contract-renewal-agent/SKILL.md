---
name: contract-renewal-agent
description: "Manage and track contract renewals. Track expiration dates, monitor renewal windows, and manage contract lifecycle. Stores all contract data locally in JSON database. No API keys required."
metadata:
  {
    "openclaw":
      {
        "emoji": "📋",
        "requires": {},
        "pricing": {
          "model": "free",
          "description": "Free to use. Data stored locally on your machine."
        },
      },
  }
---

# Contract Renewal Agent

An AI-powered agent that manages the full contract renewal lifecycle using Claude.

## What It Does

- **Track contracts** – store contract metadata, parties, terms, and expiration dates
- **Renewal reminders** – surfaces contracts due within configurable windows (30/60/90 days)
- **Analyze terms** – reads uploaded contract PDFs/text and extracts key renewal clauses
- **Draft proposals** – generates renewal proposals tailored to contract type and relationship history
- **Status tracking** – tracks each contract through: `active → renewal_due → negotiating → renewed | expired`

## How to Use

```
"What contracts are up for renewal in the next 60 days?"
"Add a contract: Acme Corp SaaS agreement, expires 2025-12-01, value $48,000/yr"
"Analyze this contract [upload PDF] and extract renewal terms"
"Draft a renewal proposal for the Acme Corp contract"
"Mark the Acme Corp contract as renewed at $52,000/yr"
```

## Running the Agent

The agent script is at `scripts/contract_renewal_agent.py`. Run it directly for CLI use, or invoke via this skill for interactive sessions:

```bash
python3 scripts/contract_renewal_agent.py
```

Or pass a task directly:

```bash
python3 scripts/contract_renewal_agent.py "What contracts are due for renewal this month?"
```

## Contract Database

Contracts are stored in `~/.openclaw/workspace/contract-renewal-agent/contracts.json`. Back this up regularly.

## Tools Available to the Agent

- `list_contracts` – list all contracts, optionally filtered by status or days-until-expiry
- `add_contract` – add a new contract with metadata
- `update_contract` – update contract status, value, notes, or renewal date
- `get_contract` – retrieve full details for a specific contract
- `analyze_contract_text` – extract key terms and dates from contract text
- `draft_renewal_proposal` – generate a renewal proposal for a contract
- `delete_contract` – remove a contract from tracking

## References

- `references/renewal_strategies.md` – negotiation strategies and renewal timing guidance
- `references/contract_templates.md` – renewal proposal templates by contract type
