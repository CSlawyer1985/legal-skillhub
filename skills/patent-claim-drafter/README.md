# Patent Claim Drafter

**Platforms:** Claude · Openclaw · Codex
**Domain:** Intellectual Property

## Purpose

A drafting partner for patent practitioners. Turns an invention disclosure into a structured DRAFT patent claim set — one independent claim plus a dependent claim ladder per requested category (apparatus, method, computer-readable medium, composition, kit) — with the formal checks a practitioner runs before filing.

## When to Use

- Turning an invention disclosure into a first-draft claim set for US (USPTO), EPO, JPO, CNIPA, or PCT filing
- Drafting parallel apparatus / method / CRM claim sets from a single disclosure
- Producing a dependency tree and antecedent-basis table for a claim set someone else drafted
- Flagging means-plus-function / §112(f) issues before filing
- Identifying candidate distinguishing limitations against named prior-art references

## What It Does

**Phase 1: Intake**
1. Captures practitioner role, target jurisdiction, application type, and categories to draft
2. Captures the invention: title, field, problem, solution, core feature set, preferred and alternative embodiments, and named prior-art references
3. Restates every fact with Confirmed / Assumed / Unknown tags and waits for user confirmation before drafting

**Phase 2: Drafting**
4. Drafts the independent claim(s) using a preamble + transition + body structure, one sentence per claim, with strict antecedent basis
5. Drafts a dependent ladder of 5–15 dependents per independent that progressively narrows on sub-features, materials/ranges, functional limitations, method-step subsets, and intended-use
6. Maintains category parallelism across apparatus, method, and CRM claim sets when multiple categories are requested

**Phase 3: Structural checks**
7. Runs antecedent-basis, single-sentence, dependency, no-new-matter, indefinite-term, functional-language, method/apparatus-mixing, and use-claim checks
8. Logs every issue in a Findings Table with Block / Fix / Note severity
9. Identifies candidate distinguishing limitations against named prior art — does not render a patentability opinion

## Output

A DRAFT claim set with:

- Numbered claims (independent + dependent ladder per category)
- Antecedent-basis table
- Dependency tree
- Category-parallelism table (when applicable)
- §112(f) / means-plus-function flag table
- Prior-art differentiation notes (drafting candidates only)
- Findings table with severity-rated issues
- Open-questions list
- Practitioner notes on transition word, multiple-dependent use, and category coverage

## Safety

This skill drafts **only**. It does not give legal advice and does not assess patentability, infringement, validity, or freedom-to-operate. Every delivered output is labeled **DRAFT — PRACTITIONER MUST REVIEW BEFORE FILING**. The invention disclosure is treated as confidential and is never written to external services.

## Feedback & Contributions

Found a gap or have a suggestion? [Open an issue or PR](https://github.com/archlab-space/Open-Skill-Hub/issues) — improvements are welcome.
