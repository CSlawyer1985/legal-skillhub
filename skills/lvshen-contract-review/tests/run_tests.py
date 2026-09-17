#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 回归测试（Regression Tests）
============================================================
用途：技能升级（尤其 scripts 校验项新增/修改）后运行，验证既有校验规则未被破坏。
    防「升级引入误伤」——校验规则变更后须回归验证：守护脚本应保持 PASS、完整版样例应放行、
    偷工版样例应拦截、边界样例（含 URL/证据标记等）应不受影响。本脚本将三类样例固化为回归资产。

覆盖范围：
  - 守护脚本回归：preflight_check（入场守护）、release_check（发布合规）应保持 PASS
  - 交付物样例回归：完整版样例应 PASS、偷工版样例应 FAIL、边界样例应 PASS（step_gate + validate 双测）
  - 提取器回归（P1-2）：数字编号/表格化合同提取数不得低估（≥ 阈值）
  - 长合同回归（P3-3）：30+ 条款长文本行为（性能 + 跨页表头式结构）
  - 数字密集回归（P2-4）：单号/序列号/日期密集场景 V13 不误报

用法：python3 tests/run_tests.py [--verbose]
退出码：0=全部 PASS（可重注册）；1=存在 FAIL（禁止重注册，先修复）。
"""

import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(BASE, "tests", "fixtures")

# 守护脚本回归：(名称, 命令, 期望结果)——技能升级不得破坏入口守护与发布合规
GUARD_CHECKS = [
    ("preflight_check（入场守护）", ["python3", "scripts/preflight_check.py"], True),
    ("release_check（发布合规）", ["python3", "scripts/release_check.py"], True),
]

# 交付物样例回归：(fixture 文件名, 期望 step_gate, 期望 validate, 说明, 条款数或 None=默认6)
CASES = [
    ("完整版样例.md", True, True, "四件套齐全，应全 PASS", 6),
    ("偷工版样例.md", False, False, "缺四件套/空泛自校验，应 FAIL", 6),
    ("边界样例.md", True, True, "含 URL 链接/证据标记，应全 PASS 不误伤", 6),
    ("悬空引用样例.md", True, False, "🔴99 引用不存在（编号重排后交叉引用未同步），validate V14 应 FAIL", 6),
    ("附件断裂样例.md", True, False, "引用「附件一」但无对应章节（附件缺条），validate V14 应 FAIL", 6),
    ("长合同样例.md", True, True, "30+ 条长合同交付物（P3-3 长文本/性能回归），应全 PASS", 30),
    ("数字密集样例.md", True, True, "单号/序列号/日期/金额密集（P2-4 V13 收紧不误报），应全 PASS", 6),
]

# 提取器回归（P1-2）：数字编号/表格合同提取数下限
EXTRACT_CASES = [
    ("数字条款合同样例.md", 15, "数字层级/表格条款号/阿拉伯「第X条」应全部识别，N 不得低估"),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def extract_count(fname):
    path = os.path.join(FIXTURES, fname)
    r = subprocess.run(["python3", "scripts/extract_clauses.py", path],
                       capture_output=True, text=True, cwd=BASE)
    m = re.search(r"共提取 (\d+) 个疑似条款编号", r.stdout)
    return int(m.group(1)) if m else -1


def main():
    verbose = "--verbose" in sys.argv
    fails = []
    print("=" * 72)
    print("律审·合同审查1.0 回归测试（Regression Tests）")
    print("=" * 72)

    # ── 守护脚本回归 ──────────────────────────────────────────────
    for name, cmd, want in GUARD_CHECKS:
        ok, out = run(cmd)
        passed = (ok == want)
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}（期望 {'PASS' if want else 'FAIL'}）{'✓' if passed else '✗'}")
        if not passed:
            fails.append(name)
        if verbose and not passed:
            print(out)

    # ── 交付物样例回归 ────────────────────────────────────────────
    for fname, want_gate, want_val, desc, clause_count in CASES:
        path = os.path.join(FIXTURES, fname)
        if not os.path.exists(path):
            print(f"[FAIL] {fname}：fixture 文件缺失（{path}）")
            fails.append(fname)
            continue
        gate_ok, gate_out = run(["python3", "scripts/step_gate.py", path, "--all", "-c", str(clause_count)])
        val_ok, val_out = run(["python3", "scripts/validate_output.py", path, "-c", str(clause_count)])
        gate_pass = (gate_ok == want_gate)
        val_pass = (val_ok == want_val)
        status = "PASS" if (gate_pass and val_pass) else "FAIL"
        print(f"[{status}] {fname}（-c {clause_count}）")
        print(f"      ├─ step_gate --all: {'PASS' if gate_ok else 'FAIL'}（期望 {'PASS' if want_gate else 'FAIL'}）{'✓' if gate_pass else '✗'}")
        print(f"      ├─ validate: {'PASS' if val_ok else 'FAIL'}（期望 {'PASS' if want_val else 'FAIL'}）{'✓' if val_pass else '✗'}")
        print(f"      └─ {desc}")
        if not gate_pass or not val_pass:
            fails.append(fname)
        if verbose and (not gate_pass or not val_pass):
            print("      --- step_gate 输出 ---")
            print(gate_out)
            print("      --- validate 输出 ---")
            print(val_out)

    # ── 提取器回归（P1-2） ────────────────────────────────────────
    for fname, min_count, desc in EXTRACT_CASES:
        path = os.path.join(FIXTURES, fname)
        if not os.path.exists(path):
            print(f"[FAIL] {fname}：fixture 文件缺失（{path}）")
            fails.append(fname)
            continue
        n = extract_count(fname)
        passed = n >= min_count
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] extract_clauses {fname}：提取 {n} ≥ {min_count}（{desc}）{'✓' if passed else '✗'}")
        if not passed:
            fails.append(fname)

    print("-" * 72)
    if fails:
        print(f"总体状态: FAIL（{len(fails)} 项未达预期: {', '.join(fails)}）")
        print("处理：先修复脚本或样例，直至全部 PASS，禁止重注册")
        sys.exit(1)
    print("总体状态: PASS → 既有校验与守护脚本均未被破坏，可进入重注册")
    sys.exit(0)


if __name__ == "__main__":
    main()
