# Contract Risk Analyzer

Upload contract PDF → AI auto-extracts key clauses → risk highlights → structured risk report.

**No legal judgment — only structured extraction and risk annotation.**

---

## Supported Contract Types

| Type | Description |
|------|-------------|
| Purchase | Procurement of goods/services |
| Sales | Product/service sales |
| Service | Delegation/outsourcing |
| Labor | Employment/labor contracts |
| Lease | Asset/property rental |
| NDA | Non-disclosure/competition agreements |

---

## Key Features

- **Auto type detection** — 6 contract types auto-identified
- **Dual extraction engine** — PyMuPDF + pdfplumber for complete text extraction
- **Three-tier risk annotation** — 🔴 High 🟠 Medium 🟡 Low
- **Feishu card push** — Report auto-sent to Feishu after generation
- **Multi-format support** — PDF / plain text / direct paste

---

## Quick Start

```python
from scripts.main import analyze_contract

result = analyze_contract(
    pdf_path="/path/to/contract.pdf",
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-4o-mini",
    user_focus="payment cycle and breach liability",
)

print(result["report_markdown"])      # Full risk report
print(result["risk_summary"])         # {"🔴": 2, "🟠": 1, "🟡": 0}
```

---

## Pricing

| Tier | Price | Contracts/Mo | Features |
|------|-------|:------------:|----------|
| Free | ¥0 | 3/mo | Basic risk annotation, text summary |
| Standard | ¥29/mo | 30/mo | 6 contract types, Excel report |
| Pro | ¥99/mo | 200/mo | Batch processing, risk comparison |
| Max | ¥299/mo | Unlimited | API priority |

---

> For paid plans, visit [YK-Global.com](https://yk-global.com)
