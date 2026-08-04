---
name: Contract Clause Extractor
slug: contract-clause-extractor
description: Extract & classify key clauses from contract PDFs into a structured risk summary — with bilingual (CN/EN) support.
tags: [contract, legal, clause-extraction, risk-analysis, pdf, bilingual, china]
version: 1.0.0
license: MIT-0
---

# Contract Clause Extractor (合同条款提取器)

Turn dense contract PDFs into structured, scannable clause summaries with risk ratings. Extract key clauses across 12 standard categories, flag hidden risks, compare multiple contracts side-by-side, and generate bilingual clause translations — all without replacing legal counsel.

## Core Capabilities

- **Multi-format contract ingestion**: Parse PDF, DOCX, plain text, or scanned images (OCR) in Chinese and English
- **12-category clause classification**: Auto-classify every clause into standard legal categories with hierarchical numbering awareness
- **Traffic-light risk annotation**: 🔴 High risk | 🟡 Medium risk | 🟢 Low risk per clause with explanatory reasoning
- **Hidden risk detection**: Flag overly broad indemnities, unilateral termination rights, unreasonable jurisdiction clauses, and missing standard protections
- **Multi-contract comparison**: Align and diff clauses across 2+ contracts for quick discrepancy spotting
- **Bilingual extraction**: Extract key clauses in CN→EN or EN→CN with terminology preservation
- **Modification suggestion engine**: Generate plain-language modification proposals for risky clauses

## Workflow (9 Steps)

### Step 1: Contract Ingestion
**Input**: User uploads contract PDF/DOCX, provides URL, or pastes text. Supports single or multiple files for comparison mode.
**Action**: Identify document structure — page layout, clause numbering pattern (1.1 / Article 1 / 第一条), table presence, signature blocks.
**Output**: Parsed document with structural metadata. If scanned/image PDF, trigger OCR pipeline.
**Logic**: Auto-detect language (Chinese, English, or mixed). Handle password-protected PDFs by requesting password.

### Step 2: Clause Segmentation
**Input**: Parsed document.
**Action**: Segment by clause boundaries using numbering patterns, heading styles, and semantic breaks. Preserve parent-child hierarchy for nested clauses.
**Output**: Indexed clause list with numbering + raw text + parent reference.
**Logic**: Handle non-standard numbering (Chinese legal: 一、/（一）/ 1. / (1)). Handle cross-page clause splits.

### Step 3: Clause Classification
**Input**: Segmented clauses.
**Action**: Classify each clause into one of 12 standard categories using LLM semantic matching:
1. **Payment Terms** (付款条款) — amounts, schedules, milestones, late fees
2. **Delivery/Performance** (交付/履约条款) — scope, timeline, acceptance criteria
3. **Breach & Penalties** (违约责任) — liquidated damages, remedies, cure periods
4. **Confidentiality** (保密条款) — scope, duration, exclusions, return/destruction
5. **Intellectual Property** (知识产权) — ownership, licensing, work-for-hire, background IP
6. **Non-Compete / Non-Solicit** (竞业限制) — scope, duration, geographic limits
7. **Jurisdiction & Dispute Resolution** (管辖权/争议解决) — governing law, venue, arbitration
8. **Termination** (终止条款) — termination for cause, convenience, effects of termination
9. **Force Majeure** (不可抗力) — definition, notice, consequences
10. **Liability & Indemnity Caps** (赔偿上限) — total liability, damages exclusions, indemnification scope
11. **Acceptance Criteria** (验收标准) — testing, UAT, defect remediation
12. **Renewal & Term** (续约/期限) — initial term, auto-renewal, notice periods

**Output**: Clauses grouped by category with confidence scores.

### Step 4: Risk Annotation
**Input**: Classified clauses.
**Action**: Score each clause on risk level:
- **🔴 High Risk**: Unlimited liability, one-sided termination, unreasonable jurisdiction, missing standard protections, IP grab, excessive penalty ratios
- **🟡 Medium Risk**: Ambiguous language, unbalanced but market-standard terms, narrow cure periods, broad force majeure
- **🟢 Low Risk**: Balanced terms, boilerplate with no unusual provisions, standard commercial terms

**Output**: Each clause tagged with risk level + brief explanation of why.

### Step 5: Hidden Risk Detection
**Input**: Entire contract + risk-annotated clauses.
**Action**: Pattern-based scanning for structural risks:
- Overly broad indemnification (e.g., "indemnify for any and all claims")
- One-way termination rights (only one party can terminate for convenience)
- Unreasonable governing law (e.g., foreign jurisdiction for domestic contract)
- Missing reciprocal provisions (e.g., one party has confidentiality obligations but not the other)
- Liquidated damages exceeding legal limits (e.g., >30% of contract value under PRC law)
- Automatic renewal without notice

**Output**: "Hidden Risk Alerts" section with specific clause references and severity rating.

### Step 6: Clause Summarization
**Input**: Risk-annotated clauses.
**Action**: Generate a structured extraction table:

| # | Clause Category | Original Text (excerpt) | Summary | Risk | Modification Suggestion |
|---|----------------|------------------------|---------|------|------------------------|
| 1 | Payment | "乙方应在收到发票后90日内付款" | 90-day payment term | 🟡 | Negotiate to 30 days standard |
| 2 | Liability | "赔偿上限为合同金额的1倍" | Liability cap = 1× contract value | 🟢 | Standard protection |

**Output**: Complete extraction table. Option to export as CSV/XLSX.

### Step 7: Multi-Contract Comparison (if applicable)
**Input**: 2+ contracts with their extraction tables.
**Action**: Align clauses by category, then:
- Identify clauses present in Contract A but missing in Contract B
- Detect wording differences in matching clauses
- Flag clauses where risk levels differ between contracts

**Output**: Side-by-side comparison table with diff highlights.

### Step 8: Bilingual Extraction (optional)
**Input**: Extraction table + target language selection.
**Action**: Translate clause summaries and key terms while preserving legal terminology consistency. Build an ad-hoc bilingual term glossary for the document.
**Output**: Bilingual extraction table (Original → Summary in Target Language). Key terms glossary.

### Step 9: Report Generation
**Input**: All analysis results.
**Action**: Compile into a comprehensive extraction report:
1. **Executive Summary**: Contract type, parties, date, overall risk score
2. **Risk Summary**: Count of 🔴/🟡/🟢 clauses, top 5 risks
3. **Clause Extraction Table**: Full categorized table
4. **Hidden Risk Alerts**: Specific warnings
5. **Modification Playbook**: Prioritized negotiation recommendations
6. **Export**: Markdown (editable), PDF (shareable), JSON (API consumption)

**Output**: Complete extraction report.

## Sample Prompts

### Prompt 1: Single Contract Quick Scan
**User**: "帮我快速提取这份合同的关键条款，标出风险点 [upload: supply-agreement.pdf]"
**Expected Output**:
```
Executive Summary: Supply Agreement | Parties: Company A vs Company B | Term: 1 year | Overall Risk: 🟡 Medium

Clause Extraction (18 clauses, 12 categories):
🔴 High Risk (2):
  - Indemnity: "甲方承担一切赔偿责任" — Unlimited indemnity, one-sided
  - Termination: "乙方可随时终止合同" — Unilateral termination without cause

🟡 Medium Risk (5):
  - Payment: Net-90 terms, market standard is Net-30
  - Force Majeure: Overly broad definition includes "market conditions"

🟢 Low Risk (11): Standard commercial terms

⚠️ Hidden Risk Alert: No confidentiality clause for Party A (imbalanced)
Top 3 Modification Priorities: 1. Cap indemnity 2. Add mutual termination 3. Shorten payment to Net-30
```

### Prompt 2: Multi-Contract Comparison
**User**: "对比这两份合同的关键差异 [upload: contract-v1.pdf, contract-v2.pdf]"
**Expected Output**: Side-by-side comparison table with 7 categories showing differences, highlighting where v2 is more/less favorable than v1, with a "verdict" column indicating which version is preferred per category.

### Prompt 3: Hidden Risk Deep-Dive
**User**: "这份30页的服务合同我不敢签，帮我找找有没有坑 [upload: service-agreement.docx]"
**Expected Output**: Hidden risk report focused on 6 structural risk patterns, each with: the offending clause text, why it's problematic, and suggested alternative wording.

### Prompt 4: Bilingual Extraction
**User**: "提取这份中文合同的核心条款，翻译成英文给海外法务看 [upload: nda-zh.pdf]"
**Expected Output**: Bilingual table with Chinese original + English summary for key clauses. Glossary: 保密信息→Confidential Information, 接收方→Receiving Party, etc. Flag terms where translation may create ambiguity.

### Prompt 5: Missing Clause Audit
**User**: "检查这份合同是否缺少了标准商业合同应该有的条款 [upload: vendor-contract.pdf]"
**Expected Output**: Checklist of 12 standard clause categories with ✓/✗ status. For missing categories, explain the risk of omission and suggest a model clause.

### Prompt 6: Negotiation Prep
**User**: "明天要和供应商谈合同，帮我准备谈判要点 [upload: draft-contract.docx]"
**Expected Output**: Prioritized negotiation playbook: Tier 1 (non-negotiable risks → must fix), Tier 2 (market-standard adjustments → push for), Tier 3 (nice-to-have → concede gracefully), with talking points for each.

## Real Task Examples

### Example 1: Startup Vendor Contract
**Scenario**: Early-stage startup receives a 15-page SaaS vendor agreement. No in-house legal.
**Input**: Upload PDF of vendor contract. Concern: "作为小公司，会不会被大厂合同坑？"
**Steps**:
1. Parse → 15 pages, 42 clauses, CN/EN bilingual.
2. Classify → 12 categories covered, missing Acceptance Criteria.
3. Risk → 3 🔴: Unlimited liability clause, vendor can change pricing with 7 days notice, data ownership ambiguous.
4. Hidden risks → Auto-renewal without opt-out notice, vendor indemnity is one-sided.
5. Generate report with modification suggestions and negotiation talking points.
**Output**: "⚠️ 重点风险: 数据归属条款模糊 —— 你的用户数据可能被供应商使用。建议修改为: 'All Customer Data remains Customer's exclusive property.'"
**Time**: ~30 seconds.

### Example 2: Employment Contract Check (Individual)
**Scenario**: Job seeker receives offer + employment contract. Wants to understand restrictions.
**Input**: "帮我看看这份劳动合同，重点看竞业限制和知识产权条款 [upload: employment-contract.pdf]"
**Steps**:
1. Focus: Non-compete, IP assignment, termination notice period.
2. Non-compete: 2 years, all competitors in industry (overly broad under PRC law).
3. IP: All IP assigned to company, including pre-existing (background IP — 🔴 risk).
4. Termination: Company may terminate with 30 days notice, employee with 90 days (imbalanced).
**Output**: "竞业限制: 范围过宽，建议限定为直接竞争公司。知识产权: 要求排除入职前已有知识产权。解除通知期: 不对等，建议双方均为30日。"

### Example 3: Lease Agreement Quick Check
**Scenario**: User about to sign a 24-month commercial lease.
**Input**: "租办公室的合同，帮我提取关键信息 [upload: lease-agreement.pdf]"
**Steps**:
1. Classify: Payment (rent + deposit), Termination (early exit penalty), Renewal, Maintenance obligations.
2. Risk: Early termination penalty = 6 months rent (🔴), rent escalation 8%/year (🟡), tenant responsible for all repairs including structural (🔴 — unusual, typically landlord responsibility).
3. Missing: Force majeure clause (risk during pandemic scenarios).
**Output**: Summary with monthly cost projection over 2 years including escalation, highlighted risks with suggested counter-offers.

## 🚀 First-Success Path (3 Steps)

1. **Step 1**: Run `contract-clause-extractor.sh classify contract.pdf` — parses and extracts all clauses into 12 categories
2. **Step 2**: Run `contract-clause-extractor.sh risk contract.pdf` — annotates each clause with 🔴/🟡/🟢 risk levels
3. **Step 3**: Run `contract-clause-extractor.sh summarize contract.pdf` — see the structured extraction table with modification suggestions

## Boundary Conditions

| Condition | Behavior |
|-----------|----------|
| Contract >100 pages | Process in chunks; summarize by chapter, flag time estimate |
| Scanned/image PDF (no text layer) | Trigger OCR; warn of possible extraction errors |
| Password-protected PDF | Request password; never attempt to crack |
| Non-contract document uploaded | Detect and warn: "This does not appear to be a legal contract" |
| Contract in unsupported language | Attempt processing; flag lower confidence for non-CN/EN languages |
| Handwritten annotations in PDF | Flag as "may contain markings" — OCR may miss handwritten text |
| Corrupted/unreadable PDF | Error with suggested fixes (re-export, convert format) |
| Multiple unrelated contracts in one PDF | Auto-detect and offer to process separately |
| User asks for legal advice | Redirect: "This is clause extraction + risk flagging, not legal advice. Consult a qualified lawyer." |

## Error Handling

| Error Code | Scenario | Handling |
|-----------|----------|----------|
| E-PARSE-FAIL | PDF structure cannot be parsed | Offer manual text input; suggest re-exporting PDF from source |
| E-OCR-FAIL | OCR on scanned document fails | Return images with note; suggest higher-quality scan |
| E-PASSWORD | Password-protected PDF without password | Prompt for password; never attempt brute-force |
| E-NO-CLAUSES | Document has no detectable clause structure | Process as paragraph-level; flag as "unstructured document" |
| E-UNSUPPORTED-FORMAT | Uploaded file is not PDF/DOCX/TXT | List supported formats; suggest conversion |
| E-AMBIGUOUS-CLASSIFICATION | Clause spans multiple categories | Tag with multiple categories; flag for human review |
| E-BILINGUAL-CONFIDENCE | Low confidence on legal term translation | Mark with ⚠️ "Translation may need legal review" |

## Security Requirements

- **Document confidentiality**: Contract contents processed locally; never sent to external services for storage. Session-only processing.
- **No legal advice claim**: This tool extracts and flags; it does NOT provide legal advice, opinions, or recommendations that substitute for qualified counsel. Always include disclaimer.
- **Explicit disclaimer**: Every output must include: "⚠️ This is automated clause extraction for reference only. It is NOT legal advice. Consult a qualified lawyer before making contractual decisions."
- **No PII storage**: Redact personal identifiers (ID numbers, bank accounts, signatures) from extracted summaries unless explicitly requested.
- **Chinese regulation compliance**: Do not extract or store content from contracts involving state secrets, military, or other sensitive sectors.
- **Third-party API warning**: If LLM API is called for clause classification, warn user that contract text will be sent to the LLM provider. Offer local-only mode for sensitive contracts.
