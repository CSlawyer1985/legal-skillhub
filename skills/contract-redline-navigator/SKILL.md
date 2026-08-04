---
name: contract-redline-navigator
description: Compare draft agreements, highlight risky clause changes, and generate
  a negotiation checklist with plain-language explanations.
version: 1.1.0
metadata:
  openclaw:
    requires:
      bins:
      - python3
    emoji: 🧰
---

# Contract Redline Navigator

## Purpose

Compare draft agreements, highlight risky clause changes, and generate a negotiation checklist with plain-language explanations.

## Trigger phrases

- 合同对比
- redline this contract
- 比较两个协议版本
- 找风险条款
- 做谈判清单

## Ask for these inputs

- old draft and new draft
- contract type
- risk tolerance
- counterparty type
- must-have fallback positions

## Workflow

1. Diff the two clause sets and isolate added, removed, and changed language.
2. Check bundled high-risk clause patterns such as indemnity, liability caps, auto-renewal, IP assignment, exclusivity, and data use.
3. Explain material changes in plain language.
4. Produce a negotiation checklist with fallback wording and questions for counsel.
5. Avoid pretending to be a lawyer; always frame as operational review support.

## Output contract

- risk-change summary
- negotiation checklist
- clause-by-clause diff
- plain-language brief

## Files in this skill

- Script: `{baseDir}/scripts/clause_diff.py`
- Resource: `{baseDir}/resources/risk_clauses.md`

## Operating rules

- Be concrete and action-oriented.
- Prefer preview / draft / simulation mode before destructive changes.
- If information is missing, ask only for the minimum needed to proceed.
- Never fabricate metrics, legal certainty, receipts, credentials, or evidence.
- Keep assumptions explicit.

## Suggested prompts

- 合同对比
- redline this contract
- 比较两个协议版本

## Use of script and resources

Use the bundled script when it helps the user produce a structured file, manifest, CSV, or first-pass draft.
Use the resource file as the default schema, checklist, or preset when the user does not provide one.

## Boundaries

- This skill supports planning, structuring, and first-pass artifacts.
- It should not claim that files were modified, messages were sent, or legal/financial decisions were finalized unless the user actually performed those actions.


## Compatibility notes

- Directory-based AgentSkills/OpenClaw skill.
- Runtime dependency declared through `metadata.openclaw.requires`.
- Helper script is local and auditable: `scripts/clause_diff.py`.
- Bundled resource is local and referenced by the instructions: `resources/risk_clauses.md`.
