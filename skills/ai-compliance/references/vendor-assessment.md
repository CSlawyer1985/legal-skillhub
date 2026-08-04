# Vendor AI Risk Assessment Questionnaire

Use this questionnaire when evaluating any third-party AI tool before procurement or continued use.

## Section 1 — Company & Product Overview
- [ ] Company name, HQ jurisdiction, parent company
- [ ] Product name and version assessed
- [ ] Is this a consumer or enterprise product?
- [ ] Enterprise tier available? (consumer use must be prohibited for business data)
- [ ] SOC 2 Type II report available? (request copy)
- [ ] ISO 27001 certified?
- [ ] ISO 42001 certified or in progress?
- [ ] Regulatory compliance claims (GDPR, CCPA, HIPAA, FedRAMP, etc.)

## Section 2 — Data Handling & Retention
- [ ] Are user prompts/queries stored? For how long?
- [ ] Is query data used to train models? (opt-out available?)
- [ ] Is query data shared with third parties or subprocessors?
- [ ] List of subprocessors available and reviewed?
- [ ] Data residency options available (EU, US, etc.)?
- [ ] Can data retention be disabled at enterprise tier?
- [ ] Data deletion process and SLA documented?
- [ ] Data portability/export available?

## Section 3 — Data Protection & Legal
- [ ] Data Processing Agreement (DPA) available?
- [ ] Standard Contractual Clauses (SCCs) available for EU data transfers?
- [ ] Privacy policy reviewed and acceptable?
- [ ] Does the vendor claim ownership of inputs or outputs?
- [ ] Intellectual property protections for firm content in outputs?
- [ ] Breach notification SLA (how quickly will they notify)? — 72 hours required for GDPR
- [ ] Right to audit contractually available?

## Section 4 — Security Controls
- [ ] Encryption in transit (TLS 1.2+)?
- [ ] Encryption at rest?
- [ ] Access controls and authentication options (SSO/SAML, MFA)?
- [ ] Role-based access control available?
- [ ] Vulnerability disclosure / bug bounty program in place?
- [ ] Penetration testing conducted? Frequency?
- [ ] Incident response plan documented?

## Section 5 — AI-Specific Risk
- [ ] Model training data sources documented?
- [ ] Model bias evaluation conducted and published?
- [ ] Hallucination/accuracy limitations documented?
- [ ] Content filtering / safety controls in place?
- [ ] Prompt injection mitigations in place?
- [ ] AI-generated output labeling available?
- [ ] Human oversight mechanisms supported?
- [ ] Explainability/interpretability features available?

## Section 6 — Operational Risk
- [ ] SLA and uptime guarantees acceptable?
- [ ] Vendor financial stability assessed (funding, public company)?
- [ ] Dependency risk — what happens if vendor shuts down?
- [ ] API stability and versioning policy?
- [ ] Geographic availability (outage risk for EU/US split ops)?

## Scoring Guide
Rate each section 1–5. Total score determines procurement path:
- **41–50**: Low risk — standard procurement
- **31–40**: Medium risk — require DPA + security review before approval
- **21–30**: High risk — require CISO approval + additional controls
- **<21**: Very high risk — block or require executive exception

## Common Findings by Tool
| Tool | Key Risks | Enterprise Tier |
|---|---|---|
| Perplexity | Query retention by default, US-based, consumer tier lacks DPA | Perplexity Enterprise Pro |
| ChatGPT | OpenAI trains on data unless opted out, SOC 2 available | ChatGPT Enterprise |
| Microsoft Copilot | M365 data residency, EU Data Boundary available | M365 Copilot (existing licensing) |
| Gemini | Google data policies, EU residency options | Google Workspace |
| Jasper.ai | Content stored, US-based | Jasper Business |
| Grammarly | Reads all text typed, wide data access | Grammarly Business |
