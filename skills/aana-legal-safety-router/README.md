# AANA Legal Safety Router Skill

This OpenClaw-style skill helps agents prevent unauthorized legal advice, missing jurisdiction caveats, and unsupported legal claims.

## Marketplace Slug

Recommended slug:

```text
aana-legal-safety-router
```

## Contents

- `SKILL.md`: agent-facing instructions.
- `manifest.json`: review metadata and boundaries.
- `schemas/legal-safety-review.schema.json`: optional review-payload shape.
- `examples/redacted-legal-safety-review.json`: safe example payload.

## What It Does

The skill asks the agent to:

1. Separate general legal information from legal advice.
2. Add jurisdiction and current-law caveats or ask when jurisdiction is missing.
3. Avoid unsupported claims about laws, deadlines, rights, penalties, enforceability, eligibility, or outcomes.
4. Route high-impact, deadline-sensitive, court, criminal, immigration, family, housing, employment, or rights-affecting matters to qualified legal help.
5. Minimize private legal data in review payloads and replies.

## What It Does Not Do

This package does not:

- install dependencies,
- execute code,
- call remote services,
- write files,
- persist memory,
- inspect legal records by itself,
- provide licensed legal advice by itself.

## Safety Model

Use redacted summaries for review payloads. Do not include raw legal records, full court filings, contracts with private details, government IDs, immigration numbers, identity documents, private messages, medical records, financial records, credentials, or unrelated private data.

High-impact, deadline-sensitive, jurisdiction-specific, or rights-affecting legal decisions should be routed to trusted legal sources, legal aid, qualified attorneys, or human review.
