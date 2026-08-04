#!/usr/bin/env python3
"""Score blind-review submissions structurally and optionally combine lawyer scores."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "tests" / "evaluation" / "scenarios.json"
HUMAN_DIMENSIONS = {
    "legal_correctness",
    "issue_recall",
    "false_positive_control",
    "drafting_quality",
    "client_side_consistency",
    "source_discipline",
}


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict) -> dict[str, object]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 12:
        errors.append("manifest must contain exactly 12 scenarios")
        scenarios = []
    identifiers: set[str] = set()
    for scenario in scenarios:
        scenario_id = str(scenario.get("id", ""))
        if not scenario_id:
            errors.append("scenario missing id")
            continue
        if scenario_id in identifiers:
            errors.append(f"duplicate scenario id: {scenario_id}")
        identifiers.add(scenario_id)
        for field in ("family", "language", "user_prompt", "expected_artifacts", "must_detect", "authority_expectations", "must_not_claim"):
            if field not in scenario:
                errors.append(f"{scenario_id}: missing {field}")
        if not any(key in scenario for key in ("fixture_dir", "files", "generator")):
            errors.append(f"{scenario_id}: no fixture source")
    dimensions = set(manifest.get("human_dimensions", []))
    if dimensions != HUMAN_DIMENSIONS:
        errors.append("human_dimensions do not match the required six-dimension rubric")
    return {"ok": not errors, "scenario_count": len(identifiers), "errors": errors}


def scenario_by_id(manifest: dict, scenario_id: str) -> dict:
    for scenario in manifest.get("scenarios", []):
        if scenario.get("id") == scenario_id:
            return scenario
    raise KeyError(scenario_id)


def docx_comment_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            if "word/comments.xml" not in archive.namelist():
                return ""
            root = etree.fromstring(archive.read("word/comments.xml"))
    except (OSError, zipfile.BadZipFile, etree.XMLSyntaxError):
        return ""
    return "\n".join("".join(comment.xpath(".//w:t/text()", namespaces=NS)) for comment in root.xpath("//w:comment", namespaces=NS))


def safe_submission_file(path: Path, submission: Path) -> bool:
    if path.is_symlink():
        return False
    try:
        path.resolve().relative_to(submission.resolve())
    except ValueError:
        return False
    return path.is_file()


def submission_corpus(submission: Path) -> str:
    parts = []
    for path in sorted(submission.rglob("*")):
        if not safe_submission_file(path, submission) or path.name.startswith("."):
            continue
        if path.suffix.lower() in {".md", ".txt", ".csv", ".json"} and path.name != "human-scorecard.json":
            try:
                parts.append(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError):
                continue
        elif path.suffix.lower() == ".docx":
            comments = docx_comment_text(path)
            if comments:
                parts.append(comments)
    return "\n".join(parts).casefold()


def artifact_checks(scenario: dict, submission: Path) -> list[dict[str, object]]:
    checks = []
    for artifact in scenario.get("expected_artifacts", []):
        paths = [submission / relative for relative in artifact.get("paths", [])]
        existing = [path for path in paths if safe_submission_file(path, submission) and path.stat().st_size > 0]
        checks.append(
            {
                "id": artifact.get("id"),
                "required": bool(artifact.get("required", True)),
                "paths": [str(path.relative_to(submission)) for path in paths],
                "found": str(existing[0].relative_to(submission)) if existing else None,
                "ok": bool(existing) or not artifact.get("required", True),
            }
        )
    return checks


def keyword_checks(items: list[dict], corpus: str) -> list[dict[str, object]]:
    checks = []
    for item in items:
        keywords = [str(keyword) for keyword in item.get("keywords_any", [])]
        hits = [keyword for keyword in keywords if keyword.casefold() in corpus]
        checks.append({"id": item.get("id"), "keywords_any": keywords, "hits": hits, "ok": bool(hits)})
    return checks


def validator_checks(submission: Path) -> list[dict[str, object]]:
    checks = []
    scripts = SKILL_ROOT / "scripts"
    for path in sorted(submission.glob("*.csv")):
        if not safe_submission_file(path, submission):
            checks.append({"file": path.name, "validator": "submission-path-safety", "ok": False})
            continue
        lowered = path.name.lower()
        script = None
        if "issue-log" in lowered:
            script = scripts / "validate_issue_log.py"
        elif "major-issue" in lowered:
            script = scripts / "validate_major_issue_list.py"
        if script:
            process = subprocess.run([sys.executable, str(script), str(path)], text=True, capture_output=True, check=False)
            checks.append(
                {
                    "file": path.name,
                    "validator": script.name,
                    "returncode": process.returncode,
                    "ok": process.returncode == 0,
                    "stderr": process.stderr.strip()[:1000],
                }
            )
        elif "comment-plan" in lowered:
            try:
                with path.open(newline="", encoding="utf-8-sig") as handle:
                    rows = list(csv.DictReader(handle))
                checks.append({"file": path.name, "validator": "nonempty-comment-plan", "ok": bool(rows), "row_count": len(rows)})
            except (OSError, csv.Error) as exc:
                checks.append({"file": path.name, "validator": "nonempty-comment-plan", "ok": False, "stderr": str(exc)})
    return checks


def comment_structure_checks(submission: Path) -> list[dict[str, object]]:
    checks = []
    for path in sorted(submission.glob("*.docx")):
        if not safe_submission_file(path, submission):
            checks.append({"file": path.name, "comment_count": 0, "ok": False, "error": "unsafe submission path"})
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                if "word/comments.xml" not in names:
                    continue
                comments = etree.fromstring(archive.read("word/comments.xml"))
                document = etree.fromstring(archive.read("word/document.xml"))
                comment_ids = {comment.get(f"{{{W_NS}}}id") for comment in comments.xpath("//w:comment", namespaces=NS)}
                start_ids = {item.get(f"{{{W_NS}}}id") for item in document.xpath("//w:commentRangeStart", namespaces=NS)}
                end_ids = {item.get(f"{{{W_NS}}}id") for item in document.xpath("//w:commentRangeEnd", namespaces=NS)}
                reference_ids = {item.get(f"{{{W_NS}}}id") for item in document.xpath("//w:commentReference", namespaces=NS)}
                ok = bool(comment_ids) and comment_ids <= start_ids & end_ids & reference_ids
                checks.append({"file": path.name, "comment_count": len(comment_ids), "ok": ok})
        except (OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
            checks.append({"file": path.name, "comment_count": 0, "ok": False, "error": str(exc)})
    return checks


def load_human_score(path: Path | None, scenario_id: str) -> dict[str, object] | None:
    if not path or not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("scenario_id") != scenario_id:
        raise ValueError("human scorecard scenario_id does not match the scored scenario")
    for field in ("reviewer", "reviewer_role", "reviewed_at"):
        if not str(data.get(field, "")).strip():
            raise ValueError(f"human scorecard requires {field}")
    try:
        dt.datetime.fromisoformat(str(data["reviewed_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("human scorecard reviewed_at must be an ISO date/time") from exc
    if not isinstance(data.get("critical_failure"), bool):
        raise ValueError("human scorecard critical_failure must be boolean")
    if data["critical_failure"] and not str(data.get("critical_failure_reason", "")).strip():
        raise ValueError("critical_failure_reason is required when critical_failure is true")
    scores = data.get("scores", {})
    if set(scores) != HUMAN_DIMENSIONS:
        raise ValueError("human scorecard must contain all six dimensions")
    values = []
    for dimension, value in scores.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 5:
            raise ValueError(f"human score {dimension} must be between 0 and 5")
        values.append(float(value))
    data["score_100"] = round(sum(values) / len(values) * 20, 2)
    return data


def score_submission(scenario: dict, submission: Path, human_score_path: Path | None = None, threshold: float = 70.0) -> dict[str, object]:
    corpus = submission_corpus(submission)
    artifacts = artifact_checks(scenario, submission)
    detection = keyword_checks(scenario.get("must_detect", []), corpus)
    authorities = keyword_checks(scenario.get("authority_expectations", []), corpus)
    prohibited = [claim for claim in scenario.get("must_not_claim", []) if str(claim).casefold() in corpus]
    validators = validator_checks(submission)
    comment_checks = comment_structure_checks(submission)

    artifact_score = 100.0 * sum(check["ok"] for check in artifacts) / max(len(artifacts), 1)
    detection_score = 100.0 * sum(check["ok"] for check in detection) / max(len(detection), 1)
    authority_score = 100.0 * sum(check["ok"] for check in authorities) / len(authorities) if authorities else 100.0
    all_validators = [*validators, *comment_checks]
    validator_score = 100.0 * sum(check["ok"] for check in all_validators) / len(all_validators) if all_validators else 100.0
    prohibited_score = 100.0 if not prohibited else 0.0
    automatic_score = round(
        artifact_score * 0.20
        + detection_score * 0.40
        + authority_score * 0.15
        + validator_score * 0.15
        + prohibited_score * 0.10,
        2,
    )
    automatic_pass = automatic_score >= threshold and not prohibited and all(check["ok"] for check in artifacts)
    human = load_human_score(human_score_path, str(scenario.get("id")))
    overall_score = None
    legal_quality_status = "not_assessed"
    if human:
        overall_score = round(automatic_score * 0.60 + float(human["score_100"]) * 0.40, 2)
        critical = bool(human.get("critical_failure"))
        legal_quality_status = "pass" if automatic_pass and overall_score >= threshold and not critical else "fail"
    return {
        "scenario_id": scenario.get("id"),
        "submission": str(submission),
        "artifact_checks": artifacts,
        "must_detect_checks": detection,
        "authority_checks": authorities,
        "prohibited_claim_hits": prohibited,
        "validator_checks": validators,
        "comment_structure_checks": comment_checks,
        "component_scores": {
            "artifacts": round(artifact_score, 2),
            "issue_recall": round(detection_score, 2),
            "authority_recall": round(authority_score, 2),
            "validators": round(validator_score, 2),
            "false_positive_control": round(prohibited_score, 2),
        },
        "automatic_score": automatic_score,
        "automatic_threshold": threshold,
        "automatic_status": "pass" if automatic_pass else "fail",
        "human_score": human,
        "overall_score": overall_score,
        "legal_quality_status": legal_quality_status,
        "completion_rule": "Automatic structure/keyword scoring is not proof of legal quality; legal_quality_status remains not_assessed without a completed lawyer scorecard.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario_id")
    parser.add_argument("submission", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--human-score", type=Path)
    parser.add_argument("--threshold", type=float, default=70.0)
    parser.add_argument("--require-human", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 0 <= args.threshold <= 100:
        print("--threshold must be between 0 and 100", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest(args.manifest)
        manifest_report = validate_manifest(manifest)
        if not manifest_report["ok"]:
            raise ValueError(f"invalid evaluation manifest: {manifest_report['errors']}")
        scenario = scenario_by_id(manifest, args.scenario_id)
        report = score_submission(scenario, args.submission, args.human_score, args.threshold)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Could not score blind evaluation: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    if args.require_human and report["human_score"] is None:
        return 1
    if args.strict and report["automatic_status"] != "pass":
        return 1
    if args.require_human and report["legal_quality_status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
