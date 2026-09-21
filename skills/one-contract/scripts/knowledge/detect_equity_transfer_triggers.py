#!/usr/bin/env python3
"""Deterministic checks for equity-transfer structural risks.

The checker consumes structured facts. It does not infer tax evasion from keywords and
does not draft an alternative external-facing contract. Missing facts require human
confirmation, while a P0 match creates a directed block against prohibited outputs
instead of stopping compliant or fact-independent revision work.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import argparse
import json


SKILL_ROOT = Path(__file__).resolve().parents[2]
TRIGGER_CATALOG = SKILL_ROOT / "assets/knowledge_v2/trigger_catalog.json"


def _money(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _different_money(values: list[float], tolerance: float = 0.01) -> bool:
    return bool(values) and max(values) - min(values) > tolerance


def _load_catalog(path: Path = TRIGGER_CATALOG) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["trigger_id"]: item for item in payload.get("assets", [])}


def detect(facts: Mapping[str, Any], catalog: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    catalog = dict(catalog or _load_catalog())
    evidence: list[dict[str, Any]] = []
    matched: list[str] = []
    missing: list[str] = []

    documents = list(facts.get("documents") or [])
    live_documents = [item for item in documents if not item.get("superseded_transparently", False)]
    considerations = [
        amount for item in live_documents
        if (amount := _money(item.get("total_consideration"))) is not None
    ]
    external_only = [item.get("document_id", "unknown") for item in live_documents if item.get("external_use_only") is True]
    side_price = [item.get("document_id", "unknown") for item in live_documents if item.get("side_agreement_controls_actual_price") is True]
    declared = _money(facts.get("declared_consideration"))
    actual = _money(facts.get("actual_total_consideration"))
    price_mismatch = _different_money(considerations)
    flow_mismatch = declared is not None and actual is not None and abs(actual - declared) > 0.01
    if external_only or side_price or price_mismatch or flow_mismatch:
        matched.append("TRG-EQ-DUAL-DOCUMENT-PRICE")
        evidence.append(
            {
                "trigger_id": "TRG-EQ-DUAL-DOCUMENT-PRICE",
                "facts": {
                    "external_use_only_documents": external_only,
                    "side_agreement_controls_actual_price": side_price,
                    "non_superseded_document_considerations": considerations,
                    "declared_consideration": declared,
                    "actual_total_consideration": actual,
                },
            }
        )
    elif not documents or declared is None or actual is None:
        missing.append("全部交易文本及申报对价、实际总对价尚未完整核对")

    disguised = []
    for payment in facts.get("payments") or []:
        if (
            payment.get("linked_to_equity_transfer") is True
            and payment.get("label") not in {None, "", "equity_consideration", "股权转让款"}
            and payment.get("independent_commercial_substance") is False
        ):
            disguised.append(
                {
                    "payment_id": payment.get("payment_id", "unknown"),
                    "label": payment.get("label"),
                    "amount": _money(payment.get("amount")),
                }
            )
    if disguised:
        matched.append("TRG-EQ-DISGUISED-CONSIDERATION")
        evidence.append({"trigger_id": "TRG-EQ-DISGUISED-CONSIDERATION", "facts": disguised})

    capital = facts.get("capital_status")
    if not isinstance(capital, Mapping):
        missing.append("标的股权的认缴、实缴、期限及瑕疵状态尚未核对")
    else:
        capital_risks = {
            "overdue_unpaid": capital.get("overdue_unpaid") is True,
            "noncash_significantly_undervalued": capital.get("noncash_significantly_undervalued") is True,
            "withdrawal_evidence": capital.get("withdrawal_evidence") is True,
        }
        if any(capital_risks.values()):
            matched.append("TRG-EQ-CAPITAL-STATUS-RISK")
            evidence.append({"trigger_id": "TRG-EQ-CAPITAL-STATUS-RISK", "facts": capital_risks})

    preemption = facts.get("preemption")
    if not isinstance(preemption, Mapping):
        missing.append("是否为对外转让及优先购买权、章程程序尚未核对")
    elif preemption.get("external_transfer") is True:
        preemption_risks = {
            "notice_receipt_not_proved": preemption.get("notice_receipt_proved") is not True,
            "notice_terms_mismatch": preemption.get("notice_terms_match_final") is not True,
            "charter_procedure_unsatisfied": preemption.get("charter_procedure_satisfied") is not True,
        }
        if any(preemption_risks.values()):
            matched.append("TRG-EQ-PREEMPTION-MISMATCH")
            evidence.append({"trigger_id": "TRG-EQ-PREEMPTION-MISMATCH", "facts": preemption_risks})

    ordered_matches = [item for item in catalog if item in set(matched)]
    trigger_assets = [catalog[item] for item in ordered_matches]
    p0 = any(item.get("severity") == "P0" for item in trigger_assets)
    confirmation_required = bool(trigger_assets or missing)
    required_modules = sorted({module for item in trigger_assets for module in item.get("required_modules", [])})
    required_outputs = list(dict.fromkeys(output for item in trigger_assets for output in item.get("required_outputs", [])))
    prohibited_outputs = list(dict.fromkeys(output for item in trigger_assets for output in item.get("prohibited_outputs", [])))
    return {
        "type_id": "type-equity-transfer",
        "status": "directed_block_required" if p0 else ("human_confirmation_required" if confirmation_required else "no_structural_trigger_detected"),
        "candidate_only": False,
        "triggered": [
            {
                "trigger_id": item["trigger_id"],
                "name": item["name"],
                "severity": item["severity"],
                "auto_action": item["auto_action"],
            }
            for item in trigger_assets
        ],
        "evidence": evidence,
        "missing_evidence": missing,
        "required_modules": required_modules,
        "required_outputs": required_outputs,
        "prohibited_outputs": prohibited_outputs,
        "human_confirmation_required": confirmation_required,
        # Compatibility flag: unspecific automation remains closed when a P0 or
        # material gap exists. Callers may still use the explicit scoped flags.
        "automatic_revision_allowed": not p0 and not missing,
        "compliance_revision_allowed": True,
        "fact_independent_revision_allowed": True,
        "notice": "触发器实行定向阻断：禁止生成隐瞒真实对价、虚假用途或其他 prohibited_outputs；合规方向及不依赖缺失事实的修订可继续，并保留律师终审。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect equity-transfer structural-risk triggers.")
    parser.add_argument("--facts", type=Path, required=True, help="Structured transaction facts JSON")
    parser.add_argument("--trigger-catalog", type=Path, default=TRIGGER_CATALOG)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    facts = json.loads(args.facts.read_text(encoding="utf-8"))
    rendered = json.dumps(detect(facts, _load_catalog(args.trigger_catalog)), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
