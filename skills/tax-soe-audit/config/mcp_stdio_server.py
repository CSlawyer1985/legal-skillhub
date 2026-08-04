#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财税政策 MCP · 通用 stdio 服务器（零第三方依赖，仅标准库）。

目的：让本技能包可被**任意支持 MCP 的 Agent / 客户端**直接以 stdio 方式运行，
      而不依赖特定 Agent 运行时。它通过 HTTP 将请求代理到公共云端 MCP 端点，
      对外暴露与云端一致的安全工具面：tax_policy_ask / risk_check / tax_calculate / kb_list。

典型接入（以任意 MCP 客户端为例）：
  {
    "mcpServers": {
      "tax-policy": {
        "command": "python",
        "args": ["<技能包目录>/config/mcp_stdio_server.py"]
      }
    }
  }

或直接复用云端 MCP 端点（若客户端支持 HTTP/SSE 型 MCP）：
  https://mcp.aitaxs.top/api/services/tax-policy-knowledge/mcp
"""
import json
import sys
import os
import urllib.request
import urllib.error

SERVICE_URL = "https://mcp.aitaxs.top/api/services/tax-policy-knowledge/mcp"
CLIENT_ID = "tax-policy-stdio"
CLIENT_VERSION = "4.0.0"

TOOLS = [
    {
        "name": "tax_policy_ask",
        "description": "财税政策问答（含风险应对政策依据）",
        "inputSchema": {"type": "object",
                         "properties": {"question": {"type": "string"}, "category": {"type": "string"}}},
    },
    {
        "name": "risk_check",
        "description": "企业税务风险初筛（自然语言 scenario，≤2000 字）",
        "inputSchema": {"type": "object",
                         "properties": {"scenario": {"type": "string"}, "level_filter": {"type": "string"}}},
    },
    {
        "name": "tax_calculate",
        "description": "各类税费计算",
        "inputSchema": {"type": "object",
                         "properties": {"tax_type": {"type": "string"}, "params": {"type": "object"}}},
    },
    {
        "name": "kb_list",
        "description": "知识库概览（仅元数据，不回正文）",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _rpc(method, params, rid=1):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": rid, "method": method, "params": params
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"tax-policy-stdio/{CLIENT_VERSION}",
        "X-Client-Id": CLIENT_ID,
        "X-Client-Version": CLIENT_VERSION,
    }
    req = urllib.request.Request(SERVICE_URL, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": {"code": e.code, "message": e.read().decode("utf-8", "replace")[:300]}}
    except Exception as e:  # 网络/超时等：优雅降级为本地提示
        return {"error": {"code": -32000, "message": f"云端服务暂不可用：{e}"}}


def _readline():
    line = sys.stdin.readline()
    if not line:
        return None
    return line.strip()


def main():
    # 强制 stdin/stdout 为 utf-8（Windows 控制台默认 GBK 易乱码）
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # 初始化时探测客户端 Agent 类型与接入方式（写盘需 TAX_ENABLE_AUTOSETUP=1）
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            from init_agent import detect_and_setup as _detect_and_setup
        except ImportError:
            from .init_agent import detect_and_setup as _detect_and_setup
        _detect_and_setup(dry_run=None)  # 尊重 TAX_ENABLE_AUTOSETUP 环境变量；默认仅探测+日志
    except Exception:
        pass

    for line in iter(_readline, None):
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        mid = msg.get("id")
        params = msg.get("params", {}) or {}

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0", "id": mid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "tax-policy-stdio", "version": CLIENT_VERSION},
                },
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {}) or {}
            res = _rpc("tools/call", {"name": name, "arguments": arguments})
            content = []
            if "error" in res:
                content = [{"type": "text", "text": f"错误：{res['error'].get('message', '')}"}]
            else:
                r = res.get("result", res)
                txt = r.get("content", [{}])[0].get("text", "") if r.get("content") else ""
                if not txt and r.get("structuredContent"):
                    txt = json.dumps(r["structuredContent"], ensure_ascii=False)
                content = [{"type": "text", "text": txt or json.dumps(r, ensure_ascii=False)}]
            resp = {"jsonrpc": "2.0", "id": mid, "result": {"content": content}}
        else:
            resp = {"jsonrpc": "2.0", "id": mid, "result": {}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
