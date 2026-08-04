# Compliance Checklist Templates

## Template 1: New AI Tool Onboarding Checklist

### Section 1 — Tool Classification
- [ ] Intended purpose documented
- [ ] EU AI Act risk tier determined (Prohibited / High / Limited / Minimal)
- [ ] NIST AI RMF risk category assigned
- [ ] ISO 42001 scope inclusion confirmed
- [ ] Personal data processed? (Yes/No → triggers GDPR obligations)
- [ ] Used in EU context or affecting EU residents? (Yes/No → triggers EU AI Act)

### Section 2 — Risk Assessment
- [ ] AI impact assessment completed
- [ ] Bias and fairness evaluation conducted
- [ ] Privacy impact assessment (DPIA) completed if required
- [ ] Security and adversarial robustness evaluated
- [ ] Third-party vendor risk assessed
- [ ] Residual risks documented and accepted by risk owner

### Section 3 — Governance
- [ ] AI system owner assigned
- [ ] Use policy documented and communicated to users
- [ ] Responsible AI training completed by all users
- [ ] Human oversight mechanism defined
- [ ] Escalation path for AI errors/incidents defined

### Section 4 — Technical Controls
- [ ] Logging and audit trail enabled
- [ ] Data minimization controls in place
- [ ] Access controls configured (least privilege)
- [ ] Model versioning and change management in place
- [ ] Incident response plan updated to include AI failures

### Section 5 — Transparency
- [ ] Users informed they are interacting with AI
- [ ] Explainability documented for consequential decisions
- [ ] User documentation available

### Section 6 — Ongoing Compliance
- [ ] Monitoring plan defined (performance, drift, incidents)
- [ ] Review cadence established (quarterly recommended)
- [ ] Registered in internal AI system inventory

---

## Template 2: Risk Assessment Determination

**Tool/Use Case:** _______________
**Date:** _______________
**Assessor:** _______________

### Step 1 — EU AI Act Tier
| Question | Yes | No |
|---|---|---|
| Is this a prohibited use (social scoring, biometric surveillance, subliminal manipulation)? | → STOP, cannot deploy | Continue |
| Does it fall under Annex III high-risk categories? | High Risk obligations apply | Continue |
| Does it involve user-facing AI interaction? | Limited Risk (disclosure required) | Minimal Risk |

**Determined Tier:** _______________

### Step 2 — High Risk Obligations (if applicable)
- [ ] Risk management system in place (Art. 9)
- [ ] Data governance controls (Art. 10)
- [ ] Technical documentation (Art. 11)
- [ ] Logging enabled (Art. 12)
- [ ] User transparency (Art. 13)
- [ ] Human oversight (Art. 14)
- [ ] Accuracy/robustness/security (Art. 15)
- [ ] Conformity assessment completed
- [ ] Registered in EU AI database

### Step 3 — ISO 42001 Controls
- [ ] A.5.1 Risk classification documented
- [ ] A.6.1 Impact assessment conducted
- [ ] A.7.1 Intended purpose documented
- [ ] A.8 Data governance controls in place
- [ ] A.9.1 Transparency to users
- [ ] A.10.2 Operational monitoring in place

### Step 4 — NIST AI RMF Alignment
- [ ] GOVERN: Policy coverage confirmed
- [ ] MAP: Use case categorized and context documented
- [ ] MEASURE: Bias, fairness, accuracy evaluated
- [ ] MANAGE: Risk treatment plan in place

---

## Template 3: Gap Analysis Output Format

**System/Tool:** _______________
**Frameworks Assessed:** EU AI Act | ISO 42001 | NIST AI RMF | GDPR

| Gap | Framework | Severity | Recommendation | Owner | Due Date |
|---|---|---|---|---|---|
| No human oversight mechanism | EU AI Act Art.14, ISO A.2.2, NIST GOVERN 1.2 | HIGH | Define and document human review process for AI outputs | ISAI | — |
| No AI impact assessment | ISO A.6.1, NIST MAP 3.1 | HIGH | Conduct and document impact assessment | Risk Team | — |
| Users not informed of AI interaction | EU AI Act Art.13, NIST GOVERN 1.4 | MEDIUM | Add disclosure to user interface | Product | — |
| No monitoring plan | ISO A.10.2, NIST MANAGE 3.1 | MEDIUM | Define KPIs and monitoring cadence | ISAI | — |
| Training not completed | ISO A.2.4, NIST GOVERN 2 | MEDIUM | Enforce training before access | HR/ISAI | — |
| No documented data provenance | ISO A.8.4, NIST MAP 3.2 | LOW | Document training and operational data sources | Data Team | — |
