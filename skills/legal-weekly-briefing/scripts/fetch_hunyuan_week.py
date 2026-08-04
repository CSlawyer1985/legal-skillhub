#!/usr/bin/env python3
"""
TokenHub 公众号文章发现器（L3 兜底通道）
使用 TokenHub 联网搜索发现法院公众号最新文章，L1/L2 全挂时的最后防线。

凭证: ~/.config/tencentcloud/tokenhub_api_key
模型: deepseek-v4-pro + web_search_options.enable

输出: scripts/mp_articles.json（5 字段：title/url/publish_time/digest/_source）

用法:
  python3 fetch_hunyuan_week.py                    # 拉取所有配置的公众号
  python3 fetch_hunyuan_week.py --account "山东高法" # 只拉指定号
  python3 fetch_hunyuan_week.py --days 7           # 最近N天（默认7）
"""

import json
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("需要 requests: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE = Path(__file__).resolve().parent
OUT = BASE / "mp_articles.json"

# 与 P1/P2 一致的 4 个号
ACCOUNTS = ["山东高法", "上海一中法院", "上海二中院", "中国应用法学"]

TOKENHUB_API = "https://tokenhub.tencentmaas.com/v1/chat/completions"
MODEL = "deepseek-v4-pro"


def load_token() -> str:
    p = Path.home() / ".config" / "tencentcloud" / "tokenhub_api_key"
    if not p.exists():
        return ""
    return p.read_text().strip()


def build_queries(account_name: str, days: int) -> list:
    """每个号生成两个搜索关键词查询：「<号> YYYY年M月」+「<号> 案例」"""
    now = datetime.now(timezone(timedelta(hours=8)))
    month_str = now.strftime("%Y年%m月")
    cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    queries = []
    for kw in [f"{account_name} {month_str}", f"{account_name} 案例"]:
        queries.append(
            f"请联网搜索「{kw}」，找出微信公众号「{account_name}」在 {cutoff} 之后发布的文章。\n"
            f"要求：\n"
            f"1. 只返回该公众号发布的文章（公众号名称完全匹配「{account_name}」）\n"
            f"2. 每篇提供：标题、URL（文章真实链接）、发布日期、内容摘要\n"
            f"3. 找不到就返回空数组，不要编造\n"
            f"输出格式为 JSON 数组，不要其他文字：\n"
            f'[{{"title":"...","url":"...","publish_time":"YYYY-MM-DD","digest":"..."}}]'
        )
    return queries


def call_api(api_key: str, prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "web_search_options": {"enable": True, "search_source": "lite"},
        "stream": False,
        "max_tokens": 8192,
        "temperature": 0.1,
    }
    try:
        resp = requests.post(TOKENHUB_API, headers=headers, json=payload, timeout=120)
        if resp.status_code in (400, 401, 403):
            print("❌ TokenHub API 密钥无效，请重新配置（~/.config/tencentcloud/tokenhub_api_key）", file=sys.stderr)
            return {"error": f"auth_failed:{resp.status_code}"}
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def parse_articles(data: dict) -> list:
    if "error" in data:
        print(f"  [ERR] {data['error']}", file=sys.stderr)
        return []

    choices = data.get("choices", [])
    if not choices:
        return []

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        return []

    # Extract JSON from markdown code block
    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        if end > start:
            content = content[start:end].strip()
    elif "```" in content:
        start = content.find("```") + 3
        end = content.find("```", start)
        if end > start:
            content = content[start:end].strip()

    try:
        articles = json.loads(content)
        if isinstance(articles, list):
            return articles
    except json.JSONDecodeError:
        pass

    # Fallback: try to find [ ... ]
    start = content.find("[")
    end = content.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    return []


def main():
    parser = argparse.ArgumentParser(description="TokenHub 公众号文章发现")
    parser.add_argument("--account", type=str, help="只拉指定公众号")
    parser.add_argument("--days", type=int, default=7, help="最近N天")
    args = parser.parse_args()

    api_key = load_token()
    if not api_key:
        print("❌ 未找到 TokenHub API Key（~/.config/tencentcloud/tokenhub_api_key）", file=sys.stderr)
        sys.exit(1)

    accounts = ACCOUNTS
    if args.account:
        accounts = [a for a in ACCOUNTS if args.account.lower() in a.lower()]
        if not accounts:
            print(f"未找到账号: {args.account}", file=sys.stderr)
            sys.exit(1)

    print(f"TokenHub 文章发现: {len(accounts)} 个账号, 最近 {args.days} 天")
    print(f"模型: {MODEL} | web_search: lite | 每号 2 关键词")
    print()

    all_articles = []
    empty_accounts = []
    for name in accounts:
        print(f"搜索: {name} ...")
        seen_urls = set()
        for qi, query in enumerate(build_queries(name, args.days)):
            print(f"  关键词 {qi + 1}/2: {query[:40]}...")
            resp = call_api(api_key, query)
            articles = parse_articles(resp)
            print(f"    -> {len(articles)} 篇")
            for art in articles:
                # 字段标准化 → 5 字段
                if "publish_date" in art and "publish_time" not in art:
                    art["publish_time"] = art.pop("publish_date")
                if "url" not in art and "link" in art:
                    art["url"] = art.pop("link")
                if "source" in art and "_source" not in art:
                    art["_source"] = art.pop("source")
                url = (art.get("url") or "").strip()
                if not url or not (art.get("title") or "").strip():
                    continue  # 无 url/标题的条目丢弃
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                art["_source"] = name
                art.setdefault("publish_time", "")
                art.setdefault("digest", "")
                # 非 mp 链接保留（兜底通道不要求本号原文）
                all_articles.append(art)
        n_acc = sum(1 for a in all_articles if a["_source"] == name)
        print(f"  -> {name} 合计 {n_acc} 篇")
        if n_acc == 0:
            empty_accounts.append(name)

    all_articles.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    OUT.write_text(json.dumps(all_articles, ensure_ascii=False, indent=2))
    print(f"\n总计 {len(all_articles)} 篇文章，已写入 {OUT}")
    for art in all_articles[:5]:
        print(f"  [{art.get('_source','')}] {art.get('title','')[:50]} | {art.get('publish_time','')}")
    if empty_accounts:
        print(f"⚠️ 无结果账号: {', '.join(empty_accounts)}")


if __name__ == "__main__":
    main()
