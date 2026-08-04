---
name: enterprise-legal-guardrails
description: Legal/compliance guardrails for outbound OpenClaw actions (anti-spam, defamation, privacy, financial claims).
---

# Enterprise Legal Guardrails

Use this skill to preflight bot output before posting, messaging, or publishing anything that could create legal/compliance risk.

## What it is
A generic **outbound** guardrail checker used by workflows before execute actions such as post/comment/message/chat/send in any app.

## When to use
- Before `create_post`, `create_comment`, `send_message`, or equivalent publish actions.
- Before market-related commentary, strategy claims, or price/certainty statements.
- Before HR-sensitive or workplace-adjacent messaging.
- Before anti-spam or coordination-heavy communications.
- Before handling or exposing personal identifiers.

## Workflow

1. Draft text.
2. Run the checker with the matching action/profile.
3. If result is **PASS/WATCH**, proceed.
4. If **REVIEW**, rewrite or route for human/legal review.
5. If **BLOCK**, do not execute.

Use it as a shared OpenClaw outbound safety layer for any skill that publishes content.
Babylon is only one current integration example, not the primary purpose of the skill.

## Quick usage

```bash
python3 scripts/check_enterprise_guardrails.py \
  --action post \
  --app <app_name> \
  --policies social antispam hr \
  --text "Draft text here"
```

```bash
python3 scripts/check_enterprise_guardrails.py \
  --action comment \
  --scope include \
  --apps whatsapp,telegram \
  --text "Draft text here"
```

```bash
python3 scripts/check_enterprise_guardrails.py \
  --action market-analysis \
  --text "Market commentary..." \
  --json
```

## App scope (global filtering)

Scope applies to any app-context passed with `--app` and these env vars (legacy names preserved for compatibility):

- `ENTERPRISE_LEGAL_GUARDRAILS_OUTBOUND_SCOPE` (`all|include|exclude`)
- `ENTERPRISE_LEGAL_GUARDRAILS_OUTBOUND_APPS` (comma-separated list)
- `BABYLON_GUARDRAILS_SCOPE`
- `BABYLON_GUARDRAILS_OUTBOUND_SCOPE`
- `BABYLON_GUARDRAILS_APPS`

Examples:

- `all`: check all outbound content.
- `include` + `whatsapp,email`: only check those apps.
- `exclude` + `whatsapp,email,moltbook,babylon`: everything except these apps.

If scope is omitted, default is `all`.

## Profiles

- `social`: public social text, comments, announcements.
- `antispam`: unsolicited/pumping/coordinating messaging.
- `hr`: workplace, hiring, performance, or employee conduct language.
- `privacy`: personally identifying data and private information disclosures.
- `market`: market/financial claims and outcome assertions.
- `legal`: legal conclusions/implication language.

If no profile is provided, defaults are derived from `--action`:
- `post|comment|message` → `social,legal`
- `trade|market-analysis` → `market,financial`
- `generic` → `legal,social`

## Output

- `PASS`: safe to execute
- `WATCH`: low risk; optional rewrite
- `REVIEW`: human/legal review recommended
- `BLOCK`: do not execute

## Tuning

You can tune decision sensitivity via environment variables (or CLI flags in direct runs):

- `ENTERPRISE_LEGAL_GUARDRAILS_REVIEW_THRESHOLD` (`default: 5`)
- `ENTERPRISE_LEGAL_GUARDRAILS_BLOCK_THRESHOLD` (`default: 9`)

CLI overrides:
- `--review-threshold`
- `--block-threshold`

Legacy aliases are supported in legacy env names: `ELG_*` and `BABYLON_GUARDRAILS_*`.

## Universal outbound adapter (no-native integration path)

For skills/tools without native guardrail hooks (for example: Gmail, custom website
publishing, custom message bots), run outbound operations through the wrapper:

```bash
python3 /path/to/enterprise-legal-guardrails/scripts/guard_and_run.py   --app <app_name>   --action <post|comment|message|trade|market-analysis|generic>   --text "$DRAFT"   -- <outbound command...>
```

Examples:

```bash
# Gmail via gog
python3 /path/to/enterprise-legal-guardrails/scripts/guard_and_run.py   --app gmail --action message   --text "Hello, ..."   -- gog gmail send --to user@domain.com --subject "Update" --body "Hello, ..."

# Website/publication publish flow
python3 /path/to/enterprise-legal-guardrails/scripts/guard_and_run.py   --app website --action post   --text "$POST_COPY"   -- npm run publish-post "$POST_COPY"
```

Use this wrapper to apply the same policy checks in non-Babylon outbound flows.

## Compatibility

Legacy name `legal-risk-checker` is preserved in OpenClaw workspaces that still reference it.

## References

See `references/guardrail-policy-map.md` for the full policy rule set and suggested rewrites.

## Packaging

A distributable bundle is available at:
- `dist/enterprise-legal-guardrails.skill`
### Hardening controls for `guard_and_run.py`

For non-native outbound integrations, treat `guard_and_run` as an execution
boundary. Recommended flags/env:

Execution safety is allowlist-first by default. Wrapper requires explicit
`--allowed-command` (or env alias) unless `--allow-any-command` is explicitly enabled.

- `--allow-any-command` / `ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND`
  - Explicitly bypass allowlist enforcement (unsafe; audit-first use only).
- `--suppress-allow-any-warning` / `ENTERPRISE_LEGAL_GUARDRAILS_SUPPRESS_ALLOW_ANY_WARNING`
  - Suppresses the runtime safety warning when `--allow-any-command` is intentionally enabled.
- `--allow-any-command-reason` / `ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND_REASON`
  - Mandatory rationale for any `allow-any` bypass invocation. Suggested format: `SEC-1234: emergency fix`.
- `--allow-any-command-approval-token` / `ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND_APPROVAL_TOKEN`
  - Mandatory approval token for any `allow-any` bypass invocation; stored as a short token fingerprint in audit logs.
- `--allowed-command <exe...>` / `ENTERPRISE_LEGAL_GUARDRAILS_ALLOWED_COMMANDS`
  - Allow-list executables (supports comma/space lists and wildcards).
- `--strict` / `ENTERPRISE_LEGAL_GUARDRAILS_STRICT`
  - Escalate `REVIEW` to hard block.
- `--sanitize-env`
- `--keep-env <VAR...>` / `--keep-env-prefix <PREFIX...>`
- `--command-timeout`, `--checker-timeout`, `--max-text-bytes`
- `--audit-log <file>` / `ENTERPRISE_LEGAL_GUARDRAILS_AUDIT_LOG`

These flags provide execution safety, command scoping, and immutable trail for
post-incident review without changing checker logic.
