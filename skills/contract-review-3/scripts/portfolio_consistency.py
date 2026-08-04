#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同智囊 · 组合（主合同+补充协议+附件）一致性校验

输入 manifest JSON（由 Agent 从各文件提取关键字段后填写）：
{
  "main":         {"parties":["甲方","乙方"], "amount":"100万", "penalty":"...", "jurisdiction":"大连", "term":"1年"},
  "supplementary":{"parties":["甲方","乙方"], "amount":"120万", "penalty":"...", "jurisdiction":"北京", "term":"1年"},
  "appendix":     {...}
}
输出：矛盾清单（主体不一致 / 金额不一致 / 管辖冲突 / 期限冲突 等）
"""
import argparse
import json
import sys
from pathlib import Path

FIELDS = ["parties", "amount", "penalty", "jurisdiction", "term"]
LABELS = {
    "parties": "签约主体",
    "amount": "合同金额",
    "penalty": "违约责任",
    "jurisdiction": "争议管辖",
    "term": "合同期限",
}


def check(manifest):
    findings = []
    for field in FIELDS:
        values = {}
        for role, data in manifest.items():
            if not isinstance(data, dict):
                print(f"[warn] 跳过 {role}：字段值非对象，已忽略", file=sys.stderr)
                continue
            v = data.get(field)
            if v:
                values[role] = str(v).strip()
        if len(values) >= 2:
            uniq = set(values.values())
            if len(uniq) > 1:
                detail = "；".join(f"{r}: {v}" for r, v in values.items())
                severity = "🔴" if field in ("parties", "jurisdiction") else "🟡"
                findings.append((severity, LABELS[field], detail))
    if not findings:
        findings.append(("🟢", "一致性", "各文件关键字段未发现矛盾"))
    return findings


def main():
    ap = argparse.ArgumentParser(description="组合一致性校验")
    ap.add_argument("--manifest", required=True, help="JSON 文件路径")
    ap.add_argument("--out", help="输出 md 路径")
    args = ap.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    findings = check(manifest)
    L = ["# 组合一致性校验报告\n",
         "> 校验维度：签约主体 / 合同金额 / 违约责任 / 争议管辖 / 合同期限\n"]
    L.append("| 严重度 | 字段 | 各文件取值 |")
    L.append("|--------|------|-----------|")
    for sev, field, detail in findings:
        L.append(f"| {sev} | {field} | {detail} |")
    L.append("\n---\n*本报告由 `scripts/portfolio_consistency.py` 生成。"
             "主体与管辖冲突为高风险，金额/期限/违约差异需结合交易结构判断。*")
    md = "\n".join(L)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"[portfolio] 已输出 {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
