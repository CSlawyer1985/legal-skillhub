# Contract Smart Compare

**Skill ID:** contract-compare  
**Version:** 1.0.0

---

## Overview

Contract Smart Compare is an AI-powered contract document comparison tool. It automatically identifies and highlights clause-level differences between two or more contract documents, generating structured diff reports.

## Core Features

1. **Smart Clause Extraction**
   - Automatically identifies numbered clauses (Article X, Section X, etc.)
   - Supports PDF, DOCX, TXT formats
   - OCR for image scans (STANDARD+)

2. **Precise Difference Detection**
   - Clause-by-clause comparison: Article X → Original → New
   - Three categories: New / Deleted / Modified
   - Multi-version timeline (PRO)

3. **AI Risk Assessment** (PRO)
   - Automatic legal risk level (High/Medium/Low)
   - Focus: liability, breach, payment clause changes

4. **Key Clause Summary** (PRO)
   - AI-powered core clause extraction
   - Quickly understand key changes per version

5. **Multi-format Export**
   - Markdown diff report (all tiers)
   - Excel diff list (STANDARD+)
   - Risk summary report (PRO)

---

## Pricing

| Tier | Monthly | Features |
|------|---------|---------|
| FREE | Free | 5 uses/month, 2-file compare (TXT/DOCX), Markdown |
| STANDARD | ¥29/mo | Unlimited, PDF/image OCR, diff classification, Excel |
| PRO | ¥99/mo | STANDARD + multi-version (3+), risk assessment, key summaries |

---

## Usage

### Compare Two Contracts

```bash
python -m src.main compare contract_a.pdf contract_b.pdf \
  --label-a "Version 1" --label-b "Version 2" -o diff_report.md
```

### Multi-version Compare (PRO)

```bash
python -m src.main multi v1.pdf v2.pdf v3.pdf \
  --labels "Draft" "Revised" "Final" \
  --dates "2024-01-01" "2024-03-15" "2024-06-01" \
  --output report.md --excel
```

### Parse Contract Text

```bash
python -m src.main parse contract.pdf --max-chars 3000
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| OPENAI_API_KEY | OpenAI API Key | One of |
| ANTHROPIC_API_KEY | Anthropic API Key | One of |
| CONTRACT_COMPARE_TOKEN | Monthly subscription token | STANDARD/PRO |

---

## Supported File Types

| Format | FREE | STANDARD | PRO |
|--------|------|----------|-----|
| TXT | ✅ | ✅ | ✅ |
| DOCX | ✅ | ✅ | ✅ |
| PDF | ❌ | ✅ | ✅ |
| JPG/PNG (OCR) | ❌ | ✅ | ✅ |

---

## Tech Stack

- **PDF:** PyMuPDF + pdfplumber
- **Word:** python-docx
- **Encoding:** chardet
- **OCR:** pytesseract + Pillow
- **AI:** OpenAI GPT-4o / Anthropic Claude (user-provided Key)
- **Excel:** openpyxl

---

## Security

- Files stored in `/tmp/contract-compare/` (temp directory)
- API Keys are user-provided, not stored
- Strict path sanitization
- 10-second timeout on all HTTP requests

---

## Subscription

STANDARD/PRO users configure `CONTRACT_COMPARE_TOKEN` (prefix: `CONTRACT-COMPARE-*`), validated via yk-global API.

---

*For paid plans, visit [YK-Global.com](https://yk-global.com)*
