# AI System Inventory Template

## Purpose
Maintain a register of all AI systems in use at the firm. Required by ISO 42001 (A.5.1), NIST AI RMF (MAP 1.6), and EU AI Act (Article 11/49).

## Inventory Fields

| Field | Description |
|---|---|
| **System ID** | Unique identifier (e.g., AI-001) |
| **System Name** | Tool or system name |
| **Version** | Version or tier in use |
| **Vendor** | Vendor name and HQ country |
| **System Owner** | Named individual accountable for the system |
| **Business Owner** | Department/team using the system |
| **Intended Purpose** | What the system is used for |
| **User Base** | Number and type of users |
| **Data Processed** | Classification of data entered/processed |
| **EU AI Act Tier** | Prohibited / High / Limited / Minimal |
| **NIST Risk Level** | High / Medium / Low |
| **ISO 42001 In Scope** | Yes / No |
| **GDPR Applies** | Yes / No |
| **DPA in Place** | Yes / No / N/A |
| **Enterprise Tier** | Yes / No / N/A (on-prem) |
| **Training Required** | Yes / No |
| **Approved Date** | Date ISAI approved use |
| **Last Review Date** | Date of last compliance review |
| **Next Review Date** | Scheduled next review |
| **Status** | Active / Under Review / Suspended / Decommissioned |
| **Notes** | Any additional compliance notes |

---

## fi.com AI Inventory (Current State)

| ID | System | Vendor | Owner | EU AI Tier | Risk | DPA | Enterprise | Status |
|---|---|---|---|---|---|---|---|---|
| AI-001 | Perplexity | Perplexity AI (US) | TBD | Limited | HIGH | ❌ | ❌ | ⚠️ Under Review |
| AI-002 | ChatGPT | OpenAI (US) | TBD | Limited | HIGH | ❌ | ❌ | ⚠️ Under Review |
| AI-003 | Microsoft 365 Copilot | Microsoft (US) | TBD | Limited | Medium | ✅ | ✅ | ✅ Active |
| AI-004 | Google AI Mode / Gemini | Google (US) | TBD | Limited | Medium | TBD | TBD | ⚠️ Under Review |
| AI-005 | Jasper.ai | Jasper (US) | TBD | Limited | Medium | TBD | TBD | ⚠️ Under Review |
| AI-006 | Microsoft Copilot | Microsoft (US) | TBD | Limited | Medium | ✅ | ✅ | ✅ Active |
| AI-007 | Grammarly | Grammarly (US) | TBD | Limited | Medium | TBD | TBD | ⚠️ Under Review |
| AI-008 | OpenClaw | openclaw.ai | B. Caddy | Limited | Medium | N/A | N/A (on-prem) | ✅ Active |

---

## Review Cadence
- **Quarterly:** Review active inventory for changes in usage, new tools, risk changes
- **Annually:** Full re-assessment of all tools including vendor questionnaire refresh
- **On-change:** Any new AI tool must be added before use begins
- **On-incident:** Re-assess affected tool immediately following any incident

## Adding New Tools
All new AI tools must be submitted to ISAI for review before use. Submit via [LINK/PROCESS].
ISAI target SLA for review: 5 business days for standard tools, 10 days for high-risk.
