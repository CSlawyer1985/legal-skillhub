---
name: vendor-contracts
description: "Pragmatic review of software contracts: IP, liability, SLAs. Use when triaging vendor agreements (not legal advice)."
---

# Vendor Contracts

Structured guidance for **software and vendor agreements** (IP, liability, SLAs—not legal advice): confirm triggers, propose the stages below, and adapt if the user wants a lighter pass.

## When to Offer This Workflow

**Trigger conditions:**
- User mentions **MSA**, **order form**, **vendor agreement**, **contract review**, or closely related work
- They want a structured workflow rather than ad-hoc tips
- They are preparing a review, rollout, or stakeholder communication

**Initial offer:**
Explain the four stages briefly and ask whether to follow this workflow or work freeform. If they decline, continue in their preferred style.

## Workflow Stages

### Stage 1: Clarify context & goals

Anchor on **deal type** (SaaS, support, data processing) and **risk appetite**. Ask what success looks like and what must not break.

### Stage 2: Structure & categories

Cover **commercial**, **legal**, **security**, **data**, and **exit** themes; flag unclear liability caps and indemnities for human counsel.

### Stage 3: Draft & refine

Produce a **red-flag summary** and **question list** for legal/business owners—not definitive legal conclusions.

### Stage 4: Verify & ship

Close the loop with owners, security review, and procurement steps as needed.

## Checklist Before Completion

- Goals and constraints are explicit for **vendor contract** review
- Risks and trade-offs are stated, not hand-waved
- Verification steps match the change’s impact (tests, canary, peer review)
- Operational follow-through is covered (monitoring, docs, owners)

## Tips for Effective Guidance

- Be procedural: stage-by-stage, with clear exit criteria
- Ask for missing context (environment, scale, deadlines) before prescribing
- Prefer checklists and concrete examples over generic platitudes
- If the user declines the workflow, switch to freeform help without lecturing

## Handling Deviations

- If the user wants to skip a stage: confirm and continue with what they need.
- If context is missing: ask targeted questions before strong recommendations.
- Prefer concrete examples, trade-offs, and verification steps over generic advice.

## Quality Bar

- Each recommendation should be **actionable** (what to do next).
- Call out **failure modes** relevant to vendor agreements (security, scale, UX, or ops).
- Keep tone direct and respectful of the user’s time.
