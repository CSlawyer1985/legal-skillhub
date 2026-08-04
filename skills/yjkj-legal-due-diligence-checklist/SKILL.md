---
slug: legal-due-diligence-checklist
version: "1.0.0"
type: descriptive
language: en
---

# Legal Due Diligence Checklist

## Overview

Creates legal due diligence checklists for transactions, investments, acquisitions, vendor onboarding, and corporate housekeeping. This is a descriptive OpenClaw skill for legal-industry workflow support. It provides structured frameworks, checklists, templates, and issue-spotting prompts. It does not execute code, call external APIs, access legal databases, retrieve court records, automate filings, or perform legal services.

## When to Use

- Preparing diligence requests
- Reviewing target company documents
- Organizing transaction risk findings


## Target Users

- Corporate attorneys
- M&A teams
- Startup counsel
- Investment teams


## Inputs to Collect

- Matter or project context, including jurisdiction if known
- Relevant facts, documents, parties, dates, and constraints
- Desired output format, audience, and level of detail
- Known deadlines, risk concerns, or review priorities

## Core Modules

1. **Corporate records checklist** — provides structured prompts, checklists, and review fields for this area.
2. **Contracts and obligations review** — provides structured prompts, checklists, and review fields for this area.
3. **Employment/IP/compliance review** — provides structured prompts, checklists, and review fields for this area.
4. **Litigation and regulatory search plan** — provides structured prompts, checklists, and review fields for this area.
5. **Red-flag summary template** — provides structured prompts, checklists, and review fields for this area.

## Workflow

1. Confirm the user's legal workflow goal and the relevant practice context.
2. Ask for missing facts, documents, dates, parties, jurisdiction, and audience where needed.
3. Apply the modules below as a structured thinking framework.
4. Produce checklists, templates, matrices, memos, or planning aids tailored to the user's context.
5. Flag uncertainty, verification needs, deadlines, ethics concerns, confidentiality issues, and attorney-review points.

## Expected Outputs

- Diligence request list
- Issue tracker
- Red-flag summary
- Document index

## Example Prompts

- "Create a legal due diligence checklist for a small acquisition."
- "Help organize diligence requests for a startup investment."

## Safety and Legal Limitations

- This skill provides informational workflow support only and is not legal advice.
- It does not create an attorney-client relationship and does not replace review by a qualified attorney.
- Laws, court rules, deadlines, ethics duties, privilege, confidentiality, and professional responsibility rules vary by jurisdiction and matter.
- Users must verify all legal authorities, filing requirements, deadlines, facts, citations, and strategic decisions with qualified counsel.
- The skill must not be used to fabricate evidence, coach false testimony, evade regulation, access data unlawfully, or bypass confidentiality obligations.
- Specific limitation for this skill: Framework only; diligence scope must be tailored by transaction counsel and local law experts.

## Acceptance Criteria

- Package is descriptive only: no handler.py, scripts, external APIs, network calls, or command execution.
- SKILL.md and README.md are English-first and include an explicit legal-information disclaimer.
- Outputs are frameworks, checklists, templates, or planning aids rather than legal conclusions.
- Includes target users, when-to-use guidance, inputs, workflow, outputs, examples, and safety limitations.
- skill.json contains unique slug, tags, trigger keywords, requires_api=false, and readiness=stable.
