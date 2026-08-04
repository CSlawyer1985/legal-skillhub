#!/usr/bin/env python3
"""Choose the next novelty-search action from observed result quality.

The policy is deliberately deterministic: it prevents an agent from declaring
success merely because a query became smaller, or from repeatedly appending
unverified words to the same Bool expression.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


VALID_LABELS = {"H", "M", "N", "D"}


def _metrics(labels: list[str]) -> dict:
    normalized = [str(label).upper() for label in labels]
    invalid = sorted(set(normalized) - VALID_LABELS)
    if invalid:
        raise ValueError(f"invalid sample labels: {', '.join(invalid)}")
    denominator = max(1, len(normalized))
    return {
        "sample_size": len(normalized),
        "h_rate": round(normalized.count("H") / denominator, 4),
        "hm_rate": round(
            (normalized.count("H") + normalized.count("M")) / denominator, 4
        ),
    }


def _next_feature(observation: dict) -> dict | None:
    used = {str(item) for item in observation.get("used_feature_ids") or []}
    candidates = []
    for feature in observation.get("available_features") or []:
        feature_id = str(feature.get("id") or "").strip()
        if not feature_id or feature_id in used:
            continue
        # A term may enter the core Bool only if its source is confirmed under
        # the admission rule in adaptive_xy_search.md.
        if not feature.get("confirmed", False):
            continue
        score = (
            float(feature.get("legal_necessity", 0))
            + float(feature.get("discriminativeness", 0))
            + float(feature.get("expressibility", 0))
        )
        candidates.append((score, feature_id, feature))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2]


def plan_next_step(observation: dict) -> dict:
    """Return one auditable next action for a search iteration."""
    role = str(observation.get("role") or "QX")
    if role not in {"QX", "QY-Base", "QY-Comp"}:
        raise ValueError("role must be QX, QY-Base, or QY-Comp")
    total = int(observation.get("total", 0))
    metrics = _metrics(observation.get("sample_labels") or [])
    base = {"role": role, "total": total, **metrics}

    joint_clause_rate = observation.get("joint_clause_rate")
    if joint_clause_rate is not None and float(joint_clause_rate) < 0.50:
        return {
            **base,
            "action": "replace_ineffective_clause_combination",
            "next_role": role,
            "reason": "目标特征与功能/关系在同一篇文献中的联合可观察率低于50%；边际命中不能证明组合有效",
        }

    clause_rates = {
        str(key): float(value)
        for key, value in (observation.get("required_clause_rates") or {}).items()
    }
    ineffective_clauses = sorted(key for key, value in clause_rates.items() if value < 0.50)
    if ineffective_clauses:
        return {
            **base,
            "action": "replace_ineffective_clause",
            "next_role": role,
            "ineffective_clause_ids": ineffective_clauses,
            "reason": "必需条件在前10中的可观察率低于50%；总量变化不能证明该AND块生效，切换IPC、字段、语言或特征组合",
        }

    field_filter_rate = observation.get("field_filter_match_rate")
    if field_filter_rate is not None and float(field_filter_rate) < 0.90:
        return {
            **base,
            "action": "repair_field_filter",
            "next_role": role,
            "reason": "申请人/国家/日期/IPC字段反查通过率低于90%；先修复字段值、别名或语法，不进入主体或地域统计",
        }

    if observation.get("ipc_probe_total") == 0:
        return {
            **base,
            "action": "repair_or_broaden_ipc",
            "next_role": role,
            "reason": "IPC单独预检为0；先修复分类空格/层级或改用上位组，禁止与关键词叠加后解释为未发现",
        }

    if observation.get("has_y_base") and observation.get("missing_features"):
        return {
            **base,
            "action": "start_qy_comp",
            "next_role": "QY-Comp",
            "target_features": list(observation["missing_features"]),
            "reason": "Y-Base已找到，转向其缺失区别特征",
        }
    if observation.get("found_x") and role == "QX":
        return {
            **base,
            "action": "start_qy_base",
            "next_role": "QY-Base",
            "reason": "X候选已出现，仍需独立寻找最接近现有技术",
        }
    if int(observation.get("stagnant_rounds", 0)) >= 2:
        return {
            **base,
            "action": "pivot_recall_channel",
            "next_role": role,
            "reason": "连续两轮没有新增X/Y，切换world、多语言、引证或语义召回",
        }

    too_broad = total >= 5000 or (metrics["sample_size"] and metrics["h_rate"] < 0.30)
    if too_broad:
        feature = _next_feature(observation)
        if feature:
            return {
                **base,
                "action": "narrow_with_feature",
                "next_role": role,
                "add_feature_id": str(feature["id"]),
                "add_query": feature.get("query"),
                "reason": "结果过宽或前排噪声高，加入已确认的高区分关键特征",
            }
        return {
            **base,
            "action": "harvest_terms_or_ipc",
            "next_role": role,
            "reason": "结果过宽但没有合格的新关键词；先从H/M文献、分类定义或标准取词",
        }

    if total <= 5 and not observation.get("found_x"):
        return {
            **base,
            "action": "relax_low_confidence_block",
            "next_role": role,
            "reason": "结果过窄且没有X；放宽最低置信限定，同时保留关键关系",
        }
    if not observation.get("found_x") and metrics["hm_rate"] >= 0.50:
        return {
            **base,
            "action": "rotate_feature_combination",
            "next_role": role,
            "reason": "相关结果较多但没有X；提取真实术语并更换特征组合，而非继续叠加",
        }
    return {
        **base,
        "action": "inspect_and_follow_leads",
        "next_role": role,
        "reason": "核对前排详情，并沿申请人、分类、引证和同族线索扩展",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="根据检索结果质量选择下一步策略")
    parser.add_argument("input", nargs="?", help="输入JSON文件；省略时从stdin读取")
    args = parser.parse_args()
    if args.input:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)
    json.dump(plan_next_step(payload), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
