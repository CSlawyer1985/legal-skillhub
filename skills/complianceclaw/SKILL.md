---
name: complianceclaw
description: Regulations change 4,000+ times per year. Your clients can't track them all. complianceclaw monitors federal and state regulatory changes, maps them to your clients' obligations, generates compliance checklists, and produces audit-ready reports—before the enforcement action arrives.
homepage: https://github.com/legal-tools/complianceclaw
metadata: {"clawdbot":{"emoji":"🏛️","requires":{"bins":["complianceclaw"]},"install":[{"id":"brew","kind":"brew","formula":"legal-tools/tap/complianceclaw","bins":["complianceclaw"],"label":"Install complianceclaw (brew)"}]}}
---

# complianceclaw

**The regulation changed 6 months ago. Your client just found out from an enforcement notice.**

Federal and state agencies publish 4,000+ rule changes per year. No attorney can read the Federal Register daily. No in-house team can monitor every state agency that touches their business. complianceclaw watches regulatory feeds, maps changes to your clients' industries and obligations, generates compliance checklists, and produces the audit-ready documentation that makes the difference between "we're in compliance" and "we have proof we're in compliance."

**Who it's for:** Regulatory attorneys, in-house compliance teams, healthcare lawyers tracking HIPAA/CMS changes, financial services counsel monitoring SEC/FINRA, and any firm that advises clients in regulated industries.

**What it replaces:** The $200K/year compliance vendor, the associate reading the Federal Register, and the "we didn't know the rule changed" defense that never works.

---

## Pricing

| Feature | Free | Pro ($49/mo) | Enterprise ($199/mo) |
|---|---|---|---|
| Regulatory feeds | Federal Register only | + 50-state + key agencies | All federal + all state + international |
| Industry filters | 1 industry | 5 industries | Unlimited |
| Change monitoring alerts | Weekly digest | Real-time + customizable | Real-time + routing to teams |
| Compliance checklists | 3 templates | 25+ industry templates | Custom + build your own |
| Obligation mapping | — | ✅ | ✅ + cross-client |
| Audit-ready reports | — | ✅ | ✅ + board-ready |
| Gap analysis | — | ✅ | ✅ + remediation tracking |
| Regulatory calendar | — | ✅ | ✅ + integration |
| Client/entity profiles | 1 | 10 | Unlimited |
| Team | 1 | 3 | Unlimited |
| Policy document management | — | — | ✅ |
| Historical regulation lookup | 1 year | 5 years | Full archive |

> `complianceclaw upgrade pro` — 14-day free trial.

---

## Core Commands

**Regulatory Monitoring**
- `complianceclaw watch --industry healthcare --topics "HIPAA,telehealth,surprise billing"`
- `complianceclaw watch --industry fintech --agencies "SEC,FINRA,CFPB,OCC"`
- `complianceclaw watch --industry "cannabis" --states "CA,CO,NY,IL"`
- `complianceclaw watch --cfr-title 21 --parts "800-899"` — Specific CFR parts (medical devices)
- `complianceclaw feed --last 7` — What changed this week
- `complianceclaw feed --last 7 --impact high` — High-impact changes only
- `complianceclaw feed --agency SEC --last 30`

**Compliance Checklists**
- `complianceclaw checklist generate --framework HIPAA --entity "HealthCo Inc"`
- `complianceclaw checklist generate --framework "SOX" --entity "PublicCorp"`
- `complianceclaw checklist generate --framework "CCPA" --entity "TechStartup"`
- `complianceclaw checklist status --entity "HealthCo Inc" --framework HIPAA` — Progress
- `complianceclaw checklist item done --id CHK-0042 --evidence "policy_v3.pdf" --by "J. Smith"`
- `complianceclaw checklist export --entity "HealthCo Inc" --format pdf` — Audit-ready

**Obligation Mapping (Pro)**
- `complianceclaw obligation map --entity "HealthCo Inc"` — All obligations by source
- `complianceclaw obligation add --entity "HealthCo Inc" --regulation "HIPAA 164.530(j)" --description "Retain policies for 6 years" --deadline recurring-yearly`
- `complianceclaw obligation list --entity "HealthCo Inc" --overdue`
- `complianceclaw obligation list --entity "HealthCo Inc" --upcoming 90`
- `complianceclaw obligation assign --id OBL-0012 --to "compliance@healthco.com"` (Enterprise)

**Gap Analysis (Pro)**
- `complianceclaw gap-analysis --entity "HealthCo Inc" --framework HIPAA`
- `complianceclaw gap-analysis --entity "FinCo" --framework "SOC 2 Type II"`
- `complianceclaw gap-analysis --entity "TechStartup" --regulation "AI Act"` — EU AI Act readiness

**Output:**
```
🟢 14.530(a) - Privacy notice: COMPLIANT (evidence: privacy_policy_v4.pdf)
🟡 164.308(a)(1) - Risk analysis: PARTIAL (last assessment: 14 months ago)
🔴 164.312(e)(1) - Encryption in transit: NON-COMPLIANT (no evidence found)
🔴 164.530(j) - Record retention: NON-COMPLIANT (retention policy expired)
```

**Regulatory Calendar**
- `complianceclaw calendar --entity "HealthCo Inc"` — All regulatory deadlines
- `complianceclaw calendar --next 90` — Cross-entity upcoming deadlines
- `complianceclaw calendar sync --google` — Sync to Google Calendar (Enterprise)

**Reporting**
- `complianceclaw report --entity "HealthCo Inc" --framework HIPAA --format pdf`
- `complianceclaw report --entity "HealthCo Inc" --board-ready` (Enterprise)
- `complianceclaw report --all-entities --summary` — Portfolio compliance status
- `complianceclaw report --changes --period 2026-Q1` — Regulatory changes impact report

**Regulation Lookup**
- `complianceclaw lookup "42 CFR 482"` — Hospital Conditions of Participation
- `complianceclaw lookup "CCPA" --current` — Current full text
- `complianceclaw lookup "HIPAA 164.312" --history` — Amendment history (Enterprise)
- `complianceclaw search "data breach notification" --state all` — Cross-state comparison

---

## Supported Frameworks & Industries

Healthcare: HIPAA, HITECH, Stark Law, Anti-Kickback, 42 CFR Part 2, CMS CoP
Financial: SOX, Dodd-Frank, BSA/AML, FINRA, SEC, GLBA, FCRA, CFPB
Privacy: CCPA/CPRA, GDPR, VCDPA, CPA, CTDPA, state breach notification
Technology: AI Act (EU), NIST CSF, SOC 2, ISO 27001, FedRAMP
Healthcare IT: ONC, 21st Century Cures Act, Information Blocking
Cannabis: State-by-state regulatory tracking
Energy: FERC, NERC CIP, EPA, state PUC
Employment: FLSA, OSHA, ADA, FMLA, state wage & hour

---

## Notes

- Federal Register data is public/free; state regulatory feeds require Pro+
- Combine with `contractclaw` for contract obligations that have compliance implications
- Combine with `caseclaw` for deadline tracking on regulatory filing dates
- Regulatory data updated daily (Pro) or real-time (Enterprise)
