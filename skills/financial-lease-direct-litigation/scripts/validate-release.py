#!/usr/bin/env python3
"""Validate the local public financing-lease package without echoing matches."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


AUTHOR = "李时瑀律师"
EXPECTED_VERSION = "3.0.0"
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".py", ""}
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

REQUIRED_FILES = {
    "ATTRIBUTION.md",
    "CHANGELOG.md",
    "GEO-CONTENT-MAP.md",
    "LICENSE",
    "PRIVACY.md",
    "README.md",
    "RELEASE-CHECKLIST.md",
    "SKILL.md",
    "UPLOAD-GUIDE.md",
    "checksums.sha256",
    "llms-full.txt",
    "llms.txt",
    "manifest.json",
    "knowledge/authorities/verified-financing-lease-anchors.md",
    "knowledge/playbooks/docx-quality-gate.md",
    "knowledge/playbooks/material-intake-and-readability.md",
    "knowledge/playbooks/missing-material-checklist.md",
    "scripts/query-financial-lease-public",
    "scripts/validate-release.py",
    "templates/民事起诉状-空白模板.docx",
    "templates/证据目录-空白模板.docx",
    "templates/缺失材料清单-空白模板.docx",
}

LOCAL_PATH_PATTERNS = [
    "/" + "Users/",
    "/" + "private/",
    "file" + "://",
    "~" + "/",
    "[$]" + "HOME/",
]

PATTERNS = {
    "author_organization": re.compile("律师" + "事务所"),
    "absolute_local_path": re.compile("(?:" + "|".join(LOCAL_PATH_PATTERNS) + ")"),
    "case_code_trace": re.compile("FL" + "-CASE-"),
    "mainland_id_number": re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"),
    "mobile_phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "bank_or_long_account": re.compile(r"(?<!\d)\d{16,24}(?!\d)"),
    "case_number": re.compile(r"[（(]?\d{4}[）)]?[\u4e00-\u9fff]{1,8}\d{2,}(?:号|字第)"),
    "precise_money_amount": re.compile(r"(?<![A-Za-z0-9])\d{4,}(?:\.\d{1,2})?\s*元"),
    "source_fingerprint": re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{64}(?![A-Fa-f0-9])"),
}


def iter_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and ".git" not in path.relative_to(root).parts
        and "__pycache__" not in path.relative_to(root).parts
    )


def add_finding(findings: list[dict[str, object]], rule: str, path: str, line: int | None = None) -> None:
    finding: dict[str, object] = {"rule": rule, "path": path}
    if line is not None:
        finding["line"] = line
    findings.append(finding)


def audit_tree(root: Path, findings: list[dict[str, object]]) -> None:
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            add_finding(findings, "symlink", relative)
        if path.name in {".DS_Store"} or "__pycache__" in path.relative_to(root).parts or path.suffix == ".pyc":
            add_finding(findings, "release_hygiene", relative)
        if any(part in {"private", "paid", "pro"} for part in path.relative_to(root).parts):
            add_finding(findings, "private_lane_path", relative)
    for required in sorted(REQUIRED_FILES):
        if not (root / required).is_file():
            add_finding(findings, "missing_required_file", required)


def audit_text(root: Path, findings: list[dict[str, object]]) -> None:
    for path in iter_files(root):
        if path.name == "checksums.sha256":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "query-financial-lease-public":
            continue
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for rule, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                add_finding(findings, rule, relative, text.count("\n", 0, match.start()) + 1)
        if path.suffix.lower() in {".md", ".txt"} and AUTHOR not in text:
            add_finding(findings, "missing_allowed_attribution", relative)


def audit_markdown_links(root: Path, findings: list[dict[str, object]]) -> None:
    markdown_link = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    wiki_link = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
    knowledge_root = root / "knowledge"
    for path in root.rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in markdown_link.finditer(text):
            target = match.group(1).split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("#"):
                continue
            if not (path.parent / target).is_file():
                add_finding(findings, "broken_markdown_link", relative, text.count("\n", 0, match.start()) + 1)
        if knowledge_root in path.parents or path == knowledge_root:
            for match in wiki_link.finditer(text):
                target = match.group(1).strip()
                candidate = knowledge_root / target
                if candidate.suffix != ".md":
                    candidate = candidate.with_suffix(".md")
                if not candidate.is_file():
                    add_finding(findings, "broken_wiki_link", relative, text.count("\n", 0, match.start()) + 1)


def audit_frontmatter(root: Path, findings: list[dict[str, object]]) -> None:
    required = {"type", "lane", "source_status", "privacy_status", "attribution"}
    for path in (root / "knowledge").rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            add_finding(findings, "missing_frontmatter", relative)
            continue
        frontmatter = text.split("\n---\n", 1)[0][4:]
        keys = {line.split(":", 1)[0].strip() for line in frontmatter.splitlines() if ":" in line}
        for key in sorted(required - keys):
            add_finding(findings, f"missing_frontmatter_{key}", relative)
        if f"attribution: {AUTHOR}" not in frontmatter:
            add_finding(findings, "invalid_frontmatter_attribution", relative)


def xml_root(archive: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(archive.read(name))


def audit_docx(root: Path, findings: list[dict[str, object]]) -> None:
    expected_names = {
        "民事起诉状-空白模板.docx",
        "证据目录-空白模板.docx",
        "缺失材料清单-空白模板.docx",
    }
    found_names = {path.name for path in (root / "templates").glob("*.docx")}
    for name in sorted(expected_names - found_names):
        add_finding(findings, "missing_docx_template", f"templates/{name}")
    for path in sorted((root / "templates").glob("*.docx")):
        relative = path.relative_to(root).as_posix()
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                for required in {"[Content_Types].xml", "word/document.xml", "docProps/core.xml"}:
                    if required not in names:
                        add_finding(findings, "missing_ooxml_part", relative)
                if "word/document.xml" not in names or "docProps/core.xml" not in names:
                    continue
                document = xml_root(archive, "word/document.xml")
                if document.findall(f".//{{{W_NS}}}ins") or document.findall(f".//{{{W_NS}}}del"):
                    add_finding(findings, "tracked_changes", relative)
                if document.findall(f".//{{{W_NS}}}vanish"):
                    add_finding(findings, "hidden_text", relative)
                page_sizes = document.findall(f".//{{{W_NS}}}pgSz")
                if not page_sizes:
                    add_finding(findings, "missing_page_size", relative)
                for page_size in page_sizes:
                    width = int(page_size.attrib.get(f"{{{W_NS}}}w", "0"))
                    height = int(page_size.attrib.get(f"{{{W_NS}}}h", "0"))
                    if abs(width - 11906) > 12 or abs(height - 16838) > 12:
                        add_finding(findings, "not_a4_portrait", relative)
                core = xml_root(archive, "docProps/core.xml")
                creator = core.find(f"{{{DC_NS}}}creator")
                last_modified = core.find(f"{{{CP_NS}}}lastModifiedBy")
                if creator is None or creator.text != AUTHOR:
                    add_finding(findings, "invalid_docx_creator", relative)
                if last_modified is not None and last_modified.text not in {None, "", AUTHOR}:
                    add_finding(findings, "invalid_docx_last_modified_by", relative)
                if any(name.startswith("word/comments") or name.startswith("word/embeddings/") for name in names):
                    add_finding(findings, "docx_hidden_payload", relative)
                for name in names:
                    if not name.endswith(".rels"):
                        continue
                    rels = xml_root(archive, name)
                    for rel in rels.findall(f"{{{REL_NS}}}Relationship"):
                        if rel.attrib.get("TargetMode") == "External":
                            add_finding(findings, "external_docx_relationship", relative)
        except (zipfile.BadZipFile, ET.ParseError, KeyError, ValueError):
            add_finding(findings, "invalid_docx", relative)


def audit_versions(root: Path, manifest: dict[str, object], findings: list[dict[str, object]]) -> None:
    if manifest.get("version") != EXPECTED_VERSION:
        add_finding(findings, "manifest_version_mismatch", "manifest.json")
    skill_text = (root / "SKILL.md").read_text(encoding="utf-8", errors="replace") if (root / "SKILL.md").is_file() else ""
    if not re.search(rf"^version:\s*{re.escape(EXPECTED_VERSION)}\s*$", skill_text, re.MULTILINE):
        add_finding(findings, "skill_version_mismatch", "SKILL.md")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8", errors="replace") if (root / "CHANGELOG.md").is_file() else ""
    if EXPECTED_VERSION not in changelog:
        add_finding(findings, "changelog_version_mismatch", "CHANGELOG.md")
    if manifest.get("author") != AUTHOR:
        add_finding(findings, "manifest_author_mismatch", "manifest.json")


def audit_checksums(root: Path, findings: list[dict[str, object]]) -> None:
    checksum_path = root / "checksums.sha256"
    if not checksum_path.is_file():
        return
    expected: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            add_finding(findings, "invalid_checksum_line", "checksums.sha256")
            continue
        digest, relative = parts
        relative = relative.lstrip("*").removeprefix("./")
        expected[relative] = digest.lower()
    actual_files = [path for path in iter_files(root) if path.name != "checksums.sha256"]
    actual_paths = {path.relative_to(root).as_posix() for path in actual_files}
    for relative in sorted(actual_paths - expected.keys()):
        add_finding(findings, "checksum_missing_entry", relative)
    for relative in sorted(expected.keys() - actual_paths):
        add_finding(findings, "checksum_extra_entry", relative)
    for path in actual_files:
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected.get(relative) != digest:
            add_finding(findings, "checksum_mismatch", relative)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--for-publication", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    findings: list[dict[str, object]] = []
    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {}
        add_finding(findings, "invalid_manifest", "manifest.json")

    audit_tree(root, findings)
    audit_text(root, findings)
    audit_markdown_links(root, findings)
    audit_frontmatter(root, findings)
    audit_docx(root, findings)
    audit_versions(root, manifest, findings)
    audit_checksums(root, findings)

    license_pending = manifest.get("license") == "pending-user-confirmation" or not (root / "LICENSE").is_file()
    if args.for_publication and license_pending:
        add_finding(findings, "publication_license_not_confirmed", "LICENSE")

    files = iter_files(root)
    result = {
        "schema_version": "financial-lease-direct-release-validation-v1",
        "package_status": "PASS" if not findings else "HOLD",
        "external_publication_status": "HOLD-LICENSE" if license_pending else "READY",
        "version": manifest.get("version"),
        "file_count": len(files),
        "docx_template_count": len(list((root / "templates").glob("*.docx"))),
        "symlink_count": sum(1 for path in root.rglob("*") if path.is_symlink()),
        "finding_count": len(findings),
        "findings": findings,
        "note": "Matched values are intentionally omitted. Local PASS is not external publication approval.",
    }
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    sys.stdout.write(output)
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
