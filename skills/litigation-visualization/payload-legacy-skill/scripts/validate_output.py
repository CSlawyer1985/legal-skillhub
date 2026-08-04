#!/usr/bin/env python3
"""Check that rendered artifacts account for a validated spec.

The render manifest is deliberately non-semantic: it may only say where a spec
element was rendered or why it was omitted. Fact status, source locators,
record type, and lifecycle remain inherited from the validated specification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from validate_spec import (
    contains_absolute_path,
    looks_absolute_path,
    nonempty_string,
    text,
    validate,
    validate_no_absolute_paths,
)


SHA256_RE = re.compile(r"[0-9a-f]{64}")
ABSOLUTE_CONTENT_PATTERNS = (
    re.compile(rb"file://", re.IGNORECASE),
    re.compile(
        rb"(?:^|(?<![A-Za-z0-9:/]))/(?:Users|Volumes|Applications|Library|System|"
        rb"opt|usr|bin|sbin|etc|var|tmp|private|home)(?:/|\b)",
        re.MULTILINE,
    ),
    re.compile(
        rb"(?:^|(?<![A-Za-z0-9:/]))/(?!/)[^/\x00\s<>\"]+/[^\x00\s<>\"]+",
        re.MULTILINE,
    ),
    re.compile(rb"[A-Za-z]:[\\/][^\x00\s<>\"]+"),
    re.compile(rb"(?:^|[\s\"'])~/[^\x00\s<>\"]+", re.MULTILINE),
    re.compile(rb"\\\\[A-Za-z0-9._-]+[\\/][^\x00\s<>\"]+"),
)
ALLOWED_TOP_LEVEL_FIELDS = {
    "spec_sha256",
    "released_fields",
    "artifacts",
    "elements",
}
ALLOWED_ARTIFACT_FIELDS = {"path", "sha256"}
RENDER_LOCATOR_RE = re.compile(
    r"(?:line|cell|page|slide|node|shape|table):[A-Za-z0-9][A-Za-z0-9._:!+-]*"
)
LINE_LOCATOR_RE = re.compile(r"line:([1-9][0-9]*)(?:-([1-9][0-9]*))?")
CELL_LOCATOR_RE = re.compile(r"cell:([A-Za-z]{1,4})([1-9][0-9]*)")
TOKEN_LOCATOR_RE = re.compile(r"(node|shape|table):([A-Za-z0-9][A-Za-z0-9._:+-]*)")
SLIDE_LOCATOR_RE = re.compile(r"slide:([1-9][0-9]*)")
OFFICE_SUFFIXES = {".docx", ".pptx", ".xlsx"}
TEXT_SUFFIXES = {".txt", ".md", ".mmd", ".csv", ".tsv", ".svg", ".xml"}
MAX_OFFICE_UNCOMPRESSED_BYTES = 50_000_000
MAX_OFFICE_MEMBERS = 10_000
MAX_ARTIFACT_BYTES = 50_000_000
PARENT_TRAVERSAL_CONTENT_RE = re.compile(
    rb"(?:^|[\s\"'`=(])\.\.[\\/][^\x00\s<>\"]+", re.MULTILINE
)
FORBIDDEN_ELEMENT_FIELDS = {
    "fact_status",
    "status",
    "support_refs",
    "source_refs",
    "context_refs",
    "conflict_refs",
    "record_type",
    "lifecycle",
    "lifecycle_reason",
    "adjudication_status",
    "adjudication_refs",
    "asserted_by",
    "verification_basis",
    "gap_reason",
}


def scan_bytes(content: bytes, label: str, errors: list[str]) -> None:
    if b"TODO_DO_NOT_DELIVER" in content:
        errors.append(f"{label} contains TODO_DO_NOT_DELIVER")
    for pattern in ABSOLUTE_CONTENT_PATTERNS:
        if pattern.search(content):
            errors.append(f"{label} contains an absolute path or file URI")
            break
    if PARENT_TRAVERSAL_CONTENT_RE.search(content):
        errors.append(f"{label} contains a parent-directory traversal reference")


def inspect_artifact(
    artifact_path: str,
    content: bytes,
    errors: list[str],
) -> dict[str, Any]:
    """Inspect text or Office content and return locator-verification material."""

    suffix = PurePosixPath(artifact_path).suffix.lower()
    info: dict[str, Any] = {"suffix": suffix, "text": None, "slides": {}}
    if suffix in OFFICE_SUFFIXES:
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile:
            errors.append(f"artifact {artifact_path!r} is not a valid Office ZIP container")
            return info
        if len(archive.infolist()) > MAX_OFFICE_MEMBERS:
            errors.append(
                f"artifact {artifact_path!r} has more than {MAX_OFFICE_MEMBERS} "
                "Office members"
            )
            archive.close()
            return info
        total_uncompressed = sum(member.file_size for member in archive.infolist())
        if total_uncompressed > MAX_OFFICE_UNCOMPRESSED_BYTES:
            errors.append(
                f"artifact {artifact_path!r} expands beyond the "
                f"{MAX_OFFICE_UNCOMPRESSED_BYTES}-byte inspection limit"
            )
            archive.close()
            return info
        text_parts: list[str] = []
        slides: dict[int, str] = {}
        with archive:
            for member in archive.infolist():
                member_name = member.filename
                pure = PurePosixPath(member_name)
                if (
                    pure.is_absolute()
                    or "\\" in member_name
                    or any(part in {"", ".", ".."} for part in pure.parts)
                ):
                    errors.append(
                        f"artifact {artifact_path!r} has unsafe Office member "
                        f"{member_name!r}"
                    )
                    continue
                if member.is_dir():
                    continue
                try:
                    member_content = archive.read(member)
                except (RuntimeError, OSError, zipfile.BadZipFile) as exc:
                    errors.append(
                        f"artifact {artifact_path!r} Office member {member_name!r} "
                        f"cannot be inspected: {exc}"
                    )
                    continue
                scan_bytes(
                    member_content,
                    f"artifact {artifact_path!r} member {member_name!r}",
                    errors,
                )
                if pure.suffix.lower() in {".xml", ".rels", ".txt", ".csv"}:
                    decoded = member_content.decode("utf-8", errors="replace")
                    text_parts.append(decoded)
                    slide_match = re.fullmatch(r"ppt/slides/slide([1-9][0-9]*)\.xml", member_name)
                    if slide_match:
                        slides[int(slide_match.group(1))] = decoded
        info["text"] = "\n".join(text_parts)
        info["slides"] = slides
        return info

    scan_bytes(content, f"artifact {artifact_path!r}", errors)
    if suffix in TEXT_SUFFIXES:
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"artifact {artifact_path!r} must be UTF-8 text")
            return info
        info["text"] = decoded
        info["lines"] = decoded.splitlines()
        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            info["cells"] = list(csv.reader(io.StringIO(decoded), delimiter=delimiter))
    return info


def column_index(letters: str) -> int:
    result = 0
    for char in letters.upper():
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1


def contains_id_token(value: str, element_id: str) -> bool:
    """Match one portable spec ID without accepting a longer-ID substring."""

    return bool(
        re.search(
            rf"(?<![A-Za-z0-9._-]){re.escape(element_id)}(?![A-Za-z0-9._-])",
            value,
        )
    )


def validate_render_locator(
    locator: str,
    element_id: str,
    artifact_path: str,
    artifact_info: dict[str, dict[str, Any]],
    context: str,
    errors: list[str],
) -> None:
    info = artifact_info.get(artifact_path)
    if info is None:
        return
    line_match = LINE_LOCATOR_RE.fullmatch(locator)
    if line_match:
        lines = info.get("lines")
        if not isinstance(lines, list):
            errors.append(f"{context}.locator line: syntax requires a UTF-8 text artifact")
            return
        start = int(line_match.group(1))
        end = int(line_match.group(2) or start)
        if end < start or end > len(lines):
            errors.append(
                f"{context}.locator line range {start}-{end} is outside "
                f"artifact {artifact_path!r} ({len(lines)} lines)"
            )
            return
        target = "\n".join(lines[start - 1 : end])
        if not contains_id_token(target, element_id):
            errors.append(
                f"{context}.locator target does not contain element id {element_id!r}"
            )
        return

    cell_match = CELL_LOCATOR_RE.fullmatch(locator)
    if cell_match:
        rows = info.get("cells")
        if not isinstance(rows, list):
            errors.append(f"{context}.locator cell: syntax requires a CSV/TSV artifact")
            return
        row_index = int(cell_match.group(2)) - 1
        col_index = column_index(cell_match.group(1))
        if row_index >= len(rows) or col_index >= len(rows[row_index]):
            errors.append(f"{context}.locator points outside artifact {artifact_path!r}")
            return
        if not contains_id_token(rows[row_index][col_index], element_id):
            errors.append(
                f"{context}.locator target does not contain element id {element_id!r}"
            )
        return

    token_match = TOKEN_LOCATOR_RE.fullmatch(locator)
    if token_match:
        artifact_text = info.get("text")
        token = token_match.group(2)
        if not isinstance(artifact_text, str):
            errors.append(f"{context}.locator token syntax requires inspectable text")
        elif token != element_id:
            errors.append(
                f"{context}.locator token must equal its spec element id {element_id!r}"
            )
        elif not contains_id_token(artifact_text, element_id):
            errors.append(
                f"{context}.locator element id token is absent from "
                f"artifact {artifact_path!r}"
            )
        return

    slide_match = SLIDE_LOCATOR_RE.fullmatch(locator)
    if slide_match:
        slides = info.get("slides")
        slide_number = int(slide_match.group(1))
        if info.get("suffix") != ".pptx" or not isinstance(slides, dict):
            errors.append(f"{context}.locator slide: syntax requires an inspectable PPTX")
        elif slide_number not in slides:
            errors.append(f"{context}.locator references a nonexistent PPTX slide")
        elif not contains_id_token(slides[slide_number], element_id):
            errors.append(
                f"{context}.locator slide does not contain element id {element_id!r}"
            )
        return

    if locator.startswith("page:"):
        errors.append(
            f"{context}.locator page: syntax is unsupported because page geometry "
            "cannot be verified with the bundled standard-library checker"
        )


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_relative_path(value: object, context: str, errors: list[str]) -> str:
    if not nonempty_string(value):
        errors.append(f"{context} must be a non-empty relative path")
        return ""
    raw = text(value).strip()
    if looks_absolute_path(raw) or "\\" in raw:
        errors.append(f"{context} must be a portable relative path, not an absolute path or URI")
        return ""
    pure = PurePosixPath(raw)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        errors.append(f"{context} must not contain empty, dot, or parent-traversal segments")
        return ""
    return raw


def spec_element_ids(spec: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for field in ("nodes", "edges", "claims"):
        value = spec.get(field)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and nonempty_string(item.get("id")):
                result.add(text(item.get("id")).strip())
    return result


def spec_elements_by_id(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for field in ("nodes", "edges", "claims"):
        value = spec.get(field)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and nonempty_string(item.get("id")):
                result[text(item.get("id")).strip()] = item
    return result


def validate_manifest(
    spec: dict[str, Any],
    spec_bytes: bytes,
    manifest: object,
    manifest_dir: Path,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["render manifest top-level value must be an object"]
    validate_no_absolute_paths(manifest, "render_manifest", errors)
    extra_top = sorted(manifest.keys() - ALLOWED_TOP_LEVEL_FIELDS)
    if extra_top:
        errors.append(
            "render manifest may contain only spec_sha256, released_fields, "
            "artifacts, and elements; "
            "unexpected fields: " + ", ".join(extra_top)
        )

    for field in ("spec_sha256", "released_fields", "artifacts", "elements"):
        if field not in manifest:
            errors.append(f"render manifest is missing {field}")

    supplied_spec_hash = text(manifest.get("spec_sha256")).strip()
    actual_spec_hash = sha256_bytes(spec_bytes)
    if not SHA256_RE.fullmatch(supplied_spec_hash):
        errors.append("spec_sha256 must be a lowercase 64-character SHA-256")
    elif supplied_spec_hash != actual_spec_hash:
        errors.append(
            f"spec_sha256 mismatch: expected {actual_spec_hash}, got {supplied_spec_hash}"
        )

    released_fields_value = manifest.get("released_fields")
    released_fields: set[str] = set()
    if not isinstance(released_fields_value, list):
        errors.append("released_fields must be a non-empty array")
    else:
        for index, value in enumerate(released_fields_value):
            if not nonempty_string(value):
                errors.append(f"released_fields[{index}] must be a non-empty string")
                continue
            field = text(value).strip()
            if field in released_fields:
                errors.append(f"duplicate released field: {field!r}")
            released_fields.add(field)
        if not released_fields:
            errors.append("released_fields must declare at least one released category")
    privacy = spec.get("privacy_authorization")
    allowed_fields: set[str] = set()
    if isinstance(privacy, dict) and isinstance(privacy.get("field_allowlist"), list):
        allowed_fields = {
            text(value).strip()
            for value in privacy.get("field_allowlist", [])
            if nonempty_string(value)
        }
    unauthorized_fields = sorted(released_fields - allowed_fields)
    if unauthorized_fields:
        errors.append(
            "released_fields exceeds privacy_authorization.field_allowlist: "
            + ", ".join(unauthorized_fields)
        )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be an array")
        artifacts = []
    if not artifacts:
        errors.append("artifacts must register at least one rendered file")

    registered_artifacts: set[str] = set()
    artifact_info: dict[str, dict[str, Any]] = {}
    root = manifest_dir.resolve()
    for index, record in enumerate(artifacts):
        context = f"artifacts[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{context} must be an object")
            continue
        extra_fields = sorted(record.keys() - ALLOWED_ARTIFACT_FIELDS)
        if extra_fields:
            errors.append(
                f"{context} may contain only path and sha256; unexpected fields: "
                + ", ".join(extra_fields)
            )
        artifact_path = safe_relative_path(record.get("path"), f"{context}.path", errors)
        supplied_hash = text(record.get("sha256")).strip()
        if not SHA256_RE.fullmatch(supplied_hash):
            errors.append(f"{context}.sha256 must be a lowercase 64-character SHA-256")
        if artifact_path in registered_artifacts:
            errors.append(f"duplicate artifact path: {artifact_path!r}")
        elif artifact_path:
            registered_artifacts.add(artifact_path)
        if not artifact_path:
            continue
        artifact_candidate = manifest_dir / artifact_path
        if artifact_candidate.is_symlink():
            errors.append(f"{context}.path must not be a symlink")
            continue
        artifact = artifact_candidate.resolve()
        try:
            artifact.relative_to(root)
        except ValueError:
            errors.append(f"{context}.path resolves outside the manifest directory")
            continue
        try:
            if artifact.stat().st_size > MAX_ARTIFACT_BYTES:
                errors.append(
                    f"{context}.path exceeds the {MAX_ARTIFACT_BYTES}-byte "
                    "inspection limit"
                )
                continue
            content = artifact.read_bytes()
        except OSError as exc:
            errors.append(f"{context}.path cannot be read: {exc}")
            continue
        actual_hash = sha256_bytes(content)
        if SHA256_RE.fullmatch(supplied_hash) and supplied_hash != actual_hash:
            errors.append(
                f"{context}.sha256 mismatch for {artifact_path!r}: "
                f"expected {actual_hash}, got {supplied_hash}"
            )
        artifact_info[artifact_path] = inspect_artifact(artifact_path, content, errors)

    elements = manifest.get("elements")
    if not isinstance(elements, list):
        errors.append("elements must be an array")
        elements = []
    spec_records = spec_elements_by_id(spec)
    expected_ids = set(spec_records)
    seen_ids: set[str] = set()
    included_ids: set[str] = set()
    omitted_ids: set[str] = set()
    for index, record in enumerate(elements):
        context = f"elements[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{context} must be an object")
            continue
        forbidden = sorted(FORBIDDEN_ELEMENT_FIELDS & record.keys())
        if forbidden:
            errors.append(
                f"{context} must inherit semantics from spec and may not redefine: "
                + ", ".join(forbidden)
            )
        element_id = text(record.get("id")).strip()
        if not element_id:
            errors.append(f"{context}.id must be non-empty")
        elif element_id in seen_ids:
            errors.append(f"duplicate render-manifest element id: {element_id!r}")
        else:
            seen_ids.add(element_id)
        if element_id and element_id not in expected_ids:
            errors.append(f"{context}.id is not present in spec: {element_id!r}")

        disposition = record.get("disposition")
        if disposition not in {"included", "omitted"}:
            errors.append(f"{context}.disposition must be 'included' or 'omitted'")
            continue
        allowed_element_fields = {"id", "disposition"}
        if disposition == "included":
            allowed_element_fields.update({"artifact", "locator"})
        else:
            allowed_element_fields.add("reason")
        unexpected_fields = sorted(record.keys() - allowed_element_fields)
        if unexpected_fields:
            errors.append(
                f"{context} contains fields outside the non-semantic manifest schema: "
                + ", ".join(unexpected_fields)
            )
        if disposition == "included":
            if element_id in expected_ids:
                included_ids.add(element_id)
            artifact_path = safe_relative_path(
                record.get("artifact"), f"{context}.artifact", errors
            )
            if artifact_path and artifact_path not in registered_artifacts:
                errors.append(
                    f"{context}.artifact is not registered in artifacts: {artifact_path!r}"
                )
            if not nonempty_string(record.get("locator")):
                errors.append(f"{context}.locator must be non-empty for included elements")
            else:
                locator = text(record.get("locator")).strip()
                if contains_absolute_path(locator) or any(
                    token in locator for token in ("..", "/", "\\")
                ):
                    errors.append(
                        f"{context}.locator must not contain a path, traversal, or file URI"
                    )
                elif not RENDER_LOCATOR_RE.fullmatch(locator):
                    errors.append(
                        f"{context}.locator must use line:, cell:, page:, slide:, "
                        "node:, shape:, or table: syntax"
                    )
                elif artifact_path and artifact_path in registered_artifacts:
                    validate_render_locator(
                        locator,
                        element_id,
                        artifact_path,
                        artifact_info,
                        context,
                        errors,
                    )
            if "reason" in record:
                errors.append(f"{context} included elements must not use omission reason")
        else:
            if element_id in expected_ids:
                omitted_ids.add(element_id)
            if not nonempty_string(record.get("reason")):
                errors.append(f"{context}.reason must be non-empty for omitted elements")
            if "artifact" in record or "locator" in record:
                errors.append(f"{context} omitted elements must not declare artifact/locator")

    missing_ids = sorted(expected_ids - seen_ids)
    if missing_ids:
        errors.append("render manifest does not account for spec IDs: " + ", ".join(missing_ids))
    for element_id in sorted(omitted_ids):
        for artifact_path, info in artifact_info.items():
            artifact_text = info.get("text")
            if isinstance(artifact_text, str) and contains_id_token(
                artifact_text, element_id
            ):
                errors.append(
                    f"omitted element {element_id!r} still appears in artifact "
                    f"{artifact_path!r}"
                )
    included_types = {
        text(spec_records[element_id].get("record_type")).strip()
        for element_id in included_ids
        if element_id in spec_records
    }
    if "legal_rule" in included_types and "legal_rules" not in released_fields:
        errors.append("released_fields must include legal_rules when a legal_rule is rendered")
    if included_types - {"legal_rule"} and "facts" not in released_fields:
        errors.append(
            "released_fields must include facts when fact, source_statement, "
            "or inference records are rendered"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("render_manifest", type=Path)
    args = parser.parse_args()

    try:
        spec_bytes = args.spec.read_bytes()
        spec = json.loads(spec_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"INVALID SPEC: {exc}", file=sys.stderr)
        return 2
    spec_errors = validate(spec)
    if spec_errors:
        for error in spec_errors:
            print(f"SPEC ERROR: {error}")
        print(f"INVALID SPEC: {len(spec_errors)} error(s)")
        return 2

    try:
        manifest = json.loads(args.render_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID MANIFEST: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(
        spec,
        spec_bytes,
        manifest,
        args.render_manifest.parent,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"INVALID OUTPUT: {len(errors)} error(s)")
        return 1
    print(
        "VALID OUTPUT: spec/artifact hashes, declared released-field subset, "
        "one-to-one manifest accounting, and locator-target ID checks passed; "
        "visual meaning, unmodeled assertions, substantive correctness, and actual "
        "release authorization still require human review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
