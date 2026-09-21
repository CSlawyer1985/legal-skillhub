#!/usr/bin/env python3
"""LaborPilot 领域评测执行器。

评测公开路由结果、复合争点、否定语境、非劳动争议边界和版本化法律口径。
输出只包含评测 ID、数量与问题，不输出知识卡正文或内部字段。
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any

from issue_router import query_knowledge


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVALS = ROOT / "evals" / "evals.json"
DEFAULT_LEGAL_VERSIONS = ROOT / "evals" / "legal-version-cases.json"
ALLOWED_CASE_TYPES = {"single", "composite", "negative_context", "out_of_domain"}
FORBIDDEN_ROUTER_FIELDS = {
    "expected_cards",
    "expected_card_ids",
    "expected_gate",
    "expected_gate_ids",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 顶层必须是 object。")
    return payload


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} 必须是非空字符串。")
    return value.strip()


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} 必须是字符串数组。")
    normalized = list(dict.fromkeys(item.strip() for item in value))
    if not allow_empty and not normalized:
        raise ValueError(f"{field} 不得为空。")
    return normalized


def parse_date(value: Any, field: str, *, nullable: bool = False) -> date | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} 必须是 YYYY-MM-DD。")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} 必须是合法 YYYY-MM-DD。") from exc


def reject_internal_router_fields(value: Any, field: str = "evals.json") -> None:
    """拒绝将内部卡片或案由门标识重新写入公开评测。"""
    if isinstance(value, dict):
        forbidden = sorted(FORBIDDEN_ROUTER_FIELDS & set(value))
        if forbidden:
            raise ValueError(f"{field} 包含内部字段：{'、'.join(forbidden)}")
        for key, item in value.items():
            reject_internal_router_fields(item, f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_internal_router_fields(item, f"{field}[{index}]")


def validate_router_dataset(payload: dict[str, Any]) -> list[dict[str, Any]]:
    reject_internal_router_fields(payload)
    if payload.get("schema_version") != "2.0":
        raise ValueError("evals.json.schema_version 必须为 2.0。")
    require_text(payload.get("dataset_version"), "evals.json.dataset_version")
    require_text(payload.get("package_version"), "evals.json.package_version")
    capabilities = require_string_list(payload.get("evaluated_capabilities"), "evaluated_capabilities")
    required_capabilities = {
        "single_issue_recall", "composite_issue_recall", "negative_context_precision",
        "out_of_domain_precision", "legal_version_resolution",
    }
    missing = sorted(required_capabilities - set(capabilities))
    if missing:
        raise ValueError("evaluated_capabilities 缺少：" + "、".join(missing))

    cases = payload.get("evals")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evals 必须是非空数组。")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    observed_types: set[str] = set()
    for index, item in enumerate(cases):
        if not isinstance(item, dict):
            raise ValueError(f"evals[{index}] 必须是 object。")
        eval_id = require_text(item.get("id"), f"evals[{index}].id")
        if eval_id in seen:
            raise ValueError(f"重复评测 ID：{eval_id}")
        seen.add(eval_id)
        case_type = item.get("case_type")
        if case_type not in ALLOWED_CASE_TYPES:
            raise ValueError(f"{eval_id}.case_type 无效：{case_type}")
        observed_types.add(case_type)
        prompt = require_text(item.get("prompt"), f"{eval_id}.prompt")
        expected = require_string_list(
            item.get("expected_issue_terms", []), f"{eval_id}.expected_issue_terms", allow_empty=True
        )
        forbidden = require_string_list(
            item.get("forbidden_issue_terms", []), f"{eval_id}.forbidden_issue_terms", allow_empty=True
        )
        result_range = item.get("expected_result_range")
        if (
            not isinstance(result_range, list) or len(result_range) != 2
            or not all(isinstance(value, int) and value >= 0 for value in result_range)
            or result_range[0] > result_range[1]
        ):
            raise ValueError(f"{eval_id}.expected_result_range 必须是 [最小值, 最大值]。")
        if case_type == "out_of_domain" and result_range != [0, 0]:
            raise ValueError(f"{eval_id} 的非劳动争议期望必须为 [0, 0]。")
        if case_type in {"negative_context", "out_of_domain"} and not forbidden:
            raise ValueError(f"{eval_id} 必须包含误召回禁止词。")
        normalized.append({
            "id": eval_id,
            "case_type": case_type,
            "prompt": prompt,
            "expected_issue_terms": expected,
            "forbidden_issue_terms": forbidden,
            "expected_result_range": result_range,
        })
    required_types = {"single", "composite", "negative_context", "out_of_domain"}
    missing_types = sorted(required_types - observed_types)
    if missing_types:
        raise ValueError("评测类型覆盖不完整：" + "、".join(missing_types))
    return normalized


def evaluate_router(cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    findings: list[str] = []
    for item in cases:
        routed = query_knowledge(item["prompt"])
        issue_text = "\n".join(str(result.get("issue", "")) for result in routed)
        case_findings: list[str] = []
        for term in item["expected_issue_terms"]:
            if term not in issue_text:
                case_findings.append(f"缺少应召回争点词：{term}")
        for term in item["forbidden_issue_terms"]:
            if term in issue_text:
                case_findings.append(f"出现禁止误召回争点词：{term}")
        minimum, maximum = item["expected_result_range"]
        if not minimum <= len(routed) <= maximum:
            case_findings.append(f"结果数量 {len(routed)} 不在 {minimum}—{maximum} 范围。")
        if case_findings:
            findings.extend(f"{item['id']}：{message}" for message in case_findings)
        results.append({
            "id": item["id"],
            "case_type": item["case_type"],
            "status": "pass" if not case_findings else "blocked",
            "result_count": len(routed),
        })
    return results, findings


def active_version_ids(versions: list[dict[str, Any]], relevant_date: date) -> list[str]:
    active: list[str] = []
    for item in versions:
        start = parse_date(item.get("effective_from"), f"{item.get('version_id')}.effective_from", nullable=True)
        end = parse_date(item.get("effective_to"), f"{item.get('version_id')}.effective_to", nullable=True)
        if start and end and end < start:
            raise ValueError(f"{item.get('version_id')} 的效力终止日早于生效日。")
        if (start is None or relevant_date >= start) and (end is None or relevant_date <= end):
            active.append(require_text(item.get("version_id"), "version_id"))
    return sorted(active)


def validate_single_active_timeline(topic_id: str, versions: list[dict[str, Any]]) -> None:
    """校验版本区间覆盖整条时间线，且任意日期只有一个生效版本。"""
    intervals: list[tuple[date | None, date | None, str]] = []
    for index, item in enumerate(versions):
        if not isinstance(item, dict):
            raise ValueError(f"{topic_id}.versions[{index}] 必须是 object。")
        version_id = require_text(item.get("version_id"), f"{topic_id}.version_id")
        start = parse_date(
            item.get("effective_from"), f"{version_id}.effective_from", nullable=True
        )
        end = parse_date(
            item.get("effective_to"), f"{version_id}.effective_to", nullable=True
        )
        if start and end and end < start:
            raise ValueError(f"{version_id} 的效力终止日早于生效日。")
        intervals.append((start, end, version_id))

    intervals.sort(key=lambda item: (item[0] is not None, item[0] or date.min))
    if intervals[0][0] is not None or intervals[-1][1] is not None:
        raise ValueError(f"{topic_id} 的 single_active 版本时间线存在空档。")

    for previous, current in zip(intervals, intervals[1:]):
        previous_end = previous[1]
        current_start = current[0]
        if previous_end is None or current_start is None:
            raise ValueError(f"{topic_id} 的 single_active 版本时间线存在重叠。")
        expected_start = previous_end + timedelta(days=1)
        if current_start < expected_start:
            raise ValueError(f"{topic_id} 的 single_active 版本时间线存在重叠。")
        if current_start > expected_start:
            raise ValueError(f"{topic_id} 的 single_active 版本时间线存在空档。")


def validate_legal_dataset(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema_version") != "1.0":
        raise ValueError("legal-version-cases.json.schema_version 必须为 1.0。")
    require_text(payload.get("dataset_version"), "legal-version-cases.json.dataset_version")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("法律版本数据必须包含核验来源。")
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{index}] 必须是 object。")
        source_id = require_text(source.get("source_id"), f"sources[{index}].source_id")
        if source_id in source_ids:
            raise ValueError(f"重复 source_id：{source_id}")
        source_ids.add(source_id)
        for field in ("document_title", "document_number", "issuing_authority", "verification_source"):
            require_text(source.get(field), f"{source_id}.{field}")
        parse_date(source.get("promulgated_on"), f"{source_id}.promulgated_on")
        parse_date(source.get("effective_from"), f"{source_id}.effective_from")

    topics = payload.get("topics")
    if not isinstance(topics, list) or not topics:
        raise ValueError("topics 必须是非空数组。")
    seen_topics: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for topic in topics:
        if not isinstance(topic, dict):
            raise ValueError("topic 必须是 object。")
        topic_id = require_text(topic.get("topic_id"), "topic_id")
        if topic_id in seen_topics:
            raise ValueError(f"重复 topic_id：{topic_id}")
        seen_topics.add(topic_id)
        if topic.get("source_id") not in source_ids:
            raise ValueError(f"{topic_id} 引用不存在的 source_id。")
        if topic.get("selection_mode") != "single_active":
            raise ValueError(f"{topic_id}.selection_mode 必须为 single_active。")
        versions = topic.get("versions")
        if not isinstance(versions, list) or not versions:
            raise ValueError(f"{topic_id}.versions 必须是非空数组。")
        if not all(isinstance(item, dict) for item in versions):
            raise ValueError(f"{topic_id}.versions 每项必须是 object。")
        version_ids = [require_text(item.get("version_id"), f"{topic_id}.version_id") for item in versions]
        if len(version_ids) != len(set(version_ids)):
            raise ValueError(f"{topic_id} 存在重复 version_id。")
        validate_single_active_timeline(topic_id, versions)
        cases = topic.get("cases")
        if not isinstance(cases, list) or len(cases) < 2:
            raise ValueError(f"{topic_id} 至少需要边界前后两个日期用例。")
        for case in cases:
            if not isinstance(case, dict):
                raise ValueError(f"{topic_id}.cases 项必须是 object。")
            case_id = require_text(case.get("id"), f"{topic_id}.case.id")
            relevant = parse_date(case.get("relevant_date"), f"{case_id}.relevant_date")
            expected = sorted(require_string_list(case.get("expected_active_version_ids"), case_id))
            unknown = sorted(set(expected) - set(version_ids))
            if unknown:
                raise ValueError(f"{case_id} 引用未知版本：{'、'.join(unknown)}")
            normalized.append({
                "id": case_id,
                "topic_id": topic_id,
                "relevant_date": relevant,
                "versions": deepcopy(versions),
                "expected_active_version_ids": expected,
            })
    return normalized


def evaluate_legal_versions(cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    findings: list[str] = []
    for item in cases:
        active = active_version_ids(item["versions"], item["relevant_date"])
        expected = item["expected_active_version_ids"]
        passed = active == expected
        if not passed:
            findings.append(
                f"{item['id']}：适用版本为 {active}，期望为 {expected}。"
            )
        results.append({
            "id": item["id"],
            "topic_id": item["topic_id"],
            "status": "pass" if passed else "blocked",
            "active_version_ids": active,
        })
    return results, findings


def evaluate(evals_path: Path, legal_versions_path: Path) -> dict[str, Any]:
    router_payload = read_json(evals_path)
    legal_payload = read_json(legal_versions_path)
    package_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    findings: list[str] = []
    if router_payload.get("package_version") != package_version:
        findings.append(
            f"评测绑定版本 {router_payload.get('package_version')!r} 与公开包 {package_version!r} 不一致。"
        )
    router_cases = validate_router_dataset(router_payload)
    legal_cases = validate_legal_dataset(legal_payload)
    router_results, router_findings = evaluate_router(router_cases)
    legal_results, legal_findings = evaluate_legal_versions(legal_cases)
    findings.extend(router_findings)
    findings.extend(legal_findings)
    return {
        "status": "pass" if not findings else "blocked",
        "package_version": package_version,
        "datasets": {
            "domain": {
                "version": router_payload["dataset_version"],
                "sha256": hashlib.sha256(evals_path.read_bytes()).hexdigest(),
            },
            "legal_versions": {
                "version": legal_payload["dataset_version"],
                "sha256": hashlib.sha256(legal_versions_path.read_bytes()).hexdigest(),
            },
        },
        "summary": {
            "router_case_count": len(router_results),
            "legal_version_case_count": len(legal_results),
            "passed_count": sum(item["status"] == "pass" for item in (*router_results, *legal_results)),
            "blocked_count": sum(item["status"] != "pass" for item in (*router_results, *legal_results)),
        },
        "router_results": router_results,
        "legal_version_results": legal_results,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 LaborPilot 领域与法律版本评测")
    parser.add_argument("--evals", default=str(DEFAULT_EVALS))
    parser.add_argument("--legal-versions", default=str(DEFAULT_LEGAL_VERSIONS))
    args = parser.parse_args()
    try:
        result = evaluate(Path(args.evals), Path(args.legal_versions))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "status": "blocked",
            "package_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            "findings": [str(exc)],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
