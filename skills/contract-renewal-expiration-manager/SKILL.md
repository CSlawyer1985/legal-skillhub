---
name: Contract Renewal & Expiration Manager
version: 1.0.0
price: 19
category: productivity
author: Remy Claw
last_validated: 2026-03-03
tagline: Never miss a vendor contract renewal — proactive system for the full renewal lifecycle.
---

# Contract Renewal & Expiration Manager
**Framework: Renewal Readiness Protocol**
**Output: A proactive renewal calendar + decision framework + renegotiation prep package**

Missing a contract renewal costs real money — auto-renewals at bad rates, emergency re-sourcing, lost leverage. This system gives you a structured process to manage every vendor contract renewal proactively: alert triggers, renewal decisions, renegotiation prep, and documentation.

---

## Phase 1: Renewal Inventory & Calendar Setup

**Step 1 — Build your renewal calendar**

For every active vendor contract, capture:

| Field | What to Record |
|-------|---------------|
| Vendor Name | Legal name + DBA |
| Contract Start | Date |
| Contract End | Date |
| Auto-Renewal Clause | Yes/No — if yes, notice period required |
| Notice Deadline | Contract end date minus notice period |
| Annual Value | $ACV or total contract value |
| Category | Software / Services / Suppliers / Professional Services |
| Owner | Internal stakeholder responsible for this vendor |

**Priority flag:** Any contract with ACV > $10K or auto-renewal clause = Priority tier (review 90 days out). All others = Standard tier (review 60 days out).

---

## Phase 2: The 90/60/30-Day Alert Protocol

**90 days before renewal:**
- Owner receives automated/calendar alert
- Trigger: Vendor Performance Audit (see Vendor Performance Audit skill)
- Decision: Is this vendor still the right solution? Flag for review.
- Action: Schedule renewal decision meeting

**60 days before renewal:**
- Complete renewal decision (renew vs. renegotiate vs. replace)
- If renewing as-is: confirm terms, draft renewal notice
- If renegotiating: begin prep (Phase 3)
- If replacing: begin vendor search, trigger parallel onboarding timeline

**30 days before renewal:**
- All paperwork finalized and signed
- If auto-renewal with notice clause: send written notice by this date
- Confirm successor vendor is ready (if replacing)
- Update renewal calendar for next cycle

**Emergency Protocol (< 30 days discovered):**
If a renewal is discovered < 30 days out:
1. Immediate owner notification
2. Assess: Can we extend month-to-month? Is auto-renewal acceptable short-term?
3. If replacing: begin emergency sourcing
4. Document the miss and add this vendor to Priority tier going forward

---

## Phase 3: Renewal Decision Framework

For each renewal, score across 4 dimensions (1-5 each):

| Dimension | Score 1 | Score 3 | Score 5 |
|-----------|---------|---------|---------|
| **Performance** | Consistently below SLA | Meets SLA most of the time | Exceeds SLA reliably |
| **Value** | Overpriced vs. market | Market rate | Below market, strong value |
| **Strategic fit** | No longer fits our direction | Neutral / functional | Core to our operations |
| **Relationship** | Difficult to work with | Professional, transactional | Strong partnership |

**Decision matrix:**
- 16-20: Renew, consider expanding scope
- 11-15: Renew, assess for renegotiation
- 6-10: Renegotiate or evaluate alternatives
- 1-5: Replace — begin sourcing

---

## Phase 4: Renegotiation Prep

If decision is to renegotiate, complete this prep package before any vendor conversation:

**Market positioning:**
- What are 2-3 comparable alternatives? Get quotes.
- What's the market rate for this category today vs. when contract was signed?
- What's your BATNA (Best Alternative to Negotiated Agreement)?

**Value ledger:**
- What have you gotten from this vendor over the contract period? (Quantify where possible)
- What problems have occurred? Document with dates and business impact.
- What do you want changed? Rank by priority: price → terms → SLA → scope

**Opening position:**
- State your ask clearly before the first call
- Lead with value received, then the gap between current and desired terms
- Anchor to market data, not just preference

**Concession ladder:**
- What will you trade? (longer term for lower price, volume commitment for discount, etc.)
- What is non-negotiable? (Define in advance, not under pressure)

---

## Phase 5: Documentation Templates

**Renewal Notice Letter (for contracts requiring written notice):**
```
[Date]
[Vendor Name]
[Address]

RE: Contract Renewal Notice — [Contract ID / Service Description]

Dear [Vendor Contact],

This letter serves as formal notice of our intent to [renew / not renew] the agreement dated [Contract Start Date] for [Service Description].

[If renewing:] We look forward to continuing our relationship under the same terms for an additional [term]. Please confirm receipt of this notice.

[If not renewing:] Please consider this our formal notice of non-renewal per Section [X] of our agreement. We will coordinate transition details separately.

Regards,
[Name, Title]
[Company]
```

**Internal Renewal Summary (for stakeholder records):**
- Vendor, Contract ID, Term, ACV
- Renewal decision + rationale
- Changes negotiated (if any)
- Next renewal date
- Owner sign-off

---

## Implementation Checklist

- [ ] Build renewal inventory for all active contracts
- [ ] Set calendar alerts at 90/60/30-day marks for all Priority contracts
- [ ] Set 60/30-day alerts for Standard contracts
- [ ] Assign owners to every contract
- [ ] Complete renewal decision framework for any contracts due within 90 days
- [ ] Store all contracts in a single accessible location (Drive folder, Notion, etc.)
