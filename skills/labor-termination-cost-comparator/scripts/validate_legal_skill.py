#!/usr/bin/env python3
"""验证法律类 Skill 的结构、入口、评测文件和基础信任边界。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from scripts.validate_legal_profile import REQUIRED_MODULES, validate_profile
    from scripts.legal_meta_security import (
        load_json_file,
        parse_frontmatter,
        resolve_regular_file,
        safe_relative_path,
        sha256_file,
        valid_review_date,
    )
except ModuleNotFoundError:
    from validate_legal_profile import REQUIRED_MODULES, validate_profile
    from legal_meta_security import (
        load_json_file,
        parse_frontmatter,
        resolve_regular_file,
        safe_relative_path,
        sha256_file,
        valid_review_date,
    )


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}"),
    re.compile(r"(?i)(?:api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9._~+/-]{16,}['\"]"),
    re.compile(r"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s/:]+:[^\s/@]+@"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

RESEARCH_SOURCE_FILE = Path("references/skill-research-sources.md")
REQUIRED_META_RESOURCES = (
    Path("README.md"),
    Path("CONTRIBUTING.md"),
    Path("SECURITY.md"),
    Path("CHANGELOG.md"),
    Path("RELEASE.md"),
    Path("LICENSE"),
    Path("NOTICE"),
    RESEARCH_SOURCE_FILE,
    Path("references/intent-and-scope.md"),
    Path("references/legal-core-rules.md"),
    Path("references/legal-eval-method.md"),
    Path("references/legal-method-core.md"),
    Path("references/legal-quality-gates.md"),
    Path("references/legal-scenario-archetypes.md"),
    Path("references/legal-skill-ir.md"),
    Path("references/legal-skill-publishing.md"),
    Path("references/legal-workspace-rules.md"),
    Path("references/legal-workflow-folder-design.md"),
    Path("references/resource-verifier-routing.md"),
    Path("references/oslaw-resource-catalog.md"),
    Path("references/workflow-profiles/case-analysis-v2.md"),
    Path("references/workflow-profiles/due-diligence.md"),
    Path("references/workflow-profiles/contract-review.md"),
    Path("references/workflow-profiles/legal-research.md"),
    Path("references/prior-art-and-trust.md"),
    Path("references/universal-legal-capability-model.md"),
    Path("references/user-input-and-acceptance.md"),
    Path("assets/templates/legal-skill-output-contract.md"),
    Path("assets/templates/legal-capability-profile.json"),
    Path("assets/templates/legal-skill-intake.json"),
    Path("assets/templates/downstream-output-assertions.json"),
    Path("assets/templates/downstream-skill.template.md"),
    Path("assets/templates/downstream-manifest.template.json"),
    Path("assets/templates/downstream-interface.template.yaml"),
    Path("assets/templates/downstream-trigger-cases.template.json"),
    Path("assets/templates/downstream-creation-handoff.template.md"),
    Path("assets/templates/provider-trigger-observations.template.json"),
    Path("assets/templates/文件夹使用说明.md"),
    Path("assets/templates/legal-scenario-checklists/compliance_regulatory.md"),
    Path("assets/templates/legal-scenario-checklists/contract_review.md"),
    Path("assets/templates/legal-scenario-checklists/dispute_resolution.md"),
    Path("assets/templates/legal-scenario-checklists/document_drafting.md"),
    Path("assets/templates/legal-scenario-checklists/evidence_files.md"),
    Path("assets/templates/legal-scenario-checklists/legal_research.md"),
    Path("assets/templates/legal-scenario-checklists/legal_retrieval.md"),
    Path("assets/templates/legal-scenario-checklists/document_review_redline.md"),
    Path("ATTRIBUTION.md"),
    Path("TRADEMARKS.md"),
    Path("scripts/create_legal_skill.py"),
    Path("scripts/plan_legal_workspace.py"),
    Path("scripts/evaluate_trigger_cases.py"),
    Path("scripts/export_legal_skill_ir.py"),
    Path("scripts/legal_meta_security.py"),
    Path("scripts/legal_meta.py"),
    Path("scripts/migrate_legal_skill.py"),
    Path("scripts/validate_legal_profile.py"),
    Path("scripts/validate_legal_skill.py"),
    Path("evals/output_assertions.json"),
    Path("evals/trigger_cases.json"),
    Path("evals/universal_legal_cases.json"),
)
MATURITY_LABELS = {
    "scaffold": "草案级",
    "production": "专业复用级",
    "library": "基础设施级",
    "governed": "高风险治理级",
}
SCENARIO_ARCHETYPES = {
    "dispute_resolution",
    "contract_review",
    "document_drafting",
    "legal_research",
    "compliance_regulatory",
    "legal_retrieval",
    "evidence_files",
    "document_review_redline",
    "other",
}
MATURITY_ORDER = {name: index for index, name in enumerate(MATURITY_LABELS)}
EVIDENCE_KEYS_BY_TIER = {
    "scaffold": ("trigger_cases",),
    "production": ("output_contract", "output_assertions", "universal_cases"),
    "library": ("skill_ir", "prior_art", "trust_review", "creation_handoff"),
    "governed": ("fixture_index", "permission_policy", "rollback_plan", "human_review_evidence"),
}
SEMANTIC_CONTRACT_FIELDS = (
    "job",
    "decision",
    "target_users",
    "inputs",
    "outputs",
    "exclusions",
    "workflow",
    "decision_points",
    "failure_modes",
)
SKIPPED_DIRECTORY_NAMES = {".git", ".superpowers", "__pycache__", ".pytest_cache"}
PLACEHOLDER_MARKERS = ("【填写", "【替换", "replace-with", "示例仅供")


def _contains_placeholder_marker(text: str) -> bool:
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def _valid_review_date(value: object) -> bool:
    """人工复核日期必须是真实存在且不晚于今天的 YYYY-MM-DD 日期。"""
    return valid_review_date(value)


def requires_strict_profile(manifest: dict[object, object]) -> bool:
    """判定新模型要求是否适用于当前 Skill，版本比较使用整数元组。"""
    if manifest.get("name") == "legal-meta-skill":
        return True
    profile = manifest.get("legal_profile")
    if isinstance(profile, dict) and "schema_version" in profile:
        return True
    creator = manifest.get("creator")
    if not isinstance(creator, dict) or creator.get("created_with") != "legal-meta-skill":
        return False
    version = creator.get("created_with_version")
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", str(version))
    if not match:
        return False
    return tuple(int(part) for part in match.groups()) >= (0, 5, 0)


def iter_package_files(skill_dir: Path):
    """遍历交付包文件，排除开发辅助及缓存目录。"""
    for path in skill_dir.rglob("*"):
        relative_parts = path.relative_to(skill_dir).parts
        if any(part in SKIPPED_DIRECTORY_NAMES for part in relative_parts):
            continue
        yield path


def read_frontmatter(skill_md: Path) -> tuple[str, str]:
    return parse_frontmatter(skill_md.read_text(encoding="utf-8"))


def _nonempty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def _specific_evaluation_reason(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = re.sub(r"[\s\W_]+", "", value)
    return len(normalized) >= 4 and normalized not in {"按需", "无", "略"}


def _maturity_at_least(maturity: str, minimum: str) -> bool:
    return MATURITY_ORDER.get(maturity, -1) >= MATURITY_ORDER[minimum]


def _safe_relative_path(value: object) -> bool:
    return safe_relative_path(value)


def _validate_semantic_contract(manifest: dict, maturity: str) -> list[str]:
    """专业复用级以上必须包含目标 Skill 自己的非空语义契约。"""
    if not _maturity_at_least(maturity, "production"):
        return []
    errors: list[str] = []
    contract = manifest.get("skill_contract")
    if not isinstance(contract, dict):
        return ["专业复用级以上缺少 manifest.skill_contract"]
    for field in SEMANTIC_CONTRACT_FIELDS:
        value = contract.get(field)
        if field == "decision":
            if not isinstance(value, dict) or not all(
                isinstance(value.get(key), str) and value[key].strip()
                for key in ("goal", "owner", "supported_action")
            ):
                errors.append("skill_contract.decision 缺少 goal、owner 或 supported_action")
        elif field == "job":
            if not isinstance(value, str) or not value.strip():
                errors.append("skill_contract.job 不能为空")
        elif not _nonempty_string_list(value):
            errors.append(f"skill_contract.{field} 必须为非空字符串数组")
    return errors


def _validate_maturity_evidence(skill_dir: Path, manifest: dict, maturity: str) -> list[str]:
    errors: list[str] = []
    evidence = manifest.get("quality_evidence")
    if not isinstance(evidence, dict):
        return ["manifest 缺少 quality_evidence，无法证明成熟度"]
    for tier, keys in EVIDENCE_KEYS_BY_TIER.items():
        if not _maturity_at_least(maturity, tier):
            continue
        for key in keys:
            relative = evidence.get(key)
            if not _safe_relative_path(relative):
                errors.append(f"quality_evidence.{key} 必须为包内安全相对路径")
                continue
            raw_path = skill_dir / str(relative)
            if not raw_path.exists():
                errors.append(f"成熟度证据不存在：{relative}")
                continue
            try:
                evidence_path = resolve_regular_file(skill_dir, relative, f"quality_evidence.{key}")
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if evidence_path.stat().st_size == 0:
                errors.append(f"成熟度证据为空文件：{relative}")
                continue
            try:
                text = evidence_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if str(relative).endswith(".json"):
                try:
                    json.loads(text)
                except json.JSONDecodeError as exc:
                    errors.append(f"成熟度证据 JSON 无法解析：{relative}：{exc}")
            if _contains_placeholder_marker(text):
                errors.append(f"成熟度证据仍含占位内容：{relative}")
            expected_hash = (manifest.get("quality_evidence_digests") or {}).get(str(relative))
            if expected_hash and expected_hash != sha256_file(evidence_path):
                errors.append(f"成熟度证据哈希不匹配：{relative}")

    digests = manifest.get("quality_evidence_digests")
    is_meta_generated = manifest.get("name") == "legal-meta-skill" or (
        isinstance(manifest.get("creator"), dict)
        and manifest["creator"].get("created_with") == "legal-meta-skill"
    )
    if is_meta_generated and _maturity_at_least(maturity, "library") and not isinstance(digests, dict):
        errors.append("基础设施级以上必须提供 quality_evidence_digests，防止证据被替换")

    ir_relative = evidence.get("skill_ir")
    if is_meta_generated and _maturity_at_least(maturity, "library") and _safe_relative_path(ir_relative):
        try:
            ir = load_json_file(resolve_regular_file(skill_dir, ir_relative, "quality_evidence.skill_ir"), "skill-ir")
            if not isinstance(ir, dict):
                errors.append("skill-ir.json 必须为对象")
            else:
                if ir.get("name") != manifest.get("name"):
                    errors.append("skill-ir.json 的 name 与 manifest 不一致")
                if ir.get("version") != manifest.get("version"):
                    errors.append("skill-ir.json 的 version 与 manifest 不一致")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def _validate_library_governance(manifest: dict, maturity: str) -> list[str]:
    if not _maturity_at_least(maturity, "library"):
        return []
    errors: list[str] = []
    for field in ("permissions", "degradation", "eval_plan"):
        value = manifest.get(field)
        if not isinstance(value, dict) or not value:
            errors.append(f"基础设施级以上缺少非空 manifest.{field}")
    review = manifest.get("review")
    if not isinstance(review, dict) or not all(
        (
            isinstance(review.get("owner"), str) and review["owner"].strip(),
            isinstance(review.get("cadence"), str) and review["cadence"].strip(),
            _nonempty_string_list(review.get("reverification_triggers")),
        )
    ):
        errors.append("基础设施级以上 review 缺少 owner、cadence 或 reverification_triggers")
    if _maturity_at_least(maturity, "governed"):
        evidence_boundary = manifest.get("evidence_boundary")
        present = evidence_boundary.get("present") if isinstance(evidence_boundary, dict) else None
        if not _nonempty_string_list(present):
            errors.append("高风险治理级缺少已取得的真实运行或人工复核证据")
    return errors


def _validate_governed_evidence(skill_dir: Path, manifest: dict, maturity: str) -> list[str]:
    if maturity != "governed":
        return []
    errors: list[str] = []
    evidence = manifest.get("quality_evidence", {})
    if not isinstance(evidence, dict):
        return errors
    fixture_path = evidence.get("fixture_index")
    human_path = evidence.get("human_review_evidence")
    for key, value in (("fixture_index", fixture_path), ("human_review_evidence", human_path)):
        if not _safe_relative_path(value):
            errors.append(f"quality_evidence.{key} 必须为包内安全相对路径")
    if errors:
        return errors
    try:
        fixtures = load_json_file(
            resolve_regular_file(skill_dir, fixture_path, "quality_evidence.fixture_index"),
            "高风险治理级 fixture_index",
        )
        if not isinstance(fixtures, list) or not fixtures:
            errors.append("高风险治理级 fixture_index 必须为非空数组")
        else:
            for index, fixture in enumerate(fixtures, start=1):
                if not isinstance(fixture, dict) or not all(
                    (
                        isinstance(fixture.get("id"), str) and fixture["id"].strip(),
                        _nonempty_string_list(fixture.get("input_files")),
                        isinstance(fixture.get("authorization"), str) and fixture["authorization"].strip(),
                        isinstance(fixture.get("expected_boundary"), str) and fixture["expected_boundary"].strip(),
                    )
                ):
                    errors.append(f"高风险治理级 fixture 第 {index} 项字段不完整")
                    continue
                for relative in fixture["input_files"]:
                    try:
                        resolve_regular_file(skill_dir, relative, "高风险治理级 fixture 文件")
                    except ValueError:
                        errors.append(f"高风险治理级 fixture 文件不存在或路径不安全：{relative}")
    except (ValueError, TypeError) as exc:
        errors.append(f"高风险治理级 fixture_index 无法读取：{exc}")

    try:
        reviews = load_json_file(
            resolve_regular_file(skill_dir, human_path, "quality_evidence.human_review_evidence"),
            "高风险治理级人工复核证据",
        )
        if not isinstance(reviews, list) or not reviews:
            errors.append("高风险治理级人工复核证据必须为非空数组")
        else:
            for index, review in enumerate(reviews, start=1):
                if not isinstance(review, dict) or not all(
                    isinstance(review.get(field), str) and review[field].strip()
                    for field in ("reviewer", "reviewed_at", "case_id", "outcome", "confidence", "reason")
                ):
                    errors.append(f"高风险治理级人工复核记录第 {index} 项字段不完整")
                elif not _valid_review_date(review["reviewed_at"]):
                    errors.append(f"高风险治理级人工复核记录第 {index} 项日期格式无效")
    except (ValueError, TypeError) as exc:
        errors.append(f"高风险治理级人工复核证据无法读取：{exc}")
    return errors


def validate_evaluation_design(
    skill_dir: Path,
    *,
    maturity: str = "library",
    require_full_module_activation: bool = True,
    require_lightweight_case: bool = True,
) -> list[str]:
    """静态校验法律输出断言及通用能力合成用例。"""
    errors: list[str] = []
    assertions_path = skill_dir / "evals/output_assertions.json"
    cases_path = skill_dir / "evals/universal_legal_cases.json"
    if not assertions_path.is_file() and not cases_path.is_file():
        if _maturity_at_least(maturity, "production"):
            return ["专业复用级以上缺少法律输出断言和合成评测用例"]
        return errors
    if not assertions_path.is_file():
        return ["存在通用法律评测用例但缺少 evals/output_assertions.json"]
    if not cases_path.is_file():
        return ["存在法律输出断言但缺少 evals/universal_legal_cases.json"]

    try:
        assertion_document = json.loads(assertions_path.read_text(encoding="utf-8"))
        case_document = json.loads(cases_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"法律评测文件无法读取：{exc}"]

    assertions = assertion_document.get("assertions", []) if isinstance(assertion_document, dict) else []
    assertion_ids: set[str] = set()
    if not isinstance(assertions, list):
        errors.append("output_assertions.json 的 assertions 必须为数组")
        assertions = []
    for index, assertion in enumerate(assertions, start=1):
        if not isinstance(assertion, dict):
            errors.append(f"输出断言第 {index} 项必须为对象")
            continue
        assertion_id = assertion.get("id")
        if not isinstance(assertion_id, str) or not assertion_id.strip():
            errors.append(f"输出断言第 {index} 项缺少 id")
            continue
        if assertion_id in assertion_ids:
            errors.append(f"输出断言 id 重复：{assertion_id}")
        assertion_ids.add(assertion_id)
        if not _nonempty_string_list(assertion.get("must")):
            errors.append(f"输出断言 {assertion_id} 缺少非空 must")
        must_not = assertion.get("must_not")
        if must_not is not None and not _nonempty_string_list(must_not):
            errors.append(f"输出断言 {assertion_id} 的 must_not 必须为非空字符串数组")

    cases = case_document.get("cases", []) if isinstance(case_document, dict) else []
    if not isinstance(cases, list) or not cases:
        errors.append("universal_legal_cases.json 必须包含非空 cases 数组")
        return errors
    minimum_case_count = 7 if _maturity_at_least(maturity, "library") else 1
    if len(cases) < minimum_case_count:
        if minimum_case_count == 7:
            errors.append("基础设施级以上通用法律评测集至少需要七类合成用例")
        else:
            errors.append("专业复用级法律评测集至少需要一个合成用例")

    required_modules = set(REQUIRED_MODULES)
    seen_case_ids: set[str] = set()
    active_coverage: set[str] = set()
    assertion_coverage: set[str] = set()
    has_not_applicable = False
    blocked_case_count = 0
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"通用法律评测用例第 {index} 项必须为对象")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"通用法律评测用例第 {index} 项缺少 id")
            case_id = f"第{index}项"
        elif case_id in seen_case_ids:
            errors.append(f"通用法律评测用例 id 重复：{case_id}")
        seen_case_ids.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"通用法律评测用例 {case_id} 缺少 prompt")

        expected = case.get("expected_modules")
        if not isinstance(expected, dict):
            errors.append(f"通用法律评测用例 {case_id} 缺少 expected_modules")
            continue
        status_sets: dict[str, set[str]] = {}
        for status in ("active", "not_applicable", "blocked"):
            value = expected.get(status)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"通用法律评测用例 {case_id} 的 {status} 必须为模块 ID 数组")
                status_sets[status] = set()
                continue
            if len(value) != len(set(value)):
                errors.append(f"通用法律评测用例 {case_id} 的 {status} 存在重复模块")
            status_sets[status] = set(value)

        active = status_sets["active"]
        not_applicable = status_sets["not_applicable"]
        blocked = status_sets["blocked"]
        if blocked:
            blocked_case_count += 1
        active_coverage.update(active)
        has_not_applicable = has_not_applicable or bool(not_applicable)
        all_listed = active | not_applicable | blocked
        duplicates = (active & not_applicable) | (active & blocked) | (not_applicable & blocked)
        if duplicates:
            errors.append(f"通用法律评测用例 {case_id} 的模块状态重复：" + "、".join(sorted(duplicates)))
        unknown = all_listed - required_modules
        missing = required_modules - all_listed
        if unknown:
            errors.append(f"通用法律评测用例 {case_id} 含未知模块：" + "、".join(sorted(unknown)))
        if missing:
            errors.append(f"通用法律评测用例 {case_id} 未记录模块状态：" + "、".join(sorted(missing)))

        status_reasons = case.get("status_reasons", {})
        if not isinstance(status_reasons, dict):
            errors.append(f"通用法律评测用例 {case_id} 的 status_reasons 必须为对象")
            status_reasons = {}
        for module_id in sorted(not_applicable):
            reason = status_reasons.get(module_id)
            if not _specific_evaluation_reason(reason):
                errors.append(f"通用法律评测用例 {case_id} 的不适用模块 {module_id} 缺少具体理由")
        for module_id in sorted(blocked):
            boundary = status_reasons.get(module_id)
            if not isinstance(boundary, dict) or not all(
                isinstance(boundary.get(field), str) and boundary[field].strip()
                for field in ("gap", "fallback", "human_owner", "review_trigger")
            ):
                errors.append(
                    f"通用法律评测用例 {case_id} 的受阻模块 {module_id} "
                    "缺少 gap、fallback、human_owner 或 review_trigger"
                )

        references = case.get("assertion_ids")
        if not _nonempty_string_list(references):
            errors.append(f"通用法律评测用例 {case_id} 缺少 assertion_ids")
        else:
            unknown_assertions = set(references) - assertion_ids
            if unknown_assertions:
                errors.append(f"通用法律评测用例 {case_id} 引用了未知断言：" + "、".join(sorted(unknown_assertions)))
            assertion_coverage.update(set(references) & assertion_ids)
        if not _nonempty_string_list(case.get("manual_review")):
            errors.append(f"通用法律评测用例 {case_id} 缺少人工复核项")

    uncovered = required_modules - active_coverage
    if require_full_module_activation and uncovered:
        errors.append("通用法律评测集未启用覆盖模块：" + "、".join(sorted(uncovered)))
    uncovered_assertions = assertion_ids - assertion_coverage
    if uncovered_assertions:
        errors.append("通用法律评测集未覆盖输出断言：" + "、".join(sorted(uncovered_assertions)))
    if not has_not_applicable:
        errors.append("通用法律评测集缺少包含 not_applicable 的条件展开用例")
    if _maturity_at_least(maturity, "library") and blocked_case_count < 4:
        errors.append("基础设施级以上通用法律评测集至少需要四类 blocked 停机用例")
    lightweight_cases = [
        case
        for case in cases
        if isinstance(case, dict)
        and isinstance(case.get("expected_modules"), dict)
        and set(case["expected_modules"].get("not_applicable", []))
        >= {"actors", "claims_and_elements", "proof", "procedure", "outcomes_and_enforcement"}
    ]
    if require_lightweight_case and not lightweight_cases:
        errors.append("通用法律评测集缺少能实质收缩五个无关模块的轻量条件展开用例")
    return errors


def check(skill_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["缺少根目录 SKILL.md"], []

    try:
        name, description = read_frontmatter(skill_md)
    except ValueError as exc:
        return [str(exc)], []

    if name != skill_dir.name:
        errors.append(f"frontmatter name={name!r} 与目录名 {skill_dir.name!r} 不一致")
    if "TODO" in skill_md.read_text(encoding="utf-8"):
        errors.append("仍包含 TODO 占位内容")
    if "<" in description or ">" in description:
        errors.append("description 不能包含尖括号")

    nested = [p for p in iter_package_files(skill_dir) if p.name == "SKILL.md" and p != skill_md]
    if nested:
        errors.append("根目录之外存在精确命名的 SKILL.md：" + ", ".join(str(p.relative_to(skill_dir)) for p in nested))

    manifest: dict = {}
    maturity = "scaffold"
    is_meta_generated = False
    manifest_path = skill_dir / "manifest.json"
    if not manifest_path.is_file():
        if name == "legal-meta-skill":
            errors.append("legal-meta-skill 缺少 manifest.json")
        else:
            warnings.append("未提供 manifest.json；仅能确认官方基础结构，不能确认法律成熟度")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"manifest.json 无法读取：{exc}")

    if manifest:
        creator = manifest.get("creator")
        is_meta_generated = name == "legal-meta-skill" or (
            isinstance(creator, dict) and creator.get("created_with") == "legal-meta-skill"
        )
        if manifest.get("name") != name:
            errors.append("manifest.name 与 frontmatter name 不一致")
        if not manifest.get("version"):
            errors.append("manifest 缺少 version")
        maturity = manifest.get("maturity_tier", "")
        if maturity not in MATURITY_LABELS:
            if is_meta_generated:
                errors.append("由 legal-meta-skill 生成的 Skill 必须声明合法 maturity_tier")
            else:
                warnings.append("manifest 未声明合法 maturity_tier；按草案级审计")
            maturity = "scaffold"
        elif manifest.get("maturity_label_zh") != MATURITY_LABELS[maturity]:
            errors.append("manifest 的成熟度机器码与中文名称不一致")

        if is_meta_generated:
            if manifest.get("license") != "Apache-2.0":
                errors.append("由 legal-meta-skill 新建的包必须声明 Apache-2.0，其他授权需单独人工处理")
            for relative in ("LICENSE", "NOTICE"):
                if not (skill_dir / relative).is_file():
                    errors.append(f"由 legal-meta-skill 新建的包缺少 {relative}")
            notice_path = skill_dir / "NOTICE"
            if notice_path.is_file():
                try:
                    notice_text = notice_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    errors.append("NOTICE 必须为 UTF-8 文本")
                else:
                    if "CSlawyer" not in notice_text:
                        errors.append("NOTICE 必须保留 CSlawyer 署名")
            for relative in ("ATTRIBUTION.md", "TRADEMARKS.md"):
                if not (skill_dir / relative).is_file():
                    errors.append(f"由 legal-meta-skill 新建的包缺少 {relative}")
            archetype = manifest.get("scenario_archetype")
            if _maturity_at_least(maturity, "production"):
                if archetype not in SCENARIO_ARCHETYPES:
                    errors.append("专业复用级以上 manifest 缺少合法 scenario_archetype 场景原型声明")
                if not (skill_dir / "references" / "legal-method-core.md").is_file():
                    errors.append("专业复用级以上缺少 references/legal-method-core.md")
                if archetype in SCENARIO_ARCHETYPES and archetype != "other" and not (
                    skill_dir / "references" / f"{archetype}.md"
                ).is_file():
                    errors.append(f"专业复用级以上缺少场景检查清单 references/{archetype}.md")
            elif archetype not in SCENARIO_ARCHETYPES:
                warnings.append("草案级 manifest 缺少合法 scenario_archetype 场景原型声明")
            if _maturity_at_least(maturity, "production"):
                if not (skill_dir / "agents/interface.yaml").is_file():
                    errors.append("专业复用级以上缺少 agents/interface.yaml")
                targets = manifest.get("target_platforms", ["openai"])
                if isinstance(targets, list) and "openai" in targets and not (
                    skill_dir / "agents/openai.yaml"
                ).is_file():
                    errors.append("声明支持 OpenAI 但缺少 agents/openai.yaml")
        if is_meta_generated or _maturity_at_least(maturity, "production"):
            if not is_meta_generated:
                warnings.append("manifest 声明专业复用级以上成熟度但非 legal-meta-skill 生成，成熟度证据未经生成器背书")
            errors.extend(_validate_maturity_evidence(skill_dir, manifest, maturity))
            errors.extend(_validate_semantic_contract(manifest, maturity))
            errors.extend(_validate_library_governance(manifest, maturity))
            errors.extend(_validate_governed_evidence(skill_dir, manifest, maturity))
        for field in ("upstream" + "_inspiration", "required_skills", "skill_dependencies"):
            if manifest.get(field):
                errors.append(f"manifest.{field} 声明了外部 Skill 依赖；应将运行所需能力内化到当前包")
        if name == "legal-meta-skill":
            self_containment = manifest.get("self_containment", {})
            if self_containment.get("external_skill_dependencies") != []:
                errors.append("legal-meta-skill 必须将 external_skill_dependencies 保持为空列表")
            if self_containment.get("rules") != "bundled-references":
                errors.append("legal-meta-skill 的运行规则必须由包内 references 承载")
            if self_containment.get("checks") != "bundled-scripts":
                errors.append("legal-meta-skill 的确定性检查必须由包内 scripts 承载")
            if self_containment.get("templates") != "bundled-assets":
                errors.append("legal-meta-skill 的输出模板必须由包内 assets 承载")
            if self_containment.get("research") != "bundled-source-guide":
                errors.append("legal-meta-skill 的研究方法必须由包内来源指南承载")
            if self_containment.get("publishing") != "bundled-release-guide":
                errors.append("legal-meta-skill 的发布规则必须由包内发布指南承载")
            for relative in REQUIRED_META_RESOURCES:
                if not (skill_dir / relative).is_file():
                    errors.append(f"legal-meta-skill 缺少包内资源：{relative}")
        profile_errors, profile_warnings = validate_profile(
            manifest, strict=requires_strict_profile(manifest)
        )
        errors.extend(profile_errors)
        warnings.extend(profile_warnings)
        if is_meta_generated:
            branding_mode = manifest.get("branding_mode", "branded")
            if branding_mode == "white-label":
                if manifest.get("white_label_authorized") is not True:
                    errors.append("白标 Skill 缺少 white_label_authorized=true")
                warnings.append("当前 Skill 为用户明确要求的白标模式")
            else:
                identity_text = skill_md.read_text(encoding="utf-8") + json.dumps(manifest, ensure_ascii=False)
                if "CSlawyer" not in identity_text:
                    errors.append("非白标 Skill 缺少 CSlawyer 作者来源标识")
                if "https://chenshi.ai" not in identity_text:
                    errors.append("非白标 Skill 缺少 https://chenshi.ai 主页标识")

    openai_yaml = skill_dir / "agents/openai.yaml"
    if openai_yaml.is_file():
        short_match = re.search(r'^\s*short_description:\s*["\'](.*?)["\']\s*$', openai_yaml.read_text(encoding="utf-8"), re.MULTILINE)
        if short_match and not 25 <= len(short_match.group(1)) <= 64:
            errors.append("agents/openai.yaml 的 short_description 必须为 25–64 个字符")
        elif not short_match:
            warnings.append("未能静态读取 agents/openai.yaml 的 short_description，交由官方工具复核")

    referenced = set(re.findall(r"(?:references|scripts|evals|assets|reports)/[A-Za-z0-9_./-]+", skill_md.read_text(encoding="utf-8")))
    for relative in sorted(referenced):
        candidate = skill_dir / relative.rstrip("`、。")
        if not candidate.exists():
            if relative in {"reports/trigger-eval.json", "reports/skill-ir.json"}:
                warnings.append(f"运行后才生成的报告暂不存在：{relative}")
                continue
            errors.append(f"SKILL.md 引用的资源不存在：{relative}")

    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for md_file in sorted(references_dir.glob("*.md")):
            try:
                md_text = md_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for link in sorted(set(re.findall(r"\]\(([^)\s]+)\)", md_text))):
                target = link.split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                target_path = Path(target)
                if target_path.is_absolute() or ".." in target_path.parts:
                    continue
                if not (md_file.parent / target_path).exists():
                    errors.append(f"{md_file.relative_to(skill_dir)} 引用的资源不存在：{target}")

    for path in iter_package_files(skill_dir):
        if not path.is_file() or path.name.endswith(".pyc"):
            continue
        if path.name == ".DS_Store":
            errors.append(f"交付包包含系统杂项文件：{path.relative_to(skill_dir)}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"疑似密钥模式出现在 {path.relative_to(skill_dir)}")
        if path.name == "validate_legal_skill.py":
            continue
        private_path_markers = ("/" + "Users/", "/" + "home/")
        windows_user_path = re.search(r"(?:[A-Za-z]:\\Users\\|\\\\Users\\)", text)
        if any(marker in text for marker in private_path_markers) or windows_user_path:
            errors.append(f"{path.relative_to(skill_dir)} 含用户绝对路径；请改为包内相对路径或运行时参数")

    trigger_relative = "evals/trigger_cases.json"
    quality_evidence = manifest.get("quality_evidence") if isinstance(manifest, dict) else None
    if isinstance(quality_evidence, dict) and _safe_relative_path(quality_evidence.get("trigger_cases")):
        trigger_relative = str(quality_evidence["trigger_cases"])
    trigger_path = skill_dir / trigger_relative
    try:
        cases = json.loads(trigger_path.read_text(encoding="utf-8"))
        if isinstance(cases, dict):
            cases = cases.get("cases", [])
        kinds = {case.get("kind") for case in cases if isinstance(case, dict)}
        for required_kind in ("should-trigger", "should-not-trigger", "near-neighbor"):
            if required_kind not in kinds:
                errors.append(f"触发用例缺少 {required_kind}")
    except FileNotFoundError:
        if is_meta_generated:
            errors.append(f"trigger_cases.json 无法读取：缺少 {trigger_relative}")
    except json.JSONDecodeError as exc:
        errors.append(f"trigger_cases.json 无法读取：{exc}")

    has_output_eval = any(
        (skill_dir / relative).is_file()
        for relative in ("evals/output_assertions.json", "evals/universal_legal_cases.json")
    )
    if is_meta_generated or has_output_eval:
        eval_plan = manifest.get("eval_plan", {}) if isinstance(manifest, dict) else {}
        errors.extend(
            validate_evaluation_design(
                skill_dir,
                maturity=maturity if is_meta_generated else "scaffold",
                require_full_module_activation=bool(
                    isinstance(eval_plan, dict) and eval_plan.get("require_full_module_activation")
                ),
                require_lightweight_case=bool(
                    isinstance(eval_plan, dict) and eval_plan.get("require_lightweight_case")
                ),
            )
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="验证法律类 Skill 的结构和基础信任边界")
    parser.add_argument("skill_dir", help="Skill 根目录")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    errors, warnings = check(skill_dir)
    for warning in warnings:
        print(f"警告：{warning}")
    if errors:
        for error in errors:
            print(f"错误：{error}")
        print(f"验证失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"验证通过：{skill_dir.name}（{len(warnings)} 个警告）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
