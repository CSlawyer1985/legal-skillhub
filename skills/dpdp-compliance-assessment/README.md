# DPDP Compliance Assessment — OpenClaw Skill 🇮🇳🔏

India's Digital Personal Data Protection Act 2023 compliance assessment via your OpenClaw agent.

## Quick Install

```bash
clawhub install dpdp-compliance-assessment
```

## Configuration

```json
{
  "skills": {
    "entries": {
      "dpdp-compliance-assessment": {
        "enabled": true,
        "env": {
          "TOOLWEB_API_KEY": "your-api-key-here"
        }
      }
    }
  }
}
```

## 7 Domains, 41 Controls

Data Governance (6), Consent Management (7), Data Principal Rights (6), Vendor Management (5), Data Security (6), Breach Management (5), Privacy Governance (6)

## 5 Maturity Levels

Initial (0-25%) → Developing (26-50%) → Defined (51-75%) → Managed (76-90%) → Optimized (91-100%)

## Example

```
You: Check our fintech company's DPDP compliance. We have basic
     consent collection but no formal data inventory or DPO.

Agent: 🇮🇳 DPDP Compliance Assessment
       Overall: 32% — DEVELOPING
       ✋ Consent: 45%
       📁 Data Governance: 15%
       📜 Privacy Governance: 20%
       📋 Action 1: Appoint DPO and establish data inventory
```

## Pricing

| Plan | Price/month | API Calls |
|------|------------|-----------|
| Free Trial | $0 | 10 calls |
| Starter | ₹2,999 (~$36) | 500 |
| Professional | ₹9,999 (~$120) | 5,000 |
| Enterprise | ₹49,999 (~$600) | Unlimited |

International: Select PayPal at checkout for USD/EUR/GBP.

## License

MIT-0

---

*Built by a CISSP & CISM certified professional at [ToolWeb.in](https://toolweb.in)*
