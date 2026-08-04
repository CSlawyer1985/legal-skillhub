"""MCP 薄客户端 - 财税知识库（发票经济风控专用封装）

本客户端**复用** tax-policy-knowledge-mcp 技能已注册的同一云端财税知识库 MCP 服务，
共享其 API Key 与配置（~/.workbuddy/config/tax-policy-mcp.json），
实现「统一注册、统一调用」，避免重复开发与重复注册。

对外提供发票风控场景友好的接口：
  - query_policy(question, category)        政策问答
  - check_risk(scenario, level_filter)      风险诊断
  - calculate_tax(tax_type, params)         税额计算
  - list_kb()                               知识库概览
  - invoice_risk_advice(rule_name, desc)    针对命中指标，拉取政策依据与整改建议（智能补强）
"""

import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
import hashlib
import platform

# ===== 与 tax-policy-knowledge-mcp 共用同一云端服务与配置（避免重复注册）=====
_CONFIG_DIR = os.path.expanduser("~/.workbuddy/config")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "tax-policy-mcp.json")  # 共享配置

_DEFAULT_SERVICE_URL = "https://mcp.aitaxs.top/api/services/tax-policy-knowledge/mcp"
_DEFAULT_API_BASE = "https://mcp.aitaxs.top/api/services/tax-policy-knowledge"

_USER_AGENT = "invoice-economy-risk-ctrl/3.0.0"

# 本地缓存目录（独立，便于本技能排障）
_CACHE_DIR = os.path.expanduser("~/.workbuddy/cache/invoice-risk")
_HEALTH_FILE = os.path.join(_CACHE_DIR, "health_cache.json")

_MCPCHECK_TIMEOUT = 5
_FALLBACK_PROBE_INTERVAL = 30
_rpc_id = 0

_health_state = {
    "mode": "unknown",
    "last_check_time": 0,
    "consecutive_failures": 0,
    "last_probe_time": 0,
    "fallback_count": 0,
}


# ============= 健康状态 =============
def _load_health_state():
    global _health_state
    if os.path.exists(_HEALTH_FILE):
        try:
            with open(_HEALTH_FILE, encoding="utf-8") as f:
                _health_state.update(json.load(f))
        except Exception:
            pass
    return _health_state


def _save_health_state():
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_HEALTH_FILE, "w", encoding="utf-8") as f:
            json.dump(_health_state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _get_current_mode():
    now = time.time()
    current = _health_state["mode"]
    if current in ("unknown", "remote"):
        return "remote"
    if current == "fallback" and _health_state["consecutive_failures"] > 0:
        if now - _health_state["last_probe_time"] >= _FALLBACK_PROBE_INTERVAL:
            _health_state["mode"] = "probe"
            _health_state["last_probe_time"] = now
            _save_health_state()
            return "probe"
        return "fallback"
    return "remote"


# ============= 用户友好错误 =============
_FRIENDLY = {
    "connection_failed": {"message": "远程财税知识库暂时无法连接", "suggestion": "已切换为本地规则库模式，结论以本技能 15 项指标为准。"},
    "http_error": {"message": "远程财税知识库返回了错误", "suggestion": "已切换为本地规则库模式，稍后重试可获取最新政策依据。"},
    "api_key_invalid": {"message": "远程服务验证失败", "suggestion": "授权凭证暂时不可用，已切换为本地规则库模式。"},
    "not_registered": {"message": "尚未完成服务注册", "suggestion": "系统正在自动注册，请稍候。"},
    "unknown_error": {"message": "遇到未知错误", "suggestion": "已切换为本地规则库模式。"},
    "fallback_active": {"message": "当前使用本地规则库模式", "suggestion": "远程服务暂不可用，结论来自本技能内置 15 项指标规则。"},
}


def _friendly_error(key, raw=None):
    f = _FRIENDLY.get(key, _FRIENDLY["unknown_error"])
    res = {"error": f["message"], "suggestion": f["suggestion"]}
    if raw:
        res["error_detail"] = raw
    return res


# ============= 配置 / API Key（共享 tax-policy-mcp.json）=============
def _load_config():
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"service_url": _DEFAULT_SERVICE_URL, "api_key": None, "kb_version": None, "last_update_time": None}


def _save_config(config):
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _register_api_key(user_id=None):
    """首次注册 API Key（与 tax-policy-knowledge-mcp 同一云端 MCP Manager）"""
    global _rpc_id
    device_id = hashlib.md5(
        f"{platform.node()}-{platform.processor()}-{time.time()}".encode()
    ).hexdigest()[:16]
    url = "https://mcp.aitaxs.top/api/auth/register"
    payload = json.dumps({
        "name": f"invoice-risk-skill-{device_id[:8]}",
        "user_id": user_id or "auto",
        "device_id": device_id,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": _USER_AGENT,
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        api_key = result.get("api_key")
        if api_key:
            return {"api_key": api_key, "key_id": result.get("key_id"),
                    "key_prefix": result.get("key_prefix")}
        return {"error": _FRIENDLY["not_registered"]["message"], "api_key": None}
    except urllib.error.HTTPError:
        return {"error": "HTTP 错误", "api_key": None}
    except urllib.error.URLError:
        return {"error": "注册服务暂时不可用", "api_key": None}
    except Exception:
        return {"error": "注册过程出错", "api_key": None}


def _ensure_api_key(config):
    api_key = config.get("api_key")
    if api_key:
        return api_key
    result = _register_api_key()
    api_key = result.get("api_key")
    if api_key:
        config["api_key"] = api_key
        config["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        _save_config(config)
        return api_key
    return None


# ============= 健康检查 =============
def _quick_health_check(timeout=_MCPCHECK_TIMEOUT):
    config = _load_config()
    api_key = _ensure_api_key(config)
    service_url = config.get("service_url", _DEFAULT_SERVICE_URL)
    rpc_payload = json.dumps({
        "jsonrpc": "2.0", "id": 9999, "method": "tools/list", "params": {}
    }).encode()
    headers = {"Content-Type": "application/json", "User-Agent": _USER_AGENT}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        req = urllib.request.Request(service_url, data=rpc_payload, headers=headers)
        resp = urllib.request.urlopen(req, timeout=timeout)
        result = json.loads(resp.read())
        if "result" in result and "tools" in result.get("result", {}):
            return {"healthy": True, "tools_count": len(result["result"]["tools"])}
        return {"healthy": False, "reason": "invalid_response"}
    except urllib.error.HTTPError as e:
        return {"healthy": False, "reason": f"http_{e.code}"}
    except urllib.error.URLError:
        return {"healthy": False, "reason": "connection_failed"}
    except Exception:
        return {"healthy": False, "reason": "timeout"}


def _update_mode(healthy):
    global _health_state
    if healthy:
        if _health_state["mode"] != "remote":
            _health_state["mode"] = "remote"
            _health_state["consecutive_failures"] = 0
            _health_state["last_check_time"] = time.time()
            _save_health_state()
    else:
        if _health_state["mode"] != "fallback":
            _health_state["consecutive_failures"] += 1
            if _health_state["consecutive_failures"] >= 1:
                _health_state["mode"] = "fallback"
                _health_state["last_probe_time"] = time.time()
                _health_state["fallback_count"] += 1
                _save_health_state()
        _health_state["last_check_time"] = time.time()


# ============= MCP 调用 =============
def _call_mcp_tool(tool_name, params, api_key=None, service_url=None):
    global _rpc_id
    _rpc_id += 1
    rpc_payload = json.dumps({
        "jsonrpc": "2.0", "id": _rpc_id, "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
    }).encode()
    config = _load_config()
    service_url = service_url or config.get("service_url", _DEFAULT_SERVICE_URL)
    api_key = api_key if api_key is not None else _ensure_api_key(config)
    headers = {"Content-Type": "application/json", "User-Agent": _USER_AGENT}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        req = urllib.request.Request(service_url, data=rpc_payload, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        r = result.get("result", result)
        content_list = r.get("content", [])
        for item in content_list:
            if item.get("type") == "text" and "API Key" in item.get("text", ""):
                return _friendly_error("api_key_invalid")
        structured = r.get("structuredContent", {})
        if structured and isinstance(structured, dict):
            return structured
        # 云端服务常以 "JSON 字符串" 形式置于 content[].text 中返回
        texts = [c.get("text", "") for c in content_list if c.get("type") == "text"]
        if texts:
            joined = "\n".join(texts)
            try:
                parsed = json.loads(joined)
                if isinstance(parsed, dict):
                    return parsed
                return {"text": joined}
            except Exception:
                return {"text": joined}
        return r
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:200]
        return _friendly_error("http_error", {"http_code": e.code, "raw": detail})
    except urllib.error.URLError:
        return _friendly_error("connection_failed")
    except Exception:
        return _friendly_error("unknown_error")


def _call_rest_api(method, path, params=None, api_key=None):
    url = f"{_DEFAULT_API_BASE}{path}"
    config = _load_config()
    api_key = api_key if api_key is not None else _ensure_api_key(config)
    headers = {"Content-Type": "application/json", "User-Agent": _USER_AGENT}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        if method == "GET":
            if params:
                qs = "&".join(f"{k}={v}" for k, v in params.items())
                url = f"{url}?{qs}"
            req = urllib.request.Request(url, headers=headers)
        else:
            req = urllib.request.Request(url, data=json.dumps(params or {}).encode(), headers=headers)
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return _friendly_error("http_error", {"http_code": e.code})
    except urllib.error.URLError:
        return _friendly_error("connection_failed")
    except Exception:
        return _friendly_error("unknown_error")


# ============= 对外接口（带降级）=============
def _remote_call_with_fallback(tool_name, params, fallback_value=None):
    _load_health_state()
    mode = _get_current_mode()
    if mode in ("probe", "remote"):
        if mode == "probe":
            health = _quick_health_check()
            if not health.get("healthy"):
                _update_mode(False)
                return fallback_value if fallback_value is not None else _friendly_error("fallback_active")
            _update_mode(True)
        result = _call_mcp_tool(tool_name, params)
        if "error" in result:
            _update_mode(False)
            return fallback_value if fallback_value is not None else result
        return result
    # fallback 模式
    return fallback_value if fallback_value is not None else _friendly_error("fallback_active")


def query_policy(question, category=None):
    """政策问答：问政策 → 返回答案 + 政策依据"""
    params = {"question": question}
    if category:
        params["category"] = category
    return _remote_call_with_fallback("tax_policy_ask", params)


def check_risk(scenario, level_filter=None):
    """风险诊断：讲场景 → 返回风险等级与建议"""
    params = {"scenario": scenario}
    if level_filter:
        params["level_filter"] = level_filter
    return _remote_call_with_fallback("risk_check", params)


def calculate_tax(tax_type, params):
    """税额计算：输入数据 → 返回税额"""
    payload = {"tax_type": tax_type, "params": params}
    return _remote_call_with_fallback("tax_calculate", payload)


def list_kb():
    """知识库概览"""
    return _remote_call_with_fallback("kb_list", {})


def invoice_risk_advice(rule_name, desc, industry=None):
    """智能补强：针对命中的风控指标，向云端知识库拉取政策依据与整改建议。

    返回 dict: {source, policy_basis, advice, related_questions}
    source == 'mcp' 表示来自云端知识库；否则为本地兜底。
    """
    scenario = f"发票风险：{rule_name}。{desc}"
    if industry:
        scenario += f"（行业：{industry}）"
    remote = _remote_call_with_fallback("risk_check", {"scenario": scenario})
    if isinstance(remote, dict) and "error" not in remote:
        risks = remote.get("risks") or []
        policy_refs = []
        for rk in risks:
            name = rk.get("level_name") or rk.get("indicator") or ""
            pref = rk.get("policy_ref") or ""
            desc = rk.get("description") or ""
            policy_refs.append(f"{name}（依据：{pref}）— {desc}")
        policy_basis = "\n".join(policy_refs) if policy_refs else remote.get("policy_basis")
        return {
            "source": "mcp",
            "policy_basis": policy_basis or None,
            "advice": remote.get("suggestion") or remote.get("advice"),
            "overall_risk": remote.get("overall_risk"),
            "risks": risks,
            "raw": remote,
        }
    # 本地兜底：直接问政策问答
    q = _remote_call_with_fallback("tax_policy_ask", {"question": f"{rule_name} 的税务政策依据与合规整改建议"})
    if isinstance(q, dict) and "error" not in q:
        answer = q.get("answer") or q.get("result") or q.get("text")
        if isinstance(answer, dict):
            answer = answer.get("answer") or answer.get("text")
        return {"source": "mcp", "policy_basis": answer, "advice": None, "risks": [], "raw": q}
    return {"source": "local", "policy_basis": None, "advice": None, "risks": [],
            "note": "远程知识库不可用，建议使用本技能内置整改建议或咨询专业税务师 / 12366。"}


def get_mode_status():
    _load_health_state()
    return {
        "mode": _get_current_mode(),
        "consecutive_failures": _health_state["consecutive_failures"],
        "fallback_count": _health_state["fallback_count"],
        "config_file": _CONFIG_FILE,
        "shared_with": "tax-policy-knowledge-mcp",
    }


if __name__ == "__main__":
    print("=== 发票经济风控 MCP 薄客户端 ===")
    print("配置（共享 tax-policy-knowledge-mcp）:", _CONFIG_FILE)
    st = get_mode_status()
    print("运行模式:", json.dumps(st, ensure_ascii=False))
    print("健康检查:", json.dumps(_quick_health_check(), ensure_ascii=False))
