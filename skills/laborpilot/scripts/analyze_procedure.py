#!/usr/bin/env python3
"""记录并校验劳动争议时效、管辖和程序路径。

`--scaffold` 只生成待复核骨架；`--input` 接收律师／Agent 基于
已核验法源作出的程序判断。脚本不自动选择程序策略，只负责检查
争点覆盖、法源引用、日期结论、地域和完整性，并生成可追溯台账。
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import uuid
from typing import Any

from case_state import (
    procedure_digest,
    read_json,
    structured_authority_errors,
    structured_calculation_errors,
    structured_evidence_errors,
    structured_issue_errors,
    structured_procedure_errors,
    validate_state,
    write_new,
    write_state,
)


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def casework_root(state_path: Path) -> Path:
    return state_path.parent if state_path.parent.name == ".casework" else state_path.parent / ".casework"


def scaffold_payload(state: dict[str, Any]) -> dict[str, Any]:
    claims_by_issue: dict[str, list[str]] = {}
    for claim in state.get("claims", []):
        if not isinstance(claim, dict) or not isinstance(claim.get("claim_id"), str):
            continue
        for issue_id in claim.get("issue_ids", []):
            if isinstance(issue_id, str):
                claims_by_issue.setdefault(issue_id, []).append(claim["claim_id"])
    return {
        "schema_version": "1.0",
        "case_id": state.get("case_id"),
        "analysis_date": state.get("analysis_date"),
        "case_jurisdiction": state.get("jurisdiction"),
        "procedural_assessments": [
            {
                "assessment_id": f"procedure-{issue.get('issue_id')}",
                "issue_id": issue.get("issue_id"),
                "claim_ids": claims_by_issue.get(str(issue.get("issue_id")), []),
                "analysis_status": "needs_confirmation",
                "case_jurisdiction": state.get("jurisdiction"),
                "analysis_date": state.get("analysis_date"),
                "limitation": {
                    "status": "disputed", "trigger_date": None, "deadline_date": None,
                    "basis_rule_ids": [], "analysis": "待核对时效起算、中断事实和截止日。",
                },
                "jurisdiction": {
                    "status": "disputed", "forum": "待确认的劳动人事争议仲裁委员会",
                    "case_jurisdiction": state.get("jurisdiction"), "basis_rule_ids": [],
                    "analysis": "待核对劳动合同履行地、用人单位所在地和管辖冲突。",
                },
                "final_award": {
                    "status": "disputed", "basis_rule_ids": [],
                    "analysis": "待核对请求类型、单项金额和一裁终局条件。",
                },
                "interim_relief": {
                    "status": "disputed", "basis_rule_ids": [],
                    "analysis": "待核对先予执行或其他临时救济的法定条件。",
                },
                "remedy_paths": ["待核对裁决类型后明确起诉、申请撤销或执行等后续路径。"],
                "pending_items": ["时效、管辖、一裁终局、临时救济和后续救济路径待逐项复核。"],
                "risk": "程序输入未确认前不得进入策略和起草节点。",
            }
            for issue in state.get("issues", [])
            if isinstance(issue, dict) and isinstance(issue.get("issue_id"), str)
        ],
    }


def prepare_records(payload: Any, actor: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        fail("程序分析输入 schema_version 必须为 1.0。")
    records = payload.get("procedural_assessments")
    if not isinstance(records, list) or not records:
        fail("procedural_assessments 必须是非空数组。")
    created_at = now_iso()
    prepared: list[dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict):
            fail("procedural_assessments 每项必须是 object。")
        record = deepcopy(item)
        record["created_by"] = actor
        record["created_at"] = created_at
        record.pop("updated_by", None)
        record.pop("updated_at", None)
        record["procedure_digest"] = procedure_digest(record)
        prepared.append(record)
    return prepared


def render_markdown(state: dict[str, Any]) -> str:
    lines = ["# 程序分析台账", "", f"> 分析日：{state.get('analysis_date')}", ""]
    for record in state.get("procedural_assessments", []):
        lines.extend([
            f"## {record.get('assessment_id')}｜{record.get('issue_id')}", "",
            f"- 分析状态：{record.get('analysis_status')}",
            f"- 时效：{record.get('limitation', {}).get('status')}；{record.get('limitation', {}).get('analysis')}",
            f"- 管辖：{record.get('jurisdiction', {}).get('status')}；{record.get('jurisdiction', {}).get('forum')}",
            f"- 一裁终局：{record.get('final_award', {}).get('status')}；{record.get('final_award', {}).get('analysis')}",
            f"- 临时救济：{record.get('interim_relief', {}).get('status')}；{record.get('interim_relief', {}).get('analysis')}",
            f"- 后续路径：{'；'.join(record.get('remedy_paths', []))}",
            f"- 风险：{record.get('risk')}", "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 程序分析执行器")
    parser.add_argument("--state", required=True, help=".casework/case_state.json")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scaffold", action="store_true", help="生成待复核程序分析骨架")
    group.add_argument("--input", help="经复核的程序分析 JSON")
    parser.add_argument("--output", help="骨架输出路径；默认位于 .casework/procedure/")
    parser.add_argument("--actor", default="labor-claims-procedure")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    state_errors = validate_state(state)
    if state_errors:
        fail("案件状态无效：\n" + "\n".join(state_errors))
    if state.get("current_node") != "claims_procedure":
        fail(f"当前节点为 {state.get('current_node')}，不能执行程序分析。")
    upstream_errors = (
        structured_issue_errors(state)
        + structured_evidence_errors(state)
        + structured_authority_errors(state)
        + structured_calculation_errors(state)
    )
    if upstream_errors:
        fail("上游业务状态未就绪：\n" + "\n".join(upstream_errors))

    output_root = casework_root(state_path) / "procedure"
    if args.scaffold:
        output_path = Path(args.output).expanduser().resolve() if args.output else output_root / "scaffold.json"
        write_new(output_path, scaffold_payload(state))
        print(json.dumps({"status": "to_review", "output": str(output_path)}, ensure_ascii=False))
        return 0

    payload = read_json(Path(args.input).expanduser().resolve())
    records = prepare_records(payload, args.actor)
    candidate = deepcopy(state)
    candidate["procedural_assessments"] = records
    candidate.setdefault("events", []).append({
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "event_type": "procedure_assessed",
        "actor": args.actor,
        "occurred_at": now_iso(),
        "details": {"assessment_ids": [item["assessment_id"] for item in records]},
    })
    errors = structured_procedure_errors(candidate) + validate_state(candidate)
    if errors:
        fail("程序分析输入无效：\n" + "\n".join(dict.fromkeys(errors)))

    output_root.mkdir(parents=True, exist_ok=True)
    atomic_write(
        output_root / "analysis.json",
        json.dumps({"schema_version": "1.0", "procedural_assessments": records}, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write(output_root / "analysis.md", render_markdown(candidate))
    write_state(state_path, candidate, source=state_path, operation="procedure-assessed")
    print(json.dumps({
        "status": "reviewed" if all(item["analysis_status"] == "reviewed" for item in records) else "needs_confirmation",
        "assessment_count": len(records),
        "output": str(output_root / "analysis.json"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
