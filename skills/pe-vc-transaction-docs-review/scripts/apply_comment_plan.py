#!/usr/bin/env python3
"""Apply or roll back bilingual comment-plan rows as native Word comments."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

import contract_clause_model
from review_schema import comment_value_for


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPE_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
COMMENTS_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
COMMENTS_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
NS = {"w": W_NS, "pr": PKG_REL_NS, "ct": CONTENT_TYPE_NS}


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def q(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def xml_bytes(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def visible_text_hash(document_root: etree._Element) -> str:
    text = "\n".join(paragraph_text(paragraph) for paragraph in document_root.xpath(".//w:p", namespaces=NS))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_match_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def read_plan(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def ensure_content_type(root: etree._Element) -> bool:
    existing = root.xpath("//ct:Override[@PartName='/word/comments.xml']", namespaces=NS)
    if existing:
        return True
    override = etree.SubElement(root, q(CONTENT_TYPE_NS, "Override"))
    override.set("PartName", "/word/comments.xml")
    override.set("ContentType", COMMENTS_CONTENT_TYPE)
    return False


def ensure_relationship(root: etree._Element) -> bool:
    for relationship in root.xpath("//pr:Relationship", namespaces=NS):
        if relationship.get("Type") == COMMENTS_REL_TYPE and relationship.get("Target") == "comments.xml":
            return True
    ids = []
    for relationship in root.xpath("//pr:Relationship", namespaces=NS):
        match = re.fullmatch(r"rId(\d+)", relationship.get("Id", ""))
        if match:
            ids.append(int(match.group(1)))
    relationship = etree.SubElement(root, q(PKG_REL_NS, "Relationship"))
    relationship.set("Id", f"rId{max(ids, default=0) + 1}")
    relationship.set("Type", COMMENTS_REL_TYPE)
    relationship.set("Target", "comments.xml")
    return False


def comments_root(existing: bytes | None) -> etree._Element:
    if existing:
        return etree.fromstring(existing)
    return etree.Element(w("comments"), nsmap={"w": W_NS})


def next_comment_id(root: etree._Element, document_root: etree._Element) -> int:
    ids = []
    for element in [*root.xpath("//w:comment", namespaces=NS), *document_root.xpath("//*[@w:id]", namespaces=NS)]:
        try:
            ids.append(int(element.get(w("id"))))
        except (TypeError, ValueError):
            continue
    return max(ids, default=-1) + 1


def append_comment(root: etree._Element, comment_id: int, text: str, author: str, initials: str) -> None:
    comment = etree.SubElement(root, w("comment"))
    comment.set(w("id"), str(comment_id))
    comment.set(w("author"), author)
    comment.set(w("initials"), initials)
    comment.set(w("date"), dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    paragraph = etree.SubElement(comment, w("p"))
    run = etree.SubElement(paragraph, w("r"))
    text_element = etree.SubElement(run, w("t"))
    parts = text.splitlines() or [text]
    text_element.text = parts[0]
    for part in parts[1:]:
        etree.SubElement(run, w("br"))
        element = etree.SubElement(run, w("t"))
        element.text = part


def anchor_paragraph(paragraph: etree._Element, comment_id: int) -> None:
    start = etree.Element(w("commentRangeStart"))
    start.set(w("id"), str(comment_id))
    insert_at = 1 if len(paragraph) and paragraph[0].tag == w("pPr") else 0
    paragraph.insert(insert_at, start)
    end = etree.Element(w("commentRangeEnd"))
    end.set(w("id"), str(comment_id))
    paragraph.append(end)
    run = etree.SubElement(paragraph, w("r"))
    run_properties = etree.SubElement(run, w("rPr"))
    style = etree.SubElement(run_properties, w("rStyle"))
    style.set(w("val"), "CommentReference")
    reference = etree.SubElement(run, w("commentReference"))
    reference.set(w("id"), str(comment_id))


def clause_ranges(paragraphs: list[etree._Element]) -> list[dict[str, object]]:
    records = [{"paragraph": index, "text": paragraph_text(paragraph)} for index, paragraph in enumerate(paragraphs, start=1)]
    return contract_clause_model.build_clauses(records)


def location_score(location: str, paragraph_index: int, clauses: list[dict[str, object]]) -> int:
    if not location:
        return 0
    compact_location = contract_clause_model.compact_text(location)
    score = 0
    paragraph_match = re.search(r"(?:paragraph|第)\s*(\d+)\s*(?:段)?", location, re.I)
    if paragraph_match and int(paragraph_match.group(1)) == paragraph_index:
        score += 5
    for clause in clauses:
        start = int(clause.get("paragraph_start") or 0)
        end = int(clause.get("paragraph_end") or start)
        if not start <= paragraph_index <= end:
            continue
        label = contract_clause_model.compact_text(clause.get("label", ""))
        normalized_label = contract_clause_model.compact_text(clause.get("normalized_label", ""))
        if label and label in compact_location:
            score += 4
        if normalized_label and normalized_label in compact_location:
            score += 2
    return score


def find_candidates(
    paragraphs: list[etree._Element],
    anchor: str,
    location: str,
    clauses: list[dict[str, object]],
) -> list[tuple[int, etree._Element, int]]:
    direct = []
    normalized_anchor = normalize_match_text(anchor)
    for index, paragraph in enumerate(paragraphs, start=1):
        text = paragraph_text(paragraph)
        if anchor in text or normalized_anchor in normalize_match_text(text):
            direct.append((index, paragraph, location_score(location, index, clauses)))
    if not direct:
        return []
    highest = max(item[2] for item in direct)
    if highest > 0:
        return [item for item in direct if item[2] == highest]
    return direct


def structural_verification(path: Path, added_ids: list[int]) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        names = set(archive.namelist())
        document_root = etree.fromstring(archive.read("word/document.xml"))
        comments = etree.fromstring(archive.read("word/comments.xml")) if "word/comments.xml" in names else None
        rels = etree.fromstring(archive.read("word/_rels/document.xml.rels")) if "word/_rels/document.xml.rels" in names else None
        content_types = etree.fromstring(archive.read("[Content_Types].xml"))
    checks = {}
    for comment_id in added_ids:
        value = str(comment_id)
        checks[value] = {
            "comment": bool(comments is not None and comments.xpath("//w:comment[@w:id=$id]", namespaces=NS, id=value)),
            "range_start": bool(document_root.xpath("//w:commentRangeStart[@w:id=$id]", namespaces=NS, id=value)),
            "range_end": bool(document_root.xpath("//w:commentRangeEnd[@w:id=$id]", namespaces=NS, id=value)),
            "reference": bool(document_root.xpath("//w:commentReference[@w:id=$id]", namespaces=NS, id=value)),
        }
    relationship_ok = bool(
        rels is not None
        and rels.xpath("//pr:Relationship[@Type=$type and @Target='comments.xml']", namespaces=NS, type=COMMENTS_REL_TYPE)
    )
    content_type_ok = bool(
        content_types.xpath("//ct:Override[@PartName='/word/comments.xml' and @ContentType=$type]", namespaces=NS, type=COMMENTS_CONTENT_TYPE)
    )
    all_ids_ok = all(all(values.values()) for values in checks.values())
    return {
        "zip_ok": bad_member is None,
        "bad_zip_member": bad_member,
        "comments_part": comments is not None,
        "relationship": relationship_ok,
        "content_type": content_type_ok,
        "comment_ids": checks,
        "ok": bad_member is None and comments is not None and relationship_ok and content_type_ok and all_ids_ok,
        "visible_text_sha256": visible_text_hash(document_root),
    }


def write_docx(archive: zipfile.ZipFile, output: Path, overrides: dict[str, bytes], remove: set[str] | None = None) -> None:
    remove = remove or set()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
            existing = set()
            for info in archive.infolist():
                name = info.filename
                existing.add(name)
                if name in remove:
                    continue
                target.writestr(info, overrides.get(name, archive.read(name)))
            for name, content in overrides.items():
                if name not in existing and name not in remove:
                    target.writestr(name, content)
        temp_path.replace(output)
    finally:
        temp_path.unlink(missing_ok=True)


def apply_comments(
    source: Path,
    plan: Path,
    output: Path,
    *,
    author: str = "Codex",
    initials: str = "CX",
    allow_partial: bool = False,
    allow_ambiguous: bool = False,
) -> dict[str, object]:
    if source.resolve() == output.resolve():
        return {
            "source": str(source),
            "output": str(output),
            "ok": False,
            "output_written": False,
            "errors": ["source and output must be different paths; in-place comment writes are prohibited"],
        }
    source_hash = sha256_file(source)
    plan_hash = sha256_file(plan)
    headers, rows = read_plan(plan)
    report: dict[str, object] = {
        "source": str(source),
        "output": str(output),
        "plan": str(plan),
        "source_sha256": source_hash,
        "plan_sha256": plan_hash,
        "rows": [],
        "added_comment_ids": [],
        "output_written": False,
    }
    if not headers or not rows:
        report["errors"] = ["comment plan must contain a header and at least one row"]
        return report
    with zipfile.ZipFile(source, "r") as archive:
        names = set(archive.namelist())
        required = {"word/document.xml", "[Content_Types].xml"}
        if not required.issubset(names):
            report["errors"] = [f"invalid DOCX; missing {sorted(required - names)}"]
            return report
        document_root = etree.fromstring(archive.read("word/document.xml"))
        paragraphs = document_root.xpath(".//w:p", namespaces=NS)
        clauses = clause_ranges(paragraphs)
        source_visible_hash = visible_text_hash(document_root)
        comments_existed = "word/comments.xml" in names
        comments = comments_root(archive.read("word/comments.xml") if comments_existed else None)
        rels_name = "word/_rels/document.xml.rels"
        rels_existed = rels_name in names
        rels = etree.fromstring(archive.read(rels_name)) if rels_existed else etree.Element(q(PKG_REL_NS, "Relationships"), nsmap={None: PKG_REL_NS})
        content_types = etree.fromstring(archive.read("[Content_Types].xml"))
        relationship_existed = ensure_relationship(rels)
        content_type_existed = ensure_content_type(content_types)
        comment_id = next_comment_id(comments, document_root)
        matches: list[tuple[dict[str, str], etree._Element, int, int, str]] = []
        failures = 0
        applicable = 0
        source_name = source.name.casefold()
        for row_index, row in enumerate(rows, start=2):
            row_file = comment_value_for(row, "file")
            anchor = comment_value_for(row, "anchor_text")
            location = comment_value_for(row, "location")
            comment_text = comment_value_for(row, "comment_text")
            row_report = {"row": row_index, "file": row_file, "location": location, "anchor_text": anchor}
            if row_file and Path(row_file).name.casefold() != source_name:
                row_report["status"] = "skipped_other_file"
                report["rows"].append(row_report)
                continue
            applicable += 1
            if not anchor or not comment_text:
                row_report["status"] = "missing_anchor_or_comment"
                failures += 1
                report["rows"].append(row_report)
                continue
            candidates = find_candidates(paragraphs, anchor, location, clauses)
            if not candidates:
                row_report["status"] = "anchor_not_found"
                failures += 1
                report["rows"].append(row_report)
                continue
            if len(candidates) > 1 and not allow_ambiguous:
                row_report["status"] = "ambiguous_anchor"
                row_report["candidate_paragraphs"] = [item[0] for item in candidates]
                failures += 1
                report["rows"].append(row_report)
                continue
            selected = candidates[0]
            status = "matched_ambiguous" if len(candidates) > 1 else "matched"
            row_report.update(
                {
                    "status": status,
                    "paragraph": selected[0],
                    "comment_id": comment_id,
                    "anchor_scope": "whole_paragraph",
                }
            )
            report["rows"].append(row_report)
            matches.append((row, selected[1], selected[0], comment_id, comment_text))
            comment_id += 1
        if applicable == 0:
            failures += 1
            report["errors"] = ["comment plan contains no rows applicable to this file"]
        if failures and not allow_partial:
            report.update(
                {
                    "source_visible_text_sha256": source_visible_hash,
                    "applicable_rows": applicable,
                    "failed_rows": failures,
                    "source_had_comments_part": comments_existed,
                    "source_had_comments_relationship": relationship_existed,
                    "source_had_comments_content_type": content_type_existed,
                }
            )
            return report
        if not matches:
            report.update(
                {
                    "source_visible_text_sha256": source_visible_hash,
                    "applicable_rows": applicable,
                    "failed_rows": failures,
                    "errors": ["no comment-plan rows could be anchored"],
                }
            )
            return report
        for _, paragraph, _, current_id, comment_text in matches:
            anchor_paragraph(paragraph, current_id)
            append_comment(comments, current_id, comment_text, author, initials)
            report["added_comment_ids"].append(current_id)
        overrides = {
            "word/document.xml": xml_bytes(document_root),
            "word/comments.xml": xml_bytes(comments),
            rels_name: xml_bytes(rels),
            "[Content_Types].xml": xml_bytes(content_types),
        }
        write_docx(archive, output, overrides)
    verification = structural_verification(output, report["added_comment_ids"])
    report.update(
        {
            "source_visible_text_sha256": source_visible_hash,
            "output_visible_text_sha256": verification["visible_text_sha256"],
            "visible_text_unchanged": source_visible_hash == verification["visible_text_sha256"],
            "source_file_unchanged": source_hash == sha256_file(source),
            "output_sha256": sha256_file(output),
            "applicable_rows": applicable,
            "failed_rows": failures,
            "added_comment_count": len(report["added_comment_ids"]),
            "source_had_comments_part": comments_existed,
            "source_had_comments_relationship": relationship_existed,
            "source_had_comments_content_type": content_type_existed,
            "structural_verification": verification,
            "output_written": True,
        }
    )
    report["ok"] = bool(
        verification["ok"]
        and report["visible_text_unchanged"]
        and report["source_file_unchanged"]
        and report["added_comment_count"] > 0
        and (failures == 0 or allow_partial)
    )
    return report


def remove_elements_by_ids(root: etree._Element, ids: set[str]) -> None:
    for tag in ("commentRangeStart", "commentRangeEnd", "commentReference"):
        for element in root.xpath(f"//w:{tag}[@w:id]", namespaces=NS):
            if element.get(w("id")) in ids:
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
                    if tag == "commentReference" and parent.tag == w("r") and all(child.tag == w("rPr") for child in parent):
                        grandparent = parent.getparent()
                        if grandparent is not None:
                            grandparent.remove(parent)


def rollback_comments(reviewed: Path, report_path: Path, output: Path) -> dict[str, object]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    ids = {str(value) for value in report.get("added_comment_ids", [])}
    result: dict[str, object] = {"reviewed": str(reviewed), "output": str(output), "removed_comment_ids": sorted(ids)}
    if reviewed.resolve() == output.resolve():
        result.update({"ok": False, "errors": ["reviewed and output must be different paths; in-place rollback is prohibited"]})
        return result
    if not ids:
        result.update({"ok": False, "errors": ["report contains no added comment IDs"]})
        return result
    reviewed_hash = sha256_file(reviewed)
    expected_hash = str(report.get("output_sha256", ""))
    if not expected_hash or reviewed_hash != expected_hash:
        result.update(
            {
                "ok": False,
                "reviewed_sha256": reviewed_hash,
                "expected_reviewed_sha256": expected_hash or None,
                "errors": ["reviewed file hash does not match the apply report; refusing report-mismatched rollback"],
            }
        )
        return result
    with zipfile.ZipFile(reviewed, "r") as archive:
        names = set(archive.namelist())
        document_root = etree.fromstring(archive.read("word/document.xml"))
        remove_elements_by_ids(document_root, ids)
        comments = etree.fromstring(archive.read("word/comments.xml"))
        for comment in comments.xpath("//w:comment[@w:id]", namespaces=NS):
            if comment.get(w("id")) in ids:
                comment.getparent().remove(comment)
        remaining_comments = comments.xpath("//w:comment", namespaces=NS)
        overrides = {"word/document.xml": xml_bytes(document_root)}
        remove: set[str] = set()
        if remaining_comments or report.get("source_had_comments_part"):
            overrides["word/comments.xml"] = xml_bytes(comments)
        else:
            remove.add("word/comments.xml")
        rels_name = "word/_rels/document.xml.rels"
        if rels_name in names and not report.get("source_had_comments_relationship") and not remaining_comments:
            rels = etree.fromstring(archive.read(rels_name))
            for relationship in rels.xpath("//pr:Relationship[@Type=$type and @Target='comments.xml']", namespaces=NS, type=COMMENTS_REL_TYPE):
                relationship.getparent().remove(relationship)
            overrides[rels_name] = xml_bytes(rels)
        content_types = etree.fromstring(archive.read("[Content_Types].xml"))
        if not report.get("source_had_comments_content_type") and not remaining_comments:
            for override in content_types.xpath("//ct:Override[@PartName='/word/comments.xml']", namespaces=NS):
                override.getparent().remove(override)
            overrides["[Content_Types].xml"] = xml_bytes(content_types)
        write_docx(archive, output, overrides, remove)
    with zipfile.ZipFile(output) as archive:
        output_document = etree.fromstring(archive.read("word/document.xml"))
        output_visible_hash = visible_text_hash(output_document)
        bad_member = archive.testzip()
    result.update(
        {
            "output_visible_text_sha256": output_visible_hash,
            "visible_text_matches_source": output_visible_hash == report.get("source_visible_text_sha256"),
            "reviewed_sha256": reviewed_hash,
            "reviewed_hash_matches_report": True,
            "zip_ok": bad_member is None,
            "output_sha256": sha256_file(output),
        }
    )
    result["ok"] = bool(result["visible_text_matches_source"] and result["zip_ok"])
    return result


def write_report(path: Path | None, report: dict[str, object]) -> None:
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply_parser = subparsers.add_parser("apply", help="Apply a CSV comment plan to a separate DOCX output.")
    apply_parser.add_argument("source", type=Path)
    apply_parser.add_argument("plan", type=Path)
    apply_parser.add_argument("--output", required=True, type=Path)
    apply_parser.add_argument("--report", type=Path)
    apply_parser.add_argument("--author", default="Codex")
    apply_parser.add_argument("--initials", default="CX")
    apply_parser.add_argument("--allow-partial", action="store_true")
    apply_parser.add_argument("--allow-ambiguous", action="store_true")
    rollback_parser = subparsers.add_parser("rollback", help="Remove only comments listed in a prior apply report.")
    rollback_parser.add_argument("reviewed", type=Path)
    rollback_parser.add_argument("report", type=Path)
    rollback_parser.add_argument("--output", required=True, type=Path)
    rollback_parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "apply":
            result = apply_comments(
                args.source.expanduser(),
                args.plan.expanduser(),
                args.output.expanduser(),
                author=args.author,
                initials=args.initials,
                allow_partial=args.allow_partial,
                allow_ambiguous=args.allow_ambiguous,
            )
            write_report(args.report, result)
        else:
            result = rollback_comments(args.reviewed.expanduser(), args.report.expanduser(), args.output.expanduser())
            write_report(args.result, result)
    except (OSError, csv.Error, zipfile.BadZipFile, etree.XMLSyntaxError, json.JSONDecodeError) as exc:
        print(f"Comment operation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
