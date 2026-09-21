#!/usr/bin/env python3
"""生成争点候选，或将经复核的请求／抗辩矩阵回写案件状态。

内置知识只用于生成有限的、待复核的争点候选；候选不会自动
进入 ``issues[]``。只有经 Agent／律师结合本案事实补齐构成要件、
双方路径、备选路径和失败后果的结构化输入，才能形成正式矩阵。
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

from case_state import read_json, structured_issue_errors, validate_state, write_state
from issue_router import query_knowledge


SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
ISSUE_TYPES = {"claim", "defense", "procedure", "threshold"}
ANALYSIS_STATUSES = {"to_review", "reviewed"}
ELEMENT_STATUSES = {"supported", "partially_supported", "unsupported", "disputed", "to_verify"}
MAX_ISSUES = 100
MAX_QUERY_CHARS = 4000


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


def clean_text(value: Any, field: str, *, minimum: int = 2, maximum: int = 1000) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) < minimum:
        fail(f"{field} 过短或为空。")
    if len(text) > maximum:
        fail(f"{field} 超过 {maximum} 字符。")
    return text


def string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"{field} 必须是非空字符串数组。")
    normalized = list(dict.fromkeys(item.strip() for item in value))
    if not allow_empty and not normalized:
        fail(f"{field} 不得为空。")
    return normalized


def checked_refs(value: Any, field: str, known: set[str]) -> list[str]:
    refs = string_list(value, field)
    missing = sorted(set(refs) - known)
    if missing:
        fail(f"{field} 引用不存在的 ID：{', '.join(missing)}")
    return refs


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\0".join(parts)
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def normalize_element(
    value: Any,
    *,
    issue_id: str,
    index: int,
    fact_ids: set[str],
    evidence_ids: set[str],
    rule_ids: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"elements[{index}] 必须是 object。")
    description = clean_text(value.get("description"), f"elements[{index}].description", minimum=4, maximum=500)
    element_id = value.get("element_id") or stable_id("element", issue_id, description)
    if not isinstance(element_id, str) or not SAFE_ID.fullmatch(element_id):
        fail(f"elements[{index}].element_id 不安全或过长：{element_id}")
    status = value.get("status")
    if status not in ELEMENT_STATUSES:
        fail(f"elements[{index}].status 无效：{status}")
    gaps = string_list(value.get("gaps", []), f"elements[{index}].gaps")
    if status in {"partially_supported", "unsupported", "disputed", "to_verify"} and not gaps:
        fail(f"elements[{index}] 尚未充分支持时必须列明 gaps。")
    return {
        "element_id": element_id,
        "description": description,
        "status": status,
        "fact_ids": checked_refs(value.get("fact_ids", []), f"elements[{index}].fact_ids", fact_ids),
        "evidence_ids": checked_refs(value.get("evidence_ids", []), f"elements[{index}].evidence_ids", evidence_ids),
        "rule_ids": checked_refs(value.get("rule_ids", []), f"elements[{index}].rule_ids", rule_ids),
        "gaps": gaps,
    }


def normalize_issue(
    value: Any,
    *,
    representation: str,
    fact_ids: set[str],
    evidence_ids: set[str],
    rule_ids: set[str],
    actor: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail("争点输入必须是 object。")
    title = clean_text(value.get("issue"), "issue", minimum=4, maximum=200)
    issue_type = value.get("issue_type")
    if issue_type not in ISSUE_TYPES:
        fail(f"issue_type 无效：{issue_type}")
    issue_id = value.get("issue_id") or stable_id("issue", issue_type, title)
    if not isinstance(issue_id, str) or not SAFE_ID.fullmatch(issue_id):
        fail(f"issue_id 不安全或过长：{issue_id}")
    analysis_status = value.get("analysis_status", "reviewed")
    if analysis_status not in ANALYSIS_STATUSES:
        fail(f"analysis_status 无效：{analysis_status}")
    if analysis_status != "reviewed":
        fail(f"正式矩阵只能接入 reviewed 争点：{title}")

    our_position = value.get("our_position")
    if not isinstance(our_position, dict):
        fail(f"our_position 必须是 object：{title}")
    raw_elements = our_position.get("elements")
    if not isinstance(raw_elements, list) or not raw_elements:
        fail(f"our_position.elements 必须是非空数组：{title}")
    elements = [
        normalize_element(
            item,
            issue_id=issue_id,
            index=index,
            fact_ids=fact_ids,
            evidence_ids=evidence_ids,
            rule_ids=rule_ids,
        )
        for index, item in enumerate(raw_elements)
    ]
    element_ids = [item["element_id"] for item in elements]
    if len(element_ids) != len(set(element_ids)):
        fail(f"同一争点中 element_id 不得重复：{title}")

    opponent = value.get("opponent_position")
    if not isinstance(opponent, dict):
        fail(f"opponent_position 必须是 object：{title}")
    opponent_normalized = {
        "strongest_argument": clean_text(
            opponent.get("strongest_argument"),
            "opponent_position.strongest_argument",
            minimum=8,
            maximum=1000,
        ),
        "fact_ids": checked_refs(opponent.get("fact_ids", []), "opponent_position.fact_ids", fact_ids),
        "evidence_ids": checked_refs(opponent.get("evidence_ids", []), "opponent_position.evidence_ids", evidence_ids),
        "rule_ids": checked_refs(opponent.get("rule_ids", []), "opponent_position.rule_ids", rule_ids),
        "response": clean_text(opponent.get("response"), "opponent_position.response", minimum=8, maximum=1000),
        "uncertainties": string_list(opponent.get("uncertainties", []), "opponent_position.uncertainties"),
    }

    raw_alternatives = value.get("alternative_paths", [])
    if not isinstance(raw_alternatives, list):
        fail(f"alternative_paths 必须是数组：{title}")
    alternatives = []
    for index, alternative in enumerate(raw_alternatives):
        if not isinstance(alternative, dict):
            fail(f"alternative_paths[{index}] 必须是 object。")
        alternatives.append({
            "path": clean_text(alternative.get("path"), f"alternative_paths[{index}].path", minimum=4, maximum=500),
            "trigger": clean_text(alternative.get("trigger"), f"alternative_paths[{index}].trigger", minimum=4, maximum=500),
            "consequence": clean_text(
                alternative.get("consequence"),
                f"alternative_paths[{index}].consequence",
                minimum=4,
                maximum=500,
            ),
        })
    no_alternative_reason = value.get("no_alternative_reason")
    if not alternatives:
        no_alternative_reason = clean_text(
            no_alternative_reason,
            "no_alternative_reason",
            minimum=8,
            maximum=500,
        )

    return {
        "issue_id": issue_id,
        "issue": title,
        "issue_type": issue_type,
        "analysis_status": analysis_status,
        "representation": representation,
        "our_position": {
            "position": clean_text(our_position.get("position"), "our_position.position", minimum=8, maximum=1000),
            "elements": elements,
            "conclusion": clean_text(our_position.get("conclusion"), "our_position.conclusion", minimum=8, maximum=1000),
        },
        "opponent_position": opponent_normalized,
        "alternative_paths": alternatives,
        "no_alternative_reason": no_alternative_reason if not alternatives else None,
        "failure_consequence": clean_text(value.get("failure_consequence"), "failure_consequence", minimum=8, maximum=1000),
        "created_by": actor,
        "created_at": now_iso(),
    }


def default_discovery_query(state: dict[str, Any]) -> str:
    parts = []
    task_context = state.get("task_context")
    if isinstance(task_context, dict) and task_context.get("user_request"):
        parts.append(str(task_context["user_request"]))
    for fact in state.get("facts", []):
        if isinstance(fact, dict) and isinstance(fact.get("statement"), str):
            parts.append(fact["statement"])
    return "\n".join(parts)[:MAX_QUERY_CHARS]


def discover(state: dict[str, Any], query: str) -> list[dict[str, Any]]:
    results = query_knowledge(query)
    return [
        {
            "candidate_id": stable_id("candidate", str(item.get("issue", ""))),
            "issue": item.get("issue", ""),
            "analysis_status": "to_review",
            "analysis_points": item.get("analysis_points", ""),
            "zhejiang_guidance": item.get("zhejiang_guidance", ""),
            "required_completion": [
                "结合本案事实确定争点类型与我方立场",
                "按构成要件关联 fact_id，并标记支持状态与缺口",
                "写明对方最强观点、回应、备选路径和失败后果",
            ],
        }
        for item in results
    ]


def render_discovery(query: str, candidates: list[dict[str, Any]], generated_at: str) -> tuple[str, str]:
    payload = {
        "status": "review_required",
        "generated_at": generated_at,
        "query": query,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    lines = [
        "# 争点候选",
        "",
        "> 候选仅为内置知识路由结果，未结合本案完成请求／抗辩分析，不能通过争点节点。",
        "",
    ]
    for index, item in enumerate(candidates, 1):
        lines.extend([
            f"## {index}. {item['issue']}",
            "",
            f"- 分析线索：{item['analysis_points'] or '无'}",
            f"- 浙江口径线索：{item['zhejiang_guidance'] or '无'}",
            "",
        ])
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def render_matrix(state: dict[str, Any], issues: list[dict[str, Any]], generated_at: str) -> tuple[str, str]:
    payload = {
        "status": "lawyer_review_required",
        "case_id": state.get("case_id"),
        "representation": state.get("representation"),
        "generated_at": generated_at,
        "issue_count": len(issues),
        "issues": issues,
    }
    lines = [
        "# 请求／抗辩矩阵",
        "",
        f"> 代理立场：{state.get('representation')}；状态：待律师复核。",
        "",
    ]
    for index, issue in enumerate(issues, 1):
        lines.extend([
            f"## {index}. {issue['issue']}",
            "",
            f"- 我方路径：{issue['our_position']['position']}",
            f"- 当前结论：{issue['our_position']['conclusion']}",
            f"- 对方最强观点：{issue['opponent_position']['strongest_argument']}",
            f"- 回应：{issue['opponent_position']['response']}",
            f"- 失败后果：{issue['failure_consequence']}",
            "",
            "| 构成要件 | 状态 | 事实 | 证据 | 法源 | 缺口 |",
            "|---|---|---|---|---|---|",
        ])
        for element in issue["our_position"]["elements"]:
            lines.append(
                f"| {element['description']} | {element['status']} | "
                f"{'、'.join(element['fact_ids']) or '无'} | {'、'.join(element['evidence_ids']) or '无'} | "
                f"{'、'.join(element['rule_ids']) or '无'} | {'、'.join(element['gaps']) or '无'} |"
            )
        if issue["alternative_paths"]:
            lines.extend(["", "备选路径："])
            for alternative in issue["alternative_paths"]:
                lines.append(
                    f"- {alternative['path']}；触发条件：{alternative['trigger']}；"
                    f"后果：{alternative['consequence']}"
                )
        else:
            lines.extend(["", f"无备选路径理由：{issue['no_alternative_reason']}"])
        lines.append("")
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def load_issues(path: Path) -> list[Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"争点输入不存在：{path}")
    except json.JSONDecodeError as exc:
        fail(f"争点输入不是合法 JSON：{exc}")
    issues = payload.get("issues") if isinstance(payload, dict) else payload
    if not isinstance(issues, list) or not issues:
        fail("争点输入必须是非空数组，或含 issues 数组的 object。")
    if len(issues) > MAX_ISSUES:
        fail(f"单次争点不得超过 {MAX_ISSUES} 项。")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 请求／抗辩矩阵执行器")
    parser.add_argument("--state", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--discover", action="store_true", help="从任务和事实生成待复核争点候选")
    mode.add_argument("--input", help="经复核的请求／抗辩矩阵 JSON")
    parser.add_argument("--query", help="发现模式下的明确查询；缺省时使用任务与事实")
    parser.add_argument(
        "--replace-existing-issues",
        action="store_true",
        help="以本次完整矩阵替换旧 issues[]；旧状态会由 case_state 历史快照保留",
    )
    parser.add_argument("--actor", default="labor-issue-analysis")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    if state.get("current_node") != "issue_analysis":
        fail(f"当前节点为 {state.get('current_node')}，不能执行争点分析。")
    if state.get("representation") not in {"employee", "employer"}:
        fail("代理立场未确认，不能生成请求／抗辩矩阵。")
    if args.discover and args.replace_existing_issues:
        fail("--replace-existing-issues 只能与 --input 一起使用。")

    output_root = casework_root(state_path) / "issue_analysis"
    generated_at = now_iso()
    if args.discover:
        query = clean_text(args.query or default_discovery_query(state), "query", minimum=2, maximum=MAX_QUERY_CHARS)
        candidates = discover(state, query)
        discovery_json, discovery_md = render_discovery(query, candidates, generated_at)
        atomic_write_text(output_root / "discovery.json", discovery_json)
        atomic_write_text(output_root / "discovery.md", discovery_md)
        print(json.dumps({
            "status": "review_required",
            "candidate_count": len(candidates),
            "discovery": str(output_root / "discovery.json"),
        }, ensure_ascii=False))
        return 0

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
    normalized = [
        normalize_issue(
            item,
            representation=state["representation"],
            fact_ids=known_facts,
            evidence_ids=known_evidence,
            rule_ids=known_rules,
            actor=args.actor,
        )
        for item in load_issues(Path(args.input).expanduser().resolve())
    ]
    issue_ids = [item["issue_id"] for item in normalized]
    if len(issue_ids) != len(set(issue_ids)):
        fail("同一批输入中 issue_id 不得重复。")

    candidate_state = json.loads(json.dumps(state, ensure_ascii=False))
    replaced_count = 0
    if args.replace_existing_issues:
        replaced_count = len(candidate_state.get("issues", []))
        candidate_state["issues"] = []
    existing_by_id = {
        item.get("issue_id"): (index, item)
        for index, item in enumerate(candidate_state.get("issues", []))
        if isinstance(item, dict) and item.get("issue_id")
    }
    added_ids = []
    updated_ids = []
    for issue in normalized:
        existing_entry = existing_by_id.get(issue["issue_id"])
        if existing_entry:
            index, existing = existing_entry
            if existing.get("issue") != issue["issue"] or existing.get("issue_type") != issue["issue_type"]:
                fail(f"issue_id 与既有争点冲突：{issue['issue_id']}")
            issue["created_at"] = existing.get("created_at") or issue["created_at"]
            issue["created_by"] = existing.get("created_by") or issue["created_by"]
            issue["updated_at"] = generated_at
            issue["updated_by"] = args.actor
            candidate_state["issues"][index] = issue
            updated_ids.append(issue["issue_id"])
        else:
            candidate_state.setdefault("issues", []).append(issue)
            added_ids.append(issue["issue_id"])

    matrix_errors = validate_state(candidate_state) + structured_issue_errors(candidate_state)
    if matrix_errors:
        hint = "\n旧 issues[] 为占位结构时，请在完整矩阵输入下使用 --replace-existing-issues。"
        fail("争点回写后的案件状态无效：\n" + "\n".join(matrix_errors) + hint)

    matrix_json_path = output_root / "matrix.json"
    matrix_md_path = output_root / "matrix.md"
    matrix_json, matrix_md = render_matrix(state, candidate_state["issues"], generated_at)
    candidate_state.setdefault("events", []).append({
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "event_type": "issue_matrix_built",
        "actor": args.actor,
        "occurred_at": generated_at,
        "details": {
            "added_issue_ids": added_ids,
            "updated_issue_ids": updated_ids,
            "replaced_previous_count": replaced_count,
            "matrix_json": str(matrix_json_path),
            "matrix_markdown": str(matrix_md_path),
        },
    })
    errors = validate_state(candidate_state) + structured_issue_errors(candidate_state)
    if errors:
        fail("争点回写后的案件状态无效：\n" + "\n".join(errors))
    atomic_write_text(matrix_json_path, matrix_json)
    atomic_write_text(matrix_md_path, matrix_md)
    write_state(state_path, candidate_state, source=state_path, operation="issue-matrix-built")
    print(json.dumps({
        "status": "lawyer_review_required",
        "issue_count": len(candidate_state["issues"]),
        "added_count": len(added_ids),
        "updated_count": len(updated_ids),
        "replaced_previous_count": replaced_count,
        "matrix": str(matrix_json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
