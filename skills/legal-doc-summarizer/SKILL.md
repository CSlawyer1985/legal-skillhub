---
name: legal-doc-summarizer
description: Read contracts, NDAs, terms of service, employment agreements, leases, and SaaS MSAs and produce a structured summary that flags risk, surfaces hidden obligations, and gives plain-language explanations. Identifies indemnification, limitation of liability, IP assignment, non-compete, auto-renewal, choice-of-law, arbitration, termination, and payment-terms clauses. Compares clauses to market norms and flags deviations. Outputs a redline checklist of what to push back on. NOT a substitute for licensed counsel — provides general information only. Use when asked to summarize a contract, review an NDA, explain an employment agreement, audit a SaaS MSA, check a lease, prepare for negotiation, redline a contract, or understand what a clause means. Triggers on "summarize this contract", "review this NDA", "explain this clause", "redline", "review my offer letter", "lease review", "MSA review", "DPA review", "ToS summary", "what does this mean".
metadata:
  tags: ["legal", "contracts", "nda", "msa", "employment", "lease", "review", "negotiation"]
---

# Legal Document Summarizer

Read a contract or legal document and return a structured, risk-aware summary. Built for non-lawyers who need to understand what they are about to sign — and what to push back on — before paying a lawyer to nitpick at $400/hr.

**This skill is not a substitute for licensed legal advice.** It surfaces issues, flags norms, and explains terminology. Final review on any high-stakes document should go to a lawyer admitted in the relevant jurisdiction.

## Usage

**Basic invocation:**
> Summarize this NDA — paste the text
> Review my offer letter
> Explain this non-compete clause
> What's wrong with this MSA?

**With context:**
> NDA from a Series B startup, mutual, I'm joining as contractor. Term: 5 years.
> SaaS MSA, vendor side, $200k ARR deal, customer is a US bank.
> Lease review: 5-year commercial in NYC, rent escalator 4%/yr.
> Employment agreement: SF Bay Area, senior engineer, $180k base + 0.1% stock.

The agent reads the document, classifies it, runs the appropriate checklist, and outputs a structured summary with risk flags, market-norm comparison, and a redline list.

## Document Type Routing

The agent first classifies the document, because the risk surface differs:

| Type | Key risk areas |
|---|---|
| NDA (mutual or one-way) | Term, scope of confidential info, residuals, return/destruction, jurisdiction |
| Employment agreement | At-will, IP assignment, non-compete, severance, equity vesting |
| Independent contractor | Worker classification, IP, payment terms, indemnification |
| Offer letter | Comp, equity, vesting, signing bonus, clawback, start date |
| SaaS MSA / SOW | SLA, data ownership, indemnification, limitation of liability, termination |
| DPA (data processing) | Sub-processors, data location, audit rights, breach notification |
| Lease (commercial) | Term, escalator, build-out, exit, personal guarantee |
| Lease (residential) | Term, deposit, repairs, early termination, jurisdiction caps |
| Investor docs (SAFE/note/term sheet) | Valuation cap, discount, MFN, pro-rata, board, liquidation prefs |
| Software license / EULA | Use scope, IP retention, audit rights, transferability |
| Settlement agreement | Releases, scope, payment terms, non-disparagement, confidentiality |
| ToS / privacy policy (consumer) | Data use, arbitration, class action waiver, jurisdiction |

For each type, the agent runs the relevant checklist below.

## Universal Risk Flags

These appear across most contracts and warrant attention regardless of document type:

### 🚩 Limitation of liability — if cap is below 12 months of fees, push back

Standard cap: 12 months of fees paid in the period before the claim. Anything below = vendor pushing too much risk to customer. "$0 cap" or "$10,000 cap" on a $200k deal = walk away or aggressive redline. Direct vs consequential damages distinction matters: vendor-side wants to exclude consequential/lost-profits, customer wants those covered for breach of confidentiality, IP, indemnification.

### 🚩 Indemnification scope and triggers

Mutual, narrow indemnification is the norm. Watch for:
- One-sided indemnification (you indemnify them, no reciprocal)
- "Arising out of or relating to" — too broad; prefer "caused by" or "resulting from"
- IP indemnification missing on vendor side (a SaaS vendor MUST indemnify for IP infringement)
- Defense vs indemnify — defense obligation is bigger; ensure the indemnifying party has duty to defend AND indemnify

### 🚩 IP assignment overreach

Employment agreements often assign "all IP created during employment" — overbroad if you have side projects. Push for:
- Carve-out for prior inventions (list them in a schedule)
- Carve-out for work done outside scope, on personal time, without company resources (some states like CA, IL, MN, NC, NV, NY, UT, WA have statutory carve-outs)
- Time/place limitation — only IP related to company business

### 🚩 Non-compete

Major shift 2024–2026:
- FTC non-compete ban faced legal challenges; status varies by jurisdiction
- California: void by statute (most non-competes unenforceable)
- Massachusetts: garden leave required (paid 50% during the non-compete)
- Most other states: enforceable if reasonable in scope, time, geography
- Standard tolerable: 12 months, customers and prospects only, geographic limit to where you actually worked. Beyond that = aggressive redline or walk.

### 🚩 Auto-renewal and termination

- Evergreen clauses with 60–90 day cancellation notice are vendor-friendly. Mark calendar.
- One-sided termination for convenience (vendor can leave anytime, customer can't) = bad
- Termination for cause cure period: 30 days for non-payment, 30 days for material breach is normal. Anything shorter = aggressive.

### 🚩 Choice of law and venue

- "Delaware law, Delaware courts" = standard for B2B
- "[Vendor's state] law, exclusive jurisdiction in [vendor's county]" = customer disadvantage; prefer customer's state or neutral
- Arbitration vs court: arbitration faster but caps damages, limits discovery, no jury. Class action waivers paired with arbitration are red flags in consumer contracts.

### 🚩 Confidentiality term

- 3–5 years for general confidential info is market
- Trade secrets: indefinite term until they enter public domain (this is fine, it's how trade secrets work)
- "Perpetual confidentiality" on everything = deviation; push to 3–5 years with trade-secret carve-out

## Document-Specific Checklists

### NDA Checklist

```
□ Mutual or one-way (mutual is preferred unless one-sided info flow)
□ Definition of "Confidential Information" — broad enough but with standard exceptions
□ Standard exceptions: publicly known, independently developed, prior knowledge, lawfully received from third party, required by law
□ Term: 2–5 years for general info, indefinite for trade secrets
□ Permitted purposes — clearly stated, not too broad
□ Return / destruction at end of relationship
□ Residuals clause — if accepted, beneficial to receiving party (employees can use general knowledge mentally retained)
□ No grant of license to IP
□ Injunctive relief without bond — standard; don't fight
□ No non-compete or no-solicit hidden in NDA (sometimes happens — flag)
□ Jurisdiction reasonable
```

### Employment Offer Checklist

```
□ Title, reporting, location (and remote policy if applicable)
□ Base salary (annual or hourly) and pay frequency
□ Bonus eligibility — discretionary vs formula vs commission plan
□ Equity — type (RSU/ISO/NSO/SAR), grant amount, strike price, vesting schedule (4yr/1yr cliff is standard), accelerated vesting on change of control
□ Sign-on bonus — clawback period and pro-rata terms
□ Benefits — health, dental, vision, 401k match, PTO policy
□ At-will employment statement (US private sector)
□ IP assignment language — check carve-outs
□ Confidentiality post-employment
□ Non-compete and non-solicit (and whether legally enforceable in your state)
□ Severance — none is normal at IC level; senior executives often negotiate
□ Arbitration agreement (often separate; review JAMS/AAA rules)
□ Background check / drug test contingency
□ Start date and at-will reminder
```

### SaaS MSA Checklist

```
□ Term and renewal — co-term with SOWs, no auto-renewal without notice
□ Fees and payment — Net 30/45 standard; late fees capped
□ SLAs — uptime % with credits as sole remedy, response time, support tiers
□ Data ownership — customer data is customer property; vendor has limited license to provide service
□ Sub-processors — list, customer right to object to new ones
□ Security — SOC 2 / ISO 27001 referenced, breach notification within 72 hours (GDPR alignment)
□ Confidentiality — mutual, term 3–5 years
□ IP — vendor retains service IP, customer retains data; no ownership of feedback/improvements unless explicit
□ Indemnification — vendor indemnifies for IP infringement, customer indemnifies for unauthorized use of service
□ Limitation of liability — 12-month cap with carve-outs (confidentiality breach, indemnification, gross negligence, willful misconduct)
□ Insurance — vendor minimum coverage cited
□ Termination — for convenience with notice + for cause with cure
□ Return / destruction of data on termination
□ Force majeure — narrow scope; not an out for performance
□ Assignment — restricted, mutual consent (with carve-out for change of control)
□ Audit rights — customer right to audit security or vendor SOC 2 report
□ Governing law / venue
□ Order of precedence between MSA, SOW, DPA
```

### Commercial Lease Checklist

```
□ Premises clearly defined (square footage, common area allocation, exclusive/non-exclusive parking)
□ Term and options to renew (with rent reset basis: fixed bumps, CPI, FMV)
□ Base rent and escalators (cap escalators if FMV-based)
□ Operating expenses / CAM / NNN — exclude capital improvements, controllable expenses cap (e.g., 4% YoY)
□ Build-out / TI allowance — sufficient for fit-out, in writing, with timeline
□ Use clause — broad enough for current and future use
□ Assignment / sublet — landlord consent not unreasonably withheld; permitted transfers (affiliates, M&A)
□ Personal guarantee — push to limit (good guy, term-limited, capped)
□ Insurance and indemnification — mutual, standard limits
□ Maintenance and repair — landlord covers structure, tenant covers interior
□ Defaults and cure — 10-day for monetary, 30-day for non-monetary
□ Termination — for convenience usually no, but negotiate option to terminate for casualty, condemnation, co-tenancy
□ Holdover — 150% rent (negotiable down to 125%)
□ Subordination, non-disturbance, attornment (SNDA) — request from existing lender
□ Estoppel certificates — limited in scope and timing
□ Brokerage commission — landlord pays
□ Surrender condition — broom-clean, no restoration of base building
```

### Investor Term Sheet Checklist (Founder Side)

```
□ Pre-money valuation and round size
□ Investor type and lead identity
□ Liquidation preference — 1x non-participating standard; multipliers and participating = aggressive
□ Anti-dilution — broad-based weighted average standard; full ratchet aggressive
□ Pro-rata rights — standard for major investors
□ Board composition — keep founder majority pre-Series B; adjust thereafter
□ Protective provisions — required votes for major decisions; shouldn't block ordinary course
□ Vesting on founders — common in early rounds; 4yr with 1yr cliff, accelerated on double-trigger
□ Drag-along — required, but with thresholds
□ Right of first refusal / co-sale on founder shares
□ Information rights — standard for major investors
□ MFN clause — tracks any later better terms (in convertibles)
□ Discount and cap (in SAFEs and notes)
□ Conversion mechanics — pre/post-money SAFE distinction matters
□ Expense reimbursement to investor — capped
□ No-shop / exclusivity — limited duration (30–45 days)
□ Confidentiality
□ Closing conditions
```

## Plain-Language Explanations

For any clause, the agent provides:

1. **What it says** (verbatim quote, key phrases)
2. **What it means** (translation into plain English)
3. **Why it's there** (the risk it allocates)
4. **Market norm** (what is typical)
5. **Risk to you** (signing-party-specific)
6. **Suggested redline** (specific language change)

Example output:

```
Clause: Section 8.3 Limitation of Liability

Says: "In no event shall Vendor's total liability under this Agreement exceed the
fees paid by Customer in the three (3) months preceding the event giving rise to
the claim."

Means: If Vendor screws up badly enough to cost you millions, the most you can
recover is what you paid them in the prior quarter.

Why: Vendors limit liability to make pricing predictable and insurable.

Market norm: 12 months of fees is standard. 3 months is aggressive.

Risk to you: At $50k MRR, your maximum recovery would be $150k. If a data
breach costs you $5M in incident response and notification, you absorb $4.85M.

Suggested redline: "...exceed the greater of (a) the fees paid by Customer in
the twelve (12) months preceding the event, or (b) [$X], with the following
carve-outs from this cap: Vendor's indemnification obligations under Section 9,
breach of Section 11 (Confidentiality), and Vendor's gross negligence or willful
misconduct."
```

## Output Format

For a contract review, the agent returns:

```
## Document: [type] | Risk: [Low/Medium/High] | Signing party: [you]

### Plain-language summary
[2–3 paragraphs on what this contract does]

### Top 5 risks
1. [Risk] — [Section] — [What to push back]
2. ...

### Market deviations
- [Clause]: [their term] vs [market norm]

### Redline checklist (paste into negotiation email)
- Section X: change "X" to "Y" because...
- Section Y: add "...carve-out for..."
- Section Z: delete (overbroad)

### Things you might miss
- [Hidden auto-renewal, off-checklist clause, schedule reference]

### Walk-away triggers
[If they refuse to fix items 1, 3, 5 — consider walking]
```

## When to Stop and Get a Lawyer

The agent will tell you to escalate if:

- Document is for a transaction worth > $100k (or material to your business)
- Personal guarantee is involved
- Restrictive covenants (non-compete, non-solicit) with multi-year scope
- IP assignment of significant prior inventions
- Litigation, settlement, or regulatory matter
- Cross-border with non-trivial choice-of-law
- M&A, financing, or material change-of-control
- You don't understand a clause and the agent's plain-language explanation didn't help
- Your gut says something is off

Better to spend $1k on a lawyer review than $50k on a bad clause.

## What This Skill Does Not Do

- Provide legal advice (it provides general information for educational purposes)
- Substitute for a lawyer admitted in your jurisdiction
- Predict litigation outcomes
- Calculate damages or settlement value
- Interpret highly specialized regulated contracts (FDA, FCC, defense) without explicit caveats
- Take responsibility for your decisions

If you're going to ignore this section, hire a lawyer instead.
