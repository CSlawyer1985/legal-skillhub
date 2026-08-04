# Review Quality Gates

Use these gates as the completion contract for every substantive review. A gate
may be marked `passed`, `passed with limitations`, or `blocked`. Do not silently
continue through a blocked gate.

Before delivery, aggregate the evidence through
`scripts/validate_review_completion.py` using
`assets/review-completion-gate-template.json`. A machine check cannot establish
substantive legal quality, so the configured judgment gates must identify the
reviewing agent or designated reviewer and the evidence checked. They do not
require the user to complete a separate form. Only an aggregate `passed` result permits an
unqualified completion statement. `passed_with_limitations` requires prominent
limitation disclosure; `blocked` prohibits any completion statement.

## Gate 0: Matter and Authority

Pass only when the user instructions and file package establish, or the user
authorizes assumptions for:

- Current matter and client side.
- Review round and scope.
- Output mode and language.
- Structure and governing law, or permission to infer them.
- Confidentiality and cross-matter boundary.
- For later rounds, the available version-chain baseline and the limitations
  caused by anything missing.

Verifier: completed matter profile plus an explicit list of assumptions and gaps.

## Gate 1: File Readiness

For every in-scope file, record:

- File type and extraction method.
- Whether text was extracted.
- Page/paragraph or OOXML location quality.
- Whether OCR, manual review, or conversion is required.
- Whether Track Changes markers and text-bearing changes are present.

Block substantive review of a file when extraction is empty or failed. Do not
count successful extraction of other files as proof that the blocked file was
reviewed.

Verifier: `scripts/build_document_map.py` plus extraction results; use
`scripts/smoke_test_transactions.py --strict` for regression verification.

## Gate 2: Package and Version Chain

Confirm:

- Document families, versions, dates, and apparent clean/redline status.
- Primary operative agreement and controlling language.
- Missing common documents and whether review can proceed without them.
- Current markup, prior draft, prior issue log, prior Major Issue List, and
  counterparty response for later-round acceptance/rejection conclusions.
- When both versions are clean, clause-level alignment/change output, confidence
  or ambiguity flags, and any manual-alignment limitations.
- Candidate cross-document conflicts in definitions, amounts, cap-table facts,
  rights families and dispute mechanisms, including unreadable or omitted files.

Treat filename-based structure/language/version output as intake hints only.
Confirm against operative text before relying on it.

Verifier: document map and version-chain table; use
`scripts/compare_contract_versions.py` for clean prior/current files and
`scripts/build_package_matrix.py --strict` for multi-document packages.

## Gate 3: Research Provenance

For every material issue, separate and label:

- Agreement fact or user-provided fact.
- External entity/background fact and query time.
- Market benchmark and benchmark period.
- Legal authority, status, pinpoint, and verification date.
- Pending fact, pending legal research, or local-counsel question.

Verifier: issue-log fields `Market Context`, `Legal Basis`, and
`Authority / Verification Status`; run `scripts/validate_issue_log.py`, independently verify historical
benchmarks before updates or high-stakes reliance, and run
`scripts/refresh_legal_authorities.py` when the registry freshness or coverage
gate is triggered.

## Gate 4: Substantive Coverage

Review every relevant checklist family, including definitions, economics,
closing, warranties/disclosure/indemnity, investor rights, founder restrictions,
governance, transfer/exit, regulatory and compliance covenants, dispute
resolution, boilerplate, schedules, and cross-document consistency.

Record `reviewed`, `not applicable`, `missing document`, or `deferred` for each
family. Absence of an issue is not proof that a family was reviewed.

Verifier: clause coverage matrix and cross-document conflict matrix.

## Gate 5: Recommendation Quality

Each recommendation must contain:

- Precise location and current text or concise excerpt.
- Issue and client-specific position.
- Market context or a reason it is not applicable.
- Legal basis and authority status when legally material.
- Risk level.
- Complete paste-ready wording, or a document/fact request when wording cannot
  responsibly be completed.
- Fallback and any client decision required.

Verifier: issue-log validation plus human spot-check of every high-risk item.

## Gate 6: Negotiation State

For later rounds:

- Preserve the same Issue ID for the same dispute.
- Use exactly one supported status per row.
- Distinguish accepted, partially accepted, rejected, new, reopened, deferred,
  and closed issues from mere text changes.
- Add new counterparty issues without renumbering existing issues.

Verifier: `scripts/update_major_issue_list.py`, followed by
`scripts/validate_major_issue_list.py`.

## Gate 7: Delivery and Confidentiality

Before delivery:

- Match the primary document language.
- Confirm requested output mode and that comments-only review did not modify the
  source document.
- For native comments, confirm unique anchors, separate output, unchanged visible
  text, valid OOXML comment wiring, inserted-count parity, clean render, and a
  tested rollback report.
- Keep the Major Issue List to exactly five semantic columns.
- Remove accidental absolute paths, unrelated matter names, temporary files,
  and internal benchmark source names from user-facing outputs.
- State unreviewed files and material limitations prominently.

Verifier: final file list, validators, source/output hashes and native-comment
apply report where comments-only integrity matters, render inspection, rollback
test, and a targeted confidentiality scan.
