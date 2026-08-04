#!/usr/bin/env python3
"""
Add comments/annotations to a Word document (.docx) based on a JSON mapping.

Keys in the JSON are text snippets to find in the document.
Values are the comment text to add at that location.

Uses direct OOXML zip + XML manipulation for maximum compatibility.
Replaces Dify's word-tools "Word文档批注" plugin node.

Usage:
    python add_word_comments.py \\
        --input contract.docx \\
        --comments '{"付款条款":"【中风险】..."}' \\
        --author "法务审核助手" \\
        --output contract_annotated.docx \\
        --threshold 0.55

    # Or read comments from a file:
    python add_word_comments.py \\
        --input contract.docx \\
        --comments-file comments.json \\
        --output contract_annotated.docx
"""

import json
import sys
import os
import re
import zipfile
import shutil
import tempfile
import argparse
from copy import deepcopy
from difflib import SequenceMatcher
from datetime import datetime, timezone
from lxml import etree

# Word XML namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"

# Content type for comments part
COMMENTS_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
COMMENTS_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"


def wq(tag):
    """Return the Clark notation for a w: namespace tag."""
    return "{%s}%s" % (W_NS, tag)


def get_run_text(run):
    """Get the concatenated text of all w:t elements in a run."""
    texts = []
    for child in run:
        if child.tag == wq("t"):
            texts.append(child.text or "")
        elif child.tag == wq("tab"):
            texts.append("\t")
        elif child.tag == wq("br"):
            texts.append("\n")
        elif child.tag == wq("cr"):
            texts.append("\n")
    return "".join(texts)


def get_paragraph_text(paragraph):
    """Get the concatenated text of all runs in a paragraph."""
    texts = []
    for child in paragraph:
        if child.tag == wq("r"):
            texts.append(get_run_text(child))
    return "".join(texts)


def get_paragraph_runs(paragraph):
    """Return list of (run_element, run_text, start_pos, end_pos) for a paragraph."""
    runs = []
    full_text = ""
    for child in paragraph:
        if child.tag == wq("r"):
            run_text = get_run_text(child)
            start = len(full_text)
            full_text += run_text
            end = len(full_text)
            runs.append((child, run_text, start, end))
    return runs, full_text


def find_best_match(full_text, search_text, threshold):
    """Find the best match position for search_text in full_text.

    Returns (start_pos, end_pos, similarity) or None.
    """
    if not search_text or not full_text:
        return None

    # Try exact match first
    pos = full_text.find(search_text)
    if pos >= 0:
        return (pos, pos + len(search_text), 1.0)

    # If search text is very short, skip fuzzy
    if len(search_text) < 4:
        return None

    # Fuzzy match using sliding window
    best_ratio = 0.0
    best_start = -1
    best_end = -1
    search_len = len(search_text)

    # Try windows of varying length around the search text length
    min_window = max(4, int(search_len * 0.7))
    max_window = min(int(search_len * 1.3), len(full_text))

    for window_len in range(min_window, max_window + 1):
        for i in range(len(full_text) - window_len + 1):
            window = full_text[i:i + window_len]
            ratio = SequenceMatcher(None, search_text, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = i
                best_end = i + window_len

    if best_ratio >= threshold and best_start >= 0:
        return (best_start, best_end, best_ratio)

    return None


def insert_comment_markers(paragraph, start_pos, end_pos, comment_id):
    """Insert commentRangeStart, commentRangeEnd, and commentReference into a paragraph.

    Anchors the comment at the run level: commentRangeStart is inserted before
    the first run containing the match start, and commentRangeEnd is inserted
    after the last run containing the match end.
    """
    runs_info, full_text = get_paragraph_runs(paragraph)

    if not runs_info:
        return False

    # Clamp positions
    start_pos = max(0, min(start_pos, len(full_text)))
    end_pos = max(start_pos + 1, min(end_pos, len(full_text)))

    if start_pos >= end_pos:
        return False

    # Find which runs the match spans
    start_run_idx = None
    end_run_idx = None

    for i, (run_elem, run_text, r_start, r_end) in enumerate(runs_info):
        if start_run_idx is None and r_end > start_pos:
            start_run_idx = i
        if r_end >= end_pos:
            end_run_idx = i
            break

    if start_run_idx is None:
        start_run_idx = len(runs_info) - 1
    if end_run_idx is None:
        end_run_idx = len(runs_info) - 1

    if start_run_idx > end_run_idx:
        start_run_idx, end_run_idx = end_run_idx, start_run_idx

    start_run_elem = runs_info[start_run_idx][0]
    end_run_elem = runs_info[end_run_idx][0]

    # Create commentRangeStart element
    comment_start = etree.Element(wq("commentRangeStart"))
    comment_start.set(wq("id"), str(comment_id))
    # Insert before the start run
    start_run_elem.addprevious(comment_start)

    # Create commentRangeEnd element
    comment_end = etree.Element(wq("commentRangeEnd"))
    comment_end.set(wq("id"), str(comment_id))
    # Insert after the end run
    end_run_elem.addnext(comment_end)

    # Create comment reference run
    ref_run = etree.Element(wq("r"))
    rpr = etree.SubElement(ref_run, wq("rPr"))
    rstyle = etree.SubElement(rpr, wq("rStyle"))
    rstyle.set(wq("val"), "CommentReference")
    comment_ref = etree.SubElement(ref_run, wq("commentReference"))
    comment_ref.set(wq("id"), str(comment_id))
    # Insert after commentRangeEnd
    comment_end.addnext(ref_run)

    return True


def create_comments_xml(comments_list, author):
    """Create the word/comments.xml content.

    Args:
        comments_list: list of (comment_id, comment_text) tuples
        author: comment author name

    Returns:
        bytes: XML content for word/comments.xml
    """
    nsmap = {"w": W_NS}
    root = etree.Element(wq("comments"), nsmap=nsmap)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for comment_id, comment_text in comments_list:
        comment_elem = etree.SubElement(root, wq("comment"))
        comment_elem.set(wq("id"), str(comment_id))
        comment_elem.set(wq("author"), author)
        comment_elem.set(wq("date"), now)
        comment_elem.set(wq("initials"), author[:2] if author else "")

        # Split long comments into multiple paragraphs for readability
        paragraphs_text = comment_text.split("\n") if "\n" in comment_text else [comment_text]

        for para_text in paragraphs_text:
            p = etree.SubElement(comment_elem, wq("p"))
            r = etree.SubElement(p, wq("r"))
            t = etree.SubElement(r, wq("t"))
            t.set("{%s}space" % XML_NS, "preserve")
            t.text = para_text

    xml_bytes = etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True
    )

    return xml_bytes


def update_content_types(content_types_xml):
    """Add comments content type to [Content_Types].xml if not present."""
    root = etree.fromstring(content_types_xml)

    # Check if comments override already exists
    for override in root.findall("{%s}Override" % CT_NS):
        part_name = override.get("PartName")
        if part_name and "comments.xml" in part_name:
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    # Add override for comments
    override = etree.SubElement(root, "{%s}Override" % CT_NS)
    override.set("PartName", "/word/comments.xml")
    override.set("ContentType", COMMENTS_CT)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def update_rels(rels_xml):
    """Add comments relationship to word/_rels/document.xml.rels if not present."""
    root = etree.fromstring(rels_xml)

    # Find max relationship ID
    max_id = 0
    for rel in root.findall("{%s}Relationship" % PR_NS):
        rel_id = rel.get("Id", "")
        if rel_id.startswith("rId"):
            try:
                num = int(rel_id[3:])
                max_id = max(max_id, num)
            except ValueError:
                pass

        # Check if comments relationship already exists
        rel_type = rel.get("Type", "")
        if rel_type == COMMENTS_REL_TYPE:
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    # Add comments relationship
    new_id = "rId%d" % (max_id + 1)
    rel = etree.SubElement(root, "{%s}Relationship" % PR_NS)
    rel.set("Id", new_id)
    rel.set("Type", COMMENTS_REL_TYPE)
    rel.set("Target", "comments.xml")

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def add_comments_to_docx(input_path, output_path, comments_dict, author="法务审核助手", threshold=0.55):
    """Add comments to a Word document.

    Args:
        input_path: Path to input .docx file
        output_path: Path to output .docx file
        comments_dict: dict mapping text snippets (keys) to comment text (values)
        author: Comment author name
        threshold: Fuzzy match similarity threshold (0.0-1.0)

    Returns:
        dict with keys: files (output path), text (summary), total (count), matched (count)
    """
    if not os.path.exists(input_path):
        return {"files": "", "text": "输入文件不存在", "total": 0, "matched": 0}

    # Copy input to temp working file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".docx")
    os.close(temp_fd)
    shutil.copy2(input_path, temp_path)

    # Read all entries from the zip
    with zipfile.ZipFile(temp_path, "r") as zin:
        names = zin.namelist()
        entries = {}
        for name in names:
            entries[name] = zin.read(name)

    # Parse document.xml
    doc_xml_bytes = entries.get("word/document.xml")
    if doc_xml_bytes is None:
        os.remove(temp_path)
        return {"files": "", "text": "无法找到 word/document.xml", "total": len(comments_dict), "matched": 0}

    parser = etree.XMLParser(remove_blank_text=False)
    doc_root = etree.fromstring(doc_xml_bytes, parser)

    # Process each comment
    comments_for_xml = []
    comment_id = 0
    matched_count = 0
    unmatched_keys = []

    # Get all paragraphs in document order
    all_paragraphs = list(doc_root.iter(wq("p")))

    for key, comment_text in comments_dict.items():
        key_clean = key.strip()
        if not key_clean or not comment_text:
            continue

        found = False

        # Search through all paragraphs
        for paragraph in all_paragraphs:
            para_text = get_paragraph_text(paragraph)
            if not para_text:
                continue

            match = find_best_match(para_text, key_clean, threshold)
            if match is None:
                continue

            start_pos, end_pos, similarity = match

            success = insert_comment_markers(paragraph, start_pos, end_pos, comment_id)
            if success:
                comments_for_xml.append((comment_id, comment_text))
                comment_id += 1
                matched_count += 1
                found = True
                break  # Only match first occurrence

        if not found:
            unmatched_keys.append(key_clean)

    # Create comments.xml
    if comments_for_xml:
        comments_xml = create_comments_xml(comments_for_xml, author)
        entries["word/comments.xml"] = comments_xml

    # Update content types
    ct_path = "[Content_Types].xml"
    if ct_path in entries:
        entries[ct_path] = update_content_types(entries[ct_path])

    # Update document relationships
    rels_path = "word/_rels/document.xml.rels"
    if rels_path in entries:
        entries[rels_path] = update_rels(entries[rels_path])

    # Serialize modified document.xml
    entries["word/document.xml"] = etree.tostring(
        doc_root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True
    )

    # Write output zip
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    # Clean up temp
    os.remove(temp_path)

    summary = "共处理 %d 条批注，成功匹配 %d 条" % (len(comments_dict), matched_count)
    if unmatched_keys:
        summary += "，未匹配 %d 条" % len(unmatched_keys)

    return {
        "files": output_path,
        "text": summary,
        "total": len(comments_dict),
        "matched": matched_count,
        "unmatched": unmatched_keys
    }


def cli_main():
    parser = argparse.ArgumentParser(
        description="Add comments/annotations to a Word document based on a JSON mapping"
    )
    parser.add_argument("--input", "-i", required=True, help="Path to input .docx file")
    parser.add_argument("--comments", help="JSON string mapping text snippets to comments")
    parser.add_argument("--comments-file", help="Path to JSON file with comments mapping")
    parser.add_argument("--author", default="法务审核助手", help="Comment author name")
    parser.add_argument("--output", "-o", required=True, help="Path to output .docx file")
    parser.add_argument("--threshold", type=float, default=0.55, help="Fuzzy match similarity threshold (0.0-1.0)")
    args = parser.parse_args()

    # Get comments dict
    if args.comments:
        comments_dict = json.loads(args.comments)
    elif args.comments_file:
        with open(args.comments_file, "r", encoding="utf-8") as f:
            comments_dict = json.load(f)
    else:
        print("ERROR: Must provide --comments or --comments-file", file=sys.stderr)
        sys.exit(1)

    if not isinstance(comments_dict, dict):
        print("ERROR: Comments must be a JSON object (dict)", file=sys.stderr)
        sys.exit(1)

    result = add_comments_to_docx(
        args.input,
        args.output,
        comments_dict,
        author=args.author,
        threshold=args.threshold
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli_main()
