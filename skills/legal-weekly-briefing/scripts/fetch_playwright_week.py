#!/usr/bin/env python3
"""
Playwright 公众号文章发现器
使用 Playwright + Edge Cookie 访问 MP 后台搜索文章。

原理：复用 Edge 浏览器中已保存的 MP 登录 Cookie，通过 Playwright
打开 MP 后台的"写文章-插入超链接"页面，搜索目标公众号文章。

凭证：Edge 浏览器已登录 MP（mp.weixin.qq.com）
"""

import json
import sys
import time
import sqlite3
import shutil
import tempfile
import argparse
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent
OUT = BASE / "mp_articles.json"

ACCOUNTS = [
    ("山东高法", "山东高法"),
    ("上海一中法院", "上海一中法院"),
    ("上海二中院", "上海二中院"),
    ("中国应用法学", "中国应用法学"),
]

# Edge Cookie 数据库路径
EDGE_COOKIE_PATH = Path.home() / "Library/Application Support/Microsoft Edge/Default/Cookies"


def get_edge_cookies(domain_filter="mp.weixin.qq.com"):
    """从 Edge SQLite 数据库提取 MP 相关 Cookie"""
    if not EDGE_COOKIE_PATH.exists():
        return []

    # 复制到临时文件避免锁定
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        shutil.copy2(EDGE_COOKIE_PATH, tmp.name)
        tmp_path = tmp.name

    try:
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly "
            "FROM cookies WHERE host_key LIKE ?",
            (f"%{domain_filter}%",)
        )
        cookies = []
        for row in cursor.fetchall():
            name, value, host_key, path, expires_utc, is_secure, is_httponly = row
            cookies.append({
                "name": name,
                "value": value,
                "domain": host_key,
                "path": path,
                "expires": expires_utc,
                "secure": bool(is_secure),
                "httpOnly": bool(is_httponly),
            })
        conn.close()
        return cookies
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def cookies_to_playwright(cookies):
    """转换为 Playwright 格式"""
    result = []
    for c in cookies:
        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c["path"],
            "secure": c["secure"],
            "httpOnly": c["httpOnly"],
        }
        if c.get("expires"):
            # Chrome 的 expires_utc 是从 1601-01-01 开始的微秒数
            chrome_epoch = 11644473600  # 1601-01-01 to 1970-01-01 的秒数
            expires = c["expires"] / 1000000 - chrome_epoch
            if expires > 0:
                cookie["expires"] = int(expires)
        result.append(cookie)
    return result


async def search_articles(account_name: str, days: int = 7):
    """用 Playwright 搜索指定公众号的文章"""
    from playwright.async_api import async_playwright

    cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=days)

    async with async_playwright() as p:
        # Use existing Chromium installation
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}", file=sys.stderr)
            print("请先安装 playwright 浏览器：python3 -m playwright install chromium", file=sys.stderr)
            sys.exit(1)

        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )

            # 加载 Edge Cookie
            edge_cookies = get_edge_cookies()
            if edge_cookies:
                pw_cookies = cookies_to_playwright(edge_cookies)
                await context.add_cookies(pw_cookies)
                print(f"  已加载 {len(pw_cookies)} 个 Edge Cookie")

            page = await context.new_page()

            # 打开 MP 后台
            print(f"  打开 MP 后台...")
            await page.goto("https://mp.weixin.qq.com/", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # 检查是否已登录
            content = await page.content()
            if "扫码登录" in content or "login" in page.url.lower():
                print("  [ERR] 未登录，请先在 Edge 中登录 MP")
                return []

            # 进入写文章页面
            print(f"  进入写文章页面...")
            await page.goto("https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isMul=1&isNew=1&lang=zh_CN&token=", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # 点击插入超链接
            print(f"  点击插入超链接...")
            # 查找超链接按钮
            link_btn = await page.query_selector(".edui-btn-insertlink") or \
                       await page.query_selector("[data-name='insertlink']") or \
                       await page.query_selector(".js_insertlink")
            if link_btn:
                await link_btn.click()
                await asyncio.sleep(1)
            else:
                print("  [WARN] 未找到插入链接按钮，尝试直接搜索...")
                # 尝试直接导航到搜索页面
                await page.goto(f"https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&begin=0&count=5&query={account_name}&token=&lang=zh_CN&f=json&ajax=1", wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)

            # 等待搜索结果
            await asyncio.sleep(2)

            # 提取搜索结果
            articles = []
            # 尝试从页面中提取文章列表
            items = await page.query_selector_all(".news-list .news-item, .search-item, .article-item, [class*='article'], [class*='news']")
            print(f"  找到 {len(items)} 个候选项")

            for item in items[:10]:
                try:
                    title_el = await item.query_selector(".title, .article-title, h4, a")
                    link_el = await item.query_selector("a[href*='mp.weixin.qq.com']")
                    time_el = await item.query_selector(".time, .date, .publish-time")

                    title = await title_el.inner_text() if title_el else ""
                    link = await link_el.get_attribute("href") if link_el else ""
                    pub_time = await time_el.inner_text() if time_el else ""

                    if title and link:
                        articles.append({
                            "title": title.strip(),
                            "url": link.strip(),
                            "publish_time": pub_time.strip(),
                            "_source": account_name,
                        })
                except Exception:
                    continue

            # 如果没找到，尝试从页面源码中提取
            if not articles:
                print("  尝试从页面源码提取...")
                html = await page.content()
                # 用正则提取文章链接和标题
                import re
                # 匹配 mp.weixin.qq.com 链接
                links = re.findall(r'href="(https?://mp\.weixin\.qq\.com/s/[^"]+)"[^>]*>([^<]+)', html)
                for link, title in links[:10]:
                    articles.append({
                        "title": title.strip(),
                        "url": link,
                        "publish_time": "",
                        "_source": account_name,
                    })

            print(f"  -> {len(articles)} 篇")
            return articles

        finally:
            await browser.close()


def main():
    import asyncio

    parser = argparse.ArgumentParser(description="Playwright 公众号文章发现")
    parser.add_argument("--account", type=str, help="只拉指定公众号")
    parser.add_argument("--days", type=int, default=7, help="最近N天")
    args = parser.parse_args()

    accounts = ACCOUNTS
    if args.account:
        accounts = [(n, n) for n, k in ACCOUNTS if args.account.lower() in n.lower()]
        if not accounts:
            print(f"未找到账号: {args.account}", file=sys.stderr)
            sys.exit(1)

    print(f"Playwright 文章发现: {len(accounts)} 个账号, 最近 {args.days} 天")
    print()

    all_articles = []
    for name, query in accounts:
        print(f"搜索: {name} ...")
        try:
            articles = asyncio.run(search_articles(query, args.days))
            all_articles.extend(articles)
        except Exception as e:
            print(f"  [ERR] {e}")

    OUT.write_text(json.dumps(all_articles, ensure_ascii=False, indent=2))
    print(f"\n总计 {len(all_articles)} 篇文章，已写入 {OUT}")


if __name__ == "__main__":
    main()
