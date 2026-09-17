#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import warnings
from pathlib import Path

from common import (
    ASSESSMENT_FIELDS,
    CLAIM_FIELDS,
    DIRECTORIES,
    FACT_FIELDS,
    GATE_FIELDS_DEFAULT,
    ISSUE_FIELDS,
    PHASES,
    PHASE_INDEX,
    PROJECT_SCHEMA_VERSION,
    SKILL_VERSION,
    SOURCE_FIELDS,
    SQLITE_SCHEMA_VERSION,
    TABLE_FIELDS,
    FlowError,
    build_sqlite,
    deterministic_zip,
    load_profile,
    load_project,
    load_state,
    normalize_rows,
    now_iso,
    phase_at_least,
    project_path,
    read_csv,
    read_json,
    relative_to_target,
    safe_write_csv,
    safe_write_json,
    safe_write_text,
    sha256,
    split_ids,
    state_path,
    update_state,
    workspace,
)
from word_builder import build_candidate_pack, build_startup_pack


def gate_fields_for(profile: dict) -> list[str]:
    fields = profile.get("fact_gate_fields")
    if isinstance(fields, dict):
        return list(fields)
    if isinstance(fields, list) and fields:
        return list(fields)
    return list(GATE_FIELDS_DEFAULT)


def emit(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def normalize_adopt_mapping(adopt: dict) -> dict:
    """将 adopt 配置归一化为声明式结构，兼容旧扁平格式。

    旧格式：{"source_records": "<path>", "formal_baseline": "<path>", ...}
    新格式：{"mapping_version": "1.1", "records": {...}, "baseline": [...], "scope": [...]}
    """
    records = adopt.get("records")
    if isinstance(records, dict):
        # 新格式
        result = {
            "mapping_version": adopt.get("mapping_version", "1.1"),
            "records": dict(records),
            "baseline": adopt.get("baseline") or [],
            "scope": adopt.get("scope") or [],
            "ignore": adopt.get("ignore") or [],
        }
        for key in ("source_records", "claim_records", "assessment_records", "issue_records"):
            if key in adopt and key not in result["records"]:
                result["records"][key] = {"path": adopt[key]}
        if "formal_baseline" in adopt and not result["baseline"]:
            result["baseline"] = [{"path": adopt["formal_baseline"], "role": "formal"}]
        return result
    # 旧扁平格式
    result = {"mapping_version": "1.0", "records": {}, "baseline": [], "scope": [], "ignore": []}
    for key in ("source_records", "claim_records", "assessment_records", "issue_records"):
        if key in adopt:
            result["records"][key] = {"path": adopt[key]}
    if "formal_baseline" in adopt:
        result["baseline"] = [{"path": adopt["formal_baseline"], "role": "formal"}]
    if adopt.get("optional_showcase"):
        result["baseline"].append({"path": adopt["optional_showcase"], "role": "optional"})
    return result


def make_project(args, mode: str) -> dict:
    template = read_json(Path(__file__).resolve().parents[1] / "assets/project-template.json")
    profile = load_profile(args.profile)
    project = dict(template)
    project.update({
        "project_id": args.project_id,
        "project_name": args.project_name,
        "use_case": args.use_case,
        "jurisdiction": args.jurisdiction,
        "profile": args.profile,
        "profile_display_name": profile["display_name"],
        "skill_version": SKILL_VERSION,
        "mode": mode,
        "created_at": now_iso(),
    })
    if mode == "adopt":
        adopt = profile.get("adopt")
        if not adopt:
            raise FlowError(f"配置不支持adopt：{args.profile}", 2)
        mapping = normalize_adopt_mapping(adopt)
        project["adopt_mapping"] = mapping
        baseline_scopes = []
        for key in ("source_records", "claim_records", "assessment_records", "issue_records"):
            if key in mapping["records"]:
                baseline_scopes.append(mapping["records"][key]["path"])
        # 仅 role=formal 的 baseline 作为接入硬性前置；optional 缺失不阻断
        for item in mapping["baseline"]:
            if item.get("role", "formal") == "formal":
                baseline_scopes.append(item["path"])
        project["baseline_scopes"] = list(dict.fromkeys(baseline_scopes))
    return project


def initialize(args, mode: str) -> None:
    target = args.target.resolve()
    project = make_project(args, mode)
    profile = load_profile(args.profile)
    if args.dry_run:
        emit({"dry_run": True, "command": mode, "target": str(target), "workspace": "ai_compliance", "profile": args.profile, "directories": DIRECTORIES})
        return
    target.mkdir(parents=True, exist_ok=True)
    ws = workspace(target)
    for name in DIRECTORIES:
        (ws / name).mkdir(parents=True, exist_ok=True)
    if mode == "init":
        for scope in project["baseline_scopes"]:
            (target / scope).mkdir(parents=True, exist_ok=True)
    else:
        missing = [path for path in project["baseline_scopes"] if not (target / path).exists()]
        if missing:
            raise FlowError("既有项目适配文件缺失：" + "; ".join(missing), 2)
    state = {
        "schema_version": "1.0",
        "skill_version": SKILL_VERSION,
        "project_id": args.project_id,
        "phase": "initialized",
        "customer_fact_status": "待核实",
        "lawyer_review_status": "需律师确认",
        "baseline_manifest_sha256": "",
        "outputs": {},
        "last_validation": "NOT_VERIFIED",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    safe_write_json(project_path(target), project)
    safe_write_json(state_path(target), state)
    gate_fields = gate_fields_for(profile)
    gate = {"schema_version": "1.0", **{field: False for field in gate_fields}, "notes": "客户事实待核实；由责任人根据真实证据填写。"}
    safe_write_json(ws / "04_fact_verification/gate_evidence.json", gate)
    safe_write_text(ws / "00_project/范围与边界.md", f"# {args.project_name}\n\n- 用例：{args.use_case}\n- 行业配置：{profile['display_name']}\n- 适用地区：{args.jurisdiction}\n- 输出边界：仅生成候选材料，不生成正式法律意见。\n")
    emit({"command": mode, "phase": "initialized", "workspace": str(ws), "next": "添加或核对输入资料后推进baseline_locked"})


def classify(path: Path, target: Path) -> tuple[str, str, str, str]:
    rp = relative_to_target(path, target)
    lower = rp.lower()
    if "/outputs/" in lower or "正式" in path.name:
        return "正式成果", "既有正式基线", "禁止直接修改", rp
    if any(part in lower for part in ("source", "来源", "原始", "论文", "法规")):
        return "原始资料", "只读来源", "禁止修改；仅允许版本化新增", rp
    if any(part in lower for part in ("candidate", "候选", "v4.3", "v4.4")):
        return "候选成果", "内部候选", "允许生成新版本；禁止原位覆盖", rp
    return "研究底稿", "活跃工作文件", "在维护入口修改", rp


def build_baseline(target: Path, project: dict) -> dict:
    ws = workspace(target)
    files: list[Path] = []
    for scope in project.get("baseline_scopes", []):
        path = target / scope
        if not path.exists():
            raise FlowError(f"基线范围不存在：{scope}", 3)
        if path.is_file():
            files.append(path)
        else:
            files.extend(item for item in path.rglob("*") if item.is_file())
    files = sorted({path.resolve() for path in files if ws.resolve() not in path.resolve().parents and ".git" not in path.parts and "__pycache__" not in path.parts})
    if not files:
        raise FlowError("基线范围内没有文件；请先放入项目输入资料", 3)
    rows = []
    for index, path in enumerate(files, 1):
        role, status, permission, maintenance = classify(path, target)
        rows.append({
            "artifact_id": f"ART-{index:04d}",
            "path": relative_to_target(path, target),
            "file_name": path.name,
            "role": role,
            "status": status,
            "sha256": sha256(path),
            "edit_policy": permission,
            "maintenance_entry": maintenance,
        })
    fields = ["artifact_id", "path", "file_name", "role", "status", "sha256", "edit_policy", "maintenance_entry"]
    manifest = ws / "01_baseline/artifact_inventory.csv"
    safe_write_csv(manifest, rows, fields)
    digest = sha256(manifest)
    safe_write_json(ws / "01_baseline/baseline_lock.json", {"schema_version": "1.0", "file_count": len(rows), "manifest": "01_baseline/artifact_inventory.csv", "manifest_sha256": digest, "locked_at": now_iso()})
    return {"manifest": "01_baseline/artifact_inventory.csv", "sha256": digest, "count": len(rows)}


def _map_record_fields(rows: list[dict], field_map: dict) -> list[dict]:
    if not field_map:
        return rows
    mapped = []
    for row in rows:
        new_row = dict(row)
        for source_col, target_col in field_map.items():
            if source_col in new_row:
                new_row[target_col] = new_row[source_col]
        mapped.append(new_row)
    return mapped


def import_or_seed_records(target: Path, project: dict, profile: dict) -> dict[str, list[dict]]:
    if project["mode"] == "adopt":
        mapping = project["adopt_mapping"]
        records = mapping["records"]

        def _load_record(key: str, fields: list[str]) -> list[dict]:
            cfg = records.get(key)
            if not cfg:
                return []
            raw_rows = read_csv(target / cfg["path"])
            mapped_rows = _map_record_fields(raw_rows, cfg.get("field_map") or {})
            return normalize_rows(mapped_rows, fields)

        source_rows = _load_record("source_records", SOURCE_FIELDS)
        for row in source_rows:
            row["external_id"] = row["external_id"] or row["source_id"]
        claim_rows = _load_record("claim_records", CLAIM_FIELDS)
        assessment_rows = _load_record("assessment_records", ASSESSMENT_FIELDS)
    else:
        source_rows = normalize_rows(profile.get("seed_sources", []), SOURCE_FIELDS)
        claim_rows = normalize_rows(profile.get("seed_claims", []), CLAIM_FIELDS)
        assessment_rows = normalize_rows(profile.get("seed_assessments", []), ASSESSMENT_FIELDS)
    fact_rows = []
    initial_status = (profile.get("fact_status_values") or ["未提供"])[0]
    for index, item in enumerate(profile.get("p0_items", []), 1):
        fact_rows.append({
            "fact_id": f"FACT-{index:03d}",
            "fact": item,
            "evidence_id": "",
            "evidence_location": "",
            "evidence_hash": "",
            "owner": "",
            "fact_status": initial_status,
            "confirmation_method": "",
            "confirmed_by": "",
            "confirmed_at": "",
            "conflict_status": "未检查",
            "lawyer_review_status": "需律师确认",
            "recheck_status": "未复评",
            "boundary": "客户事实待核实",
        })
    return {
        "source_records": source_rows,
        "claim_records": claim_rows,
        "fact_records": normalize_rows(fact_rows, FACT_FIELDS),
        "assessment_records": assessment_rows,
        "issue_records": [],
    }


def preflight_adopt(target: Path, project: dict) -> dict:
    """接入前预检：映射存在性、字段映射、差异、项目外依赖。只读，不修改任何文件。"""
    target = target.resolve()
    mapping = project["adopt_mapping"]
    missing_paths = []
    field_issues = []
    mapped_rel = set()

    records = mapping["records"]
    for key, cfg in records.items():
        path = target / cfg["path"]
        mapped_rel.add(cfg["path"].replace("\\", "/"))
        if not path.exists():
            missing_paths.append(cfg["path"])
            continue
        field_map = cfg.get("field_map") or {}
        if field_map:
            try:
                header = read_csv(path)[0]
            except FlowError:
                header = []
            for source_col, _target_col in field_map.items():
                if source_col not in header:
                    field_issues.append(f"{key}: 源列 '{source_col}' 不存在于 {cfg['path']}")

    baseline_missing = []
    baseline_optional_missing = []
    baseline_outside = []
    for item in mapping["baseline"]:
        path = target / item["path"]
        mapped_rel.add(item["path"].replace("\\", "/"))
        if not path.exists():
            if item.get("role", "formal") == "formal":
                baseline_missing.append(item["path"])
            else:
                baseline_optional_missing.append(item["path"])
        else:
            try:
                path.resolve().relative_to(target)
            except ValueError:
                baseline_outside.append(item["path"])

    unrecognized = []
    scope = mapping.get("scope") or []
    ignore = mapping.get("ignore") or [".git", "ai_compliance", "__pycache__"]
    for directory in scope:
        root = target / directory
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in ignore for part in path.parts):
                continue
            relative = path.relative_to(target).as_posix()
            if relative not in mapped_rel:
                unrecognized.append(relative)

    return {
        "mapping_version": mapping.get("mapping_version", "1.0"),
        "missing_paths": missing_paths,
        "baseline_missing": baseline_missing,
        "baseline_optional_missing": baseline_optional_missing,
        "baseline_outside_project": baseline_outside,
        "field_mapping_issues": field_issues,
        "unrecognized_in_scope": unrecognized,
        "passed": not missing_paths and not baseline_missing and not field_issues and not baseline_outside,
    }


def preflight(args) -> None:
    target = args.target.resolve()
    project = make_project(args, "adopt")
    report = preflight_adopt(target, project)
    emit(report)
    raise SystemExit(0 if report["passed"] else 5)


def build_evidence(target: Path, project: dict, profile: dict) -> dict:
    evidence = workspace(target) / "02_evidence"
    records = import_or_seed_records(target, project, profile)
    for name, rows in records.items():
        safe_write_csv(evidence / f"{name}.csv", rows, TABLE_FIELDS[name])
    tables = {name: (TABLE_FIELDS[name], rows) for name, rows in records.items()}
    build_sqlite(evidence / "evidence_hub.sqlite", tables)
    return {name: len(rows) for name, rows in records.items()}


def load_records(target: Path) -> dict[str, list[dict]]:
    evidence = workspace(target) / "02_evidence"
    return {name: read_csv(evidence / f"{name}.csv") for name in TABLE_FIELDS}


LAW_UPDATE_CHANGE_TYPES = ["新增", "修订", "替代", "废止"]
LAW_UPDATE_CSV_FIELDS = ["source_id", "title", "version", "effect_status", "change_type", "verification_date", "note"]


def law_update(target: Path, source_file: Path) -> dict:
    """本地受控法源导入：差异分析 + 受影响主张分析 + 律师复核队列。只读既有证据，不修改证据中台。"""
    target = target.resolve()
    if not source_file.exists():
        raise FlowError(f"法源更新文件不存在：{source_file}", 2)
    incoming = read_csv(source_file)
    if not incoming:
        raise FlowError("法源更新文件为空", 2)
    missing_fields = [f for f in LAW_UPDATE_CSV_FIELDS if f not in incoming[0]]
    if missing_fields:
        raise FlowError("法源更新文件缺字段：" + ", ".join(missing_fields), 2)
    records = load_records(target)
    existing = {row.get("source_id", ""): row for row in records.get("source_records", [])}
    claims = records.get("claim_records", [])
    assessments = records.get("assessment_records", [])
    diffs = []
    for row in incoming:
        source_id = row.get("source_id", "")
        change_type = row.get("change_type", "").strip()
        if change_type not in LAW_UPDATE_CHANGE_TYPES:
            raise FlowError(f"非法变更类型：{change_type}（应为 {'/'.join(LAW_UPDATE_CHANGE_TYPES)}）", 2)
        before = existing.get(source_id)
        if change_type == "新增" and before:
            raise FlowError(f"法源 {source_id} 已存在，不能标记为新增", 2)
        if change_type in {"修订", "替代", "废止"} and not before:
            raise FlowError(f"法源 {source_id} 不存在，不能标记为{change_type}", 2)
        diff = {
            "source_id": source_id,
            "change_type": change_type,
            "title": row.get("title", before.get("title", "") if before else ""),
            "before_version": before.get("version", "") if before else "",
            "after_version": row.get("version", ""),
            "effect_status": row.get("effect_status", before.get("effect_status", "") if before else ""),
            "verification_date": row.get("verification_date", ""),
            "note": row.get("note", ""),
        }
        diffs.append(diff)
    # 受影响主张/评估：source_ids 含该法源
    affected = []
    for claim in claims:
        claim_sources = split_ids(claim.get("source_ids", ""))
        hit = [d for d in diffs if d["source_id"] in claim_sources]
        if hit:
            affected.append({
                "claim_id": claim.get("claim_id", ""),
                "claim": claim.get("claim", ""),
                "source_ids": claim.get("source_ids", ""),
                "risks": claim.get("risks", ""),
                "gates": claim.get("gates", ""),
                "documents": claim.get("documents", ""),
                "affected_sources": [d["source_id"] for d in hit],
                "lawyer_review_status": claim.get("lawyer_review_status", "需律师确认"),
            })
    for assessment in assessments:
        if assessment.get("source_id", "") in {d["source_id"] for d in diffs}:
            affected.append({
                "assessment_id": assessment.get("assessment_id", ""),
                "claim": assessment.get("assessment_text", ""),
                "source_ids": assessment.get("source_id", ""),
                "risks": assessment.get("risks", ""),
                "gates": assessment.get("gates", ""),
                "documents": assessment.get("documents", ""),
                "affected_sources": [assessment.get("source_id", "")],
                "lawyer_review_status": assessment.get("lawyer_review_status", "需律师确认"),
            })
    # 律师复核队列：差异 + 受影响项，未复核保持候选
    review_queue = [
        {
            "item_type": "法源变更",
            "item_id": d["source_id"],
            "summary": f"{d['change_type']}：{d['title']}（{d['before_version']} → {d['after_version']}）",
            "lawyer_review_status": "需律师确认",
            "candidate_only": True,
        }
        for d in diffs
    ]
    review_queue.extend(
        {
            "item_type": "受影响主张" if "claim_id" in a else "受影响评估",
            "item_id": a.get("claim_id") or a.get("assessment_id", ""),
            "summary": a.get("claim", ""),
            "lawyer_review_status": a.get("lawyer_review_status", "需律师确认"),
            "candidate_only": True,
        }
        for a in affected
    )
    return {
        "command": "law-update",
        "source_file": relative_to_target(source_file, target),
        "diff_count": len(diffs),
        "diffs": diffs,
        "affected_count": len(affected),
        "affected": affected,
        "review_queue": review_queue,
        "review_pending": len(review_queue),
        "boundary": "法源更新只生成候选影响分析，未经律师复核不得升级为确定法律结论。",
    }


def law_update_command(args) -> None:
    target = args.target.resolve()
    report = law_update(target, args.source_file)
    emit(report)


INTAKE_ROOT = Path(__file__).resolve().parents[1] / "assets/intake-questions"


def load_intake_questions(question_set: str) -> list[dict]:
    """加载问题集：产业专属文件 extends generic 时合并。"""
    if not question_set or question_set == "generic":
        path = INTAKE_ROOT / "generic.json"
        if not path.exists():
            raise FlowError(f"通用问题集不存在：{path}", 2)
        data = read_json(path)
        return data.get("sections", [])
    path = INTAKE_ROOT / f"{question_set}.json"
    if not path.exists():
        raise FlowError(f"问题集不存在：{path}", 2)
    data = read_json(path)
    sections = list(data.get("sections", []))
    if data.get("extends") == "generic":
        generic = read_json(INTAKE_ROOT / "generic.json")
        sections = list(generic.get("sections", [])) + sections
    return sections


def intake_command(args) -> None:
    """第一步：创建 intake 骨架（问题清单 + 空答案）。已存在时幂等——不覆盖已有答案，仅列出待问问题。"""
    target = args.target.resolve()
    path = workspace(target) / "00_project/intake.json"
    # 幂等：已存在且未强制重置 → 读取现有状态，不重建
    if path.exists() and not args.force:
        intake = read_json(path)
        pending = [q["id"] for section in intake.get("sections", []) for q in section["questions"]
                   if not intake.get("answers", {}).get(q["id"], {}).get("asked")]
        emit({"command": "intake", "project_id": intake.get("project_id"), "question_set": intake.get("industry"),
              "total_questions": len(pending), "pending": pending, "already_exists": True,
              "note": "intake 已存在，未重建（防止覆盖已记录答案）；如需重置请加 --force",
              "next": "用 intake-record 记录回答，或读 00_project/intake.json 查看现状"})
        return
    sections = load_intake_questions(args.question_set)
    answers = {}
    for section in sections:
        for question in section["questions"]:
            answers[question["id"]] = {"answer": "", "asked": False}
    intake = {
        "schema_version": "1.0",
        "project_id": args.project_id,
        "industry": args.question_set,
        "created_at": now_iso(),
        "sections": sections,
        "answers": answers,
        "closed": False,
    }
    safe_write_json(path, intake, allow_update=True)
    # 输出待问问题清单（供对话引导）
    pending = [q["id"] for section in sections for q in section["questions"] if not answers[q["id"]]["asked"]]
    emit({"command": "intake", "project_id": args.project_id, "question_set": args.question_set, "total_questions": len(pending), "pending": pending, "next": "逐条询问律师，用 intake-record 记录回答"})


def _split_risk_items(text: str) -> list[str]:
    """切分客户申报风险条目：支持 1. / 1、 / 1） / 1) / （1） / ①② 等中英文编号。

    原实现仅按分号/换行切分，中文全角编号（1）2）3））无分隔符时整段粘连，
    且编号剥除正则无法处理全角右括号，导致条数错乱与编号残留。
    """
    import re as re_module
    # 分号转换行 + 编号前统一插入换行（兼容中英文全半角编号与圈号）
    normalized = re_module.sub(r"[；;]+", "\n", text)
    normalized = re_module.sub(r"[①-⑩]|\d+[.、)）]", lambda m: "\n" + m.group(0), normalized)
    pieces = [p.strip() for p in normalized.split("\n") if p.strip()]
    cleaned = []
    for piece in pieces:
        body = re_module.sub(r"^[①-⑩]\s*|^（?\d+[.、)）]?\s*", "", piece)
        if body:
            cleaned.append(body)
    return cleaned


def intake_record_command(args) -> None:
    """第一步：记录一条律师回答。"""
    target = args.target.resolve()
    path = workspace(target) / "00_project/intake.json"
    if not path.exists():
        raise FlowError("intake 尚未创建，先运行 intake", 2)
    intake = read_json(path)
    if args.question_id not in intake["answers"]:
        raise FlowError(f"未知问题：{args.question_id}", 2)
    intake["answers"][args.question_id] = {"answer": args.answer, "asked": True}
    intake["updated_at"] = now_iso()
    safe_write_json(path, intake, allow_update=True)
    emit({"command": "intake-record", "question_id": args.question_id, "recorded": True, "remaining": sum(1 for v in intake["answers"].values() if not v["asked"])})


def intake_close_command(args) -> None:
    """第一步：判断信息充分性。必填问题未答完 → 输出缺失清单；答完 → 可进入下一步。"""
    target = args.target.resolve()
    path = workspace(target) / "00_project/intake.json"
    if not path.exists():
        raise FlowError("intake 尚未创建，先运行 intake", 2)
    intake = read_json(path)
    missing = []
    for section in intake["sections"]:
        if not section.get("required", False):
            continue
        for question in section["questions"]:
            answer = intake["answers"].get(question["id"], {}).get("answer", "")
            if not answer:
                missing.append({"section": section["title"], "question_id": question["id"], "text": question["text"]})
    answered = sum(1 for v in intake["answers"].values() if v.get("asked") and v.get("answer"))
    if missing and not args.force:
        intake["closed"] = False
        safe_write_json(path, intake, allow_update=True)
        raise FlowError("信息不充分：" + json.dumps({"missing": missing, "answered": answered, "total": len(intake["answers"])}, ensure_ascii=False), 3)
    intake["closed"] = True
    intake["updated_at"] = now_iso()
    safe_write_json(path, intake, allow_update=True)
    emit({"command": "intake-close", "project_id": intake["project_id"], "answered": answered, "total": len(intake["answers"]), "closed": True, "next": "可进入第二步构建知识库（kb-build）"})


def find_knowledge_base_root() -> Path:
    """定位知识库根目录，按优先级：
    1. 环境变量 AI_COMPLIANCE_KB_ROOT
    2. 随包知识库：skill 同级或上级的 knowledge-base/（安装包默认布局，零配置）
    3. 向上查找原知识库布局（含 论文集锦/ 与 法规与规范性文件数据库/ 的目录）
    """
    import os as os_module
    configured = os_module.environ.get("AI_COMPLIANCE_KB_ROOT")
    if configured:
        candidate = Path(configured).resolve()
        if candidate.exists():
            return candidate
        raise FlowError(f"AI_COMPLIANCE_KB_ROOT 指向的目录不存在：{configured}", 2)
    # 随包知识库：安装包默认布局（bootstrap-ai-data-compliance 与 knowledge-base 同级）
    skill_root = Path(__file__).resolve().parents[1]
    for candidate in (skill_root.parent / "knowledge-base", skill_root / "knowledge-base"):
        if candidate.exists():
            return candidate
    # 向上查找原知识库布局
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "论文集锦").exists() and (parent / "法规与规范性文件数据库").exists():
            return parent
    raise FlowError(
        "未找到知识库根目录。安装包默认布局：将 skill 与 knowledge-base 放在同一目录（保持解压结构）即可自动识别；"
        "或将知识库置于任意位置并设置环境变量 AI_COMPLIANCE_KB_ROOT=<知识库根目录>"
        "（知识库根目录含 论文集锦/ 与 法规与规范性文件数据库/ 子目录）", 2)


KB_COLLECTIONS = {
    "论文库": "论文集锦",
    "实务文章库": "医疗数据公众号相关",
    "法律法规库": "法规与规范性文件数据库",
}


def kb_build_command(args) -> None:
    """第二步：从原三库按产业关键词筛选，生成引用索引 kb_index.json + 待补充清单。只读原库，不复制文件。"""
    target = args.target.resolve()
    intake_path = workspace(target) / "00_project/intake.json"
    if not intake_path.exists():
        raise FlowError("intake 尚未创建，先运行 intake", 2)
    intake = read_json(intake_path)
    if not intake.get("closed"):
        raise FlowError("intake 未收口，先运行 intake-close", 3)
    # 关键词：优先用显式关键词；缺省从 intake 回答提取（按分隔符切分 + 已知主题词表）
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()] if args.keywords else []
    if not keywords:
        topic_words = ["客服", "对话", "订单", "物流", "画像", "训练", "模型", "API", "供应商", "权限", "日志", "跨境", "备案", "标识", "转人工", "投诉", "退款", "售后", "用户", "个人信息", "数据"]
        for answer in intake["answers"].values():
            text = answer.get("answer", "")
            for topic in topic_words:
                if topic in text and topic not in keywords:
                    keywords.append(topic)
    if not keywords:
        keywords = [answer.get("answer", "")[:8] for answer in intake["answers"].values() if answer.get("answer")]
    root = find_knowledge_base_root()
    index = {"schema_version": "1.0", "industry": intake.get("industry", ""), "keywords": keywords, "collections": {}}
    for collection_name, directory_name in KB_COLLECTIONS.items():
        collection_root = root / directory_name
        if not collection_root.exists():
            continue
        entries = []
        for path in sorted(collection_root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".pdf", ".docx", ".md", ".csv", ".sqlite"}:
                continue
            relative = path.relative_to(root).as_posix()
            matched = any(kw.lower() in path.name.lower() for kw in keywords if kw)
            entries.append({"path": relative, "name": path.name, "matched": matched})
        index["collections"][collection_name] = {"directory": directory_name, "entries": entries}
    # 待补充清单：原库中未匹配的产业关键词
    matched_keywords = set()
    for collection in index["collections"].values():
        for entry in collection["entries"]:
            if entry["matched"]:
                for kw in keywords:
                    if kw.lower() in entry["name"].lower():
                        matched_keywords.add(kw)
    missing_keywords = [kw for kw in keywords if kw not in matched_keywords]
    kb_dir = workspace(target) / "03_knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)
    safe_write_json(kb_dir / "kb_index.json", index, allow_update=True)
    emit({
        "command": "kb-build",
        "keywords": keywords,
        "collections": {name: sum(1 for e in c["entries"]) for name, c in index["collections"].items()},
        "matched_in_original": {name: sum(1 for e in c["entries"] if e["matched"]) for name, c in index["collections"].items()},
        "missing_keywords": missing_keywords,
        "index": relative_to_target(kb_dir / "kb_index.json", target),
        "next": "如有产业特有资料，用 kb-add 补充；然后可进入第三步（model-generate）",
    })


def kb_add_command(args) -> None:
    """第二步：律师补充产业特有资料入索引（引用路径，不复制文件）。"""
    target = args.target.resolve()
    kb_dir = workspace(target) / "03_knowledge_base"
    index_path = kb_dir / "kb_index.json"
    if not index_path.exists():
        raise FlowError("kb_index 尚未创建，先运行 kb-build", 2)
    index = read_json(index_path)
    source = args.source.resolve()
    root = find_knowledge_base_root()
    try:
        relative = source.relative_to(root).as_posix()
    except ValueError:
        raise FlowError(f"资料须位于知识库根目录内：{source}", 4)
    collection_name = args.collection
    if collection_name not in index["collections"]:
        raise FlowError(f"未知资料库：{collection_name}（应为 {'/'.join(KB_COLLECTIONS)}）", 2)
    entries = index["collections"][collection_name]["entries"]
    if not any(e["path"] == relative for e in entries):
        entries.append({"path": relative, "name": source.name, "matched": True})
    safe_write_json(index_path, index, allow_update=True)
    emit({"command": "kb-add", "collection": collection_name, "path": relative, "added": True})


MODEL_ASSETS = Path(__file__).resolve().parents[1] / "assets/model"

GENERIC_STAGES = [
    ("S01", "需求触发与边界界定"),
    ("S02", "数据采集与授权"),
    ("S03", "数据存储与治理"),
    ("S04", "模型调用与推理"),
    ("S05", "输出生成与审核"),
    ("S06", "留存、退出与复核"),
]

GENERIC_RISKS = [
    {"familyId": "RF01", "theme": "个人信息泄露", "description": "处理过程中个人信息被未授权访问或披露"},
    {"familyId": "RF02", "theme": "权限越界", "description": "AI或人员访问超出授权范围的数据"},
    {"familyId": "RF03", "theme": "输出内容失实", "description": "AI生成内容与事实或最新规则不符"},
    {"familyId": "RF04", "theme": "生成内容标识缺失", "description": "AI生成内容未添加标识"},
    {"familyId": "RF05", "theme": "供应商责任不清", "description": "外部模型供应商数据处理责任边界模糊"},
    {"familyId": "RF06", "theme": "人工复核缺失", "description": "高风险场景缺少人工复核或转接"},
]

GENERIC_GATES = [
    {"id": "G01", "name": "数据来源与授权核验", "description": "训练/检索数据来源与授权链闭环"},
    {"id": "G02", "name": "上线准入", "description": "标识、人工复核、风险控制齐备后方可上线"},
    {"id": "G03", "name": "变更与退出复核", "description": "模型/数据/供应商变更须复评，退出须删除返还"},
]

GENERIC_DOCUMENTS = [
    {"id": "DOC01", "name": "场景与产品边界备忘录", "purpose": "记录AI系统边界、用户与用途"},
    {"id": "DOC02", "name": "数据来源与授权链专项意见", "purpose": "核验数据授权链"},
    {"id": "DOC03", "name": "数据处理协议（DPA）", "purpose": "供应商委托处理责任"},
    {"id": "DOC04", "name": "个人信息保护影响评估（PIPIA）", "purpose": "个保影响评估"},
    {"id": "DOC05", "name": "风险评估候选报告", "purpose": "风险识别与评价"},
    {"id": "DOC06", "name": "上线准入核验表", "purpose": "上线前门禁核验"},
]


def _auto_layout_system_nodes(nodes: list[dict]) -> list[dict]:
    """自动布局：按 category 分行；每行节点均分铺满内容区（宽 1610，节点宽 205，间距最小 60）。"""
    rows = {"external": 0, "device": 1, "internal": 2, "third_party": 3}
    content_left, content_right = 40, 1600
    counts = {}
    for node in nodes:
        category = node.get("category", "internal")
        counts[category] = counts.get(category, 0) + 1
    used_rows = sorted({rows.get(node.get("category", "internal"), 2) for node in nodes})
    row_y = {}
    for index, row in enumerate(used_rows):
        row_y[row] = 130 + index * 240
    counters = {}
    for node in nodes:
        category = node.get("category", "internal")
        row = rows.get(category, 2)
        col = counters.get(category, 0)
        counters[category] = col + 1
        count_in_row = counts.get(category, 1)
        # 节点均分铺满：起点 content_left，步长 (可用宽度-节点宽)/(数量-1)
        if count_in_row > 1:
            step = (content_right - content_left - 205) / (count_in_row - 1)
        else:
            step = 0
        node["x"] = round(content_left + col * step)
        node["y"] = row_y.get(row, 130)
    return nodes


def model_generate_command(args) -> None:
    """第三步：从 intake + kb_index 自动生成通用产业全景模型 JSON。"""
    target = args.target.resolve()
    intake_path = workspace(target) / "00_project/intake.json"
    if not intake_path.exists():
        raise FlowError("intake 尚未创建，先运行 intake", 2)
    intake = read_json(intake_path)
    if not intake.get("closed"):
        raise FlowError("intake 未收口，先运行 intake-close", 3)
    answers = {qid: v.get("answer", "") for qid, v in intake["answers"].items()}
    # 提取关键信息
    use_case = answers.get("BB-01", "") or intake.get("industry", "")
    user_scope = answers.get("BB-03", "")
    region = answers.get("BB-04", "")
    suppliers = [answers.get("MS-01", ""), answers.get("MS-02", "")]
    architecture = answers.get("AR-01", "")
    # 数据对象：优先用产业配置 profile 的 data_types（权威清单，一次成型）；未提供时从 intake 回答提取
    profile_data_types = []
    industry = intake.get("industry", "")
    if industry:
        profile_path = Path(__file__).resolve().parents[1] / "assets/profiles" / f"{industry}.json"
        if profile_path.exists():
            profile_data_types = read_json(profile_path).get("data_types", [])
    data_sources_text = "；".join(filter(None, [answers.get("DS-01", ""), answers.get("DS-03", ""), answers.get("CD-01", "")]))
    if args.data_types:
        data_types = args.data_types
    elif profile_data_types:
        data_types = "；".join(profile_data_types)
    else:
        data_types = data_sources_text
    # 系统节点：从架构/供应商回答生成
    system_nodes = [
        {"id": "SYS01", "role": "用户/客户", "name": "用户/客户", "actualSystemName": "【系统名称｜待核实】", "category": "external", "factStatus": "待核实"},
        {"id": "SYS02", "role": "业务入口（前端/渠道）", "name": "业务入口", "actualSystemName": "【系统名称｜待核实】", "category": "external", "factStatus": "待核实"},
        {"id": "SYS03", "role": "AI应用服务", "name": "AI应用服务", "actualSystemName": "【系统名称｜待核实】", "category": "internal", "factStatus": "待核实"},
        {"id": "SYS04", "role": "数据存储（库/向量库）", "name": "数据存储", "actualSystemName": "【系统名称｜待核实】", "category": "internal", "factStatus": "待核实"},
        {"id": "SYS05", "role": "外部模型API", "name": "外部模型API", "actualSystemName": suppliers[0] or "【待核实】", "category": "third_party", "factStatus": "待核实"},
        {"id": "SYS06", "role": "人工工作台/审核", "name": "人工工作台", "actualSystemName": "【系统名称｜待核实】", "category": "internal", "factStatus": "待核实"},
    ]
    _auto_layout_system_nodes(system_nodes)
    noise_words = {"个人信息", "敏感个人信息", "重要数据", "敏感", "含敏感个人信息", "文本", "图片", "语音", "历史", "平台自有", "用户协议", "平台授权", "合同", "内部", "账户"}

    generic_terms = {"用户", "平台", "系统", "业务", "信息", "数据", "记录", "日志", "文本", "对话", "历史", "人工", "客服", "售后", "商品", "物流"}

    def _core_terms(name: str) -> set[str]:
        """核心词集合：去通用后缀后按 2 字滑动窗口提取，剔除通用词（用于语义去重）。"""
        cleaned = name
        for suffix in ("记录", "信息", "数据", "知识库", "详情", "日志", "索引", "手机号"):
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)]
                break
        if len(cleaned) < 2:
            return set()
        return {cleaned[i : i + 2] for i in range(len(cleaned) - 1)} - generic_terms

    data_objects = []
    for item in re.split(r"[;；、，,+／/()（）]", str(data_types)):
        item = item.strip().strip("（）()")
        if item and len(item) >= 2 and item not in noise_words:
            classification = "敏感个人信息" if "敏感" in item or "手机" in item or "账户" in item or "身份" in item or "收货" in item else "个人信息"
            terms = _core_terms(item)
            # 语义去重：与已有对象的 2 字核心词（非通用词）有交集则跳过
            if terms and any(terms & _core_terms(existing) for existing in (o["name"] for o in data_objects)):
                continue
            data_objects.append({"id": f"D{len(data_objects) + 1:02d}", "name": item, "classification": classification})
    if not data_objects:
        data_objects = [{"id": "D01", "name": "业务数据", "classification": "个人信息"}]
    def _data_edge(edge_id: str, source: str, dest: str, object_id: str, bidirectional: bool = False) -> dict:
        return {
            "id": edge_id,
            "from": source,
            "to": dest,
            "dataObjectIds": [object_id],
            "direction": "bidirectional" if bidirectional else "one_way",
            "sensitive": False,
            "externalShare": False,
            "externalTool": False,
            "paths": [],
            "eventIds": [],
            "riskIds": [],
            "gateIds": [],
            "documentIds": [],
            "provider": source,
            "recipient": dest,
            "visualRole": "data-flow",
        }

    primary_object = data_objects[0]["id"] if data_objects else "D01"
    data_edges = [
        _data_edge("DE01", "SYS01", "SYS02", primary_object),
        _data_edge("DE02", "SYS02", "SYS03", primary_object),
        _data_edge("DE03", "SYS03", "SYS04", primary_object, bidirectional=True),
        _data_edge("DE04", "SYS03", "SYS05", primary_object),
        _data_edge("DE05", "SYS03", "SYS06", primary_object),
    ]
    # 业务节点：通用 6 阶段各一个（渲染器数据契约：paths/title/eventIds/riskIds/gateIds/documentIds）
    def _process_node(node_id: str, name: str, stage_id: str, layer: str) -> dict:
        return {
            "id": node_id,
            "title": name,
            "name": name,
            "stageId": stage_id,
            "layer": layer,
            "paths": ["P1"],
            "eventIds": [],
            "riskIds": [],
            "gateIds": [],
            "documentIds": [],
            "factStatus": "待核实",
        }

    # 技术/数据层按阶段逐一对应（每阶段一列，三层纵向对齐）
    tech_names = {
        "S01": "需求与边界评估工具",
        "S02": "数据采集与授权系统",
        "S03": "存储与治理平台",
        "S04": "AI推理与模型调用",
        "S05": "内容审核与过滤",
        "S06": "留存、日志与审计系统",
    }
    data_names = {
        "S01": "业务需求数据",
        "S02": "采集与授权数据",
        "S03": "业务数据存储",
        "S04": "模型输入数据",
        "S05": "生成输出数据",
        "S06": "日志与审计数据",
    }
    business_nodes = [_process_node(f"B{index + 1:02d}", stage_name, stage_id, "BUSINESS") for index, (stage_id, stage_name) in enumerate(GENERIC_STAGES)]
    technology_nodes = [_process_node(f"TN{index + 1:02d}", tech_names[stage_id], stage_id, "TECHNOLOGY") for index, (stage_id, _) in enumerate(GENERIC_STAGES)]
    data_nodes = [_process_node(f"DN{index + 1:02d}", data_names[stage_id], stage_id, "DATA") for index, (stage_id, _) in enumerate(GENERIC_STAGES)]
    layer_links = []
    for index, (stage_id, _) in enumerate(GENERIC_STAGES):
        layer_links.append({"id": f"LL{index * 2 + 1:02d}", "from": f"B{index + 1:02d}", "to": f"TN{index + 1:02d}"})
        layer_links.append({"id": f"LL{index * 2 + 2:02d}", "from": f"B{index + 1:02d}", "to": f"DN{index + 1:02d}"})
    # 风险：通用模板 + intake 风险关注（RF-01）注入为具体风险条目
    # 注入后 risks 进入访谈提纲重点核查问题与评估报告风险清单，使场景风险可核查、可追溯；
    # certainty="客户陈述" 区别于模板的"待核实"（客户申报事实，仍需律师复核）
    risk_focus = answers.get("RF-01", "")
    risks = []
    for index, template in enumerate(GENERIC_RISKS):
        risks.append({
            "id": f"R{index + 1:02d}",
            "familyId": template["familyId"],
            "theme": template["theme"],
            "description": template["description"],
            "likelihood": "中",
            "impact": "中",
            "level": "中",
            "certainty": "待核实",
        })
    if risk_focus:
        for piece in _split_risk_items(risk_focus):
            body = piece
            theme = (body.split("：")[0].split(":")[0].strip())[:20]
            risks.append({
                "id": f"R{len(risks) + 1:02d}",
                "familyId": "RF-CUSTOM",
                "theme": theme,
                "description": body,
                "likelihood": "中",
                "impact": "中",
                "level": "中",
                "certainty": "客户陈述",
            })
    # 法源：从 kb_index 的法规库匹配条目
    sources = []
    kb_index_path = workspace(target) / "03_knowledge_base/kb_index.json"
    if kb_index_path.exists():
        kb = read_json(kb_index_path)
        for entry in kb.get("collections", {}).get("法律法规库", {}).get("entries", []):
            if entry.get("matched"):
                sources.append({"id": f"SRC{len(sources) + 1:02d}", "title": entry["name"], "version": "现行", "evidenceLabel": "文件明确记载"})
    if not sources:
        sources = [{"id": "SRC01", "title": "个人信息保护法", "version": "现行", "evidenceLabel": "需律师确认"}]
    verification_items = []
    for section in intake.get("sections", []):
        for question in section.get("questions", []):
            qid = question["id"]
            if not answers.get(qid):
                verification_items.append({"id": f"V{len(verification_items) + 1:02d}", "question": question["text"], "targetRole": section["title"]})
    model = {
        "meta": {"title": f"{use_case}｜AI数据合规全景模型", "version": "v0.3.0-candidate", "industry": intake.get("industry", ""),
                 "scene": intake.get("industry", ""),  # 产业场景标识（DFD 场景视图文件名 <scene>-dataflow.json）；用 generic 问题集但需要专属视图的项目，可手动改为专属标识
                 "legalBoundary": "基于既有材料，法规版本及适用性待专项校验"},
        "phases": [{"id": "P1", "name": "主业务路径", "priority": "首期深做"}],
        "stages": [{"id": sid, "index": i + 1, "name": name, "eventIds": []} for i, (sid, name) in enumerate(GENERIC_STAGES)],
        "processMap": {
            "stages": [{"id": sid, "index": i + 1, "name": name, "eventIds": []} for i, (sid, name) in enumerate(GENERIC_STAGES)],
            "businessNodes": business_nodes,
            "technologyNodes": technology_nodes,
            "dataNodes": data_nodes,
            "layerLinks": layer_links,
        },
        "dataFlowMap": {
            "systemNodes": system_nodes,
            "dataObjects": data_objects,
            "dataEdges": data_edges,
            "institutionZone": False,
        },
        "businessNodes": business_nodes,
        "technologyNodes": technology_nodes,
        "dataNodes": data_nodes,
        "layerLinks": layer_links,
        "systemNodes": system_nodes,
        "dataObjects": data_objects,
        "dataEdges": data_edges,
        "risks": risks,
        "gates": GENERIC_GATES,
        "documents": GENERIC_DOCUMENTS,
        "sources": sources,
        "verificationItems": verification_items,
    }
    model_dir = workspace(target) / "05_model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "industry-model.json"
    safe_write_json(model_path, model, allow_update=True)
    emit({
        "command": "model-generate",
        "model": relative_to_target(model_path, target),
        "stages": len(model["stages"]),
        "system_nodes": len(model["systemNodes"]),
        "risks": len(model["risks"]),
        "documents": len(model["documents"]),
        "sources": len(model["sources"]),
        "verification_items": len(model["verificationItems"]),
        "next": "可运行 render 生成数据流图与评估报告",
    })


def render_command(args) -> None:
    """第三步：渲染数据流图（panorama Node 引擎）+ 生成简单评估报告（HTML）。"""
    import shutil
    import subprocess
    target = args.target.resolve()
    model_path = workspace(target) / "05_model/industry-model.json"
    if not model_path.exists():
        raise FlowError("模型尚未生成，先运行 model-generate", 2)
    renderer = Path(__file__).resolve().parent / "generic_render.mjs"
    if not renderer.exists():
        raise FlowError(f"通用渲染器不存在：{renderer}", 2)
    out_dir = workspace(target) / "05_model/rendered"
    out_dir.mkdir(parents=True, exist_ok=True)
    # 调 Node generic_render 渲染三层流程 + 数据流图 SVG
    node = shutil.which("node") or "/Applications/MyAgents.app/Contents/Resources/nodejs/bin/node"
    result = subprocess.run([node, str(renderer), str(model_path), str(out_dir)], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise FlowError(f"panorama 渲染失败：{result.stderr[-500:]}", 5)
    # 数据流向图：模板引擎（场景配置 + 自动布局/路由 + 校验）
    model = read_json(model_path)
    dfd_builder = Path(__file__).resolve().parent / "dfd_builder.py"
    scene_root = Path(__file__).resolve().parents[1] / "assets/dfd-scenes"
    industry = model.get("meta", {}).get("industry", "generic")
    scene_path = scene_root / f"{industry}.json"
    if not scene_path.exists():
        scene_path = scene_root / "retail-ecommerce.json"  # 缺省用通用模板
    dfd_result = subprocess.run([sys.executable, str(dfd_builder), str(scene_path), str(model_path), str(out_dir / "data-flow-map.svg")], capture_output=True, text=True, timeout=60)
    if dfd_result.returncode != 0:
        raise FlowError(f"DFD 生成失败：{dfd_result.stderr[-500:]}", 5)
    # 三层流程图（Swimlane 视角）：model.json → 自包含 HTML（diagram-design 规范）
    processmap_builder = Path(__file__).resolve().parent / "processmap_builder.py"
    pm_html = subprocess.run([sys.executable, str(processmap_builder), str(model_path), str(out_dir / "process-map.html")], capture_output=True, text=True, timeout=60)
    if pm_html.returncode != 0:
        raise FlowError(f"三层流程图 HTML 生成失败：{pm_html.stderr[-500:]}", 5)
    # 数据流向图（角色泳道视角）：Data flow 视图 JSON → 自包含 HTML（diagram-design 规范）
    # 场景标识查找顺序：meta.scene（专属）→ meta.industry → 零售模板回退；未命中专属视图时显式警告（不静默）
    dataflow_builder = Path(__file__).resolve().parent / "dataflow_builder.py"
    scene = model.get("meta", {}).get("scene") or industry
    dataflow_view = scene_root / f"{scene}-dataflow.json"
    if not dataflow_view.exists():
        dataflow_view = scene_root / "retail-ecommerce-dataflow.json"  # 缺省通用视图
        warnings.warn(f"未找到 {scene}-dataflow.json 场景视图，回退零售模板；需要专属视图请按 SKILL.md 创建 assets/dfd-scenes/{scene}-dataflow.json（参照 retail-ecommerce-dataflow.json）")
    if dataflow_view.exists():
        df_html = subprocess.run([sys.executable, str(dataflow_builder), str(dataflow_view), str(out_dir / "data-flow-map.html")], capture_output=True, text=True, timeout=60)
        if df_html.returncode != 0:
            raise FlowError(f"DataFlow HTML 生成失败：{df_html.stderr[-500:]}", 5)
    # 数据流图几何自检：箭头穿节点 / label 压节点即失败（与 self_check 互补）
    geometry_check = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "verify_geometry.py"), str(out_dir / "data-flow-map.html")],
        capture_output=True, text=True, timeout=60)
    if geometry_check.returncode != 0:
        raise FlowError(f"数据流图几何自检失败（箭头穿节点/label 压节点）：{geometry_check.stdout[-800:]}", 5)
    # 从模型 + intake 生成评估报告（深度版）
    intake_path = workspace(target) / "00_project/intake.json"
    intake = read_json(intake_path) if intake_path.exists() else None
    report = _build_report_html(model, intake=intake)
    report_path = out_dir / "评估报告.html"
    safe_write_text(report_path, report, allow_update=True)
    # 合并为单个交付 HTML（内嵌两张 SVG + 评估报告）
    deliverable = _build_deliverable_html(model, out_dir / "process-map.html", out_dir / "data-flow-map.html", report_path)
    deliverable_path = out_dir / "全景交付.html"
    safe_write_text(deliverable_path, deliverable, allow_update=True)
    # 最终成果聚合：全景交付.html → 07_final_deliverables/
    final_dir = workspace(target) / "07_final_deliverables"
    final_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(deliverable_path, final_dir / "全景交付.html")
    emit({
        "command": "render",
        "svgs": [relative_to_target(out_dir / "process-map.svg", target), relative_to_target(out_dir / "data-flow-map.svg", target)],
        "html": [relative_to_target(out_dir / "process-map.html", target), relative_to_target(out_dir / "data-flow-map.html", target)],
        "report": relative_to_target(report_path, target),
        "deliverable": relative_to_target(deliverable_path, target),
        "svg_views": ["三层流程", "数据流图(拓扑)", "数据流图(角色泳道)"],
        "html_views": ["三层流程图(Swimlane)", "数据流图(角色泳道)"],
        "next": "可进入第四步生成手册指引文件包（field-pack）",
    })


def _ans(intake: dict | None, qid: str, default: str = "待补充") -> str:
    """取 intake 答案文本。"""
    if not intake:
        return default
    a = intake.get("answers", {}).get(qid)
    if isinstance(a, dict):
        return (a.get("answer") or "").strip() or default
    return default


def _kw_status(intake: dict | None, kws: list[str], positive: str, negative: str = "") -> str:
    """关键词命中判断：从 intake 全部答案中匹配关键词，命中返回 positive，否则 negative 或"待核实"。"""
    if intake:
        text = json.dumps(intake.get("answers", {}), ensure_ascii=False)
        if any(k in text for k in kws):
            return positive
    return negative or "待核实"


def _build_report_html(model: dict, intake: dict | None = None) -> str:
    """生成评估报告（深度版）：业务全景 / 数据资产 / 供应商生态 / 风险分析 / 义务核对 / 差距行动 / 风险事件 / 待核验。

    事实来源：intake 答案（客户陈述，需律师核实）；法规依据：元典核验过的现行有效条款。
    输出始终为候选版，未经律师复核不得作为正式法律意见。
    """
    meta = model["meta"]
    industry = meta.get("industry", "AI产业")

    # ---------- 模型基础表 ----------
    rows_risk = "\n".join(
        f"<tr><td>{r.get('id')}</td><td>{r.get('theme')}</td><td>{r.get('description')}</td></tr>"
        for r in model.get("risks", [])
    )
    rows_verify = "\n".join(
        f"<tr><td>{v.get('id')}</td><td>{v.get('question')}</td><td>{v.get('targetRole','')}</td></tr>"
        for v in model.get("verificationItems", [])
    )
    # ---------- intake 事实 ----------
    bb01, bb02, bb03, bb04 = (_ans(intake, q) for q in ("BB-01", "BB-02", "BB-03", "BB-04"))
    ds01, ds02, ds03 = (_ans(intake, q) for q in ("DS-01", "DS-02", "DS-03"))
    ms01, ms02, ms03, ms04 = (_ans(intake, q) for q in ("MS-01", "MS-02", "MS-03", "MS-04"))
    rf01, rf02, rf03 = (_ans(intake, q) for q in ("RF-01", "RF-02", "RF-03"))

    # ---------- 重点合规义务核对表（法规为元典核验条款） ----------
    obligations = [
        ("深度合成内容标识（显式+隐式）", "《互联网信息服务深度合成管理规定》§16、§17；《人工智能生成合成内容标识办法》（2025-09-01 施行）",
         _kw_status(intake, ["标识"], "存在缺口：客户自述 AI 生成语音/形象未添加显著标识，已受网安部门口头提醒")),
        ("真实身份认证", "深度合成规定§9",
         _kw_status(intake, ["实名"], "已实施实名认证（手机号+身份证二要素），但存在未成年人借用家长身份绕过风险")),
        ("生物识别信息处理单独同意", "深度合成规定§14②；个保法§28、§29",
         _kw_status(intake, ["单独同意", "声纹"], "存在缺口：语音/形象数据未获单独明确同意，混在通用注册协议中")),
        ("生成/编辑人脸、人声功能安全评估", "深度合成规定§15",
         _kw_status(intake, ["安全评估"], "待核实：TTS 仿声、形象生成涉及人脸/人声编辑功能，需确认是否已委托专业机构评估")),
        ("算法备案（舆论属性/社会动员能力）", "暂行办法§17；深度合成规定§19",
         _kw_status(intake, ["备案"], "计划 2026-09 完成深度合成算法备案（客户时间表）")),
        ("数据出境安全评估/标准合同备案", "个保法§38；数据出境安全评估办法",
         _kw_status(intake, ["跨境", "出境"], "存在缺口：Azure 东亚节点处理语音数据涉及出境，尚未评估（计划 2026-11）")),
        ("未成年人网络保护（模式/防沉迷/监护人同意）", "《未成年人网络保护条例》§38、§42-46；未保法（2024修正）§72、§77",
         _kw_status(intake, ["未成年"], "存在缺口：已发现未成年人借用家长身份证绕过实名认证，未设未成年人模式")),
        ("违法内容处置与投诉举报机制", "暂行办法§14、§15；网安法（2025修正）§49、§69",
         _kw_status(intake, ["人工", "干预", "投诉"], "已有机制：机审+高风险人工二审、自伤自杀危机干预、48h 投诉复核")),
        ("供应商数据处理与训练权利约束", "个保法§21；暂行办法§19",
         _kw_status(intake, ["训练", "供应商"], "存在缺口：讯飞保留 API 数据用于模型优化权利，无企业级数据隔离条款")),
        ("个人信息删除/注销（多供应商全链路）", "个保法§47",
         _kw_status(intake, ["删除", "注销"], "存在缺口：多供应商架构下无统一退出删除 SOP，30 天删除无验证机制")),
        ("死者个人信息处置规则", "个保法§49；民法典§994",
         _kw_status(intake, ["死亡"], "存在缺口：已有用户询问数据继承/删除规则，当前无政策")),
    ]
    rows_oblig = "\n".join(
        f"<tr><td>{name}</td><td>{law}</td><td>{status}</td></tr>" for name, law, status in obligations
    )

    # ---------- 风险事件（RF-02 拆分） ----------
    events = []
    if intake:
        raw = intake.get("answers", {}).get("RF-02", {}).get("answer", "")
        for line in [x.strip() for x in raw.split("；") if x.strip()]:
            events.append(f"<tr><td>{line}</td></tr>")
    rows_events = "\n".join(events) or "<tr><td>待补充</td></tr>"

    # ---------- 行动建议（对照 RF-03 时间表） ----------
    actions = [
        ("完成深度合成内容标识改造（显式+隐式），覆盖语音/形象/视频全形态", "深度合成规定§16、§17；标识办法", "公测前", "高"),
        ("语音/形象数据单独同意整改，修订注册协议与隐私政策", "个保法§28、§29；深度合成规定§14②", "公测前", "高"),
        ("完成深度合成算法备案并公示备案编号", "暂行办法§17；深度合成规定§19", "2026-09（客户计划）", "高"),
        ("供应商合同补充：数据隔离、禁止训练、退出删除验证与审计权", "个保法§21、§47", "公测前", "高"),
        ("未成年人识别加固（防借用身份）+ 未成年人模式与消费限制", "未保条例§42-46；未保法§72", "公测前", "高"),
        ("通过等保 2.0 三级测评", "网安法（2025修正）§23", "2026-10（客户计划）", "中"),
        ("完成数据出境安全评估/标准合同备案（Azure TTS 部分）", "个保法§38", "2026-11（客户计划）", "高"),
        ("建立注销/死亡数据处置 SOP（含多供应商删除验证）", "个保法§47、§49", "公测前", "中"),
    ]
    rows_action = "\n".join(
        f"<tr><td>{act}</td><td>{law}</td><td>{when}</td><td>{prio}</td></tr>" for act, law, when, prio in actions
    )

    fact_rows = [
        ("产品形态", bb01), ("AI 与人工分工", bb02), ("用户画像与规模", bb03), ("适用地区与跨境", bb04),
        ("数据来源与用途", ds01), ("授权链状态", ds02), ("数据类型分级", ds03),
        ("模型/API 清单", ms01), ("部署方式", ms02), ("供应商安全条款", ms03), ("供应商退出机制", ms04),
        ("核心合规风险（客户申报）", rf01), ("已发生风险事件", rf02), ("上线时间表", rf03),
    ]
    rows_fact = "\n".join(
        f"<tr><td style='white-space:nowrap;font-weight:600'>{k}</td><td>{v}</td></tr>" for k, v in fact_rows
    )

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{meta.get('title','AI数据合规评估')}</title>
<style>
body{{font-family:-apple-system,"PingFang SC",sans-serif;margin:0;background:#f6f8fa;color:#1a2b3c}}
header{{background:#173851;color:#fff;padding:28px 40px}}
header h1{{margin:0 0 8px;font-size:24px;line-height:1.35}}header p{{margin:2px 0;color:#a8c3d8;font-size:13px}}
main{{padding:28px 40px;max-width:1200px;margin:0 auto}}
section{{background:#fff;border-radius:12px;padding:20px 24px;margin:16px 0;box-shadow:0 1px 4px rgba(23,56,81,.08)}}
h2{{font-size:17px;color:#173851;border-left:4px solid #0e7490;padding-left:10px;margin:0 0 12px}}
h3{{font-size:14px;color:#0e7490;margin:18px 0 8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th{{background:#eef4f7;text-align:left;padding:8px;border:1px solid #d3dee5}}td{{padding:8px;border:1px solid #d3dee5;vertical-align:top;line-height:1.55}}
.badge{{display:inline-block;background:#fff2df;color:#8a5a00;border-radius:6px;padding:2px 10px;font-size:12px}}
.gap{{background:#fdf2f2;color:#a23b36;font-weight:600}} .ok{{background:#eef7ee;color:#2e7d32;font-weight:600}}
footer{{padding:16px 40px;color:#64798c;font-size:12px}}
</style></head><body>
<header><h1>{meta.get('title','AI数据合规评估报告')}</h1><p>{industry} · 版本 {meta.get('version','')}</p><p><span class="badge" style="background:#fde8e8;color:#a23b36">候选版／需律师确认</span> {meta.get('legalBoundary','')}</p></header>
<main>
<section><h2>一、业务与产品全景</h2>
<p style="font-size:13px;color:#64798c;margin:0 0 8px">以下事实来自 intake 客户陈述，正式引用前需经律师与客户核实。</p>
<table><tr><th style="width:140px">维度</th><th>内容</th></tr>{rows_fact}</table></section>
<section><h2>二、重点合规义务核对</h2>
<p style="font-size:13px;color:#64798c;margin:0 0 8px">法规为元典核验过的现行有效条款（2026-08-20）；对照结论由 intake 陈述归纳，标"待核实"项进企调研时优先核查。</p>
<table><tr><th style="width:170px">合规义务</th><th>法律依据</th><th style="width:280px">本项目对照（intake 归纳）</th></tr>{rows_oblig}</table></section>
<section><h2>三、核心合规风险分析</h2>
<h3>3.1 客户申报风险（RF-01）</h3>
<p style="font-size:13px;color:#1a2b3c;line-height:1.8">{rf01}</p>
<h3>3.2 模型风险清单</h3>
<table><tr><th>编号</th><th>风险主题</th><th>描述</th></tr>{rows_risk}</table></section>
<section><h2>四、合规差距与行动建议</h2>
<p style="font-size:13px;color:#64798c;margin:0 0 8px">时间节点引用客户 RF-03 上线计划；所有动作完成前保持候选状态。</p>
<table><tr><th>行动</th><th>依据</th><th>建议时间</th><th>优先级</th></tr>{rows_action}</table></section>
<section><h2>五、已发生风险事件（RF-02）</h2>
<table><tr><th>事件（客户陈述）</th></tr>{rows_events}</table></section>
<section><h2>六、待核验事项（进企调研前）</h2>
<table><tr><th>编号</th><th>问题</th><th>对象</th></tr>{rows_verify}</table></section>
</main><footer>本报告为候选评估材料，未经律师复核不得作为正式法律意见；法规版本及适用性待专项校验。风险/事件/时间表述均来自客户 intake 陈述。</footer>
</body></html>"""


def field_pack_command(args) -> None:
    """第四步：以手册为指引生成进企调研前全套文件（调研表/风险识别表/访谈提纲/文件清单）。"""
    import csv as csv_module
    target = args.target.resolve()
    root = find_knowledge_base_root()
    handbook_dir = root / "ai/work/practice_knowledge_base/04_handbook_structured"
    survey_path = handbook_dir / "survey_items.csv"
    indicators_path = handbook_dir / "evaluation_indicators.csv"
    if not survey_path.exists() or not indicators_path.exists():
        raise FlowError(f"手册结构化数据缺失：{handbook_dir}", 2)
    # 读取手册 CSV
    def read_handbook_csv(path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8-sig") as handle:
            return list(csv_module.DictReader(handle))
    handbook = {
        "survey_items": read_handbook_csv(survey_path),
        "evaluation_indicators": read_handbook_csv(indicators_path),
    }
    from word_builder import build_field_pack
    import shutil as shutil_module
    project = {"project_id": "FIELD-PACK", "project_name": args.project_name or "AI数据合规项目"}
    out = workspace(target) / "06_field_pack"
    if out.exists():
        shutil_module.rmtree(out)
    # 注入模型（risks/verificationItems → 访谈提纲重点核查问题段）与 intake（适用性裁剪/领域扩充）
    model_path = workspace(target) / "05_model/industry-model.json"
    model = read_json(model_path) if model_path.exists() else None
    intake_path = workspace(target) / "00_project/intake.json"
    intake = read_json(intake_path) if intake_path.exists() else None
    docs = build_field_pack(project, handbook, out, model=model, intake=intake)
    # 最终成果聚合：7 份 Word → 07_final_deliverables/
    final_dir = workspace(target) / "07_final_deliverables"
    final_dir.mkdir(parents=True, exist_ok=True)
    final_docs = []
    for doc_path in docs:
        dest = final_dir / doc_path.name
        shutil_module.copy2(doc_path, dest)
        final_docs.append(dest)
    emit({
        "command": "field-pack",
        "documents": [relative_to_target(p, target) for p in docs],
        "final_deliverables": [relative_to_target(p, target) for p in final_docs],
        "survey_items": len(handbook["survey_items"]),
        "evaluation_indicators": len(handbook["evaluation_indicators"]),
        "next": "进企调研前文件包已生成（最终成果已聚合至 07_final_deliverables/）；可结合模型 verificationItems 开展实地调研",
    })


def _extract_view_svg(html_path: Path) -> str:
    """从 diagram-design 视图 HTML 提取 <svg>，将 class 样式内联化，供全景页嵌入。

    视图 HTML 的 SVG 依赖自身 <style>（含 :root 变量与 .class 规则），直接内嵌会与
    全景页样式冲突。做法：解析 :root 变量并替换 var(--x)，再把每个元素的 class 规则
    合并为 style 属性（按 CSS 定义顺序，后者覆盖前者）。
    """
    import re as re_module
    html = html_path.read_text(encoding="utf-8")
    style_m = re_module.search(r"<style>(.*?)</style>", html, re_module.S)
    css = style_m.group(1) if style_m else ""
    svg_m = re_module.search(r"<svg.*?</svg>", html, re_module.S)
    if not svg_m:
        raise FlowError(f"视图 HTML 缺少 <svg>：{html_path}", 5)
    svg = svg_m.group(0)
    # 1) :root 变量
    root_vars = {}
    for m in re_module.finditer(r"--([a-z0-9-]+)\s*:\s*([^;]+);", css):
        root_vars[m.group(1)] = m.group(2).strip()
    # 2) class 规则（跳过 @media / 伪类 / 元素选择器），保持定义顺序
    rules = []  # [(class_name, declarations)]
    for m in re_module.finditer(r"([^{}]+)\{([^{}]*)\}", css, re_module.S):
        selector, decl = m.group(1).strip(), m.group(2).strip()
        if selector.startswith("@") or not decl:
            continue
        for one in selector.split(","):
            one = one.strip()
            if one.startswith(".") and " " not in one and ":" not in one and one[1:]:
                rules.append((one[1:], decl))
    # 3) class → style 内联（var() 替换为实际值）
    def inline(m):
        cls_names = m.group(1).split()
        decls = [d for name, d in rules if name in cls_names]
        if not decls:
            return ""
        style = "; ".join(decls)
        style = re_module.sub(r"var\(--([a-z0-9-]+)\)", lambda mm: root_vars.get(mm.group(1), ""), style)
        return f' style="{style}"'
    return re_module.sub(r' class="([^"]+)"', inline, svg)


def _build_deliverable_html(model: dict, process_html_path: Path, dataflow_html_path: Path, report_path: Path) -> str:
    """合并三层流程图 + 数据流图 + 评估报告 为单个自包含 HTML（页签切换）。"""
    process_svg = _extract_view_svg(process_html_path)
    dataflow_svg = _extract_view_svg(dataflow_html_path)
    report_html = report_path.read_text(encoding="utf-8")
    # 抽取报告 body 内容（去掉外层 html/head/body）
    report_body = report_html
    for marker in ("<body>", "</body>", "<html>", "</html>", "<!doctype html>"):
        report_body = report_body.replace(marker, "")
    meta = model.get("meta", {})
    industry = meta.get("industry", "AI产业")
    title = meta.get("title", "AI数据合规全景交付")
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<style>
body{{font-family:-apple-system,"PingFang SC",sans-serif;margin:0;background:#f6f8fa;color:#1a2b3c}}
header{{background:#173851;color:#fff;padding:24px 32px}}
header h1{{margin:0 0 6px;font-size:24px}}header p{{margin:2px 0;color:#a8c3d8;font-size:13px}}
nav.tabs{{background:#0e7490;display:flex;padding:0 32px}}
nav.tabs button{{background:transparent;border:none;color:#cde8f0;padding:12px 20px;font-size:14px;cursor:pointer;border-bottom:3px solid transparent}}
nav.tabs button.active{{color:#fff;border-bottom-color:#fff;font-weight:700}}
main{{padding:20px 32px}}
.view{{display:none}}.view.active{{display:block}}
.view svg{{max-width:100%;height:auto;background:#fff;border-radius:12px;box-shadow:0 1px 6px rgba(23,56,81,.1)}}
.scroll-wrap{{overflow-x:auto;border-radius:12px}}
footer{{padding:16px 32px;color:#64798c;font-size:12px}}
section{{background:#fff;border-radius:12px;padding:18px 22px;margin:14px 0;box-shadow:0 1px 4px rgba(23,56,81,.08)}}
h2{{font-size:18px;color:#173851;border-left:4px solid #0e7490;padding-left:10px;margin-top:0}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th{{background:#eef4f7;text-align:left;padding:8px;border:1px solid #d3dee5}}td{{padding:8px;border:1px solid #d3dee5;vertical-align:top}}
.badge{{display:inline-block;background:#fff2df;color:#8a5a00;border-radius:6px;padding:2px 10px;font-size:12px}}
</style></head><body>
<header><h1>{title}</h1><p>{industry} · 版本 {meta.get('version','')} · 候选版／需律师确认</p><p><span class="badge" style="background:#fde8e8;color:#a23b36">候选版</span> {meta.get('legalBoundary','')}</p></header>
<nav class="tabs"><button class="active" onclick="showView('process')">三层流程图</button><button onclick="showView('dataflow')">数据流向图</button><button onclick="showView('report')">评估报告</button></nav>
<main>
<div id="view-process" class="view active"><div class="scroll-wrap">{process_svg}</div></div>
<div id="view-dataflow" class="view"><div class="scroll-wrap">{dataflow_svg}</div></div>
<div id="view-report" class="view">{report_body}</div>
</main>
<footer>本交付为 AI 数据合规冷启动候选材料；未经律师复核不得作为正式法律意见。法规版本及适用性待专项校验。</footer>
<script>
function showView(name) {{
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body></html>"""


def migrate_project(target: Path, *, dry_run: bool = False) -> dict:
    """版本迁移：检测旧项目 → 预检 → 备份 → 差异展示 → 迁移。禁止跨版本静默改写。"""
    target = target.resolve()
    ws = workspace(target)
    project_path_file = project_path(target)
    state_path_file = state_path(target)
    if not project_path_file.exists() or not state_path_file.exists():
        raise FlowError("不是有效项目：缺少 project.json 或 state.json", 2)
    project = read_json(project_path_file)
    state = read_json(state_path_file)
    old_skill = state.get("skill_version", "")
    old_schema = project.get("schema_version", "")
    current_skill = SKILL_VERSION
    current_schema = PROJECT_SCHEMA_VERSION
    changes = []
    # 1. skill_version 升级
    if old_skill != current_skill:
        changes.append({"item": "skill_version", "before": old_skill, "after": current_skill})
    # 2. schema_version 对齐
    if old_schema != current_schema:
        changes.append({"item": "schema_version", "before": old_schema, "after": current_schema})
    # 3. SQLite user_version 升级
    db_path = ws / "02_evidence/evidence_hub.sqlite"
    sqlite_before = 0
    sqlite_changed = False
    if db_path.exists():
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            sqlite_before = conn.execute("PRAGMA user_version").fetchone()[0]
        finally:
            conn.close()
        if sqlite_before != SQLITE_SCHEMA_VERSION:
            changes.append({"item": "sqlite_user_version", "before": str(sqlite_before), "after": str(SQLITE_SCHEMA_VERSION)})
            sqlite_changed = True
    # 4. 旧 fact 字段兼容（无 fact_status 的 fact_records.csv）
    fact_path = ws / "02_evidence/fact_records.csv"
    fact_migration = False
    if fact_path.exists():
        facts = read_csv(fact_path)
        if facts and not any("fact_status" in row for row in facts):
            fact_migration = True
            changes.append({"item": "fact_records字段", "before": "confirmation_status(旧)", "after": "fact_status(新)"})
    if not changes:
        return {"command": "migrate", "target": str(target), "current": True, "changes": [], "backup": None, "boundary": "项目已是最新版本，无需迁移。"}
    if dry_run:
        return {"command": "migrate", "target": str(target), "dry_run": True, "current": False, "changes": changes, "backup": None, "boundary": "预检完成；执行 migrate 前将先备份。"}
    # 备份
    backup_dir = ws / "06_validation/migration_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    for source in (project_path_file, state_path_file, db_path if db_path.exists() else None):
        if source:
            shutil.copy2(source, backup_dir / source.name)
    # 执行迁移
    project["schema_version"] = current_schema
    safe_write_json(project_path_file, project, allow_update=True)
    state["skill_version"] = current_skill
    safe_write_json(state_path_file, state, allow_update=True)
    if sqlite_changed:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(f"PRAGMA user_version = {SQLITE_SCHEMA_VERSION}")
            conn.commit()
        finally:
            conn.close()
    if fact_migration:
        facts = read_csv(fact_path)
        for row in facts:
            if "fact_status" not in row:
                row["fact_status"] = "客户已确认" if row.get("confirmation_status") == "已核实" else "未提供"
            if "recheck_status" not in row:
                row["recheck_status"] = "未复评"
            if "confirmation_method" not in row:
                row["confirmation_method"] = ""
        safe_write_csv(fact_path, facts, FACT_FIELDS, allow_update=True)
    return {
        "command": "migrate",
        "target": str(target),
        "current": False,
        "changes": changes,
        "backup": relative_to_target(backup_dir, target),
        "fact_migration": fact_migration,
        "boundary": "迁移已完成；建议运行 validate 确认迁移后产物完整。",
    }


def migrate_command(args) -> None:
    target = args.target.resolve()
    report = migrate_project(target, dry_run=args.dry_run)
    emit(report)


def verify_fact_gate(target: Path, profile: dict) -> dict:
    gate_path = workspace(target) / "04_fact_verification/gate_evidence.json"
    gate = read_json(gate_path)
    gate_fields = gate_fields_for(profile)
    missing = [field for field in gate_fields if gate.get(field) is not True]
    facts = read_csv(workspace(target) / "02_evidence/fact_records.csv")
    # 已确认：状态属于配置的已确认态（默认：客户已确认/律师已复核），且证据编号与确认主体齐备
    confirmed_statuses = {status for status in profile.get("fact_status_values", []) if status in {"客户已确认", "律师已复核"}} or {"客户已确认", "律师已复核"}
    unresolved = [row.get("fact_id", "") for row in facts if row.get("fact_status") not in confirmed_statuses or not row.get("evidence_id") or not row.get("confirmed_by")]
    conflicts = [row.get("fact_id", "") for row in facts if row.get("conflict_status") not in {"无冲突", "已解决"}]
    recheck = [row.get("fact_id", "") for row in facts if row.get("recheck_status") == "变化待复评"]
    if missing or unresolved or conflicts or recheck:
        raise FlowError("事实核验门禁未通过：" + json.dumps({"missing_gate_fields": missing, "unresolved_facts": unresolved, "conflicting_facts": conflicts, "recheck_pending": recheck}, ensure_ascii=False), 3)
    return {"gate_fields": len(gate_fields), "confirmed_facts": len(facts)}


def build_archive(target: Path) -> dict:
    ws = workspace(target)
    archive_dir = ws / f"07_archive/{SKILL_VERSION}"
    bundle = archive_dir / f"AI数据合规候选交付包-{SKILL_VERSION}.zip"
    if bundle.exists():
        return {"archive": relative_to_target(bundle, target), "sha256": sha256(bundle), "reused": True}
    selected: list[Path] = []
    for relative in ("00_project/project.json", "01_baseline/artifact_inventory.csv", "02_evidence", "04_fact_verification/gate_evidence.json", "05_candidate_delivery"):
        path = ws / relative
        if path.is_file():
            selected.append(path)
        elif path.is_dir():
            selected.extend(item for item in path.rglob("*") if item.is_file())
    rows = []
    for path in sorted(set(selected)):
        rows.append({"path": path.relative_to(ws).as_posix(), "sha256": sha256(path), "size": path.stat().st_size})
    archive_dir.mkdir(parents=True, exist_ok=True)
    safe_write_csv(archive_dir / "成果清单.csv", rows, ["path", "sha256", "size"])
    checksum_lines = [f"{row['sha256']}  {row['path']}" for row in rows]
    safe_write_text(archive_dir / "SHA256SUMS.txt", "\n".join(checksum_lines) + "\n")
    zip_files = [(path, path.relative_to(ws).as_posix()) for path in selected]
    zip_files.extend([(archive_dir / "成果清单.csv", f"07_archive/{SKILL_VERSION}/成果清单.csv"), (archive_dir / "SHA256SUMS.txt", f"07_archive/{SKILL_VERSION}/SHA256SUMS.txt")])
    deterministic_zip(bundle, zip_files)
    return {"archive": relative_to_target(bundle, target), "sha256": sha256(bundle), "reused": False}


def execute_phase(target: Path, next_phase: str, project: dict, state: dict) -> dict:
    profile = load_profile(project["profile"])
    outputs = dict(state.get("outputs", {}))
    if next_phase == "baseline_locked":
        result = build_baseline(target, project)
        outputs["baseline"] = result
        state = update_state(target, state, phase=next_phase, baseline_manifest_sha256=result["sha256"], outputs=outputs)
    elif next_phase == "evidence_ready":
        result = build_evidence(target, project, profile)
        outputs["evidence"] = result
        state = update_state(target, state, phase=next_phase, outputs=outputs)
    elif next_phase == "startup_pack_ready":
        out = workspace(target) / "03_client_start/Word公文包"
        docs = build_startup_pack(project, profile, out)
        outputs["startup_pack"] = {"documents": len(docs), "zip": "03_client_start/客户启动Word公文包.zip"}
        state = update_state(target, state, phase=next_phase, outputs=outputs)
    elif next_phase == "facts_verified":
        result = verify_fact_gate(target, profile)
        outputs["fact_gate"] = result
        state = update_state(target, state, phase=next_phase, customer_fact_status="已核实", outputs=outputs)
    elif next_phase == "candidate_ready":
        records = load_records(target)
        out = workspace(target) / "05_candidate_delivery/Word候选包"
        docs = build_candidate_pack(project, profile, records, out)
        outputs["candidate_pack"] = {"documents": len(docs), "zip": "05_candidate_delivery/AI数据合规候选交付Word包.zip"}
        state = update_state(target, state, phase=next_phase, outputs=outputs)
    elif next_phase == "validated_archived":
        from validator import validate_project
        report = validate_project(target, write_report=True, minimum_phase="candidate_ready")
        if not report["passed"]:
            raise FlowError("独立验收失败，禁止归档", 5)
        archive = build_archive(target)
        outputs["archive"] = archive
        state = update_state(target, state, phase=next_phase, last_validation="DOMAIN_VERIFIED", outputs=outputs)
    else:
        raise FlowError(f"不支持阶段：{next_phase}", 2)
    return state


def advance(args) -> None:
    target = args.target.resolve()
    project = load_project(target)
    state = load_state(target)
    target_index = PHASE_INDEX[args.to]
    current_index = PHASE_INDEX[state["phase"]]
    if target_index < current_index:
        raise FlowError("禁止回退项目阶段；请创建新版本", 3)
    if args.dry_run:
        emit({"dry_run": True, "current": state["phase"], "target": args.to, "steps": PHASES[current_index + 1:target_index + 1]})
        return
    if target_index == current_index:
        emit({"phase": state["phase"], "changed": False, "message": "项目已处于该阶段或更高阶段"})
        return
    for next_phase in PHASES[current_index + 1:target_index + 1]:
        state = execute_phase(target, next_phase, project, state)
    emit({"phase": state["phase"], "changed": True, "outputs": state.get("outputs", {})})


def status(args) -> None:
    target = args.target.resolve()
    project = load_project(target)
    state = load_state(target)
    index = PHASE_INDEX[state["phase"]]
    next_phase = PHASES[index + 1] if index + 1 < len(PHASES) else None
    next_action = {
        "initialized": "核对输入资料并推进baseline_locked",
        "baseline_locked": "构建证据中台",
        "evidence_ready": "生成客户启动Word包",
        "startup_pack_ready": "收集并确认客户事实，完成事实门禁",
        "facts_verified": "生成候选交付包",
        "candidate_ready": "运行独立验收并归档",
        "validated_archived": "根据项目变化触发新版本复评",
    }[state["phase"]]
    emit({"project_id": project["project_id"], "project_name": project["project_name"], "profile": project["profile"], "phase": state["phase"], "next_phase": next_phase, "next_action": next_action, "customer_fact_status": state["customer_fact_status"], "lawyer_review_status": state["lawyer_review_status"], "last_validation": state.get("last_validation", "NOT_VERIFIED")})


def validate_command(args) -> None:
    if args.dry_run:
        emit({"dry_run": True, "command": "validate", "target": str(args.target.resolve()), "writes": "06_validation/domain_validation.*"})
        return
    from validator import validate_project
    report = validate_project(args.target.resolve(), write_report=True)
    emit(report)
    if not report["passed"]:
        raise FlowError("独立验收失败", 5)


def package_command(args) -> None:
    target = args.target.resolve()
    state = load_state(target)
    if not phase_at_least(state, "candidate_ready"):
        raise FlowError("尚未形成候选交付包，禁止封包", 3)
    if args.dry_run:
        emit({"dry_run": True, "command": "package", "target": str(target), "output": f"ai_compliance/07_archive/{SKILL_VERSION}"})
        return
    from validator import validate_project
    report = validate_project(target, write_report=True, minimum_phase="candidate_ready")
    if not report["passed"]:
        raise FlowError("独立验收失败，禁止封包", 5)
    emit(build_archive(target))


def list_profiles() -> list[str]:
    from common import PROFILES
    return sorted(path.stem for path in PROFILES.glob("*.json") if path.is_file())


def add_common_creation(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--profile", required=True, help=f"场景配置标识（当前可用：{', '.join(list_profiles())}）")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--use-case", required=True)
    parser.add_argument("--jurisdiction", default="中国大陆")
    parser.add_argument("--dry-run", action="store_true")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="AI数据合规冷启动项目状态机")
    sub = root.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init")
    add_common_creation(init_parser)
    init_parser.set_defaults(handler=lambda args: initialize(args, "init"))
    adopt_parser = sub.add_parser("adopt")
    add_common_creation(adopt_parser)
    adopt_parser.set_defaults(handler=lambda args: initialize(args, "adopt"))
    preflight_parser = sub.add_parser("preflight")
    add_common_creation(preflight_parser)
    preflight_parser.set_defaults(handler=preflight)
    advance_parser = sub.add_parser("advance")
    advance_parser.add_argument("--target", type=Path, required=True)
    advance_parser.add_argument("--to", choices=PHASES, required=True)
    advance_parser.add_argument("--dry-run", action="store_true")
    advance_parser.set_defaults(handler=advance)
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--target", type=Path, required=True)
    status_parser.set_defaults(handler=status)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--target", type=Path, required=True)
    validate_parser.add_argument("--dry-run", action="store_true")
    validate_parser.set_defaults(handler=validate_command)
    package_parser = sub.add_parser("package")
    package_parser.add_argument("--target", type=Path, required=True)
    package_parser.add_argument("--dry-run", action="store_true")
    package_parser.set_defaults(handler=package_command)
    validate_config_parser = sub.add_parser("validate-config")
    validate_config_parser.add_argument("--profile", required=True, help="场景配置标识（如 bci-medical-ai）")
    validate_config_parser.set_defaults(handler=validate_config_command)
    law_update_parser = sub.add_parser("law-update")
    law_update_parser.add_argument("--target", type=Path, required=True)
    law_update_parser.add_argument("--source-file", type=Path, required=True, help="本地受控法源CSV（source_id,title,version,effect_status,change_type,verification_date,note）")
    law_update_parser.set_defaults(handler=law_update_command)
    migrate_parser = sub.add_parser("migrate")
    migrate_parser.add_argument("--target", type=Path, required=True)
    migrate_parser.add_argument("--dry-run", action="store_true", help="只检测并展示差异，不执行迁移")
    migrate_parser.set_defaults(handler=migrate_command)
    intake_parser = sub.add_parser("intake")
    intake_parser.add_argument("--target", type=Path, required=True)
    intake_parser.add_argument("--question-set", default="generic", help="问题集标识（generic 或 assets/intake-questions/ 下的产业专属文件）")
    intake_parser.add_argument("--project-id", required=True)
    intake_parser.add_argument("--force", action="store_true", help="强制重建骨架（清空已有答案；默认已存在时不重建）")
    intake_parser.set_defaults(handler=intake_command)
    intake_record_parser = sub.add_parser("intake-record")
    intake_record_parser.add_argument("--target", type=Path, required=True)
    intake_record_parser.add_argument("--question-id", required=True, help="问题标识（如 BB-01）")
    intake_record_parser.add_argument("--answer", required=True, help="律师回答内容")
    intake_record_parser.set_defaults(handler=intake_record_command)
    intake_close_parser = sub.add_parser("intake-close")
    intake_close_parser.add_argument("--target", type=Path, required=True)
    intake_close_parser.add_argument("--force", action="store_true", help="忽略缺失问题强制收口")
    intake_close_parser.set_defaults(handler=intake_close_command)
    kb_build_parser = sub.add_parser("kb-build")
    kb_build_parser.add_argument("--target", type=Path, required=True)
    kb_build_parser.add_argument("--keywords", default="", help="补充关键词（逗号分隔），默认从 intake 回答提取")
    kb_build_parser.set_defaults(handler=kb_build_command)
    kb_add_parser = sub.add_parser("kb-add")
    kb_add_parser.add_argument("--target", type=Path, required=True)
    kb_add_parser.add_argument("--collection", required=True, help="论文库/实务文章库/法律法规库")
    kb_add_parser.add_argument("--source", type=Path, required=True, help="知识库根目录内的资料路径")
    kb_add_parser.set_defaults(handler=kb_add_command)
    model_generate_parser = sub.add_parser("model-generate")
    model_generate_parser.add_argument("--target", type=Path, required=True)
    model_generate_parser.add_argument("--data-types", default="", help="补充数据类型（逗号分隔），缺省从 intake 数据回答提取")
    model_generate_parser.set_defaults(handler=model_generate_command)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--target", type=Path, required=True)
    render_parser.set_defaults(handler=render_command)
    field_pack_parser = sub.add_parser("field-pack")
    field_pack_parser.add_argument("--target", type=Path, required=True)
    field_pack_parser.add_argument("--project-name", default="AI数据合规项目")
    field_pack_parser.set_defaults(handler=field_pack_command)
    return root


def validate_config_command(args) -> None:
    from validate_config import validate_profile
    from common import PROFILES
    profile = read_json(PROFILES / f"{args.profile}.json")
    report = validate_profile(profile, args.profile)
    emit(report)
    raise SystemExit(0 if report["passed"] else 5)


def main() -> None:
    args = parser().parse_args()
    try:
        args.handler(args)
    except FlowError as exc:
        emit({"error": str(exc), "code": exc.code})
        raise SystemExit(exc.code)


if __name__ == "__main__":
    main()
