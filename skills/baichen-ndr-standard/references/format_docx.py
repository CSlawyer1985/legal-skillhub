"""NDR / DR 系统一文档生成入口。所有 NDR/DR 技能通过 create_document() 生成 .docx。"""
import os, sys
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)
from format_base import *
import re


# ── 共享三重复核（金额三要素/高危错别字/主体指代一致·可选）──
def _post_check_content(content_blocks, subject_terms=None):
    """共享层生成后校验。返回 (ok, errors[])。非阻断：失败仅打印警告。"""
    errors = []
    _CN_NUM = '壹贰叁肆伍陆柒捌玖拾佰仟万亿零整角分'
    _TYPO = [('军无异议', '均无异议'), ('的的', '的'), ('了了', '了'), ('在在', '在'), ('是是', '是')]
    texts = []
    for b in content_blocks:
        t = b.get('text', '')
        if isinstance(t, list):
            t = '\n'.join(str(x) for x in t)
        if t:
            texts.append(str(t))
        attrs = b.get('attrs', {}) or {}
        for k in ('lines', 'rows'):
            v = attrs.get(k)
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, (list, tuple)):
                        texts.extend(str(x) for x in item)
                    else:
                        texts.append(str(item))
    full = '\n'.join(texts)
    for m in re.finditer(r'人民币[^。；;]{0,40}', full):
        seg = m.group(0)
        has_cn = any(c in _CN_NUM for c in seg)
        has_digit = re.search(r'\d', seg) is not None
        if not (has_cn and has_digit):
            errors.append('[金额] 双标注不完整: "%s"（须 人民币+汉字大写+（￥数字）成对）' % seg[:30])
        if re.search(r'[壹贰叁肆伍陆柒捌玖拾佰仟万亿零整]{1,10}\d', seg):
            errors.append('[金额] 疑似半截大写: "%s"（大写与数字粘连）' % seg[:30])
    for wrong, right in _TYPO:
        idx = full.find(wrong)
        if idx >= 0:
            errors.append('[错别字] "%s" 应为 "%s"（...%s...）' % (wrong, right, full[max(0, idx - 15):idx + 15]))
    if subject_terms and len(subject_terms) == 2:
        a, b = subject_terms
        ca, cb = full.count(a), full.count(b)
        if ca > 0 and cb > 0:
            errors.append('[主体指代] 混用: 同时出现"%s"×%d 与"%s"×%d，须全文统一' % (a, ca, b, cb))
    return (len(errors) == 0, errors)

# ── 内部辅助 ──

# 跨平台字体映射 _EA_FONT_MAP / _ea_font 由 format_base 统一提供（from format_base import *）

def _east_asian(run, font_name):
    run.font.name = font_name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    rfonts.set(qn('w:eastAsia'), _ea_font(font_name))
    rfonts.set(qn('w:ascii'), _ea_font(font_name))
    rfonts.set(qn('w:hAnsi'), _ea_font(font_name))

def _setup_page(doc):
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = MARGIN_TB
    sec.bottom_margin = MARGIN_TB
    sec.left_margin = MARGIN_LR
    sec.right_margin = MARGIN_LR

def _setup_normal_style(doc):
    s = doc.styles['Normal']
    s.font.name = FONT_VARIANT
    s.font.size = BODY_SIZE
    s.paragraph_format.line_spacing = LINE_SPACING
    s.paragraph_format.space_after = Pt(0)
    rpr = s.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.append(rf)
    rf.set(qn('w:eastAsia'), _ea_font(FONT_VARIANT))
    rf.set(qn('w:ascii'), _ea_font(FONT_VARIANT))
    rf.set(qn('w:hAnsi'), _ea_font(FONT_VARIANT))

def _add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    _east_asian(r, TITLE_FONT)
    r.font.size = Pt(22)
    r.bold = True
    return p

def _add_subtitle(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    r = p.add_run(text)
    _east_asian(r, TITLE_FONT)
    r.font.size = Pt(16)
    r.bold = True
    return p

def _add_body(doc, text, indent=True):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = FIRST_INDENT
    if isinstance(text, list):
        for line in text:
            r = p.add_run(line)
            _east_asian(r, FONT_VARIANT)
            r.font.size = _resolve_size(BODY_SIZE)
    else:
        r = p.add_run(text)
        _east_asian(r, FONT_VARIANT)
        r.font.size = _resolve_size(BODY_SIZE)
    return p

def _add_section_title(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run(text)
    _east_asian(r, TITLE_FONT)
    r.font.size = BODY_SIZE
    r.bold = True
    return p

def _add_signature_block(doc, lines, date_str=None):
    for line in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(line)
        _east_asian(r, FONT_VARIANT)
        r.font.size = BODY_SIZE
    if date_str:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Pt(6)
        r = p.add_run(_to_chinese_date(date_str))
        _east_asian(r, FONT_VARIANT)
        r.font.size = BODY_SIZE

# ── 扩展辅助 ──

def _add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = BODY_SIZE
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    _east_asian(r, TITLE_FONT)
    r.font.size = Pt(14)
    r.bold = True
    return p

def _add_h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    _east_asian(r, FONT_VARIANT)
    r.font.size = _resolve_size(BODY_SIZE)
    r.bold = True
    return p

def _add_center(doc, text, attrs=None):
    if attrs is None:
        attrs = {}
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    if attrs.get('space_before'):
        p.paragraph_format.space_before = attrs['space_before']
    if attrs.get('space_after'):
        p.paragraph_format.space_after = attrs['space_after']
    r = p.add_run(text)
    font_name = attrs.get('font_name', FONT_VARIANT)
    _east_asian(r, font_name)
    r.font.size = _resolve_size(attrs.get('size', BODY_SIZE))
    r.bold = attrs.get('bold', False)
    return p

def _add_right(doc, text, attrs=None):
    if attrs is None:
        attrs = {}
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    if attrs.get('space_before'):
        p.paragraph_format.space_before = attrs['space_before']
    r = p.add_run(text)
    font_name = attrs.get('font_name', FONT_VARIANT)
    _east_asian(r, font_name)
    r.font.size = _resolve_size(attrs.get('size', BODY_SIZE))
    r.bold = attrs.get('bold', False)
    if attrs.get('color'):
        from docx.shared import RGBColor
        r.font.color.rgb = RGBColor(*attrs['color'])
    return p

def _add_list_item(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(1.27)
    r = p.add_run('• ' + text)
    _east_asian(r, FONT_VARIANT)
    r.font.size = _resolve_size(BODY_SIZE)
    return p

def _add_info_block(doc, lines):
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        if i == 0:
            p.paragraph_format.space_before = Pt(6)
        r = p.add_run(line)
        _east_asian(r, FONT_VARIANT)
        r.font.size = _resolve_size(BODY_SIZE)

def _add_page_break(doc):
    from docx.oxml import OxmlElement
    p = doc.add_paragraph()
    run = p.add_run()
    br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    run._element.append(br)

def _add_evidence_table(doc, headers, rows):
    from docx.enum.table import WD_TABLE_ALIGNMENT
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        r = hdr[i].paragraphs[0].add_run(h)
        _east_asian(r, TITLE_FONT)
        r.font.size = Pt(11)
        r.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ''
            r = cells[i].paragraphs[0].add_run(str(val))
            _east_asian(r, FONT_VARIANT)
            r.font.size = Pt(11)

def _add_bold_body(doc, text, indent=True):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = FIRST_INDENT
    r = p.add_run(text)
    _east_asian(r, FONT_VARIANT)
    r.font.size = _resolve_size(BODY_SIZE)
    r.bold = True
    return p

# ── 公共入口 ──

def create_document(content_blocks, output_path=None, title=None, meta=None, auto_title=True):
    """
    统一文档生成入口——所有 NDR/DR 技能共用此函数。

    content_blocks: [{type, text, attrs}]
      type: 'title'|'subtitle'|'body'|'body_ni'|'section'|'heading'|'signature'|'table'|'blank'
            |'h2'|'h3'|'center'|'right'|'list_item'|'info'|'page_break'|'evidence_table'|'bold'
      text: str | [str]
      attrs: {lines: [str], date: str, size, bold, font_name, color, space_before, space_after,
              headers: [str], rows: [[str]], cols: [str]}

    output_path: 输出路径。None 时由 build_filename 自动生成
    title:       文档标题（文字）
    meta:        {doc_type, party, matter, date, court, case_number}
    auto_title:  是否自动从 content_blocks 提取首个 title 并前置渲染（默认 True）

    返回: Document 对象
    """
    doc = Document()
    _setup_page(doc)
    _setup_normal_style(doc)

    # 标题：优先 meta 中显式提供的 title，其次首个 content_block 的 title 类型
    doc_title = title
    if auto_title and doc_title is None and content_blocks:
        for b in content_blocks:
            if b.get('type') == 'title':
                doc_title = b.get('text', '')
                break
    if doc_title:
        _add_title(doc, doc_title)

    # 渲染内容块（auto_title 模式下跳过已作为标题使用的第一个 title 块）
    title_seen = False
    for block in content_blocks:
        bt = block.get('type', 'body')
        text = block.get('text', '')
        attrs = block.get('attrs', {}) or {}

        if bt == 'title':
            if auto_title and not title_seen:
                title_seen = True
                if doc_title is None:
                    _add_title(doc, text)
                continue
            _add_title(doc, text)

        elif bt == 'subtitle':
            _add_subtitle(doc, text)

        elif bt == 'section':
            _add_section_title(doc, text)

        elif bt in ('body', 'body_ni'):
            _add_body(doc, text, indent=(bt == 'body'))

        elif bt == 'heading':
            _add_section_title(doc, text)

        elif bt == 'signature':
            lines = attrs.get('lines', [text] if isinstance(text, str) else text)
            if not isinstance(lines, list):
                lines = [lines]
            _add_signature_block(doc, lines, attrs.get('date', meta.get('date') if meta else None))

        elif bt == 'table':
            rows = attrs.get('rows', [])
            cols = attrs.get('cols', [])
            if rows and cols:
                table = doc.add_table(rows=len(rows) + 1, cols=len(cols))
                table.style = 'Table Grid'
                for i, h in enumerate(cols):
                    cell = table.rows[0].cells[i]
                    r = cell.paragraphs[0].add_run(h)
                    _east_asian(r, FONT_VARIANT)
                    r.font.size = _resolve_size(BODY_SIZE)
                    r.bold = True
                for ri, row in enumerate(rows):
                    for ci, val in enumerate(row):
                        cell = table.rows[ri + 1].cells[ci]
                        r = cell.paragraphs[0].add_run(str(val))
                        _east_asian(r, FONT_VARIANT)
                        r.font.size = _resolve_size(BODY_SIZE)

        elif bt == 'h2':
            _add_h2(doc, text)

        elif bt == 'h3':
            _add_h3(doc, text)

        elif bt == 'center':
            _add_center(doc, text, attrs)

        elif bt == 'right':
            _add_right(doc, text, attrs)

        elif bt == 'list_item':
            _add_list_item(doc, text)

        elif bt == 'info':
            _add_info_block(doc, attrs.get('lines', [text] if isinstance(text, str) else text))

        elif bt == 'page_break':
            _add_page_break(doc)

        elif bt == 'evidence_table':
            _add_evidence_table(doc, attrs.get('headers', []), attrs.get('rows', []))

        elif bt == 'bold':
            _add_bold_body(doc, text, indent=True)

        elif bt == 'blank':
            doc.add_paragraph()

    # 自动落款日期（如果 meta 中有 date 但 content_blocks 中没有 signature 块）
    if meta and meta.get('date') and not any(b.get('type') == 'signature' for b in content_blocks):
        _add_signature_block(doc, [], meta['date'])

    # 共享三重复核（非阻断：失败打印警告，由调用方决定修正后重生成）
    try:
        _ok, _errs = _post_check_content(content_blocks, (meta or {}).get('subject_terms'))
        if not _ok:
            for _e in _errs:
                print('[POST-CHECK FAIL] %s' % _e, file=sys.stderr)
        else:
            print('[POST-CHECK] 三重复核通过（金额/错别字/主体指代）', file=sys.stderr)
    except Exception as _e:
        print('[POST-CHECK] 校验异常（不影响输出）: %s' % _e, file=sys.stderr)


    # 输出
    if output_path is None and meta:
        output_path = build_filename(
            meta.get('doc_type', 'document'),
            meta.get('party', ''),
            meta.get('matter', '')
        )

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) if os.path.dirname(output_path) else '.', exist_ok=True)
        doc.save(output_path)

    return doc
