#!/usr/bin/env python3
"""
Track Changes 生成工具 - 在Word文档中生成带修改痕迹的修订版

用法:
    from tracked_changes import generate_modified_contract

    modifications = [
        {"old_text": "...", "new_text": "...", "description": "..."},
    ]

    generate_modified_contract(input_path, output_path, modifications)
"""

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

REVISION_ID = [0]
AUTHOR = "Pacgate Law Firm"


def next_id():
    REVISION_ID[0] += 1
    return REVISION_ID[0]


def make_del(text, date):
    e = OxmlElement('w:del')
    e.set(qn('w:id'), str(next_id()))
    e.set(qn('w:author'), AUTHOR)
    e.set(qn('w:date'), date)
    r = OxmlElement('w:r')
    r.append(OxmlElement('w:rPr'))
    dt = OxmlElement('w:delText')
    dt.set(qn('xml:space'), 'preserve')
    dt.text = text
    r.append(dt)
    e.append(r)
    return e


def make_ins(text, date):
    e = OxmlElement('w:ins')
    e.set(qn('w:id'), str(next_id()))
    e.set(qn('w:author'), AUTHOR)
    e.set(qn('w:date'), date)
    r = OxmlElement('w:r')
    r.append(OxmlElement('w:rPr'))
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    e.append(r)
    return e


def tracked_replace(paragraph, old_text, new_text, date):
    """Replace old_text with new_text using OOXML tracked changes."""
    full = paragraph.text
    if old_text not in full:
        return False
    p_elem = paragraph._element
    pos = full.index(old_text)
    before = full[:pos]
    after = full[pos + len(old_text):]
    for r in list(p_elem.findall(qn('w:r'))):
        p_elem.remove(r)
    if before:
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.set(qn('xml:space'), 'preserve')
        t.text = before
        r.append(t)
        p_elem.append(r)
    p_elem.append(make_del(old_text, date))
    p_elem.append(make_ins(new_text, date))
    if after:
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.set(qn('xml:space'), 'preserve')
        t.text = after
        r.append(t)
        p_elem.append(r)
    return True


def generate_modified_contract(input_path, output_path, modifications, date=None):
    """
    Generate a modified contract with tracked changes.

    Args:
        input_path: Path to original contract .docx
        output_path: Path to save modified contract .docx
        modifications: List of dicts with 'old_text', 'new_text', 'description'
        date: ISO datetime string for revision marks (default: current time)

    Returns:
        List of (description, success) tuples
    """
    from datetime import datetime
    if date is None:
        date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    doc = Document(input_path)
    paragraphs = doc.paragraphs
    results = []

    for mod in modifications:
        old_text = mod['old_text']
        new_text = mod['new_text']
        desc = mod.get('description', '')

        found = False
        for p in paragraphs:
            if old_text in p.text:
                if tracked_replace(p, old_text, new_text, date):
                    found = True
                    break

        results.append((desc, found))
        status = "✓" if found else "✗ NOT FOUND"
        print(f"  {status}: {desc[:60]}")

    doc.save(output_path)
    return results
