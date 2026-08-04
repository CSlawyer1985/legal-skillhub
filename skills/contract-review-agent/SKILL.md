---
name: contract-review-agent
version: 1.0.0
description: >
  Contract clause analysis, risk flagging, renewal tracking, and obligation
  extraction for business agreements. Use when you need to review vendor
  contracts, service agreements, NDAs, SaaS subscriptions, or client
  engagement letters — identifying risky clauses, extracting key obligations,
  building renewal calendars, and generating executive summaries. Supports
  PDF and text input. NOT for legal advice, litigation strategy, or drafting
  new contracts from scratch (use a legal drafting tool for that). NOT for
  highly specialized agreements (M&A, securities, complex IP licensing) where
  licensed attorney review is mandatory.
tags:
  - contracts
  - legal
  - risk
  - compliance
  - finance
  - operations
---

# Contract Review Agent

Analyze contracts quickly: surface risky clauses, extract obligations, track renewals, and generate summaries — without replacing attorney review for high-stakes agreements.

---

## When to Use

- Reviewing vendor/supplier agreements before signing
- Auditing SaaS subscription terms (auto-renewal traps, data ownership, liability caps)
- Extracting obligations and deadlines from active contracts
- Building a contract renewal calendar
- Generating executive summaries for leadership review
- Flagging red-flag clauses (indemnification, limitation of liability, IP assignment)
- Comparing two contract versions for material changes

## When NOT to Use

- **Litigation strategy or legal advice** — always involve licensed counsel
- **M&A agreements, securities contracts, complex IP licensing** — specialized attorney required
- **Drafting new contracts from scratch** — use a legal drafting tool or attorney
- **Regulatory filings that require attorney signature** — out of scope
- **Final approval gate** — this tool surfaces issues; humans make binding decisions

---

## Key Capabilities

### 1. Clause Risk Analysis

Identify and score risky clauses across five risk categories:

| Category | Examples |
|---|---|
| **Financial** | Auto-renewal, price escalation, penalty clauses, payment terms |
| **Liability** | Indemnification scope, liability caps, consequential damages waivers |
| **Termination** | Notice periods, termination for convenience, cure periods |
| **IP & Data** | IP assignment, data ownership, confidentiality obligations |
| **Operational** | SLA commitments, exclusivity, non-compete, change-of-control |

Risk scores: 🔴 High / 🟡 Medium / 🟢 Low

---

### 2. Obligation Extraction

Pull structured obligation data from contract text:

```
OBLIGATIONS EXTRACTED
─────────────────────
Party: [Vendor/Client/Both]
Obligation: [Description]
Deadline/Frequency: [Date or recurring schedule]
Consequence of breach: [Penalty, termination right, etc.]
Owner (internal): [Department or role to assign]
```

---

### 3. Renewal & Deadline Calendar

Build a renewal tracker from extracted dates:

```
CONTRACT CALENDAR
─────────────────
Contract: [Name / Counterparty]
Effective Date: [Date]
Initial Term: [Duration]
Auto-Renewal: [Yes/No] — [X days notice to cancel]
⚠️  Cancel-by Date: [Date] — [X days from today]
Expiration: [Date]
Next Review: [Recommended review date]
```

Flag contracts where the cancel-by date is within 60 days.

---

### 4. Executive Summary Template

```
CONTRACT SUMMARY
────────────────
Agreement: [Type] — [Counterparty]
Date: [Effective] | Term: [Duration]
Value: [Contract value / annual spend]

KEY TERMS
• Payment: [Net 30/60, milestones, etc.]
• Liability cap: [Amount or formula]
• Termination: [Notice period, conditions]
• Auto-renewal: [Yes/No + notice window]

TOP RISKS (Flagged)
🔴 [Risk 1 — clause reference]
🟡 [Risk 2 — clause reference]

RECOMMENDED ACTIONS
1. [Action + owner + deadline]
2. [Action + owner + deadline]

ATTORNEY REVIEW NEEDED: [Yes/No — reason]
```

---

### 5. Contract Comparison (Redline Review)

When comparing two versions:
1. Identify added/removed/modified clauses
2. Flag material changes (financial impact, rights, obligations)
3. Summarize net change in risk profile
4. Highlight any clauses that were previously accepted and are now altered

---

## Workflow: Review a Contract

### Step 1 — Ingest

```bash
# PDF contract
pdf contract.pdf "Extract all clauses, obligations, dates, and parties"

# Or paste text directly into prompt
```

### Step 2 — Structured Extraction Prompt

```
Review this contract and provide:

1. PARTIES — Full legal names, roles (buyer/seller/licensor/etc.)
2. TERM — Effective date, duration, renewal terms, notice windows
3. FINANCIAL TERMS — Payment amounts, schedules, escalation clauses, penalties
4. OBLIGATIONS — All commitments by each party with deadlines
5. RISK FLAGS — Rank each flagged clause 🔴/🟡/🟢 with section reference
6. TERMINATION — How can each party exit? What are the conditions?
7. GOVERNING LAW — Jurisdiction, dispute resolution method
8. RECOMMENDED ACTIONS — What needs attorney review? What can be negotiated?

Format as structured sections. Be specific — include section numbers.
```

### Step 3 — Output Artifacts

- **Risk Register**: Spreadsheet row per risk (clause, category, severity, owner, action)
- **Obligation Log**: Task list with owners and due dates
- **Renewal Calendar**: Dates loaded into calendar system
- **Executive Summary**: 1-page PDF for leadership sign-off

---

## Common Red Flags by Contract Type

### SaaS/Software Agreements
- Auto-renewal with short cancel window (< 30 days notice)
- Data ownership vague or assigned to vendor
- Unlimited liability for IP infringement
- Unilateral price increase rights
- Broad "acceptable use" termination triggers

### Vendor/Supplier Agreements
- Price escalation tied to CPI or vendor discretion
- Indemnification that covers third-party claims broadly
- Exclusivity clauses limiting your options
- IP developed jointly assigned fully to vendor
- Termination fees that exceed remaining contract value

### Client Engagement Letters (Accounting/Finance)
- Scope of services defined too broadly (scope creep risk)
- Liability cap below engagement fee
- No limitation on client reliance on deliverables
- Governing law outside your state
- No clear change-order process

### NDAs
- One-sided (only you are bound)
- Perpetual term with no sunset
- Overly broad definition of "confidential information"
- No carve-outs for publicly available information
- Residuals clause allowing retained memory of disclosed info

---

## Contract Inventory Maintenance

Keep a running inventory. Recommended fields:

```
| Field | Description |
|---|---|
| contract_id | Unique internal ID |
| counterparty | Vendor/client legal name |
| contract_type | NDA / MSA / SOW / SaaS / Lease / etc. |
| effective_date | When it started |
| expiration_date | Hard end date |
| auto_renewal | Yes/No |
| cancel_by_date | Calculated: expiration - notice window |
| annual_value | Dollar amount |
| risk_score | 1-5 overall |
| owner | Internal owner (name/department) |
| location | File path or doc URL |
| last_reviewed | Date of last review |
| notes | Key flags or negotiation history |
```

---

## Integration with PrecisionLedger Workflows

- **AP/AR:** Cross-reference payment terms in contracts against actual invoice terms — flag discrepancies
- **Compliance Monitor:** Load contract obligations into compliance calendar alongside regulatory deadlines
- **Financial Reporting:** Flag contracts with contingent liabilities (indemnification, guarantees) for disclosure
- **Client Onboarding:** Use engagement letter checklist during new client setup
- **Budget Forecasting:** Extract contract escalation clauses to model future spend increases

---

## Escalation Rules

Always escalate to licensed attorney when:
- Contract value > $50,000
- Indemnification is unlimited or uncapped
- IP assignment affects core business assets
- Personal liability clauses (executive sign-off required)
- Governing law is outside your operating jurisdiction
- Any clause that waives statutory rights
- M&A, securities, or financing-related terms appear

---

## Example Run

**Input:** SaaS vendor agreement PDF

**Output:**
```
RISK SUMMARY — Acme SaaS Agreement (2026-03-15)
────────────────────────────────────────────────
🔴 HIGH: Auto-renewal — 7 days cancel notice only (§12.3)
   → Cancel-by date: 2026-03-22. ACTION: Decide NOW.

🔴 HIGH: Data ownership — "all data processed becomes vendor property" (§8.1)
   → Unacceptable. Negotiate or reject.

🟡 MEDIUM: Liability cap — capped at 1 month fees (§15.2)
   → Low coverage for a $24k/year contract. Push for 12 months.

🟡 MEDIUM: Price escalation — up to 15% annual increase, no notice required (§5.4)
   → Budget risk. Request 30-day notice + cap at CPI.

🟢 LOW: Governing law — Texas (§20.1)
   → Acceptable, matches our jurisdiction.

OBLIGATIONS (Your side):
• Pay net-30 from invoice date (§5.1) — Finance/AP
• Provide access credentials within 5 business days of signing (§3.2) — IT
• Report data breaches within 24 hours (§9.4) — Security/Compliance

ATTORNEY REVIEW: YES — §8.1 data ownership clause is non-standard and high-risk.
```
