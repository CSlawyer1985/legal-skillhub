#!/usr/bin/env python3
"""MCP 数据源采集器（stdio 传输，极简 JSON-RPC 客户端）。
用法: python3 scripts/mcp_collect.py <公司全称> <输出目录> [mcp_config.json]

行为：
- 读取 mcp_config.json（默认取 Skill 根目录），对每个数据源按 dimensions 配置
  调用对应 tool，原始返回写入 <输出目录>/采集原始数据/<source>_<dimension>.json。
- token 从环境变量读取（token_env），缺失/调用失败 → 该维度标记降级，
  由 AI 改用 WebSearch/FetchURL 采集，采集结果汇总写入 mcp采集结果.md。
- 全部数据源不可用时退出码 0 并打印降级提示（不阻断流程）。
"""
import json
import os
import subprocess
import sys


def rpc(proc, method, params=None, rid=0, notify=False):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        msg["id"] = rid
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()
    if notify:
        return None
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("MCP 服务无响应")
        resp = json.loads(line)
        if resp.get("id") == rid:
            return resp


class HttpMCP:
    """stream-http 传输的极简 MCP 客户端（企查查等远程端点）。"""

    def __init__(self, url, token):
        self.url = url
        self.headers = {"Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"}
        self.rid = 0

    def call(self, method, params=None, notify=False):
        import urllib.request
        self.rid += 1
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            msg["id"] = self.rid
        req = urllib.request.Request(self.url, data=json.dumps(msg).encode(),
                                     headers=self.headers, method="POST")
        if notify:
            urllib.request.urlopen(req, timeout=60).read()
            return None
        body = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                resp = json.loads(line[5:].strip())
                if resp.get("id") == self.rid:
                    return resp
            elif line.startswith("{"):
                resp = json.loads(line)
                if resp.get("id") == self.rid:
                    return resp
        raise RuntimeError(f"MCP 响应中未找到 id={self.rid} 的结果: {body[:200]}")



def collect(company, outdir, cfg_path):
    try:
        cfg = json.load(open(cfg_path, encoding="utf-8"))
    except FileNotFoundError:
        print(f"未找到 MCP 配置（{cfg_path}），整单降级为公开网页检索。"
              f"如需启用 MCP 数据源，复制 mcp_config.example.json 为 mcp_config.json 并配置 token 环境变量。")
        return
    raw_dir = os.path.join(outdir, "采集原始数据")
    os.makedirs(raw_dir, exist_ok=True)
    summary, rid = [], 0
    for src in cfg.get("sources", []):
        token = os.environ.get(src.get("token_env", ""), "")
        if not token:
            summary.append(f"- {src['label']}：降级（环境变量 {src['token_env']} 未设置）")
            continue
        env = dict(os.environ)
        try:
            if src.get("transport") == "stream-http":
                client = HttpMCP(src["url"], token)
                popen = None
                def rpc_fn(method, params=None, rid=None, notify=False):
                    return client.call(method, params, notify)
                rpc_fn("initialize", {"protocolVersion": "2024-11-05",
                                      "capabilities": {},
                                      "clientInfo": {"name": "bgcheck-skill", "version": "2.2"}})
                rpc_fn("notifications/initialized", notify=True)
                tools = [t["name"] for t in rpc_fn("tools/list", {})["result"]["tools"]]
            else:
                popen = subprocess.Popen([src["command"], *src["args"]],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, env=env)
                def rpc_fn(method, params=None, rid=None, notify=False):
                    nonlocal_rid[0] += 1
                    return rpc(popen, method, params, nonlocal_rid[0], notify)
                nonlocal_rid = [rid]
                rpc_fn("initialize", {"protocolVersion": "2024-11-05",
                                      "capabilities": {},
                                      "clientInfo": {"name": "bgcheck-skill", "version": "2.2"}})
                rpc_fn("notifications/initialized", notify=True)
                tools = [t["name"] for t in rpc_fn("tools/list", {})["result"]["tools"]]
            for dim, spec in src.get("dimensions", {}).items():
                tools_wanted = spec.get("tools") or [spec["tool"]]
                available = [t for t in tools_wanted if t in tools]
                if not available:
                    summary.append(f"- {src['label']}/{dim}：降级（工具均不存在 {tools_wanted}）")
                    continue
                for tool in available:
                    resp = rpc_fn("tools/call",
                                  {"name": tool,
                                   "arguments": {spec["query_field"]: company}})
                    with open(os.path.join(raw_dir, f"{src['name']}_{dim}_{tool}.json"), "w",
                              encoding="utf-8") as f:
                        json.dump(resp, f, ensure_ascii=False, indent=2)
                summary.append(f"- {src['label']}/{dim}：✅ 已采集 {len(available)} 个工具（MCP）")
            if popen is not None:
                popen.terminate()
        except Exception as e:  # noqa: BLE001
            summary.append(f"- {src['label']}：降级（{type(e).__name__}: {e}）")
    with open(os.path.join(outdir, "mcp采集结果.md"), "w", encoding="utf-8") as f:
        f.write(f"# MCP 采集结果（{company}）\n\n" + "\n".join(summary)
                + "\n\n> 标记“降级”的维度由 AI 改用公开网页检索采集，证据账本中来源类型标“公开网页检索”。\n")
    print("\n".join(summary))


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    collect(sys.argv[1], sys.argv[2],
            sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, "mcp_config.json"))
