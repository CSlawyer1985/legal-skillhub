#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
PROFILES = ASSETS / "profiles"
WORKSPACE_NAME = "ai_compliance"
SKILL_VERSION = "0.3.0-candidate"
CONFIG_SCHEMA_VERSION = "1.1"
PROJECT_SCHEMA_VERSION = "1.0"
SQLITE_SCHEMA_VERSION = 1
PHASES = [
    "initialized",
    "baseline_locked",
    "evidence_ready",
    "startup_pack_ready",
    "facts_verified",
    "candidate_ready",
    "validated_archived",
]
PHASE_INDEX = {name: index for index, name in enumerate(PHASES)}
ALLOWED_EVIDENCE_LABELS = {
    "文件明确记载",
    "多个文件归纳",
    "需律师确认",
    "无直接法源",
    "客户事实待核实",
}

DIRECTORIES = [
    "00_project",
    "01_baseline",
    "02_evidence",
    "03_client_start",
    "04_fact_verification",
    "05_candidate_delivery",
    "06_validation",
    "07_archive",
]

GATE_FIELDS_DEFAULT = [
    "p0_registered",
    "interviews_confirmed",
    "data_map_complete",
    "system_map_complete",
    "role_matrix_complete",
    "authorization_and_suppliers_verified",
    "unconfirmed_facts_listed",
    "scope_changes_recorded",
    "lawyer_review_fields_defined",
]

WORD_DOCS_DEFAULT = {
    "startup": [
        {"doc_no": "00", "title": "使用说明及文件索引", "short_title": "使用说明", "purpose": "说明发送顺序、填写边界、证据编号和阶段门禁。"},
        {"doc_no": "01", "title": "项目启动说明及P0资料清单", "short_title": "P0资料清单", "purpose": "收集确认项目边界所需的第一批最低资料。"},
        {"doc_no": "02", "title": "管理层及跨部门访谈提纲", "short_title": "访谈提纲", "purpose": "按角色核验用例、数据、系统、供应商和责任。"},
        {"doc_no": "03", "title": "数据资产、处理活动及授权链调研表", "short_title": "数据与授权链", "purpose": "记录数据来源、用途、处理活动、授权和共享。"},
        {"doc_no": "04", "title": "系统、供应商及外部模型调研表", "short_title": "系统与供应商", "purpose": "核验系统边界、接口、外部模型、日志和退出安排。"},
        {"doc_no": "05", "title": "数据安全风险评估及整改复验表", "short_title": "评估与复验", "purpose": "在事实核验后记录适用指标、问题、整改和复验。"},
        {"doc_no": "06", "title": "最小试点准入核验表", "short_title": "试点准入", "purpose": "事实和前置控制未满足时不得启动真实试点。"},
    ],
    "candidate": [
        {"doc_no": "00", "title": "候选交付包使用说明及成果索引", "short_title": "成果索引"},
        {"doc_no": "01", "title": "管理层摘要", "short_title": "管理层摘要"},
        {"doc_no": "02", "title": "项目范围及事实确认稿", "short_title": "事实确认稿"},
        {"doc_no": "03", "title": "数据、系统、角色与授权链说明", "short_title": "数据系统说明"},
        {"doc_no": "04", "title": "法律适用性及证据矩阵", "short_title": "适用性矩阵"},
        {"doc_no": "05", "title": "AI数据安全风险评估候选报告", "short_title": "风险评估"},
        {"doc_no": "06", "title": "问题、整改及复验清单", "short_title": "整改复验"},
        {"doc_no": "07", "title": "未决事项、律师确认及证据索引", "short_title": "未决与证据"},
    ],
}

SOURCE_FIELDS = [
    "source_id", "external_id", "source_type", "title", "version", "effect_status",
    "authority_level", "official_url", "file_location", "locator", "verification_date",
    "verification_status", "evidence_label", "evidence_boundary",
]
CLAIM_FIELDS = [
    "claim_id", "claim", "evidence_label", "legal_effect", "applicability_conditions",
    "source_ids", "locator", "paths", "events", "risks", "gates", "documents",
    "lawyer_review_status", "claim_boundary",
]
FACT_FIELDS = [
    "fact_id", "fact", "evidence_id", "evidence_location", "evidence_hash", "owner",
    "fact_status", "confirmation_method", "confirmed_by", "confirmed_at",
    "conflict_status", "lawyer_review_status", "recheck_status", "boundary",
]
FACT_STATUS_VALUES = ["未提供", "已提供未核验", "存在矛盾", "客户已确认", "律师已复核", "变化待复评"]
FACT_CONFIRMATION_METHODS = ["书面材料", "访谈陈述", "系统验证"]
ASSESSMENT_FIELDS = [
    "assessment_id", "source_id", "theme", "assessment_text", "method", "criteria",
    "expected_evidence", "paths", "events", "risks", "gates", "documents",
    "applicability_status", "legal_effect", "customer_fact_status", "assessment_status",
    "risk_level", "remediation_status", "retest_status", "lawyer_review_status",
]
ISSUE_FIELDS = [
    "issue_id", "fact_ids", "assessment_ids", "risk", "evidence_label", "severity",
    "remediation", "owner", "due_date", "retest_method", "closure_evidence", "status",
    "lawyer_review_status",
]
TABLE_FIELDS = {
    "source_records": SOURCE_FIELDS,
    "claim_records": CLAIM_FIELDS,
    "fact_records": FACT_FIELDS,
    "assessment_records": ASSESSMENT_FIELDS,
    "issue_records": ISSUE_FIELDS,
}


class FlowError(RuntimeError):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def safe_write_bytes(path: Path, content: bytes, *, allow_update: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.read_bytes()
        if current == content:
            return False
        if not allow_update:
            raise FlowError(f"同名异内容成果冲突：{path}", 4)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(content)
    temporary.replace(path)
    return True


def safe_write_text(path: Path, content: str, *, allow_update: bool = False) -> bool:
    return safe_write_bytes(path, content.encode("utf-8"), allow_update=allow_update)


def safe_write_json(path: Path, value, *, allow_update: bool = False) -> bool:
    return safe_write_bytes(path, json_bytes(value), allow_update=allow_update)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise FlowError(f"无法读取JSON：{path}: {exc}", 2) from exc


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError as exc:
        raise FlowError(f"缺少CSV：{path}", 2) from exc


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    import io
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def safe_write_csv(path: Path, rows: list[dict], fields: list[str], *, allow_update: bool = False) -> bool:
    return safe_write_bytes(path, csv_bytes(rows, fields), allow_update=allow_update)


def split_ids(value: str) -> list[str]:
    return [part for part in re.split(r"[;,；，\s]+", value or "") if part]


def load_profile(profile_id: str) -> dict:
    path = PROFILES / f"{profile_id}.json"
    if not path.exists():
        raise FlowError(f"未知行业配置：{profile_id}", 2)
    profile = read_json(path)
    profile = {**profile}
    profile.setdefault("config_version", CONFIG_SCHEMA_VERSION)
    profile.setdefault("jurisdiction", "中国大陆")
    profile.setdefault("scope", "")
    profile.setdefault("negative_boundary", [])
    profile.setdefault("interview_targets", profile.get("roles", []))
    profile.setdefault("data_types", [])
    profile.setdefault("fact_gate_fields", {field: field for field in GATE_FIELDS_DEFAULT})
    profile.setdefault("fact_status_values", list(FACT_STATUS_VALUES))
    profile.setdefault("confirmation_methods", list(FACT_CONFIRMATION_METHODS))
    word_docs = profile.get("word_docs")
    if not isinstance(word_docs, dict):
        word_docs = {}
    word_docs.setdefault("startup", WORD_DOCS_DEFAULT["startup"])
    word_docs.setdefault("candidate", WORD_DOCS_DEFAULT["candidate"])
    profile["word_docs"] = word_docs
    return profile


def workspace(target: Path) -> Path:
    return target.resolve() / WORKSPACE_NAME


def project_path(target: Path) -> Path:
    return workspace(target) / "00_project/project.json"


def state_path(target: Path) -> Path:
    return workspace(target) / "00_project/state.json"


def load_project(target: Path) -> dict:
    return read_json(project_path(target))


def load_state(target: Path) -> dict:
    state = read_json(state_path(target))
    if state.get("phase") not in PHASE_INDEX:
        raise FlowError(f"非法项目阶段：{state.get('phase')}", 2)
    return state


def update_state(target: Path, state: dict, **changes) -> dict:
    updated = dict(state)
    updated.update(changes)
    updated["updated_at"] = now_iso()
    safe_write_json(state_path(target), updated, allow_update=True)
    return updated


def phase_at_least(state: dict, phase: str) -> bool:
    return PHASE_INDEX[state["phase"]] >= PHASE_INDEX[phase]


def normalize_rows(rows: list[dict], fields: list[str]) -> list[dict[str, str]]:
    return [{field: str(row.get(field, "") or "") for field in fields} for row in rows]


def build_sqlite(path: Path, tables: dict[str, tuple[list[str], list[dict]]]) -> None:
    if path.exists():
        raise FlowError(f"同名异内容成果冲突：{path}", 4)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        for table_name, (fields, rows) in tables.items():
            columns = ", ".join(f'"{field}" TEXT' for field in fields)
            conn.execute(f'CREATE TABLE "{table_name}" ({columns})')
            if rows:
                placeholders = ",".join("?" for _ in fields)
                conn.executemany(
                    f'INSERT INTO "{table_name}" VALUES ({placeholders})',
                    [[row.get(field, "") for field in fields] for row in rows],
                )
        conn.execute(f"PRAGMA user_version = {SQLITE_SCHEMA_VERSION}")
        conn.commit()
    finally:
        conn.close()


def relative_to_target(path: Path, target: Path) -> str:
    try:
        return path.resolve().relative_to(target.resolve()).as_posix()
    except ValueError as exc:
        raise FlowError(f"项目外路径禁止写入活跃记录：{path}", 4) from exc


def deterministic_zip(zip_path: Path, files: list[tuple[Path, str]]) -> None:
    if zip_path.exists():
        raise FlowError(f"同名异内容成果冲突：{zip_path}", 4)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in sorted(files, key=lambda item: item[1]):
            info = zipfile.ZipInfo(arcname, (2026, 8, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())


def clean_filename(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\n\r]+", "-", value).strip(" .-")
    return cleaned[:80] or "AI数据合规项目"


def list_text_files(root: Path) -> list[Path]:
    suffixes = {".json", ".csv", ".md", ".txt", ".html", ".py", ".yaml", ".yml"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes)
