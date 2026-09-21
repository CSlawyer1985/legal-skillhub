#!/usr/bin/env python3
"""Create accepted/rejected DOCX views without relying on a desktop Word engine."""

from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from defusedxml import minidom


REVISION_WRAPPERS = {
    "accept": {"unwrap": {"w:ins", "w:moveTo"}, "remove": {"w:del", "w:moveFrom"}},
    "reject": {"unwrap": {"w:del", "w:moveFrom"}, "remove": {"w:ins", "w:moveTo"}},
}
REVISION_MARKERS = {
    "w:moveFromRangeStart",
    "w:moveFromRangeEnd",
    "w:moveToRangeStart",
    "w:moveToRangeEnd",
    "w:customXmlInsRangeStart",
    "w:customXmlInsRangeEnd",
    "w:customXmlDelRangeStart",
    "w:customXmlDelRangeEnd",
    "w:customXmlMoveFromRangeStart",
    "w:customXmlMoveFromRangeEnd",
    "w:customXmlMoveToRangeStart",
    "w:customXmlMoveToRangeEnd",
}
PROPERTY_CHANGE_TAGS = {
    "w:rPrChange",
    "w:pPrChange",
    "w:tblPrChange",
    "w:tblGridChange",
    "w:trPrChange",
    "w:tcPrChange",
    "w:sectPrChange",
    "w:numberingChange",
}
REVISION_TAGS = (
    {"w:ins", "w:del", "w:moveFrom", "w:moveTo"}
    | REVISION_MARKERS
    | PROPERTY_CHANGE_TAGS
)
STORY_PATTERN = re.compile(
    r"^word/(document|header\d+|footer\d+|footnotes|endnotes)\.xml$"
)


def _element_children(node):
    return [child for child in node.childNodes if child.nodeType == child.ELEMENT_NODE]


def _replace_deleted_text_names(node) -> None:
    for old_name, new_name in (("w:delText", "w:t"), ("w:delInstrText", "w:instrText")):
        for old in list(node.getElementsByTagName(old_name)):
            replacement = old.ownerDocument.createElement(new_name)
            for index in range(old.attributes.length):
                attr = old.attributes.item(index)
                replacement.setAttribute(attr.name, attr.value)
            while old.firstChild:
                replacement.appendChild(old.firstChild)
            old.parentNode.replaceChild(replacement, old)


def _unwrap(node) -> None:
    parent = node.parentNode
    for child in list(node.childNodes):
        parent.insertBefore(child, node)
    parent.removeChild(node)


def _resolve_property_changes(dom, mode: str) -> None:
    for tag in PROPERTY_CHANGE_TAGS:
        for change in list(dom.getElementsByTagName(tag)):
            current_properties = change.parentNode
            if mode == "reject":
                prior_candidates = _element_children(change)
                if prior_candidates and current_properties.parentNode is not None:
                    prior = prior_candidates[0].cloneNode(deep=True)
                    current_properties.parentNode.replaceChild(prior, current_properties)
                    continue
            if change.parentNode is not None:
                change.parentNode.removeChild(change)


def resolve_dom_revisions(dom, mode: str):
    if mode not in REVISION_WRAPPERS:
        raise ValueError(f"unsupported revision mode: {mode}")
    policy = REVISION_WRAPPERS[mode]
    before = count_dom_revisions(dom)

    _resolve_property_changes(dom, mode)
    for tag in policy["remove"]:
        for node in list(dom.getElementsByTagName(tag)):
            node.parentNode.removeChild(node)
    for tag in policy["unwrap"]:
        for node in list(dom.getElementsByTagName(tag)):
            if mode == "reject" and tag in {"w:del", "w:moveFrom"}:
                _replace_deleted_text_names(node)
            _unwrap(node)
    for tag in REVISION_MARKERS:
        for node in list(dom.getElementsByTagName(tag)):
            node.parentNode.removeChild(node)

    after = count_dom_revisions(dom)
    return {"before": before, "after": after}


def count_dom_revisions(dom) -> int:
    return sum(len(dom.getElementsByTagName(tag)) for tag in REVISION_TAGS)


def _attr_by_local_name(element, local_name: str) -> str | None:
    for index in range(element.attributes.length):
        attr = element.attributes.item(index)
        if attr.name.rsplit(":", 1)[-1] == local_name:
            return attr.value
    return None


def _remove_elements_by_attr(dom, tag: str, attr_name: str, removed_values: set[str]) -> int:
    removed = 0
    for element in list(dom.getElementsByTagName(tag)):
        if (_attr_by_local_name(element, attr_name) or "") in removed_values:
            element.parentNode.removeChild(element)
            removed += 1
    return removed


def prune_orphan_comments(unpacked_dir: Path) -> dict[str, object]:
    """Remove comments whose complete anchor disappeared with accepted/rejected text."""
    comments_path = unpacked_dir / "word/comments.xml"
    if not comments_path.exists():
        return {"orphan_comment_ids": [], "removed_comment_count": 0}

    anchor_counts = {
        "w:commentRangeStart": Counter(),
        "w:commentRangeEnd": Counter(),
        "w:commentReference": Counter(),
    }
    story_doms = {}
    for path in sorted((unpacked_dir / "word").rglob("*.xml")):
        relative = path.relative_to(unpacked_dir).as_posix()
        if not STORY_PATTERN.match(relative):
            continue
        dom = minidom.parseString(path.read_bytes())
        story_doms[path] = dom
        for tag, counter in anchor_counts.items():
            for element in dom.getElementsByTagName(tag):
                counter[_attr_by_local_name(element, "id") or ""] += 1

    comments_dom = minidom.parseString(comments_path.read_bytes())
    comments = list(comments_dom.getElementsByTagName("w:comment"))
    comment_ids = {
        _attr_by_local_name(comment, "id") or ""
        for comment in comments
        if _attr_by_local_name(comment, "id") is not None
    }
    valid_ids = {
        comment_id
        for comment_id in comment_ids
        if comment_id
        and all(counter[comment_id] > 0 for counter in anchor_counts.values())
        and len({counter[comment_id] for counter in anchor_counts.values()}) == 1
    }
    orphan_ids = comment_ids - valid_ids
    if not orphan_ids:
        return {"orphan_comment_ids": [], "removed_comment_count": 0}

    for path, dom in story_doms.items():
        for tag in anchor_counts:
            _remove_elements_by_attr(dom, tag, "id", orphan_ids)
        path.write_bytes(dom.toxml(encoding="utf-8"))

    removed_para_ids: set[str] = set()
    for comment in comments:
        comment_id = _attr_by_local_name(comment, "id") or ""
        if comment_id not in orphan_ids:
            continue
        for paragraph in comment.getElementsByTagName("w:p"):
            para_id = _attr_by_local_name(paragraph, "paraId")
            if para_id:
                removed_para_ids.add(para_id)
        comment.parentNode.removeChild(comment)
    comments_path.write_bytes(comments_dom.toxml(encoding="utf-8"))

    remaining_para_ids = {
        para_id
        for comment in comments_dom.getElementsByTagName("w:comment")
        for paragraph in comment.getElementsByTagName("w:p")
        if (para_id := _attr_by_local_name(paragraph, "paraId"))
    }
    extended_path = unpacked_dir / "word/commentsExtended.xml"
    if extended_path.exists():
        dom = minidom.parseString(extended_path.read_bytes())
        for element in list(dom.getElementsByTagName("w15:commentEx")):
            if (_attr_by_local_name(element, "paraId") or "") not in remaining_para_ids:
                element.parentNode.removeChild(element)
            elif (
                parent_id := _attr_by_local_name(element, "paraIdParent")
            ) and parent_id not in remaining_para_ids:
                for index in reversed(range(element.attributes.length)):
                    attr = element.attributes.item(index)
                    if attr.name.rsplit(":", 1)[-1] == "paraIdParent":
                        element.removeAttribute(attr.name)
        extended_path.write_bytes(dom.toxml(encoding="utf-8"))

    durable_ids: set[str] = set()
    ids_path = unpacked_dir / "word/commentsIds.xml"
    if ids_path.exists():
        dom = minidom.parseString(ids_path.read_bytes())
        for element in list(dom.getElementsByTagName("w16cid:commentId")):
            if (_attr_by_local_name(element, "paraId") or "") not in remaining_para_ids:
                element.parentNode.removeChild(element)
            else:
                durable_id = _attr_by_local_name(element, "durableId")
                if durable_id:
                    durable_ids.add(durable_id)
        ids_path.write_bytes(dom.toxml(encoding="utf-8"))

    extensible_path = unpacked_dir / "word/commentsExtensible.xml"
    if extensible_path.exists():
        dom = minidom.parseString(extensible_path.read_bytes())
        for element in list(dom.getElementsByTagName("w16cex:commentExtensible")):
            if (_attr_by_local_name(element, "durableId") or "") not in durable_ids:
                element.parentNode.removeChild(element)
        extensible_path.write_bytes(dom.toxml(encoding="utf-8"))

    return {
        "orphan_comment_ids": sorted(orphan_ids),
        "removed_comment_count": len(orphan_ids),
        "removed_comment_para_ids": sorted(removed_para_ids),
    }


def transform_xml_bytes(data: bytes, mode: str) -> tuple[bytes, dict[str, int]]:
    dom = minidom.parseString(data)
    counts = resolve_dom_revisions(dom, mode)
    return dom.toxml(encoding="utf-8"), counts


def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"unsafe ZIP member: {member.filename}")
    archive.extractall(destination)


def resolve_unpacked_revisions(unpacked_dir: Path, mode: str) -> dict[str, object]:
    parts = []
    total_before = 0
    total_after = 0
    for path in sorted((unpacked_dir / "word").rglob("*.xml")):
        data, counts = transform_xml_bytes(path.read_bytes(), mode)
        path.write_bytes(data)
        if counts["before"] or counts["after"]:
            parts.append({"part": path.relative_to(unpacked_dir).as_posix(), **counts})
        total_before += counts["before"]
        total_after += counts["after"]
    comment_resolution = prune_orphan_comments(unpacked_dir)
    return {
        "mode": mode,
        "revision_count_before": total_before,
        "revision_count_after": total_after,
        "parts": parts,
        "comment_resolution": comment_resolution,
    }


def create_revision_view(input_docx: Path, output_docx: Path, mode: str) -> dict[str, object]:
    input_docx = Path(input_docx)
    output_docx = Path(output_docx)
    if output_docx.exists():
        raise FileExistsError(f"refusing to overwrite revision view: {output_docx}")
    if input_docx.resolve() == output_docx.resolve():
        raise ValueError("input and output must differ")

    with tempfile.TemporaryDirectory(prefix=f"contract-{mode}-") as temp_dir:
        unpacked = Path(temp_dir) / "unpacked"
        with zipfile.ZipFile(input_docx, "r") as archive:
            _safe_extract(archive, unpacked)
        report = resolve_unpacked_revisions(unpacked, mode)
        if report["revision_count_after"]:
            raise ValueError(f"unresolved revision elements after {mode}: {report}")
        output_docx.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(item for item in unpacked.rglob("*") if item.is_file()):
                archive.write(path, path.relative_to(unpacked).as_posix())
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="生成接受修订版或拒绝修订版 DOCX")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", required=True, choices=("accept", "reject"))
    args = parser.parse_args()
    report = create_revision_view(args.input, args.output, args.mode)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
