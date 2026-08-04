#!/usr/bin/env python3
"""
元宝补充融合 L2 通道：对「缺失本号原文」的 L1 条目用腾讯元宝反查 mp 直链。

输入：
  - L1: scripts/mp_articles_weread.json（5 字段，P1 产物）
  - 登录态: ~/.config/yuanbao_state.json（yuanbao_login.py 产物）

用法：
  python3 scripts/fetch_yuanbao_supplement.py                # 反查缺失本号原文的条目
  python3 scripts/fetch_yuanbao_supplement.py --test-weekly  # 分层抽 7 条周报标题做反查测试
  python3 scripts/fetch_yuanbao_supplement.py --days 7       # 指定时间窗（默认 7 天）
  python3 scripts/fetch_yuanbao_supplement.py --list-keys    # 只打印待反查清单，不执行

输出：scripts/yuanbao_links.json
  每条: {title, account, query, answer, mp_urls[], status: ok|转载版|元宝不可用, l1_url}

策略：
  - 缺失本号原文 = 该号条目中 url 的 __biz 与该号主流 __biz 指纹不一致（微信读书搜到的转载号文章）
  - 元宝回答无 mp 链接 → status=转载版，保留 L1 转载链接（merge 时兜底）
  - 元宝风控 → 等 30 秒重试 1 次，仍失败 → status=元宝不可用，继续下一条
  - 提问间隔 ≥5 秒
"""

import argparse
import asyncio
import json
import random
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
L1_PATH = BASE / "mp_articles_weread.json"
OUT_PATH = BASE / "yuanbao_links.json"
STATE_PATH = Path.home() / ".config" / "yuanbao_state.json"

YUANBAO_URL = "https://yuanbao.tencent.com/chat"
MIN_INTERVAL = 5        # 提问最小间隔（秒）
RETRY_WAIT = 30         # 风控等待（秒）
ANSWER_TIMEOUT = 60     # 单条回答超时（秒）
INPUT_SELECTORS = [
    "div[contenteditable='true']",
    "textarea",
    "[contenteditable]:not([contenteditable='false'])",
]

MP_URL_RE = re.compile(r'https?://mp\.weixin\.qq\.com/\S+')
RISK_KW = ["操作过于频繁", "请求太频繁", "请稍后再试", "验证码", "人机验证", "访问异常", "频率过高"]
LOGGED_OUT_KW = ["未登录", "扫码登录", "请使用微信扫描二维码", "立即登录"]


def load_state() -> list:
    """加载元宝登录态 cookie（有 cookie 即可，登录标志由输入框检测兜底）"""
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text())
            cookies = data.get("cookies", []) if isinstance(data, dict) else []
            if cookies:
                return cookies
        except json.JSONDecodeError:
            pass
    return []


def biz_of(url: str) -> str:
    """提取 URL 中的 __biz 指纹"""
    if not url:
        return ""
    q = parse_qs(urlparse(url).query)
    return q.get("__biz", [""])[0]


def pick_test_keys(articles, n=7) -> list:
    """分层抽样：每号至少 1 条，多的号补足到 n 条（保持可复现：按 publish_time 排序取前 N）"""
    by_src = {}
    for a in articles:
        by_src.setdefault(a["_source"], []).append(a)
    # 每号按时间倒序，取最新的
    picked = []
    accounts = sorted(by_src.keys())
    for acc in accounts:
        src = sorted(by_src[acc], key=lambda x: x.get("publish_time", ""), reverse=True)
        picked.append(src[0])
    # 补足到 n：按剩余条数比例轮转
    rest = [a for a in articles if a not in picked]
    rest.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    i = 0
    while len(picked) < n and rest:
        a = rest[i % len(rest)]
        if a not in picked:
            picked.append(a)
            rest.remove(a)
        i += 1
    return picked


def find_missing_originals(articles, days: int) -> list:
    """标记「缺失本号原文」：__biz 与该号主流指纹不一致的条目"""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=days)

    biz_by_acc = {}
    for a in articles:
        biz_by_acc.setdefault(a["_source"], []).append(biz_of(a["url"]))

    # 每号主流指纹 = 出现次数最多的 __biz
    main_biz = {}
    for acc, bizs in biz_by_acc.items():
        from collections import Counter
        c = Counter(b for b in bizs if b)
        if c:
            main_biz[acc] = c.most_common(1)[0][0]

    missing = []
    for a in articles:
        if a["_source"] not in main_biz:
            continue
        if biz_of(a["url"]) != main_biz[a["_source"]]:
            missing.append(a)
    return missing


def extract_mp_urls(text: str) -> list:
    """从回答文本提取 mp 链接（去重、去尾部标点）"""
    if not text:
        return []
    urls = []
    for m in MP_URL_RE.finditer(text):
        u = m.group(0).rstrip("。，；、,.;)\u301d\u301e\"'】]）")
        if u not in urls:
            urls.append(u)
    return urls


async def detect_input(page) -> bool:
    for sel in INPUT_SELECTORS:
        try:
            if await page.query_selector(sel):
                return True
        except Exception:
            continue
    return False


async def get_body_text(page) -> str:
    try:
        return await page.evaluate("document.body ? document.body.innerText : ''")
    except Exception:
        return ""


async def logged_in(page) -> bool:
    """输入框存在 且 页面无未登录特征（防误判）"""
    if not await detect_input(page):
        return False
    text = await get_body_text(page)
    return not any(k in text for k in LOGGED_OUT_KW)


async def ask_yuanbao(context, account: str, title: str) -> dict:
    """向元宝提问并等待回答，返回 {answer, mp_urls, risk}"""
    page = await context.new_page()
    try:
        await page.goto(YUANBAO_URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(6)
        if not await logged_in(page):
            return {"answer": "", "mp_urls": [], "risk": "no_input"}

        # 输入并发送
        query = f"搜索微信公众号「{account}」的《{title}》原文链接"
        for sel in INPUT_SELECTORS:
            try:
                box = await page.query_selector(sel)
                if box:
                    await box.click()
                    await page.keyboard.type(query, delay=30)
                    await page.keyboard.press("Enter")
                    break
            except Exception:
                continue

        # 等待回答：body 文本增长且 3 秒稳定（或超时）
        await asyncio.sleep(3)
        base_len = len(await get_body_text(page))
        prev_text = await get_body_text(page)
        stable_rounds = 0
        waited = 0
        while waited < ANSWER_TIMEOUT:
            await asyncio.sleep(3)
            waited += 3
            cur = await get_body_text(page)
            # 风控检测
            if any(k in cur for k in RISK_KW) and "发送" in cur[-3000:]:
                return {"answer": cur[-2000:], "mp_urls": [], "risk": "risk"}
            if len(cur) > base_len and cur == prev_text:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
            prev_text = cur

        # 提取回答：截取提问后的新文本
        tail = prev_text[-4000:] if len(prev_text) > 4000 else prev_text
        urls = extract_mp_urls(tail)
        return {"answer": tail[-2000:], "mp_urls": urls, "risk": ""}
    finally:
        await page.close()


async def run_queries(keys: list, out_path: Path) -> list:
    from playwright.async_api import async_playwright

    cookies = load_state()
    if not cookies:
        print("❌ 未找到元宝登录态。请先运行：python3 scripts/yuanbao_login.py", file=sys.stderr)
        sys.exit(1)

    results = []
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

        for i, k in enumerate(keys):
            account, title, l1_url = k["_source"], k["title"], k.get("url", "")
            print(f"[{i+1}/{len(keys)}] 反查: [{account}] {title[:40]} ...", flush=True)
            entry = {
                "title": title,
                "account": account,
                "query": f"搜索微信公众号「{account}」的《{title}》原文链接",
                "answer": "",
                "mp_urls": [],
                "status": "ok",
                "l1_url": l1_url,
            }
            try:
                r = await ask_yuanbao(context, account, title)
                if r["risk"] == "risk":
                    print(f"  ⚠️ 疑似风控，等待 {RETRY_WAIT}s 重试 ...")
                    await asyncio.sleep(RETRY_WAIT)
                    r = await ask_yuanbao(context, account, title)
                    if r["risk"] == "risk":
                        print(f"  ❌ 重试仍失败，标记「元宝不可用」")
                        entry.update(answer="", mp_urls=[], status="元宝不可用")
                        results.append(entry)
                        continue
                if r["risk"] == "no_input":
                    print(f"  ❌ 输入框未出现（登录态可能失效），标记「元宝不可用」")
                    entry.update(status="元宝不可用")
                    results.append(entry)
                    continue
                entry.update(answer=r["answer"], mp_urls=r["mp_urls"])
                if r["mp_urls"]:
                    print(f"  ✅ 命中 {len(r['mp_urls'])} 个 mp 链接: {r['mp_urls'][0][:70]}")
                else:
                    print(f"  ↩️ 无 mp 链接，标记「转载版」（保留 L1 链接）")
                    entry["status"] = "转载版"
            except Exception as e:
                print(f"  [ERR] {e}")
                entry.update(status="元宝不可用")
            results.append(entry)

            # 提问间隔 ≥5 秒（最后一条不 sleep）
            if i < len(keys) - 1:
                gap = max(MIN_INTERVAL, random.uniform(5, 9))
                await asyncio.sleep(gap)

            # 即时落盘：每条完成后立即写，中断只丢当前条
            out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
            print(f"  [进度 {i+1}/{len(keys)} 已落盘]", flush=True)

        await browser.close()

    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    ok = sum(1 for r in results if r["mp_urls"])
    print(f"\n反查完成: {ok}/{len(results)} 命中 mp 链接，结果已写入 {out_path}", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description="元宝补充融合 L2 通道")
    parser.add_argument("--test-weekly", action="store_true", help="从 L1 分层抽 7 条周报标题做反查测试")
    parser.add_argument("--days", type=int, default=7, help="时间窗（默认 7 天）")
    parser.add_argument("--list-keys", action="store_true", help="只打印待反查清单，不执行")
    args = parser.parse_args()

    if not L1_PATH.exists():
        print(f"❌ 缺少 L1 输入: {L1_PATH}（先跑 fetch_weread_week.py）", file=sys.stderr)
        sys.exit(1)
    articles = json.loads(L1_PATH.read_text())

    if args.test_weekly:
        keys = pick_test_keys(articles, 7)
        print(f"测试模式: 从 L1 分层抽取 7 条周报标题（覆盖 {len(set(k['_source'] for k in keys))} 个号）")
    else:
        keys = find_missing_originals(articles, args.days)
        print(f"正常模式: 标记「缺失本号原文」{len(keys)} 条（近 {args.days} 天）")

    for k in keys:
        print(f"  - [{k['_source']}] {k['title'][:50]}")

    if args.list_keys:
        return
    if not keys:
        print("✅ 无待反查条目。")
        return

    asyncio.run(run_queries(keys, OUT_PATH))


if __name__ == "__main__":
    main()
