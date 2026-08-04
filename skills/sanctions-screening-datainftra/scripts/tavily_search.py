#!/usr/bin/env python3
"""
制裁情报搜索模块 — 基于 Tavily API
用途：实时搜索全球制裁新闻、执法动态、合规趋势
纯线上查询，无需本地数据维护
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# 自动加载 .env 文件中的 API Key
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from env_loader import load_dotenv
load_dotenv()


TAVILY_API_URL = "https://api.tavily.com/search"

# 预设搜索模板
SEARCH_TEMPLATES = {
    "entity_sanctions": '"{entity}" sanctions OR sanctioned OR designated OR blacklisted',
    "entity_ofac": '"{entity}" OFAC SDN list OR specially designated nationals',
    "entity_eu": '"{entity}" EU sanctions OR EEAS restrictive measures',
    "entity_un": '"{entity}" UN Security Council sanctions',
    "entity_uk": '"{entity}" UK sanctions OFSI',
    "entity_export_control": '"{entity}" export control OR dual-use OR EAR OR ITAR',
    "entity_china": '"{entity}" 制裁 OR 出口管制 OR 不可靠实体清单',
    "daily_intel": "sanctions news enforcement action {date}",
    "policy_update": "sanctions policy update new designation {region} {date}",
}

# 高权威制裁信息源域名（28源体系）
TRUSTED_DOMAINS = [
    # 官方政府
    "treasury.gov", "sanctionssearch.ofac.treas.gov",
    "eeas.europa.eu", "un.org", "scsanctions.un.org",
    "gov.uk", "sanctionslist.fcdo.gov.uk",
    "dfat.gov.au", "international.gc.ca", "mof.go.jp",
    # 开源/商业数据库
    "opensanctions.org", "castellum.ai", "sanctions.io",
    # 律所/咨询
    "whitecase.com", "cliffordchance.com", "steptoe.com", "jdsupra.com",
    # 研究智库
    "csis.org", "carnegieendowment.org", "piie.com",
    "atlanticcouncil.org", "chathamhouse.org",
    # 金融/新闻
    "lseg.com", "moodys.com", "bloomberg.com",
    "reuters.com", "insurancejournal.com", "kyivindependent.com",
]


def get_api_keys() -> list:
    """从环境变量获取 Tavily API Key 列表（支持多 key 自动轮换）"""
    keys_str = os.environ.get("TAVILY_API_KEYS", "")
    if keys_str:
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        if keys:
            return keys
    key = os.environ.get("TAVILY_API_KEY", "")
    if key:
        return [key]
    print("错误：未设置 TAVILY_API_KEYS 或 TAVILY_API_KEY 环境变量", file=sys.stderr)
    sys.exit(1)


_current_key_index = 0


def get_api_key() -> str:
    """获取当前使用的 API Key（兼容旧调用方式）"""
    keys = get_api_keys()
    return keys[_current_key_index % len(keys)]


def verify_url(url, timeout=5):
    """
    验证 URL 是否有效（HEAD 请求检查，不下载完整内容）。
    返回 True 如果 URL 可访问（2xx/3xx），False 如果 404 或超时。
    """
    if not url:
        return False
    try:
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except urllib.error.HTTPError as e:
        return e.code < 400  # 3xx 重定向也算有效
    except Exception:
        return False


def verify_results(results, max_verify=15):
    """
    验证搜索结果中的 URL 是否可访问，过滤掉 404 的。
    为了速度，最多验证 max_verify 条。
    """
    if not results:
        return results
    verified = []
    for r in results:
        if len(verified) >= max_verify:
            break
        url = r.get("url", "")
        if url and verify_url(url):
            r["url_verified"] = True
            verified.append(r)
        else:
            print(f"  [SKIP] URL not accessible: {url[:80]}", file=sys.stderr)
    return verified


def _is_quota_error(status_code: int, body: str) -> bool:
    """判断是否为配额耗尽/限流错误"""
    if status_code in (429, 402, 403):
        return True
    lower = body.lower()
    return any(kw in lower for kw in ("rate limit", "quota", "exceeded", "limit reached", "usage limit"))


def tavily_search(
    query: str,
    max_results: int = 10,
    search_depth: str = "advanced",
    include_domains: list = None,
    topic: str = "news",
    days: int = 30,
) -> dict:
    """
    调用 Tavily API 执行搜索（支持多 key 自动轮换）

    参数:
        query: 搜索查询文本
        max_results: 最大返回结果数（默认10）
        search_depth: 搜索深度，'basic' 或 'advanced'
        include_domains: 限制搜索的域名列表
        topic: 搜索主题，'general' 或 'news'
        days: 搜索时间范围（天），仅 topic='news' 时生效
    返回:
        Tavily API 响应字典
    """
    global _current_key_index
    api_keys = get_api_keys()
    last_error = None

    for attempt in range(len(api_keys)):
        key_idx = (_current_key_index + attempt) % len(api_keys)
        api_key = api_keys[key_idx]

        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "topic": topic,
        }
        if topic == "news" and days:
            payload["days"] = days
        if include_domains:
            payload["include_domains"] = include_domains

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            TAVILY_API_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                _current_key_index = key_idx
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if _is_quota_error(e.code, body) and attempt < len(api_keys) - 1:
                print(f"  [Tavily] Key #{key_idx+1} 配额耗尽，切换到下一个 key...", file=sys.stderr)
                continue
            last_error = f"HTTP {e.code}: {body}"
            break
        except urllib.error.URLError as e:
            last_error = f"网络错误: {e}"
            break
        except Exception as e:
            last_error = f"未知错误: {e}"
            break

    if last_error and _is_quota_error(0, last_error):
        _current_key_index = (_current_key_index + 1) % len(api_keys)

    return {"error": last_error or "所有 API key 均已耗尽", "results": []}


def search_entity_sanctions(entity_name: str, max_results: int = 10) -> dict:
    """搜索特定实体的全球制裁信息（多轮搜索覆盖不同法域）"""
    # 注入当前日期到查询中，提升时效性
    today = datetime.now()
    date_hint = today.strftime("%Y")  # 只加年份，避免限制太窄
    results = {
        "entity": entity_name,
        "timestamp": today.isoformat(),
        "searches": [],
    }
    # 所有轮次统一用 topic='news' 确保返回 published_date
    search_configs = [
        ("general_sanctions", "entity_sanctions", {"max_results": max_results, "days": 180}),
        ("ofac", "entity_ofac", {"max_results": 5, "days": 365}),
        ("eu_sanctions", "entity_eu", {"max_results": 5, "days": 365}),
        ("un_sanctions", "entity_un", {"max_results": 5, "days": 365}),
        ("uk_sanctions", "entity_uk", {"max_results": 5, "days": 365}),
        ("export_control", "entity_export_control", {"max_results": 5, "days": 365}),
        ("china_sanctions", "entity_china", {"max_results": 5, "days": 365}),
    ]
    for search_type, template_key, kwargs in search_configs:
        query = SEARCH_TEMPLATES[template_key].format(entity=entity_name)
        # 给首轮搜索注入年份提升时效性
        if search_type == "general_sanctions":
            query = f"{query} {date_hint}"
        resp = tavily_search(query, topic="news", **kwargs)
        results["searches"].append({
            "type": search_type,
            "query": query,
            "results": resp.get("results", []),
            "error": resp.get("error"),
        })
    return results


def search_daily_intel(date: str = None, region: str = "global", max_results: int = 15) -> dict:
    """获取每日制裁情报摘要"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    results = {
        "date": date, "region": region,
        "timestamp": datetime.now().isoformat(), "articles": [],
    }
    # 头条新闻
    news = tavily_search(
        f"sanctions enforcement action news {date}",
        max_results=max_results, topic="news", days=3,
    )
    results["articles"].extend(news.get("results", []))
    # 政策更新
    policy = tavily_search(
        f"sanctions policy update new designation {region} {date}",
        max_results=5, topic="news", days=3,
    )
    results["articles"].extend(policy.get("results", []))
    return results


def search_trusted_sources(query: str, max_results: int = 10) -> dict:
    """仅从28个受信任制裁信息源搜索"""
    return tavily_search(
        query, max_results=max_results, search_depth="advanced",
        include_domains=TRUSTED_DOMAINS, topic="general",
    )


def format_results_markdown(results: dict) -> str:
    """将搜索结果格式化为 Markdown"""
    lines = []
    if "entity" in results:
        lines.append(f"# 制裁情报搜索结果：{results['entity']}")
        lines.append(f"\n**查询时间：** {results.get('timestamp', 'N/A')}\n")
        type_names = {
            "general_sanctions": "🌐 通用制裁搜索",
            "ofac": "🇺🇸 OFAC SDN 搜索",
            "eu_sanctions": "🇪🇺 欧盟制裁搜索",
            "un_sanctions": "🇺🇳 联合国制裁搜索",
            "uk_sanctions": "🇬🇧 英国制裁搜索",
            "export_control": "📦 出口管制搜索",
            "china_sanctions": "🇨🇳 中国制裁/管制搜索",
        }
        for search in results.get("searches", []):
            name = type_names.get(search["type"], search["type"])
            lines.append(f"\n## {name}")
            lines.append(f"**查询：** `{search['query']}`")
            items = search.get("results", [])
            lines.append(f"**结果数：** {len(items)}")
            if search.get("error"):
                lines.append(f"**错误：** {search['error']}")
            for i, r in enumerate(items, 1):
                lines.append(f"\n### {i}. {r.get('title', '无标题')}")
                url = r.get("url", "")
                lines.append(f"**URL:** [{url}]({url})")
                score = r.get("score", 0)
                if score:
                    lines.append(f"**相关性:** {score:.2f}")
                lines.append(f"\n{r.get('content', '无摘要')}\n")
                lines.append("---")
    elif "date" in results:
        lines.append(f"# 📰 每日制裁情报 — {results['date']}")
        lines.append(f"\n**地区：** {results.get('region', 'global')}")
        lines.append(f"**查询时间：** {results['timestamp']}")
        articles = results.get("articles", [])
        lines.append(f"**文章总数：** {len(articles)}\n")
        for i, a in enumerate(articles, 1):
            lines.append(f"## {i}. {a.get('title', '无标题')}")
            url = a.get("url", "")
            lines.append(f"**URL:** [{url}]({url})")
            lines.append(f"\n{a.get('content', '无摘要')}\n")
            lines.append("---")
    return "\n".join(lines)


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="制裁情报搜索 — Tavily API")
    sub = parser.add_subparsers(dest="command")

    p1 = sub.add_parser("entity", help="搜索实体制裁信息")
    p1.add_argument("name", help="实体名称")
    p1.add_argument("--max-results", type=int, default=10)
    p1.add_argument("--json", action="store_true")

    p2 = sub.add_parser("daily", help="每日制裁情报")
    p2.add_argument("--date", default=None)
    p2.add_argument("--region", default="global")
    p2.add_argument("--max-results", type=int, default=15)
    p2.add_argument("--json", action="store_true")

    p3 = sub.add_parser("search", help="自定义搜索")
    p3.add_argument("query")
    p3.add_argument("--max-results", type=int, default=10)
    p3.add_argument("--days", type=int, default=30)
    p3.add_argument("--json", action="store_true")

    p4 = sub.add_parser("trusted", help="受信任源搜索")
    p4.add_argument("query")
    p4.add_argument("--max-results", type=int, default=10)
    p4.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    output_json = getattr(args, "json", False)

    if args.command == "entity":
        res = search_entity_sanctions(args.name, args.max_results)
    elif args.command == "daily":
        res = search_daily_intel(args.date, args.region, args.max_results)
    elif args.command == "search":
        r = tavily_search(args.query, args.max_results, topic="news", days=args.days)
        res = {"results": r.get("results", [])}
    elif args.command == "trusted":
        r = search_trusted_sources(args.query, args.max_results)
        res = {"results": r.get("results", [])}

    if output_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif "entity" in res or "date" in res:
        print(format_results_markdown(res))
    else:
        for i, item in enumerate(res.get("results", []), 1):
            print(f"## {i}. {item.get('title', 'N/A')}")
            print(f"**URL:** {item.get('url', '')}")
            print(f"\n{item.get('content', '')}\n---")


if __name__ == "__main__":
    main()
