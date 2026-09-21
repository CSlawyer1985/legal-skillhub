from __future__ import annotations

import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from yuandian_mcp_probe import probe, LATEST_PROTOCOL
from mock_mcp_server import TOKEN, start_server

server, base = start_server()
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    r = probe(base + "?mode=ready", TOKEN, ["yuandian_rh_fg_zq_search"], 2)
    assert r.state == "READY", r
    assert r.protocol == LATEST_PROTOCOL
    assert "yuandian_rh_fg_zq_search" in r.tools

    r = probe(base + "?mode=strict_modern", TOKEN, ["yuandian_rh_fg_zq_search"], 2)
    assert r.state == "READY", r
    assert r.protocol == LATEST_PROTOCOL

    r = probe(base + "?mode=paged", TOKEN, ["yuandian_rh_ssgsgg_search"], 2)
    assert r.state == "READY", r
    assert "yuandian_rh_ssgsgg_search" in r.tools

    r = probe(base + "?mode=missing", TOKEN, ["yuandian_rh_fg_zq_search"], 2)
    assert r.state == "CAPABILITY_MISSING", r

    r = probe(base + "?mode=auth", TOKEN, [], 2)
    assert r.state == "AUTH_FAILED", r

    r = probe(base + "?mode=rate", TOKEN, [], 2)
    assert r.state == "RATE_LIMITED", r

    r = probe(base + "?mode=server_error", TOKEN, [], 2)
    assert r.state == "NETWORK_FAILED", r

    r = probe(base + "?mode=legacy", TOKEN, ["yuandian_rh_fg_zq_search"], 2)
    assert r.state == "READY", r
    assert r.protocol == "2025-11-25", r

    r = probe(base + "?mode=legacy_2025_03", TOKEN, ["yuandian_rh_fg_zq_search"], 2)
    assert r.state == "READY", r
    assert r.protocol == "2025-03-26", r

    r = probe(base, None, [], 2)
    assert r.state == "NOT_CONFIGURED", r
finally:
    server.shutdown()
    server.server_close()
print("PASS: MCP probe client states and legacy fallback")
