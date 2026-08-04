# Contract Writing Phases

## Phase 1: Discovery (BLOCKING)

**Cannot proceed until complete.** This phase determines everything.

### Required Information
- [ ] Contract type (services, NDA, lease, loan, partnership, etc.)
- [ ] All parties (names, roles, legal entities)
- [ ] Jurisdiction/governing law
- [ ] Is this B2B or B2C? (affects valid clauses)
- [ ] Existing relationship between parties?
- [ ] Previous contracts between them?

### Questions by Relationship Type

**Business (formal):**
- Legal entity names, tax IDs, authorized signatories
- Insurance requirements
- Dispute resolution preferences

**Personal (informal):**
- What's the relationship? (family, friends, acquaintance)
- Desired formality level (full contract vs. simple agreement)
- Main concern to protect against?

### Output
Create `intake.md` with all answers. Create `parties.md` with party details.

---

## Phase 2: Structure

### Define Sections
Based on contract type, determine required sections:

| Type | Core Sections |
|------|---------------|
| Services | Scope, deliverables, payment, IP, termination, liability |
| NDA | Definition of confidential, obligations, duration, exceptions |
| Lease | Property, term, rent, deposit, maintenance, termination |
| Loan | Amount, interest, repayment schedule, collateral, default |
| Partnership | Contributions, profit sharing, decisions, exit, dissolution |

### Mandatory Clause Checklist
- [ ] Parties clearly identified
- [ ] Subject matter defined
- [ ] Term/duration specified
- [ ] Payment terms (if applicable)
- [ ] Termination conditions
- [ ] Dispute resolution
- [ ] Governing law
- [ ] Notice provisions

---

## Phase 3: Draft

### Clause-by-Clause Generation

1. Generate each clause independently
2. For critical clauses, offer 2-3 alternatives:
   - Aggressive (favors client)
   - Balanced
   - Conservative (favors counterparty)
3. Flag risks in each version
4. Let user choose

### Critical Clauses Requiring Alternatives
- Liability limitation
- Indemnification
- Termination for convenience
- Non-compete (if applicable)
- Penalty clauses

### Version Control
```
# Before ANY edit:
1. cp current.md versions/v00{n+1}.md
2. Make changes to current.md
3. Log change in notes.md: "[date] v00{n+1}: Changed X because Y"
```

---

## Phase 4: Review

### Internal Coherence Check
- [ ] All defined terms used correctly
- [ ] Dates and amounts consistent throughout
- [ ] Cross-references valid ("per Section 5.2" exists)
- [ ] No contradicting clauses

### Risk Analysis
For each clause, ask:
- "If this goes wrong, what happens?"
- "Can counterparty interpret this against us?"
- "What's missing that could hurt us?"

See `risks.md` for common red flags.

### Ambiguity Detection
Flag vague terms:
- "reasonable" → define what's reasonable
- "promptly" → specify hours/days
- "material" → define threshold
- "best efforts" → specify what efforts

---

## Phase 5: Negotiate (if multiple parties)

### Track Positions
In `notes.md`:
```
[date] Party A requests: Change payment to net-60
[date] Our position: Counteroffer net-45 with 2% early payment discount
[date] Resolution: Accepted net-45
```

### Balance Analysis
After each round, assess:
- Is this contract balanced?
- Which party bears more risk?
- Would I sign this if I were the other party?

### Deadlock Resolution
If parties disagree:
1. Identify underlying interests (not positions)
2. Propose creative alternatives
3. Suggest escalation to mediator if needed

---

## Phase 6: Finalize

### Pre-Signature Checklist
- [ ] All blanks filled
- [ ] Signature blocks for all parties
- [ ] Date fields present
- [ ] Exhibit/attachment references valid
- [ ] Disclaimer included

### Human Approval Required
**NEVER consider a contract final without explicit human confirmation.**

"The draft is ready. Please review and confirm you want to finalize."

### Post-Signature
1. Move from `drafting/` to main `~/contracts/` folder
2. Create `meta.md` per contracts skill format
3. Set up calendar alerts if applicable
