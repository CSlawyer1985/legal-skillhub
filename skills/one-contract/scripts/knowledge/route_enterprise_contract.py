#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import argparse
import json
import re


SKILL_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = SKILL_ROOT / "assets/knowledge_v2"


def load_taxonomy() -> dict[str, Any]:
    return json.loads((ASSET_ROOT / "taxonomy_v2.json").read_text(encoding="utf-8"))


def type_domain_map(taxonomy: Mapping[str, Any]) -> dict[str, str]:
    """Return the canonical type-to-domain mapping from the full taxonomy."""
    return {
        item["type_id"]: item["domain_code"]
        for item in taxonomy.get("catalog_types", [])
        if item.get("type_id") and item.get("domain_code")
    }


def infer_document_kind(title: str) -> str:
    for kind, pattern in (
        ("resolution", r"决议|议事规则|章程"),
        ("notice_or_letter", r"函|通知|声明|确认书"),
        ("form_or_attachment", r"清单|验收单|申请表|交接单|模板"),
        ("agreement_or_contract", r"合同|协议|契约|合约"),
    ):
        if re.search(pattern, title):
            return kind
    return "unknown"


def route(
    *,
    title: str,
    legacy_type: str,
    our_role: str,
    transaction_structure: str,
    scene_tags: list[str],
    taxonomy: Mapping[str, Any],
) -> dict[str, Any]:
    scored: list[tuple[int, Mapping[str, Any], list[str], bool]] = []
    route_catalog = taxonomy.get("routable_types") or taxonomy.get("pilot_types") or []
    for contract_type in route_catalog:
        score = 0
        evidence: list[str] = []
        title_hit = False
        structure_aligned = False
        for pattern in contract_type.get("title_patterns", []):
            if re.search(pattern, title, re.IGNORECASE):
                title_hit = True
                score = max(score, 5)
                evidence.append(f"title_pattern:{pattern}")
                break
        for pattern in contract_type.get("negative_patterns", []):
            if re.search(pattern, title, re.IGNORECASE):
                score -= 6
                evidence.append(f"negative_pattern:{pattern}")
        if legacy_type and legacy_type in contract_type.get("broad_types", []):
            score += 2
            evidence.append(f"broad_type_alignment:{legacy_type}")
        if transaction_structure:
            structure_aligned = contract_type["name"] in transaction_structure or any(
                re.search(pattern, transaction_structure, re.IGNORECASE)
                for pattern in contract_type.get("title_patterns", [])
            )
            if structure_aligned:
                score += 1
                evidence.append("transaction_structure_alignment")
        if title_hit and score >= 5:
            scored.append((score, contract_type, evidence, structure_aligned))
    scored.sort(key=lambda item: (-item[0], item[1]["code"]))

    if not scored:
        domain_code = taxonomy["legacy_broad_type_domains"].get(legacy_type, "EC-10")
        fallback = next(item for item in taxonomy["domain_fallbacks"] if item["domain_code"] == domain_code)
        return {
            "primary_type_id": fallback["type_id"],
            "secondary_type_ids": [],
            "primary_domain_code": domain_code,
            "secondary_domain_codes": [],
            "document_kind": infer_document_kind(title),
            "our_role": our_role,
            "scene_tags": sorted(set([domain_code, *scene_tags])),
            "classification_status": "low",
            "evidence": [f"legacy_broad_type:{legacy_type or 'unknown'}", "no_routable_title_match"],
            "required_doctrines": [],
            "required_modules": [],
            "human_confirmation_required": True,
        }

    top_score, top, evidence, structure_aligned = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else -999
    secondary = [item[1]["type_id"] for item in scored[1:4] if item[0] >= top_score - 1]
    domain_by_type = type_domain_map(taxonomy)
    primary_domain_code = top["domain_code"]
    secondary_domain_codes = sorted(
        {
            domain_by_type.get(type_id)
            for type_id in secondary
            if domain_by_type.get(type_id)
            and domain_by_type.get(type_id) != primary_domain_code
        }
    )
    broad_aligned = legacy_type in top.get("broad_types", [])
    if top_score >= 8 and broad_aligned and top_score - second_score >= 2:
        confidence = "high"
    elif top_score >= 5 and top_score > second_score:
        confidence = "medium"
    else:
        confidence = "low"
    role_confirmed = our_role not in {"", "unknown", "mixed"}
    human_required = not (
        confidence == "high"
        and role_confirmed
        and structure_aligned
        and not secondary
    )
    return {
        "primary_type_id": top["type_id"],
        "secondary_type_ids": secondary,
        "primary_domain_code": primary_domain_code,
        "secondary_domain_codes": secondary_domain_codes,
        "document_kind": infer_document_kind(title),
        "our_role": our_role or "unknown",
        "scene_tags": sorted(set([top["domain_code"], top["name"], *scene_tags])),
        "classification_status": confidence,
        "evidence": evidence + [f"candidate_score:{top_score}"],
        "required_doctrines": top.get("required_doctrines", []),
        "required_modules": top.get("required_modules", []),
        "human_confirmation_required": human_required,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Route an enterprise contract to the v2 taxonomy.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--legacy-type", default="")
    parser.add_argument("--our-role", default="unknown")
    parser.add_argument("--transaction-structure", default="")
    parser.add_argument("--scene-tag", action="append", default=[])
    args = parser.parse_args()
    result = route(
        title=args.title,
        legacy_type=args.legacy_type,
        our_role=args.our_role,
        transaction_structure=args.transaction_structure,
        scene_tags=args.scene_tag,
        taxonomy=load_taxonomy(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
