#!/usr/bin/env python3
"""Validate and render bounded, auditable PatSeek Markdown reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BANNED = ("不存在侵权风险", "可自由实施", "全球无人申请", "保证新颖性", "已经具备新颖性")
REQUIRED = ("title", "role", "decision", "task_type", "as_of", "scope", "features", "searches", "gate", "limitations")


def validate(evidence: dict) -> list[str]:
    errors = [f"缺少字段: {field}" for field in REQUIRED if not evidence.get(field)]
    if errors:
        return errors
    if not isinstance(evidence["features"], list) or not evidence["features"]:
        errors.append("features必须为非空列表")
    if not isinstance(evidence["searches"], list) or not evidence["searches"]:
        errors.append("searches必须为非空列表")
    for index, search in enumerate(evidence.get("searches") or [], 1):
        for field in ("id", "market", "query", "total", "sample_size"):
            if field not in search:
                errors.append(f"searches[{index}]缺少{field}")
        if int(search.get("total") or 0) == 0 and not search.get("zero_result_explained"):
            errors.append(f"searches[{index}]为0条但未说明字段/语言/表达式预检")
    gate = evidence.get("gate") or {}
    if not gate.get("status"):
        errors.append("gate缺少status")
    if evidence.get("task_type") == "fto" and gate.get("status") != "candidate_screening_only":
        errors.append("FTO报告只能通过candidate_screening_only闸门渲染")
    conclusion = str(evidence.get("conclusion") or "")
    if any(word in conclusion for word in BANNED):
        errors.append("结论包含禁止的保证性表述")
    return errors


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def bounded_conclusion(task_type: str, gate: dict) -> str:
    status = gate.get("status")
    if task_type == "fto":
        return "本次结果仅为候选权利筛查；不得据此作低风险、无侵权或自由实施结论。"
    if status == "not_comparable":
        return "现有证据不足以进行定量比较或排名；仅可交付分支技术线索与补检方向。"
    if status == "contradicted":
        return "已识别反例；不得将目标组合称为专利空白，应缩窄问题后重新验证。"
    if status == "no_x_candidate_in_scope":
        return "本次范围未形成X候选；这不保证新颖性，需继续QY-Comp、非专利和日期核验。"
    if status == "contact_lead_only":
        return "结果仅形成待联系技术线索，不构成团队排名、合作适格性或许可可行性判断。"
    if status == "unverified":
        return "当前证据不足以支持目标结论；保留为下一轮检索和外部核验输入。"
    return "结论受所列范围和限制约束；不得外推为法律、市场或商业保证。"


def render(evidence: dict) -> str:
    errors = validate(evidence)
    if errors:
        raise ValueError("; ".join(errors))
    scope = evidence["scope"]
    lines = [f"# {evidence['title']}", "", "## 结论摘要", "", bounded_conclusion(evidence["task_type"], evidence["gate"]), ""]
    lines.extend(["## 任务与范围", "", _table(
        ["字段", "内容"],
        [["使用者", evidence["role"]], ["待支持决策", evidence["decision"]], ["任务类型", evidence["task_type"]], ["检索日期", evidence["as_of"]], ["市场/数据库", scope.get("market", "未说明")], ["语言/文献", scope.get("language_and_sources", "未说明")], ["关键日期", scope.get("critical_date", "不适用/未提供")]],
    ), "", "## 特征或实施要素", "", _table(["ID", "内容"], [[item.get("id", "-"), item.get("text", "-")] for item in evidence["features"]]), ""])
    search_rows = []
    for search in evidence["searches"]:
        search_rows.append([search["id"], search["market"], search["query"], search["total"], search["sample_size"], search.get("observability", "未提供"), search.get("action", "待说明")])
    lines.extend(["## 检索记录", "", _table(["分支", "市场", "检索式", "命中", "样本", "可观察性", "处理"], search_rows), ""])
    details = evidence.get("details") or []
    if details:
        detail_rows = [[item.get("pid", "-"), item.get("applicant", "-"), item.get("feature_hits", "-"), item.get("evidence_location", "未提供—仅文本/字段代理"), item.get("review_status", "待复核")] for item in details]
        lines.extend(["## 候选证据", "", _table(["文献", "主体", "特征命中", "证据位置", "状态"], detail_rows), ""])
    lines.extend(["## 质量闸门", "", "```json", json.dumps(evidence["gate"], ensure_ascii=False, indent=2), "```", "", "## 限制与下一步", ""])
    lines.extend([f"- {item}" for item in evidence["limitations"]])
    lines.extend(["", "## 限定结论", "", bounded_conclusion(evidence["task_type"], evidence["gate"]), ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="PatSeek可审计报告守卫与Markdown渲染")
    parser.add_argument("evidence", type=Path, help="结构化证据JSON")
    parser.add_argument("--output", type=Path, required=True, help="输出Markdown路径")
    args = parser.parse_args()
    try:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        rendered = render(evidence)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
