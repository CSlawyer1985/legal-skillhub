#!/usr/bin/env python3
"""Build a tracked-changes comparison docx: NEW as base, revisions vs OLD.

Usage:
    python3 compare_docx_tracked.py OLD.docx NEW.docx OUT.docx \
        [--author "Name"] [--date "YYYY-MM-DDT00:00:00Z"] [--threshold 0.45]

The output opens in Word as a tracked-changes (revision) view:
- content added/changed in NEW  -> <w:ins>
- content present in OLD only   -> <w:del> with <w:delText>
- word/settings.xml gets <w:trackChanges/>
"""
import argparse, re, difflib, copy, zipfile, sys, datetime
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
PR = 'http://schemas.openxmlformats.org/package/2006/relationships'
XML_NS = 'http://www.w3.org/XML/1998/namespace'
NS = {'w': W, 'm': M, 'r': R, 'a': A}

def qn(tag):
    pre, local = tag.split(':')
    return '{%s}%s' % ({'w': W, 'm': M, 'r': R, 'a': A}[pre], local)

# ---------- text extraction / normalization ----------
def para_full_text(p):
    out = []
    for el in p.iter():
        if el.tag in (qn('w:t'), qn('m:t')):
            out.append(el.text or '')
    return ''.join(out)

_norm_map = {'\u201c':'"','\u201d':'"','\u2018':"'",'\u2019':"'",'\u2013':'-','\u2014':'-','\u2010':'-','\u2011':'-',
             '\u00a0':' ','\u2009':' ','\u2002':' ','\u2003':' ','\u200b':'',
             '\u2026':'...', '\u2212':'-', '\t':' '}
def normalize(s):
    for k, v in _norm_map.items():
        s = s.replace(k, v)
    return re.sub(r'\s+', ' ', s).strip().lower()

def main():
    ap = argparse.ArgumentParser(description='Tracked-changes diff of two docx files.')
    ap.add_argument('old', help='base (older) docx')
    ap.add_argument('new', help='revised (newer) docx')
    ap.add_argument('out', help='output docx with revision marks')
    ap.add_argument('--author', default='Editor')
    ap.add_argument('--date', default=datetime.date.today().isoformat() + 'T00:00:00Z')
    ap.add_argument('--threshold', type=float, default=0.45,
                    help='paragraph similarity threshold to treat as modified vs delete+insert')
    args = ap.parse_args()
    AUTHOR, DATE, THR = args.author, args.date, args.threshold

    # ---------- load packages ----------
    zo = zipfile.ZipFile(args.old)
    zn = zipfile.ZipFile(args.new)
    old_tree = etree.fromstring(zo.read('word/document.xml'))
    new_tree = etree.fromstring(zn.read('word/document.xml'))

    def get_rels(z):
        t = etree.fromstring(z.read('word/_rels/document.xml.rels'))
        return t, {rel.get('Id'): (rel.get('Target'), rel.get('Type'), rel.get('TargetMode'))
                   for rel in t.iter('{%s}Relationship' % PR)}

    old_rels_tree, old_rels = get_rels(zo)
    new_rels_tree, new_rels = get_rels(zn)
    new_target2rid = {}
    for rid, (tgt, typ, mode) in new_rels.items():
        new_target2rid.setdefault((tgt, typ), rid)

    used_rids = set(new_rels)
    def fresh_rid():
        n = 9000
        while ('rId%d' % n) in used_rids:
            n += 1
        rid = 'rId%d' % n
        used_rids.add(rid)
        return rid

    new_media_names = {n.split('word/media/')[1] for n in zn.namelist() if n.startswith('word/media/')}
    extra_parts = {}  # partname -> bytes  (added media)

    def ensure_relationship(old_rid):
        """Return a rid valid in the NEW package pointing at the same content as old_rid in OLD."""
        tgt, typ, mode = old_rels[old_rid]
        key = (tgt, typ)
        if typ.endswith('/image'):
            old_bytes = zo.read('word/' + tgt)
            # reuse the NEW relationship only when the image BYTES are identical;
            # same target name does NOT imply same bytes (figure may have changed)
            if key in new_target2rid:
                new_rid = new_target2rid[key]
                try:
                    if zn.read('word/' + new_rels[new_rid][0]) == old_bytes:
                        return new_rid
                except KeyError:
                    pass
            # copy the OLD image into the package under a collision-free name
            base = tgt.split('/')[-1]
            name = 'tracked_' + base
            i = 1
            while name in new_media_names:
                name = 'tracked_%d_%s' % (i, base); i += 1
            new_media_names.add(name)
            extra_parts['word/media/' + name] = old_bytes
            tgt = 'media/' + name
            mode = None
        elif key in new_target2rid:
            return new_target2rid[key]
        rid = fresh_rid()
        rel = etree.SubElement(new_rels_tree, '{%s}Relationship' % PR)
        rel.set('Id', rid); rel.set('Type', typ); rel.set('Target', tgt)
        if mode:
            rel.set('TargetMode', mode)
        new_target2rid[(tgt, typ)] = rid
        return rid

    # ---------- paragraph lists ----------
    old_paras = old_tree.findall('.//w:p', NS)
    new_paras = new_tree.findall('.//w:p', NS)
    old_texts = [para_full_text(p) for p in old_paras]
    new_texts = [para_full_text(p) for p in new_paras]
    old_norm = [normalize(t) for t in old_texts]
    new_norm = [normalize(t) for t in new_texts]

    # ---------- alignment ----------
    def sub_align(old_idx, new_idx, thr=THR):
        n, m = len(old_idx), len(new_idx)
        rat = [[0.0]*m for _ in range(n)]
        for a, i in enumerate(old_idx):
            for b, j in enumerate(new_idx):
                rat[a][b] = difflib.SequenceMatcher(a=old_norm[i], b=new_norm[j], autojunk=False).ratio()
        dp = [[0.0]*(m+1) for _ in range(n+1)]
        back = [[None]*(m+1) for _ in range(n+1)]
        for a in range(1, n+1): back[a][0] = 'del'
        for b in range(1, m+1): back[0][b] = 'ins'
        for a in range(1, n+1):
            for b in range(1, m+1):
                best, act = dp[a-1][b], 'del'
                if dp[a][b-1] > best: best, act = dp[a][b-1], 'ins'
                ps = rat[a-1][b-1] - thr
                if dp[a-1][b-1] + ps > best: best, act = dp[a-1][b-1] + ps, 'pair'
                dp[a][b], back[a][b] = best, act
        res = []
        a, b = n, m
        while a > 0 or b > 0:
            act = back[a][b]
            if act == 'pair': res.append(('pair', old_idx[a-1], new_idx[b-1])); a -= 1; b -= 1
            elif act == 'del': res.append(('del', old_idx[a-1])); a -= 1
            else: res.append(('ins', new_idx[b-1])); b -= 1
        res.reverse()
        return res

    sm = difflib.SequenceMatcher(a=old_norm, b=new_norm, autojunk=False)
    actions = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            actions += [('equal', i1+k, j1+k) for k in range(i2-i1)]
        elif tag == 'insert':
            actions += [('ins', j) for j in range(j1, j2)]
        elif tag == 'delete':
            actions += [('del', i) for i in range(i1, i2)]
        else:
            actions += sub_align(list(range(i1, i2)), list(range(j1, j2)))

    # reclassify equal pairs whose images differ (byte compare via rel targets)
    def para_images(p, rels, z):
        out = []
        for b in p.findall('.//a:blip', NS):
            rid = b.get(qn('r:embed'))
            if rid and rid in rels:
                tgt = rels[rid][0]
                try: out.append(z.read('word/' + tgt))
                except KeyError: out.append(b'?')
        return out

    for k, a in enumerate(actions):
        if a[0] == 'equal':
            i, j = a[1], a[2]
            oi, ni = para_images(old_paras[i], old_rels, zo), para_images(new_paras[j], new_rels, zn)
            if oi != ni and (oi or ni):
                actions[k] = ('pair_img', i, j)

    # ---------- revision markup helpers ----------
    _id = [0]
    def next_id():
        _id[0] += 1
        return str(_id[0])

    def mark_attrs(el):
        el.set(qn('w:id'), next_id())
        el.set(qn('w:author'), AUTHOR)
        el.set(qn('w:date'), DATE)

    def to_deltext(root):
        for t in root.iter(qn('w:t')):
            t.tag = qn('w:delText')
            t.set('{%s}space' % XML_NS, 'preserve')

    def mark_para_boundary(p, kind):
        pPr = p.find(qn('w:pPr'))
        if pPr is None:
            pPr = etree.Element(qn('w:pPr'))
            p.insert(0, pPr)
        rPr = pPr.find(qn('w:rPr'))
        if rPr is None:
            rPr = etree.SubElement(pPr, qn('w:rPr'))
        mark = etree.Element(qn('w:' + kind))
        mark_attrs(mark)
        rPr.insert(0, mark)

    def wrap_children(p, kind):
        for ch in list(p):
            if ch.tag == qn('w:pPr'):
                continue
            w = etree.Element(qn('w:' + kind))
            mark_attrs(w)
            idx = list(p).index(ch)
            p.remove(ch)
            w.append(ch)
            p.insert(idx, w)
            if kind == 'del':
                to_deltext(w)

    def mark_para_inserted(p):
        mark_para_boundary(p, 'ins')
        wrap_children(p, 'ins')

    STRIP_IN_COPIES = ('w:bookmarkStart', 'w:bookmarkEnd', 'w:proofErr', 'w:permStart', 'w:permEnd')

    def make_deleted_copy(old_p):
        cp = copy.deepcopy(old_p)
        for tag in STRIP_IN_COPIES:
            for el in cp.findall('.//' + qn(tag)):
                el.getparent().remove(el)
        for el in cp.iter():
            for attr in (qn('r:id'), qn('r:embed'), qn('r:link')):
                v = el.get(attr)
                if v and v in old_rels:
                    el.set(attr, ensure_relationship(v))
        mark_para_boundary(cp, 'del')
        wrap_children(cp, 'del')
        return cp

    def insert_before(anchor_el, new_el):
        parent = anchor_el.getparent()
        parent.insert(parent.index(anchor_el), new_el)

    # ---------- granular (word-level) rewrite ----------
    TOK_RE = re.compile(r'\s+|\w+|[^\w\s]+')
    def tokenize(s):
        return TOK_RE.findall(s)

    def clone_run_with_text(run, text):
        r = copy.deepcopy(run)
        for t in r.findall(qn('w:t')):
            r.remove(t)
        t = etree.SubElement(r, qn('w:t'))
        t.set('{%s}space' % XML_NS, 'preserve')
        t.text = text
        return r

    def wrap_el(el, kind):
        w = etree.Element(qn('w:' + kind))
        mark_attrs(w)
        w.append(el)
        return w

    def granular_rewrite(new_p, old_text):
        items = []
        for ch in new_p:
            if ch.tag == qn('w:pPr'):
                continue
            if ch.tag == qn('w:r') and all(g.tag in (qn('w:rPr'), qn('w:t')) for g in ch):
                txt = ''.join(t.text or '' for t in ch.findall(qn('w:t')))
                items.append([ch, 'run', txt])
            else:
                txt = ''.join((t.text or '') for t in ch.iter() if t.tag in (qn('w:t'), qn('m:t')))
                items.append([ch, 'atomic', txt])
        new_text = ''.join(it[2] for it in items)
        old_toks, new_toks = tokenize(old_text), tokenize(new_text)
        sm2 = difflib.SequenceMatcher(a=old_toks, b=new_toks, autojunk=False)
        segs = []
        for tag, a1, a2, b1, b2 in sm2.get_opcodes():
            if tag == 'equal': segs.append(('eq', ''.join(new_toks[b1:b2])))
            elif tag == 'insert': segs.append(('ins', ''.join(new_toks[b1:b2])))
            elif tag == 'delete': segs.append(('del', ''.join(old_toks[a1:a2])))
            else:
                segs.append(('del', ''.join(old_toks[a1:a2])))
                segs.append(('ins', ''.join(new_toks[b1:b2])))
        merged = []
        for op, txt in segs:
            if merged and merged[-1][0] == op:
                merged[-1] = (op, merged[-1][1] + txt)
            else:
                merged.append((op, txt))
        segs = [(op, txt) for op, txt in merged if txt]
        assert ''.join(t for op, t in segs if op in ('eq', 'ins')) == new_text

        out = []
        si, off = 0, 0
        last_rpr = None

        def emit_del(text):
            r = etree.Element(qn('w:r'))
            if last_rpr is not None:
                r.append(copy.deepcopy(last_rpr))
            t = etree.SubElement(r, qn('w:delText'))
            t.set('{%s}space' % XML_NS, 'preserve')
            t.text = text
            out.append(wrap_el(r, 'del'))

        def flush_dels():
            nonlocal si, off
            while si < len(segs) and segs[si][0] == 'del':
                emit_del(segs[si][1]); si += 1; off = 0

        for el, kind, text in items:
            rpr = el.find(qn('w:rPr')) if kind == 'run' else None
            if rpr is not None:
                last_rpr = rpr
            if not text:
                out.append(el)
                continue
            flush_dels()
            if si >= len(segs):
                return False
            op, stext = segs[si]
            if kind == 'atomic':
                if len(text) > len(stext) - off:
                    return False
                if op == 'eq':
                    out.append(el)
                else:
                    out.append(wrap_el(el, 'ins'))
                off += len(text)
                if off == len(stext):
                    si += 1; off = 0
            else:
                remaining = text
                first_piece = True
                while remaining:
                    if si >= len(segs):
                        return False
                    op, stext = segs[si]
                    if op == 'del':
                        emit_del(stext); si += 1; off = 0
                        continue
                    take = min(len(remaining), len(stext) - off)
                    piece, remaining = remaining[:take], remaining[take:]
                    if take == len(text) and op == 'eq' and first_piece:
                        out.append(el)
                    else:
                        piece_run = clone_run_with_text(el, piece)
                        out.append(piece_run if op == 'eq' else wrap_el(piece_run, 'ins'))
                    first_piece = False
                    off += take
                    if off == len(stext):
                        si += 1; off = 0
                    flush_dels()
        flush_dels()
        if si != len(segs):
            return False
        for ch in list(new_p):
            if ch.tag != qn('w:pPr'):
                new_p.remove(ch)
        for el in out:
            new_p.append(el)
        return True

    # ---------- apply actions ----------
    body = new_tree.find(qn('w:body'))
    sectPr = body.find(qn('w:sectPr'))

    next_anchor = [None]*len(actions)
    nxt = None
    for k in range(len(actions)-1, -1, -1):
        next_anchor[k] = nxt
        a = actions[k]
        if a[0] in ('equal', 'pair', 'pair_img', 'ins'):
            nxt = new_paras[a[-1]]

    stats = {'ins_para': 0, 'del_para': 0, 'mod_para': 0, 'mod_fallback': 0}
    for k, a in enumerate(actions):
        kind = a[0]
        if kind == 'equal':
            continue
        if kind == 'ins':
            mark_para_inserted(new_paras[a[1]])
            stats['ins_para'] += 1
        elif kind == 'del':
            cp = make_deleted_copy(old_paras[a[1]])
            anchor = next_anchor[k] if next_anchor[k] is not None else sectPr
            insert_before(anchor, cp)
            stats['del_para'] += 1
        elif kind in ('pair', 'pair_img'):
            i, j = a[1], a[2]
            new_p = new_paras[j]
            ok = False
            if kind == 'pair':
                ok = granular_rewrite(new_p, old_texts[i])
            if ok:
                stats['mod_para'] += 1
            else:
                cp = make_deleted_copy(old_paras[i])
                insert_before(new_p, cp)
                mark_para_inserted(new_p)
                stats['mod_fallback'] += 1

    # ---------- settings.xml: trackChanges ----------
    settings = etree.fromstring(zn.read('word/settings.xml'))
    tc = etree.Element(qn('w:trackChanges'))
    anchor = settings.find(qn('w:doNotTrackMoves'))
    if anchor is not None:
        settings.insert(settings.index(anchor), tc)
    else:
        anchor = settings.find(qn('w:defaultTabStop'))
        if anchor is not None:
            settings.insert(settings.index(anchor), tc)
        else:
            settings.append(tc)

    # ---------- write package ----------
    xml_decl = b"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n"
    def ser(t):
        return xml_decl + etree.tostring(t, xml_declaration=False, encoding='UTF-8')

    with zipfile.ZipFile(args.out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zn.infolist():
            data = zn.read(item.filename)
            if item.filename == 'word/document.xml':
                data = ser(new_tree)
            elif item.filename == 'word/settings.xml':
                data = ser(settings)
            elif item.filename == 'word/_rels/document.xml.rels':
                data = ser(new_rels_tree)
            zout.writestr(item, data)
        for part, data in extra_parts.items():
            zout.writestr(part, data)

    print('stats:', stats)
    print('revision ids used:', _id[0])
    print('extra media parts:', list(extra_parts))
    print('written:', args.out)

if __name__ == '__main__':
    main()
