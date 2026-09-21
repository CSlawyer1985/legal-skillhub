#!/usr/bin/env python3
"""初始化、验证、迁移并推进劳动争议案件状态。

用户侧始终只保留一份 case_state.json；就地更新前的状态自动进入
.casework/history/，以兼顾可回溯与目录可读性。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from authority_status import known_repeal
from typing import Any
from urllib.parse import urlparse

from claims_engine import (
    FORMULA_TYPES,
    FORMULA_VERSION,
    CalculationError,
    calculation_digest,
    calculate_formula,
)


SCHEMA_VERSION = "2.0"
REPRESENTATIONS = {"employee", "employer", "undetermined"}
STAGES = ["undetermined", "intake", "pre_arbitration", "arbitration", "first_instance", "second_instance", "closure"]
FACT_STATUSES = {"supported", "client_statement", "opponent_allegation", "disputed", "to_verify"}
FACT_CONFLICT_STATUSES = {"none", "unresolved", "resolved"}
ISSUE_TYPES = {"claim", "defense", "procedure", "threshold"}
ISSUE_ANALYSIS_STATUSES = {"to_review", "reviewed"}
ELEMENT_STATUSES = {"supported", "partially_supported", "unsupported", "disputed", "to_verify"}
EVIDENCE_ORIENTATIONS = {"supports_our_position", "supports_opponent_position", "cuts_both_ways", "gap_only"}
BURDEN_PARTIES = {"employee", "employer", "both"}
CONTROL_PARTIES = {"employee", "employer", "both", "third_party", "unknown"}
BURDEN_RULES = {"general", "employer_controlled", "burden_shift", "shared"}
EVIDENCE_ITEM_STATUSES = {"available", "missing", "opponent_controlled", "third_party_controlled", "to_verify"}
AUTHENTICITY_STATUSES = {"original", "copy", "derived", "to_verify", "not_applicable"}
EVIDENCE_ASSESSMENT_STATUSES = {"sufficient", "partially_sufficient", "insufficient", "disputed", "to_verify"}
AUTHORITY_LEVELS = {
    "law", "administrative_regulation", "judicial_interpretation", "department_rule",
    "local_regulation", "local_rule", "local_guidance", "case_reference",
}
AUTHORITY_ORIENTATIONS = {"supports_our_position", "supports_opponent_position", "cuts_both_ways", "neutral"}
AUTHORITY_ADOPTION_STATUSES = {"adopted", "reference_only", "excluded"}
AUTHORITY_VERIFICATION_STATUSES = {"verified", "conflict"}
AUTHORITY_VALIDITY_STATUSES = {"effective", "amended", "repealed", "expired", "not_yet_effective", "unknown"}
AUTHORITY_APPLICABILITY_STATUSES = {"applicable", "not_applicable", "conditional", "to_verify"}
AUTHORITY_TERRITORY_SCOPES = {"national", "local", "case_specific"}
AUTHORITY_SOURCE_TYPES = {"official", "legal_database"}
RISK_LEVELS = {"standard", "complex", "high"}
BUSINESS_ARRAYS = ["parties", "goals", "facts", "materials", "issues", "evidence", "rules", "claims", "deadlines", "decisions", "deliverables"]
GRAPH_ARRAYS = ["node_runs", "validations", "approvals", "checkpoints", "artifacts", "events"]
OPTIONAL_GRAPH_ARRAYS = ["node_requirement_waivers"]
OPTIONAL_BUSINESS_ARRAYS = ["calculations", "procedural_assessments"]
LIMITATION_STATUSES = {"in_time", "out_of_time", "disputed", "not_applicable"}
JURISDICTION_STATUSES = {"proper", "improper", "disputed"}
BINARY_PROCEDURE_STATUSES = {"applicable", "not_applicable", "disputed"}


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"文件不存在：{path}")
    except json.JSONDecodeError as exc:
        fail(f"JSON 解析失败：{path}：{exc}")


def write_new(path: Path, payload: Any) -> None:
    if path.exists():
        fail(f"拒绝覆盖已有文件：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _snapshot_path(source: Path, operation: str) -> Path:
    internal = source.parent if source.parent.name == ".casework" else source.parent / ".casework"
    history = internal / "history"
    history.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    safe_operation = re.sub(r"[^a-zA-Z0-9_-]+", "-", operation).strip("-") or "update"
    return history / f"{timestamp}-{safe_operation}.json"


def write_state(path: Path, payload: Any, *, source: Path | None = None, operation: str = "update") -> None:
    """写入案件状态。

    当输入与输出是同一个文件时，先把旧状态保存到隐藏历史目录，再原子替换
    case_state.json。显式指定不同输出路径时保留旧版兼容行为，但仍拒绝覆盖。
    """
    source = source.resolve() if source is not None else None
    target = path.resolve()
    same_file = source is not None and source == target
    if same_file:
        if not source.exists():
            fail(f"源状态文件不存在：{source}")
        snapshot = _snapshot_path(source, operation)
        snapshot.write_bytes(source.read_bytes())
        if isinstance(payload, dict):
            payload["previous_state"] = str(snapshot.resolve())
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(rendered, encoding="utf-8")
        os.replace(temporary, target)
        return
    write_new(path, payload)


def valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def check_unique_ids(items: Any, key: str, label: str, errors: list[str]) -> None:
    if not isinstance(items, list):
        return
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] 必须是 object。")
            continue
        value = item.get(key)
        if not isinstance(value, str) or not value.strip() or value in seen:
            errors.append(f"{label}[{index}].{key} 缺失或重复。")
        else:
            seen.add(value)


def fact_conflict_errors(state: dict[str, Any]) -> list[str]:
    """校验事实冲突关系、处理状态和双向一致性。"""
    errors: list[str] = []
    facts = state.get("facts", [])
    if not isinstance(facts, list):
        return ["facts 必须是数组。"]
    fact_map = {
        item.get("fact_id"): item
        for item in facts
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str) and item.get("fact_id")
    }
    valid_ids = set(fact_map)
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            continue
        label = f"facts[{index}]"
        fact_id = fact.get("fact_id")
        refs = fact.get("conflicts_with_fact_ids", [])
        if not isinstance(refs, list) or not all(isinstance(item, str) and item for item in refs):
            errors.append(f"{label}.conflicts_with_fact_ids 必须是事实 ID 字符串数组。")
            continue
        if len(refs) != len(set(refs)):
            errors.append(f"{label}.conflicts_with_fact_ids 不得包含重复 ID。")
        if isinstance(fact_id, str) and fact_id in refs:
            errors.append(f"{label} 不得与自身建立事实冲突。")
        missing = sorted(set(refs) - valid_ids)
        if missing:
            errors.append(f"{label}.conflicts_with_fact_ids 引用不存在的事实：{', '.join(missing)}。")

        conflict_status = fact.get("conflict_status")
        explanation = fact.get("conflict_explanation")
        next_action = fact.get("conflict_next_action")
        if refs:
            if not isinstance(conflict_status, str) or conflict_status not in {"unresolved", "resolved"}:
                errors.append(f"{label}.conflict_status 必须为 unresolved 或 resolved。")
            if not isinstance(explanation, str) or len(explanation.strip()) < 8:
                errors.append(f"{label}.conflict_explanation 过短或为空。")
            if conflict_status == "unresolved" and (
                not isinstance(next_action, str) or len(next_action.strip()) < 8
            ):
                errors.append(f"{label}.conflict_next_action 未说明具体待核实行动。")
            if conflict_status == "resolved" and next_action is not None and not isinstance(next_action, str):
                errors.append(f"{label}.conflict_next_action 必须为字符串或 null。")
            if conflict_status == "unresolved" and fact.get("status") == "supported":
                errors.append(f"{label} 存在未解决事实冲突，不得标记为 supported。")
        else:
            if conflict_status is not None and conflict_status != "none":
                errors.append(f"{label} 没有冲突引用时 conflict_status 必须为 none。")
            if (explanation is not None and explanation != "") or (
                next_action is not None and next_action != ""
            ):
                errors.append(f"{label} 没有冲突引用时不得保留冲突说明或行动。")

        if not isinstance(fact_id, str):
            continue
        for other_id in refs:
            other = fact_map.get(other_id)
            if not isinstance(other, dict):
                continue
            other_refs = other.get("conflicts_with_fact_ids", [])
            if not isinstance(other_refs, list) or fact_id not in other_refs:
                errors.append(f"事实冲突关系必须双向一致：{fact_id} → {other_id} 缺少反向引用。")
                continue
            other_status = other.get("conflict_status")
            if (
                isinstance(conflict_status, str)
                and conflict_status in {"unresolved", "resolved"}
                and other_status != conflict_status
            ):
                errors.append(f"事实冲突双方状态不一致：{fact_id} 与 {other_id}。")
    return errors


def structured_fact_errors(state: dict[str, Any]) -> list[str]:
    """校验事实陈述、来源和冲突结构。"""
    errors: list[str] = []
    facts = state.get("facts", [])
    if not isinstance(facts, list):
        return ["facts 必须是数组。"]
    material_ids = {
        item.get("material_id") for item in state.get("materials", [])
        if isinstance(item, dict) and isinstance(item.get("material_id"), str)
    }
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            continue
        label = f"facts[{index}]"
        if not isinstance(fact.get("statement"), str) or len(fact["statement"].strip()) < 4:
            errors.append(f"{label}.statement 过短或为空。")
        if fact.get("status") not in FACT_STATUSES:
            errors.append(f"{label}.status 无效。")
        sources = fact.get("sources")
        if not isinstance(sources, list) or not all(isinstance(item, str) and item for item in sources):
            errors.append(f"{label}.sources 必须是材料 ID 字符串数组。")
            continue
        missing = sorted(set(sources) - material_ids)
        if missing:
            errors.append(f"{label}.sources 引用未登记材料：{', '.join(missing)}。")
        if fact.get("status") == "supported" and not sources:
            errors.append(f"{label} 标记 supported 但没有材料来源。")
    errors.extend(fact_conflict_errors(state))
    return errors


def structured_issue_errors(state: dict[str, Any]) -> list[str]:
    """验证请求／抗辩矩阵，确保争点不是只含 ID 的占位符。"""
    errors: list[str] = []
    issues = state.get("issues", [])
    if not isinstance(issues, list):
        return ["issues 必须是数组。"]
    known_facts = {
        item.get("fact_id") for item in state.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str)
    }
    known_evidence = {
        item.get("evidence_id") for item in state.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    known_rules = {
        value
        for item in state.get("rules", []) if isinstance(item, dict)
        for value in (item.get("rule_id"), item.get("article_id"))
        if isinstance(value, str)
    }

    def check_refs(value: Any, known: set[str], label: str) -> None:
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            errors.append(f"{label} 必须是字符串数组。")
            return
        missing = sorted(set(value) - known)
        if missing:
            errors.append(f"{label} 引用不存在的 ID：{', '.join(missing)}。")

    for issue_index, issue in enumerate(issues):
        label = f"issues[{issue_index}]"
        if not isinstance(issue, dict):
            errors.append(f"{label} 必须是 object。")
            continue
        if not isinstance(issue.get("issue"), str) or len(issue["issue"].strip()) < 4:
            errors.append(f"{label}.issue 过短或为空。")
        if issue.get("issue_type") not in ISSUE_TYPES:
            errors.append(f"{label}.issue_type 无效。")
        if issue.get("analysis_status") not in ISSUE_ANALYSIS_STATUSES:
            errors.append(f"{label}.analysis_status 无效。")
        elif issue.get("analysis_status") != "reviewed":
            errors.append(f"{label}.analysis_status 尚未达到 reviewed。")
        if issue.get("representation") != state.get("representation"):
            errors.append(f"{label}.representation 与案件代理立场不一致。")
        our_position = issue.get("our_position")
        if not isinstance(our_position, dict):
            errors.append(f"{label}.our_position 必须是 object。")
        else:
            for field in ("position", "conclusion"):
                if not isinstance(our_position.get(field), str) or len(our_position[field].strip()) < 8:
                    errors.append(f"{label}.our_position.{field} 过短或为空。")
            elements = our_position.get("elements")
            if not isinstance(elements, list) or not elements:
                errors.append(f"{label}.our_position.elements 必须是非空数组。")
            else:
                element_ids: set[str] = set()
                for element_index, element in enumerate(elements):
                    element_label = f"{label}.our_position.elements[{element_index}]"
                    if not isinstance(element, dict):
                        errors.append(f"{element_label} 必须是 object。")
                        continue
                    element_id = element.get("element_id")
                    if not isinstance(element_id, str) or not element_id or element_id in element_ids:
                        errors.append(f"{element_label}.element_id 缺失或重复。")
                    else:
                        element_ids.add(element_id)
                    if not isinstance(element.get("description"), str) or len(element["description"].strip()) < 4:
                        errors.append(f"{element_label}.description 过短或为空。")
                    if element.get("status") not in ELEMENT_STATUSES:
                        errors.append(f"{element_label}.status 无效。")
                    gaps = element.get("gaps")
                    if not isinstance(gaps, list) or not all(isinstance(item, str) and item for item in gaps):
                        errors.append(f"{element_label}.gaps 必须是字符串数组。")
                    elif element.get("status") != "supported" and not gaps:
                        errors.append(f"{element_label} 尚未充分支持时必须列明 gaps。")
                    check_refs(element.get("fact_ids"), known_facts, f"{element_label}.fact_ids")
                    check_refs(element.get("evidence_ids"), known_evidence, f"{element_label}.evidence_ids")
                    check_refs(element.get("rule_ids"), known_rules, f"{element_label}.rule_ids")
        opponent = issue.get("opponent_position")
        if not isinstance(opponent, dict):
            errors.append(f"{label}.opponent_position 必须是 object。")
        else:
            for field in ("strongest_argument", "response"):
                if not isinstance(opponent.get(field), str) or len(opponent[field].strip()) < 8:
                    errors.append(f"{label}.opponent_position.{field} 过短或为空。")
            check_refs(opponent.get("fact_ids"), known_facts, f"{label}.opponent_position.fact_ids")
            check_refs(opponent.get("evidence_ids"), known_evidence, f"{label}.opponent_position.evidence_ids")
            check_refs(opponent.get("rule_ids"), known_rules, f"{label}.opponent_position.rule_ids")
            uncertainties = opponent.get("uncertainties")
            if not isinstance(uncertainties, list) or not all(isinstance(item, str) and item for item in uncertainties):
                errors.append(f"{label}.opponent_position.uncertainties 必须是字符串数组。")
        alternatives = issue.get("alternative_paths")
        if not isinstance(alternatives, list):
            errors.append(f"{label}.alternative_paths 必须是数组。")
        elif not alternatives and (
            not isinstance(issue.get("no_alternative_reason"), str)
            or len(issue["no_alternative_reason"].strip()) < 8
        ):
            errors.append(f"{label} 无备选路径时必须说明 no_alternative_reason。")
        else:
            for alternative_index, alternative in enumerate(alternatives):
                alternative_label = f"{label}.alternative_paths[{alternative_index}]"
                if not isinstance(alternative, dict):
                    errors.append(f"{alternative_label} 必须是 object。")
                    continue
                for field in ("path", "trigger", "consequence"):
                    if not isinstance(alternative.get(field), str) or len(alternative[field].strip()) < 4:
                        errors.append(f"{alternative_label}.{field} 过短或为空。")
        if not isinstance(issue.get("failure_consequence"), str) or len(issue["failure_consequence"].strip()) < 8:
            errors.append(f"{label}.failure_consequence 过短或为空。")
    return errors


def structured_evidence_errors(state: dict[str, Any]) -> list[str]:
    """验证证据链、举证责任与争点要件之间的双向链接。"""
    errors: list[str] = []
    records = state.get("evidence", [])
    if not isinstance(records, list):
        return ["evidence 必须是数组。"]
    if not records:
        return errors
    known_facts = {
        item.get("fact_id") for item in state.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str)
    }
    known_materials = {
        item.get("material_id") for item in state.get("materials", [])
        if isinstance(item, dict) and isinstance(item.get("material_id"), str)
    }
    issue_map: dict[str, dict[str, Any]] = {}
    element_map: dict[str, tuple[str, dict[str, Any]]] = {}
    for issue in state.get("issues", []):
        if not isinstance(issue, dict) or not isinstance(issue.get("issue_id"), str):
            continue
        issue_id = issue["issue_id"]
        issue_map[issue_id] = issue
        our_position = issue.get("our_position")
        if not isinstance(our_position, dict):
            continue
        for element in our_position.get("elements", []):
            if isinstance(element, dict) and isinstance(element.get("element_id"), str):
                element_map[element["element_id"]] = (issue_id, element)

    evidence_ids = {
        item.get("evidence_id") for item in records
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    expected_by_element: dict[str, set[str]] = {element_id: set() for element_id in element_map}
    expected_for_opponent: dict[str, set[str]] = {issue_id: set() for issue_id in issue_map}

    def check_refs(value: Any, known: set[str], label: str, *, allow_empty: bool = True) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            errors.append(f"{label} 必须是字符串数组。")
            return []
        if not allow_empty and not value:
            errors.append(f"{label} 不得为空。")
        missing = sorted(set(value) - known)
        if missing:
            errors.append(f"{label} 引用不存在的 ID：{', '.join(missing)}。")
        return value

    for record_index, record in enumerate(records):
        label = f"evidence[{record_index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} 必须是 object。")
            continue
        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            errors.append(f"{label}.evidence_id 缺失。")
            continue
        if record.get("analysis_status") != "reviewed":
            errors.append(f"{label}.analysis_status 必须为 reviewed。")
        issue_id = record.get("issue_id")
        if issue_id not in issue_map:
            errors.append(f"{label}.issue_id 引用不存在的争点。")
        element_ids = check_refs(record.get("element_ids"), set(element_map), f"{label}.element_ids", allow_empty=False)
        for element_id in element_ids:
            owner = element_map.get(element_id)
            if owner is not None and owner[0] != issue_id:
                errors.append(f"{label}.element_ids 中的 {element_id} 不属于争点 {issue_id}。")
            elif owner is not None:
                expected_by_element[element_id].add(evidence_id)
        if not isinstance(record.get("proposition"), str) or len(record["proposition"].strip()) < 8:
            errors.append(f"{label}.proposition 过短或为空。")
        orientation = record.get("orientation")
        if orientation not in EVIDENCE_ORIENTATIONS:
            errors.append(f"{label}.orientation 无效。")
        elif issue_id in expected_for_opponent and orientation in {"supports_opponent_position", "cuts_both_ways"}:
            expected_for_opponent[issue_id].add(evidence_id)
        check_refs(record.get("fact_ids"), known_facts, f"{label}.fact_ids")

        burden = record.get("burden")
        if not isinstance(burden, dict):
            errors.append(f"{label}.burden 必须是 object。")
        else:
            if burden.get("primary_party") not in BURDEN_PARTIES:
                errors.append(f"{label}.burden.primary_party 无效。")
            if burden.get("control_party") not in CONTROL_PARTIES:
                errors.append(f"{label}.burden.control_party 无效。")
            burden_rule = burden.get("rule")
            if burden_rule not in BURDEN_RULES:
                errors.append(f"{label}.burden.rule 无效。")
            shifted_to = burden.get("shifted_to")
            if shifted_to is not None and shifted_to not in BURDEN_PARTIES:
                errors.append(f"{label}.burden.shifted_to 无效。")
            if burden_rule in {"employer_controlled", "burden_shift"} and shifted_to is None:
                errors.append(f"{label}.burden 发生责任转移时必须写明 shifted_to。")
            if burden_rule == "employer_controlled" and burden.get("control_party") != "employer":
                errors.append(f"{label}.burden 使用 employer_controlled 时证据控制方必须为 employer。")
            for field in ("rationale", "initial_showing", "shift_condition", "adverse_consequence"):
                if not isinstance(burden.get(field), str) or len(burden[field].strip()) < 8:
                    errors.append(f"{label}.burden.{field} 过短或为空。")

        items = record.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"{label}.items 必须是非空数组。")
        else:
            item_ids: set[str] = set()
            for item_index, item in enumerate(items):
                item_label = f"{label}.items[{item_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_label} 必须是 object。")
                    continue
                item_id = item.get("evidence_item_id")
                if not isinstance(item_id, str) or not item_id or item_id in item_ids:
                    errors.append(f"{item_label}.evidence_item_id 缺失或重复。")
                else:
                    item_ids.add(item_id)
                if not isinstance(item.get("name"), str) or len(item["name"].strip()) < 4:
                    errors.append(f"{item_label}.name 过短或为空。")
                status = item.get("status")
                if status not in EVIDENCE_ITEM_STATUSES:
                    errors.append(f"{item_label}.status 无效。")
                material_refs = check_refs(item.get("material_ids"), known_materials, f"{item_label}.material_ids")
                if status == "available" and not material_refs:
                    errors.append(f"{item_label} 标记 available 时必须关联 material_id。")
                if item.get("authenticity_status") not in AUTHENTICITY_STATUSES:
                    errors.append(f"{item_label}.authenticity_status 无效。")
                if not isinstance(item.get("purpose"), str) or len(item["purpose"].strip()) < 8:
                    errors.append(f"{item_label}.purpose 过短或为空。")
                locator = item.get("source_locator")
                if locator is not None:
                    if not isinstance(locator, dict):
                        errors.append(f"{item_label}.source_locator 必须是 object 或 null。")
                    elif locator.get("material_id") is not None and locator.get("material_id") not in material_refs:
                        errors.append(f"{item_label}.source_locator 引用了 material_ids 之外的材料。")
            if orientation == "gap_only" and any(
                isinstance(item, dict) and item.get("status") == "available" for item in items
            ):
                errors.append(f"{label} 为 gap_only 时不得包含 available 证据。")

        assessment = record.get("assessment")
        if not isinstance(assessment, dict):
            errors.append(f"{label}.assessment 必须是 object。")
        else:
            status = assessment.get("status")
            if status not in EVIDENCE_ASSESSMENT_STATUSES:
                errors.append(f"{label}.assessment.status 无效。")
            if not isinstance(assessment.get("reasoning"), str) or len(assessment["reasoning"].strip()) < 8:
                errors.append(f"{label}.assessment.reasoning 过短或为空。")
            gaps = assessment.get("gaps")
            actions = assessment.get("actions")
            if not isinstance(gaps, list) or not all(isinstance(item, str) and item for item in gaps):
                errors.append(f"{label}.assessment.gaps 必须是字符串数组。")
            if not isinstance(actions, list) or not all(isinstance(item, str) and item for item in actions):
                errors.append(f"{label}.assessment.actions 必须是字符串数组。")
            reliable_available = isinstance(items, list) and any(
                isinstance(item, dict)
                and item.get("status") == "available"
                and item.get("authenticity_status") in {"original", "copy", "derived"}
                and bool(item.get("material_ids"))
                for item in items
            )
            if status == "sufficient" and not reliable_available:
                errors.append(
                    f"{label} 证据评估为 sufficient 时至少需要一项已关联材料"
                    "且真实性状态已明确的 available 证据。"
                )
            if status != "sufficient" and (
                not isinstance(gaps, list) or not gaps or not isinstance(actions, list) or not actions
            ):
                errors.append(f"{label} 证据尚未充分时必须同时列明 gaps 和 actions。")

    for element_id, (issue_id, element) in element_map.items():
        actual = element.get("evidence_ids")
        if not isinstance(actual, list) or not all(isinstance(item, str) and item for item in actual):
            errors.append(f"构成要件 {element_id}.evidence_ids 必须是字符串数组。")
            continue
        missing = sorted(set(actual) - evidence_ids)
        if missing:
            errors.append(f"构成要件 {element_id} 引用不存在的证据链：{', '.join(missing)}。")
        expected = expected_by_element[element_id]
        if not expected:
            errors.append(f"构成要件 {element_id} 尚未建立证据链或缺口链。")
        if set(actual) != expected:
            errors.append(f"构成要件 {element_id} 与 evidence[] 的双向链接不一致。")
        if issue_id not in issue_map:
            errors.append(f"构成要件 {element_id} 所属争点不存在。")
    for issue_id, issue in issue_map.items():
        opponent = issue.get("opponent_position")
        if not isinstance(opponent, dict):
            continue
        actual = opponent.get("evidence_ids")
        if not isinstance(actual, list) or not all(isinstance(item, str) and item for item in actual):
            errors.append(f"争点 {issue_id}.opponent_position.evidence_ids 必须是字符串数组。")
            continue
        if set(actual) != expected_for_opponent[issue_id]:
            errors.append(f"争点 {issue_id} 的对方路径与 evidence[] 的双向链接不一致。")
    return errors


def structured_authority_errors(state: dict[str, Any]) -> list[str]:
    """验证法源的原文、来源、效力、地域、时间适用性与争点双向链接。"""
    errors: list[str] = []
    records = state.get("rules", [])
    if not isinstance(records, list):
        return ["rules 必须是数组。"]
    if not records:
        return errors

    issue_map: dict[str, dict[str, Any]] = {}
    element_map: dict[str, tuple[str, dict[str, Any]]] = {}
    for issue in state.get("issues", []):
        if not isinstance(issue, dict) or not isinstance(issue.get("issue_id"), str):
            continue
        issue_id = issue["issue_id"]
        issue_map[issue_id] = issue
        our_position = issue.get("our_position")
        if not isinstance(our_position, dict):
            continue
        for element in our_position.get("elements", []):
            if isinstance(element, dict) and isinstance(element.get("element_id"), str):
                element_map[element["element_id"]] = (issue_id, element)

    rule_ids = {
        item.get("rule_id") for item in records
        if isinstance(item, dict) and isinstance(item.get("rule_id"), str)
    }
    expected_by_element: dict[str, set[str]] = {element_id: set() for element_id in element_map}
    expected_for_opponent: dict[str, set[str]] = {issue_id: set() for issue_id in issue_map}

    def required_text(record: dict[str, Any], field: str, label: str, minimum: int = 4) -> None:
        if not isinstance(record.get(field), str) or len(record[field].strip()) < minimum:
            errors.append(f"{label}.{field} 过短或为空。")

    def checked_date(value: Any, label: str, *, nullable: bool = False) -> date | None:
        if value is None and nullable:
            return None
        if not valid_iso_date(value):
            errors.append(f"{label} 必须是合法 YYYY-MM-DD。")
            return None
        return date.fromisoformat(value)

    for index, record in enumerate(records):
        label = f"rules[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} 必须是 object。")
            continue
        rule_id = record.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            errors.append(f"{label}.rule_id 缺失。")
            continue
        if record.get("analysis_status") != "reviewed":
            errors.append(f"{label}.analysis_status 必须为 reviewed。")
        issue_id = record.get("issue_id")
        if issue_id not in issue_map:
            errors.append(f"{label}.issue_id 引用不存在的争点。")
        element_ids = record.get("element_ids")
        if not isinstance(element_ids, list) or not element_ids or not all(isinstance(item, str) and item for item in element_ids):
            errors.append(f"{label}.element_ids 必须是非空字符串数组。")
            element_ids = []
        for element_id in element_ids:
            owner = element_map.get(element_id)
            if owner is None:
                errors.append(f"{label}.element_ids 引用不存在的要件：{element_id}。")
            elif owner[0] != issue_id:
                errors.append(f"{label}.element_ids 中的 {element_id} 不属于争点 {issue_id}。")
        required_text(record, "proposition", label, 8)
        orientation = record.get("orientation")
        if orientation not in AUTHORITY_ORIENTATIONS:
            errors.append(f"{label}.orientation 无效。")
        adoption = record.get("adoption_status")
        verification = record.get("verification_status")
        applicability = record.get("applicability_status")
        if adoption not in AUTHORITY_ADOPTION_STATUSES:
            errors.append(f"{label}.adoption_status 无效。")
        if verification not in AUTHORITY_VERIFICATION_STATUSES:
            errors.append(f"{label}.verification_status 无效。")
        if applicability not in AUTHORITY_APPLICABILITY_STATUSES:
            errors.append(f"{label}.applicability_status 无效。")

        for field in (
            "document_id", "document_title", "issuing_authority", "article_id",
            "article_text", "temporal_basis", "applicability_reasoning", "source_name",
        ):
            required_text(record, field, label, 4 if field not in {"article_text", "applicability_reasoning"} else 12)
        required_text(record, "article_number", label, 1)
        if record.get("authority_level") not in AUTHORITY_LEVELS:
            errors.append(f"{label}.authority_level 无效。")
        if record.get("validity_status") not in AUTHORITY_VALIDITY_STATUSES:
            errors.append(f"{label}.validity_status 无效。")
        if record.get("territory_scope") not in AUTHORITY_TERRITORY_SCOPES:
            errors.append(f"{label}.territory_scope 无效。")
        if record.get("source_type") not in AUTHORITY_SOURCE_TYPES:
            errors.append(f"{label}.source_type 必须为 official 或 legal_database。")

        source_url = record.get("source_url")
        parsed = urlparse(source_url) if isinstance(source_url, str) else None
        if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label}.source_url 必须是完整 HTTP(S) URL。")
        retrieved_at = record.get("retrieved_at")
        try:
            datetime.fromisoformat(str(retrieved_at).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{label}.retrieved_at 必须是合法 ISO 时间。")

        article_text = record.get("article_text")
        digest = record.get("article_text_sha256")
        if isinstance(article_text, str):
            expected_digest = hashlib.sha256(article_text.encode("utf-8")).hexdigest()
            if digest != expected_digest:
                errors.append(f"{label}.article_text_sha256 与条文原文不一致。")

        effective_from = checked_date(record.get("effective_from"), f"{label}.effective_from", nullable=True)
        effective_to = checked_date(record.get("effective_to"), f"{label}.effective_to", nullable=True)
        relevant_date = checked_date(record.get("relevant_date"), f"{label}.relevant_date")
        if effective_from and effective_to and effective_to < effective_from:
            errors.append(f"{label} 效力终止日早于生效日。")
        if applicability == "applicable" and relevant_date:
            if effective_from and relevant_date < effective_from:
                errors.append(f"{label} 相关日期早于法源生效日。")
            if effective_to and relevant_date > effective_to:
                errors.append(f"{label} 相关日期晚于法源效力终止日。")

        jurisdictions = record.get("applicable_jurisdictions")
        if not isinstance(jurisdictions, list) or not jurisdictions or not all(isinstance(item, str) and item for item in jurisdictions):
            errors.append(f"{label}.applicable_jurisdictions 必须是非空字符串数组。")
            jurisdictions = []
        case_jurisdiction = str(state.get("jurisdiction", ""))
        if record.get("case_jurisdiction") != case_jurisdiction:
            errors.append(f"{label}.case_jurisdiction 与当前案件管辖地不一致。")
        if record.get("analysis_date") != state.get("analysis_date"):
            errors.append(f"{label}.analysis_date 与当前案件分析日不一致。")
        if record.get("territory_scope") != "national" and applicability == "applicable" and not any(
            item in case_jurisdiction or case_jurisdiction in item for item in jurisdictions
        ):
            errors.append(f"{label} 地域范围与案件管辖地不匹配。")

        # 废止复核：已确认废止的地方文件不能借旧状态或空终止日期冒充现行法源。
        if known_repeal(record):
            if record.get("validity_status") != "repealed":
                errors.append(f"{label} 已列入浙江2026-08-25废止目录，效力须标记 repealed。")
            if adoption == "adopted":
                errors.append(f"{label} 已废止地方文件仅可 reference_only 或 excluded；历史观点须另核有效依据。")
        if record.get("validity_status") in {"amended", "repealed", "expired"} and (
            not isinstance(record.get("warning"), str) or len(record["warning"].strip()) < 8
        ):
            errors.append(f"{label} 对修改／废止／失效法源必须写明 warning。")

        if adoption == "adopted":
            if verification != "verified":
                errors.append(f"{label} 正式采用的法源必须已核验。")
            if applicability != "applicable":
                errors.append(f"{label} 正式采用的法源必须明确适用于本案。")
            if record.get("validity_status") in {"not_yet_effective", "unknown"}:
                errors.append(f"{label} 未生效或效力未明的法源不得正式采用。")
            for element_id in element_ids:
                if element_id in expected_by_element:
                    expected_by_element[element_id].add(rule_id)
            if issue_id in expected_for_opponent and orientation in {"supports_opponent_position", "cuts_both_ways"}:
                expected_for_opponent[issue_id].add(rule_id)

    for element_id, (_, element) in element_map.items():
        actual = element.get("rule_ids")
        if not isinstance(actual, list) or not all(isinstance(item, str) and item for item in actual):
            errors.append(f"构成要件 {element_id}.rule_ids 必须是字符串数组。")
            continue
        missing = sorted(set(actual) - rule_ids)
        if missing:
            errors.append(f"构成要件 {element_id} 引用不存在的法源：{', '.join(missing)}。")
        expected = expected_by_element[element_id]
        if not expected:
            errors.append(f"构成要件 {element_id} 尚未关联已核验且适用的法源。")
        if set(actual) != expected:
            errors.append(f"构成要件 {element_id} 与 rules[] 的双向链接不一致。")
    for issue_id, issue in issue_map.items():
        opponent = issue.get("opponent_position")
        if not isinstance(opponent, dict):
            continue
        actual = opponent.get("rule_ids")
        if not isinstance(actual, list) or not all(isinstance(item, str) and item for item in actual):
            errors.append(f"争点 {issue_id}.opponent_position.rule_ids 必须是字符串数组。")
        elif set(actual) != expected_for_opponent[issue_id]:
            errors.append(f"争点 {issue_id} 的对方法源路径与 rules[] 双向链接不一致。")
    return errors


def structured_calculation_errors(state: dict[str, Any]) -> list[str]:
    """验证金额台账、请求和可重算结果之间的双向关系。"""
    errors: list[str] = []
    calculations = state.get("calculations", [])
    claims = state.get("claims", [])
    if not isinstance(calculations, list):
        return ["calculations 必须是数组。"]
    if not isinstance(claims, list):
        return ["claims 必须是数组。"]

    issue_ids = {
        item.get("issue_id") for item in state.get("issues", [])
        if isinstance(item, dict) and isinstance(item.get("issue_id"), str)
    }
    adopted_rules = {
        item.get("rule_id"): item for item in state.get("rules", [])
        if isinstance(item, dict)
        and isinstance(item.get("rule_id"), str)
        and item.get("adoption_status") == "adopted"
        and item.get("verification_status") == "verified"
        and item.get("applicability_status") == "applicable"
    }
    source_fields = [
        ("materials", "material_id"), ("facts", "fact_id"), ("evidence", "evidence_id"),
        ("rules", "rule_id"), ("issues", "issue_id"), ("decisions", "decision_id"),
    ]
    known_sources = {
        item[key]
        for collection, key in source_fields
        for item in state.get(collection, [])
        if isinstance(item, dict) and isinstance(item.get(key), str) and item[key]
    }
    safe_id = re.compile(r"[A-Za-z0-9_-]{1,80}")
    calculation_by_id: dict[str, dict[str, Any]] = {}
    claim_by_id: dict[str, dict[str, Any]] = {}
    prior_amounts: dict[str, Decimal] = {}

    for index, record in enumerate(calculations):
        label = f"calculations[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} 必须是 object。")
            continue
        calculation_id = record.get("calculation_id")
        claim_id = record.get("claim_id")
        if not isinstance(calculation_id, str) or not safe_id.fullmatch(calculation_id):
            errors.append(f"{label}.calculation_id 无效。")
            continue
        if calculation_id in calculation_by_id:
            errors.append(f"calculation_id 重复：{calculation_id}。")
        calculation_by_id[calculation_id] = record
        if not isinstance(claim_id, str) or not safe_id.fullmatch(claim_id):
            errors.append(f"{label}.claim_id 无效。")
        if record.get("formula_type") not in FORMULA_TYPES:
            errors.append(f"{label}.formula_type 无效。")
        if record.get("formula_version") != FORMULA_VERSION:
            errors.append(f"{label}.formula_version 必须为 {FORMULA_VERSION}。")
        status = record.get("status")
        if status not in {"calculated", "needs_confirmation"}:
            errors.append(f"{label}.status 无效。")
        record_issue_ids = record.get("issue_ids")
        if not isinstance(record_issue_ids, list) or not record_issue_ids or not all(
            isinstance(item, str) and item in issue_ids for item in record_issue_ids
        ):
            errors.append(f"{label}.issue_ids 必须引用已登记争点。")
            record_issue_ids = []
        record_rule_ids = record.get("rule_ids")
        if not isinstance(record_rule_ids, list) or not record_rule_ids or not all(
            isinstance(item, str) and item in adopted_rules for item in record_rule_ids
        ):
            errors.append(f"{label}.rule_ids 必须引用已核验且适用的法源。")
            record_rule_ids = []
        elif any(adopted_rules[item].get("issue_id") not in record_issue_ids for item in record_rule_ids):
            errors.append(f"{label}.rule_ids 与争点不匹配。")
        relevant_date = record.get("relevant_date")
        if not valid_iso_date(relevant_date):
            errors.append(f"{label}.relevant_date 无效。")
        assumptions = record.get("assumptions")
        if not isinstance(assumptions, list) or not assumptions or not all(
            isinstance(item, str) and len(item.strip()) >= 8 for item in assumptions
        ):
            errors.append(f"{label}.assumptions 必须包含具体计算口径。")
        if not isinstance(record.get("risk"), str) or len(record["risk"].strip()) < 8:
            errors.append(f"{label}.risk 过短或为空。")

        inputs = record.get("inputs")
        collected_sources: list[str] = []
        if not isinstance(inputs, dict):
            errors.append(f"{label}.inputs 必须是 object。")
            inputs = {}
        for key, value in inputs.items():
            if key == "component_ids":
                if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
                    errors.append(f"{label}.inputs.component_ids 必须是非空计算 ID 数组。")
                continue
            if not isinstance(value, dict) or "value" not in value:
                errors.append(f"{label}.inputs.{key} 缺少 value。")
                continue
            sources = value.get("source_ids")
            if not isinstance(sources, list) or not sources or not all(
                isinstance(item, str) and item in known_sources for item in sources
            ):
                errors.append(f"{label}.inputs.{key}.source_ids 必须引用已登记来源。")
            else:
                collected_sources.extend(sources)
        expected_sources = list(dict.fromkeys(collected_sources))
        if record.get("input_source_ids") != expected_sources:
            errors.append(f"{label}.input_source_ids 与逐输入来源不一致。")

        parameter_refs = record.get("parameter_refs")
        resolved = record.get("resolved_parameters")
        if not isinstance(parameter_refs, dict) or not isinstance(resolved, dict):
            errors.append(f"{label} 的 parameter_refs 与 resolved_parameters 必须是 object。")
            parameter_refs = {}
            resolved = {}
        if status == "calculated" and set(parameter_refs) != set(resolved):
            errors.append(f"{label} 的参数引用与已解析参数不一致。")
        for alias, parameter in resolved.items():
            if not isinstance(parameter, dict):
                errors.append(f"{label}.resolved_parameters.{alias} 必须是 object。")
                continue
            ref = parameter_refs.get(alias)
            if not isinstance(ref, dict) or ref.get("package_id") != parameter.get("package_id") or (
                ref.get("parameter_key") != parameter.get("parameter_key")
            ):
                errors.append(f"{label}.resolved_parameters.{alias} 与参数引用不一致。")
            digest = parameter.get("package_sha256")
            package_path = Path(str(parameter.get("package_path", ""))).expanduser()
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                errors.append(f"{label}.resolved_parameters.{alias} 缺少合法参数包哈希。")
            elif not package_path.is_file():
                errors.append(f"{label}.resolved_parameters.{alias} 的参数包文件不存在。")
            elif hashlib.sha256(package_path.read_bytes()).hexdigest() != digest:
                errors.append(f"{label}.resolved_parameters.{alias} 的参数包哈希不一致。")
            source = parameter.get("source")
            parsed = urlparse(source.get("url")) if isinstance(source, dict) and isinstance(source.get("url"), str) else None
            if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(f"{label}.resolved_parameters.{alias} 缺少官方来源 URL。")
            start = parameter.get("effective_from")
            end = parameter.get("effective_to")
            if valid_iso_date(relevant_date) and (
                not valid_iso_date(start)
                or (end is not None and not valid_iso_date(end))
                or relevant_date < start
                or (end and relevant_date > end)
            ):
                errors.append(f"{label}.resolved_parameters.{alias} 不覆盖相关日期。")
            if parameter.get("jurisdiction_scope") == "local" and not any(
                item in state.get("jurisdiction", "") or state.get("jurisdiction", "") in item
                for item in parameter.get("applicable_jurisdictions", [])
                if isinstance(item, str)
            ):
                errors.append(f"{label}.resolved_parameters.{alias} 与案件地域不匹配。")

        pending = record.get("pending_inputs")
        if not isinstance(pending, list) or not all(isinstance(item, str) and item for item in pending):
            errors.append(f"{label}.pending_inputs 必须是字符串数组。")
            pending = []
        if record.get("rounding") != "ROUND_HALF_UP" or record.get("decimal_places") != 2:
            errors.append(f"{label} 必须按 ROUND_HALF_UP 精确到分。")
        if record.get("currency") != "CNY":
            errors.append(f"{label}.currency 必须为 CNY。")

        if status == "needs_confirmation":
            if not pending:
                errors.append(f"{label} 待确认时必须列明 pending_inputs。")
            if record.get("amount") is not None or record.get("expression") is not None or record.get("steps") != []:
                errors.append(f"{label} 存在待确认输入时不得生成金额、算式或计算步骤。")
        elif status == "calculated":
            if pending:
                errors.append(f"{label} 已计算时不得仍有 pending_inputs。")
            try:
                raw, expression, steps = calculate_formula(
                    str(record.get("formula_type")), inputs, resolved, prior_amounts
                )
                expected_amount = raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                actual_amount = Decimal(str(record.get("amount")))
                if actual_amount != expected_amount or record.get("expression") != expression or record.get("steps") != steps:
                    errors.append(f"{label} 的金额、算式或中间步骤与重新计算结果不一致。")
                prior_amounts[calculation_id] = expected_amount
            except (CalculationError, InvalidOperation, ValueError, TypeError) as exc:
                errors.append(f"{label} 无法重新计算：{exc}")
        if record.get("calculation_digest") != calculation_digest(record):
            errors.append(f"{label}.calculation_digest 与计算内容不一致。")

    for index, claim in enumerate(claims):
        label = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} 必须是 object。")
            continue
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not safe_id.fullmatch(claim_id):
            errors.append(f"{label}.claim_id 无效。")
            continue
        if claim_id in claim_by_id:
            errors.append(f"claim_id 重复：{claim_id}。")
        claim_by_id[claim_id] = claim
        if claim.get("claim_type") not in {"monetary", "non_monetary"}:
            errors.append(f"{label}.claim_type 无效。")
        if claim.get("analysis_status") != "reviewed":
            errors.append(f"{label}.analysis_status 必须为 reviewed。")
        if not isinstance(claim.get("issue_ids"), list) or not claim["issue_ids"] or not all(
            isinstance(item, str) and item in issue_ids for item in claim["issue_ids"]
        ):
            errors.append(f"{label}.issue_ids 必须引用已登记争点。")
        if not isinstance(claim.get("rule_ids"), list) or not claim["rule_ids"] or not all(
            isinstance(item, str) and item in adopted_rules for item in claim["rule_ids"]
        ):
            errors.append(f"{label}.rule_ids 必须引用已核验且适用的法源。")
        if not isinstance(claim.get("risk"), str) or len(claim["risk"].strip()) < 8:
            errors.append(f"{label}.risk 过短或为空。")
        if claim.get("claim_type") == "monetary":
            calculation = calculation_by_id.get(claim.get("calculation_id"))
            if calculation is None:
                errors.append(f"{label} 未关联存在的 calculation_id。")
            elif calculation.get("claim_id") != claim_id:
                errors.append(f"{label} 与 calculations[] 的双向链接不一致。")
            elif any(
                claim.get(field) != calculation.get(field)
                for field in ("amount", "status", "issue_ids", "rule_ids", "pending_inputs")
                if field != "status"
            ) or claim.get("calculation_status") != calculation.get("status"):
                errors.append(f"{label} 的金额状态或引用与计算记录不一致。")
        elif claim.get("amount") is not None or claim.get("calculation_id") is not None:
            errors.append(f"{label} 非金额请求不得带 amount 或 calculation_id。")
    for calculation_id, calculation in calculation_by_id.items():
        claim = claim_by_id.get(calculation.get("claim_id"))
        if claim is None or claim.get("calculation_id") != calculation_id:
            errors.append(f"计算 {calculation_id} 未与 claims[] 双向关联。")
    return errors


def procedure_digest(record: dict[str, Any]) -> str:
    """计算程序分析业务内容摘要，排除审计时间字段。"""
    fields = (
        "assessment_id", "issue_id", "claim_ids", "analysis_status",
        "case_jurisdiction", "analysis_date", "limitation", "jurisdiction",
        "final_award", "interim_relief", "remedy_paths", "pending_items", "risk",
    )
    rendered = json.dumps(
        {field: record.get(field) for field in fields},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def structured_procedure_errors(state: dict[str, Any]) -> list[str]:
    """校验时效、管辖、一裁终局、先予执行和救济路径记录。"""
    errors: list[str] = []
    records = state.get("procedural_assessments", [])
    if not isinstance(records, list):
        return ["procedural_assessments 必须是数组。"]
    if not records:
        return errors

    issues = {
        item.get("issue_id"): item
        for item in state.get("issues", [])
        if isinstance(item, dict) and isinstance(item.get("issue_id"), str)
    }
    claims = {
        item.get("claim_id"): item
        for item in state.get("claims", [])
        if isinstance(item, dict) and isinstance(item.get("claim_id"), str)
    }
    adopted_rules = {
        item.get("rule_id"): item
        for item in state.get("rules", [])
        if isinstance(item, dict)
        and isinstance(item.get("rule_id"), str)
        and item.get("adoption_status") == "adopted"
        and item.get("verification_status") == "verified"
        and item.get("applicability_status") == "applicable"
    }
    safe_id = re.compile(r"[A-Za-z0-9_-]{1,80}")
    seen_ids: set[str] = set()
    covered_issues: set[str] = set()
    allowed_fields = {
        "assessment_id", "issue_id", "claim_ids", "analysis_status",
        "case_jurisdiction", "analysis_date", "limitation", "jurisdiction",
        "final_award", "interim_relief", "remedy_paths", "pending_items", "risk",
        "procedure_digest", "created_by", "created_at", "updated_by", "updated_at",
    }

    def rule_refs(value: Any, label: str, issue_id: str, *, required: bool) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            errors.append(f"{label} 必须是字符串数组。")
            return []
        if required and not value:
            errors.append(f"{label} 不得为空。")
        unknown = sorted(set(value) - set(adopted_rules))
        if unknown:
            errors.append(f"{label} 引用未核验或不适用法源：{', '.join(unknown)}。")
        mismatched = sorted(
            rule_id for rule_id in value
            if rule_id in adopted_rules and adopted_rules[rule_id].get("issue_id") != issue_id
        )
        if mismatched:
            errors.append(f"{label} 与争点 {issue_id} 不匹配：{', '.join(mismatched)}。")
        return value

    def common_section(
        section: Any,
        label: str,
        issue_id: str,
        statuses: set[str],
        *,
        not_applicable_allowed: bool,
    ) -> dict[str, Any]:
        if not isinstance(section, dict):
            errors.append(f"{label} 必须是 object。")
            return {}
        status = section.get("status")
        if status not in statuses:
            errors.append(f"{label}.status 无效。")
        not_applicable = not_applicable_allowed and status == "not_applicable"
        refs = rule_refs(section.get("basis_rule_ids"), f"{label}.basis_rule_ids", issue_id, required=not not_applicable)
        if not_applicable and refs:
            errors.append(f"{label} 不适用时不应保留 basis_rule_ids。")
        if not isinstance(section.get("analysis"), str) or len(section["analysis"].strip()) < 8:
            errors.append(f"{label}.analysis 过短或为空。")
        return section

    for index, record in enumerate(records):
        label = f"procedural_assessments[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} 必须是 object。")
            continue
        extra = sorted(set(record) - allowed_fields)
        if extra:
            errors.append(f"{label} 包含未定义字段：{', '.join(extra)}。")
        assessment_id = record.get("assessment_id")
        if not isinstance(assessment_id, str) or not safe_id.fullmatch(assessment_id):
            errors.append(f"{label}.assessment_id 无效。")
        elif assessment_id in seen_ids:
            errors.append(f"assessment_id 重复：{assessment_id}。")
        else:
            seen_ids.add(assessment_id)
        issue_id = record.get("issue_id")
        if issue_id not in issues:
            errors.append(f"{label}.issue_id 引用不存在的争点。")
            issue_id = str(issue_id or "")
        else:
            covered_issues.add(issue_id)
        claim_ids = record.get("claim_ids")
        if not isinstance(claim_ids, list) or not all(isinstance(item, str) and item in claims for item in claim_ids):
            errors.append(f"{label}.claim_ids 必须引用已登记请求。")
            claim_ids = []
        elif any(issue_id not in claims[claim_id].get("issue_ids", []) for claim_id in claim_ids):
            errors.append(f"{label}.claim_ids 与争点 {issue_id} 不匹配。")
        status = record.get("analysis_status")
        if status not in {"reviewed", "needs_confirmation"}:
            errors.append(f"{label}.analysis_status 无效。")
        if record.get("case_jurisdiction") != state.get("jurisdiction"):
            errors.append(f"{label}.case_jurisdiction 与当前案件管辖地不一致。")
        if record.get("analysis_date") != state.get("analysis_date"):
            errors.append(f"{label}.analysis_date 与当前案件分析日不一致。")

        limitation = common_section(
            record.get("limitation"), f"{label}.limitation", issue_id,
            LIMITATION_STATUSES, not_applicable_allowed=True,
        )
        limitation_status = limitation.get("status")
        trigger_date = limitation.get("trigger_date")
        deadline_date = limitation.get("deadline_date")
        if limitation_status == "not_applicable":
            if trigger_date is not None or deadline_date is not None:
                errors.append(f"{label}.limitation 不适用时起算日和截止日应为 null。")
        else:
            if trigger_date is not None and not valid_iso_date(trigger_date):
                errors.append(f"{label}.limitation.trigger_date 无效。")
            if deadline_date is not None and not valid_iso_date(deadline_date):
                errors.append(f"{label}.limitation.deadline_date 无效。")
            if limitation_status in {"in_time", "out_of_time"} and (
                not valid_iso_date(trigger_date) or not valid_iso_date(deadline_date)
            ):
                errors.append(f"{label}.limitation 得出明确时效结论时必须写明起算日和截止日。")
            if valid_iso_date(trigger_date) and valid_iso_date(deadline_date) and trigger_date > deadline_date:
                errors.append(f"{label}.limitation 截止日早于起算日。")
            analysis_date = state.get("analysis_date")
            if limitation_status == "in_time" and valid_iso_date(deadline_date) and deadline_date < analysis_date:
                errors.append(f"{label}.limitation 标记 in_time 但截止日已早于分析日。")
            if limitation_status == "out_of_time" and valid_iso_date(deadline_date) and deadline_date >= analysis_date:
                errors.append(f"{label}.limitation 标记 out_of_time 但截止日尚未早于分析日。")

        jurisdiction = common_section(
            record.get("jurisdiction"), f"{label}.jurisdiction", issue_id,
            JURISDICTION_STATUSES, not_applicable_allowed=False,
        )
        if jurisdiction.get("case_jurisdiction") != state.get("jurisdiction"):
            errors.append(f"{label}.jurisdiction.case_jurisdiction 与案件不一致。")
        if not isinstance(jurisdiction.get("forum"), str) or len(jurisdiction["forum"].strip()) < 4:
            errors.append(f"{label}.jurisdiction.forum 过短或为空。")
        common_section(
            record.get("final_award"), f"{label}.final_award", issue_id,
            BINARY_PROCEDURE_STATUSES, not_applicable_allowed=True,
        )
        common_section(
            record.get("interim_relief"), f"{label}.interim_relief", issue_id,
            BINARY_PROCEDURE_STATUSES, not_applicable_allowed=True,
        )
        remedy_paths = record.get("remedy_paths")
        if not isinstance(remedy_paths, list) or not remedy_paths or not all(
            isinstance(item, str) and len(item.strip()) >= 8 for item in remedy_paths
        ):
            errors.append(f"{label}.remedy_paths 必须包含具体救济路径。")
        pending = record.get("pending_items")
        if not isinstance(pending, list) or not all(isinstance(item, str) and item.strip() for item in pending):
            errors.append(f"{label}.pending_items 必须是字符串数组。")
            pending = []
        if status == "reviewed" and pending:
            errors.append(f"{label} 标记 reviewed 时不得仍有 pending_items。")
        if status == "needs_confirmation" and not pending:
            errors.append(f"{label} 待确认时必须列明 pending_items。")
        if not isinstance(record.get("risk"), str) or len(record["risk"].strip()) < 8:
            errors.append(f"{label}.risk 过短或为空。")
        if record.get("procedure_digest") != procedure_digest(record):
            errors.append(f"{label}.procedure_digest 与程序分析内容不一致。")

    missing_issues = sorted(set(issues) - covered_issues)
    if missing_issues:
        errors.append("程序分析未覆盖争点：" + "、".join(missing_issues) + "。")
    return errors


def validate_state(state: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["顶层必须是 JSON object。"]
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 必须为 {SCHEMA_VERSION}；1.0 状态请先执行 migrate。")
    if not isinstance(state.get("case_id"), str) or not state.get("case_id", "").strip():
        errors.append("case_id 不得为空。")
    if state.get("representation") not in REPRESENTATIONS:
        errors.append("representation 必须为 employee、employer 或 undetermined。")
    if state.get("stage") not in STAGES:
        errors.append(f"stage 必须为：{', '.join(STAGES)}。")
    if not isinstance(state.get("jurisdiction"), str) or not state.get("jurisdiction", "").strip():
        errors.append("jurisdiction 不得为空。")
    if not valid_iso_date(state.get("analysis_date")):
        errors.append("analysis_date 必须为合法 YYYY-MM-DD。")
    if state.get("risk_level") not in RISK_LEVELS:
        errors.append("risk_level 必须为 standard、complex 或 high。")
    if not isinstance(state.get("current_node"), str) or not state.get("current_node", "").strip():
        errors.append("current_node 不得为空。")
    if not isinstance(state.get("pending_nodes"), list) or not all(isinstance(node, str) and node for node in state.get("pending_nodes", [])):
        errors.append("pending_nodes 必须是字符串数组。")
    if state.get("paused") is not None and not isinstance(state.get("paused"), dict):
        errors.append("paused 必须为 null 或 object。")
    for key in BUSINESS_ARRAYS + GRAPH_ARRAYS:
        if not isinstance(state.get(key), list):
            errors.append(f"{key} 必须是数组。")
    for key in OPTIONAL_GRAPH_ARRAYS:
        if key in state and not isinstance(state.get(key), list):
            errors.append(f"{key} 必须是数组。")
    for key in OPTIONAL_BUSINESS_ARRAYS:
        if key in state and not isinstance(state.get(key), list):
            errors.append(f"{key} 必须是数组。")
    if "next_action" not in state:
        errors.append("缺少 next_action。")
    task_context = state.get("task_context")
    if task_context is not None and not isinstance(task_context, dict):
        errors.append("task_context 必须为 object 或缺省。")

    for items, key, label in [
        (state.get("facts"), "fact_id", "facts"),
        (state.get("materials"), "material_id", "materials"),
        (state.get("issues"), "issue_id", "issues"),
        (state.get("evidence"), "evidence_id", "evidence"),
        (state.get("calculations", []), "calculation_id", "calculations"),
        (state.get("claims"), "claim_id", "claims"),
        (state.get("procedural_assessments", []), "assessment_id", "procedural_assessments"),
        (state.get("node_runs"), "run_id", "node_runs"),
        (state.get("validations"), "validation_id", "validations"),
        (state.get("approvals"), "approval_id", "approvals"),
        (state.get("checkpoints"), "checkpoint_id", "checkpoints"),
        (state.get("artifacts"), "artifact_id", "artifacts"),
        (state.get("events"), "event_id", "events"),
        (state.get("node_requirement_waivers", []), "waiver_id", "node_requirement_waivers"),
    ]:
        check_unique_ids(items, key, label, errors)

    errors.extend(structured_fact_errors(state))
    for index, decision in enumerate(state.get("decisions", []) if isinstance(state.get("decisions"), list) else []):
        if not isinstance(decision, dict):
            continue
        for key in ("decision", "confirmed_on", "confirmed_by"):
            if not decision.get(key):
                errors.append(f"decisions[{index}] 缺少 {key}。")
    for index, waiver in enumerate(state.get("node_requirement_waivers", []) if isinstance(state.get("node_requirement_waivers", []), list) else []):
        if not isinstance(waiver, dict):
            continue
        for key in ("node", "requirement_id", "reason", "confirmed_by", "confirmed_at"):
            if not isinstance(waiver.get(key), str) or not waiver[key].strip():
                errors.append(f"node_requirement_waivers[{index}] 缺少 {key}。")
        if waiver.get("status") != "approved":
            errors.append(f"node_requirement_waivers[{index}].status 必须为 approved。")
        if isinstance(waiver.get("reason"), str) and len(waiver["reason"].strip()) < 8:
            errors.append(f"node_requirement_waivers[{index}].reason 过于空泛。")
    return errors


def initial_state(args: argparse.Namespace) -> dict[str, Any]:
    created_at = now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": args.case_id or new_id("labor"),
        "representation": args.representation,
        "stage": args.stage,
        "jurisdiction": args.jurisdiction,
        "analysis_date": args.analysis_date or date.today().isoformat(),
        "previous_state": None,
        "risk_level": args.risk_level,
        "current_node": "task_intake",
        "pending_nodes": [],
        "paused": None,
        "task_context": {
            "user_request": None,
            "requested_outputs": [],
            "constraints": [],
            "confirmed_by": None,
            "confirmed_at": None,
        },
        "parties": [], "goals": [], "facts": [], "materials": [], "issues": [],
        "evidence": [], "rules": [], "calculations": [], "claims": [],
        "procedural_assessments": [], "deadlines": [], "decisions": [], "deliverables": [],
        "node_runs": [], "validations": [], "approvals": [], "checkpoints": [], "artifacts": [],
        "node_requirement_waivers": [],
        "events": [{
            "event_id": new_id("evt"), "event_type": "state_initialized", "actor": args.actor,
            "occurred_at": created_at, "details": {"schema_version": SCHEMA_VERSION}
        }],
        "next_action": "询问并确认用户任务、代理立场和案件阶段；确认前不读取案件材料",
    }


def command_init(args: argparse.Namespace) -> int:
    state = initial_state(args)
    errors = validate_state(state)
    if errors:
        fail("\n".join(errors))
    write_new(Path(args.output), state)
    print(f"已创建案件图状态：{args.output}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    state = read_json(Path(args.input))
    errors = validate_state(state)
    print(json.dumps({
        "status": "valid" if not errors else "invalid",
        "schema_version": state.get("schema_version") if isinstance(state, dict) else None,
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def migrate_v1(state: dict[str, Any], actor: str) -> dict[str, Any]:
    if state.get("schema_version") != "1.0":
        fail("仅支持将 schema_version=1.0 迁移到 2.0。")
    migrated = deepcopy(state)
    migrated["schema_version"] = SCHEMA_VERSION
    migrated.setdefault("previous_state", None)
    migrated.update({"risk_level": "standard", "current_node": "task_intake", "pending_nodes": [], "paused": None})
    migrated["task_context"] = {
        "user_request": None, "requested_outputs": [], "constraints": [],
        "confirmed_by": None, "confirmed_at": None,
    }
    for key in GRAPH_ARRAYS:
        migrated[key] = []
    for key in OPTIONAL_GRAPH_ARRAYS:
        migrated[key] = []
    for key in OPTIONAL_BUSINESS_ARRAYS:
        migrated[key] = []
    migrated["events"].append({
        "event_id": new_id("evt"), "event_type": "state_migrated", "actor": actor,
        "occurred_at": now_iso(), "details": {"from": "1.0", "to": SCHEMA_VERSION}
    })
    return migrated


def command_migrate(args: argparse.Namespace) -> int:
    source = Path(args.input)
    migrated = migrate_v1(read_json(source), args.actor)
    migrated["previous_state"] = str(source.resolve())
    errors = validate_state(migrated)
    if errors:
        fail("迁移后状态无效：\n" + "\n".join(errors))
    write_new(Path(args.output), migrated)
    print(f"已生成 2.0 案件状态：{args.output}")
    return 0


def command_advance(args: argparse.Namespace) -> int:
    source = Path(args.input)
    state = read_json(source)
    errors = validate_state(state)
    if errors:
        fail("源状态无效：\n" + "\n".join(errors))
    old_stage = state["stage"]
    if STAGES.index(args.stage) < STAGES.index(old_stage):
        fail(f"拒绝将阶段从 {old_stage} 回退到 {args.stage}。")
    state["stage"] = args.stage
    state["analysis_date"] = args.analysis_date or date.today().isoformat()
    state["events"].append({
        "event_id": new_id("evt"), "event_type": "stage_advanced", "actor": args.actor,
        "occurred_at": now_iso(), "details": {"from": old_stage, "to": args.stage}
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation="stage-advance")
    print(f"已更新案件状态：{output}")
    return 0


def command_set_task(args: argparse.Namespace) -> int:
    source = Path(args.input)
    state = read_json(source)
    errors = validate_state(state)
    if errors:
        fail("源状态无效：\n" + "\n".join(errors))
    if state.get("current_node") not in {"task_intake", "material_ingestion", "intake"}:
        fail("仅允许在任务确认、材料接入或案件接入节点补录任务上下文。")
    confirmed_at = now_iso()
    state["representation"] = args.representation
    state["stage"] = args.stage
    state["jurisdiction"] = args.jurisdiction or state["jurisdiction"]
    state["task_context"] = {
        "user_request": args.user_request.strip(),
        "requested_outputs": list(args.requested_output),
        "constraints": list(args.constraint),
        "confirmed_by": args.confirmed_by,
        "confirmed_at": confirmed_at,
    }
    if args.user_request.strip() not in state["goals"]:
        state["goals"].append(args.user_request.strip())
    state["next_action"] = "通过 task_intake 门禁后进入材料接入"
    state["events"].append({
        "event_id": new_id("evt"), "event_type": "task_context_confirmed", "actor": args.confirmed_by,
        "occurred_at": confirmed_at,
        "details": {"representation": args.representation, "stage": args.stage, "jurisdiction": state["jurisdiction"]},
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation="task-confirmed")
    print(f"已更新任务确认状态：{output}")
    return 0


def command_record_decision(args: argparse.Namespace) -> int:
    """登记经用户或律师确认、可供后续计算和起草引用的决定。"""
    source = Path(args.input)
    state = read_json(source)
    errors = validate_state(state)
    if errors:
        fail("源状态无效：\n" + "\n".join(errors))
    decision = args.decision.strip()
    if len(decision) < 8:
        fail("确认内容不得为空泛，至少应说明具体事实、数值或策略口径。")
    decision_id = args.decision_id or new_id("decision")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", decision_id):
        fail("decision_id 只能包含字母、数字、下划线和连字符，且不超过 80 字符。")
    if any(item.get("decision_id") == decision_id for item in state.get("decisions", []) if isinstance(item, dict)):
        fail(f"decision_id 已存在：{decision_id}")
    confirmed_on = args.confirmed_on or date.today().isoformat()
    try:
        confirmed_on = date.fromisoformat(confirmed_on).isoformat()
    except ValueError:
        fail("confirmed_on 必须是合法 YYYY-MM-DD。")
    record = {
        "decision_id": decision_id,
        "decision": decision,
        "confirmed_on": confirmed_on,
        "confirmed_by": args.confirmed_by,
    }
    state["decisions"].append(record)
    state["events"].append({
        "event_id": new_id("evt"),
        "event_type": "decision_confirmed",
        "actor": args.confirmed_by,
        "occurred_at": now_iso(),
        "details": {"decision_id": decision_id},
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation="decision-confirmed")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="劳动争议案件图状态工具")
    sub = root.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--representation", choices=sorted(REPRESENTATIONS), default="undetermined")
    init_parser.add_argument("--stage", choices=STAGES, default="undetermined")
    init_parser.add_argument("--jurisdiction", default="浙江省")
    init_parser.add_argument("--analysis-date")
    init_parser.add_argument("--risk-level", choices=sorted(RISK_LEVELS), default="standard")
    init_parser.add_argument("--actor", default="labor-dispute-casework")
    init_parser.add_argument("--case-id")
    init_parser.add_argument("--output", required=True)
    init_parser.set_defaults(func=command_init)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--input", required=True)
    validate_parser.set_defaults(func=command_validate)
    migrate_parser = sub.add_parser("migrate")
    migrate_parser.add_argument("--input", required=True)
    migrate_parser.add_argument("--output", required=True)
    migrate_parser.add_argument("--actor", default="labor-dispute-casework")
    migrate_parser.set_defaults(func=command_migrate)
    advance_parser = sub.add_parser("advance")
    advance_parser.add_argument("--input", required=True)
    advance_parser.add_argument("--stage", choices=STAGES, required=True)
    advance_parser.add_argument("--analysis-date")
    advance_parser.add_argument("--actor", default="labor-dispute-casework")
    advance_parser.add_argument("--output", help="默认就地更新 --input，旧状态存入 .casework/history/")
    advance_parser.set_defaults(func=command_advance)
    task_parser = sub.add_parser("set-task")
    task_parser.add_argument("--input", required=True)
    task_parser.add_argument("--representation", choices=["employee", "employer"], required=True)
    task_parser.add_argument("--stage", choices=[item for item in STAGES if item != "undetermined"], required=True)
    task_parser.add_argument("--jurisdiction")
    task_parser.add_argument("--user-request", required=True)
    task_parser.add_argument("--requested-output", action="append", default=[])
    task_parser.add_argument("--constraint", action="append", default=[])
    task_parser.add_argument("--confirmed-by", default="user")
    task_parser.add_argument("--output", help="默认就地更新 --input，旧状态存入 .casework/history/")
    task_parser.set_defaults(func=command_set_task)
    decision_parser = sub.add_parser("record-decision")
    decision_parser.add_argument("--input", required=True)
    decision_parser.add_argument("--decision", required=True)
    decision_parser.add_argument("--decision-id")
    decision_parser.add_argument("--confirmed-on")
    decision_parser.add_argument("--confirmed-by", default="user")
    decision_parser.add_argument("--output", help="默认就地更新 --input，旧状态存入 .casework/history/")
    decision_parser.set_defaults(func=command_record_decision)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
