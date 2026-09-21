"""
介绍信生成脚本（调取案件卷宗）
A5横向每张一份；支持多份合并到A4一页（上下各一张，中间虚线裁切线）。
"""
import argparse
import json
import os
import sys
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from user_config import load_config


def set_font(run, name_cn='仿宋_GB2312', name_en='Times New Roman', size=12, bold=False):
    run.font.name = name_en
    run.font.size = Pt(size)
    run.font.bold = bold
    r = run._element
    r.rPr.rFonts.set(qn('w:eastAsia'), name_cn)


def add_p(doc, text, alignment=WD_ALIGN_PARAGRAPH.CENTER, font_cn='仿宋_GB2312',
          font_en='Times New Roman', size=12, bold=False, space_before=0, space_after=0,
          first_line_indent=None):
    p = doc.add_paragraph()
    p.alignment = alignment
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if first_line_indent is not None:
        pf.first_line_indent = Cm(first_line_indent)
    pf.line_spacing = Pt(size * 1.3)
    run = p.add_run(text)
    set_font(run, font_cn, font_en, size, bold)
    return p


def add_cut_line(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    run = p.add_run('─' * 50)
    set_font(run, '仿宋_GB2312', 'Times New Roman', size=6)


def make_letter_content(doc, config, court_name, case_number, parties, cause, letter_no,
                         usable_cm=13.0):
    """在文档中追加一份介绍信内容，自动调整字号确保不溢出"""
    firm = config.get('law_firm', '律师事务所')
    lawyer = config.get('name', '律师')
    license_no = config.get('license_number', '')

    # ── 参考版式 ──
    ref = {
        'title':           {'size': 15, 'after': 4,  'lines': 1},
        'letter_no':       {'size': 11, 'after': 6,  'lines': 1},
        'court_greeting':  {'size': 11, 'after': 2,  'lines': 1},
        'body_intro':      {'size': 11, 'after': 2,  'lines': 1},
        'case_number':     {'size': 11, 'after': 1,  'lines': 1},
        'parties':         {'size': 11, 'after': 1,  'lines': 1},
        'cause':           {'size': 11, 'after': 3,  'lines': 1},
        'please':          {'size': 11, 'after': 3,  'lines': 1},
        'cizhi':           {'size': 11, 'after': 4,  'lines': 1},
        'court_end':       {'size': 11, 'after': 8,  'lines': 1},
        'seal':            {'size': 10, 'after': 1,  'lines': 1},
        'date':            {'size': 10, 'after': 0,  'lines': 1},
    }

    PT_TO_CM = 1 / 28.35
    total_h = 0
    for v in ref.values():
        total_h += v['size'] * 1.3 * PT_TO_CM * v['lines'] + v['after'] * PT_TO_CM

    ratio = min(1.0, usable_cm / max(total_h, 0.1))

    def scale(v):
        return max(8, round(v * ratio))

    # ── 生成（先标题，再文号）──
    add_p(doc, '介 绍 信', font_cn='黑体',
          size=scale(ref['title']['size']), bold=True,
          space_after=scale(ref['title']['after']))

    add_p(doc, letter_no, size=scale(ref['letter_no']['size']),
          space_after=scale(ref['letter_no']['after']))

    add_p(doc, f'{court_name}：',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['court_greeting']['size']),
          space_after=scale(ref['court_greeting']['after']))

    add_p(doc, f'兹介绍{lawyer}律师（执业证号：{license_no}）前往贵院调取已归档的以下案件诉讼卷宗：',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['body_intro']['size']),
          space_after=scale(ref['body_intro']['after']),
          first_line_indent=0.74)

    add_p(doc, f'案号：{case_number}',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['case_number']['size']),
          space_after=scale(ref['case_number']['after']),
          first_line_indent=0.74)

    add_p(doc, f'当事人：{parties}',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['parties']['size']),
          space_after=scale(ref['parties']['after']),
          first_line_indent=0.74)

    add_p(doc, f'案由：{cause}',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['cause']['size']),
          space_after=scale(ref['cause']['after']),
          first_line_indent=0.74)

    add_p(doc, '请予接洽。',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['please']['size']),
          space_after=scale(ref['please']['after']),
          first_line_indent=0.74)

    add_p(doc, '此致',
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['cizhi']['size']),
          space_after=scale(ref['cizhi']['after']),
          first_line_indent=0.74)

    add_p(doc, court_name,
          alignment=WD_ALIGN_PARAGRAPH.LEFT,
          size=scale(ref['court_end']['size']),
          space_after=scale(ref['court_end']['after']))

    add_p(doc, f'{firm}（公章）',
          alignment=WD_ALIGN_PARAGRAPH.RIGHT,
          size=scale(ref['seal']['size']),
          space_after=scale(ref['seal']['after']))

    add_p(doc, '    年  月  日',
          alignment=WD_ALIGN_PARAGRAPH.RIGHT,
          size=scale(ref['date']['size']))

    return ratio


def get_next_number(numbering_file, counter_key='intro_letter'):
    numbering = {"year": 2026, "firm_abbr": "友安", "counters": {"intro_letter": 0, "law_firm_letter": 0, "contract": 0}}
    if os.path.exists(numbering_file):
        with open(numbering_file, 'r', encoding='utf-8') as f:
            numbering = json.load(f)
    current = numbering["counters"].get(counter_key, 0)
    next_no = current + 1
    numbering["counters"][counter_key] = next_no
    os.makedirs(os.path.dirname(os.path.abspath(numbering_file)), exist_ok=True)
    with open(numbering_file, 'w', encoding='utf-8') as f:
        json.dump(numbering, f, ensure_ascii=False, indent=2)
    return next_no, numbering["year"], numbering["firm_abbr"]


def generate_documents(config, cases, output_dir, numbering_file, combine=False):
    os.makedirs(output_dir, exist_ok=True)

    if combine and len(cases) > 1:
        # A4 竖版，上下各一张 A5 横版
        doc = Document()
        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(0.8)
        section.bottom_margin = Cm(0.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

        # 每份可用高度 ≈ (29.7 - 0.8 - 0.5) / len(cases) - 裁切开销
        per = (29.7 - 0.8 - 0.5) / len(cases) - 0.3

        for i, case in enumerate(cases):
            no, year, abbr = get_next_number(numbering_file)
            letter_no = f'〔{year}〕{abbr}介字第{no:03d}号'
            make_letter_content(doc, config, case['court'], case['number'],
                                case['parties'], case['cause'], letter_no,
                                usable_cm=per)
            if i < len(cases) - 1:
                add_cut_line(doc)

        first_party = cases[0]['parties'].split('、')[0].split('与')[0].strip()
        filename = f'{output_dir}/介绍信_{first_party}等案_合并.docx'
        doc.save(filename)
        return [filename]
    else:
        files = []
        for case in cases:
            doc = Document()
            section = doc.sections[0]
            section.page_width = Cm(21.0)
            section.page_height = Cm(14.8)
            section.top_margin = Cm(1.0)
            section.bottom_margin = Cm(0.8)
            section.left_margin = Cm(2.0)
            section.right_margin = Cm(2.0)

            no, year, abbr = get_next_number(numbering_file)
            letter_no = f'〔{year}〕{abbr}介字第{no:03d}号'
            make_letter_content(doc, config, case['court'], case['number'],
                                case['parties'], case['cause'], letter_no,
                                usable_cm=14.8 - 1.0 - 0.8)

            first_party = case['parties'].split('、')[0].split('与')[0].strip()
            filename = f'{output_dir}/介绍信_{first_party}.docx'
            doc.save(filename)
            files.append(filename)
        return files


def main():
    parser = argparse.ArgumentParser(description='生成调取卷宗介绍信')
    parser.add_argument('--user-config', required=True)
    parser.add_argument('--output-dir', default=None)
    parser.add_argument('--combine', action='store_true')
    parser.add_argument('--case', action='append', dest='cases',
                        help='法院名称|案号|当事人|案由，可重复')
    parser.add_argument('--court-name', help='单案件模式')
    parser.add_argument('--case-number', help='单案件模式')
    parser.add_argument('--parties', help='单案件模式')
    parser.add_argument('--cause', help='单案件模式')

    args = parser.parse_args()
    config = load_config(args.user_config)
    if not config:
        print('错误：未找到用户配置，请先录入信息。')
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(os.path.dirname(args.user_config), '..', 'output')
    numbering_file = config.get('numbering_file', os.path.join(output_dir, 'numbering.json'))

    cases = []
    if args.cases:
        for c in args.cases:
            parts = c.split('|', 3)
            if len(parts) == 4:
                cases.append({'court': parts[0], 'number': parts[1],
                              'parties': parts[2], 'cause': parts[3]})
    elif args.court_name and args.case_number:
        cases.append({'court': args.court_name, 'number': args.case_number,
                      'parties': args.parties or '', 'cause': args.cause or ''})
    else:
        print('错误：请提供案件信息。')
        sys.exit(1)

    files = generate_documents(config, cases, output_dir, numbering_file, args.combine)
    for f in files:
        print(f'已生成：{f}')


if __name__ == '__main__':
    main()
