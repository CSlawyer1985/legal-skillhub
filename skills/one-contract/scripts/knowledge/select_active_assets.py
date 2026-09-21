#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional
import argparse
import json


SKILL_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = SKILL_ROOT / "assets/knowledge_v2"
GLOBAL_RULES = [
    "references/review-doctrine.md",
    "references/redline-comment-policy.md",
    "references/common-clause-doctrine.md",
]


def load(name: str) -> dict[str, Any]:
    return json.loads((ASSET_ROOT / name).read_text(encoding="utf-8"))


def applicable(asset: Mapping[str, Any], type_ids: set[str], our_role: str, scene_tags: set[str]) -> bool:
    # active 判定必须同时检查审批轴与执行轴：审批通过但尚未激活的资产
    # 不属于运行时集合。字段缺失一律 fail closed（DRIFT-11）。
    if asset.get("approval_status") != "active" or asset.get("activation_status") != "active":
        return False
    asset_types = set(asset.get("type_ids", [asset.get("type_id")])) - {None}
    if not asset_types.intersection(type_ids):
        return False
    roles = set(asset.get("roles", []))
    if roles and our_role not in roles and "any" not in roles:
        return False
    required_scenes = set(asset.get("scene_tags", []))
    return not required_scenes or bool(required_scenes.intersection(scene_tags))


def type_domain_map(taxonomy: Mapping[str, Any]) -> dict[str, str]:
    mapping = {
        item["type_id"]: item["domain_code"]
        for item in taxonomy.get("catalog_types", [])
        if item.get("type_id") and item.get("domain_code")
    }
    mapping.update(
        {
            item["type_id"]: item["domain_code"]
            for item in taxonomy.get("domain_fallbacks", [])
            if item.get("type_id") and item.get("domain_code")
        }
    )
    return mapping


def shadow_metadata(card: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """Expose routing facts without returning any candidate doctrine text."""
    if card is None:
        return None
    coverage = card.get("coverage", {})
    return {
        "domain_doctrine_id": card.get("domain_doctrine_id"),
        "domain_code": card.get("domain_code"),
        "coverage_status": coverage.get("coverage_status"),
        "supported_type_count": coverage.get("supported_type_count", 0),
        "total_type_count": coverage.get("total_type_count", 0),
        "source_count": len(card.get("source_ids", [])),
        "approval_status": card.get("approval_status"),
        "activation_status": card.get("activation_status"),
        "body_included": False,
    }


def select_assets(
    *,
    primary_type_id: str,
    secondary_type_ids: list[str],
    our_role: str,
    scene_tags: list[str],
    classification_status: str,
    confirmed_domain_code: str,
) -> dict[str, Any]:
    manifest = load("asset_manifest.json")
    domains = type_domain_map(load("taxonomy_v2.json"))
    type_ids = {primary_type_id, *secondary_type_ids}
    scenes = set(scene_tags)
    principles = [
        asset for asset in load("principle_catalog.json")["assets"]
        if applicable(asset, type_ids, our_role, scenes)
    ]
    modules = [
        asset for asset in load("module_catalog.json")["assets"]
        if applicable(asset, type_ids, our_role, scenes)
    ]
    primary_domain_code = domains.get(primary_type_id)
    secondary_domain_codes = sorted(
        {
            domains[type_id]
            for type_id in secondary_type_ids
            if domains.get(type_id) and domains[type_id] != primary_domain_code
        }
    )
    domain_cards = {
        item["domain_code"]: item
        for item in load("domain_principle_catalog.json").get("assets", [])
    }
    domain_card = domain_cards.get(primary_domain_code)
    explicitly_confirmed = bool(
        confirmed_domain_code and confirmed_domain_code == primary_domain_code
    )
    automatically_confirmed = (
        classification_status == "high"
        and our_role not in {"", "unknown", "mixed"}
        and not secondary_domain_codes
    )
    domain_execution_allowed = explicitly_confirmed or automatically_confirmed
    active_domain_principle = None
    if (
        domain_execution_allowed
        and domain_card
        and domain_card.get("approval_status") == "active"
        and domain_card.get("activation_status") == "active"
        and domain_card.get("coverage", {}).get("coverage_status") != "gap"
    ):
        active_domain_principle = domain_card

    if active_domain_principle and (principles or modules):
        coverage_level = "domain_and_type"
        coverage_notice = "已同时加载active大类原则卡和active具体类型资产。"
    elif active_domain_principle:
        coverage_level = "domain_only"
        coverage_notice = "尚未命中成熟具体类型资产；当前仅使用active大类原则卡，不提供未批准的类型条款正文。"
    elif principles or modules:
        coverage_level = "global_only"
        coverage_notice = "已命中active具体类型资产；第二层大类卡尚未激活，正式运行保持既有专项路径。"
    elif domain_card:
        coverage_level = "global_only"
        coverage_notice = "第二层大类卡仅提供影子元数据，candidate正文未读取；暂无成熟专项资产。"
    else:
        coverage_level = "global_only"
        coverage_notice = "暂无大类或具体类型active资产，继续使用全局规则。"

    status = "ok" if principles or modules or active_domain_principle else "blocked_need_approval"
    return {
        "status": status,
        "primary_type_id": primary_type_id,
        "primary_domain_code": primary_domain_code,
        "secondary_domain_codes": secondary_domain_codes,
        "global_rules_applied": GLOBAL_RULES,
        "domain_principle": active_domain_principle,
        "type_principles": principles,
        "principles": principles,
        "modules": modules,
        "coverage_level": coverage_level,
        "coverage_notice": coverage_notice,
        "shadow_domain_metadata": shadow_metadata(domain_card),
        "rule_precedence": {
            "global_hard_boundaries": "non_overridable",
            "type_specific_defaults": "override_domain_defaults_within_explicit_scope",
            "hard_boundary_conflict": "rule_conflict_human_review",
            "p0_policy": "directed_block_only",
            "secondary_domain_policy": "metadata_only",
        },
        "runtime_eligible_status": manifest["runtime_eligible_status"],
        "message": "只返回active资产；空结果时继续原则型审查，不得读取候选正文。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select active assets in global/domain/type layers.")
    parser.add_argument("--primary-type-id", required=True)
    parser.add_argument("--secondary-type-id", action="append", default=[])
    parser.add_argument("--our-role", default="unknown")
    parser.add_argument("--scene-tag", action="append", default=[])
    parser.add_argument(
        "--classification-status",
        choices=("high", "medium", "low"),
        default="high",
        help="Medium/low classification never auto-loads a domain card.",
    )
    parser.add_argument(
        "--confirmed-domain-code",
        default="",
        help="Explicitly confirmed EC-01..EC-10 domain; must match the primary type.",
    )
    args = parser.parse_args()
    payload = select_assets(
        primary_type_id=args.primary_type_id,
        secondary_type_ids=args.secondary_type_id,
        our_role=args.our_role,
        scene_tags=args.scene_tag,
        classification_status=args.classification_status,
        confirmed_domain_code=args.confirmed_domain_code,
    )
    if args.confirmed_domain_code and args.confirmed_domain_code != payload["primary_domain_code"]:
        parser.error(
            "confirmed domain does not match the canonical domain of primary type: "
            f"{args.confirmed_domain_code} != {payload['primary_domain_code']}"
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
