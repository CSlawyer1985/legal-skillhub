#!/usr/bin/env python3
"""本地接入案件材料，生成可追溯索引并回写案件状态。

本脚本只做确定性文件处理：不改动原件，不调用云端服务，不把 OCR
结果当作已证事实。PDF 文本层提取优先使用本机 ``pdftotext``；工具缺失
或文本层不足时只登记 OCR 待处理状态，由运行环境另行完成 OCR。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from case_state import read_json, validate_state, write_state
from xml_safe import UnsafeXMLError, fromstring as safe_fromstring


TEXT_SUFFIXES = {
    ".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".log",
    ".rtf", ".yaml", ".yml",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp", ".heic"}
MIN_PDF_PAGE_TEXT_CHARS = 20
SAFE_MATERIAL_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
MAX_LOCAL_TEXT_BYTES = 32 * 1024 * 1024
MAX_PDF_FALLBACK_BYTES = 64 * 1024 * 1024
MAX_PDF_TEXT_OUTPUT_BYTES = 64 * 1024 * 1024


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def normalized_text(text: str) -> str:
    return text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def decode_text_file(path: Path) -> tuple[str | None, str | None]:
    if path.stat().st_size > MAX_LOCAL_TEXT_BYTES:
        return None, None
    raw = path.read_bytes()
    if b"\x00" in raw[:8192]:
        return None, None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return normalized_text(raw.decode(encoding)), encoding
        except UnicodeDecodeError:
            continue
    return None, None


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            document = archive.read("word/document.xml")
        root = safe_fromstring(document)
    except (KeyError, OSError, zipfile.BadZipFile, ElementTree.ParseError, UnsafeXMLError) as exc:
        fail(f"DOCX 无法读取：{path}：{exc}")
    lines: list[str] = []
    for paragraph in root.iter():
        if paragraph.tag.endswith("}p"):
            text = "".join(
                node.text or ""
                for node in paragraph.iter()
                if node.tag.endswith("}t")
            ).strip()
            if text:
                lines.append(text)
    return normalized_text("\n".join(lines))


def pdf_page_count(path: Path) -> int | None:
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        result = subprocess.run(
            [pdfinfo, str(path)], capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            match = re.search(r"^Pages:\s*(\d+)\s*$", result.stdout, re.MULTILINE)
            if match:
                return int(match.group(1))
    try:
        if path.stat().st_size > MAX_PDF_FALLBACK_BYTES:
            return None
        raw = path.read_bytes()
    except OSError:
        return None
    count = len(re.findall(rb"/Type\s*/Page(?!s)\b", raw))
    return count or None


def extract_pdf_text(path: Path, target: Path) -> tuple[str | None, str]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return None, "pdftotext_unavailable"
    result = subprocess.run(
        [pdftotext, "-layout", "-enc", "UTF-8", str(path), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not target.is_file():
        return None, "pdftotext_failed"
    if target.stat().st_size > MAX_PDF_TEXT_OUTPUT_BYTES:
        return None, "pdftotext_output_too_large"
    try:
        text = normalized_text(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None, "pdftotext_invalid_output"
    return text, "pdftotext"


def meaningful_char_count(text: str | None) -> int:
    if not text:
        return 0
    return len(re.sub(r"\s+", "", text))


def pdf_text_layer_status(text: str | None, page_count: int | None) -> tuple[str, int]:
    if not text:
        return "none", 0
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    text_page_count = sum(meaningful_char_count(page) >= MIN_PDF_PAGE_TEXT_CHARS for page in pages)
    expected_pages = page_count or len(pages)
    if expected_pages > 0 and text_page_count >= expected_pages:
        return "complete", text_page_count
    if meaningful_char_count(text) > 0:
        return "partial", text_page_count
    return "none", 0


def build_page_index(
    text: str | None,
    page_count: int | None,
    file_kind: str,
) -> list[dict[str, Any]]:
    """生成不含页面正文的逐页索引。"""
    if page_count is None:
        return []
    if page_count < 1:
        raise ValueError("page_count 必须大于等于 1。")

    page_texts: list[str] = []
    if file_kind == "pdf" and text is not None:
        page_texts = text.split("\f")
        if len(page_texts) > page_count and not page_texts[-1].strip():
            page_texts.pop()
    elif file_kind == "text" and text is not None:
        page_texts = [text]

    index: list[dict[str, Any]] = []
    for page_number in range(1, page_count + 1):
        page_text = page_texts[page_number - 1] if page_number <= len(page_texts) else None
        character_count = meaningful_char_count(page_text)
        if file_kind in {"pdf", "text"}:
            if character_count >= MIN_PDF_PAGE_TEXT_CHARS or (
                file_kind == "text" and character_count > 0
            ):
                text_status = "complete"
            elif character_count > 0:
                text_status = "partial"
            else:
                text_status = "none"
        elif file_kind == "image":
            text_status = "none"
        else:
            text_status = "unknown"
        index.append({
            "page_number": page_number,
            "text_layer_status": text_status,
            "extracted_char_count": character_count,
            "ocr_status": (
                "pending"
                if file_kind in {"pdf", "image"} and text_status != "complete"
                else "not_needed"
            ),
        })
    return index


def material_id_for(path: Path, digest: str) -> str:
    identity = hashlib.sha256(f"{path}\0{digest}".encode("utf-8")).hexdigest()[:16]
    return f"material-{identity}"


def casework_root(state_path: Path) -> Path:
    return state_path.parent if state_path.parent.name == ".casework" else state_path.parent / ".casework"


def inspect_source(
    source: Path,
    staging_root: Path,
    *,
    original_or_copy: str,
    ocr_language: str,
) -> tuple[dict[str, Any], Path]:
    source_stat_before = source.stat()
    digest = sha256_file(source)
    material_id = material_id_for(source, digest)
    if not SAFE_MATERIAL_ID.fullmatch(material_id):
        fail(f"材料 ID 含不安全字符，拒绝写入派生目录：{material_id}")
    stage_dir = staging_root / material_id
    stage_dir.mkdir(parents=True, exist_ok=False)
    derivative_stage = stage_dir / "text.txt"
    suffix = source.suffix.casefold()
    media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    text: str | None = None
    text_encoding: str | None = None
    page_count: int | None = 1
    file_kind = "binary"
    ingestion_method = "metadata_only"

    if suffix == ".pdf":
        file_kind = "pdf"
        page_count = pdf_page_count(source)
        text, ingestion_method = extract_pdf_text(source, derivative_stage)
    elif suffix == ".docx":
        file_kind = "document"
        page_count = None
        text = extract_docx_text(source)
        text_encoding = "docx-xml"
        ingestion_method = "docx_xml"
    elif suffix in IMAGE_SUFFIXES or media_type.startswith("image/"):
        file_kind = "image"
        page_count = 1
    elif suffix in TEXT_SUFFIXES or media_type.startswith("text/"):
        file_kind = "text"
        text, text_encoding = decode_text_file(source)
        ingestion_method = "local_text_decode" if text is not None else "metadata_only"
    else:
        candidate, encoding = decode_text_file(source)
        if candidate is not None:
            file_kind = "text"
            text, text_encoding = candidate, encoding
            ingestion_method = "local_text_decode"

    char_count = meaningful_char_count(text)
    source_stat_after = source.stat()
    digest_after = sha256_file(source)
    if (
        source_stat_before.st_size != source_stat_after.st_size
        or source_stat_before.st_mtime_ns != source_stat_after.st_mtime_ns
        or digest_after != digest
    ):
        fail(f"材料在接入过程中发生变化，请确认原件稳定后重试：{source}")
    text_page_count: int | None = None
    if file_kind in {"text", "document"}:
        text_layer_status = "complete" if text is not None else "unknown"
    elif file_kind == "pdf":
        text_layer_status, text_page_count = pdf_text_layer_status(text, page_count)
    elif file_kind == "image":
        text_layer_status = "none"
    else:
        text_layer_status = "unknown"
    needs_ocr = file_kind in {"image", "pdf"} and text_layer_status != "complete"
    ocr_status = "pending" if needs_ocr else "not_needed"
    page_index = build_page_index(text, page_count, file_kind)

    if text is not None and not derivative_stage.exists():
        derivative_stage.write_text(text, encoding="utf-8")
    if derivative_stage.exists() and char_count == 0:
        derivative_stage.unlink()

    record_stage = stage_dir / "record.json"
    ingested_at = now_iso()
    record: dict[str, Any] = {
        "material_id": material_id,
        "file_name": source.name,
        "source_path": str(source),
        "source_sha256": digest,
        "source_size_bytes": source_stat_after.st_size,
        "source_mtime_ns": source_stat_after.st_mtime_ns,
        "media_type": media_type,
        "file_kind": file_kind,
        "page_count": page_count,
        "page_start": 1,
        "page_end": page_count,
        "page_index": page_index,
        "text_layer_status": text_layer_status,
        "text_page_count": text_page_count,
        "extracted_char_count": char_count,
        "text_encoding": text_encoding,
        "derivative_path": None,
        "ocr_engine": None,
        "ocr_language": ocr_language if needs_ocr else None,
        "ocr_status": ocr_status,
        "visual_review_status": "not_started",
        "original_or_copy": original_or_copy,
        "ingestion_method": ingestion_method,
        "ingested_at": ingested_at,
        "ingestion_record_path": None,
    }
    record_stage.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record, stage_dir


def render_index(materials: list[dict[str, Any]], generated_at: str) -> tuple[str, str]:
    payload = {"generated_at": generated_at, "material_count": len(materials), "materials": materials}
    markdown = [
        "# 材料接入索引", "", f"> 生成时间：{generated_at}", "",
        "| 材料 ID | 文件名 | 类型 | 页数 | 文字层 | OCR 状态 | 可视复核 | SHA-256 |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for item in materials:
        markdown.append(
            "| {material_id} | {file_name} | {file_kind} | {page_count} | "
            "{text_layer_status} | {ocr_status} | {visual_review_status} | {digest} |".format(
                material_id=item.get("material_id", ""),
                file_name=str(item.get("file_name", "")).replace("|", "\\|"),
                file_kind=item.get("file_kind", ""),
                page_count=item.get("page_count") or "—",
                text_layer_status=item.get("text_layer_status", ""),
                ocr_status=item.get("ocr_status", ""),
                visual_review_status=item.get("visual_review_status", ""),
                digest=str(item.get("source_sha256", ""))[:16] + "…",
            )
        )
    markdown.extend([
        "", "## 分页索引", "",
        "| 材料 ID | 页码 | 文字层 | OCR 状态 | 可提取字符数 |",
        "|---|---:|---|---|---:|",
    ])
    for item in materials:
        for page in item.get("page_index", []):
            markdown.append(
                "| {material_id} | {page_number} | {text_status} | {ocr_status} | {char_count} |".format(
                    material_id=item.get("material_id", ""),
                    page_number=page.get("page_number", ""),
                    text_status=page.get("text_layer_status", ""),
                    ocr_status=page.get("ocr_status", ""),
                    char_count=page.get("extracted_char_count", ""),
                )
            )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "\n".join(markdown) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="LaborPilot 本地材料接入执行器")
    parser.add_argument("--state", required=True, help=".casework/case_state.json")
    parser.add_argument("--source", action="append", required=True, help="原始材料路径，可重复")
    parser.add_argument("--original-or-copy", choices=["original", "copy", "unknown"], default="unknown")
    parser.add_argument("--ocr-language", default="chi_sim+eng")
    parser.add_argument("--actor", default="labor-material-ingestion")
    args = parser.parse_args()

    state_path = Path(args.state).expanduser().resolve()
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        fail("案件状态无效：\n" + "\n".join(errors))
    if state.get("current_node") != "material_ingestion":
        fail(f"当前节点为 {state.get('current_node')}，不能执行材料接入。")

    sources: list[Path] = []
    seen_sources: set[Path] = set()
    for value in args.source:
        source = Path(value).expanduser().resolve()
        if not source.is_file():
            fail(f"材料不是可读取文件：{source}")
        if source == state_path or ".casework" in source.parts:
            fail(f"拒绝把案件内部状态或派生文件作为原始材料接入：{source}")
        if source not in seen_sources:
            sources.append(source)
            seen_sources.add(source)

    internal_root = casework_root(state_path)
    materials_root = internal_root / "materials"
    materials_root.mkdir(parents=True, exist_ok=True)
    existing_by_identity = {
        (str(Path(str(item.get("source_path", ""))).expanduser().resolve()), item.get("source_sha256")): item
        for item in state.get("materials", [])
        if isinstance(item, dict) and item.get("source_path") and item.get("source_sha256")
    }
    new_records: list[dict[str, Any]] = []
    repaired_ids: set[str] = set()
    staged: list[tuple[dict[str, Any], Path]] = []
    with tempfile.TemporaryDirectory(prefix=".ingest-", dir=materials_root) as temporary:
        staging_root = Path(temporary)
        for source in sources:
            record, stage_dir = inspect_source(
                source,
                staging_root,
                original_or_copy=args.original_or_copy,
                ocr_language=args.ocr_language,
            )
            existing = existing_by_identity.get((str(source), record["source_sha256"]))
            if isinstance(existing, dict):
                existing_id = str(existing.get("material_id", ""))
                if not SAFE_MATERIAL_ID.fullmatch(existing_id):
                    fail(f"既有材料 ID 含不安全字符，拒绝修复：{existing_id}")
                refreshed = dict(existing)
                refreshed.update(record)
                record = refreshed
                record["material_id"] = existing_id
                if args.original_or_copy == "unknown" and existing.get("original_or_copy") in {"original", "copy"}:
                    record["original_or_copy"] = existing["original_or_copy"]
                if existing.get("visual_review_status") in {"sampled", "critical_pages_reviewed", "completed"}:
                    record["visual_review_status"] = existing["visual_review_status"]
                existing_derivative = existing.get("derivative_path")
                if (
                    existing.get("ocr_status") in {"partial", "completed"}
                    and isinstance(existing_derivative, str)
                    and Path(existing_derivative).expanduser().is_file()
                ):
                    record["derivative_path"] = existing_derivative
                    record["ocr_engine"] = existing.get("ocr_engine")
                    record["ocr_language"] = existing.get("ocr_language")
                    record["ocr_status"] = existing.get("ocr_status")
                    existing_page_index = existing.get("page_index")
                    if isinstance(existing_page_index, list) and existing_page_index:
                        record["page_index"] = existing_page_index
                    # ``text.txt`` 可能就是外部 OCR 工具写入的派生件。
                    # 重新接入只刷新元数据，不用 pdftotext 结果覆盖它。
                    derivative_stage = stage_dir / "text.txt"
                    if derivative_stage.is_file():
                        derivative_stage.unlink()
                record["first_ingested_at"] = existing.get("first_ingested_at") or existing.get("ingested_at")
                record["reindexed_at"] = record["ingested_at"]
            final_dir = materials_root / record["material_id"]
            derivative_stage = stage_dir / "text.txt"
            record_stage = stage_dir / "record.json"
            if derivative_stage.is_file() and record.get("ocr_status") not in {"partial", "completed"}:
                record["derivative_path"] = str(final_dir / "text.txt")
            record["ingestion_record_path"] = str(final_dir / "record.json")
            record_stage.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            staged.append((record, stage_dir))

        candidate_state = json.loads(json.dumps(state, ensure_ascii=False))
        for record, _ in staged:
            replaced = False
            for index, existing in enumerate(candidate_state.get("materials", [])):
                if isinstance(existing, dict) and existing.get("material_id") == record["material_id"]:
                    candidate_state["materials"][index] = record
                    repaired_ids.add(record["material_id"])
                    replaced = True
                    break
            if not replaced:
                candidate_state.setdefault("materials", []).append(record)
                new_records.append(record)
        candidate_state.setdefault("events", []).append({
            "event_id": f"evt-{uuid.uuid4().hex[:12]}",
            "event_type": "materials_ingested",
            "actor": args.actor,
            "occurred_at": now_iso(),
            "details": {
                "material_ids": [record["material_id"] for record, _ in staged],
                "new_count": len(new_records),
                "repaired_count": len(repaired_ids),
            },
        })
        errors = validate_state(candidate_state)
        if errors:
            fail("材料接入后的案件状态无效：\n" + "\n".join(errors))

        for record, stage_dir in staged:
            final_dir = materials_root / record["material_id"]
            if final_dir.exists():
                # 修复既有登记时只原子更新本执行器负责的文件，保留后续人工
                # 复核、OCR 或其他工具写入同一材料目录的产物。
                for child in stage_dir.iterdir():
                    os.replace(child, final_dir / child.name)
                stage_dir.rmdir()
            else:
                os.replace(stage_dir, final_dir)

        generated_at = now_iso()
        index_json, index_markdown = render_index(candidate_state["materials"], generated_at)
        atomic_write_text(materials_root / "index.json", index_json)
        atomic_write_text(materials_root / "index.md", index_markdown)
        write_state(state_path, candidate_state, source=state_path, operation="materials-ingested")

    print(json.dumps({
        "status": "ok",
        "material_count": len(staged),
        "new_count": len(new_records),
        "repaired_count": len(repaired_ids),
        "ocr_pending": sum(record.get("ocr_status") == "pending" for record, _ in staged),
        "index": str(materials_root / "index.json"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
