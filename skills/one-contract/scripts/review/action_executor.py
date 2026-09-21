#!/usr/bin/env python3
"""Execute review actions from explicit evidence and decision states."""

from __future__ import annotations

from typing import Any

try:
    from ..docx_engine.reviewer import ContractReviewer
except ImportError:
    from scripts.docx_engine.reviewer import ContractReviewer


DEFAULT_TAG_BY_ACTION = {
    "comment": "w:p",
    "delete": "w:r",
    "insert": "w:p",
    "replace": "w:r",
}
ACTION_ALIASES = {
    "comment": "comment",
    "批注": "comment",
    "注释": "comment",
    "report-only": "report-only",
    "report_only": "report-only",
    "仅报告": "report-only",
    "仅写入意见书": "report-only",
    "意见书": "report-only",
    "delete": "delete",
    "删除": "delete",
    "insert": "insert",
    "插入": "insert",
    "新增": "insert",
    "replace": "replace",
    "修订": "replace",
    "修改": "replace",
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
SUPPORTED_ACTIONS = {
    "comment",
    "report-only",
    "delete",
    "insert",
    "replace",
    "none",
    "skip",
    "auto",
}
EDIT_POLICIES = {"comment-first", "balanced", "revise-first"}
DIRECT_EDIT_ACTIONS = {"delete", "insert", "replace"}


def normalize_action(action: Any, default: str = "comment") -> str:
    raw = str(action or "").strip()
    if not raw:
        return default
    return ACTION_ALIASES.get(raw.lower()) or ACTION_ALIASES.get(raw) or raw.lower()


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


def normalize_evidence_state(finding: dict[str, Any]) -> str:
    raw = str(finding.get("evidence_state") or finding.get("decision_state") or "").strip()
    if raw:
        state = EVIDENCE_ALIASES.get(raw.lower()) or EVIDENCE_ALIASES.get(raw)
        if not state:
            raise ValueError(f"不支持的 evidence_state: {raw}")
        return state
    if _is_truthy(finding.get("not_applicable")):
        return "not_applicable"
    if any(
        _is_truthy(finding.get(key))
        for key in ("requires_authorization", "needs_negotiation", "requires_negotiation", "needs_confirmation")
    ):
        return "major_choice"
    if finding.get("unknown_facts") or finding.get("assumptions"):
        return "reasonable_assumption"
    return "confirmed"


def resolve_replacement_text(
    finding: dict[str, Any], *, edit_policy: str = "revise-first"
) -> str | None:
    replacement_text = finding.get("replacement_text")
    if replacement_text is not None:
        return str(replacement_text)
    if normalize_edit_policy(edit_policy) != "comment-first":
        recommended_text = str(finding.get("recommended_text") or "").strip()
        return recommended_text or None
    return None


def infer_revision_action(
    finding: dict[str, Any], *, strict: bool = False, edit_policy: str = "revise-first"
) -> str:
    explicit = normalize_action(
        finding.get("edit_type")
        or finding.get("preferred_action")
        or finding.get("suggested_action"),
        default="",
    )
    if explicit in DIRECT_EDIT_ACTIONS:
        return explicit
    if _is_truthy(finding.get("delete")) or _is_truthy(finding.get("remove")):
        return "delete"
    if finding.get("insert_text") is not None:
        return "insert"
    replacement = resolve_replacement_text(finding, edit_policy=edit_policy)
    if replacement is not None:
        return "delete" if replacement == "" else "replace"
    if strict and explicit == "replace":
        raise ValueError("replace 缺少 replacement_text")
    return "comment"


def infer_auto_action(
    finding: dict[str, Any], *, edit_policy: str = "revise-first"
) -> str:
    state = normalize_evidence_state(finding)
    if state == "not_applicable":
        return "skip"
    if _is_truthy(finding.get("report_only")):
        return "report-only"
    if state == "major_choice" or normalize_edit_policy(edit_policy) == "comment-first":
        return "comment"
    return infer_revision_action(finding, edit_policy=edit_policy)


def resolve_delivery_action(
    finding: dict[str, Any], *, requested_action: str, action: str, edit_policy: str
) -> str:
    state = normalize_evidence_state(finding)
    if state == "not_applicable":
        return "skip"
    if state == "major_choice":
        return "report-only" if action == "report-only" else "comment"
    if action not in DIRECT_EDIT_ACTIONS:
        return action
    if _is_truthy(finding.get("requires_authorization")):
        return "comment"
    if finding.get("assertions_unverified") and not _is_truthy(
        finding.get("uses_placeholders_or_conditions")
    ):
        return "comment"
    return action


def resolve_directed_block(
    finding: dict[str, Any], *, action: str
) -> dict[str, Any] | None:
    """Return the scoped block when this exact finding/action is prohibited.

    A P0 elsewhere in the plan never stops unrelated findings.  The caller must
    either attach an explicit block to this finding or provide an exact
    output_kind match through plan_loader's trigger-result bridge.
    """
    block = finding.get("directed_block")
    if not isinstance(block, dict) or not _is_truthy(block.get("active")):
        return None
    prohibited_actions = {
        normalize_action(item, default="")
        for item in block.get("prohibited_actions", [])
        if str(item).strip()
    }
    prohibited_outputs = {
        str(item).strip() for item in block.get("prohibited_outputs", []) if str(item).strip()
    }
    output_kind = str(finding.get("output_kind") or "").strip()
    action_blocked = action in (prohibited_actions or DIRECT_EDIT_ACTIONS)
    output_blocked = bool(output_kind and output_kind in prohibited_outputs)
    if not (action_blocked or output_blocked):
        return None
    return {
        "reason": str(block.get("reason") or "该项动作已被定向阻断").strip(),
        "scope": "this_finding",
        "attempted_action": action,
        "output_kind": output_kind or None,
        "trigger_ids": list(block.get("trigger_ids") or []),
        "prohibited_outputs": list(block.get("prohibited_outputs") or []),
        "required_outputs": list(block.get("required_outputs") or []),
    }


def resolve_action_tag(finding: dict[str, Any], action: str) -> str:
    selector = finding.get("selector")
    if isinstance(selector, dict) and selector.get("tag"):
        return str(selector["tag"])
    return str(finding.get("tag") or DEFAULT_TAG_BY_ACTION.get(action, "w:p"))


def resolve_occurrence(finding: dict[str, Any]) -> int | None:
    selector = finding.get("selector")
    raw = selector.get("occurrence") if isinstance(selector, dict) else None
    if raw is None:
        raw = finding.get("occurrence")
    if raw is None:
        return None
    value = int(raw)
    if value < 1:
        raise ValueError("occurrence 必须从 1 开始")
    return value


def resolve_node(reviewer: ContractReviewer, finding: dict[str, Any], action: str):
    selector = finding.get("selector")
    occurrence = resolve_occurrence(finding)
    if isinstance(selector, dict):
        line_number = selector.get("line_number")
        if isinstance(line_number, list) and len(line_number) == 2:
            line_number = range(int(line_number[0]), int(line_number[1]) + 1)
        return reviewer.find_node(
            tag=resolve_action_tag(finding, action),
            attrs=selector.get("attrs") if isinstance(selector.get("attrs"), dict) else None,
            line_number=line_number,
            contains=str(selector["contains"]) if selector.get("contains") is not None else None,
            occurrence=occurrence,
        )
    target_text = finding.get("target_text") or finding.get("search")
    if not target_text:
        raise ValueError(f"action={action} 缺少 target_text 或 selector")
    return reviewer.find_text(
        str(target_text), tag=resolve_action_tag(finding, action), occurrence=occurrence
    )


def build_comment_text(finding: dict[str, Any]) -> str:
    lines = [
        f"【风险等级】{str(finding.get('risk_level') or 'P2').upper()}",
        f"【风险点】{str(finding.get('title') or finding.get('risk') or '风险提示').strip()}",
    ]
    clause = str(finding.get("clause") or finding.get("clause_position") or "").strip()
    if clause:
        lines.append(f"【条款位置】{clause}")
    lines.append(
        f"【说明】{str(finding.get('risk') or finding.get('description') or '未提及/待补充').strip()}"
    )
    lines.append(
        f"【修改建议】{str(finding.get('suggestion') or finding.get('fix') or '未提及/待补充').strip()}"
    )
    basis_value = (
        finding.get("legal_basis")
        or finding.get("basis")
        or finding.get("principle_basis")
        or ""
    )
    if isinstance(basis_value, list):
        basis = "；".join(str(item).strip() for item in basis_value if str(item).strip())
    else:
        basis = str(basis_value).strip()
    if basis:
        lines.append(f"【判断依据】{basis}")
    unknowns = finding.get("unknown_facts") or finding.get("assumptions")
    if unknowns:
        rendered = "；".join(map(str, unknowns)) if isinstance(unknowns, list) else str(unknowns)
        lines.append(f"【待确认/假设】{rendered}")
    recommended = str(finding.get("recommended_text") or "").strip()
    if recommended and recommended != str(finding.get("suggestion") or "").strip():
        lines.append(f"【建议措辞】{recommended}")
    return "\n".join(lines)


def resolve_revision_comment(
    finding: dict[str, Any], *, action: str, requested_action: str
) -> str | None:
    explicit = str(finding.get("comment") or "").strip()
    if explicit:
        return explicit
    if _is_truthy(finding.get("suppress_comment_on_revision")):
        return None
    if action not in DIRECT_EDIT_ACTIONS:
        return None
    state = normalize_evidence_state(finding)
    has_reason = bool(
        str(finding.get("risk") or finding.get("description") or "").strip()
        or str(
            finding.get("legal_basis")
            or finding.get("basis")
            or finding.get("principle_basis")
            or ""
        ).strip()
    )
    if state == "reasonable_assumption" or _is_truthy(finding.get("keep_comment_on_revision")):
        return build_comment_text(finding)
    if str(finding.get("risk_level") or "P2").upper() in {"P0", "P1"} and has_reason:
        return build_comment_text(finding)
    return None


def apply_finding(
    reviewer: ContractReviewer,
    finding: dict[str, Any],
    *,
    edit_policy: str = "revise-first",
) -> dict[str, Any]:
    policy = normalize_edit_policy(edit_policy)
    state = normalize_evidence_state(finding)
    requested_action = normalize_action(finding.get("action"), default="auto")
    action = (
        infer_auto_action(finding, edit_policy=policy)
        if requested_action == "auto"
        else requested_action
    )
    action = resolve_delivery_action(
        finding,
        requested_action=requested_action,
        action=action,
        edit_policy=policy,
    )
    if action not in SUPPORTED_ACTIONS:
        raise ValueError(f"不支持的 action: {requested_action}")

    result: dict[str, Any] = {
        "id": finding.get("id"),
        "evidence_state": state,
        "action": action,
        "requested_action": requested_action,
        "status": "skipped",
        "message": "",
    }
    directed_block = resolve_directed_block(finding, action=action)
    if directed_block is not None:
        result.update(
            status="directed_blocked",
            message=(
                "已仅阻断本 finding 的命中动作，其他审查项继续执行："
                f"{directed_block['reason']}"
            ),
            directed_block=directed_block,
        )
        return result
    if action in {"none", "skip"}:
        result["message"] = "不适用或按计划跳过"
        return result
    if action == "report-only":
        result["status"] = "report_only"
        result["message"] = "仅写入审查意见书，不写入 Word 正文"
        return result

    tag = resolve_action_tag(finding, action)
    if action == "comment":
        node = resolve_node(reviewer, finding, action)
        reviewer.add_comment(node, finding.get("comment") or build_comment_text(finding))
        result.update(status="applied", message="已添加批注")
        return result

    comment = resolve_revision_comment(
        finding, action=action, requested_action=requested_action
    )
    if action == "delete":
        target_text = finding.get("target_text") or finding.get("search")
        if target_text:
            changed = reviewer.delete_text(
                str(target_text), tag=tag, comment_text=comment, occurrence=resolve_occurrence(finding)
            )
        else:
            node = resolve_node(reviewer, finding, action)
            reviewer.suggest_deletion(node)
            if comment:
                reviewer.add_comment(node, comment)
            changed = {"fallback": None}
        result.update(status="applied", message="已形成真实删除修订")
    elif action == "insert":
        node = resolve_node(reviewer, finding, action)
        new_text = finding.get("replacement_text") or finding.get("insert_text")
        if not new_text:
            raise ValueError("insert 缺少 replacement_text/insert_text")
        inserted = reviewer.insert_text_after(node, str(new_text), as_paragraph=(tag == "w:p"))
        if comment and inserted:
            reviewer.add_comment(inserted[0], comment)
        changed = {"fallback": None}
        result.update(status="applied", message="已形成真实插入修订")
    elif action == "replace":
        target_text = finding.get("target_text") or finding.get("search")
        replacement = resolve_replacement_text(finding, edit_policy=policy)
        if replacement is None:
            raise ValueError("replace 缺少 replacement_text")
        if target_text:
            changed = reviewer.replace_text(
                str(target_text),
                str(replacement),
                tag=tag,
                comment_text=comment,
                occurrence=resolve_occurrence(finding),
            )
        else:
            node = resolve_node(reviewer, finding, action)
            changed = reviewer.replace_node(node, str(replacement), tag=tag, comment_text=comment)
        result.update(status="applied", message="已形成真实替换修订")
    else:
        raise ValueError(f"不支持的 action: {action}")

    fallback = changed.get("fallback") if isinstance(changed, dict) else None
    if fallback:
        result["locator_fallback"] = fallback
    if comment:
        result["message"] += "并附批注"
    return result
