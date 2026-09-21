#!/usr/bin/env python3
"""Strict, evidence-producing OOXML quality gate for reviewed DOCX files."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET

try:
    from .revision_views import REVISION_TAGS, create_revision_view
except ImportError:
    from revision_views import REVISION_TAGS, create_revision_view


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_PART_SUFFIXES = (".xml", ".rels")
REQUIRED_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/_rels/document.xml.rels",
}
STORY_PATTERN = re.compile(
    r"^word/(document|header\d+|footer\d+|footnotes|endnotes)\.xml$"
)
ENCODING_RE = re.compile(br"<\?xml[^>]*encoding=[\"']([^\"']+)[\"']", re.I)
VISUAL_POLICIES = {"require", "allow-structural", "structural-only"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _attribute(element, local_name: str) -> str | None:
    for key, value in element.attrib.items():
        if _local_name(key) == local_name:
            return value
    return None


def _relationship_source(rels_name: str) -> str:
    if rels_name == "_rels/.rels":
        return ""
    directory, filename = posixpath.split(rels_name)
    if posixpath.basename(directory) != "_rels" or not filename.endswith(".rels"):
        raise ValueError(f"invalid relationship part path: {rels_name}")
    source_dir = posixpath.dirname(directory)
    source_name = filename[: -len(".rels")]
    return posixpath.join(source_dir, source_name)


def _resolve_target(rels_name: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    source = _relationship_source(rels_name)
    base = posixpath.dirname(source)
    return posixpath.normpath(posixpath.join(base, target))


def _normalize_semantic_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _read_story_text(docx_path: Path) -> str:
    paragraphs: list[str] = []
    with zipfile.ZipFile(docx_path, "r") as archive:
        for name in sorted(archive.namelist()):
            if not STORY_PATTERN.match(name):
                continue
            root = ET.fromstring(archive.read(name))
            for paragraph in root.iter(f"{{{W}}}p"):
                parts = []
                for node in paragraph.iter():
                    if node.tag in {f"{{{W}}}t", f"{{{W}}}tab"}:
                        parts.append("\t" if node.tag.endswith("}tab") else (node.text or ""))
                paragraphs.append("".join(parts))
    return _normalize_semantic_text("\n".join(paragraphs))


def _view_text(docx_path: Path, mode: str) -> str:
    if mode == "raw":
        return _read_story_text(docx_path)
    with tempfile.TemporaryDirectory(prefix=f"baseline-{mode}-") as temp_dir:
        view = Path(temp_dir) / f"{mode}.docx"
        create_revision_view(docx_path, view, mode)
        return _read_story_text(view)


def inspect_docx(docx_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {
        "xml_part_count": 0,
        "relationship_count": 0,
        "revision_count": 0,
        "comment_count": 0,
    }
    parsed: dict[str, Any] = {}

    try:
        with zipfile.ZipFile(docx_path, "r") as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
            if duplicates:
                errors.append(f"ZIP 包含重复部件: {duplicates}")
            corrupt = archive.testzip()
            if corrupt:
                errors.append(f"ZIP CRC 校验失败: {corrupt}")
            name_set = set(names)
            missing = sorted(REQUIRED_PARTS - name_set)
            if missing:
                errors.append(f"缺少必需部件: {missing}")

            for name in names:
                if not name.endswith(XML_PART_SUFFIXES):
                    continue
                metrics["xml_part_count"] += 1
                data = archive.read(name)
                match = ENCODING_RE.search(data[:256])
                if match and match.group(1).decode("ascii", errors="replace").lower() not in {
                    "utf-8",
                    "utf8",
                    "utf-16",
                    "utf16",
                }:
                    errors.append(
                        f"{name} 使用不兼容 XML 编码声明: "
                        f"{match.group(1).decode('ascii', errors='replace')}"
                    )
                try:
                    parsed[name] = ET.fromstring(data)
                except Exception as exc:
                    errors.append(f"{name} XML 解析失败: {exc}")

            for name, root in parsed.items():
                if not name.endswith(".rels"):
                    continue
                ids = []
                for rel in root:
                    if _local_name(rel.tag) != "Relationship":
                        continue
                    metrics["relationship_count"] += 1
                    rel_id = rel.attrib.get("Id")
                    if not rel_id:
                        errors.append(f"{name} 存在无 Id 的 Relationship")
                    else:
                        ids.append(rel_id)
                    if rel.attrib.get("TargetMode", "").lower() == "external":
                        continue
                    target = rel.attrib.get("Target")
                    if not target:
                        errors.append(f"{name} 的 {rel_id or '<unknown>'} 缺少 Target")
                        continue
                    resolved = _resolve_target(name, target)
                    if resolved.startswith("../") or resolved not in name_set:
                        errors.append(
                            f"{name} 的 {rel_id or '<unknown>'} 指向不存在部件: {target}"
                        )
                duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
                if duplicate_ids:
                    errors.append(f"{name} 包含重复 Relationship Id: {duplicate_ids}")

            revision_ids: list[str] = []
            for name, root in parsed.items():
                if not STORY_PATTERN.match(name):
                    continue
                for element in root.iter():
                    qualified = f"w:{_local_name(element.tag)}"
                    if qualified not in REVISION_TAGS:
                        continue
                    metrics["revision_count"] += 1
                    if qualified in {"w:ins", "w:del", "w:moveFrom", "w:moveTo"}:
                        change_id = _attribute(element, "id")
                        revision_ids.append(change_id or "")
                        if not change_id:
                            errors.append(f"{name} 的 {qualified} 缺少 w:id")
                        if not _attribute(element, "author"):
                            errors.append(f"{name} 的 {qualified} 缺少 w:author")
                        if not _attribute(element, "date"):
                            errors.append(f"{name} 的 {qualified} 缺少 w:date")
            duplicate_revision_ids = sorted(
                item for item, count in Counter(revision_ids).items() if item and count > 1
            )
            if duplicate_revision_ids:
                warnings.append(f"修订 Id 重复（可能来自历史修订）: {duplicate_revision_ids}")

            comments_root = parsed.get("word/comments.xml")
            comment_ids: list[str] = []
            if comments_root is not None:
                for comment in comments_root.iter(f"{{{W}}}comment"):
                    comment_id = _attribute(comment, "id")
                    if comment_id is None:
                        errors.append("comments.xml 存在无 w:id 的 comment")
                    else:
                        comment_ids.append(comment_id)
                metrics["comment_count"] = len(comment_ids)
                duplicates = sorted(
                    item for item, count in Counter(comment_ids).items() if count > 1
                )
                if duplicates:
                    errors.append(f"comments.xml 包含重复 comment Id: {duplicates}")

            anchor_counts = {
                "commentRangeStart": Counter(),
                "commentRangeEnd": Counter(),
                "commentReference": Counter(),
            }
            for name, root in parsed.items():
                if not STORY_PATTERN.match(name):
                    continue
                for kind in anchor_counts:
                    for element in root.iter(f"{{{W}}}{kind}"):
                        anchor_counts[kind][_attribute(element, "id") or ""] += 1
            known = set(comment_ids)
            anchored = set().union(*(set(counter) - {""} for counter in anchor_counts.values()))
            for comment_id in sorted(known):
                counts = {kind: counter[comment_id] for kind, counter in anchor_counts.items()}
                if not all(counts.values()) or len(set(counts.values())) != 1:
                    errors.append(f"批注 {comment_id} 锚点不闭合: {counts}")
            dangling = sorted(anchored - known)
            if dangling:
                errors.append(f"正文存在无对应 comment 的批注锚点: {dangling}")

            if comments_root is not None:
                rels_root = parsed.get("word/_rels/document.xml.rels")
                has_comments_rel = False
                if rels_root is not None:
                    for rel in rels_root:
                        if rel.attrib.get("Type", "").endswith("/comments"):
                            has_comments_rel = _resolve_target(
                                "word/_rels/document.xml.rels", rel.attrib.get("Target", "")
                            ) == "word/comments.xml"
                if not has_comments_rel:
                    errors.append("存在 comments.xml 但 document.xml.rels 缺少 comments 关系")

                types_root = parsed.get("[Content_Types].xml")
                has_comments_type = False
                if types_root is not None:
                    for override in types_root:
                        if (
                            _local_name(override.tag) == "Override"
                            and override.attrib.get("PartName") == "/word/comments.xml"
                        ):
                            has_comments_type = True
                if not has_comments_type:
                    errors.append("存在 comments.xml 但 [Content_Types].xml 缺少对应 Override")
    except zipfile.BadZipFile as exc:
        errors.append(f"不是有效 ZIP/DOCX: {exc}")

    return {
        "path": str(docx_path.resolve()),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def render_docx_evidence(
    docx_path: Path,
    *,
    output_dir: Path,
    visual_policy: str = "allow-structural",
) -> dict[str, Any]:
    """Render DOCX to PDF/PNG and return machine-checkable page evidence.

    This gate proves that LibreOffice can render non-empty pages.  It deliberately
    does not claim that a human/agent has checked overlap, clipping or typography.
    """
    if visual_policy not in VISUAL_POLICIES:
        raise ValueError(f"unsupported visual_policy: {visual_policy}")
    docx_path = Path(docx_path).resolve()
    output_dir = Path(output_dir).resolve()
    commands = {
        "soffice": shutil.which("soffice") or shutil.which("libreoffice"),
        "pdfinfo": shutil.which("pdfinfo"),
        "pdftoppm": shutil.which("pdftoppm"),
    }
    missing = [name for name, path in commands.items() if not path]
    if visual_policy == "structural-only":
        return {
            "status": "STRUCTURAL_ONLY",
            "delivery_level": "structural_validation",
            "visual_final_eligible": False,
            "visual_inspection_status": "not_performed",
            "reason": "visual_policy=structural-only; 未执行渲染，不得冒充视觉终版",
            "commands": commands,
            "errors": [],
            "pages": [],
        }
    if missing:
        status = "FAIL" if visual_policy == "require" else "STRUCTURAL_ONLY"
        errors = [f"缺少渲染命令: {', '.join(missing)}"] if status == "FAIL" else []
        return {
            "status": status,
            "delivery_level": "blocked" if status == "FAIL" else "structural_validation",
            "visual_final_eligible": False,
            "visual_inspection_status": "blocked" if status == "FAIL" else "not_performed",
            "reason": (
                "渲染环境不完整；仅可标注为结构验证版，不得冒充视觉终版"
            ),
            "commands": commands,
            "missing_commands": missing,
            "errors": errors,
            "pages": [],
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    if pdf_path.exists() or list(output_dir.glob(f"{docx_path.stem}-*.png")):
        raise FileExistsError(f"refusing to overwrite render evidence in: {output_dir}")
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="one-contract-lo-") as profile_dir:
        command = [
            str(commands["soffice"]),
            f"-env:UserInstallation={Path(profile_dir).resolve().as_uri()}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(docx_path),
        ]
        completed = subprocess.run(
            command, text=True, capture_output=True, check=False, timeout=60
        )
    if completed.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        errors.append(
            "LibreOffice 渲染失败: "
            + (completed.stderr.strip() or completed.stdout.strip() or f"exit={completed.returncode}")
        )
    pages_expected = 0
    pdfinfo_output = ""
    if not errors:
        info = subprocess.run(
            [str(commands["pdfinfo"]), str(pdf_path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        pdfinfo_output = info.stdout
        match = re.search(r"^Pages:\s*(\d+)\s*$", info.stdout, re.MULTILINE)
        if info.returncode != 0 or not match:
            errors.append("无法读取渲染 PDF 页数")
        else:
            pages_expected = int(match.group(1))
            if pages_expected < 1:
                errors.append("渲染 PDF 页数为 0")
    if not errors:
        images = subprocess.run(
            [
                str(commands["pdftoppm"]), "-png", "-r", "120", str(pdf_path),
                str(output_dir / docx_path.stem),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if images.returncode != 0:
            errors.append(
                "PDF 转 PNG 失败: "
                + (images.stderr.strip() or images.stdout.strip() or f"exit={images.returncode}")
            )
    page_paths = sorted(output_dir.glob(f"{docx_path.stem}-*.png"))
    page_evidence: list[dict[str, Any]] = []
    for page in page_paths:
        dimensions = _png_dimensions(page)
        if dimensions is None or min(dimensions) < 100:
            errors.append(f"PNG 页面无效或尺寸异常: {page.name}")
            continue
        page_evidence.append(
            {
                "path": str(page),
                "bytes": page.stat().st_size,
                "width": dimensions[0],
                "height": dimensions[1],
            }
        )
    if pages_expected and len(page_evidence) != pages_expected:
        errors.append(f"PNG 页数与 PDF 不一致: {len(page_evidence)} != {pages_expected}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "delivery_level": "rendered_evidence_ready" if not errors else "blocked",
        "visual_final_eligible": False,
        "visual_inspection_status": "required" if not errors else "blocked",
        "reason": (
            "已生成逐页渲染证据；仍须人工或视觉代理检查裁切、重叠、缺字和字体替代"
            if not errors
            else "渲染失败，不得对外交付"
        ),
        "commands": commands,
        "pdf": str(pdf_path) if pdf_path.exists() else None,
        "pdf_pages": pages_expected,
        "pdfinfo": pdfinfo_output,
        "pages": page_evidence,
        "errors": errors,
    }


def run_quality_gate(
    reviewed_docx: Path,
    *,
    original_docx: Path,
    output_dir: Path,
    baseline_view: str = "reject",
    require_revisions: bool = False,
    visual_policy: str = "structural-only",
) -> dict[str, Any]:
    reviewed_docx = Path(reviewed_docx)
    original_docx = Path(original_docx)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    accepted = output_dir / f"{reviewed_docx.stem}.accepted.docx"
    rejected = output_dir / f"{reviewed_docx.stem}.rejected.docx"
    report_path = output_dir / "quality-gate.json"
    for path in (accepted, rejected, report_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite quality artifact: {path}")

    accepted_resolution = create_revision_view(reviewed_docx, accepted, "accept")
    rejected_resolution = create_revision_view(reviewed_docx, rejected, "reject")
    package_reports = {
        "reviewed": inspect_docx(reviewed_docx),
        "accepted": inspect_docx(accepted),
        "rejected": inspect_docx(rejected),
    }
    errors = [
        f"{name}: {error}"
        for name, report in package_reports.items()
        for error in report["errors"]
    ]
    if accepted_resolution["revision_count_after"] or rejected_resolution["revision_count_after"]:
        errors.append("接受版或拒绝版仍含修订元素")
    revision_count = package_reports["reviewed"]["metrics"]["revision_count"]
    if require_revisions and not revision_count:
        errors.append("计划要求正文修订，但成品不含修订元素")

    baseline_text = _view_text(original_docx, baseline_view)
    rejected_text = _read_story_text(rejected)
    semantic_baseline_equal = baseline_text == rejected_text
    if not semantic_baseline_equal:
        errors.append("拒绝全部新修订后，正文语义未回到声明的原始基线")

    compatibility: dict[str, str] = {}
    try:
        from docx import Document as PythonDocxDocument

        for name, path in (("reviewed", reviewed_docx), ("accepted", accepted), ("rejected", rejected)):
            PythonDocxDocument(path)
            compatibility[name] = "PASS"
    except Exception as exc:
        compatibility["python-docx"] = f"FAIL: {exc}"
        errors.append(f"python-docx 兼容性检查失败: {exc}")

    visual_validation = {
        name: render_docx_evidence(
            path,
            output_dir=output_dir / "render" / name,
            visual_policy=visual_policy,
        )
        for name, path in (("reviewed", reviewed_docx), ("accepted", accepted), ("rejected", rejected))
    }
    errors.extend(
        f"{name} visual: {error}"
        for name, validation in visual_validation.items()
        if validation.get("status") == "FAIL"
        for error in validation.get("errors", [])
    )
    delivery_level = (
        "blocked"
        if errors
        else (
            "structural_validation"
            if any(item.get("status") == "STRUCTURAL_ONLY" for item in visual_validation.values())
            else "rendered_evidence_ready"
        )
    )

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS" if not errors else "FAIL",
        "reviewed_docx": str(reviewed_docx.resolve()),
        "original_docx": str(original_docx.resolve()),
        "baseline_view": baseline_view,
        "accepted_docx": str(accepted.resolve()),
        "rejected_docx": str(rejected.resolve()),
        "require_revisions": require_revisions,
        "semantic_baseline_equal": semantic_baseline_equal,
        "accepted_resolution": accepted_resolution,
        "rejected_resolution": rejected_resolution,
        "packages": package_reports,
        "compatibility": compatibility,
        "visual_policy": visual_policy,
        "visual_validation": visual_validation,
        "delivery_level": delivery_level,
        "visual_final_eligible": False,
        "visual_inspection_status": (
            "blocked"
            if errors
            else "not_performed"
            if delivery_level == "structural_validation"
            else "required"
        ),
        "errors": errors,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="严格验证审查后的 DOCX")
    parser.add_argument("reviewed", type=Path)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--baseline-view", choices=("accept", "reject", "raw"), default="reject")
    parser.add_argument("--require-revisions", action="store_true")
    parser.add_argument(
        "--visual-policy",
        choices=sorted(VISUAL_POLICIES),
        default="allow-structural",
        help="require=缺渲染即失败；allow-structural=无工具时仅结构版；structural-only=显式跳过渲染",
    )
    args = parser.parse_args()
    report = run_quality_gate(
        args.reviewed,
        original_docx=args.original,
        output_dir=args.output_dir,
        baseline_view=args.baseline_view,
        require_revisions=args.require_revisions,
        visual_policy=args.visual_policy,
    )
    print(json.dumps({"status": report["status"], "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
