#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式五 · 金标准定时刷新核验。

扫描 references/golden/ 中所有 ✅ 金标准条款，逐条核验是否仍有效：
  1. 打「最后核验」时间戳；
  2. best-effort HTTP 探测来源 URL 可达性：
       200/30x            → 页面存在（未在源头消失）
       404 / 410          → 疑似废止或迁移（重点复核）
       403 / 超时 / 异常   → 无法自动判定（需模式一人工复核，不擅自标废止）
  3. 交叉核对 online_readability.md：若属采标（采用 ISO/IEC 国际标准，官网不提供在线阅读），
     则**只能 detect 不能 auto-pull** —— 标「采标标准：无法自动拉取新版，请用户自行下载 PDF 更新」。
  4. 交叉核对 catalog.md / 规范速查表.md 状态列：若官方已标「废止」，重点复核。

输出：stdout 摘要 + references/golden/REFRESH_REPORT.md 复核清单（含每条处置建议）。

设计纪律：
  - 本脚本**从不擅自改写金标准条文**，也**不自动 abolish**（废止是高风险动作，须人/模式一确认）。
  - 仅做「detect + 报告」，把需复核项交给 agent（模式一）或用户决策。
  - 采标标准因版权无法在线拉取，绝不一味提示「已更新」，只提示「请用户自行获取新版原文核对」。

依赖：Python 标准库（urllib）。无第三方依赖，纯在线/离线 agent 均可跑探测骨架（离线时探测会报「无法访问」）。
"""

import os
import re
import sys
import argparse
import datetime
import urllib.request
import urllib.error

UA = "Mozilla/5.0 (compatible; china-fire-code-golden-refresh/1.0)"


def _base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def golden_dir():
    return os.path.join(_base(), "references", "golden")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _norm(s):
    return s.replace(" ", "").replace(" ", "")


# ── 交叉核对来源 ──────────────────────────────────────────────────


def _load_online_readability():
    p = os.path.join(_base(), "references", "online_readability.md")
    if not os.path.exists(p):
        return ""
    return _read(p)


def _is_cai_biao(std_norm, ol_text):
    """std_norm 如 'GB/T14402-2026'；在 online_readability 中查编号命中即视为采标。"""
    if not ol_text:
        return False
    # 取 online_readability 中出现的「GB/T xxxx」「GB xxxx」编号做归一化比对
    for m in re.finditer(r"GB/?T?\s*\d{4,5}-?\d{0,4}", ol_text):
        if _norm(m.group(0)) == std_norm:
            return True
    return False


def _catalog_status(std_norm):
    """在 catalog.md / 规范速查表.md 中查该规范编号所在行是否标「废止」。"""
    hits = []
    for fn in ("catalog.md", "规范速查表.md"):
        p = os.path.join(_base(), "references", fn)
        if not os.path.exists(p):
            continue
        for line in _read(p).splitlines():
            if std_norm in _norm(line):
                hits.append(line)
    for line in hits:
        if "废止" in line:
            return "废止"
    return "有效/未知"


# ── HTTP 探测 ────────────────────────────────────────────────────


def probe(url, timeout=8):
    """返回 ('ok'|'gone'|'blocked'|'error', detail)。"""
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            if code in (200, 301, 302, 303, 307, 308):
                return "ok", f"HTTP {code}"
            if code in (404, 410):
                return "gone", f"HTTP {code}"
            return "blocked", f"HTTP {code}"
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return "gone", f"HTTP {e.code}"
        return "blocked", f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return "error", f"{type(e).__name__}: {e}"


# ── 解析 golden 条目 ─────────────────────────────────────────────


BLOCK_RE = re.compile(r"^###\s+(.+?)\s+第\s+([\d.]+)\s+条.*$", re.MULTILINE)


def iter_golden_blocks():
    """yield (file_path, std, clause, block_text) for every ✅ block in golden/."""
    gd = golden_dir()
    if not os.path.isdir(gd):
        return
    for fn in sorted(os.listdir(gd)):
        if not fn.endswith(".md") or fn == "README.md" or fn == "REFRESH_REPORT.md":
            continue
        path = os.path.join(gd, fn)
        try:
            text = _read(path)
        except Exception:
            continue
        for m in BLOCK_RE.finditer(text):
            block = _block_slice(text, m.start(), m.end())
            if "✅" in block:
                yield path, m.group(1).strip(), m.group(2).strip(), block


def _block_slice(text, start, end_line_end):
    # 从当前 ### 标题到下一个 ### 或文件尾
    nxt = text.find("\n### ", end_line_end)
    if nxt == -1:
        return text[start:]
    return text[start:nxt]


def _field(block, name):
    m = re.search(rf"^-\s*{re.escape(name)}：(.*?)(?=\n-\s|\Z)", block, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _stamp_last_checked(block, today):
    """在块内写入/更新「最后核验：<date>」。"""
    if re.search(r"^-\s*最后核验：", block, re.MULTILINE):
        return re.sub(r"^(-\s*最后核验：).*$", f"\\1{today}", block, flags=re.MULTILINE)
    # 插在「核对状态」行之后
    return re.sub(r"^(-\s*核对状态：.*)$", f"\\1\n- 最后核验：{today}", block, flags=re.MULTILINE)


# ── 主流程 ──────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description="金标准定时刷新核验（detect + 报告，不擅自改写/废止）")
    ap.add_argument("--no-probe", action="store_true", help="跳过 HTTP 探测（纯离线模式，仅做交叉核对）")
    ap.add_argument("--write-report", action="store_true", help="额外把复核清单写入 references/golden/REFRESH_REPORT.md")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    ol_text = _load_online_readability()

    rows = []
    counts = {"ok": 0, "gone": 0, "blocked": 0, "error": 0, "caibiao": 0, "catalog_abolish": 0}

    for fpath, std, clause, block in iter_golden_blocks():
        key = f"{std} 第 {clause} 条"
        source = _field(block, "来源")
        std_norm = _norm(std)

        flags = []
        status = "ok"

        # 1) 采标 detect（仅提示，不 auto-pull）
        if _is_cai_biao(std_norm, ol_text):
            flags.append("采标标准：无法自动拉取新版，请用户自行下载官方 PDF 更新金标准")
            counts["caibiao"] += 1
            # 采标不强行探测正文，仍探测来源 URL 是否 404（判断迁移/撤销）
        # 2) catalog 状态
        cat = _catalog_status(std_norm)
        if cat == "废止":
            flags.append("catalog/规范速查表 已标「废止」——重点复核是否应 abolish")
            counts["catalog_abolish"] += 1
            status = "gone"
        # 3) HTTP 探测
        if not args.no_probe and source:
            kind, detail = probe(source)
            counts[kind] = counts.get(kind, 0) + 1
            if kind == "gone":
                flags.append(f"来源 URL 探测返回 {detail} —— 疑似废止/迁移，须模式一核实")
                status = "gone"
            elif kind in ("blocked", "error"):
                flags.append(f"来源 URL 探测 {detail} —— 无法自动判定，需模式一人工复核")
            else:
                flags.append(f"来源 URL 探测 {detail} —— 页面存在")
        elif not source:
            flags.append("缺来源 URL，无法探测，需人工补全")

        rows.append((key, status, "; ".join(flags) if flags else "正常", source))

        # 4) 回写最后核验时间戳
        new_block = _stamp_last_checked(block, today)
        _rewrite_block(fpath, block, new_block)

    # 报告
    lines = []
    lines.append(f"# 金标准刷新复核清单（{today}）")
    lines.append("")
    lines.append("> 本清单由 `scripts/refresh_golden.py` 自动生成。仅 detect + 报告，**不擅自改写/废止**金标准。")
    lines.append("> 需复核项须由 agent 用「模式一」联网核实，或用户确认后再执行 `golden.py abolish` / 更新条文。")
    lines.append("")
    lines.append(f"- 探测正常(ok)：{counts.get('ok',0)}")
    lines.append(f"- 疑似废止/迁移(gone)：{counts.get('gone',0)}")
    lines.append(f"- 被拦截/无法判定(blocked)：{counts.get('blocked',0)}")
    lines.append(f"- 网络异常(error)：{counts.get('error',0)}")
    lines.append(f"- 采标标准(仅 detect)：{counts.get('caibiao',0)}")
    lines.append(f"- catalog 已标废止：{counts.get('catalog_abolish',0)}")
    lines.append("")
    lines.append("| 条款 | 探测状态 | 处置建议 | 来源 |")
    lines.append("|---|---|---|---|")
    for key, status, advice, source in rows:
        icon = {"ok": "✅", "gone": "⚠️", "blocked": "❓", "error": "❓"}.get(status, "❓")
        lines.append(f"| {key} | {icon} {status} | {advice} | {source or '—'} |")
    lines.append("")
    report = "\n".join(lines)

    print(report)
    if args.write_report:
        rp = os.path.join(golden_dir(), "REFRESH_REPORT.md")
        with open(rp, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[已写入复核清单] {os.path.relpath(rp, _base())}")

    # 重点项提示
    risky = [r for r in rows if r[1] in ("gone", "blocked", "error")]
    if risky:
        print(f"\n[重点] {len(risky)} 条需复核，请用模式一联网核实后决定是否 abolish / 更新。")


def _rewrite_block(fpath, old_block, new_block):
    try:
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        if old_block in content:
            content = content.replace(old_block, new_block, 1)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception:
        pass


if __name__ == "__main__":
    main()
