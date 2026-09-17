#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 条款提取辅助脚本（Clause Extractor）
============================================================
用途：审查开始前运行，从合同文本提取「疑似条款编号清单」（含正文引用的条款号），
      辅助 AI 核对逐条表全覆盖，防止漏扫条款或漏核引用条款。
规则：提取结果为【疑似清单】供 AI 对照，AI 须人工判断哪些是条款定义、哪些是正文引用；
      逐条表须覆盖清单中全部条款编号（正文引用的条款号亦须核验对应关系）。
用法：python3 extract_clauses.py <合同文本文件路径>
退出码：0=正常；2=用法错误。
"""

import re
import sys

# P1-2 修复：识别宽度扩展——中文/阿拉伯数字「第X条」（含空格变体）、
# 「1.1」式数字层级、表格化合同条款号、括号编号、正文引用。
# 结果为【疑似清单】供 AI 对照，宁多勿漏（逐条表 ≥ N 是硬校验，N 低估 = 漏扫风险）。
PATTERNS = [
    ("章节（中文序号）", re.compile(r"^[一二三四五六七八九十]+、")),
    ("条款（第X条·中文）", re.compile(r"第[一二三四五六七八九十百零〇]+条")),
    ("条款（第X条·数字）", re.compile(r"第\s*\d+(?:\.\d+)*\s*条")),
    ("数字层级", re.compile(r"^\d+(?:\.\d+)*[、.．]?")),
    ("表格条款号", re.compile(r"^\|\s*\d+(?:\.\d+)*\s*\|")),
    ("括号编号", re.compile(r"^[（(]\d+[)）]")),
    ("正文引用（X.X款）", re.compile(r"[通专]用条款\s*\d+(?:\.\d+)*\s*款")),
]


def main():
    if len(sys.argv) < 2:
        print("用法: python3 extract_clauses.py <合同文本文件路径>")
        sys.exit(2)
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:  # noqa: BLE001
        print(f"无法读取文件: {e}")
        sys.exit(2)

    results = []  # (line_no, label, matched, preview)
    seen = set()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        for label, pat in PATTERNS:
            m = pat.search(stripped)
            if m:
                key = (label, m.group(0))
                if key not in seen:
                    seen.add(key)
                    results.append((i, label, m.group(0), stripped[:60]))
                break  # 每行只取第一个匹配

    print("=" * 58)
    print("律审·合同审查1.0 条款提取辅助（Clause Extractor · 供逐条表对照）")
    print("=" * 58)
    print(f"共提取 {len(results)} 个疑似条款编号（含正文引用，供逐条表全覆盖核对）：")
    print("-" * 58)
    for line_no, label, matched, preview in results:
        print(f"L{line_no:>4} [{label}] {matched}  |  {preview}")
    print("-" * 58)
    print("提示：逐条表须覆盖上表全部条款编号；正文引用的条款号须核验对应关系（交叉回溯）。")


if __name__ == "__main__":
    main()
