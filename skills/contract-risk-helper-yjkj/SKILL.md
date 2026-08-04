---
name: contract-risk-helper
description: Contract Risk Helper — scan contracts for common risk clauses. Triggers on 合同风险、合同审查、条款风险、帮我看合同、合同检查. Read-only local analysis, no network calls, no credential access.
---

# Contract Risk Helper

## Overview

Contract Risk Helper identifies common risk clauses in contract text using local pattern matching. **No network calls, no credential access, no exec** — pure read-only text analysis.

**⚠️ Disclaimer**: Preliminary identification only. Not legal advice. Consult a qualified attorney for important decisions.

## When to Use

- User provides contract text and asks for risk scan
- Keywords: 合同风险、合同审查、条款风险、帮我看合同、合同检查、扫描合同

## Workflow

1. **Receive contract text** — user provides full contract or specific clauses
2. **Identify contract type** — service agreement, NDA, employment, lease, etc.
3. **Run local pattern scan** — match against known risk patterns (reference file)
4. **Return findings** — categorized by severity (critical/warning/advisory) with suggestions
5. **Flag for attorney review** — for critical items

## Risk Categories

| Severity | Examples |
|----------|----------|
| 🔴 Critical | Unlimited liability, no termination for convenience, broad indemnification |
| 🟡 Warning | Net 60+ payment, auto-renewal without notice, work-for-hire without scope limit |
| 🟢 Advisory | Missing dispute resolution clause, ambiguous definitions |

## Output Format

```
## 风险扫描结果

共发现 N 个风险项

### 🔴 Critical (X)
- **[条款位置]** 描述
  → 建议操作

### 🟡 Warning (X)
- **[条款位置]** 描述
  → 建议操作
```

## Notes

- All analysis is local pattern matching against reference/common-risks.md
- No data leaves the local environment
- Does not store or transmit contract content
- No external API calls
