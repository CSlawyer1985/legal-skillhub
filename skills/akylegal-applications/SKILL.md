---
name: akylegal-applications
description: "Comprehensive legal applications skill covering civil/criminal/administrative litigation workflows, trial defense strategies, legal document drafting (complaints, answers, appeals, retrial petitions, enforcement applications, representation opinions, defense statements, legal opinions, etc.), arbitration (commercial & labor), mediation, enforcement procedures, evidence rules, and litigation risk assessment. Trigger when users ask about: lawsuit/litigation/trial, legal documents, court defense, evidence/cross-examination, arbitration, enforcement, legal strategy, filing a case, appeal, retrial, representation, pleading, or any legal procedural guidance."
---

# Comprehensive Legal Applications (全维法律应用技能包)

A comprehensive legal practice skill covering the full lifecycle from case intake to enforcement. This skill complements existing legal skills (contract review, criminal defense, labor law, due diligence, etc.) with a focus on litigation practice and legal document drafting.

---

## I. Skill Architecture

```
Comprehensive Legal Applications
├── Litigation Workflows       → Civil / Criminal / Administrative
├── Trial Practice             → Court Preparation / Defense / Cross-Examination
├── Legal Document Drafting    → Complaints / Answers / Appeals / Opinions
├── Non-Contentious Procedures → Arbitration / Mediation / Admin Review
├── Enforcement                → Execution Applications / Objections
└── Litigation Strategy        → Risk Assessment / Cost-Benefit Analysis
```

---

## II. Core Workflows

### Workflow A: Litigation Procedure Guidance

When the user needs procedural guidance for civil, criminal, or administrative litigation:

```
Step 1: Identify case type
    ├── Civil dispute → Read references/civil-procedure.md
    ├── Criminal case → Read references/criminal-procedure.md
    └── Admin dispute → Read references/admin-procedure.md

Step 2: Determine current stage
    ├── Pre-filing → Evidence collection + pre-action preservation + jurisdiction
    ├── Filing → Filing materials checklist + jurisdiction rules
    ├── First instance → Evidence deadlines + trial prep + cross-examination plan
    ├── Appeal → Appeal deadline: 15 days(civil)/10 days(criminal) + draft appeal
    ├── Retrial → Apply within 6 months + retrial grounds analysis
    └── Enforcement → Enforcement application + objections

Step 3: Output stage-specific guidance
    - Time limits and deadlines for this stage
    - Required documents
    - Key legal risk warnings
    - Strategic recommendations
```

### Workflow B: Trial Defense & Cross-Examination

When the user needs to prepare for trial, needs defense strategy, or cross-examination plans:

```
Step 1: Identify trial type and role
    ├── Plaintiff/Prosecution: Claims + evidence presentation + cross-examination
    ├── Defendant/Defense: Defense + evidence + cross-examination
    └── Third party / Appellant / Respondent: Role-specific strategy

Step 2: Generate trial plan based on role
    Plaintiff/Prosecution:
        - Core claims → evidence list → examination outline
        - Anticipate defense counterarguments → prepare rebuttals
        - Predict trial focus points → outline closing arguments

    Defendant/Defense:
        - Core defense position → cross-examination plan
        - Analyze plaintiff's evidence on three dimensions (authenticity/legality/relevance)
        - Prepare counter-evidence / corroborating evidence

    General preparation:
        - Questioning outlines (for opposing party/witnesses/experts)
        - Legal authority index (compiled statutes)
        - Comparable case research report (to persuade judge)

Step 3: Generate trial document package
    └── See Legal Document Drafting and references/trial-practice.md
```

### Workflow C: Legal Document Drafting

When the user needs to draft legal documents, select the template by document type:

| Document Type | Reference | Approach |
|---------------|-----------|----------|
| Civil Complaint | references/legal-document-templates.md → Complaint | Extract case elements → Fill template → Verify legal basis |
| Civil Answer | references/legal-document-templates.md → Answer | Respond to complaint point by point |
| Appeal | references/legal-document-templates.md → Appeal | Note deadline + appeal request + facts & reasons |
| Retrial Petition | references/legal-document-templates.md → Retrial | 6-month deadline check + cite statutory retrial grounds |
| Representation/Defense Statement | references/legal-document-templates.md → Representation | Trial focus + factual argument + legal application |
| Enforcement Application | references/legal-document-templates.md → Enforcement | Final judgment + debtor's asset leads |
| Asset Preservation Application | references/legal-document-templates.md → Preservation | Security method + scope of preservation |
| Jurisdictional Objection | references/legal-document-templates.md → Jurisdiction | Jurisdiction rules + objection grounds |
| Evidence Investigation Application | references/legal-document-templates.md → Investigation | Evidence leads + application reasons |
| Enforcement Objection | references/legal-document-templates.md → Objection | Objection type analysis + statutory grounds |
| Cross-Examination Opinion | references/legal-document-templates.md → Cross-Examination | Three-dimensional evidence analysis |
| Legal Opinion | references/legal-document-templates.md → Legal Opinion | Facts → Legal analysis → Conclusion & recommendations |

**General drafting rules:**
1. Collect essential case elements (party info, cause of action, facts, relief sought)
2. Follow correct document format (court name, case number, requests, facts & reasons)
3. Verify statute of limitations / appeal deadlines / application deadlines
4. Cite precise legal provisions (full name + article number)
5. Provide review checklist after draft completion

### Workflow D: Arbitration Procedure Guidance

When the user needs arbitration procedure guidance or to draft arbitration documents:

```
Step 1: Identify arbitration type
    ├── Commercial arbitration (contracts / other commercial disputes)
    ├── Labor arbitration (mandatory pre-litigation procedure)
    └── International arbitration (cross-border parties / international rules)

Step 2: Verify arbitration foundation
    ├── Is there a valid arbitration agreement?
    ├── Does the agreement specify a clear arbitration institution?
    └── Is the dispute within the scope of arbitrable matters?
        → If no valid agreement, recommend litigation route

Step 3: Guide arbitration process
    ├── Application → Draft arbitration application materials
    ├── Tribunal formation → Select arbitrators / sole arbitrator
    ├── Hearing → Evidence + examination + written/oral hearing
    ├── Award → Award types / finality of award
    └── Post-award remedies → Set aside / enforcement / non-enforcement
        → See references/arbitration.md

Step 4: Distinguish labor arbitration
    ├── Labor arbitration is a mandatory prerequisite to litigation
    ├── No arbitration agreement needed; apply directly to labor arbitration committee
    ├── 1-year statute of limitations
    ├── No fee
    ├── After award, if dissatisfied → sue in court within 15 days
    └── See references/arbitration.md → Labor Arbitration section
```

### Workflow E: Litigation Strategy Assessment

When the user needs to make a "litigation decision" assessment:

```
Step 1: Case facts review
    ├── Party information
    ├── Key timeline
    ├── Core legal facts
    └── Existing evidence inventory

Step 2: Legal risk assessment
    ├── Win rate assessment (based on facts + law + comparable cases)
    ├── Cost-benefit analysis (court fees + attorney fees + time cost)
    ├── Enforcement risk assessment (counterparty's solvency)
    └── Procedural risk assessment (statute of limitations / jurisdiction / evidence capacity)

Step 3: Strategic recommendations
    ├── Optimal plan (litigation / mediation / arbitration / negotiation)
    ├── Alternative plan
    └── Risk warnings and mitigation
```

---

## III. Integration with Existing Legal Skills

This skill complements existing installed legal skills:

| Scenario | Primary Skill | Supplementary Skill |
|----------|--------------|-------------------|
| Contract dispute litigation | This skill (strategy + documents) | contract-risk-reviewer (contract review) |
| Criminal defense | defense-lawyer (defense strategy) | This skill (trial + documents) |
| Labor dispute arbitration | labor-law-advisor (labor law) | This skill (arbitration procedure + application) |
| Legal text analysis | legal-seven-step-workflow (7-step method) | This skill (document drafting) |
| Rights protection letter | legal-rights-drafter-claw (letters) | This skill (subsequent litigation) |
| Legal concept interpretation | legal-concept-deep-dive (concept deep dive) | This skill (trial application strategy) |
| M&A due diligence | lawyer-due-diligence (DD report) | This skill (litigation risk for contract terms) |

---

## IV. Reference Resources

| File | Content | When to Load |
|------|---------|-------------|
| references/civil-procedure.md | Civil litigation full workflow guide | When handling civil disputes |
| references/criminal-procedure.md | Criminal case stages and key points | When handling criminal cases |
| references/admin-procedure.md | Administrative litigation guide | When handling administrative cases |
| references/legal-document-templates.md | 12 core legal document templates | When drafting legal documents |
| references/trial-practice.md | Court preparation, defense, cross-examination strategies | When preparing for trial |
| references/evidence-rules.md | Burden of proof, evidence three-dimension test, evidence chain | When dealing with evidence issues |
| references/arbitration.md | Commercial arbitration, labor arbitration, international arbitration full workflow | When handling arbitration/labor arbitration cases |

---

## V. Important Notes

1. All legal documents and strategic recommendations output by this skill are **for reference only**. Review by a licensed attorney is required before formal use.
2. Verify all cited laws and regulations for the latest version — AI may not cover recent amendments.
3. Litigation strategy is highly dependent on individual case details; tailor output to actual case circumstances.
4. For substantive legal analysis of specific cases, consider coordinating with the `legal-seven-step-workflow-mctmilk` skill.
5. Critical deadlines (appeal period, statute of limitations, evidence submission period) must be manually verified.
6. This skill does not substitute for formal legal advice. For significant cases, retain a qualified attorney.
