#!/usr/bin/env python3
"""验证通用法律能力配置的完整性，不评价实体法律结论。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MODULE_CONTRACTS = {
    "task_context": (
        "任务目的与受众",
        ("task_type", "decision_goal", "target_users", "audience", "decision_owner", "reviewer"),
    ),
    "jurisdiction": (
        "法域",
        ("jurisdiction_scope", "governing_law_basis", "forum_or_seat", "conflict_rules"),
    ),
    "temporal": (
        "时间",
        (
            "as_of_date",
            "event_timeline",
            "applicable_versions",
            "limitation_and_deadline_checks",
            "temporal_gaps",
        ),
    ),
    "actors": (
        "主体角色",
        ("actor_map", "legal_status", "roles_and_interests", "authority_and_capacity", "conflicts_of_interest"),
    ),
    "matter": (
        "法律事项",
        ("issue_scope", "legal_relationships", "issue_tree", "material_facts", "exclusions"),
    ),
    "claims_and_elements": (
        "请求与要件",
        ("claims_defenses", "legal_elements", "element_fact_mapping", "remedies_requested", "counterarguments"),
    ),
    "authority_and_interpretation": (
        "法源与解释",
        (
            "authority_inventory",
            "authority_hierarchy",
            "verification_status",
            "interpretation_method",
            "application_analysis",
            "conflicting_authorities",
        ),
    ),
    "proof": (
        "证明",
        ("facts_to_prove", "evidence_locator", "burden_of_proof", "standard_of_proof", "evidence_gaps", "adverse_consequences"),
    ),
    "procedure": (
        "程序",
        (
            "forum_and_jurisdiction",
            "procedural_posture",
            "procedural_steps",
            "deadlines_to_verify",
            "admissibility_or_prerequisites",
            "procedural_risks",
        ),
    ),
    "outcomes_and_enforcement": (
        "结果与执行",
        ("outcome_scenarios", "legal_effects", "liability_and_exposure", "enforceability", "enforcement_path", "recovery_constraints"),
    ),
    "strategy_and_uncertainty": (
        "策略与不确定性",
        ("options", "assumptions", "uncertainties", "scenario_analysis", "recommended_actions", "escalation_triggers"),
    ),
    "governance": (
        "职业治理",
        (
            "confidentiality_and_data_boundary",
            "permissions",
            "human_review",
            "source_and_audit_trail",
            "professional_responsibility_limits",
            "review_cycle",
        ),
    ),
}
REQUIRED_MODULES = tuple(MODULE_CONTRACTS)
ALLOWED_STATUSES = {"active", "not_applicable", "blocked"}
SCHEMA_VERSION = "universal-legal-core/v0.1"
ACTIVATION_POLICY = "mandatory-review-conditional-expansion"
PLACEHOLDER_REASONS = {"按需", "无", "略", "否", "无关", "不适用", "暂无", "未知", "待定"}


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _contains_chinese(value: object) -> bool:
    return isinstance(value, str) and re.search(r"[\u4e00-\u9fff]", value) is not None


def _specific_reason(value: object) -> bool:
    if not _nonempty_text(value):
        return False
    normalized = re.sub(r"[\s\W_]+", "", value)
    return len(normalized) >= 4 and normalized not in PLACEHOLDER_REASONS


def validate_profile(
    manifest: dict[object, object], strict: bool
) -> tuple[list[str], list[str]]:
    """返回法律能力配置的中文错误和警告，且不产生任何副作用。"""
    errors: list[str] = []
    warnings: list[str] = []
    profile = manifest.get("legal_profile")

    if not isinstance(profile, dict) or "schema_version" not in profile:
        if strict:
            errors.append("缺少通用法律能力模型")
        else:
            warnings.append("旧版法律能力配置，建议升级")
        return errors, warnings

    if profile.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"法律能力模型版本必须为 {SCHEMA_VERSION}")
    if profile.get("activation_policy") != ACTIVATION_POLICY:
        errors.append(f"法律能力模型激活策略必须为 {ACTIVATION_POLICY}")

    modules = profile.get("modules")
    if not isinstance(modules, dict):
        errors.append("法律能力模型的 modules 必须为对象")
        return errors, warnings

    required_ids = set(REQUIRED_MODULES)
    actual_ids = set(modules)
    missing_ids = required_ids - actual_ids
    extra_ids = actual_ids - required_ids
    if missing_ids:
        errors.append("法律能力模型缺少模块：" + "、".join(sorted(missing_ids)))
    if extra_ids:
        errors.append("法律能力模型存在未知模块：" + "、".join(sorted(extra_ids)))

    for module_id in REQUIRED_MODULES:
        module = modules.get(module_id)
        if not isinstance(module, dict):
            if module_id in modules:
                errors.append(f"模块 {module_id} 必须为对象")
            continue
        expected_label, minimum_outputs = MODULE_CONTRACTS[module_id]
        if module.get("label_zh") != expected_label:
            errors.append(f"模块 {module_id} 的中文标签必须为 {expected_label}")
        status = module.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"模块 {module_id} 的状态不合法")
            continue
        if not _specific_reason(module.get("reason")):
            errors.append(f"模块 {module_id} 缺少具体理由；理由必须与目标任务相关")
        if status == "active":
            required_outputs = module.get("required_outputs")
            if not isinstance(required_outputs, list) or not required_outputs or not all(
                _nonempty_text(item) for item in required_outputs
            ):
                errors.append(f"已启用模块 {module_id} 缺少最低输出")
            else:
                missing_outputs = set(minimum_outputs) - set(required_outputs)
                if missing_outputs:
                    errors.append(
                        f"已启用模块 {module_id} 缺少通用最低输出："
                        + "、".join(sorted(missing_outputs))
                    )
        elif status == "not_applicable":
            if module.get("required_outputs") not in (None, []):
                warnings.append(f"不适用模块 {module_id} 仍声明了最低输出，建议清空")
        elif status == "blocked":
            if not _specific_reason(module.get("gap")):
                errors.append(f"受阻模块 {module_id} 缺少输入或依据缺口")
            if not _specific_reason(module.get("fallback")):
                errors.append(f"受阻模块 {module_id} 缺少停止或降级路径")
            if not _specific_reason(module.get("human_owner")):
                errors.append(f"受阻模块 {module_id} 缺少人工责任人")
            if not _specific_reason(module.get("review_trigger")):
                errors.append(f"受阻模块 {module_id} 缺少重新核验触发条件")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="验证通用法律能力配置")
    parser.add_argument("skill_dir", help="Skill 根目录")
    parser.add_argument("--strict", action="store_true", help="旧版配置按错误处理")
    args = parser.parse_args()
    manifest_path = Path(args.skill_dir).resolve() / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"错误：manifest.json 无法读取：{exc}")
        return 1

    errors, warnings = validate_profile(manifest, strict=args.strict)
    for warning in warnings:
        print(f"警告：{warning}")
    for error in errors:
        print(f"错误：{error}")
    if errors:
        print(f"验证失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"验证通过：{manifest_path.parent.name}（{len(warnings)} 个警告）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
