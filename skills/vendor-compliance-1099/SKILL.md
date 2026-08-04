---
name: vendor-compliance-1099
description: >
  1099 vendor compliance pipeline for accounting firms. Pulls full-year General Ledger from QBO,
  aggregates vendor payments, applies IRS $600 threshold, classifies 1099-NEC vs 1099-MISC,
  checks corporate exemptions, tracks W-9 and TIN status, filters credit card payments (1099-K
  handled by processor), calculates late-filing penalties, and produces year-over-year CDC.
  Outputs an 8-tab Excel workbook. Use for year-end 1099 compliance runs, W-9 tracking, and
  IRS threshold checks. NOT for payroll W-2, 1042-S foreign withholding, or 1099-K reconciliation.
version: 1.0.0
author: samledger67
tags:
  - finance
  - accounting
  - tax
  - 1099
  - compliance
  - vendor-management
  - QBO
updated: 2026-03-18
---

# Skill: vendor-compliance-1099

## Description
1099 vendor compliance pipeline for accounting firms. Pulls the full-year General Ledger from QBO, aggregates vendor payments by name, applies IRS $600 threshold, classifies 1099-NEC vs 1099-MISC, checks corporate exemptions, tracks W-9 and TIN status, filters credit card payments (1099-K handled by processor), calculates late-filing penalties, and produces a year-over-year CDC. Outputs an 8-tab Excel workbook.

**Trigger phrases:** "run 1099 compliance," "vendor 1099 check," "pull 1099 list," "who needs a 1099," "1099 vendor scan," "W-9 tracker," "1099-NEC list," "1099-MISC list"

**NOT for:** payroll W-2 compliance, 1042-S foreign withholding, 1099-K reconciliation (CC processor), or non-US entities.

---

## Pipeline Location
```
scripts/pipelines/vendor-compliance-1099.py
```

## Usage

```bash
# Standard run
python3 scripts/pipelines/vendor-compliance-1099.py --slug my-client --year 2025

# QBO sandbox
python3 scripts/pipelines/vendor-compliance-1099.py --slug my-client --year 2025 --sandbox

# Custom output directory
python3 scripts/pipelines/vendor-compliance-1099.py --slug my-client --year 2025 --out ~/Desktop/1099s

# Skip GL pull (empty vendor list — testing only)
python3 scripts/pipelines/vendor-compliance-1099.py --slug my-client --year 2025 --skip-gl
```

**Arguments:**
| Flag | Required | Default | Notes |
|------|----------|---------|-------|
| `--slug` | ✅ | — | QBO client slug |
| `--year` | ✅ | — | Tax year (e.g. 2025) |
| `--sandbox` | ❌ | false | Use QBO sandbox |
| `--skip-gl` | ❌ | false | Skip GL pull (empty output — testing only) |
| `--out` | ❌ | ~/Desktop | Output directory |

---

## Output: 8-Tab Excel Workbook

| Tab | Contents |
|-----|----------|
| **Vendor Summary** | All vendors: total paid, ACH/check/wire vs CC split, form type, corp exempt flag, action required |
| **1099-NEC List** | Contractors/service vendors ≥$600 (reportable amount only), W-9 status, TIN status, action |
| **1099-MISC List** | Rent, royalties, prizes ≥$600 with MISC box classification (Box 1/2/3/6/10) |
| **Exemptions** | Corp-flagged vendors (LLC/Inc/Corp/Ltd) requiring manual entity-type verification before skipping 1099 |
| **W-9 Tracker** | Per-vendor W-9 received/pending/missing status; persisted between runs; editable date/TIN fields |
| **Payment Methods** | ACH/check/wire vs. credit card split per vendor; CC excluded from 1099 reportable amount |
| **Penalties Calc** | IRC §6721/6722 penalty scenarios: on-time, 15/30/45/60/90 days late + today's actual exposure |
| **CDC Log** | New vendors (not in prior year), dropped vendors, amount changes ≥10% or ≥$500 YoY |

**Output filename:** `VendorCompliance_1099_{slug}_{year}.xlsx`

---

## Key IRS Rules Implemented

### $600 Threshold
- Applied to **ACH/check/wire amounts only** — credit card payments excluded (processor files 1099-K)
- Threshold is per-vendor, full calendar year aggregate

### 1099 Type Classification
| Form | When | Keyword triggers |
|------|------|-----------------|
| **1099-NEC** | Non-employee compensation: contractors, consultants, attorneys, sole proprietors | contractor, freelance, consultant, attorney, repair, cleaning, design, etc. |
| **1099-MISC** | Rent, royalties, prizes, medical payments | rent, royalty, prize, award, medical, healthcare |

**Default is 1099-NEC** — NEC is assumed for all service payments unless account/memo indicates MISC category.

### Corporate Exemption
- Vendor names matching `LLC|Inc|Corp|Ltd|Co.|Company|etc.` → flagged as **potentially exempt**
- Still appear in Exemptions tab for manual verification
- **Exception — always file regardless of entity type:**
  - Attorneys (IRC §6045(f)) → 1099-NEC
  - Medical providers → 1099-MISC Box 6

### Payment Method Filter
- **Credit card keywords** in memo/txn_type/split → classified as CC, excluded from reportable amount
- **ACH/check/wire** → included in reportable amount
- Unclassified payments → included (conservative — better to over-report)

### W-9 & TIN Tracking
- W-9 status persisted at `.cache/vendor-compliance-1099/{slug}-w9.json`
- New vendors auto-default to `NO` status
- TIN status persisted at `.cache/vendor-compliance-1099/{slug}-tin.json`
- **Backup withholding:** 24% applies if vendor fails to provide valid TIN

---

## Filing Deadlines

| Form | Recipient Copy | IRS Paper | IRS e-File |
|------|---------------|-----------|-----------|
| 1099-NEC | January 31 | January 31 | January 31 |
| 1099-MISC (Box 7) | January 31 | January 31 | January 31 |
| 1099-MISC (other boxes) | January 31 | February 28 | March 31 |

**e-File required** if filing 10+ information returns.

---

## Penalty Rates (IRC §6721/6722 — 2024)

| Days Late | Per Form | Small Biz Annual Cap |
|-----------|----------|---------------------|
| ≤30 days | $60 | $232,500 |
| 31–60 days | $120 | $664,500 |
| >60 days | $310 | $1,329,000 |
| Intentional disregard | $630 minimum | No cap |

Small business = avg annual gross receipts ≤$5M for 3 prior years.

---

## Cache Files

| File | Purpose |
|------|---------|
| `.cache/vendor-compliance-1099/{slug}-{year}.json` | YoY snapshot for CDC (auto-saved each run) |
| `.cache/vendor-compliance-1099/{slug}-{year-1}.json` | Prior year snapshot for comparison |
| `.cache/vendor-compliance-1099/{slug}-w9.json` | W-9 status (persisted, editable manually) |
| `.cache/vendor-compliance-1099/{slug}-tin.json` | TIN status (persisted, editable manually) |

**Updating W-9 status manually:**
```bash
# Edit cache file directly to update W-9 status
cat .cache/vendor-compliance-1099/my-client-w9.json
# Modify "VendorName": "YES" | "NO" | "PENDING"
# Then re-run pipeline — status will be loaded automatically
```

---

## Integration Requirements

- **QBO Client:** Node.js QBO client (auth token must be set)
- **Python packages:** `pip install openpyxl`
- **GL access required:** Pipeline reads full-year GL — ensure QBO auth has GL report access
- **No write access to QBO** — read-only integration

---

## Decimal Math

All financial calculations use Python `Decimal` with `ROUND_HALF_UP` at 2 decimal places. No float arithmetic. Same pattern as `tax-package-prep.py` and `pl-deep-analysis.py`.

---

## When NOT to Use This Skill

- **Payroll / W-2 compliance** → separate payroll workflow
- **1099-K reconciliation** → CC processor provides (not Sam's responsibility)
- **Foreign vendor withholding** → Form 1042-S, different rules
- **State-level 1099 filing** → varies by state, not covered here
- **1099-INT / 1099-DIV / 1099-B** → investment/bank-issued, not vendor compliance

---

## Workflow Checklist

Run this pipeline as part of year-end close:

1. **November/December:** Pre-screen — run pipeline to identify missing W-9s before year-end
2. **January (early):** Final run — full year GL aggregation
3. **January 15:** W-9 collection deadline (internal)
4. **January 25:** Prepare and review filings
5. **January 31:** File 1099-NEC (recipient + IRS)
6. **February 28 / March 31:** File 1099-MISC (IRS paper/e-file)

---

