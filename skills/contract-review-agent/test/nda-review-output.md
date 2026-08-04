# Contract Review Agent -- Dogfood Test Run
## Subject: Mutual NDA -- PrecisionLedger LLC / TechStartup Inc

**Test Date:** 2026-03-17
**Reviewer:** contract-review-agent skill (v1.0.0)
**Input:** `skills/contract-review-agent/test/sample-mutual-nda.md`

---

# STEP 1 — STRUCTURED EXTRACTION (per Workflow Step 2)

## 1. PARTIES

| Role | Legal Name | Signer | Title |
|------|-----------|--------|-------|
| Disclosing Party | PrecisionLedger LLC (DE LLC) | Sam Householder | Managing Member |
| Receiving Party | TechStartup Inc (DE Corp) | Jordan Chen | CEO |

**Observation:** The Agreement is titled "Mutual NDA" and the recitals say both Parties "may disclose" information. However, the defined roles assign "Disclosing Party" only to PrecisionLedger and "Receiving Party" only to TechStartup. The body clauses in Section 2 only bind the "Receiving Party." The indemnification in Section 7 is entirely one-sided toward PrecisionLedger. This creates an asymmetry that contradicts the "mutual" label.

## 2. TERM

| Field | Value | Section |
|-------|-------|---------|
| Effective Date | March 15, 2026 | Preamble |
| Duration | 3 years | §3.1 |
| Expiration Date | March 15, 2029 | Calculated |
| Early Termination | 30 days written notice | §3.1 |
| Auto-Renewal | No | §3.1 (silent) |
| Confidentiality Survival | Perpetual / indefinite | §3.2 |
| Return/Destroy Deadline | 15 business days post-termination | §3.3 |

## 3. FINANCIAL TERMS

| Field | Value | Section |
|-------|-------|---------|
| Contract Value | $0 (no fees — NDA only) | N/A |
| Liquidated Damages | $50,000 per breach | §6.2 |
| Indemnification | PrecisionLedger only -> TechStartup | §7.1 |
| Attorneys' Fees | Prevailing party recovers | §8.3 |

## 4. OBLIGATIONS — See Step 2 below (Obligation Extraction)

## 5. RISK FLAGS — See Step 1 below (Clause Risk Analysis)

## 6. TERMINATION

| Mechanism | Details | Section |
|-----------|---------|---------|
| Termination for convenience | Either Party, 30 days written notice | §3.1 |
| Return / destroy materials | 15 business days, written certification required | §3.3 |
| Post-termination obligations | Confidentiality survives perpetually (§3.2); Non-solicitation survives 2 years (§4.1) |

## 7. GOVERNING LAW

| Field | Value | Section |
|-------|-------|---------|
| Governing Law | Delaware (no conflicts-of-law) | §8.1 |
| Venue | State/federal courts, New Castle County, DE | §8.2 |
| Dispute Resolution | Litigation (no arbitration/mediation clause) | §8.2 |

## 8. RECOMMENDED ACTIONS — See Step 5 below

---

# WORKFLOW STEP 1 — CLAUSE RISK ANALYSIS

## Risk Register

| # | Clause | Section | Category | Risk | Rationale |
|---|--------|---------|----------|------|-----------|
| R1 | Overbroad Confidential Information definition — "all information disclosed in any form whatsoever" with no limitations | §1.1 | IP & Data | 🔴 HIGH | Captures literally everything, including non-sensitive info. Impossible to administer; creates compliance burden with no practical boundary. |
| R2 | No carve-out for publicly available information | §1 (absent) | IP & Data | 🔴 HIGH | Standard NDAs exclude information that is publicly known, independently developed, lawfully obtained from third parties, or already in the Receiving Party's possession. Absence of all four standard carve-outs is a critical deficiency. Any breach claim could rest on information that was never truly confidential. |
| R3 | Perpetual survival of confidentiality obligations | §3.2 | Termination | 🔴 HIGH | "Survive in perpetuity ... indefinitely" creates an unending obligation. Industry standard for NDAs is 2-5 years post-termination. Perpetual obligations are difficult to enforce, create indefinite compliance burden, and are disfavored by courts in many jurisdictions. |
| R4 | One-sided indemnification in a "Mutual" NDA | §7.1-7.2 | Liability | 🔴 HIGH | Only PrecisionLedger indemnifies TechStartup. TechStartup has zero indemnification obligation. This is fundamentally incompatible with a mutual agreement and creates asymmetric risk. If TechStartup breaches, PrecisionLedger bears its own legal costs. |
| R5 | Residuals clause — retained unaided memory | §5.1-5.2 | IP & Data | 🔴 HIGH | Allows either Party to freely use any Confidential Information retained in "unaided memory" for any purpose. This effectively creates a massive loophole in the confidentiality protections — anything a person remembers is fair game. Particularly dangerous when disclosing proprietary financial methodologies, pricing models, or client lists. |
| R6 | Liquidated damages of $50,000 per breach | §6.2 | Financial | 🟡 MEDIUM | The $50,000 per-breach figure is aggressive for an NDA. While the clause asserts it is "reasonable," it may be challenged as a penalty clause depending on the nature of the breach. Multiple inadvertent disclosures could compound to massive exposure. Must assess whether this is proportional to actual harm. |
| R7 | Non-solicitation: 2 years, all employees/contractors regardless of involvement | §4.1-4.2 | Operational | 🟡 MEDIUM | The 2-year post-termination non-solicitation covering ALL employees and contractors — even those with no connection to the engagement — is unusually broad. May be unenforceable in certain states (e.g., California). Could impede normal recruiting activity. |
| R8 | Injunctive relief without posting bond or proving damages | §6.1 | Liability | 🟡 MEDIUM | Waives the bond requirement and proof-of-actual-damages prerequisite for injunctive relief. While common in NDAs, it lowers the bar for obtaining court orders against PrecisionLedger. |
| R9 | No limitation of liability / no cap on damages | (absent) | Liability | 🟡 MEDIUM | The agreement has no overall liability cap. Combined with the one-sided indemnification, uncapped attorneys' fees, and $50K/breach liquidated damages, PrecisionLedger's total exposure is unlimited. |
| R10 | No dispute resolution escalation (mediation/arbitration) | §8.2 | Operational | 🟢 LOW | Jumps straight to litigation. Mediation or arbitration clauses are standard cost-containment measures. Not a red flag, but a missed optimization. |
| R11 | Assignment permitted in M&A without consent | §9.3 | Operational | 🟢 LOW | Standard carve-out. However, should confirm PrecisionLedger is comfortable with Confidential Information transferring to an unknown acquirer of TechStartup. |
| R12 | Governing law / venue in Delaware | §8.1-8.2 | Operational | 🟢 LOW | PrecisionLedger is a DE LLC, so Delaware governing law is acceptable. Austin-based TechStartup may find New Castle County venue inconvenient, but this is favorable for PrecisionLedger. |

---

# WORKFLOW STEP 2 — OBLIGATION EXTRACTION

```
OBLIGATIONS EXTRACTED
─────────────────────

Party: PrecisionLedger LLC (Receiving Party / Disclosing Party)
Obligation: Hold all Confidential Information in strict confidence; no disclosure without written consent
Deadline/Frequency: Ongoing (perpetual per §3.2)
Consequence of breach: Injunctive relief (§6.1) + $50,000 liquidated damages per breach (§6.2) + indemnification liability (§7.1)
Owner (internal): Engagement lead / all staff with access

──────

Party: PrecisionLedger LLC
Obligation: Use Confidential Information solely for the Purpose (financial advisory / tech integration exploration)
Deadline/Frequency: Ongoing (perpetual)
Consequence of breach: Same — injunctive relief + $50K/breach + indemnification
Owner (internal): Engagement lead

──────

Party: Both Parties
Obligation: Restrict access to Confidential Information to need-to-know employees/officers/advisors who are bound by equivalent confidentiality obligations
Deadline/Frequency: Ongoing
Consequence of breach: Breach of Agreement
Owner (internal): HR / Legal — must ensure all personnel with access have signed comparable NDAs

──────

Party: Receiving Party (per terms — but practically both if truly "mutual")
Obligation: Return or destroy all Confidential Information within 15 business days of termination; provide written certification
Deadline/Frequency: 15 business days after termination/expiration
Consequence of breach: Breach of Agreement
Owner (internal): IT / Engagement lead

──────

Party: Both Parties
Obligation: Non-solicitation — do not solicit, recruit, or hire any employee, contractor, consultant, or agent of the other Party
Deadline/Frequency: During Term + 2 years post-termination (through ~March 15, 2031)
Consequence of breach: Breach of Agreement (no specific penalty stated — gap)
Owner (internal): HR / Recruiting team

──────

Party: PrecisionLedger LLC (only)
Obligation: Indemnify, defend, and hold harmless TechStartup against all claims arising from PrecisionLedger's breach, unauthorized disclosure, or negligence
Deadline/Frequency: Ongoing / upon claim
Consequence of breach: Full cost exposure (attorneys' fees, damages, costs)
Owner (internal): Legal / Managing Member

──────

Party: Both Parties (giving notice)
Obligation: Deliver notices in writing via hand delivery, certified mail, or overnight courier
Deadline/Frequency: As needed
Consequence of breach: Notice may be deemed ineffective
Owner (internal): Legal / Operations
```

---

# WORKFLOW STEP 3 — RENEWAL & DEADLINE CALENDAR

```
CONTRACT CALENDAR
─────────────────
Contract: Mutual NDA — PrecisionLedger LLC / TechStartup Inc (NDA-2026-0317)
Effective Date: 2026-03-15
Initial Term: 3 years
Auto-Renewal: No
Termination Notice: 30 days written notice (either Party)
Expiration: 2029-03-15
Next Review: 2027-03-15 (annual review recommended)

KEY DATES
─────────
2026-03-15    Agreement effective
2026-03-17    ← TODAY — 2 days into term
2027-03-15    Recommended annual review
2028-03-15    Recommended annual review
2029-02-13    Last day to give 30-day termination notice before expiration
2029-03-15    Agreement expires
2029-04-05    Deadline: return/destroy Confidential Information (15 business days after expiration)
2031-03-15    Non-solicitation period ends (2 years post-expiration)
∞             Confidentiality obligations — NO sunset date (perpetual survival per §3.2)

⚠️  PERPETUAL OBLIGATION ALERT: Confidentiality obligations never expire.
    Unlike a standard NDA, there is no cancel-by date for confidentiality.
    This should be renegotiated to a defined sunset (e.g., 3-5 years post-termination).
```

---

# WORKFLOW STEP 4 — EXECUTIVE SUMMARY

```
CONTRACT SUMMARY
────────────────
Agreement: Mutual NDA — TechStartup Inc
Date: 2026-03-15 | Term: 3 years (expires 2029-03-15)
Value: $0 (NDA only; no service fees)

KEY TERMS
• Confidential Information: All information in any form (extremely broad, §1.1)
• Confidentiality survival: Perpetual (§3.2)
• Non-solicitation: 2 years post-termination, all personnel (§4)
• Liquidated damages: $50,000 per breach (§6.2)
• Indemnification: One-sided — PrecisionLedger only (§7)
• Termination: 30 days written notice (§3.1)
• Governing law: Delaware, New Castle County courts (§8)

TOP RISKS (Flagged)
🔴 No carve-outs for public information — any information could be deemed "confidential" (§1)
🔴 Perpetual confidentiality obligations — no sunset clause (§3.2)
🔴 One-sided indemnification contradicts "mutual" framing (§7)
🔴 Residuals clause creates massive confidentiality loophole (§5)
🔴 Overbroad CI definition — "all information in any form" (§1.1)
🟡 $50K/breach liquidated damages may be disproportionate (§6.2)
🟡 Non-solicitation covers all personnel regardless of involvement (§4.2)
🟡 No liability cap — unlimited exposure (absent)
🟡 Injunctive relief without bond or proof of damages (§6.1)

RECOMMENDED ACTIONS
1. NEGOTIATE: Add standard carve-outs to CI definition (public info, independent development,
   prior knowledge, third-party lawful receipt) — Engagement Lead — before signing
2. NEGOTIATE: Change perpetual survival to 3-5 years post-termination — Engagement Lead — before signing
3. NEGOTIATE: Add reciprocal indemnification or remove §7 entirely — Legal — before signing
4. NEGOTIATE: Delete or substantially narrow residuals clause (§5) — Legal — before signing
5. NEGOTIATE: Narrow non-solicitation to only personnel directly involved in the engagement — Legal — before signing
6. REVIEW: Assess whether $50K liquidated damages is reasonable relative to potential harm — Legal — before signing
7. ADD: Overall liability cap (e.g., $100K or mutual) — Legal — before signing
8. ADD: Mediation-first dispute resolution before litigation — Legal — before signing

ATTORNEY REVIEW NEEDED: YES
— One-sided indemnification in a mutual agreement (§7)
— Perpetual survival clause (§3.2)
— Aggressive liquidated damages with no cap on number of breaches (§6.2)
— Residuals clause undermining core confidentiality protections (§5)
```

---

# WORKFLOW STEP 5 — RED FLAG IDENTIFICATION (NDA Checklist from SKILL.md)

The SKILL.md lists five NDA-specific red flags (§ "Common Red Flags by Contract Type > NDAs"). Here is the checklist applied to this sample NDA:

| # | SKILL.md NDA Red Flag | Present? | Section | Notes |
|---|----------------------|----------|---------|-------|
| 1 | One-sided (only you are bound) | **PARTIAL** | §2, §7 | The NDA is labeled "mutual" but indemnification is entirely one-sided (§7). Confidentiality duties reference "Receiving Party" which is defined only as TechStartup, yet §2.1 arguably binds whichever party receives info. The structural ambiguity itself is a red flag. |
| 2 | Perpetual term with no sunset | **YES** | §3.2 | Confidentiality obligations survive "in perpetuity ... indefinitely." No sunset clause. |
| 3 | Overly broad definition of "confidential information" | **YES** | §1.1 | "All information disclosed ... in any form whatsoever" — maximally broad. |
| 4 | No carve-outs for publicly available information | **YES** | §1 (absent) | None of the four standard carve-outs (public domain, independent development, prior possession, lawful third-party receipt) appear anywhere in the Agreement. |
| 5 | Residuals clause allowing retained memory of disclosed info | **YES** | §5.1-5.2 | Explicitly permits use of information retained in "unaided memory" for any purpose. |

**Result: 4 out of 5 NDA red flags fully present; 1 partially present. All 5 were detected.**

### Additional Red Flags Found (Beyond the NDA Checklist)

These risks were identified but are NOT covered by the SKILL.md NDA-specific checklist:

| # | Additional Red Flag | Section | Should Be in Checklist? |
|---|-------------------|---------|------------------------|
| A1 | One-sided indemnification in a mutual NDA | §7 | YES — distinct from "one-sided binding" |
| A2 | Aggressive liquidated damages ($50K/breach, cumulative, no cap) | §6.2 | YES — financial risk |
| A3 | Overbroad non-solicitation (all personnel, 2 years) | §4 | YES — operational risk |
| A4 | No overall liability cap | (absent) | YES — liability risk |
| A5 | Injunctive relief without bond/proof of damages | §6.1 | Debatable — common but aggressive |
| A6 | No alternative dispute resolution mechanism | §8.2 | LOW — nice to have |

---

# SKILL.MD EVALUATION

## Does it correctly identify NDA-specific red flags?

**Rating: PASS**

The NDA checklist in the skill (five items) correctly maps to the most common NDA pitfalls:
1. One-sided binding
2. Perpetual term / no sunset
3. Overbroad CI definition
4. No carve-outs for public info
5. Residuals clause

All five were testable against the sample NDA, and all five were detectable by following the skill's framework. The checklist is accurate and well-prioritized.

**Gap:** The checklist does not call out one-sided *indemnification* as a distinct item from one-sided *binding*. In this NDA, the confidentiality obligations are arguably mutual (both parties can be disclosers), but the indemnification is completely one-sided. The checklist item "One-sided (only you are bound)" does not cleanly capture this pattern. This is a meaningful gap.

---

## Is the risk scoring framework usable?

**Rating: PASS**

The three-tier system (🔴 High / 🟡 Medium / 🟢 Low) is simple, intuitive, and adequate for executive communication. It maps well to action urgency:
- 🔴 = must negotiate or reject before signing
- 🟡 = should negotiate; accept with documented risk if needed
- 🟢 = acceptable or favorable

**Observation:** The skill does not define scoring criteria (what makes something 🔴 vs 🟡). This works when a skilled reviewer applies judgment, but it creates inconsistency risk if multiple people use the skill. A brief rubric would help:
- 🔴 = material financial exposure, unenforceable clause, contradicts agreement intent, or triggers escalation rule
- 🟡 = above-market terms, negotiable risk, or compliance burden
- 🟢 = market-standard or favorable to our side

---

## Does the obligation extraction format work?

**Rating: PARTIAL PASS**

The template format (Party / Obligation / Deadline / Consequence / Owner) works well for most obligations. However, several issues surfaced:

1. **Perpetual obligations don't fit the Deadline field cleanly.** "Ongoing (perpetual)" is an awkward entry. The template assumes deadlines are dates or recurring schedules. A perpetual obligation with no sunset is a different animal and should be flagged distinctly.

2. **Missing: obligation severity/priority.** Not all obligations are equal. The obligation to "deliver notices in writing" is not the same as "indemnify and hold harmless." The template has no priority field.

3. **Missing: linked risk flag.** It would be useful to cross-reference obligations to the Risk Register (e.g., "See R4" for the indemnification obligation). The current format does not link them.

4. **Owner assignment is ambiguous for small firms.** "HR / Legal" may not exist as distinct departments in a fractional CFO practice. The template could suggest role-based ownership (e.g., "Engagement Lead," "Managing Member," "External Counsel").

---

## Is the escalation trigger list complete?

**Rating: PARTIAL PASS**

The seven escalation rules in the skill:

| # | Escalation Rule | Triggered by This NDA? | Assessment |
|---|----------------|----------------------|------------|
| 1 | Contract value > $50,000 | NO ($0 NDA) | OK |
| 2 | Indemnification is unlimited or uncapped | **YES** — §7.1 has no cap | Correctly triggered |
| 3 | IP assignment affects core business assets | NO | OK |
| 4 | Personal liability clauses (executive sign-off) | NO | OK |
| 5 | Governing law outside operating jurisdiction | NO (DE LLC, DE law) | OK |
| 6 | Any clause that waives statutory rights | MAYBE — bond waiver in §6.1 | Edge case |
| 7 | M&A, securities, or financing-related terms | NO | OK |

**Missing escalation triggers that should be added:**

- **Perpetual or indefinite obligations** — §3.2's perpetual survival should independently trigger attorney review. Many courts disfavor perpetual obligations and enforceability varies by jurisdiction.
- **One-sided terms in a mutual agreement** — structural asymmetry (mutual label, one-sided substance) is a red flag that should trigger escalation regardless of dollar value.
- **Liquidated damages clauses above a threshold** — $50K/breach with no cap on number of breaches can compound to significant exposure. Should trigger review at some threshold (e.g., >$25K per incident or >$100K aggregate potential).
- **Non-compete / non-solicitation clauses** — enforceability varies dramatically by state (CA, CO, MN, etc.). These should always get attorney review for enforceability analysis.
- **Residuals clauses** — these are sufficiently unusual and dangerous that they should independently trigger escalation.

---

## Are there gaps for different contract types?

**Rating: PARTIAL PASS**

The skill covers four contract types well: SaaS, Vendor/Supplier, Client Engagement Letters, and NDAs. However:

**Missing contract types that a fractional CFO practice encounters frequently:**
1. **Independent Contractor / Consulting Agreements** — IP ownership, work-for-hire, non-compete, benefits misclassification risk
2. **Lease Agreements** — personal guarantees, escalation clauses, early termination penalties, CAM charges
3. **Loan / Credit Agreements** — covenants, default triggers, cross-default, personal guarantees
4. **Partnership / Operating Agreements** — profit splits, capital calls, dissolution, non-compete
5. **Insurance Policies** — exclusions, duty to defend vs. duty to indemnify, claims-made vs. occurrence

**Gaps within the NDA checklist specifically:**
- No mention of one-sided indemnification as distinct from one-sided binding
- No mention of liquidated damages / penalty clauses
- No mention of non-solicitation (which frequently appears in NDAs)
- No mention of overbroad scope of "Purpose" or permitted use
- No mention of mandatory destruction/return timeline issues

---

# STRUCTURED TEST RESULT

## Test Scenario

Created a realistic Mutual NDA between PrecisionLedger LLC and TechStartup Inc with 10 intentionally problematic clauses. Ran the full five-step contract-review-agent workflow (Clause Risk Analysis, Obligation Extraction, Renewal & Deadline Calendar, Executive Summary, Red Flag Identification) against the NDA. Evaluated whether the SKILL.md framework correctly identified all issues and whether the output templates were functional.

## Overall Result: PARTIAL PASS

The skill successfully surfaces the majority of NDA risks and produces usable structured output. However, there are meaningful gaps in the escalation rules, the NDA-specific checklist, and the obligation extraction format that would cause a real-world reviewer to miss issues or produce inconsistent results.

---

## What Worked Well

1. **NDA red flag checklist (5 items) correctly identified all 5 planted issues.** The checklist is well-targeted and the items are the right ones for NDA review.

2. **The risk scoring framework (🔴/🟡/🟢) is simple, intuitive, and action-oriented.** Easy to communicate to non-legal stakeholders. Maps cleanly to negotiate/accept/favorable.

3. **The Executive Summary template is excellent.** It forces structure, includes a clear "Attorney Review Needed" gate, and produces a one-page output suitable for leadership review.

4. **The Renewal & Deadline Calendar format works.** The cancel-by-date flagging (60-day warning) is a useful practical feature.

5. **The Structured Extraction prompt (Step 2) covers all necessary dimensions** — parties, term, financial terms, obligations, risks, termination, governing law, and actions.

6. **Escalation rules correctly triggered** on the uncapped indemnification clause.

7. **The workflow sequence is logical** — ingest, extract, analyze, calendar, summarize — and avoids common pitfalls like jumping to conclusions before full extraction.

---

## What Broke or Was Missing

### Critical Gaps

1. **NDA checklist missing one-sided indemnification as a distinct red flag.** The "one-sided (only you are bound)" item does not clearly cover the case where confidentiality is mutual but indemnification is asymmetric. This is a common negotiation tactic and should be called out explicitly.

2. **Escalation rules missing perpetual obligations trigger.** Perpetual survival clauses should independently require attorney review. The current rules would not flag a perpetual NDA unless another trigger (>$50K value, uncapped indemnification) happens to also be present.

3. **Escalation rules missing non-solicitation / non-compete trigger.** These clauses have highly variable enforceability across jurisdictions and should always get legal review.

4. **No scoring rubric for 🔴/🟡/🟢.** Without defined criteria, two reviewers could score the same clause differently. The skill needs 2-3 sentences defining each level.

### Moderate Gaps

5. **Obligation extraction template lacks a priority/severity field.** All obligations appear equal in the current format. A "High/Med/Low" priority would help triage.

6. **Obligation template lacks cross-reference to Risk Register.** Obligations tied to risky clauses (e.g., the indemnification obligation tied to R4) should link back.

7. **Perpetual obligations break the Deadline/Frequency field.** The template assumes time-bound deadlines. Perpetual obligations need a distinct treatment (e.g., "PERPETUAL — flag for renegotiation").

8. **No contract-type checklist for Independent Contractor Agreements, Leases, or Loan/Credit Agreements** — all common in fractional CFO work.

### Minor Gaps

9. **Residuals clause is listed but not explained in the skill.** A reviewer unfamiliar with residuals clauses would not understand why it is dangerous. One sentence of context would help.

10. **No mention of "structural asymmetry" as a meta-red-flag.** When a contract is labeled mutual but contains one-sided provisions, that pattern itself is a red flag independent of any single clause.

---

## Specific Recommended Fixes

### Fix 1: Expand NDA Red Flag Checklist (§ "Common Red Flags by Contract Type > NDAs")

Add these items:
```
### NDAs
- One-sided (only you are bound)
- Perpetual term with no sunset
- Overly broad definition of "confidential information"
- No carve-outs for publicly available information
- Residuals clause allowing retained memory of disclosed info
+ - One-sided indemnification in a nominally "mutual" NDA
+ - Liquidated damages or penalty clauses disproportionate to potential harm
+ - Overbroad non-solicitation covering personnel not involved in the engagement
+ - No limitation of liability or damages cap
+ - Structural asymmetry: contract labeled "mutual" but obligations are one-sided
```

### Fix 2: Add Escalation Triggers

Add to "Escalation Rules" section:
```
Always escalate to licensed attorney when:
  ...existing rules...
+ - Perpetual or indefinite obligations (confidentiality, non-compete, non-solicitation)
+ - Non-compete or non-solicitation clauses (enforceability varies by state)
+ - Liquidated damages exceeding $25,000 per incident or $100,000 aggregate
+ - Residuals clauses that could undermine core IP protections
+ - Structural asymmetry between contract title/framing and actual obligations
```

### Fix 3: Add Risk Scoring Rubric

Add after "Risk scores: 🔴 High / 🟡 Medium / 🟢 Low":
```
Scoring criteria:
- 🔴 HIGH: Material financial exposure (>$25K potential), unenforceable or void clause,
  contradicts stated agreement intent, triggers any escalation rule, or creates unlimited liability.
- 🟡 MEDIUM: Above-market terms that are negotiable, compliance burden that is manageable
  but non-trivial, or missing clause that should be present (e.g., no liability cap).
- 🟢 LOW: Market-standard terms, favorable to our client, or minor optimization opportunities.
```

### Fix 4: Enhance Obligation Extraction Template

```
OBLIGATIONS EXTRACTED
─────────────────────
Party: [Vendor/Client/Both]
Obligation: [Description]
+ Priority: [High/Medium/Low]
Deadline/Frequency: [Date, recurring schedule, or PERPETUAL ⚠️]
Consequence of breach: [Penalty, termination right, etc.]
Owner (internal): [Department or role to assign]
+ Linked Risk: [Risk Register reference, e.g., R4]
```

### Fix 5: Add Contract Type Checklists

Add sections for:
- Independent Contractor / Consulting Agreements (IP assignment, work-for-hire, misclassification)
- Lease Agreements (personal guarantees, CAM, escalation, early termination)
- Loan / Credit Agreements (covenants, cross-default, personal guarantees)

### Fix 6: Add Brief Explanatory Context to Non-Obvious Red Flags

For "Residuals clause," add:
```
- Residuals clause allowing retained memory of disclosed info
  (permits the receiving party to freely use anything their personnel can recall
  from memory — effectively hollows out confidentiality for non-tangible information
  like methodologies, pricing strategies, and business processes)
```
