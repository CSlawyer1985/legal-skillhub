#!/usr/bin/env python3
"""Extract review-ready text or tracked changes from transaction documents."""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
REVISION_TYPES = {
    "ins": "inserted",
    "del": "deleted",
    "moveFrom": "moved_from",
    "moveTo": "moved_to",
}
STORY_PART_PATTERN = re.compile(r"^word/(?:document|footnotes|endnotes|header\d+|footer\d+)\.xml$")


def _local_tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _w_attr(element: ET.Element, name: str) -> str | None:
    return element.get(f"{{{W_NS}}}{name}")


def _text_view(element: ET.Element, view: str = "all") -> str:
    tag = _local_tag(element)
    if view == "after" and tag in {"del", "moveFrom"}:
        return ""
    if view == "before" and tag in {"ins", "moveTo"}:
        return ""
    if tag in {"t", "delText"}:
        return element.text or ""
    if tag == "tab":
        return "\t"
    if tag in {"br", "cr"}:
        return "\n"
    return "".join(_text_view(child, view) for child in element)


def _text_from_element(element: ET.Element) -> str:
    return _text_view(element, "all")


def _para_text(paragraph: ET.Element, include_deleted: bool = False) -> str:
    view = "all" if include_deleted else "after"
    return _text_view(paragraph, view).strip()


def _join_change_parts(parts: list[str]) -> str:
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _story_parts(zf: zipfile.ZipFile) -> list[str]:
    parts = [name for name in zf.namelist() if STORY_PART_PATTERN.match(name)]
    return sorted(parts, key=lambda name: (name != "word/document.xml", name))


def _error(path: Path, scope: str, message: str) -> dict:
    return {"file": str(path), "scope": scope, "error": message}


def _add_warning(result: dict, message: str) -> None:
    warnings = result.setdefault("warnings", [])
    if message not in warnings:
        warnings.append(message)
    result["warning"] = " ".join(warnings)


def extract_docx(path: Path, scope: str, high_volume_threshold: int = 500) -> dict:
    try:
        with zipfile.ZipFile(path) as zf:
            part_names = _story_parts(zf)
            if "word/document.xml" not in part_names:
                return _error(path, scope, "DOCX is missing word/document.xml")
            roots: list[tuple[str, ET.Element]] = []
            for part_name in part_names:
                try:
                    roots.append((part_name, ET.fromstring(zf.read(part_name))))
                except (KeyError, ET.ParseError) as exc:
                    return _error(path, scope, f"Could not parse {part_name}: {exc}")
    except (OSError, zipfile.BadZipFile) as exc:
        return _error(path, scope, f"DOCX could not be opened: {exc}")

    if scope == "track-changes":
        changes: list[dict] = []
        changed_paragraphs: list[dict] = []
        revision_marker_count = 0
        global_index = 0
        for part_name, root in roots:
            for part_index, paragraph in enumerate(root.findall(".//w:p", NS), start=1):
                global_index += 1
                revisions = [node for node in paragraph.iter() if _local_tag(node) in REVISION_TYPES]
                revision_marker_count += len(revisions)
                if not revisions:
                    continue

                grouped = {"inserted": [], "deleted": [], "moved_from": [], "moved_to": []}
                authors: list[str] = []
                dates: list[str] = []
                text_change_count = 0
                for revision in revisions:
                    revision_type = REVISION_TYPES[_local_tag(revision)]
                    text = _text_from_element(revision).strip()
                    author = _w_attr(revision, "author")
                    date = _w_attr(revision, "date")
                    revision_id = _w_attr(revision, "id")
                    if author and author not in authors:
                        authors.append(author)
                    if date and date not in dates:
                        dates.append(date)
                    if not text:
                        continue
                    text_change_count += 1
                    grouped[revision_type].append(text)
                    changes.append({
                        "paragraph": global_index,
                        "part_paragraph": part_index,
                        "source_part": part_name,
                        "type": revision_type,
                        "text": text,
                        "author": author,
                        "date": date,
                        "revision_id": revision_id,
                    })

                if text_change_count:
                    before_text = _text_view(paragraph, "before").strip()
                    after_text = _text_view(paragraph, "after").strip()
                    changed_paragraphs.append({
                        "paragraph": global_index,
                        "part_paragraph": part_index,
                        "source_part": part_name,
                        "before_text": before_text,
                        "after_text": after_text,
                        "inserted_text": _join_change_parts(grouped["inserted"]),
                        "deleted_text": _join_change_parts(grouped["deleted"]),
                        "moved_from_text": _join_change_parts(grouped["moved_from"]),
                        "moved_to_text": _join_change_parts(grouped["moved_to"]),
                        "context": after_text or _text_view(paragraph, "all").strip(),
                        "authors": authors,
                        "dates": dates,
                        "revision_marker_count": len(revisions),
                        "text_change_count": text_change_count,
                    })

        result = {
            "file": str(path),
            "scope": scope,
            "docx_parts": part_names,
            "track_changes_present": revision_marker_count > 0,
            "revision_marker_count": revision_marker_count,
            "changes": changes,
            "change_count": len(changes),
            "raw_change_count": len(changes),
            "changed_paragraphs": changed_paragraphs,
            "changed_paragraph_count": len(changed_paragraphs),
        }
        if revision_marker_count and not changes:
            _add_warning(
                result,
                "Revision markers are present, but no substantive text-bearing changes were detected; compare against a prior draft or run a full review.",
            )
        if high_volume_threshold >= 0 and len(changed_paragraphs) > high_volume_threshold:
            _add_warning(
                result,
                "High-volume Track Changes detected; use staged review, filter by core clauses, or confirm whether a full redline review is needed.",
            )
        return result

    paragraphs: list[dict] = []
    global_index = 0
    for part_name, root in roots:
        for part_index, paragraph in enumerate(root.findall(".//w:p", NS), start=1):
            global_index += 1
            text = _para_text(paragraph)
            if text:
                paragraphs.append({
                    "paragraph": global_index,
                    "part_paragraph": part_index,
                    "source_part": part_name,
                    "text": text,
                })
    return {
        "file": str(path),
        "scope": scope,
        "method": "docx-ooxml",
        "docx_parts": part_names,
        "paragraphs": paragraphs,
        "paragraph_count": len(paragraphs),
        "text_char_count": sum(len(item["text"]) for item in paragraphs),
    }


def _paragraphs_from_pages(pages: list[str]) -> list[dict]:
    paragraphs: list[dict] = []
    index = 0
    for page_number, page_text in enumerate(pages, start=1):
        blocks = [block.strip() for block in re.split(r"\n\s*\n", page_text) if block.strip()]
        for block_number, block in enumerate(blocks, start=1):
            index += 1
            paragraphs.append({
                "paragraph": index,
                "page": page_number,
                "page_block": block_number,
                "text": block,
            })
    return paragraphs


def _pdftotext_pages(path: Path, executable: str) -> tuple[list[str], str | None]:
    proc = subprocess.run(
        [executable, "-layout", str(path), "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return [], proc.stderr.strip() or f"pdftotext exited with {proc.returncode}"
    if not proc.stdout.strip():
        return [], None
    pages = proc.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages or [proc.stdout], None


def extract_pdf(path: Path) -> dict:
    errors: list[str] = []
    pages: list[str] = []
    method = ""
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        pages, error = _pdftotext_pages(path, pdftotext)
        if error:
            errors.append(error)
        if pages:
            method = "pdftotext"

    if not pages:
        try:
            logging.getLogger("pypdf").setLevel(logging.ERROR)
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            pages = [(page.extract_text() or "") for page in reader.pages]
            method = "pypdf"
        except Exception as exc:  # pragma: no cover - environment dependent
            errors.append(str(exc))
            return _error(path, "full", f"PDF text extraction failed; use OCR or manual review: {'; '.join(errors)}")

    paragraphs = _paragraphs_from_pages(pages)
    result = {
        "file": str(path),
        "scope": "full",
        "method": method,
        "page_count": len(pages),
        "paragraphs": paragraphs,
        "paragraph_count": len(paragraphs),
        "text_char_count": sum(len(item["text"]) for item in paragraphs),
    }
    if not paragraphs:
        _add_warning(
            result,
            "No text extracted; this may be a scanned or image-only PDF. Run scripts/ocr_pdf.py or perform manual/OCR review.",
        )
    return result


def _paragraphs_from_text(text: str) -> list[dict]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    return [{"paragraph": index, "text": block} for index, block in enumerate(blocks, start=1)]


def extract_doc_or_other(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            return _error(path, "full", f"plain-text extraction failed: {exc}")
        paragraphs = _paragraphs_from_text(text)
        return {
            "file": str(path),
            "scope": "full",
            "method": "plain-text",
            "paragraphs": paragraphs,
            "paragraph_count": len(paragraphs),
            "text_char_count": sum(len(item["text"]) for item in paragraphs),
        }

    textutil = shutil.which("textutil")
    if textutil and suffix in {".doc", ".rtf"}:
        proc = subprocess.run(
            [textutil, "-convert", "txt", "-stdout", str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            paragraphs = _paragraphs_from_text(proc.stdout)
            return {
                "file": str(path),
                "scope": "full",
                "method": "textutil",
                "paragraphs": paragraphs,
                "paragraph_count": len(paragraphs),
                "text_char_count": sum(len(item["text"]) for item in paragraphs),
            }
        return _error(path, "full", proc.stderr.strip() or "textutil failed")
    return _error(path, "full", f"unsupported file type: {path.suffix}")


def print_text(result: dict) -> None:
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}", file=sys.stderr)
    if "changed_paragraphs" in result:
        for item in result["changed_paragraphs"]:
            print(
                f"[{item['source_part']} p{item['part_paragraph']}] "
                f"before: {item['before_text'] or '-'} | after: {item['after_text'] or '-'}"
            )
        return
    for paragraph in result.get("paragraphs", []):
        location = f"page {paragraph['page']} " if paragraph.get("page") else ""
        print(f"[{location}p{paragraph['paragraph']}] {paragraph['text']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path)
    ap.add_argument("--scope", choices=["full", "track-changes"], default="full")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    ap.add_argument("--high-volume-threshold", type=int, default=500)
    args = ap.parse_args()

    if args.high_volume_threshold < 0:
        print("--high-volume-threshold must be zero or greater", file=sys.stderr)
        return 2
    path = args.file.expanduser()
    if not path.is_file():
        print(f"file not found or not a regular file: {path}", file=sys.stderr)
        return 2

    try:
        suffix = path.suffix.lower()
        if suffix == ".docx":
            result = extract_docx(path, args.scope, args.high_volume_threshold)
        elif suffix == ".pdf":
            result = extract_pdf(path)
            if args.scope == "track-changes":
                _add_warning(result, "PDF Track Changes cannot be structurally extracted; inspect the redline manually or compare versions.")
        else:
            result = extract_doc_or_other(path)
            if args.scope == "track-changes":
                _add_warning(result, f"{suffix or 'This file type'} does not expose structural Track Changes; compare versions instead.")
    except Exception as exc:  # defensive CLI boundary
        result = _error(path, args.scope, f"Unexpected extraction failure: {exc}")

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    if result.get("error"):
        return 1
    if args.scope == "full" and not result.get("paragraph_count"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
