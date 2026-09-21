from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from mock_mcp_server import TOKEN, start_server

server, base = start_server()
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    env = os.environ.copy()
    env["YUANDIAN_API_KEY"] = TOKEN
    cp = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "yuandian_mcp_probe.py"), "--url", base, "--require-tool", "yuandian_rh_fg_zq_search", "--json"],
        env=env, text=True, capture_output=True, timeout=10,
    )
    assert cp.returncode == 0, (cp.returncode, cp.stdout, cp.stderr)
    assert '"state": "READY"' in cp.stdout
    assert TOKEN not in cp.stdout + cp.stderr

    env.pop("YUANDIAN_API_KEY", None)
    cp = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "yuandian_mcp_probe.py"), "--url", base, "--json"],
        env=env, text=True, capture_output=True, timeout=10,
    )
    assert cp.returncode == 2, (cp.returncode, cp.stdout, cp.stderr)
    assert '"state": "NOT_CONFIGURED"' in cp.stdout
finally:
    server.shutdown(); server.server_close()
print("PASS: MCP probe CLI and secret non-disclosure")
