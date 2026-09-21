#!/usr/bin/env python3
"""为每个争点构成要件建立证据链和举证责任记录。

``--scaffold`` 只生成待复核骨架，不写入案件状态。``--input``
接入经 Agent／律师复核的证据链，并反向回写争点要件与对方
路径的 ``evidence_ids``。一项要件即使完全缺证，也必须以“缺口链”
写明负担主体、控制方、转移条件、不利后果和补证行动。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from case_state import (
    read_json,
    structured_evidence_errors,
    structured_issue_errors,
    validate_state,
    write_state,
)


SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
ORIENTATIONS = {"supports_our_position", "supports_opponent_position", "cuts_both_ways", "gap_only"}
BURDEN_PARTIES = {"employee", "employer", "both"}
CONTROL_PARTIES = {"employee", "employer", "both", "third_party", "unknown"}
BURDEN_RULES = {"general", "employer_controlled", "burden_shift", "shared"}
ITEM_STATUSES = {"available", "missing", "opponent_controlled", "third_party_controlled", "to_verify"}
AUTHENTICITY_STATUSES = {"original", "copy", "derived", "to_verify", "not_applicable"}
ASSESSMENT_STATUSES = {"sufficient", "partially_sufficient", "insufficient", "disputed", "to_verify"}
MAX_CHAINS = 300


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


def clean_text(value: Any, field: str, *, minimum: int = 4, maximum: int = 1200) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) < minimum:
        fail(f"{field} 过短或为空。")
    if len(text) > maximum:
        fail(f"{field} 超过 {maximum} 字符。")
    return text


def string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"{field} 必须是字符串数组。")
    normalized = list(dict.fromkeys(item.strip() for item in value))
    if not allow_empty and not normalized:
        fail(f"{field} 不得为空。")
    return normalized


def checked_refs(value: Any, field: str, known: set[str], *, allow_empty: bool = True) -> list[str]:
    refs = string_list(value, field, allow_empty=allow_empty)
    missing = sorted(set(refs) - known)
    if missing:
        fail(f"{field} 引用不存在的 ID：{', '.join(missing)}")
    return refs


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


def normalize_item(
    value: Any,
    *,
    evidence_id: str,
    index: int,
    material_ids: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"items[{index}] 必须是 object。")
    name = clean_text(value.get("name"), f"items[{index}].name", maximum=300)
    item_id = value.get("evidence_item_id") or stable_id("eitem", evidence_id, name)
    if not isinstance(item_id, str) or not SAFE_ID.fullmatch(item_id):
        fail(f"items[{index}].evidence_item_id 不安全或过长：{item_id}")
    status = value.get("status")
    if status not in ITEM_STATUSES:
        fail(f"items[{index}].status 无效：{status}")
    materials = checked_refs(value.get("material_ids", []), f"items[{index}].material_ids", material_ids)
    if status == "available" and not materials:
        fail(f"items[{index}] 标记 available 时必须关联 material_id。")
    authenticity = value.get("authenticity_status")
    if authenticity not in AUTHENTICITY_STATUSES:
        fail(f"items[{index}].authenticity_status 无效：{authenticity}")
    locator = value.get("source_locator")
    if locator is not None:
        if not isinstance(locator, dict):
            fail(f"items[{index}].source_locator 必须是 object 或 null。")
        locator_material = locator.get("material_id")
        if locator_material is not None and locator_material not in materials:
            fail(f"items[{index}].source_locator 引用了 material_ids 之外的材料。")
    return {
        "evidence_item_id": item_id,
        "name": name,
        "status": status,
        "material_ids": materials,
        "purpose": clean_text(value.get("purpose"), f"items[{index}].purpose", minimum=8),
        "authenticity_status": authenticity,
        "source_locator": locator,
    }


def normalize_chain(
    value: Any,
    *,
    issues: dict[str, dict[str, Any]],
    elements: dict[str, tuple[str, dict[str, Any]]],
    fact_ids: set[str],
    material_ids: set[str],
    actor: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail("证据链输入必须是 object。")
    issue_id = value.get("issue_id")
    if issue_id not in issues:
        fail(f"证据链引用不存在的 issue_id：{issue_id}")
    element_ids = string_list(value.get("element_ids"), "element_ids", allow_empty=False)
    for element_id in element_ids:
        owner = elements.get(element_id)
        if owner is None:
            fail(f"证据链引用不存在的 element_id：{element_id}")
        if owner[0] != issue_id:
            fail(f"element_id {element_id} 不属于争点 {issue_id}。")
    proposition = clean_text(value.get("proposition"), "proposition", minimum=8)
    evidence_id = value.get("evidence_id") or stable_id("evidence", issue_id, *sorted(element_ids), proposition)
    if not isinstance(evidence_id, str) or not SAFE_ID.fullmatch(evidence_id):
        fail(f"evidence_id 不安全或过长：{evidence_id}")
    orientation = value.get("orientation")
    if orientation not in ORIENTATIONS:
        fail(f"orientation 无效：{orientation}")

    burden = value.get("burden")
    if not isinstance(burden, dict):
        fail(f"burden 必须是 object：{evidence_id}")
    primary_party = burden.get("primary_party")
    control_party = burden.get("control_party")
    burden_rule = burden.get("rule")
    shifted_to = burden.get("shifted_to")
    if primary_party not in BURDEN_PARTIES:
        fail(f"burden.primary_party 无效：{primary_party}")
    if control_party not in CONTROL_PARTIES:
        fail(f"burden.control_party 无效：{control_party}")
    if burden_rule not in BURDEN_RULES:
        fail(f"burden.rule 无效：{burden_rule}")
    if shifted_to is not None and shifted_to not in BURDEN_PARTIES:
        fail(f"burden.shifted_to 无效：{shifted_to}")
    if burden_rule in {"employer_controlled", "burden_shift"} and shifted_to is None:
        fail(f"burden.rule={burden_rule} 时必须写明 shifted_to。")
    if burden_rule == "employer_controlled" and control_party != "employer":
        fail("employer_controlled 必须对应 control_party=employer。")
    normalized_burden = {
        "primary_party": primary_party,
        "control_party": control_party,
        "rule": burden_rule,
        "shifted_to": shifted_to,
        "rationale": clean_text(burden.get("rationale"), "burden.rationale", minimum=8),
        "initial_showing": clean_text(burden.get("initial_showing"), "burden.initial_showing", minimum=8),
        "shift_condition": clean_text(burden.get("shift_condition"), "burden.shift_condition", minimum=8),
        "adverse_consequence": clean_text(
            burden.get("adverse_consequence"), "burden.adverse_consequence", minimum=8
        ),
    }

    raw_items = value.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        fail(f"items 必须是非空数组：{evidence_id}")
    items = [
        normalize_item(item, evidence_id=evidence_id, index=index, material_ids=material_ids)
        for index, item in enumerate(raw_items)
    ]
    item_ids = [item["evidence_item_id"] for item in items]
    if len(item_ids) != len(set(item_ids)):
        fail(f"同一证据链中 evidence_item_id 不得重复：{evidence_id}")
    if orientation == "gap_only" and any(item["status"] == "available" for item in items):
        fail(f"gap_only 证据链不得包含 available 证据：{evidence_id}")

    assessment = value.get("assessment")
    if not isinstance(assessment, dict):
        fail(f"assessment 必须是 object：{evidence_id}")
    assessment_status = assessment.get("status")
    if assessment_status not in ASSESSMENT_STATUSES:
        fail(f"assessment.status 无效：{assessment_status}")
    gaps = string_list(assessment.get("gaps", []), "assessment.gaps")
    actions = string_list(assessment.get("actions", []), "assessment.actions")
    reliable_available = any(
        item["status"] == "available"
        and item["authenticity_status"] in {"original", "copy", "derived"}
        for item in items
    )
    if assessment_status == "sufficient" and not reliable_available:
        fail(f"证据评估为 sufficient 时至少需要一项已关联材料且真实性状态已明确的 available 证据：{evidence_id}")
    if assessment_status != "sufficient" and (not gaps or not actions):
        fail(f"证据尚未充分时必须同时列明 gaps 和 actions：{evidence_id}")

    return {
        "evidence_id": evidence_id,
        "analysis_status": "reviewed",
        "issue_id": issue_id,
        "element_ids": element_ids,
        "proposition": proposition,
        "orientation": orientation,
        "fact_ids": checked_refs(value.get("fact_ids", []), "fact_ids", fact_ids),
        "burden": normalized_burden,
        "items": items,
        "assessment": {
            "status": assessment_status,
            "reasoning": clean_text(assessment.get("reasoning"), "assessment.reasoning", minimum=8),
            "gaps": gaps,
            "actions": actions,
        },
        "created_by": actor,
        "created_at": now_iso(),
    }


def scaffold_chains(state: dict[str, Any]) -> list[dict[str, Any]]:
    facts = {
        item.get("fact_id"): item
        for item in state.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str)
    }
    candidates = []
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
            fact_ids = [item for item in element.get("fact_ids", []) if item in facts]
            material_ids = list(dict.fromkeys(
                source
                for fact_id in fact_ids
                for source in facts[fact_id].get("sources", [])
                if isinstance(source, str)
            ))
            candidates.append({
                "candidate_id": stable_id("ecandidate", issue_id, element["element_id"]),
                "analysis_status": "to_review",
                "issue_id": issue_id,
                "element_ids": [element["element_id"]],
                "proposition": element.get("description", ""),
                "fact_ids": fact_ids,
                "candidate_material_ids": material_ids,
                "required_completion": [
                    "核对证据项与材料定位，不得因事实引用材料就推定证明力充分",
                    "明确初始举证主体、证据控制方、转移条件与举证不能后果",
                    "对非充分状态写明缺口和可执行补证行动",
                ],
            })
    return candidates


def rebuild_issue_links(state: dict[str, Any]) -> None:
    evidence_records = {
        item.get("evidence_id"): item
        for item in state.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
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
                element["evidence_ids"] = sorted(
                    evidence_id
                    for evidence_id, record in evidence_records.items()
                    if record.get("issue_id") == issue_id and element_id in record.get("element_ids", [])
                )
        opponent = issue.get("opponent_position")
        if isinstance(opponent, dict):
            opponent["evidence_ids"] = sorted(
                evidence_id
                for evidence_id, record in evidence_records.items()
                if record.get("issue_id") == issue_id
                and record.get("orientation") in {"supports_opponent_position", "cuts_both_ways"}
            )


def render_scaffold(state: dict[str, Any], candidates: list[dict[str, Any]], generated_at: str) -> tuple[str, str]:
    payload = {
        "status": "review_required",
        "case_id": state.get("case_id"),
        "generated_at": generated_at,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    lines = [
        "# 证据链待复核骨架",
        "",
        "> 骨架只根据争点要件、事实和材料关系生成，不代表证据三性、证明力或举证责任已经确定。",
        "",
        "| 争点 | 构成要件 | 待证命题 | 事实 | 候选材料 |",
        "|---|---|---|---|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item['issue_id']} | {'、'.join(item['element_ids'])} | {item['proposition']} | "
            f"{'、'.join(item['fact_ids']) or '无'} | {'、'.join(item['candidate_material_ids']) or '无'} |"
        )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def render_matrix(state: dict[str, Any], generated_at: str) -> tuple[str, str]:
    records = state.get("evidence", [])
    payload = {
        "status": "lawyer_review_required",
        "case_id": state.get("case_id"),
        "representation": state.get("representation"),
        "generated_at": generated_at,
        "evidence_chain_count": len(records),
        "evidence": records,
    }
    lines = [
        "# 证据链与举证责任矩阵",
        "",
        "> 状态：待律师复核；证据缺口链不等于已有证据。",
        "",
    ]
    for index, record in enumerate(records, 1):
        burden = record["burden"]
        assessment = record["assessment"]
        lines.extend([
            f"## {index}. {record['proposition']}",
            "",
            f"- 争点／要件：{record['issue_id']} ／ {'、'.join(record['element_ids'])}",
            f"- 证据方向：{record['orientation']}",
            f"- 初始举证方：{burden['primary_party']}；证据控制方：{burden['control_party']}",
            f"- 责任规则：{burden['rule']}；转移至：{burden['shifted_to'] or '不适用'}",
            f"- 初步举证：{burden['initial_showing']}",
            f"- 转移条件：{burden['shift_condition']}",
            f"- 举证不能后果：{burden['adverse_consequence']}",
            f"- 当前评估：{assessment['status']}；{assessment['reasoning']}",
            f"- 缺口：{'、'.join(assessment['gaps']) or '无'}",
            f"- 行动：{'、'.join(assessment['actions']) or '无'}",
            "",
            "| 证据项 | 状态 | 材料 | 证明目的 | 真实性状态 |",
            "|---|---|---|---|---|",
        ])
        for item in record["items"]:
            lines.append(
                f"| {item['name']} | {item['status']} | {'、'.join(item['material_ids']) or '无'} | "
                f"{item['purpose']} | {item['authenticity_status']} |"
            )
        lines.append("")
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def load_chains(path: Path) -> list[Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"证据链输入不存在：{path}")
    except json.JSONDecodeError as exc:
        fail(f"证据链输入不是合法 JSON：{exc}")
    records = payload.get("evidence") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        fail("证据链输入必须是非空数组，或含 evidence 数组的 object。")
    if len(records) > MAX_CHAINS:
        fail(f"单次证据链不得超过 {MAX_CHAINS} 条。")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 证据链与举证责任执行器")
    parser.add_argument("--state", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--scaffold", action="store_true", help="按争点要件生成待复核证据链骨架")
    mode.add_argument("--input", help="经复核的证据链 JSON")
    parser.add_argument(
        "--replace-existing-evidence",
        action="store_true",
        help="以本次完整证据链替换旧 evidence[]；旧状态由历史快照保留",
    )
    parser.add_argument("--actor", default="labor-evidence-analysis")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    if state.get("current_node") != "evidence_analysis":
        fail(f"当前节点为 {state.get('current_node')}，不能执行证据分析。")
    if args.scaffold and args.replace_existing_evidence:
        fail("--replace-existing-evidence 只能与 --input 一起使用。")

    issue_errors = structured_issue_errors(state)
    if issue_errors:
        fail("争点矩阵未完成，不能建立证据链：\n" + "\n".join(issue_errors))

    output_root = casework_root(state_path) / "evidence_analysis"
    generated_at = now_iso()
    if args.scaffold:
        candidates = scaffold_chains(state)
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
    facts = {
        item.get("fact_id") for item in state.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str)
    }
    materials = {
        item.get("material_id") for item in state.get("materials", [])
        if isinstance(item, dict) and isinstance(item.get("material_id"), str)
    }
    normalized = [
        normalize_chain(
            item,
            issues=issues,
            elements=elements,
            fact_ids=facts,
            material_ids=materials,
            actor=args.actor,
        )
        for item in load_chains(Path(args.input).expanduser().resolve())
    ]
    evidence_ids = [item["evidence_id"] for item in normalized]
    if len(evidence_ids) != len(set(evidence_ids)):
        fail("同一批输入中 evidence_id 不得重复。")

    candidate_state = json.loads(json.dumps(state, ensure_ascii=False))
    replaced_count = 0
    if args.replace_existing_evidence:
        replaced_count = len(candidate_state.get("evidence", []))
        candidate_state["evidence"] = []
    existing_by_id = {
        item.get("evidence_id"): (index, item)
        for index, item in enumerate(candidate_state.get("evidence", []))
        if isinstance(item, dict) and item.get("evidence_id")
    }
    added_ids = []
    updated_ids = []
    for record in normalized:
        existing_entry = existing_by_id.get(record["evidence_id"])
        if existing_entry:
            index, existing = existing_entry
            record["created_at"] = existing.get("created_at") or record["created_at"]
            record["created_by"] = existing.get("created_by") or record["created_by"]
            record["updated_at"] = generated_at
            record["updated_by"] = args.actor
            candidate_state["evidence"][index] = record
            updated_ids.append(record["evidence_id"])
        else:
            candidate_state.setdefault("evidence", []).append(record)
            added_ids.append(record["evidence_id"])
    rebuild_issue_links(candidate_state)
    chain_errors = validate_state(candidate_state) + structured_evidence_errors(candidate_state)
    if chain_errors:
        hint = "\n旧 evidence[] 为占位结构时，请在完整证据链输入下使用 --replace-existing-evidence。"
        fail("证据链回写后的案件状态无效：\n" + "\n".join(chain_errors) + hint)

    matrix_json_path = output_root / "matrix.json"
    matrix_md_path = output_root / "matrix.md"
    matrix_json, matrix_md = render_matrix(candidate_state, generated_at)
    candidate_state.setdefault("events", []).append({
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "event_type": "evidence_chain_built",
        "actor": args.actor,
        "occurred_at": generated_at,
        "details": {
            "added_evidence_ids": added_ids,
            "updated_evidence_ids": updated_ids,
            "replaced_previous_count": replaced_count,
            "matrix_json": str(matrix_json_path),
            "matrix_markdown": str(matrix_md_path),
        },
    })
    atomic_write_text(matrix_json_path, matrix_json)
    atomic_write_text(matrix_md_path, matrix_md)
    write_state(state_path, candidate_state, source=state_path, operation="evidence-chain-built")
    print(json.dumps({
        "status": "lawyer_review_required",
        "evidence_chain_count": len(candidate_state["evidence"]),
        "added_count": len(added_ids),
        "updated_count": len(updated_ids),
        "replaced_previous_count": replaced_count,
        "matrix": str(matrix_json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
