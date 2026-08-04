#!/usr/bin/env python3
"""Deterministic decision-quality gates for PatSeek evidence records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def sample_complete(pool: dict) -> bool:
    total = int(pool.get("total") or 0)
    sample_size = int(pool.get("sample_size") or 0)
    # A zero response can be an over-narrow query, an unsupported field, or an
    # index/language mismatch. It is not a completely reviewed candidate pool.
    return total > 0 and sample_size >= (total if total < 30 else 30)


def international_reasons(record: dict) -> list[str]:
    """Return extra evidence failures for an explicitly world-market branch."""
    if record.get("market") != "world":
        return []
    reasons = []
    if record.get("country_prefix_rate") != 1.0:
        reasons.append("country_prefix_unverified")
    if record.get("preflight_validated") is not True:
        reasons.append("world_preflight_unvalidated")
    return reasons


def route_comparison(routes: list[dict]) -> dict:
    rejected = []
    for route in routes:
        reasons = []
        if route.get("truncated") or int(route.get("total") or 0) >= 10000:
            reasons.append("truncated")
        if not sample_complete(route):
            reasons.append("sample_incomplete")
        if not route.get("precision_accepted", False):
            reasons.append("precision_not_accepted")
        reasons.extend(international_reasons(route))
        if reasons:
            rejected.append({"id": route.get("id"), "reasons": reasons})
    return {
        "status": "comparable" if routes and not rejected else "not_comparable",
        "rejected_routes": rejected,
        "allow_quantitative_ranking": bool(routes) and not rejected,
    }


def opportunity(channels: list[dict], counterexamples: list[dict], boundary_stable: bool) -> dict:
    if counterexamples:
        return {
            "status": "contradicted",
            "allowed_label": "已有反例，不得称空白",
            "counterexamples": counterexamples,
        }
    problems = []
    for channel in channels:
        if channel.get("truncated") or int(channel.get("total") or 0) >= 10000:
            problems.append({"id": channel.get("id"), "reason": "truncated"})
        elif not sample_complete(channel):
            problems.append({"id": channel.get("id"), "reason": "sample_incomplete"})
        elif not channel.get("precision_accepted", False):
            problems.append({"id": channel.get("id"), "reason": "precision_not_accepted"})
        for reason in international_reasons(channel):
            problems.append({"id": channel.get("id"), "reason": reason})
    if not boundary_stable:
        problems.append({"id": "boundary", "reason": "not_stable"})
    return {
        "status": "unverified" if problems or not channels else "low_density_hypothesis",
        "allowed_label": "当前证据不足以判断密度" if problems or not channels else "所列范围内的低密度假设",
        "problems": problems,
    }


def novelty(required_features: list[str], documents: list[dict]) -> dict:
    required = set(required_features)
    x_candidates = []
    for document in documents:
        if document.get("date_eligible") and required <= set(document.get("disclosed") or []):
            x_candidates.append(document.get("pid"))
    observed = set().union(*(set(document.get("disclosed") or []) for document in documents)) if documents else set()
    missing = sorted(required - observed)
    return {
        "status": "x_candidate_found" if x_candidates else "no_x_candidate_in_scope",
        "x_candidates": x_candidates,
        "missing_features": missing,
        "allow_novelty_guarantee": False,
        "drafting_action": "evidence_review" if x_candidates else "ask_inventor_and_run_qy_comp",
    }


def partner(team_records: list[dict]) -> dict:
    rows = []
    for team in team_records:
        families = {str(value) for value in team.get("relevant_family_ids") or [] if value}
        technical_lead = bool(families and team.get("applicant_verified"))
        rows.append({
            "id": team.get("id"),
            "status": "comparable_team_lead" if technical_lead and len(families) >= 2 else "contact_lead_only" if technical_lead else "unverified",
            "relevant_family_count": len(families),
            "partner_ready": bool(
                technical_lead
                and len(families) >= 2
                and team.get("current_team_verified")
                and team.get("ownership_verified")
                and team.get("maturity_verified")
                and team.get("cooperation_interest_verified")
            ),
        })
    return {"teams": rows, "allow_partner_ranking": bool(rows) and all(row["status"] == "comparable_team_lead" for row in rows)}


def fto(branches: list[dict]) -> dict:
    """Keep FTO output at candidate-screening level until external checks exist."""
    rows = []
    for branch in branches:
        reasons = []
        if not sample_complete(branch):
            reasons.append("sample_incomplete")
        reasons.extend(international_reasons(branch))
        if int(branch.get("claim_candidate_count") or 0) <= 0:
            reasons.append("no_claim_mapped_candidate")
        if branch.get("official_status_verified") is not True:
            reasons.append("official_status_unverified")
        rows.append({"id": branch.get("id"), "reasons": reasons})
    return {
        "status": "candidate_screening_only",
        "branches": rows,
        "allow_low_risk_conclusion": False,
        "required_next_step": "逐项权利要求映射、目标国官方状态和同族/继续申请核验",
    }


def evaluate(payload: dict) -> dict:
    kind = payload.get("kind")
    if kind == "route_comparison":
        return route_comparison(payload.get("routes") or [])
    if kind == "opportunity":
        return opportunity(payload.get("channels") or [], payload.get("counterexamples") or [], bool(payload.get("boundary_stable")))
    if kind == "novelty":
        return novelty(payload.get("required_features") or [], payload.get("documents") or [])
    if kind == "partner":
        return partner(payload.get("teams") or [])
    if kind == "fto":
        return fto(payload.get("branches") or [])
    raise ValueError("kind必须是route_comparison、opportunity、novelty、partner或fto")


def main() -> int:
    parser = argparse.ArgumentParser(description="PatSeek决策输出质量闸门")
    parser.add_argument("evidence", type=Path, help="结构化证据JSON")
    args = parser.parse_args()
    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
        print(json.dumps(evaluate(payload), ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
