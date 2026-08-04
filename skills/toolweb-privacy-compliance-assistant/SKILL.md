# Privacy Compliance Assistant

Generate a Privacy Impact Assessment (PIA) and Data Protection Officer (DPO) advisory report for your organization. Describe your company type, the personal data you process, your processing purpose, systems in use, and data sharing relationships — get back a comprehensive privacy compliance report aligned to GDPR, CCPA, and global privacy regulations.

---

## Usage

```json
{
  "tool": "privacy_compliance_assistant",
  "input": {
    "company_type": "SaaS Platform",
    "data_types": ["Name", "Email Address", "IP Address", "Payment Information", "Usage Analytics"],
    "processing_purpose": "Providing subscription-based project management software to business customers and processing payments",
    "systems_used": ["AWS RDS", "Stripe", "HubSpot CRM", "Google Analytics", "Intercom"],
    "data_shared_with": ["Stripe (payment processing)", "HubSpot (CRM/marketing)", "AWS (infrastructure)", "Intercom (customer support)"]
  }
}
```

---

## Parameters

All fields are **required**.

| Field | Type | Description |
|-------|------|-------------|
| `company_type` | string | Type of organization. Examples: `SaaS Platform`, `E-commerce`, `Healthcare Provider`, `Financial Services`, `HR Tech`, `EdTech`, `Marketplace`, `Enterprise Software` |
| `data_types` | array | Types of personal data collected/processed. Examples: `Name`, `Email Address`, `Phone Number`, `IP Address`, `Payment Information`, `Health Records`, `Biometric Data`, `Location Data`, `Cookies`, `Usage Analytics`, `Government ID` |
| `processing_purpose` | string | Clear description of why personal data is collected and how it is used |
| `systems_used` | array | Technology systems, platforms, and tools used to store or process personal data. Examples: `AWS RDS`, `Salesforce`, `Stripe`, `Google Analytics`, `Okta`, `Snowflake`, `Mailchimp` |
| `data_shared_with` | array | Third parties with whom personal data is shared, including purpose. Examples: `Stripe (payment processing)`, `Google Analytics (web analytics)`, `AWS (infrastructure hosting)` |

---

## What You Get

- **Privacy Impact Assessment (PIA)** — structured assessment of privacy risks across the data lifecycle
- **Data Processing Register entry** — Article 30 GDPR-compliant record of processing activities (ROPA)
- **Legal basis analysis** — recommended lawful basis for each processing activity (consent, legitimate interest, contract, legal obligation)
- **Data subject rights checklist** — how to fulfill access, erasure, portability, and objection requests
- **Third-party risk summary** — privacy risk assessment for each data sharing relationship
- **Retention and deletion guidance** — recommended data retention periods per data type
- **Cross-border transfer analysis** — flags if data transfers outside EEA/adequate countries require SCCs or BCRs
- **Remediation recommendations** — prioritized actions to close privacy compliance gaps

---

## Example Output

```json
{
  "company_type": "SaaS Platform",
  "pia_risk_rating": "Medium",
  "gdpr_applicable": true,
  "ccpa_applicable": true,
  "processing_activities": [
    {
      "purpose": "Payment processing",
      "data_types": ["Name", "Payment Information"],
      "legal_basis": "Contract (Article 6(1)(b))",
      "retention_period": "7 years (financial regulation)",
      "cross_border_transfer": false
    },
    {
      "purpose": "Usage analytics",
      "data_types": ["IP Address", "Usage Analytics"],
      "legal_basis": "Legitimate Interest (Article 6(1)(f))",
      "retention_period": "26 months",
      "cross_border_transfer": true,
      "transfer_mechanism": "Standard Contractual Clauses (SCCs)"
    }
  ],
  "third_party_risks": [
    {
      "vendor": "Google Analytics",
      "risk": "High — US-based transfer, requires SCCs and consent banner",
      "action": "Implement cookie consent and execute DPA with Google"
    }
  ],
  "data_subject_rights": {
    "access": "Implement self-service data export in account settings",
    "erasure": "Build account deletion workflow with cascade delete",
    "portability": "Provide JSON/CSV export of user data",
    "objection": "Allow opt-out of analytics tracking"
  },
  "top_gaps": [
    "No Data Processing Agreement (DPA) executed with Google Analytics",
    "No cookie consent mechanism for analytics tracking",
    "Privacy policy does not document all third-party data sharing",
    "No formal data retention and deletion schedule"
  ],
  "immediate_actions": [
    "Execute DPAs with all data processors (Stripe, HubSpot, Intercom, AWS)",
    "Deploy cookie consent banner covering analytics and marketing cookies",
    "Update privacy policy to include complete ROPA disclosures"
  ]
}
```

---

## API Reference

**Base URL:** `https://portal.toolweb.in/apis/compliance/privacy-assistant`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate-dpo` | POST | Generate Privacy Impact Assessment and DPO advisory report |

**Authentication:** Pass your API key as `X-API-Key` header or `mcp_api_key` argument via MCP.

---

## Pricing

| Plan | Daily Limit | Monthly Limit | Price |
|------|-------------|---------------|-------|
| Free | 5 / day | 50 / month | $0 |
| Developer | 20 / day | 500 / month | $39 |
| Professional | 200 / day | 5,000 / month | $99 |
| Enterprise | 100,000 / day | 1,000,000 / month | $299 |

---

## About

**ToolWeb.in** — 200+ security APIs, CISSP & CISM certified, built for enterprise compliance practitioners.

Platforms: Pay-per-run · API Gateway · MCP Server · OpenClaw · RapidAPI · YouTube

- 🌐 [toolweb.in](https://toolweb.in)
- 🔌 [portal.toolweb.in](https://portal.toolweb.in)
- 🤖 [hub.toolweb.in](https://hub.toolweb.in) (MCP Server)
- 🦞 [toolweb.in/openclaw/](https://toolweb.in/openclaw/)
- ⚡ [rapidapi.com/user/mkrishna477](https://rapidapi.com/user/mkrishna477)
- 📺 [youtube.com/@toolweb-009](https://youtube.com/@toolweb-009)
