# Contract Review Assistant

Analyze business contracts for risks, unfavorable terms, and missing clauses. Get a plain-English summary of what you're signing.

## What It Does
- Reads contracts (paste text or provide file path)
- Flags risky clauses: auto-renewal, non-compete, unlimited liability, IP assignment
- Checks for missing protections: termination rights, data ownership, SLA guarantees
- Scores overall risk (Low / Medium / High / Walk Away)
- Generates a negotiation checklist with suggested counter-terms

## Usage
Paste your contract text or say: "Review the contract at [file path]"

## Review Framework

### 1. Quick Summary
- Parties, effective date, term length
- What each side is agreeing to (plain English)
- Total financial commitment

### 2. Risk Flags (Red / Yellow / Green)

**Red Flags (negotiate or walk):**
- Unlimited liability or uncapped indemnification
- Automatic IP assignment for work product
- Non-compete broader than 12 months / reasonable geography
- Unilateral termination rights (they can, you can't)
- Auto-renewal with 60+ day notice requirement
- Mandatory arbitration in unfavorable jurisdiction
- "Most favored nation" pricing locks

**Yellow Flags (negotiate if possible):**
- Payment terms beyond Net 30
- Broad confidentiality surviving 3+ years
- Change-of-control provisions
- Audit rights without reasonable notice
- Force majeure that's too narrow or too broad

**Green (standard, acceptable):**
- Mutual termination for convenience with 30-day notice
- Standard limitation of liability (12 months of fees)
- Reasonable confidentiality (2 years, excludes public info)
- Clear data ownership and return provisions

### 3. Missing Clause Check
- [ ] Termination for convenience
- [ ] Data ownership and portability
- [ ] SLA with remedies (credits, termination right)
- [ ] Liability cap
- [ ] Insurance requirements
- [ ] Dispute resolution process
- [ ] Amendment process (written, mutual)
- [ ] Assignment restrictions

### 4. Negotiation Checklist
Generate specific counter-proposals for each red/yellow flag with market-standard alternatives.

### 5. Overall Risk Score
Rate the contract and provide a one-line recommendation.

## Output Format
Deliver results as a structured report with clear sections. Use tables for clause-by-clause analysis. Bold the risk level for each flag.

---

*Built by [AfrexAI](https://afrexai-cto.github.io/context-packs/) — AI context packs for business teams. Need deeper legal, compliance, or procurement automation? Check our [industry-specific context packs](https://afrexai-cto.github.io/context-packs/) ($47 each) or run the [AI Revenue Calculator](https://afrexai-cto.github.io/ai-revenue-calculator/) to see what automation could save your team.*
