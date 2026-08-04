# AI Training Requirements Matrix

## By Role

| Role | Required Training | Frequency | Before AI Access? |
|---|---|---|---|
| All employees | Responsible AI Usage (general) | Annual | ✅ Yes |
| All employees | Data Classification + AI Inputs | Annual | ✅ Yes |
| Developers/Engineers | Secure AI Development | Annual | ✅ Yes (for dev tools) |
| Data Scientists / ML Engineers | AI Model Risk & Governance | Annual | ✅ Yes |
| Risk & Compliance | AI Regulatory Landscape | Annual | Recommended |
| Managers / Team Leads | AI Oversight & Accountability | Annual | Recommended |
| Executives / Senior Management | AI Strategy & Risk Governance | Annual | Recommended |
| Procurement / Vendor Management | AI Vendor Risk Assessment | Annual | Before any AI procurement |
| Legal / Compliance | AI Regulatory Deep Dive (EU AI Act, NIST, ISO) | Annual | Recommended |
| HR | AI in Employment (bias, discrimination risk) | Annual | Before using AI in HR |
| Finance / Investment | MNPI + AI Tools (regulatory risk) | Annual | ✅ Yes — HIGH PRIORITY |

---

## Framework Requirements

| Framework | Training Requirement | Details |
|---|---|---|
| ISO 42001 | A.2.4 Training and awareness | All users of AI systems must receive appropriate training |
| NIST AI RMF | GOVERN 2 | AI risk management workforce and culture cultivated |
| EU AI Act | Art.4 AI literacy | Providers/deployers must ensure AI literacy of staff working with AI systems |
| GDPR | Art.39 DPO duties / general accountability | Staff handling personal data (including via AI) must be trained |

---

## Core Training Modules (Minimum Viable Program)

### Module 1: Responsible AI Usage (All Staff) — 30 min
- What AI tools are approved and how to access them
- What data can and cannot be entered into AI tools
- How to verify AI outputs before acting on them
- How to report an AI-related incident
- Policy acknowledgment and sign-off

### Module 2: Data Classification + AI Inputs (All Staff) — 20 min
- Data classification tiers (Public → Restricted)
- What each tier means for AI tool usage
- Real examples: what's OK, what's prohibited
- MNPI awareness for investment/finance staff

### Module 3: Secure AI Development (Developers) — 60 min
- Prompt injection risks and mitigations
- Secrets management — never hardcode credentials
- AI API security (key rotation, rate limiting, input validation)
- Model risk: drift, poisoning, adversarial inputs
- Supply chain risk for AI dependencies

### Module 4: AI Vendor Risk (Procurement) — 45 min
- How to complete the vendor AI risk questionnaire
- What to look for in a DPA
- Red flags: no SOC 2, no data retention controls, no DPA
- Consumer vs. enterprise tier distinctions
- Escalation path for borderline vendors

### Module 5: MNPI + AI (Finance/Investment Staff) — 45 min
- What counts as MNPI
- Why entering MNPI into AI tools is a regulatory violation
- Real-world enforcement cases
- What to do if you accidentally entered MNPI into an AI tool
- Attestation required

---

## Training Tracking

Current fi.com status (from training_completions vs webhook_events):
- **Total users with AI access:** 289
- **Trained:** 31 (11%) ✅
- **Untrained:** 258 (89%) 🚨

**Priority groups for immediate training:**
1. Finance/Investment staff — MNPI risk
2. Top 20 users by event volume — highest exposure
3. Anyone with blocked events for financial data or investment strategies
