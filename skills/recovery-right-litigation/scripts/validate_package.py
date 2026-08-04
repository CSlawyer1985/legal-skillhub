#!/usr/bin/env python3
"""Profile-driven validator for the platform-lite legal Skill packages."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

MAX_FILES = 200
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".csv", ".json", ".md", ".mmd", ".py", ".svg", ".txt"}
ALLOWED_EXTENSIONLESS = {"LICENSE", "NOTICE", "VERSION"}
ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
DENIED_PARTS = {
    "__MACOSX",
    "__pycache__",
    "e2e",
    "evidence",
    "fixtures",
    "renders",
    "preview",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() or path.is_symlink()),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            result[match.group(1)] = match.group(2).strip().strip("\"'")
    return result


def parse_checksums(path: Path) -> tuple[dict[str, str], list[str]]:
    entries: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"SHA256SUMS.txt:{line_number}: invalid checksum line")
            continue
        digest, relative = match.groups()
        if relative in entries:
            errors.append(f"SHA256SUMS.txt:{line_number}: duplicate {relative}")
        entries[relative] = digest
    return entries, errors


def validate(root: Path) -> dict[str, object]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, object] = {}

    profile_path = root / "PACKAGE-PROFILE.json"
    if not root.is_dir() or not profile_path.is_file():
        return {
            "status": "FAIL",
            "root": str(root),
            "errors": ["missing package directory or PACKAGE-PROFILE.json"],
            "warnings": [],
            "checks": {},
        }

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "FAIL",
            "root": str(root),
            "errors": [f"invalid PACKAGE-PROFILE.json: {exc}"],
            "warnings": [],
            "checks": {},
        }

    files = package_files(root)
    regular_files = [path for path in files if path.is_file() and not path.is_symlink()]
    relative_paths = [path.relative_to(root).as_posix() for path in files]
    total_bytes = sum(path.stat().st_size for path in regular_files)
    checks["file_count"] = len(files)
    checks["total_uncompressed_bytes"] = total_bytes

    if len(files) > MAX_FILES:
        errors.append(f"file count {len(files)} exceeds {MAX_FILES}")
    if total_bytes >= MAX_BYTES:
        errors.append(f"uncompressed bytes {total_bytes} are not below {MAX_BYTES}")

    required = set(profile.get("required_paths", []))
    missing_required = sorted(required - set(relative_paths))
    if missing_required:
        errors.append(f"missing required paths: {missing_required}")

    skill_paths = [
        relative for relative in relative_paths if Path(relative).name == "SKILL.md"
    ]
    checks["skill_entrypoints"] = skill_paths
    if skill_paths != ["SKILL.md"]:
        errors.append(f"expected exactly one root SKILL.md, found {skill_paths}")

    mac_user_pattern = r"/" + r"Users/[^/\s]+"
    stale_wrapper_names = set(profile.get("stale_wrapper_names", []))
    for path, relative in zip(files, relative_paths):
        parts = set(Path(relative).parts)
        if path.is_symlink():
            errors.append(f"symlink is not allowed: {relative}")
            continue
        if parts & DENIED_PARTS:
            errors.append(f"historical/binary validation payload is not allowed: {relative}")
        if path.name in {".DS_Store"} or path.suffix.lower() in {".pyc", ".pyo"}:
            errors.append(f"cache or metadata is not allowed: {relative}")
        if path.suffix.lower() in ARCHIVE_SUFFIXES:
            errors.append(f"nested archive is not allowed: {relative}")
        if path.suffix:
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                errors.append(f"non-platform text extension: {relative}")
        elif path.name not in ALLOWED_EXTENSIONLESS:
            errors.append(f"unexpected extensionless file: {relative}")
        if path.stat().st_size >= MAX_BYTES:
            errors.append(f"individual file is not below 10 MB: {relative}")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"not UTF-8 text: {relative}")
            continue

        if re.search(mac_user_pattern, text):
            errors.append(f"macOS user path leaked: {relative}")
        for stale in stale_wrapper_names:
            if stale and stale in text:
                errors.append(f"stale wrapper marker {stale!r}: {relative}")
        if path.suffix.lower() == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON {relative}: {exc}")
        if path.suffix.lower() == ".py":
            try:
                ast.parse(text, filename=relative)
            except SyntaxError as exc:
                errors.append(f"invalid Python {relative}: {exc}")

    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(skill_text)
        checks["frontmatter"] = frontmatter
        for field in ("name", "description", "license"):
            if not frontmatter.get(field):
                errors.append(f"SKILL.md frontmatter missing {field}")
        if frontmatter.get("name") != profile.get("skill_name"):
            errors.append("SKILL.md name does not match PACKAGE-PROFILE.json")
        if frontmatter.get("license") != profile.get("package_license"):
            errors.append("SKILL.md license does not match PACKAGE-PROFILE.json")
        if len(frontmatter.get("description", "")) > 1024:
            errors.append("SKILL.md description exceeds 1024 characters")
        missing_markers = sorted(
            marker
            for marker in profile.get("workflow_markers", [])
            if marker not in skill_text
        )
        if missing_markers:
            errors.append(f"SKILL.md missing workflow markers: {missing_markers}")

    license_path = root / "LICENSE"
    if license_path.is_file():
        license_text = license_path.read_text(encoding="utf-8")
        expected_family = profile.get("license_text_family")
        if expected_family == "MIT" and "MIT License" not in license_text:
            errors.append("LICENSE does not contain the MIT License text")
        if expected_family == "GPL-3.0" and (
            "GNU GENERAL PUBLIC LICENSE" not in license_text
            or "Version 3" not in license_text
        ):
            errors.append("LICENSE does not contain GNU GPL version 3")

    provenance_path = root / "LICENSE-PROVENANCE.json"
    if provenance_path.is_file():
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            if provenance.get("package_license") != profile.get("package_license"):
                errors.append("license provenance package_license mismatch")
            if provenance.get("source_archive_sha256") != profile.get(
                "source_archive_sha256"
            ):
                errors.append("license provenance source archive binding mismatch")
            if provenance.get("upload_executed") is not False:
                errors.append("license provenance must record upload_executed=false")
            if not provenance.get("external_distribution_gate"):
                errors.append("license provenance must preserve distribution gate")
        except json.JSONDecodeError:
            pass

    prompts_path = root / "tests" / "route-prompts.json"
    if prompts_path.is_file():
        try:
            prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
            type_counts: dict[str, int] = {}
            for case in prompts.get("cases", []):
                case_type = case.get("type", "")
                type_counts[case_type] = type_counts.get(case_type, 0) + 1
            checks["route_test_counts"] = type_counts
            for case_type, minimum in (
                ("should_trigger", 3),
                ("should_not_trigger", 3),
                ("edge_case", 2),
            ):
                if type_counts.get(case_type, 0) < minimum:
                    errors.append(
                        f"route prompts need at least {minimum} {case_type} cases"
                    )
        except json.JSONDecodeError:
            pass

    checksum_path = root / "SHA256SUMS.txt"
    if checksum_path.is_file():
        entries, checksum_errors = parse_checksums(checksum_path)
        errors.extend(checksum_errors)
        expected = set(relative_paths) - {"SHA256SUMS.txt"}
        if set(entries) != expected:
            errors.append(
                "checksum inventory mismatch "
                f"missing={sorted(expected - set(entries))} "
                f"extra={sorted(set(entries) - expected)}"
            )
        for relative, expected_hash in entries.items():
            target = root / relative
            if target.is_file() and sha256_file(target) != expected_hash:
                errors.append(f"checksum mismatch: {relative}")

    receipt_path = root / "PACKAGE-RECEIPT.json"
    if receipt_path.is_file():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("file_count") != len(files):
                errors.append("PACKAGE-RECEIPT.json file_count mismatch")
            if receipt.get("upload_executed") is not False:
                errors.append("PACKAGE-RECEIPT.json must record upload_executed=false")
            if receipt.get("legacy_package_overwritten") is not False:
                errors.append(
                    "PACKAGE-RECEIPT.json must record legacy_package_overwritten=false"
                )
        except json.JSONDecodeError:
            pass

    checks["nested_archives"] = [
        relative
        for path, relative in zip(files, relative_paths)
        if path.suffix.lower() in ARCHIVE_SUFFIXES
    ]
    checks["symlinks"] = [
        relative for path, relative in zip(files, relative_paths) if path.is_symlink()
    ]
    checks["text_profile"] = all(
        path.suffix.lower() in ALLOWED_SUFFIXES
        or path.name in ALLOWED_EXTENSIONLESS
        for path in regular_files
    )

    return {
        "status": "PASS" if not errors else "FAIL",
        "root": str(root),
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def run_selftest(root: Path) -> dict[str, object]:
    cases: list[dict[str, object]] = []
    mutations = (
        (
            "nested_archive",
            lambda temp_root: (temp_root / "bad.zip").write_bytes(
                b"PK\x05\x06" + b"\0" * 18
            ),
            "nested archive",
        ),
        (
            "extra_skill",
            lambda temp_root: (
                (temp_root / "extra").mkdir(),
                (temp_root / "extra" / "SKILL.md").write_text(
                    "---\nname: extra\ndescription: extra\nlicense: MIT\n---\n",
                    encoding="utf-8",
                ),
            ),
            "exactly one root SKILL.md",
        ),
        (
            "absolute_path",
            lambda temp_root: (temp_root / "README.md").write_text(
                (temp_root / "README.md").read_text(encoding="utf-8")
                + "\n/"
                + "Users/example/private\n",
                encoding="utf-8",
            ),
            "user path leaked",
        ),
    )
    for name, mutate, expected in mutations:
        with tempfile.TemporaryDirectory(prefix="platform-lite-selftest-") as temp:
            temp_root = Path(temp) / "package"
            shutil.copytree(root, temp_root)
            mutate(temp_root)
            result = validate(temp_root)
            text = "\n".join(result["errors"])
            passed = result["status"] == "FAIL" and expected in text
            cases.append(
                {
                    "name": name,
                    "status": "PASS" if passed else "FAIL",
                    "expected_error_fragment": expected,
                }
            )
    return {
        "status": "PASS" if all(case["status"] == "PASS" for case in cases) else "FAIL",
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    result = validate(root)
    if args.selftest and result["status"] == "PASS":
        result["selftest"] = run_selftest(root.resolve())
        if result["selftest"]["status"] != "PASS":
            result["status"] = "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
