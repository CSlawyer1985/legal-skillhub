"""财税政策 MCP 薄客户端（安全收敛版 · v4.0.0）

安全设计要点（与云端服务硬化后的安全工具面严格对齐）：
- 仅暴露云端已开放的安全工具：tax_policy_ask / risk_check / tax_calculate / kb_list。
- 已彻底移除所有被服务端下线或移出白名单的危险运维端点对应的客户端函数，避免内部接口设计暴露。
- 本地数据目录通用化：改用跨平台用户数据目录（~/.tax-policy-client），
  便于其它 Agent / 通用 Python 环境直接复用本客户端。
- 注册仅采集本地随机匿名标识，不采集任何主机指纹；API Key 仅记前缀、不落明细日志。
- 全程标准库实现，不禁用 TLS 校验，不做 eval/exec/动态导入。
"""
import json
import os
import re
import time
import threading
import urllib.request
import urllib.error
import urllib.parse
import hashlib
import uuid


# ============================================================
# 初始化时自动识别 Agent 类型并决策接入方式（探测+日志，默认不写盘）
# 由 config/init_agent.py 提供；导入失败时静默跳过，不影响客户端主流程。
# ============================================================
def _maybe_init_agent():
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            from init_agent import detect_and_setup as _detect_and_setup
        except ImportError:
            from .init_agent import detect_and_setup as _detect_and_setup
        # 客户端导入阶段仅探测+日志；写盘需显式 auto_setup(dry_run=False) 或 TAX_ENABLE_AUTOSETUP=1
        _detect_and_setup(dry_run=True)
    except Exception:
        pass


_maybe_init_agent()

# 本地数据目录（通用、跨平台、非品牌专属）：~/.tax-policy-client/{config,cache,logs}
_DATA_ROOT = os.path.join(os.path.expanduser("~"), ".tax-policy-client")
_CONFIG_DIR = os.path.join(_DATA_ROOT, "config")
_CACHE_DIR = os.path.join(_DATA_ROOT, "cache")
_LOG_DIR = os.path.join(_DATA_ROOT, "logs")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "tax-policy-mcp.json")
_FEEDBACK_QUEUE_FILE = os.path.join(_CACHE_DIR, "feedback_queue.jsonl")
_LAST_VERSION_FILE = os.path.join(_CACHE_DIR, "last_version.json")
_HEALTH_FILE = os.path.join(_CACHE_DIR, "health_cache.json")

# 远程服务地址（公共云端 MCP 端点，标准 MCP over HTTP）
_DEFAULT_SERVICE_URL = "https://mcp.aitaxs.top/api/services/tax-policy-knowledge/mcp"
_DEFAULT_API_BASE = "https://mcp.aitaxs.top/api/services/tax-policy-knowledge"

# JSON-RPC ID 计数器
_rpc_id = 0

# 降级超时设置
_MCPCHECK_TIMEOUT = 5
_FALLBACK_PROBE_INTERVAL = 30

# ============================================================
# 客户端身份（注入 X-Client-Id，供服务端按客户端归因与限流）
# ============================================================
_CLIENT_ID = "tax-legal-tax-review"
_CLIENT_VERSION = "3.15.10"

# 429 退避：最多重试次数 + 单次退避上限（秒），防止被长窗口拖死
_MAX_429_RETRIES = 2
_RATE_RETRY_CAP = 10

# 工具超时（与云端安全工具对齐；仅保留开放工具）
_TOOL_TIMEOUT_FALLBACK = {
    "tax_policy_ask": 30,
    "risk_check": 5,
    "tax_calculate": 10,
    "kb_list": 5,
}


def _base_headers(api_key: str = None) -> dict:
    h = {
        "Content-Type": "application/json",
        "User-Agent": f"tax-policy-client/{_CLIENT_VERSION}",
        "X-Client-Id": _CLIENT_ID,
        "X-Client-Version": _CLIENT_VERSION,
    }
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
    return h


def _parse_retry_after(headers) -> int:
    try:
        ra = headers.get("Retry-After") if headers else None
        if ra is not None:
            return max(1, int(str(ra).strip()))
    except Exception:
        pass
    return 5


# 工具目录缓存（由 kb_list 填充，供 per-tool 超时与兼容检查）
_tools_catalog = None


def _tool_timeout(name: str) -> int:
    cat = _tools_catalog or {}
    t = cat.get(name, {}).get("timeout_s") if isinstance(cat, dict) else None
    if not t:
        t = _TOOL_TIMEOUT_FALLBACK.get(name, 30)
    return int(t) + 10


def get_tools_catalog() -> dict:
    """返回服务端工具目录（含 timeout_s），按需拉取并缓存"""
    global _tools_catalog
    if _tools_catalog is None:
        try:
            cfg = _load_config()
            res = _call_mcp_tool("kb_list", {}, cfg.get("api_key"), cfg.get("service_url", _DEFAULT_SERVICE_URL), _retry=False)
            if isinstance(res, dict) and res.get("tools"):
                _tools_catalog = {t["name"]: t for t in res["tools"]}
        except Exception:
            pass
    return _tools_catalog or {}


# ============================================================
# LLM优化：缓存管理
# ============================================================
_result_cache = {}
_CACHE_TTL = 300  # 5分钟


def _cache_get(key: str):
    if key in _result_cache:
        cached = _result_cache[key]
        if time.time() - cached["ts"] < _CACHE_TTL:
            _result_cache.move_to_end(key)
            return cached["result"]
        else:
            del _result_cache[key]
    return None


def _cache_set(key: str, result: dict):
    if len(_result_cache) >= 100:
        _result_cache.popitem(last=False)
    _result_cache[key] = {"ts": time.time(), "result": result}


def _cache_clear():
    global _result_cache
    _result_cache = {}


# ============================================================
# 本地搜索配置（远程不可用时回退，仅作兜底，不调用任何内部端点）
# ============================================================
_LOCAL_ENGINES = [
    {"name": "bing_cn", "url": "https://cn.bing.com/search?q={q}", "parser": "_parse_bing"},
    {"name": "baidu", "url": "https://www.baidu.com/s?wd={q}", "parser": "_parse_baidu"},
]

_TAX_KEYWORDS = {
    "vat": ["增值税", "小规模纳税人", "一般纳税人", "征收率", "留抵退税"],
    "cit": ["企业所得税", "小微企业", "高新企业", "研发费用", "加计扣除"],
    "pit": ["个人所得税", "专项附加扣除", "年终奖", "经营所得"],
    "small_tax": ["印花税", "房产税", "土地使用税", "车船税", "契税"],
    "local_fee": ["教育费附加", "水利建设基金", "残疾人就业保障金", "工会经费"],
    "social_insurance": ["社保费", "养老保险", "医疗保险", "失业保险", "住房公积金"],
    "risk": ["金税四期", "税务预警", "虚开发票", "稽查", "纳税评估"],
}


def _local_ua() -> str:
    return f"tax-policy-client/{_CLIENT_VERSION}"


def _local_fetch(url, timeout=12):
    headers = {
        "User-Agent": _local_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=timeout)
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
        except Exception:
            if attempt == 0:
                time.sleep(1)
    return ""


def _strip_html(html):
    return re.sub(r"<[^>]+>", "", html).strip()


def _parse_bing(html):
    results = []
    pattern = r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>'
    for i, (href, title_html) in enumerate(re.findall(pattern, html, re.DOTALL)[:5]):
        title = _strip_html(title_html)
        if len(title) < 5 or "bing.com" in href:
            continue
        snippet = ""
        pos = html.find(href)
        if pos >= 0:
            cap = re.search(r'<p[^>]*>(.*?)</p>', html[pos:pos + 2000], re.DOTALL)
            if cap:
                snippet = _strip_html(cap.group(1))
        results.append({"title": title, "url": href, "snippet": snippet, "rank": len(results) + 1})
    return results


def _parse_baidu(html):
    if "验证" in html[:500] or "captcha" in html.lower()[:500]:
        return []
    results = []
    title_pattern = r'<h3[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
    snippet_pattern = r'<div class="c-abstract[^>]*>(.*?)</div>'
    titles = re.findall(title_pattern, html, re.DOTALL)
    snippets = re.findall(snippet_pattern, html, re.DOTALL)
    for i, (href, title_html) in enumerate(titles[:5]):
        title = _strip_html(title_html).strip()
        if len(title) < 5:
            continue
        snippet = ""
        if i < len(snippets):
            snippet = _strip_html(snippets[i]).strip()
        results.append({"title": title, "url": href, "snippet": snippet, "rank": len(results) + 1})
    return results


def _local_web_search(query, max_results=5):
    search_query = query
    for cat, keywords in _TAX_KEYWORDS.items():
        if any(kw in query for kw in keywords[:2]):
            search_query = f"{query} {' '.join(keywords[:2])}"
            break
    encoded = urllib.parse.quote(search_query)
    all_results = []
    for engine in _LOCAL_ENGINES:
        if all_results:
            break
        url = engine["url"].format(q=encoded)
        html = _local_fetch(url, timeout=8)
        if not html:
            continue
        parser = globals().get(engine["parser"])
        if parser:
            r = parser(html)
            if r:
                all_results.extend(r[:max_results])
    return all_results[:max_results]


# ============================================================
# 健康状态管理
# ============================================================
_health_state = {
    "mode": "unknown",
    "last_check_time": 0,
    "consecutive_failures": 0,
    "last_probe_time": 0,
    "fallback_count": 0,
}


def _load_health_state():
    global _health_state
    if os.path.exists(_HEALTH_FILE):
        try:
            with open(_HEALTH_FILE, encoding="utf-8") as f:
                saved = json.load(f)
                _health_state.update(saved)
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
    if current == "unknown":
        current = "remote"
    if current == "fallback" and _health_state["consecutive_failures"] > 0:
        if now - _health_state["last_probe_time"] >= _FALLBACK_PROBE_INTERVAL:
            _health_state["mode"] = "probe"
            _health_state["last_probe_time"] = now
            _save_health_state()
            return "probe"
        return "fallback"
    if current == "probe":
        return "probe"
    return "remote"


# ============================================================
# 用户友好错误
# ============================================================
_FRIENDLY_ERRORS = {
    "connection_failed": {
        "message": "无法连接到远程财税服务",
        "suggestion": "已自动切换为本地搜索模式。请检查网络后重试；若网络正常仍失败，可能是服务临时不可用。",
    },
    "timeout": {
        "message": "远程财税服务响应超时",
        "suggestion": "服务可能较繁忙。已切换为本地搜索模式，建议稍后重试，或把问题拆得更具体一些。",
    },
    "http_error": {
        "message": "远程服务返回了错误（HTTP {code}）",
        "suggestion": "服务可能正在维护或过载。已切换为本地搜索模式，可稍后重试。",
    },
    "api_key_invalid": {
        "message": "服务授权校验未通过（凭证失效或为空）",
        "suggestion": "正在尝试自动重新注册以获取新凭证；若仍失败，请重新启用本技能或联系技术支持。",
    },
    "not_registered": {
        "message": "尚未完成服务注册",
        "suggestion": "系统正在为您自动注册，请稍候再试。",
    },
    "unknown_error": {
        "message": "处理请求时出现意外错误",
        "suggestion": "已切换为本地搜索模式。可重新提问或换一种表述方式；若持续出现，请联系技术支持。",
    },
    "scenario_invalid": {
        "message": "风险场景描述不合法",
        "suggestion": "请使用纯文本描述业务场景（≤2000 字），不要粘贴文件或编码内容。可换一种表述重试。",
    },
    "rate_limited": {
        "message": "请求过于频繁，已被服务端限流",
        "suggestion": "已按服务端建议自动退避重试。若仍受限，请稍候片刻再试，或降低调用频率。",
    },
}


def _friendly_error(error_key: str, raw: dict = None):
    friendly = _FRIENDLY_ERRORS.get(error_key, _FRIENDLY_ERRORS["unknown_error"])
    msg = friendly["message"]
    if raw and isinstance(raw, dict):
        code = raw.get("http_code")
        if code and "{code}" in msg:
            msg = msg.format(code=code)
    result = {"error": msg, "suggestion": friendly["suggestion"]}
    if raw:
        result["error_detail"] = raw
    return result


# ============================================================
# 配置管理（通用本地目录）
# ============================================================
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


# ============================================================
# API Key 管理（仅本地随机匿名标识，不采集主机指纹）
# ============================================================
def _register_api_key(user_id=None, device_id=None):
    global _rpc_id
    if not device_id:
        device_id = uuid.uuid4().hex[:16]
    url = "https://mcp.aitaxs.top/api/auth/register"
    payload = json.dumps({"name": f"tax-policy-client-{device_id[:8]}", "user_id": user_id or "auto", "device_id": device_id}).encode()
    req = urllib.request.Request(url, data=payload, headers=_base_headers())
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        api_key = result.get("api_key")
        if api_key:
            _log("registration", {"status": "success", "key_prefix": result.get("key_prefix", "unknown")})
            return {
                "api_key": api_key,
                "key_id": result.get("key_id"),
                "key_prefix": result.get("key_prefix"),
                "user_id": result.get("user_id", user_id or "auto"),
                "rate_limit": result.get("rate_limit"),
                "daily_limit": result.get("daily_limit"),
            }
        _log("registration", {"status": "failed", "reason": "no_api_key_in_response"})
        return {"error": _FRIENDLY_ERRORS["not_registered"]["message"], "api_key": None}
    except urllib.error.HTTPError as e:
        _log("registration", {"status": "failed", "reason": f"http_{e.code}"})
        return {"error": f"HTTP {e.code}", "api_key": None}
    except urllib.error.URLError:
        _log("registration", {"status": "failed", "reason": "connection_failed"})
        return {"error": "注册服务暂时不可用", "api_key": None}
    except Exception:
        _log("registration", {"status": "failed", "reason": "unknown"})
        return {"error": "注册过程出错", "api_key": None}


def _ensure_api_key(config: dict, force_refresh: bool = False) -> str:
    api_key = config.get("api_key")
    if api_key and not force_refresh:
        return api_key
    if api_key and force_refresh:
        config["api_key"] = None
        config["key_id"] = None
        config["user_id"] = None
        _save_config(config)
    device_id = config.get("device_id") or uuid.uuid4().hex[:16]
    if not config.get("device_id"):
        config["device_id"] = device_id
    result = _register_api_key(device_id=device_id)
    api_key = result.get("api_key")
    if api_key:
        config["api_key"] = api_key
        config["key_id"] = result.get("key_id")
        config["user_id"] = result.get("user_id")
        config["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        _save_config(config)
        return api_key
    _log("registration", {"status": "failed", "error": result.get("error", "unknown")})
    return None


# ============================================================
# 健康检查
# ============================================================
def _quick_health_check(timeout=_MCPCHECK_TIMEOUT) -> dict:
    config = _load_config()
    api_key = config.get("api_key")
    service_url = config.get("service_url", _DEFAULT_SERVICE_URL)
    rpc_payload = json.dumps({"jsonrpc": "2.0", "id": 9999, "method": "tools/list", "params": {}}).encode()
    headers = _base_headers(api_key)
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
        if e.code == 401 and api_key:
            return {"healthy": False, "reason": "api_key_invalid", "should_reregister": True}
        return {"healthy": False, "reason": f"http_{e.code}"}
    except urllib.error.URLError:
        return {"healthy": False, "reason": "connection_failed"}
    except Exception:
        return {"healthy": False, "reason": "timeout"}


def _update_mode(healthy: bool):
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


# ============================================================
# MCP调用（仅安全工具：tax_policy_ask / risk_check / tax_calculate / kb_list）
# ============================================================
def _call_mcp_tool(tool_name: str, params: dict, api_key: str = None, service_url: str = None, _retry: bool = True):
    """调用 MCP 工具。服务端仅认完整tool名，不使用短名映射。"""
    global _rpc_id
    _rpc_id += 1

    if service_url is None:
        service_url = _DEFAULT_SERVICE_URL

    if api_key and "api_key" not in params:
        params["api_key"] = api_key

    rpc_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": _rpc_id,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
    }).encode()

    headers = _base_headers(api_key)
    timeout = _tool_timeout(tool_name)

    for _attempt in range(1 + _MAX_429_RETRIES):
        try:
            req = urllib.request.Request(service_url, data=rpc_payload, headers=headers)
            resp = urllib.request.urlopen(req, timeout=timeout)
            result = json.loads(resp.read())
            r = result.get("result", result)
            content_list = r.get("content", [])
            for item in content_list:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    if "API Key" in text and _retry:
                        return _friendly_error("api_key_invalid")
                    if text.startswith("错误:") or text.startswith("❌"):
                        return _friendly_error("server_error", {"message": text[:200]})

            structured = r.get("structuredContent", {})
            if structured and isinstance(structured, dict):
                for key, value in structured.items():
                    if isinstance(value, str) and len(value) > 1500:
                        structured[key] = value[:1500] + f"\n\n... (内容已截断，共{len(value)}字符)"
                    if isinstance(value, list) and len(value) > 30:
                        structured[key] = value[:30]
                        structured[f"{key}_more"] = f"... 还有{len(value) - 30}条"
                return structured

            for item in content_list:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, dict):
                            return parsed
                    except (json.JSONDecodeError, TypeError):
                        pass
            return r
        except urllib.error.HTTPError as e:
            if e.code == 401 and _retry:
                return _friendly_error("api_key_invalid")
            if e.code == 429:
                ra = _parse_retry_after(e.headers)
                if _attempt < _MAX_429_RETRIES:
                    time.sleep(min(ra, _RATE_RETRY_CAP))
                    continue
                return _friendly_error("rate_limited", {"retry_after": ra, "http_code": 429})
            detail = e.read().decode("utf-8", errors="replace")[:200]
            return _friendly_error("http_error", {"http_code": e.code, "raw": detail})
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", None)
            if isinstance(reason, TimeoutError) or (isinstance(reason, str) and "timed out" in reason.lower()):
                return _friendly_error("timeout")
            return _friendly_error("connection_failed")
        except Exception:
            return _friendly_error("unknown_error")
    return _friendly_error("unknown_error")


def batch_call(calls: list, api_key: str = None, service_url: str = None):
    """批量MCP调用（安全工具范围内并行执行）"""
    results = []

    def call_one(call):
        tool_name = call.get("tool")
        params = call.get("params", {})
        result = _call_mcp_tool(tool_name, params, api_key, service_url)
        results.append(result)

    threads = []
    for call in calls:
        t = threading.Thread(target=call_one, args=(call,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=60)

    return results


# ============================================================
# 本地回退搜索
# ============================================================
def _web_search(query: str, timeout: int = 10) -> dict:
    results = _local_web_search(query, max_results=5)
    return {"source": "local_search", "query": query, "results": results, "result_count": len(results)}


def _generate_local_answer(question: str, category: str = None) -> dict:
    query = question
    if category:
        query = f"{category} {query}"
    search_result = _web_search(query)
    if search_result.get("error"):
        return {"source": "local_fallback", "status": "search_failed", "question": question,
                "message": "当前处于本地搜索模式，但搜索服务暂时不可用。建议稍后重试或咨询专业税务师。"}
    results = search_result.get("results", [])
    if not results:
        return {"source": "local_fallback", "status": "no_results", "question": question,
                "message": "当前处于本地搜索模式，未找到相关信息。建议稍后重试，或咨询专业税务师。"}
    answer_parts = [f"## 关于「{question}」", "",
                    "⚠️ 当前处于**本地搜索模式**（远程服务暂时不可用），以下内容来自公开财税政策资料：", ""]
    for i, r in enumerate(results):
        answer_parts.append(f"### {i + 1}. {r['title']}")
        if r.get("snippet"):
            answer_parts.append(f"> {r['snippet']}")
        answer_parts.append("")
    answer_parts.extend(["---", "",
                         "> 📌 **提示**：当前为本地搜索模式，信息可能不够完整。",
                         "> 远程MCP服务恢复后会自动切换，届时将获得更精准的政策依据和专业分析。",
                         "> 如需最新政策，建议访问[国家税务总局官网](https://www.chinatax.gov.cn)。"])
    return {"source": "local_fallback", "status": "ok", "question": question,
            "result": "\n".join(answer_parts), "search_query": query, "result_count": len(results)}


# ============================================================
# 对外安全接口（仅 4 个云端安全工具 + 本地兜底）
# ============================================================
def tax_policy_ask(question: str, category: str = None) -> dict:
    """政策问答（含风险应对政策依据）"""
    _load_health_state()
    mode = _get_current_mode()
    if mode == "probe":
        health = _quick_health_check()
        if health.get("healthy"):
            _update_mode(True)
        elif health.get("should_reregister"):
            _update_mode(False)
            config = _load_config()
            _ensure_api_key(config, force_refresh=True)
        else:
            _update_mode(False)
    elif mode == "fallback":
        pass

    cache_key = f"ask:{question}:{category}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = _do_remote_policy_ask(question, category)
    _cache_set(cache_key, result)
    return result


def _do_remote_policy_ask(question: str, category: str = None, _retry_count: int = 0) -> dict:
    config = _load_config()
    service_url = config.get("service_url", _DEFAULT_SERVICE_URL)
    api_key = _ensure_api_key(config)
    if not api_key:
        _log("policy_ask", {"question": question, "status": "no_api_key", "mode": "local"})
        return _generate_local_answer(question, category)
    params = {"question": question}
    if category:
        params["category"] = category
    result = _call_mcp_tool("tax_policy_ask", params, api_key, service_url)
    if "error" in result and "api_key" in str(result.get("error", "")).lower():
        if _retry_count < 1:
            api_key = _ensure_api_key(config, force_refresh=True)
            if api_key:
                return _do_remote_policy_ask(question, category, _retry_count=_retry_count + 1)
        _log("policy_ask", {"question": question, "status": "api_key_invalid", "mode": "local"})
        return _generate_local_answer(question, category)
    if "error" not in result:
        _log("policy_ask", {"question": question, "status": "ok"})
    else:
        _log("policy_ask", {"question": question, "status": "error", "detail": result.get("error")})
        if _get_current_mode() in ["fallback", "probe"]:
            return _generate_local_answer(question, category)
    return result


def risk_check(scenario: str, level_filter: str = None) -> dict:
    """企业税务风险初筛（自然语言 scenario，≤2000 字）"""
    if not isinstance(scenario, str):
        return _friendly_error("scenario_invalid", {"error_code": "InvalidScenarioType"})
    _load_health_state()
    mode = _get_current_mode()
    if mode == "probe":
        health = _quick_health_check()
        if health.get("healthy"):
            _update_mode(True)
        elif health.get("should_reregister"):
            _update_mode(False)
            config = _load_config()
            _ensure_api_key(config, force_refresh=True)
        else:
            _update_mode(False)
    elif mode == "fallback":
        pass

    cache_key = f"risk:{scenario}:{level_filter}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = _do_remote_risk_check(scenario, level_filter)
    _cache_set(cache_key, result)
    return result


def _do_remote_risk_check(scenario: str, level_filter: str = None, _retry_count: int = 0) -> dict:
    config = _load_config()
    service_url = config.get("service_url", _DEFAULT_SERVICE_URL)
    api_key = _ensure_api_key(config)
    if not api_key:
        _log("risk_check", {"scenario": scenario, "status": "no_api_key", "mode": "local"})
        return _generate_local_answer(scenario)
    params = {"scenario": scenario}
    if level_filter:
        params["level_filter"] = level_filter
    result = _call_mcp_tool("risk_check", params, api_key, service_url)
    if result.get("error_code") in ("InvalidScenarioType", "PayloadTooLarge"):
        return _friendly_error("scenario_invalid", {"error_code": result.get("error_code")})
    if "error" in result and "api_key" in str(result.get("error", "")).lower():
        if _retry_count < 1:
            api_key = _ensure_api_key(config, force_refresh=True)
            if api_key:
                return _do_remote_risk_check(scenario, level_filter, _retry_count=_retry_count + 1)
        _log("risk_check", {"scenario": scenario, "status": "api_key_invalid", "mode": "local"})
        return _generate_local_answer(scenario)
    if "error" not in result:
        _log("risk_check", {"scenario": scenario, "status": "ok"})
    else:
        _log("risk_check", {"scenario": scenario, "status": "error", "detail": result.get("error")})
        if _get_current_mode() in ["fallback", "probe"]:
            return _generate_local_answer(scenario)
    return result


def tax_calculate(tax_type: str, params: dict) -> dict:
    """各类税费计算"""
    _load_health_state()
    cache_key = f"calc:{tax_type}:{json.dumps(params, sort_keys=True)}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    result = _do_remote_tax_calculate(tax_type, params)
    if "error" in result and _get_current_mode() in ["fallback", "probe"]:
        return _friendly_error("fallback_active")
    _cache_set(cache_key, result)
    return result


def _do_remote_tax_calculate(tax_type: str, params: dict) -> dict:
    config = _load_config()
    service_url = config.get("service_url", _DEFAULT_SERVICE_URL)
    api_key = _ensure_api_key(config)
    if not api_key:
        return _friendly_error("not_registered")
    payload = {"tax_type": tax_type, "params": params}
    result = _call_mcp_tool("tax_calculate", payload, api_key, service_url)
    if "error" not in result:
        _log("tax_calculate", {"tax_type": tax_type, "status": "ok"})
    else:
        _log("tax_calculate", {"tax_type": tax_type, "status": "error", "detail": result.get("error")})
    return result


def kb_list() -> dict:
    """知识库概览（仅元数据，不回正文）"""
    _load_health_state()
    config = _load_config()
    api_key = _ensure_api_key(config)
    if not api_key:
        return _friendly_error("not_registered")
    service_url = config.get("service_url", _DEFAULT_SERVICE_URL)
    result = _call_mcp_tool("kb_list", {}, api_key, service_url)
    if "error" not in result:
        global _tools_catalog
        tools = result.get("tools")
        if isinstance(tools, list):
            _tools_catalog = {t.get("name"): t for t in tools if isinstance(t, dict)}
        return result
    if _get_current_mode() in ["fallback", "probe"]:
        return _generate_local_answer("知识库列表")
    return result


def get_mode_status() -> dict:
    """查询当前运行模式"""
    _load_health_state()
    return {"mode": _get_current_mode(), "consecutive_failures": _health_state["consecutive_failures"],
            "fallback_count": _health_state["fallback_count"], "last_check_time": _health_state["last_check_time"]}


# ============================================================
# 本地日志（仅记前缀，不记 API Key 明细）
# ============================================================
def _log(action: str, data: dict):
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        today = time.strftime("%Y-%m-%d")
        log_file = os.path.join(_LOG_DIR, f"{today}.jsonl")
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": action, **data}
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    print("=== 财税政策 MCP 客户端（安全收敛版 v4.0.0）===")
    print(f"缓存容量: {_CACHE_TTL}秒")
    config = _load_config()
    print(f"服务地址: {config.get('service_url')}")
    print(f"API Key: {'已配置' if config.get('api_key') else '未配置（首次调用将自动注册）'}")
    print("\n测试模式状态...")
    print(json.dumps(get_mode_status(), ensure_ascii=False, indent=2))
