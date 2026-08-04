---
name: eu-ai-compliance
description: EU AI Act risk classification, Article 12 compliance logging, and self-assessment reports — deadline August 2, 2026
user-invocable: true
metadata: {"openclaw":{"requires":{"env":[]}},"homepage":"https://soulledger.sputnikx.xyz/compliance","author":"SputnikX","version":"1.0.0","tags":["compliance","eu-ai-act","regulation","audit","risk"]}
---

# EU AI Act Compliance

Free risk classification + paid full assessments. EU AI Act enforcement deadline: August 2, 2026. Fines: EUR 35M or 7% global turnover.

## Base URL

`https://soul.sputnikx.xyz`

## Endpoints

### Risk Classification (FREE)
```bash
curl "https://soul.sputnikx.xyz/soul/compliance/risk-classification?description=facial+recognition+for+hiring"
```
Returns: `{ risk_level, reasoning, annex_iii_matches, disclaimer }` — instant HIGH/LIMITED/MINIMAL classification.

### Article 12 Mapping (FREE)
```bash
curl https://soul.sputnikx.xyz/soul/compliance/mapping
```
Returns: Full Article 12 → data field mapping for compliance logging requirements.

### Self-Assessment ($1.00 x402 USDC)
```bash
curl https://soul.sputnikx.xyz/soul/compliance/self-assessment/{agent_id}
```
Complete EU AI Act self-assessment report with recommendations.

### Annex IV Technical Documentation ($1.00 x402 USDC)
```bash
curl https://soul.sputnikx.xyz/soul/compliance/annex-iv/{agent_id}
```

### Annex V EU Declaration ($0.50 x402 USDC)
```bash
curl https://soul.sputnikx.xyz/soul/compliance/annex-v
```

### Full Compliance Report ($2.00 x402 USDC)
```bash
curl https://soul.sputnikx.xyz/soul/compliance/full-report
```
Complete bundle: risk classification + self-assessment + Annex IV + Annex V.

## Web Interface

Free compliance checker: https://soulledger.sputnikx.xyz/compliance

## Infrastructure

- Hash-chain logging (SHA-256, append-only)
- Merkle root anchoring on Base chain
- Behavioral drift detection
- Runtime monitoring (not one-time reports)

## When to use this skill
- Check if your AI system is EU AI Act compliant
- Generate compliance documentation before the August 2026 deadline
- Implement Article 12 automatic logging
- Get risk classification for any AI system description
