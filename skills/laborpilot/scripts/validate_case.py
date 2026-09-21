#!/usr/bin/env python3
"""对案件图状态执行独立的确定性一致性检查。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from case_state import (
    fact_conflict_errors,
    read_json,
    structured_authority_errors,
    structured_calculation_errors,
    structured_evidence_errors,
    structured_issue_errors,
    structured_procedure_errors,
    validate_state,
)
from workflow_graph import (
    DEFAULT_GRAPH,
    FORMAL_DELIVERY_STATUSES,
    artifact_lineage_errors,
    artifact_traceability_result,
    task_context_errors,
    workflow_blockers,
)


def finding(code: str, severity: str, message: str, affected: list[str] | None = None) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "affected_nodes": affected or []}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ids(items: Any, key: str) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {item.get(key) for item in items if isinstance(item, dict) and isinstance(item.get(key), str)}


def approved(state: dict[str, Any], gate: str) -> bool:
    return any(
        isinstance(item, dict)
        and item.get("gate") == gate
        and item.get("status") == "approved"
        for item in state.get("approvals", [])
    )


def validate_artifacts(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    graph = read_json(DEFAULT_GRAPH)
    for index, artifact in enumerate(state.get("artifacts", [])):
        if not isinstance(artifact, dict):
            findings.append(finding("ARTIFACT_OBJECT", "blocker", f"artifacts[{index}] 不是 object。"))
            continue
        path = Path(str(artifact.get("path", ""))).expanduser()
        if not path.is_file():
            findings.append(finding("ARTIFACT_MISSING", "high", f"产物文件不存在：{path}。", ["validation"]))
            continue
        expected = artifact.get("sha256")
        actual = sha256_file(path)
        if expected != actual:
            findings.append(finding("ARTIFACT_HASH", "high", f"产物哈希与登记值不一致：{path}。", ["validation"]))
        artifact_id = artifact.get("artifact_id")
        if isinstance(artifact_id, str):
            for message in artifact_lineage_errors(state, artifact_id):
                findings.append(finding("ARTIFACT_LINEAGE", "blocker", message, ["drafting", "validation"]))
            if (
                state.get("current_node") == "stage_close"
                and artifact.get("delivery_status") in FORMAL_DELIVERY_STATUSES
            ):
                trace = artifact_traceability_result(state, graph, artifact_id, require_approval=True)
                for message in trace["errors"]:
                    findings.append(finding("ARTIFACT_TRACE", "blocker", message, ["lawyer_approval", "stage_close"]))


def validate_links(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    fact_ids = ids(state.get("facts"), "fact_id")
    evidence_ids = ids(state.get("evidence"), "evidence_id")
    issue_ids = ids(state.get("issues"), "issue_id")
    rule_ids = ids(state.get("rules"), "rule_id") | ids(state.get("rules"), "article_id")
    for index, claim in enumerate(state.get("claims", [])):
        if not isinstance(claim, dict):
            continue
        for field, known, code in [
            ("fact_ids", fact_ids, "CLAIM_FACT_LINK"),
            ("evidence_ids", evidence_ids, "CLAIM_EVIDENCE_LINK"),
            ("issue_ids", issue_ids, "CLAIM_ISSUE_LINK"),
            ("rule_ids", rule_ids, "CLAIM_RULE_LINK"),
        ]:
            refs = claim.get(field, [])
            if refs is not None and not isinstance(refs, list):
                findings.append(finding(code, "high", f"claims[{index}].{field} 必须是数组。", ["issue_analysis"]))
                continue
            invalid = [ref for ref in refs or [] if not isinstance(ref, str)]
            if invalid:
                findings.append(finding(code, "high", f"claims[{index}].{field} 只能包含字符串 ID。", ["issue_analysis"]))
            missing = sorted({ref for ref in refs or [] if isinstance(ref, str)} - known)
            if missing:
                findings.append(finding(code, "high", f"claims[{index}].{field} 引用不存在的 ID：{', '.join(missing)}。", ["issue_analysis"]))
        if claim.get("amount") is not None and not claim.get("calculation_id"):
            findings.append(finding("CLAIM_CALCULATION", "high", f"claims[{index}] 含金额但缺少 calculation_id。", ["claims_procedure"]))


def validate_rules(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    for message in structured_authority_errors(state):
        findings.append(finding("AUTHORITY_MATRIX", "blocker", message, ["authority_research"]))


def validate_calculations(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    for message in structured_calculation_errors(state):
        findings.append(finding("CALCULATION_LEDGER", "blocker", message, ["claims_procedure"]))
    for item in state.get("calculations", []):
        if isinstance(item, dict) and item.get("status") == "needs_confirmation":
            findings.append(finding(
                "CALCULATION_PENDING", "high",
                f"计算 {item.get('calculation_id')} 仍有待确认输入，不得作为确定金额使用。",
                ["claims_procedure"],
            ))


def validate_procedure(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    for message in structured_procedure_errors(state):
        findings.append(finding("PROCEDURE_ANALYSIS", "blocker", message, ["claims_procedure"]))
    for item in state.get("procedural_assessments", []):
        if isinstance(item, dict) and item.get("analysis_status") == "needs_confirmation":
            findings.append(finding(
                "PROCEDURE_PENDING", "blocker",
                f"程序分析 {item.get('assessment_id')} 仍有待确认项。",
                ["claims_procedure"],
            ))


def validate_gates(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    node = state.get("current_node")
    after_strategy = {"drafting", "validation", "lawyer_approval", "stage_close"}
    if node in after_strategy and not approved(state, "strategy_approval"):
        findings.append(finding("STRATEGY_GATE", "blocker", "起草或后续节点缺少策略审批。", ["strategy_approval"]))
    if node == "stage_close" and not approved(state, "lawyer_approval"):
        findings.append(finding("LAWYER_GATE", "blocker", "阶段结案前缺少律师交付审批。", ["lawyer_approval"]))


def validate_material_traceability(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    for index, material in enumerate(state.get("materials", [])):
        if not isinstance(material, dict):
            continue
        source = Path(str(material.get("source_path", ""))).expanduser()
        expected = material.get("source_sha256")
        if not source.is_file():
            findings.append(finding(
                "MATERIAL_SOURCE_MISSING", "blocker",
                f"materials[{index}] 原始材料不存在：{source}。",
                ["material_ingestion"],
            ))
        elif not expected:
            findings.append(finding(
                "MATERIAL_HASH", "high",
                f"materials[{index}] 已登记原始路径但缺少 source_sha256。",
                ["material_ingestion"],
            ))
        else:
            actual = sha256_file(source)
            if expected != actual:
                findings.append(finding(
                    "MATERIAL_HASH_MISMATCH", "blocker",
                    f"materials[{index}] 原始材料当前哈希与接入登记不一致：{source}。",
                    ["material_ingestion"],
                ))
            if material.get("source_size_bytes") != source.stat().st_size:
                findings.append(finding(
                    "MATERIAL_SIZE_MISMATCH", "high",
                    f"materials[{index}] 原始材料大小与接入登记不一致：{source}。",
                    ["material_ingestion"],
                ))
        required_metadata = {
            "file_kind": {"text", "document", "pdf", "image", "binary"},
            "text_layer_status": {"complete", "partial", "none", "unknown"},
            "ocr_status": {"not_needed", "pending", "partial", "completed", "failed"},
            "visual_review_status": {"not_started", "sampled", "critical_pages_reviewed", "completed"},
            "original_or_copy": {"original", "copy", "unknown"},
        }
        for field, allowed in required_metadata.items():
            if material.get(field) not in allowed:
                findings.append(finding(
                    "MATERIAL_METADATA", "high",
                    f"materials[{index}].{field} 缺失或无效。",
                    ["material_ingestion"],
                ))
        record_path = Path(str(material.get("ingestion_record_path", ""))).expanduser()
        if not record_path.is_file():
            findings.append(finding(
                "MATERIAL_RECORD", "high",
                f"materials[{index}] 缺少真实材料接入记录。",
                ["material_ingestion"],
            ))
        else:
            try:
                record_payload = json.loads(record_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                record_payload = None
            if not isinstance(record_payload, dict) or any(
                record_payload.get(field) != material.get(field)
                for field in (
                    "material_id", "source_path", "source_sha256", "source_size_bytes", "page_index"
                )
            ):
                findings.append(finding(
                    "MATERIAL_RECORD_MISMATCH", "blocker",
                    f"materials[{index}] 的逐材料接入记录与案件状态不一致。",
                    ["material_ingestion"],
                ))
        page_start = material.get("page_start")
        page_end = material.get("page_end")
        if not isinstance(page_start, int) or page_start < 1 or (
            page_end is not None and (not isinstance(page_end, int) or page_end < page_start)
        ):
            findings.append(finding(
                "MATERIAL_PAGE_RANGE", "high",
                f"materials[{index}] 缺少合法页码范围。",
                ["material_ingestion"],
            ))
        page_count = material.get("page_count")
        page_index = material.get("page_index")
        expected_numbers = list(range(1, page_count + 1)) if isinstance(page_count, int) else []
        actual_numbers = (
            [page.get("page_number") for page in page_index if isinstance(page, dict)]
            if isinstance(page_index, list)
            else None
        )
        valid_page_items = isinstance(page_index, list) and all(
            isinstance(page, dict)
            and page.get("text_layer_status") in {"complete", "partial", "none", "unknown"}
            and isinstance(page.get("extracted_char_count"), int)
            and page["extracted_char_count"] >= 0
            and page.get("ocr_status") in {"not_needed", "pending", "partial", "completed", "failed"}
            for page in page_index
        )
        if not valid_page_items or actual_numbers != expected_numbers:
            findings.append(finding(
                "MATERIAL_PAGE_INDEX", "high",
                f"materials[{index}] 缺少与页数一致的连续分页索引。",
                ["material_ingestion"],
            ))
        derivative_value = material.get("derivative_path")
        derivative = Path(str(derivative_value)).expanduser() if derivative_value else None
        if derivative is not None and not derivative.is_file():
            findings.append(finding(
                "MATERIAL_DERIVATIVE_MISSING", "high",
                f"materials[{index}] 登记的派生文本不存在：{derivative}。",
                ["material_ingestion"],
            ))
        if material.get("ocr_status") in {"partial", "completed"} and derivative is None:
            findings.append(finding(
                "OCR_DERIVATIVE", "high",
                f"materials[{index}] 已记录 OCR 结果但缺少 derivative_path。",
                ["material_ingestion"],
            ))


def validate_fact_provenance(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    material_ids = ids(state.get("materials"), "material_id")
    for index, fact in enumerate(state.get("facts", [])):
        if not isinstance(fact, dict):
            continue
        statement = fact.get("statement")
        if not isinstance(statement, str) or len(statement.strip()) < 4:
            findings.append(finding(
                "FACT_STATEMENT", "high",
                f"facts[{index}] 缺少可复核的事实陈述。",
                ["intake"],
            ))
        sources = fact.get("sources")
        if not isinstance(sources, list):
            continue
        missing = sorted({item for item in sources if isinstance(item, str)} - material_ids)
        if missing:
            findings.append(finding(
                "FACT_SOURCE", "high",
                f"facts[{index}] 引用不存在的材料 ID：{', '.join(missing)}。",
                ["intake"],
            ))
        if fact.get("status") == "supported" and not sources:
            findings.append(finding(
                "FACT_SUPPORTED_SOURCE", "blocker",
                f"facts[{index}] 标记为 supported 但没有材料来源。",
                ["intake"],
            ))
    for message in fact_conflict_errors(state):
        findings.append(finding("FACT_CONFLICT", "blocker", message, ["intake", "validation"]))


def validate_issue_matrix(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    for message in structured_issue_errors(state):
        findings.append(finding(
            "ISSUE_MATRIX",
            "blocker",
            message,
            ["issue_analysis"],
        ))


def validate_evidence_chains(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    for message in structured_evidence_errors(state):
        findings.append(finding(
            "EVIDENCE_CHAIN",
            "blocker",
            message,
            ["evidence_analysis"],
        ))


def validate_workflow_state(state: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    graph = read_json(DEFAULT_GRAPH)
    if state.get("current_node") == "task_intake":
        for message in task_context_errors(state):
            findings.append(finding("TASK_CONTEXT", "blocker", message, ["task_intake"]))
    for message in workflow_blockers(state, graph):
        findings.append(finding("WORKFLOW_REACHABILITY", "blocker", message, ["workflow"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="劳动争议案件独立确定性验证")
    parser.add_argument("--state", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    state = read_json(Path(args.state))
    findings: list[dict[str, Any]] = []
    for message in validate_state(state):
        findings.append(finding("STATE_SCHEMA", "blocker", message))
    if isinstance(state, dict):
        validate_artifacts(state, findings)
        validate_links(state, findings)
        validate_rules(state, findings)
        validate_calculations(state, findings)
        validate_procedure(state, findings)
        validate_gates(state, findings)
        validate_material_traceability(state, findings)
        validate_fact_provenance(state, findings)
        validate_issue_matrix(state, findings)
        validate_evidence_chains(state, findings)
        validate_workflow_state(state, findings)
    severities = {item["severity"] for item in findings}
    status = "blocked" if "blocker" in severities else "return" if "high" in severities else "pass"
    result = {"status": status, "validator": "deterministic", "findings": findings}
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        if output.exists():
            raise SystemExit(f"拒绝覆盖已有文件：{output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
