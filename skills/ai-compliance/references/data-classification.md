# Data Classification × AI Tool Matrix

## Data Classification Tiers

| Tier | Definition | Examples |
|---|---|---|
| **Public** | Approved for public release | Press releases, public filings, marketing materials |
| **Internal** | For internal use only, not sensitive | General business comms, internal FAQs, org charts |
| **Confidential** | Sensitive business information | Business strategies, vendor contracts, internal financials |
| **Restricted** | Highly sensitive, strictly controlled | MNPI, client PII, credentials, source code, legal privilege |
| **Regulated** | Subject to specific legal/regulatory controls | GDPR PII, HIPAA, FINRA, attorney-client privilege |

---

## AI Tool Usage Matrix

| Data Tier | Consumer AI (ChatGPT Free, Perplexity Free, etc.) | Approved Enterprise AI (M365 Copilot, ChatGPT Enterprise, etc.) | Internal/On-Prem AI (OpenClaw, self-hosted models) |
|---|---|---|---|
| **Public** | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| **Internal** | ❌ Prohibited | ✅ Permitted with care | ✅ Permitted |
| **Confidential** | ❌ Prohibited | ⚠️ Case-by-case, ISAI approval | ✅ Permitted |
| **Restricted** | ❌ Prohibited | ❌ Prohibited | ⚠️ ISAI approval required |
| **Regulated** | ❌ Prohibited | ❌ Prohibited | ⚠️ ISAI + Legal approval required |

---

## Prohibited Input Quick Reference

Always prohibited in **any** AI tool unless explicitly approved:

| Category | Examples | Why |
|---|---|---|
| MNPI | Unreleased earnings, M&A targets, trading strategies | Securities law (SEC, FCA, MAR) |
| Client PII | Names + account numbers, portfolio details | GDPR, CCPA, fiduciary duty |
| Credentials | Passwords, API keys, tokens, secrets | Credential theft, unauthorized access |
| Source code | Proprietary algorithms, trading systems | IP theft, competitive risk |
| Legal privilege | Legal advice, litigation strategy | Waives privilege |
| Audit findings | Control weaknesses, vulnerabilities | Security risk |
| Network details | IP ranges, firewall rules, architecture | Security risk |
| HR data | Salaries, performance reviews, health info | Privacy law, discrimination risk |

---

## fi.com Specific Guidance

Based on current webhook_events data, the following are **actively being entered** into Perplexity and ChatGPT and must be addressed immediately:

| Detected Input Type | Current Status | Required Action |
|---|---|---|
| Financial data / reports | 🔴 Being entered, 100% blocked | DLP working — enforce AUP, gate with training |
| Investment strategies | 🔴 Being entered, 100% blocked | Escalate to Legal/Compliance — potential MNPI |
| Investment decisions | 🔴 Being entered, 100% blocked | Escalate to Legal/Compliance — potential MNPI |
| Internal communications | 🟡 Being entered, partially blocked | Strengthen DLP rules |
| Network infrastructure | 🟡 Being entered, partially blocked | Security risk — tighten DLP |
| Source code | 🔴 New this week, not fully blocked | Update DLP rules immediately |
| Credentials/passwords | 🔴 Being entered, some blocked | Credential rotation + DLP tightening |
| GitHub tokens | 🔴 New this week | Immediate credential rotation required |

---

## Decision Tree: Can I use AI for this task?

```
Is the data Public?
  → YES: Any approved tool is fine
  → NO: Continue ↓

Is the data Internal only (no PII, no financial)?
  → YES: Use approved enterprise tools only. No consumer AI.
  → NO: Continue ↓

Is the data Confidential (strategies, contracts, internal financials)?
  → YES: Contact ISAI for approval. On-prem tools preferred.
  → NO: Continue ↓

Is it MNPI, client PII, credentials, source code, or regulated data?
  → YES: DO NOT enter into any AI tool. Contact ISAI.
```
