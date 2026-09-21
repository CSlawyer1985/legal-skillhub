#!/usr/bin/env python3
"""查询并执行劳动争议工作图转换，默认更新单一案件状态文件。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from case_state import (
    read_json,
    structured_authority_errors,
    structured_calculation_errors,
    structured_evidence_errors,
    structured_fact_errors,
    structured_issue_errors,
    structured_procedure_errors,
    validate_state,
    write_state,
)
from adversarial_validation import adversarial_report_errors, VALIDATOR_ID
from docx_style import validate_jls_docx


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "workflow" / "graph.json"
PACKAGE_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DELIVERY_STATUSES = {"internal_work_product", "lawyer_review_draft", "final_submission"}
FORMAL_DELIVERY_STATUSES = {"lawyer_review_draft", "final_submission"}
SOURCE_COLLECTION_IDS = {
    "materials": "material_id",
    "facts": "fact_id",
    "issues": "issue_id",
    "evidence": "evidence_id",
    "rules": "rule_id",
    "calculations": "calculation_id",
    "claims": "claim_id",
    "decisions": "decision_id",
    "deliverables": "deliverable_id",
}
STATUS_BY_EVENT = {
    "pass": "passed", "approved": "passed", "return": "returned",
    "pause": "paused", "escalate": "escalated", "blocked": "failed",
}


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def collection_record(state: dict[str, Any], collection: str, record_id: str) -> dict[str, Any] | None:
    id_key = SOURCE_COLLECTION_IDS.get(collection)
    if not id_key:
        return None
    for item in state.get(collection, []):
        if isinstance(item, dict) and item.get(id_key) == record_id:
            return item
    return None


def artifact_index(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["artifact_id"]: item
        for item in state.get("artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("artifact_id"), str)
    }


def artifact_lineage_errors(state: dict[str, Any], artifact_id: str) -> list[str]:
    """复算产物文件身份、业务来源和上游产物链，不检查验证或审批。"""
    known = artifact_index(state)
    errors: list[str] = []
    fully_checked: dict[str, bool] = {}

    def inspect(current_id: str, stack: tuple[str, ...]) -> bool:
        if current_id in stack:
            errors.append("产物上游链形成循环：" + " -> ".join((*stack, current_id)) + "。")
            return False
        if current_id in fully_checked:
            return fully_checked[current_id]
        artifact = known.get(current_id)
        if artifact is None:
            errors.append(f"引用的产物不存在：{current_id}。")
            return False

        delivery_status = artifact.get("delivery_status")
        if delivery_status not in DELIVERY_STATUSES:
            errors.append(f"产物 {current_id} 缺少合法 delivery_status。")
        path = Path(str(artifact.get("path", ""))).expanduser()
        if not path.is_file():
            errors.append(f"产物 {current_id} 文件不存在：{path}。")
        else:
            expected = artifact.get("sha256")
            actual = sha256_file(path)
            if expected != actual:
                errors.append(f"产物 {current_id} 当前文件哈希与登记值不一致。")
            if delivery_status in FORMAL_DELIVERY_STATUSES and path.suffix.lower() == ".docx":
                for message in validate_jls_docx(path, delivery_status=delivery_status):
                    errors.append(f"正式 DOCX {current_id} 未通过 JLS 版式校验：{message}")
        if delivery_status in FORMAL_DELIVERY_STATUSES:
            for field, label in (
                ("version", "版本"),
                ("generator", "生成器"),
                ("producer_version", "LaborPilot 版本"),
                ("created_by", "生成者"),
                ("created_at", "生成时间"),
            ):
                value = artifact.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"正式产物 {current_id} 缺少{label}。")

        has_business_source = False
        source_refs = artifact.get("source_refs", [])
        if not isinstance(source_refs, list):
            errors.append(f"产物 {current_id}.source_refs 必须是数组。")
            source_refs = []
        seen_sources: set[tuple[str, str]] = set()
        for index, reference in enumerate(source_refs):
            if not isinstance(reference, dict):
                errors.append(f"产物 {current_id}.source_refs[{index}] 不是 object。")
                continue
            collection = reference.get("collection")
            record_id = reference.get("record_id")
            if collection not in SOURCE_COLLECTION_IDS or not isinstance(record_id, str) or not record_id:
                errors.append(f"产物 {current_id}.source_refs[{index}] 缺少合法集合名或记录 ID。")
                continue
            key = (collection, record_id)
            if key in seen_sources:
                errors.append(f"产物 {current_id} 重复引用业务来源 {collection}:{record_id}。")
                continue
            seen_sources.add(key)
            record = collection_record(state, collection, record_id)
            if record is None:
                errors.append(f"产物 {current_id} 引用的业务来源不存在：{collection}:{record_id}。")
                continue
            has_business_source = True
            if reference.get("sha256") != canonical_digest(record):
                errors.append(f"产物 {current_id} 的业务来源摘要已过期：{collection}:{record_id}。")
            if collection == "materials":
                source_path = Path(str(record.get("source_path", ""))).expanduser()
                if not source_path.is_file() or sha256_file(source_path) != record.get("source_sha256"):
                    errors.append(f"产物 {current_id} 引用的原始材料当前哈希不匹配：{record_id}。")

        parents = artifact.get("derived_from", [])
        if not isinstance(parents, list):
            errors.append(f"产物 {current_id}.derived_from 必须是数组。")
            parents = []
        if len(parents) != len(set(parents)):
            errors.append(f"产物 {current_id}.derived_from 存在重复 ID。")
        for parent_id in parents:
            if not isinstance(parent_id, str) or not parent_id:
                errors.append(f"产物 {current_id}.derived_from 只能包含非空产物 ID。")
                continue
            has_business_source = inspect(parent_id, (*stack, current_id)) or has_business_source

        if delivery_status == "final_submission":
            draft_parents = [
                parent_id for parent_id in parents
                if isinstance(parent_id, str)
                and known.get(parent_id, {}).get("delivery_status") == "lawyer_review_draft"
            ]
            if not draft_parents:
                errors.append(f"最终提交版 {current_id} 必须直接派生自律师复核初稿。")
            elif not any(
                approval.get("gate") == "lawyer_approval"
                and approval.get("status") == "approved"
                and parent_id in approval.get("artifact_ids", [])
                and approval.get("artifact_sha256s", {}).get(parent_id) == known[parent_id].get("sha256")
                for parent_id in draft_parents
                for approval in state.get("approvals", [])
                if isinstance(approval, dict)
            ):
                errors.append(f"最终提交版 {current_id} 的直接初稿尚未形成绑定当前文件哈希的律师批准。")

        if delivery_status in FORMAL_DELIVERY_STATUSES and not has_business_source:
            errors.append(f"正式产物 {current_id} 未形成可回溯的业务来源链。")
        fully_checked[current_id] = has_business_source
        return has_business_source

    inspect(artifact_id, ())
    return errors


def load(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], Path]:
    state_path = Path(args.state)
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    graph = read_json(Path(args.graph))
    return state, graph, state_path


def transitions_for(graph: dict[str, Any], node: str) -> list[dict[str, Any]]:
    return [item for item in graph.get("transitions", []) if item.get("from") == node]


def graph_nodes(graph: dict[str, Any]) -> set[str]:
    nodes = {str(graph.get("entry_node", "")), str(graph.get("terminal_node", ""))}
    for transition in graph.get("transitions", []):
        nodes.add(str(transition.get("from", "")))
        target = transition.get("to")
        if isinstance(target, list):
            nodes.update(str(item) for item in target)
        elif target:
            nodes.add(str(target))
    return {node for node in nodes if node}


def descendants(graph: dict[str, Any], start: str) -> set[str]:
    result: set[str] = set()
    pending = [start]
    while pending:
        node = pending.pop()
        for transition in transitions_for(graph, node):
            target = transition.get("to")
            targets = target if isinstance(target, list) else [target]
            for item in targets:
                if isinstance(item, str) and item not in result and item != start:
                    result.add(item)
                    pending.append(item)
    return result


def forward_descendants(graph: dict[str, Any], start: str) -> set[str]:
    """仅沿正常完成路径判断下游，避免 return 边形成反向环。"""
    result: set[str] = set()
    pending = [start]
    while pending:
        node = pending.pop()
        for transition in transitions_for(graph, node):
            if transition.get("on") not in {"pass", "approved"}:
                continue
            target = transition.get("to")
            targets = target if isinstance(target, list) else [target]
            for item in targets:
                if isinstance(item, str) and item not in result and item != start:
                    result.add(item)
                    pending.append(item)
    return result


def node_run_outcome(run: dict[str, Any]) -> str:
    value = str(run.get("status") or run.get("result") or "").casefold()
    if value.startswith("return"):
        return "returned"
    if value.startswith("fail") or value == "blocked":
        return "failed"
    if value.startswith("pause"):
        return "paused"
    if value.startswith("escalat"):
        return "escalated"
    if value.startswith("pass"):
        return "passed"
    return value


def task_context_errors(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task = state.get("task_context")
    if not isinstance(task, dict):
        return ["缺少经用户确认的 task_context。"]
    if state.get("representation") not in {"employee", "employer"}:
        errors.append("代理立场未确认：必须明确为劳动者方或用人单位方。")
    if state.get("stage") in {None, "", "undetermined"}:
        errors.append("案件阶段未确认。")
    if not isinstance(task.get("user_request"), str) or not task.get("user_request", "").strip():
        errors.append("用户的本轮具体任务未确认。")
    if not task.get("confirmed_by") or not task.get("confirmed_at"):
        errors.append("任务上下文缺少用户确认记录。")
    return errors


def returned_nodes_with_rework_started(state: dict[str, Any]) -> set[str]:
    """返回已由工作图正式退回修复的节点。

    单纯在历史记录中写入 returned 仍应阻断下游；但通过
    workflow_transition 的 return 事件回到修复节点，是合法的返工路径，
    不能再被同一条 returned 记录锁死。
    """
    resolved: set[str] = set()
    for event in state.get("events", []):
        if not isinstance(event, dict) or event.get("event_type") != "workflow_transition":
            continue
        details = event.get("details")
        if not isinstance(details, dict) or details.get("event") != "return":
            continue
        node = details.get("from")
        if isinstance(node, str) and node:
            resolved.add(node)
    return resolved


def has_explicit_escalation_route(graph: dict[str, Any], node: str) -> bool:
    """节点若声明了升级去向，升级即为合法完成路径，由目标节点承接风险。"""
    return any(
        transition.get("on") == "escalate" and transition.get("to") != node
        for transition in transitions_for(graph, node)
    )


def workflow_blockers(state: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    current = state.get("current_node")
    blockers: list[str] = []
    if current not in graph_nodes(graph):
        blockers.append(f"当前节点不存在于工作图：{current}。")
        return blockers
    if current != "task_intake":
        blockers.extend(task_context_errors(state))
    latest: dict[str, dict[str, Any]] = {}
    for run in state.get("node_runs", []):
        if isinstance(run, dict) and isinstance(run.get("node"), str):
            latest[run["node"]] = run
    resolved_returns = returned_nodes_with_rework_started(state)
    for node, run in latest.items():
        outcome = node_run_outcome(run)
        if outcome == "returned" and node in resolved_returns:
            continue
        if outcome == "escalated" and has_explicit_escalation_route(graph, node):
            continue
        if outcome in {"returned", "failed", "paused", "escalated"} and current != node and current in descendants(graph, node):
            blockers.append(f"上游节点 {node} 最新结果为 {outcome}，未修复前不得处理 {current}。")
    if current == "claims_procedure" and state.get("pending_nodes"):
        blockers.append("证据或法源分支尚未全部完成，不得进入金额程序节点。")
    blockers.extend(completed_node_requirement_errors(state, graph))
    return blockers


def latest_gate_approved(state: dict[str, Any], gate: str) -> bool:
    return any(item.get("gate") == gate and item.get("status") == "approved" for item in reversed(state["approvals"]))


def required_validation_kinds(state: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    return graph.get("risk_routes", {}).get(state["risk_level"], {}).get("required_validations", [])


def passed_validation_kinds(state: dict[str, Any]) -> set[str]:
    latest: dict[str, dict[str, Any]] = {}
    for item in state["validations"]:
        if isinstance(item, dict) and isinstance(item.get("kind"), str):
            latest[item["kind"]] = item
    return {kind for kind, item in latest.items() if item.get("status") == "pass"}


def requirements_for(graph: dict[str, Any], node: str) -> list[dict[str, Any]]:
    requirements = graph.get("node_requirements", {}).get(node, [])
    return [item for item in requirements if isinstance(item, dict)]


def requirement_waived(state: dict[str, Any], node: str, requirement_id: str) -> bool:
    for waiver in reversed(state.get("node_requirement_waivers", [])):
        if not isinstance(waiver, dict):
            continue
        if (
            waiver.get("node") == node
            and waiver.get("requirement_id") == requirement_id
            and waiver.get("status") == "approved"
            and isinstance(waiver.get("reason"), str)
            and len(waiver["reason"].strip()) >= 8
            and waiver.get("confirmed_by")
            and waiver.get("confirmed_at")
        ):
            return True
    return False


def validation_report_is_valid(record: dict[str, Any], state: dict[str, Any]) -> bool:
    report_path = record.get("report_path")
    if not isinstance(report_path, str) or not report_path:
        return False
    path = Path(report_path).expanduser()
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    digest = record.get("report_sha256")
    if not isinstance(digest, str) or sha256_file(path) != digest:
        return False
    basic_valid = (
        isinstance(payload, dict)
        and payload.get("status") == record.get("status")
        and isinstance(payload.get("findings"), list)
    )
    if not basic_valid:
        return False
    if record.get("kind") == "adversarial":
        return not adversarial_report_errors(payload, state)
    return True


def latest_required_validations(
    state: dict[str, Any], graph: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    required = set(required_validation_kinds(state, graph))
    latest: dict[str, dict[str, Any]] = {}
    for item in state.get("validations", []):
        if isinstance(item, dict) and item.get("kind") in required:
            latest[item["kind"]] = item
    return latest


def artifact_traceability_result(
    state: dict[str, Any],
    graph: dict[str, Any],
    artifact_id: str,
    *,
    require_approval: bool = True,
) -> dict[str, Any]:
    """复算正式产物到来源、验证报告和律师审批的完整追溯链。"""
    errors = artifact_lineage_errors(state, artifact_id)
    artifact = artifact_index(state).get(artifact_id)
    if artifact is None:
        return {
            "status": "blocked",
            "artifact_id": artifact_id,
            "validation_ids": [],
            "approval_id": None,
            "errors": errors,
        }
    if artifact.get("delivery_status") not in FORMAL_DELIVERY_STATUSES:
        errors.append(f"产物 {artifact_id} 不是律师复核初稿或最终提交版。")

    latest = latest_required_validations(state, graph)
    validation_ids: list[str] = []
    for kind in required_validation_kinds(state, graph):
        record = latest.get(kind)
        if record is None:
            errors.append(f"正式产物 {artifact_id} 缺少最新的 {kind} 验证记录。")
            continue
        validation_id = record.get("validation_id")
        if isinstance(validation_id, str):
            validation_ids.append(validation_id)
        if artifact_id not in record.get("artifact_ids", []):
            errors.append(f"验证记录 {validation_id or kind} 未绑定正式产物 {artifact_id}。")
        snapshots = record.get("artifact_sha256s")
        if not isinstance(snapshots, dict) or snapshots.get(artifact_id) != artifact.get("sha256"):
            errors.append(f"验证记录 {validation_id or kind} 的产物哈希快照不匹配。")
        if record.get("status") not in {"pass", "escalate"} or not validation_report_is_valid(record, state):
            errors.append(f"验证记录 {validation_id or kind} 的报告当前无效。")

    approval: dict[str, Any] | None = None
    for item in reversed(state.get("approvals", [])):
        if (
            isinstance(item, dict)
            and item.get("gate") == "lawyer_approval"
            and item.get("status") == "approved"
            and artifact_id in item.get("artifact_ids", [])
        ):
            approval = item
            break
    if require_approval:
        if approval is None:
            errors.append(f"正式产物 {artifact_id} 缺少绑定到该文件的律师审批。")
        else:
            artifact_snapshots = approval.get("artifact_sha256s")
            if not isinstance(artifact_snapshots, dict) or artifact_snapshots.get(artifact_id) != artifact.get("sha256"):
                errors.append(f"律师审批 {approval.get('approval_id')} 的产物哈希快照不匹配。")
            approved_validations = approval.get("validation_ids")
            if not isinstance(approved_validations, list) or not set(validation_ids).issubset(set(approved_validations)):
                errors.append(f"律师审批 {approval.get('approval_id')} 未绑定全部必需验证记录。")
            validation_snapshots = approval.get("validation_report_sha256s")
            validation_by_id = {
                item.get("validation_id"): item
                for item in state.get("validations", [])
                if isinstance(item, dict) and isinstance(item.get("validation_id"), str)
            }
            if not isinstance(validation_snapshots, dict):
                errors.append(f"律师审批 {approval.get('approval_id')} 缺少验证报告哈希快照。")
            else:
                for validation_id in validation_ids:
                    record = validation_by_id.get(validation_id, {})
                    if validation_snapshots.get(validation_id) != record.get("report_sha256"):
                        errors.append(f"律师审批 {approval.get('approval_id')} 的验证报告快照不匹配：{validation_id}。")

    return {
        "status": "pass" if not errors else "blocked",
        "artifact_id": artifact_id,
        "validation_ids": validation_ids,
        "approval_id": approval.get("approval_id") if approval else None,
        "errors": errors,
    }


def requirement_is_met(
    state: dict[str, Any],
    graph: dict[str, Any],
    requirement: dict[str, Any],
    transition_output_artifact_ids: list[str],
) -> bool:
    requirement_type = requirement.get("type")
    if requirement_type == "non_empty_collection":
        collection = state.get(str(requirement.get("collection", "")))
        if not isinstance(collection, list) or not collection:
            return False
        id_key = requirement.get("id_key")
        if id_key:
            return all(
                isinstance(item, dict)
                and isinstance(item.get(str(id_key)), str)
                and bool(item[str(id_key)].strip())
                for item in collection
            )
        return True
    if requirement_type == "traceable_material":
        materials = state.get("materials", [])
        if not isinstance(materials, list) or not materials:
            return False
        for material in materials:
            if not isinstance(material, dict):
                return False
            digest = str(material.get("source_sha256", ""))
            source = Path(str(material.get("source_path", ""))).expanduser()
            record = Path(str(material.get("ingestion_record_path", ""))).expanduser()
            derivative_value = material.get("derivative_path")
            derivative = Path(str(derivative_value)).expanduser() if derivative_value else None
            try:
                record_payload = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else None
            except (OSError, json.JSONDecodeError):
                return False
            try:
                current_digest = sha256_file(source) if source.is_file() else None
                current_size = source.stat().st_size if source.is_file() else None
            except OSError:
                return False
            page_count = material.get("page_count")
            page_index = material.get("page_index")
            expected_page_numbers = (
                list(range(1, page_count + 1)) if isinstance(page_count, int) else []
            )
            page_index_valid = isinstance(page_index, list) and all(
                isinstance(page, dict)
                and page.get("text_layer_status") in {"complete", "partial", "none", "unknown"}
                and isinstance(page.get("extracted_char_count"), int)
                and page["extracted_char_count"] >= 0
                and page.get("ocr_status") in {"not_needed", "pending", "partial", "completed", "failed"}
                for page in page_index
            ) and [page.get("page_number") for page in page_index] == expected_page_numbers
            if not (
                isinstance(material.get("material_id"), str)
                and bool(material["material_id"].strip())
                and source.is_file()
                and len(digest) == 64
                and all(character in "0123456789abcdefABCDEF" for character in digest)
                and current_digest == digest
                and isinstance(material.get("source_size_bytes"), int)
                and material["source_size_bytes"] == current_size
                and material.get("file_kind") in {"text", "document", "pdf", "image", "binary"}
                and isinstance(material.get("page_start"), int)
                and material["page_start"] >= 1
                and (material.get("page_end") is None or (
                    isinstance(material.get("page_end"), int)
                    and material["page_end"] >= material["page_start"]
                ))
                and material.get("text_layer_status") in {"complete", "partial", "none", "unknown"}
                and material.get("ocr_status") in {"not_needed", "pending", "partial", "completed", "failed"}
                and material.get("visual_review_status") in {"not_started", "sampled", "critical_pages_reviewed", "completed"}
                and material.get("original_or_copy") in {"original", "copy", "unknown"}
                and isinstance(record_payload, dict)
                and record_payload.get("material_id") == material.get("material_id")
                and record_payload.get("source_sha256") == digest
                and record_payload.get("source_path") == material.get("source_path")
                and record_payload.get("source_size_bytes") == material.get("source_size_bytes")
                and record_payload.get("page_index") == page_index
                and page_index_valid
                and (derivative is None or derivative.is_file())
                and (material.get("ocr_status") not in {"partial", "completed"} or derivative is not None)
            ):
                return False
        return True
    if requirement_type == "structured_facts":
        facts = state.get("facts", [])
        if not isinstance(facts, list) or not facts:
            return False
        return not structured_fact_errors(state)
    if requirement_type == "structured_issues":
        issues = state.get("issues", [])
        return (
            isinstance(issues, list)
            and bool(issues)
            and all(
                isinstance(issue, dict) and issue.get("analysis_status") == "reviewed"
                for issue in issues
            )
            and not structured_issue_errors(state)
        )
    if requirement_type == "structured_evidence_chains":
        evidence = state.get("evidence", [])
        return (
            isinstance(evidence, list)
            and bool(evidence)
            and not structured_evidence_errors(state)
        )
    if requirement_type == "verified_authority":
        rules = state.get("rules", [])
        return (
            isinstance(rules, list)
            and any(
                isinstance(rule, dict)
                and rule.get("adoption_status") == "adopted"
                and rule.get("verification_status") == "verified"
                and rule.get("applicability_status") == "applicable"
                for rule in rules
            )
            and not structured_authority_errors(state)
        )
    if requirement_type == "claims_ready":
        claims = state.get("claims", [])
        return (
            isinstance(claims, list)
            and bool(claims)
            and not structured_calculation_errors(state)
            and all(
                isinstance(claim, dict)
                and claim.get("analysis_status") == "reviewed"
                and (
                    claim.get("claim_type") == "non_monetary"
                    or (
                        claim.get("claim_type") == "monetary"
                        and claim.get("calculation_status") == "calculated"
                        and claim.get("amount") is not None
                        and claim.get("calculation_id")
                    )
                )
                for claim in claims
            )
        )
    if requirement_type == "procedure_ready":
        records = state.get("procedural_assessments", [])
        return (
            isinstance(records, list)
            and bool(records)
            and not structured_procedure_errors(state)
            and all(
                isinstance(record, dict)
                and record.get("analysis_status") == "reviewed"
                and record.get("pending_items") == []
                for record in records
            )
        )
    if requirement_type == "transition_output_artifact":
        if not transition_output_artifact_ids:
            return False
        known = {
            item.get("artifact_id"): item
            for item in state.get("artifacts", [])
            if isinstance(item, dict) and item.get("artifact_id")
        }
        return all(
            artifact_id in known
            and Path(str(known[artifact_id].get("path", ""))).expanduser().is_file()
            and known[artifact_id].get("delivery_status") == "lawyer_review_draft"
            and not artifact_lineage_errors(state, artifact_id)
            for artifact_id in transition_output_artifact_ids
        )
    if requirement_type == "report_backed_validations":
        latest: dict[str, dict[str, Any]] = {}
        for item in state.get("validations", []):
            if isinstance(item, dict) and isinstance(item.get("kind"), str):
                latest[item["kind"]] = item
        return all(
            kind in latest
            and latest[kind].get("status") in {"pass", "escalate"}
            and validation_report_is_valid(latest[kind], state)
            for kind in required_validation_kinds(state, graph)
        )
    return False


def node_requirement_statuses(
    state: dict[str, Any],
    graph: dict[str, Any],
    node: str,
    transition_output_artifact_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    output_ids = transition_output_artifact_ids or []
    statuses = []
    for requirement in requirements_for(graph, node):
        requirement_id = str(requirement.get("id", ""))
        met = requirement_is_met(state, graph, requirement, output_ids)
        waived = (
            not met
            and bool(requirement.get("waiver_allowed"))
            and requirement_waived(state, node, requirement_id)
        )
        statuses.append({
            "id": requirement_id,
            "met": met,
            "waived": waived,
            "waiver_allowed": bool(requirement.get("waiver_allowed")),
            "message": requirement.get("message", "节点完成条件未满足。"),
        })
    return statuses


def completed_node_requirement_errors(state: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    current = state.get("current_node")
    if not isinstance(current, str):
        return []
    latest_runs: dict[str, dict[str, Any]] = {}
    for run in state.get("node_runs", []):
        if isinstance(run, dict) and isinstance(run.get("node"), str):
            latest_runs[run["node"]] = run
    errors: list[str] = []
    for node in graph.get("node_requirements", {}):
        if node == current or current not in forward_descendants(graph, node):
            continue
        run = latest_runs.get(node, {})
        output_ids = run.get("output_artifact_ids", []) if isinstance(run, dict) else []
        if not isinstance(output_ids, list):
            output_ids = []
        for status in node_requirement_statuses(state, graph, node, output_ids):
            if not status["met"] and not status["waived"]:
                errors.append(
                    f"上游节点 {node} 的完成条件 {status['id']} 当前不成立：{status['message']}"
                )
    return errors


def gate_errors(
    state: dict[str, Any],
    graph: dict[str, Any],
    node: str,
    event: str,
    transition_output_artifact_ids: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    errors.extend(workflow_blockers(state, graph))
    if node == "task_intake" and event == "pass":
        errors.extend(task_context_errors(state))
    if node == "strategy_approval" and event == "approved" and not latest_gate_approved(state, "strategy_approval"):
        errors.append("缺少 strategy_approval 的律师批准记录。")
    if node == "validation" and event == "pass":
        missing = sorted(set(required_validation_kinds(state, graph)) - passed_validation_kinds(state))
        if missing:
            errors.append("缺少已通过的验证类型：" + "、".join(missing) + "。")
    if node == "lawyer_approval" and event == "approved" and not latest_gate_approved(state, "lawyer_approval"):
        errors.append("缺少 lawyer_approval 的律师批准记录。")
    if node == "lawyer_approval" and event == "approved" and latest_gate_approved(state, "lawyer_approval"):
        approval = next(
            item for item in reversed(state["approvals"])
            if item.get("gate") == "lawyer_approval" and item.get("status") == "approved"
        )
        artifact_ids = approval.get("artifact_ids", [])
        if not artifact_ids:
            errors.append("lawyer_approval 未绑定任何正式产物。")
        for artifact_id in artifact_ids:
            trace = artifact_traceability_result(state, graph, artifact_id, require_approval=True)
            errors.extend(f"正式产物 {artifact_id}：{message}" for message in trace["errors"])
    completes_requirements = event == "pass" or (node == "validation" and event == "escalate")
    if completes_requirements:
        for status in node_requirement_statuses(
            state,
            graph,
            node,
            transition_output_artifact_ids,
        ):
            if not status["met"] and not status["waived"]:
                errors.append(f"节点完成条件 {status['id']} 未满足：{status['message']}")
    return errors


def command_route(args: argparse.Namespace) -> int:
    state, graph, _ = load(args)
    node = state["current_node"]
    blockers = workflow_blockers(state, graph)
    required_user_confirmations = task_context_errors(state) if node == "task_intake" else []
    result = {
        "status": "blocked" if blockers else "paused" if state["paused"] else "awaiting_user_input" if required_user_confirmations else "ready",
        "current_node": node,
        "pending_nodes": state["pending_nodes"],
        "risk_level": state["risk_level"],
        "allowed_transitions": [] if blockers else transitions_for(graph, node),
        "required_validations": required_validation_kinds(state, graph),
        "node_requirements": node_requirement_statuses(state, graph, node),
        "paused": state["paused"],
        "blockers": blockers,
        "required_user_confirmations": required_user_confirmations,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def resolve_target(state: dict[str, Any], target: Any, use_pending: bool = True) -> str:
    if isinstance(target, list):
        if not target:
            fail("工作图分支目标为空。")
        state["pending_nodes"] = list(target[1:]) + state["pending_nodes"]
        return target[0]
    if use_pending and state["pending_nodes"]:
        return state["pending_nodes"].pop(0)
    if not isinstance(target, str):
        fail("工作图目标节点无效。")
    return target


def command_transition(args: argparse.Namespace) -> int:
    state, graph, source = load(args)
    if state["paused"] and args.event != "resume":
        fail("案件已暂停；请先执行 resume。")
    if args.event == "resume":
        if not state["paused"]:
            fail("案件当前未暂停。")
        state["events"].append({
            "event_id": new_id("evt"), "event_type": "workflow_resumed", "actor": args.actor,
            "occurred_at": now_iso(), "details": {"checkpoint_id": state["paused"].get("checkpoint_id")}
        })
        state["paused"] = None
        output = Path(args.output) if args.output else source
        write_state(output, state, source=source, operation="workflow-resume")
        print(f"已从检查点恢复：{output}")
        return 0

    node = state["current_node"]
    matches = [item for item in transitions_for(graph, node) if item.get("on") == args.event]
    synthetic_escalation = False
    if not matches and args.event == "pause":
        matches = [{"from": node, "on": "pause", "to": node}]
    if not matches and args.event == "escalate":
        matches = [{"from": node, "on": "escalate", "to": node}]
        synthetic_escalation = True
    if len(matches) != 1:
        fail(f"节点 {node} 不存在唯一的 {args.event} 转换。")
    errors = gate_errors(state, graph, node, args.event, args.output_artifact)
    if errors:
        fail("门禁未通过：\n" + "\n".join(errors))

    completed_at = now_iso()
    state["node_runs"].append({
        "run_id": new_id("run"), "node": node, "status": STATUS_BY_EVENT.get(args.event, "passed"),
        "actor": args.actor, "started_at": args.started_at or completed_at, "completed_at": completed_at,
        "input_artifact_ids": args.input_artifact, "output_artifact_ids": args.output_artifact,
        "note": args.note,
    })
    if args.event == "pause" or synthetic_escalation:
        checkpoint_id = new_id("cp")
        checkpoint = {"checkpoint_id": checkpoint_id, "node": node, "created_at": completed_at, "reason": args.note}
        state["checkpoints"].append(checkpoint)
        default_reason = "等待律师处理升级事项" if synthetic_escalation else "等待补充信息"
        state["paused"] = {"reason": args.note or default_reason, "checkpoint_id": checkpoint_id, "paused_at": completed_at, "resume_condition": args.resume_condition}
        target = node
    else:
        if args.event != "pass":
            state["pending_nodes"] = []
        target = resolve_target(state, matches[0].get("to"), use_pending=args.event == "pass")
    state["current_node"] = target
    state["next_action"] = f"处理工作图节点：{target}"
    state["events"].append({
        "event_id": new_id("evt"), "event_type": "workflow_transition", "actor": args.actor,
        "occurred_at": completed_at, "details": {"from": node, "event": args.event, "to": target, "note": args.note}
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation=f"transition-{node}-{args.event}")
    print(f"已更新工作图状态：{output}")
    return 0


def command_approve(args: argparse.Namespace) -> int:
    state, graph, source = load(args)
    if state["current_node"] != args.gate:
        fail(f"当前节点为 {state['current_node']}，不能记录 {args.gate} 审批。")
    required_scope = set(graph.get("approval_gates", {}).get(args.gate, []))
    missing_scope = sorted(required_scope - set(args.scope))
    if args.status == "approved" and missing_scope:
        fail("批准范围不完整，缺少：" + "、".join(missing_scope) + "。")
    artifact_sha256s: dict[str, str] = {}
    validation_report_sha256s: dict[str, str] = {}
    if args.gate == "lawyer_approval" and args.status == "approved":
        if not args.artifact_id:
            fail("律师批准必须明确绑定至少一项正式产物。")
        if not args.validation_id:
            fail("律师批准必须明确绑定本次使用的验证记录。")
        known_artifacts = artifact_index(state)
        known_validations = {
            item.get("validation_id"): item
            for item in state.get("validations", [])
            if isinstance(item, dict) and isinstance(item.get("validation_id"), str)
        }
        required_latest = latest_required_validations(state, graph)
        required_ids = {
            item.get("validation_id") for item in required_latest.values()
            if isinstance(item.get("validation_id"), str)
        }
        if not required_ids.issubset(set(args.validation_id)):
            fail("律师批准未绑定当前风险等级要求的全部最新验证记录。")
        for artifact_id in args.artifact_id:
            artifact = known_artifacts.get(artifact_id)
            if artifact is None:
                fail(f"律师批准引用的产物不存在：{artifact_id}")
            if artifact.get("delivery_status") not in FORMAL_DELIVERY_STATUSES:
                fail(f"律师批准只能绑定律师复核初稿或最终提交版：{artifact_id}")
            trace = artifact_traceability_result(state, graph, artifact_id, require_approval=False)
            if trace["errors"]:
                fail("正式产物在审批前未通过追溯校验：\n" + "\n".join(trace["errors"]))
            artifact_sha256s[artifact_id] = artifact["sha256"]
        for validation_id in args.validation_id:
            validation = known_validations.get(validation_id)
            if validation is None:
                fail(f"律师批准引用的验证记录不存在：{validation_id}")
            if not validation_report_is_valid(validation, state):
                fail(f"律师批准引用的验证报告当前无效：{validation_id}")
            if not set(args.artifact_id).issubset(set(validation.get("artifact_ids", []))):
                fail(f"验证记录未覆盖本次批准的全部正式产物：{validation_id}")
            validation_report_sha256s[validation_id] = validation.get("report_sha256")
    approval_record = {
        "approval_id": new_id("approval"), "gate": args.gate, "status": args.status,
        "approved_by": args.approved_by, "decided_at": now_iso(), "scope": args.scope, "note": args.note,
        "artifact_ids": args.artifact_id,
        "artifact_sha256s": artifact_sha256s,
        "validation_ids": args.validation_id,
        "validation_report_sha256s": validation_report_sha256s,
    }
    state["approvals"].append(approval_record)
    state["events"].append({
        "event_id": new_id("evt"), "event_type": "approval_recorded", "actor": args.approved_by,
        "occurred_at": now_iso(), "details": {"gate": args.gate, "status": args.status, "scope": args.scope}
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation=f"approval-{args.gate}")
    print(f"已记录审批：{output}")
    return 0


def command_artifact(args: argparse.Namespace) -> int:
    state, _, source = load(args)
    artifact_path = Path(args.path).expanduser().resolve()
    if not artifact_path.is_file():
        fail(f"产物文件不存在：{artifact_path}")
    artifact_id = args.artifact_id or new_id("artifact")
    if artifact_id in artifact_index(state):
        fail(f"artifact_id 已存在：{artifact_id}")
    if args.delivery_status in FORMAL_DELIVERY_STATUSES and not args.generator.strip():
        fail("正式产物必须登记实际生成器。")
    source_refs: list[dict[str, str]] = []
    seen_sources: set[tuple[str, str]] = set()
    for value in args.source_ref:
        if ":" not in value:
            fail(f"业务来源必须使用 collection:record_id 格式：{value}")
        collection, record_id = value.split(":", 1)
        record = collection_record(state, collection, record_id)
        if collection not in SOURCE_COLLECTION_IDS or not record_id or record is None:
            fail(f"业务来源不存在或类型不受支持：{value}")
        key = (collection, record_id)
        if key in seen_sources:
            fail(f"业务来源重复：{value}")
        seen_sources.add(key)
        source_refs.append({
            "collection": collection,
            "record_id": record_id,
            "sha256": canonical_digest(record),
        })
    sha256 = sha256_file(artifact_path)
    artifact = {
        "artifact_id": artifact_id, "kind": args.kind,
        "delivery_status": args.delivery_status,
        "path": str(artifact_path), "version": args.version, "sha256": sha256,
        "generator": args.generator.strip(), "producer_version": PACKAGE_VERSION,
        "created_by": args.created_by, "created_at": now_iso(),
        "derived_from": args.derived_from, "source_refs": source_refs,
    }
    state["artifacts"].append(artifact)
    lineage_errors = artifact_lineage_errors(state, artifact_id)
    if lineage_errors:
        fail("产物追溯登记无效：\n" + "\n".join(lineage_errors))
    state["events"].append({
        "event_id": new_id("evt"), "event_type": "artifact_registered", "actor": args.created_by,
        "occurred_at": now_iso(), "details": {"artifact_id": artifact["artifact_id"], "sha256": sha256}
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation="artifact-registered")
    print(json.dumps(artifact, ensure_ascii=False, indent=2))
    return 0


def command_record_validation(args: argparse.Namespace) -> int:
    state, _, source = load(args)
    findings: list[dict[str, Any]] = []
    report_path: str | None = None
    report_sha256: str | None = None
    if args.report:
        report = Path(args.report).expanduser().resolve()
        if not report.is_file():
            fail(f"验证报告不存在：{report}")
        payload = read_json(report)
        if (
            not isinstance(payload, dict)
            or "status" not in payload
            or "findings" not in payload
            or not isinstance(payload.get("findings"), list)
        ):
            fail("验证报告必须是含 status 和 findings 数组的 JSON object。")
        findings = payload.get("findings", [])
        if args.status is None:
            args.status = payload.get("status")
        elif payload.get("status") and payload.get("status") != args.status:
            fail("--status 与验证报告中的 status 不一致。")
        report_path = str(report)
        report_sha256 = sha256_file(report)
        if args.kind == "adversarial":
            errors = adversarial_report_errors(payload, state)
            if errors:
                fail("对抗验证报告未通过重新计算校验：\n" + "\n".join(errors))
            if args.validator != VALIDATOR_ID:
                fail(f"对抗验证报告必须由 {VALIDATOR_ID} 登记。")
    if args.status not in {"pass", "return", "pause", "escalate", "blocked"}:
        fail("必须通过 --status 或报告提供合法验证状态。")
    if args.status in {"pass", "escalate"} and not report_path:
        fail("验证结论为 pass 或 escalate 时必须提供含 status 和 findings 的 JSON 报告。")
    known_artifacts = artifact_index(state)
    artifact_sha256s: dict[str, str] = {}
    for artifact_id in args.artifact_id:
        artifact = known_artifacts.get(artifact_id)
        if artifact is None:
            fail(f"验证记录引用的产物不存在：{artifact_id}")
        lineage_errors = artifact_lineage_errors(state, artifact_id)
        if lineage_errors:
            fail("验证前产物追溯校验未通过：\n" + "\n".join(lineage_errors))
        artifact_sha256s[artifact_id] = artifact.get("sha256")
    formal_ids = [
        artifact_id for artifact_id, artifact in known_artifacts.items()
        if artifact.get("delivery_status") in FORMAL_DELIVERY_STATUSES
    ]
    if args.status in {"pass", "escalate"} and formal_ids and not args.artifact_id:
        fail("验证正式产物时必须通过 --artifact-id 明确绑定实际文件。")
    record = {
        "validation_id": new_id("validation"), "kind": args.kind, "validator": args.validator,
        "status": args.status, "checked_at": now_iso(), "findings": findings,
        "artifact_ids": args.artifact_id, "artifact_sha256s": artifact_sha256s,
        "report_path": report_path,
        "report_sha256": report_sha256, "note": args.note,
    }
    state["validations"].append(record)
    state["events"].append({
        "event_id": new_id("evt"), "event_type": "validation_recorded", "actor": args.validator,
        "occurred_at": now_iso(), "details": {"validation_id": record["validation_id"], "kind": args.kind, "status": args.status}
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation=f"validation-{args.kind}")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def command_trace_artifact(args: argparse.Namespace) -> int:
    state, graph, _ = load(args)
    result = artifact_traceability_result(state, graph, args.artifact_id, require_approval=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


def command_record_waiver(args: argparse.Namespace) -> int:
    state, graph, source = load(args)
    node = state["current_node"]
    requirements = {
        item.get("id"): item
        for item in requirements_for(graph, node)
        if item.get("id")
    }
    requirement = requirements.get(args.requirement)
    if not requirement:
        fail(f"当前节点 {node} 不存在完成条件 {args.requirement}。")
    if not requirement.get("waiver_allowed"):
        fail(f"完成条件 {args.requirement} 不允许豁免。")
    reason = args.reason.strip()
    if len(reason) < 8:
        fail("豁免理由不得为空泛，至少应说明无相应材料或记录的具体原因。")
    waiver = {
        "waiver_id": new_id("waiver"),
        "node": node,
        "requirement_id": args.requirement,
        "status": "approved",
        "reason": reason,
        "confirmed_by": args.confirmed_by,
        "confirmed_at": now_iso(),
    }
    state.setdefault("node_requirement_waivers", []).append(waiver)
    state["events"].append({
        "event_id": new_id("evt"),
        "event_type": "node_requirement_waiver_recorded",
        "actor": args.confirmed_by,
        "occurred_at": waiver["confirmed_at"],
        "details": {
            "waiver_id": waiver["waiver_id"],
            "node": node,
            "requirement_id": args.requirement,
        },
    })
    output = Path(args.output) if args.output else source
    write_state(output, state, source=source, operation=f"waiver-{node}-{args.requirement}")
    print(json.dumps(waiver, ensure_ascii=False, indent=2))
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state", required=True)
    parser.add_argument("--graph", default=str(DEFAULT_GRAPH))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="劳动争议办案工作图")
    sub = root.add_subparsers(dest="command", required=True)
    route = sub.add_parser("route")
    add_common(route)
    route.set_defaults(func=command_route)
    transition = sub.add_parser("transition")
    add_common(transition)
    transition.add_argument("--event", required=True, choices=["pass", "return", "pause", "escalate", "approved", "resume"])
    transition.add_argument("--actor", required=True)
    transition.add_argument("--started-at")
    transition.add_argument("--note")
    transition.add_argument("--resume-condition")
    transition.add_argument("--input-artifact", action="append", default=[])
    transition.add_argument("--output-artifact", action="append", default=[])
    transition.add_argument("--output", help="默认就地更新 --state，旧状态存入 .casework/history/")
    transition.set_defaults(func=command_transition)
    approve = sub.add_parser("approve")
    add_common(approve)
    approve.add_argument("--gate", required=True, choices=["strategy_approval", "lawyer_approval"])
    approve.add_argument("--status", required=True, choices=["approved", "returned", "rejected"])
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--scope", action="append", required=True)
    approve.add_argument("--note")
    approve.add_argument("--artifact-id", action="append", default=[])
    approve.add_argument("--validation-id", action="append", default=[])
    approve.add_argument("--output", help="默认就地更新 --state，旧状态存入 .casework/history/")
    approve.set_defaults(func=command_approve)
    artifact = sub.add_parser("register-artifact")
    add_common(artifact)
    artifact.add_argument("--path", required=True)
    artifact.add_argument("--kind", required=True)
    artifact.add_argument("--version", required=True)
    artifact.add_argument("--delivery-status", choices=sorted(DELIVERY_STATUSES), default="internal_work_product")
    artifact.add_argument("--generator", default="")
    artifact.add_argument("--created-by", required=True)
    artifact.add_argument("--artifact-id")
    artifact.add_argument("--derived-from", action="append", default=[])
    artifact.add_argument("--source-ref", action="append", default=[])
    artifact.add_argument("--output", help="默认就地更新 --state，旧状态存入 .casework/history/")
    artifact.set_defaults(func=command_artifact)
    validation = sub.add_parser("record-validation")
    add_common(validation)
    validation.add_argument("--kind", required=True, choices=["deterministic", "adversarial", "authority_second_pass"])
    validation.add_argument("--validator", required=True)
    validation.add_argument("--status", choices=["pass", "return", "pause", "escalate", "blocked"])
    validation.add_argument("--report")
    validation.add_argument("--artifact-id", action="append", default=[])
    validation.add_argument("--note")
    validation.add_argument("--output", help="默认就地更新 --state，旧状态存入 .casework/history/")
    validation.set_defaults(func=command_record_validation)
    trace_artifact = sub.add_parser("trace-artifact")
    add_common(trace_artifact)
    trace_artifact.add_argument("--artifact-id", required=True)
    trace_artifact.set_defaults(func=command_trace_artifact)
    waiver = sub.add_parser("record-waiver")
    add_common(waiver)
    waiver.add_argument("--requirement", required=True)
    waiver.add_argument("--reason", required=True)
    waiver.add_argument("--confirmed-by", required=True)
    waiver.add_argument("--output", help="默认就地更新 --state，旧状态存入 .casework/history/")
    waiver.set_defaults(func=command_record_waiver)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
