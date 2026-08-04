#!/usr/bin/env python3
"""
微信读书搜一搜 公众号文章发现器（mp 直链版）

原理：微信读书网页版「搜一搜」可搜索公众号文章，返回 mp.weixin.qq.com 原文直链。
这是 2026-07-29 微信关闭 MP 跨号接口后唯一稳定的公众号文章发现通道。

前置：已通过微信读书扫码登录，登录态保存在 /tmp/weread_state.json（或 ~/.config/weread_state.json）

用法：
  python3 fetch_weread_week.py                    # 全部公众号
  python3 fetch_weread_week.py --account 山东高法  # 指定公众号
  python3 fetch_weread_week.py --days 7           # 最近N天（默认7）
"""

import json
import sys
import re
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

BASE = Path(__file__).resolve().parent
OUT = BASE / "mp_articles_weread.json"
STATE_PATHS = [
    Path.home() / ".config" / "weread_state.json",  # 主登录态（weread_login.py 写入）
    Path("/tmp/weread_state.json"),                 # 历史遗留 fallback
]

ACCOUNTS = ["山东高法", "上海一中法院", "上海二中院", "中国应用法学"]

SEARCH_URL = "https://search.weixin.qq.com/cgi-bin/newsearchweb/userclientjump?path=page/search/weread&query={kw}&platform=pc"


def parse_date(date_str: str) -> datetime:
    """解析微信读书的相对/绝对时间"""
    now = datetime.now(timezone(timedelta(hours=8)))
    if not date_str:
        return None
    m = re.search(r'(\d+)\s*分钟前', date_str)
    if m:
        return now - timedelta(minutes=int(m.group(1)))
    m = re.search(r'(\d+)\s*小时前', date_str)
    if m:
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r'(\d+)\s*天前', date_str)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r'(\d+)\s*个月前', date_str)
    if m:
        return now - timedelta(days=30 * int(m.group(1)))
    m = re.search(r'(\d+)\s*年前', date_str)
    if m:
        return now - timedelta(days=365 * int(m.group(1)))
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone(timedelta(hours=8)))
        except ValueError:
            return None
    return None


def load_state() -> list:
    """加载登录态 cookie，必须含有效 wr_vid（微信读书登录凭证），否则视为未登录"""
    for p in STATE_PATHS:
        if p.exists():
            try:
                data = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            cookies = data.get("cookies", []) if isinstance(data, dict) else []
            if any(c.get("name") == "wr_vid" and c.get("value") for c in cookies):
                return cookies
    return []


async def search_account(context, account: str, days: int) -> list:
    """搜索一个公众号的文章"""
    page = await context.new_page()

    kw = quote(account)
    await page.goto(SEARCH_URL.format(kw=kw), wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(8)

    # 滚动加载（最多 6 轮）
    prev = 0
    for r in range(6):
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        await asyncio.sleep(3)
        c = await page.evaluate("document.querySelectorAll('.search_list_item').length")
        if c == prev and r > 2:
            break
        prev = c
        if c > 500:
            break

    # 提取元数据
    arts_json = await page.evaluate("""(() => {
        const arts = [];
        document.querySelectorAll('.search_list_item').forEach((item, i) => {
            const t = item.querySelector('.article__title-text');
            const d = item.querySelector('.article__desc');
            const s = item.querySelector('.source__title');
            const dt = item.querySelector('.source__text.date');
            arts.push({
                idx: i,
                title: (t?.textContent || '').trim(),
                desc: (d?.textContent || '').trim().substring(0, 300),
                source: (s?.textContent || '').trim(),
                date: (dt?.textContent || '').trim(),
            });
        });
        return JSON.stringify(arts);
    })()""")
    arts = json.loads(arts_json)

    # 提取 mp 直链（拦截 window.open）
    urls_json = await page.evaluate("""(async function() {
        var sleep = ms => new Promise(r => setTimeout(r, ms));
        var items = document.querySelectorAll('.search_list_item');
        var orig = window.open;
        var results = [];
        var targets = Array.from({length: items.length}, (_, i) => i);
        for (var i = 0; i < targets.length; i++) {
            var captured = '';
            window.open = function(u) { captured = u; };
            items[targets[i]].scrollIntoView({block: 'center', behavior: 'instant'});
            items[targets[i]].click();
            await sleep(40);
            results.push({idx: targets[i], url: captured});
        }
        window.open = orig;
        return JSON.stringify(results);
    })()""")
    urls = json.loads(urls_json)
    url_map = {r["idx"]: r["url"] for r in urls}

    # URL 提取诊断：有元数据但直链全空 = 页面结构变化
    if arts and not any(url_map.values()):
        print(f"  [WARN] {account}: 提取到 {len(arts)} 条元数据但 mp 直链全为空，疑似页面结构变化", file=sys.stderr)

    # 合并 + 过滤
    cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=days)
    results = []
    seen = set()
    for a in arts:
        url = url_map.get(a["idx"], "")
        if not url or "mp.weixin.qq.com" not in url:
            continue
        # 严格公众号名匹配（搜索结果可能混入其他号）
        if a["source"] != account:
            continue
        if url in seen:
            continue
        seen.add(url)
        pub = parse_date(a["date"])
        if pub is None:
            continue  # 无法确定时间的文章跳过
        if pub < cutoff:
            continue
        results.append({
            "title": a["title"],
            "url": url,
            "publish_time": pub.strftime("%Y-%m-%d %H:%M"),
            "digest": a["desc"],
            "_source": account,
        })

    await page.close()
    return results


async def main_async(accounts, days):
    from playwright.async_api import async_playwright

    cookies = load_state()
    if not cookies:
        print("❌ 未找到有效微信读书登录态（缺 wr_vid）。请重新扫码：python3 scripts/weread_login.py", file=sys.stderr)
        sys.exit(1)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}", file=sys.stderr)
            print("请先安装 playwright 浏览器：python3 -m playwright install chromium", file=sys.stderr)
            sys.exit(1)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        await context.add_cookies(cookies)

        # weread 备份标签页保持 session + 登录态过期检测
        keep = await context.new_page()
        await keep.goto("https://weread.qq.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        live = await context.cookies("https://weread.qq.com")
        if not any(c.get("name") == "wr_vid" and c.get("value") for c in live):
            print("❌ 微信读书登录态已过期。请重新扫码：python3 scripts/weread_login.py", file=sys.stderr)
            sys.exit(1)

        all_articles = []
        empty_accounts = []
        for account in accounts:
            print(f"搜索: {account} ...")
            try:
                arts = await search_account(context, account, days)
                print(f"  -> {len(arts)} 篇")
                if not arts:
                    empty_accounts.append(account)
                all_articles.extend(arts)
            except Exception as e:
                print(f"  [ERR] {account}: {e}")
                empty_accounts.append(account)

        await browser.close()

    all_articles.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    OUT.write_text(json.dumps(all_articles, ensure_ascii=False, indent=2))
    print(f"\n总计 {len(all_articles)} 篇，已写入 {OUT}")
    for a in all_articles[:10]:
        print(f"  [{a['_source']}] {a['title'][:45]} | {a['publish_time']}")
    if empty_accounts:
        print(f"⚠️ 无结果账号: {', '.join(empty_accounts)}")


def main():
    parser = argparse.ArgumentParser(description="微信读书 公众号文章发现")
    parser.add_argument("--account", type=str, help="只搜索指定公众号")
    parser.add_argument("--days", type=int, default=7, help="最近N天")
    args = parser.parse_args()

    accounts = ACCOUNTS
    if args.account:
        accounts = [a for a in ACCOUNTS if args.account.lower() in a.lower()]

    print(f"微信读书搜一搜: {len(accounts)} 个公众号, 最近 {args.days} 天")
    print()
    asyncio.run(main_async(accounts, args.days))


if __name__ == "__main__":
    main()
