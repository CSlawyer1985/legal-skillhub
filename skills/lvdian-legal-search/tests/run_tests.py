#!/usr/bin/env python3
"""
律典·法律检索 回归测试入口（tests/ 层）
========================================
作用：任何脚本升级或 SKILL.md 结构调整后，必须运行本脚本，
      全 PASS 才允许重注册（防升级破坏既有校验——律审 V10 误伤/V13 误报教训）。

测试项：
  T1  validate_output 对合规样例（fixtures/valid_output.md）应 PASS（退出码 0）
  T2  validate_output 对违规样例（fixtures/invalid_output.md）应 FAIL（退出码 1）
  T3  preflight_check 入场预检应 PASS（退出码 0，需外网可达 flk）
  T4  flk_search 检索应命中并返回直链（退出码 0，需外网可达 flk）
  T5  common-laws 回灌的 flk detail id 格式校验（32 位十六进制，静态扫描 references/common-laws.md）
  T6  validate_output 对「法条卡+层级覆盖自检表」共存样例应 PASS（P1-1 C2 修复回归，纯本地无网络）
  T7  flk_search 候选分级：检索已废止国家条例仅地方命中时应输出警示（P2 回归，需外网；断言 stdout 含
      「国家层面」或替代警示「征收与补偿」）
  T8  flk_search 新法替代追踪：检索旧《危险化学品安全管理条例》应输出新法替代警示（P1 回归，需外网；
      断言 stdout 含「危险化学品安全法」）
  T9  validate_output 用户引文豁免：含「**用户提问**」简称回放的样例应 PASS（P6 回归，纯本地无网络）
  T10 validate_output 第三方域名黑名单：含 findlaw.cn 来源链接的样例应 FAIL（C10 回归，纯本地无网络）

用法：
  python3 tests/run_tests.py

退出码：0 = 全 PASS（允许重注册）；1 = 有 FAIL（禁止重注册）。
幂等只读。
"""

import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)  # 技能根目录


def run_case(script: str, args: list, expect_code: int):
    """运行脚本并断言退出码。"""
    cmd = [sys.executable, os.path.join(ROOT, script)] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        ok = r.returncode == expect_code
        last = [l for l in r.stdout.strip().splitlines() if l.strip()][-1] if r.stdout.strip() else "(无输出)"
        return ok, f"期望={expect_code} 实际={r.returncode} | {last}"
    except subprocess.TimeoutExpired:
        return False, "超时"


def run_case_grep(script: str, args: list, patterns: list):
    """运行脚本并断言 stdout 含任一关键词（用于 flk_search 分级/替代提示回归）。"""
    cmd = [sys.executable, os.path.join(ROOT, script)] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        out = r.stdout
        hit = [p for p in patterns if p in out]
        ok = len(hit) > 0
        detail = f"命中关键词={hit}" if ok else f"未命中 {patterns}；stdout尾行: {out.strip().splitlines()[-1] if out.strip() else '(无输出)'}"
        return ok, detail
    except subprocess.TimeoutExpired:
        return False, "超时"


def run_static(name: str, text: str, pattern: re.Pattern, transform=lambda m: m.group(0)):
    """静态扫描：text 中所有匹配 pattern 的内容须通过 transform 校验，返回 (是否通过, 说明)。"""
    found = pattern.findall(text)
    # findall 带捕获组时返回字符串列表；无捕获组时返回完整匹配串列表；均不含 match 对象
    vals = [m if isinstance(m, str) else m.group(0) for m in found]
    bad = [v for v in vals if not re.fullmatch(r"[0-9a-fA-F]{24,40}", v)]
    ok = len(bad) == 0
    detail = f"id 数={len(vals)}、格式异常={len(bad)}" + ("" if ok else f" 异常id={bad[:3]}")
    return ok, detail


def main():
    print("=" * 64)
    print("律典·法律检索 回归测试报告")
    print("=" * 64)
    results = []

    # T1: 合规样例应 PASS
    ok, detail = run_case("scripts/validate_output.py",
                          ["--file", os.path.join(SCRIPT_DIR, "fixtures", "valid_output.md")], 0)
    results.append(("T1 validate_output 合规样例应PASS", ok, detail))

    # T2: 违规样例应 FAIL
    ok, detail = run_case("scripts/validate_output.py",
                          ["--file", os.path.join(SCRIPT_DIR, "fixtures", "invalid_output.md")], 1)
    results.append(("T2 validate_output 违规样例应FAIL", ok, detail))

    # T3: preflight 应 PASS
    ok, detail = run_case("scripts/preflight_check.py", [], 0)
    results.append(("T3 preflight 入场预检应PASS", ok, detail))

    # T4: flk_search 应命中
    ok, detail = run_case("scripts/flk_search.py", ["--name", "中华人民共和国行政处罚法"], 0)
    results.append(("T4 flk_search 检索应PASS", ok, detail))

    # T5: common-laws 回灌 id 格式校验（静态扫描，无网络）
    cl_path = os.path.join(ROOT, "references", "common-laws.md")
    cl_text = open(cl_path, encoding="utf-8").read()
    ok, detail = run_static("T5", cl_text, re.compile(r"detail\?id=([0-9a-fA-F]{20,40})"))
    results.append(("T5 common-laws 回灌id格式校验", ok, detail))

    # T6: 法条卡+层级覆盖自检表 共存应 PASS（P1-1 回归，纯本地）
    ok, detail = run_case("scripts/validate_output.py",
                          ["--file", os.path.join(SCRIPT_DIR, "fixtures", "valid_with_selfcheck.md")], 0)
    results.append(("T6 法条卡+层级自检表共存应PASS(P1-1回归)", ok, detail))

    # T7: flk_search 候选分级（P2 回归）：已废止国家条例仅地方命中 → 输出警示
    ok, detail = run_case_grep("scripts/flk_search.py",
                               ["--name", "城市房屋拆迁管理条例"],
                               ["国家层面", "征收与补偿"])
    results.append(("T7 flk_search 地方条例命中输出警示(P2回归)", ok, detail))

    # T8: flk_search 新法替代追踪（P1 回归）：旧危化品条例 → 输出新法警示
    ok, detail = run_case_grep("scripts/flk_search.py",
                               ["--name", "危险化学品安全管理条例"],
                               ["危险化学品安全法"])
    results.append(("T8 flk_search 新法替代警示输出(P1回归)", ok, detail))

    # T9: validate_output 用户引文豁免（P6 回归，纯本地）
    ok, detail = run_case("scripts/validate_output.py",
                          ["--file", os.path.join(SCRIPT_DIR, "fixtures", "valid_with_user_quote.md")], 0)
    results.append(("T9 用户引文简称豁免应PASS(P6回归)", ok, detail))

    # T10: validate_output 第三方域名黑名单（C10 回归，纯本地）
    ok, detail = run_case("scripts/validate_output.py",
                          ["--file", os.path.join(SCRIPT_DIR, "fixtures", "invalid_with_thirdparty.md")], 1)
    results.append(("T10 第三方域名黑名单应FAIL(C10回归)", ok, detail))

    print("-" * 64)
    all_pass = True
    for name, ok, detail in results:
        mark = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_pass = False
        print(f"  [{mark}] {name}: {detail}")
    print("-" * 64)
    if all_pass:
        print("✅ 回归测试全 PASS：允许重注册。")
        sys.exit(0)
    else:
        print("❌ 回归测试有 FAIL：禁止重注册，修复后重跑。")
        sys.exit(1)


if __name__ == "__main__":
    main()
