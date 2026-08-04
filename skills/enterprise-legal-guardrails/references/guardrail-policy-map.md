# Enterprise Legal Guardrails - Policy Map

This map defines rule families used by `scripts/check_enterprise_guardrails.py`.

## Core families

- `legal` – legal-conclusion or legal-process claims that look like definitive legal claims.
- `defamation` – unverified allegations against named parties.
- `financial` – guaranteed outcomes, certainty claims, or absolute market predictions.
- `market` – market manipulation framing, coordinated trade narratives.
- `antispam` – unsolicited amplification/fake urgency and coordinated prompts.
- `harassment` – abuse, threats, doxxing behavior.
- `privacy` – personal identifiers and sensitive disclosures.
- `hr` – discrimination, retaliation, workplace intimidation, or sensitive employee-conduct accusations.

## Guidance

- Prefer factual statements with uncertainty framing.
- Avoid accusatory certainty language unless it is verifiable and contextually required.
- For legal claims, switch to:
  - opinion framing
  - factual basis
  - disclaimer where appropriate
- For anti-spam: require consent, relevance, and no manipulative call-to-action.
- For HR-sensitive messaging: avoid protected-class references unless strictly necessary and policy-justified.

## Decision meanings

- `PASS` → execute.
- `WATCH` → optional cleanup is recommended.
- `REVIEW` → send to manual review.
- `BLOCK` → stop and rewrite.
