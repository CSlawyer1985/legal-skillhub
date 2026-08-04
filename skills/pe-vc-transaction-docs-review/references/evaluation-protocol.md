# Blind Evaluation Protocol

Use this protocol when testing whether the skill generalizes beyond unit tests.
Automated checks prove artifact structure and bounded issue recall only; they do
not prove legal correctness.

## Isolation Rules

1. Prepare a bundle with `scripts/prepare_blind_evaluation.py`. Give the
   executing reviewer only `USER_REQUEST.md`, `input/`, the installed skill and
   an empty `submission/` directory.
2. Do not provide `tests/evaluation/scenarios.json`, expected issue families,
   intended fixes, prior audit conclusions or another reviewer's output.
3. Use a fresh task or reviewer for each run. Keep output from earlier runs out
   of the next bundle.
4. Use only synthetic files in the committed evaluation set. Real matters may
   be tested privately, but their names, text and raw output must remain outside
   Git and must be anonymized in any durable report.
5. Record the input hashes from `run-manifest.json`. A run with changed inputs is
   a different evaluation and must not be compared as if identical.

## Twelve Scenario Families

The private evaluation manifest covers: RMB first draft, native Track Changes,
clean-version renumbering/movement, scanned-PDF readiness, offshore direct
holding, VIE, down round, founder secondary sale, connector degradation,
comments-only integrity, matter isolation and cross-document inconsistency.

## Scoring Layers

Run `scripts/score_blind_evaluation.py` after the submission is complete.

- Artifact score: required output files exist and are non-empty.
- Issue recall: at least one output contains a scenario's required issue-family
  signal. This is a coarse recall proxy, not semantic legal grading.
- Authority recall: required official-authority signals appear where relevant.
- Validator score: issue logs, Major Issue Lists, comment plans and native Word
  comment structures pass their deterministic gates.
- False-positive control: prohibited definitive claims or cross-matter terms do
  not appear.

The automatic score weights those components 20/40/15/15/10. Keep
`legal_quality_status=not_assessed` until an independent transaction lawyer
completes all six 0-5 dimensions in
`assets/blind-evaluation-human-scorecard.json`: legal correctness, issue recall,
false-positive control, drafting quality, client-side consistency and source
discipline. The scorecard must identify the matching scenario, reviewer,
transaction-lawyer role and ISO review time. Any critical legal or
confidentiality failure overrides the numeric score; a human score cannot
override a failed automatic artifact/prohibited-claim gate.

## Acceptance Gate

A scenario is fully passed only when:

1. Required artifacts and deterministic validators pass.
2. Automatic score is at least the approved threshold and no prohibited claim
   is present.
3. A lawyer scorecard is complete, no critical failure is marked and the
   combined score meets the threshold.
4. The evaluator records limitations and does not treat keyword recall as proof
   that the proposed drafting or legal conclusion is correct.
