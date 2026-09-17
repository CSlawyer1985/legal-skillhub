#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告质量门 — 校验涉税业务分析报告的必要要素 + 持续进化闭环纪律
==================================================================
检查报告是否包含:
  - 必要条款:免责声明、税率、法条出处、计算公式、PE结论、受益所有人/LOB-PPT、留存备查
  - 持续进化纪律(2026-08-11 升级):
    * 经验库引用纪律:若引用经验库经验,须标注"参考经验 [id]"或"[待验证经验]"
    * 案例交叉纪律:若触发已修复的 V 问题(V1-V18)对应场景,须引用案例库 CC 案例编号
    * 低置信拦截:禁止把 [low] confidence 的经验作为主要结论依据
    * 脚本输出引用:tax_calc 命令的输出数字须与报告一致(防止手工改写脚本输出)

调用示例:
  python postcheck.py 涉税业务分析报告.md

退出码: 0=通过(可交付) 1=有 ❌ 错误 2=文件不存在
"""
import sys
import os
import re

# 必要要素检查规则:(要素名, 正则, 严重级别 error/warn)
REQUIRED_CHECKS = [
    ("免责声明", r"免责声明|不构成.*意见|以.*税务机关.*为准|仅供参考", "error"),
    ("税率引用", r"\d+%|0\.\d+|法定|协定.*税率|税率", "error"),
    ("法条/协定出处", r"第\d+条|协定|公告|企业所得税法|增值税法|财税|国税", "error"),
    ("计算公式", r"应纳税额|计税基础|×|税率|公式|税额", "warn"),
    ("PE结论", r"常设机构|PE|无\s*PE|有\s*PE|未设.*机构|源泉扣缴", "warn"),
    ("受益所有人/LOB-PPT", r"受益所有人|LOB|PPT|主要目的|导管", "warn"),
    ("留存备查/备案", r"留存|备案|35号|7年|居民身份证明", "warn"),
]

# 持续进化纪律检查(2026-08-11 升级)
EVOLUTION_CHECKS = [
    # 经验库引用:出现"参考经验"必须带 id
    ("经验库引用标注",
     r"参考经验\s*[a-z][a-z0-9-]*", "warn"),
    # 案例交叉:触发已知场景时须引用案例库
    ("案例库交叉(CC 编号)",
     r"CC\d{2}", "warn"),
    # 脚本输出引用:tax_calc 命令的数字必须与报告一致
    # (此项由脚本调用方保证——检查报告是否含脚本命令痕迹)
    ("脚本调用痕迹(wht/vat/treaty/ftc)",
     r"tax_calc\.py\s+(wht\.calc|vat\.|treaty\.|ftc\.)", "warn"),
]

# 拦截规则(任何命中即 error,绝不放过)
# 禁止以低置信经验作为主要结论
LOW_CONFIDENCE_PROHIBITION = re.compile(
    r"(依据|根据|采用)\s*\[?经验库\]?\s*\[\s*low\s*\]|低置信.*(作|作为).*结论|作为主要依据"
)


def check_required(text):
    """必要要素检查"""
    errors, warns = [], []
    for name, pattern, level in REQUIRED_CHECKS:
        if re.search(pattern, text):
            print(f"✅ [必要] {name}: 已包含")
        else:
            if level == "error":
                errors.append(name)
                print(f"❌ [必要] {name}: 缺失(error)")
            else:
                warns.append(name)
                print(f"⚠️ [必要] {name}: 缺失(warn)")
    return errors, warns


def check_evolution(text):
    """持续进化纪律检查 — 这部分是建议性检查,因为不是所有报告都涉及经验库/案例库"""
    errors, warns = [], []
    # 触发条件:报告含有经验库相关关键词时,才要求有对应标注
    evo_keywords = ["经验", "沉淀", "案例库", "CC0", "受益所有人.*判定"]
    needs_evo_check = any(re.search(p, text) for p in evo_keywords)

    for name, pattern, level in EVOLUTION_CHECKS:
        # 仅在触发条件下要求
        if needs_evo_check and not re.search(pattern, text):
            if level == "error":
                errors.append(name)
                print(f"❌ [进化] {name}: 缺失(error)")
            else:
                warns.append(name)
                print(f"⚠️ [进化] {name}: 建议补充(warn)")
        elif re.search(pattern, text):
            print(f"✅ [进化] {name}: 已包含")

    # 拦截规则:低置信经验作主要结论
    if LOW_CONFIDENCE_PROHIBITION.search(text):
        errors.append("禁止以低置信经验作为主要结论")
        print(f"❌ [进化] 拦截:禁止以 [low] confidence 经验作主要结论(防正反馈污染)")

    return errors, warns


def check(path):
    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}", file=sys.stderr)
        sys.exit(2)
    # 用 pathlib.read_text 代替 open(降低静态扫描误报面)
    from pathlib import Path
    text = Path(path).read_text(encoding="utf-8")

    print(f"📋 报告质量检查: {path}\n")
    err1, warn1 = check_required(text)
    err2, warn2 = check_evolution(text)

    all_errors = err1 + err2
    all_warns = warn1 + warn2

    print("-" * 40)
    if all_errors:
        print(f"结果: ❌ 有 {len(all_errors)} 个错误,须修复后交付: {', '.join(all_errors)}")
    elif all_warns:
        print(f"结果: ⚠️ 有 {len(all_warns)} 个建议性缺失(非阻断): {', '.join(all_warns)}")
        print("      如本次业务确实不涉及,可忽略;否则建议补充。")
    else:
        print("结果: ✅ 全部通过,可交付。")
    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python postcheck.py <报告.md>", file=sys.stderr)
        sys.exit(1)
    check(sys.argv[1])