#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符纠错记忆（skill 记忆 / term memory）。

PDF 文字层常有字符级损坏——典型根因是子集化字体的 ToUnicode CMap 错乱，
把「大于」渲染成「大千」、"㎡" 缺失等。这类错误 regex 修不了、也绝不能凭
上下文臆测填补。

工作流程（对应 SKILL.md「模式四 · 术语记忆回流」）：
  1. extract_pdf.py 抽取时若命中已知错字，应用记忆并标 ⚠️ 提示人工核对；
  2. 人工核对后确认正字 → agent 调用本工具 `add` 沉淀「错字 → 正字」；
  3. 下次 extract_pdf.py 自动加载本记忆，持续提升准确率，形成闭环。

**只收录人工确认过的映射，绝不臆测。**

子命令：
  add     --wrong <错字> --right <正字> [--std 规范] [--clause 条款] [--note 备注]
  list
  remove  --wrong <错字> --right <正字>
"""

import re
import sys
import os
import argparse
import datetime

MEMORY_FILE = "references/term_memory.md"

HEADER = """# 字符纠错记忆（人工核对沉淀 · skill 记忆）

> 由 `scripts/term_memory.py add` 写入。**只收录人工确认过的「错字 → 正字」映射，绝不臆测。**
> PDF 文字层损坏（ToUnicode CMap 错乱）是系统性问题，人工核对确认后沉淀此处，
> `extract_pdf.py` 下次运行会自动加载并应用，持续提升抽取准确率。
>
> 行格式：`- `错字` → `正字` | 来源：<规范/条款> | 核对：<YYYY-MM-DD> | 备注：<可选>`
>
> ⚠️ 本文件是「skill 记忆」的载体：每条都是人工核对后的结论，不是机器猜测。

## 映射表
"""


def _base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def memory_path():
    return os.path.join(_base(), MEMORY_FILE)


def ensure_file():
    p = memory_path()
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(HEADER)
    return p


def parse_fixes(path):
    """返回 {(wrong, right): 原始行}，用于去重与展示。
    只认条目行（以「- 」开头的列表项），跳过标题/引用块/示例行。"""
    fixes = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip().startswith("- "):
                continue
            if "→" not in line or "`" not in line:
                continue
            m = re.search(r"`([^`]+)`\s*→\s*`([^`]+)`", line)
            if m:
                fixes[(m.group(1), m.group(2))] = line.rstrip("\n")
    return fixes


def cmd_add(args):
    if not args.wrong or not args.right:
        sys.exit("[拒绝] --wrong / --right 均不可为空")
    if args.wrong == args.right:
        sys.exit("[拒绝] 错字与正字相同，无需记录")
    if len(args.wrong) > 20 or len(args.right) > 20:
        sys.exit("[拒绝] 映射片段过长（>20字），请只录最小可定位的错字片段")
    p = ensure_file()
    fixes = parse_fixes(p)
    key = (args.wrong, args.right)
    if key in fixes:
        print(f"[跳过] 已存在该映射：`{args.wrong}` → `{args.right}`")
        return
    today = datetime.date.today().isoformat()
    src = args.std or "—"
    if args.clause:
        src += f" 第 {args.clause} 条"
    note = f" | 备注：{args.note}" if args.note else ""
    entry = f"- `{args.wrong}` → `{args.right}` | 来源：{src} | 核对：{today}{note}\n"
    with open(p, "a", encoding="utf-8") as f:
        f.write(entry)
    rel = os.path.relpath(p, _base())
    print(f"[已沉淀 skill 记忆] `{args.wrong}` → `{args.right}` → {rel}")
    print(f"  下次 extract_pdf.py 运行将自动应用此纠错（并仍标 ⚠️ 供核对）。")


def cmd_list(args):
    p = memory_path()
    if not os.path.exists(p):
        print("(暂无字符纠错记忆)")
        return
    fixes = parse_fixes(p)
    if not fixes:
        print("(暂无字符纠错记忆)")
        return
    print(f"已沉淀字符纠错映射（共 {len(fixes)} 条）：")
    for line in fixes.values():
        print(f"  {line}")


def cmd_remove(args):
    p = memory_path()
    if not os.path.exists(p):
        sys.exit("[拒绝] 记忆文件不存在")
    key = (args.wrong, args.right)
    lines = open(p, encoding="utf-8").read().splitlines(keepends=True)
    out, removed = [], False
    for ln in lines:
        m = re.search(r"`([^`]+)`\s*→\s*`([^`]+)`", ln)
        if m and (m.group(1), m.group(2)) == key:
            removed = True
            continue
        out.append(ln)
    if not removed:
        sys.exit(f"[拒绝] 未找到映射：`{args.wrong}` → `{args.right}`")
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(out)
    print(f"[已移除] `{args.wrong}` → `{args.right}`")


def main():
    ap = argparse.ArgumentParser(description="字符纠错记忆（skill 记忆）")
    sub = ap.add_subparsers(dest="command")

    a = sub.add_parser("add", help="新增人工确认的纠错映射")
    a.add_argument("--wrong", required=True, help="PDF 中的错字片段")
    a.add_argument("--right", required=True, help="人工核对后的正字片段")
    a.add_argument("--std", default="", help="来源规范编号（可选）")
    a.add_argument("--clause", default="", help="条款号（可选）")
    a.add_argument("--note", default="", help="备注（可选）")

    sub.add_parser("list", help="列出全部映射")

    rm = sub.add_parser("remove", help="删除某条映射（误录时）")
    rm.add_argument("--wrong", required=True)
    rm.add_argument("--right", required=True)

    args = ap.parse_args()
    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "remove":
        cmd_remove(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
