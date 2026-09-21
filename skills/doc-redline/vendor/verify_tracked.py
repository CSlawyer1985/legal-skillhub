#!/usr/bin/env python3
"""Verify a tracked-changes comparison docx.

Usage:
    python3 verify_tracked.py OUT.docx OLD.docx NEW.docx

Checks:
 1. revision ids unique; no w:t left inside w:del; all r:id/r:embed/r:link resolve
 2. settings.xml contains w:trackChanges
 3. simulated "accept all revisions" text == NEW text (paragraph by paragraph)
 4. simulated "reject all revisions" text == OLD text
 5. every OLD-only paragraph text appears in some w:delText
Prints PASS/FAIL per check plus ins/del counts.
"""
import sys, re, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR = 'http://schemas.openxmlformats.org/package/2006/relationships'
NS = {'w': W, 'm': M, 'r': R}

def qn(tag):
    pre, local = tag.split(':')
    return '{%s}%s' % ({'w': W, 'm': M, 'r': R}[pre], local)

_norm_map = {'\u201c':'"','\u201d':'"','\u2018':"'",'\u2019':"'",'\u2013':'-','\u2014':'-','\u2010':'-','\u2011':'-',
             '\u00a0':' ','\u2009':' ','\u2002':' ','\u2003':' ','\u200b':'',
             '\u2026':'...', '\u2212':'-', '\t':' '}
def normalize(s):
    for k, v in _norm_map.items():
        s = s.replace(k, v)
    return re.sub(r'\s+', ' ', s).strip().lower()

def load(path):
    z = zipfile.ZipFile(path)
    tree = etree.fromstring(z.read('word/document.xml'))
    return z, tree

def plain_paras(tree):
    """Paragraph texts ignoring any revision markup (for unmarked docs)."""
    out = []
    for p in tree.findall('.//w:p', NS):
        out.append(''.join((t.text or '') for t in p.iter()
                           if t.tag in (qn('w:t'), qn('m:t'))))
    return out

def view_paras(tree, mode):
    """mode='accept': keep ins, drop del.  mode='reject': keep del(as text), drop ins.
    Paragraph-level marks: ins paragraph -> only in accept; del paragraph -> only in reject."""
    out = []
    for p in tree.findall('.//w:p', NS):
        pPr = p.find(qn('w:pPr'))
        para_ins = para_del = False
        if pPr is not None:
            rPr = pPr.find(qn('w:rPr'))
            if rPr is not None:
                para_ins = rPr.find(qn('w:ins')) is not None
                para_del = rPr.find(qn('w:del')) is not None
        if mode == 'accept' and para_del:
            continue
        if mode == 'reject' and para_ins:
            continue
        texts = []
        def walk(el, in_ins=False, in_del=False):
            tag = el.tag
            if tag == qn('w:ins'): in_ins = True
            if tag == qn('w:del'): in_del = True
            if tag == qn('w:t') or tag == qn('m:t'):
                if mode == 'accept' and not in_del:
                    texts.append(el.text or '')
                if mode == 'reject' and not in_ins:
                    texts.append(el.text or '')
            elif tag == qn('w:delText'):
                if mode == 'reject' and not in_ins:
                    texts.append(el.text or '')
            for c in el:
                walk(c, in_ins, in_del)
        walk(p)
        out.append(''.join(texts))
    return out

def main():
    out_path, old_path, new_path = sys.argv[1], sys.argv[2], sys.argv[3]
    z, tree = load(out_path)
    results = []

    # --- check 1: structural sanity ---
    # .//w:ins already includes paragraph-boundary marks (w:pPr/w:rPr/w:ins)
    ins_els = tree.findall('.//w:ins', NS)
    del_els = tree.findall('.//w:del', NS)
    ids = [e.get(qn('w:id')) for e in ins_els + del_els
           if e.get(qn('w:id')) is not None]
    dup = len(ids) - len(set(ids))
    stray_t = 0
    for d in del_els:
        stray_t += len([t for t in d.iter(qn('w:t'))])
    rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
    rel_ids = {rel.get('Id') for rel in rels.iter('{%s}Relationship' % PR)}
    bad_refs = 0
    for el in tree.iter():
        for attr in (qn('r:id'), qn('r:embed'), qn('r:link')):
            v = el.get(attr)
            if v and v not in rel_ids:
                bad_refs += 1
    ok1 = dup == 0 and stray_t == 0 and bad_refs == 0
    results.append(('structure (unique ids=%d, stray w:t in del=%d, bad refs=%d)'
                    % (len(ids), stray_t, bad_refs), ok1))

    # --- check 2: trackChanges on ---
    settings = etree.fromstring(z.read('word/settings.xml'))
    ok2 = settings.find(qn('w:trackChanges')) is not None
    results.append(('settings.xml has w:trackChanges', ok2))

    # --- check 3/4: accept/reject simulation ---
    _, old_tree = load(old_path)
    _, new_tree = load(new_path)
    acc = [normalize(t) for t in view_paras(tree, 'accept')]
    rej = [normalize(t) for t in view_paras(tree, 'reject')]
    new_plain = [normalize(t) for t in plain_paras(new_tree)]
    old_plain = [normalize(t) for t in plain_paras(old_tree)]
    ok3 = acc == new_plain
    ok4 = rej == old_plain
    results.append(('accept-all == NEW (%d vs %d paras)' % (len(acc), len(new_plain)), ok3))
    results.append(('reject-all == OLD (%d vs %d paras)' % (len(rej), len(old_plain)), ok4))

    # --- check 5: purely-deleted OLD paragraphs fully covered by delText ---
    # ('replace' blocks become word-level diffs or fallback pairs, so their
    #  paragraphs only appear partially in delText by design -- skip them)
    # join with '' — original paragraph text concatenates runs without a
    # separator; joining with ' ' would insert phantom spaces at run breaks
    deltext = ''.join(t.text or '' for t in tree.iter(qn('w:delText')))
    ndel = normalize(deltext)
    sm = __import__('difflib').SequenceMatcher(a=old_plain, b=new_plain, autojunk=False)
    missing = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'delete':
            for i in range(i1, i2):
                t = old_plain[i]
                if t and t not in ndel:
                    missing.append(i)
    ok5 = len(missing) == 0
    results.append(('OLD-only paragraphs present in delText (missing=%d)' % len(missing), ok5))

    # --- check 6: every revision carries author and date ---
    no_author = sum(1 for e in ins_els + del_els if not e.get(qn('w:author')))
    no_date = sum(1 for e in ins_els + del_els if not e.get(qn('w:date')))
    ok6 = no_author == 0 and no_date == 0
    results.append(('all revisions have author & date (missing author=%d, date=%d)'
                    % (no_author, no_date), ok6))

    # --- check 7: image fidelity — every OLD image's bytes survive in OUT ---
    # (a deleted paragraph showing an OLD figure must still resolve to OLD bytes;
    #  same media filename in NEW does NOT imply same bytes)
    import hashlib
    def media_hashes(zz):
        return {hashlib.md5(zz.read(n)).hexdigest()
                for n in zz.namelist() if n.startswith('word/media/')}
    zo_, _ = load(old_path)
    out_hashes = media_hashes(z)
    missing_imgs = [h for h in media_hashes(zo_) if h not in out_hashes]
    ok7 = len(missing_imgs) == 0
    results.append(('OLD image bytes preserved in package (missing=%d)' % len(missing_imgs), ok7))

    # --- summary ---
    print('ins elements: %d | del elements: %d' % (len(ins_els), len(del_els)))
    for name, ok in results:
        print(('PASS' if ok else 'FAIL'), '-', name)
    sys.exit(0 if all(ok for _, ok in results) else 1)

if __name__ == '__main__':
    main()
