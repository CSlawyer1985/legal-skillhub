#!/usr/bin/env python3
"""
微信读书扫码登录向导

打开微信读书网页版（有头浏览器），触发登录弹窗，等待扫码，
检测到 wr_vid cookie 后保存 Playwright storage_state 到 ~/.config/weread_state.json。

用法：
  python3 scripts/weread_login.py            # 正常扫码登录
  python3 scripts/weread_login.py --force   # 已登录也重新走扫码流程

退出码：0 = 登录态已保存；1 = 失败/超时
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

STATE_PATH = Path.home() / ".config" / "weread_state.json"

POLL_INTERVAL = 2      # 秒
POLL_TIMEOUT = 300     # 秒（5 分钟扫码窗口）
SETTLE_SECONDS = 3     # wr_vid 出现后再等 cookie 稳定


def has_vid(cookies) -> bool:
    return any(c.get("name") == "wr_vid" and c.get("value") for c in cookies)


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
        print("打开微信读书 https://weread.qq.com/ ...")
        await page.goto("https://weread.qq.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # 已有登录态：默认直接复用，除非 --force
        if not force:
            cur = await context.cookies("https://weread.qq.com")
            if has_vid(cur):
                print("检测到已登录（wr_vid 存在），直接保存现有登录态。")
                await context.storage_state(path=str(STATE_PATH))
                print(f"✅ 登录态已保存: {STATE_PATH}")
                await browser.close()
                return 0

        # 触发登录弹窗（多选择器兜底，找不到就提示手动点击）
        print("未检测到登录态，尝试触发登录弹窗...")
        clicked = False
        for sel in [
            "text=登录",
            "button:has-text(\"登录\")",
            "[class*='login'] >> nth=0",
            "text=扫码登录",
        ]:
            try:
                await page.click(sel, timeout=3000)
                clicked = True
                print(f"已点击登录入口 ({sel})，请在弹出的二维码窗口扫码。")
                break
            except Exception:
                continue
        if not clicked:
            print("未能自动触发登录弹窗，请在浏览器窗口中手动点击「登录」并扫码。")

        # 轮询 wr_vid
        waited = 0
        while waited < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
            cur = await context.cookies("https://weread.qq.com")
            if has_vid(cur):
                await asyncio.sleep(SETTLE_SECONDS)  # 等 wr_skey 等 cookie 落定
                await context.storage_state(path=str(STATE_PATH))
                state = json.loads(STATE_PATH.read_text())
                n = len(state.get("cookies", []))
                print(f"✅ 扫码成功！wr_vid 已写入，共 {n} 个 cookie，登录态保存至 {STATE_PATH}")
                await browser.close()
                return 0
            if waited % 30 == 0:
                print(f"  等待扫码... {waited}s / {POLL_TIMEOUT}s")

        print("❌ 等待扫码超时（5 分钟），未检测到 wr_vid。请重试。", file=sys.stderr)
        await browser.close()
        return 1


def main():
    parser = argparse.ArgumentParser(description="微信读书扫码登录向导")
    parser.add_argument("--force", action="store_true", help="已登录也重新扫码")
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args.force)))


if __name__ == "__main__":
    main()
