#!/usr/bin/env python3
"""
OpenSanctions 在线查询模块
用途：通过 OpenSanctions API 进行实体制裁名单匹配
纯线上查询，无需本地下载/维护名单数据

OpenSanctions 已聚合全球 100+ 制裁名单，包括：
  OFAC SDN、UN 安理会、EU 制裁、UK Sanctions List、
  AU DFAT、CA SEMA、JP MOF 等
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

# OpenSanctions 公开 API（yente 引擎）
# 免费层有速率限制，付费层无限制
OPENSANCTIONS_API = "https://api.opensanctions.org"

# 可选数据集：
#   "default"    — 全部制裁+PEP+犯罪（最全）
#   "sanctions"  — 仅制裁名单
#   "peps"       — 仅政治敏感人物
DATASET = "default"


def get_api_key() -> str:
    """获取 OpenSanctions API Key（可选，免费层无需 key）"""
    return os.environ.get("OPENSANCTIONS_API_KEY", "")


def _request(method: str, path: str, data: dict = None, params: dict = None) -> dict:
    """发送 HTTP 请求到 OpenSanctions API"""
    url = f"{OPENSANCTIONS_API}{path}"
    if params:
        query_str = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v is not None)
        url = f"{url}?{query_str}"

    headers = {"Content-Type": "application/json"}
    api_key = get_api_key()
    if api_key:
        headers["Authorization"] = f"ApiKey {api_key}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"  [OpenSanctions API] HTTP {e.code} error: {error_body[:200]}", file=sys.stderr)
        return {"error": f"HTTP {e.code}: {error_body}", "responses": {}, "results": []}
    except urllib.error.URLError as e:
        return {"error": f"网络错误: {e}", "responses": {}, "results": []}
    except Exception as e:
        return {"error": f"未知错误: {e}", "responses": {}, "results": []}


import urllib.parse


def match_entity(
    name: str,
    schema: str = "LegalEntity",
    birth_date: str = None,
    countries: list = None,
    id_number: str = None,
    limit: int = 10,
    score_threshold: float = 0.5,
) -> dict:
    """
    使用 OpenSanctions /match 端点进行实体匹配

    参数:
        name: 实体名称（公司或个人）
        schema: 实体类型 — "Person"(个人) 或 "LegalEntity"(法人/公司) 或 "Thing"(通用)
        birth_date: 出生日期 (YYYY-MM-DD)，仅个人适用
        countries: 国家代码列表 (如 ["cn", "ru"])
        id_number: 身份证/护照号码
        limit: 返回结果上限
        score_threshold: 最低匹配分数（0-1）
    返回:
        匹配结果字典
    """
    # 构造查询属性
    properties = {"name": [name]}
    if birth_date:
        properties["birthDate"] = [birth_date]
    if countries:
        properties["country"] = countries
    if id_number:
        properties["idNumber"] = [id_number]

    query = {
        "queries": {
            "entity_query": {
                "schema": schema,
                "properties": properties,
            }
        }
    }

    resp = _request("POST", f"/match/{DATASET}", data=query)

    # 处理响应
    result = {
        "entity": name,
        "schema": schema,
        "timestamp": datetime.now().isoformat(),
        "matches": [],
        "total_matches": 0,
        "error": resp.get("error"),
    }

    if "responses" in resp:
        entity_resp = resp["responses"].get("entity_query", {})
        raw_results = entity_resp.get("results", [])
        for r in raw_results:
            score = r.get("score", 0)
            if score >= score_threshold:
                match = {
                    "score": score,
                    "name": r.get("caption", ""),
                    "id": r.get("id", ""),
                    "schema": r.get("schema", ""),
                    "datasets": r.get("datasets", []),
                    "properties": {},
                    "referents": r.get("referents", []),
                    "first_seen": r.get("first_seen", ""),
                    "last_seen": r.get("last_seen", ""),
                    "last_change": r.get("last_change", ""),
                }
                # 提取关键属性
                props = r.get("properties", {})
                for key in ["name", "alias", "country", "birthDate",
                            "nationality", "position", "program",
                            "topics", "notes", "description",
                            "address", "idNumber", "sourceUrl"]:
                    if key in props:
                        match["properties"][key] = props[key]
                result["matches"].append(match)

        result["total_matches"] = len(result["matches"])
        result["matches"] = result["matches"][:limit]

    return result


def search_entity(query: str, limit: int = 10) -> dict:
    """
    使用 OpenSanctions /search 端点进行文本搜索

    参数:
        query: 搜索关键词
        limit: 返回结果上限
    返回:
        搜索结果字典
    """
    resp = _request("GET", f"/search/{DATASET}", params={"q": query, "limit": limit})

    result = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "results": [],
        "total": resp.get("total", 0),
        "error": resp.get("error"),
    }

    for r in resp.get("results", []):
        item = {
            "name": r.get("caption", ""),
            "id": r.get("id", ""),
            "schema": r.get("schema", ""),
            "score": r.get("score", 0),
            "datasets": r.get("datasets", []),
            "first_seen": r.get("first_seen", ""),
            "last_seen": r.get("last_seen", ""),
        }
        props = r.get("properties", {})
        for key in ["name", "alias", "country", "topics", "program"]:
            if key in props:
                item[key] = props[key]
        result["results"].append(item)

    return result


def scrape_opensanctions(query: str, limit: int = 5) -> dict:
    """
    当 API 不可用（429/401）时，通过网页抓取 OpenSanctions 搜索结果。
    解析 HTML 页面提取实体名称、类型、标签和国家。
    """
    import re as _re
    url = f"https://www.opensanctions.org/search/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    }
    req = urllib.request.Request(url, headers=headers)
    result = {"query": query, "timestamp": datetime.now().isoformat(), "results": [], "total": 0, "source": "web_scrape"}
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # 解析搜索结果：提取 <a> 标签中的实体链接和名称
        # 格式: <a href="/entities/...">Entity Name</a>
        entity_pattern = _re.compile(r'<a[^>]+href="/entities/([^"]+)"[^>]*>([^<]+)</a>')
        tag_pattern = _re.compile(r'<span[^>]*class="[^"]*badge[^"]*"[^>]*>([^<]+)</span>')
        matches = entity_pattern.findall(html)
        seen = set()
        for entity_id, name in matches:
            name = name.strip()
            if entity_id in seen or not name or len(name) < 2:
                continue
            seen.add(entity_id)
            # 提取该实体附近的标签（Sanctioned entity, Export controlled 等）
            result["results"].append({
                "name": name,
                "id": entity_id,
                "score": 0.8,  # 网页搜索不提供分数，给默认值
                "datasets": [],
                "schema": "LegalEntity",
                "properties": {},
                "source": "web_scrape",
            })
            if len(result["results"]) >= limit:
                break
        result["total"] = len(result["results"])
        if result["results"]:
            print(f"  [OpenSanctions] 网页抓取成功: {result['total']} 条结果", file=sys.stderr)
    except Exception as e:
        result["error"] = str(e)
        print(f"  [OpenSanctions] 网页抓取失败: {e}", file=sys.stderr)
    return result


def get_entity_detail(entity_id: str) -> dict:
    """获取特定实体的详细信息"""
    return _request("GET", f"/entities/{entity_id}")


def format_match_results(results: dict) -> str:
    """将匹配结果格式化为 Markdown"""
    lines = []
    lines.append(f"# 🔍 OpenSanctions 名单匹配结果")
    lines.append(f"\n**查询实体：** {results['entity']}")
    lines.append(f"**实体类型：** {results['schema']}")
    lines.append(f"**查询时间：** {results['timestamp']}")
    lines.append(f"**匹配总数：** {results['total_matches']}")

    if results.get("error"):
        lines.append(f"\n> ⚠️ 错误: {results['error']}")

    if results["total_matches"] == 0:
        lines.append("\n✅ **未发现制裁名单匹配** — 该实体未在已知制裁名单中找到。")
        lines.append("\n> 注意：此结果基于 OpenSanctions 聚合的 100+ 全球制裁名单。")
        lines.append("> 建议配合 Tavily 搜索进行交叉验证。")
    else:
        lines.append(f"\n⚠️ **发现 {results['total_matches']} 个潜在匹配！**\n")
        for i, m in enumerate(results["matches"], 1):
            score_pct = m["score"] * 100
            # 匹配度标签
            if score_pct >= 90:
                badge = "🔴 高度匹配"
            elif score_pct >= 70:
                badge = "🟠 中度匹配"
            else:
                badge = "🟡 低度匹配"

            lines.append(f"## {i}. {m['name']} — {badge} ({score_pct:.0f}%)")
            lines.append(f"**ID:** `{m['id']}`")
            lines.append(f"**类型:** {m['schema']}")

            # 数据来源（哪些名单命中）
            datasets = m.get("datasets", [])
            if datasets:
                ds_display = []
                ds_map = {
                    "us_ofac_sdn": "🇺🇸 OFAC SDN",
                    "un_sc_sanctions": "🇺🇳 UN安理会",
                    "eu_fsf": "🇪🇺 EU制裁",
                    "gb_hmt_sanctions": "🇬🇧 UK制裁",
                    "au_dfat_sanctions": "🇦🇺 澳洲DFAT",
                    "ca_sema_sanctions": "🇨🇦 加拿大SEMA",
                    "jp_mof_sanctions": "🇯🇵 日本MOF",
                    "us_bis_denied": "🇺🇸 BIS拒绝清单",
                    "us_state_debarred": "🇺🇸 国务院禁止清单",
                }
                for ds in datasets:
                    ds_display.append(ds_map.get(ds, ds))
                lines.append(f"**命中名单:** {', '.join(ds_display)}")

            # 关键属性
            props = m.get("properties", {})
            if props.get("alias"):
                lines.append(f"**别名:** {', '.join(props['alias'][:5])}")
            if props.get("country"):
                lines.append(f"**国家:** {', '.join(props['country'])}")
            if props.get("birthDate"):
                lines.append(f"**出生日期:** {', '.join(props['birthDate'])}")
            if props.get("program"):
                lines.append(f"**制裁项目:** {', '.join(props['program'][:3])}")
            if props.get("notes"):
                lines.append(f"**备注:** {props['notes'][0][:200]}")
            if props.get("sourceUrl"):
                for url in props["sourceUrl"][:2]:
                    lines.append(f"**来源:** [{url}]({url})")

            lines.append(f"**首次记录:** {m.get('first_seen', 'N/A')}")
            lines.append(f"**最后更新:** {m.get('last_change', 'N/A')}")
            lines.append("")
            lines.append("---")

    return "\n".join(lines)


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="OpenSanctions 在线制裁名单查询")
    sub = parser.add_subparsers(dest="command")

    # match 命令
    p1 = sub.add_parser("match", help="实体匹配（推荐，支持模糊匹配）")
    p1.add_argument("name", help="实体名称")
    p1.add_argument("--type", choices=["Person", "LegalEntity", "Thing"],
                     default="LegalEntity", help="实体类型")
    p1.add_argument("--birth-date", default=None, help="出生日期 (YYYY-MM-DD)")
    p1.add_argument("--countries", nargs="+", default=None, help="国家代码 (如 cn ru)")
    p1.add_argument("--id-number", default=None, help="身份证/护照号码")
    p1.add_argument("--threshold", type=float, default=0.5, help="最低匹配分 (0-1)")
    p1.add_argument("--limit", type=int, default=10, help="结果上限")
    p1.add_argument("--json", action="store_true", help="JSON 输出")

    # search 命令
    p2 = sub.add_parser("search", help="文本搜索")
    p2.add_argument("query", help="搜索关键词")
    p2.add_argument("--limit", type=int, default=10)
    p2.add_argument("--json", action="store_true")

    # detail 命令
    p3 = sub.add_parser("detail", help="获取实体详情")
    p3.add_argument("id", help="实体 ID (如 ofac-12345)")
    p3.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "match":
        res = match_entity(
            name=args.name, schema=args.type, birth_date=args.birth_date,
            countries=args.countries, id_number=args.id_number,
            limit=args.limit, score_threshold=args.threshold,
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(format_match_results(res))

    elif args.command == "search":
        res = search_entity(args.query, args.limit)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"# 搜索结果: {args.query}\n")
            for i, r in enumerate(res.get("results", []), 1):
                print(f"## {i}. {r['name']} (score: {r.get('score', 0):.2f})")
                print(f"**ID:** `{r['id']}`  **类型:** {r['schema']}")
                print(f"**数据集:** {', '.join(r.get('datasets', []))}")
                print("---")

    elif args.command == "detail":
        res = get_entity_detail(args.id)
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
