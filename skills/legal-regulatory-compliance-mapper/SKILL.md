---
slug: legal-regulatory-compliance-mapper
version: 1.1.1
type: descriptive
language: en
tags: compliance, regulatory-mapping, legal-operations, multi-jurisdiction
---

# Legal Regulatory Compliance Mapper

## Overview

Helps map regulatory obligations, controls, owners, evidence, and review cadence for a product, business unit, or jurisdiction. This is a descriptive OpenClaw skill for legal-industry workflow support. It provides structured frameworks, checklists, templates, and issue-spotting prompts. It does not execute code, call external APIs, access legal databases, retrieve court records, automate filings, or perform legal services.

## When to Use

- Building a compliance program
- Entering a regulated market
- Preparing an internal audit


## Target Users

- Compliance counsel
- In-house legal teams
- Risk managers
- Startup operators


## Inputs to Collect

- Matter or project context, including jurisdiction if known
- Relevant facts, documents, parties, dates, and constraints
- Desired output format, audience, and level of detail
- Known deadlines, risk concerns, or review priorities

## Core Modules

1. **Regulatory obligation inventory** — provides structured prompts, checklists, and review fields for this area.
2. **Control-owner mapping** — provides structured prompts, checklists, and review fields for this area.
3. **Evidence and documentation tracker** — provides structured prompts, checklists, and review fields for this area.
4. **Review cadence planner** — provides structured prompts, checklists, and review fields for this area.
5. **Issue escalation matrix** — provides structured prompts, checklists, and review fields for this area.

## Workflow

1. Confirm the user's legal workflow goal and the relevant practice context.
2. Ask for missing facts, documents, dates, parties, jurisdiction, and audience where needed.
3. Apply the modules below as a structured thinking framework.
4. Produce checklists, templates, matrices, memos, or planning aids tailored to the user's context.
5. Flag uncertainty, verification needs, deadlines, ethics concerns, confidentiality issues, and attorney-review points.
6. Label every obligation row with jurisdiction, source basis, verification status, owner, evidence, review cadence, and attorney-review trigger.

## Expected Outputs

- Compliance obligation map
- Controls tracker
- Evidence checklist
- Review calendar
- Verification gap list

## Required Output Columns

When producing a matrix, include these columns unless the user asks for a shorter
format:

| Column | Purpose |
|---|---|
| Jurisdiction | Country/state/region or "unknown" |
| Obligation / Issue | The compliance topic to verify |
| Source basis | User-provided source, known framework, or "needs authoritative source" |
| Verification status | confirmed by user / likely / unknown / needs counsel |
| Owner | Business, legal, compliance, product, security, or other owner |
| Evidence | Document, control, filing, policy, log, or artifact to retain |
| Review cadence | One-time, launch gate, monthly, quarterly, annual, event-driven |
| Attorney-review trigger | Why qualified counsel should review |

## Example Prompts

- "Map compliance obligations for a fintech product launch."
- "Create a regulatory controls tracker for a healthcare startup."

## Safety and Legal Limitations

- This skill provides informational workflow support only and is not legal advice.
- It does not create an attorney-client relationship and does not replace review by a qualified attorney.
- Laws, court rules, deadlines, ethics duties, privilege, confidentiality, and professional responsibility rules vary by jurisdiction and matter.
- Users must verify all legal authorities, filing requirements, deadlines, facts, citations, and strategic decisions with qualified counsel.
- The skill must not be used to fabricate evidence, coach false testimony, evade regulation, access data unlawfully, or bypass confidentiality obligations.
- Specific limitation for this skill: Does not determine full legal compliance; users must confirm obligations with qualified jurisdiction-specific professionals.
- Do not invent citations, filing deadlines, regulator names, thresholds, or license requirements. If the user has not provided an authoritative source, mark the item as a verification gap.

## Acceptance Criteria

- Package is descriptive only: no handler.py, scripts, external APIs, network calls, or command execution.
- SKILL.md and README.md are English-first and include an explicit legal-information disclaimer.
- Outputs are frameworks, checklists, templates, or planning aids rather than legal conclusions.
- Includes target users, when-to-use guidance, inputs, workflow, outputs, examples, and safety limitations.
- skill.json contains unique slug, tags, trigger keywords, requires_api=false, and readiness=stable.
- Matrices include jurisdiction, source basis, verification status, evidence, cadence, and attorney-review trigger.


## Usage Scenarios

| # | User Input | Expected Output |
|---|---|---|
| 1 | "Map the regulatory requirements for a fintech offering BNPL services in the US, UK, and Australia." | Jurisdiction comparison matrix: US (state-level lender licenses, CFPB oversight, TILA disclosure), UK (FCA authorization, Consumer Duty, CONC rules), Australia (ASIC credit license, NCCP Act, DDO). Color-coded: harmonized (AML/KYC), divergent (rate-cap rules), missing (Australian BNPR code pending). |
| 2 | "We are compliant in the EU. What additional requirements apply if we add Singapore?" | Delta analysis: additional requirements (MAS licensing for payment services, PDPA data-protection obligations, Singapore-specific consumer-protection guidelines). Implementation roadmap with 90-day timeline. |
| 3 | "Generate a compliance calendar with all filing deadlines, renewal dates, and audit requirements across our 5 operating countries." | Annual calendar: Q1 (US annual report, EU DPO review), Q2 (UK FCA renewal, AU ASIC levy), Q3 (SG MAS quarterly return), Q4 (US state license renewals, EU SCC review). Deadline-alert settings and document-prep checklists per event. |


### Scenario 2: 开公司要办什么证
**User input:** "我想在上海注册一家餐饮公司，但搞不清楚要办哪些许可证、怎么办、找谁办。能帮我梳理一下流程吗？"
**Expected output:** 上海餐饮公司开办证照流程——第一步：营业执照（去上海市市场监督管理局网站/一网通办线上申请，经营范围写"餐饮服务""食品销售"，约3-5个工作日）；第二步：食品经营许可证（拿到营业执照后申请，需要场地平面图+食品安全管理制度+健康证，15个工作日）；第三步：消防安全检查合格证（消防部门实地检查后才发，50-200平方米的餐饮店必须通过）；第四步：环境影响登记表（环保局备案，网上填表即可）；第五步：税务登记（拿到营业执照后30天内办好，在一网通办上就能一起办）。总流程约45-60天。关键工具：上海一网通办（zwdt.sh.gov.cn）+各区行政服务中心现场咨询。
