#!/usr/bin/env python3
"""审查报告渲染工具。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    skill_root = Path(__file__).resolve().parents[2]
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    from scripts.report.report_docx import write_review_report_docx
else:
    from .report_docx import write_review_report_docx

RISK_ORDER = {"P0": 0, "P1": 1, "P2": 2}
PENDING_MARKER_RE = re.compile(r"【待填\s*[:：]\s*([^】]+?)\s*】")

#: `coverage_level` → 报告里写给律师看的审查深度。
#: 取值来自 `select_active_assets.py`，**不得为了好看写高一级**（SKILL.md §1）。
COVERAGE_DEPTH_LABELS = {
    "domain_and_type": "三层（类型级）",
    "domain_only": "两层（域级）",
    "global_only": "一层（全局）",
}

#: 报告章节契约：与 `templates/review-report-template.md`、`SKILL.md` 一一对应。
#: 生成器按此**逐节自检**，缺一节即报错——避免再出现"文档要求了、实现没做"的静默缺口。
REPORT_SECTION_CONTRACT_PATH = Path(__file__).with_name("report-sections.json")
PENDING_KEYS = (
    "pending_items",
    "to_fill_items",
    "missing_information",
    "missing_fields",
    "待填事项",
)
TAX_SUGGESTION_KEYS = (
    "tax_suggestions",
    "tax_advice",
    "tax_recommendations",
    "tax_notes",
    "tax_suggestion",
    "tax_recommendation",
    "涉税建议",
)
TAX_SIGNAL_RE = re.compile(
    r"(?:\btax\b|涉税|税务|纳税|税费|税率|含税|不含税|价税|发票|开票|完税|代扣代缴|申报)",
    re.IGNORECASE,
)


def _normalize_risk_level(value: Any) -> str:
    text = str(value or "P2").upper().strip()
    if text in RISK_ORDER:
        return text
    if "高" in text:
        return "P0"
    if "中" in text:
        return "P1"
    return "P2"


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON 顶层必须是对象")
    return payload


def collect_findings(plan: dict[str, Any]) -> list[dict[str, Any]]:
    findings = plan.get("findings") or plan.get("risks") or []
    if not isinstance(findings, list):
        raise ValueError("findings 必须是数组")
    normalized = []
    for idx, item in enumerate(findings, start=1):
        if not isinstance(item, dict):
            continue
        current = dict(item)
        current.setdefault("id", f"R{idx:03d}")
        current["risk_level"] = _normalize_risk_level(current.get("risk_level"))
        normalized.append(current)
    normalized.sort(key=lambda x: (RISK_ORDER.get(x["risk_level"], 99), x["id"]))
    return normalized


def _safe_line(value: Any, fallback: str = "未提及/待补充") -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text
            continue
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def _to_text_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _walk_text_values(value: Any) -> list[str]:
    """Return every non-empty text leaf while preserving document order."""
    if isinstance(value, dict):
        texts: list[str] = []
        for child in value.values():
            texts.extend(_walk_text_values(child))
        return texts
    if isinstance(value, (list, tuple, set)):
        texts = []
        for child in value:
            texts.extend(_walk_text_values(child))
        return texts
    return _to_text_list(value)


def _append_unique(items: list[str], value: Any) -> None:
    text = _first_text(value).strip(" 。；;，,")
    if text and text not in items:
        items.append(text)


def _pending_labels(value: Any) -> list[str]:
    labels: list[str] = []
    for text in _walk_text_values(value):
        markers = PENDING_MARKER_RE.findall(text)
        if markers:
            for marker in markers:
                _append_unique(labels, marker)
        else:
            _append_unique(labels, text)
    return labels


def _collect_pending_items(
    plan: dict[str, Any],
    summary: dict[str, Any],
    meta: dict[str, Any],
    findings: list[dict[str, Any]],
) -> list[str]:
    """Collect only fill items, explicit lists and explicit placeholder markers."""
    labels: list[str] = []
    for container in (plan, summary, meta):
        for key in PENDING_KEYS:
            for label in _pending_labels(container.get(key)):
                _append_unique(labels, label)

    for finding in findings:
        for key in PENDING_KEYS:
            for label in _pending_labels(finding.get(key)):
                _append_unique(labels, label)
        if finding.get("pending_kind") == "fill":
            for value in (finding.get("unknown_facts"), finding.get("assumptions")):
                for label in _pending_labels(value):
                    _append_unique(labels, label)

    # Markers may also be embedded in replacement text, comments or summaries.
    for text in _walk_text_values(plan):
        for label in PENDING_MARKER_RE.findall(text):
            _append_unique(labels, label)
    return labels


def _is_tax_finding(item: dict[str, Any]) -> bool:
    explicit = item.get("report_bucket")
    if explicit in {"general", "mixed"}:
        return False
    if explicit == "tax":
        return True
    if any(item.get(key) for key in TAX_SUGGESTION_KEYS):
        return True
    signal_values = [
        item.get("category"),
        item.get("clause_group"),
        item.get("basis_type"),
        item.get("tags"),
        item.get("title"),
        item.get("risk"),
        item.get("description"),
    ]
    signal_text = " ".join(_walk_text_values(signal_values))
    return bool(TAX_SIGNAL_RE.search(signal_text))


def _is_tax_text(value: Any) -> bool:
    return bool(TAX_SIGNAL_RE.search(" ".join(_walk_text_values(value))))


def _as_tax_suggestion(value: Any) -> str:
    text = _first_text(value).strip(" 。；;，,")
    if not text:
        return ""
    if text.startswith(("建议", "可考虑", "宜")):
        return text
    return f"建议{text}"


def _collect_tax_suggestions(
    plan: dict[str, Any],
    summary: dict[str, Any],
    meta: dict[str, Any],
    findings: list[dict[str, Any]],
) -> list[str]:
    suggestions: list[str] = []
    for container in (plan, summary, meta):
        for key in TAX_SUGGESTION_KEYS:
            for text in _walk_text_values(container.get(key)):
                _append_unique(suggestions, _as_tax_suggestion(text))
    for text in _walk_text_values(summary.get("key_recommendations")):
        if _is_tax_text(text):
            _append_unique(suggestions, _as_tax_suggestion(text))

    for finding in findings:
        explicit_bucket = finding.get("report_bucket")
        if explicit_bucket == "general":
            continue
        if explicit_bucket not in {"tax", "mixed"} and not _is_tax_finding(finding):
            continue
        finding_suggestions: list[str] = []
        for key in TAX_SUGGESTION_KEYS:
            for text in _walk_text_values(finding.get(key)):
                _append_unique(finding_suggestions, _as_tax_suggestion(text))
        if not finding_suggestions and explicit_bucket != "mixed":
            _append_unique(
                finding_suggestions,
                _as_tax_suggestion(_resolve_review_direction(finding)),
            )
        title = _first_text(finding.get("title"), finding.get("risk"))
        for suggestion in finding_suggestions:
            rendered = f"{title}：{suggestion}" if title else suggestion
            _append_unique(suggestions, rendered)
    return suggestions


def _merge_report_meta(
    plan_meta: dict[str, Any],
    execution: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(plan_meta)
    if not isinstance(execution, dict):
        return merged
    review_context = execution.get("review_context")
    if isinstance(review_context, dict):
        for key in ("client_name", "party_role", "review_intensity"):
            if not merged.get(key) and review_context.get(key):
                merged[key] = review_context.get(key)
    reviewer_profile = execution.get("reviewer_profile")
    if not isinstance(reviewer_profile, dict):
        return merged
    if not merged.get("reviewer"):
        merged["reviewer"] = reviewer_profile.get("author")
    if not merged.get("reviewer_organization"):
        merged["reviewer_organization"] = reviewer_profile.get("organization")
    if not merged.get("reviewer_department"):
        merged["reviewer_department"] = reviewer_profile.get("department")
    return merged


def _resolve_meta_text(summary: dict[str, Any], meta: dict[str, Any], *keys: str) -> str:
    for key in keys:
        text = _first_text(summary.get(key), meta.get(key))
        if text:
            return text
    return ""


def _resolve_parties(summary: dict[str, Any], meta: dict[str, Any]) -> str:
    for container in (summary, meta):
        parties = container.get("parties")
        if isinstance(parties, dict):
            party_a = _first_text(
                parties.get("party_a"),
                parties.get("party_a_name"),
                parties.get("甲方"),
            )
            party_b = _first_text(
                parties.get("party_b"),
                parties.get("party_b_name"),
                parties.get("乙方"),
            )
            if party_a or party_b:
                parts = []
                if party_a:
                    parts.append(f"甲方：{party_a}")
                if party_b:
                    parts.append(f"乙方：{party_b}")
                return "；".join(parts)

        party_list = _to_text_list(parties)
        if party_list:
            return "；".join(party_list)

        party_a = _first_text(
            container.get("party_a"),
            container.get("party_a_name"),
            container.get("甲方"),
        )
        party_b = _first_text(
            container.get("party_b"),
            container.get("party_b_name"),
            container.get("乙方"),
        )
        if party_a or party_b:
            parts = []
            if party_a:
                parts.append(f"甲方：{party_a}")
            if party_b:
                parts.append(f"乙方：{party_b}")
            return "；".join(parts)

    return "未提及/待补充"


def _resolve_party_entities(summary: dict[str, Any], meta: dict[str, Any]) -> tuple[str, str]:
    for container in (summary, meta):
        parties = container.get("parties")
        if isinstance(parties, dict):
            party_a = _first_text(
                parties.get("party_a"),
                parties.get("party_a_name"),
                parties.get("甲方"),
            )
            party_b = _first_text(
                parties.get("party_b"),
                parties.get("party_b_name"),
                parties.get("乙方"),
            )
            if party_a or party_b:
                return party_a, party_b

        party_a = _first_text(
            container.get("party_a"),
            container.get("party_a_name"),
            container.get("甲方"),
        )
        party_b = _first_text(
            container.get("party_b"),
            container.get("party_b_name"),
            container.get("乙方"),
        )
        if party_a or party_b:
            return party_a, party_b

    return "", ""


def _resolve_my_party(summary: dict[str, Any], meta: dict[str, Any], party_role: str) -> str:
    party_a, party_b = _resolve_party_entities(summary, meta)
    role = str(party_role or "").strip().lower()
    if role in {"party_a", "甲方", "a"} and party_a:
        return party_a
    if role in {"party_b", "乙方", "b"} and party_b:
        return party_b
    return "未提及/待补充"


def _resolve_other_parties(summary: dict[str, Any], meta: dict[str, Any], party_role: str) -> str:
    party_a, party_b = _resolve_party_entities(summary, meta)
    role = str(party_role or "").strip().lower()
    if role in {"party_a", "甲方", "a"} and party_b:
        return party_b
    if role in {"party_b", "乙方", "b"} and party_a:
        return party_a
    parties = _resolve_parties(summary, meta)
    return parties if parties != "未提及/待补充" else "未提及/待补充"


def _resolve_structured_text(summary: dict[str, Any], meta: dict[str, Any], *keys: str) -> str:
    for container in (summary, meta):
        for key in keys:
            value = container.get(key)
            if isinstance(value, dict):
                parts = []
                for part_key, part_value in value.items():
                    text = _first_text(part_value)
                    if text:
                        parts.append(f"{part_key}：{text}")
                if parts:
                    return "；".join(parts)
            items = _to_text_list(value)
            if items:
                return "；".join(items)
            text = _first_text(value)
            if text:
                return text
    return ""


def _resolve_key_milestones(summary: dict[str, Any], meta: dict[str, Any]) -> list[str]:
    for key in ("key_milestones", "milestones", "timeline"):
        items = _to_text_list(summary.get(key))
        if items:
            return items
        items = _to_text_list(meta.get(key))
        if items:
            return items
    return []


def _resolve_business_overview(
    summary: dict[str, Any],
    meta: dict[str, Any],
    contract_name: str,
    contract_type: str,
    party_role: str,
) -> str:
    overview = _resolve_meta_text(
        summary,
        meta,
        "business_overview",
        "transaction_profile",
        "contract_summary",
        "overview",
        "business_model",
    )
    if overview:
        return overview

    parts: list[str] = []
    if contract_name != "未提及/待补充":
        parts.append(f"本次审查对象为《{contract_name}》")
    if contract_type != "未提及/待补充":
        parts.append(f"合同类型暂识别为{contract_type}")
    if party_role != "未提及/待补充":
        parts.append(f"当前按{party_role}立场进行审查")
    if not parts:
        return "未提及/待补充"
    return "，".join(parts) + "。"


def _resolve_transaction_content(
    summary: dict[str, Any],
    meta: dict[str, Any],
    contract_name: str,
    contract_type: str,
    party_role: str,
) -> str:
    content = _resolve_structured_text(
        summary,
        meta,
        "transaction_content",
        "deal_overview",
        "business_overview",
        "contract_summary",
        "overview",
        "business_model",
    )
    if content:
        return content
    return _resolve_business_overview(summary, meta, contract_name, contract_type, party_role)


def _resolve_price_overview(summary: dict[str, Any], meta: dict[str, Any]) -> str:
    amount = _resolve_meta_text(summary, meta, "contract_amount", "amount", "total_amount")
    payment = _resolve_structured_text(
        summary,
        meta,
        "payment_terms",
        "payment_arrangement",
        "price_terms",
        "pricing_terms",
    )
    parts = [item for item in (amount, payment) if item]
    if not parts:
        return "未提及/待补充"
    return "；".join(parts)


def _resolve_rights_obligations(summary: dict[str, Any], meta: dict[str, Any]) -> str:
    rights = _resolve_structured_text(
        summary,
        meta,
        "rights_obligations",
        "rights_obligations_summary",
        "core_rights_obligations",
        "rights_and_obligations",
        "obligations_overview",
    )
    return rights or "未提及/待补充"


def _resolve_legal_basis(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("legal_basis", "basis", "source_references", "sources"):
        value = item.get(key)
        values = _to_text_list(value)
        if not values:
            text = _first_text(value)
            values = [text] if text else []
        for text in values:
            if text and text not in parts:
                parts.append(text)
    return "；".join(parts) or "/"


def _resolve_review_direction(item: dict[str, Any]) -> str:
    return _first_text(
        item.get("suggestion"),
        item.get("fix"),
        item.get("comment"),
        item.get("rationale"),
        # 纯税务 finding 用 `tax_advice` 承载意见；此前不在候选键里，
        # 于是 `report_bucket=tax` 的条目会被完整性检查误判为"缺少审查意见"。
        item.get("tax_advice"),
        item.get("replacement_text"),
        item.get("recommended_text"),
        item.get("insert_text"),
    )


def _directed_block_applies(item: dict[str, Any]) -> bool:
    block = item.get("directed_block")
    if not isinstance(block, dict) or not bool(block.get("active")):
        return False
    action = str(item.get("action") or "auto").strip().lower().replace("_", "-")
    prohibited_actions = {
        str(value).strip().lower().replace("_", "-")
        for value in block.get("prohibited_actions", [])
        if str(value).strip()
    }
    output_kind = str(item.get("output_kind") or "").strip()
    prohibited_outputs = {
        str(value).strip() for value in block.get("prohibited_outputs", []) if str(value).strip()
    }
    if prohibited_actions and action in prohibited_actions:
        return True
    if output_kind and output_kind in prohibited_outputs:
        return True
    return not prohibited_actions and action in {"auto", "replace", "insert", "delete"}


def _report_completeness_errors(
    meta: dict[str, Any],
    findings: list[dict[str, Any]],
    plan: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not _first_text(meta.get("contract_name"), meta.get("title")):
        errors.append("缺少合同名称")
    if not _first_text(meta.get("party_role"), meta.get("role")):
        errors.append("缺少审查立场")
    provenance = meta.get("classification_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    if not _first_text(provenance.get("coverage_level")):
        errors.append(
            "缺少覆盖层级（meta.classification_provenance.coverage_level）——"
            "SKILL.md §1 要求写明本次审查深度"
        )
    if plan is not None and not isinstance(plan.get("linkage_checklist"), dict):
        errors.append(
            "缺少条款联动必检清单（linkage_checklist）——五组：付款交付验收／变更解除违约／"
            "保密数据知识产权／责任限制赔偿保险／到期退出交接，每组须登记 checked 或 not_applicable+理由"
        )
    for item in findings:
        finding_id = _safe_line(item.get("id"), fallback="未编号")
        if not _resolve_review_direction(item):
            errors.append(f"{finding_id} 缺少审查意见或可执行修改方向")
        if _resolve_legal_basis(item) == "/":
            errors.append(f"{finding_id} 缺少依据或来源状态")
    return errors


def _resolve_key_recommendations(
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
) -> list[str]:
    blocked_directions = {
        _resolve_review_direction(item)
        for item in findings
        if _directed_block_applies(item) and _resolve_review_direction(item)
    }
    recommendations = [
        item
        for item in _to_text_list(summary.get("key_recommendations"))
        if not _is_tax_text(item) and item not in blocked_directions
    ]
    if recommendations:
        return recommendations

    derived: list[str] = []
    for item in findings:
        if _directed_block_applies(item):
            continue
        suggestion = _resolve_review_direction(item)
        if suggestion and suggestion not in derived:
            derived.append(suggestion)
        if len(derived) >= 5:
            break
    return derived


def _resolve_overall_opinion(
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
    overall: str,
    conclusion: str,
) -> str:
    opinion = _resolve_meta_text(
        summary,
        {},
        "overall_opinion",
        "review_opinion",
        "opinion",
    )
    if opinion:
        return opinion

    focus_titles: list[str] = []
    for item in findings:
        if item.get("risk_level") not in {"P0", "P1"}:
            continue
        title = _safe_line(item.get("title") or item.get("risk"))
        if title not in focus_titles:
            focus_titles.append(title)
        if len(focus_titles) >= 3:
            break

    parts: list[str] = []
    if overall != "未提及/待补充":
        parts.append(f"当前总体风险等级为{overall}")
    if conclusion != "未提及/待补充":
        parts.append(f"审查结论为{conclusion.rstrip('。；; ')}")

    if not parts and not focus_titles:
        return "未提及/待补充"

    sentence = "，".join(parts)
    if sentence:
        sentence += "。"
    if focus_titles:
        sentence += f" 现阶段建议优先关注{'、'.join(focus_titles)}。"
    return sentence.strip()


def _resolve_recipient(my_party: str, other_parties: str) -> str:
    if my_party != "未提及/待补充":
        return my_party
    if other_parties != "未提及/待补充":
        return other_parties
    return "委托方"


def _resolve_opening_paragraph(
    *,
    contract_name: str,
    recipient: str,
    contract_type: str,
    party_role: str,
) -> str:
    role_text = party_role if party_role != "未提及/待补充" else "委托方"
    contract_text = f"《{contract_name}》" if contract_name != "未提及/待补充" else "相关合同文本"
    type_text = contract_type if contract_type != "未提及/待补充" else "合同"
    return (
        f"致：{recipient}\n\n"
        f"就 {recipient} 拟签署的{contract_text}，本次从 {role_text} 立场对该{type_text}进行合同审查。"
        "以下意见基于当前提供的合同文本及已识别信息形成，供签署、谈判和后续修订时参考。"
    )


def _resolve_high_risk_alerts(findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    for item in findings:
        if item.get("risk_level") not in {"P0", "P1"}:
            continue
        alerts.append(
            {
                "title": _safe_line(item.get("title") or item.get("risk")),
                "clause": _safe_line(item.get("clause") or item.get("clause_position")),
                "risk": _safe_line(item.get("risk") or item.get("description")),
                "suggestion": (
                    "该具体输出已定向阻断；仅保留合规核验、补正、保全和退出方向。"
                    if _directed_block_applies(item)
                    else _safe_line(_resolve_review_direction(item))
                ),
            }
        )
        if len(alerts) >= 5:
            break
    return alerts


def _execution_status_lines(
    execution: dict[str, Any] | None,
    report_errors: list[str] | None = None,
) -> list[str]:
    if not isinstance(execution, dict):
        return []
    results = execution.get("results")
    results = results if isinstance(results, list) else []
    failed_items = [
        item
        for item in results
        if isinstance(item, dict) and item.get("status") == "failed"
    ]
    directed_items = [
        item
        for item in results
        if isinstance(item, dict) and item.get("status") == "directed_blocked"
    ]
    quality = execution.get("quality_gate")
    quality = quality if isinstance(quality, dict) else {}
    quality_errors = quality.get("errors")
    quality_errors = (
        [str(e) for e in quality_errors] if isinstance(quality_errors, list) else []
    )
    # 对外审查意见书正常时不披露执行/质量门等技术状态；
    # 仅当存在未落文项目、质量门错误或报告未闭合时，给出简短警示与必要详情。
    structural_only = quality.get("delivery_level") == "structural_validation"
    if not failed_items and not directed_items and not quality_errors and not report_errors and not structural_only:
        return []
    lines = [""]
    if failed_items or quality_errors or report_errors:
        lines.append("> 提示：本次审查存在未完成事项，不得作为正式交付版本；请人工复核后再作处理。")
    if directed_items:
        lines.append("> 定向阻断：下列具体输出/动作已停止，其他不受影响的审查项已继续执行。")
        for item in directed_items:
            lines.append(
                f"> - {_safe_line(item.get('id'), fallback='未编号')}："
                f"{_safe_line(item.get('message'), fallback='已定向阻断')}"
            )
    if structural_only:
        lines.append("> 交付级别：当前仅为结构验证版，未取得完整渲染证据，不得冒充视觉终版。")
    if failed_items:
        lines.append("> 未完整落文项目：")
        for item in failed_items:
            lines.append(
                f"> - {_safe_line(item.get('id'), fallback='未编号')}："
                f"{_safe_line(item.get('message'), fallback='执行失败')}"
            )
    for error in quality_errors:
        lines.append(f"> - {_safe_line(error)}")
    if report_errors:
        lines.append("> 报告未闭合事项：")
        for error in report_errors:
            lines.append(f"> - {_safe_line(error)}")
    return lines


#: 法条引用抽取：`《法名》…第X条`。用于产出「待复核法条清单」。
CITATION_RE = re.compile(
    r"(《[^》]{2,60}》[^。；;，,、\n]{0,24}?第[〇零一二三四五六七八九十百千0-9]+条(?:之[〇零一二三四五六七八九十]+)?)"
)


def collect_legal_citations(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从全部 `legal_basis` 中抽取法条引用，产出「待复核法条清单」。

    本库条文在建库时经元典核验并随文标注了日期，但**那是冻结时点的结论**；
    引用会随法律修改而过时。离线的定位不变，这份清单让"要不要复核"
    成为使用方**可执行的选择**，而不是隐性假设。
    """
    collected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in findings:
        if not isinstance(item, dict):
            continue
        basis = _resolve_legal_basis(item)
        for citation in CITATION_RE.findall(basis):
            normalized = citation.strip()
            if normalized in seen:
                continue
            seen.add(normalized)
            collected.append(
                {
                    "citation": normalized,
                    "finding_id": item.get("id"),
                    "risk_level": item.get("risk_level"),
                    "legal_basis": basis,
                }
            )
    return collected


def _load_section_contract() -> dict[str, Any]:
    try:
        data = json.loads(REPORT_SECTION_CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _enforce_section_contract(report_text: str) -> list[str]:
    """按章节契约逐节自检，返回缺失项。缺节不得静默通过。"""
    contract = _load_section_contract()
    missing: list[str] = []
    for title in contract.get("required_sections", []):
        if f"## {title}" not in report_text:
            missing.append(str(title))
    for title in contract.get("required_subsections", []):
        if f"### {title}" not in report_text:
            missing.append(str(title))
    return missing


def _resolve_coverage_section(
    meta: dict[str, Any],
    summary: dict[str, Any],
    contract_type: str,
) -> list[str]:
    """「5. 审查依据与覆盖层级」——SKILL.md §1 要求的强制小节。

    数据源：`meta.classification_provenance`（分类三步与 `select_active_assets.py` 的产物）。
    取不到 `coverage_level` 时**如实写「未记录」**并由完整性检查报出，不得省略整节。
    写法是**中性事实说明**：不是风险提示，也不是免责声明。
    """
    provenance = meta.get("classification_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    level = _first_text(
        provenance.get("coverage_level"),
        summary.get("coverage_level"),
    )
    depth = COVERAGE_DEPTH_LABELS.get(level, "未记录")
    type_id = _first_text(
        provenance.get("primary_type_id"),
        meta.get("primary_type_id"),
        summary.get("primary_type_id"),
    )
    domain_code = _first_text(
        provenance.get("primary_domain_code"),
        summary.get("confirmed_domain_code"),
        summary.get("primary_domain_code"),
    )
    assets = _first_text(summary.get("coverage_assets"), provenance.get("coverage_assets"))
    stub_topics = _to_text_list(summary.get("stub_topics"))

    hit = contract_type
    suffix = f"（{type_id}）" if type_id else ""
    if domain_code:
        suffix += f"；主大类 {domain_code}"
    lines = [
        "### 5. 审查依据与覆盖层级",
        "",
        f"- 命中类型：{hit}{suffix}",
        f"- 本项目已审查深度：{depth}",
        f"- 生效资产：{_safe_line(assets)}",
    ]
    if stub_topics:
        lines.append(
            "- 本类型下暂无具体检查项的议题："
            + "、".join(_safe_line(topic) for topic in stub_topics)
        )
    else:
        lines.append("- 本类型下暂无具体检查项的议题：无")
    if level == "domain_only":
        lines.append(
            "- 说明：本次生效的是该大类在本域共通层面的审查目标与判断坐标；"
            "该类型特有的风险点可能未被覆盖。"
        )
    elif level == "global_only":
        lines.append("- 说明：本次仅有全局规则生效，未加载大类或类型级资产，审查深度受限。")
    lines.append("")
    return lines


def _resolve_source_comment_section(plan: dict, execution: dict | None) -> list[str]:
    """「源文档批注意见处理」：对方每条批注各自的下落。

    只在 **plan 里有 `responses`** 或**源文档存在悬空批注**时渲染。
    正文修订之外，这一节回答的是"对方提的意见，我们逐条怎么处理了"——
    此前这类信息只散落在批注与对话里，报告上看不到。
    """
    try:
        from scripts.review.comment_targets import RESPONSE_STANCES
    except ImportError:  # pragma: no cover - 包内运行时走相对导入
        from review.comment_targets import RESPONSE_STANCES

    responses = plan.get("responses")
    responses = responses if isinstance(responses, list) else []
    execution = execution if isinstance(execution, dict) else {}
    exec_by_id = {
        str(item.get("id")): item
        for item in (execution.get("responses") or [])
        if isinstance(item, dict)
    }
    orphans = execution.get("orphan_comments")
    orphans = orphans if isinstance(orphans, dict) else {}
    orphan_items = orphans.get("orphans") if isinstance(orphans.get("orphans"), list) else []

    if not responses and not orphan_items:
        return []

    lines = ["## 源文档批注意见处理", ""]
    if responses:
        lines.append(f"- 源文档批注意见共 {len(responses)} 条，逐条处理口径如下：")
        lines.append("")
        for index, item in enumerate(responses, start=1):
            if not isinstance(item, dict):
                continue
            stance = str(item.get("stance") or "")
            label = RESPONSE_STANCES.get(stance, stance or "未标注口径")
            executed = exec_by_id.get(str(item.get("id")), {})
            author = executed.get("source_author") or item.get("source_author") or "未标注作者"
            source_text = _first_text(item.get("source_text"), item.get("summary")) or ""
            title = f"{index}. 【{label}】{source_text or '源文档批注意见'}（{author}）"
            lines.append(title)
            evidence = _first_text(item.get("evidence"))
            if evidence:
                lines.append(f"  - 依据／落点：{evidence}")
            text = _first_text(item.get("text"))
            if text:
                lines.append(f"  - 回复：{text}")
            status = executed.get("status")
            if status == "failed":
                lines.append(f"  - 执行状态：未完成——{executed.get('message', '')}")
            elif status == "skipped":
                lines.append(f"  - 执行状态：{executed.get('message', '')}")
            lines.append("")
    if orphan_items:
        lines.append(
            f"- 源文档另有 {len(orphan_items)} 条批注在正文中没有任何锚点"
            "（Word 修订窗格不可见）。其内容如下，未随本次修订处理："
        )
        lines.append("")
        for index, item in enumerate(orphan_items, start=1):
            if not isinstance(item, dict):
                continue
            author = item.get("author") or "未标注作者"
            date = item.get("date") or ""
            text = _first_text(item.get("text")) or ""
            suffix = f"（{date}）" if date else ""
            lines.append(f"{index}. {text}——{author}{suffix}")
        lines.append("")
    return lines


def render_review_report(
    plan: dict[str, Any],
    execution: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> str:
    plan_meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
    meta = _merge_report_meta(plan_meta, execution)
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    findings = collect_findings(plan)
    non_tax_findings = [item for item in findings if not _is_tax_finding(item)]
    pending_items = _collect_pending_items(plan, summary, meta, findings)
    tax_suggestions = _collect_tax_suggestions(plan, summary, meta, findings)

    timestamp = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M")
    contract_name = _safe_line(meta.get("contract_name") or meta.get("title"))
    project_name = _safe_line(meta.get("project_name"))
    reviewer = _safe_line(meta.get("reviewer"))
    reviewer_organization = _safe_line(
        meta.get("reviewer_organization"), fallback="未设置"
    )
    reviewer_department = _first_text(meta.get("reviewer_department"))
    client_name = _safe_line(meta.get("client_name"))
    party_role = _safe_line(meta.get("party_role") or meta.get("role"))
    review_intensity = _safe_line(meta.get("review_intensity"))
    contract_type = _safe_line(
        _resolve_meta_text(summary, meta, "contract_type") or contract_name
    )
    contract_term = _safe_line(
        _resolve_meta_text(summary, meta, "contract_term", "term", "duration")
    )
    signing_date = _safe_line(
        _resolve_meta_text(summary, meta, "signing_date", "review_version", "version")
    )
    my_party = _resolve_my_party(summary, meta, party_role)
    other_parties = _resolve_other_parties(summary, meta, party_role)
    transaction_content = _resolve_transaction_content(
        summary=summary,
        meta=meta,
        contract_name=contract_name,
        contract_type=contract_type,
        party_role=party_role,
    )
    price_overview = _resolve_price_overview(summary, meta)
    rights_obligations = _resolve_rights_obligations(summary, meta)
    key_milestones = _resolve_key_milestones(summary, meta)
    derived_overall = findings[0]["risk_level"] if findings else ""
    overall = _safe_line(
        summary.get("overall_risk") or summary.get("risk_level") or derived_overall
    )
    derived_conclusion = (
        f"共识别 {len(findings)} 项需处理事项；应以修订稿、待确认事实和执行结果共同复核。"
        if findings
        else ""
    )
    conclusion = _safe_line(
        summary.get("core_conclusion") or summary.get("conclusion") or derived_conclusion
    )
    overall_opinion = _resolve_overall_opinion(
        summary=summary,
        findings=non_tax_findings,
        overall=overall,
        conclusion=conclusion,
    )
    key_recommendations = _resolve_key_recommendations(
        summary=summary,
        findings=non_tax_findings,
    )
    recipient = _resolve_recipient(my_party=my_party, other_parties=other_parties)
    opening_paragraph = _resolve_opening_paragraph(
        contract_name=contract_name,
        recipient=recipient,
        contract_type=contract_type,
        party_role=party_role,
    )
    high_risk_alerts = _resolve_high_risk_alerts(non_tax_findings)

    lines: list[str] = [
        f"# 关于《{contract_name}》的审查意见书",
        "",
        opening_paragraph,
        "",
        f"- 合同名称：{contract_name}",
        f"- 项目名称：{project_name}",
        f"- 客户名称：{client_name}",
        f"- 审查日期：{timestamp}",
        f"- 审查立场：{party_role}",
        f"- 审查口径：{review_intensity}",
        f"- 审查人：{reviewer}",
        f"- 所属机构/公司：{reviewer_organization}",
        *([f"- 所属部门：{reviewer_department}"] if reviewer_department else []),
        "",
        "## 一、合同概况",
        "",
        "### 1. 合同主体",
        "",
        f"- 我方主体：{my_party}",
        f"- 其他签约方：{other_parties}",
        f"- 合同类型：{contract_type}",
        "",
        "### 2. 交易内容",
        "",
        f"- 交易内容：{transaction_content}",
        f"- 合同期限：{contract_term}",
        f"- 签署时间/版本：{signing_date}",
    ]

    if key_milestones:
        lines.append("- 关键时间节点：")
        for milestone in key_milestones:
            lines.append(f"  - {_safe_line(milestone)}")
    else:
        lines.append("- 关键时间节点：未提及/待补充")

    lines.extend(
        [
            "",
            "### 3. 合同价款",
            "",
            f"- 价款安排：{price_overview}",
            "",
            "### 4. 核心权利义务",
            "",
            f"- 核心权利义务：{rights_obligations}",
            "",
        ]
    )

    lines.extend(_resolve_coverage_section(meta, summary, contract_type))

    lines.extend(
        [
            "## 二、综合审查意见",
            "",
            f"- 总体风险等级：{overall}",
            f"- 核心结论：{conclusion}",
            f"- 审查意见：{overall_opinion}",
        ]
    )

    if key_recommendations:
        lines.append("- 重点处理事项：")
        for recommendation in key_recommendations:
            lines.append(f"  - {_safe_line(recommendation)}")

    report_errors = _report_completeness_errors(meta, findings, plan)
    lines.extend(_execution_status_lines(execution, report_errors))

    lines.extend(["", "## 三、重要风险提示", ""])
    if high_risk_alerts:
        for index, alert in enumerate(high_risk_alerts, start=1):
            lines.append(f"### {index}. {alert['title']}")
            lines.append("")
            lines.append(f"- 条款位置：{alert['clause']}")
            lines.append(f"- 风险说明：{alert['risk']}")
            lines.append(f"- 修改方向：{alert['suggestion']}")
            lines.append("")
    else:
        lines.extend(["- 当前未识别出需单独前置提示的重要风险。", ""])

    lines.extend(["## 四、详细审查意见", ""])

    if not non_tax_findings:
        lines.extend(["- 未识别到需要提示的具体审查问题。", ""])
    else:
        for index, item in enumerate(non_tax_findings, start=1):
            title = _safe_line(item.get("title") or item.get("risk"))
            block = item.get("directed_block")
            is_directed_blocked = _directed_block_applies(item)
            review_comment = (
                "该具体输出已定向阻断；仅保留合规核验、补正、保全和退出方向。"
                if is_directed_blocked
                else _safe_line(_resolve_review_direction(item))
            )
            target_text = _first_text(item.get("target_text"), item.get("search"))
            revision_text = "" if is_directed_blocked else _first_text(
                item.get("replacement_text"), item.get("recommended_text"), item.get("insert_text")
            )
            lines.append(f"### {index}. {title}")
            lines.append("")
            lines.append(f"- 风险等级：{item['risk_level']}")
            lines.append(
                f"- 条款位置：{_safe_line(item.get('clause') or item.get('clause_position'))}"
            )
            lines.append(
                f"- 风险概述：{_safe_line(item.get('risk') or item.get('description'))}"
            )
            lines.append(f"- 审查意见：{review_comment}")
            if target_text:
                lines.append(f"- 原条款：{target_text}")
            if revision_text:
                lines.append(f"- 建议修改：{revision_text}")
            if is_directed_blocked:
                lines.append(f"- 定向阻断理由：{_safe_line(block.get('reason'))}")
                required_outputs = _to_text_list(block.get("required_outputs"))
                if required_outputs:
                    lines.append(f"- 允许/必要输出：{'；'.join(required_outputs)}")
            pending_kind = item.get("pending_kind")
            unknown_facts = _to_text_list(item.get("unknown_facts"))
            if pending_kind == "verify" and unknown_facts:
                lines.append(f"- 待核验事实：{'；'.join(unknown_facts)}")
            elif pending_kind == "authorization" and unknown_facts:
                lines.append(f"- 待授权事项：{'；'.join(unknown_facts)}")
            lines.append(f"- 法律依据：{_resolve_legal_basis(item)}")
            lines.append("")

    lines.extend(_resolve_source_comment_section(plan, execution))

    lines.extend(
        [
            "## 五、声明",
            "",
            "- 本意见书基于当前提供的合同文本、已识别事实和现行有效规则形成，仅供本次合同谈判、修订和签署决策时参考。",
            "- 如后续合同文本、项目事实、审批程序、对方主体信息或交易安排发生变化，本意见书内容应相应调整。",
            "- 本意见书不替代项目事实核查、主体资信核查、审批合规核查及专项法律意见。",
            "",
            "## 六、出具信息",
            "",
            f"- 审查人及机构：{reviewer} / {reviewer_organization}",
            *([f"- 所属部门：{reviewer_department}"] if reviewer_department else []),
            "",
        ]
    )

    lines.extend(["## 【待填事项汇总】", ""])
    if pending_items:
        for item in pending_items:
            lines.append(f"- 【待填：{item}】——请在签署或交付前核实并补齐。")
    else:
        lines.append("- 当前未识别需汇总的待填事项。")

    lines.extend(["", "## 【涉税建议】", ""])
    if tax_suggestions:
        for suggestion in tax_suggestions:
            lines.append(f"- {suggestion}")
    else:
        lines.append("- 本次审查未识别需单独汇总的涉税事项。")

    report_text = "\n".join(lines)
    missing_sections = _enforce_section_contract(report_text)
    if missing_sections:
        raise RuntimeError(
            "审查报告缺少契约要求的章节："
            + "、".join(missing_sections)
            + "（契约见 scripts/report/report-sections.json）"
        )
    return report_text


def main() -> None:
    parser = argparse.ArgumentParser(description="根据结构化审查计划生成 Markdown 审查意见书")
    parser.add_argument("--plan", required=True, help="审查计划 JSON 文件路径")
    parser.add_argument("--output", required=True, help="输出 Markdown 报告路径")
    parser.add_argument("--output-docx", help="可选，输出 Word 报告路径")
    parser.add_argument(
        "--execution",
        help="可选，执行日志 JSON 文件路径（用于补充本地审查人配置）",
    )
    args = parser.parse_args()

    plan = load_json(args.plan)
    execution = load_json(args.execution) if args.execution else None
    report = render_review_report(plan=plan, execution=execution)

    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"拒绝覆盖既有报告: {output_path}")
    if args.output_docx and Path(args.output_docx).exists():
        raise FileExistsError(f"拒绝覆盖既有 DOCX 报告: {args.output_docx}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    if args.output_docx:
        output_docx_path = Path(args.output_docx)
        output_docx_path.parent.mkdir(parents=True, exist_ok=True)
        meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
        write_review_report_docx(
            markdown_content=report,
            output_path=output_docx_path,
            title=str(meta.get("contract_name") or meta.get("title") or "合同审查报告"),
            author=str(meta.get("reviewer") or "合同审查助手"),
        )
    print(f"审查报告已生成: {output_path}")
    if args.output_docx:
        print(f"审查报告 DOCX 已生成: {output_docx_path}")


if __name__ == "__main__":
    main()
