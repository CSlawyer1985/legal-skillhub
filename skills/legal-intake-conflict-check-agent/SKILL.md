---
name: legal-intake-conflict-check-agent
version: 1.0.0
description: "Ultra-high-ticket intake agent for Law Firms. Qualifies leads, performs preliminary conflict-of-interest checks, and books consultations. Hardened with ThumbGate to prevent illegal legal advice or unauthorized practice of law (UPL)."
author: "Igor Ganapolsky"
tags: ["legal", "law-firm", "intake", "conflict-check", "thumbgate", "high-ticket"]
price: 497
---

# Legal Intake & Conflict Check Agent with ThumbGate Safety

## What This Agent Does
- Screens new potential clients (PNCs) 24/7 via Voice and Text.
- Performs preliminary conflict checks against your "Adverse Parties" list in Google Sheets.
- Qualifies leads based on Case Type, Statute of Limitations, and Budget.
- Books paid or free consultations directly into Clio, MyCase, or Google Calendar.
- Uses **ThumbGate** to ensure the AI NEVER provides legal advice or makes promises about case outcomes.

## Critical ThumbGate Rules
- **UPL Block:** Physically block any response that begins with "You should..." or "Legally, you can..." or any variation of direct legal advice.
- **No Outcome Promises:** Block any claim that a case is "a winner" or "worth $X" or "easy to win".
- **Conflict Trigger:** If a PNC name matches an entry in the 'Adverse Parties' sheet, immediately block the agent and route to a senior partner.
- **Statute Check:** Block booking a consultation if the incident date is past the calculated Statute of Limitations for the specific case type.

## Setup
1. Upload your 'Adverse Parties' and 'Statute of Limitations' sheets.
2. Link your legal CRM (via Make.com).
3. Load skill: `openclaw skill load legal-intake-agent`
