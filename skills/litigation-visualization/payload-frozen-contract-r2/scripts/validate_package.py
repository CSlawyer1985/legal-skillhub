#!/usr/bin/env python3
"""Static validation for the local lawyer distillation candidate package."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


PACKAGE_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "SKILL.md",
    "README.md",
    "LICENSE.md",
    "PRIVACY.md",
    "CHANGELOG.md",
    "manifest.json",
    "PIPELINE_STATE.md",
    "INDEX.md",
    "VALIDATION-REPORT.json",
    "checksums.sha256",
    "references/01-授权来源与只读基线.md",
    "references/02-三类材料提取协议.md",
    "references/03-法律四重验证与候选晋升.md",
    "references/04-原子知识记录与SSOT.md",
    "references/05-Sublation扬弃矩阵.md",
    "references/06-GEO公开发布与测量协议.md",
    "references/07-多席独立验收与冻结.md",
    "references/08-方法来源与原创边界.md",
    "references/09-领域基线继承与产物门禁.md",
    "templates/distillation-plan.example.json",
    "templates/atomic-knowledge-record.schema.json",
    "templates/atomic-knowledge-record.example.json",
    "templates/Sublation比较矩阵.md",
    "templates/geo-query-set.example.json",
    "templates/test-prompts.json",
    "templates/domain-baseline-inheritance.schema.json",
    "templates/domain-baseline-inheritance.example.json",
    "templates/output-contract.schema.json",
    "templates/output-contract.example.json",
    "templates/promotion-evidence.schema.json",
    "templates/promotion-evidence.example.json",
    "scripts/validate_package.py",
    "tests/test_package.py",
    "candidates/README.md",
    "rejected/README.md",
}

REQUIRED_DIRS = {
    "references",
    "templates",
    "scripts",
    "tests",
    "candidates",
    "rejected",
}

REQUIRED_HOLDS = {
    "HOLD-AUTHORIZATION",
    "HOLD-RIGHTS",
    "HOLD-PRIVACY",
    "HOLD-READABILITY",
    "HOLD-ANSWER-KEY",
    "HOLD-PROVENANCE",
    "HOLD-EVIDENCE",
    "HOLD-LEGAL",
    "HOLD-MISUSE",
    "HOLD-GEO-FIDELITY",
    "HOLD-BASELINE-INHERITANCE",
    "HOLD-OUTPUT-CONTRACT",
    "HOLD-COURT-TEXT",
    "HOLD-RENDER",
    "HOLD-E2E",
    "HOLD-RELEASE",
}

TEXT_SUFFIXES = {".md", ".json", ".txt", ".yaml", ".yml"}
FORBIDDEN_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
FORBIDDEN_PARTS = {"__pycache__", ".git"}
SENSITIVE_PATTERNS = {
    "macOS absolute user path": re.compile(r"/Users/[^\s/]+/"),
    "Windows absolute user path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\s\\\\]+\\\\"),
    "file URI": re.compile(r"file://"),
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "OpenAI-like secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "mainland phone number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_package_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def check_structure(root: Path, errors: list[str]) -> None:
    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    for relative in sorted(REQUIRED_DIRS):
        if not (root / relative).is_dir():
            errors.append(f"missing required directory: {relative}")


def check_manifest(root: Path, errors: list[str]) -> None:
    path = root / "manifest.json"
    if not path.is_file():
        return
    manifest = load_json(path)
    if not isinstance(manifest, dict):
        errors.append("manifest.json must contain an object")
        return

    expected = {
        "name": "lawyer-legal-knowledge-distillation-geo",
        "version": "1.0.0-rc.3",
        "status": "candidate-local-only",
        "license": "proprietary-internal",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"manifest {key} must equal {value!r}")

    privacy = manifest.get("privacy", {})
    publication = manifest.get("publication", {})
    if privacy.get("case_payload_files") != 0:
        errors.append("manifest must declare zero case payload files")
    if privacy.get("answer_key_included") is not False:
        errors.append("manifest must declare answer_key_included=false")
    if privacy.get("absolute_paths_allowed") is not False:
        errors.append("manifest must forbid absolute paths")
    if publication.get("external_publish_authorized") is not False:
        errors.append("external publication must remain unauthorized")
    if publication.get("formal_skill_install_authorized") is not False:
        errors.append("formal skill installation must remain unauthorized")
    if publication.get("ranking_or_citation_guarantee") is not False:
        errors.append("ranking or citation guarantees must be false")

    deployment = manifest.get("deployment_observation", {})
    if deployment.get("physical_install_observed") is not True:
        errors.append("manifest must record the observed historical physical install")
    if deployment.get("observed_installed_version") != "1.0.0-rc.1":
        errors.append("manifest must identify the observed installed version as rc.1")
    if deployment.get("install_authorization_receipt") != "missing":
        errors.append("missing historical install receipt must not be retroactively supplied")
    if deployment.get("candidate_version_installed") is not False:
        errors.append("the rc.3 candidate must remain uninstalled")
    if deployment.get("production_promotion_authorized") is not False:
        errors.append("production promotion must remain unauthorized")

    output_contract = manifest.get("output_contract", {})
    if set(output_contract.get("artifact_classes", [])) != {
        "court_submission",
        "professional_service",
    }:
        errors.append("manifest must declare exactly the two current artifact classes")
    if output_contract.get("write_back_allowed") is not False:
        errors.append("derived outputs must not write back to SSOT")
    if output_contract.get("additional_class_requires_new_sublation") is not True:
        errors.append("new artifact classes must require a separate Sublation cycle")

    holds = set(manifest.get("required_holds", []))
    missing_holds = REQUIRED_HOLDS - holds
    if missing_holds:
        errors.append(f"manifest missing HOLD states: {sorted(missing_holds)}")


def check_skill(root: Path, errors: list[str]) -> None:
    path = root / "SKILL.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append("SKILL.md must start with YAML frontmatter")
    frontmatter = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    if "name: lawyer-legal-knowledge-distillation-geo" not in frontmatter:
        errors.append("SKILL.md frontmatter has the wrong name")
    if "description:" not in frontmatter:
        errors.append("SKILL.md frontmatter is missing description")
    if "阶段 11" not in text:
        errors.append("SKILL.md must include the final freeze stage")
    for marker in (
        "领域基线覆盖",
        "法院件纯净度",
        "DOCX 稳定性",
        "真实任务 E2E",
        "court_submission",
        "professional_service",
        "write_back=false",
    ):
        if marker not in text:
            errors.append(f"SKILL.md missing rc.3 gate marker: {marker}")
    for hold in sorted(REQUIRED_HOLDS):
        if hold not in text:
            errors.append(f"SKILL.md missing HOLD state: {hold}")


def check_json_files(root: Path, errors: list[str]) -> None:
    for path in iter_package_files(root):
        if path.suffix != ".json":
            continue
        try:
            load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(root)}: {exc}")


def check_atomic_schema(root: Path, errors: list[str]) -> None:
    path = root / "templates/atomic-knowledge-record.schema.json"
    if not path.is_file():
        return
    schema = load_json(path)
    required = set(schema.get("required", [])) if isinstance(schema, dict) else set()
    expected = {
        "id",
        "source_locator",
        "source_hash",
        "claim",
        "conditions",
        "legal_authority",
        "privacy_class",
        "rights_status",
        "failure_modes",
        "status",
        "public_projection",
    }
    missing = expected - required
    if missing:
        errors.append(f"atomic schema missing required fields: {sorted(missing)}")
    if not schema.get("allOf"):
        errors.append("atomic schema must enforce the public projection gate")


def check_plan_template(root: Path, errors: list[str]) -> None:
    path = root / "templates/distillation-plan.example.json"
    if not path.is_file():
        return
    plan = load_json(path)
    zones = plan.get("zones", {})
    if len(set(zones.values())) != 4:
        errors.append("distillation plan zones must be distinct")
    release = plan.get("release", {})
    if release.get("formal_skill_install_authorized") is not False:
        errors.append("plan template must not authorize formal installation")
    if release.get("physical_install_observed") is not False:
        errors.append("example plan must not claim a physical install")
    if release.get("install_authorization_receipt") != "not-applicable":
        errors.append("example plan must separate install observation from authorization receipt")
    if release.get("production_promotion_authorized") is not False:
        errors.append("plan template must not authorize production promotion")
    if release.get("external_publish_authorized") is not False:
        errors.append("plan template must not authorize external publication")


def check_test_prompts(root: Path, errors: list[str]) -> None:
    path = root / "templates/test-prompts.json"
    if not path.is_file():
        return
    payload = load_json(path)
    cases = payload.get("cases", [])
    counts = {
        kind: sum(case.get("type") == kind for case in cases)
        for kind in ("should_trigger", "should_not_trigger", "edge_case")
    }
    minimums = {"should_trigger": 3, "should_not_trigger": 3, "edge_case": 2}
    for kind, minimum in minimums.items():
        if counts[kind] < minimum:
            errors.append(f"test prompts need at least {minimum} {kind} cases")
    combined = json.dumps(cases, ensure_ascii=False)
    for marker in (
        "HOLD-PRIVACY",
        "HOLD-LEGAL",
        "HOLD-ANSWER-KEY",
        "HOLD-GEO-FIDELITY",
        "HOLD-BASELINE-INHERITANCE",
        "HOLD-OUTPUT-CONTRACT",
        "HOLD-COURT-TEXT",
        "HOLD-RENDER",
        "HOLD-E2E",
    ):
        if marker not in combined:
            errors.append(f"test prompts missing legal safety bait: {marker}")


def check_geo_template(root: Path, errors: list[str]) -> None:
    path = root / "templates/geo-query-set.example.json"
    if not path.is_file():
        return
    payload = load_json(path)
    measurement = payload.get("measurement", {})
    if measurement.get("ranking_guarantee") is not False:
        errors.append("GEO template must not guarantee rankings")
    required_metrics = {
        "citation_selection",
        "citation_absorption",
        "citation_fidelity",
        "hallucination_rate",
        "boundary_compliance",
    }
    missing = required_metrics - set(measurement.get("metrics", []))
    if missing:
        errors.append(f"GEO template missing metrics: {sorted(missing)}")
    if set(measurement.get("branches", [])) != {"control", "treatment"}:
        errors.append("GEO template must define control and treatment branches")


def check_sublation_matrix(root: Path, errors: list[str]) -> None:
    path = root / "templates/Sublation比较矩阵.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for donor in ("原创基底", "仓颉", "GEORank"):
        if donor not in text:
            errors.append(f"Sublation matrix missing donor: {donor}")
    for decision in ("保留", "强化", "替换", "组合", "舍弃"):
        if f"| {decision} |" not in text:
            errors.append(f"Sublation matrix missing decision: {decision}")
    if "回归测试" not in text:
        errors.append("Sublation matrix must include regression evidence")
    for marker in (
        "已验证领域基线继承",
        "法院件与治理 sidecar 分层",
        "固定字体双遍逐页渲染",
        "完整案与 HOLD 案双 E2E",
    ):
        if marker not in text:
            errors.append(f"Sublation matrix missing feedback-cycle gate: {marker}")


def check_domain_baseline_template(root: Path, errors: list[str]) -> None:
    schema_path = root / "templates/domain-baseline-inheritance.schema.json"
    example_path = root / "templates/domain-baseline-inheritance.example.json"
    if not schema_path.is_file() or not example_path.is_file():
        return

    schema = load_json(schema_path)
    expected_schema_fields = {
        "schema_version",
        "target_skill",
        "donor_inventories",
        "decisions",
        "coverage",
    }
    if set(schema.get("required", [])) != expected_schema_fields:
        errors.append("domain baseline schema required fields are incomplete")

    payload = load_json(example_path)
    required_pairs: list[tuple[str, str]] = []
    for donor in payload.get("donor_inventories", []):
        donor_id = donor.get("donor_id")
        freeze_hash = donor.get("source_freeze_sha256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", freeze_hash):
            errors.append(f"domain donor {donor_id!r} has an invalid freeze hash")
        gate_ids = donor.get("required_gate_ids", [])
        if len(gate_ids) != len(set(gate_ids)):
            errors.append(f"domain donor {donor_id!r} has duplicate required gates")
        required_pairs.extend((donor_id, gate_id) for gate_id in gate_ids)

    decision_pairs: list[tuple[str, str]] = []
    required_decision_fields = {
        "donor_id",
        "gate_id",
        "decision",
        "donor_evidence",
        "legal_impact",
        "decision_reason",
        "regression_test",
    }
    for decision in payload.get("decisions", []):
        missing = required_decision_fields - set(decision)
        if missing:
            errors.append(f"domain decision missing fields: {sorted(missing)}")
        decision_pairs.append((decision.get("donor_id"), decision.get("gate_id")))

    if len(decision_pairs) != len(set(decision_pairs)):
        errors.append("domain baseline decisions contain duplicate donor/gate pairs")
    if set(required_pairs) != set(decision_pairs):
        errors.append("domain baseline inventory and decisions are not an exact set match")

    coverage = payload.get("coverage", {})
    if coverage.get("required_gate_count") != len(required_pairs):
        errors.append("domain baseline coverage required_gate_count is incorrect")
    if coverage.get("decision_count") != len(decision_pairs):
        errors.append("domain baseline coverage decision_count is incorrect")
    if coverage.get("missing_gate_ids") != [] or coverage.get("duplicate_gate_ids") != []:
        errors.append("domain baseline example must have zero missing and duplicate gates")
    if coverage.get("status") != "PASS":
        errors.append("domain baseline example must report PASS")


def check_output_contract_template(root: Path, errors: list[str]) -> None:
    schema_path = root / "templates/output-contract.schema.json"
    example_path = root / "templates/output-contract.example.json"
    if not schema_path.is_file() or not example_path.is_file():
        return

    schema = load_json(schema_path)
    if set(schema.get("required", [])) != {"schema_version", "contracts"}:
        errors.append("output contract schema must require schema_version and contracts")

    payload = load_json(example_path)
    contracts = payload.get("contracts", [])
    classes = [contract.get("artifact_class") for contract in contracts]
    if set(classes) != {"court_submission", "professional_service"} or len(classes) != 2:
        errors.append("output contract example must contain exactly the two current classes")
    for contract in contracts:
        if contract.get("write_back") is not False:
            errors.append(f"output contract {contract.get('artifact_class')!r} must be read-only")
        redaction = contract.get("redaction_policy", {})
        if any(redaction.get(key) is not False for key in (
            "private_case_payload",
            "absolute_paths",
            "governance_metadata_visible",
        )):
            errors.append(f"output contract {contract.get('artifact_class')!r} weakens redaction")
        if contract.get("language") != "zh-CN":
            errors.append(f"output contract {contract.get('artifact_class')!r} must be Chinese-first")

    court = next((item for item in contracts if item.get("artifact_class") == "court_submission"), {})
    render = court.get("render_gate", {})
    if not (
        render.get("applicable") is True
        and render.get("fixed_font_double_render") is True
        and render.get("page_pixel_hash_match") is True
        and render.get("sparse_page_count") == 0
        and render.get("ooxml_editable") is True
        and render.get("external_relationship_count") == 0
    ):
        errors.append("court output contract must enforce the full DOCX render gate")


def check_promotion_evidence_template(root: Path, errors: list[str]) -> None:
    schema_path = root / "templates/promotion-evidence.schema.json"
    example_path = root / "templates/promotion-evidence.example.json"
    if not schema_path.is_file() or not example_path.is_file():
        return

    schema = load_json(schema_path)
    expected = {
        "schema_version",
        "candidate_skill",
        "domain_baseline",
        "court_visible_text",
        "render",
        "e2e_cases",
        "seats",
        "overall",
    }
    if set(schema.get("required", [])) != expected:
        errors.append("promotion evidence schema required fields are incomplete")

    payload = load_json(example_path)
    if payload.get("overall") != "PASS":
        errors.append("promotion evidence example must report PASS")
    if payload.get("domain_baseline", {}).get("missing_gate_ids") != []:
        errors.append("promotion evidence must have no missing baseline gates")
    if payload.get("domain_baseline", {}).get("duplicate_gate_ids") != []:
        errors.append("promotion evidence must have no duplicate baseline gates")
    court = payload.get("court_visible_text", {})
    for key in (
        "governance_jargon_hits",
        "placeholder_hits",
        "non_chinese_anomaly_hits",
        "hidden_text_hits",
    ):
        if court.get(key) != 0:
            errors.append(f"promotion evidence court gate {key} must be zero")
    render = payload.get("render", {})
    if render.get("fixed_font_double_render") is not True:
        errors.append("promotion evidence must require fixed-font double rendering")
    if render.get("pixel_mismatch_pages") != [] or render.get("sparse_pages") != []:
        errors.append("promotion evidence render mismatches and sparse pages must be empty")

    roles = {case.get("role") for case in payload.get("e2e_cases", [])}
    if roles != {"complete-nine-document", "hold-case"}:
        errors.append("promotion evidence must contain complete and HOLD E2E roles")
    complete = next((case for case in payload.get("e2e_cases", []) if case.get("role") == "complete-nine-document"), {})
    hold = next((case for case in payload.get("e2e_cases", []) if case.get("role") == "hold-case"), {})
    if complete.get("document_count") != 9 or complete.get("status") != "PASS":
        errors.append("complete E2E role must pass with exactly nine documents")
    if hold.get("hold_triggered") is not True or hold.get("status") != "PASS":
        errors.append("HOLD E2E role must pass by triggering HOLD")
    seats = payload.get("seats", {})
    if seats.get("builder") == seats.get("acceptance"):
        errors.append("builder and acceptance seats must be independent")


def check_scope_lock(root: Path, errors: list[str]) -> None:
    forbidden = ("derived" + "_view", "case-knowledge" + "-graph")
    for path in iter_package_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in forbidden:
            if marker in text:
                errors.append(f"rc.3 scope includes deferred marker {marker!r} in {path.relative_to(root)}")


def check_hygiene(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            errors.append(f"symbolic link is forbidden: {relative}")
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden metadata file: {relative}")
        if any(part in FORBIDDEN_PARTS for part in relative.parts):
            errors.append(f"forbidden cache or repository path: {relative}")
        if path.is_file() and path.suffix == ".pyc":
            errors.append(f"compiled Python file is forbidden: {relative}")

        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"sensitive pattern ({label}) in {relative}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_checksums(root: Path, errors: list[str]) -> None:
    checksum_path = root / "checksums.sha256"
    if not checksum_path.is_file():
        return

    listed: set[str] = set()
    for number, raw_line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        if "  " not in raw_line:
            errors.append(f"invalid checksum line {number}")
            continue
        expected, relative = raw_line.split("  ", 1)
        relative = relative.removeprefix("./")
        path = root / relative
        if relative == "checksums.sha256":
            errors.append("checksums.sha256 must not hash itself")
            continue
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            errors.append(f"invalid SHA-256 on checksum line {number}")
            continue
        if not path.is_file():
            errors.append(f"checksum references missing file: {relative}")
            continue
        listed.add(relative)
        actual = sha256(path)
        if actual != expected:
            errors.append(f"checksum mismatch: {relative}")

    actual_files = {
        str(path.relative_to(root))
        for path in iter_package_files(root)
        if path.name != "checksums.sha256"
        and not any(part in FORBIDDEN_PARTS for part in path.relative_to(root).parts)
        and path.suffix != ".pyc"
    }
    missing = actual_files - listed
    extra = listed - actual_files
    if missing:
        errors.append(f"checksum file missing entries: {sorted(missing)}")
    if extra:
        errors.append(f"checksum file has unexpected entries: {sorted(extra)}")


def validate_package(root: Path = PACKAGE_ROOT) -> list[str]:
    errors: list[str] = []
    checks = (
        check_structure,
        check_manifest,
        check_skill,
        check_json_files,
        check_atomic_schema,
        check_plan_template,
        check_test_prompts,
        check_geo_template,
        check_sublation_matrix,
        check_domain_baseline_template,
        check_output_contract_template,
        check_promotion_evidence_template,
        check_scope_lock,
        check_hygiene,
        check_checksums,
    )
    for check in checks:
        try:
            check(root, errors)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            errors.append(f"{check.__name__} failed: {exc}")
    return errors


def main() -> int:
    errors = validate_package(PACKAGE_ROOT)
    result = {
        "package": "lawyer-legal-knowledge-distillation-geo",
        "version": "1.0.0-rc.3",
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
        "external_publish_authorized": False,
        "formal_skill_install_authorized": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
