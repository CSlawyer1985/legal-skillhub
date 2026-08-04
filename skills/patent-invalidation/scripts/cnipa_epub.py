#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cnipa_epub.py —— 中国专利公布公告系统 (epub.cnipa.gov.cn) 获取助手
=====================================================================
本脚本是 patent-invalidation 技能 G6「其他检索途径」中，**针对中国专利(CN)的官方全文/
附图获取通道**。

为什么需要它：
    PatSeek 的内置 `patent` 详情接口目前仅稳定返回 CN **文本**（权利要求/说明书文字），
    不含原始附图。无效分析做 G7 同色标注比对时往往需要涉案/对比文件的**原始附图**与
    **专利单行本 PDF**（含说明书全文 + 附图）。CNIPA「中国专利公布公告系统」是官方的、
    社会公众免注册的权威来源，覆盖 1985 年至今的发明公布/授权、实用新型、外观设计。

使用前提：
    - 网络需能访问 epub.cnipa.gov.cn（本技能开发沙箱通常不可达，请在可访问 CNIPA 的
      环境中运行）。
    - 依赖 Python `requests` 库（与本技能其他脚本一致）。

重要限制（验证码）：
    该系统的「下载PDF」按钮带有**图形验证码**（"请输入图片中的四字成语或阿拉伯数字答案"）。
    纯 requests 的自动化下载很可能被验证码拦截。本脚本会**尽力尝试**最常见的
    `patentPdf?pubNo=...&token=...` 机制；若返回的不是 PDF（触发验证码/访问限制），
    则**明确回退到手工步骤**，不静默假装成功。需要全自动化批量下载时，可改用带人工
    过验证码的浏览器方案（Playwright + 人工/打码），作为扩展。

子命令：
    url    <公开号>            打印检索主页 / 直达链接 / 在线浏览与下载说明
    pdf    <公开号> [--out D]  尽力下载专利单行本 PDF；失败给出手工步骤
    batch  <文件>  [--cmd ...] 从文本文件逐行读取公开号，url 或 pdf
"""
import argparse
import os
import re
import sys

BASE = "http://epub.cnipa.gov.cn"
HOME = BASE + "/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def normalize(pub_no: str) -> str:
    """归一化公开号：接受 CN111121359A / 111121359A / CN111121359B 等。"""
    s = pub_no.strip().upper()
    if not s.startswith("CN"):
        s = "CN" + s
    return s


def print_urls(pub_no: str) -> None:
    pub = normalize(pub_no)
    print(f"[CNIPA 公布公告] 公开号 {pub}")
    print(f"  检索主页（在搜索框输入公开号/申请号即可） : {HOME}")
    print(f"  构造检索直达链接（参数可能随官网版本调整） : {BASE}/?searchText={pub}")
    print(f"  在线浏览/附图查看 ：检索结果页点击对应条目，")
    print(f"                      在线图像浏览器可直接看附图（无需验证码）")
    print(f"  下载 PDF（权威专利单行本，含说明书+附图）：")
    print(f"                      结果页点右上角『下载PDF』→ 输入图形验证码 → 下载")


def try_download_pdf(pub_no: str, out_dir: str) -> str | None:
    """尽力下载专利单行本 PDF；命中验证码/访问限制则回退手工步骤，返回保存路径或 None。"""
    import requests  # 延迟导入，避免无网络环境下 import 报错阻断 url 子命令

    pub = normalize(pub_no)
    os.makedirs(out_dir, exist_ok=True)
    sess = requests.Session()
    sess.headers.update(HEADERS)

    # 第 1 步：取首页，尝试提取前端 token（部分接口需要）
    token = None
    try:
        r = sess.get(HOME, timeout=30)
        m = re.search(r'"token"\s*:\s*"([^"]+)"', r.text)
        if m:
            token = m.group(1)
    except Exception as e:  # 网络不可达等
        print(f"  [warn] 首页获取失败（{e}）；将直接尝试 PDF 端点。")

    # 第 2 步：尝试 patentPdf 端点
    url = f"{BASE}/patentPdf?pubNo={pub}"
    if token:
        url += f"&token={token}"
    print(f"  [try] GET {url}")
    try:
        r = sess.get(url, timeout=60, stream=True)
        ctype = r.headers.get("Content-Type", "")
        body = r.content
        if ("application/pdf" in ctype) or (len(body) > 50000 and body[:4] == b"%PDF"):
            out = os.path.join(out_dir, pub + ".pdf")
            with open(out, "wb") as f:
                f.write(body)
            print(f"  [ok] 已保存 PDF: {out} ({len(body)} bytes)")
            return out
        print(f"  [blocked] 未返回 PDF（Content-Type={ctype or '无'}, "
              f"size={len(body)}）—— 很可能触发图形验证码/访问限制。")
    except Exception as e:
        print(f"  [error] 下载请求失败: {e}")

    print(f"  [manual] 请手工下载：打开 {HOME} ，输入 {pub} 检索，")
    print(f"           结果页点『下载PDF』并输入图形验证码后保存。")
    return None


def cmd_batch(path: str, out_dir: str, sub: str) -> None:
    with open(path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    for ln in lines:
        print("=" * 48)
        print(ln)
        if sub == "pdf":
            try_download_pdf(ln, out_dir)
        else:
            print_urls(ln)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="CNIPA 公布公告系统获取助手 (epub.cnipa.gov.cn) —— G6 的中国专利官方全文/附图通道"
    )
    sub = ap.add_subparsers(dest="cmd")

    p_url = sub.add_parser("url", help="打印检索/下载链接与说明")
    p_url.add_argument("pub_no", help="公开号，如 CN111121359A")

    p_pdf = sub.add_parser("pdf", help="尽力下载专利单行本 PDF")
    p_pdf.add_argument("pub_no")
    p_pdf.add_argument("--out", default=".", help="输出目录（默认当前目录）")

    p_batch = sub.add_parser("batch", help="批量：从文件逐行读取公开号")
    p_batch.add_argument("file", help="含公开号的文本文件（# 开头为注释）")
    p_batch.add_argument("--out", default=".", help="输出目录")
    p_batch.add_argument("--cmd", default="url", choices=["url", "pdf"])

    args = ap.parse_args()
    if args.cmd == "url":
        print_urls(args.pub_no)
    elif args.cmd == "pdf":
        try_download_pdf(args.pub_no, args.out)
    elif args.cmd == "batch":
        cmd_batch(args.file, args.out, args.cmd)
    else:
        ap.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
