# -*- coding: utf-8 -*-
"""
《案件当事人授权委托书》扫描件 → 可编辑 Word（保真重建 v7）

字体字号依据 990 款候选字体的像素级字形匹配（IoU 网格搜索，见
skills/scanned-pdf-to-word/scripts/identify_font.py）：
  · 正文   = 方正楷体简体 15pt    （四样本字形分 0.807/0.819/0.894/0.717 均居首，
                                   同族楷体变体包揽前三；仿宋仅 0.425、黑体 0.371、
                                   宋体 0.381 → 楷体是仿宋的 1.9 倍，断层胜出。
                                   字宽实测 15.24pt，Word 精度 0.5pt 取 15pt）
  · 标题   = 方正小标宋简体 21pt  （0.822/0.832；字宽实测 21.18~21.21pt → 21pt）
  · 附件１ = 方正黑体简体 15pt    （0.807；“１”取全角，半角方案只有 0.547 且全为误配）
  · 页码   = 宋体 14pt（四号，双页码居左空一字）
  · 行距   = 固定 20.5pt；版心 76.06 → 504.96pt（宽 428.90）

ASCII 走 Times New Roman（见 AFONT 注释）：决定下划线的下沉量，楷体 "_" 偏浅 2.3pt。

填空线 = ASCII 下划线字符（advance 0.5em = 7.5pt，ink 0.517em > advance，相邻重叠成一条直线）。
  每行手动断行，且行宽一律留 ≈8pt 余量：连续下划线会被引擎视为不可断的“西文单词”，
  一旦超宽就整串跳到下一行；行末空格还会被引擎修剪（连带吃掉其下划线）。
"""
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PW, PH = 595.0, 841.0
ML, MR = 76.06, 90.04
TOP, FOOT = 100.4, 92.4
FS, LINE = 15.0, 20.5
F_KAI, F_TITLE, F_HEI, F_SONG = "方正楷体简体", "方正小标宋简体", "方正黑体简体", "宋体"
# 字号：.docx 的 w:sz 只能 0.5pt 步进，但原件实测正文 15.28pt（墨迹宽法 15.22~15.33、
# 列投影字宽法 15.32，六样本交叉）、标题 21.19pt，都不是 0.5 的整数倍。
# 用 Word 的「字符缩放」w:w（整数百分比）补齐精度：
#   正文 15.0pt × 102% = 15.30pt（目标 15.28，偏差 0.02pt）
#   标题 21.0pt × 101% = 21.21pt（目标 21.19，偏差 0.02pt）
# 若渲染器忽略 w:w，则退化为 15.0/21.0pt——仍是安全值，不会失控。
SCALE = {15.0: 102, 21.0: 101}
# 公文经典配置：eastAsia 用中文字体、ascii/hAnsi 用 Times New Roman。
# 这里不是为了好看——下划线字符 "_" 走 ascii 分支，而两款字体的 "_" 下沉量差很多：
#   方正楷体简体 "_" 墨迹中心在基线下 0.0485em（15pt 时 0.73pt）
#   Times New Roman "_"       在基线下 0.1952em（15pt 时 2.93pt）
# 原件实测下沉 0.135em（比重建版低 2.19~2.44pt，两个样本一致）。
# 换成 TNR 后差值只剩 0.62~1.25pt；两款 "_" 的 advance 都是 0.500em、墨迹 0.517em，
# 故换字体不改变填空线长度（"ink > advance" 保证相邻重叠成一条连续直线）。
AFONT = {F_KAI: "Times New Roman"}
UL, BR = "_", "\n"

# w:w 在 rPr 里的合法位置：紧跟 w:spacing，在 w:kern 之前
_W_SUCC = ('w:kern', 'w:position', 'w:sz', 'w:szCs', 'w:highlight', 'w:u', 'w:effect',
           'w:bdr', 'w:shd', 'w:fitText', 'w:vertAlign', 'w:rtl', 'w:cs', 'w:em',
           'w:lang', 'w:eastAsianLayout', 'w:specVanish', 'w:oMath')

_SUCC = ('w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN',
         'w:bidi', 'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind',
         'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
         'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl',
         'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange')


def set_run(run, font, size, scale=True):
    rPr = run._element.get_or_add_rPr()
    rf = OxmlElement("w:rFonts")
    rf.set(qn("w:ascii"), AFONT.get(font, font))
    rf.set(qn("w:hAnsi"), AFONT.get(font, font))
    rf.set(qn("w:eastAsia"), font)
    rf.set(qn("w:cs"), font)
    rPr.insert(0, rf)
    w = SCALE.get(size) if scale else None
    if w and w != 100:
        e = OxmlElement("w:w"); e.set(qn("w:val"), str(w))
        rPr.insert_element_before(e, *_W_SUCC)
    run.font.size = Pt(size)
    return run


def relax(pPr):
    """关避头尾、允许西文词内换行 —— 减少引擎把标点整组挤走／长串跳行。"""
    for tag, val in (("w:kinsoku", "0"), ("w:wordWrap", "0")):
        e = OxmlElement(tag); e.set(qn("w:val"), val)
        pPr.insert_element_before(e, *_SUCC)


def add_par(doc, text, font=F_KAI, size=FS, indent=0.0, align=None,
            line=LINE, before=0.0, after=0.0):
    p = doc.add_paragraph()
    relax(p._element.get_or_add_pPr())
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(line)
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.first_line_indent = Pt(indent)
    if align is not None:
        pf.alignment = align
    run = set_run(p.add_run(), font, size)
    for i, seg in enumerate(text.split(BR)):
        if i:
            run.add_break()
        run.add_text(seg)
    return p


doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Pt(PW), Pt(PH)
sec.left_margin, sec.right_margin = Pt(ML), Pt(MR)
sec.top_margin, sec.bottom_margin = Pt(TOP), Pt(60.0)
sec.footer_distance = Pt(FOOT)

st = doc.styles["Normal"]
st.font.name = AFONT.get(F_KAI, F_KAI)
st.font.size = Pt(FS)
st._element.rPr.rFonts.set(qn("w:eastAsia"), F_KAI)
st._element.rPr.rFonts.set(qn("w:ascii"), AFONT.get(F_KAI, F_KAI))
st._element.rPr.rFonts.set(qn("w:hAnsi"), AFONT.get(F_KAI, F_KAI))
if SCALE.get(FS, 100) != 100:
    e = OxmlElement("w:w"); e.set(qn("w:val"), str(SCALE[FS]))
    st._element.rPr.insert_element_before(e, *_W_SUCC)

# ---------------- 正文 ----------------
add_par(doc, "附件\uff11", F_HEI, FS)

add_par(doc, "案件当事人授权委托书", F_TITLE, 21.0,
        align=WD_ALIGN_PARAGRAPH.CENTER, line=36.0, before=26.9, after=34.0)

add_par(doc, "委托人：")

# □自然人段（17 字 + 16 个下划线；次行 55 个下划线 + 半角分号）
add_par(doc, "□自然人：（姓名，公民身份号码）：" + UL * 16 + BR + UL * 54 + "；",
        indent=45.5)

# □法人段（行1 断在“法人代表姓”后、行2 起于“名、”，避免「、」触发整组换行）
add_par(doc, "□法人：（单位名称、统一社会信用代码，法人代表姓" + BR
            + "名、公民身份号码）：" + UL * 36 + BR + UL * 56 + BR + UL * 56,
        indent=45.5)

add_par(doc, "受托人：")

# 姓名段（21/17/4 字，下划线 10 / 22 / 48）
add_par(doc, "姓名：" + UL * 10 + "，□律师、□基层法律服务工作者执业证" + BR
            + "书编号：" + UL * 22 + "，律师事务所、基层法律服务" + BR
            + "所名称" + UL * 48 + "。",
        indent=30.5)

add_par(doc, "授权委托事项：", before=20.5)

# 本人同意段（下划线 26 / 56 / 34）
add_par(doc, "本人同意授权由受托人代理" + UL * 26 + BR + UL * 56 + BR
            + UL * 34 + "诉讼案件（仲裁事务）。",
        indent=45.5)

add_par(doc, "委托人（签名捺印/盖章）：" + UL * 17, indent=106.0, before=41.5)

add_par(doc, UL * 11 + "年" + UL * 4 + "月" + UL * 4 + "日", indent=221.5)

# ---------------- 页脚页码 ----------------
fp = sec.footer.paragraphs[0]
fp.paragraph_format.first_line_indent = Pt(14.0)
set_run(fp.add_run("—10—"), F_SONG, 14)

doc.save("案件当事人授权委托书.docx")
print("已生成 v7")
