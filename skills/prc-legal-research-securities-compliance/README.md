# prc-legal-research-securities-compliance

Production-oriented Agent Skill for PRC mainland securities-compliance research with a **MCP-first onboarding loop** for Yuandian.

## Primary product behavior

The skill no longer treats “MCP not configured” as a dead end.

```text
user securities query
        ↓
preserve original query
        ↓
MCP discovery + read-only probe
        ↓
READY ───────────────→ run research
  │
  └ not ready
        ↓
classify state
        ↓
NOT_CONFIGURED / AUTH_FAILED / NETWORK_FAILED /
CAPABILITY_MISSING / RATE_LIMITED / UNKNOWN_FAILURE
        ↓
registration/configuration/repair guidance
        ↓
re-probe
        ↓
READY → automatically resume original query
```

## Package

```text
prc-legal-research-securities-compliance/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── MCP_LIVE_SIGNOFF.md
├── requirements-dev.txt
├── references/
│   ├── mcp-onboarding.md
│   ├── tool-contract.md
│   └── deployment-notes.md
├── scripts/
│   ├── validate_skill.py
│   └── yuandian_mcp_probe.py
└── tests/
    ├── acceptance-cases.md
    ├── mock_mcp_server.py
    ├── test_probe_client.py
    ├── test_probe_cli.py
    └── mock_mcp_server.py
```

## Local verification

Runtime use of the Skill does not require Python packages. The optional structural test suite uses PyYAML:

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_skill.py
python tests/test_probe_client.py
python tests/test_probe_cli.py
```

These tests are offline and do not require a real Yuandian key.

## Live MCP verification

A target user with a Yuandian API key can run:

```bash
export YUANDIAN_API_KEY='YOUR_API_KEY'
python scripts/yuandian_mcp_probe.py --server securities --require-tool yuandian_rh_fg_zq_search
```

A `READY` result proves the diagnostic process authenticated, enumerated the complete paginated tool catalog, and found the required capability. The probe sends the MCP 2026-07-28 per-request metadata envelope and falls back to initialize/session flow for older Streamable HTTP servers. Production sign-off still requires that the **actual agent host** sees the MCP and completes one low-cost read-only tool call; follow `MCP_LIVE_SIGNOFF.md`.

## Security model

- never request a real API key in chat;
- never commit a literal key;
- prefer host credential storage or environment-backed bearer tokens;
- never send the key in a URL query string;
- never downgrade to model memory when sourced legal retrieval is unavailable.

## Important boundary

元典开放平台现已公开 `yuandian-securities`，提供证券法规、法条、监管文书和上市公司公告等五项专用能力。企业行政处罚仍不得冒充证券监管处罚；缺少专用工具时返回 `CAPABILITY_MISSING`。
