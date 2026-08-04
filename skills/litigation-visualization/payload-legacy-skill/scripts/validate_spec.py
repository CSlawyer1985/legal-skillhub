#!/usr/bin/env python3
"""Validate a source-linked litigation-visualization JSON specification.

This validator checks schema, authorization gates, locator syntax, and whether
locators point back to a registered source ID. It does not determine whether a
statement is true, admissible, persuasive, or legally correct.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


FACT_STATUSES = {"confirmed", "disputed", "unknown"}
RECORD_TYPES = {"fact", "source_statement", "inference", "legal_rule"}
LIFECYCLES = {"current", "superseded", "not_applicable"}
WORKFLOW_STATUSES = {"ready", "research_draft", "hold"}
LAW_CHECK_STATUSES = {"not_required", "pending", "verified"}
REDACTION_STATUSES = {"not_required", "internal_minimized", "pending", "completed"}
RELEASE_FIELD_CATEGORIES = {
    "case_id",
    "labels",
    "facts",
    "legal_rules",
    "source_ids",
    "dates",
    "amounts",
    "relationships",
    "procedures",
    "spatial_data",
    "notes",
}
SOURCE_KINDS = {
    "evidence",
    "party_statement",
    "legal_authority",
    "decision",
    "context",
    "derived",
}
ALLOWED_SUPPORT_KINDS_BY_RECORD_TYPE = {
    "fact": {"evidence", "party_statement", "decision", "derived"},
    "source_statement": {"evidence", "party_statement", "decision", "derived"},
    "inference": {
        "evidence",
        "party_statement",
        "legal_authority",
        "decision",
        "derived",
    },
    "legal_rule": {"legal_authority", "decision"},
}
ADJUDICATION_STATUSES = {
    "not_adjudicated",
    "party_admission",
    "procedurally_disputed",
    "judicially_determined",
}
REQUIRED_TOP_LEVEL = {
    "case_id",
    "audience",
    "purpose",
    "source_cutoff",
    "workflow_status",
    "hold_control",
    "spatial_review",
    "source_ledger",
    "privacy_authorization",
    "legal_review",
    "nodes",
    "edges",
    "claims",
    "legend",
}
REQUIRED_SPATIAL_FIELDS = {
    "required",
    "diagram_kind",
    "measurement_method",
    "coordinate_system_or_scale",
    "direction_basis",
    "collected_at",
    "data_version",
    "occlusion",
    "measurement_error",
    "projection_distortion",
    "temporal_change",
    "viewpoint_bias",
    "modeling_assumptions",
}
REQUIRED_SOURCE_FIELDS = {
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
REQUIRED_PRIVACY_FIELDS = {
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
}
REQUIRED_LEGAL_FIELDS = {
    "required",
    "jurisdiction",
    "legal_rule_refs",
    "effective_at",
    "law_checked_at",
    "law_check_status",
    "reviewer",
}
REQUIRED_ITEM_FIELDS = {
    "id",
    "fact_status",
    "record_type",
    "lifecycle",
    "asserted_by",
    "verification_basis",
    "adjudication_status",
    "adjudication_refs",
    "support_refs",
    "conflict_refs",
    "context_refs",
    "gap_reason",
}
REF_RE = re.compile(
    r"(?P<source_id>[A-Za-z0-9][A-Za-z0-9._-]*)#(?:"
    r"p[1-9][0-9]*|"
    r"para-[1-9][0-9]*|"
    r"cell-[A-Za-z]{1,4}[1-9][0-9]*|"
    r"ts-(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r")"
)
SOURCE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
INLINE_ABS_RE = re.compile(
    r"(?:file://|[A-Za-z]:[\\/]|"
    r"(?:^|(?<![A-Za-z0-9:/]))/(?:Users|Volumes|Applications|Library|System|"
    r"opt|usr|bin|sbin|etc|var|tmp|private|home)(?:/|\b)|"
    r"(?:^|(?<![A-Za-z0-9:/]))/(?!/)[^/\s<>\"']+/[^\s<>\"']+|"
    r"(?:^|\s)~/|\\\\[^\s]+)"
)
ISO_DATE_RE = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])")
SOURCE_HASH_OR_VERSION_RE = re.compile(
    r"(?:sha256:[0-9a-f]{64}|version:[A-Za-z0-9][A-Za-z0-9._:+-]{0,199}|"
    r"unhashed-with-reason:.{3,200})"
)
LEGAL_TRIGGER_RE = re.compile(
    r"(?:procedure|procedural|deadline|limitation|statute|legal|law|jurisdiction|"
    r"appeal|remedy|程序|流程|期限|时效|法条|法律|法定条件|管辖|救济|上诉|"
    r"裁判规则)",
    re.IGNORECASE,
)
SPATIAL_TRIGGER_RE = re.compile(
    r"(?:spatial|site\s*plan|route|boundary|coordinate|空间|现场|路线|边界|"
    r"方位|平面|坐标|测绘)",
    re.IGNORECASE,
)
VAGUE_ASSERTORS = {
    "unknown",
    "unspecified",
    "n/a",
    "not_applicable",
    "未知",
    "不明",
    "未注明",
}


def text(value: object) -> str:
    """Return string values and safely collapse every other type to empty."""

    return value if isinstance(value, str) else ""


def nonempty_string(value: object) -> bool:
    return bool(text(value).strip())


def looks_absolute_path(value: str) -> bool:
    stripped = value.strip()
    return (
        stripped.startswith(("/", "~/", "file://", "\\\\"))
        or bool(WINDOWS_ABS_RE.match(stripped))
    )


def contains_absolute_path(value: str) -> bool:
    return looks_absolute_path(value) or bool(INLINE_ABS_RE.search(value))


def valid_iso_date(value: object) -> bool:
    candidate = text(value).strip()
    if not ISO_DATE_RE.fullmatch(candidate):
        return False
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def validate_string_list(
    value: object,
    context: str,
    errors: list[str],
    *,
    allow_empty: bool,
) -> list[str]:
    """Validate a JSON array of non-blank strings and return cleaned values."""

    if not isinstance(value, list):
        errors.append(f"{context} must be an array")
        return []
    if not value and not allow_empty:
        errors.append(f"{context} must contain at least one value")
    cleaned: list[str] = []
    for index, entry in enumerate(value):
        if not nonempty_string(entry):
            errors.append(f"{context}[{index}] must be a non-blank string")
            continue
        cleaned.append(text(entry).strip())
    return cleaned


def validate_source_ledger(
    value: object, errors: list[str], *, global_cutoff: object
) -> dict[str, str]:
    """Validate the source registry and return source ID to kind mappings."""

    if not isinstance(value, list):
        errors.append("source_ledger must be an array")
        return {}
    if not value:
        errors.append("source_ledger must register at least one source")
    source_registry: dict[str, str] = {}
    for index, entry in enumerate(value):
        context = f"source_ledger[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{context} must be an object")
            continue
        missing = sorted(REQUIRED_SOURCE_FIELDS - entry.keys())
        if missing:
            errors.append(f"{context} is missing fields: " + ", ".join(missing))
        for field in REQUIRED_SOURCE_FIELDS - {"authorized_use"}:
            if field in entry and not nonempty_string(entry.get(field)):
                errors.append(f"{context}.{field} must be non-empty")
        validate_string_list(
            entry.get("authorized_use"),
            f"{context}.authorized_use",
            errors,
            allow_empty=False,
        )
        source_id = text(entry.get("source_id")).strip()
        source_kind = text(entry.get("source_kind")).strip()
        source_hash_or_version = text(entry.get("source_hash_or_version")).strip()
        prefix = text(entry.get("locator_prefix")).strip()
        description = text(entry.get("description")).strip()
        if source_id and not SOURCE_ID_RE.fullmatch(source_id):
            errors.append(
                f"{context}.source_id must use letters, digits, dot, underscore, or hyphen"
            )
        if source_kind and source_kind not in SOURCE_KINDS:
            errors.append(
                f"{context}.source_kind must be one of {sorted(SOURCE_KINDS)}"
            )
        if source_hash_or_version and not SOURCE_HASH_OR_VERSION_RE.fullmatch(
            source_hash_or_version
        ):
            errors.append(
                f"{context}.source_hash_or_version must use sha256:<64 lowercase hex>, "
                "version:<portable-id>, or unhashed-with-reason:<reason>"
            )
        if entry.get("ingested_at") is not None and not valid_iso_date(
            entry.get("ingested_at")
        ):
            errors.append(f"{context}.ingested_at must use a real YYYY-MM-DD date")
        if entry.get("source_cutoff") is not None and not valid_iso_date(
            entry.get("source_cutoff")
        ):
            errors.append(f"{context}.source_cutoff must use a real YYYY-MM-DD date")
        elif valid_iso_date(global_cutoff) and text(entry.get("source_cutoff")) > text(
            global_cutoff
        ):
            errors.append(
                f"{context}.source_cutoff must not be later than top-level source_cutoff"
            )
        if source_id in source_registry:
            errors.append(f"duplicate source_id in source_ledger: {source_id!r}")
        elif source_id and SOURCE_ID_RE.fullmatch(source_id):
            source_registry[source_id] = source_kind
        if prefix and looks_absolute_path(prefix):
            errors.append(f"{context}.locator_prefix must not be an absolute path or file URI")
        if source_id and prefix and prefix != f"{source_id}#":
            errors.append(
                f"{context}.locator_prefix must equal {source_id + '#'!r}"
            )
        if description and contains_absolute_path(description):
            errors.append(
                f"{context}.description must not contain an absolute path or file URI"
            )
    return source_registry


def validate_ref(ref: object, context: str, source_ids: set[str], errors: list[str]) -> None:
    """Validate one source locator and its source-ledger back-link."""

    if not nonempty_string(ref):
        errors.append(f"{context} must be a non-blank locator")
        return
    locator = text(ref).strip()
    if looks_absolute_path(locator):
        errors.append(f"{context} must not contain an absolute path or file URI")
        return
    match = REF_RE.fullmatch(locator)
    if not match:
        errors.append(
            f"{context} has invalid locator format; expected "
            "SOURCE_ID#pN, #para-N, #cell-A1, or #ts-HH:MM:SS"
        )
        return
    source_id = match.group("source_id")
    if source_id not in source_ids:
        errors.append(
            f"{context} references unregistered source_id {source_id!r}"
        )


def validate_ref_list(
    value: object,
    context: str,
    source_ids: set[str],
    errors: list[str],
    *,
    required_nonempty: bool,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{context} must be an array")
        return []
    if required_nonempty and not value:
        errors.append(f"{context} must contain at least one locator")
    locators: list[str] = []
    for index, ref in enumerate(value):
        validate_ref(ref, f"{context}[{index}]", source_ids, errors)
        if nonempty_string(ref):
            locators.append(text(ref).strip())
    if len(locators) != len(set(locators)):
        errors.append(f"{context} must not contain duplicate locators")
    return locators


def validate_privacy(
    value: object, workflow_status: object, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append("privacy_authorization must be an object")
        return
    missing = sorted(REQUIRED_PRIVACY_FIELDS - value.keys())
    if missing:
        errors.append(
            "privacy_authorization is missing fields: " + ", ".join(missing)
        )

    for field in (
        "processing_location",
        "allowed_channel",
        "redaction_status",
        "retention_policy",
        "authorization_basis",
    ):
        if field in value and not nonempty_string(value.get(field)):
            errors.append(f"privacy_authorization.{field} must be non-empty")

    processors = validate_string_list(
        value.get("allowed_processors"),
        "privacy_authorization.allowed_processors",
        errors,
        allow_empty=False,
    )
    recipients = validate_string_list(
        value.get("allowed_recipients"),
        "privacy_authorization.allowed_recipients",
        errors,
        allow_empty=False,
    )
    field_allowlist = validate_string_list(
        value.get("field_allowlist"),
        "privacy_authorization.field_allowlist",
        errors,
        allow_empty=False,
    )
    unknown_release_fields = sorted(set(field_allowlist) - RELEASE_FIELD_CATEGORIES)
    if unknown_release_fields:
        errors.append(
            "privacy_authorization.field_allowlist contains unknown semantic "
            "categories: " + ", ".join(unknown_release_fields)
        )

    redaction_status = text(value.get("redaction_status")).strip()
    if redaction_status and redaction_status not in REDACTION_STATUSES:
        errors.append(
            "privacy_authorization.redaction_status must be one of "
            f"{sorted(REDACTION_STATUSES)}"
        )

    for field, entries in (
        ("allowed_processors", processors),
        ("allowed_recipients", recipients),
    ):
        for index, entry in enumerate(entries):
            if not entry.startswith(("internal:", "external:")):
                errors.append(
                    f"privacy_authorization.{field}[{index}] must start with "
                    "'internal:' or 'external:'"
                )

    approval = value.get("human_release_approved")
    if not isinstance(approval, bool):
        errors.append("privacy_authorization.human_release_approved must be boolean")
        approval = False
    release_by = value.get("human_release_by")
    release_at = value.get("human_release_at")
    if approval is True:
        if not nonempty_string(release_by) or text(release_by).strip().lower() in VAGUE_ASSERTORS:
            errors.append(
                "privacy_authorization.human_release_by must identify the approver "
                "when human_release_approved is true"
            )
        if not valid_iso_date(release_at):
            errors.append(
                "privacy_authorization.human_release_at must use a real YYYY-MM-DD "
                "date when human_release_approved is true"
            )
        if text(value.get("authorization_basis")).strip().lower() in VAGUE_ASSERTORS:
            errors.append(
                "privacy_authorization.authorization_basis must state a concrete basis "
                "when human_release_approved is true"
            )
    else:
        if release_by is not None or release_at is not None:
            errors.append(
                "privacy_authorization.human_release_by and human_release_at must be "
                "null when human_release_approved is false"
            )

    processing_location = text(value.get("processing_location")).strip()
    allowed_channel = text(value.get("allowed_channel")).strip()
    # Treat every non-internal party label as external. Invalid labels already
    # fail their format check; this conservative fallback also keeps the
    # authorization gate closed.
    has_external_party = any(
        not entry.startswith("internal:") for entry in processors + recipients
    )
    leaves_local_boundary = (
        processing_location != "local_only"
        or allowed_channel != "local_only"
        or has_external_party
    )
    if leaves_local_boundary and approval is False and workflow_status != "hold":
        errors.append(
            "workflow_status must be 'hold' when processing or delivery leaves the "
            "local boundary without human_release_approved"
        )
    if (
        leaves_local_boundary
        and approval is True
        and redaction_status not in {"completed", "not_required"}
        and workflow_status == "ready"
    ):
        errors.append(
            "workflow_status cannot be 'ready' for external processing or delivery "
            "unless privacy_authorization.redaction_status is completed or "
            "explicitly not_required"
        )


def metadata_requires_legal_review(data: dict[str, Any]) -> bool:
    """Conservatively detect legal/procedural visuals from user-facing metadata."""

    candidates: list[str] = []
    for field in ("purpose", "title", "visual_mode", "mode", "diagram_type"):
        value = data.get(field)
        if isinstance(value, str):
            candidates.append(value)
        elif isinstance(value, list):
            candidates.extend(text(entry) for entry in value)
    return bool(LEGAL_TRIGGER_RE.search(" ".join(candidates)))


def metadata_requires_spatial_review(data: dict[str, Any]) -> bool:
    candidates: list[str] = []
    for field in ("purpose", "title", "visual_mode", "mode", "diagram_type"):
        value = data.get(field)
        if isinstance(value, str):
            candidates.append(value)
        elif isinstance(value, list):
            candidates.extend(text(entry) for entry in value)
    return bool(SPATIAL_TRIGGER_RE.search(" ".join(candidates)))


def validate_spatial_review(
    value: object, *, required_by_metadata: bool, errors: list[str]
) -> None:
    if value is None:
        if required_by_metadata:
            errors.append(
                "spatial_review must be an object for spatial, site, route, boundary, "
                "or coordinate visuals"
            )
        return
    if not isinstance(value, dict):
        errors.append("spatial_review must be null or an object")
        return
    missing = sorted(REQUIRED_SPATIAL_FIELDS - value.keys())
    if missing:
        errors.append("spatial_review is missing fields: " + ", ".join(missing))
    required = value.get("required")
    if required is not True:
        errors.append("spatial_review.required must be true when the object is present")
    for field in REQUIRED_SPATIAL_FIELDS - {"required", "collected_at"}:
        if field in value and not nonempty_string(value.get(field)):
            errors.append(f"spatial_review.{field} must be non-empty")
    if not valid_iso_date(value.get("collected_at")):
        errors.append("spatial_review.collected_at must use a real YYYY-MM-DD date")
    if value.get("diagram_kind") not in {
        "not_to_scale_schematic",
        "to_scale",
        "coordinate_map",
    }:
        errors.append(
            "spatial_review.diagram_kind must be not_to_scale_schematic, to_scale, "
            "or coordinate_map"
        )


def validate_legal_review(
    value: object,
    *,
    workflow_status: object,
    source_registry: dict[str, str],
    requires_legal_review: bool,
    errors: list[str],
) -> set[str]:
    if not isinstance(value, dict):
        errors.append("legal_review must be an object")
        return set()
    missing = sorted(REQUIRED_LEGAL_FIELDS - value.keys())
    if missing:
        errors.append("legal_review is missing fields: " + ", ".join(missing))

    required = value.get("required")
    if not isinstance(required, bool):
        errors.append("legal_review.required must be boolean")
        required = False
    if requires_legal_review and required is not True:
        errors.append(
            "legal_review.required must be true for legal_rule records or procedural visuals"
        )

    for field in ("jurisdiction", "effective_at", "reviewer"):
        if field in value and not nonempty_string(value.get(field)):
            errors.append(f"legal_review.{field} must be non-empty")

    law_status = value.get("law_check_status")
    if law_status not in LAW_CHECK_STATUSES:
        errors.append(
            f"legal_review.law_check_status must be one of {sorted(LAW_CHECK_STATUSES)}"
        )

    refs_value = value.get("legal_rule_refs")
    effective_required = required is True or requires_legal_review
    require_refs = effective_required and law_status == "verified"
    legal_refs = validate_ref_list(
        refs_value,
        "legal_review.legal_rule_refs",
        set(source_registry),
        errors,
        required_nonempty=require_refs,
    )
    for index, locator in enumerate(legal_refs):
        match = REF_RE.fullmatch(locator)
        if not match:
            continue
        source_id = match.group("source_id")
        if source_registry.get(source_id) not in {"legal_authority", "decision"}:
            errors.append(
                f"legal_review.legal_rule_refs[{index}] must point to a source_ledger "
                "entry whose source_kind is 'legal_authority' or 'decision'"
            )

    checked_at = value.get("law_checked_at")
    if law_status == "verified" and not nonempty_string(checked_at):
        errors.append("legal_review.law_checked_at must be non-empty when verified")
    elif law_status == "verified" and not valid_iso_date(checked_at):
        errors.append(
            "legal_review.law_checked_at must use YYYY-MM-DD when verified"
        )
    if law_status == "verified":
        if not valid_iso_date(value.get("effective_at")):
            errors.append(
                "legal_review.effective_at must use a real YYYY-MM-DD date when verified"
            )
        for field in ("jurisdiction", "effective_at", "reviewer"):
            normalized = text(value.get(field)).strip().lower()
            if normalized in VAGUE_ASSERTORS:
                errors.append(
                    f"legal_review.{field} must identify the verified scope, not "
                    f"{value.get(field)!r}"
                )
    if required is True and law_status == "not_required":
        errors.append("required legal review cannot use law_check_status 'not_required'")
    if required is False and law_status != "not_required":
        errors.append(
            "legal_review.law_check_status must be 'not_required' when required is false"
        )
    if effective_required and law_status != "verified" and workflow_status == "ready":
        errors.append(
            "workflow_status cannot be 'ready' while required legal review is unverified; "
            "use 'research_draft' or 'hold'"
        )
    return set(legal_refs)


def validate_item(
    item: dict[str, Any],
    kind: str,
    item_id: str,
    source_registry: dict[str, str],
    errors: list[str],
) -> None:
    source_ids = set(source_registry)
    missing_fields = sorted(REQUIRED_ITEM_FIELDS - item.keys())
    if missing_fields:
        errors.append(
            f"{kind} {item_id!r}: missing required fields: "
            + ", ".join(missing_fields)
        )
    if "status" in item:
        errors.append(f"{kind} {item_id!r}: use fact_status, not legacy status")
    if "source_refs" in item:
        errors.append(f"{kind} {item_id!r}: use support_refs, not legacy source_refs")

    if not nonempty_string(item.get("label") or item.get("text")):
        errors.append(f"{kind} {item_id!r}: missing label/text")

    fact_status = item.get("fact_status")
    if fact_status not in FACT_STATUSES:
        errors.append(
            f"{kind} {item_id!r}: invalid fact_status {fact_status!r}; "
            "use confirmed, disputed, or unknown"
        )
    record_type = item.get("record_type")
    if record_type not in RECORD_TYPES:
        errors.append(f"{kind} {item_id!r}: invalid record_type {record_type!r}")
    lifecycle = item.get("lifecycle")
    if lifecycle not in LIFECYCLES:
        errors.append(f"{kind} {item_id!r}: invalid lifecycle {lifecycle!r}")
    if lifecycle in {"superseded", "not_applicable"} and not nonempty_string(
        item.get("lifecycle_reason")
    ):
        errors.append(
            f"{kind} {item_id!r}: {lifecycle} requires non-empty lifecycle_reason"
        )

    asserted_by = item.get("asserted_by")
    verification_basis = item.get("verification_basis")
    if not nonempty_string(asserted_by):
        errors.append(f"{kind} {item_id!r}: asserted_by must be non-empty")
    if not nonempty_string(verification_basis):
        errors.append(f"{kind} {item_id!r}: verification_basis must be non-empty")
    if record_type == "source_statement" and text(asserted_by).strip().lower() in VAGUE_ASSERTORS:
        errors.append(
            f"{kind} {item_id!r}: source_statement asserted_by must identify a speaker "
            "or source role, not a vague unknown value"
        )

    adjudication_status = item.get("adjudication_status")
    if adjudication_status not in ADJUDICATION_STATUSES:
        errors.append(
            f"{kind} {item_id!r}: invalid adjudication_status {adjudication_status!r}"
        )

    adjudication_refs = item.get("adjudication_refs", [])
    if adjudication_status in ADJUDICATION_STATUSES - {"not_adjudicated"}:
        validated_adjudication_refs = validate_ref_list(
            adjudication_refs,
            f"{kind} {item_id!r}.adjudication_refs",
            source_ids,
            errors,
            required_nonempty=True,
        )
        if adjudication_status == "judicially_determined":
            for index, locator in enumerate(validated_adjudication_refs):
                match = REF_RE.fullmatch(locator)
                if match and source_registry.get(match.group("source_id")) != "decision":
                    errors.append(
                        f"{kind} {item_id!r}.adjudication_refs[{index}] must point "
                        "to source_kind 'decision' for judicially_determined"
                    )
        elif adjudication_status in {"party_admission", "procedurally_disputed"}:
            for index, locator in enumerate(validated_adjudication_refs):
                match = REF_RE.fullmatch(locator)
                if match and source_registry.get(match.group("source_id")) not in {
                    "party_statement",
                    "evidence",
                    "decision",
                }:
                    errors.append(
                        f"{kind} {item_id!r}.adjudication_refs[{index}] for "
                        f"{adjudication_status} must point to source_kind "
                        "'party_statement', 'evidence', or 'decision'"
                    )
    elif adjudication_status == "not_adjudicated":
        if not isinstance(adjudication_refs, list):
            errors.append(
                f"{kind} {item_id!r}.adjudication_refs must be an array when present"
            )
        elif adjudication_refs:
            errors.append(
                f"{kind} {item_id!r}: not_adjudicated must not claim adjudication_refs"
            )
            for index, ref in enumerate(adjudication_refs):
                validate_ref(
                    ref,
                    f"{kind} {item_id!r}.adjudication_refs[{index}]",
                    source_ids,
                    errors,
                )

    if adjudication_status == "procedurally_disputed" and fact_status != "disputed":
        errors.append(
            f"{kind} {item_id!r}: procedurally_disputed requires fact_status 'disputed'"
        )

    support_value = item.get("support_refs", [])
    validated_support_refs: list[str] = []
    if fact_status in {"confirmed", "disputed"}:
        validated_support_refs = validate_ref_list(
            support_value,
            f"{kind} {item_id!r}.support_refs",
            source_ids,
            errors,
            required_nonempty=True,
        )
        support_kinds: list[str] = []
        for index, locator in enumerate(validated_support_refs):
            match = REF_RE.fullmatch(locator)
            if not match:
                continue
            source_kind = source_registry.get(match.group("source_id"), "")
            support_kinds.append(source_kind)
            if source_kind == "context":
                errors.append(
                    f"{kind} {item_id!r}.support_refs[{index}] points to source_kind "
                    "'context'; use context_refs instead"
                )
            allowed_support_kinds = ALLOWED_SUPPORT_KINDS_BY_RECORD_TYPE.get(
                text(record_type), set()
            )
            if source_kind and source_kind not in allowed_support_kinds:
                errors.append(
                    f"{kind} {item_id!r}.support_refs[{index}] for record_type "
                    f"{record_type!r} must point to one of "
                    f"{sorted(allowed_support_kinds)}"
                )
        if record_type == "fact" and support_kinds and set(support_kinds) == {
            "party_statement"
        }:
            errors.append(
                f"{kind} {item_id!r}: a fact supported only by party_statement sources "
                "must be modeled as source_statement or receive independent support"
            )
    elif fact_status == "unknown":
        if not isinstance(support_value, list):
            errors.append(f"{kind} {item_id!r}.support_refs must be an array when present")
        elif support_value:
            errors.append(
                f"{kind} {item_id!r}: unknown items must not have support_refs as proof"
            )
            for index, ref in enumerate(support_value):
                validate_ref(
                    ref,
                    f"{kind} {item_id!r}.support_refs[{index}]",
                    source_ids,
                    errors,
                )

    if "context_refs" in item:
        validate_ref_list(
            item.get("context_refs"),
            f"{kind} {item_id!r}.context_refs",
            source_ids,
            errors,
            required_nonempty=False,
        )

    conflict_value = item.get("conflict_refs", [])
    if fact_status == "disputed":
        validated_conflict_refs = validate_ref_list(
            conflict_value,
            f"{kind} {item_id!r}.conflict_refs",
            source_ids,
            errors,
            required_nonempty=True,
        )
        overlap = sorted(set(validated_support_refs) & set(validated_conflict_refs))
        if overlap:
            errors.append(
                f"{kind} {item_id!r}: support_refs and conflict_refs must be "
                "disjoint; overlapping locators: " + ", ".join(overlap)
            )
    elif fact_status == "confirmed":
        if not isinstance(conflict_value, list):
            errors.append(f"{kind} {item_id!r}.conflict_refs must be an array when present")
        elif conflict_value:
            errors.append(
                f"{kind} {item_id!r}: confirmed cannot coexist with conflict_refs; "
                "use disputed or resolve the conflict in a new version"
            )
            for index, ref in enumerate(conflict_value):
                validate_ref(
                    ref,
                    f"{kind} {item_id!r}.conflict_refs[{index}]",
                    source_ids,
                    errors,
                )
    elif fact_status == "unknown" and "conflict_refs" in item:
        validate_ref_list(
            conflict_value,
            f"{kind} {item_id!r}.conflict_refs",
            source_ids,
            errors,
            required_nonempty=False,
        )

    if fact_status == "unknown" and not nonempty_string(item.get("gap_reason")):
        errors.append(f"{kind} {item_id!r}: unknown requires non-empty gap_reason")
    elif "gap_reason" in item and not nonempty_string(item.get("gap_reason")):
        errors.append(f"{kind} {item_id!r}.gap_reason must be non-empty when present")


def validate_no_absolute_paths(value: object, context: str, errors: list[str]) -> None:
    """Reject local absolute paths or file URIs anywhere in a portable spec."""

    if isinstance(value, dict):
        for key, entry in value.items():
            validate_no_absolute_paths(entry, f"{context}.{key}", errors)
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            validate_no_absolute_paths(entry, f"{context}[{index}]", errors)
    elif isinstance(value, str) and contains_absolute_path(value):
        errors.append(f"{context} must not contain an absolute path or file URI")


def validate_hold_control(
    value: object, workflow_status: object, errors: list[str]
) -> None:
    """Require an actionable, bounded recovery record whenever the spec is on hold."""

    if workflow_status != "hold":
        if value is not None:
            errors.append("hold_control must be null unless workflow_status is 'hold'")
        return
    if not isinstance(value, dict):
        errors.append("hold_control must be an object when workflow_status is 'hold'")
        return
    required_fields = {"scope", "reason", "owner", "recovery_conditions"}
    missing = sorted(required_fields - value.keys())
    if missing:
        errors.append("hold_control is missing fields: " + ", ".join(missing))
    for field in ("scope", "reason", "owner"):
        if field in value and not nonempty_string(value.get(field)):
            errors.append(f"hold_control.{field} must be non-empty")
    validate_string_list(
        value.get("recovery_conditions"),
        "hold_control.recovery_conditions",
        errors,
        allow_empty=False,
    )


def validate(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["top-level value must be an object"]

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append("missing top-level fields: " + ", ".join(missing))

    for field in ("case_id", "audience", "purpose", "source_cutoff"):
        if field in data and not nonempty_string(data.get(field)):
            errors.append(f"{field} must be non-empty")
    if data.get("source_cutoff") is not None and not valid_iso_date(
        data.get("source_cutoff")
    ):
        errors.append("source_cutoff must use a real YYYY-MM-DD date")

    workflow_status = data.get("workflow_status")
    if workflow_status not in WORKFLOW_STATUSES:
        errors.append(
            f"workflow_status must be one of {sorted(WORKFLOW_STATUSES)}"
        )
    validate_hold_control(data.get("hold_control"), workflow_status, errors)
    validate_spatial_review(
        data.get("spatial_review"),
        required_by_metadata=metadata_requires_spatial_review(data),
        errors=errors,
    )

    source_registry = validate_source_ledger(
        data.get("source_ledger"), errors, global_cutoff=data.get("source_cutoff")
    )
    validate_privacy(data.get("privacy_authorization"), workflow_status, errors)
    validate_no_absolute_paths(data, "spec", errors)

    collection_values: dict[str, list[Any]] = {}
    for field in ("nodes", "edges", "claims"):
        value = data.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} must be an array")
            collection_values[field] = []
        else:
            collection_values[field] = value

    ids: set[str] = set()
    node_ids: set[str] = set()
    has_legal_rule = False
    legal_rule_support_refs: set[str] = set()
    for kind, field in (("node", "nodes"), ("edge", "edges"), ("claim", "claims")):
        for index, item in enumerate(collection_values[field]):
            if not isinstance(item, dict):
                errors.append(f"{kind}[{index}] must be an object")
                continue
            item_id = text(item.get("id")).strip()
            if not item_id:
                errors.append(f"{kind}[{index}] is missing id")
            elif not SOURCE_ID_RE.fullmatch(item_id):
                errors.append(
                    f"{kind}[{index}].id must use letters, digits, dot, underscore, "
                    "or hyphen"
                )
            elif item_id in ids:
                errors.append(f"duplicate id: {item_id}")
            else:
                ids.add(item_id)
                if kind == "node":
                    node_ids.add(item_id)
            if item.get("record_type") == "legal_rule":
                has_legal_rule = True
                refs = item.get("support_refs")
                if isinstance(refs, list):
                    legal_rule_support_refs.update(
                        text(ref).strip() for ref in refs if nonempty_string(ref)
                    )
            validate_item(item, kind, item_id, source_registry, errors)

    for edge in collection_values["edges"]:
        if not isinstance(edge, dict):
            continue
        edge_id = edge.get("id")
        for endpoint in ("from", "to"):
            value = text(edge.get(endpoint)).strip()
            if not value:
                errors.append(f"edge {edge_id!r}: missing {endpoint}")
            elif value not in node_ids:
                errors.append(f"edge {edge_id!r}: dangling {endpoint} node {value!r}")

    legend = data.get("legend")
    if not isinstance(legend, dict):
        errors.append("legend must be an object")
    else:
        keys = set(legend.keys())
        missing_legend = sorted(FACT_STATUSES - keys)
        extra_legend = sorted(keys - FACT_STATUSES)
        if missing_legend:
            errors.append("legend is missing semantics for: " + ", ".join(missing_legend))
        if extra_legend:
            errors.append(
                "legend may explain only confirmed, disputed, and unknown; extra keys: "
                + ", ".join(str(key) for key in extra_legend)
            )
        for status in FACT_STATUSES:
            if status in legend and not nonempty_string(legend.get(status)):
                errors.append(f"legend semantics for {status!r} must be non-empty")

    reviewed_legal_refs = validate_legal_review(
        data.get("legal_review"),
        workflow_status=workflow_status,
        source_registry=source_registry,
        requires_legal_review=has_legal_rule or metadata_requires_legal_review(data),
        errors=errors,
    )
    uncovered_legal_refs = sorted(legal_rule_support_refs - reviewed_legal_refs)
    if uncovered_legal_refs:
        errors.append(
            "legal_review.legal_rule_refs must cover every legal_rule support locator; "
            "missing: " + ", ".join(uncovered_legal_refs)
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"INVALID: {len(errors)} error(s)")
        return 1
    print(
        "VALID: structure, locator syntax, source-ledger back-links, and gate-field "
        "consistency passed; substantive truth, evidentiary weight, authorization "
        "authenticity, adjudicative effect, and legal correctness were not verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
