#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金标准库（golden）管理 —— 模式三知识回流的「信任主源」。

  write   — 联网检索到的权威条文追加进 references/golden/<规范>.md，默认 ⏳ 待人工核对。
  confirm — 人工核对某条目无误后，将 ⏳ 待人工核对 晋升为 ✅ 金标准（此后可直接调用，不弹 ⚠️）。
  lookup  — 查询某 (规范, 条款) 是否已存在 ✅ 金标准；命中则直接输出原文（agent 优先采用，无需重新抓取）。
  abolish — 检测到废止条款时，从 golden 移入 references/archive/<规范>.md，仅作历史追溯。

闸门：
  - 来源域须为白名单
  - 去重键 (规范, 条款, 版本)
  - 不覆盖 ✅ 条目（write）
  - 废止操作需确认（abolish）

「金标准」定义：仅 ✅ 已核对（人工确认）的条款才算金标准，可零摩擦直接引用；
⏳ 仅为候选，引用时须标注「待核对」，不可当作金标准。

依赖：Python 标准库。
"""

import re
import sys
import os
import argparse
import datetime
import shutil

# 权威源白名单（与 SKILL.md 精准性铁律一致）：覆盖法律/行政法规/部门规章/国标/行标 的官方发布域。
WHITELIST = (
    "npc.gov.cn",          # 法律（全国人大常委会）
    "gov.cn",              # 行政法规 / 国务院规范性文件
    "openstd.samr.gov.cn", # 国家标准全文公开系统
    "samr.gov.cn",         # 国家市场监督管理总局（标准主管）
    "mohurd.gov.cn",       # 住建部（工程建设标准/部令）
    "mem.gov.cn",          # 应急管理部（消防规章/部令）
    "119.gov.cn",          # 国家消防救援局
)


def domain_ok(source):
    return any(d in source for d in WHITELIST)


def _base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def golden_path(std):
    safe = std.replace(" ", "_")
    return os.path.join(_base(), "references", "golden", f"{safe}.md")


def archive_path(std):
    safe = std.replace(" ", "_")
    return os.path.join(_base(), "references", "archive", f"{safe}.md")


def dedup_exists(path, key):
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        return key in f.read()


# ── 块解析工具 ──────────────────────────────────────────────────


def _find_block(content, key):
    pattern = re.compile(
        rf"(^###\s*{re.escape(key)}.*?)(?=\n### |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(content)
    return m.group(0) if m else None


def _field(block, name):
    """提取 `- 字段名：...` 直到下一个 `- ` 字段或块尾的内容（固定宽度锚定，避免变长 look-behind）。"""
    m = re.search(rf"^-\s*{re.escape(name)}：(.*?)(?=\n-\s|\Z)", block, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    val = m.group(1).strip()
    if name == "原文" and val.startswith("（逐字，待人工核对）"):
        val = val[len("（逐字，待人工核对）"):].strip()
    return val


# ── mode 3a : write ───────────────────────────────────────────────


def cmd_write(args):
    if not domain_ok(args.source):
        sys.exit(f"[拒绝] 来源域不在白名单，已丢弃：{args.source}")
    key = f"{args.std} 第 {args.clause} 条"
    path = golden_path(args.std)
    if dedup_exists(path, key):
        print(f"[跳过] 已存在去重键：{key}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    today = datetime.date.today().isoformat()
    block = (
        f"\n### {args.std} 第 {args.clause} 条\n"
        f"- 原文：（逐字，待人工核对）\n{args.text}\n"
        f"- 来源：{args.source}\n"
        f"- 抓取日期：{today}\n"
        f"- 版本：{args.version}\n"
        f"- 核对状态：⏳ 待人工核对\n"
    )
    with open(path, "a", encoding="utf-8") as f:
        f.write(block)
    mode = "auto" if args.auto else "manual"
    rel = os.path.relpath(path, _base())
    print(f"[已写入 golden · {mode}] {key} → {rel} （⏳ 待人工核对）")
    if not args.auto:
        print("提示：当前为 manual 模式，请用户确认后调 `golden.py confirm` 晋升为金标准。")


# ── lookup : 直接调金标准 ─────────────────────────────────────────


def cmd_lookup(args):
    key = f"{args.std} 第 {args.clause} 条"
    path = golden_path(args.std)
    if not os.path.exists(path):
        sys.exit(f"[未命中] golden 中无该规范：{args.std}")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    block = _find_block(content, key)
    if not block:
        sys.exit(f"[未命中] golden 中无该条款：{key}")
    if "✅" not in block:
        sys.exit(f"[非金标准] {key} 仍为 ⏳ 待核对，不可直接调用；请先 confirm 或回退模式一/二（标待核对）。")
    text = _field(block, "原文")
    source = _field(block, "来源")
    version = _field(block, "版本")
    checked = _field(block, "核对状态")
    print(text)
    print(f"\n[金标准] {key} | 版本：{version} | {checked} | 来源：{source}")
    print("（以上内容来自已人工核对的金标准库，可直接引用，无需重新抓取。）")


# ── mode 3b : abolish ──────────────────────────────────────────────


def cmd_abolish(args):
    """把指定条款从 golden 移至 archive。"""
    key = f"{args.std} 第 {args.clause} 条"

    # 1) 从 golden 文件中找到并移除该条目
    gpath = golden_path(args.std)
    removed_block = None
    if os.path.exists(gpath):
        with open(gpath, encoding="utf-8") as f:
            content = f.read()
        pattern = re.compile(
            rf"(^###\s*{re.escape(key)}.*?)(?=\n### |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        m = pattern.search(content)
        if m:
            removed_block = m.group(0)
            new_content = pattern.sub("", content)
            new_content = re.sub(r"\n{3,}", "\n\n", new_content).strip() + "\n"
            with open(gpath, "w", encoding="utf-8") as f:
                f.write(new_content)

    # 2) 写入 archive
    apath = archive_path(args.std)
    os.makedirs(os.path.dirname(apath), exist_ok=True)

    text_body = args.text or ""
    if removed_block:
        old_m = re.search(r"(?<=原文：).*?(?=来源：|抓取日期|$)", removed_block, re.DOTALL)
        if old_m:
            text_body = old_m.group(0).strip()

    today = datetime.date.today().isoformat()
    block = (
        f"\n### {args.std} 第 {args.clause} 条 [废止]\n"
        f"- 状态：废止\n"
        f"- 废止日期：{args.abolish_date or today}\n"
        f"- 替代标准：{args.replaced_by or '—'}\n"
        f"- 废止依据来源：{args.source}\n"
        f"- 归档日期：{today}\n"
        f"- 原文：（废止前版本）\n{text_body or args.text or '（原文未捕获）'}\n"
        f"- 备注：本条已从活跃金标准库移出，仅作历史追溯。\n"
    )
    with open(apath, "a", encoding="utf-8") as f:
        f.write(block)

    grel = os.path.relpath(gpath, _base()) if os.path.exists(gpath) else "(无金标准)"
    arel = os.path.relpath(apath, _base())
    print(f"[已废止归档] {key}")
    print(f"  golden → {grel} （已移除）")
    print(f"  archive ← {arel} （已入库）")
    if args.replaced_by:
        print(f"  替代标准：{args.replaced_by}")


# ── confirm : 人工核对无误，晋升为 ✅ 金标准 ──────────────────────────


def cmd_confirm(args):
    """人工核对某 golden 条目无误后，将 ⏳ 待人工核对 晋升为 ✅ 金标准。"""
    key = f"{args.std} 第 {args.clause} 条"
    gpath = golden_path(args.std)
    if not os.path.exists(gpath):
        sys.exit(f"[拒绝] golden 中无该条目：{key}")
    with open(gpath, encoding="utf-8") as f:
        content = f.read()
    block = _find_block(content, key)
    if not block:
        sys.exit(f"[拒绝] 未找到条目块：{key}")
    if "✅" in block:
        print(f"[跳过] 该条目已为 ✅：{key}")
        return
    today = datetime.date.today().isoformat()
    new_block = block.replace("⏳ 待人工核对", f"✅ 金标准（{today} 人工核对）")
    content = content.replace(block, new_block)
    with open(gpath, "w", encoding="utf-8") as f:
        f.write(content)
    rel = os.path.relpath(gpath, _base())
    print(f"[已晋升为金标准] {key} → {rel} （✅ 金标准 {today}）")
    print("  该条此后作为本地 ✅ 基准输出，优先级高于在线待核对候选；lookup 可直接调用。")


# ── main ──────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(
        description="金标准库管理：write（写回）/ lookup（直接调用）/ confirm（晋升✅）/ abolish（废止归档）"
    )
    sub = ap.add_subparsers(dest="command")

    # write
    w = sub.add_parser("write", help="联网新条文写回 golden（默认 ⏳ 待核对）")
    w.add_argument("--std", required=True)
    w.add_argument("--clause", required=True)
    w.add_argument("--text", required=True)
    w.add_argument("--source", required=True)
    w.add_argument("--version", default="")
    w.add_argument("--auto", action="store_true")

    # lookup
    lk = sub.add_parser("lookup", help="查询是否已存在 ✅ 金标准条款，命中则直接输出原文")
    lk.add_argument("--std", required=True, help="规范编号")
    lk.add_argument("--clause", required=True, help="条款号")

    # abolish
    ab = sub.add_parser("abolish", help="废止条款从 golden 移入 archive")
    ab.add_argument("--std", required=True, help="规范编号")
    ab.add_argument("--clause", required=True, help="条款号")
    ab.add_argument("--source", required=True, help="废止依据的权威 URL")
    ab.add_argument("--abolish_date", default="", help="官方废止日期（YYYY-MM-DD）")
    ab.add_argument("--replaced_by", default="", help="替代标准编号/名称")
    ab.add_argument("--text", default="", help="废止前的原文（可选，优先从 golden 提取）")

    # confirm
    cf = sub.add_parser("confirm", help="人工核对无误，⏳ 晋升为 ✅ 金标准")
    cf.add_argument("--std", required=True, help="规范编号")
    cf.add_argument("--clause", required=True, help="条款号")

    args = ap.parse_args()

    if args.command == "write":
        cmd_write(args)
    elif args.command == "lookup":
        cmd_lookup(args)
    elif args.command == "abolish":
        cmd_abolish(args)
    elif args.command == "confirm":
        cmd_confirm(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
