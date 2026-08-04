# OpenClaw — Case File Analysis Reference

## When an Advocate Uploads a Document

Use this workflow whenever a case file, judgment, charge sheet, FIR, agreement,
notice, or any legal document is uploaded for analysis.

---

## Step 1: Document Identification

Identify the document type first:

| Type | Key Markers |
|------|-------------|
| FIR / NCR | "First Information Report", FIR No., Police Station name, Sections |
| Charge Sheet | "Report under Section 173 CrPC / 193 BNSS", charge columns |
| Judgment | "IN THE COURT OF", "JUDGMENT", operative portion, "ORDER" |
| Plaint / Petition | "MOST RESPECTFULLY SHOWETH", "PRAYER" |
| Order / Decree | "ORDER DATED", "It is ordered that" |
| Agreement / Contract | "THIS AGREEMENT", "WHEREAS", "NOW THEREFORE" |
| Legal Notice | Advocate letterhead, "LEGAL NOTICE", demand |
| Affidavit | "AFFIDAVIT", "do hereby solemnly affirm" |
| Chargesheet / Panchnama | Police document with witness list, seizure list |

---

## Step 2: Extract Structured Information

For every uploaded document, extract and present in this format:

```
CASE BRIEF — [Document Type]
================================================
Forum / Court:
Case Number:
Parties:
  Plaintiff/Petitioner/Complainant:
  Defendant/Respondent/Accused:

Date of Document:
Date of Filing (if different):

Sections / Provisions Invoked:
  [List all statutes and section numbers]

Key Facts (bullet points — chronological):
  •
  •

Relief Sought / Issue Before Court:

Current Stage:
  [ ] Pre-trial / Investigation
  [ ] Bail stage
  [ ] Framing of charges
  [ ] Evidence recording
  [ ] Arguments
  [ ] Judgment delivered
  [ ] Appeal / Revision pending
  [ ] Execution stage

Limitation Analysis:
  Cause of action arose on: ___________
  Applicable limitation period: ___________
  Last date to file / appeal: ___________
  Status: [In time / Possibly barred — verify]

Missing Documents / Gaps Identified:
  •

Suggested Next Steps:
  1.
  2.
================================================
```

---

## Step 3: Judgment Analysis (if document is a judgment)

When analysing a judgment, extract:

### A. Ratio Decidendi
- What legal question did the court answer?
- What rule/principle did the court lay down?

### B. Facts Relied Upon
- Which facts were decisive in reaching the conclusion?

### C. Operative Order
- Exactly what has been directed/ordered?
- Within what time frame?
- Against whom?

### D. Distinguishing Factors
- Can this judgment be distinguished on facts for the advocate's case?
- Is it binding (SC/HC) or merely persuasive?

### E. Appeal / Challenge Assessment
- Is the order appealable? Under what provision?
- Limitation for appeal: ___
- Grounds available: ___

---

## Step 4: Contract / Agreement Analysis

For agreements, analyse:

1. **Parties & Capacity** — Are parties correctly identified? Competency to contract (Sec 11 Indian Contract Act)?
2. **Consideration** — Present and lawful?
3. **Term & Termination** — Duration, notice period, conditions for exit
4. **Key Obligations** — What must each party do / not do?
5. **Default & Remedy Clauses** — Liquidated damages, indemnity, dispute resolution
6. **Arbitration Clause** — Exists? Institutional or ad hoc? Seat and governing law?
7. **Jurisdiction Clause** — Exclusive or non-exclusive? Consistent with Indian law?
8. **Force Majeure** — Scope and mechanism
9. **Limitation of Liability** — Cap present?
10. **Red Flags** — Unfair terms, missing clauses, ambiguous language

---

## Step 5: FIR / Charge Sheet Analysis

For FIRs and charge sheets:

1. **Sections Invoked** — List all; map to BNS/IPC (dual cite)
2. **Bailable vs Non-bailable** — For each section
3. **Cognizable vs Non-cognizable** — Police power to arrest without warrant?
4. **Triable by** — Magistrate / Sessions / Special Court
5. **Bail Eligibility** — Which court? JMFC or Sessions?
6. **Anticipatory Bail Window** — Still available? (Section 482 BNSS / 438 CrPC)
7. **Investigation Status** — Under investigation / chargesheet filed / supplementary chargesheet
8. **Witnesses** — How many? Hostile? Key prosecution witnesses
9. **Material Objects / Seizure** — What was seized? Relevance?
10. **Defence Strategy Pointers** —
    - Alibi potential?
    - Identification parade conducted?
    - Medical evidence inconsistency?
    - Delay in FIR (explain or exploit)?
    - Interested witnesses?

---

## Step 6: Red Flag Checklist

Always scan for:

- [ ] Limitation period — is it running out within 30/60/90 days?
- [ ] Section 80 CPC notice — has it been sent before suing government?
- [ ] Correct forum — has advocate filed in the right court?
- [ ] Parties — is there a necessary party missing? (Rule 11 — non-joinder)
- [ ] Interim relief — urgency requiring immediate application?
- [ ] Vakalatnama — filed / signed?
- [ ] Court fees — correctly calculated and paid?
- [ ] Verification — signed and sworn before competent officer?
- [ ] Certified copies — obtained for appeals?
- [ ] Stay / Suspension — is adverse order being implemented? Need urgent stay?

---

## Legal Research Output Format

When asked to research case law on a point, output in this format:

```
LEGAL RESEARCH NOTE
Topic: [Issue]
Prepared for: [Matter name if given]
================================================

LEGAL POSITION:
[Statement of the law in 2–3 sentences]

GOVERNING PROVISIONS:
• Section ___, [Act]
• [Additional provisions]

LANDMARK AUTHORITY:
1. [Case Name], [Citation] — [What it held in 1 sentence]
2. [Case Name], [Citation] — [What it held in 1 sentence]

RECENT DEVELOPMENTS (post-2020 if applicable):
• [SC/HC judgment and brief holding]

APPLICATION TO PRESENT FACTS:
[How the law applies to the advocate's case]

COUNTER-ARGUMENTS TO ANTICIPATE:
• [Opposing argument 1]
• [Opposing argument 2]

RECOMMENDATION:
[What the advocate should argue / file]
================================================
Note: Verify citations on SCC Online / Manupatra before filing.
```
