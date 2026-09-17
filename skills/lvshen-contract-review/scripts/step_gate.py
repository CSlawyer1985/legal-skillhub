#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 顺序闸门（Step Gate）
============================================================
用途：在审查流程中按序校验「交付物四件套」中间产物，未过闸不得进入下一环节。
    与 validate_output.py（终检）互补：step_gate 管「四件套逐件落盘达标」，
    validate 管「终检全面校验」。二者任一 FAIL = 交付物不得视为完成。
    判定逻辑与 validate_output 共用 scripts/_checks.py（P1-1 修复：单实现双入口，
    杜绝两闸门口径分叉）。

四关（对应交付物四件套）：
  gate elements      要素提取表存在（「要素提取」章节 + 关键要素词命中 ≥5）
  gate table         逐条表行数 ≥ 提取条款数（需 -c 参数）
  gate suggestions   5字段覆盖度（修改建议「### 🔴/🟠」标题数 ≥ 风险分级清单 🔴🟠 行数）
  gate checklist     核对清单存在（「核对清单」+ ✅/⚠️ 结果标记 ≥25）

聚合一致性：--pieces 传入分步落盘的中间产物文件列表，
    校验终稿包含各中间产物的章节标题指纹（防止中间产物与终稿脱节）。

用法：
  python3 scripts/step_gate.py <交付物文件> -c <条款数> [--pieces 中间1 中间2 ...]   # 四关全查（推荐终稿一次过闸）
  python3 scripts/step_gate.py <交付物文件> --all -c <条款数> [--pieces ...]          # 同上，显式全查别名
  python3 scripts/step_gate.py <交付物文件> --gate elements       # 查单关（分步落盘用）
退出码：0=全部 PASS；1=存在 FAIL；2=用法错误。
"""

import os
import re
import sys

# 单实现双入口（P1-1）：判定逻辑唯一源为 _checks.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _checks import (  # noqa: E402
    gate_checklist,
    gate_elements,
    gate_suggestions,
    gate_table,
)


def main():
    args = [a for a in sys.argv[1:]]
    clause_count = None
    gate_filter = None
    pieces = []
    all_flag = "--all" in args
    if all_flag:
        args = [a for a in args if a != "--all"]
    if "--pieces" in args:
        idx = args.index("--pieces")
        rest = args[idx + 1:]
        consume = 0  # 已作为 pieces 消费的参数个数
        for a in rest:
            if a.startswith("-"):
                break
            pieces.append(a)
            consume += 1
        # 保留剩余参数（含选项及其取值，如 -c 67）供后续解析
        args = args[:idx] + rest[consume:]
    if "-c" in args:
        idx = args.index("-c")
        try:
            clause_count = int(args[idx + 1])
            args = args[:idx] + args[idx + 2:]
        except (ValueError, IndexError):
            print("用法: python3 scripts/step_gate.py <交付物文件> [-c 条款数] [--all|--gate 关名] [--pieces 中间产物...]")
            sys.exit(2)
    if "--gate" in args:
        if all_flag:
            print("用法: --all 与 --gate 互斥（--all = 四关全查；--gate = 单关）")
            sys.exit(2)
        idx = args.index("--gate")
        if idx + 1 >= len(args):
            print("用法: python3 scripts/step_gate.py <交付物文件> [-c 条款数] [--all|--gate 关名] [--pieces 中间产物...]")
            sys.exit(2)
        gate_filter = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if len(args) < 1:
        print("用法: python3 scripts/step_gate.py <交付物文件> [-c 条款数] [--all|--gate 关名] [--pieces 中间产物...]")
        sys.exit(2)
    path = args[0]
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:  # noqa: BLE001
        print(f"无法读取文件: {e}")
        sys.exit(2)

    gates = [
        ("elements", "G1 要素提取表", lambda: gate_elements(content)),
        ("table", "G2 逐条表覆盖", lambda: gate_table(content, clause_count) if clause_count else (False, "table 关需要 -c 条款数参数")),
        ("suggestions", "G3 5字段覆盖度", lambda: gate_suggestions(content)),
        ("checklist", "G4 核对清单", lambda: gate_checklist(content)),
    ]

    print("=" * 58)
    print("律审·合同审查1.0 顺序闸门（Step Gate）")
    print("=" * 58)
    fails = []
    for key, name, fn in gates:
        if gate_filter and key != gate_filter:
            continue
        ok, detail = fn()
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        if detail:
            print(f"      └─ {detail}")
        if not ok:
            fails.append(name)

    # G5 聚合一致性：终稿须包含各中间产物章节标题指纹（防中间产物与终稿脱节）
    if pieces and (not gate_filter or gate_filter == "pieces"):
        missing_pieces = []
        for p in pieces:
            if not os.path.exists(p):
                missing_pieces.append(f"{p}（文件不存在）")
                continue
            with open(p, encoding="utf-8") as f:
                piece_text = f.read()
            title_m = re.search(r"^#{1,3}\s+.+$", piece_text, re.M)
            fingerprint = title_m.group(0).strip() if title_m else os.path.basename(p)
            if fingerprint not in content:
                missing_pieces.append(f"{os.path.basename(p)}（缺章节指纹「{fingerprint}」）")
        if missing_pieces:
            print("[FAIL] G5 聚合一致性（终稿含中间产物指纹）")
            print(f"      └─ 缺失: {missing_pieces}")
            fails.append("G5 聚合一致性")
        else:
            print(f"[PASS] G5 聚合一致性（终稿含 {len(pieces)} 个中间产物指纹）")

    print("-" * 58)
    if fails:
        print(f"总体状态: FAIL（未过闸: {', '.join(fails)}）→ 补齐对应环节产物后重跑，禁止进入下一环节")
        sys.exit(1)
    print("总体状态: PASS → 四件套中间产物齐备，可进入终检（validate_output.py）")
    sys.exit(0)


if __name__ == "__main__":
    main()
