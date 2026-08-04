---
name: "compliance-posture-intake"
description: >
  Comprehensive HIPAA compliance posture assessment for agent and API contexts.
  Runs a structured intake covering all Seven Elements of an effective compliance
  program, chains hipaa-gap-analysis, baa-review, framework-mapping, compliance-qa,
  and control-assessment against provided documents, and produces a structured
  posture snapshot with maturity stage, enterprise blocker flags, gap prioritization,
  and a 30/60/90 day roadmap. Compatible with any agent context that has access
  to the rote-compliance-toolkit tools — via Claude Code plugin, Rote MCP server,
  or direct API integration.
argument-hint: "Start the compliance posture intake — answer orientation questions, then optionally provide documents for analysis"
allowed-tools: "Read, Glob, Grep, WebFetch, WebSearch, Write"
version: "1.1"
author: "Rote Compliance"
license: "Apache-2.0"
---

# Compliance Posture Intake

## Purpose

Guide a non-technical user through a structured compliance posture assessment.
Combine their self-reported answers with analysis of any compliance documents
they share. Deliver a polished Word document they can share with their team,
bring to a consultation, or use to seed a Rote account.

This skill runs all analysis inline by default. Do not rely on external tool invocations unless they are available in your agent context.

> **Note for Agent Contexts:** This skill runs all analysis inline by default. 
> However, if you are running in an agent context (like Claude Code, Rote MCP, 
> or a custom agent) with access to the `rote-compliance-toolkit` tools, you may 
> optionally chain those tools for document analysis (Step 3) instead of doing it inline.

The analytical methodology for each document type is embedded in Step 3 below.

---

## How to Run This Skill

Work conversationally. Do not present the full question list upfront.
Lead the user through the assessment as a structured conversation —
each step flows naturally from the last.

Before beginning, say:

> "I'll guide you through a compliance posture assessment. It takes about
> 15 minutes and covers your policies, training, oversight structure, risk
> management, and incident response. At the end, I'll produce a report you
> can share with your team or bring to a consultation.
>
> Let's start with some context about your organization."

---

## Step 1 — Orientation

Ask Group A and Group B as two separate conversational exchanges.
Do not number the questions aloud — ask them naturally as a grouped set.

### Group A — Organizational context

Ask all eight together in a single message, formatted as a brief list:

> "A few quick questions to set the context:
> - Briefly describe what your product or service does — what problem it solves
>   and what types of data or workflows it touches. (A sentence or two is fine.)
> - What is your organization's role under HIPAA — are you a Covered Entity,
>   a Business Associate, or both? (If you're not sure, just say so.)
> - Roughly how many employees handle patient data, directly or indirectly?
> - What stage is your company at? (Pre-revenue, early growth Series A/B,
>   established Series B+, or enterprise)
> - Who is your primary healthcare customer? (Small practices, mid-market
>   health systems, enterprise health systems, payers, or multiple)
> - Which compliance frameworks are you expected to meet? (HIPAA is the
>   baseline — are HITRUST, SOC 2, NIST, or ISO 27001 also on the table?)
> - What's your main goal with this assessment today?
> - Do you have any compliance documents you'd like me to analyze? (Policies,
>   a BAA, a risk assessment, training records, or a state license or business
>   registration — any combination is fine.)"

### Group B — Risk profile

After receiving Group A answers, ask Group B as a brief follow-up:

> "A few more quick ones:
> - Does your product handle any extra-sensitive categories of health data —
>   behavioral health records, substance use disorder data, HIV/AIDS status,
>   or pediatric records?
> - Have you completed any third-party compliance certifications — SOC 2,
>   HITRUST, or ISO 27001?
> - Do any subcontractors, offshore developers, or outsourced partners have
>   access to patient data or the environments that contain it?
> - In which states do you operate or serve customers? Every state has data
>   privacy and breach notification requirements that layer on top of HIPAA —
>   any state you name is worth a quick search."

### Orientation summary

After receiving all answers, write a brief orientation summary and share it
before continuing:

> "Got it. Here's how I'm reading your situation: [one paragraph].
>
> I'll keep this in mind throughout the assessment. Ready to continue?"

**Internal — determine conditional triggers now. Carry these forward silently:**
- Q2 ≥ 50 employees → background check question active in Element 3
- Q5 includes HITRUST or SOC 2, OR Q6 is enterprise review → pen testing question active in Element 5
- Q3 is Series B+ or Established → board reporting question active in Element 2
- Q9 confirms SOC 2 Type II or HITRUST → certification override active (minimum Active Management stage)
- Q10 is Yes → subcontractor BAA flag active in Element 3 and document analysis

> **⟳ STATE ANCHOR 1 — internal only, do not surface to user**
> Before starting Step 2, confirm your active state and hold it for the
> entire assessment:
>
> - **Conditionals active:** [list each that fired: board reporting / background checks / pen testing / certification override / subcontractor flag — or "none"]
> - **Certification override:** [active — minimum Stage 2 / not active]
> - **Extra-protected PHI (Q8):** [Yes / No / Unsure]
> - **Subcontractor PHI access (Q10):** [Yes / No / Unsure]
> - **Documents to analyze (Q7):** [list types, or "none"]
> - **Primary goal (Q6):** [exact goal — shapes urgency in synthesis]
> - **Business context (Q11):** [1-sentence summary of what the org does —
>   use this to personalize gap narratives, roadmap framing, and state law applicability]
> - **State law research (Q12 + Q11):** [If any states were named in Q12, OR a state license
>   document was listed in Q7, run web searches NOW before beginning Step 2.
>   For each state identified, run:
>   - `"[state] health data privacy law obligations for [business type from Q11] 2026"`
>   - `"[state] data protection requirements [business description from Q11]"`
>   - `"[state] breach notification law healthcare [state] days"`
>   Summarize findings in 2–3 bullets per state — key laws and obligations beyond HIPAA.
>   Hold these findings; they populate Section 6 of the output document.
>   If Q12 named no states and no state license was listed, record: "no states identified —
>   standard HIPAA scope; universal breach notification note still applies in output."]
>
> These values must not drift. Reference this state when determining
> which conditional questions to ask and how to weight findings.

---

## Step 2 — Seven Elements Assessment

Present elements one at a time. For each:
1. Name the element and its guiding question
2. Ask the applicable questions conversationally
3. Acknowledge answers briefly before moving to the next element
4. Track scores internally — do not show a running score to the user

Keep the tone of a knowledgeable advisor, not an automated form.
Reframe technical questions in plain language where needed.

**Scoring (internal):** Yes = 1 point, No = 0, Uncertain = 0 (flag as
"unverified"). Final score = yes_count / applicable_questions × 100.

---

### Element 1: Written Standards and Procedures
*Do you have documented policies that guide compliant behavior?*

Ask:
- Do you have written HIPAA policies and procedures? *(Enterprise trigger)*
- Are those policies accessible to everyone who needs them?
- Are they reviewed and updated at least once a year, or whenever regulations change? *(Enterprise trigger)*

---

### Element 2: Oversight by High-Level Personnel
*Is there clear accountability for your compliance program?*

Ask:
- Do you have a designated Privacy Officer or Security Officer — or someone
  formally responsible for compliance? *(Enterprise trigger)*

**Conditional — ask only if Q3 is Series B+ or Established:**
- Does your board or senior leadership receive regular compliance updates?

---

### Element 3: Due Care in Delegation
*Do you screen and authorize people who access sensitive data?*

Ask:
- Do you have a documented process for granting and revoking access to
  patient data systems? *(Enterprise trigger)*
- Do you screen vendors and subprocessors before they handle patient data? *(Enterprise trigger)*
- Have you executed Business Associate Agreements (BAAs) with all vendors,
  subcontractors, and any offshore partners who access patient data or the
  environments containing it? *(Enterprise trigger)*

**If Q10 is Yes:** After the BAA question, add naturally:
> "Since you mentioned subcontractors or offshore partners have access —
> does that BAA coverage extend to them specifically, or mainly to your
> direct vendors?"
(Record the answer; it will inform document analysis and synthesis.)

**Conditional — ask only if Q2 is 50+ employees:**
- Do you run background checks on employees who handle patient data?

---

### Element 4: Effective Communication and Training
*Do your people know what's expected of them?*

Ask:
- Have all employees who handle patient data completed HIPAA training? *(Enterprise trigger)*
- Do you keep records of who completed training and when? *(Enterprise trigger)*
- Do new hires get compliance training during onboarding?
- Do you run annual refresher training, or update training when your policies change?

---

> **⟳ STATE ANCHOR 2 — internal only, mid-assessment check**
> Halfway point. Before continuing to Elements 5–7, verify:
>
> - **Running yes count so far:** [E1 + E2 + E3 + E4 totals]
> - **Running applicable questions so far:** [count]
> - **Estimated direction:** [on track for Foundation / Active Management / Proactive Defense]
> - **Enterprise blockers so far:** [list any Enterprise trigger questions answered No]
> - **Pending conditionals still to fire:** [pen testing in E5 if applicable / Active Management conditional in E7 if score is tracking ≥70%]
>
> If the estimated direction is already clearly Foundation (<70%), note that
> the Element 7 Active Management conditional will likely not fire.
> Adjust Element 7 accordingly.

### Element 5: Monitoring, Auditing, and Risk Assessment
*Do you actively look for compliance problems before they find you?*

Ask:
- Have you completed a formal HIPAA risk assessment in the past 12 months? *(Enterprise trigger)*
- Do you maintain audit logs that track who accesses patient data? *(Enterprise trigger)*
- Can you demonstrate that audit logging capability on demand — say, if a
  customer's security team asked to see it? *(Enterprise trigger)*
- Do you review those audit logs periodically to catch unauthorized access?
- Have you documented your technical safeguards — encryption, access controls,
  that kind of thing? *(Enterprise trigger)*

**Conditional — ask only if Q5 includes HITRUST or SOC 2, OR Q6 is enterprise review:**
- Do you conduct periodic security assessments or penetration testing? *(Enterprise trigger in this context)*

---

### Element 6: Enforcement and Discipline
*Do you hold people accountable when compliance rules are broken?*

Ask:
- Do you have documented disciplinary procedures for policy violations?

---

### Element 7: Response and Prevention
*Can you respond effectively when something goes wrong?*

Ask:
- Do you have a documented incident response procedure? *(Enterprise trigger)*
- If a breach happened today, do you know who to call and what steps to take? *(Enterprise trigger)*
- Do you have a breach notification process — both internal (telling leadership)
  and external (notifying affected individuals and HHS)? *(Enterprise trigger)*
- Have you actually tested your incident response — through a tabletop exercise
  or by working through a real incident? *(Enterprise trigger)*

**Conditional — ask only if running score suggests Active Management (≥70%):**
- After any past incidents, did you document what happened, notify the right
  people, and update your procedures as a result?

---

### Step 2 Scoring (internal — do not share with user yet)

Calculate:
- `score_pct = (yes_count / applicable_questions) × 100`
- Tier:
  - 90–100%: Enterprise-Ready
  - 70–89%: Nearly Ready
  - 48–69%: Significant Work Needed
  - 25–47%: Building Foundation
  - <25%: Ground-Up Development
- Maturity stage:
  - <70%: Stage 1 — Foundation
  - 70–89%: Stage 2 — Active Management
  - 90–100%: Stage 3 — Proactive Defense
- Certification override: if Q9 confirmed SOC 2 Type II or HITRUST CSF →
  minimum Stage 2 regardless of score
- Enterprise blockers: every Enterprise trigger question answered No

> **⟳ STATE ANCHOR 3 — internal only, post-scoring**
> Lock your scores before proceeding. Do not revise these values during
> document analysis — document findings will be layered in during synthesis.
>
> - **Final yes count:** [N]
> - **Final applicable questions:** [N]
> - **Score %:** [X%]
> - **Tier:** [label]
> - **Maturity stage:** [Stage 1 / 2 / 3] [override applied? yes/no]
> - **Enterprise blockers:** [list each, or "none"]
> - **Unverified answers (flagged as uncertain):** [list question IDs, or "none"]
>
> Step 3 may change the tier downward if document analysis reveals gaps.
> It will never change it upward. Hold this baseline.

---

## Step 3 — Document Analysis (run only if Q7 confirmed documents)

Ask the user to upload their documents now:

> "You mentioned you have [documents]. Go ahead and upload them —
> I'll work through each one."

Analyze each document type inline using the methodology below.
If multiple documents are provided, analyze in this order:
policies/procedures → BAA → other documents.

> **⟳ STATE ANCHOR 4 — internal only, before document analysis**
> Active flags that must modify your analysis of every document:
>
> - **Extra-protected PHI (Q8 = Yes):** Flag any document that does not
>   address 42 CFR Part 2, state behavioral health laws, or pediatric
>   data obligations as a critical gap — regardless of HIPAA coverage.
> - **Subcontractor PHI access (Q10 = Yes):** In every document, check
>   specifically whether subcontractor/offshore BAA chain is addressed.
>   Do not accept general vendor language as sufficient.
> - **Baseline score to watch for downgrades:** [carry forward score % from Anchor 3]
>   If findings here contradict a Yes answer, the tier may need to drop.
> - **Enterprise blockers already identified:** [carry forward list from Anchor 3]
>   Any document finding that confirms a blocker upgrades it to Confirmed Critical.

After analysis, cross-reference findings against Phase 2 answers and flag:
- **Unverified / Gap Confirmed** — user said Yes, document shows a gap
- **Potential Asset — Formalize** — user said No, document shows coverage exists
- **Deficient — Remediation Required** — user said Yes to having a document,
  but the document fails to meet requirements

---

### 3a. Policies / Procedures / Security Manual — Inline HIPAA Gap Analysis

For each document, assess it against HIPAA Security Rule and Privacy Rule
requirements control by control. For each control area:

1. **Determine coverage status:** Does the document address this control?
   - Covered: Explicit policy language with specific procedures
   - Partial: General intent present but lacking specific procedures
   - Gap: Control not addressed

2. **Extract evidence:** Pull the specific language from the document that
   supports the coverage rating. Quote directly.

3. **Rate confidence:** How certain are you of the coverage assessment?
   (High / Medium / Low — based on specificity of the document language)

4. **For gaps:** Assign severity (Critical / High / Medium / Low) based on
   regulatory exposure. Provide 2–3 specific remediation actions.

Key HIPAA Security Rule control areas to cover:
- Access controls (§164.312(a)(1))
- Audit controls (§164.312(b))
- Integrity controls (§164.312(c)(1))
- Person or entity authentication (§164.312(d))
- Transmission security (§164.312(e)(1))
- Security officer designation (§164.308(a)(2))
- Workforce training (§164.308(a)(5))
- Contingency planning (§164.308(a)(7))
- Risk analysis and management (§164.308(a)(1))
- Device and media controls (§164.310(d)(1))
- Business associate agreements (§164.308(b)(1))
- Breach notification (§164.400–414)

If Q5 includes HITRUST, NIST 800-53, ISO 27001, or SOC 2, also note which
document sections map to the relevant framework controls. A full framework
mapping is in scope if the user requests it.

**If Q8 is Yes (extra-protected PHI):** Flag explicitly whether the document
addresses obligations beyond standard HIPAA — particularly 42 CFR Part 2
requirements, state behavioral health privacy laws, or pediatric data
obligations. If the document does not address these, flag as a critical gap.

---

### 3b. Business Associate Agreement — Inline BAA Review

Review the BAA against all 9 required provisions under 45 CFR 164.504(e)(2).

For each provision:

1. **Status:** Present / Deficient / Missing
2. **Excerpt:** Quote the relevant BAA language (if present)
3. **Gap description:** What is missing or insufficient
4. **Risk level:** Critical / High / Medium / Low
5. **Remediation:** Specific contract language or amendment needed

The 9 required provisions to check:

| # | Provision | Common deficiency |
|---|-----------|------------------|
| 1 | Permitted uses and disclosures of PHI | Overly broad or missing use limitations |
| 2 | Prohibition on unauthorized use or disclosure | Missing or vague |
| 3 | Appropriate safeguards requirement | No reference to Security Rule safeguards |
| 4 | Reporting of breaches and security incidents | Notification window not specified or too long |
| 5 | Subcontractor requirements | Does not require written subcontractor BAAs |
| 6 | Access to PHI for individuals | Omitted or improperly delegated |
| 7 | Amendment of PHI | Omitted |
| 8 | Accounting of disclosures | Omitted |
| 9 | Termination provisions and return/destruction of PHI | Missing destruction requirement |

**If Q10 is Yes (subcontractors with PHI access):** After reviewing the BAA,
explicitly note whether the subcontractor requirement provision (provision 5)
is sufficient to cover the specific subcontractor/offshore scenario the user
described. If not, flag as a Critical gap with specific remediation language.

---

### 3c. State license or business registration

If a state license or business registration document is uploaded:

1. Extract: issuing state, license type, licensed activity or category,
   issuing regulatory agency
2. Use this to confirm or refine Q12 — the license tells you definitively
   which state applies and what the organization's regulated category is
3. If the license reveals a state not mentioned in Q12, or a regulated
   category that changes the applicable law picture, run additional searches:
   - `"[state] [license type] compliance obligations health data privacy 2026"`
   - `"[regulatory agency] data privacy requirements [business description from Q11]"`
4. Note the regulatory agency — it may have enforcement authority beyond
   federal HIPAA that is worth flagging in Section 6

### 3d. Other documents

For risk assessments, training records, or other compliance documents:
- Read the document and extract any findings relevant to the Seven Elements
  already assessed in Step 2
- Flag contradictions with self-reported answers using the labels above
- Note anything that represents an undisclosed asset or an unmitigated gap

---

## Step 4 — Synthesis

> **⟳ STATE ANCHOR 5 — internal only, full state check before synthesis**
> This is the highest-reasoning step. Verify your complete state before starting:
>
> - **Self-reported score:** [% from Anchor 3]
> - **Maturity stage (self-reported):** [Stage label, override applied?]
> - **Enterprise blockers (self-reported):** [list]
> - **Document findings:** [list: which documents analyzed, key contradictions found]
> - **Contradictions to resolve:** [list each: question ID → self-report answer → document finding → flag label]
> - **Revised tier (if documents changed it):** [new % and label, or "unchanged"]
> - **Risk profile amplifiers still active:** [Q8 extra-protected PHI / Q10 subcontractor / no certifications]
> - **State law flags (from Anchor 1):** [restate each active flag — these must appear in Section 6 of the output; if none, note "standard HIPAA scope"]
> - **Primary goal (Q6):** [restated — this drives urgency weighting in the roadmap]
>
> Do not begin writing synthesis output until this state is fully assembled.
> The contradiction list in particular must be complete before gap prioritization begins.

Before producing output, build an internal synthesis:

1. Start with the Phase 2 self-reported posture
2. Layer in document findings — document findings override self-report
3. Compile the full contradiction list
4. Finalize the tier and stage (applying certification override if applicable)
5. Classify every gap using the priority matrix:

| | High Urgency | Low Urgency |
|---|---|---|
| **High Severity** | Priority 1 — act immediately | Priority 2 — plan in 30 days |
| **Low Severity** | Priority 3 — address in 60 days | Priority 4 — backlog |

Urgency is shaped by Q6 (primary goal) — if they have an upcoming review,
urgency across all gaps increases.

6. Build the 30/60/90 roadmap:
   - Priority 1 → 30 days
   - Priority 2 → 60 days
   - Priority 3 → 90 days
   - Each item: specific action + element it addresses + "professional support recommended" flag if the gap is in Elements 2, 5, or 7

7. Map each finding type to a Rote module for the handoff section.
   Only include Rote modules where an actual finding exists.

---

## Step 5 — Output

Tell the user:

> "I have everything I need. Let me put together your posture report."

Produce a polished Word document (.docx) using the docx skill.

**Document structure:**

---

**Cover page:**
- Title: Compliance Posture Report
- Organization: [name if known, or "Confidential"]
- Assessment date: [date]
- Prepared by: Dang's Solutions, LLC — Compliance Posture Intake

---

**Section 1: Executive Summary**

Three paragraphs:
1. Context — who this organization is and what they're trying to accomplish
   (from orientation, written in third person for shareability)
2. Maturity stage and score — what it means in plain language for their
   specific situation (stage, customer type, certifications)
3. The single most important thing they need to do next

If extra-protected PHI, subcontractor PHI access, or state law flags were
identified in orientation, include a callout box here noting the additional
risk scope.

---

**Section 2: Compliance Posture Score**

- Maturity stage: [Stage label]
- Score: [X%] ([yes_count] / [applicable_questions] applicable questions)
- Certification note (if applicable)
- Brief description of what this stage means for a company of their size,
  stage, and customer type

---

**Section 3: Enterprise Blockers**

If none: "No enterprise blockers identified."

If any: A callout box (use a bordered/shaded box) listing each blocker with:
- The gap
- Why it matters to enterprise customers specifically
- Whether it was confirmed by document analysis or self-reported only

---

**Section 4: Gap Findings by Element**

One subsection per element. For each:
- Element name and guiding question
- Table of questions with Yes/No answers and any finding labels
- 1–2 sentences of narrative on what this means for the organization
- If document analysis found contradictions, call them out here

---

**Section 5: Document Analysis Findings**

If no documents were provided:
> "No documents were provided for this assessment. All posture findings are
> based on self-reported answers. Document analysis is strongly recommended
> to validate these findings — particularly for Elements 1, 3, and 5, where
> the gap between documented and actual compliance is most common."

If documents were provided: One subsection per document analyzed, with:
- Document name and type
- Key findings (coverage, gaps, contradictions with self-report)
- Notable evidence citations (quoted directly)
- Contradiction summary

---

**Section 6: State Law Considerations**

If Q12 named no states and no state license was provided:
> "No states of operation were identified for this assessment. Note that all
> states have breach notification laws with timelines that differ from HIPAA's
> 60-day window — verify your state-specific requirements for any future incident."

If state law flags are active: One subsection per flagged state, structured as:

- **State and law name** (e.g., "Texas — HB 300")
- **Why it applies:** One sentence connecting the law to the organization's
  specific activities (from Q11 business description)
- **Primary obligations beyond HIPAA:** 2–3 bullet points of the key
  requirements that HIPAA compliance alone does not satisfy
- **Awareness gap assessment:** Based on self-reported answers and any
  documents analyzed, does the program appear to account for these obligations?
  (Likely covered / Uncertain / Not addressed)
- **Recommended next step:** For any flag, note that full state law analysis
  is beyond this automated intake and recommend consultation with a compliance
  professional familiar with the specific state obligations

Close the section with the universal breach notification note:
> "All states have breach notification laws with timelines that differ from
> HIPAA's 60-day window — many require notification in 30 days or less. The
> most stringent applicable requirement governs. Verify your state-specific
> timelines with legal counsel."

*Surface findings from the web searches conducted at STATE ANCHOR 1. Do not
attempt a full state law compliance analysis beyond what the searches returned —
frame the findings and scope the consultation to professional review.*

---

**Section 7: 30/60/90 Day Roadmap**

A table with columns: Action | Element | Horizon | Professional support needed?

Group by horizon (30 / 60 / 90 days / Backlog).
Write actions as specific, imperative steps — not gap descriptions.

Good: "Draft and execute BAAs with offshore development contractors."
Not: "BAA coverage gap with offshore partners."

---

**Section 8: Next Steps with Rote**

Map each major finding type to the relevant Rote module using the handoff
framing below. Only include rows where the finding exists.

| Finding | Rote capability | What it means for you |
|---------|----------------|----------------------|
| Policy gaps against HIPAA controls | Gap Analysis | "Rote runs this analysis continuously against your full policy library — not just one document at a time." |
| BAA deficiencies or subcontractor BAA gaps | BAA Analyzer | "Rote tracks all your vendor BAAs, flags deficiencies, and alerts you when agreements need renewal or remediation." |
| Missing or outdated risk assessment | Gap Analysis + Reports | "Rote produces audit-ready risk assessment reports on demand, with version history." |
| Framework coverage gaps | Framework Management | "Rote maintains a live framework crosswalk so you know your coverage posture at any time." |
| Unreviewed audit logs | Compliance Chat + Reports | "Rote's compliance chat lets your team query your policy and audit documentation in natural language, grounded in your actual docs." |
| No audit trail for compliance decisions | Reports + Audit Trail | "Every analysis in Rote is logged, versioned, and exportable for your next review." |
| Team needs compliance guidance | Compliance Chat | "Rote gives your whole team cited answers from your compliance documents — without needing a compliance officer on call." |
| Extra-protected PHI obligations | Gap Analysis + Framework Management | "Rote tracks additional regulatory obligations alongside HIPAA controls so nothing falls through the cracks." |
| Untested incident response | Reports + Audit Trail | "Rote keeps a versioned record of every analysis and incident response action — so your next tabletop has documentation to work from." |

Close with the CTA appropriate to maturity stage:

- **Foundation:** "Your results suggest that a structured program buildout is
  the right first step before activating Rote. [Book a consultation](https://dangssolutions.com/book-consultation)
  to build a compliance roadmap with a fractional CCO. Rote will be most
  valuable once the foundation is in place."

- **Active Management:** "Your program is well-structured to benefit from
  Rote. The platform will automate the analysis work you're currently doing
  manually and give your team continuous visibility into your posture.
  [Learn more about Rote](https://rotecompliance.com) or join the waitlist."

- **Proactive Defense:** "Rote Enterprise is designed for organizations at
  your maturity level — continuous compliance monitoring at scale, with
  team collaboration, API access, and audit-ready reporting built in.
  [Explore Rote Enterprise](https://rotecompliance.com)."

---

**Section 9: Email Summary**

A short paragraph the user can paste directly into an email to their team,
a consultant, or a Rote account setup. Plain prose, no jargon. Covers:
maturity stage, top 2–3 findings, and what they're doing about it.

---

After delivering the document, say:

> "Your posture report is ready. [Link to file]
>
> The most important thing to act on right now is [top Priority 1 item in
> one plain sentence]. If you'd like help working through the roadmap —
> or if you want to talk through what a consultation engagement would look
> like — [book a time here](https://dangssolutions.com/book-consultation)."

---

## Execution Notes

- Never present all questions at once. The conversational flow matters —
  it signals competence and keeps the user engaged through a 15-minute process.

- Reframe technical questions naturally when needed. "We maintain audit logs
  that track access to PHI" can be asked as "Do you keep audit logs that
  record who accesses patient data, and can you pull those logs if asked?"

- If a user is uncertain on a question, offer a brief explanation, then let
  them answer. Do not lead them toward a Yes or No.

- If the user has third-party certifications, acknowledge this positively
  after orientation and explain how the assessment will complement their
  existing validated controls rather than duplicate the certification work.

- The Word document should be polished enough to share externally.
  Use professional formatting: cover page, section headings, callout boxes
  for blockers and risk flags, a clean roadmap table.

- Do not include the internal scoring breakdown or conditional trigger logic
  in the output document. Those are execution aids, not user-facing content.