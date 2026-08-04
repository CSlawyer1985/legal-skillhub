#!/usr/bin/env python3
"""Route privacy-safe sales-contract litigation intake signals."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

EXPECTED_SCOPE = "sales-contract-filing-and-preparation"
ADJACENT_SCOPES = {
    "financing-lease-contract-filing-and-preparation": "financial-lease-litigation",
    "construction-contract-filing-and-preparation": "construction-contract-litigation",
    "loan-contract-filing-and-preparation": "loan-contract",
    "guarantee-contract-filing-and-preparation": "guarantee-dispute",
    "sales-contract-enforcement": "enforcement-procedure",
}


def route(signals: dict[str, Any]) -> dict[str, Any]:
    scope = signals.get("scope")
    if scope != EXPECTED_SCOPE or signals.get("execution_document_requested"):
        adjacent = ADJACENT_SCOPES.get(scope, "legal-matter-intake")
        if signals.get("execution_document_requested"):
            adjacent = "enforcement-procedure"
        return {
            "trigger": False,
            "adjacent_skill": adjacent,
            "reason": "out-of-scope",
            "holds": [],
            "l1_gate": "NOT-APPLICABLE",
            "allowed_outputs": [],
        }

    holds: list[str] = []
    tags: list[str] = []

    if signals.get("competing_cause_signals_present"):
        primary = "mixed-cause-boundary"
        holds.append("HOLD-ROUTE")
    elif signals.get("installment_terms_verified") or signals.get("title_retention_verified"):
        primary = "installment-title-retention"
    elif signals.get("sale_agreement_verified"):
        primary = "ordinary-goods-sale"
    else:
        primary = "HOLD-ROUTE"
        holds.append("HOLD-ROUTE")

    if signals.get("reconciliation_verified"):
        tags.append("reconciliation-confirmation")
    if signals.get("quality_or_quantity_dispute_present"):
        tags.append("quality-quantity-defense")
        if not signals.get("quality_evidence_reviewed"):
            holds.append("HOLD-DEFENSE-EVIDENCE")
    if signals.get("guarantee_or_security_present"):
        tags.append("guarantee-security")
        if not signals.get("guarantee_scope_verified"):
            holds.append("HOLD-GUARANTEE")
    if signals.get("party_name_contains_lease_word"):
        tags.append("party-name-misroute-warning")

    if not signals.get("materials_readable"):
        holds.append("HOLD-READABILITY")
    if not signals.get("provenance_verified"):
        holds.append("HOLD-PROVENANCE")
    if not signals.get("delivery_or_acceptance_verified") or not signals.get("price_or_payment_schedule_verified"):
        holds.append("HOLD-EVIDENCE")
    if not signals.get("p0_3_consistency_verified"):
        holds.append("HOLD-CONSISTENCY")

    mode = signals.get("mode")
    if mode == "production-intake":
        if (
            not signals.get("prior_proceeding_reviewed")
            or signals.get("has_prior_final_disposition")
            or signals.get("duplicate_action_risk")
        ):
            holds.append("HOLD-PRIOR-PROCEEDING")
        if not signals.get("jurisdiction_connected"):
            holds.append("HOLD-JURISDICTION")
    elif mode == "retrospective-benchmark":
        if not signals.get("cutoff_primary_verified") or not signals.get("input_allowlist_frozen"):
            holds.append("HOLD-CUTOFF")
        if not signals.get("answer_key_isolated"):
            holds.append("HOLD-ANSWER-KEY")
        if signals.get("post_cutoff_material_in_input"):
            holds.append("HOLD-POST-CUTOFF")
    else:
        holds.append("HOLD-MODE")

    if not signals.get("court_profile_frozen"):
        holds.append("HOLD-COURT-PROFILE")
    if not signals.get("legal_source_temporally_verified"):
        holds.append("HOLD-LEGAL")
    if signals.get("sensitive_data_in_public_output"):
        holds.append("HOLD-PRIVACY")
    if signals.get("guaranteed_outcome_requested"):
        holds.append("HOLD-MISUSE")

    formal_cross_requested = signals.get("formal_cross_requested") or signals.get("request") == "formal-cross"
    if formal_cross_requested and not signals.get("opponent_evidence_received"):
        holds.append("HOLD-FORMAL-CROSS")
        formal_cross_status = "DISABLED-NO-OPPONENT-EVIDENCE"
    elif formal_cross_requested:
        formal_cross_status = "ELIGIBLE-CONDITIONAL-REVIEW"
    else:
        formal_cross_status = "NOT-REQUESTED"

    unique_holds = sorted(set(holds))
    if "HOLD-PRIVACY" in unique_holds:
        allowed_outputs = ["PRIVACY-DISPOSITION-RECORD"]
    elif unique_holds:
        allowed_outputs = ["EVIDENCE-GAP-LIST"]
        if "HOLD-FORMAL-CROSS" in unique_holds:
            allowed_outputs.append("CROSS-EXAMINATION-PLAN")
    else:
        allowed_outputs = ["SSOT", "L1-DRAFT-CANDIDATE", "L2-DRAFT-CANDIDATE", "CROSS-EXAMINATION-PLAN"]

    return {
        "trigger": True,
        "primary_route": primary,
        "secondary_tags": sorted(set(tags)),
        "holds": unique_holds,
        "l1_gate": "HOLD" if unique_holds else "ELIGIBLE-FOR-DRAFT-CANDIDATE",
        "formal_cross_status": formal_cross_status,
        "allowed_outputs": allowed_outputs,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: route_case.py INPUT.json", file=sys.stderr)
        return 2
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    signals = dict(payload.get("signals", payload))
    signals.setdefault("scope", payload.get("scope"))
    signals.setdefault("mode", payload.get("mode"))
    print(json.dumps(route(signals), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
