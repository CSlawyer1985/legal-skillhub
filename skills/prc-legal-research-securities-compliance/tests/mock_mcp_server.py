from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TOKEN = "test-secret-token"
TOOLS = [
    {"name": "yuandian_rh_fg_zq_search", "description": "securities regulation search", "inputSchema": {"type": "object"}},
    {"name": "yuandian_rh_zqcfws_search", "description": "securities enforcement search", "inputSchema": {"type": "object"}},
]
PAGED_TOOL = {"name": "yuandian_rh_ssgsgg_search", "description": "listed-company announcement search", "inputSchema": {"type": "object"}}


class Handler(BaseHTTPRequestHandler):
    server_version = "MockMCP/1.2"

    def log_message(self, *_):
        return

    def _mode(self):
        return parse_qs(urlparse(self.path).query).get("mode", ["ready"])[0]

    def _json(self, status, payload, headers=None):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        mode = self._mode()
        if mode == "auth" or self.headers.get("Authorization") != f"Bearer {TOKEN}":
            return self._json(401, {"error": "unauthorized"})
        if mode == "rate":
            return self._json(429, {"error": "rate limited"}, {"Retry-After": "1"})
        if mode == "server_error":
            return self._json(503, {"error": "temporary"})
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        method = body.get("method")
        protocol = self.headers.get("MCP-Protocol-Version")

        if mode == "strict_modern" and protocol == "2026-07-28":
            if self.headers.get("Mcp-Method") != method:
                return self._json(400, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32001, "message": "HeaderMismatch"}})
            meta = (body.get("params") or {}).get("_meta") or {}
            if meta.get("io.modelcontextprotocol/protocolVersion") != "2026-07-28":
                return self._json(400, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32020, "message": "missing protocolVersion meta"}})
            if "io.modelcontextprotocol/clientCapabilities" not in meta:
                return self._json(400, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32021, "message": "missing clientCapabilities meta"}})

        if mode in ("legacy", "legacy_2025_03"):
            if method == "tools/list" and protocol == "2026-07-28":
                return self._json(400, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32022, "message": "UnsupportedProtocolVersion"}})
            if method == "initialize":
                requested = ((body.get("params") or {}).get("protocolVersion"))
                if mode == "legacy_2025_03" and requested != "2025-03-26":
                    return self._json(400, {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32022, "message": "UnsupportedProtocolVersion"}})
                negotiated = "2025-03-26" if mode == "legacy_2025_03" else "2025-11-25"
                return self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "result": {"protocolVersion": negotiated, "capabilities": {"tools": {}}, "serverInfo": {"name": "mock", "version": "1"}}}, {"MCP-Session-Id": "session-123"})
            if method == "notifications/initialized":
                return self._json(202, {})
            if method == "tools/list":
                if self.headers.get("MCP-Session-Id") != "session-123":
                    return self._json(400, {"error": "missing session"})
                return self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": TOOLS}})

        if method == "tools/list":
            if mode == "paged":
                cursor = (body.get("params") or {}).get("cursor")
                if not cursor:
                    return self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": [TOOLS[1]], "nextCursor": "page-2", "ttlMs": 1000, "cacheScope": "private"}})
                if cursor == "page-2":
                    return self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": [PAGED_TOOL], "ttlMs": 1000, "cacheScope": "private"}})
            tools = [] if mode == "missing" else TOOLS
            return self._json(200, {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": tools, "ttlMs": 1000, "cacheScope": "private"}})
        return self._json(404, {"error": "unknown method"})


def start_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    return server, f"http://127.0.0.1:{server.server_port}/mcp"
