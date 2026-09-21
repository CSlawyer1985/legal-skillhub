#!/usr/bin/env python3
"""生成并核验可重算的劳动争议对抗验证报告。

本模块不调用模型补写观点，而是检查已经进入案件状态的对方最强论证、
失败边界、事实分层、事实冲突、引用关系和程序完整性是否形成真实业务结果。报告绑定当前业务
状态摘要，工作流登记和节点转换时均可重新计算，不能用任意 JSON 自报通过。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
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
)


REPORT_VERSION = "1.1"
VALIDATOR_ID = "laborpilot-adversarial-validator"
CHECK_IDS = (
    "opponent_case",
    "failure_boundaries",
    "fact_layering",
    "fact_conflicts",
    "citation_consistency",
    "procedure_completeness",
)
BUSINESS_STATE_FIELDS = (
    "case_id",
    "task_context",
    "representation",
    "stage",
    "jurisdiction",
    "analysis_date",
    "risk_level",
    "materials",
    "facts",
    "issues",
    "evidence",
    "rules",
    "calculations",
    "claims",
    "procedural_assessments",
    "deadlines",
    "decisions",
    "deliverables",
    "artifacts",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical_digest(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def business_state_digest(state: dict[str, Any]) -> str:
    """只绑定案件业务内容，排除验证登记自身造成的审计字段变化。"""
    return canonical_digest({field: state.get(field) for field in BUSINESS_STATE_FIELDS})


def finding(
    check_id: str,
    code: str,
    severity: str,
    message: str,
    *,
    issue_id: str | None = None,
    affected_nodes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "code": code,
        "severity": severity,
        "message": message,
        "issue_id": issue_id,
        "affected_nodes": affected_nodes or [],
    }


def check_status(items: list[dict[str, Any]], check_id: str) -> str:
    severities = {
        item["severity"] for item in items
        if item.get("check_id") == check_id
    }
    if "blocker" in severities:
        return "blocked"
    if "high" in severities:
        return "return"
    if "medium" in severities or "low" in severities:
        return "pass_with_risk"
    return "pass"


def overall_status(items: list[dict[str, Any]]) -> str:
    severities = {item["severity"] for item in items}
    if "blocker" in severities:
        return "blocked"
    if "high" in severities:
        return "return"
    return "pass"


def build_adversarial_report(
    state: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    facts = {
        item.get("fact_id"): item
        for item in state.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str)
    }
    findings: list[dict[str, Any]] = []
    challenge_matrix: list[dict[str, Any]] = []
    issues = [item for item in state.get("issues", []) if isinstance(item, dict)]
    if not issues:
        findings.append(finding(
            "citation_consistency",
            "NO_REVIEWED_ISSUES",
            "blocker",
            "对抗验证没有可复核的争点，不能生成空挑战矩阵并自报通过。",
            affected_nodes=["issue_analysis", "validation"],
        ))

    consistency_groups = (
        ("ISSUE_MATRIX", structured_issue_errors(state), ["issue_analysis"]),
        ("EVIDENCE_CHAIN", structured_evidence_errors(state), ["evidence_analysis"]),
        ("AUTHORITY_MATRIX", structured_authority_errors(state), ["authority_research"]),
        ("CALCULATION_LEDGER", structured_calculation_errors(state), ["claims_procedure"]),
    )
    for code, messages, affected_nodes in consistency_groups:
        for message in messages:
            findings.append(finding(
                "citation_consistency",
                code,
                "blocker",
                message,
                affected_nodes=affected_nodes,
            ))

    fact_conflict_matrix: list[dict[str, Any]] = []
    seen_conflict_pairs: set[tuple[str, str]] = set()
    for fact_id in sorted(facts):
        fact = facts[fact_id]
        refs = fact.get("conflicts_with_fact_ids")
        refs = refs if isinstance(refs, list) else []
        if refs:
            fact_conflict_matrix.append({
                "fact_id": fact_id,
                "fact_status": fact.get("status"),
                "conflicts_with_fact_ids": refs,
                "conflict_status": fact.get("conflict_status"),
                "conflict_explanation": fact.get("conflict_explanation"),
                "conflict_next_action": fact.get("conflict_next_action"),
            })
        for other_id in refs:
            if not isinstance(other_id, str):
                continue
            pair = tuple(sorted((fact_id, other_id)))
            if pair in seen_conflict_pairs:
                continue
            seen_conflict_pairs.add(pair)
            if fact.get("conflict_status") == "unresolved":
                findings.append(finding(
                    "fact_conflicts",
                    "UNRESOLVED_FACT_CONFLICT",
                    "high",
                    f"事实 {pair[0]} 与 {pair[1]} 的冲突尚未解决，须完成既定核实行动后再审批。",
                    affected_nodes=["intake", "issue_analysis", "validation"],
                ))
    for message in fact_conflict_errors(state):
        findings.append(finding(
            "fact_conflicts",
            "FACT_CONFLICT_STRUCTURE",
            "blocker",
            message,
            affected_nodes=["intake", "issue_analysis", "validation"],
        ))

    procedure_records = [
        item for item in state.get("procedural_assessments", []) if isinstance(item, dict)
    ]
    procedure_matrix = sorted([
        {
            "assessment_id": item.get("assessment_id"),
            "issue_id": item.get("issue_id"),
            "claim_ids": item.get("claim_ids"),
            "analysis_status": item.get("analysis_status"),
            "limitation_status": item.get("limitation", {}).get("status")
            if isinstance(item.get("limitation"), dict) else None,
            "jurisdiction_status": item.get("jurisdiction", {}).get("status")
            if isinstance(item.get("jurisdiction"), dict) else None,
            "final_award_status": item.get("final_award", {}).get("status")
            if isinstance(item.get("final_award"), dict) else None,
            "interim_relief_status": item.get("interim_relief", {}).get("status")
            if isinstance(item.get("interim_relief"), dict) else None,
            "remedy_paths": item.get("remedy_paths"),
            "pending_items": item.get("pending_items"),
            "procedure_digest": item.get("procedure_digest"),
        }
        for item in procedure_records
    ], key=lambda item: str(item.get("assessment_id", "")))
    procedure_errors = structured_procedure_errors(state)
    if issues and not procedure_records:
        procedure_errors.append("程序分析未覆盖任何已复核争点。")
    for message in dict.fromkeys(procedure_errors):
        findings.append(finding(
            "procedure_completeness",
            "PROCEDURE_INCOMPLETE",
            "blocker",
            message,
            affected_nodes=["claims_procedure", "validation"],
        ))
    for item in procedure_records:
        if item.get("analysis_status") != "reviewed" or item.get("pending_items"):
            findings.append(finding(
                "procedure_completeness",
                "PROCEDURE_PENDING",
                "blocker",
                f"程序分析 {item.get('assessment_id')} 尚未完成复核或仍有待确认项。",
                issue_id=item.get("issue_id") if isinstance(item.get("issue_id"), str) else None,
                affected_nodes=["claims_procedure", "validation"],
            ))

    for issue in issues:
        issue_id = issue.get("issue_id")
        if not isinstance(issue_id, str) or not issue_id:
            continue
        our_position = issue.get("our_position") if isinstance(issue.get("our_position"), dict) else {}
        opponent = issue.get("opponent_position") if isinstance(issue.get("opponent_position"), dict) else {}
        alternatives = issue.get("alternative_paths") if isinstance(issue.get("alternative_paths"), list) else []
        opponent_refs = {
            "fact_ids": opponent.get("fact_ids") if isinstance(opponent.get("fact_ids"), list) else [],
            "evidence_ids": opponent.get("evidence_ids") if isinstance(opponent.get("evidence_ids"), list) else [],
            "rule_ids": opponent.get("rule_ids") if isinstance(opponent.get("rule_ids"), list) else [],
        }
        uncertainties = opponent.get("uncertainties") if isinstance(opponent.get("uncertainties"), list) else []
        strongest = opponent.get("strongest_argument")
        response = opponent.get("response")
        if not isinstance(strongest, str) or len(strongest.strip()) < 8:
            findings.append(finding(
                "opponent_case",
                "OPPONENT_ARGUMENT_MISSING",
                "high",
                f"争点 {issue_id} 缺少可复核的对方最强论证。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))
        if not isinstance(response, str) or len(response.strip()) < 8:
            findings.append(finding(
                "opponent_case",
                "OPPONENT_RESPONSE_MISSING",
                "high",
                f"争点 {issue_id} 缺少针对对方最强论证的回应。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))
        if not any(opponent_refs.values()) and not uncertainties:
            findings.append(finding(
                "opponent_case",
                "OPPONENT_CASE_UNGROUNDED",
                "high",
                f"争点 {issue_id} 的对方最强论证既无事实、证据或法源引用，也未列明待核实事项。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))
        if isinstance(strongest, str) and isinstance(response, str) and strongest.strip() == response.strip():
            findings.append(finding(
                "opponent_case",
                "OPPONENT_RESPONSE_DUPLICATES_ARGUMENT",
                "high",
                f"争点 {issue_id} 的回应与对方最强论证完全相同，未形成对抗分析。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))

        conclusion = our_position.get("conclusion")
        failure_boundary = issue.get("failure_consequence")
        if not isinstance(failure_boundary, str) or len(failure_boundary.strip()) < 8:
            findings.append(finding(
                "failure_boundaries",
                "FAILURE_BOUNDARY_MISSING",
                "high",
                f"争点 {issue_id} 缺少具体失败边界。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))
        if not alternatives and (
            not isinstance(issue.get("no_alternative_reason"), str)
            or len(issue["no_alternative_reason"].strip()) < 8
        ):
            findings.append(finding(
                "failure_boundaries",
                "ALTERNATIVE_PATH_UNEXPLAINED",
                "high",
                f"争点 {issue_id} 没有备选路径，也未说明原因。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))
        if (
            isinstance(conclusion, str)
            and isinstance(failure_boundary, str)
            and conclusion.strip() == failure_boundary.strip()
        ):
            findings.append(finding(
                "failure_boundaries",
                "FAILURE_BOUNDARY_DUPLICATES_CONCLUSION",
                "high",
                f"争点 {issue_id} 的失败边界与我方结论完全相同，未说明结论如何失效。",
                issue_id=issue_id,
                affected_nodes=["issue_analysis", "validation"],
            ))

        element_snapshots: list[dict[str, Any]] = []
        elements = our_position.get("elements") if isinstance(our_position.get("elements"), list) else []
        for element in elements:
            if not isinstance(element, dict):
                continue
            fact_ids = element.get("fact_ids") if isinstance(element.get("fact_ids"), list) else []
            fact_layers = [
                {"fact_id": fact_id, "status": facts[fact_id].get("status")}
                for fact_id in fact_ids
                if fact_id in facts
            ]
            supported_facts = [item for item in fact_layers if item.get("status") == "supported"]
            uncertain_facts = [item for item in fact_layers if item.get("status") != "supported"]
            if element.get("status") == "supported" and not supported_facts:
                findings.append(finding(
                    "fact_layering",
                    "SUPPORTED_ELEMENT_WITHOUT_SUPPORTED_FACT",
                    "high",
                    f"争点 {issue_id} 的要件 {element.get('element_id')} 标记为 supported，但没有任何已证事实支撑。",
                    issue_id=issue_id,
                    affected_nodes=["intake", "issue_analysis", "validation"],
                ))
            elif element.get("status") == "supported" and uncertain_facts:
                findings.append(finding(
                    "fact_layering",
                    "SUPPORTED_ELEMENT_USES_UNCERTAIN_FACT",
                    "medium",
                    f"争点 {issue_id} 的要件 {element.get('element_id')} 同时引用未证或争议事实，须在审批时保留风险。",
                    issue_id=issue_id,
                    affected_nodes=["intake", "issue_analysis", "validation"],
                ))
            element_snapshots.append({
                "element_id": element.get("element_id"),
                "element_status": element.get("status"),
                "facts": fact_layers,
                "evidence_ids": element.get("evidence_ids") if isinstance(element.get("evidence_ids"), list) else [],
                "rule_ids": element.get("rule_ids") if isinstance(element.get("rule_ids"), list) else [],
            })

        challenge_matrix.append({
            "issue_id": issue_id,
            "issue": issue.get("issue"),
            "our_conclusion": conclusion,
            "opponent_strongest_argument": strongest,
            "opponent_references": opponent_refs,
            "response": response,
            "uncertainties": uncertainties,
            "failure_boundary": failure_boundary,
            "alternative_paths": alternatives,
            "elements": element_snapshots,
        })

    challenge_matrix.sort(key=lambda item: str(item.get("issue_id", "")))
    checks = [
        {
            "check_id": check_id,
            "status": check_status(findings, check_id),
            "finding_codes": [
                item["code"] for item in findings
                if item.get("check_id") == check_id
            ],
        }
        for check_id in CHECK_IDS
    ]
    return {
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_ID,
        "status": overall_status(findings),
        "generated_at": generated_at or now_iso(),
        "case_id": state.get("case_id"),
        "state_digest": business_state_digest(state),
        "checks": checks,
        "fact_conflict_matrix": fact_conflict_matrix,
        "procedure_matrix": procedure_matrix,
        "challenge_matrix": challenge_matrix,
        "findings": findings,
    }


def adversarial_report_errors(payload: Any, state: dict[str, Any]) -> list[str]:
    if not isinstance(payload, dict):
        return ["对抗验证报告必须是 JSON object。"]
    generated_at = payload.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        return ["对抗验证报告缺少 generated_at。"]
    try:
        datetime.fromisoformat(generated_at)
    except ValueError:
        return ["对抗验证报告 generated_at 不是合法 ISO 时间。"]
    expected = build_adversarial_report(state, generated_at=generated_at)
    fields = (
        "report_version",
        "validator",
        "status",
        "case_id",
        "state_digest",
        "checks",
        "fact_conflict_matrix",
        "procedure_matrix",
        "challenge_matrix",
        "findings",
    )
    return [
        f"对抗验证报告字段 {field} 与当前案件业务状态的重新计算结果不一致。"
        for field in fields
        if payload.get(field) != expected.get(field)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 实质性对抗验证器")
    parser.add_argument("--state", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    state = read_json(Path(args.state))
    if not isinstance(state, dict):
        raise SystemExit("案件状态必须是 JSON object。")
    report = build_adversarial_report(state)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        if output.exists():
            raise SystemExit(f"拒绝覆盖已有文件：{output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
