#!/usr/bin/env python3
"""
PatSeek 专利检索客户端脚本

支持三种检索模式：
1. bool_search — 关键词/号码 Bool 检索（支持 AND/OR 组合、字段前缀）
2. get_patent  — 按公开号/申请号获取专利详情
3. semantic_search_async — 异步语义检索（提交 + 轮询 + 返回结果）

字段前缀: AP=(申请人) IPC=(分类号) PID=(公开号) AN=(申请号) AD/PD=(日期) NOT=(排除)

用法:
  python3 patseek_client.py bool "低空空域 AND 无人机" [--page 1] [--page-size 20]
  python3 patseek_client.py bool "AP=(华为) IPC=(H01M) AD>=2020" [--page-size 10]
  python3 patseek_client.py patent CN118658342A
  python3 patseek_client.py semantic "新能源汽车电池管理系统" [--timeout 180]
  python3 patseek_client.py task <task_id> [--include-partial]
  python3 patseek_client.py cancel <task_id>
  python3 patseek_client.py tasks [--limit 10]
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

# 尝试导入 requests，若无则给出提示
try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库。请运行: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://patseek.cn"

# API Key 优先级: 命令行参数 > 环境变量 PATSEEK_API_KEY
API_KEY = os.environ.get("PATSEEK_API_KEY", "")

# ── 缓存 / 去重 / 节流 配置 ──────────────────────────────────────
# 目标：消灭"短时间内重复调用 + 检索式高度雷同/完全相同"造成的重复扣费与 429。
CACHE_DIR = Path(os.environ.get("PATSEEK_CACHE_DIR", Path.home() / ".cache" / "patseek"))
CALLS_LOG = CACHE_DIR / "calls.log"
CALL_LOG_DISABLED = os.environ.get("PATSEEK_DISABLE_CALL_LOG", "").lower() in {"1", "true", "yes"}

# 各命令缓存有效期（秒）：bool 15min / 增强详情 12h / semantic 60min
CACHE_TTL = {"bool": 900, "patent": 43200, "semantic": 3600}
DUP_WINDOW = 900          # 近似检索式比对时间窗（秒）
DUP_THRESHOLD = 0.72      # Jaccard 相似度阈值，≥ 视为雷同（含"仅加/减一个同义词"这类微调）
MIN_INTERVAL = 1.0        # 同类 API 请求最小间隔（秒），简单节流
BROAD_RESULT_THRESHOLD = 5000
RESULT_CAP_HINT = 10000

# Keep status checks inexpensive for the task service.  A semantic task normally
# completes in seconds; checking too frequently across multiple callers creates
# avoidable load.  Poll at a fixed interval (currently every 20 seconds).
POLL_INTERVALS = ((float("inf"), 20),)


_IPC_GROUP_RE = re.compile(r"(?i)\bIPC\s*([=:])\s*\(([^()]*)\)")
_COMPACT_IPC_RE = re.compile(r"^\s*([A-HY]\d{2}[A-Z])\s*(\d.*)$", re.IGNORECASE)


def normalize_ipc_query(query: str) -> str:
    """Normalize compact IPCs to the indexed form (for example H01M 10/0525).

    Real CN responses store the subclass and main group separated by a space.
    Compact inputs such as H01M10/0525 can otherwise return a false zero.
    """

    def normalize_group(match: re.Match) -> str:
        operator, inner = match.group(1), match.group(2)
        parts = re.split(r"(?i)\s+OR\s+", inner)
        normalized = []
        for part in parts:
            code = part.strip()
            compact = _COMPACT_IPC_RE.match(code)
            if compact:
                code = f"{compact.group(1).upper()} {compact.group(2)}"
            normalized.append(code)
        return f"IPC{operator}({' OR '.join(normalized)})"

    return _IPC_GROUP_RE.sub(normalize_group, query)


def task_poll_interval(elapsed: float) -> int:
    """Return the next semantic-task status polling interval in seconds."""
    for until, interval in POLL_INTERVALS:
        if elapsed < until:
            return interval
    raise AssertionError("poll interval schedule must have a final interval")


# ── 检索式归一化与分词 ──────────────────────────────────────────
_FIELD_PREFIXES = ("AP", "IPC", "PID", "AN", "NOT", "CC")


def canonical_query(q: str) -> str:
    """把检索式归一到规范形式，使"实质相同"的写法命中同一缓存 key。

    处理：折叠空白、字段前缀分隔符 ':'→'='、日期运算符去空格、
    布尔运算符大写、括号内 OR 词排序（(A OR B) ≡ (B OR A)），最后统一小写。
    """
    s = q.strip()
    s = re.sub(r"\s+", " ", s)
    for f in _FIELD_PREFIXES:
        s = re.sub(rf"(?i)\b{f}\s*[:=]\s*", f"{f}=", s)
    s = re.sub(r"\s*(>=|<=|>|<|=)\s*", r"\1", s)
    s = re.sub(r"(?i)\b(and|or|not)\b", lambda m: m.group(1).upper(), s)

    def _sort_paren(m):
        inner = m.group(1)
        if " OR " in inner:
            parts = sorted(p.strip() for p in inner.split(" OR "))
            return "(" + " OR ".join(parts) + ")"
        return m.group(0)

    s = re.sub(r"\(([^()]*)\)", _sort_paren, s)
    return s.lower()


def query_tokens(canonical: str) -> set:
    """提取保留字段语义的 token，避免 AP/IPC/NOT 等不同检索被误判为等价。"""
    s = re.sub(r"[()><=:\"']", " ", canonical)
    s = re.sub(r"(?i)\b(and|or|to)\b", " ", s)
    return {t for t in re.split(r"\s+", s) if t and len(t) > 1}


def _key_fingerprint(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]


def _private_tokens(api_key: str, canonical: str) -> list[str]:
    """用 Key 派生摘要保存 token；支持近似去重但不在日志中落盘技术原文。"""
    salt = _key_fingerprint(api_key)
    return sorted(
        hashlib.sha256(f"{salt}|{token}".encode("utf-8")).hexdigest()[:16]
        for token in query_tokens(canonical)
    )


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ── 缓存读写 ────────────────────────────────────────────────────
def _cache_key(api_key: str, command: str, market: str, page, page_size, canonical: str) -> str:
    raw = f"{api_key}|{command}|{market}|{page}|{page_size}|{canonical}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def load_cache(command: str, key: str, ttl: int):
    p = CACHE_DIR / command / f"{key}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if time.time() - data.get("ts", 0) > ttl:
        return None
    return data.get("payload")


def save_cache(command: str, key: str, payload, query: str) -> None:
    p = CACHE_DIR / command / f"{key}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(
            json.dumps({"ts": time.time(), "query": query, "payload": payload}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[缓存] 写入失败（忽略）: {e}", file=sys.stderr)


# ── 调用日志 / 去重 / 节流 ──────────────────────────────────────
def recent_calls(window: int) -> list:
    if not CALLS_LOG.exists():
        return []
    now = time.time()
    out = []
    try:
        for line in CALLS_LOG.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if now - rec.get("ts", 0) <= window:
                out.append(rec)
    except Exception:
        return []
    return out


def log_call(
    api_key: str,
    command: str,
    market: str,
    canonical: str,
    cached: bool,
    credits,
    page: int = 1,
    disabled: bool = False,
) -> None:
    if disabled or CALL_LOG_DISABLED:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": time.time(),
        "key_fp": _key_fingerprint(api_key),
        "command": command,
        "market": market,
        "page": page,
        "query_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16],
        "tokens": _private_tokens(api_key, canonical),
        "cached": cached,
        "credits": credits or 0,
    }
    try:
        with open(CALLS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def find_near_dup(api_key: str, command: str, market: str, canonical: str, page: int = 1):
    """在时间窗内查找与当前检索式雷同（Jaccard≥阈值）的历史调用。"""
    # 翻页是同一检索的正常后续操作，不进入近似检索拦截。
    if page != 1:
        return None, 0.0
    toks = set(_private_tokens(api_key, canonical))
    key_fp = _key_fingerprint(api_key)
    best = None
    best_sim = 0.0
    for rec in reversed(recent_calls(DUP_WINDOW)):
        if (
            rec.get("key_fp") != key_fp
            or rec.get("command") != command
            or rec.get("market") != market
            or rec.get("page", 1) != 1
        ):
            continue
        previous_tokens = set(rec.get("tokens") or [])
        # 新增 AND 关键特征、IPC、日期或排除条件是有效收窄。隐私日志不保存
        # 原始布尔结构，因此对严格 token 超集保守放行，由结果规模警告继续把关。
        if previous_tokens and previous_tokens < toks:
            continue
        sim = jaccard(toks, previous_tokens)
        if sim >= DUP_THRESHOLD and sim > best_sim:
            best, best_sim = rec, sim
    return best, best_sim


def session_summary(api_key: str, window: int = 3600) -> str:
    """汇总近 1 小时调用次数与累计积分，作为消耗刹车提示。"""
    key_fp = _key_fingerprint(api_key)
    calls = [c for c in recent_calls(window) if c.get("key_fp") == key_fp]
    n = len(calls)
    hits = sum(1 for c in calls if c.get("cached"))
    credits = sum(int(c.get("credits") or 0) for c in calls)
    return f"[会话统计·近1h] 调用 {n} 次（其中缓存命中 {hits} 次·未扣费），累计消耗 {credits} 积分"


def broad_result_warning(total: int) -> str:
    """为过宽 Bool 结果生成可执行的收窄提示。"""
    if total < BROAD_RESULT_THRESHOLD:
        return ""
    cap = "；结果已达到或接近系统显示上限，当前数量不可用于统计" if total >= RESULT_CAP_HINT else ""
    return (
        f"[检索式过宽] 命中 {total} 条{cap}。不要直接把该批结果并入候选池。"
        "先抽样前5-10篇识别噪声，再增加至少一个关键区别特征（结构/步骤关系、"
        "特定部件、控制逻辑或参数），并优先配合已验证IPC或日期后重检。"
    )


def throttle(api_key: str) -> None:
    """同类请求最小间隔节流，避免请求过快触发 429。"""
    key_fp = _key_fingerprint(api_key)
    calls = [c for c in recent_calls(60) if c.get("key_fp") == key_fp]
    if not calls:
        return
    last_api = [c for c in calls if not c.get("cached")]
    if not last_api:
        return
    gap = time.time() - max(c["ts"] for c in last_api)
    if gap < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - gap)


def _request(method: str, url: str, **kwargs):
    """带 429/503 指数退避重试的请求封装。"""
    last = None
    for attempt in range(4):
        resp = requests.request(method, url, **kwargs)
        if resp.status_code in (429, 503) and attempt < 3:
            wait = 2 ** attempt
            print(f"[节流] 收到 {resp.status_code}，{wait}s 后重试（第 {attempt + 1} 次）...", file=sys.stderr)
            time.sleep(wait)
            last = resp
            continue
        resp.raise_for_status()
        return resp
    if last is not None:
        last.raise_for_status()
    return resp


def guard_or_exit(
    api_key: str,
    command: str,
    market: str,
    query: str,
    canonical: str,
    force: bool,
    page: int = 1,
) -> None:
    """执行前去重闸门：命中雷同且未加 --force 则拦截退出。"""
    if force:
        return
    dup, sim = find_near_dup(api_key, command, market, canonical, page=page)
    if dup:
        ago = int(time.time() - dup.get("ts", 0))
        print(f"[去重拦截] 与 {ago}s 前的一次 {command} 检索高度相似（相似度 {sim:.0%}），已阻断以免重复扣费。", file=sys.stderr)
        print(f"  上次检索摘要: {dup.get('query_hash', 'N/A')}（技术原文未写入日志）", file=sys.stderr)
        print(f"  本次检索: {query}", file=sys.stderr)
        print("  处理建议:", file=sys.stderr)
        print("    · 想看更多结果 → 用 --page 翻页，不要重跑整条检索", file=sys.stderr)
        print("    · 确需重复执行 → 加 --force 强制运行", file=sys.stderr)
        print("    · 想换角度 → 调整检索式后再执行", file=sys.stderr)
        sys.exit(2)


def get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def bool_search(
    api_key: str, query: str, page: int = 1, page_size: int = 20, market: str = "cn"
) -> dict:
    """Bool 检索，支持 AND/OR 逻辑组合、字段前缀（AP/IPC/PID/AN/AD/PD/NOT）

    market: "cn"（默认，中国专利）| "world"（国际/外文专利，如美国、欧洲、日本、韩国、PCT 等）
    两个库接受相同表面语法，但底层字段映射/分析器可能不同，需分别抽样验证。
    """
    # The space-normalized main-group form is verified for the CN index only.
    # World index storage can differ, so preserve the user's independently
    # preflighted compact/space form rather than silently converting it.
    if market == "cn":
        query = normalize_ipc_query(query)
    resp = _request(
        "POST",
        f"{BASE_URL}/v1/search",
        headers=get_headers(api_key),
        json={"query": query, "page": page, "page_size": page_size, "market": market},
        timeout=30,
    )
    return resp.json()


def get_patent(
    api_key: str,
    identifier: str,
    market: str = "cn",
    include_enrichment: bool = True,
) -> dict:
    """按公开号或申请号获取单条专利详情及可选增强摘要。

    market: "cn"（默认，中国专利）| "world"（国际/外文专利）
    """
    normalized_identifier = identifier.strip().upper()
    encoded_identifier = urllib.parse.quote(normalized_identifier, safe=".-")
    resp = _request(
        "GET",
        f"{BASE_URL}/v1/patent/{encoded_identifier}",
        headers=get_headers(api_key),
        params={
            "market": market,
            "include_enrichment": str(include_enrichment).lower(),
        },
        timeout=30,
    )
    return resp.json()


def get_key_info(api_key: str) -> dict:
    """查询当前 API Key 的类型、权限、有效期与本地余额。"""
    resp = _request(
        "GET",
        f"{BASE_URL}/v1/key-info",
        headers=get_headers(api_key),
        timeout=30,
    )
    return resp.json()


def semantic_search_async_submit(api_key: str, query: str) -> dict:
    """提交异步语义检索任务，返回 task_id 等信息"""
    resp = _request(
        "POST",
        f"{BASE_URL}/v1/semantic/async",
        headers=get_headers(api_key),
        json={"query": query},
        timeout=30,
    )
    return resp.json()


def query_task(api_key: str, task_id: str, include_partial: bool = False) -> dict:
    """查询异步任务状态/结果"""
    params = {}
    if include_partial:
        params["include_partial"] = "true"
    resp = _request(
        "GET",
        f"{BASE_URL}/v1/tasks/{task_id}",
        headers=get_headers(api_key),
        params=params,
        timeout=30,
    )
    return resp.json()


def cancel_task(api_key: str, task_id: str) -> dict:
    """取消正在运行的异步任务"""
    resp = _request(
        "DELETE",
        f"{BASE_URL}/v1/tasks/{task_id}",
        headers=get_headers(api_key),
        timeout=30,
    )
    return resp.json()


def list_tasks(api_key: str, limit: int = 20) -> dict:
    """列出任务历史"""
    resp = _request(
        "GET",
        f"{BASE_URL}/v1/tasks",
        headers=get_headers(api_key),
        params={"limit": limit},
        timeout=30,
    )
    return resp.json()


def _print_credits(data: dict) -> None:
    """打印积分消耗信息（从 API 响应中提取）"""
    charged = data.get("credits_charged", 0)
    remaining = data.get("credits_remaining", None)
    if remaining is not None:
        print(f"[积分] 本次消耗: {charged}, 剩余: {remaining}", file=sys.stderr)


# ── 附图处理辅助函数 ──────────────────────────────────────────

def parse_figures(p: dict) -> list[dict]:
    """从专利数据中解析附图，返回 [{"url": ..., "label": ...}, ...]；空列表表示无附图
    
    支持两种格式：
    1. Google 专利图片 URL 列表（换行分隔）
       → 直接作为 URL，标签自动编号
    2. xinxin.chat 格式（分号分隔的 label:filename 对）
       例 "None:202610332006.JPG;图1:FT_1.JPG;图2:FT_2.JPG"
       → label "None" 替换为空，filename 补全为 https://xinxin.chat/view/<filename>
    """
    raw = p.get("figures", "")
    if not raw or not isinstance(raw, str) or not raw.strip():
        return []
    
    raw_stripped = raw.strip()
    
    # ── 格式判断 ──
    # xinxin 格式特征：包含分号分隔符，且至少有一个 ":" 出现在分号之前
    if ";" in raw_stripped:
        entries = [e.strip() for e in raw_stripped.split(";") if e.strip()]
        # 当以 "None" 开头时，仅第一张图片有效，后续条目忽略
        if entries and entries[0].startswith("None:"):
            entries = entries[:1]
        results = []
        for entry in entries:
            if ":" in entry:
                label, filename = entry.split(":", 1)
                label = label.strip()
                filename = filename.strip()
                url = f"https://xinxin.chat/view/{filename}"
                # "None" 标签表示无特定图号，使用"主图"标记
                if label.lower() == "none":
                    label = "主图"
            else:
                filename = entry.strip()
                url = f"https://xinxin.chat/view/{filename}"
                label = ""
            results.append({"url": url, "label": label})
        return results
    
    # Google 专利图片格式（换行分隔的 URL）
    urls = [u.strip() for u in raw_stripped.split("\n") if u.strip()]
    results = []
    for i, u in enumerate(urls, 1):
        parsed = urllib.parse.urlparse(u)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            results.append({"url": u, "label": f"图{i}"})
    return results


def download_figure(fig: dict, save_dir: str, index: int) -> str | None:
    """下载单张附图到指定目录，返回本地文件路径；失败返回 None"""
    url = fig.get("url", "")
    if not url:
        return None
    try:
        # 尝试从 URL 中提取原始扩展名
        parsed = urllib.parse.urlparse(url)
        path_part = parsed.path
        filename_base = os.path.basename(path_part)
        if not filename_base or "." not in filename_base:
            filename = f"{index:02d}.png"
        else:
            ext = os.path.splitext(filename_base)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
                ext = ".png"
            filename = f"{index:02d}{ext}"
        filepath = os.path.join(save_dir, filename)
        if os.path.exists(filepath):
            return filepath
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath
    except Exception as e:
        print(f"  附图 {index} 下载失败: {e}", file=sys.stderr)
        return None


def download_all_figures(patent: dict, save_dir: str) -> list[str]:
    """下载专利所有附图，返回本地文件路径列表"""
    figures = parse_figures(patent)
    if not figures:
        return []
    os.makedirs(save_dir, exist_ok=True)
    saved = []
    for i, fig in enumerate(figures, 1):
        path = download_figure(fig, save_dir, i)
        if path:
            saved.append(path)
    return saved


# ── 格式化输出辅助函数 ──────────────────────────────────────────

def _format_figures_text(p: dict, indent: str = "") -> str:
    """格式化附图信息文本"""
    figures = parse_figures(p)
    if not figures:
        return f"{indent}附图:   无"
    lines = [f"{indent}附图:   {len(figures)} 张"]
    for i, fig in enumerate(figures, 1):
        label = fig.get("label", f"图{i}")
        url = fig.get("url", "")
        lines.append(f"{indent}        [{i}] {label}: {url}")
    return "\n".join(lines)


def semantic_search_async(api_key: str, query: str, timeout: int = 180) -> list:
    """
    异步语义检索完整流程：提交 -> 轮询 -> 返回结果列表

    轮询策略:
      全程每 20 秒查询一次
    """
    # 1. 提交任务
    submit_data = semantic_search_async_submit(api_key, query)
    task_id = submit_data["task_id"]
    status = submit_data["status"]
    print(json.dumps(submit_data, ensure_ascii=False), file=sys.stderr)

    # 如果缓存命中，直接返回
    if status == "succeeded":
        task_data = query_task(api_key, task_id)
        return task_data.get("result", [])

    # 2. 轮询
    elapsed = 0
    task_data = {}
    while elapsed < timeout:
        interval = task_poll_interval(elapsed)
        time.sleep(interval)
        elapsed += interval

        task_data = query_task(api_key, task_id, include_partial=True)
        status = task_data["status"]
        received = task_data.get("progress", {}).get("received", 0)
        print(
            f"  [{elapsed}s] status={status}, received={received}",
            file=sys.stderr,
        )

        if status == "succeeded":
            return task_data.get("result", [])
        elif status in ("failed", "cancelled"):
            # 关键：上游任务失败绝不能静默返回 []（会被误读为"0 命中/未检出现有技术"）。
            # 抛出异常，让调用方（如 patseek_adapter）以非零退出码明确失败。
            err = task_data.get("error")
            print(f"任务终止: {err}", file=sys.stderr)
            raise RuntimeError(f"语义检索任务{status}: {err}")

    # 轮询超时同样不能静默返回 []。附带已收到的部分结果数量，便于调用方决定是否放宽 timeout / 收窄检索式。
    partial = task_data.get("progress", {}).get("received", 0)
    print("轮询超时", file=sys.stderr)
    raise TimeoutError(f"语义检索轮询超时（{timeout}s，已收到部分结果约 {partial} 条，未完成即视为失败）")


# ── 格式化输出辅助函数 ──────────────────────────────────────────

def format_patent_brief(p: dict, show_figures: bool = False) -> str:
    """格式化单条专利的简要信息（Bool 检索结果）"""
    lines = [
        f"公开号: {p.get('pid', 'N/A')}",
        f"申请号: {p.get('appnum', 'N/A')}",
        f"名称:   {p.get('title', 'N/A')}",
        f"申请人: {p.get('applicant', 'N/A')}",
        f"IPC:    {p.get('ipcs', 'N/A')}",
        f"申请日: {p.get('appdate', 'N/A')}  公开日: {p.get('pubdate', 'N/A')}",
    ]
    abstract = p.get("abstract", "")
    if abstract:
        lines.append(f"摘要:   {abstract[:200]}{'...' if len(abstract) > 200 else ''}")
    if show_figures:
        lines.append(_format_figures_text(p, indent=""))
    return "\n".join(lines)


def format_enrichment_summary(p: dict) -> str:
    """格式化备用详情源提供的常用增强摘要；兼容旧 API 无此字段的响应。"""
    enrichment = p.get("enrichment") or {}
    aggregation = p.get("aggregation") or {}
    status = aggregation.get("status")
    if not enrichment:
        if status == "primary_only":
            return "扩展信息: 暂不可用（基础专利详情已正常返回）"
        if status == "identity_mismatch":
            return "扩展信息: 数据源身份不一致，已安全忽略"
        return ""

    lines = ["扩展信息:"]
    inventors = enrichment.get("inventors") or []
    if inventors:
        lines.append(f"  发明人: {', '.join(inventors)}")
    if enrichment.get("priority_date"):
        lines.append(f"  优先权日: {enrichment['priority_date']}")
    if enrichment.get("legal_status"):
        lines.append(f"  法律状态: {enrichment['legal_status']}")
    latest_event = enrichment.get("latest_legal_event") or {}
    if latest_event:
        event_text = " ".join(
            str(value) for value in (
                latest_event.get("date"),
                latest_event.get("code"),
                latest_event.get("title"),
            ) if value
        )
        if event_text:
            lines.append(f"  最新事件: {event_text}")
    lines.append(
        "  关系摘要: "
        f"同族 {enrichment.get('family_count', 0)} / "
        f"引用 {enrichment.get('citation_count', 0)} / "
        f"被引 {enrichment.get('cited_by_count', 0)} / "
        f"相似 {enrichment.get('similar_count', 0)}"
    )
    if enrichment.get("pdf_url"):
        lines.append(f"  PDF: {enrichment['pdf_url']}")
    if enrichment.get("canonical_url"):
        lines.append(f"  来源页: {enrichment['canonical_url']}")
    if status:
        cached = "，缓存命中" if aggregation.get("enrichment_cached") else ""
        lines.append(f"  聚合状态: {status}{cached}")
    return "\n".join(lines)


def format_semantic_patent_brief(p: dict, show_figures: bool = False) -> str:
    """格式化单条语义检索专利的简要信息"""
    lines = [
        f"公开号:   {p.get('pid', 'N/A')}",
        f"相似度:   {p.get('similarity', 'N/A')}",
        f"名称:     {p.get('title', 'N/A')}",
        f"申请人:   {p.get('applicant', 'N/A')}",
        f"IPC:      {p.get('ipcs', 'N/A')}",
        f"申请日:   {p.get('appdate', 'N/A')}  公开日: {p.get('pubdate', 'N/A')}",
    ]
    abstract = p.get("abstract", "")
    if abstract:
        lines.append(f"摘要:     {abstract[:200]}{'...' if len(abstract) > 200 else ''}")
    if show_figures:
        lines.append(_format_figures_text(p, indent="  "))
    return "\n".join(lines)


# ── CLI 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PatSeek 专利检索客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Bool 关键词检索
  python3 patseek_client.py bool "低空空域 AND 无人机" --page-size 5

  # Bool 检索 + 显示附图 URL
  python3 patseek_client.py bool "固态电池" --show-figures --page-size 3

  # Bool 检索 + 下载附图
  python3 patseek_client.py bool "固态电池" --figures-dir ./patent_images --page-size 3

  # 申请人限定
  python3 patseek_client.py bool "AP=(华为) 5G" --page-size 10

  # IPC + 日期
  python3 patseek_client.py bool "IPC=(H01M) AD>=2020" --page-size 10

  # 组合检索
  python3 patseek_client.py bool "AP=(比亚迪) IPC=(H01M) AD>=2020 NOT=(液态)"

  # 检索国际/外文专利（表面语法相同，结果需单独抽样验证）
  python3 patseek_client.py bool "battery management system" --market world --page-size 5

  # 限定国家/地区（仅 world 库支持，用 CC=() 前缀）
  python3 patseek_client.py bool "battery management system CC=(US)" --market world --page-size 5
  python3 patseek_client.py bool "battery management system CC=(US OR EP)" --market world --page-size 5

  # 按公开号获取专利详情（默认含发明人、法律状态、同族与引证摘要）
  python3 patseek_client.py patent CN118658342A --show-figures

  # 仅获取原有 Bool 主数据源详情
  python3 patseek_client.py patent CN118658342A --no-enrichment

  # 按公开号获取专利详情 + 下载附图
  python3 patseek_client.py patent CN114824336A --figures-dir ./figures

  # 异步语义检索
  python3 patseek_client.py semantic "新能源汽车电池管理系统"

  # 查询当前 API Key 的权限、有效期与余额
  python3 patseek_client.py key-info

  # 查询任务状态
  python3 patseek_client.py task <task_id>

  # 取消任务
  python3 patseek_client.py cancel <task_id>

  # 列出任务历史
  python3 patseek_client.py tasks --limit 5
        """,
    )
    parser.add_argument(
        "--api-key",
        default=API_KEY,
        help="PatSeek API Key (或设置环境变量 PATSEEK_API_KEY)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="跳过本地缓存，强制请求 API（仍会写入缓存与调用日志）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="跳过近似检索式去重拦截，强制执行本次检索",
    )
    parser.add_argument(
        "--no-call-log",
        action="store_true",
        help="不写入本地调用统计日志（缓存仍可正常使用）",
    )

    def add_common_subcommand_args(subparser):
        """允许公共参数写在子命令之前或之后，且不覆盖主解析器已经取得的值。"""
        subparser.add_argument("--api-key", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        subparser.add_argument("--no-cache", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        subparser.add_argument("--force", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        subparser.add_argument("--no-call-log", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command", required=True)

    # bool 子命令
    bool_parser = subparsers.add_parser("bool", help="Bool 检索（支持 AND/OR、字段前缀 AP/IPC/PID/AN/AD/PD/NOT）")
    add_common_subcommand_args(bool_parser)
    bool_parser.add_argument("query", help='检索表达式，如 "AP=(华为) IPC=(H01M) AD>=2020"')
    bool_parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    bool_parser.add_argument("--page-size", type=int, default=20, help="每页条数 1-100 (默认 20)")
    bool_parser.add_argument(
        "--market", choices=["cn", "world"], default="cn",
        help="专利库: cn=中国专利(默认), world=国际/外文专利(美国/欧洲/日本/韩国/PCT等)",
    )
    bool_parser.add_argument("--show-figures", action="store_true", help="显示附图 URL")
    bool_parser.add_argument("--figures-dir", default=None, help="下载附图到此目录")

    # patent 子命令
    patent_parser = subparsers.add_parser("patent", help="按公开号/申请号获取专利详情")
    add_common_subcommand_args(patent_parser)
    patent_parser.add_argument("identifier", help="公开号或申请号，如 CN118658342A")
    patent_parser.add_argument(
        "--market", choices=["cn", "world"], default="cn",
        help="专利库: cn=中国专利(默认), world=国际/外文专利",
    )
    patent_parser.add_argument("--show-figures", action="store_true", help="显示附图 URL")
    patent_parser.add_argument("--figures-dir", default=None, help="下载附图到此目录")
    patent_parser.add_argument(
        "--no-enrichment",
        action="store_true",
        help="仅返回主 Bool 数据源详情，不调用备用详情增强",
    )

    # semantic 子命令
    semantic_parser = subparsers.add_parser("semantic", help="异步语义检索")
    add_common_subcommand_args(semantic_parser)
    semantic_parser.add_argument("query", help="技术方案或技术问题描述")
    semantic_parser.add_argument("--timeout", type=int, default=180, help="轮询超时秒数 (默认 180)")

    # key-info 子命令
    key_info_parser = subparsers.add_parser("key-info", help="查询当前 API Key 的权限、有效期与余额")
    add_common_subcommand_args(key_info_parser)

    # task 子命令
    task_parser = subparsers.add_parser("task", help="查询异步任务状态/结果")
    add_common_subcommand_args(task_parser)
    task_parser.add_argument("task_id", help="任务 ID")
    task_parser.add_argument("--include-partial", action="store_true", help="是否返回运行中的部分结果")

    # cancel 子命令
    cancel_parser = subparsers.add_parser("cancel", help="取消异步任务")
    add_common_subcommand_args(cancel_parser)
    cancel_parser.add_argument("task_id", help="任务 ID")

    # tasks 子命令
    tasks_parser = subparsers.add_parser("tasks", help="列出任务历史")
    add_common_subcommand_args(tasks_parser)
    tasks_parser.add_argument("--limit", type=int, default=20, help="返回条数 1-100 (默认 20)")

    args = parser.parse_args()

    if not args.api_key:
        print("错误: 未提供 PatSeek API Key", file=sys.stderr)
        print("", file=sys.stderr)
        print("请通过以下方式之一提供 API Key：", file=sys.stderr)
        print("  1. 设置环境变量：export PATSEEK_API_KEY=ps_你的Key", file=sys.stderr)
        print("  2. 使用 --api-key 参数：python3 patseek_client.py --api-key ps_你的Key ...", file=sys.stderr)
        print("", file=sys.stderr)
        print("如何获取 API Key？", file=sys.stderr)
        print("  → 访问 https://patseek.cn 注册登录", file=sys.stderr)
        print("  → 进入「个人中心 → API Key 管理」创建新 Key", file=sys.stderr)
        print("  → Key 格式示例：ps_加32位十六进制字符", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "key-info":
            result = get_key_info(args.api_key)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "bool":
            show_figs = getattr(args, "show_figures", False)
            figs_dir = getattr(args, "figures_dir", None)
            market = getattr(args, "market", "cn")
            effective_query = normalize_ipc_query(args.query) if market == "cn" else args.query
            canonical = canonical_query(effective_query)
            key = _cache_key(args.api_key, "bool", market, args.page, args.page_size, canonical)
            result = None
            from_cache = False
            if not args.no_cache:
                cached = load_cache("bool", key, CACHE_TTL["bool"])
                if cached is not None:
                    result = cached
                    from_cache = True
                    print("[缓存命中·未扣积分] 返回近 15 分钟内的相同检索结果（如需最新数据加 --no-cache）\n", file=sys.stderr)
            if result is None:
                if not args.no_cache:
                    guard_or_exit(args.api_key, "bool", market, args.query, canonical, args.force, page=args.page)
                throttle(args.api_key)
                result = bool_search(args.api_key, effective_query, args.page, args.page_size, market)
                save_cache("bool", key, result, effective_query)
            log_call(
                args.api_key, "bool", market, canonical, from_cache,
                result.get("credits_charged", 0) if not from_cache else 0,
                page=args.page, disabled=args.no_call_log,
            )
            market_label = " [World 国际专利库]" if market == "world" else ""
            print(f"检索结果{market_label}: 共 {result['total']} 条, 第 {result['current_page']}/{result['total_pages']} 页\n")
            warning = broad_result_warning(int(result.get("total", 0)))
            if warning:
                print(warning, file=sys.stderr)
            for i, p in enumerate(result.get("patent_list", []), 1):
                print(f"--- 第 {i} 条 ---")
                print(format_patent_brief(p, show_figures=show_figs))
                if figs_dir:
                    patent_figs_dir = os.path.join(figs_dir, p.get("pid", f"patent_{i}"))
                    saved = download_all_figures(p, patent_figs_dir)
                    if saved:
                        print(f"  附图已下载至: {patent_figs_dir} ({len(saved)} 张)")
                print()
            if not from_cache:
                _print_credits(result)
            if not args.no_call_log and not CALL_LOG_DISABLED:
                print(session_summary(args.api_key), file=sys.stderr)

        elif args.command == "patent":
            show_figs = getattr(args, "show_figures", False)
            figs_dir = getattr(args, "figures_dir", None)
            market = getattr(args, "market", "cn")
            include_enrichment = not getattr(args, "no_enrichment", False)
            canonical = args.identifier.strip().upper()
            cache_variant = f"{canonical}|enrichment={str(include_enrichment).lower()}|schema=v2"
            key = _cache_key(args.api_key, "patent", market, 0, 0, cache_variant)
            result = None
            from_cache = False
            if not args.no_cache:
                cached = load_cache("patent", key, CACHE_TTL["patent"])
                if cached is not None:
                    result = cached
                    from_cache = True
                    print("[缓存命中·未扣积分] 返回近 12 小时内的相同专利详情（如需最新数据加 --no-cache）\n", file=sys.stderr)
            if result is None:
                throttle(args.api_key)
                result = get_patent(
                    args.api_key,
                    args.identifier,
                    market,
                    include_enrichment=include_enrichment,
                )
                save_cache("patent", key, result, args.identifier)
            log_call(
                args.api_key, "patent", market, canonical, from_cache,
                result.get("credits_charged", 0) if not from_cache else 0,
                disabled=args.no_call_log,
            )
            patents = result.get("patent_list", [])
            if not patents:
                print(f"未找到专利: {args.identifier}")
            else:
                p = patents[0]
                print(f"公开号:   {p.get('pid', 'N/A')}")
                print(f"申请号:   {p.get('appnum', 'N/A')}")
                print(f"名称:     {p.get('title', 'N/A')}")
                print(f"申请人:   {p.get('applicant', 'N/A')}")
                print(f"IPC:      {p.get('ipcs', 'N/A')}")
                print(f"申请日:   {p.get('appdate', 'N/A')}")
                print(f"公开日:   {p.get('pubdate', 'N/A')}")
                print(f"被引次数: {p.get('cited_cnt', 'N/A')}")
                print(f"\n摘要:\n{p.get('abstract', 'N/A')}")
                print(f"\n权利要求:\n{p.get('claims', 'N/A')}")
                description = p.get("description") or ""
                print(f"\n说明书:\n{description[:2000] or 'N/A'}{'...' if len(description) > 2000 else ''}")
                enrichment_summary = format_enrichment_summary(p)
                if enrichment_summary:
                    print(f"\n{enrichment_summary}")
                if show_figs:
                    print(f"\n{_format_figures_text(p)}")
                if figs_dir:
                    patent_figs_dir = os.path.join(figs_dir, p.get("pid", args.identifier))
                    saved = download_all_figures(p, patent_figs_dir)
                    if saved:
                        print(f"\n附图已下载至: {patent_figs_dir} ({len(saved)} 张)")
            if not from_cache:
                _print_credits(result)
            if not args.no_call_log and not CALL_LOG_DISABLED:
                print(session_summary(args.api_key), file=sys.stderr)

        elif args.command == "semantic":
            canonical = canonical_query(args.query)
            key = _cache_key(args.api_key, "semantic", "cn", 0, 0, canonical)
            results = None
            from_cache = False
            if not args.no_cache:
                cached = load_cache("semantic", key, CACHE_TTL["semantic"])
                if cached is not None:
                    results = cached
                    from_cache = True
                    print("[缓存命中·未扣积分] 返回近 60 分钟内的相同语义检索结果（如需最新数据加 --no-cache）", file=sys.stderr)

            if results is None:
                if not args.no_cache:
                    guard_or_exit(args.api_key, "semantic", "cn", args.query, canonical, args.force)
                throttle(args.api_key)
            # 语义检索：提交时打印积分信息
            submit_charged = 0
            if results is None:
                submit_data = semantic_search_async_submit(args.api_key, args.query)
                print(json.dumps(submit_data, ensure_ascii=False), file=sys.stderr)
                _print_credits(submit_data)
                submit_charged = submit_data.get("credits_charged", 0) or 0
                task_id = submit_data["task_id"]
                status = submit_data["status"]

                if status == "succeeded":
                    task_data = query_task(args.api_key, task_id)
                    results = task_data.get("result", [])
                else:
                    # 轮询
                    elapsed = 0
                    while elapsed < args.timeout:
                        interval = task_poll_interval(elapsed)
                        time.sleep(interval)
                        elapsed += interval
                        task_data = query_task(args.api_key, task_id, include_partial=True)
                        status = task_data["status"]
                        received = task_data.get("progress", {}).get("received", 0)
                        print(f"  [{elapsed}s] status={status}, received={received}", file=sys.stderr)
                        if status == "succeeded":
                            results = task_data.get("result", [])
                            break
                        elif status in ("failed", "cancelled"):
                            raise RuntimeError(f"语义检索任务{status}: {task_data.get('error') or '未提供原因'}")
                    else:
                        raise TimeoutError(f"语义检索轮询超时（{args.timeout}s），不能将失败解释为 0 条结果")

                # 仅在成功且有结果时写入缓存，避免把失败/超时的空结果缓存住
                if results:
                    save_cache("semantic", key, results, args.query)

            log_call(
                args.api_key, "semantic", "cn", canonical, from_cache,
                0 if from_cache else submit_charged, disabled=args.no_call_log,
            )
            print(f"\n语义检索完成，共 {len(results)} 条结果\n")
            for i, p in enumerate(results[:20], 1):
                print(f"--- 第 {i} 条 (相似度 {p.get('similarity', 'N/A')}%) ---")
                print(format_semantic_patent_brief(p))
                print()
            if len(results) > 20:
                print(f"... 还有 {len(results) - 20} 条结果未显示")
            if not args.no_call_log and not CALL_LOG_DISABLED:
                print(session_summary(args.api_key), file=sys.stderr)

        elif args.command == "task":
            result = query_task(args.api_key, args.task_id, args.include_partial)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "cancel":
            result = cancel_task(args.api_key, args.task_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "tasks":
            result = list_tasks(args.api_key, args.limit)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "account":
            result = get_account(args.api_key)
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except requests.exceptions.HTTPError as e:
        resp = e.response
        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print(f"HTTP 错误 {status}: {body}", file=sys.stderr)
        if status == 401:
            print("", file=sys.stderr)
            print("提示: API Key 无效或已过期", file=sys.stderr)
            print("  → 请访问 https://patseek.cn 登录后检查 Key 状态", file=sys.stderr)
            print("  → 或在「个人中心 → API Key 管理」中重新创建 Key", file=sys.stderr)
        elif status == 402:
            print("", file=sys.stderr)
            print("提示: 积分不足，无法完成本次请求", file=sys.stderr)
            print("  → 请访问 https://patseek.cn 登录后充值积分", file=sys.stderr)
            print("  → 或在「个人中心」查看积分余额", file=sys.stderr)
        elif status == 403:
            print("", file=sys.stderr)
            print("提示: 该 API Key 已被禁用", file=sys.stderr)
            print("  → 请访问 https://patseek.cn 联系平台管理员", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("请求超时", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("连接失败，请检查网络", file=sys.stderr)
        sys.exit(1)
    except (TimeoutError, RuntimeError) as e:
        print(f"任务失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
