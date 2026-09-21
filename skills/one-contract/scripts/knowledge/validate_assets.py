#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile
import argparse
import json
import re


ALLOWED_STATUSES = {"candidate", "lawyer_approved", "regression_passed", "active", "deprecated"}
TEXT_EXTENSIONS = {".md", ".json", ".py", ".yaml", ".yml", ".txt", ".csv"}
MODULE_REQUIRED = {
    "module_id", "version", "type_id", "clause_group", "review_objective", "failure_mode",
    "roles", "scene_tags", "requiredness", "assumptions", "placeholders", "variants",
    "dependencies", "conflicts", "source_ids", "source_family_ids", "approval_status",
    "reviewer", "reviewed_at", "legal_checked_at",
}
GROUP_REQUIRED = {
    "module_group_id", "version", "type_id", "name", "member_module_ids",
    "review_sequence", "joint_failure_modes", "consistency_checks", "approval_status",
    "activation_status",
}
TEMPLATE_REQUIRED = {
    "template_id", "version", "type_id", "type_code", "name", "relative_path",
    "document_kind", "sample_support_status", "approval_status", "activation_status",
}
SOURCE_REQUIRED = {
    "source_id", "source_kind", "title", "author", "jurisdiction",
    "published_at", "verified_at", "knowledge_tags", "used_for", "approval_status",
}
TRIGGER_REQUIRED = {
    "trigger_id", "version", "type_id", "name", "severity", "hard_signals",
    "false_positive_guards", "evidence_state", "human_confirmation_required",
    "auto_action", "required_modules", "required_outputs", "prohibited_outputs",
    "source_ids", "approval_status", "activation_status",
}
EXPERIENCE_REQUIRED = {
    "experience_id", "type_id", "title", "source_ids", "source_status",
    "observation", "review_rule", "limits", "approval_status", "activation_status",
}
DOMAIN_PRINCIPLE_REQUIRED = {
    "domain_doctrine_id", "domain_code", "domain_name", "version", "coverage",
    "review_objectives", "judgment_coordinates", "review_sequence",
    "common_failure_modes", "default_tendencies", "applicability_conditions",
    "override_factors", "hard_boundaries", "required_evidence", "module_index",
    "derived_principle_ids", "derived_module_ids", "source_ids", "knowledge_gaps",
    "approval_status", "activation_status", "reviewer", "reviewed_at",
    "legal_checked_at", "content_status",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _belongs_to_active_type(item: Mapping[str, Any], active_types: set[str]) -> bool:
    """Return True if an asset serves any activated type."""
    type_ids = item.get("type_ids")
    if isinstance(type_ids, list):
        return bool(set(type_ids) & active_types)
    return bool(item.get("type_id") in active_types)


def _validate_independent_state(
    item: Mapping[str, Any], *, label: str, errors: list[str]
) -> None:
    status = item.get("approval_status")
    activation = item.get("activation_status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"{label} has invalid approval_status: {status}")
    elif status == "active" and activation != "active":
        errors.append(f"active {label} must have activation_status=active")
    elif status != "active" and activation != "inactive":
        errors.append(f"non-active {label} must have activation_status=inactive")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate modular knowledge assets and privacy boundaries.")
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.skill_root.resolve()
    assets = root / "assets/knowledge_v2"
    errors: list[str] = []
    manifest = load(assets / "asset_manifest.json")
    if manifest.get("runtime_eligible_status") != "active":
        errors.append("runtime_eligible_status must be active")
    active_types = set(manifest.get("active_type_ids", []))
    taxonomy = load(assets / "taxonomy_v2.json")
    catalog_types = taxonomy.get("catalog_types", [])
    catalog_type_ids = {item.get("type_id") for item in catalog_types}
    active_catalog_types = {
        item.get("type_id") for item in catalog_types if item.get("approval_status") == "active"
    }
    if active_types != active_catalog_types:
        errors.append("manifest active_type_ids/catalog active types mismatch")
    routable_types = taxonomy.get("routable_types")
    if not isinstance(routable_types, list):
        errors.append("taxonomy routable_types must be present")
        routable_types = []
    routable_ids = [item.get("type_id") for item in routable_types]
    if len(routable_ids) != len(set(routable_ids)):
        errors.append("taxonomy routable type ids must be unique")
    if not set(routable_ids).issubset(catalog_type_ids):
        errors.append("taxonomy routable_types references unknown catalog type")
    if not active_types.issubset(set(routable_ids)):
        errors.append("every active type must be present in routable_types")
    modules = load(assets / "module_catalog.json").get("assets", [])
    principles = load(assets / "principle_catalog.json").get("assets", [])
    domain_principles = load(assets / "domain_principle_catalog.json").get("assets", [])
    groups = load(assets / "module_group_catalog.json").get("assets", [])
    templates = load(assets / "template_catalog.json").get("assets", [])
    sources = load(assets / "source_catalog.json").get("assets", [])
    triggers = load(assets / "trigger_catalog.json").get("assets", [])
    experiences = load(assets / "experience_catalog.json").get("assets", [])
    module_ids = {item.get("module_id") for item in modules}
    principle_ids = {item.get("doctrine_id") for item in principles}
    principle_record_keys = [
        (item.get("doctrine_id"), item.get("type_id")) for item in principles
    ]
    if len(principle_record_keys) != len(set(principle_record_keys)):
        errors.append("type principle doctrine_id/type_id pairs must be unique")
    source_ids = {item.get("source_id") for item in sources}
    if len(source_ids) != len(sources):
        errors.append("source ids must be unique")
    source_by_id = {item.get("source_id"): item for item in sources}
    taxonomy_domains = {item.get("code"): item for item in taxonomy.get("domains", [])}
    type_domain = {
        item.get("type_id"): item.get("domain_code") for item in catalog_types
    }
    domain_ids = [item.get("domain_doctrine_id") for item in domain_principles]
    domain_codes = [item.get("domain_code") for item in domain_principles]
    if len(domain_ids) != len(set(domain_ids)):
        errors.append("domain doctrine ids must be unique")
    if len(domain_codes) != len(set(domain_codes)):
        errors.append("domain doctrine codes must be unique")
    if set(domain_codes) != set(taxonomy_domains):
        errors.append("domain principle catalog must contain exactly one card per taxonomy domain")
    for card in domain_principles:
        card_id = card.get("domain_doctrine_id")
        code = card.get("domain_code")
        missing = DOMAIN_PRINCIPLE_REQUIRED - set(card)
        if missing:
            errors.append(f"domain principle {card_id} missing {sorted(missing)}")
            continue
        if card_id != f"domain-doctrine-{str(code).lower()}":
            errors.append(f"domain principle {card_id} permanent id/domain mismatch")
        _validate_independent_state(card, label=f"domain principle {card_id}", errors=errors)
        coverage = card.get("coverage", {})
        domain_type_ids = {
            type_id for type_id, domain_code in type_domain.items() if domain_code == code
        }
        supported = set(coverage.get("supported_type_ids", []))
        unsupported = set(coverage.get("unsupported_type_ids", []))
        if supported & unsupported or supported | unsupported != domain_type_ids:
            errors.append(f"domain principle {card_id} coverage does not partition taxonomy types")
        if coverage.get("total_type_count") != len(domain_type_ids):
            errors.append(f"domain principle {card_id} total_type_count mismatch")
        if coverage.get("supported_type_count") != len(supported):
            errors.append(f"domain principle {card_id} supported_type_count mismatch")
        indexed_module_ids = {
            module_id
            for group in card.get("module_index", [])
            for module_id in group.get("module_ids", [])
        }
        if indexed_module_ids != set(card.get("derived_module_ids", [])):
            errors.append(f"domain principle {card_id} module index/provenance mismatch")
        if not indexed_module_ids.issubset(module_ids):
            errors.append(f"domain principle {card_id} references unknown module")
        if not set(card.get("derived_principle_ids", [])).issubset(principle_ids):
            errors.append(f"domain principle {card_id} references unknown principle")
        if not set(card.get("source_ids", [])).issubset(source_ids):
            errors.append(f"domain principle {card_id} references unknown source")
        if any(
            source_by_id[source_id].get("approval_status") != "active"
            for source_id in card.get("source_ids", [])
            if source_id in source_by_id
        ):
            errors.append(f"domain principle {card_id} uses a non-active source")
        if coverage.get("coverage_status") == "gap":
            operative_fields = (
                "review_objectives", "judgment_coordinates", "review_sequence",
                "common_failure_modes", "default_tendencies", "applicability_conditions",
                "override_factors", "hard_boundaries", "required_evidence", "module_index",
                "derived_principle_ids", "derived_module_ids", "source_ids",
            )
            if any(card.get(field) for field in operative_fields):
                errors.append(f"gap domain principle {card_id} contains operative content")
            if card.get("approval_status") == "active":
                errors.append(f"gap domain principle {card_id} must not be active")
        elif not all(
            card.get(field)
            for field in (
                "review_objectives", "judgment_coordinates", "review_sequence",
                "common_failure_modes", "default_tendencies", "applicability_conditions",
                "override_factors", "hard_boundaries", "required_evidence",
                "module_index", "derived_principle_ids", "derived_module_ids", "source_ids",
            )
        ):
            errors.append(f"substantive domain principle {card_id} has an empty core field")
        if card.get("approval_status") == "active" and not all(
            card.get(field) for field in ("reviewer", "reviewed_at", "legal_checked_at")
        ):
            errors.append(f"active domain principle {card_id} lacks approval evidence")
    for module in modules:
        missing = MODULE_REQUIRED - set(module)
        if missing:
            errors.append(f"module {module.get('module_id')} missing {sorted(missing)}")
        if module.get("approval_status") not in ALLOWED_STATUSES:
            errors.append(f"module {module.get('module_id')} has invalid status")
        if module.get("approval_status") == "active" and module.get("activation_status") != "active":
            errors.append(f"active module {module.get('module_id')} must be active")
        if module.get("approval_status") == "active" and not all(
            module.get(key) for key in ("reviewer", "reviewed_at", "legal_checked_at")
        ):
            errors.append(f"active module {module.get('module_id')} lacks approval evidence")
        if module.get("approval_status") != "active" and module.get("activation_status") != "inactive":
            errors.append(f"non-active module {module.get('module_id')} must remain inactive")
        if module.get("approval_status") == "active" and "awaiting" in str(module.get("content_status", "")):
            errors.append(f"active module {module.get('module_id')} still claims approval is pending")
        # ── 空壳模块的标记一致性（2026-09-17 加）─────────────────────────────
        # 背景：曾有 56 个模块的每个字段都是模板套话（review_checks 只有一句
        # "应明确对象、条件、程序、期限和后果"），但状态为 active，运行时会被
        # 当作"类型级覆盖"计入，使审查报告的覆盖层级**高估深度**。
        # 处置：这类模块必须显式标记 content_status 以 `stub_` 开头（唯一真值来源，
        # 不做启发式判断），且标记与内容必须双向一致。
        _stub_marked = str(module.get("content_status", "")).startswith("stub_")
        _placeholder = "应明确对象、条件、程序、期限和后果"
        _is_placeholder_only = list(module.get("review_checks") or []) == [_placeholder]
        if _stub_marked and len(module.get("review_checks") or []) != 1:
            errors.append(
                f"module {module.get('module_id')} is marked stub but carries "
                f"{len(module.get('review_checks') or [])} review_checks — "
                "内容已填充则应移除 stub 标记"
            )
        if _is_placeholder_only and not _stub_marked:
            errors.append(
                f"module {module.get('module_id')} still carries only the placeholder "
                "review_check but is not marked as stub — "
                "请标记 content_status 以 stub_ 开头，或补入实际检查项"
            )
        if set(module.get("dependencies_by_type", {})) != set(module.get("type_ids", [])):
            errors.append(f"module {module.get('module_id')} dependency map/type_ids mismatch")
        if not set(module.get("source_ids", [])).issubset(source_ids):
            errors.append(f"module {module.get('module_id')} references unknown source")
        if module.get("content_status") == "lawyer_approved_v1_migration_20260912":
            migrated_fields = {
                "review_checks", "recommended_actions", "remediation_steps",
                "legal_basis_notes", "risk_examples",
            }
            empty = sorted(field for field in migrated_fields if not module.get(field))
            if empty:
                errors.append(
                    f"approved migrated module {module.get('module_id')} missing structured knowledge {empty}"
                )
    for principle in principles:
        if principle.get("approval_status") not in ALLOWED_STATUSES:
            errors.append(f"principle {principle.get('doctrine_id')} has invalid status")
        if principle.get("approval_status") != "active" and principle.get("activation_status") != "inactive":
            errors.append(f"non-active principle {principle.get('doctrine_id')} must remain inactive")
        if principle.get("approval_status") == "active" and principle.get("activation_status") != "active":
            errors.append(f"active principle {principle.get('doctrine_id')} must be active")
        if principle.get("approval_status") == "active" and "awaiting" in str(principle.get("content_status", "")):
            errors.append(f"active principle {principle.get('doctrine_id')} still claims approval is pending")
        if not set(principle.get("source_ids", [])).issubset(source_ids):
            errors.append(f"principle {principle.get('doctrine_id')} references unknown source")
    for group in groups:
        missing = GROUP_REQUIRED - set(group)
        if missing:
            errors.append(f"module group {group.get('module_group_id')} missing {sorted(missing)}")
        if not set(group.get("member_module_ids", [])).issubset(module_ids):
            errors.append(f"module group {group.get('module_group_id')} references unknown module")
        _validate_independent_state(
            group, label=f"module group {group.get('module_group_id')}", errors=errors
        )
        if group.get("approval_status") == "active" and not _belongs_to_active_type(group, active_types):
            errors.append(f"active module group {group.get('module_group_id')} serves no active type")
        if group.get("approval_status") == "active" and "awaiting" in str(group.get("content_status", "")):
            errors.append(f"active module group {group.get('module_group_id')} still claims approval is pending")
    for template in templates:
        missing = TEMPLATE_REQUIRED - set(template)
        if missing:
            errors.append(f"template {template.get('template_id')} missing {sorted(missing)}")
            continue
        _validate_independent_state(
            template, label=f"template {template.get('template_id')}", errors=errors
        )
        if template.get("approval_status") == "active" and not _belongs_to_active_type(template, active_types):
            errors.append(f"active template {template.get('template_id')} serves no active type")
        relative = Path(str(template["relative_path"]))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"template {template.get('template_id')} has unsafe path")
            continue
        docx_path = root / relative
        if not docx_path.is_file():
            errors.append(f"template {template.get('template_id')} file missing")
            continue
        try:
            with ZipFile(docx_path) as archive:
                if archive.testzip():
                    errors.append(f"template {template.get('template_id')} has corrupt ZIP member")
                for name in archive.namelist():
                    if name.endswith((".xml", ".rels")):
                        ET.fromstring(archive.read(name))
                document_xml = ET.fromstring(archive.read("word/document.xml"))
                visible_text = "".join(document_xml.itertext())
                semantic_markers = {
                    "type code": str(template.get("type_code", "")),
                    "template name": str(template.get("name", "")),
                    "placeholder marker": "待填充",
                }
                if template.get("approval_status") == "active":
                    semantic_markers.update(
                        {
                            "active status": "active / active",
                            "lawyer approval gate": "律师批准：已批准",
                            "activation gate": "激活状态：active",
                        }
                    )
                else:
                    semantic_markers.update(
                        {
                            "candidate status": "candidate / inactive",
                            "lawyer approval gate": "律师批准：未批准",
                            "activation gate": "激活状态：inactive",
                        }
                    )
                for marker_name, marker in semantic_markers.items():
                    if marker and marker not in visible_text:
                        errors.append(
                            f"template {template.get('template_id')} missing {marker_name}: {marker}"
                        )
                if template.get("approval_status") != "active" and "律师批准：已批准" in visible_text:
                    errors.append(
                        f"template {template.get('template_id')} falsely claims lawyer approval"
                    )
        except (BadZipFile, ET.ParseError) as exc:
            errors.append(f"template {template.get('template_id')} invalid DOCX/XML: {exc}")
    active_asset_source_ids = {
        source_id
        for item in modules + principles
        if item.get("approval_status") == "active"
        for source_id in item.get("source_ids", [])
    }
    for source in sources:
        missing = SOURCE_REQUIRED - set(source)
        if missing:
            errors.append(f"source {source.get('source_id')} missing {sorted(missing)}")
        if source.get("source_id") in active_asset_source_ids:
            if source.get("approval_status") != "active":
                errors.append(f"source {source.get('source_id')} used by active assets must be active")
        elif source.get("approval_status") != "candidate":
            errors.append(f"source {source.get('source_id')} must remain candidate")
        if not (source.get("url") or source.get("access_scope") or source.get("discovery_channel")):
            errors.append(f"source {source.get('source_id')} lacks locator")
    discovery_source_ids = {
        item.get("source_id") for item in sources
        if item.get("source_kind") == "wechat_practice_article_discovery"
    }
    used_source_ids = {
        source_id
        for item in modules + principles + triggers
        for source_id in item.get("source_ids", [])
    }
    if discovery_source_ids & used_source_ids:
        errors.append("discovery-only WeChat source is used for a legal conclusion")
    for trigger in triggers:
        missing = TRIGGER_REQUIRED - set(trigger)
        if missing:
            errors.append(f"trigger {trigger.get('trigger_id')} missing {sorted(missing)}")
        _validate_independent_state(
            trigger, label=f"trigger {trigger.get('trigger_id')}", errors=errors
        )
        if trigger.get("approval_status") == "active" and not _belongs_to_active_type(trigger, active_types):
            errors.append(f"active trigger {trigger.get('trigger_id')} serves no active type")
        if not set(trigger.get("required_modules", [])).issubset(module_ids):
            errors.append(f"trigger {trigger.get('trigger_id')} references unknown module")
        if not set(trigger.get("source_ids", [])).issubset(source_ids):
            errors.append(f"trigger {trigger.get('trigger_id')} references unknown source")
    for experience in experiences:
        missing = EXPERIENCE_REQUIRED - set(experience)
        if missing:
            errors.append(f"experience {experience.get('experience_id')} missing {sorted(missing)}")
        _validate_independent_state(
            experience, label=f"experience {experience.get('experience_id')}", errors=errors
        )
        if experience.get("approval_status") == "active" and not _belongs_to_active_type(experience, active_types):
            errors.append(f"active experience {experience.get('experience_id')} serves no active type")
        if not set(experience.get("source_ids", [])).issubset(source_ids):
            errors.append(f"experience {experience.get('experience_id')} references unknown source")
    counts = manifest.get("framework_counts", {})
    expected_counts = {
        "domain_principles": len(domain_principles),
        "principles": len(principles),
        "modules": len(modules),
        "module_groups": len(groups),
        "docx_skeletons": len(templates),
        "triggers": len(triggers),
        "experience_cards": len(experiences),
        "sources": len(sources),
    }
    if counts and counts != expected_counts:
        errors.append(f"manifest framework_counts mismatch: {counts} != {expected_counts}")
    active_modules = {item.get("module_id") for item in modules if item.get("approval_status") == "active"}
    active_principles = {item.get("doctrine_id") for item in principles if item.get("approval_status") == "active"}
    active_domain_principles = {
        item.get("domain_doctrine_id")
        for item in domain_principles
        if item.get("approval_status") == "active"
    }
    if active_modules != set(manifest.get("active_module_ids", [])):
        errors.append("manifest active_module_ids mismatch")
    if active_principles != set(manifest.get("active_doctrine_ids", [])):
        errors.append("manifest active_doctrine_ids mismatch")
    if active_domain_principles != set(manifest.get("active_domain_doctrine_ids", [])):
        errors.append("manifest active_domain_doctrine_ids mismatch")
    for type_id in active_types:
        has_principle = any(
            item.get("approval_status") == "active"
            and type_id in set(item.get("type_ids", [item.get("type_id")]))
            for item in principles
        )
        has_module = any(
            item.get("approval_status") == "active"
            and type_id in set(item.get("type_ids", [item.get("type_id")]))
            for item in modules
        )
        if not has_principle or not has_module:
            errors.append(f"active type {type_id} lacks active principle or module")

    home_path = re.compile("/" + "Users/")
    family_id = re.compile(r"\bcf-[0-9a-f]{20}\b")
    long_hash = re.compile(r"\b[0-9a-f]{64}\b")
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(root)
        if home_path.search(text):
            errors.append(f"absolute user path leaked in {relative}")
        if family_id.search(text):
            errors.append(f"contract family id leaked in {relative}")
        if long_hash.search(text):
            errors.append(f"raw hash leaked in {relative}")
    for path in root.rglob("*.docx"):
        try:
            with ZipFile(path) as archive:
                docx_text = "\n".join(
                    archive.read(name).decode("utf-8", errors="replace")
                    for name in archive.namelist()
                    if name.endswith((".xml", ".rels"))
                )
        except BadZipFile:
            continue
        relative = path.relative_to(root)
        if home_path.search(docx_text):
            errors.append(f"absolute user path leaked in {relative}")
        if family_id.search(docx_text):
            errors.append(f"contract family id leaked in {relative}")
        if long_hash.search(docx_text):
            errors.append(f"raw hash leaked in {relative}")
    result = {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "active_principle_records": sum(
            1 for item in principles if item.get("approval_status") == "active"
        ),
        "active_principles": len(active_principles),
        "active_domain_principles": len(active_domain_principles),
        "active_modules": len(active_modules),
        "framework_counts": expected_counts,
        "install_eligible": bool(manifest.get("install_eligible")),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
