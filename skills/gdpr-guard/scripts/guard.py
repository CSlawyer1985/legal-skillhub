#!/usr/bin/env python3
"""GDPR 护栏检测内核 (pipl-guard)。

运行时护栏：在 AI 应用的输入/输出链路中实时检测个人信息，
按风险分级执行脱敏或阻断，供 Agent 主动调用。

设计原则：
  - 纯本地运行，零网络请求，零动态执行（无 eval/exec/动态 import）。
  - 敏感数据不出机器，检测在本地完成。
  - 规则与内核分离：内核不变，换规则包即得行业版。

用法：
    # 检测一段文本
    python3 scripts/guard.py --text "我的身份证是110101199003074477"
    # 从标准输入读取（适合管道 / Agent 调用）
    echo "手机号13800138000" | python3 scripts/guard.py --stdin
    # 指定动作与规则包
    python3 scripts/guard.py --text "..." --action mask --profile common
    python3 scripts/guard.py --text "..." --action block --format json
    # 列出可用规则包
    python3 scripts/guard.py --list-profiles
"""

import argparse
import json
import re
import sys

from rules import gdpr as _gdpr

# 显式规则映射：不使用动态 import，便于安全审计。
# 行业版（如 finance）在此登记后即可通过 --profile 选用。
PROFILES = {
    "gdpr": _gdpr,
}

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}


# ============ 额外校验器 ============
def _luhn_ok(number: str) -> bool:
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 12:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _china_id_ok(number: str) -> bool:
    if len(number) != 18:
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    codes = "10X98765432"
    try:
        s = sum(int(number[i]) * weights[i] for i in range(17))
    except ValueError:
        return False
    return codes[s % 11].upper() == number[17].upper()


def _ipv4_ok(number: str) -> bool:
    parts = number.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


VALIDATORS = {
    "luhn": _luhn_ok,
    "china_id": _china_id_ok,
    "ipv4": _ipv4_ok,
}


# ============ 脱敏策略 ============
def _mask_value(value: str, strategy: str) -> str:
    if strategy == "full":
        return "*" * len(value)
    if strategy == "hash":
        # 非加密用途，仅做稳定占位，避免引入依赖
        return "<HASH:%08x>" % (hash(value) & 0xFFFFFFFF)
    # partial：保留首尾，中间打码
    if len(value) <= 2:
        return "*" * len(value)
    if len(value) <= 6:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    return value[:3] + "*" * (len(value) - 5) + value[-2:]


# ============ 检测核心 ============
def detect(text, profile_name="gdpr"):
    """返回 (findings, compiled_by_span)。findings 为命中列表。"""
    profile = PROFILES.get(profile_name)
    if profile is None:
        raise ValueError("未知规则包: %s" % profile_name)

    findings = []
    for pid, regex, label, category, severity, validate, mask in profile.PATTERNS:
        for m in re.finditer(regex, text):
            value = m.group(0)
            if validate:
                v = VALIDATORS.get(validate)
                if v and not v(value):
                    continue
            findings.append({
                "id": pid, "label": label, "category": category,
                "severity": severity, "value": value,
                "start": m.start(), "end": m.end(), "mask": mask,
                "kind": "pattern",
            })

    for kw, label, category, severity in profile.KEYWORDS:
        idx = text.find(kw)
        while idx != -1:
            findings.append({
                "id": "kw_" + kw, "label": label, "category": category,
                "severity": severity, "value": kw,
                "start": idx, "end": idx + len(kw), "mask": "none",
                "kind": "keyword",
            })
            idx = text.find(kw, idx + len(kw))

    findings.sort(key=lambda f: (f["start"], -SEVERITY_ORDER.get(f["severity"], 0)))
    return findings


def _dedup_spans(findings):
    """去除重叠命中，保留风险更高者；同级取更长的匹配。

    关键词（上下文线索）不参与区间竞争，始终保留。
    这样可避免同一身份证号被同时报成多种 PII 的误报，
    保证报告与脱敏结果一致、可信。
    """
    keywords = [f for f in findings if f["kind"] == "keyword"]
    patterns = [f for f in findings if f["kind"] != "keyword"]
    chosen = []
    for f in sorted(patterns, key=lambda x: (-SEVERITY_ORDER.get(x["severity"], 0),
                                             -(x["end"] - x["start"]), x["start"])):
        if any(not (f["end"] <= c["start"] or f["start"] >= c["end"]) for c in chosen):
            continue
        chosen.append(f)
    return sorted(chosen + keywords, key=lambda x: x["start"])


def apply_mask(text, findings):
    spans = [f for f in findings if f["mask"] not in ("none", None)]
    out, cursor = [], 0
    for f in spans:
        out.append(text[cursor:f["start"]])
        out.append(_mask_value(f["value"], f["mask"]))
        cursor = f["end"]
    out.append(text[cursor:])
    return "".join(out)


def highest_severity(findings):
    if not findings:
        return None
    return max(findings, key=lambda f: SEVERITY_ORDER.get(f["severity"], 0))["severity"]


def evaluate(text, profile_name="gdpr", action="mask", block_on="high"):
    """护栏主入口。返回结构化裁决结果。

    action: detect（仅检测） / mask（脱敏放行） / block（高危阻断，否则脱敏）
    block_on: 触发阻断的最低风险等级
    """
    findings = _dedup_spans(detect(text, profile_name))
    top = highest_severity(findings)
    threshold = SEVERITY_ORDER.get(block_on, 3)
    hit_block = top is not None and SEVERITY_ORDER.get(top, 0) >= threshold

    result = {
        "profile": profile_name,
        "action": action,
        "risk_level": top or "none",
        "finding_count": len(findings),
        "findings": [
            {k: v for k, v in f.items() if k != "value"} | {
                "preview": _mask_value(f["value"], "partial") if f["kind"] == "pattern" else f["value"]
            }
            for f in findings
        ],
    }

    if action == "detect":
        result["decision"] = "inspect_only"
        result["output"] = text
    elif action == "block" and hit_block:
        result["decision"] = "blocked"
        result["output"] = None
        result["reason"] = "检测到 %s 级敏感个人信息，已按策略阻断" % top
    else:
        result["decision"] = "masked" if findings else "pass"
        result["output"] = apply_mask(text, findings) if findings else text
    return result


# ============ CLI ============
def _read_input(args):
    if args.text is not None:
        return args.text
    if args.stdin:
        return sys.stdin.read()
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description="GDPR 护栏检测内核")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--text", help="直接传入待检测文本")
    src.add_argument("--stdin", action="store_true", help="从标准输入读取")
    p.add_argument("--profile", default="gdpr", help="规则包（默认 common）")
    p.add_argument("--action", default="mask",
                   choices=["detect", "mask", "block"], help="护栏动作")
    p.add_argument("--block-on", default="high",
                   choices=["low", "medium", "high"], help="阻断阈值")
    p.add_argument("--format", default="text",
                   choices=["text", "json"], help="输出格式")
    p.add_argument("--list-profiles", action="store_true", help="列出可用规则包")
    args = p.parse_args(argv)

    if args.list_profiles:
        for name, mod in PROFILES.items():
            pr = mod.PROFILE
            print("%-10s %s (v%s)" % (name, pr["name"], pr["version"]))
        return 0

    text = _read_input(args)
    if text is None:
        p.error("需要 --text 或 --stdin 提供输入")

    result = evaluate(text, args.profile, args.action, args.block_on)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("规则包: %s | 动作: %s | 风险: %s | 命中: %d 处"
              % (result["profile"], result["action"],
                 result["risk_level"], result["finding_count"]))
        print("裁决: %s" % result["decision"])
        for f in result["findings"]:
            print("  [%s] %s (%s) @%d-%d → %s"
                  % (f["severity"], f["label"], f["category"],
                     f["start"], f["end"], f["preview"]))
        if result.get("reason"):
            print("原因: %s" % result["reason"])
        print("---- 输出 ----")
        print("<已阻断>" if result["output"] is None else result["output"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
