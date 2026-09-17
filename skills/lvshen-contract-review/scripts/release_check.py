#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 对外发布检查（Release Check）
============================================================
用途：对外分享/发布前运行，扫描技能库全部文件，检测「命名与语言规范」违规项。
     FAIL 或未运行 = 不得对外发布。
检测项：
  R1 版本印记词：重建版/补全版/恢复版/返工/瘦身/沙箱/丢失/待恢复（全库）
  R2 内部过程词：教训/试验/内部记忆机制/内部类型标记/内部知识沉淀（内容文件）
  R3 内部编号：O-0x、R-0x、TC/CM、回链（内容文件；脚本代码内规则定义豁免）
  R4 内部路径：/sandbox/（全库，排除自身）
  R5 PII：手机号/身份证/银行卡（全库，剔除 URL 后检测）
范围：SKILL.md + references/ + assets/ + tests/fixtures/（内容文件）；
      scripts/ + tests/run_tests.py 仅查 R1/R4/R5（代码内引用禁用词属规则定义，豁免 R2/R3）
用法：python3 scripts/release_check.py
退出码：0=PASS（可对外发布）；1=FAIL（禁止发布）。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _checks import pii_hits_of  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF_NAME = os.path.basename(__file__)

# 全库检测（所有文件）
VERSION_MARKS = ["重建版", "补全版", "恢复版", "返工", "瘦身", "沙箱", "丢失", "待恢复"]
INTERNAL_PATHS = ["/sandbox/"]

# 内容文件检测（.md 文档）
INTERNAL_WORDS = ["教训", "试验", "内部记忆机制", "内部类型标记", "内部知识沉淀"]
INTERNAL_CODES = [r"O-0\d", r"R-0\d", r"TC/CM", r"回链"]

# 内容文件清单（.md 文档）
CONTENT_FILES = ["SKILL.md"] + \
    [os.path.join("references", f) for f in os.listdir(os.path.join(BASE, "references")) if f.endswith(".md")] + \
    [os.path.join("assets", f) for f in os.listdir(os.path.join(BASE, "assets")) if f.endswith(".md")] + \
    [os.path.join("tests", "fixtures", f) for f in os.listdir(os.path.join(BASE, "tests", "fixtures")) if f.endswith(".md")]


def all_files():
    """全库文件（排除自身）"""
    for root, dirs, files in os.walk(BASE):
        # 排除 tests 外的脚本目录不豁免——scripts 全部文件参与全库检测
        for fname in files:
            if fname == SELF_NAME:
                continue
            yield os.path.relpath(os.path.join(root, fname), BASE)


def read_content(rel):
    """读取文件内容；SKILL.md 豁免「命名与语言规范」章节（该章节为规则定义本身）。"""
    path = os.path.join(BASE, rel)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if rel == "SKILL.md":
        start = text.find("## 命名与语言规范")
        if start >= 0:
            end = text.find("## ", start + 2)
            if end < 0:
                end = len(text)
            text = text[:start] + text[end:]
    return text


def main():
    fails = []

    # ── R1 版本印记词（全库） ──────────────────────────────────────────
    r1_hits = []
    for rel in all_files():
        try:
            text = read_content(rel)
        except Exception:
            continue
        for w in VERSION_MARKS:
            if w in text:
                r1_hits.append(f"{rel}: 「{w}」")
    if r1_hits:
        fails.append("R1 版本印记词")
        for h in r1_hits[:10]:
            print(f"  [FAIL R1] {h}")

    # ── R4 内部路径（全库） ────────────────────────────────────────────
    r4_hits = []
    for rel in all_files():
        try:
            text = read_content(rel)
        except Exception:
            continue
        for p in INTERNAL_PATHS:
            if p in text:
                r4_hits.append(f"{rel}: 「{p}」")
    if r4_hits:
        fails.append("R4 内部路径")
        for h in r4_hits[:10]:
            print(f"  [FAIL R4] {h}")

    # ── R5 PII（全库，剔除 URL；与 validate V13 共用 pii_hits_of 收紧版） ─────
    r5_hits = []
    for rel in all_files():
        try:
            text = read_content(rel)
        except Exception:
            continue
        pii_hits = pii_hits_of(text)
        for name, found in pii_hits.items():
            r5_hits.append(f"{rel}: {name} {found[:2]}")
    if r5_hits:
        fails.append("R5 PII 泄露")
        for h in r5_hits[:10]:
            print(f"  [FAIL R5] {h}")

    # ── R2 内部过程词（内容文件） ──────────────────────────────────────
    r2_hits = []
    for rel in CONTENT_FILES:
        path = os.path.join(BASE, rel)
        if not os.path.exists(path):
            continue
        text = read_content(rel)
        for w in INTERNAL_WORDS:
            if w in text:
                r2_hits.append(f"{rel}: 「{w}」")
    if r2_hits:
        fails.append("R2 内部过程词")
        for h in r2_hits[:10]:
            print(f"  [FAIL R2] {h}")

    # ── R3 内部编号（内容文件） ────────────────────────────────────────
    r3_hits = []
    for rel in CONTENT_FILES:
        path = os.path.join(BASE, rel)
        if not os.path.exists(path):
            continue
        text = read_content(rel)
        for pat in INTERNAL_CODES:
            m = re.search(pat, text)
            if m:
                r3_hits.append(f"{rel}: 「{m.group(0)}」")
    if r3_hits:
        fails.append("R3 内部编号")
        for h in r3_hits[:10]:
            print(f"  [FAIL R3] {h}")

    # ── 汇总 ───────────────────────────────────────────────────────────
    print("=" * 58)
    print("律审·合同审查1.0 对外发布检查（Release Check）")
    print("=" * 58)
    for name in ["R1 版本印记词", "R2 内部过程词", "R3 内部编号", "R4 内部路径", "R5 PII 泄露"]:
        ok = name not in fails
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 58)
    if fails:
        print(f"总体状态: FAIL（{len(fails)} 项未过: {', '.join(fails)}）→ 禁止对外发布，先清理后重跑")
        sys.exit(1)
    print("总体状态: PASS → 符合命名与语言规范，可对外发布")
    sys.exit(0)


if __name__ == "__main__":
    main()
