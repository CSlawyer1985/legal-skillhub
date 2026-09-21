"""元典现行 Stateless Streamable HTTP MCP 轻量兼容层。"""
from __future__ import annotations

import json
import os
from typing import Any

import requests

from yuandian_api import _local_config_value


SERVERS = {
    "law": "https://open.chineselaw.com/mcp/law/stream",
    "case": "https://open.chineselaw.com/mcp/case/stream",
    "company": "https://open.chineselaw.com/mcp/company/stream",
    "securities": "https://open.chineselaw.com/mcp/securities/stream",
}
LATEST_PROTOCOL = "2026-07-28"
DEFAULT_TIMEOUT = 60.0


class MCPError(RuntimeError):
    def __init__(self, state: str, message: str):
        super().__init__(message)
        self.state = state


def _server_url(server: str) -> str:
    if server in SERVERS:
        return SERVERS[server]
    if server.startswith("https://"):
        return server
    raise MCPError("NOT_CONFIGURED", f"未知元典 MCP Server: {server}")


def _api_key(api_key: str | None) -> str:
    key = api_key or os.getenv("YUANDIAN_API_KEY") or _local_config_value("API_KEY")
    if not isinstance(key, str) or not key.strip() or key == "YOUR_YUANDIAN_API_KEY_HERE":
        raise MCPError("NOT_CONFIGURED", "未配置 YUANDIAN_API_KEY")
    return key.strip()


def _timeout() -> float:
    try:
        return max(1.0, float(os.getenv("YUANDIAN_MCP_TIMEOUT", DEFAULT_TIMEOUT)))
    except ValueError:
        return DEFAULT_TIMEOUT


def _meta() -> dict[str, Any]:
    return {
        "io.modelcontextprotocol/protocolVersion": LATEST_PROTOCOL,
        "io.modelcontextprotocol/clientInfo": {
            "name": "prc-legal-research",
            "version": "1.1.0",
        },
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def _parse_payload(response) -> dict[str, Any]:
    content_type = response.headers.get("Content-Type", "").lower()
    if "text/event-stream" not in content_type:
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise MCPError("UNKNOWN_FAILURE", "MCP 响应不是有效 JSON") from exc
        if not isinstance(payload, dict):
            raise MCPError("UNKNOWN_FAILURE", "MCP 响应结构无效")
        return payload

    data_lines: list[str] = []
    for line in response.text.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif not line.strip() and data_lines:
            try:
                payload = json.loads("\n".join(data_lines))
            except json.JSONDecodeError:
                data_lines = []
                continue
            if isinstance(payload, dict):
                return payload
            data_lines = []
    if data_lines:
        try:
            payload = json.loads("\n".join(data_lines))
        except json.JSONDecodeError as exc:
            raise MCPError("UNKNOWN_FAILURE", "MCP SSE 数据不是有效 JSON") from exc
        if isinstance(payload, dict):
            return payload
    raise MCPError("UNKNOWN_FAILURE", "MCP SSE 响应中没有 JSON data 事件")


def _post(server: str, api_key: str | None, method: str, request_id: int,
          params: dict[str, Any]) -> dict[str, Any]:
    key = _api_key(api_key)
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": LATEST_PROTOCOL,
        "Mcp-Method": method,
        "User-Agent": "prc-legal-research/1.1.0",
    }
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    try:
        response = requests.post(
            _server_url(server),
            headers=headers,
            json=payload,
            timeout=_timeout(),
        )
    except requests.RequestException as exc:
        raise MCPError("NETWORK_FAILED", f"MCP 网络请求失败: {type(exc).__name__}") from exc

    if response.status_code in (401, 403):
        raise MCPError("AUTH_FAILED", f"MCP 鉴权失败: HTTP {response.status_code}")
    if response.status_code == 429:
        raise MCPError("RATE_LIMITED", "MCP 请求被限流: HTTP 429")
    if response.status_code >= 500:
        raise MCPError("NETWORK_FAILED", f"MCP 服务异常: HTTP {response.status_code}")
    if not 200 <= response.status_code < 300:
        raise MCPError("UNKNOWN_FAILURE", f"MCP 请求失败: HTTP {response.status_code}")

    body = _parse_payload(response)
    error = body.get("error")
    if isinstance(error, dict):
        code = error.get("code", "")
        message = error.get("message") or "JSON-RPC 错误"
        raise MCPError("UNKNOWN_FAILURE", f"MCP {method} 失败 ({code}): {message}")
    return body


def list_tools(server: str, api_key: str | None = None) -> list[dict[str, Any]]:
    """运行时发现工具及 inputSchema；静态工具清单不作为调用依据。"""
    tools: list[dict[str, Any]] = []
    cursor: str | None = None
    seen: set[str] = set()
    request_id = 1
    while True:
        params: dict[str, Any] = {"_meta": _meta()}
        if cursor:
            params["cursor"] = cursor
        body = _post(server, api_key, "tools/list", request_id, params)
        result = body.get("result")
        page = result.get("tools") if isinstance(result, dict) else None
        if not isinstance(page, list):
            raise MCPError("UNKNOWN_FAILURE", "tools/list 未返回工具目录")
        tools.extend(tool for tool in page if isinstance(tool, dict))
        cursor = result.get("nextCursor")
        if not cursor:
            return tools
        if not isinstance(cursor, str) or cursor in seen or request_id >= 50:
            raise MCPError("UNKNOWN_FAILURE", "tools/list 分页游标无效")
        seen.add(cursor)
        request_id += 1


def _validate_arguments(tool: dict[str, Any], arguments: dict[str, Any]) -> None:
    schema = tool.get("inputSchema")
    if not isinstance(schema, dict):
        return
    required = schema.get("required", [])
    if not isinstance(required, list):
        return
    missing = [name for name in required if name not in arguments]
    if missing:
        raise MCPError("INVALID_ARGUMENTS", "缺少运行时 Schema 必填参数: " + ", ".join(missing))


def call_tool(server: str, tool_name: str, arguments: dict[str, Any],
              api_key: str | None = None) -> dict[str, Any]:
    """先发现并校验运行时 Schema，再调用指定工具。"""
    catalog = list_tools(server, api_key=api_key)
    tool = next((item for item in catalog if item.get("name") == tool_name), None)
    if tool is None:
        raise MCPError("CAPABILITY_MISSING", f"MCP 未暴露工具: {tool_name}")
    _validate_arguments(tool, arguments)
    body = _post(
        server,
        api_key,
        "tools/call",
        2,
        {"name": tool_name, "arguments": arguments, "_meta": _meta()},
    )
    result = body.get("result")
    if not isinstance(result, dict):
        raise MCPError("UNKNOWN_FAILURE", "tools/call 未返回有效 result")
    return result
