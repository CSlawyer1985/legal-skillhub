#!/usr/bin/env python3
"""Aggregate review evidence and block unsupported completion claims."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import review_checkpoint


SCHEMA_VERSION = 1
TERMINAL_STAGE_STATUSES = {"completed", "completed_with_limitations", "not_applicable"}
JUDGMENT_GATE_NAMES = {
    "matter_and_authority",
    "substantive_coverage",
    "high_risk_spot_check",
    "delivery_and_confidentiality",
}
JUDGMENT_GATE_STATUSES = {"passed", "passed_with_limitations", "blocked"}
ABSOLUTE_USER_PATH = re.compile(r"/(?:Users|Volumes)/[^\s\"'<>]+")
INTERNAL_SOURCE_NAME = re.compile(r"(?!)")
PRIVATE_TREE_NAME = re.compile(r"(?!)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(base: Path, value: object) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def machine_check(check_id: str, ok: bool, detail: str, evidence: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {"id": check_id, "kind": "machine", "ok": ok, "detail": detail}
    if evidence:
        result["evidence"] = evidence
    return result


def run_validator(script: Path, artifact: Path) -> tuple[bool, str]:
    process = subprocess.run(
        [sys.executable, str(script), str(artifact)],
        text=True,
        capture_output=True,
        check=False,
    )
    detail = (process.stdout.strip() or process.stderr.strip() or f"return code {process.returncode}")[:2000]
    return process.returncode == 0, detail


def validate_checkpoint(
    config: dict[str, object],
    base: Path,
    checks: list[dict[str, object]],
) -> tuple[dict[str, object] | None, list[Path]]:
    checkpoint_value = config.get("checkpoint")
    source_values = config.get("source_files")
    if not checkpoint_value:
        checks.append(machine_check("checkpoint", False, "checkpoint is required"))
        return None, []
    if not isinstance(source_values, list) or not source_values:
        checks.append(machine_check("source_files", False, "at least one source file is required"))
        return None, []

    checkpoint_path = resolve_path(base, checkpoint_value)
    sources = [resolve_path(base, value) for value in source_values]
    missing_sources = [path for path in sources if not path.is_file()]
    if missing_sources:
        checks.append(
            machine_check(
                "source_files",
                False,
                "missing source file(s): " + ", ".join(path.name for path in missing_sources),
            )
        )
        return None, sources
    try:
        state = review_checkpoint.load_state(checkpoint_path)
    except (OSError, ValueError) as exc:
        checks.append(machine_check("checkpoint", False, str(exc), str(checkpoint_path)))
        return None, sources

    matter_id = str(config.get("matter_id", "")).strip()
    identity_ok = bool(matter_id) and state.get("matter_id") == matter_id
    checks.append(
        machine_check(
            "matter_identity",
            identity_ok,
            "checkpoint matter matches config" if identity_ok else "matter_id is missing or does not match checkpoint",
            str(checkpoint_path),
        )
    )
    current_records = review_checkpoint.source_records(sources)
    fingerprint_ok = state.get("source_files") == current_records
    checks.append(
        machine_check(
            "source_fingerprints",
            fingerprint_ok,
            "source fingerprints unchanged" if fingerprint_ok else "source files changed after checkpoint creation",
            str(checkpoint_path),
        )
    )
    stages = state.get("stages") if isinstance(state.get("stages"), dict) else {}
    incomplete = {
        stage: (stages.get(stage) or {}).get("status", "missing")
        for stage in review_checkpoint.STAGES
        if not isinstance(stages.get(stage), dict)
        or (stages.get(stage) or {}).get("status") not in TERMINAL_STAGE_STATUSES
    }
    checks.append(
        machine_check(
            "checkpoint_stages",
            not incomplete,
            "all review stages reached a terminal status" if not incomplete else f"non-terminal stages: {incomplete}",
            str(checkpoint_path),
        )
    )
    return state, sources


def validate_artifacts(
    config: dict[str, object],
    base: Path,
    sources: list[Path],
    checks: list[dict[str, object]],
) -> list[Path]:
    artifacts = config.get("artifacts")
    if not isinstance(artifacts, dict):
        checks.append(machine_check("artifacts", False, "artifacts object is required"))
        return []
    scripts = Path(__file__).resolve().parent
    requirements = config.get("requirements") if isinstance(config.get("requirements"), dict) else {}
    deliverables: list[Path] = []

    issue_value = artifacts.get("issue_log")
    if not issue_value:
        checks.append(machine_check("issue_log", False, "issue_log is required"))
    else:
        issue_log = resolve_path(base, issue_value)
        if not issue_log.is_file():
            checks.append(machine_check("issue_log", False, "issue log is missing", str(issue_log)))
        else:
            ok, detail = run_validator(scripts / "validate_issue_log.py", issue_log)
            checks.append(machine_check("issue_log", ok, detail, str(issue_log)))
            deliverables.append(issue_log)

    major_required = bool(requirements.get("major_issue_list", False))
    major_value = artifacts.get("major_issue_list")
    if major_required and not major_value:
        checks.append(machine_check("major_issue_list", False, "major issue list is required"))
    elif major_value:
        major = resolve_path(base, major_value)
        if not major.is_file():
            checks.append(machine_check("major_issue_list", False, "major issue list is missing", str(major)))
        else:
            ok, detail = run_validator(scripts / "validate_major_issue_list.py", major)
            checks.append(machine_check("major_issue_list", ok, detail, str(major)))
            deliverables.append(major)

    matrix_required = bool(requirements.get("package_matrix", False))
    matrix_value = artifacts.get("package_matrix")
    if matrix_required and not matrix_value:
        checks.append(machine_check("package_matrix", False, "package matrix is required"))
    elif matrix_value:
        matrix_path = resolve_path(base, matrix_value)
        try:
            matrix = load_json(matrix_path)
            if not isinstance(matrix, dict):
                raise ValueError("package matrix must be a JSON object")
            extraction_errors = matrix.get("extraction_errors", [])
            document_count = int(matrix.get("document_count", 0))
            ok = document_count > 0 and not extraction_errors
            detail = (
                f"{document_count} document(s); no extraction errors"
                if ok
                else f"document_count={document_count}; extraction_errors={extraction_errors}"
            )
            checks.append(machine_check("package_matrix", ok, detail, str(matrix_path)))
            deliverables.append(matrix_path)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            checks.append(machine_check("package_matrix", False, f"invalid package matrix: {exc}", str(matrix_path)))

    comment_required = bool(requirements.get("native_comments", False))
    comment_value = artifacts.get("comment_apply_report")
    if comment_required and not comment_value:
        checks.append(machine_check("native_comments", False, "comment apply report is required"))
    elif comment_value:
        report_path = resolve_path(base, comment_value)
        try:
            report = load_json(report_path)
            if not isinstance(report, dict):
                raise ValueError("comment apply report must be a JSON object")
            ok = all(
                (
                    report.get("ok") is True,
                    report.get("visible_text_unchanged") is True,
                    report.get("source_file_unchanged") is True,
                    int(report.get("added_comment_count", 0)) > 0,
                    int(report.get("failed_rows", 0)) == 0,
                )
            )
            checks.append(
                machine_check(
                    "native_comments",
                    ok,
                    "native comments passed source and visible-text integrity checks"
                    if ok
                    else "native comment integrity report is incomplete or failed",
                    str(report_path),
                )
            )
            deliverables.append(report_path)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            checks.append(machine_check("native_comments", False, f"invalid comment report: {exc}", str(report_path)))

    extra = artifacts.get("deliverables", [])
    if not isinstance(extra, list):
        checks.append(machine_check("deliverables", False, "artifacts.deliverables must be a list"))
    else:
        extra_paths = [resolve_path(base, value) for value in extra]
        missing = [path for path in extra_paths if not path.is_file() or path.stat().st_size == 0]
        checks.append(
            machine_check(
                "deliverables",
                not missing and bool(extra_paths),
                "all declared deliverables exist and are non-empty"
                if not missing and extra_paths
                else "missing, empty, or undeclared final deliverables: " + ", ".join(path.name for path in missing),
            )
        )
        deliverables.extend(path for path in extra_paths if path.is_file())

    source_hashes = {sha256_file(path) for path in sources if path.is_file()}
    output_overwrites_source = any(path.is_file() and sha256_file(path) in source_hashes for path in deliverables)
    checks.append(
        machine_check(
            "source_output_separation",
            not output_overwrites_source,
            "deliverables are distinct from source files"
            if not output_overwrites_source
            else "a declared deliverable is identical to a source file",
        )
    )
    return list(dict.fromkeys(deliverables))


def scan_deliverables(
    deliverables: list[Path],
    forbidden_terms: list[str],
    checks: list[dict[str, object]],
) -> None:
    findings: list[str] = []
    for path in deliverables:
        if path.suffix.lower() not in {".md", ".txt", ".csv", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        if ABSOLUTE_USER_PATH.search(text):
            findings.append(f"{path.name}: absolute local path")
        if INTERNAL_SOURCE_NAME.search(text):
            findings.append(f"{path.name}: named internal benchmark source")
        if PRIVATE_TREE_NAME.search(text):
            findings.append(f"{path.name}: private source-tree reference")
        for term in forbidden_terms:
            if term and term in text:
                findings.append(f"{path.name}: forbidden term {term!r}")
    checks.append(
        machine_check(
            "confidentiality_scan",
            not findings,
            "no configured confidentiality leak pattern found" if not findings else "; ".join(findings),
        )
    )


def validate_judgment_gates(config: dict[str, object]) -> tuple[list[dict[str, object]], bool]:
    raw = config.get("judgment_gates")
    results: list[dict[str, object]] = []
    has_limitations = False
    if not isinstance(raw, dict):
        return [
            {
                "id": name,
                "kind": "judgment",
                "status": "blocked",
                "ok": False,
                "detail": "required judgment gate is missing",
            }
            for name in sorted(JUDGMENT_GATE_NAMES)
        ], False
    for name in sorted(JUDGMENT_GATE_NAMES):
        gate = raw.get(name)
        if not isinstance(gate, dict):
            results.append(
                {"id": name, "kind": "judgment", "status": "blocked", "ok": False, "detail": "gate is missing"}
            )
            continue
        status = str(gate.get("status", ""))
        reviewer = str(gate.get("reviewer", "")).strip()
        evidence = str(gate.get("evidence", "")).strip()
        valid = status in JUDGMENT_GATE_STATUSES and bool(reviewer) and bool(evidence) and status != "blocked"
        if status == "passed_with_limitations":
            has_limitations = True
        results.append(
            {
                "id": name,
                "kind": "judgment",
                "status": status or "blocked",
                "ok": valid,
                "reviewer": reviewer,
                "detail": evidence or "reviewer and evidence are required",
            }
        )
    return results, has_limitations


def evaluate(config: dict[str, object], config_path: Path) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    if config.get("schema_version") != SCHEMA_VERSION:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "blocked",
            "completion_claim_allowed": False,
            "errors": ["config schema_version must be 1"],
            "checks": [],
        }
    base = config_path.resolve().parent
    _, sources = validate_checkpoint(config, base, checks)
    deliverables = validate_artifacts(config, base, sources, checks)
    forbidden_terms = config.get("forbidden_terms", [])
    if not isinstance(forbidden_terms, list) or not all(isinstance(term, str) for term in forbidden_terms):
        checks.append(machine_check("forbidden_terms", False, "forbidden_terms must be a list of strings"))
        forbidden_terms = []
    scan_deliverables(deliverables, forbidden_terms, checks)
    judgment_checks, judgment_limitations = validate_judgment_gates(config)
    checks.extend(judgment_checks)

    limitations = config.get("limitations", [])
    limitation_errors: list[str] = []
    disclosed_limitations = False
    if not isinstance(limitations, list):
        limitation_errors.append("limitations must be a list")
    else:
        for index, limitation in enumerate(limitations, start=1):
            if not isinstance(limitation, dict):
                limitation_errors.append(f"limitation {index} must be an object")
                continue
            if not str(limitation.get("code", "")).strip() or not str(limitation.get("description", "")).strip():
                limitation_errors.append(f"limitation {index} requires code and description")
            if limitation.get("disclosed") is not True:
                limitation_errors.append(f"limitation {index} is not marked disclosed")
            disclosed_limitations = True
    checks.append(
        machine_check(
            "limitations",
            not limitation_errors,
            "limitations are disclosed and structured" if disclosed_limitations and not limitation_errors else (
                "no limitations declared" if not limitation_errors else "; ".join(limitation_errors)
            ),
        )
    )

    failed = [check for check in checks if not check.get("ok")]
    checkpoint_limited = False
    checkpoint_value = config.get("checkpoint")
    if checkpoint_value:
        try:
            state = review_checkpoint.load_state(resolve_path(base, checkpoint_value))
            checkpoint_limited = any(
                isinstance(record, dict) and record.get("status") == "completed_with_limitations"
                for record in (state.get("stages") or {}).values()
            )
        except (OSError, ValueError):
            pass
    has_limitations = judgment_limitations or disclosed_limitations or checkpoint_limited
    status = "blocked" if failed else ("passed_with_limitations" if has_limitations else "passed")
    return {
        "schema_version": SCHEMA_VERSION,
        "matter_id": config.get("matter_id"),
        "status": status,
        "completion_claim_allowed": status == "passed",
        "limited_completion_claim_allowed": status == "passed_with_limitations",
        "summary": {
            "check_count": len(checks),
            "failed_count": len(failed),
            "limitation_count": len(limitations) if isinstance(limitations, list) else 0,
        },
        "checks": checks,
        "errors": [str(check.get("detail")) for check in failed],
        "completion_rule": (
            "Only status=passed permits an unqualified completion claim. "
            "status=passed_with_limitations must be delivered as completed with prominently disclosed limitations. "
            "status=blocked prohibits any completion claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config = load_json(args.config)
        if not isinstance(config, dict):
            raise ValueError("config must be a JSON object")
        report = evaluate(config, args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not run completion gate: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if report["status"] == "passed":
        return 0
    if report["status"] == "passed_with_limitations":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
