#!/usr/bin/env python3
"""导出轻量、平台中立的法律 Skill IR。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    from scripts.validate_legal_profile import (
        ALLOWED_STATUSES,
        REQUIRED_MODULES,
        SCHEMA_VERSION,
    )
    from scripts.legal_meta_security import parse_frontmatter
except ModuleNotFoundError:
    from validate_legal_profile import ALLOWED_STATUSES, REQUIRED_MODULES, SCHEMA_VERSION
    from legal_meta_security import parse_frontmatter


RESOURCE_DIRECTORIES = ("references", "scripts", "evals", "assets")
CACHE_DIRECTORIES = {"__pycache__", ".pytest_cache", ".mypy_cache"}
CAPABILITY_STATUSES = ("active", "not_applicable", "blocked")
LEGACY_PROFILE_DEFAULT = {
    "jurisdiction_default": "中国大陆",
    "verification": "具体法条、司法解释、时效和案例独立核验",
    "fact_evidence_model": ["材料", "事实", "法律评价", "程序"],
}


def frontmatter(skill_md: Path) -> tuple[str, str]:
    return parse_frontmatter(skill_md.read_text(encoding="utf-8"))


def _is_ignored_resource(path: Path, skill_dir: Path) -> bool:
    return any(
        part.startswith(".") or part in CACHE_DIRECTORIES
        for part in path.relative_to(skill_dir).parts
    )


def _resources(skill_dir: Path) -> dict[str, list[str]]:
    resources = {}
    for directory in RESOURCE_DIRECTORIES:
        root = skill_dir / directory
        resources[directory] = (
            sorted(
                str(path.relative_to(skill_dir))
                for path in root.rglob("*")
                if path.is_file() and not path.is_symlink() and not _is_ignored_resource(path, skill_dir)
            )
            if root.exists()
            else []
        )
    return resources


def _profile_export(
    legal_profile: object,
) -> tuple[object, dict[str, int], list[str]]:
    if not isinstance(legal_profile, dict):
        return (
            legal_profile,
            {"total": 0, "active": 0, "not_applicable": 0, "blocked": 0},
            ["法律能力配置尚未迁移至 universal-legal-core/v0.1；已保留原始字段，未生成模块摘要。"],
        )

    modules = legal_profile.get("modules")
    if legal_profile.get("schema_version") != SCHEMA_VERSION or not isinstance(modules, dict):
        return (
            legal_profile,
            {"total": 0, "active": 0, "not_applicable": 0, "blocked": 0},
            ["法律能力配置尚未迁移至 universal-legal-core/v0.1；已保留原始字段，未生成模块摘要。"],
        )

    ordered_module_ids = [module_id for module_id in REQUIRED_MODULES if module_id in modules]
    ordered_module_ids.extend(sorted(set(modules) - set(REQUIRED_MODULES)))
    ordered_profile = dict(legal_profile)
    ordered_profile["modules"] = {
        module_id: modules[module_id] for module_id in ordered_module_ids
    }
    summary = {"total": len(ordered_module_ids), **{status: 0 for status in CAPABILITY_STATUSES}}
    for module in ordered_profile["modules"].values():
        if isinstance(module, dict) and module.get("status") in ALLOWED_STATUSES:
            summary[module["status"]] += 1
    return ordered_profile, summary, []


def _contract_export(manifest: dict) -> tuple[dict, list[str]]:
    """读取目标 Skill 自己的语义契约；缺失时保持空值，绝不套用元技能内容。"""
    contract = manifest.get("skill_contract")
    if not isinstance(contract, dict):
        return {}, ["manifest 缺少 skill_contract；IR 已保留空语义字段，未套用元技能默认任务。"]
    return contract, []


def build_ir(skill_dir: Path, generated_at: str | None = None) -> dict:
    """从 Skill 目录构造 IR，不写入文件或修改输入目录。"""
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise ValueError("缺少根目录 SKILL.md")
    name, description = frontmatter(skill_md)
    manifest_path = skill_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json 必须为 JSON 对象")
    cases_path = skill_dir / "evals/trigger_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8")) if cases_path.exists() else []
    cases = cases.get("cases", cases) if isinstance(cases, dict) else cases
    if not isinstance(cases, list):
        raise ValueError("evals/trigger_cases.json 必须为数组或含 cases 数组的对象")
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict) or not str(case.get("prompt", "")).strip():
            raise ValueError(f"evals/trigger_cases.json 第 {index} 项必须为含非空 prompt 的对象")
    grouped = {
        "should": [case["prompt"] for case in cases if case.get("kind") == "should-trigger"],
        "should_not": [case["prompt"] for case in cases if case.get("kind") == "should-not-trigger"],
        "near_neighbor": [case["prompt"] for case in cases if case.get("kind") == "near-neighbor"],
    }
    legal_profile, capability_summary, migration_warnings = _profile_export(
        manifest.get("legal_profile", LEGACY_PROFILE_DEFAULT)
    )
    contract, contract_warnings = _contract_export(manifest)
    migration_warnings.extend(contract_warnings)

    return {
        "schema_version": "legal-skill-ir/v0.3",
        "generated_at": generated_at or date.today().isoformat(),
        "name": name,
        "version": manifest.get("version", "0.1.0"),
        "owner": manifest.get("owner", ""),
        "homepage": manifest.get("homepage", ""),
        "branding_mode": manifest.get("branding_mode", "branded"),
        "provenance": manifest.get("creator", {}),
        "downstream_attribution": manifest.get("downstream_attribution", {}),
        "quality_evidence_digests": manifest.get("quality_evidence_digests", {}),
        "self_containment": manifest.get("self_containment", {}),
        "maturity": manifest.get("maturity_tier", "scaffold"),
        "maturity_label_zh": manifest.get("maturity_label_zh", "草案级"),
        "description": description,
        "job": contract.get("job", ""),
        "decision": contract.get("decision", {}),
        "target_users": contract.get("target_users", []),
        "inputs": contract.get("inputs", []),
        "outputs": contract.get("outputs", []),
        "exclusions": contract.get("exclusions", []),
        "triggers": grouped,
        "workflow": contract.get("workflow", []),
        "decision_points": contract.get("decision_points", []),
        "failure_modes": contract.get("failure_modes", []),
        "legal_profile": legal_profile,
        "capability_summary": capability_summary,
        "migration_warnings": migration_warnings,
        "resources": _resources(skill_dir),
        "permissions": manifest.get("permissions", {}),
        "degradation": manifest.get("degradation", {}),
        "eval_plan": manifest.get("eval_plan", {}),
        "evidence_boundary": manifest.get("evidence_boundary", {}),
        "review": manifest.get("review", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="导出法律 Skill IR JSON")
    parser.add_argument("skill_dir", help="Skill 根目录")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = skill_dir / output
    try:
        ir = build_ir(skill_dir)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}")
        return 1
    print(f"已导出法律 Skill IR：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
