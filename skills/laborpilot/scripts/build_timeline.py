#!/usr/bin/env python3
"""把经标注事实和材料中的日期句转为可追溯案件时间轴。

自动从材料文字中提取的内容一律标记为 ``to_verify``，不会因为某句话
出现在文件中就冒充已证事实。``supported`` 只能由显式输入提供，且必须
关联已经登记的材料 ID。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from case_state import FACT_CONFLICT_STATUSES, FACT_STATUSES, read_json, validate_state, write_state


DATE_PATTERNS = (
    re.compile(r"(?P<year>19\d{2}|20\d{2})[年./-](?P<month>0?[1-9]|1[0-2])[月./-](?P<day>0?[1-9]|[12]\d|3[01])日?"),
    re.compile(r"(?P<year>19\d{2}|20\d{2})年(?P<month>0?[1-9]|1[0-2])月"),
    re.compile(r"(?P<year>19\d{2}|20\d{2})年"),
)
ID_PATTERN = re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)")
PHONE_PATTERN = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
SAFE_FACT_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
SUPPORTED_EXTRACTION_METHODS = {"explicit_reviewed_input", "date_sentence"}
MAX_SENTENCE_BUFFER_CHARS = 1024 * 1024


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def casework_root(state_path: Path) -> Path:
    return state_path.parent if state_path.parent.name == ".casework" else state_path.parent / ".casework"


def sanitize_statement(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = ID_PATTERN.sub("【身份证号已隐去】", text)
    text = PHONE_PATTERN.sub("【手机号已隐去】", text)
    if len(text) > 500:
        text = text[:497].rstrip() + "…"
    return text


def normalize_date(value: Any) -> tuple[str | None, str]:
    if value is None or value == "":
        return None, "unknown"
    text = str(value).strip()
    exact = re.fullmatch(r"(19\d{2}|20\d{2})-(\d{2})-(\d{2})", text)
    if exact:
        try:
            return date.fromisoformat(text).isoformat(), "day"
        except ValueError:
            fail(f"无效事实日期：{text}")
    month = re.fullmatch(r"(19\d{2}|20\d{2})-(\d{2})", text)
    if month and 1 <= int(month.group(2)) <= 12:
        return text, "month"
    year = re.fullmatch(r"(19\d{2}|20\d{2})", text)
    if year:
        return text, "year"
    for pattern in DATE_PATTERNS:
        match = pattern.fullmatch(text)
        if not match:
            continue
        groups = match.groupdict()
        y = int(groups["year"])
        m = int(groups["month"]) if groups.get("month") else None
        d = int(groups["day"]) if groups.get("day") else None
        if d is not None and m is not None:
            try:
                return date(y, m, d).isoformat(), "day"
            except ValueError:
                fail(f"无效事实日期：{text}")
        if m is not None:
            return f"{y:04d}-{m:02d}", "month"
        return f"{y:04d}", "year"
    fail(f"事实日期必须为 YYYY、YYYY-MM、YYYY-MM-DD 或对应中文日期：{text}")


def first_date_in_text(text: str) -> tuple[str | None, str]:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return normalize_date(match.group(0))
    return None, "unknown"


def sentence_candidates_from_path(path: Path):
    """以有界缓冲区逐段读取派生文本，避免大文件整体进入内存。"""
    buffer = ""
    with path.open("r", encoding="utf-8") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            buffer += chunk.replace("\r\n", "\n").replace("\r", "\n")
            parts = re.split(r"(?<=[。！？；])|\n+", buffer)
            buffer = parts.pop() if parts else ""
            for part in parts:
                if part.strip():
                    yield part.strip()
            while len(buffer) > MAX_SENTENCE_BUFFER_CHARS:
                segment, buffer = buffer[:MAX_SENTENCE_BUFFER_CHARS], buffer[MAX_SENTENCE_BUFFER_CHARS:]
                if segment.strip():
                    yield segment.strip()
    if buffer.strip():
        yield buffer.strip()


def load_explicit_facts(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"事实输入不存在：{path}")
    except json.JSONDecodeError as exc:
        fail(f"事实输入不是合法 JSON：{path}：{exc}")
    facts = payload.get("facts") if isinstance(payload, dict) else payload
    if not isinstance(facts, list):
        fail("事实输入必须是数组，或含 facts 数组的 JSON object。")
    return facts


def extracted_facts(
    materials: list[dict[str, Any]],
    limit: int,
    *,
    allowed_root: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    allowed_root = allowed_root.resolve()
    for material in materials:
        if not isinstance(material, dict):
            continue
        derivative = material.get("derivative_path")
        if not isinstance(derivative, str) or not derivative:
            continue
        path = Path(derivative).expanduser().resolve()
        if not path.is_relative_to(allowed_root):
            fail(f"拒绝读取 .casework/materials 之外的派生文本：{path}")
        if not path.is_file():
            continue
        try:
            for sentence in sentence_candidates_from_path(path):
                occurred_on, precision = first_date_in_text(sentence)
                if occurred_on is None:
                    continue
                statement = sanitize_statement(sentence)
                if len(statement) < 6:
                    continue
                results.append({
                    "statement": statement,
                    "status": "to_verify",
                    "sources": [material.get("material_id")],
                    "occurred_on": occurred_on,
                    "date_precision": precision,
                    "extraction_method": "date_sentence",
                    "source_locators": [{
                        "material_id": material.get("material_id"),
                        "derivative_path": str(path),
                    }],
                })
                if len(results) >= limit:
                    return results
        except (OSError, UnicodeDecodeError):
            continue
    return results


def normalize_fact(
    candidate: Any,
    material_ids: set[str],
    *,
    actor: str,
) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        fail(f"事实候选必须是 object：{candidate}")
    statement = sanitize_statement(candidate.get("statement"))
    if len(statement) < 4:
        fail("事实陈述过短或为空。")
    status = candidate.get("status")
    if status not in FACT_STATUSES:
        fail(f"事实状态无效：{status}")
    sources = candidate.get("sources", [])
    if not isinstance(sources, list) or not all(isinstance(item, str) and item for item in sources):
        fail(f"事实 sources 必须是材料 ID 字符串数组：{statement}")
    sources = list(dict.fromkeys(sources))
    missing = sorted(set(sources) - material_ids)
    if missing:
        fail(f"事实引用未登记材料：{', '.join(missing)}")
    if status == "supported" and not sources:
        fail(f"supported 事实必须关联材料来源：{statement}")
    occurred_on, precision = normalize_date(candidate.get("occurred_on"))
    supplied_precision = candidate.get("date_precision")
    if supplied_precision is not None and supplied_precision != precision:
        fail(f"事实日期精度与 occurred_on 不一致：{statement}")
    source_locators = candidate.get("source_locators", [])
    if not isinstance(source_locators, list):
        fail(f"事实 source_locators 必须是数组：{statement}")
    normalized_locators = []
    for locator in source_locators:
        if not isinstance(locator, dict):
            fail(f"事实 source_locators 只能包含 object：{statement}")
        locator_material_id = locator.get("material_id")
        if locator_material_id not in sources:
            fail(f"事实定位信息引用了 sources 之外的材料：{statement}")
        normalized_locators.append(dict(locator))
    extraction_method = candidate.get("extraction_method", "explicit_reviewed_input")
    if extraction_method not in SUPPORTED_EXTRACTION_METHODS:
        fail(f"不支持的事实提取方式：{extraction_method}")
    if extraction_method == "date_sentence" and status != "to_verify":
        fail("自动日期句只能标记为 to_verify。")
    conflict_fields = {
        "conflicts_with_fact_ids", "conflict_status",
        "conflict_explanation", "conflict_next_action",
    }
    conflict_fields_supplied = any(field in candidate for field in conflict_fields)
    conflict_refs = candidate.get("conflicts_with_fact_ids", [])
    if not isinstance(conflict_refs, list) or not all(
        isinstance(item, str) and SAFE_FACT_ID.fullmatch(item) for item in conflict_refs
    ):
        fail(f"事实 conflicts_with_fact_ids 必须是安全事实 ID 数组：{statement}")
    conflict_refs = list(dict.fromkeys(conflict_refs))
    conflict_status = candidate.get("conflict_status", "none" if not conflict_refs else None)
    if not isinstance(conflict_status, str) or conflict_status not in FACT_CONFLICT_STATUSES:
        fail(f"事实 conflict_status 无效：{statement}")
    conflict_explanation = candidate.get("conflict_explanation")
    if conflict_explanation is not None:
        conflict_explanation = sanitize_statement(conflict_explanation)
    conflict_next_action = candidate.get("conflict_next_action")
    if conflict_next_action is not None:
        conflict_next_action = sanitize_statement(conflict_next_action)
    identity_payload = json.dumps(
        {"statement": statement, "occurred_on": occurred_on},
        ensure_ascii=False,
        sort_keys=True,
    )
    fact_id = candidate.get("fact_id") or f"fact-{hashlib.sha256(identity_payload.encode('utf-8')).hexdigest()[:16]}"
    if not isinstance(fact_id, str) or not SAFE_FACT_ID.fullmatch(fact_id):
        fail(f"事实 ID 含不安全字符或过长：{fact_id}")
    return {
        "fact_id": fact_id,
        "statement": statement,
        "status": status,
        "sources": sources,
        "source_locators": normalized_locators,
        "occurred_on": occurred_on,
        "date_precision": precision,
        "extraction_method": extraction_method,
        "conflicts_with_fact_ids": conflict_refs,
        "conflict_status": conflict_status,
        "conflict_explanation": conflict_explanation,
        "conflict_next_action": conflict_next_action,
        "created_by": actor,
        "created_at": now_iso(),
        "_fact_id_supplied": bool(candidate.get("fact_id")),
        "_conflict_fields_supplied": conflict_fields_supplied,
    }


def semantic_fact_key(fact: dict[str, Any]) -> tuple[str, str | None]:
    return str(fact.get("statement", "")), fact.get("occurred_on")


def fact_sort_key(fact: dict[str, Any]) -> tuple[str, str]:
    value = fact.get("occurred_on")
    return (str(value) if value else "9999-99-99", str(fact.get("fact_id", "")))


def render_timeline(facts: list[dict[str, Any]], case_id: str, generated_at: str) -> tuple[str, str]:
    ordered = sorted(facts, key=fact_sort_key)
    counts = Counter(str(item.get("status")) for item in ordered)
    payload = {
        "case_id": case_id,
        "generated_at": generated_at,
        "fact_count": len(ordered),
        "status_counts": dict(sorted(counts.items())),
        "facts": ordered,
    }
    markdown = [
        "# 案件事实与时间轴", "", f"> 生成时间：{generated_at}", "",
        "> 自动提取的日期句均标记为“待核实”，不得直接作为已证事实。", "",
        "| 日期 | 状态 | 事实陈述 | 来源材料 | 冲突状态 | 冲突事实 |",
        "|---|---|---|---|---|---|",
    ]
    for item in ordered:
        statement = str(item.get("statement", "")).replace("|", "\\|").replace("\n", " ")
        markdown.append(
            f"| {item.get('occurred_on') or '日期待核实'} | {item.get('status', '')} | "
            f"{statement} | {'、'.join(item.get('sources', [])) or '无'} | "
            f"{item.get('conflict_status') or 'none'} | "
            f"{'、'.join(item.get('conflicts_with_fact_ids', [])) or '无'} |"
        )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(markdown) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 事实分层与时间轴执行器")
    parser.add_argument("--state", required=True)
    parser.add_argument("--input", help="显式标注的事实 JSON")
    parser.add_argument("--extract-from-materials", action="store_true", help="从派生文本提取含日期的待核实事实")
    parser.add_argument("--max-extracted", type=int, default=200)
    parser.add_argument("--actor", default="labor-case-intake")
    args = parser.parse_args()
    if not args.input and not args.extract_from_materials:
        fail("必须提供 --input 或 --extract-from-materials。")
    if args.max_extracted < 1 or args.max_extracted > 1000:
        fail("--max-extracted 必须在 1—1000 之间。")

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    if state.get("current_node") != "intake":
        fail(f"当前节点为 {state.get('current_node')}，不能生成案件时间轴。")
    materials = state.get("materials", [])
    material_ids = {
        item.get("material_id") for item in materials
        if isinstance(item, dict) and isinstance(item.get("material_id"), str)
    }

    candidates: list[dict[str, Any]] = []
    if args.input:
        candidates.extend(load_explicit_facts(Path(args.input).expanduser().resolve()))
    if args.extract_from_materials:
        candidates.extend(extracted_facts(
            materials,
            args.max_extracted,
            allowed_root=casework_root(state_path) / "materials",
        ))
    if len(candidates) > 1000:
        fail("单次事实候选不得超过 1000 条，请分批复核后接入。")
    normalized = [normalize_fact(item, material_ids, actor=args.actor) for item in candidates]

    candidate_state = json.loads(json.dumps(state, ensure_ascii=False))
    known_by_id = {
        item.get("fact_id"): (index, item)
        for index, item in enumerate(candidate_state.get("facts", []))
        if isinstance(item, dict) and item.get("fact_id")
    }
    known_by_semantics = {
        semantic_fact_key(item): (index, item)
        for index, item in enumerate(candidate_state.get("facts", []))
        if isinstance(item, dict) and item.get("fact_id")
    }
    added = []
    updated = []
    for fact in normalized:
        fact_id_supplied = fact.pop("_fact_id_supplied")
        conflict_fields_supplied = fact.pop("_conflict_fields_supplied")
        existing_entry = known_by_id.get(fact["fact_id"])
        semantic_entry = known_by_semantics.get(semantic_fact_key(fact))
        if existing_entry is None and semantic_entry is not None:
            semantic_index, semantic_existing = semantic_entry
            if fact_id_supplied and fact["fact_id"] != semantic_existing.get("fact_id"):
                fail(f"同一事实已使用其他 fact_id：{semantic_existing.get('fact_id')}")
            fact["fact_id"] = semantic_existing["fact_id"]
            existing_entry = (semantic_index, semantic_existing)
        if existing_entry:
            existing_index, existing = existing_entry
            comparable_fields = ("statement", "occurred_on")
            if any(existing.get(field) != fact.get(field) for field in comparable_fields):
                fail(f"fact_id 与既有事实冲突：{fact['fact_id']}")
            if fact["extraction_method"] == "date_sentence":
                continue
            revised = dict(existing)
            revised.update({
                "status": fact["status"],
                "sources": fact["sources"],
                "source_locators": fact["source_locators"],
                "date_precision": fact["date_precision"],
                "extraction_method": fact["extraction_method"],
                "updated_by": args.actor,
                "updated_at": now_iso(),
            })
            if conflict_fields_supplied:
                revised.update({
                    "conflicts_with_fact_ids": fact["conflicts_with_fact_ids"],
                    "conflict_status": fact["conflict_status"],
                    "conflict_explanation": fact["conflict_explanation"],
                    "conflict_next_action": fact["conflict_next_action"],
                })
            compared_fields = [
                "status", "sources", "source_locators", "date_precision", "extraction_method",
            ]
            if conflict_fields_supplied:
                compared_fields.extend([
                    "conflicts_with_fact_ids", "conflict_status",
                    "conflict_explanation", "conflict_next_action",
                ])
            if any(existing.get(field) != revised.get(field) for field in compared_fields):
                candidate_state["facts"][existing_index] = revised
                known_by_id[fact["fact_id"]] = (existing_index, revised)
                known_by_semantics[semantic_fact_key(revised)] = (existing_index, revised)
                updated.append(revised)
            continue
        candidate_state.setdefault("facts", []).append(fact)
        added_index = len(candidate_state["facts"]) - 1
        known_by_id[fact["fact_id"]] = (added_index, fact)
        known_by_semantics[semantic_fact_key(fact)] = (added_index, fact)
        added.append(fact)
    generated_at = now_iso()
    internal_root = casework_root(state_path)
    intake_root = internal_root / "intake"
    timeline_json_path = intake_root / "timeline.json"
    timeline_md_path = intake_root / "timeline.md"
    timeline_json, timeline_md = render_timeline(candidate_state["facts"], str(state.get("case_id")), generated_at)
    candidate_state.setdefault("events", []).append({
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "event_type": "facts_timeline_built",
        "actor": args.actor,
        "occurred_at": generated_at,
        "details": {
            "added_fact_ids": [item["fact_id"] for item in added],
            "updated_fact_ids": [item["fact_id"] for item in updated],
            "timeline_json": str(timeline_json_path),
            "timeline_markdown": str(timeline_md_path),
        },
    })
    errors = validate_state(candidate_state)
    if errors:
        fail("事实回写后的案件状态无效：\n" + "\n".join(errors))

    atomic_write_text(timeline_json_path, timeline_json)
    atomic_write_text(timeline_md_path, timeline_md)
    write_state(state_path, candidate_state, source=state_path, operation="facts-timeline-built")
    print(json.dumps({
        "status": "ok",
        "candidate_count": len(candidates),
        "added_count": len(added),
        "updated_count": len(updated),
        "fact_count": len(candidate_state["facts"]),
        "timeline": str(timeline_json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
