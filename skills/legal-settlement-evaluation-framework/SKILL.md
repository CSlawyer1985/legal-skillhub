---
slug: legal-settlement-evaluation-framework
version: "1.1.0"
type: descriptive
language: en
tags: settlement-analysis, litigation-strategy, risk-evaluation, legal-decision-support, dispute-resolution
---


# Legal Settlement Evaluation Framework

## Overview

Helps evaluate settlement options using exposure, evidence strength, litigation cost, non-monetary terms, timing, and uncertainty. This is a descriptive OpenClaw skill for legal-industry workflow support. It provides structured frameworks, checklists, templates, and issue-spotting prompts. It does not execute code, call external APIs, access legal databases, retrieve court records, automate filings, or perform legal services.

## When to Use

- Assessing settlement offers
- Preparing client recommendation memos
- Comparing litigation versus resolution options


## Target Users

- Litigators
- In-house counsel
- Claims teams
- Business stakeholders


## Inputs to Collect

- Matter or project context, including jurisdiction if known
- Relevant facts, documents, parties, dates, and constraints
- Desired output format, audience, and level of detail
- Known deadlines, risk concerns, or review priorities

## Core Modules

1. **Exposure and damages range table** — provides structured prompts, checklists, and review fields for this area.
2. **Evidence strength factors** — provides structured prompts, checklists, and review fields for this area.
3. **Cost/time/risk comparison** — provides structured prompts, checklists, and review fields for this area.
4. **Non-monetary term checklist** — provides structured prompts, checklists, and review fields for this area.
5. **Decision memo template** — provides structured prompts, checklists, and review fields for this area.

## Workflow

1. Confirm the user's legal workflow goal and the relevant practice context.
2. Ask for missing facts, documents, dates, parties, jurisdiction, and audience where needed.
3. Apply the modules below as a structured thinking framework.
4. Produce checklists, templates, matrices, memos, or planning aids tailored to the user's context.
5. Flag uncertainty, verification needs, deadlines, ethics concerns, confidentiality issues, and attorney-review points.

## Expected Outputs

- Settlement evaluation matrix
- Risk-adjusted comparison
- Client recommendation outline
- Open issues list

## Example Prompts

- "Build a settlement evaluation matrix for a contract dispute."
- "Help compare accepting an offer versus continuing litigation."

## Usage Scenarios

### Scenario 1

**User input:** "Plaintiff offered $85K settlement on our $200K claim. Evidence is mixed. Should we accept?"

**Expected output:** Structured cost-benefit matrix weighing evidence strength (60% confidence), litigation costs ($40K estimated), time-to-resolution (18 months), and non-monetary factors (precedent risk, confidentiality value).

### Scenario 2

**User input:** "Evaluate three settlement options for an employment dispute with a former executive."

**Expected output:** Comparative table scoring each option on exposure limit, reputational impact, enforceability, tax implications, and future-relationship preservation.

### Scenario 3

**User input:** "Create a settlement evaluation template our legal team can reuse for consumer class actions."

**Expected output:** Reusable template with fields for claim value, defense cost projection, class size, opt-out risk, media exposure, and insurer coverage alignment.
### Scenario 4: 被车撞了对方想私了
**User input:** "骑电动车被小轿车撞了，轻微擦伤交警定了对方全责，对方想私了赔我3000块完事，接受吗？"
**Expected output:** 评估私了方案的合理性：1）列出潜在医疗费用——急诊检查（CT/X光约300-600元）、后续复查、可能的物理治疗费用；2）误工费——按实际收入计算休息天数；3）电动车维修费；4）精神损害抚慰金（轻微伤一般没有）。建议先去医院做完整检查后再谈赔偿。如果检查后无大碍，建议谈判价位在5000-8000元（含医疗费+3天误工+修车费）。保留对方联系方式、车牌号和事故认定书再签私了协议。如果对方是网约车或共享汽车，一定要走保险。

## Safety and Legal Limitations

- This skill provides informational workflow support only and is not legal advice.
- It does not create an attorney-client relationship and does not replace review by a qualified attorney.
- Laws, court rules, deadlines, ethics duties, privilege, confidentiality, and professional responsibility rules vary by jurisdiction and matter.
- Users must verify all legal authorities, filing requirements, deadlines, facts, citations, and strategic decisions with qualified counsel.
- The skill must not be used to fabricate evidence, coach false testimony, evade regulation, access data unlawfully, or bypass confidentiality obligations.
- Specific limitation for this skill: Does not predict court outcomes or advise acceptance; final settlement decisions require attorney-client analysis.

## Acceptance Criteria

- Package is descriptive only: no handler.py, scripts, external APIs, network calls, or command execution.
- SKILL.md and README.md are English-first and include an explicit legal-information disclaimer.
- Outputs are frameworks, checklists, templates, or planning aids rather than legal conclusions.
- Includes target users, when-to-use guidance, inputs, workflow, outputs, examples, and safety limitations.
- skill.json contains unique slug, tags, trigger keywords, requires_api=false, and readiness=stable.
