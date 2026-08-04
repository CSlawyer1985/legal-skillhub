#!/usr/bin/env python3
"""Deterministic consistency checker for PatSeek X/Y candidate evidence.

Input JSON schema is documented in references/adaptive_xy_search.md. This tool
does not make a legal conclusion; it verifies that proposed X/Y labels satisfy
the skill's minimum evidence rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _as_set(value) -> set[str]:
    return {str(item) for item in (value or [])}


def evaluate_xy(payload: dict) -> dict:
    features = payload.get("features") or []
    documents = payload.get("documents") or []
    if not features:
        raise ValueError("features must not be empty")

    weights: dict[str, float] = {}
    required: set[str] = set()
    critical: set[str] = set()
    for feature in features:
        feature_id = str(feature.get("id") or "").strip()
        if not feature_id:
            raise ValueError("each feature requires a non-empty id")
        if feature_id in weights:
            raise ValueError(f"duplicate feature id: {feature_id}")
        weights[feature_id] = float(feature.get("weight", 1.0))
        if feature.get("required", True):
            required.add(feature_id)
        if feature.get("critical", False):
            critical.add(feature_id)

    if not required:
        raise ValueError("at least one feature must be required")
    if not critical:
        critical = set(required)

    required_weight = sum(weights[item] for item in required)
    evaluations: list[dict] = []
    by_pid: dict[str, dict] = {}

    for document in documents:
        pid = str(document.get("pid") or "").strip()
        if not pid:
            raise ValueError("each document requires pid")
        if pid in by_pid:
            raise ValueError(f"duplicate document pid: {pid}")
        disclosed = _as_set(document.get("disclosed")) & set(weights)
        covered_required = disclosed & required
        coverage = sum(weights[item] for item in covered_required) / required_weight
        missing = sorted(required - disclosed)
        date_eligible = bool(document.get("date_eligible", False))
        relationships_ok = bool(document.get("relationships_ok", False))
        enabling = bool(document.get("enabling", False))
        same_field = bool(document.get("same_field", False))
        same_problem = bool(document.get("same_problem", False))
        analogous_field = bool(document.get("analogous_field", False))

        if date_eligible and not missing and relationships_ok and enabling:
            code = "X"
            reason = "单篇覆盖全部必要特征及关系，日期适格且公开可实施"
        elif (
            date_eligible
            and coverage >= 0.60
            and bool(disclosed & critical)
            and (same_field or same_problem)
        ):
            code = "Y-Base"
            reason = "同领域/问题接近并覆盖大部分必要特征"
        elif (
            date_eligible
            and bool(disclosed & critical)
            and (same_field or same_problem or analogous_field)
        ):
            code = "Y-Comp"
            reason = "公开关键区别特征，需与基础文献核对结合理由"
        else:
            code = "A"
            if not date_eligible:
                reason = "日期不适格或日期未核验"
            elif not disclosed:
                reason = "未见必要特征证据"
            else:
                reason = "证据不足以支持X/Y候选"

        item = {
            "pid": pid,
            "code": code,
            "coverage": round(coverage, 4),
            "disclosed": sorted(disclosed),
            "missing": missing,
            "reason": reason,
        }
        evaluations.append(item)
        by_pid[pid] = {**item, "raw": document}

    key_y_pairs: list[dict] = []
    rejected_links: list[dict] = []
    for link in payload.get("combination_links") or []:
        base_pid = str(link.get("base") or "")
        comp_pid = str(link.get("comp") or "")
        reason = str(link.get("reason") or "").strip()
        evidence = str(link.get("evidence") or "").strip()
        base = by_pid.get(base_pid)
        comp = by_pid.get(comp_pid)
        problems: list[str] = []
        if not base or not comp:
            problems.append("文献不存在")
        else:
            if base_pid == comp_pid:
                problems.append("Y组合必须是不同文献")
            union = _as_set(base["disclosed"]) | _as_set(comp["disclosed"])
            if base["code"] != "Y-Base":
                problems.append("base不是Y-Base候选")
            if comp["code"] not in {"Y-Base", "Y-Comp"}:
                problems.append("comp不是Y候选")
            if not required <= union:
                problems.append("组合仍未覆盖全部必要特征")
        if not reason or not evidence:
            problems.append("缺少结合理由或证据")

        record = {
            "base": base_pid,
            "comp": comp_pid,
            "reason": reason,
            "evidence": evidence,
        }
        if problems:
            rejected_links.append({**record, "problems": problems})
        else:
            key_y_pairs.append(record)

    return {
        "documents": evaluations,
        "x_candidates": [item["pid"] for item in evaluations if item["code"] == "X"],
        "y_base_candidates": [item["pid"] for item in evaluations if item["code"] == "Y-Base"],
        "y_comp_candidates": [item["pid"] for item in evaluations if item["code"] == "Y-Comp"],
        "key_y_pairs": key_y_pairs,
        "rejected_combination_links": rejected_links,
        "disclaimer": "规则一致性检查，不替代全文、日期、公开充分性和创造性法律判断",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查结构化专利证据的X/Y候选分类")
    parser.add_argument("input", nargs="?", help="输入JSON文件；省略时从stdin读取")
    args = parser.parse_args()
    if args.input:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)
    json.dump(evaluate_xy(payload), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
