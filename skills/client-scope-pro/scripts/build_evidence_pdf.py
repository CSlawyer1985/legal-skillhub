#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_evidence_pdf.py — 附件PDF汇编生成器（ClientScope Pro 配套脚本）

用法:
  python3 build_evidence_pdf.py --content content.json -o 附件汇编.pdf

content.json 结构（全部字段可伸缩，模块数3-9个均可）:
{
  "report_title": "苏州仕净科技股份有限公司背景调查报告",
  "attachment_title": "附件：风险模块与证据材料汇编",
  "cutoff": "2026年9月19日",
  "date_cn": "二〇二六年九月",
  "modules": [
    {"id": "m1", "title": "模块一　高优先级：……", "priority": "高",
     "map": "第三部分·三；十二（一）1", "facts": ["F08、F09"],
     "logic": "衔接逻辑段落…",
     "key_facts": ["1.【已核验事实】……【F08】", ...],
     "evidence": [["A02","材料名","主体/日期","一级","已保存"], ...],
     "interview": ["问题1", ...],
     "todo": ["待核实1", ...]},
    ...
  ],
  "appendix_a": [["A01","材料名","主体/日期","来源","存证状态"], ...],
  "appendix_b": ["已存证文件说明1", ...],
  "appendix_c": [["1","待核实事项","核实渠道","关联模块/Fact ID"], ...],
  "disclaimer": "免责声明文字…"
}

特性: 可点击目录(带页码) / PDF书签 / 页脚页码 / 每部分分页 / 统一黑白灰表格(行不跨页)
环境: reportlab（pip install reportlab）; 中文字体取 macOS 系统 Songti.ttc
"""
import argparse, hashlib, json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

SONG_TTC = '/System/Library/Fonts/Supplemental/Songti.ttc'
pdfmetrics.registerFont(TTFont('Song', SONG_TTC, subfontIndex=6))    # Songti SC Regular
pdfmetrics.registerFont(TTFont('SongBd', SONG_TTC, subfontIndex=1))  # Songti SC Bold

S = {
 'cover1': ParagraphStyle('cover1', fontName='SongBd', fontSize=16, leading=24, alignment=TA_CENTER, spaceBefore=10),
 'coverL': ParagraphStyle('coverL', fontName='SongBd', fontSize=22, leading=33, alignment=TA_CENTER, spaceBefore=16, spaceAfter=8),
 'h1': ParagraphStyle('H1', fontName='SongBd', fontSize=14, leading=21, alignment=TA_CENTER, spaceBefore=14, spaceAfter=13, pageBreakBefore=1),
 'h2': ParagraphStyle('H2', fontName='SongBd', fontSize=12, leading=18, alignment=TA_LEFT, firstLineIndent=24, spaceBefore=10, spaceAfter=5),
 'bt': ParagraphStyle('BT', fontName='Song', fontSize=12, leading=18, firstLineIndent=24, alignment=TA_JUSTIFY, spaceAfter=2),
 'lv2': ParagraphStyle('LV2', fontName='Song', fontSize=12, leading=18, firstLineIndent=24, alignment=TA_JUSTIFY, spaceAfter=2),
 'note': ParagraphStyle('NOTE', fontName='Song', fontSize=10.5, leading=15.75, firstLineIndent=0, alignment=TA_JUSTIFY, spaceAfter=4, textColor=colors.HexColor('#333333')),
 'cell': ParagraphStyle('CELL', fontName='Song', fontSize=10.5, leading=12.6, alignment=TA_LEFT),
 'cellB': ParagraphStyle('CELLB', fontName='SongBd', fontSize=10.5, leading=12.6, alignment=TA_LEFT),
 'tocH': ParagraphStyle('TOCH', fontName='SongBd', fontSize=14, leading=21, alignment=TA_CENTER, spaceBefore=14, spaceAfter=13, pageBreakBefore=1),
}
TOC_L1 = ParagraphStyle('TOC1', fontName='Song', fontSize=12, leading=20)
TOC_L2 = ParagraphStyle('TOC2', fontName='Song', fontSize=12, leading=18, leftIndent=24)

GRID = TableStyle([
 ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
 ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2F2F2')),
 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
 ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
 ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
])


def tbl(headers, rows, widths):
    data = [[Paragraph(h, S['cellB']) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), S['cell']) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1, splitByRow=1)
    t.setStyle(GRID)
    return t


class Doc(BaseDocTemplate):
    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name in ('H1', 'H2'):
            txt = fl.getPlainText()
            level = 0 if fl.style.name == 'H1' else 1
            key = 'h' + hashlib.md5(txt.encode('utf-8')).hexdigest()[:10]  # 跨multiBuild轮次必须稳定
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(txt, key, level, closed=False)
            self.notify('TOCEntry', (level, txt, self.page, key))


def on_page(canv, doc):
    canv.saveState()
    canv.setFont('Song', 9)
    canv.drawCentredString(A4[0] / 2, 1.4 * cm, '第 %d 页' % canv.getPageNumber())
    canv.restoreState()


def build(content, out):
    story = []
    P = lambda t, s='bt': story.append(Paragraph(t, S[s]))

    # 封面
    story.append(Spacer(1, 3 * cm))
    P(content['report_title'], 'cover1')
    P(content['attachment_title'], 'coverL')
    P('（与主报告"第三部分·风险与服务机会"及"十二、法律服务机会优先级汇总"对应编制）', 'cover1')
    story.append(Spacer(1, 1.2 * cm))
    P(content.get('date_cn', ''), 'cover1')

    # 目录
    story.append(Paragraph('目　　录', S['tocH']))
    toc = TableOfContents()
    toc.levelStyles = [TOC_L1, TOC_L2]
    toc.dotsMinLevel = 0
    story.append(toc)

    # 编制说明
    story.append(Paragraph('编制说明与使用指引', S['h1']))
    cutoff = content.get('cutoff', '')
    P('本附件系《' + content['report_title'].replace('背景调查报告', '背景调查及法律服务机会分析报告') + '》（以下简称"主报告"）的配套汇编文件，信息检索截止日与主报告一致（' + cutoff + '）。本附件按主报告服务机会优先级框架对各风险模块重新排序与布局，每个模块按"对应关系与衔接逻辑→核心事实要点→证据材料清单→访谈建议→待核实事项"统一体例编排。')
    P('主报告与附件通过Fact ID、附件编号及下表互相索引；术语含义见主报告第一部分"释义"，本附件不再重复。')
    story.append(tbl(['附件模块', '优先级', '对应主报告位置', '核心关联Fact ID'],
                     [[m['title'], m['priority'], m['map'], '、'.join(m['facts'])] for m in content['modules']]
                     + [['附录A—C', '—', '第五部分·四、五', '全部']],
                     [4.1 * cm, 1.5 * cm, 6.2 * cm, 2.9 * cm]))
    P('标注体例与主报告一致：<b>【已核验事实】</b>指已回溯至监管决定原文或法定披露的信息；<b>【主体观点】</b>为他方表述；<b>【分析判断】</b>为编制方基于公开信息的推断；<b>【待核实】</b>指未能回溯官方原始信源或检索日后尚在变化的事项。')

    W5 = [1.7 * cm, 5.6 * cm, 3.1 * cm, 2.2 * cm, 2.1 * cm]
    H5 = ['编号', '材料名称', '发布主体/日期', '信源等级', '存证状态']

    # 模块
    for m in content['modules']:
        story.append(Paragraph(m['title'], S['h1']))
        story.append(Paragraph('（一）对应关系与衔接逻辑', S['h2']))
        P('本模块对应主报告' + m['map'] + '。' + m['logic'])
        story.append(Paragraph('（二）核心事实要点', S['h2']))
        for f in m['key_facts']:
            P(f, 'lv2')
        story.append(Paragraph('（三）证据材料清单', S['h2']))
        story.append(tbl(H5, m['evidence'], W5))
        if m.get('interview'):
            story.append(Paragraph('（四）访谈建议', S['h2']))
            for q in m['interview']:
                P(q, 'lv2')
        if m.get('todo'):
            story.append(Paragraph('（五）待核实事项', S['h2']))
            for q in m['todo']:
                P(q, 'lv2')

    # 附录A
    story.append(Paragraph('附录A　证据材料总索引', S['h1']))
    P('使用说明：本索引与主报告附件索引一致，用于正文反向追溯原始材料；无法稳定保存的文件如实记录来源，不伪造附件。', 'note')
    story.append(tbl(['编号', '材料名称', '发布主体/日期', '原始来源', '存证状态'],
                     content['appendix_a'], [1.5 * cm, 4.6 * cm, 2.9 * cm, 4.0 * cm, 2.7 * cm]))

    # 附录B
    story.append(Paragraph('附录B　已存证原始文件清单（Evidence Pack）', S['h1']))
    for line in content['appendix_b']:
        P(line, 'lv2')

    # 附录C
    story.append(Paragraph('附录C　待核实事项汇总清单', S['h1']))
    story.append(tbl(['序号', '待核实事项', '核实渠道建议', '关联模块/Fact ID'],
                     content['appendix_c'], [1.2 * cm, 6.4 * cm, 4.2 * cm, 2.9 * cm]))

    # 免责声明
    story.append(Paragraph('免责声明', S['h1']))
    P(content['disclaimer'])

    doc = Doc(out, pagesize=A4,
              leftMargin=3.18 * cm, rightMargin=3.18 * cm, topMargin=2.54 * cm, bottomMargin=2.54 * cm,
              title=content['attachment_title'], author='律师工作底稿')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='f')
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=on_page)])
    doc.multiBuild(story)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--content', required=True, help='content.json 路径')
    ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    with open(a.content, encoding='utf-8') as f:
        content = json.load(f)
    print('PDF built:', build(content, a.out))
