#!/usr/bin/env python3
"""
腾讯元宝扫码登录向导

打开 https://yuanbao.tencent.com/chat（有头浏览器），等待扫码登录，
检测到对话输入框出现（登录成功的标志）后保存 Playwright storage_state 到 ~/.config/yuanbao_state.json。

用法：
  python3 scripts/yuanbao_login.py            # 正常扫码登录
  python3 scripts/yuanbao_login.py --force   # 已登录也重新扫码

退出码：0 = 登录态已保存；1 = 失败/超时
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

STATE_PATH = Path.home() / ".config" / "yuanbao_state.json"

POLL_INTERVAL = 3      # 秒
POLL_TIMEOUT = 600     # 秒（10 分钟扫码窗口，元宝登录流程较慢）
SETTLE_SECONDS = 3

# 登录成功标志：对话输入框出现（contenteditable 或 textarea）
INPUT_SELECTORS = [
    "div[contenteditable='true']",
    "textarea",
    "[contenteditable]:not([contenteditable='false'])",
]

# 未登录特征文本（登录弹窗/未登录态）—— 防输入框选择器误判
LOGGED_OUT_KW = ["未登录", "扫码登录", "请使用微信扫描二维码", "立即登录"]


async def get_body_text(page) -> str:
    try:
        return await page.evaluate("document.body ? document.body.innerText : ''")
    except Exception:
        return ""


async def detect_input(page) -> bool:
    for sel in INPUT_SELECTORS:
        try:
            el = await page.query_selector(sel)
            if el:
                return True
        except Exception:
            continue
    return False


async def is_logged_out(page) -> bool:
    text = await get_body_text(page)
    return any(k in text for k in LOGGED_OUT_KW)


async def logged_in(page) -> bool:
    """登录成功 = 输入框存在 且 页面无未登录特征"""
    if not await detect_input(page):
        return False
    return not await is_logged_out(page)


async def main_async(force: bool) -> int:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=False)
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}", file=sys.stderr)
            print("请先安装 playwright 浏览器：python3 -m playwright install chromium", file=sys.stderr)
            sys.exit(1)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        print("打开腾讯元宝 https://yuanbao.tencent.com/chat ...")
        await page.goto("https://yuanbao.tencent.com/chat", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(6)

        # 已登录：输入框可用且无未登录特征
        if not force and await logged_in(page):
            print("检测到已登录（输入框可用），直接保存现有登录态。")
            await context.storage_state(path=str(STATE_PATH))
            print(f"✅ 登录态已保存: {STATE_PATH}")
            await browser.close()
            return 0

        print("未检测到有效登录态，请在浏览器窗口中扫码/登录腾讯元宝。")
        print("（如页面有登录按钮，请手动点击并完成登录）")

        # 轮询登录成功（输入框 + 无未登录特征）
        waited = 0
        while waited < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
            try:
                if await logged_in(page):
                    await asyncio.sleep(SETTLE_SECONDS)
                    await context.storage_state(path=str(STATE_PATH))
                    state = json.loads(STATE_PATH.read_text())
                    n = len(state.get("cookies", []))
                    print(f"✅ 登录成功！输入框已出现且无未登录特征，共 {n} 个 cookie，登录态保存至 {STATE_PATH}")
                    await browser.close()
                    return 0
            except Exception:
                pass
            if waited % 30 == 0:
                print(f"  等待登录... {waited}s / {POLL_TIMEOUT}s")

        print("❌ 等待登录超时（10 分钟），未检测到有效登录态。请重试。", file=sys.stderr)
        await browser.close()
        return 1


def main():
    parser = argparse.ArgumentParser(description="腾讯元宝扫码登录向导")
    parser.add_argument("--force", action="store_true", help="已登录也重新扫码")
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args.force)))


if __name__ == "__main__":
    main()
