---
name: firm-legal-pack
version: 1.0.0
description: >
  Curated skill bundle for law firms, legal departments and compliance teams.
  Activates the firm pyramid with Legal, Compliance, Privacy and Contracting agents
  pre-configured for document review, regulatory tracking and risk analysis.
author: romainsantoli-web
license: MIT
metadata:
  openclaw:
    requires:
      env: []
      bins: []
    tools:
      - sessions_send
      - sessions_spawn
      - sessions_history
    primaryEnv: ""
tags:
  - legal
  - compliance
  - contracts
  - firm-pack
  - enterprise
  - sector
---

# firm-legal-pack

Sector bundle for **legal & compliance** environments.

## Activated departments

| Department | Services activated | Focus |
|---|---|---|
| Legal | Contracting · Privacy/Data · IP & Compliance | Contract review, GDPR, patent filings |
| Quality | Compliance auditing · Accessibility | Regulatory adherence |
| Finance | Unit economics · Billing & Collections | Cost analysis for legal ops |
| RA | Governance & Performance | Agent onboarding for legal roles |
| Operations | Documentation · Release | Knowledge base management |

## Recommended ClawHub skills to install alongside

```bash
npx clawhub@latest install academic-research        # Legal research via OpenAlex
npx clawhub@latest install pdf-documents            # Contract PDF parsing
npx clawhub@latest install arc-security-audit       # Compliance audit trail
npx clawhub@latest install agent-audit-trail        # Hash-chained audit logging
npx clawhub@latest install firm-orchestration       # This pack depends on it
```

## Firm configuration overlay

Add to `~/.openclaw/openclaw.json`:

```json
{
  "agent": {
    "model": "anthropic/claude-opus-4-6",
    "workspace": "~/.openclaw/workspace"
  },
  "agents": {
    "defaults": {
      "sandbox": { "mode": "non-main" },
      "workspace": "~/.openclaw/workspace/legal-firm"
    }
  }
}
```

## Prompt: standard legal delivery

```
Use firm-orchestration with:
  objective: "Review NDA agreement for data residency compliance with GDPR Art. 44-49"
  departments: ["legal", "quality"]
  constraints: ["read-only document access", "cite specific articles"]
  definition_of_done: "Risk matrix with recommended redlines and clause references"
  delivery_format: "markdown_report"
```

## Prompt: contract negotiation prep

```
Use firm-orchestration with:
  objective: "Prepare negotiation brief for SaaS vendor contract renewal"
  departments: ["legal", "finance", "commercial"]
  constraints: ["no signatures", "max budget: current + 15%"]
  definition_of_done: "Negotiation playbook with red/amber/green clauses"
  delivery_format: "structured_document"
```

## Security notes

- Legal data is sensitive: activate `SECURE_PRODUCTION_MODE=true` in mcp-openclaw
- Enable `AUDIT_ENABLED=true` for all legal workflow runs
- Restrict `OPENCLAW_ALLOWED_METHODS` to `agent.run,sessions_send`
- Use `dmPolicy: "pairing"` on all channels

## Compliance coverage

| Regulation | Coverage |
|---|---|
| GDPR / CCPA | Privacy/Data Protection service |
| SOC 2 | Security & Compliance quality service |
| ISO 27001 | Security audit trail + documentation ops |
| Contract law | Contracting service + IP legal |

---

## 💎 Support

Si ce skill vous est utile, vous pouvez soutenir le développement :

**Dogecoin** : `DQBggqFNWsRNTPb6kkiwppnMo1Hm8edfWq`
