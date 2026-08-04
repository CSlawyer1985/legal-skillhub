---
slug: legal-due-diligence-checklist
version: "1.1.0"
type: descriptive
language: en
tags: legal-due-diligence, transaction-review, risk-assessment, compliance-checklist, corporate-law
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

## Usage Scenarios

### Scenario 1

**User input:** "We're acquiring a SaaS company with 50 employees in Germany. What due diligence checklist do we need?"

**Expected output:** Structured checklist covering corporate docs, IP, employment, data privacy (GDPR), commercial contracts, and litigation history with priority tiers.

### Scenario 2

**User input:** "Generate a compliance-first DD checklist for a Series A investment in a health-tech startup."

**Expected output:** HIPAA/health-reg focused checklist with regulatory, IP ownership, clinical trial liability, and data handling sections.

### Scenario 3

**User input:** "I need a vendor due diligence template for onboarding a critical IT supplier."

**Expected output:** Vendor DD template covering financial stability, security posture, SLA history, subcontractor dependencies, and exit clauses.
### Scenario 4: 朋友拉我合伙开公司
**User input:** "发小拉我一起开个餐饮公司，他出钱我出技术，说让我占30%，但合同什么都没签，我要怎么先做个尽调？"
**Expected output:** 提供创业合伙简易尽调清单：1）核查发起人信用——通过天眼查/企查查看发小名下公司的经营状态、涉诉记录；2）股权架构建议——明确出资形式（现金/技术/资源折股）、持股比例、分红规则；3）必须签署的法律文件——出资协议、公司章程、竞业限制条款；4）知识产权归属——如果涉及技术或品牌，明确商标和专利的权属。建议先花500-2000元找律师起草一份规范的《股东合作协议》。

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
