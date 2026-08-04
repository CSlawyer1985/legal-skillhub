#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
foreign_patent_fetch.py —— 国外专利全文 PDF / 附图获取助手
============================================================

本脚本是 patent-invalidation 技能 G6「其他检索途径」中，**针对国外专利
(US/EP/JP/KR/WO/DE/FR/GB/CA/AU/CH 等) 的全文与附图获取通道**。

为什么需要它：
    PatSeek 的内置 `patent` 详情接口目前仅稳定返回 CN 文本（权利要求/说明书
    文字），不含原始附图，也不含 PDF；而国外文献 `semantic` 命中后也不返
    附图/全文。无效分析做 G7 同色标注比对需要原始附图（最好含说明书全文
    PDF）。本脚本覆盖 Google Patents（首选，无验证码、附图单独可下载）和
    Espacenet（备选，可下完整 PDF）。

数据源策略：
    - **Google Patents**（默认）：HTML 页面解析附图 src，逐张下载为 PNG
        优点：零验证码、覆盖 US/EP/JP/KR/WO/DE/FR/GB/CA/AU 全球、附图单独
        缺点：附图与说明书文字分离
    - **Espacenet**（备选）：取完整 PDF（含说明书 + 附图）作为完整存档
        优点：含完整说明书 + 附图单文件
        缺点：部分文献需跳转、有反爬

使用前提：
    - 依赖 Python `requests` + `beautifulsoup4`（解析 HTML）+ `PyMuPDF`（PDF
      拆分附图）。无 PyMuPDF 时仅 `figures` 子命令仍可用。
    - 网络可访问 patents.google.com / worldwide.espacenet.com（开发沙箱可能
      不可达，属正常）。

子命令：
    info     <公开号>            抓取并打印元数据（标题/申请人/日期/摘要）
    figures  <公开号> [--out D]  下载附图为 PNG；输出到 out/<id>/fig-*.png
    pdf      <公开号> [--out D]  下载完整 PDF（Espacenet）；失败回退 Google
    batch    <文件>   [--cmd ...]从文件逐行读取公开号执行

公开号格式（自动归一化）：
    US10234567B2 / US10234567 / 10234567B2        → US10234567B2
    EP1234567A1 / EP1234567                       → EP1234567A1
    JP2021-123456A / JP2021123456A                → JP2021123456A
    KR10-2021-0012345 / KR1020210012345           → KR1020210012345
    WO2021/123456A1 / WO2021123456A1              → WO2021123456A1
    DE102020123456A1 / FR3056789A1 / GB2581234A   → 通用
"""
import argparse
import os
import re
import sys
from typing import Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库。请运行: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    BeautifulSoup = None  # type: ignore

# PyMuPDF 仅 pdf/figures 拆页时需要
try:
    import fitz  # type: ignore
except ImportError:
    fitz = None

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# ── 公开号归一化 ──────────────────────────────────────────

COUNTRY_CODES = {
    "US", "EP", "JP", "KR", "WO", "DE", "FR", "GB", "CA", "AU",
    "CH", "AT", "BE", "NL", "SE", "ES", "IT", "RU", "CN", "TW", "HK",
}

# 公开号规范化正则（按国家分别处理，输出 URL 友好形式）
# Google Patents URL 形如: /patent/US12345678B2/en
# Espacenet 检索形如:    /patent/search?q=US12345678B2


def normalize_pubno(raw: str) -> str:
    """归一化公开号为 Google Patents URL 友好形式（含 kind code）。
    不能识别的格式原样返回（大写 + 去空格）。
    """
    s = re.sub(r"\s+", "", raw).upper()

    # 已是 CC + 数字 + 字母 kind 模式（WO/US/EP/JP/KR/CH/GB/FR/DE/AT/BE/NL/SE/ES/IT/RU/CA/AU/TW/HK）
    m = re.match(r"^([A-Z]{2})([0-9A-Z]+?)([A-Z][0-9]?)$", s)
    if m and m.group(1) in COUNTRY_CODES:
        return s

    # CC + 纯数字（无 kind，尝试加 A）—— 仅对少数国家
    m = re.match(r"^([A-Z]{2})([0-9]+)$", s)
    if m and m.group(1) in {"US", "EP", "DE", "FR", "GB", "CH", "CA", "AU", "AT", "BE", "NL", "SE", "ES", "IT", "RU", "TW", "HK"}:
        return s + "A1"

    # 无 CC 仅有数字+末尾 kind（B1/B2/A1/A2 等）—— 默认 US
    m = re.match(r"^([0-9]+)([A-Z][0-9]?)$", s)
    if m:
        return "US" + s

    # 纯数字 → 默认 US + A1
    if re.match(r"^[0-9]+$", s):
        return "US" + s + "A1"

    # JP/KR 形式：JP2021-123456A / KR10-2021-0012345
    m = re.match(r"^JP(\d{4})-?(\d+)([A-Z][0-9]?)$", s)
    if m:
        return f"JP{m.group(1)}{m.group(2)}{m.group(3)}"
    m = re.match(r"^KR(\d{2})-?(\d{4})-?(\d+)([A-Z][0-9]?)$", s)
    if m:
        return f"KR{m.group(1)}{m.group(2)}{m.group(3)}{m.group(4)}"

    # WO 形式：WO2021/123456A1
    m = re.match(r"^WO(\d{4})/?(\d+)([A-Z][0-9]?)$", s)
    if m:
        return f"WO{m.group(1)}{m.group(2)}{m.group(3)}"

    return s


def google_patent_url(pubno: str) -> str:
    """Google Patents 详情页 URL（en 视图）。"""
    return f"https://patents.google.com/patent/{pubno}/en"


def espacenet_search_url(pubno: str) -> str:
    """Espacenet 检索 URL（按公开号精确查询）。"""
    return f"https://worldwide.espacenet.com/patent/search?q={quote(pubno)}"


# ── Google Patents 抓取 ─────────────────────────────────────


def fetch_google_html(pubno: str) -> Optional[str]:
    """抓 Google Patents 详情页 HTML。失败返回 None。"""
    url = google_patent_url(pubno)
    try:
        r = requests.get(url, headers=HEADERS, timeout=45)
        if r.status_code != 200:
            print(f"  [warn] HTTP {r.status_code}", file=sys.stderr)
            return None
        return r.text
    except Exception as e:
        print(f"  [error] 请求失败: {e}", file=sys.stderr)
        return None


def extract_metadata_from_google(html: str) -> dict:
    """从 Google Patents HTML 提取元数据（标题/申请人/申请日/公开日/摘要）。"""
    if BeautifulSoup is None:
        # 纯 regex 兜底（仅抓 <title>）
        m = re.search(r"<title>([^<]+)</title>", html)
        return {"title": m.group(1).strip() if m else "N/A", "source": "google(no-bs4)"}
    soup = BeautifulSoup(html, "html.parser")
    meta = {}

    # 标题：<meta name="DC.title" content="...">
    el = soup.find("meta", attrs={"name": "DC.title"})
    if el and el.get("content"):
        meta["title"] = el["content"].strip()

    # 申请人：<meta name="DC.contributor" content="...">（多个取首个）
    applicants = []
    for el in soup.find_all("meta", attrs={"name": "DC.contributor"}):
        if el.get("content"):
            applicants.append(el["content"].strip())
    if applicants:
        meta["applicant"] = "; ".join(applicants[:5])

    # 申请日 / 公开日：<meta name="DC.date" content="...">
    dates = []
    for el in soup.find_all("meta", attrs={"name": "DC.date"}):
        if el.get("content"):
            dates.append(el["content"].strip())
    if dates:
        meta["dates"] = "; ".join(dates[:4])

    # 摘要：<abstract>...</abstract>
    ab = soup.find("abstract")
    if ab:
        meta["abstract"] = ab.get_text(" ", strip=True)[:500]

    meta["url"] = google_patent_url(_extract_pubno_from_html(html) or "")
    meta["source"] = "google"
    return meta


def _extract_pubno_from_html(html: str) -> Optional[str]:
    """从 Google Patents HTML 提取原始公开号（用于回显）。"""
    m = re.search(r'meta name="DC.identifier" content="([^"]+)"', html)
    return m.group(1) if m else None


# Google Patents 附图 src 模式：patentimages.storage.googleapis.com/.../*.png|*.jpg
GOOGLE_FIGURE_RE = re.compile(
    r"https?://patentimages\.storage\.googleapis\.com/[^'\"\s>]+\.(?:png|jpg|jpeg)",
    re.IGNORECASE,
)


def extract_figure_urls_from_google(html: str) -> list[str]:
    """从 Google Patents HTML 提取所有附图 URL（去重保序）。"""
    urls = GOOGLE_FIGURE_RE.findall(html)
    # 去重
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def download_figures(pubno: str, out_dir: str) -> list[str]:
    """下载 Google Patents 附图到 out_dir/<pubno>/fig-NN.png。"""
    html = fetch_google_html(pubno)
    if not html:
        print("  [error] HTML 抓取失败", file=sys.stderr)
        return []

    urls = extract_figure_urls_from_google(html)
    if not urls:
        print(f"  [warn] 未在 Google Patents 找到附图（可能文献类型无附图）", file=sys.stderr)
        return []

    pub_dir = os.path.join(out_dir, pubno)
    os.makedirs(pub_dir, exist_ok=True)

    saved = []
    print(f"  [info] 找到 {len(urls)} 张附图 URL，开始下载...")
    for i, u in enumerate(urls, 1):
        # 文件名: fig-001.png
        ext = os.path.splitext(u)[1].split("?")[0] or ".png"
        out_path = os.path.join(pub_dir, f"fig-{i:03d}{ext}")
        try:
            r = requests.get(u, headers=HEADERS, timeout=60)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            saved.append(out_path)
            print(f"    [{i:03d}/{len(urls)}] {os.path.basename(out_path)} ({len(r.content):,} bytes)")
        except Exception as e:
            print(f"    [{i:03d}] [error] {e}", file=sys.stderr)
    return saved


# ── Espacenet PDF 抓取 ──────────────────────────────────────


def download_espacenet_pdf(pubno: str, out_dir: str) -> Optional[str]:
    """尝试从 Espacenet 下载完整 PDF。失败返回 None。
    注：Espacenet 反爬较强，本函数可能经常触发重定向或反爬——失败时回退到 Google Patents HTML 打印人工指引。
    """
    out_path = os.path.abspath(os.path.join(out_dir, f"{pubno}.pdf"))
    os.makedirs(out_dir, exist_ok=True)

    # 1. 访问检索页拿真实详情页 URL（可能有重定向）
    search_url = espacenet_search_url(pubno)
    try:
        r = requests.get(search_url, headers=HEADERS, timeout=45, allow_redirects=True)
        if r.status_code != 200:
            print(f"  [warn] Espacenet 搜索页 HTTP {r.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"  [warn] Espacenet 搜索页请求失败: {e}", file=sys.stderr)
        return None

    # 2. 在搜索结果 HTML 中找详情页链接（pattern: /patent/family/...）
    detail_urls = re.findall(
        r'href="(/patent/family/[^"]+)"', r.text
    )
    if not detail_urls:
        print("  [warn] Espacenet 搜索页未找到详情链接", file=sys.stderr)
        print(f"  [manual] 请手工访问: {search_url}", file=sys.stderr)
        return None

    detail_url = "https://worldwide.espacenet.com" + detail_urls[0]
    print(f"  [info] 详情页: {detail_url}")

    # 3. 访问详情页找 Original document PDF 链接
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=45, allow_redirects=True)
        if r.status_code != 200:
            print(f"  [warn] Espacenet 详情页 HTTP {r.status_code}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"  [error] Espacenet 详情页请求失败: {e}", file=sys.stderr)
        return None

    # 4. 找 PDF 链接（多种 pattern 兼容）
    pdf_patterns = [
        r'href="([^"]*\.pdf[^"]*)"',
        r'"(https?://[^"]*\.pdf[^"]*)"',
        r'data-pdf-url="([^"]+)"',
    ]
    pdf_urls = []
    for pat in pdf_patterns:
        pdf_urls = re.findall(pat, r.text)
        if pdf_urls:
            break

    if not pdf_urls:
        print("  [warn] Espacenet 详情页未找到 PDF 链接（反爬或页面改版）", file=sys.stderr)
        print(f"  [manual] 请手工访问: {detail_url}", file=sys.stderr)
        return None

    # 5. 尝试下载第一个 PDF（通常是 Original document）
    pdf_url = pdf_urls[0]
    if not pdf_url.startswith("http"):
        pdf_url = "https://worldwide.espacenet.com" + pdf_url

    try:
        r = requests.get(pdf_url, headers=HEADERS, timeout=120, stream=True)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "").lower()
        body = r.content
        if "pdf" in ctype or (len(body) > 10000 and body[:4] == b"%PDF"):
            with open(out_path, "wb") as f:
                f.write(body)
            print(f"  [ok] PDF 已保存: {out_path} ({len(body):,} bytes)")
            return out_path
        print(f"  [warn] 返回非 PDF（Content-Type={ctype}, size={len(body)}）", file=sys.stderr)
    except Exception as e:
        print(f"  [error] PDF 下载失败: {e}", file=sys.stderr)

    return None


# ── PDF 拆附图（PyMuPDF）────────────────────────────────────


def extract_figures_from_pdf(pdf_path: str, out_dir: str, prefix: str = "fig") -> list[str]:
    """从 PDF 拆出含图的页面，导出为 PNG。

    判定「含图页面」: 页面含至少 1 个内嵌 raster image, 且图面积 > 页面 5%。
    """
    if fitz is None:
        print("  [error] 需要安装 PyMuPDF (pip install PyMuPDF)", file=sys.stderr)
        return []

    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved = []
    for i, page in enumerate(doc, 1):
        # 渲染整页为 PNG（最稳，即使没有内嵌 image 也保留手绘示意图）
        mat = fitz.Matrix(2.0, 2.0)  # 2x 分辨率
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = os.path.join(out_dir, f"{prefix}-{i:03d}.png")
        pix.save(out_path)
        saved.append(out_path)
    doc.close()
    print(f"  [ok] 从 PDF 拆出 {len(saved)} 页 → {out_dir}")
    return saved


# ── 子命令：info ────────────────────────────────────────────


def cmd_info(pubno: str) -> int:
    """抓取并打印元数据。"""
    pn = normalize_pubno(pubno)
    print(f"[Foreign Patent] 公开号: {pn}")
    html = fetch_google_html(pn)
    if not html:
        print("  [error] HTML 抓取失败", file=sys.stderr)
        return 1
    meta = extract_metadata_from_google(html)
    print(f"  URL:       {meta.get('url', google_patent_url(pn))}")
    for k in ("title", "applicant", "dates", "abstract"):
        if k in meta:
            v = meta[k]
            if k == "abstract" and len(v) > 200:
                v = v[:200] + "..."
            print(f"  {k:10s}: {v}")
    return 0


# ── 子命令：figures ─────────────────────────────────────────


def cmd_figures(pubno: str, out_dir: str) -> int:
    """下载 Google Patents 附图为 PNG。"""
    pn = normalize_pubno(pubno)
    print(f"[Foreign Patent Figures] 公开号: {pn}")
    print(f"  输出目录: {os.path.abspath(out_dir)}")
    saved = download_figures(pn, out_dir)
    if saved:
        print(f"\n  [done] 共 {len(saved)} 张附图：")
        for s in saved:
            print(f"    {s}")
        return 0
    print("  [error] 附图下载失败", file=sys.stderr)
    return 1


# ── 子命令：pdf ─────────────────────────────────────────────


def cmd_pdf(pubno: str, out_dir: str, also_extract_figures: bool = False) -> int:
    """下载完整 PDF（Espacenet 优先, 失败回退到人工指引）。"""
    pn = normalize_pubno(pubno)
    print(f"[Foreign Patent PDF] 公开号: {pn}")
    print(f"  输出目录: {os.path.abspath(out_dir)}")
    pdf_path = download_espacenet_pdf(pn, out_dir)
    if pdf_path and also_extract_figures and fitz is not None:
        fig_dir = os.path.join(out_dir, pn + "-figures")
        extract_figures_from_pdf(pdf_path, fig_dir, prefix="fig")
    if not pdf_path:
        print("  [fallback] Espacenet 失败，请改用以下渠道：")
        print(f"    Google Patents (HTML+附图): {google_patent_url(pn)}")
        print(f"    WIPO PatentScope (WO):       https://patentscope.wipo.int/")
        print(f"    USPTO (US):                  https://ppubs.uspto.gov/pubwebapp/")
        print(f"    J-PlatPat (JP):              https://www.j-platpat.inpit.go.jp/")
        return 1
    return 0


# ── 子命令：batch ───────────────────────────────────────────


def cmd_batch(path: str, out_dir: str, sub: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    for ln in lines:
        print("=" * 60)
        if sub == "info":
            cmd_info(ln)
        elif sub == "figures":
            cmd_figures(ln, out_dir)
        elif sub == "pdf":
            cmd_pdf(ln, out_dir)
        else:
            print(f"未知子命令: {sub}")
            return 1
    return 0


# ── CLI 入口 ───────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(
        description="国外专利全文 PDF / 附图获取助手（Google Patents + Espacenet）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 元数据
  python foreign_patent_fetch.py info US10234567B2

  # 下载附图（推荐，最快）
  python foreign_patent_fetch.py figures US10234567B2 --out ./figs

  # 下载完整 PDF（Espacenet，含说明书+附图）
  python foreign_patent_fetch.py pdf EP1234567A1 --out ./pdfs

  # PDF 下载后顺便拆附图
  python foreign_patent_fetch.py pdf US10234567B2 --out ./pdfs --extract-figures

  # 批量
  python foreign_patent_fetch.py batch compare_list.txt --cmd figures --out ./figs
        """,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info", help="抓取元数据（标题/申请人/日期/摘要）")
    p_info.add_argument("pubno", help="公开号，如 US10234567B2 / EP1234567A1")

    p_fig = sub.add_parser("figures", help="下载附图为 PNG（Google Patents）")
    p_fig.add_argument("pubno", help="公开号")
    p_fig.add_argument("--out", default=".", help="输出目录（默认当前目录）")

    p_pdf = sub.add_parser("pdf", help="下载完整 PDF（Espacenet）")
    p_pdf.add_argument("pubno", help="公开号")
    p_pdf.add_argument("--out", default=".", help="输出目录")
    p_pdf.add_argument("--extract-figures", action="store_true", help="PDF 下载后顺便拆附图")

    p_batch = sub.add_parser("batch", help="批量：从文件逐行读取公开号")
    p_batch.add_argument("file", help="含公开号的文本文件（# 开头为注释）")
    p_batch.add_argument("--cmd", default="figures", choices=["info", "figures", "pdf"], help="对每行执行的子命令")
    p_batch.add_argument("--out", default=".", help="输出目录")

    args = ap.parse_args()

    if args.cmd == "info":
        return cmd_info(args.pubno)
    elif args.cmd == "figures":
        return cmd_figures(args.pubno, args.out)
    elif args.cmd == "pdf":
        return cmd_pdf(args.pubno, args.out, args.extract_figures)
    elif args.cmd == "batch":
        return cmd_batch(args.file, args.out, args.cmd)
    return 1


if __name__ == "__main__":
    sys.exit(main())
