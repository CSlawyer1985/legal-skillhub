#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import zipfile
from pathlib import Path

from common import (
    ALLOWED_EVIDENCE_LABELS,
    DIRECTORIES,
    PHASE_INDEX,
    SKILL_VERSION,
    TABLE_FIELDS,
    list_text_files,
    load_profile,
    load_project,
    load_state,
    read_csv,
    read_json,
    safe_write_json,
    safe_write_text,
    sha256,
    split_ids,
    workspace,
)
from word_builder import docx_text


def _load_instruction_stability() -> str:
    """读取 Skill 知识库中的三轮稳定性报告（若存在且通过），否则保持 NOT_VERIFIED。"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        reports = sorted(parent.glob("ai/work/knowledge_hub/07_validation/stability_report_v*.json"))
        if reports:
            try:
                report = read_json(reports[-1])
                if report.get("instruction_stability") == "INSTRUCTION_STABILITY_VERIFIED":
                    return "INSTRUCTION_STABILITY_VERIFIED"
            except FlowError:
                pass
    return "NOT_VERIFIED"


def check_zip(path: Path, expected_docx: int) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            return archive.testzip() is None and len([name for name in names if name.lower().endswith(".docx")]) == expected_docx
    except (FileNotFoundError, zipfile.BadZipFile):
        return False


def validate_project(target: Path, *, write_report: bool = False, minimum_phase: str | None = None) -> dict:
    target = target.resolve()
    ws = workspace(target)
    project = load_project(target)
    state = load_state(target)
    profile = load_profile(project["profile"])
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    checks["workspace_structure"] = all((ws / directory).is_dir() for directory in DIRECTORIES)
    if minimum_phase:
        checks["minimum_phase"] = PHASE_INDEX[state["phase"]] >= PHASE_INDEX[minimum_phase]

    if PHASE_INDEX[state["phase"]] >= PHASE_INDEX["baseline_locked"]:
        manifest_path = ws / "01_baseline/artifact_inventory.csv"
        rows = read_csv(manifest_path) if manifest_path.exists() else []
        missing, changed, outside = [], [], []
        seen = set()
        for row in rows:
            rel = row.get("path", "")
            if rel.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", rel):
                outside.append(rel)
                continue
            path = target / rel
            if rel in seen:
                outside.append(f"duplicate:{rel}")
            seen.add(rel)
            if not path.exists():
                missing.append(rel)
            elif sha256(path) != row.get("sha256"):
                changed.append(rel)
        checks["baseline_manifest_nonempty"] = bool(rows)
        checks["baseline_paths_unique_relative"] = not outside
        checks["baseline_files_unchanged"] = not missing and not changed
        checks["baseline_manifest_bound"] = bool(rows) and sha256(manifest_path) == state.get("baseline_manifest_sha256")
        details["baseline"] = {"count": len(rows), "missing": missing, "changed": changed, "path_issues": outside}

    records: dict[str, list[dict]] = {}
    if PHASE_INDEX[state["phase"]] >= PHASE_INDEX["evidence_ready"]:
        evidence_dir = ws / "02_evidence"
        header_issues, duplicate_ids, illegal_labels = [], [], []
        id_fields = {"source_records": "source_id", "claim_records": "claim_id", "fact_records": "fact_id", "assessment_records": "assessment_id", "issue_records": "issue_id"}
        for name, fields in TABLE_FIELDS.items():
            path = evidence_dir / f"{name}.csv"
            rows = read_csv(path) if path.exists() else []
            records[name] = rows
            actual_headers = set(rows[0]) if rows else set()
            if not path.exists() or (rows and not set(fields).issubset(actual_headers)):
                header_issues.append(name)
            id_field = id_fields[name]
            ids = [row.get(id_field, "") for row in rows if row.get(id_field, "")]
            if len(ids) != len(set(ids)):
                duplicate_ids.append(name)
            for row in rows:
                label = row.get("evidence_label", "")
                if label and label not in ALLOWED_EVIDENCE_LABELS:
                    illegal_labels.append(f"{name}:{row.get(id_field, '')}:{label}")
        source_ids = {row.get("source_id", "") for row in records.get("source_records", [])}
        broken = []
        for claim in records.get("claim_records", []):
            for source_id in split_ids(claim.get("source_ids", "")):
                if source_id not in source_ids:
                    broken.append(f"{claim.get('claim_id')}:{source_id}")
        for assessment in records.get("assessment_records", []):
            source_id = assessment.get("source_id", "")
            if source_id and source_id not in source_ids:
                broken.append(f"{assessment.get('assessment_id')}:{source_id}")
        fact_ids = {row.get("fact_id", "") for row in records.get("fact_records", [])}
        assessment_ids = {row.get("assessment_id", "") for row in records.get("assessment_records", [])}
        for issue in records.get("issue_records", []):
            for fact_id in split_ids(issue.get("fact_ids", "")):
                if fact_id not in fact_ids:
                    broken.append(f"{issue.get('issue_id')}:{fact_id}")
            for assessment_id in split_ids(issue.get("assessment_ids", "")):
                if assessment_id not in assessment_ids:
                    broken.append(f"{issue.get('issue_id')}:{assessment_id}")
        sources_by_id = {row.get("source_id", ""): row for row in records.get("source_records", [])}
        elevated = []
        for claim in records.get("claim_records", []):
            referenced = [sources_by_id.get(source_id, {}) for source_id in split_ids(claim.get("source_ids", ""))]
            only_research = bool(referenced) and all(item.get("source_type") in {"论文", "公众号及实务资料", "行业指南", "工作手册"} for item in referenced)
            if only_research and "法律义务" in claim.get("legal_effect", "") and "不得" not in claim.get("claim_boundary", ""):
                elevated.append(claim.get("claim_id", ""))
        db_path = evidence_dir / "evidence_hub.sqlite"
        sqlite_ok, sqlite_counts = False, {}
        if db_path.exists():
            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                sqlite_ok = conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                for name in TABLE_FIELDS:
                    sqlite_counts[name] = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                conn.close()
            except sqlite3.Error:
                sqlite_ok = False
        checks["evidence_headers"] = not header_issues
        checks["record_ids_unique"] = not duplicate_ids
        checks["evidence_labels_controlled"] = not illegal_labels
        checks["evidence_references_resolve"] = not broken
        checks["research_not_elevated_to_law"] = not elevated
        checks["sqlite_integrity_and_counts"] = sqlite_ok and all(sqlite_counts.get(name) == len(records.get(name, [])) for name in TABLE_FIELDS)
        details["evidence"] = {"counts": {name: len(rows) for name, rows in records.items()}, "header_issues": header_issues, "duplicate_ids": duplicate_ids, "illegal_labels": illegal_labels, "broken_references": broken, "research_elevation": elevated, "sqlite_counts": sqlite_counts}

    if PHASE_INDEX[state["phase"]] >= PHASE_INDEX["startup_pack_ready"]:
        startup_dir = ws / "03_client_start/Word公文包"
        docs = sorted(startup_dir.glob("*.docx"))
        readable, boundary = True, True
        for path in docs:
            try:
                text = docx_text(path)
                boundary = boundary and "客户事实待核实" in text and "不得据此直接认定合规" in text
            except (zipfile.BadZipFile, KeyError):
                readable = False
        startup_docs = (profile.get("word_docs") or {}).get("startup") or []
        startup_count = len(startup_docs) or 7
        checks["startup_word_count"] = len(docs) == startup_count
        checks["startup_word_structural"] = readable and boundary
        checks["startup_zip"] = check_zip(ws / "03_client_start/客户启动Word公文包.zip", startup_count)

    if PHASE_INDEX[state["phase"]] >= PHASE_INDEX["facts_verified"]:
        gate = read_json(ws / "04_fact_verification/gate_evidence.json")
        gate_values = [value for key, value in gate.items() if key not in {"schema_version", "notes"}]
        facts = records.get("fact_records") or read_csv(ws / "02_evidence/fact_records.csv")
        checks["fact_gate_all_true"] = bool(gate_values) and all(value is True for value in gate_values)

        def fact_is_confirmed(row: dict) -> bool:
            status = row.get("fact_status", "")
            if not status:
                # 旧字段兼容：confirmation_status=="已核实" 视为已确认
                status = "客户已确认" if row.get("confirmation_status") == "已核实" else ""
            return status in {"客户已确认", "律师已复核"}

        checks["facts_evidenced_and_confirmed"] = bool(facts) and all(fact_is_confirmed(row) and row.get("evidence_id") and row.get("confirmed_by") and row.get("conflict_status") in {"无冲突", "已解决"} and row.get("recheck_status") != "变化待复评" for row in facts)

    client_doc_texts: list[tuple[Path, str]] = []
    if PHASE_INDEX[state["phase"]] >= PHASE_INDEX["candidate_ready"]:
        candidate_dir = ws / "05_candidate_delivery/Word候选包"
        docs = sorted(candidate_dir.glob("*.docx"))
        readable, candidate_boundary, formal_misstatement = True, True, []
        for path in docs:
            try:
                text = docx_text(path)
                client_doc_texts.append((path, text))
                candidate_boundary = candidate_boundary and "候选版／需律师确认" in text and "不得据此直接认定合规" in text
                if "本文件为正式法律意见" in text or "已确认合规" in text:
                    formal_misstatement.append(path.name)
            except (zipfile.BadZipFile, KeyError):
                readable = False
        candidate_docs = (profile.get("word_docs") or {}).get("candidate") or []
        candidate_count = len(candidate_docs) or 8
        checks["candidate_word_count"] = len(docs) == candidate_count
        checks["candidate_word_structural"] = readable
        checks["candidate_boundary_present"] = candidate_boundary
        checks["no_formal_legal_opinion"] = not formal_misstatement
        checks["candidate_zip"] = check_zip(ws / "05_candidate_delivery/AI数据合规候选交付Word包.zip", candidate_count)
        details["candidate"] = {"documents": len(docs), "formal_misstatement": formal_misstatement}

    absolute_hits = []
    for path in list_text_files(ws):
        if path.parts[-2:] and "06_validation" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        if re.search(r"/Users/[^\s\"']+|[A-Za-z]:\\\\", text):
            absolute_hits.append(path.relative_to(ws).as_posix())
    checks["active_paths_relative"] = not absolute_hits
    details["absolute_path_hits"] = absolute_hits

    banned_hits = []
    if profile.get("banned_terms"):
        if not client_doc_texts:
            for directory in (ws / "03_client_start/Word公文包", ws / "05_candidate_delivery/Word候选包"):
                for path in directory.glob("*.docx") if directory.exists() else []:
                    client_doc_texts.append((path, docx_text(path)))
        for path, text in client_doc_texts:
            for term in profile["banned_terms"]:
                if term in text:
                    banned_hits.append(f"{path.name}:{term}")
    checks["profile_isolation"] = not banned_hits
    details["profile_isolation_hits"] = banned_hits

    if state["phase"] == "validated_archived":
        archive_dir = ws / f"07_archive/{SKILL_VERSION}"
        bundle = archive_dir / f"AI数据合规候选交付包-{SKILL_VERSION}.zip"
        checks["archive_complete"] = bundle.exists() and (archive_dir / "成果清单.csv").exists() and (archive_dir / "SHA256SUMS.txt").exists()

    passed = bool(checks) and all(checks.values())
    candidate_hashes = {}
    for directory in (ws / "03_client_start", ws / "05_candidate_delivery"):
        if directory.exists():
            for path in sorted(item for item in directory.rglob("*") if item.is_file()):
                candidate_hashes[path.relative_to(ws).as_posix()] = sha256(path)
    report = {
        "schema_version": "1.0",
        "project_id": project["project_id"],
        "phase": state["phase"],
        "passed": passed,
        "completion_marker": "DOMAIN_VERIFIED" if passed else "NOT_VERIFIED",
        "instruction_stability": _load_instruction_stability(),
        "checks": checks,
        "details": details,
        "candidate_hashes": candidate_hashes,
        "boundary": "本报告验证当前本地产物的结构化不变量，不替代律师的法律判断，也不证明多轮指令稳定性。",
    }
    if write_report:
        output = ws / "06_validation/domain_validation.json"
        safe_write_json(output, report, allow_update=True)
        lines = ["# AI数据合规冷启动项目验收", "", f"- 项目：{project['project_name']}", f"- 阶段：{state['phase']}", f"- 结果：{'DOMAIN_VERIFIED' if passed else 'NOT_VERIFIED'}", f"- 指令稳定性：NOT_VERIFIED", "", "## 检查项", ""]
        lines.extend(f"- {'通过' if value else '失败'}：{name}" for name, value in checks.items())
        lines.extend(["", "本验收只确认当前本地产物的可观察不变量；正式法律意见仍须律师确认。", ""])
        safe_write_text(ws / "06_validation/domain_validation.md", "\n".join(lines), allow_update=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = validate_project(args.target, write_report=args.write_report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 5)


if __name__ == "__main__":
    main()
