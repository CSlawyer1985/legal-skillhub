#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同智囊 · 批量审查汇总

读取一个目录下多份 review-issues-*.json 台账，产出 batch_report.md：
  · 总览（合同数 / 问题数 / 风险分布）
  · 每合同风险画像
  · 跨合同共性高风险章节
  · 跨合同条款一致性提示（同章节不同风险等级）
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_ledgers(d):
    ledgers = []
    for f in sorted(Path(d).glob("review-issues-*.json")):
        try:
            ledgers.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"[warn] 跳过 {f.name}: {e}", file=sys.stderr)
    return ledgers


def _risk_key(rl):
    rl = str(rl)
    if "高" in rl:
        return "高"
    if "中" in rl:
        return "中"
    return "低"


def build(ledgers):
    total_issues = 0
    risk_total = {"高": 0, "中": 0, "低": 0}
    per_contract = []
    section_map = defaultdict(list)
    for lg in ledgers:
        name = lg.get("document", "?")
        ctype = lg.get("contract_type", "?")
        dist = {"高": 0, "中": 0, "低": 0}
        for it in lg.get("issues", []):
            key = _risk_key(it.get("risk_level", "低"))
            dist[key] += 1
            risk_total[key] += 1
            total_issues += 1
            section_map[it.get("section", "未命名章节")].append((name, key))
        per_contract.append((name, ctype, len(lg.get("issues", [])), dist))

    common = []
    common_secs = set()
    for sec, items in section_map.items():
        highs = [c for c, k in items if k == "高"]
        mids = [c for c, k in items if k == "中"]
        if len(highs) >= 2:
            common.append((sec, "高", highs))
            common_secs.add(sec)
        elif len(items) >= 2 and (highs or len(mids) >= 2):
            common.append((sec, "中", highs + mids))
            common_secs.add(sec)

    divergent = []
    for sec, items in section_map.items():
        if sec in common_secs:
            continue  # 已在「共性高风险」列出，避免重复
        levels = {k for _, k in items}
        if len(items) >= 2 and len(levels) >= 2:
            divergent.append((sec, items))

    return total_issues, risk_total, per_contract, common, divergent


def render(ledgers, total_issues, risk_total, per_contract, common, divergent):
    L = []
    L.append("# 批量审查汇总报告\n")
    L.append(f"> 覆盖合同数：**{len(ledgers)}** ｜ 发现问题总数：**{total_issues}**"
             f"｜ 风险分布：🔴 高 {risk_total['高']} ｜ 🟡 中 {risk_total['中']} ｜ 🟢 低 {risk_total['低']}\n")
    L.append("## 一、各合同风险画像\n")
    L.append("| 合同 | 类型 | 问题数 | 高 | 中 | 低 |")
    L.append("|------|------|--------|----|----|----|")
    for name, ctype, cnt, dist in per_contract:
        L.append(f"| {name} | {ctype} | {cnt} | {dist['高']} | {dist['中']} | {dist['低']} |")
    L.append("\n## 二、跨合同共性高风险章节\n")
    if common:
        L.append("| 章节 | 风险等级 | 命中合同 |")
        L.append("|------|---------|---------|")
        for sec, lvl, contracts in common:
            L.append(f"| {sec} | {lvl} | {', '.join(contracts)} |")
    else:
        L.append("（未检测到跨合同共性高风险章节）")
    L.append("\n## 三、跨合同条款一致性提示\n")
    if divergent:
        L.append("> 以下章节在不同合同中风险定级不一致，建议复核审查标准是否统一：\n")
        for sec, items in divergent:
            detail = "；".join(f"{c}:{k}" for c, k in items)
            L.append(f"- **{sec}**：{detail}")
    else:
        L.append("（各合同同章节风险定级一致）")
    L.append("\n---\n*本报告由 `scripts/batch_review.py` 自动聚合多份审核台账生成。*")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="合同智囊批量审查汇总")
    ap.add_argument("--ledger-dir", required=True)
    ap.add_argument("--out", help="输出 md 路径，默认打印到 stdout")
    args = ap.parse_args()
    ledgers = load_ledgers(args.ledger_dir)
    if not ledgers:
        print("未找到 review-issues-*.json 台账。", file=sys.stderr)
        sys.exit(1)
    total_issues, risk_total, per_contract, common, divergent = build(ledgers)
    md = render(ledgers, total_issues, risk_total, per_contract, common, divergent)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"[batch_review] 已输出 {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
