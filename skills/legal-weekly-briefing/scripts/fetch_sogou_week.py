#!/usr/bin/env python3
"""
搜狗微信搜索 公众号文章发现器

原理：
1. 搜狗微信搜索 (weixin.sogou.com) 收录公众号文章，微信未关闭此入口
2. 按关键词搜索文章 → 按公众号名过滤 → 解析发布时间（JS 时间戳）→ 过滤近 N 天
3. 跟随搜狗跳转链接 → 解析 JS 拼接 → 得到 mp.weixin.qq.com 原文链接

用法：
  python3 fetch_sogou_week.py                    # 拉取所有配置的公众号
  python3 fetch_sogou_week.py --account 山东高法  # 只拉指定号
  python3 fetch_sogou_week.py --days 7           # 最近N天（默认7）
  python3 fetch_sogou_week.py --pages 3          # 每个关键词翻页数（默认3）
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
OUT = BASE / "mp_articles.json"

# 目标公众号：搜狗显示名称 + 搜索关键词（低频模式：每号1个关键词、1-2页，避开风控）
ACCOUNTS = [
    ("山东高法", ["鲁法案例 山东高法"]),
    ("上海一中法院", ["上海一中法院 案例"]),
    ("上海二中院", ["至正-案例分析"]),
    ("中国应用法学", ["法官办案心得"]),
]

SOGOU = "https://weixin.sogou.com"
SEARCH_URL = f"{SOGOU}/weixin"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{SOGOU}/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def new_session():
    """新建带风控 Cookie 的 session"""
    s = requests.Session()
    s.get(SOGOU, timeout=15)
    return s


def parse_publish_time(s_p):
    """从 .s-p 中解析发布时间。搜狗用 JS 时间戳渲染：timeConvert('1709030602')"""
    html = str(s_p)
    m = re.search(r"timeConvert\('(\d+)'\)", html)
    if m:
        ts = int(m.group(1))
        return datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
    return None


def resolve_wechat_url(session, link):
    """跟随搜狗跳转链接，解析出 mp.weixin.qq.com 原文 URL"""
    if link.startswith("/"):
        link = SOGOU + link
    try:
        resp = session.get(link, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return ""
        # 提取 JS 拼接的 URL 片段
        parts = re.findall(r"url\s*\+=\s*'([^']*)'", resp.text)
        if not parts:
            # 可能是 302 直跳
            if resp.url.startswith("http"):
                return resp.url
            return ""
        url = "".join(parts)
        # 清理 JS 转义
        url = url.replace("\\'", "'").replace('\\"', '"')
        if url.startswith("http"):
            return url
    except Exception:
        pass
    return ""


def search_account(session, account_name, keywords, days, max_pages):
    """搜索一个公众号的文章"""
    now = datetime.now(timezone(timedelta(hours=8)))
    cutoff = now - timedelta(days=days)
    found = {}

    for keyword in keywords:
        # 每个关键词用全新 session（降低风控概率）
        sess = new_session()
        for page in range(1, max_pages + 1):
            try:
                params = {"type": 2, "query": keyword, "page": page, "ie": "utf8"}
                resp = sess.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
                if resp.status_code != 200:
                    break

                # 风控检测
                if "antispider" in resp.text or "验证码" in resp.text:
                    print(f"    [WARN] 第{page}页被风控，停止翻页")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select(".news-list li")
                if not items:
                    break

                for item in items:
                    s_p = item.select_one(".s-p")
                    account_field = s_p.get_text(strip=True) if s_p else ""
                    if account_name not in account_field:
                        continue

                    h3 = item.select_one("h3 a")
                    if not h3:
                        continue
                    title = h3.get_text(strip=True)
                    link = h3.get("href", "")

                    pub_time = parse_publish_time(s_p) if s_p else None
                    if pub_time and pub_time < cutoff:
                        continue

                    # 去重（按标题）
                    if title in found:
                        continue

                    # 解析微信原文 URL
                    wx_url = resolve_wechat_url(sess, link)
                    if not wx_url:
                        continue  # 拿不到微信原文就跳过

                    found[title] = {
                        "title": title,
                        "url": wx_url,
                        "publish_time": pub_time.strftime("%Y-%m-%d %H:%M") if pub_time else "",
                        "digest": "",
                        "_source": account_name,
                    }

                time.sleep(5)  # 低频模式：间隔5秒，避开风控
            except Exception as e:
                print(f"    [ERR] 第{page}页: {e}")
                break

    return list(found.values())


def main():
    parser = argparse.ArgumentParser(description="搜狗微信 公众号文章发现")
    parser.add_argument("--account", type=str, help="只拉指定公众号")
    parser.add_argument("--days", type=int, default=7, help="最近N天")
    parser.add_argument("--pages", type=int, default=2, help="每个关键词翻页数（低频模式建议1-2）")
    args = parser.parse_args()

    accounts = ACCOUNTS
    if args.account:
        accounts = [(n, k) for n, k in ACCOUNTS if args.account.lower() in n.lower()]
        if not accounts:
            print(f"未找到账号: {args.account}", file=sys.stderr)
            sys.exit(1)

    session = new_session()
    print(f"搜狗微信 文章发现: {len(accounts)} 个账号, 最近 {args.days} 天, 每关键词 {args.pages} 页")
    print()

    all_articles = []
    for name, keywords in accounts:
        print(f"搜索: {name} ({' / '.join(keywords)}) ...")
        articles = search_account(session, name, keywords, args.days, args.pages)
        print(f"  -> {len(articles)} 篇")
        all_articles.extend(articles)

    all_articles.sort(key=lambda x: x.get("publish_time", ""), reverse=True)

    OUT.write_text(json.dumps(all_articles, ensure_ascii=False, indent=2))
    print(f"\n总计 {len(all_articles)} 篇文章，已写入 {OUT}")

    for art in all_articles[:10]:
        url = art.get("url", "")
        is_wx = "mp.weixin.qq.com" in url
        print(f"  [{'微信' if is_wx else '跳转'}] [{art.get('_source','')}] {art.get('title','')[:45]} | {art.get('publish_time','')}")


if __name__ == "__main__":
    main()
