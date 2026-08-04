---
name: ai-compliance
description: >
  AI compliance analysis for EU AI Act, ISO 42001, NIST AI RMF, GDPR, OECD, financial services
  regulations (SEC, FCA, FINRA, DORA, MiFID II), and other frameworks. Use when asked to generate
  a compliance checklist for an AI tool or use case, determine if a risk assessment is required,
  score an AI tool's risk level, identify where an AI tool or use case could run afoul of regulatory
  requirements, perform a gap analysis, recommend remediation steps, assess a vendor, draft an
  acceptable use policy, map training requirements, or review jurisdiction-specific AI rules.
  Triggers on phrases like "compliance checklist", "risk assessment", "risk score", "does this
  comply", "EU AI Act", "ISO 42001", "NIST AI RMF", "AI governance", "gap analysis", "vendor
  assessment", "acceptable use policy", "MNPI", "AI training requirements", or any request to
  evaluate an AI tool or use case for regulatory compliance or risk.
---

# AI Compliance Skill

## Reference Files
Load only what's needed based on the request type:

### Frameworks
- **EU AI Act** → `references/eu-ai-act.md` — risk tiers, prohibited uses, obligations
- **ISO 42001** → `references/iso-42001.md` — clauses, Annex A controls
- **NIST AI RMF** → `references/nist-ai-rmf.md` — GOVERN/MAP/MEASURE/MANAGE
- **GDPR, OECD, IEEE, UK, Singapore** → `references/other-frameworks.md`
- **Financial services (SEC, FCA, FINRA, DORA, MiFID II, MNPI)** → `references/finserv-regulations.md`
- **Jurisdiction map (global regulatory landscape)** → `references/jurisdiction-map.md`
- **ISO 27001 alignment** → `references/iso27001-alignment.md`

### Output Templates & Tools
- **Checklists, risk assessment, gap analysis templates** → `references/checklist-templates.md`
- **Vendor AI risk assessment questionnaire** → `references/vendor-assessment.md`
- **Acceptable use policy template** → `references/aup-template.md`
- **Data classification × AI tool matrix** → `references/data-classification.md`
- **AI system inventory template** → `references/ai-inventory.md`
- **AI risk scoring model (0–100)** → `references/risk-scoring.md`
- **Training requirements by role** → `references/training-requirements.md`

### Remediation
- **Incident response playbooks** → `references/incident-response.md`
- **Remediation playbooks (common gaps)** → `references/remediation-playbooks.md`

When in doubt about which files to load, load the framework files + the relevant output template.

## Workflow

### 1. Understand the AI Tool/Use Case
Gather (or ask for):
- What does the AI system do? (intended purpose)
- Who uses it and how? (internal staff, customers, automated pipeline)
- What data does it process? (personal, financial, confidential, public)
- Where is it deployed? (EU context? affecting EU residents?)
- Consumer or enterprise tier? Third-party or internal?

### 2. Select Output Type

| Request | Load | Output |
|---|---|---|
| Compliance checklist | Framework files + checklist-templates.md | Full checklist per Template 1 |
| Risk assessment needed? | eu-ai-act.md + checklist-templates.md | Risk tier determination per Template 2 |
| Gap analysis | All framework files + checklist-templates.md | Gap table per Template 3 |
| Risk score | risk-scoring.md | Scored worksheet + risk level |
| Vendor assessment | vendor-assessment.md | Questionnaire + scoring |
| AUP draft | aup-template.md | Customized policy draft |
| Data classification guidance | data-classification.md | Matrix + decision tree |
| Incident response | incident-response.md | Relevant playbook |
| Remediation steps | remediation-playbooks.md | Relevant playbook(s) |
| Financial services overlay | finserv-regulations.md | Regulatory requirements |
| Training requirements | training-requirements.md | Role-based matrix |
| Jurisdiction guidance | jurisdiction-map.md | Applicable rules by region |

### 3. Output Structure
Always structure output as:

```
## AI Compliance Assessment: [Tool/Use Case Name]
### Risk Classification
### Applicable Frameworks
### Compliance Checklist (or Gap Analysis or Risk Score)
### Issues Found
### Recommendations
### Priority Actions
```

## Key Principles
- Reference exact articles, clauses, controls (e.g., "EU AI Act Art.14", "ISO 42001 A.6.1", "NIST GOVERN 1.2")
- Flag HIGH/CRITICAL severity issues prominently — these are blockers
- Always include remediation steps, not just gaps — link to remediation-playbooks.md when relevant
- Cross-reference frameworks where they overlap
- For financial services firms: always check finserv-regulations.md for MNPI and sector-specific rules
- When uncertain about risk tier, err toward higher risk classification
