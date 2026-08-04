#!/usr/bin/env python3
"""Query, collect information for, and audit element-based pleadings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = BASE / "references" / "element-pleading-claim-matrix.json"
POSITIONS = {"admit", "deny", "partial", "unknown"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    return "".join(value.casefold().split()).replace("纠纷", "")


def resolve_dispute(data: dict, query: str) -> dict:
    q = norm(query)
    matches = []
    for dispute in data["disputes"]:
        names = [dispute["element_node_id"], dispute["dispute_type"], *dispute["aliases"]]
        if any(q == norm(name) or q in norm(name) or norm(name) in q for name in names):
            matches.append(dispute)
    if len(matches) != 1:
        options = "、".join(item["dispute_type"] for item in data["disputes"])
        raise SystemExit(f"无法唯一识别纠纷“{query}”。可选：{options}")
    return matches[0]


def select_claims(dispute: dict, query: str | None) -> list[dict]:
    if not query:
        return dispute["claims"]
    q = norm(query)
    matches = [
        claim
        for claim in dispute["claims"]
        if q == norm(claim["claim_id"]) or q in norm(claim["request_name"])
    ]
    if not matches:
        raise SystemExit(f"未在{dispute['dispute_type']}中找到诉请“{query}”")
    return matches


def print_list(data: dict) -> None:
    for dispute in data["disputes"]:
        print(f"{dispute['element_node_id']}\t{dispute['dispute_type']}\t{len(dispute['claims'])}项")
        for claim in dispute["claims"]:
            print(f"  {claim['claim_id']}\t{claim['request_name']}")


def print_intake(dispute: dict, claims: list[dict], role: str) -> None:
    print(f"# {dispute['dispute_type']}要素式{('起诉' if role == 'plaintiff' else '答辩')}信息清单")
    print(f"\n现行路由：法〔2025〕82号；教材定位：{dispute['source_guide_pages']}")
    print("\n> 未核实内容写“待核实”，不得按示例补造。正式提交前逐条核验现行法和地方要求。")
    for claim in claims:
        print(f"\n## {claim['claim_id']} {claim['request_name']}")
        print("\n### 法律要件")
        for item in claim["elements"]:
            print(f"- {item}")
        print("\n### 必答事实")
        for question in claim["fact_questions"]:
            print(f"- [{question['question_id']}] {question['prompt']}")
        print("\n### 证据组")
        for group in claim["evidence_groups"]:
            print(f"- [{group['evidence_id']}] {group['group']}")
        if role == "defendant":
            print("\n### 可审查的答辩路径")
            for item in claim["defense_paths"]:
                print(f"- {item}")
        print("\n### 法院审查")
        for item in claim["court_review_checks"]:
            print(f"- {item}")
        print(f"\n计算／处理：{claim['calculation_rule']}")


def example_case(dispute: dict, role: str) -> dict:
    selected = [claim["claim_id"] for claim in dispute["claims"][:1]]
    claim = dispute["claims"][0]
    result = {
        "dispute": dispute["element_node_id"],
        "role": role,
        "selected_claims": selected,
        "answers": {item["question_id"]: "待核实" for item in claim["fact_questions"]},
        "evidence": {item["evidence_id"]: [] for item in claim["evidence_groups"]},
        "responses": {},
    }
    if role == "defendant":
        result["responses"][claim["claim_id"]] = {"position": "unknown", "reason": "待核实"}
    return result


def audit(data: dict, case_path: Path) -> tuple[dict, int]:
    case = load(case_path)
    dispute = resolve_dispute(data, str(case.get("dispute", "")))
    role = case.get("role")
    if role not in {"plaintiff", "defendant"}:
        return {"status": "blocked", "blocking": ["role必须是plaintiff或defendant"], "warnings": []}, 2
    claim_map = {item["claim_id"]: item for item in dispute["claims"]}
    selected_ids = case.get("selected_claims") or []
    blocking: list[str] = []
    warnings: list[str] = []
    if not selected_ids:
        blocking.append("未选择诉请或被诉请求")
    unknown = [item for item in selected_ids if item not in claim_map]
    if unknown:
        blocking.append(f"诉请不属于该纠纷：{unknown}")
    selected = [claim_map[item] for item in selected_ids if item in claim_map]
    selected_set = set(selected_ids)
    for claim in selected:
        conflicts = selected_set.intersection(claim["conflicts_with"])
        if conflicts:
            blocking.append(f"{claim['claim_id']}与{sorted(conflicts)}存在救济冲突，须改为主位/备位或重新选择")
        for question in claim["fact_questions"]:
            value = str((case.get("answers") or {}).get(question["question_id"], "")).strip()
            if not value or value in {"待核实", "不知道", "不清楚"}:
                blocking.append(f"缺少阻断事实 {question['question_id']}：{question['prompt']}")
        for group in claim["evidence_groups"]:
            values = (case.get("evidence") or {}).get(group["evidence_id"])
            if not values:
                warnings.append(f"缺少证据或缺失说明 {group['evidence_id']}：{group['group']}")
        if role == "defendant":
            response = (case.get("responses") or {}).get(claim["claim_id"], {})
            position = response.get("position")
            if position not in POSITIONS:
                blocking.append(f"{claim['claim_id']}未作承认/否认/部分承认/不知回应")
            if position in {"deny", "partial"} and not str(response.get("reason", "")).strip():
                blocking.append(f"{claim['claim_id']}否认或部分承认但未说明理由")
    result = {
        "status": "blocked" if blocking else ("needs_evidence" if warnings else "structure_ready"),
        "dispute": dispute["dispute_type"],
        "role": role,
        "selected_claims": selected_ids,
        "blocking": blocking,
        "warnings": warnings,
        "next_step": "补齐阻断事实后再生成；证据缺口须说明无法取得原因和调查路径。" if blocking else "进行现行法条、管辖、期限和地方格式核验。",
    }
    return result, 2 if blocking else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    intake_parser = sub.add_parser("intake")
    intake_parser.add_argument("--dispute", required=True)
    intake_parser.add_argument("--role", choices=["plaintiff", "defendant"], required=True)
    intake_parser.add_argument("--claim")
    show_parser = sub.add_parser("show")
    show_parser.add_argument("--dispute", required=True)
    show_parser.add_argument("--claim")
    example_parser = sub.add_parser("example")
    example_parser.add_argument("--dispute", required=True)
    example_parser.add_argument("--role", choices=["plaintiff", "defendant"], required=True)
    audit_parser = sub.add_parser("audit")
    audit_parser.add_argument("--case-json", type=Path, required=True)
    args = parser.parse_args()
    data = load(args.matrix)
    if args.command == "list":
        print_list(data)
        return
    if args.command == "audit":
        result, code = audit(data, args.case_json)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(code)
    dispute = resolve_dispute(data, args.dispute)
    if args.command == "example":
        print(json.dumps(example_case(dispute, args.role), ensure_ascii=False, indent=2))
        return
    claims = select_claims(dispute, getattr(args, "claim", None))
    if args.command == "intake":
        print_intake(dispute, claims, args.role)
    else:
        print(json.dumps(claims, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
