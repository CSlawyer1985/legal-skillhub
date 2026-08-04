---
name: legal-memo-writer
description: Write formal legal memos with proper structure, citations, legal analysis, and professional tone. Use when drafting legal memoranda, case analysis, statutory interpretation, regulatory summaries, or any structured legal document requiring IRAC or CREAC format. Supports US federal, UK, and EU/GDPR jurisdictions with Bluebook and OSCOLA citation standards.
license: MIT
metadata:
  version: "2.0.0"
  domain: legal
  triggers: legal memo, legal memorandum, IRAC, CREAC, case law, statute, regulation, legal analysis, brief, legal opinion, contract law, tort, compliance memo, NDA, SLA, GDPR, HIPAA, SOC2, CCPA, Bluebook, OSCOLA, jurisdiction template
  role: writer
  scope: document
  output-format: markdown
  related-skills: contract-analyzer, audit-checklist-creator, policy-document-writer
---

# Legal Memo Writer

Drafts professional legal memoranda following standard legal writing conventions (IRAC/CREAC) across US federal, UK, and EU/GDPR jurisdictions with correct citation standards.

## When to Use This Skill

- Drafting internal legal memos analyzing a legal question
- Summarizing case law or statutory requirements
- Analyzing regulatory compliance obligations
- Writing legal opinions on contracts, liability, or IP
- Structuring legal arguments for review by attorneys
- Creating client-facing legal summaries
- Drafting NDA, SLA, IP assignment, and GDPR clause blocks
- Compliance gap analysis (SOC2, HIPAA, GDPR, CCPA)

---

## Quick Start

```python
"""
Legal Memo Writer — Quick Start
Generates a fully-structured IRAC legal memo in markdown.
Requires: Python 3.8+ stdlib only.
"""

import textwrap
from datetime import date

def build_memo(
    to: str,
    from_: str,
    re: str,
    question: str,
    brief_answer: str,
    facts: str,
    irac_blocks: list[dict],
    conclusion: str,
    jurisdiction: str = "US Federal",
) -> str:
    """
    Build a formatted legal memo string.

    irac_blocks: list of dicts with keys:
        issue, rule, application, conclusion
    """
    divider = "─" * 50

    discussion_parts = []
    for i, block in enumerate(irac_blocks, 1):
        section = textwrap.dedent(f"""
### Issue {i}: {block['issue']}

**Rule:** {block['rule']}

**Application:** {block['application']}

**Sub-Conclusion:** {block['conclusion']}
""").strip()
        discussion_parts.append(section)

    discussion = "\n\n".join(discussion_parts)

    memo = textwrap.dedent(f"""
TO:     {to}
FROM:   {from_}
DATE:   {date.today().isoformat()}
RE:     {re}
JURISDICTION: {jurisdiction}

{divider}
QUESTION PRESENTED
{divider}
{question}

{divider}
BRIEF ANSWER
{divider}
{brief_answer}

{divider}
STATEMENT OF FACTS
{divider}
{facts}

{divider}
DISCUSSION
{divider}
{discussion}

{divider}
CONCLUSION
{divider}
{conclusion}

---
*This memo is for informational purposes and does not constitute legal advice.
All citations must be independently verified.*
""").strip()
    return memo


# Example usage
if __name__ == "__main__":
    memo = build_memo(
        to="Legal Team",
        from_="AI Legal Assistant",
        re="GDPR lawful basis for employee monitoring",
        question="Does continuous keystroke logging of remote employees constitute lawful processing under GDPR Article 6?",
        brief_answer="Likely no. Keystroke logging is disproportionate to legitimate interest under Art. 6(1)(f) and conflicts with employee rights under Art. 88. Explicit consent (Art. 6(1)(a)) may be invalid in an employment context due to power imbalance.",
        facts="Acme Corp proposes 24/7 keystroke logging of all remote EU-based employees. No existing consent mechanism. Employees are subject to termination risk.",
        irac_blocks=[
            {
                "issue": "Whether keystroke logging is proportionate under Art. 6(1)(f)",
                "rule": "GDPR Art. 6(1)(f) requires processing to be necessary for legitimate interests and not overridden by data subject rights. WP29 Opinion 2/2017 on data processing at work applies.",
                "application": "Continuous keystroke capture is broader than 'necessary' — periodic screenshots or output measurement achieve the same monitoring objective with less intrusion. WP29 Opinion 2/2017 at pp. 6-9 cautions against disproportionate employee surveillance.",
                "conclusion": "Art. 6(1)(f) does not support continuous keystroke logging without a narrowly-tailored necessity showing.",
            }
        ],
        conclusion="Advise against deployment without a DPIA (Art. 35), consultation with works council if applicable, and switch to less-intrusive monitoring. Seek explicit DPA guidance if proceeding.",
        jurisdiction="EU/GDPR",
    )
    print(memo)
```

---

## Standard Memo Structure

```
TO:     [Recipient Name / Title]
FROM:   [Author Name / Title]
DATE:   [Date]
RE:     [Subject — state the precise legal question]

─────────────────────────────────────────
QUESTION PRESENTED
─────────────────────────────────────────
[One-sentence statement of the legal question.]

─────────────────────────────────────────
BRIEF ANSWER
─────────────────────────────────────────
[2-4 sentences. State the conclusion directly. No hedging.]

─────────────────────────────────────────
STATEMENT OF FACTS
─────────────────────────────────────────
[Objective narrative of legally relevant facts. No argument.]

─────────────────────────────────────────
DISCUSSION
─────────────────────────────────────────
[IRAC or CREAC analysis. See below.]

─────────────────────────────────────────
CONCLUSION
─────────────────────────────────────────
[Restate answer; note caveats; recommend next steps.]
```

---

## IRAC Format (Discussion Section)

- **Issue** — Precise sub-issue being analyzed
- **Rule** — Applicable statute, regulation, or case law (cite fully)
- **Application** — Apply rule to facts; address counterarguments
- **Conclusion** — Sub-issue conclusion

Repeat IRAC for each sub-issue.

## CREAC Format (Alternative — Preferred for US Court Briefs)

- **Conclusion** — State your conclusion up front (inverted from IRAC)
- **Rule** — Applicable legal standard
- **Explanation** — Elaborate the rule with supporting authority
- **Application** — Apply rule + explanation to client facts
- **Conclusion** — Restate conclusion with emphasis

Use CREAC when the audience already knows the question; use IRAC when building up to a conclusion for a skeptical reader.

---

## Multi-Jurisdiction Templates

### US Federal Memo

```
TO:     [Recipient]
FROM:   [Author]
DATE:   [Date]
RE:     [Legal question — cite circuit if relevant]

GOVERNING LAW: [Statute/Reg, e.g., 42 U.S.C. § 1983; 9th Cir. precedent]

QUESTION PRESENTED
Whether [party] is liable under [statute] when [key facts].

BRIEF ANSWER
[Yes/No/Likely.] Under [statute], [element satisfied/not] because [one-line reason].
[Circuit split note if applicable.]

STATEMENT OF FACTS
[Objective facts. Cite record where applicable.]

DISCUSSION

I. [ISSUE HEADING IN ALL CAPS — e.g., THE DEFENDANT IS ENTITLED TO QUALIFIED IMMUNITY]

   A. Legal Standard
      [State the applicable test, e.g., two-part Saucier test.]

   B. Application
      [Apply each prong to facts.]

   C. Counterargument
      [Address strongest opposing argument; distinguish cases.]

CONCLUSION
[Recommendation. Flag circuit split or cert risk if relevant.]
```

**US Citation format (Bluebook):**

| Source | Format |
|--------|--------|
| Federal case | *Smith v. Jones*, 123 F.3d 456, 460 (9th Cir. 2001) |
| Statute | 42 U.S.C. § 1983 (2018) |
| CFR regulation | 29 C.F.R. § 825.100 (2023) |
| Federal Register | 88 Fed. Reg. 12,345 (Feb. 28, 2023) |
| Secondary (law review) | Jane Doe, *Title of Article*, 45 Harv. L. Rev. 123, 130 (2022) |
| Restatement | Restatement (Second) of Torts § 402A (1965) |

### UK Memo (OSCOLA Format)

```
MEMORANDUM

To:      [Recipient]
From:    [Author]
Date:    [Date]
Subject: [Legal question]

Governing Law: [UK Act/Statutory Instrument/Case]

1. QUESTION
   [State the legal question.]

2. SUMMARY
   [Brief answer in 2-4 sentences.]

3. FACTS
   [Objective facts.]

4. ANALYSIS

   4.1 [Issue]
       Rule: [Statute or case in OSCOLA format]
       Application: [Apply to facts]
       Conclusion: [Sub-conclusion]

5. CONCLUSION
   [Overall recommendation.]
```

**UK Citation format (OSCOLA):**

| Source | Format |
|--------|--------|
| Case (neutral citation) | *R v Jones* [2006] UKHL 16 |
| Case (law report) | *Donoghue v Stevenson* [1932] AC 562 (HL) |
| UK Act | Companies Act 2006, s 172 |
| Statutory Instrument | Civil Procedure Rules 1998, SI 1998/3132, r 3.4 |
| EU Retained Regulation | UK GDPR art 6 |
| Secondary | Andrew Burrows, *A Restatement of the English Law of Contract* (OUP 2016) 45 |

*Note: No full-stop after citations; commas separate pinpoints from reporter.*

### EU/GDPR Memo

```
LEGAL MEMORANDUM — EU/GDPR

To:           [DPO / Legal Counsel]
From:         [Author]
Date:         [Date]
Subject:      [GDPR compliance question]
Jurisdiction: EU — Regulation (EU) 2016/679 (GDPR)

1. QUESTION PRESENTED
   [Specific GDPR compliance question.]

2. BRIEF ANSWER
   [Yes/No/Likely. Cite key Article.]

3. FACTS
   [Processing activity, data types, data subjects, purposes.]

4. ANALYSIS

   4.1 Lawful Basis (Art. 6)
       [Identify candidate basis; apply necessity/proportionality test.]

   4.2 Special Category Data (Art. 9)
       [If applicable: identify Art. 9(2) exception.]

   4.3 Data Subject Rights Implications (Arts. 12-22)
       [Right to erasure, portability, objection as applicable.]

   4.4 DPIA Requirement (Art. 35)
       [Trigger analysis: systematic monitoring / large scale / sensitive data.]

5. CONCLUSION AND RECOMMENDATIONS
   [Lawful/Unlawful determination. Remediation steps. DPIA if needed.]
```

**EU Citation format:**

| Source | Format |
|--------|--------|
| GDPR Article | GDPR art 6(1)(f) |
| Recital | GDPR recital 47 |
| WP29/EDPB Opinion | Article 29 WP, Opinion 06/2014 on Notion of Legitimate Interests (WP217) |
| CJEU Case | *Data Protection Commissioner v Facebook Ireland*, Case C-311/18, ECLI:EU:C:2020:559 |
| National DPA Guidance | ICO, *Guide to the UK GDPR* (2021) s 3.2 |

---

## Citation Standards

### Bluebook Quick Reference (US)

```python
"""
Bluebook citation formatter helpers (US legal memos).
"""

def format_case_us(plaintiff: str, defendant: str, volume: int,
                    reporter: str, page: int, pinpoint: int | None,
                    court: str, year: int) -> str:
    """Format a US case citation per Bluebook Rule 10."""
    pin = f", {pinpoint}" if pinpoint else ""
    return f"*{plaintiff} v. {defendant}*, {volume} {reporter} {page}{pin} ({court} {year})"


def format_statute_us(title: int, section: str, year: int | None = None) -> str:
    """Format a USC citation per Bluebook Rule 12."""
    yr = f" ({year})" if year else ""
    return f"{title} U.S.C. § {section}{yr}"


def format_cfr(title: int, section: str, year: int | None = None) -> str:
    """Format a CFR citation per Bluebook Rule 14."""
    yr = f" ({year})" if year else ""
    return f"{title} C.F.R. § {section}{yr}"


# Examples
if __name__ == "__main__":
    print(format_case_us("Smith", "Jones", 123, "F.3d", 456, 460, "9th Cir.", 2001))
    # → *Smith v. Jones*, 123 F.3d 456, 460 (9th Cir. 2001)
    print(format_statute_us(42, "1983", 2018))
    # → 42 U.S.C. § 1983 (2018)
    print(format_cfr(29, "825.100", 2023))
    # → 29 C.F.R. § 825.100 (2023)
```

### OSCOLA Quick Reference (UK)

- Cases: *Parties* [Year] Report Page (Court) — no full-stop after.
- Statutes: Act Year, s Section — comma before section only when needed for clarity.
- No underlining; italicize case names only.
- Pinpoints use comma + page: *Jones v Smith* [2010] EWCA Civ 100, [45].

---

## Contract Clause Library

Ready-to-insert clause blocks. Replace `[BRACKETED]` fields before use.

### NDA — Mutual Confidentiality

```
MUTUAL NON-DISCLOSURE AGREEMENT CLAUSE

1. Definition of Confidential Information. "Confidential Information" means any
   non-public information disclosed by either Party ("Disclosing Party") to the
   other ("Receiving Party") in connection with [PURPOSE], whether in written,
   oral, electronic, or other form, that is designated as confidential or that
   reasonably should be understood to be confidential given the nature of the
   information and circumstances of disclosure.

2. Obligations. Each Receiving Party shall: (a) hold Confidential Information
   in strict confidence using at least the same degree of care used to protect
   its own confidential information, but no less than reasonable care; (b) not
   disclose Confidential Information to third parties without prior written
   consent; and (c) use Confidential Information solely for [PURPOSE].

3. Exclusions. Obligations do not apply to information that: (a) is or becomes
   publicly known through no breach; (b) was rightfully known before disclosure;
   (c) is received from a third party without restriction; or (d) is independently
   developed without use of Confidential Information.

4. Term. Obligations survive for [X] years following termination of this Agreement
   or until the information no longer qualifies as confidential, whichever occurs first.

5. Governing Law. This clause is governed by the laws of [JURISDICTION].
```

### SLA — Service Level Agreement Core Clause

```
SERVICE LEVELS

1. Availability. Provider shall make the Service available [99.9]% of the time
   in any calendar month ("Uptime Commitment"), excluding Scheduled Maintenance
   and Force Majeure Events.

2. Measurement. Availability is calculated as:
   (Total Minutes − Downtime Minutes) / Total Minutes × 100.
   "Downtime" means the Service is unavailable for more than [5] consecutive
   minutes as measured by Provider's monitoring system.

3. Service Credits. If availability falls below the Uptime Commitment in any
   calendar month, Customer is eligible for the following credits:
   | Availability | Credit (% of monthly fee) |
   |--------------|--------------------------|
   | 99.0–99.9%   | 10%                      |
   | 95.0–99.0%   | 25%                      |
   | < 95.0%      | 50%                      |

4. Credit Procedure. Customer must request credits within [30] days of the
   end of the affected month. Credits are the sole remedy for availability failures.

5. Scheduled Maintenance. Provider will give [48] hours' notice for maintenance
   windows. Scheduled Maintenance does not count as Downtime.
```

### IP Assignment Clause

```
INTELLECTUAL PROPERTY ASSIGNMENT

1. Assignment. Employee/Contractor hereby irrevocably assigns to [COMPANY] all
   right, title, and interest in and to any Work Product, including all patent,
   copyright, trade secret, and other intellectual property rights therein, to
   the maximum extent permitted by applicable law.

2. Work Product. "Work Product" means all inventions, discoveries, improvements,
   developments, software, writings, designs, and other works created, conceived,
   or reduced to practice by Employee/Contractor: (a) during the term of
   engagement; (b) using Company resources; or (c) relating to Company's actual
   or reasonably anticipated business, research, or development.

3. Moral Rights Waiver. To the extent permitted by law, Employee/Contractor
   waives all moral rights in Work Product and consents to any modification,
   adaptation, or exploitation by Company without attribution.

4. Prior Inventions. Schedule A lists all inventions made prior to this Agreement
   that Employee/Contractor wishes to exclude. Absent Schedule A, no exclusions apply.

5. Assistance. Employee/Contractor will execute all documents and take all actions
   reasonably requested to perfect Company's rights under this clause.
```

### Liability Limitation Clause

```
LIMITATION OF LIABILITY

1. Exclusion of Consequential Damages. NEITHER PARTY WILL BE LIABLE TO THE
   OTHER FOR ANY INDIRECT, INCIDENTAL, SPECIAL, PUNITIVE, OR CONSEQUENTIAL
   DAMAGES, OR DAMAGES FOR LOSS OF PROFITS, REVENUE, GOODWILL, OR ANTICIPATED
   SAVINGS, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

2. Cap on Liability. EACH PARTY'S TOTAL CUMULATIVE LIABILITY ARISING OUT OF
   OR RELATED TO THIS AGREEMENT, WHETHER IN CONTRACT, TORT, OR OTHERWISE, WILL
   NOT EXCEED THE GREATER OF: (A) [USD $X,XXX] OR (B) THE AMOUNTS PAID BY
   CUSTOMER TO PROVIDER IN THE [12] MONTHS PRECEDING THE CLAIM.

3. Essential Basis. THE PARTIES ACKNOWLEDGE THAT THE LIMITATIONS IN THIS SECTION
   REFLECT A REASONABLE ALLOCATION OF RISK AND ARE AN ESSENTIAL ELEMENT OF THE
   BASIS OF THE BARGAIN BETWEEN THE PARTIES.

4. Exceptions. The limitations above do not apply to: (a) death or personal
   injury caused by negligence; (b) fraud or fraudulent misrepresentation;
   (c) breaches of confidentiality; or (d) indemnification obligations.
```

### GDPR Data Processing Agreement (DPA) Core Clause

```
DATA PROCESSING AGREEMENT — CORE CLAUSE (Art. 28 GDPR)

1. Processor Obligations. Processor shall process Personal Data only on
   documented instructions of Controller, including with regard to transfers
   of Personal Data to a third country (GDPR Art. 28(3)(a)).

2. Confidentiality. Processor shall ensure that persons authorised to process
   Personal Data have committed themselves to confidentiality or are under an
   appropriate statutory obligation of confidentiality (Art. 28(3)(b)).

3. Security. Processor shall implement measures per Art. 32, including as
   appropriate: (a) pseudonymisation and encryption; (b) ongoing confidentiality,
   integrity, availability assurance; (c) restore capability; (d) regular testing
   and evaluation of security measures.

4. Sub-processors. Processor shall not engage a sub-processor without prior
   specific or general written authorisation of Controller. General authorisation
   requires Processor to notify Controller of intended changes and allow Controller
   [30] days to object. Sub-processors must be bound by equivalent obligations.

5. Data Subject Rights. Processor shall assist Controller to fulfil data subject
   rights requests (Arts. 12–22) within [5] business days of receiving a request.

6. Deletion/Return. Upon termination, Processor shall, at Controller's choice,
   delete or return all Personal Data and delete existing copies unless EU/Member
   State law requires storage.

7. Audit Rights. Processor shall make available to Controller all information
   necessary to demonstrate compliance and allow for and contribute to audits
   and inspections conducted by Controller or an authorised auditor.

8. Governing Law. This DPA is governed by [JURISDICTION] law. Supervisory authority:
   [DPA NAME, e.g., ICO for UK, CNIL for France].
```

---

## Legal Analysis Patterns

### Statutory Interpretation Canons

When a statute's meaning is disputed, apply these canons in order:

1. **Plain Meaning** — If text is unambiguous, apply it as written. *Chevron U.S.A. v. NRDC*, 467 U.S. 837 (1984); *Bostock v. Clayton County*, 590 U.S. 644 (2020).
2. **Whole-Act Rule** — Read provisions in context of the whole statute; avoid surplusage.
3. **Specific over General** (*Generalia specialibus non derogant*) — Specific provision controls over a general one.
4. **Ejusdem Generis** — When a general term follows specific terms, the general term is limited to the same class.
5. **Expressio Unius** — Expression of one excludes others.
6. **Legislative History** — Use only after exhausting textual tools; consult committee reports, floor statements (US); Hansard (UK, *Pepper v Hart* [1993] AC 593).
7. **Remedial Construction** — Remedial statutes construed broadly to effectuate purpose.
8. **Avoidance Canon** — Construe to avoid constitutional doubt when possible.

### Case Synthesis Method

When multiple cases govern an issue:

```
1. List all directly-on-point cases chronologically.
2. Extract the KEY FACT that determined the outcome in each.
3. Identify the governing RULE stated by the court.
4. Note any DISTINCTIONS between cases (factual, doctrinal, procedural).
5. Build a matrix:
   | Case | Key Fact | Outcome | Distinguishing Feature |
6. Apply: map client facts to the case whose key facts are most analogous.
7. Address the best counter-case explicitly — distinguish it or concede the risk.
```

---

## Compliance Memo Templates

### SOC2 Gap Analysis Memo

```
COMPLIANCE MEMORANDUM — SOC2 TYPE II GAP ANALYSIS

To:     CISO / Audit Committee
From:   [Author]
Date:   [Date]
Re:     SOC2 Type II Readiness — [System/Service Name]

EXECUTIVE SUMMARY
[2-3 sentences: overall readiness rating, critical gaps, timeline to remediation.]

SCOPE
Trust Service Criteria: [Security | Availability | Confidentiality | Processing
Integrity | Privacy — select applicable]
Audit Period: [12 months ending DATE]
In-scope systems: [List]

GAP ANALYSIS

| TSC Criterion | Control Description | Status | Gap / Risk | Priority |
|---------------|---------------------|--------|------------|----------|
| CC6.1         | Logical access controls | Partial | MFA not enforced for VPN | High |
| CC7.2         | System monitoring | Pass | — | — |
| A1.1          | Availability capacity mgmt | Fail | No capacity forecast process | Critical |

REMEDIATION ROADMAP
[Table: Gap → Owner → Target Date → Evidence Required]

CONCLUSION
[Recommend proceed / delay audit / engage readiness consultant.]
```

### HIPAA Compliance Memo

```
COMPLIANCE MEMORANDUM — HIPAA SECURITY RULE ANALYSIS

To:     Privacy Officer / Legal Counsel
From:   [Author]
Date:   [Date]
Re:     HIPAA Security Rule compliance — [System/Vendor]

REGULATORY FRAMEWORK
45 C.F.R. §§ 164.302–164.318 (Security Rule)
45 C.F.R. §§ 164.500–164.534 (Privacy Rule)
Applicable to: Covered Entity / Business Associate [select]

ANALYSIS

Administrative Safeguards (§ 164.308)
[ ] Risk analysis conducted and documented (§ 164.308(a)(1)(ii)(A))
[ ] Workforce training on PHI handling (§ 164.308(a)(5))
[ ] Sanctions policy for workforce violations (§ 164.308(a)(1)(ii)(C))

Physical Safeguards (§ 164.310)
[ ] Facility access controls (§ 164.310(a))
[ ] Workstation use policy (§ 164.310(b))

Technical Safeguards (§ 164.312)
[ ] Unique user IDs (§ 164.312(a)(2)(i))
[ ] Audit controls / logs (§ 164.312(b))
[ ] Transmission encryption (§ 164.312(e)(1))

BAA STATUS
Business Associate Agreement in place: [Yes / No / Pending]
BAA must include 45 C.F.R. § 164.504(e) provisions.

GAPS AND RECOMMENDATIONS
[Table: Requirement → Current State → Gap → Remediation → Owner]

CONCLUSION
[Compliant / Non-compliant / Partial. Estimated breach risk if unaddressed.]
```

### GDPR Compliance Memo

```
COMPLIANCE MEMORANDUM — GDPR PROCESSING ACTIVITY REVIEW

To:     DPO / Legal Counsel
From:   [Author]
Date:   [Date]
Re:     GDPR Article 30 Record — [Processing Activity Name]

PROCESSING ACTIVITY DETAILS
Controller: [Entity name, contact]
Purpose: [Specific, explicit purpose — Art. 5(1)(b)]
Legal Basis: Art. 6(1)([a/b/c/d/e/f]) — [explain]
Special Category Basis (if applicable): Art. 9(2)([a-j])
Data Subjects: [Categories, estimated count]
Data Categories: [Types of personal data]
Recipients: [Internal teams, processors, third countries]
Retention Period: [Specific period with justification — Art. 5(1)(e)]
International Transfers: [Art. 46 mechanism: SCCs / Adequacy / BCRs]

RISK ASSESSMENT
DPIA Required (Art. 35)? [Yes / No — justify using EDPB Guidelines 09/2022]
Residual Risks: [List]

COMPLIANCE STATUS
[ ] RoPA entry created (Art. 30)
[ ] Privacy notice updated (Arts. 13/14)
[ ] DPIA completed (if required)
[ ] Data subject rights mechanism in place (Arts. 15-22)
[ ] DPA notified (if high-risk Art. 35(4))

RECOMMENDATION
[Approve / Require modifications / Suspend processing]
```

### CCPA Compliance Memo

```
COMPLIANCE MEMORANDUM — CCPA/CPRA COMPLIANCE REVIEW

To:     Privacy Counsel / CCO
From:   [Author]
Date:   [Date]
Re:     CCPA/CPRA — [Business Practice / Data Flow]

GOVERNING LAW
Cal. Civ. Code §§ 1798.100–1798.199.100 (CCPA as amended by CPRA)
Cal. Code Regs. tit. 11, §§ 7000–7304 (CPRA Regulations)

THRESHOLD ANALYSIS
Business qualifies as "Business" under § 1798.140(d) if:
[ ] Annual gross revenue > $25M
[ ] Buys/sells/receives/shares PI of ≥ 100,000 consumers or households
[ ] Derives ≥ 50% of revenue from selling/sharing PI

CONSUMER RIGHTS CHECKLIST (§§ 1798.100–1798.125)
[ ] Right to Know (categories + specific pieces)
[ ] Right to Delete (with exceptions)
[ ] Right to Correct (CPRA addition)
[ ] Right to Opt-Out of Sale/Sharing
[ ] Right to Limit Use of Sensitive PI (CPRA)
[ ] Right to Non-Discrimination

REQUIRED NOTICES
[ ] Privacy Policy updated — disclose all categories collected/sold/shared
[ ] "Do Not Sell or Share My Personal Information" link prominent
[ ] Notice at Collection at point of collection

GAPS AND RECOMMENDATIONS
[Table: Requirement → Gap → Owner → Deadline]

CONCLUSION
[Compliant / Non-compliant. Penalty exposure: up to $7,500/intentional violation (§ 1798.155).]
```

---

## Core Workflow

1. **Clarify the legal question** — Identify jurisdiction, governing law, and specific question
2. **Select template** — US Federal / UK / EU/GDPR based on jurisdiction
3. **Identify applicable rules** — Statutes, regulations, binding case law, persuasive authority
4. **Apply citation standard** — Bluebook (US), OSCOLA (UK), GDPR citation style (EU)
5. **Analyze facts against rules** — Use IRAC or CREAC; address both favorable and unfavorable authority
6. **Draft** — Follow template structure; use plain professional language
7. **Clause insertion if needed** — Pull from Contract Clause Library for transactional work
8. **Review** — Confirm citations are plausible (note if AI-generated and require verification)
9. **Output** — Return as formatted markdown or plain text

## Important Caveats

- Always include disclaimer: *"This memo is for informational purposes and does not constitute legal advice. All citations must be independently verified."*
- Never fabricate specific case citations — if unsure, use `[citation needed]`
- Flag jurisdictional uncertainty explicitly
- If the question requires licensed legal advice, note this clearly
- GDPR memos: always recommend engaging a qualified DPO for final review

## Tone and Style

- Formal, precise, objective in fact section
- Analytical but direct in discussion
- Active voice preferred; avoid hedging language in conclusions
- Short paragraphs; use headers for each IRAC/CREAC section
- All-caps for conclusion headings in US court-style memos; sentence case for client memos
