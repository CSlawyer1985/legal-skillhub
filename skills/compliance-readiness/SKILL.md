---
name: compliance-readiness
description: AI Compliance Readiness Assessment — evaluate how prepared an organization is for AI governance regulations (EU AI Act, NIST AI RMF, HHS mandates, state bar AI rules). Scores readiness across 8 dimensions and generates an action plan. Use when assessing AI compliance gaps, preparing for audits, or building a governance roadmap.
---

# AI Compliance Readiness Assessment

Evaluate organizational readiness for AI governance regulations and generate an actionable compliance roadmap.

## When to Use
- Assessing AI compliance posture before an audit
- Preparing for EU AI Act (Aug 2026), HHS AI mandates, NIST AI RMF
- Building a governance roadmap for AI deployments
- Evaluating risk exposure from current AI usage

## How to Use

When asked to assess AI compliance readiness, gather these inputs:

### Required Inputs
1. **Industry** (legal, healthcare, financial-services, insurance, construction, manufacturing, government, other)
2. **Company size** (employees or revenue range)
3. **AI systems in use** (list: chatbots, document review, fraud detection, hiring tools, customer service, analytics, other)
4. **Jurisdictions** (US-only, EU-exposed, both, global)

### Optional Inputs
- Current governance framework (if any)
- Upcoming audit dates
- Existing compliance certifications (SOC2, ISO 27001, HIPAA, etc.)
- Number of AI vendors/tools in use

## Assessment Framework

Score each dimension 1-5 (1=no controls, 5=mature):

### 8 Dimensions
1. **Risk Classification** — Have you categorized AI systems by risk level per EU AI Act / NIST?
2. **Documentation** — Technical docs, model cards, data lineage for each AI system?
3. **Human Oversight** — Defined human-in-the-loop processes for high-risk decisions?
4. **Bias & Fairness** — Regular bias audits, fairness metrics, disparate impact testing?
5. **Data Governance** — Training data provenance, consent, retention, and deletion policies?
6. **Incident Response** — AI-specific incident playbook, reporting procedures, rollback plans?
7. **Vendor Management** — AI vendor risk assessments, contractual AI governance requirements?
8. **Audit Trail** — Logging, explainability, decision traceability for AI-assisted outputs?

### Scoring
- **35-40**: Compliance-ready — minor gaps to address
- **25-34**: Partially prepared — significant work needed in specific areas
- **15-24**: High risk — major gaps across multiple dimensions
- **8-14**: Critical — immediate action required before any regulatory review

## Output Format

Generate a report with:

1. **Executive Summary** — Overall score, risk level, top 3 gaps
2. **Dimension Scores** — Table with score, evidence, and gap description per dimension
3. **Regulatory Exposure** — Which regulations apply and key deadlines:
   - EU AI Act: Aug 2, 2026 (high-risk system requirements)
   - HHS AI Transparency: April 3, 2026 (healthcare)
   - NIST AI RMF: Ongoing (federal contractors + best practice)
   - State bar AI rules: Varies (legal industry)
