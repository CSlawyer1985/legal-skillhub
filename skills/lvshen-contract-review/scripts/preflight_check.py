#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 运行守护前置校验脚本（Runtime Guard Preflight）
============================================================
用途：P1-P7 前置校验（加载守护 + 环境守护）的【代码强制】执行载体。
规则：审查开始前必须运行本脚本（幂等只读、安全可重复）；输出 PASS 方可进入审查流程，
      FAIL 或未运行 = 禁止进入审查流程，须修复后重跑直至 PASS。
设计背景：执行环节存在「声称已执行但实际未执行」的风险——纯文字指令为软约束，执行者可能误以为已执行而跳过步骤；本脚本输出为确定性结果（PASS/FAIL），无法伪装通过，为流程入口提供代码级强制校验。

用法：python3 preflight_check.py
退出码：0=PASS（可进入审查）；1=FAIL（禁止进入审查）。
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # SKILL 根目录
GUARD_MARK = "运行铁律"  # 守护标记（SKILL.md 须含此特征词）

CHECKS = []  # 每项: (name, ok, detail)


def check(name, ok, detail=""):
    CHECKS.append({"name": name, "ok": bool(ok), "detail": detail})


def main():
    # ── P1 SKILL.md 存在 + 守护协议完整性 ──────────────────────────────
    skill_path = os.path.join(BASE, "SKILL.md")
    if os.path.exists(skill_path) and os.path.getsize(skill_path) > 1000:
        with open(skill_path, encoding="utf-8") as f:
            content = f.read()
        markers = [
            "运行铁律",
            "逐条表",
            "法条双轨核验",
            "自校验",
            "preflight_check.py",
            "extract_clauses.py",
            "validate_output.py",
        ]
        missing = [m for m in markers if m not in content]
        guard_ok = "运行铁律" in content
        if not missing and guard_ok:
            check("P1 SKILL.md 存在且含运行守护（轻量版） + 守护标记",
                  True, f"完整（含 {GUARD_MARK}）")
        else:
            detail = []
            if missing:
                detail.append(f"缺失标记: {missing}")
            if not guard_ok:
                detail.append(f"未含守护标记 {GUARD_MARK}")
            check("P1 SKILL.md 存在且含运行守护（轻量版） + 守护标记", False, "；".join(detail))
    else:
        check("P1 SKILL.md 存在且含运行守护（轻量版） + 守护标记",
              False, f"SKILL.md 不存在或过小: {skill_path}")

    # ── P2-P4 references 三文件存在且非空 ──────────────────────────────
    refs = {
        "clause-library.md": "条款库（模板）",
        "core-checklist.md": "主核对清单",
        "omission-checklist.md": "场景专项（标⭐高频项）",
    }
    for i, (fname, label) in enumerate(refs.items(), start=2):
        p = os.path.join(BASE, "references", fname)
        ok = os.path.exists(p) and os.path.getsize(p) > 100
        check(f"P{i} references/{fname}（{label}）",
              ok, "OK" if ok else "缺失或为空（<100B）")

    # ── P5 frontmatter settings 字段（注册配置关键） ─────────────────────
    try:
        with open(skill_path, encoding="utf-8") as f:
            head = f.read(2000)
        has_settings = "settings:" in head and ("fast_max" in head or "deep_min" in head)
        check("P5 frontmatter settings 字段存在（深度阈值配置）",
              has_settings, "OK" if has_settings else "缺失（config 为保留字段名，须用 settings）")
    except Exception as e:  # noqa: BLE001
        check("P5 frontmatter settings 字段存在（深度阈值配置）", False, str(e))

    # ── P6 step_gate.py 存在且非空（v2 新增：顺序闸门脚本） ───────────────
    step_gate_path = os.path.join(BASE, "scripts", "step_gate.py")
    sg_ok = os.path.exists(step_gate_path) and os.path.getsize(step_gate_path) > 500
    check("P6 scripts/step_gate.py 存在且非空（顺序闸门）",
          sg_ok, "OK" if sg_ok else "缺失或过小（<500B）")

    # ── P7 SKILL.md 脚本引用与实际脚本一致性（v2 新增：流程接入校验） ─────
    try:
        with open(skill_path, encoding="utf-8") as f:
            skill_text = f.read()
        script_names = ["preflight_check.py", "extract_clauses.py", "validate_output.py", "step_gate.py", "release_check.py"]
        ref_missing = [s for s in script_names if s not in skill_text]
        scripts_dir = os.path.join(BASE, "scripts")
        file_missing = [s for s in script_names if not os.path.exists(os.path.join(scripts_dir, s))]
        p7_ok = (not ref_missing) and (not file_missing)
        detail_parts = []
        if ref_missing:
            detail_parts.append(f"SKILL.md 未引用: {ref_missing}")
        if file_missing:
            detail_parts.append(f"目录缺失: {file_missing}")
        check("P7 SKILL.md 脚本引用与实际脚本一致（流程接入）",
              p7_ok, "OK" if p7_ok else "；".join(detail_parts))
    except Exception as e:  # noqa: BLE001
        check("P7 SKILL.md 脚本引用与实际脚本一致（流程接入）", False, str(e))

    # ── 汇总输出 ────────────────────────────────────────────────────────
    fails = [c for c in CHECKS if not c["ok"]]
    print("=" * 58)
    print("律审·合同审查1.0 运行守护前置校验（Runtime Guard Preflight）")
    print("=" * 58)
    for c in CHECKS:
        mark = "PASS" if c["ok"] else "FAIL"
        print(f"[{mark}] {c['name']}")
        if c["detail"] and c["detail"] != "OK":
            print(f"      └─ {c['detail']}")
    print("-" * 58)
    if fails:
        print(f"总体状态: FAIL（{len(fails)} 项未通过）→ 禁止进入审查流程")
        print("处理：修复对应项后重新运行本脚本，直至 PASS")
        sys.exit(1)
    print("总体状态: PASS → 可进入审查流程")
    print("强制声明：审查输出首行须标注「✅ preflight PASS（校验时间见上）」")
    sys.exit(0)


if __name__ == "__main__":
    main()
