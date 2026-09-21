#!/usr/bin/env python3
"""将官方来源或法律数据库的核验结果适配为本案法源矩阵。

``--scaffold`` 只生成待复核的检索任务，不写入 ``rules[]``。
``--input`` 接入外部核验结果，但不绑定某一 MCP、法律数据库或网络服务。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from case_state import (
    AUTHORITY_ADOPTION_STATUSES,
    AUTHORITY_APPLICABILITY_STATUSES,
    AUTHORITY_LEVELS,
    AUTHORITY_ORIENTATIONS,
    AUTHORITY_SOURCE_TYPES,
    AUTHORITY_TERRITORY_SCOPES,
    AUTHORITY_VALIDITY_STATUSES,
    AUTHORITY_VERIFICATION_STATUSES,
    read_json,
    structured_authority_errors,
    structured_issue_errors,
    validate_state,
    write_state,
)


SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
MAX_RECORDS = 300


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


def clean_text(value: Any, field: str, *, minimum: int = 4, maximum: int = 5000) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) < minimum:
        fail(f"{field} 过短或为空。")
    if len(text) > maximum:
        fail(f"{field} 超过 {maximum} 字符。")
    return text


def optional_text(value: Any, field: str, *, maximum: int = 1000) -> str | None:
    if value is None or value == "":
        return None
    return clean_text(value, field, minimum=1, maximum=maximum)


def string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"{field} 必须是字符串数组。")
    normalized = list(dict.fromkeys(item.strip() for item in value))
    if not allow_empty and not normalized:
        fail(f"{field} 不得为空。")
    return normalized


def valid_date(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        fail(f"{field} 必须是 YYYY-MM-DD。")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        fail(f"{field} 必须是合法 YYYY-MM-DD。")


def valid_datetime(value: Any, field: str) -> str:
    if not isinstance(value, str):
        fail(f"{field} 必须是 ISO 时间。")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{field} 必须是合法 ISO 时间。")
    return value


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\0".join(parts)
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def issue_elements(state: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, tuple[str, dict[str, Any]]]]:
    issues: dict[str, dict[str, Any]] = {}
    elements: dict[str, tuple[str, dict[str, Any]]] = {}
    for issue in state.get("issues", []):
        if not isinstance(issue, dict) or not isinstance(issue.get("issue_id"), str):
            continue
        issue_id = issue["issue_id"]
        issues[issue_id] = issue
        our_position = issue.get("our_position")
        if not isinstance(our_position, dict):
            continue
        for element in our_position.get("elements", []):
            if isinstance(element, dict) and isinstance(element.get("element_id"), str):
                elements[element["element_id"]] = (issue_id, element)
    return issues, elements


def normalize_record(
    value: Any,
    *,
    state: dict[str, Any],
    issues: dict[str, dict[str, Any]],
    elements: dict[str, tuple[str, dict[str, Any]]],
    actor: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail("法源输入必须是 object。")
    issue_id = value.get("issue_id")
    if issue_id not in issues:
        fail(f"法源引用不存在的 issue_id：{issue_id}")
    element_ids = string_list(value.get("element_ids"), "element_ids")
    for element_id in element_ids:
        owner = elements.get(element_id)
        if owner is None:
            fail(f"法源引用不存在的 element_id：{element_id}")
        if owner[0] != issue_id:
            fail(f"element_id {element_id} 不属于争点 {issue_id}。")

    proposition = clean_text(value.get("proposition"), "proposition", minimum=8, maximum=1200)
    document_title = clean_text(value.get("document_title"), "document_title", maximum=300)
    article_number = clean_text(value.get("article_number"), "article_number", minimum=1, maximum=100)
    document_id = value.get("document_id") or stable_id("document", document_title)
    article_id = value.get("article_id") or stable_id("article", document_id, article_number)
    for field, identifier in (("document_id", document_id), ("article_id", article_id)):
        if not isinstance(identifier, str) or not SAFE_ID.fullmatch(identifier):
            fail(f"{field} 不安全或过长：{identifier}")
    rule_id = value.get("rule_id") or stable_id("rule", issue_id, *sorted(element_ids), article_id, proposition)
    if not isinstance(rule_id, str) or not SAFE_ID.fullmatch(rule_id):
        fail(f"rule_id 不安全或过长：{rule_id}")

    enumerations = {
        "authority_level": AUTHORITY_LEVELS,
        "orientation": AUTHORITY_ORIENTATIONS,
        "adoption_status": AUTHORITY_ADOPTION_STATUSES,
        "verification_status": AUTHORITY_VERIFICATION_STATUSES,
        "validity_status": AUTHORITY_VALIDITY_STATUSES,
        "applicability_status": AUTHORITY_APPLICABILITY_STATUSES,
        "territory_scope": AUTHORITY_TERRITORY_SCOPES,
        "source_type": AUTHORITY_SOURCE_TYPES,
    }
    normalized_enums: dict[str, str] = {}
    for field, allowed in enumerations.items():
        selected = value.get(field)
        if selected not in allowed:
            fail(f"{field} 无效：{selected}")
        normalized_enums[field] = selected

    article_text = clean_text(value.get("article_text"), "article_text", minimum=12, maximum=30000)
    source_url = value.get("source_url")
    parsed = urlparse(source_url) if isinstance(source_url, str) else None
    if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail("source_url 必须是完整 HTTP(S) URL。")
    effective_from = valid_date(value.get("effective_from"), "effective_from", nullable=True)
    effective_to = valid_date(value.get("effective_to"), "effective_to", nullable=True)
    relevant_date = valid_date(value.get("relevant_date"), "relevant_date")
    if effective_from and effective_to and effective_to < effective_from:
        fail("效力终止日不得早于生效日。")
    if normalized_enums["applicability_status"] == "applicable":
        if effective_from and relevant_date < effective_from:
            fail("相关日期早于法源生效日。")
        if effective_to and relevant_date > effective_to:
            fail("相关日期晚于法源效力终止日。")

    jurisdictions = string_list(value.get("applicable_jurisdictions"), "applicable_jurisdictions")
    if normalized_enums["territory_scope"] != "national" and normalized_enums["applicability_status"] == "applicable":
        case_jurisdiction = str(state.get("jurisdiction", ""))
        if not any(item in case_jurisdiction or case_jurisdiction in item for item in jurisdictions):
            fail("法源地域范围与案件管辖地不匹配。")

    warning = optional_text(value.get("warning"), "warning", maximum=1000)
    if normalized_enums["validity_status"] in {"amended", "repealed", "expired"} and (
        warning is None or len(warning) < 8
    ):
        fail("对修改／废止／失效法源必须写明 warning。")
    if normalized_enums["adoption_status"] == "adopted":
        if normalized_enums["verification_status"] != "verified":
            fail("正式采用的法源必须已核验。")
        if normalized_enums["applicability_status"] != "applicable":
            fail("正式采用的法源必须明确适用于本案。")
        if normalized_enums["validity_status"] in {"not_yet_effective", "unknown"}:
            fail("未生效或效力未明的法源不得正式采用。")

    result = {
        "rule_id": rule_id,
        "analysis_status": "reviewed",
        "issue_id": issue_id,
        "element_ids": element_ids,
        "proposition": proposition,
        "orientation": normalized_enums["orientation"],
        "adoption_status": normalized_enums["adoption_status"],
        "document_id": document_id,
        "document_title": document_title,
        "document_number": optional_text(value.get("document_number"), "document_number", maximum=200),
        "issuing_authority": clean_text(value.get("issuing_authority"), "issuing_authority", maximum=300),
        "authority_level": normalized_enums["authority_level"],
        "article_id": article_id,
        "article_number": article_number,
        "article_text": article_text,
        "article_text_sha256": hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
        "verification_status": normalized_enums["verification_status"],
        "validity_status": normalized_enums["validity_status"],
        "effective_from": effective_from,
        "effective_to": effective_to,
        "territory_scope": normalized_enums["territory_scope"],
        "applicable_jurisdictions": jurisdictions,
        "case_jurisdiction": state["jurisdiction"],
        "analysis_date": state["analysis_date"],
        "relevant_date": relevant_date,
        "temporal_basis": clean_text(value.get("temporal_basis"), "temporal_basis", minimum=8, maximum=1000),
        "applicability_status": normalized_enums["applicability_status"],
        "applicability_reasoning": clean_text(
            value.get("applicability_reasoning"), "applicability_reasoning", minimum=12, maximum=2000
        ),
        "source_type": normalized_enums["source_type"],
        "source_name": clean_text(value.get("source_name"), "source_name", maximum=300),
        "source_url": source_url,
        "retrieved_at": valid_datetime(value.get("retrieved_at"), "retrieved_at"),
        "warning": warning,
        "created_by": actor,
        "created_at": now_iso(),
    }
    supplied_digest = value.get("article_text_sha256")
    if supplied_digest is not None and supplied_digest != result["article_text_sha256"]:
        fail("article_text_sha256 与条文原文不一致。")
    return result


def rebuild_issue_links(state: dict[str, Any]) -> None:
    adopted = {
        item.get("rule_id"): item
        for item in state.get("rules", [])
        if isinstance(item, dict)
        and isinstance(item.get("rule_id"), str)
        and item.get("adoption_status") == "adopted"
    }
    for issue in state.get("issues", []):
        if not isinstance(issue, dict):
            continue
        issue_id = issue.get("issue_id")
        our_position = issue.get("our_position")
        if isinstance(our_position, dict):
            for element in our_position.get("elements", []):
                if not isinstance(element, dict):
                    continue
                element_id = element.get("element_id")
                element["rule_ids"] = sorted(
                    rule_id for rule_id, record in adopted.items()
                    if record.get("issue_id") == issue_id and element_id in record.get("element_ids", [])
                )
        opponent = issue.get("opponent_position")
        if isinstance(opponent, dict):
            opponent["rule_ids"] = sorted(
                rule_id for rule_id, record in adopted.items()
                if record.get("issue_id") == issue_id
                and record.get("orientation") in {"supports_opponent_position", "cuts_both_ways"}
            )


def scaffold_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for issue in state.get("issues", []):
        if not isinstance(issue, dict):
            continue
        issue_id = issue.get("issue_id")
        our_position = issue.get("our_position")
        if not isinstance(issue_id, str) or not isinstance(our_position, dict):
            continue
        for element in our_position.get("elements", []):
            if not isinstance(element, dict) or not isinstance(element.get("element_id"), str):
                continue
            candidates.append({
                "candidate_id": stable_id("acandidate", issue_id, element["element_id"]),
                "analysis_status": "to_review",
                "issue_id": issue_id,
                "element_ids": [element["element_id"]],
                "legal_question": element.get("description", ""),
                "case_jurisdiction": state.get("jurisdiction"),
                "analysis_date": state.get("analysis_date"),
                "required_verification": [
                    "核对法律全称、文号、条号和完整条文",
                    "保存官方来源或法律数据库 URL 及检索时间",
                    "核对效力状态、生效／终止日期、地域与本案相关日期",
                    "区分正式采用、仅作参考和排除的法源",
                ],
            })
    return candidates


def render_scaffold(state: dict[str, Any], candidates: list[dict[str, Any]], generated_at: str) -> tuple[str, str]:
    payload = {
        "status": "review_required",
        "case_id": state.get("case_id"),
        "generated_at": generated_at,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    lines = [
        "# 法源核验待办",
        "",
        "> 内置知识只能提供检索线索；本骨架不是已验证法源，不写入 rules[]。",
        "",
        "| 争点 | 构成要件 | 待核验法律问题 | 地域 | 分析日期 |",
        "|---|---|---|---|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item['issue_id']} | {'、'.join(item['element_ids'])} | {item['legal_question']} | "
            f"{item['case_jurisdiction']} | {item['analysis_date']} |"
        )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def render_matrix(state: dict[str, Any], generated_at: str) -> tuple[str, str]:
    records = state.get("rules", [])
    payload = {
        "status": "lawyer_review_required",
        "case_id": state.get("case_id"),
        "generated_at": generated_at,
        "authority_count": len(records),
        "rules": records,
    }
    lines = ["# 法源核验与适用性矩阵", "", "> 状态：待律师复核。", ""]
    for index, record in enumerate(records, 1):
        lines.extend([
            f"## {index}. {record['document_title']}{record['article_number']}",
            "",
            f"- 采用状态：{record['adoption_status']}；核验状态：{record['verification_status']}",
            f"- 争点／要件：{record['issue_id']} ／ {'、'.join(record['element_ids'])}",
            f"- 效力：{record['validity_status']} ／ {record['effective_from'] or '未记载'} 至 {record['effective_to'] or '未记载'}",
            f"- 地域：{record['territory_scope']} ／ {'、'.join(record['applicable_jurisdictions'])}",
            f"- 时间适用：{record['relevant_date']} ／ {record['temporal_basis']}",
            f"- 适用结论：{record['applicability_status']} ／ {record['applicability_reasoning']}",
            f"- 来源：{record['source_name']} ／ {record['source_url']}",
            f"- 警示：{record['warning'] or '无'}",
            "",
            f"> {record['article_text']}",
            "",
        ])
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def load_records(path: Path) -> list[Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"法源输入不存在：{path}")
    except json.JSONDecodeError as exc:
        fail(f"法源输入不是合法 JSON：{exc}")
    records = payload.get("rules") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        fail("法源输入必须是非空数组，或含 rules 数组的 object。")
    if len(records) > MAX_RECORDS:
        fail(f"单次法源记录不得超过 {MAX_RECORDS} 条。")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 法源核验结果适配器")
    parser.add_argument("--state", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--scaffold", action="store_true", help="按争点要件生成待复核法源核验任务")
    mode.add_argument("--input", help="官方来源或法律数据库的经复核结果 JSON")
    parser.add_argument(
        "--replace-existing-rules", action="store_true",
        help="以本次完整法源矩阵替换旧 rules[]；旧状态保留在历史快照",
    )
    parser.add_argument("--actor", default="labor-authority-research")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    if state.get("current_node") != "authority_research":
        fail(f"当前节点为 {state.get('current_node')}，不能执行法源研究。")
    if args.scaffold and args.replace_existing_rules:
        fail("--replace-existing-rules 只能与 --input 一起使用。")
    issue_errors = structured_issue_errors(state)
    if issue_errors:
        fail("争点矩阵未完成，不能建立法源矩阵：\n" + "\n".join(issue_errors))

    output_root = casework_root(state_path) / "authority"
    generated_at = now_iso()
    if args.scaffold:
        candidates = scaffold_records(state)
        scaffold_json, scaffold_md = render_scaffold(state, candidates, generated_at)
        atomic_write_text(output_root / "scaffold.json", scaffold_json)
        atomic_write_text(output_root / "scaffold.md", scaffold_md)
        print(json.dumps({
            "status": "review_required",
            "candidate_count": len(candidates),
            "scaffold": str(output_root / "scaffold.json"),
        }, ensure_ascii=False))
        return 0

    issues, elements = issue_elements(state)
    normalized = [
        normalize_record(item, state=state, issues=issues, elements=elements, actor=args.actor)
        for item in load_records(Path(args.input).expanduser().resolve())
    ]
    rule_ids = [item["rule_id"] for item in normalized]
    if len(rule_ids) != len(set(rule_ids)):
        fail("同一批输入中 rule_id 不得重复。")

    candidate_state = json.loads(json.dumps(state, ensure_ascii=False))
    replaced_count = 0
    if args.replace_existing_rules:
        replaced_count = len(candidate_state.get("rules", []))
        candidate_state["rules"] = []
    existing_by_id = {
        item.get("rule_id"): (index, item)
        for index, item in enumerate(candidate_state.get("rules", []))
        if isinstance(item, dict) and item.get("rule_id")
    }
    added_ids: list[str] = []
    updated_ids: list[str] = []
    for record in normalized:
        existing = existing_by_id.get(record["rule_id"])
        if existing:
            index, previous = existing
            record["created_at"] = previous.get("created_at") or record["created_at"]
            record["created_by"] = previous.get("created_by") or record["created_by"]
            record["updated_at"] = generated_at
            record["updated_by"] = args.actor
            candidate_state["rules"][index] = record
            updated_ids.append(record["rule_id"])
        else:
            candidate_state.setdefault("rules", []).append(record)
            added_ids.append(record["rule_id"])
    rebuild_issue_links(candidate_state)
    authority_errors = validate_state(candidate_state) + structured_authority_errors(candidate_state)
    if authority_errors:
        hint = "\n旧 rules[] 为占位结构时，请在完整法源输入下使用 --replace-existing-rules。"
        fail("法源回写后的案件状态无效：\n" + "\n".join(authority_errors) + hint)

    matrix_json_path = output_root / "matrix.json"
    matrix_md_path = output_root / "matrix.md"
    matrix_json, matrix_md = render_matrix(candidate_state, generated_at)
    candidate_state.setdefault("events", []).append({
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "event_type": "authority_matrix_built",
        "actor": args.actor,
        "occurred_at": generated_at,
        "details": {
            "added_rule_ids": added_ids,
            "updated_rule_ids": updated_ids,
            "replaced_previous_count": replaced_count,
            "matrix_json": str(matrix_json_path),
            "matrix_markdown": str(matrix_md_path),
        },
    })
    atomic_write_text(matrix_json_path, matrix_json)
    atomic_write_text(matrix_md_path, matrix_md)
    write_state(state_path, candidate_state, source=state_path, operation="authority-matrix-built")
    print(json.dumps({
        "status": "lawyer_review_required",
        "authority_count": len(candidate_state["rules"]),
        "added_count": len(added_ids),
        "updated_count": len(updated_ids),
        "replaced_previous_count": replaced_count,
        "matrix": str(matrix_json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
