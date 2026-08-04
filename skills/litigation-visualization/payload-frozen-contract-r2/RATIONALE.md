# Rationale

Candidate: `gaotao-litigation-visualization-extension/20260723-contract-r2-codex`

Root authorized candidate-only work in four-party message `1784799652144-user`. The accepted real-case E2E proved that a frozen `L2-05` litigation plan can feed a deterministic, traceable local visualization run, while preserving correct HOLD behavior and rejecting validator drift. It did not authorize a formal Skill write or prove cross-case promotion readiness.

This candidate applies the smallest architecture delta agreed by Codex and Claude Code:

- the mother Skill publishes a stable, versioned extension contract;
- a distilled case-type Skill freezes the nine `L2-05` semantic anchors and emits anchor-map plus handoff;
- the independent `litigation-visualization-cn` Skill consumes that handoff;
- the renderer and its dependencies stay outside the mother Skill;
- capability defaults to `hold`, and a run may render only after all fail-closed gates pass.

The route remains reversible because the formal root is unchanged, `promotion_mode=none`, the patch is isolated, and rollback at this stage is deletion or rejection of this candidate. Promotion still requires inheritance tests, at least one different case-type E2E, installation dry-run, rollback evidence, an observation window, independent review, and a new root decision.
