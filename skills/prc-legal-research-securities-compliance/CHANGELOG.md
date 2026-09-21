# Changelog

## 1.2.0 — 2026-08-26

- Added the public `yuandian-securities` endpoint and five-tool baseline.
- Moved version and compatibility into standards-compliant metadata.
- Removed obsolete generic law-detail tool assumptions from securities routing.
- Added Yuanli platform connection states, runtime schema discovery and secret-store rules.
- Updated the probe, mock server and offline tests for the securities server.

## 1.1.0 — 2026-08-18

MCP-connectivity-first release.

### Added

- Closed-loop MCP state machine: `READY`, `NOT_CONFIGURED`, `AUTH_FAILED`, `NETWORK_FAILED`, `CAPABILITY_MISSING`, `RATE_LIMITED`, `UNKNOWN_FAILURE`.
- Automatic preservation and resumption of the user's original securities query after successful configuration/re-probe.
- Registration/API-key onboarding for users with no Yuandian MCP configured.
- Credential-safety rule: never ask users to paste API keys into chat.
- Current public Yuandian MCP endpoints for law, case and company servers.
- Host-aware configuration runbook for Claude Code, Codex, Cursor, ChatGPT and generic MCP hosts.
- Dependency-free Streamable HTTP MCP probe supporting the current stateless protocol with a legacy initialize/session fallback.
- Full MCP 2026-07-28 per-request metadata envelope and paginated `tools/list` discovery in the probe.
- Host-native MCP management preference when the runtime can safely register/refresh servers without receiving secrets through chat.
- Offline mock MCP protocol tests for success, missing capability, auth failure, rate limit, server failure and legacy compatibility.
- Explicit public-vs-private capability contract; no false equivalence between generic administrative punishment/court-case tools and a dedicated securities regulatory-enforcement database.

### Changed

- “MCP missing → stop” is now “MCP missing → onboard → re-probe → resume”.
- `compatibility` now describes onboarding rather than assuming the connector is already authenticated.
- Production readiness is defined by actual host discovery + authentication + required tool presence + a read-only call, not by config-file presence.

## 1.0.0 — 2026-08-18

Production-hardening release based on the uploaded legacy `SKILL.md`.

### Fixed

- Rebuilt malformed YAML frontmatter to valid Agent Skills metadata.
- Moved non-standard `argument-hint` into `metadata`.
- Rewrote discovery description around explicit trigger conditions.
- Added `compatibility` dependency declaration.
- Removed the contradictory model-memory fallback when MCP is unavailable.
- Reduced provenance to exactly three source levels.
- Added fail-closed live MCP capability/schema verification.
- Made runtime schema authoritative over hard-coded parameter notes.
- Added current-law versus historical-law/version handling.
- Added search-to-detail verification and semantic-search boundaries.
- Added evidence-conflict resolution rules.
- Removed the simplistic cross-norm linear hierarchy rule.
- Added enforcement evidence-chain requirements.
- Added explicit issuer-announcement versus regulator-finding separation.
- Added timeout/auth/rate-limit/empty-result/schema-drift handling.
- Added non-exhaustive-result safeguards.
- Added legal-opinion boundary and handoff rules.
- Added acceptance scenarios, structural validator and deployment notes.
