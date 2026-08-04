#!/usr/bin/env python3
"""
网易号 公众号文章抓取器
抓取法院公众号在网易的同步号文章列表。

上海一中院在网易有官方同步号（上海一中法院），文章按时间倒序，
与微信公众号同步发布，内容完整。用于补充搜狗索引不足的账号。

用法：
  python3 fetch_163_week.py                    # 抓取所有配置的网易号
  python3 fetch_163_week.py --days 7           # 最近N天
"""

import json
import sys
import re
import time
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "mp_articles_163.json"

# 网易号主页
N163_ACCOUNTS = [
    ("上海一中法院", "https://dy.163.com/v2/media/T1500031294266.html"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://dy.163.com/",
}


def fetch_content(url):
    """抓取网易文章正文前300字作为 digest"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.select_one(".post_body")
        if content:
            text = content.get_text(" ", strip=True)
            return text[:300]
    except Exception:
        pass
    return ""


def fetch_articles(account_name, home_url, days):
    """抓取网易号主页文章列表"""
    cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=days)
    articles = []

    resp = requests.get(home_url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        print(f"  [ERR] 主页请求失败: {resp.status_code}")
        return articles

    soup = BeautifulSoup(resp.text, "html.parser")

    # 网易号列表：li.js-item.item
    seen = set()
    for item in soup.select("li.js-item"):
        # 标题：h4 a 或 img alt
        title_el = item.select_one("h4 a")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            img = item.select_one("img")
            title = img.get("alt", "").strip() if img else ""
        if not title:
            continue

        # 链接
        link_el = item.select_one("a[href*='163.com/dy/article/']")
        if not link_el:
            continue
        href = link_el.get("href", "")
        m = re.search(r'(https?://www\.163\.com/dy/article/[A-Za-z0-9]+\.html)', href)
        if not m:
            continue
        url = m.group(1)
        if url in seen:
            continue
        seen.add(url)

        # 时间：desc 里的时间文本
        time_el = item.select_one(".desc .time") or item.select_one(".time")
        pub_time = time_el.get_text(strip=True) if time_el else ""

        # 抓正文摘要
        digest = fetch_content(url)
        time.sleep(1)  # 控制频率

        articles.append({
            "title": title,
            "url": url,
            "publish_time": pub_time,
            "digest": digest,
            "_source": account_name,
        })

    return articles


def main():
    parser = argparse.ArgumentParser(description="网易号 公众号文章抓取")
    parser.add_argument("--days", type=int, default=7, help="最近N天")
    args = parser.parse_args()

    print(f"网易号 文章抓取: {len(N163_ACCOUNTS)} 个账号, 最近 {args.days} 天")
    print()

    all_articles = []
    for name, url in N163_ACCOUNTS:
        print(f"抓取: {name} ...")
        articles = fetch_articles(name, url, args.days)
        print(f"  -> {len(articles)} 篇")
        all_articles.extend(articles)

    # 去重（按 URL）
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    OUT.write_text(json.dumps(unique, ensure_ascii=False, indent=2))
    print(f"\n总计 {len(unique)} 篇文章，已写入 {OUT}")

    for art in unique[:10]:
        print(f"  [{art.get('_source','')}] {art.get('title','')[:45]}")


if __name__ == "__main__":
    main()
