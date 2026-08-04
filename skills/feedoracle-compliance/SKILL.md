---
name: feedoracle-compliance
description: "MiCA compliance evidence and stablecoin risk scoring for regulated tokenized markets. 27 MCP tools with ES256K-signed responses. Use when the user explicitly asks about stablecoin compliance, MiCA regulatory status, or needs verifiable evidence for audit workflows."
version: 1.2.2
metadata:
  openclaw:
    requires:
      bins:
        - curl
    emoji: "🛡️"
    homepage: https://feedoracle.io
---

# FeedOracle Compliance Intelligence

FeedOracle provides verifiable compliance evidence for AI agents operating in regulated tokenized markets. Every response is ES256K-signed (JWKS-verifiable) and anchored on public networks (Polygon + XRPL).

**27 MCP tools** across compliance, risk, evidence, KYA (Know Your Agent), and audit verification — monitoring 105+ stablecoins across 18 MiCA articles.

**MCP Server URL:** `https://feedoracle.io/mcp/`
**Auth:** Free tier requires no API key (300 units/day). Optional `FEEDORACLE_API_KEY` for higher limits.
**Privacy Policy:** https://feedoracle.io/privacy
**Trust Policy:** https://github.com/feedoracle/feedoracle-mcp/blob/main/docs/TRUST_POLICY.md

## Authentication

| Tier | API Key? | Limits |
|------|----------|--------|
| **Free** | Not required | 300 units/day, read-only tools |
| **Pro** | Optional `FEEDORACLE_API_KEY` | 15,000 units/mo |
| **Agent** | Optional `FEEDORACLE_API_KEY` | 150,000 units/mo |
| **Enterprise** | Custom | Unlimited |

No environment variables are required. The free tier works without any configuration.

## When to use this skill

Use this skill **only when the user explicitly requests** one of the following:

- Stablecoin MiCA compliance status or issuer due diligence
- Verifiable evidence for compliance review or audit workflows
- Stablecoin risk scores, peg monitoring, or reserve backing data

**This skill does NOT auto-invoke.** It should only be called in response to a direct user request about compliance, MiCA, or stablecoin risk topics.

## Data Handling & Privacy

### What each tool sends to feedoracle.io

**Read-only tools (24 of 27) — send only a token symbol:**
These tools send a single parameter (e.g. `token_symbol: "USDC"`) and receive signed evidence back. No conversation content, no user data, no PII is transmitted.

Includes: `compliance_preflight`, `mica_status`, `mica_full_pack`, `mica_market_overview`, `peg_deviation`, `peg_history`, `significant_issuer`, `interest_check`, `document_compliance`, `reserve_quality`, `rlusd_integrity`, `evidence_profile`, `evidence_leaderboard`, `evidence_bundle`, `custody_risk`, `market_liquidity`, `macro_risk`, `ai_explain`, `ai_provenance`, `kya_status`, `audit_query`, `audit_verify`, `ping`, `generate_report`

**ai_query — sends question text (user-initiated only):**
This tool sends the user's natural language question to feedoracle.io for routing to the correct evidence API. **Only invoke when the user explicitly asks a compliance question.** Do not send conversation history, PII, or unrelated text.

| Sent | NOT sent |
|------|----------|
| The specific question text | Conversation history |
| Optional token symbol | User identity or PII |

**kya_register — sends agent metadata (user-initiated only):**
Registers an agent identity for trust scoring. **Only invoke when the user explicitly requests agent registration.**

| Sent | NOT sent |
|------|----------|
| Agent name, purpose, org name | Conversation content |
| Contact email (user-provided) | User browsing data |

**audit_log — sends decision text (user-initiated only):**
Logs a compliance decision with evidence references. **Only invoke when the user explicitly requests decision logging.**

| Sent | NOT sent |
|------|----------|
| Decision (PASS/WARN/BLOCK) | Full conversation logs |
| Reasoning text (user-provided) | User identity or PII |
| Evidence request IDs | Unrelated context |

### Data retention
- Read-only queries: **Stateless — no data stored**
- KYA profiles: Stored until deletion requested
- Audit trail: Append-only, retained for compliance verification
- Full policy: https://feedoracle.io/privacy
- GDPR: Operated from Germany, Art. 6(1)(b)

## MCP Tools (27)

### Compliance — 11 tools (read-only, sends token symbol only)
| Tool | Description |
|------|-------------|
| `compliance_preflight` | Pre-flight PASS/WARN/BLOCK decision |
| `mica_status` | MiCA authorization status (ESMA/EBA cross-referenced) |
| `mica_full_pack` | Full 12-article MiCA evidence pack |
| `mica_market_overview` | Market-wide MiCA status dashboard |
| `peg_deviation` | Real-time Art. 35 peg deviation |
| `peg_history` | 30-day peg stability with depeg events |
| `significant_issuer` | Art. 45/58 significant issuer check |
| `interest_check` | Art. 23/52 interest prohibition scan |
| `document_compliance` | Art. 29/30/55 recovery/redemption/audit |
| `reserve_quality` | Art. 24/25/53 reserve composition |
| `rlusd_integrity` | RLUSD reserve attestation |

### Risk & Evidence — 6 tools (read-only, sends token symbol or protocol name only)
| Tool | Description |
|------|-------------|
| `evidence_profile` | Multi-dimensional evidence grade A-F |
| `evidence_leaderboard` | Top protocols by evidence grade |
| `evidence_bundle` | Multi-framework evidence aggregation |
| `custody_risk` | Custodian SIFI status, concentration risk |
| `market_liquidity` | DEX liquidity depth, exit channels |
| `macro_risk` | US macro risk composite (86 FRED series) |

### AI Gateway — 3 tools
| Tool | Description | Data sent |
|------|-------------|-----------|
| `ai_query` | Natural language evidence query | Question text (user-initiated only) |
| `ai_explain` | Grade explanation with counterfactual | Token symbol only |
| `ai_provenance` | Cryptographic provenance chain | Token symbol only |

### KYA (Know Your Agent) — 2 tools
| Tool | Description | Data sent |
|------|-------------|-----------|
| `kya_register` | Register agent identity (user-initiated only) | Agent metadata (name, purpose, org, email) |
| `kya_status` | Check trust level (read-only) | Client ID only |

### Audit Trail — 3 tools
| Tool | Description | Data sent |
|------|-------------|-----------|
| `audit_log` | Log decision (user-initiated only) | Decision, reasoning, evidence IDs |
| `audit_query` | Query history (read-only) | Client ID only |
| `audit_verify` | Verify chain integrity (read-only) | Client ID only |

### System — 2 tools
| Tool | Description | Data sent |
|------|-------------|-----------|
| `ping` | Connectivity test | Nothing |
| `generate_report` | Signed PDF report (requires API key) | Report type only |

## Behavior Instructions

1. **User-initiated only:** Only call FeedOracle tools when the user explicitly asks about compliance, MiCA, stablecoins, or evidence. Never auto-invoke.
2. **Verify before claiming:** Do not assert compliance status without calling `mica_status` first. Present data and let the user decide.
3. **Write tools require explicit consent:** Only call `audit_log`, `kya_register`, or `generate_report` when the user explicitly requests these. Never auto-invoke write tools.
4. **Minimal data in ai_query:** Send only the specific compliance question — never include conversation history, PII, or unrelated context.
5. **Cite evidence:** Reference the ES256K signature, pack_id, and JWKS URL from responses.
6. **Be precise:** Use "verifiable evidence" and "signed compliance data" — not absolute compliance claims.

## Controlling Invocation Scope

This skill is designed to be invoked only on explicit user request. If your agent framework supports trigger configuration:

- **Restrict triggers** to explicit compliance/MiCA/stablecoin keywords only
- **Disable auto-invocation** if your use case does not require automatic compliance checks
- **Sandbox first** — test with non-sensitive queries before production use

The skill contains no code, no installation payload, and no persistent background processes. All external communication is to `feedoracle.io` over HTTPS only.

## Connection

```bash
# Claude Code
claude mcp add --transport http feedoracle https://feedoracle.io/mcp/

# Claude Desktop (claude_desktop_config.json)
{
  "mcpServers": {
    "feedoracle": {
      "url": "https://feedoracle.io/mcp/"
    }
  }
}
```

## Error Handling

- 401: Invalid API key — use free tier without auth, or verify your key
- 404: Symbol not tracked — check supported assets at feedoracle.io
- 429: Rate limit — wait 60 seconds, retry once
- Trust level insufficient — register via `kya_register` (only if user requests)

API keys: [feedoracle.io/pricing](https://feedoracle.io/pricing) | Docs: [github.com/feedoracle/feedoracle-mcp](https://github.com/feedoracle/feedoracle-mcp)
