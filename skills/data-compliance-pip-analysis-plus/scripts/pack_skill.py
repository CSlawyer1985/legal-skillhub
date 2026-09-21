#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包校验脚本：将本技能打包为 zip，并校验 SkillHub 发布约束。

约束（与 SkillHub 技能包规范一致）：
  1. 必须包含 SKILL.md（位于技能根目录）
  2. 文件总数 <= 200
  3. 总大小 <= 10.00 MB（10 * 1024 * 1024 字节）

用法：
  python3 pack_skill.py
  python3 pack_skill.py --output /path/to/out.zip

说明：
  - 仅打包本技能目录内的文件；自动排除本脚本自身、已生成的 .zip、
    隐藏文件/目录（.DS_Store、.git、__pycache__ 等）。
  - 校验通过才会写出 zip；任一约束不满足则退出码非 0，并提示原因。
"""

import os
import sys
import zipfile
import argparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_FILES = 200
MAX_SIZE = 10 * 1024 * 1024  # 10.00 MB

# 打包时排除的文件名 / 扩展名 / 前缀
EXCLUDE_NAMES = {os.path.basename(__file__), "pack_skill.py"}
EXCLUDE_EXT = {".zip"}
HIDDEN_PREFIXES = (".",)


def collect_files():
    collected = []
    for root, dirs, names in os.walk(SKILL_DIR):
        # 排除隐藏目录（.git / __pycache__ / .DS_Store 目录等）
        dirs[:] = [d for d in dirs if not d.startswith(HIDDEN_PREFIXES)]
        for n in names:
            if n.startswith(HIDDEN_PREFIXES):
                continue
            full = os.path.join(root, n)
            rel = os.path.relpath(full, SKILL_DIR)
            if os.path.basename(full) in EXCLUDE_NAMES:
                continue
            if os.path.splitext(n)[1].lower() in EXCLUDE_EXT:
                continue
            collected.append((full, rel))
    return collected


def main():
    parser = argparse.ArgumentParser(description="打包并校验本技能是否符合发布约束")
    default_out = os.path.expanduser(
        "~/Desktop/人工智能（AI）、数据合规与个人信息保护法律分析Plus.zip"
    )
    parser.add_argument("--output", default=default_out, help="输出 zip 路径")
    args = parser.parse_args()

    files = collect_files()
    total = sum(os.path.getsize(f) for f, _ in files)

    print("=== 发布约束校验 ===")
    print(f"文件总数: {len(files)}  (上限 {MAX_FILES})")
    print(f"总大小:   {total/1024/1024:.2f} MB  (上限 10.00 MB)")
    has_skill = any(rel == "SKILL.md" for _, rel in files)
    print(f"根目录 SKILL.md 存在: {has_skill}")

    ok = True
    if not has_skill:
        print("✗ 缺少根目录 SKILL.md")
        ok = False
    if len(files) > MAX_FILES:
        print(f"✗ 文件数超限: {len(files)} > {MAX_FILES}")
        ok = False
    if total > MAX_SIZE:
        print(f"✗ 总大小超限: {total} 字节 > {MAX_SIZE} 字节")
        ok = False

    if not ok:
        print("\n未通过约束，已停止打包。")
        sys.exit(1)

    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for full, rel in sorted(files, key=lambda x: x[1]):
            z.write(full, rel)

    print(f"\n✓ 校验通过，已生成压缩包:\n  {out}")
    print(f"  压缩包内文件数: {len(files)} | 原始总大小: {total/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()
