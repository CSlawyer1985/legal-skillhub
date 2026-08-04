# AI Risk Scoring Model

## Purpose
Generate a numeric risk score (0–100) for any AI tool or use case to enable consistent prioritization and triage.

## Scoring Dimensions

### 1. Data Sensitivity (0–25 points)
Score based on the most sensitive data type processed by the tool:

| Data Type | Score |
|---|---|
| Public data only | 0 |
| Internal / non-sensitive | 5 |
| Confidential business data | 10 |
| Personal data (PII) | 15 |
| Regulated data (GDPR, HIPAA, FINRA) | 20 |
| MNPI / financial secrets / credentials | 25 |

### 2. Data Destination (0–20 points)
Where does the data go?

| Destination | Score |
|---|---|
| On-premises / fully air-gapped | 0 |
| On-premises with external API calls (known, audited) | 5 |
| Enterprise SaaS (DPA in place, data residency confirmed) | 8 |
| Enterprise SaaS (no DPA confirmed) | 14 |
| Consumer cloud (no enterprise controls) | 18 |
| Unknown / unassessed destination | 20 |

### 3. User Base & Training (0–15 points)

| Situation | Score |
|---|---|
| All users trained, access gated | 0 |
| Most users trained (>80%) | 3 |
| Partially trained (50–80%) | 7 |
| Mostly untrained (<50% trained) | 11 |
| No training program, all users untrained | 15 |

### 4. Human Oversight (0–15 points)

| Situation | Score |
|---|---|
| Mandatory human review for all outputs | 0 |
| Human review for consequential outputs | 4 |
| Recommended but not enforced | 8 |
| No oversight — AI outputs acted on directly | 15 |

### 5. Governance & Legal (0–15 points)

| Situation | Score |
|---|---|
| DPA in place, AUP published, owner assigned, in inventory | 0 |
| Most governance in place (minor gaps) | 4 |
| Partial governance (DPA missing or AUP missing) | 8 |
| Minimal governance (no DPA, no AUP, no owner) | 12 |
| No governance whatsoever | 15 |

### 6. Regulatory Exposure (0–10 points)

| Situation | Score |
|---|---|
| No regulatory exposure (minimal/no risk tier, no sector rules) | 0 |
| Limited regulatory exposure | 3 |
| Moderate (GDPR, Limited Risk EU AI Act) | 5 |
| High (financial services sector rules, High Risk EU AI Act) | 8 |
| Critical (MNPI exposure, prohibited AI use risk) | 10 |

---

## Total Score Interpretation

| Score | Risk Level | Action |
|---|---|---|
| 0–20 | 🟢 Low | Standard monitoring, annual review |
| 21–40 | 🟡 Medium | Quarterly review, close governance gaps |
| 41–60 | 🟠 High | ISAI review required, remediation plan needed |
| 61–80 | 🔴 Very High | CISO approval required, immediate remediation |
| 81–100 | 🚨 Critical | Consider suspension pending remediation |

---

## Scored Examples (fi.com Tools)

### Perplexity (Consumer Tier — Current State)
| Dimension | Score | Rationale |
|---|---|---|
| Data Sensitivity | 25 | MNPI and financial data detected in prompts |
| Data Destination | 18 | Consumer cloud, no DPA |
| User Training | 15 | 89% untrained |
| Human Oversight | 8 | Not enforced |
| Governance | 12 | No DPA, no AUP, no formal owner |
| Regulatory Exposure | 10 | Financial services MNPI exposure |
| **TOTAL** | **88** | 🚨 **CRITICAL** |

### Microsoft 365 Copilot (Enterprise)
| Dimension | Score | Rationale |
|---|---|---|
| Data Sensitivity | 10 | M365 data, some confidential |
| Data Destination | 8 | Enterprise SaaS, DPA in place |
| User Training | 11 | Mostly untrained still |
| Human Oversight | 8 | Recommended, not enforced |
| Governance | 4 | DPA yes, AUP partially in place |
| Regulatory Exposure | 5 | GDPR applies |
| **TOTAL** | **46** | 🟠 **High** |

### OpenClaw (On-Premises)
| Dimension | Score | Rationale |
|---|---|---|
| Data Sensitivity | 20 | Processes security telemetry, some PII |
| Data Destination | 5 | Mostly on-prem; Anthropic API calls |
| User Training | 0 | Single user (Bryan), trained |
| Human Oversight | 4 | Bryan reviews outputs |
| Governance | 8 | No formal AUP, not in inventory yet |
| Regulatory Exposure | 5 | GDPR (PII), some finserv data |
| **TOTAL** | **42** | 🟠 **High** — Anthropic API + secrets mgmt gaps |

---

## Scoring Worksheet

**Tool/Use Case:** _______________
**Date:** _______________
**Assessed by:** _______________

| Dimension | Score (0–max) | Notes |
|---|---|---|
| Data Sensitivity | /25 | |
| Data Destination | /20 | |
| User Training | /15 | |
| Human Oversight | /15 | |
| Governance & Legal | /15 | |
| Regulatory Exposure | /10 | |
| **TOTAL** | **/100** | |

**Risk Level:** _______________
**Recommended Action:** _______________
