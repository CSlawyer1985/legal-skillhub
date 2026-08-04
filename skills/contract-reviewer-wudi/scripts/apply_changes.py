#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修订与批注写入引擎 v2.4.0
将审核发现以 Word 原生修订痕迹（Track Changes）和批注气泡（Comment）写入 docx

v2.4.0 改进:
  - 段落精确匹配：先用 JSON 的 paragraph_index，失败后自动语义搜索文档找正确位置
  - 原生批注样式：风险等级颜色区分（高=红/中=橙/低=蓝）+ 段落结构化排版
  - 修订失败时降级为批注：找不到原文时自动转批注而非报错
  - 新增读取修订痕迹：parse_tracked_changes() 可读取对方 Word 修订版

输入 changes.json 格式:
{
  "author": "Claude",
  "date": "2026-04-15T11:00:00Z",
  "revisions": [
    {
      "paragraph_index": 42,       // 优先用索引
      "search_hint": "第13条违约金", // 语义搜索关键词（索引失败时用）
      "original_text": "原文",
      "revised_text": "修订文",
      "reason": "修订原因",
      "fallback_to_comment": true  // 找不到原文时降级为批注
    }
  ],
  "comments": [
    {
      "paragraph_index": 55,
      "highlight_text": "被批注文本",
      "comment": "批注内容",
      "severity": "高风险|中风险|低风险",
      "reason": "修改原因",
      "legal_basis": "法律依据",
      "suggestion": "建议条款"
    }
  ],
  "clean_mode": false
}
"""

import json, os, re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

# 导入共享配置
try:
    from config import (
        SEVERITY_COLORS as CONFIG_COLORS,
        SEVERITY_BG as CONFIG_BG,
        SEVERITY_DOTS as CONFIG_DOTS,
        DEFAULT_FONT,
        DEFAULT_FONT_SIZE,
        get_system_font,
    )
except ImportError:
    # 兜底：如果 config.py 不存在，使用默认值
    CONFIG_COLORS = None
    DEFAULT_FONT = 'SimSun'
    DEFAULT_FONT_SIZE = 21
    def get_system_font():
        return 'SimSun'

ET.register_namespace('w',  'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
ET.register_namespace('r',  'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
ET.register_namespace('w14','http://schemas.microsoft.com/office/word/2010/wordml')
ET.register_namespace('w15','http://schemas.microsoft.com/office/word/2012/wordml')
ET.register_namespace('mc', 'http://schemas.openxmlformats.org/markup-compatibility/2006')

W  = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R  = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
W14= 'http://schemas.microsoft.com/office/word/2010/wordml'
W15= 'http://schemas.microsoft.com/office/word/2012/wordml'

def qn(tag, ns=W):
    return f'{{{ns}}}{tag}'


# ============================================================
# 配色常量（优先使用 config.py）
# ============================================================
if CONFIG_COLORS:
    SEVERITY_COLORS = CONFIG_COLORS
    SEVERITY_BG = CONFIG_BG
    SEVERITY_DOTS = CONFIG_DOTS
else:
    # 兜底定义
    SEVERITY_COLORS = {
        '高风险': 'C00000',
        '中风险': 'E36C09',
        '低风险': '2E75B6',
        '信息':   '595959',
    }
    SEVERITY_BG = {
        '高风险': 'FFE7E7',
        '中风险': 'FFF3E0',
        '低风险': 'E7F3FF',
        '信息':   'F5F5F5',
    }
    SEVERITY_DOTS = {
        '高风险': '🔴',
        '中风险': '🟡',
        '低风险': '🔵',
        '信息':   '⚪',
    }


# ============================================================
# 修订 ID 管理器
# ============================================================
class RevisionIdManager:
    def __init__(self):
        self.next_id = 1
        self.used = set()

    def next(self):
        while self.next_id in self.used:
            self.next_id += 1
        nid = self.next_id
        self.used.add(nid)
        self.next_id += 1
        return nid

    def mark_used(self, nid):
        self.used.add(nid)


class CommentIdManager:
    def __init__(self):
        self.next_id = 0
        self.used = set()

    def next(self):
        while self.next_id in self.used:
            self.next_id += 1
        nid = self.next_id
        self.used.add(nid)
        self.next_id += 1
        return nid

    def mark_used(self, nid):
        self.used.add(nid)


# ============================================================
# XML 工具
# ============================================================
def _escape_xml(text):
    if not text: return ''
    return (text.replace('&','&amp;')
             .replace('<','&lt;')
             .replace('>','&gt;')
             .replace('"','&quot;'))


# WPS 兼容性：生成 8-char uppercase hex paraId
import random
def _gen_para_id():
    return format(random.getrandbits(32), '08X').upper()


def get_paragraph_text(p_elem):
    return ''.join(t.text or '' for t in p_elem.iter(qn('t')))


def find_all_text_runs(p_elem):
    """遍历段落中所有 w:r，返回 [{elem, text, start}]"""
    runs, pos = [], 0
    for r in p_elem.iter(qn('r')):
        texts = [t.text for t in r.iter(qn('t')) if t.text]
        text = ''.join(texts)
        runs.append({'elem': r, 'text': text, 'start': pos})
        pos += len(text)
    return runs


def find_runs_spanning_text(runs, target_text):
    """
    在 runs 中找包含 target_text 的范围。
    返回 (start_idx, end_idx, offset_in_start, offset_in_end)
    失败返回 None
    """
    if not runs or not target_text:
        return None
    full = ''.join(r['text'] for r in runs)
    pos = full.find(target_text)
    if pos == -1:
        return None
    end_pos = pos + len(target_text)
    s_idx = e_idx = None
    cur = 0
    for i, r in enumerate(runs):
        rs, re_ = cur, cur + len(r['text'])
        if s_idx is None and rs <= pos < re_:
            s_idx = i
        if re_ >= end_pos:
            e_idx = i
            break
        cur = re_
    if s_idx is None or e_idx is None:
        return None
    return (s_idx, e_idx,
            pos - runs[s_idx]['start'],
            end_pos - runs[e_idx]['start'])


# ============================================================
# 段落精确匹配（核心改进）
# ============================================================
def find_paragraph_index_by_search(paragraphs, search_hint, original_text):
    """
    通过语义搜索找到最匹配的段落索引。

    策略（按优先级）：
    1. 精确子串：original_text 在段落中完整出现
    2. 长子串：original_text 的长片段（>=8字）命中
    3. 关键词交集：多个中文词（>=2字）在同一段落中
    4. search_hint 辅助：hint 中的关键词命中

    返回: (best_paragraph_index, match_confidence)
    """
    if not original_text:
        return None, 0

    # 提取关键词
    hint_words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', search_hint or '')]
    orig_words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', original_text) if len(w) >= 2]
    all_words = list(dict.fromkeys(hint_words + orig_words))  # 去重保序

    scores = []
    for i, p in enumerate(paragraphs):
        text = get_paragraph_text(p).strip()
        if not text:
            continue
        score = 0
        matched = []

        # 策略1：original_text 完整匹配
        if original_text in text:
            score += 100
            matched.append(f'完整匹配({len(original_text)}字)')

        # 策略2：长子串匹配
        if score == 0:
            for L in range(min(len(original_text), 40), 7, -2):
                for s in range(len(original_text) - L + 1):
                    chunk = original_text[s:s+L]
                    if chunk in text:
                        score += L * 3
                        matched.append(f'子串{L}字')
                        break
                if score > 0:
                    break

        # 策略3：关键词交集
        word_hits = sum(1 for w in all_words if w in text)
        if word_hits >= 2:
            score += word_hits * 15
            matched.append(f'关键词{word_hits}个')
        elif word_hits == 1:
            score += 8

        if score > 0:
            scores.append((score, i, matched, text[:50]))

    if not scores:
        return None, 0

    scores.sort(reverse=True)
    best_score, best_idx, best_matched, snippet = scores[0]
    return best_idx, best_score


# ============================================================
# 修订操作
# ============================================================
def apply_revision(p_elem, rev_data, rev_id_mgr, author, date_str):
    """在段落中应用修订（w:del + w:ins）。找不到原文时返回 False。"""
    original = rev_data['original_text']
    revised  = rev_data['revised_text']
    runs = find_all_text_runs(p_elem)
    if not runs:
        return False

    match = find_runs_spanning_text(runs, original)
    if match is None:
        stripped = original.strip()
        match = find_runs_spanning_text(runs, stripped)

    if match is None:
        return False

    start_idx, end_idx, offset_start, offset_end = match
    first_r = runs[start_idx]['elem']
    rpr_elem = first_r.find(qn('rPr'))
    rpr_xml = ET.tostring(rpr_elem, encoding='unicode') if rpr_elem is not None else ''

    del_id = rev_id_mgr.next()
    ins_id = rev_id_mgr.next()

    # WPS 兼容性：获取段落 paraId
    para_id = p_elem.get(qn('paraId', W14)) or _gen_para_id()

    if start_idx == end_idx:
        _replace_run_within_single(p_elem, first_r, runs[start_idx]['text'],
                                   original, revised, rpr_xml,
                                   del_id, ins_id, author, date_str, para_id)
    else:
        _replace_run_across_multiple(p_elem, runs, start_idx, end_idx,
                                     original, revised, rpr_xml,
                                     del_id, ins_id, author, date_str, para_id)
    return True


def _replace_run_within_single(p_elem, run_elem, run_text,
                                original, revised, rpr_xml,
                                del_id, ins_id, author, date_str,
                                para_id=None):
    pos = run_text.find(original)
    if pos == -1:
        pos = run_text.find(original.strip())
        if pos == -1:
            return

    prefix = run_text[:pos]
    suffix = run_text[pos + len(original):]
    p_children = list(p_elem)
    r_idx = p_children.index(run_elem) if run_elem in p_children else -1
    if r_idx == -1:
        return

    try:
        p_elem.remove(run_elem)
    except ValueError:
        # 元素已被其他操作移除，跳过
        return
    new_runs = []
    if prefix:
        new_runs.append(_make_run(prefix, rpr_xml))
    new_runs.append(_make_del_run(original, del_id, author, date_str, para_id))
    new_runs.append(_make_ins_run(revised, ins_id, author, date_str, para_id))
    if suffix:
        new_runs.append(_make_run(suffix, rpr_xml))
    for i, nr in enumerate(new_runs):
        p_elem.insert(r_idx + i, nr)


def _replace_run_across_multiple(p_elem, runs, start_idx, end_idx,
                                   original, revised, rpr_xml,
                                   del_id, ins_id, author, date_str,
                                   para_id=None):
    run_elems = [runs[i]['elem'] for i in range(start_idx, end_idx + 1)]
    combined = ''.join(runs[i]['text'] for i in range(start_idx, end_idx + 1))
    pos = combined.find(original)
    if pos == -1:
        return

    prefix = runs[start_idx]['text'][:pos]
    suffix = runs[end_idx]['text'][pos + len(original):]
    all_children = list(p_elem)
    first_pos = all_children.index(run_elems[0])

    # 去重后再移除（防止同一元素被多次引用导致 ValueError）
    seen = set()
    for re_ in run_elems:
        rid = id(re_)
        if rid not in seen:
            seen.add(rid)
            try:
                p_elem.remove(re_)
            except ValueError:
                pass  # 已移除则跳过

    new_runs = []
    if prefix:
        new_runs.append(_make_run(prefix, rpr_xml))
    new_runs.append(_make_del_run(original, del_id, author, date_str, para_id))
    new_runs.append(_make_ins_run(revised, ins_id, author, date_str, para_id))
    if suffix:
        new_runs.append(_make_run(suffix, rpr_xml))
    for i, nr in enumerate(new_runs):
        p_elem.insert(first_pos + i, nr)


def _make_run(text, rpr_xml=''):
    r = ET.Element(qn('r'))
    if rpr_xml:
        try:
            rpr = ET.fromstring(f'<root xmlns:w="{W}">{rpr_xml}</root>')
            for child in list(rpr):
                r.append(child)
        except Exception:
            pass
    t = ET.SubElement(r, qn('t'))
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text
    return r


def _make_del_run(text, del_id, author, date_str, para_id=None):
    """
    删除文本（显示红色删除线）。
    <w:del w:id w:author w:date>
      <w:r w:rsidRPr>
        <w:rPr>
          <w:rFonts .../>
          <w:strike/>           ← 删除线
          <w:color w:val="FF0000"/> ← 红色
        </w:rPr>
        <w:delText .../>
      </w:r>
    </w:del>
    """
    d = ET.Element(qn('del'))
    d.set(qn('id'), str(del_id))
    d.set(qn('author'), _escape_xml(author))
    d.set(qn('date'), _escape_xml(date_str))

    r = ET.SubElement(d, qn('r'))
    r.set(qn('rsidRPr'), format(del_id, '08X'))

    rpr = ET.SubElement(r, qn('rPr'))
    rFonts = ET.SubElement(rpr, qn('rFonts'))
    font = get_system_font()
    rFonts.set(qn('ascii'), font)
    rFonts.set(qn('hAnsi'), font)
    rFonts.set(qn('eastAsia'), font)
    
    # 删除线 + 红色
    strike = ET.SubElement(rpr, qn('strike'))
    color = ET.SubElement(rpr, qn('color'))
    color.set(qn('val'), 'FF0000')

    delText = ET.SubElement(r, qn('delText'))
    delText.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    delText.text = text
    return d


def _make_ins_run(text, ins_id, author, date_str, para_id=None):
    """
    插入文本（显示蓝色 + 下划线）。
    <w:ins w:id w:author w:date>
      <w:r w:rsidRPr>
        <w:rPr>
          <w:color w:val="0000FF"/> ← 蓝色
          <w:u w:val="single"/>    ← 下划线
        </w:rPr>
        <w:t .../>
      </w:r>
    </w:ins>
    """
    i = ET.Element(qn('ins'))
    i.set(qn('id'), str(ins_id))
    i.set(qn('author'), _escape_xml(author))
    i.set(qn('date'), _escape_xml(date_str))

    r = ET.SubElement(i, qn('r'))
    r.set(qn('rsidRPr'), format(ins_id, '08X'))

    # 添加蓝色 + 下划线格式
    rpr = ET.SubElement(r, qn('rPr'))
    color = ET.SubElement(rpr, qn('color'))
    color.set(qn('val'), '0000FF')
    
    u = ET.SubElement(rpr, qn('u'))
    u.set(qn('val'), 'single')

    t = ET.SubElement(r, qn('t'))
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text
    return i


# ============================================================
# 批注操作（原生样式版）
# ============================================================
def apply_comment(p_elem, comment_data, comment_id_mgr, author, date_str):
    """
    在段落中插入批注（带原生 Word 样式）。

    返回 (cid, full_comment_text) 或 None
    找不到 highlight_text 时降级为整段批注。
    """
    highlight   = comment_data.get('highlight_text', '').strip()
    comment_txt = comment_data.get('comment') or comment_data.get('text', '')
    severity    = comment_data.get('severity', '')
    reason      = comment_data.get('reason', '').strip()
    legal_basis = comment_data.get('legal_basis', '').strip()
    suggestion  = comment_data.get('suggestion', '').strip()

    cid = comment_id_mgr.next()

    # ── 构造段落结构化批注文本 ──────────────────────────────────
    # 格式：标题行 + 若干段落（每个字段一段）
    sections = []
    if severity:
        sections.append(('severity', f'【{severity}】'))
    sections.append(('body', comment_txt))
    if reason:
        sections.append(('reason', f'【修改原因】{reason}'))
    if legal_basis:
        sections.append(('legal', f'【法律依据】{legal_basis}'))
    if suggestion:
        sections.append(('suggest', f'【修改建议】{suggestion}'))

    # 注册批注内容（带样式）
    if not highlight:
        # 整段批注
        ref_run = ET.Element(qn('r'))
        rpr = ET.SubElement(ref_run, qn('rPr'))
        rstyle = ET.SubElement(rpr, qn('rStyle'))
        rstyle.set(qn('val'), 'CommentReference')
        cref = ET.SubElement(ref_run, qn('commentReference'))
        cref.set(qn('id'), str(cid))
        p_elem.append(ref_run)
        return cid, _build_comment_text(sections)

    # 有高亮文本：插入 range markers
    runs = find_all_text_runs(p_elem)
    if not runs:
        return cid, _build_comment_text(sections)

    match = find_runs_spanning_text(runs, highlight)
    if match is None:
        stripped = highlight.strip()
        match = find_runs_spanning_text(runs, stripped)

    if match is None:
        # 降级：整段批注
        ref_run = ET.Element(qn('r'))
        rpr = ET.SubElement(ref_run, qn('rPr'))
        rstyle = ET.SubElement(rpr, qn('rStyle'))
        rstyle.set(qn('val'), 'CommentReference')
        cref = ET.SubElement(ref_run, qn('commentReference'))
        cref.set(qn('id'), str(cid))
        p_elem.append(ref_run)
        return cid, _build_comment_text(sections)

    start_idx, end_idx, _, _ = match
    first_r = runs[start_idx]['elem']
    last_r  = runs[end_idx]['elem']
    p_children = list(p_elem)
    first_pos = p_children.index(first_r) if first_r in p_children else 0
    last_pos  = p_children.index(last_r)  if last_r  in p_children else first_pos

    # ── 正确 OOXML 批注结构（来源: python-docx 实测标准）─────────────
    #
    #   <w:p>
    #     <w:pPr>...</w:pPr>           ← 段落属性（已有）
    #     <w:commentRangeStart w:id="N"/> ← ① 紧跟 </w:pPr> 之后
    #     <w:r>...<w:t>原文文字</w:t>...</w:r>  ← ② 原文 runs（保留）
    #     <w:commentRangeEnd w:id="N"/>   ← ③ 在原文 runs 之后
    #     <w:r><w:rPr><w:rStyle val="CommentReference"/>
    #              <w:commentReference w:id="N"/>
    #              <w14:commentReference w14:id="N"/></w:r> ← ④ 批注引用 run
    #   </w:p>
    #
    # 注意: w14:ref 在 OOXML 标准中为可选扩展，Word 2010+ 读取 w:commentReference
    # 即正确显示批注气泡。w14:ref 存在时可增强 Word 2010 兼容性。
    # ────────────────────────────────────────────────────────────────────

    cs = ET.Element(qn('commentRangeStart'))
    cs.set(qn('id'), str(cid))

    ce = ET.Element(qn('commentRangeEnd'))
    ce.set(qn('id'), str(cid))

    cr = ET.Element(qn('r'))
    rpr2 = ET.SubElement(cr, qn('rPr'))
    rs = ET.SubElement(rpr2, qn('rStyle'))
    rs.set(qn('val'), 'CommentReference')
    cref2 = ET.SubElement(cr, qn('commentReference'))
    cref2.set(qn('id'), str(cid))
    # w14:commentReference（Word 2010 增强）
    cref2_w14 = ET.SubElement(cr, qn('commentReference', W14))
    cref2_w14.set(qn('id', W14), str(cid))

    # ① commentRangeStart：紧跟 </w:pPr> 之后
    p_elem.insert(first_pos, cs)

    # ③ commentRangeEnd：在 last_r 之后
    #    由于已插入 cs（位置 first_pos），last_r 的新位置 = last_pos + 1
    try:
        last_new_idx = list(p_elem).index(last_r) + 1
        p_elem.insert(last_new_idx, ce)
        # ④ commentReference run：在 commentRangeEnd 之后
        cr_new_idx = list(p_elem).index(ce) + 1
        p_elem.insert(cr_new_idx, cr)
    except ValueError:
        # last_r 不在当前 p_elem 中（罕见 XML 结构），降级为末尾追加
        p_elem.append(ce)
        p_elem.append(cr)

    return cid, _build_comment_text(sections)


def _build_comment_text(sections):
    """将 sections 列表转为换行分隔的纯文本（供 add_to_comments_xml 使用）"""
    return '\n'.join(text for _, text in sections)


def ensure_comments_xml(doc_dir):
    """确保 comments.xml 存在，返回路径"""
    comments_path = doc_dir / 'word' / 'comments.xml'
    if not comments_path.exists():
        root = ET.Element(qn('comments'))
        tree = ET.ElementTree(root)
        pass  # ET.indent disabled (corrupts namespace attrs on macOS Python3.9)
        tree.write(comments_path, encoding='UTF-8', xml_declaration=True)
        _ensure_content_type(doc_dir, 'comments.xml',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml')
        _ensure_rel(doc_dir, 'comments.xml',
            'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
    return comments_path


def _ensure_content_type(doc_dir, filename, content_type):
    ct_path = doc_dir / '[Content_Types].xml'
    if not ct_path.exists():
        return
    tree = ET.parse(ct_path)
    root = tree.getroot()
    CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
    ns_ct = f'{{{CT}}}Override' if False else f'{{{CT}}}'
    # 简单追加
    override = ET.SubElement(root, f'{{{CT}}}Override')
    override.set('PartName', f'/{filename}')
    override.set('ContentType', content_type)
    tree.write(ct_path, encoding='UTF-8', xml_declaration=True)


def _ensure_rel(doc_dir, target, rel_type):
    rels_path = doc_dir / 'word' / '_rels' / 'document.xml.rels'
    if not rels_path.exists():
        return
    tree = ET.parse(rels_path)
    root = tree.getroot()
    R_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
    rels_ns = f'{{{R_NS}}}'
    existing = root.find(f'.//{rels_ns}Relationship[@Target="{target}"]')
    if existing is not None:
        return
    max_id = 0
    for rel in root.iter(f'{rels_ns}Relationship'):
        rid = rel.get('Id', 'rId0')
        if rid.startswith('rId'):
            try: max_id = max(max_id, int(rid[3:]))
            except ValueError: pass
    new_id = f'rId{max_id + 1}'
    rel = ET.SubElement(root, f'{rels_ns}Relationship')
    rel.set('Id', new_id)
    rel.set('Type', rel_type)
    rel.set('Target', target)
    tree.write(rels_path, encoding='UTF-8', xml_declaration=True)


def add_to_comments_xml(comments_path, comment_id, author, date_str,
                         comment_text, severity=''):
    """
    向 comments.xml 添加一条批注（原生样式：宋体五号 + 风险颜色）

    comment_text: 换行分隔的多段落文本
    severity: 高风险|中风险|低风险|信息
    """
    if comments_path.exists():
        tree = ET.parse(comments_path)
        root = tree.getroot()
    else:
        root = ET.Element(qn('comments'))
        tree = ET.ElementTree(root)

    comment = ET.SubElement(root, qn('comment'))
    comment.set(qn('id'), str(comment_id))
    comment.set(qn('author'), _escape_xml(author))
    comment.set(qn('date'), _escape_xml(date_str))
    comment.set(qn('initials'), 'CL')
    # w14:commentId（Word 2010 批注识别关键）
    comment.set(qn('commentId', W14), str(comment_id))

    # 逐行解析 comment_text，生成段落结构
    lines = comment_text.split('\n')
    first_line = True
    for line in lines:
        if not line.strip():
            continue
        p = ET.SubElement(comment, qn('p'))
        ppr = ET.SubElement(p, qn('pPr'))
        pstyle = ET.SubElement(ppr, qn('pStyle'))
        pstyle.set(qn('val'), 'CommentText')

        r = ET.SubElement(p, qn('r'))
        rpr = ET.SubElement(r, qn('rPr'))

        # 宋体五号基础字体（使用配置）
        rfonts = ET.SubElement(rpr, qn('rFonts'))
        font = get_system_font()
        rfonts.set(qn('eastAsia', W14), font)
        rfonts.set(qn('ascii', W14), font)
        rfonts.set(qn('hAnsi', W14), font)
        sz = ET.SubElement(rpr, qn('sz'))
        sz.set(qn('val'), str(DEFAULT_FONT_SIZE))
        szcs = ET.SubElement(rpr, qn('szCs'))
        szcs.set(qn('val'), str(DEFAULT_FONT_SIZE))

        # 风险颜色（第一行标题用颜色区分）
        if first_line and severity in SEVERITY_COLORS:
            color = ET.SubElement(rpr, qn('color'))
            color.set(qn('val'), SEVERITY_COLORS[severity])
            b = ET.SubElement(rpr, qn('b'))  # 标题加粗
            first_line = False
        else:
            first_line = False

        t = ET.SubElement(r, qn('t'))
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = line

    pass  # ET.indent disabled (corrupts namespace attrs on macOS Python3.9)
    tree.write(comments_path, encoding='UTF-8', xml_declaration=True)


# ============================================================
# 读取修订痕迹（新增：解析对方 Word 修订版）
# ============================================================
def parse_tracked_changes(docx_path):
    """
    读取 docx 中的修订痕迹，返回结构化列表。

    返回:
    {
        'insertions': [{'author', 'date', 'text', 'paragraph_index'}, ...],
        'deletions':  [{'author', 'date', 'text', 'paragraph_index'}, ...],
        'total': int
    }
    """
    result = {'insertions': [], 'deletions': [], 'total': 0}
    try:
        with zipfile.ZipFile(docx_path, 'r') as zf:
            xml_data = zf.read('word/document.xml')
    except Exception:
        return result

    tree = ET.fromstring(xml_data)
    body = tree.find(qn('body'))
    if body is None:
        return result

    paras = list(body.iter(qn('p')))
    for p_idx, p in enumerate(paras):
        p_text = get_paragraph_text(p).strip()
        if not p_text:
            continue

        for ins in p.iter(qn('ins')):
            ins_text = ''.join(t.text or '' for t in ins.iter(qn('t')))
            if ins_text.strip():
                result['insertions'].append({
                    'author': ins.get(qn('author'), '未知'),
                    'date':   ins.get(qn('date'), ''),
                    'text':   ins_text,
                    'paragraph_index': p_idx,
                    'context': p_text[:80],
                })

        for d in p.iter(qn('del')):
            del_text = ''.join(t.text or '' for t in d.iter(qn('delText')))
            if del_text.strip():
                result['deletions'].append({
                    'author': d.get(qn('author'), '未知'),
                    'date':   d.get(qn('date'), ''),
                    'text':   del_text,
                    'paragraph_index': p_idx,
                    'context': p_text[:80],
                })

    result['total'] = len(result['insertions']) + len(result['deletions'])
    return result


# ============================================================
# 主流程
# ============================================================
def apply_changes(doc_dir, changes_json_path, dry_run=False):
    """
    应用变更到 unpacked docx 目录。

    增强：段落索引精确匹配（JSON索引失败 → 语义搜索 → 降级批注）
    """
    doc_dir = Path(doc_dir)
    doc_xml_path = doc_dir / 'word' / 'document.xml'

    if not doc_dir.exists():
        return {'success': False, 'error': f'目录不存在: {doc_dir}'}
    if not doc_xml_path.exists():
        return {'success': False, 'error': f'文件不存在: {doc_xml_path}'}

    with open(changes_json_path, 'r', encoding='utf-8') as f:
        changes = json.load(f)

    author   = changes.get('author', 'Claude')
    date_str = changes.get('date', datetime.now(timezone.utc).isoformat())
    revisions = changes.get('revisions', [])
    comments  = changes.get('comments', [])

    tree = ET.parse(doc_xml_path)
    root = tree.getroot()
    body = root.find(qn('body'))
    if body is None:
        return {'success': False, 'error': '无法找到文档主体'}

    paragraphs = list(body.iter(qn('p')))
    if not paragraphs:
        return {'success': False, 'error': '文档中没有段落'}

    rev_id_mgr = RevisionIdManager()
    comment_id_mgr = CommentIdManager()

    # 预扫描已有 ID
    for elem in root.iter():
        for attr in [qn('id')]:
            val = elem.get(attr)
            if val:
                try:
                    rev_id_mgr.mark_used(int(val))
                    comment_id_mgr.mark_used(int(val))
                except (ValueError, TypeError):
                    pass

    applied_revisions   = []
    failed_revisions    = []
    applied_comments    = []

    # ── 应用修订 ──────────────────────────────────────────────
    total = len(revisions)
    for i, rev in enumerate(revisions, 1):
        # 进度提示
        if total > 5 and i % 5 == 0:
            print(f"  ⏳ 应用修订 {i}/{total}...")
        
        p_idx     = rev.get('paragraph_index')
        search_hint = rev.get('search_hint', rev.get('original_text', ''))
        original  = rev.get('original_text', '')
        fallback  = rev.get('fallback_to_comment', True)

        # 尝试用 JSON 索引
        ok = False
        if p_idx is not None and 0 <= p_idx < len(paragraphs):
            p_elem = paragraphs[p_idx]
            ok = apply_revision(p_elem, rev, rev_id_mgr, author, date_str)

        # 索引失败 → 语义搜索
        if not ok:
            best_idx, score = find_paragraph_index_by_search(
                paragraphs, search_hint, original)
            if best_idx is not None and score >= 15:
                p_idx = best_idx
                p_elem = paragraphs[p_idx]
                ok = apply_revision(p_elem, rev, rev_id_mgr, author, date_str)

        if ok:
            applied_revisions.append({
                'paragraph_index': p_idx,
                'original_text': original[:50],
            })
            # ✅ v2.7.9 新增：修订成功后，自动为有 comment 字段的修订添加配套批注
            # 原理：修订痕迹显示"改了什么"，批注说明"为什么改"
            if rev.get('comment'):
                cs_path = ensure_comments_xml(doc_dir)
                comment_data = {
                    'highlight_text': rev.get('highlight_text', original[:30] if len(original) > 30 else original),
                    'comment': rev['comment'],
                    'severity': rev.get('severity', '中风险'),
                }
                result = apply_comment(p_elem, comment_data, comment_id_mgr, author, date_str)
                if result:
                    cid, full_text = result
                    add_to_comments_xml(cs_path, cid, author, date_str,
                                        full_text, comment_data.get('severity', ''))
                    applied_comments.append({
                        'paragraph_index': p_idx,
                        'comment_id': cid,
                        'comment': rev['comment'][:50],
                        'auto_generated': True,  # 标记为自动生成
                    })
        else:
            if fallback:
                # 降级为批注（给出修订建议）
                rev['paragraph_index'] = p_idx
                rev['comment'] = (
                    f"【建议修订】原文：{original}\n"
                    f"【建议改为】{rev.get('revised_text','')}\n"
                    f"【原因】{rev.get('reason','')}"
                )
                rev['severity'] = '中风险'
                rev['highlight_text'] = original
                result = apply_comment(
                    paragraphs[p_idx or 0] if p_idx else paragraphs[0],
                    rev, comment_id_mgr, author, date_str)
                if result:
                    cid, full_text = result
                    cs_path = ensure_comments_xml(doc_dir)
                    add_to_comments_xml(cs_path, cid, author, date_str,
                                        full_text, rev.get('severity', ''))
                    applied_comments.append({
                        'paragraph_index': p_idx or 0,
                        'comment_id': cid,
                        'comment': original[:50],
                        'fallback': True,
                    })
            else:
                failed_revisions.append({
                    'original_text': original[:50],
                    'error': '未找到匹配的文本'
                })

    # ── 应用批注 ──────────────────────────────────────────────
    cs_path = ensure_comments_xml(doc_dir)
    for comm in comments:
        p_idx = comm.get('paragraph_index')
        search_hint = comm.get('highlight_text', '') or comm.get('comment', '')

        # 尝试 JSON 索引
        ok = False
        if p_idx is not None and 0 <= p_idx < len(paragraphs):
            result = apply_comment(
                paragraphs[p_idx], comm, comment_id_mgr, author, date_str)
            ok = result is not None

        # 索引失败 → 语义搜索
        if not ok:
            best_idx, score = find_paragraph_index_by_search(
                paragraphs, search_hint, comm.get('highlight_text', ''))
            if best_idx is not None and score >= 10:
                p_idx = best_idx
                result = apply_comment(
                    paragraphs[p_idx], comm, comment_id_mgr, author, date_str)
                ok = result is not None

        if ok:
            cid, full_text = result
            add_to_comments_xml(cs_path, cid, author, date_str,
                                full_text, comm.get('severity', ''))
            applied_comments.append({
                'paragraph_index': p_idx,
                'comment_id': cid,
                'comment': comm.get('comment', '')[:50],
            })
        else:
            applied_comments.append({
                'paragraph_index': p_idx,
                'comment': comm.get('comment', '')[:50],
                'error': '无法定位段落，批注失败'
            })

    if dry_run:
        return {
            'success': True, 'dry_run': True,
            'revisions_applied': len(applied_revisions),
            'revisions_failed': len(failed_revisions),
            'comments_added': len(applied_comments),
        }

    tree.write(doc_xml_path, encoding='UTF-8', xml_declaration=True)

    # ── 批注 Word 兼容性修复 ─────────────────────────────────────────────
    # 在 document.xml 根标签注入 xmlns:w14（lxml 无法直接输出 w14: 前缀，
    # 用文本方式注入，确保 Word 2010+ 能识别 w14:commentId 属性）
    _inject_w14_namespace(doc_xml_path)

    # 生成 commentsExtended.xml（Word 2013+ 批注扩展）
    _generate_comments_extended(doc_dir, comment_id_mgr)

    # 修正 Content_Types.xml 的 PartName 路径（/comments.xml → /word/comments.xml）
    _fix_comments_content_type(doc_dir)

    return {
        'success': True,
        'revisions_applied': applied_revisions,
        'revisions_failed': failed_revisions,
        'comments_added': applied_comments,
        'total_revisions': len(revisions),
        'total_comments': len(comments),
    }


def _inject_w14_namespace(doc_xml_path):
    """
    在 document.xml 根标签注入 xmlns:w14="..." 和 mc:Ignorable="w14"。
    lxml 无法直接输出 w14: 前缀（XML 保留名），用文本方式注入。
    """
    W14_URI = 'http://schemas.microsoft.com/office/word/2010/wordml'
    MC_NS   = 'http://schemas.openxmlformats.org/markup-compatibility/2006'

    with open(doc_xml_path, 'r', encoding='utf-8') as f:
        xml_str = f.read()

    # 找 <w:document ...> 根标签
    root_start = xml_str.find('<w:document')
    if root_start < 0:
        return
    root_end = xml_str.find('>', root_start)
    root_tag = xml_str[root_start:root_end + 1]

    # 添加 xmlns:w14（若不存在）
    if 'xmlns:w14=' not in root_tag:
        new_root = root_tag[:-1] + ' xmlns:w14="' + W14_URI + '">'
        xml_str = xml_str[:root_start] + new_root + xml_str[root_end + 1:]

    # 添加 mc:Ignorable="w14"（若不存在）
    if 'mc:Ignorable' in xml_str[:root_end + 1]:
        if 'w14' not in xml_str[root_start:root_end + 1]:
            xml_str = xml_str[:root_end] + ' mc:Ignorable="w14">' + xml_str[root_end + 1:]
    else:
        xml_str = xml_str[:root_end] + ' mc:Ignorable="w14">' + xml_str[root_end + 1:]

    with open(doc_xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)


def _generate_comments_extended(doc_dir, comment_id_mgr):
    """
    生成 word/commentsExtended.xml（Word 2013+ 批注扩展）。
    同时更新 document.xml.rels 注册关系。
    """
    W15_URI = 'http://schemas.microsoft.com/office/word/2012/wordml'
    REL_NS  = 'http://schemas.microsoft.com/office/2011/relationships/commentsExtended'
    PKG_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
    MC_NS   = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
    CT_NS   = 'http://schemas.openxmlformats.org/package/2006/content-types'

    ce_path = doc_dir / 'word' / 'commentsExtended.xml'

    # 生成 commentsExtended.xml（文本拼接，规避 lxml 的 ns0: 前缀问题）
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w15:commentsEx xmlns:w15="' + W15_URI + '" '
        'xmlns:mc="' + MC_NS + '" mc:Ignorable="w15">'
    ]
    for nid in sorted(comment_id_mgr.used):
        para_id = "%08X" % (nid * 0x13579BDF + 0x12345678)
        lines.append('  <w15:commentEx w15:paraId="' + para_id + '" w15:done="0"/>')
    lines.append('</w15:commentsEx>')
    ce_xml = '\n'.join(lines) + '\n'

    with open(ce_path, 'w', encoding='utf-8') as f:
        f.write(ce_xml)

    # 更新 document.xml.rels（添加 commentsExtended 关系）
    rels_path = doc_dir / 'word' / '_rels' / 'document.xml.rels'
    if rels_path.exists():
        with open(rels_path, 'r', encoding='utf-8') as f:
            rels_str = f.read()

        if 'commentsExtended' not in rels_str:
            # 找最高 rId
            import re
            rids = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels_str)]
            next_rid = max(rids) + 1 if rids else 1
            RELS_ENTRY = ('<ns0:Relationship Id="rId' + str(next_rid) + '" '
                          'Type="' + REL_NS + '" Target="commentsExtended.xml"/>')
            rels_str = rels_str.replace('</Relationships>',
                                         RELS_ENTRY + '</Relationships>')
            rels_str = rels_str.replace('<Relationship ',
                                         '<ns0:Relationship ')
            with open(rels_path, 'w', encoding='utf-8') as f:
                f.write(rels_str)

    # 更新 Content_Types.xml（注册 commentsExtended.xml）
    ct_path = doc_dir / '[Content_Types].xml'
    if ct_path.exists():
        with open(ct_path, 'r', encoding='utf-8') as f:
            ct_str = f.read()

        if 'commentsExtended' not in ct_str:
            # 修正 /comments.xml → /word/comments.xml（OPC 规范路径）
            ct_str = ct_str.replace(
                'PartName="/comments.xml"',
                'PartName="/word/comments.xml"'
            )
            # 添加 commentsExtended Override
            EXT_OVR = ('<ns0:Override PartName="/word/commentsExtended.xml" '
                       'ContentType="application/vnd.openxmlformats-officedocument.'
                       'wordprocessingml.commentsExtended+xml"/>')
            ct_str = ct_str.replace('</Types>', EXT_OVR + '</Types>')
            ct_str = ct_str.replace('<Override ', '<ns0:Override ')
            with open(ct_path, 'w', encoding='utf-8') as f:
                f.write(ct_str)


def _fix_comments_content_type(doc_dir):
    """修正 comments.xml 的 Content_Types.xml PartName 路径"""
    ct_path = doc_dir / '[Content_Types].xml'
    if ct_path.exists():
        with open(ct_path, 'r', encoding='utf-8') as f:
            ct_str = f.read()
        if 'PartName="/comments.xml"' in ct_str:
            ct_str = ct_str.replace(
                'PartName="/comments.xml"',
                'PartName="/word/comments.xml"'
            )
            with open(ct_path, 'w', encoding='utf-8') as f:
                f.write(ct_str)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='将审核变更写入 docx（修订痕迹 + 批注气泡）v2.4.0')
    parser.add_argument('doc_dir', help='unpacked docx 目录')
    parser.add_argument('changes_json', help='变更指令 JSON 文件')
    parser.add_argument('--dry-run', action='store_true', help='仅验证，不写入')
    args = parser.parse_args()

    result = apply_changes(Path(args.doc_dir), Path(args.changes_json), args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
