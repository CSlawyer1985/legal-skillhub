#!/usr/bin/env python3
"""Load review plans and enrich only explicit, structured decision fields."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ACTION_ALIAS = {
    "comment": "comment",
    "批注": "comment",
    "注释": "comment",
    "report-only": "report-only",
    "report_only": "report-only",
    "仅报告": "report-only",
    "仅写入意见书": "report-only",
    "意见书": "report-only",
    "replace": "replace",
    "修订": "replace",
    "修改": "replace",
    "insert": "insert",
    "插入": "insert",
    "新增": "insert",
    "delete": "delete",
    "删除": "delete",
    "auto": "auto",
    "自动": "auto",
    "none": "none",
    "skip": "skip",
}
EVIDENCE_ALIASES = {
    "confirmed": "confirmed",
    "已确认": "confirmed",
    "确定": "confirmed",
    "reasonable_assumption": "reasonable_assumption",
    "reasonable-assumption": "reasonable_assumption",
    "合理假设": "reasonable_assumption",
    "major_choice": "major_choice",
    "major-choice": "major_choice",
    "重大选择": "major_choice",
    "not_applicable": "not_applicable",
    "not-applicable": "not_applicable",
    "不适用": "not_applicable",
}
EDIT_POLICIES = {"comment-first", "balanced", "revise-first"}
DIRECT_EDIT_ACTIONS = {"replace", "insert", "delete"}
try:  # 与执行器/报告侧共用同一份口径定义，避免两处漂移
    from .comment_targets import RESPONSE_STANCES as RESPONSE_STANCE_MAP
except ImportError:  # 直接以脚本方式运行时（无包上下文）
    from comment_targets import RESPONSE_STANCES as RESPONSE_STANCE_MAP

RESPONSE_STANCE_VALUES = set(RESPONSE_STANCE_MAP)

RISK_LEVELS = {"P0", "P1", "P2"}
PENDING_KINDS = {"fill", "verify", "authorization"}
REPORT_BUCKETS = {"general", "tax", "mixed"}

#: 条款联动**必检组**（`review-doctrine.md` 六 / `modular-knowledge-routing.md`「联动组」）。
#: 每组须显式登记 `status=checked`，或 `status=not_applicable` + 理由。
#: 写成清单的原因是一次实测漏检：把"要不要投保是商业取舍"（动作判断）
#: 误当成"不必检查保险安排"（识别），整组（责任限制/赔偿/**保险**）被漏掉。
#: 漏检类问题的根因往往不是不知道，而是**没有交付物逼你交**——这张清单就是那个交付物。
LINKAGE_GROUPS = {
    "payment_delivery_acceptance": "付款、开票、交付与验收",
    "change_termination_breach": "变更、通知、解除与违约",
    "confidentiality_data_ip": "保密、数据处理与知识产权",
    "liability_insurance": "责任限制、违约金、赔偿与保险",
    "role_and_third_party": "角色边界与第三方专业服务（组织、协调、转介、外包）",
    "expiry_exit_handover": "到期、续期、退出、交接与数据迁移",
}

#: 审查人**不得使用**的当事人表态措辞（`redline-comment-policy` 十一）。
#: 回复是审查人的核对结论，不是当事人的意思表示——"采纳/同意/接受/认可"一律越位。
#: 之所以做成硬校验：同类错误实测发生过（把现稿本来就有的内容写成"已采纳"），
#: 既是事实错误，也是角色错误。
REVIEWER_VOICE_FORBIDDEN = (
    "已采纳",
    "予以采纳",
    "同意该意见",
    "接受该意见",
    "认可该意见",
    "我方同意",
    "我们会落实",
)
SUPPORTED_ACTIONS = {
    "auto", "comment", "report-only", "replace", "insert", "delete", "none", "skip"
}
SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "knowledge_v2"
    / "schemas"
    / "review_plan.schema.json"
)


def load_plan(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("审查计划 JSON 顶层必须是对象")
    # Read the bundled contract on every load so packaging/reference regressions fail
    # before a contract is edited.  Runtime validation remains dependency-free.
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"审查计划 schema 不存在: {SCHEMA_PATH}")
    json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return payload


def get_plan_meta(plan: dict[str, Any]) -> dict[str, Any]:
    meta = plan.get("meta")
    return meta if isinstance(meta, dict) else {}


def get_findings(plan: dict[str, Any]) -> list[Any]:
    findings = plan.get("findings") or plan.get("risks") or []
    if not isinstance(findings, list):
        raise ValueError("findings 必须是数组")
    return findings


def _normalize_action(action: Any) -> str:
    raw = str(action or "").strip()
    if not raw:
        return "auto"
    return ACTION_ALIAS.get(raw.lower(), ACTION_ALIAS.get(raw, raw.lower()))


def _normalize_risk_level(value: Any) -> str:
    raw = str(value or "P2").strip().upper()
    aliases = {"高": "P0", "HIGH": "P0", "中": "P1", "MEDIUM": "P1", "低": "P2", "LOW": "P2"}
    return aliases.get(raw, raw)


def _text_present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(isinstance(item, str) and item.strip() for item in value)
    return False


def _normalize_legacy_fields(finding: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(finding)
    if not _text_present(normalized.get("legal_basis")):
        for key in ("basis", "principle_basis"):
            if _text_present(normalized.get(key)):
                normalized["legal_basis"] = normalized[key]
                break
    if not _text_present(normalized.get("tax_advice")):
        for key in (
            "tax_suggestions", "tax_recommendations", "tax_notes",
            "tax_suggestion", "tax_recommendation", "涉税建议",
        ):
            if _text_present(normalized.get(key)):
                normalized["tax_advice"] = normalized[key]
                break
    normalized["risk_level"] = _normalize_risk_level(normalized.get("risk_level"))
    normalized["action"] = _normalize_action(normalized.get("action"))
    return normalized


def normalize_edit_policy(policy: Any, default: str = "revise-first") -> str:
    raw = str(policy or "").strip().lower()
    if not raw:
        return default
    if raw not in EDIT_POLICIES:
        raise ValueError(f"不支持的 edit_policy: {policy}")
    return raw


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "是"}
    return False


def _has_direct_edit_payload(finding: dict[str, Any], *, edit_policy: str) -> bool:
    if (
        finding.get("replacement_text") is not None
        or finding.get("insert_text") is not None
        or _is_truthy(finding.get("delete"))
        or _is_truthy(finding.get("remove"))
    ):
        return True
    return edit_policy != "comment-first" and bool(
        str(finding.get("recommended_text") or "").strip()
    )


def infer_evidence_state(
    finding: dict[str, Any], *, edit_policy: str = "revise-first"
) -> str:
    explicit = str(
        finding.get("evidence_state") or finding.get("decision_state") or ""
    ).strip()
    if explicit:
        normalized = EVIDENCE_ALIASES.get(explicit.lower()) or EVIDENCE_ALIASES.get(explicit)
        if not normalized:
            raise ValueError(f"不支持的 evidence_state: {explicit}")
        return normalized
    if _is_truthy(finding.get("not_applicable")):
        return "not_applicable"
    if any(
        _is_truthy(finding.get(key))
        for key in (
            "requires_authorization",
            "needs_negotiation",
            "requires_negotiation",
            "needs_confirmation",
            "requires_confirmation",
        )
    ):
        return "major_choice"
    if finding.get("unknown_facts") or finding.get("assumptions"):
        return "reasonable_assumption"
    action = _normalize_action(finding.get("action"))
    if action in {"none", "skip"}:
        return "not_applicable"
    if action == "comment":
        return "major_choice"
    if action in DIRECT_EDIT_ACTIONS or _has_direct_edit_payload(
        finding, edit_policy=normalize_edit_policy(edit_policy)
    ):
        return "confirmed"
    return "major_choice"


def infer_strategy_flags(
    finding: dict[str, Any], *, edit_policy: str = "revise-first"
) -> dict[str, bool]:
    """Compatibility fields derived from the explicit evidence state."""
    state = infer_evidence_state(finding, edit_policy=edit_policy)
    return {
        "needs_negotiation": state == "major_choice",
        "deterministic_edit": state == "confirmed"
        and _has_direct_edit_payload(
            finding, edit_policy=normalize_edit_policy(edit_policy)
        ),
    }


def enrich_findings(
    findings: list[Any], *, edit_policy: str = "revise-first"
) -> list[Any]:
    policy = normalize_edit_policy(edit_policy)
    enriched: list[Any] = []
    for index, item in enumerate(findings, start=1):
        if not isinstance(item, dict):
            enriched.append(item)
            continue
        finding = _normalize_legacy_fields(item)
        finding.setdefault("id", f"R{index:03d}")
        finding.setdefault("evidence_state", infer_evidence_state(finding, edit_policy=policy))
        inferred = infer_strategy_flags(finding, edit_policy=policy)
        finding.setdefault("needs_negotiation", inferred["needs_negotiation"])
        finding.setdefault("deterministic_edit", inferred["deterministic_edit"])
        enriched.append(finding)
    return enriched


def _collect_trigger_results(plan: dict[str, Any]) -> list[dict[str, Any]]:
    safety = plan.get("safety") if isinstance(plan.get("safety"), dict) else {}
    results = safety.get("trigger_results")
    if not isinstance(results, list):
        results = plan.get("trigger_results")
    normalized = [item for item in (results or []) if isinstance(item, dict)]

    meta = get_plan_meta(plan)
    primary_type_id = str(
        meta.get("primary_type_id") or meta.get("contract_type_id") or ""
    ).strip()
    facts = plan.get("transaction_facts")
    if primary_type_id == "type-equity-transfer" and isinstance(facts, dict):
        try:
            from ..knowledge.detect_equity_transfer_triggers import detect
        except ImportError:
            from scripts.knowledge.detect_equity_transfer_triggers import detect
        computed = detect(facts)
        if not any(item.get("type_id") == computed.get("type_id") for item in normalized):
            normalized.append(computed)
    return normalized


def _attach_directed_blocks(plan: dict[str, Any]) -> None:
    results = _collect_trigger_results(plan)
    safety = plan.get("safety") if isinstance(plan.get("safety"), dict) else {}
    safety["trigger_results"] = results
    plan["safety"] = safety
    if not results:
        return

    for finding in get_findings(plan):
        if not isinstance(finding, dict):
            continue
        existing = finding.get("directed_block")
        if isinstance(existing, dict) and _is_truthy(existing.get("active")):
            continue
        output_kind = str(finding.get("output_kind") or "").strip()
        if not output_kind:
            continue
        finding_trigger_ids = {
            str(item).strip() for item in finding.get("trigger_ids", []) if str(item).strip()
        }
        matched_results: list[dict[str, Any]] = []
        for result in results:
            if result.get("status") != "directed_block_required":
                continue
            prohibited = {str(item).strip() for item in result.get("prohibited_outputs", [])}
            result_trigger_ids = {
                str(item.get("trigger_id") or "").strip()
                for item in result.get("triggered", [])
                if isinstance(item, dict)
            }
            if output_kind not in prohibited:
                continue
            if finding_trigger_ids and not (finding_trigger_ids & result_trigger_ids):
                continue
            matched_results.append(result)
        if not matched_results:
            continue
        trigger_ids = sorted(
            {
                str(item.get("trigger_id") or "").strip()
                for result in matched_results
                for item in result.get("triggered", [])
                if isinstance(item, dict) and item.get("trigger_id")
            }
        )
        required_outputs = list(
            dict.fromkeys(
                str(item).strip()
                for result in matched_results
                for item in result.get("required_outputs", [])
                if str(item).strip()
            )
        )
        finding["directed_block"] = {
            "active": True,
            "scope": "this_finding",
            "reason": "该项输出与已命中 P0 触发器的禁止输出精确匹配",
            "prohibited_actions": [
                "auto", "comment", "report-only", "replace", "insert", "delete"
            ],
            "prohibited_outputs": [output_kind],
            "required_outputs": required_outputs,
            "trigger_ids": trigger_ids,
        }


def validate_plan(plan: dict[str, Any]) -> None:
    """Validate the executable subset of review-plan.schema.json without jsonschema."""
    errors: list[str] = []
    meta = get_plan_meta(plan)
    if not str(meta.get("contract_name") or "").strip():
        errors.append("meta.contract_name 不得为空")
    if not str(meta.get("party_role") or meta.get("role") or "").strip():
        errors.append("meta.party_role 不得为空")
    try:
        normalize_edit_policy(meta.get("edit_policy"))
    except ValueError as exc:
        errors.append(str(exc))

    findings = get_findings(plan)
    seen_ids: set[str] = set()
    for index, item in enumerate(findings, start=1):
        prefix = f"findings[{index - 1}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} 必须是对象")
            continue
        finding_id = str(item.get("id") or "").strip()
        if not finding_id:
            errors.append(f"{prefix}.id 不得为空")
        elif finding_id in seen_ids:
            errors.append(f"{prefix}.id 重复: {finding_id}")
        seen_ids.add(finding_id)
        if item.get("risk_level") not in RISK_LEVELS:
            errors.append(f"{prefix}.risk_level 必须为 P0/P1/P2")
        state = str(item.get("evidence_state") or "")
        if state not in set(EVIDENCE_ALIASES.values()):
            errors.append(f"{prefix}.evidence_state 无效: {state or '<empty>'}")
        action = _normalize_action(item.get("action"))
        if action not in SUPPORTED_ACTIONS:
            errors.append(f"{prefix}.action 无效: {action}")
        # 1.5 的**机制落点**：命中库内明确规则且方向明确 ⇒ 不是"该由客户决定的结构性选择"，
        # 因而不得记 major_choice（执行器见到 major_choice 会强制仅批注）。
        # 只写在文档里的规则拦不住人——这条校验就是它的执行点。
        rule_hit = str(item.get("rule_hit") or "").strip()
        direction_clear = item.get("direction_clear")
        if rule_hit and direction_clear is None:
            errors.append(
                f"{prefix}.direction_clear 在填写 rule_hit 时必填"
                "（方向不明确的，不应声称命中明确规则）"
            )
        if rule_hit and _is_truthy(direction_clear) and state == "major_choice":
            errors.append(
                f"{prefix} 自相矛盾：已命中库内明确规则（{rule_hit}）且 direction_clear=true，"
                "却记 evidence_state=major_choice。按 redline-comment-policy 1.5，"
                "命中明确规则且方向明确时应记 confirmed（口径已定）或 "
                "reasonable_assumption（填入默认值并注明可调整）——"
                "major_choice 只留给「没有规则可依的纯商业取舍」。"
            )
        if not _text_present(item.get("legal_basis")):
            errors.append(f"{prefix}.legal_basis 不得为空")
        pending_kind = item.get("pending_kind")
        if pending_kind is not None and pending_kind not in PENDING_KINDS:
            errors.append(f"{prefix}.pending_kind 无效: {pending_kind}")
        report_bucket = item.get("report_bucket")
        if report_bucket is not None and report_bucket not in REPORT_BUCKETS:
            errors.append(f"{prefix}.report_bucket 无效: {report_bucket}")
        if report_bucket in {"tax", "mixed"} and not _text_present(item.get("tax_advice")):
            errors.append(f"{prefix}.tax_advice 在 report_bucket={report_bucket} 时必填")
        block = item.get("directed_block")
        if block is not None:
            if not isinstance(block, dict):
                errors.append(f"{prefix}.directed_block 必须是对象")
            elif _is_truthy(block.get("active")):
                if block.get("scope") != "this_finding":
                    errors.append(f"{prefix}.directed_block.scope 必须为 this_finding")
                if not str(block.get("reason") or "").strip():
                    errors.append(f"{prefix}.directed_block.reason 不得为空")
    # 联动必检清单：**结构**在此校验；**缺整张清单**不阻断执行，
    # 而是由报告侧的完整性检查报为未闭合事项——这样既保证新审查必须登记，
    # 又不打破"历史 plan 仍可执行"的兼容承诺（见 test_rule_studio_integration 的 RES-026）。
    checklist = plan.get("linkage_checklist")
    if isinstance(checklist, dict):
        for key, label in LINKAGE_GROUPS.items():
            entry = checklist.get(key)
            if not isinstance(entry, dict):
                errors.append(
                    f"linkage_checklist.{key} 缺失（{label}）："
                    "须填 status=checked，或 status=not_applicable 并写明 reason"
                )
                continue
            status = str(entry.get("status") or "").strip()
            if status not in {"checked", "not_applicable"}:
                errors.append(
                    f"linkage_checklist.{key}.status 必须为 checked 或 not_applicable"
                    f"（当前：{status or '<空>'}）"
                )
            if status == "not_applicable" and not str(entry.get("reason") or "").strip():
                errors.append(f"linkage_checklist.{key} 标为 not_applicable 时必须写明 reason")

    responses = plan.get("responses")
    if responses is not None:
        if not isinstance(responses, list):
            errors.append("responses 必须是数组")
        else:
            for index, item in enumerate(responses, start=1):
                prefix = f"responses[{index - 1}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix} 必须是对象")
                    continue
                if not str(item.get("id") or "").strip():
                    errors.append(f"{prefix}.id 不得为空")
                stance = str(item.get("stance") or "").strip()
                if stance not in RESPONSE_STANCE_VALUES:
                    errors.append(
                        f"{prefix}.stance 无效：{stance or '<空>'}"
                        f"（允许：{'/'.join(sorted(RESPONSE_STANCE_VALUES))}）"
                    )
                if not str(item.get("text") or "").strip():
                    errors.append(f"{prefix}.text 不得为空")
                else:
                    voice_hits = [
                        word for word in REVIEWER_VOICE_FORBIDDEN if word in str(item["text"])
                    ]
                    if voice_hits:
                        errors.append(
                            f"{prefix}.text 使用了当事人表态措辞：{'、'.join(voice_hits)}——"
                            "审查人只写核对结论（经核对，现稿已体现／本轮已在第X条补充／"
                            "未按该意见修改／仍需填写），不得写「采纳、同意、接受、认可」"
                            "（redline-comment-policy 十一）"
                        )
                if stance == "already_present" and not str(item.get("evidence") or "").strip():
                    errors.append(
                        f"{prefix}.evidence 在 stance=already_present 时必填"
                        "（没有依据不得声称现稿已覆盖）"
                    )
                target = item.get("target")
                if target is not None:
                    if not isinstance(target, dict):
                        errors.append(f"{prefix}.target 必须是对象")
                    elif (
                        target.get("comment_id") is None
                        and not str(target.get("anchor_text") or "").strip()
                    ):
                        # 注意 `comment_id=0` 是合法值，不能用真值判断
                        errors.append(
                            f"{prefix}.target 须给出 comment_id 或 anchor_text 之一"
                        )

    if errors:
        raise ValueError("审查计划校验失败：\n- " + "\n- ".join(errors))


def enrich_plan(
    plan: dict[str, Any], *, edit_policy: str | None = None
) -> dict[str, Any]:
    result = deepcopy(plan)
    meta = get_plan_meta(result)
    policy = normalize_edit_policy(
        edit_policy or meta.get("edit_policy"), default="revise-first"
    )
    meta["edit_policy"] = policy
    result["meta"] = meta
    findings = get_findings(result)
    key = "findings" if "findings" in result or "risks" not in result else "risks"
    result[key] = enrich_findings(findings, edit_policy=policy)
    if key == "risks":
        result["findings"] = result.pop("risks")
    result.setdefault("schema_version", "2.0")
    _attach_directed_blocks(result)
    return result


# --------------------------------------------------------------------------- #
# Rule Studio 集成扩展（W6）
#
# 以下函数**只读**既有 plan 结构，不改变 `enrich_plan` / `validate_plan` 的行为：
# - 旧 plan 缺少 `meta.resolution_provenance` 时一律按"无客户旧流程"处理，
#   不猜测客户（INT-003）；
# - 新字段是可选的，缺失不报错（§14「plan_loader 新字段必须可选」）。
# --------------------------------------------------------------------------- #

#: 旧 plan 在缺少 provenance 时的默认客户选择状态。
DEFAULT_CLIENT_SELECTION: dict[str, Any] = {
    "client_profile_id": None,
    "client_policy_snapshot_id": None,
    "mode": "none",
}


def get_client_selection(plan: dict[str, Any]) -> dict[str, Any]:
    """读取本轮客户选择。缺失时返回"未选择"，**绝不猜测**。"""
    meta = get_plan_meta(plan)
    selection = meta.get("client_selection")
    if not isinstance(selection, dict):
        return dict(DEFAULT_CLIENT_SELECTION)
    return {
        "client_profile_id": selection.get("client_profile_id"),
        "client_policy_snapshot_id": selection.get("client_policy_snapshot_id"),
        "mode": selection.get("mode") or (
            "explicit" if selection.get("client_profile_id") else "none"
        ),
    }


def get_resolution_provenance(plan: dict[str, Any]) -> dict[str, Any]:
    """读取本轮解析溯源。缺失时返回空字典，不抛错（旧 plan 兼容）。"""
    meta = get_plan_meta(plan)
    provenance = meta.get("resolution_provenance")
    return dict(provenance) if isinstance(provenance, dict) else {}


def has_resolution_provenance(plan: dict[str, Any]) -> bool:
    """新 plan 是否携带本轮溯源信息。"""
    return bool(get_resolution_provenance(plan))
