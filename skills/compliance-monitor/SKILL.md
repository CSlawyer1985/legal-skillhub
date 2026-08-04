---
name: compliance-monitor
version: 1.0.0
description: >
  Regulatory change tracking, filing deadline management, audit prep checklists, and compliance
  calendar maintenance for accounting and finance firms. Use when you need to track IRS/state
  deadlines, monitor regulatory updates (GAAP, FASB, IRS, state tax), prepare audit checklists,
  or manage client compliance calendars. NOT for legal advice, securities compliance (SEC/FINRA),
  or tax preparation itself — use a tax specialist for actual filing work.
metadata:
  openclaw:
    tags: [finance, compliance, accounting, regulatory, audit, deadlines]
    author: PrecisionLedger
    channel: any
---

# Compliance Monitor Skill

Regulatory tracking, deadline management, and audit prep for accounting and finance firms.

## When to Use

- Tracking federal and state tax filing deadlines for clients
- Monitoring GAAP/FASB/IRS regulatory changes that affect client engagements
- Generating audit preparation checklists
- Managing compliance calendars and sending deadline reminders
- Flagging upcoming obligations across a client portfolio

## When NOT to Use

- **Actual tax preparation or filing** — use a tax professional and licensed software
- **Securities/investment compliance** (SEC, FINRA, CFTC) — out of scope
- **Legal advice** — always escalate to counsel
- **Real-time regulatory databases** — this skill uses web search + known sources; always verify with primary sources
- **International compliance** outside US federal/state — limited coverage

---

## Core Capabilities

### 1. Filing Deadline Tracking

Track key IRS and common state filing deadlines:

```
Key Federal Deadlines (Tax Year 2025):
- Jan 15: Q4 estimated tax payment (Form 1040-ES)
- Jan 31: W-2 / 1099-NEC / 1099-MISC employer filing
- Feb 28: Paper 1099 information returns to IRS
- Mar 17: S-Corp / Partnership returns (1120-S, 1065) — or 6-month extension
- Apr 15: Individual (1040), C-Corp (1120), FBAR (FinCEN 114), Gift Tax (709)
- Apr 15: Q1 estimated tax payment
- Jun 16: Q2 estimated tax payment
- Sep 15: Q3 estimated tax payment; extended S-Corp/Partnership returns
- Oct 15: Extended individual and C-Corp returns
- Dec 31: Year-end planning cutoff (retirement contributions, charitable gifts, etc.)
```

To look up a specific deadline or extension:
1. Use `web_search` with query: `"[form number] [tax year] due date IRS"` or `"[state] [entity type] filing deadline [year]"`
2. Cross-reference with IRS.gov Tax Calendar: https://www.irs.gov/businesses/small-businesses-self-employed/online-tax-calendar

### 2. Regulatory Change Monitoring

Monitor for updates from key sources:

**Federal Sources:**
- IRS Newsroom: https://www.irs.gov/newsroom
- FASB Standards Updates (ASUs): https://www.fasb.org/page/PageContent?pageId=/standards/accounting-standards-updates.html
- AICPA Standards: https://www.aicpa-cima.com/resources/landing/professional-standards
- Federal Register (tax regs): https://www.federalregister.gov/agencies/internal-revenue-service

**Search Pattern:**
```
web_search: "IRS [topic] [year] update" OR "FASB ASU [year] [topic]" OR "GAAP change [year] [industry]"
```

**What to watch for:**
- New or revised tax forms
- Rate/threshold changes (standard deduction, contribution limits, depreciation tables)
- New reporting requirements (e.g., 1099-K threshold changes, digital asset reporting)
- FASB ASUs affecting client financials (revenue recognition, lease accounting, credit losses)
- State conformity with federal changes

### 3. Audit Preparation Checklists

#### Financial Statement Audit Checklist

**Pre-Audit (60-90 days before fieldwork):**
- [ ] Confirm audit scope and materiality thresholds with engagement partner
- [ ] Update permanent file: entity structure, key contracts, related parties
- [ ] Request client PBC (Provided By Client) document list
- [ ] Confirm trial balance tie to prior year audited financials
- [ ] Identify significant accounting estimates (impairment, reserves, fair value)
- [ ] Update risk assessment — new systems, transactions, personnel changes

**PBC Document Request List (standard):**
- [ ] General ledger (full year)
- [ ] Bank statements and reconciliations (all accounts)
- [ ] AR aging schedule and subledger
- [ ] AP aging schedule and subledger
- [ ] Fixed asset register with additions/disposals
- [ ] Debt agreements, schedules, and confirmation responses
- [ ] Lease agreements (ASC 842 schedules)
- [ ] Payroll records and tax filings (941s, W-3)
- [ ] Entity formation docs, minutes, and resolutions
- [ ] Related party transaction schedule
- [ ] Significant contracts entered/modified during year
- [ ] Insurance policies and certificates
- [ ] Prior year audit report and management letter

**Fieldwork:**
- [ ] Confirm cash — bank confirmations sent and returned
- [ ] Test AR — confirmations, subsequent receipts
- [ ] Test AP — search for unrecorded liabilities, subsequent disbursements
- [ ] Inventory count observation (if applicable)
- [ ] Test journal entries for unusual/late entries
- [ ] Analytical procedures — fluctuation analysis vs. prior year and budget
- [ ] Evaluate going concern indicators

**Wrap-Up:**
- [ ] Subsequent events review (S-1 and S-2 events)
- [ ] Representation letter obtained
- [ ] Contingencies and commitments confirmed
- [ ] Disclosure checklist completed
- [ ] Final quality review

#### IRS Audit Response Checklist

- [ ] Identify audit type: correspondence, office, or field
- [ ] Note response deadline (typically 30-60 days from notice date)
- [ ] Pull all documents related to questioned items
- [ ] Prepare organized binder: chronological, tabbed by issue
- [ ] Draft response letter — factual, concise, no volunteering
- [ ] Identify potential penalties and abatement opportunities
- [ ] Consider power of attorney (Form 2848) if CPA will represent
- [ ] Document all communications with IRS (dates, contact names, reference numbers)

### 4. Compliance Calendar Generation

To generate a compliance calendar for a client, collect:
- Entity type (individual, S-Corp, C-Corp, Partnership, LLC)
- State(s) of filing
- Fiscal year end
- Special situations: payroll, sales tax, multi-state, nonprofit, foreign accounts

Then produce a month-by-month action list with:
- Deadline date
- Form/filing required
- Responsible party (client vs. firm)
- Status tracking (pending / in progress / filed)

**Example output format:**
```
CLIENT: Acme Corp (S-Corp, Texas, FYE Dec 31)
COMPLIANCE CALENDAR — 2026

JAN 31  → W-2s to employees; 1099-NECs to contractors
JAN 31  → File W-2s (W-3) and 1099-NECs with IRS
MAR 17  → Form 1120-S due (or file 7004 extension)
APR 15  → TX Franchise Tax Report due
APR 15  → Shareholder K-1s delivered
SEP 15  → 1120-S extended return due
DEC 31  → Year-end tax planning review
```

### 5. Regulatory Change Alert Workflow

When asked to monitor for regulatory changes on a topic:

1. **Search** for recent updates:
   ```
   web_search: "[topic] IRS 2026 update" 
   web_search: "FASB ASU 2025 2026 [topic]"
   web_search: "[state] tax law change 2026"
   ```

2. **Summarize** the change: what changed, effective date, who it affects, action required

3. **Flag impact** for known client types:
   - Individuals vs. businesses
   - Industry-specific (real estate, healthcare, manufacturing)
   - Size thresholds that trigger/exclude the rule

4. **Recommend action**: update workpapers, notify clients, revise checklists, or monitor further

---

## Usage Examples

### Example 1: Client Deadline Check
"What are all filing deadlines for our S-Corp clients in Q1 2026?"
→ Generate list: 1099s (Jan 31), W-2s (Jan 31), 1120-S (Mar 17) or extension, state variants

### Example 2: Regulatory Alert
"Has the 1099-K threshold changed for 2025?"
→ web_search for IRS 1099-K 2025 threshold → summarize current rule, effective date, client impact

### Example 3: Audit Prep
"We have a financial statement audit starting in 6 weeks. What do we need?"
→ Run through Pre-Audit checklist, generate PBC request list, identify risk areas

### Example 4: Compliance Calendar
"Build a compliance calendar for a new C-Corp client in Illinois, FYE June 30"
→ Map fiscal year to federal Form 1120 deadlines, IL corporate income tax, plus any payroll/sales tax obligations

---

## Key References

- IRS Tax Calendar for Businesses: https://www.irs.gov/businesses/small-businesses-self-employed/online-tax-calendar
- FASB Standards & ASUs: https://www.fasb.org
- AICPA Practice Aids: https://www.aicpa-cima.com
- State Tax Authority Directory: https://taxfoundation.org/state-tax-agencies/
- FinCEN (FBAR, BSA): https://www.fincen.gov

---

## Important Disclaimers

This skill provides compliance **frameworks and checklists** — not legal or tax advice. All deadlines should be verified against primary sources before relying on them. Tax law changes frequently; always confirm current rules with IRS.gov or a licensed tax professional before advising clients.
