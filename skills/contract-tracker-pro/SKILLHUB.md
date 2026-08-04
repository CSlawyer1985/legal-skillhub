# Contract Tracker Pro

**Slug:** `contract-tracker-pro`
**Name:** Contract Tracker Pro
**Category:** Productivity / Document Management
**Tags:** `contract`, `tracking`, `PDF`, `AI`, `payment-nodes`, `delivery-dates`, `reminder`, `feishu`

---

## Description

Upload contract PDF → AI automatically extracts payment milestones, delivery dates, and expiry dates → Builds a contract ledger with Feishu reminders.

**Contract Status:** 🟡 Pending / 🟢 Completed / 🔴 Overdue

---

## Features

- **PDF Upload** — Upload contract PDF or paste text for AI field extraction
- **AI Field Extraction** — Automatically extracts: contract name/number, sign date, payment nodes, delivery milestones, expiry date, penalty clauses
- **Contract Ledger** — Local JSON storage with CSV export
- **Feishu Reminders**:
  - 3 days before deadline
  - On the deadline day
  - Daily overdue alerts until marked complete
- **Token Verification** — 4-tier system (Free/Standard/Pro/Max) with 5-minute cache

---

## Workflow

1. User uploads contract PDF (or pastes text)
2. AI automatically extracts: contract name/number, sign date, payment milestones, delivery dates, expiry date, penalty clauses
3. Creates contract ledger (local JSON, exportable to CSV)
4. Feishu push notifications for reminders

---

## Pricing

| Tier | Price | Contracts/Mo | Features |
|------|-------|:------------:|----------|
| **Free** | ¥0 | 3 | PDF parsing, basic reminders |
| **Standard** | ¥29/mo | 20 | Text + PDF, all reminder types |
| **Pro** | ¥99/mo | 100 | CSV export, overdue analysis |
| **Max** | ¥299/mo | Unlimited | Advanced reports, dashboard |

---

## Contract Status

| Status | Meaning |
|--------|---------|
| 🟡 Pending | Deadline not yet reached |
| 🟢 Completed | Manually marked done |
| 🔴 Overdue | Past deadline, not completed |

---

## Milestone Types

- **Payment milestones** — Amount + due date
- **Delivery milestones** — Content + due date
- **Contract expiry** — Final deadline
- **Penalty clauses** — Amount or percentage

---

## Requirements

### System Requirements
- Python 3.8+
- Internet access (for AI API calls)
- PDFplumber or PyPDF2 for PDF text extraction

### Python Dependencies
```
pdfplumber>=0.10.0
# or
PyPDF2>=3.0.0
requests>=2.28.0
```

---

## Quick Start

```python
from scripts.main import add_contract_from_pdf

result = add_contract_from_pdf(
    pdf_path="/path/to/contract.pdf",
    api_key="CONT-TRACK-xxxxx",
    ai_api_key="sk-xxxxx",
    ai_base_url="https://api.openai.com/v1",
    ai_model="gpt-4o-mini",
)

if result["success"]:
    contract = result["contract"]
    print(f"Contract added: {contract['name']}, {len(contract['nodes'])} milestones")
```

---

## Reminder Rules

| Scenario | Trigger |
|----------|---------|
| Advance reminder | 3 days before deadline |
| Day-of reminder | On deadline day |
| Overdue reminder | Daily until marked complete |

---

## Token Verification

- **Endpoint**: `POST https://api.yk-global.com/v1/verify`
- **Header**: `Authorization: Bearer {api_key}`
- **Body**: `{}`
- **Response**: Check `valid` field
- **Fallback**: Network error → FREE tier, no blocking
- **Cache**: 5-minute TTL

---

## Configuration

| Parameter | Description |
|-----------|-------------|
| `api_key` | Token (format: `CONT-TRACK-*`) |
| `ai_api_key` | AI model API key (OpenAI-compatible) |
| `ai_base_url` | AI API URL (optional, defaults to OpenAI) |
| `ai_model` | Model name (optional, defaults to `gpt-4o-mini`) |
| `feishu_webhook` | Feishu bot Webhook URL (optional) |

---

## File Structure

```
contract-tracker-pro/
├── SKILL.md              # Skill definition
├── README.md             # Documentation
├── SKILLHUB.md          # Tencent Skillhub listing (this file)
├── requirements.txt     # Python dependencies
├── references/
│   └── changelog.md      # Changelog
└── scripts/
    ├── __init__.py
    ├── main.py           # Main entry point
    ├── pdf_extractor.py   # PDF text extraction
    ├── ai_extractor.py    # AI field extraction
    ├── ledger_manager.py  # Contract ledger management
    ├── reminder_checker.py # Reminder checking logic
    ├── token_validator.py # Token verification
    └── feishu_notifier.py  # Feishu push notifications
```

---

## Data Storage

- **Location**: `contract_ledger.json` (same directory as scripts)
- **Custom path**: Set via `CONTRACT_TRACKER_LEDGER` environment variable
- **Format**: JSON, exportable to CSV (Pro+ tiers)

---

## License

Proprietary — YK Global

> For paid plans, visit [YK-Global.com](https://yk-global.com)
