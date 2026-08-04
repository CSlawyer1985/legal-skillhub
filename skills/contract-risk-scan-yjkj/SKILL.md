---
name: contract-risk-scan
description: Scan contracts for common risk clauses and potential issues. Use when the user asks about 合同风险、合同审查、条款风险、合同问题、帮我看合同、合同检查, or wants to identify problematic clauses in a contract draft. This skill provides preliminary risk identification only and does not constitute legal advice.
---

# Contract Risk Scan

## Overview

This skill helps users identify common risk clauses and potential issues in contract drafts. It scans for problematic language, ambiguous terms, and high-risk provisions that may need attention.

**⚠️ Important Disclaimer**: This tool provides preliminary risk identification only. It does not constitute legal advice, nor does it replace professional legal counsel. Always consult a qualified attorney for important contract decisions.

## When to Use This Skill

- Reviewing a contract draft before signing
- Identifying potentially risky clauses
- Getting a quick overview of contract concerns
- Preparing questions for legal consultation

## Limitations

- Only identifies **common** risk patterns, not all possible issues
- Cannot assess context-specific risks
- Does not evaluate enforceability under specific jurisdictions
- Not a substitute for professional legal review

## Workflow

1. **Receive contract text** — User provides contract content or specific clauses
2. **Identify contract type** — Determine if it's a service agreement, NDA, employment contract, lease, etc.
3. **Scan for risks** — Check against common risk patterns (see references/common-risks.md)
4. **Report findings** — Present identified risks with severity levels and explanations
5. **Suggest next steps** — Recommend consulting an attorney for high-risk items

## Risk Severity Levels

| Level | Description | Action Recommended |
|-------|-------------|-------------------|
| 🔴 Critical | High-risk clauses that could cause significant harm | Consult attorney immediately |
| 🟡 Warning | Potentially problematic clauses needing review | Discuss with attorney |
| 🟢 Advisory | Minor issues or suggestions for improvement | Consider revisions |

## Common Risk Categories

### 1. Liability & Indemnification
- Unlimited liability clauses
- One-sided indemnification
- Missing liability caps

### 2. Termination
- No termination for convenience
- Excessive notice periods
- Harsh termination penalties

### 3. Payment Terms
- Net 60+ payment terms
- No late payment penalties
- Unclear payment schedules

### 4. Intellectual Property
- Unclear IP ownership
- Overly broad IP assignments
- Missing license grants

### 5. Confidentiality
- Indefinite confidentiality obligations
- Unclear definition of confidential info
- Missing return/destruction clauses

### 6. Dispute Resolution
- Unfair venue selection
- Missing arbitration/mediation clauses
- One-sided attorney fee provisions

## Usage

### Basic Scan
```
"帮我扫描这份合同的风险"
"检查这个条款有没有问题"
"合同风险审查"
```

### Specific Focus
```
"重点看付款条款的风险"
"检查知识产权相关条款"
"看看违约责任部分"
```

## Output Format

For each identified risk:
- **Clause location** (section/paragraph reference)
- **Risk description** (what's problematic)
- **Severity level** (🔴🟡🟢)
- **Suggested action** (what to consider)

## References

For detailed risk patterns and examples, see:
- [references/common-risks.md](references/common-risks.md) — Common contract risk patterns database

## Privacy Note

Contract content is processed for risk analysis only. No contract data is stored or transmitted to third parties.
