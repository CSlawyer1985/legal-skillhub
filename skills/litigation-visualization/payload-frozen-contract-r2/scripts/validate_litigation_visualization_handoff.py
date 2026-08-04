#!/usr/bin/env python3
"""Fail-closed validator for the Gaotao litigation-visualization handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "litigation-visualization-handoff/1.0"
VALIDATE_SPEC_SHA256 = (
    "5b71446ea24710e8624875ae55cc568f5a257956457624769f4cc67b7b0b5f06"
)
VALIDATE_OUTPUT_SHA256 = (
    "84bd8acd9524d528f976877b21137653632e5b4e86501280d2b09ba92720d47a"
)
TOP_LEVEL_KEYS = {
    "schema_version",
    "handoff_id",
    "created_at",
    "upstream",
    "route",
    "validator_compatibility",
    "source_ledger",
    "privacy_authorization",
    "legal_review",
    "workflow_status",
    "hold_control",
    "gates",
    "write_back_allowed",
}
SOURCE_FIELDS = {
    "source_id",
    "source_kind",
    "source_hash_or_version",
    "custody_or_processing_location",
    "ingested_at",
    "source_cutoff",
    "authorized_use",
    "locator_prefix",
    "page_or_unit_locator_scheme",
    "ocr_or_derivation_note",
    "description",
}
SOURCE_KINDS = {
    "evidence",
    "party_statement",
    "legal_authority",
    "decision",
    "context",
    "derived",
}
FIELD_ALLOWLIST = {
    "case_id",
    "labels",
    "facts",
    "legal_rules",
    "source_ids",
    "dates",
    "amounts",
    "relationships",
    "procedures",
    "notes",
}
VIEW_ALLOWLIST = {
    "case_process_flow",
    "claim_evidence_matrix",
}
GATE_FIELDS = {
    "litigation_plan_frozen",
    "source_ledger_complete",
    "privacy_authorized",
    "semantic_spec_valid",
    "independent_semantic_review_pass",
    "render_allowed",
}
SHA256_RE = re.compile(r"[a-f0-9]{64}")
SOURCE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
INTERNAL_PARTY_RE = re.compile(r"internal:[A-Za-z0-9][A-Za-z0-9._-]*")
SOURCE_HASH_RE = re.compile(
    r"(?:sha256:[a-f0-9]{64}|"
    r"version:[A-Za-z0-9][A-Za-z0-9._:+-]{0,199}|"
    r"unhashed-with-reason:.{3,200})"
)
SOURCE_REF_RE = re.compile(
    r"(?P<source_id>[A-Za-z0-9][A-Za-z0-9._-]*)#(?:"
    r"p[1-9][0-9]*|"
    r"para-[1-9][0-9]*|"
    r"cell-[A-Za-z]{1,4}[1-9][0-9]*|"
    r"ts-(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r")"
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?:file://|[A-Za-z]:[\\/]|"
    r"(?:^|(?<![A-Za-z0-9:/]))/(?:Users|Volumes|Applications|Library|System|"
    r"opt|usr|bin|sbin|etc|var|tmp|private|home)(?:/|\b)|"
    r"(?:^|\s)~/|\\\\[^\s]+)"
)
LOCATOR_SCHEME = (
    "SOURCE_ID#pN | SOURCE_ID#para-N | SOURCE_ID#cell-A1 | "
    "SOURCE_ID#ts-HH:MM:SS"
)


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_real_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def is_real_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
        return True
    except ValueError:
        return False


def is_safe_relative_path(value: Any) -> bool:
    if not is_nonempty_string(value):
        return False
    text = value.strip()
    if "\\" in text or text.startswith(("/", "~")):
        return False
    if re.match(r"^[A-Za-z]:", text):
        return False
    return ".." not in PurePosixPath(text).parts


def add(errors: list[str], code: str, detail: str) -> None:
    errors.append(f"{code}: {detail}")


def validate_string_array(
    value: Any,
    *,
    code: str,
    field: str,
    errors: list[str],
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    if not isinstance(value, list) or not value:
        add(errors, code, f"{field} must be a non-empty array")
        return []
    valid: list[str] = []
    for index, item in enumerate(value):
        if not is_nonempty_string(item):
            add(errors, code, f"{field}[{index}] must be a non-blank string")
            continue
        text = item.strip()
        if pattern is not None and not pattern.fullmatch(text):
            add(errors, code, f"{field}[{index}] has an incompatible value")
            continue
        valid.append(text)
    if len(valid) != len(set(valid)):
        add(errors, code, f"{field} must not contain duplicates")
    return valid


def validate_skill_binding(value: Any, field: str, errors: list[str]) -> None:
    required = {
        "skill_id",
        "version",
        "skill_sha256",
        "manifest_or_contract_sha256",
    }
    if not isinstance(value, dict):
        add(errors, "SKILL_BINDING", f"{field} must be an object")
        return
    if set(value) != required:
        add(errors, "SKILL_BINDING", f"{field} must contain exactly {sorted(required)}")
    for key in ("skill_id", "version"):
        if not is_nonempty_string(value.get(key)):
            add(errors, "SKILL_BINDING", f"{field}.{key} must be non-empty")
    for key in ("skill_sha256", "manifest_or_contract_sha256"):
        if not isinstance(value.get(key), str) or not SHA256_RE.fullmatch(value[key]):
            add(errors, "SKILL_HASH", f"{field}.{key} must be lowercase SHA-256")


def validate_litigation_plan(value: Any, errors: list[str]) -> tuple[str, str]:
    if not isinstance(value, dict):
        add(errors, "L2_BINDING", "upstream.litigation_plan must be an object")
        return "", ""
    expected = {
        "artifact_id",
        "artifact_version",
        "artifact_sha256",
        "relative_path",
        "source_id",
        "source_cutoff",
        "locator_profile",
        "anchor_contract_version",
        "anchor_contract_sha256",
        "anchor_map_relative_path",
        "anchor_map_sha256",
        "filing_status",
    }
    if set(value) != expected:
        add(errors, "L2_BINDING", f"litigation_plan must contain exactly {sorted(expected)}")
    if value.get("artifact_id") != "L2-05":
        add(errors, "L2_ARTIFACT_ID", "artifact_id must be L2-05")
    if value.get("filing_status") != "internal_work_product":
        add(errors, "L2_FILING_STATUS", "filing_status must be internal_work_product")
    if value.get("locator_profile") != "l2-markdown-paragraph-table-v1":
        add(errors, "L2_LOCATOR_PROFILE", "unexpected L2 locator profile")
    if value.get("anchor_contract_version") != "l2-anchor-contract/1.0":
        add(errors, "L2_ANCHOR_CONTRACT", "unexpected anchor contract version")
    for field in ("artifact_sha256", "anchor_contract_sha256", "anchor_map_sha256"):
        item = value.get(field)
        if not isinstance(item, str) or not SHA256_RE.fullmatch(item):
            add(errors, "L2_HASH", f"{field} must be lowercase SHA-256")
    for field in ("relative_path", "anchor_map_relative_path"):
        if not is_safe_relative_path(value.get(field)):
            add(errors, "RELATIVE_PATH", f"litigation_plan.{field} must be portable and relative")
    source_id = value.get("source_id")
    if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
        add(errors, "L2_SOURCE_ID", "litigation_plan.source_id is invalid")
        source_id = ""
    if not is_real_date(value.get("source_cutoff")):
        add(errors, "DATE_FORMAT", "litigation_plan.source_cutoff must be YYYY-MM-DD")
    return source_id, str(value.get("artifact_sha256", ""))


def validate_route(value: Any, errors: list[str]) -> str:
    if not isinstance(value, dict):
        add(errors, "ROUTE", "route must be an object")
        return ""
    expected = {
        "downstream_skill",
        "output_profile",
        "capability_status",
        "trigger",
        "requested_views",
    }
    if set(value) != expected:
        add(errors, "ROUTE", f"route must contain exactly {sorted(expected)}")
    validate_skill_binding(value.get("downstream_skill"), "route.downstream_skill", errors)
    if value.get("output_profile") != "professional_service.litigation_visualization":
        add(errors, "OUTPUT_PROFILE", "unexpected output profile")
    capability = value.get("capability_status")
    if capability not in {"supported", "hold", "not_applicable"}:
        add(errors, "CAPABILITY_STATUS", "invalid capability status")
        capability = ""
    if value.get("trigger") not in {"on_request", "explicit_package_option"}:
        add(errors, "TRIGGER", "invalid trigger")
    views = validate_string_array(
        value.get("requested_views"),
        code="ROUTE_VIEW",
        field="route.requested_views",
        errors=errors,
    )
    unknown_views = sorted(set(views) - VIEW_ALLOWLIST)
    if unknown_views:
        add(errors, "ROUTE_VIEW", f"unsupported v1 views: {unknown_views}")
    return str(capability)


def validate_validator_compatibility(value: Any, errors: list[str]) -> None:
    expected = {
        "downstream_skill_id": "litigation-visualization-cn",
        "validate_spec_sha256": VALIDATE_SPEC_SHA256,
        "validate_output_sha256": VALIDATE_OUTPUT_SHA256,
        "privacy_contract": "local-only-internal-parties-v1",
        "source_ledger_contract": "downstream-source-ledger-11-fields-v1",
        "source_ref_contract": "downstream-source-ref-v1",
    }
    if not isinstance(value, dict):
        add(errors, "VALIDATOR_BINDING", "validator_compatibility must be an object")
        return
    if set(value) != set(expected):
        add(errors, "VALIDATOR_BINDING", "validator_compatibility fields drifted")
    for field, required_value in expected.items():
        if value.get(field) != required_value:
            add(
                errors,
                "VALIDATOR_DRIFT",
                f"validator_compatibility.{field} does not match the pinned contract",
            )


def validate_source_ledger(
    value: Any,
    *,
    expected_l2_source_id: str,
    expected_l2_sha256: str,
    errors: list[str],
) -> set[str]:
    if not isinstance(value, list) or not value:
        add(errors, "SOURCE_LEDGER", "source_ledger must be a non-empty array")
        return set()
    source_ids: set[str] = set()
    l2_binding_found = False
    for index, entry in enumerate(value):
        field = f"source_ledger[{index}]"
        if not isinstance(entry, dict):
            add(errors, "SOURCE_LEDGER", f"{field} must be an object")
            continue
        if set(entry) != SOURCE_FIELDS:
            add(errors, "SOURCE_LEDGER_FIELDS", f"{field} must contain all 11 canonical fields")
        source_id = entry.get("source_id")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            add(errors, "SOURCE_ID", f"{field}.source_id is invalid")
            continue
        if source_id in source_ids:
            add(errors, "SOURCE_ID", f"duplicate source_id {source_id}")
        source_ids.add(source_id)
        if entry.get("source_kind") not in SOURCE_KINDS:
            add(errors, "SOURCE_KIND", f"{field}.source_kind is invalid")
        source_hash = entry.get("source_hash_or_version")
        if not isinstance(source_hash, str) or not SOURCE_HASH_RE.fullmatch(source_hash):
            add(errors, "SOURCE_HASH_OR_VERSION", f"{field}.source_hash_or_version drifted")
        if entry.get("custody_or_processing_location") != "local_only":
            add(errors, "SOURCE_LOCATION", f"{field} must remain local_only")
        for date_field in ("ingested_at", "source_cutoff"):
            if not is_real_date(entry.get(date_field)):
                add(errors, "DATE_FORMAT", f"{field}.{date_field} must be YYYY-MM-DD")
        validate_string_array(
            entry.get("authorized_use"),
            code="SOURCE_AUTHORIZED_USE",
            field=f"{field}.authorized_use",
            errors=errors,
        )
        if entry.get("locator_prefix") != f"{source_id}#":
            add(errors, "LOCATOR_PREFIX", f"{field}.locator_prefix must equal {source_id}#")
        if entry.get("page_or_unit_locator_scheme") != LOCATOR_SCHEME:
            add(errors, "LOCATOR_SCHEME", f"{field} uses an incompatible locator scheme")
        for text_field in ("ocr_or_derivation_note", "description"):
            if not is_nonempty_string(entry.get(text_field)):
                add(errors, "SOURCE_LEDGER_FIELDS", f"{field}.{text_field} must be non-empty")
        if (
            source_id == expected_l2_source_id
            and source_hash == f"sha256:{expected_l2_sha256}"
        ):
            l2_binding_found = True
    if expected_l2_source_id and not l2_binding_found:
        add(errors, "L2_LEDGER_BINDING", "source_ledger does not bind the declared L2 hash")
    return source_ids


def validate_privacy(value: Any, workflow_status: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        add(errors, "PRIVACY", "privacy_authorization must be an object")
        return
    required = {
        "processing_location",
        "allowed_processors",
        "allowed_recipients",
        "allowed_channel",
        "field_allowlist",
        "redaction_status",
        "retention_policy",
        "human_release_approved",
        "human_release_by",
        "human_release_at",
        "authorization_basis",
        "external_processing_authorized",
        "external_delivery_authorized",
    }
    if set(value) != required:
        add(errors, "PRIVACY_FIELDS", "privacy_authorization fields drifted")
    if value.get("processing_location") != "local_only":
        add(errors, "PRIVACY_PROCESSING_LOCATION", "processing_location must be local_only")
    if value.get("allowed_channel") != "local_only":
        add(errors, "PRIVACY_CHANNEL", "allowed_channel must be local_only")
    validate_string_array(
        value.get("allowed_processors"),
        code="PRIVACY_PROCESSORS",
        field="privacy_authorization.allowed_processors",
        errors=errors,
        pattern=INTERNAL_PARTY_RE,
    )
    validate_string_array(
        value.get("allowed_recipients"),
        code="PRIVACY_RECIPIENTS",
        field="privacy_authorization.allowed_recipients",
        errors=errors,
        pattern=INTERNAL_PARTY_RE,
    )
    fields = validate_string_array(
        value.get("field_allowlist"),
        code="PRIVACY_FIELD_ALLOWLIST",
        field="privacy_authorization.field_allowlist",
        errors=errors,
    )
    unknown_fields = sorted(set(fields) - FIELD_ALLOWLIST)
    if unknown_fields:
        add(errors, "PRIVACY_FIELD_ALLOWLIST", f"unsupported fields: {unknown_fields}")
    if value.get("redaction_status") not in {
        "not_required",
        "internal_minimized",
        "pending",
        "completed",
    }:
        add(errors, "PRIVACY_REDACTION_STATUS", "invalid redaction status")
    for field in ("retention_policy", "authorization_basis"):
        if not is_nonempty_string(value.get(field)):
            add(errors, "PRIVACY_FIELDS", f"privacy_authorization.{field} must be non-empty")
    approved = value.get("human_release_approved")
    if not isinstance(approved, bool):
        add(errors, "HUMAN_RELEASE", "human_release_approved must be boolean")
    elif approved:
        if not INTERNAL_PARTY_RE.fullmatch(str(value.get("human_release_by", ""))):
            add(errors, "HUMAN_RELEASE", "human_release_by must identify an internal approver")
        if not is_real_date(value.get("human_release_at")):
            add(errors, "HUMAN_RELEASE", "human_release_at must be YYYY-MM-DD")
    elif value.get("human_release_by") is not None or value.get("human_release_at") is not None:
        add(errors, "HUMAN_RELEASE", "unapproved release fields must be null")
    if value.get("external_processing_authorized") is not False:
        add(errors, "EXTERNAL_BOUNDARY", "external processing is forbidden in v1")
    if value.get("external_delivery_authorized") is not False:
        add(errors, "EXTERNAL_BOUNDARY", "external delivery is forbidden in v1")
    if workflow_status != "hold" and value.get("redaction_status") == "pending":
        add(errors, "PRIVACY_HOLD", "pending redaction requires workflow_status=hold")


def validate_legal_review(value: Any, source_ids: set[str], errors: list[str]) -> None:
    required = {
        "required",
        "jurisdiction",
        "effective_at",
        "law_checked_at",
        "law_check_status",
        "reviewer",
        "legal_rule_refs",
    }
    if not isinstance(value, dict):
        add(errors, "LEGAL_REVIEW", "legal_review must be an object")
        return
    if set(value) != required:
        add(errors, "LEGAL_REVIEW", "legal_review fields drifted")
    if not isinstance(value.get("required"), bool):
        add(errors, "LEGAL_REVIEW", "legal_review.required must be boolean")
    if not is_nonempty_string(value.get("jurisdiction")):
        add(errors, "LEGAL_REVIEW", "legal_review.jurisdiction must be non-empty")
    if not is_nonempty_string(value.get("effective_at")):
        add(errors, "LEGAL_REVIEW", "legal_review.effective_at must be non-empty")
    checked_at = value.get("law_checked_at")
    if checked_at is not None and not is_real_date(checked_at):
        add(errors, "DATE_FORMAT", "legal_review.law_checked_at must be YYYY-MM-DD or null")
    if value.get("law_check_status") not in {"not_required", "pending", "verified"}:
        add(errors, "LEGAL_REVIEW", "invalid law_check_status")
    if not is_nonempty_string(value.get("reviewer")):
        add(errors, "LEGAL_REVIEW", "legal_review.reviewer must be non-empty")
    refs = value.get("legal_rule_refs")
    if not isinstance(refs, list):
        add(errors, "LEGAL_REFS", "legal_rule_refs must be an array")
        return
    for index, ref in enumerate(refs):
        if not isinstance(ref, str) or not SOURCE_REF_RE.fullmatch(ref):
            add(errors, "LEGAL_REFS", f"legal_rule_refs[{index}] has invalid locator syntax")
            continue
        source_id = ref.split("#", 1)[0]
        if source_id not in source_ids:
            add(errors, "LEGAL_REFS", f"legal_rule_refs[{index}] uses an unregistered source")


def validate_hold_and_gates(
    workflow_status: Any,
    hold_control: Any,
    capability_status: str,
    gates: Any,
    errors: list[str],
) -> None:
    if workflow_status not in {"ready", "research_draft", "hold"}:
        add(errors, "WORKFLOW_STATUS", "invalid workflow_status")
    if workflow_status == "hold":
        required = {"scope", "reason", "owner", "recovery_conditions"}
        if not isinstance(hold_control, dict) or set(hold_control) != required:
            add(errors, "HOLD_CONTROL", "hold workflow requires complete hold_control")
        elif not isinstance(hold_control.get("recovery_conditions"), list) or not hold_control[
            "recovery_conditions"
        ]:
            add(errors, "HOLD_CONTROL", "recovery_conditions must be non-empty")
    elif hold_control is not None:
        add(errors, "HOLD_CONTROL", "non-hold workflow requires hold_control=null")
    if not isinstance(gates, dict) or set(gates) != GATE_FIELDS:
        add(errors, "GATES", f"gates must contain exactly {sorted(GATE_FIELDS)}")
        return
    for field in GATE_FIELDS:
        if not isinstance(gates.get(field), bool):
            add(errors, "GATES", f"gates.{field} must be boolean")
    render_allowed = gates.get("render_allowed")
    if capability_status != "supported" and render_allowed is not False:
        add(errors, "CAPABILITY_HOLD", "non-supported capability must not render")
    if render_allowed is True:
        for field in GATE_FIELDS - {"render_allowed"}:
            if gates.get(field) is not True:
                add(errors, "RENDER_GATE", f"render_allowed requires gates.{field}=true")


def walk_strings(value: Any, prefix: str = "$") -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if isinstance(value, str):
        items.append((prefix, value))
    elif isinstance(value, dict):
        for key, item in value.items():
            items.extend(walk_strings(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            items.extend(walk_strings(item, f"{prefix}[{index}]"))
    return items


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_bound_file(
    path: Path | None,
    expected_sha256: Any,
    label: str,
    errors: list[str],
) -> None:
    if path is None:
        return
    try:
        actual = file_sha256(path)
    except OSError as exc:
        add(errors, "BOUND_FILE_READ", f"{label}: {exc}")
        return
    if actual != expected_sha256:
        add(
            errors,
            "BOUND_FILE_HASH",
            f"{label} hash mismatch: expected {expected_sha256}, got {actual}",
        )


def validate_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["TOP_LEVEL: handoff must be an object"]
    if set(data) != TOP_LEVEL_KEYS:
        add(errors, "TOP_LEVEL", f"handoff must contain exactly {sorted(TOP_LEVEL_KEYS)}")
    if data.get("schema_version") != SCHEMA_VERSION:
        add(errors, "SCHEMA_VERSION", f"schema_version must be {SCHEMA_VERSION}")
    if not is_nonempty_string(data.get("handoff_id")):
        add(errors, "HANDOFF_ID", "handoff_id must be non-empty")
    if not is_real_datetime(data.get("created_at")):
        add(errors, "DATE_TIME_FORMAT", "created_at must be an ISO 8601 date-time")

    upstream = data.get("upstream")
    if not isinstance(upstream, dict) or set(upstream) != {
        "gaotao_skill",
        "case_skill",
        "litigation_plan",
    }:
        add(errors, "UPSTREAM", "upstream fields drifted")
        upstream = {}
    validate_skill_binding(upstream.get("gaotao_skill"), "upstream.gaotao_skill", errors)
    validate_skill_binding(upstream.get("case_skill"), "upstream.case_skill", errors)
    l2_source_id, l2_sha256 = validate_litigation_plan(
        upstream.get("litigation_plan"), errors
    )

    capability_status = validate_route(data.get("route"), errors)
    validate_validator_compatibility(data.get("validator_compatibility"), errors)
    source_ids = validate_source_ledger(
        data.get("source_ledger"),
        expected_l2_source_id=l2_source_id,
        expected_l2_sha256=l2_sha256,
        errors=errors,
    )
    validate_privacy(data.get("privacy_authorization"), data.get("workflow_status"), errors)
    validate_legal_review(data.get("legal_review"), source_ids, errors)
    validate_hold_and_gates(
        data.get("workflow_status"),
        data.get("hold_control"),
        capability_status,
        data.get("gates"),
        errors,
    )
    if data.get("write_back_allowed") is not False:
        add(errors, "WRITE_BACK", "write_back_allowed must remain false")
    for field, text in walk_strings(data):
        if ABSOLUTE_PATH_RE.search(text):
            add(errors, "ABSOLUTE_PATH", f"{field} contains an absolute path or file URI")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--litigation-plan", type=Path)
    parser.add_argument("--anchor-contract", type=Path)
    parser.add_argument("--anchor-map", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.handoff.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID\nREAD_ERROR: {exc}")
        return 1
    errors = validate_data(data)
    litigation_plan = data.get("upstream", {}).get("litigation_plan", {})
    validate_bound_file(
        args.litigation_plan,
        litigation_plan.get("artifact_sha256"),
        "litigation_plan",
        errors,
    )
    validate_bound_file(
        args.anchor_contract,
        litigation_plan.get("anchor_contract_sha256"),
        "anchor_contract",
        errors,
    )
    validate_bound_file(
        args.anchor_map,
        litigation_plan.get("anchor_map_sha256"),
        "anchor_map",
        errors,
    )
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
