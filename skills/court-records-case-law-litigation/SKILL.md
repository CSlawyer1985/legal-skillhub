---
name: court-records-case-law-litigation
description: Court records, case law & litigation search for AI agents — search US court opinions and case law by keyword via CourtListener. Use to find lawsuits, legal precedent, or litigation involving a company, person, or topic — for due diligence, legal research, and risk checks. Pay-per-call in USDC via x402 — no API key, no signup.
tags: [court-records, case-law, litigation, lawsuit, legal-research, courtlistener, opinions, precedent, due-diligence, legal]
author: gocreative
version: 1.0.0
license: MIT
---

# Court Records, Case Law & Litigation

> Search US court opinions and case law by keyword. One install, pay-per-call, no API key.

## When to use this
- Find **lawsuits or litigation** involving a company or person.
- Pull **case law / legal precedent** on a topic.
- Add a **litigation check** to due diligence.

## How it's paid (x402)
Plain HTTPS GET. First call returns HTTP 402; your wallet auto-pays the USDC fee and retries → JSON.

## Tool
| Call | What you get | Price |
|---|---|---|
| `GET https://api.gocreativeai.com/v1/lookup/case-law/{keyword}` | Matching US court opinions / case law (CourtListener) | ~$0.03 |

Example: `GET /v1/lookup/case-law/data%20breach%20negligence` → matching opinions.

## Why GoCreative
Live US court-opinion data, pay-per-call, no signup — the **only native case-law/litigation search for agents** (pairs with `gocreative-compliance` for full due diligence).

*Provider: GoCreative — Agent Compliance & Data API · https://api.gocreativeai.com*
