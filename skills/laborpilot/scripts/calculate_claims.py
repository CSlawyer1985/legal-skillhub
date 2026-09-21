#!/usr/bin/env python3
"""生成可追溯的劳动争议专业金额台账并回写案件状态。

``--scaffold`` 只生成待复核计算任务；``--input`` 执行律师／Agent 已选定
的公式。待确认输入会保留为空金额，不能通过金额程序节点。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from case_state import (
    read_json,
    structured_authority_errors,
    structured_calculation_errors,
    structured_evidence_errors,
    structured_issue_errors,
    validate_state,
    write_state,
)
from claims_engine import (
    FORMULA_TYPES,
    FORMULA_VERSION,
    CalculationError,
    calculation_digest,
    calculate_formula,
    decimal_value,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DEFAULT_PARAMETER_DIR = ROOT / "data" / "parameters"
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
MAX_CALCULATIONS = 100
MONEY_QUANTIZER = Decimal("0.01")
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


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def canonical_digest(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def source_reference(state: dict[str, Any], record_id: str) -> dict[str, str]:
    matches: list[tuple[str, dict[str, Any]]] = []
    for collection, id_key in SOURCE_COLLECTION_IDS.items():
        for item in state.get(collection, []):
            if isinstance(item, dict) and item.get(id_key) == record_id:
                matches.append((collection, item))
    if len(matches) != 1:
        fail(f"金额台账来源 ID 必须在案件状态中唯一定位：{record_id}")
    collection, record = matches[0]
    return {
        "collection": collection,
        "record_id": record_id,
        "sha256": canonical_digest(record),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def casework_root(state_path: Path) -> Path:
    return state_path.parent if state_path.parent.name == ".casework" else state_path.parent / ".casework"


def clean_text(value: Any, field: str, *, minimum: int = 4, maximum: int = 2000) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) < minimum:
        fail(f"{field} 过短或为空。")
    if len(text) > maximum:
        fail(f"{field} 超过 {maximum} 字符。")
    return text


def string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"{field} 必须是字符串数组。")
    result = list(dict.fromkeys(item.strip() for item in value))
    if not allow_empty and not result:
        fail(f"{field} 不得为空。")
    return result


def valid_date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        fail(f"{field} 必须为 YYYY-MM-DD。")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        fail(f"{field} 必须为合法 YYYY-MM-DD。")


def optional_date(value: Any, field: str) -> str | None:
    return None if value is None else valid_date(value, field)


def package_matches_case(package: dict[str, Any], jurisdiction: str) -> bool:
    if package["jurisdiction_scope"] == "national":
        return True
    return any(item in jurisdiction or jurisdiction in item for item in package["applicable_jurisdictions"])


def validate_parameter_package(payload: Any, path: Path) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        fail(f"参数包 schema_version 无效：{path}")
    package_id = payload.get("package_id")
    if not isinstance(package_id, str) or not SAFE_ID.fullmatch(package_id):
        fail(f"参数包 package_id 无效：{path}")
    if not isinstance(payload.get("version"), str) or not payload["version"].strip():
        fail(f"参数包 version 为空：{path}")
    if payload.get("jurisdiction_scope") not in {"national", "local"}:
        fail(f"参数包 jurisdiction_scope 无效：{path}")
    jurisdictions = payload.get("applicable_jurisdictions")
    if not isinstance(jurisdictions, list) or not jurisdictions or not all(
        isinstance(item, str) and item.strip() for item in jurisdictions
    ):
        fail(f"参数包 applicable_jurisdictions 无效：{path}")
    start = valid_date(payload.get("effective_from"), f"{package_id}.effective_from")
    end = optional_date(payload.get("effective_to"), f"{package_id}.effective_to")
    valid_date(payload.get("published_at"), f"{package_id}.published_at")
    if end and end < start:
        fail(f"参数包效力终止日早于生效日：{package_id}")
    source = payload.get("source")
    if not isinstance(source, dict):
        fail(f"参数包 source 无效：{package_id}")
    for field in ("title", "issuer", "url", "retrieved_at"):
        if not isinstance(source.get(field), str) or not source[field].strip():
            fail(f"参数包 source.{field} 为空：{package_id}")
    parsed = urlparse(source["url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail(f"参数包 source.url 不是完整 HTTP(S) URL：{package_id}")
    try:
        datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00"))
    except ValueError:
        fail(f"参数包 source.retrieved_at 不是合法 ISO 时间：{package_id}")
    values = payload.get("values")
    if not isinstance(values, dict) or not values:
        fail(f"参数包 values 必须是非空 object：{package_id}")
    for key, record in values.items():
        if not isinstance(key, str) or not SAFE_ID.fullmatch(key) or not isinstance(record, dict):
            fail(f"参数包数值键或记录无效：{package_id}.{key}")
        try:
            numeric = decimal_value(record.get("value"), f"{package_id}.{key}.value")
        except CalculationError as exc:
            fail(str(exc))
        if numeric <= 0:
            fail(f"参数包数值必须大于 0：{package_id}.{key}")
        if not isinstance(record.get("unit"), str) or not record["unit"].strip():
            fail(f"参数包数值缺少单位：{package_id}.{key}")
        value_start = valid_date(record.get("effective_from"), f"{package_id}.{key}.effective_from")
        value_end = optional_date(record.get("effective_to"), f"{package_id}.{key}.effective_to")
        if value_end and value_end < value_start:
            fail(f"参数值效力终止日早于生效日：{package_id}.{key}")
        if not isinstance(record.get("source_locator"), str) or not record["source_locator"].strip():
            fail(f"参数值缺少原文定位：{package_id}.{key}")
    result = json.loads(json.dumps(payload, ensure_ascii=False))
    result["_path"] = str(path)
    result["_sha256"] = sha256_bytes(path.read_bytes())
    return result


def load_parameter_packages(extra_paths: list[str]) -> dict[str, dict[str, Any]]:
    paths = sorted(DEFAULT_PARAMETER_DIR.glob("*.json"))
    paths.extend(Path(item).expanduser().resolve() for item in extra_paths)
    packages: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"无法读取参数包 {path}：{exc}")
        package = validate_parameter_package(payload, path)
        previous = packages.get(package["package_id"])
        if previous and previous["_sha256"] != package["_sha256"]:
            fail(f"存在 package_id 相同但内容不同的参数包：{package['package_id']}")
        packages[package["package_id"]] = package
    return packages


def resolve_parameters(
    refs: Any,
    *,
    packages: dict[str, dict[str, Any]],
    relevant_date: str,
    jurisdiction: str,
) -> dict[str, Any]:
    if refs is None:
        return {}
    if not isinstance(refs, dict):
        fail("parameter_refs 必须是 object。")
    resolved: dict[str, Any] = {}
    for alias, ref in refs.items():
        if not isinstance(alias, str) or not SAFE_ID.fullmatch(alias) or not isinstance(ref, dict):
            fail(f"parameter_refs.{alias} 无效。")
        package_id = ref.get("package_id")
        parameter_key = ref.get("parameter_key")
        package = packages.get(package_id)
        if package is None:
            fail(f"找不到参数包：{package_id}")
        if parameter_key not in package["values"]:
            fail(f"参数包 {package_id} 不包含 {parameter_key}。")
        if not package_matches_case(package, jurisdiction):
            fail(f"参数包 {package_id} 与案件地域 {jurisdiction} 不匹配。")
        if relevant_date < package["effective_from"] or (
            package["effective_to"] and relevant_date > package["effective_to"]
        ):
            fail(f"参数包 {package_id} 不覆盖本案相关日期 {relevant_date}。")
        value = package["values"][parameter_key]
        if relevant_date < value["effective_from"] or (
            value["effective_to"] and relevant_date > value["effective_to"]
        ):
            fail(f"参数 {package_id}.{parameter_key} 不覆盖本案相关日期 {relevant_date}。")
        resolved[alias] = {
            "package_id": package_id,
            "package_version": package["version"],
            "package_sha256": package["_sha256"],
            "package_path": package["_path"],
            "parameter_key": parameter_key,
            "value": str(value["value"]),
            "unit": value["unit"],
            "effective_from": value["effective_from"],
            "effective_to": value["effective_to"],
            "source_locator": value["source_locator"],
            "selection_note": value.get("selection_note"),
            "jurisdiction_scope": package["jurisdiction_scope"],
            "applicable_jurisdictions": package["applicable_jurisdictions"],
            "source": package["source"],
        }
    return resolved


def known_source_ids(state: dict[str, Any]) -> set[str]:
    fields = [
        ("materials", "material_id"), ("facts", "fact_id"), ("evidence", "evidence_id"),
        ("rules", "rule_id"), ("issues", "issue_id"), ("decisions", "decision_id"),
    ]
    return {
        item[key]
        for collection, key in fields
        for item in state.get(collection, [])
        if isinstance(item, dict) and isinstance(item.get(key), str) and item[key]
    }


def normalize_inputs(value: Any, known_sources: set[str]) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(value, dict):
        fail("inputs 必须是 object。")
    result: dict[str, Any] = {}
    all_sources: list[str] = []
    for key, record in value.items():
        if key == "component_ids":
            result[key] = string_list(record, "inputs.component_ids")
            continue
        if not isinstance(record, dict) or "value" not in record:
            fail(f"inputs.{key} 必须包含 value 和 source_ids。")
        sources = string_list(record.get("source_ids"), f"inputs.{key}.source_ids")
        missing = sorted(set(sources) - known_sources)
        if missing:
            fail(f"inputs.{key}.source_ids 引用不存在的 ID：{', '.join(missing)}")
        result[key] = {"value": str(record["value"]), "source_ids": sources}
        note = record.get("note")
        if note is not None:
            result[key]["note"] = clean_text(note, f"inputs.{key}.note", minimum=2, maximum=500)
        all_sources.extend(sources)
    return result, list(dict.fromkeys(all_sources))


def normalize_calculations(
    records: list[Any],
    *,
    state: dict[str, Any],
    packages: dict[str, dict[str, Any]],
    actor: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    issues = {
        item.get("issue_id"): item for item in state.get("issues", [])
        if isinstance(item, dict) and isinstance(item.get("issue_id"), str)
    }
    adopted_rules = {
        item.get("rule_id"): item for item in state.get("rules", [])
        if isinstance(item, dict)
        and item.get("adoption_status") == "adopted"
        and item.get("verification_status") == "verified"
        and item.get("applicability_status") == "applicable"
    }
    sources = known_source_ids(state)
    generated_at = now_iso()
    calculations: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    prior_amounts: dict[str, Decimal] = {}
    seen_claims: set[str] = set()

    for index, value in enumerate(records):
        if not isinstance(value, dict):
            fail(f"calculations[{index}] 必须是 object。")
        calculation_id = value.get("calculation_id")
        claim_id = value.get("claim_id")
        for field, identifier in (("calculation_id", calculation_id), ("claim_id", claim_id)):
            if not isinstance(identifier, str) or not SAFE_ID.fullmatch(identifier):
                fail(f"calculations[{index}].{field} 无效。")
        if claim_id in seen_claims:
            fail(f"同一批输入中 claim_id 不得重复：{claim_id}")
        seen_claims.add(claim_id)
        formula_type = value.get("formula_type")
        if formula_type not in FORMULA_TYPES:
            fail(f"calculations[{index}].formula_type 无效：{formula_type}")
        issue_ids = string_list(value.get("issue_ids"), f"calculations[{index}].issue_ids")
        missing_issues = sorted(set(issue_ids) - set(issues))
        if missing_issues:
            fail(f"计算项引用不存在的争点：{', '.join(missing_issues)}")
        rule_ids = string_list(value.get("rule_ids"), f"calculations[{index}].rule_ids")
        missing_rules = sorted(set(rule_ids) - set(adopted_rules))
        if missing_rules:
            fail(f"计算项必须引用已核验且适用的法源：{', '.join(missing_rules)}")
        unrelated_rules = [
            rule_id for rule_id in rule_ids if adopted_rules[rule_id].get("issue_id") not in issue_ids
        ]
        if unrelated_rules:
            fail(f"计算项法源与争点不匹配：{', '.join(unrelated_rules)}")
        inputs, input_sources = normalize_inputs(value.get("inputs", {}), sources)
        pending_inputs = string_list(
            value.get("pending_inputs", []), f"calculations[{index}].pending_inputs", allow_empty=True
        )
        assumptions = string_list(value.get("assumptions"), f"calculations[{index}].assumptions")
        assumptions = [clean_text(item, "assumption", minimum=8, maximum=1000) for item in assumptions]
        relevant_date = valid_date(value.get("relevant_date"), f"calculations[{index}].relevant_date")
        risk = clean_text(value.get("risk"), f"calculations[{index}].risk", minimum=8, maximum=1200)
        name = clean_text(value.get("name"), f"calculations[{index}].name", minimum=2, maximum=200)
        parameter_refs = value.get("parameter_refs", {})
        resolved_parameters: dict[str, Any] = {}
        amount: str | None = None
        expression: str | None = None
        steps: list[dict[str, str]] = []
        status = "needs_confirmation" if pending_inputs else "calculated"
        if status == "calculated":
            resolved_parameters = resolve_parameters(
                parameter_refs, packages=packages, relevant_date=relevant_date,
                jurisdiction=state["jurisdiction"],
            )
            try:
                raw, expression, steps = calculate_formula(
                    formula_type, inputs, resolved_parameters, prior_amounts
                )
            except CalculationError as exc:
                fail(f"{calculation_id} 计算失败：{exc}")
            rounded = raw.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)
            amount = format(rounded, ".2f")
            prior_amounts[calculation_id] = rounded
        elif parameter_refs and not isinstance(parameter_refs, dict):
            fail(f"calculations[{index}].parameter_refs 必须是 object。")

        record = {
            "calculation_id": calculation_id, "claim_id": claim_id, "name": name,
            "formula_type": formula_type, "formula_version": FORMULA_VERSION, "status": status,
            "issue_ids": issue_ids, "rule_ids": rule_ids, "relevant_date": relevant_date,
            "inputs": inputs, "input_source_ids": input_sources, "parameter_refs": parameter_refs,
            "resolved_parameters": resolved_parameters, "assumptions": assumptions,
            "pending_inputs": pending_inputs, "risk": risk, "expression": expression,
            "steps": steps, "amount": amount, "currency": "CNY",
            "rounding": "ROUND_HALF_UP", "decimal_places": 2,
            "alternative": bool(value.get("alternative", False)),
            "created_by": actor, "created_at": generated_at,
        }
        record["calculation_digest"] = calculation_digest(record)
        calculations.append(record)
        claims.append({
            "claim_id": claim_id, "name": name, "claim_type": "monetary",
            "analysis_status": "reviewed", "calculation_status": status,
            "issue_ids": issue_ids, "rule_ids": rule_ids, "amount": amount,
            "currency": "CNY", "calculation_id": calculation_id,
            "pending_inputs": pending_inputs, "risk": risk,
            "alternative": bool(value.get("alternative", False)),
            "created_by": actor, "created_at": generated_at,
        })
    return calculations, claims


def load_records(path: Path) -> list[Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"计算输入不存在：{path}")
    except json.JSONDecodeError as exc:
        fail(f"计算输入不是合法 JSON：{exc}")
    records = payload.get("calculations") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        fail("计算输入必须是非空数组，或含 calculations 数组的 object。")
    if len(records) > MAX_CALCULATIONS:
        fail(f"单次计算不得超过 {MAX_CALCULATIONS} 项。")
    return records


def formula_suggestions(issue: dict[str, Any]) -> list[str]:
    text = f"{issue.get('issue', '')} {issue.get('our_position', {}).get('position', '')}"
    suggestions: list[str] = []
    mappings = [
        (("违法解除", "赔偿金"), ["unlawful_termination_compensation"]),
        (("经济补偿",), ["economic_compensation", "n_plus_one"]),
        (("代通知", "N＋1", "N+1"), ["n_plus_one"]),
        (("加班",), ["overtime_workday", "overtime_rest_day", "overtime_statutory_holiday"]),
        (("工伤", "伤残"), [
            "work_injury_lump_sum_disability", "work_injury_disability_allowance",
            "work_injury_regional_benefit", "work_injury_three_lump_sums",
        ]),
        (("竞业",), ["non_compete_compensation"]),
    ]
    for terms, formulas in mappings:
        if any(term in text for term in terms):
            suggestions.extend(formulas)
    return list(dict.fromkeys(suggestions))


def render_scaffold(state: dict[str, Any], generated_at: str) -> tuple[str, str]:
    candidates = []
    for issue in state.get("issues", []):
        if not isinstance(issue, dict) or issue.get("issue_type") not in {"claim", "defense"}:
            continue
        candidates.append({
            "candidate_id": f"ccandidate-{hashlib.sha256(str(issue['issue_id']).encode()).hexdigest()[:16]}",
            "analysis_status": "to_review", "issue_id": issue["issue_id"], "issue": issue["issue"],
            "formula_suggestions": formula_suggestions(issue),
            "required_confirmation": [
                "请求权基础与公式类型", "工资基数、工作年限或待遇月数",
                "每个数值输入的事实／证据来源", "动态参数的年度、地域、用途与官方来源",
                "互斥请求、备选口径和金额风险",
            ],
        })
    payload = {
        "status": "review_required", "case_id": state.get("case_id"),
        "generated_at": generated_at, "candidate_count": len(candidates), "candidates": candidates,
    }
    lines = [
        "# 金额计算待办", "", "> 本骨架只提示可能的计算路径，不写入 claims[] 或 calculations[]。", "",
        "| 争点 | 公式候选 | 必须确认 |", "|---|---|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item['issue']} | {'、'.join(item['formula_suggestions']) or '由律师选择'} | "
            f"{'；'.join(item['required_confirmation'])} |"
        )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def render_ledger(state: dict[str, Any], generated_at: str) -> tuple[str, str]:
    calculations = state.get("calculations", [])
    payload = {
        "status": "lawyer_review_required", "case_id": state.get("case_id"),
        "generated_at": generated_at, "calculation_count": len(calculations),
        "calculations": calculations,
    }
    lines = ["# 金额计算台账", "", "> 状态：待律师复核；脚本不自行决定请求权基础。", ""]
    for index, item in enumerate(calculations, 1):
        lines.extend([
            f"## {index}. {item['name']}", "", f"- 状态：{item['status']}",
            f"- 公式：{item['formula_type']}（{item['formula_version']}）",
            f"- 争点：{'、'.join(item['issue_ids'])}", f"- 法源：{'、'.join(item['rule_ids'])}",
            f"- 相关日期：{item['relevant_date']}",
            f"- 算式：{item['expression'] or '待确认输入补齐后计算'}",
            f"- 金额：{item['amount'] or '未生成'}",
            f"- 输入来源：{'、'.join(item['input_source_ids']) or '尚待补齐'}",
            f"- 待确认：{'、'.join(item['pending_inputs']) or '无'}", f"- 风险：{item['risk']}", "",
        ])
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(lines) + "\n"


def merge_records(
    state: dict[str, Any], calculations: list[dict[str, Any]], claims: list[dict[str, Any]], *, replace: bool
) -> tuple[int, list[str], list[str]]:
    state.setdefault("calculations", [])
    replaced_count = 0
    if replace:
        replaced_count = len(state["calculations"])
        state["calculations"] = []
        state["claims"] = []
    calc_by_id = {
        item.get("calculation_id"): index for index, item in enumerate(state["calculations"])
        if isinstance(item, dict) and item.get("calculation_id")
    }
    claim_by_id = {
        item.get("claim_id"): index for index, item in enumerate(state["claims"])
        if isinstance(item, dict) and item.get("claim_id")
    }
    added: list[str] = []
    updated: list[str] = []
    for calculation, claim in zip(calculations, claims):
        existing_index = calc_by_id.get(calculation["calculation_id"])
        if existing_index is None:
            state["calculations"].append(calculation)
            added.append(calculation["calculation_id"])
        else:
            previous = state["calculations"][existing_index]
            calculation["created_at"] = previous.get("created_at") or calculation["created_at"]
            calculation["created_by"] = previous.get("created_by") or calculation["created_by"]
            calculation["updated_at"] = now_iso()
            state["calculations"][existing_index] = calculation
            updated.append(calculation["calculation_id"])
        claim_index = claim_by_id.get(claim["claim_id"])
        if claim_index is None:
            state["claims"].append(claim)
        else:
            previous_claim = state["claims"][claim_index]
            claim["created_at"] = previous_claim.get("created_at") or claim["created_at"]
            claim["created_by"] = previous_claim.get("created_by") or claim["created_by"]
            claim["updated_at"] = now_iso()
            state["claims"][claim_index] = claim
    return replaced_count, added, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 专业金额计算器")
    parser.add_argument("--state", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--scaffold", action="store_true", help="按争点生成待复核金额任务")
    mode.add_argument("--input", help="经复核的金额计算输入 JSON")
    parser.add_argument("--parameter-package", action="append", default=[], help="追加版本化参数包 JSON")
    parser.add_argument(
        "--replace-existing-calculations", action="store_true",
        help="以本次台账替换旧 calculations[] 与 claims[]；旧状态保留在历史快照",
    )
    parser.add_argument("--actor", default="labor-claims-procedure")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    if state.get("current_node") != "claims_procedure":
        fail(f"当前节点为 {state.get('current_node')}，不能执行金额程序。")
    if state.get("pending_nodes"):
        fail("证据或法源分支尚未全部完成，不能执行金额程序。")
    if args.scaffold and args.replace_existing_calculations:
        fail("--replace-existing-calculations 只能与 --input 一起使用。")
    upstream_errors = structured_issue_errors(state) + structured_evidence_errors(state) + structured_authority_errors(state)
    if upstream_errors:
        fail("金额计算上游尚未完成：\n" + "\n".join(upstream_errors))

    output_root = casework_root(state_path) / "calculations"
    generated_at = now_iso()
    if args.scaffold:
        scaffold_json, scaffold_md = render_scaffold(state, generated_at)
        atomic_write_text(output_root / "scaffold.json", scaffold_json)
        atomic_write_text(output_root / "scaffold.md", scaffold_md)
        payload = json.loads(scaffold_json)
        print(json.dumps({
            "status": payload["status"], "candidate_count": payload["candidate_count"],
            "scaffold": str(output_root / "scaffold.json"),
        }, ensure_ascii=False))
        return 0

    packages = load_parameter_packages(args.parameter_package)
    records = load_records(Path(args.input).expanduser().resolve())
    calculations, claims = normalize_calculations(records, state=state, packages=packages, actor=args.actor)
    ids = [item["calculation_id"] for item in calculations]
    if len(ids) != len(set(ids)):
        fail("同一批输入中 calculation_id 不得重复。")

    candidate_state = json.loads(json.dumps(state, ensure_ascii=False))
    replaced_count, added_ids, updated_ids = merge_records(
        candidate_state, calculations, claims, replace=args.replace_existing_calculations
    )
    calculation_errors = structured_calculation_errors(candidate_state)
    if calculation_errors:
        hint = "\n旧 claims[] 或 calculations[] 为占位结构时，请使用 --replace-existing-calculations。"
        fail("金额回写后的案件状态无效：\n" + "\n".join(calculation_errors) + hint)

    ledger_json, ledger_md = render_ledger(candidate_state, generated_at)
    ledger_json_path = output_root / "ledger.json"
    ledger_md_path = output_root / "ledger.md"
    artifact_id = f"artifact-calculation-{hashlib.sha256(ledger_json.encode()).hexdigest()[:16]}"
    ledger_source_ids = sorted({
        *[item["calculation_id"] for item in calculations],
        *[item["claim_id"] for item in claims],
        *[source_id for item in calculations for source_id in item["input_source_ids"]],
    })
    candidate_state.setdefault("artifacts", []).append({
        "artifact_id": artifact_id, "kind": "calculation_ledger", "path": str(ledger_json_path),
        "delivery_status": "internal_work_product",
        "version": FORMULA_VERSION, "sha256": sha256_bytes(ledger_json.encode("utf-8")),
        "generator": "scripts/calculate_claims.py", "producer_version": PACKAGE_VERSION,
        "created_by": args.actor, "created_at": generated_at,
        "derived_from": [],
        "source_refs": [source_reference(candidate_state, source_id) for source_id in ledger_source_ids],
    })
    candidate_state.setdefault("events", []).append({
        "event_id": f"evt-{uuid.uuid4().hex[:12]}", "event_type": "calculation_ledger_built",
        "actor": args.actor, "occurred_at": generated_at,
        "details": {
            "added_calculation_ids": added_ids, "updated_calculation_ids": updated_ids,
            "replaced_previous_count": replaced_count, "ledger_json": str(ledger_json_path),
            "ledger_markdown": str(ledger_md_path), "artifact_id": artifact_id,
        },
    })
    final_errors = validate_state(candidate_state) + structured_calculation_errors(candidate_state)
    if final_errors:
        fail("金额台账最终状态无效：\n" + "\n".join(final_errors))
    atomic_write_text(ledger_json_path, ledger_json)
    atomic_write_text(ledger_md_path, ledger_md)
    write_state(state_path, candidate_state, source=state_path, operation="calculation-ledger-built")
    calculated_count = sum(item["status"] == "calculated" for item in calculations)
    print(json.dumps({
        "status": "lawyer_review_required", "calculation_count": len(candidate_state["calculations"]),
        "calculated_count": calculated_count,
        "needs_confirmation_count": len(calculations) - calculated_count,
        "replaced_previous_count": replaced_count, "ledger": str(ledger_json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
