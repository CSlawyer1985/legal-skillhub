# Evidence

Candidate: `gaotao-litigation-visualization-extension/20260723-contract-r2-codex`

## Authorization and boundary

- Root candidate-only authorization: four-party message `1784799652144-user`.
- Claude Code scope acknowledgement and strict-audit assignment: `1784799768569-claude-code`.
- Formal source: `${HOME}/.codex/skills/lawyer-legal-knowledge-distillation-geo`.
- Frozen source tree hash: `sha256:c6078ce8839c60e5e6d0518515fd95af1d09bb3dea060f3b8b82d57da4ce57b8`.
- Candidate type: `script-enhance` (contract, validator, and regression fixtures).
- Formal root, frozen architecture packages, and accepted E2E artifacts remained read-only.

## Architecture and contract evidence

- Frozen architecture package: `artifacts/gaotao-litigation-visualization-sublation-20260723-codex-r2`.
- Architecture decision SHA-256: `38ecfc36047988779babf39eb06761dc1c08ccc906e3bef1521882cb9a43a035`.
- Handoff schema SHA-256: `5b506950d04d9b0fe0c15ff07d890acd55c69e69d92d4f92b5b5c9abd4591241`.
- L2 anchor contract SHA-256: `aa0bb5640c0ba60f87face0c22ef45272ef179c26c546daa1738f9e6bd910b14`.
- Handoff validator SHA-256: `e0ea6139414e08391383b1597cda23c95fa4674915a32af4538f0fb0c2fb55f7`.
- Drift fixture SHA-256: `d2c279a46c9e7744c3cb5c8485b466c8c77f3b3e15eee151a272512925cc25c9`.

## Real-case E2E evidence

- Frozen semantic spec: `artifacts/gaotao-litigation-visualization-e2e-run-20260723-r2-candidate/semantic/litigation-visualization-spec-r2.json`.
- Frozen semantic spec SHA-256: `0ed84d216ace61b6f62f3851cf3e91a9c57d0ec89a925cf0f88fce207660cd2a`.
- Accepted render bundle: `artifacts/gaotao-litigation-visualization-e2e-render-20260723-r2-candidate`.
- Render manifest SHA-256: `48d0a924d2dd87ff57aa32fe270e8bcea3babb147f92d3df1d7e72b87af839b9`.
- Independent artifact review SHA256SUMS: `2d7dbeb35de056cf5d785c1253d9ce65ba385045118808a5b5e044afa3890e11`.

The E2E result is `E2E-ACCEPTED-LOCAL-INTERNAL`. It does not authorize installation, promotion, external delivery, publication, filing, or court use.

## Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_litigation_visualization_extension.py
python3 ../../skill-sublation/20260710-one-shot-orchestrator-codex/scripts/audit.py --strict .
```

Claude Code independent strict audit remains pending when this evidence note is first written.
