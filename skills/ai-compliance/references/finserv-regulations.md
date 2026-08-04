# Financial Services AI Regulatory Overlay

## Overview
Financial services firms face AI compliance obligations beyond general AI frameworks. This overlay covers key regulations relevant to firms operating in the US, UK, and EU financial services sector.

---

## US Regulations

### SEC (Securities and Exchange Commission)
- **AI in Investment Advice (2023 proposed rule):** Investment advisers using AI/predictive analytics must disclose use to clients; conflicts of interest in AI recommendations must be eliminated or neutralized
- **MNPI / Insider Trading:** Entering non-public financial information into third-party AI tools may constitute unauthorized disclosure of MNPI; potential SEC enforcement exposure
- **Regulation Best Interest (Reg BI):** AI-generated investment recommendations must still meet best interest standard
- **Cybersecurity Rule (2023):** Material AI-related cybersecurity incidents must be reported on Form 8-K within 4 business days

### FINRA
- **Regulatory Notice 21-15:** AI/ML models used in trading or customer-facing recommendations require supervisory controls
- **Books and Records:** AI-generated communications with clients must be retained per applicable books and records rules
- **Supervision:** Firms must supervise AI tools as they would human representatives

### CFTC
- **AI in Trading:** Algorithmic/AI trading systems require pre-deployment testing, risk controls, and monitoring
- **Data Privacy:** Customer data used in AI models subject to CFTC privacy regulations

---

## UK Regulations

### FCA (Financial Conduct Authority)
- **Consumer Duty (2023):** AI tools used in customer journeys must deliver good outcomes; AI cannot be used to exploit behavioral biases
- **PS23/3 (Operational Resilience):** AI systems critical to business continuity must be within operational resilience frameworks
- **AI Principles:** FCA expects firms to be able to explain AI decisions affecting consumers
- **Senior Managers Regime (SMR):** Senior managers remain personally accountable for AI-driven decisions in their area; accountability cannot be delegated to AI

### Bank of England / PRA
- **SS1/23:** Model risk management applies to AI/ML models — governance, validation, ongoing monitoring required
- **Systemic Risk:** AI used in systemic or critical functions requires enhanced governance

---

## EU Regulations

### MiFID II / MiFIR
- **Algorithmic Trading:** AI used in trading requires pre-approval, testing, and circuit breakers
- **Record-keeping:** AI-generated communications and recommendations must be logged
- **Suitability:** AI cannot be used to generate unsuitable investment recommendations

### DORA (Digital Operational Resilience Act — effective Jan 2025)
- AI systems classified as critical or important ICT systems fall under DORA
- Requires ICT risk management framework covering AI
- Third-party AI providers may be classified as critical ICT third-party providers — subject to direct EU oversight
- Incident reporting for AI-related outages affecting financial services

### EU AI Act + Financial Services
- AI used in credit scoring → **High Risk** (Annex III)
- AI used in insurance underwriting → **High Risk**
- AI used in employment decisions → **High Risk**
- AI used for customer advice/recommendations → **Limited Risk minimum**

---

## Key MNPI / Insider Trading Risk (All Jurisdictions)

**The core risk:** Employees entering non-public financial information into cloud AI tools may constitute:
1. Unauthorized disclosure of insider information
2. Potential tipping violation
3. Regulatory violation if AI provider uses data to train models

**What counts as MNPI:**
- Unreleased earnings, guidance, or financial results
- Pending M&A, mergers, acquisitions, divestitures
- Unannounced restructurings, layoffs
- Regulatory investigations not yet public
- Major contract wins/losses not yet disclosed
- Investment strategies under active consideration

**Current exposure at fi.com:**
Based on webhook_events data, 3,365 financial data events and 1,384 investment strategy events have been detected entering third-party AI tools. Legal and Compliance must be briefed immediately.

---

## Compliance Requirements Matrix for finserv AI

| Requirement | US (SEC/FINRA) | UK (FCA/PRA) | EU (MiFID/DORA/AI Act) |
|---|---|---|---|
| AI model governance | ✅ Required | ✅ Required | ✅ Required |
| Explainability for customer decisions | ✅ Reg BI | ✅ Consumer Duty | ✅ EU AI Act |
| MNPI controls on AI inputs | ✅ Critical | ✅ Critical | ✅ Critical |
| Senior accountability for AI | ✅ Implied | ✅ SMR | ✅ EU AI Act |
| AI incident reporting | ✅ Cyber Rule | ✅ DORA | ✅ DORA + AI Act |
| Third-party AI vendor oversight | ✅ FINRA | ✅ PRA SS1/23 | ✅ DORA |
| AI in trading controls | ✅ CFTC | ✅ FCA | ✅ MiFID II |
