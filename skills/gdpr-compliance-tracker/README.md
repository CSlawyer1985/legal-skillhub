# GDPR Compliance Tracker — OpenClaw Skill 🔐🇪🇺

Assess GDPR compliance with a single message to your OpenClaw agent.

## Quick Install

```bash
clawhub install gdpr-compliance-tracker
```

## Configuration

```json
{
  "skills": {
    "entries": {
      "gdpr-compliance-tracker": {
        "enabled": true,
        "env": {
          "TOOLWEB_API_KEY": "your-api-key-here"
        }
      }
    }
  }
}
```

## Get Your API Key

Visit [portal.toolweb.in](https://portal.toolweb.in) — free trial includes 10 API calls.

## What It Assesses

- Data processing activities and lawful basis
- Consent management and data subject rights (DSAR)
- Privacy policies and data retention
- International data transfers and transfer mechanisms
- DPO appointment and DPIA processes
- Breach notification procedures
- Staff training and vendor agreements

## Example

```
You: Check if our SaaS company is GDPR compliant. We're medium-sized,
     process EU customer data, have a privacy policy but no DPO.

Agent: 🔐 GDPR Compliance Assessment
       Score: 55/100
       🚨 Critical: No DPO appointed despite EU data processing
       🚨 Critical: No breach notification procedures
       📋 Action 1: Appoint DPO within 30 days
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
