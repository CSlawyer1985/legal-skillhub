#!/usr/bin/env python3
"""Dependency-free diagnostic for Yuandian Streamable HTTP MCP endpoints.

Reads the bearer token only from an environment variable. It never prints the token.
It first tries MCP 2026-07-28 stateless tools/list, then falls back to a
2025-era initialize/session flow for older Streamable HTTP servers.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Iterable

OFFICIAL_SERVERS = {
    "law": "https://open.chineselaw.com/mcp/law/stream",
    "case": "https://open.chineselaw.com/mcp/case/stream",
    "company": "https://open.chineselaw.com/mcp/company/stream",
    "securities": "https://open.chineselaw.com/mcp/securities/stream",
}
LATEST_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26")


@dataclass
class ProbeResult:
    state: str
    url: str
    protocol: str | None = None
    tools: list[str] | None = None
    missing_tools: list[str] | None = None
    detail: str | None = None


def _parse_body(raw: bytes, content_type: str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    if "text/event-stream" in (content_type or "").lower():
        # A POST response can carry one or more SSE events. Take the first JSON data event.
        data_lines: list[str] = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif not line.strip() and data_lines:
                candidate = "\n".join(data_lines)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    data_lines = []
        if data_lines:
            return json.loads("\n".join(data_lines))
        raise ValueError("SSE response contained no JSON data event")
    return json.loads(text)


def _post(url: str, token: str, payload: dict[str, Any], timeout: float,
          protocol: str | None = None, session_id: str | None = None,
          method_header: str | None = None, name_header: str | None = None) -> tuple[int, dict[str, str], dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": "yuandian-skill-mcp-probe/1.2.0",
    }
    if protocol:
        headers["MCP-Protocol-Version"] = protocol
    if session_id:
        headers["MCP-Session-Id"] = session_id
    if method_header:
        headers["Mcp-Method"] = method_header
    if name_header:
        headers["Mcp-Name"] = name_header
    req = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            h = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, h, _parse_body(raw, h.get("content-type", ""))
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        h = {k.lower(): v for k, v in exc.headers.items()}
        body: dict[str, Any]
        try:
            body = _parse_body(raw, h.get("content-type", ""))
        except Exception:
            body = {"raw": raw.decode("utf-8", errors="replace")[:500]}
        return exc.code, h, body


def _notification(url: str, token: str, payload: dict[str, Any], timeout: float,
                  protocol: str, session_id: str | None) -> int:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": protocol,
        "Mcp-Method": payload.get("method", "notifications/initialized"),
        "User-Agent": "yuandian-skill-mcp-probe/1.2.0",
    }
    if session_id:
        headers["MCP-Session-Id"] = session_id
    req = urllib.request.Request(url, method="POST", data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            return resp.status
    except urllib.error.HTTPError as exc:
        exc.read()
        return exc.code


def _extract_tool_page(body: dict[str, Any]) -> tuple[list[str] | None, str | None]:
    result = body.get("result")
    if not isinstance(result, dict):
        return None, None
    tools = result.get("tools")
    if not isinstance(tools, list):
        return None, None
    names: list[str] = []
    for tool in tools:
        if isinstance(tool, dict) and isinstance(tool.get("name"), str):
            names.append(tool["name"])
    cursor = result.get("nextCursor")
    if cursor is not None and not isinstance(cursor, str):
        return None, None
    return names, cursor


def _modern_meta() -> dict[str, Any]:
    # MCP 2026-07-28 carries protocol identity and capabilities per request.
    return {
        "io.modelcontextprotocol/protocolVersion": LATEST_PROTOCOL,
        "io.modelcontextprotocol/clientInfo": {"name": "yuandian-skill-probe", "version": "1.2.0"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def _append_unique(target: list[str], values: Iterable[str]) -> None:
    seen = set(target)
    for value in values:
        if value not in seen:
            target.append(value)
            seen.add(value)


def _jsonrpc_error(body: dict[str, Any]) -> str:
    err = body.get("error")
    if isinstance(err, dict):
        return f"{err.get('code', '')} {err.get('message', '')}".strip()
    return ""


def _classify_http(status: int) -> str | None:
    if status in (401, 403):
        return "AUTH_FAILED"
    if status == 429:
        return "RATE_LIMITED"
    if status >= 500:
        return "NETWORK_FAILED"
    return None


def _finish(url: str, protocol: str, tools: list[str], required: Iterable[str]) -> ProbeResult:
    required = list(required)
    missing = [name for name in required if name not in tools]
    if missing:
        return ProbeResult("CAPABILITY_MISSING", url, protocol, tools, missing, "MCP reachable but required tool(s) absent")
    return ProbeResult("READY", url, protocol, tools, [], "MCP authentication, tool discovery and required capability check succeeded")


def probe(url: str, token: str | None, required_tools: Iterable[str] = (), timeout: float = 10.0) -> ProbeResult:
    if not token or not token.strip():
        return ProbeResult("NOT_CONFIGURED", url, detail="API key environment/credential is not available to the probe process")
    token = token.strip()

    # 1) Current stateless protocol: tools/list is self-describing; no initialize/session.
    latest_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {"_meta": _modern_meta()},
    }
    try:
        status, _, body = _post(url, token, latest_payload, timeout, protocol=LATEST_PROTOCOL, method_header="tools/list")
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        return ProbeResult("NETWORK_FAILED", url, detail=f"network error: {type(exc).__name__}: {exc}")

    state = _classify_http(status)
    if state:
        return ProbeResult(state, url, LATEST_PROTOCOL, detail=f"HTTP {status}")
    if 200 <= status < 300:
        tools, cursor = _extract_tool_page(body)
        if tools is not None:
            all_tools = list(tools)
            page = 1
            seen_cursors: set[str] = set()
            while cursor:
                if cursor in seen_cursors or page >= 50:
                    return ProbeResult("UNKNOWN_FAILURE", url, LATEST_PROTOCOL, all_tools, detail="invalid or excessive tools/list pagination")
                seen_cursors.add(cursor)
                page += 1
                payload = {
                    "jsonrpc": "2.0",
                    "id": page,
                    "method": "tools/list",
                    "params": {"cursor": cursor, "_meta": _modern_meta()},
                }
                try:
                    p_status, _, p_body = _post(
                        url, token, payload, timeout,
                        protocol=LATEST_PROTOCOL, method_header="tools/list",
                    )
                except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
                    return ProbeResult("NETWORK_FAILED", url, LATEST_PROTOCOL, all_tools, detail=f"network error during tools/list pagination: {type(exc).__name__}: {exc}")
                p_state = _classify_http(p_status)
                if p_state:
                    return ProbeResult(p_state, url, LATEST_PROTOCOL, all_tools, detail=f"HTTP {p_status} during tools/list pagination")
                if not (200 <= p_status < 300):
                    return ProbeResult("UNKNOWN_FAILURE", url, LATEST_PROTOCOL, all_tools, detail=f"HTTP {p_status} during tools/list pagination")
                page_tools, cursor = _extract_tool_page(p_body)
                if page_tools is None:
                    return ProbeResult("UNKNOWN_FAILURE", url, LATEST_PROTOCOL, all_tools, detail="invalid tools/list pagination response")
                _append_unique(all_tools, page_tools)
            return _finish(url, LATEST_PROTOCOL, all_tools, required_tools)
        err = _jsonrpc_error(body).lower()
        # Some older servers return JSON-RPC errors with 2xx; fall through only for protocol/init errors.
        if not any(x in err for x in ("unsupported", "initialize", "protocol", "method not found")):
            return ProbeResult("UNKNOWN_FAILURE", url, LATEST_PROTOCOL, detail="2xx response did not contain a tools catalog")
    elif status not in (400, 404, 405, 406, 415, 422):
        return ProbeResult("UNKNOWN_FAILURE", url, LATEST_PROTOCOL, detail=f"unexpected HTTP {status}")

    # 2) Backward-compatible Streamable HTTP initialize/session flow.
    last_detail = "latest protocol not accepted; legacy fallback attempted"
    for legacy in LEGACY_PROTOCOLS:
        init_payload = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "initialize",
            "params": {
                "protocolVersion": legacy,
                "capabilities": {},
                "clientInfo": {"name": "yuandian-skill-probe", "version": "1.2.0"},
            },
        }
        try:
            status, headers, body = _post(url, token, init_payload, timeout, method_header="initialize")
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            return ProbeResult("NETWORK_FAILED", url, legacy, detail=f"network error: {type(exc).__name__}: {exc}")
        state = _classify_http(status)
        if state:
            return ProbeResult(state, url, legacy, detail=f"HTTP {status} during initialize")
        if not (200 <= status < 300) or not isinstance(body.get("result"), dict):
            last_detail = f"legacy {legacy} initialize rejected (HTTP {status}; {_jsonrpc_error(body) or 'no InitializeResult'})"
            continue
        negotiated = body["result"].get("protocolVersion") or legacy
        session_id = headers.get("mcp-session-id")
        notif_status = _notification(
            url, token,
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            timeout, negotiated, session_id,
        )
        if notif_status in (401, 403):
            return ProbeResult("AUTH_FAILED", url, negotiated, detail=f"HTTP {notif_status} after initialize")
        if notif_status == 429:
            return ProbeResult("RATE_LIMITED", url, negotiated, detail="HTTP 429 after initialize")
        if notif_status >= 500:
            return ProbeResult("NETWORK_FAILED", url, negotiated, detail=f"HTTP {notif_status} after initialize")

        list_payload = {"jsonrpc": "2.0", "id": 11, "method": "tools/list", "params": {}}
        try:
            status, _, body = _post(
                url, token, list_payload, timeout,
                protocol=negotiated, session_id=session_id, method_header="tools/list",
            )
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            return ProbeResult("NETWORK_FAILED", url, negotiated, detail=f"network error: {type(exc).__name__}: {exc}")
        state = _classify_http(status)
        if state:
            return ProbeResult(state, url, negotiated, detail=f"HTTP {status} during tools/list")
        if 200 <= status < 300:
            tools, cursor = _extract_tool_page(body)
            if tools is not None:
                all_tools = list(tools)
                page = 1
                seen_cursors: set[str] = set()
                pagination_failed = False
                while cursor:
                    if cursor in seen_cursors or page >= 50:
                        last_detail = f"legacy {legacy} invalid or excessive tools/list pagination"
                        pagination_failed = True
                        break
                    seen_cursors.add(cursor)
                    page += 1
                    payload = {"jsonrpc": "2.0", "id": 11 + page, "method": "tools/list", "params": {"cursor": cursor}}
                    try:
                        p_status, _, p_body = _post(
                            url, token, payload, timeout,
                            protocol=negotiated, session_id=session_id, method_header="tools/list",
                        )
                    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
                        return ProbeResult("NETWORK_FAILED", url, negotiated, all_tools, detail=f"network error during legacy tools/list pagination: {type(exc).__name__}: {exc}")
                    p_state = _classify_http(p_status)
                    if p_state:
                        return ProbeResult(p_state, url, negotiated, all_tools, detail=f"HTTP {p_status} during legacy tools/list pagination")
                    if not (200 <= p_status < 300):
                        last_detail = f"legacy {legacy} tools/list pagination failed (HTTP {p_status})"
                        pagination_failed = True
                        break
                    page_tools, cursor = _extract_tool_page(p_body)
                    if page_tools is None:
                        last_detail = f"legacy {legacy} invalid tools/list pagination response"
                        pagination_failed = True
                        break
                    _append_unique(all_tools, page_tools)
                if not pagination_failed:
                    return _finish(url, negotiated, all_tools, required_tools)
        last_detail = f"legacy {legacy} tools/list failed (HTTP {status}; {_jsonrpc_error(body) or 'invalid catalog'})"

    return ProbeResult("UNKNOWN_FAILURE", url, detail=last_detail)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Yuandian Streamable HTTP MCP without exposing the API key")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--server", choices=sorted(OFFICIAL_SERVERS), help="Use an official Yuandian public MCP endpoint")
    target.add_argument("--url", help="Probe an explicit/private MCP URL")
    parser.add_argument("--api-key-env", default="YUANDIAN_API_KEY", help="Environment variable containing the Bearer API key")
    parser.add_argument("--require-tool", action="append", default=[], help="Tool name that must be present; may be repeated")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    url = OFFICIAL_SERVERS[args.server] if args.server else args.url
    result = probe(url, os.getenv(args.api_key_env), args.require_tool, args.timeout)
    payload = asdict(result)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"state={result.state}")
        print(f"url={result.url}")
        if result.protocol:
            print(f"protocol={result.protocol}")
        if result.tools is not None:
            print(f"tools={len(result.tools)}")
            for name in result.tools:
                print(f"- {name}")
        if result.missing_tools:
            print("missing_tools=" + ",".join(result.missing_tools))
        if result.detail:
            print(f"detail={result.detail}")
    return 0 if result.state == "READY" else 2 if result.state == "NOT_CONFIGURED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
