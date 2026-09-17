# -*- coding: utf-8 -*-
"""
generate_demo_pack.py — 生成示范包 2 份虚构示范母版（全脱敏）

产物（写入 references/demo-pack/）：
  1. 委托代理合同（计件版·示范母版）.docx —— 含双层编号/勾选框/金额/日期 全教学难点
  2. 授权委托书+律所函（示范母版）.docx —— 同页双文书，特别授权权限清单

样式规则（法律文书母版通用）：
  全部楷体；大标题小二22pt加粗；正文小四12pt；行距默认23pt；法院抬头加粗

脱敏铁律：所有当事人一律虚构（张三/李四/××公司），金额用占位数字，
         律所名用「浙江示范律师事务所」（明确表示示范用途，非真实律所）。

用法:
  python generate_demo_pack.py
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "references", "demo-pack")

KAITI = "楷体"


def set_font(run, size=12, bold=False):
    """统一设置楷体字体（中西文均需指定 eastAsia）"""
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    r = run._element
    r.rPr.rFonts.set(qn("w:eastAsia"), KAITI)


def para(doc, text, size=12, bold=False, align=None, line=23,
         space_after=0, indent=False):
    """添加段落：默认小四楷体、23pt行距、段后0"""
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(line)
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    if indent:
        pf.first_line_indent = Pt(size * 2)  # 首行缩进两字符
    run = p.add_run(text)
    set_font(run, size=size, bold=bold)
    return p


def title(doc, text):
    """大标题：小二22pt加粗居中"""
    return para(doc, text, size=22, bold=True,
                align=WD_ALIGN_PARAGRAPH.CENTER, line=36, space_after=12)


def h2(doc, text):
    """小标题：三号16pt加粗"""
    return para(doc, text, size=16, bold=True, line=28, space_after=6)


# ============================================================
# 母版一：委托代理合同（计件版·示范母版）
# ============================================================
def build_contract():
    doc = Document()
    # 页边距：上下2.54cm 左右3.17cm（Word默认，法律文书惯例）
    for section in doc.sections:
        section.page_width = Pt(595.3)   # A4
        section.page_height = Pt(841.9)

    title(doc, "法律服务委托合同书")
    para(doc, "【{{合同编号年份}}】浙示范律民第{{合同编号序号}}号",
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    para(doc, "委托人（甲方）：{{委托人姓名}}")
    para(doc, "地址：{{委托人地址}}　　联系电话：{{委托人电话}}", space_after=6)
    para(doc, "受托人（乙方）：浙江示范律师事务所")
    para(doc, "地址：{{律所地址}}　　联系电话：{{律所电话}}", space_after=12)

    para(doc, "本合同由甲、乙双方依据《中华人民共和国律师法》和其他相关法律、"
              "法规，就下列法律服务事项达成一致，共同订立如下条款。",
         indent=True, space_after=12)

    h2(doc, "一、法律服务范围")
    para(doc, "1.乙方接受甲方委托指派律师，为甲方下列“□”内的法律事务"
              "（下称“本事务”）提供服务。", indent=True)
    para(doc, "{{勾选_民事诉讼}}民事诉讼案件：{{勾选_一审}}一审；"
              "{{勾选_二审}}二审；{{勾选_再审}}申请再审；"
              "{{勾选_执行}}申请执行。")
    para(doc, "{{勾选_行政诉讼}}行政诉讼案件：{{勾选_听证}}听证；"
              "{{勾选_复议}}申请复议；{{勾选_行政一审}}一审；"
              "{{勾选_行政二审}}二审。")
    para(doc, "{{勾选_仲裁}}仲裁案件：{{勾选_代理仲裁}}代理仲裁；"
              "{{勾选_仲裁执行}}申请执行。", space_after=6)
    para(doc, "乙方接受甲方的委托指派律师，为甲方与{{对方当事人}}"
              "一案（案由：{{案由}}）的诉讼/仲裁代理人。",
         indent=True, space_after=12)

    h2(doc, "二、委托权限")
    para(doc, "为：{{勾选_一般代理}}一般代理　{{勾选_特别授权}}特别授权"
              "（具体委托权限依授权委托书为准）。", indent=True, space_after=12)

    h2(doc, "三、承办律师")
    para(doc, "乙方指派{{承办律师}}律师为本事务的承办律师（下称“律师”）。"
              "本合同履行过程中，若律师因合理原因（包括但不限于正常调动、离职、"
              "时间冲突、回避、身体状况等）无法继续或暂时不能承办本事务的，"
              "乙方应及时另行指派其他合适的律师接替；甲方明确不同意其他律师接替，"
              "视为甲方撤销委托、解除合同，本合同终止。",
         indent=True, space_after=12)

    h2(doc, "四、乙方及律师的义务")
    para(doc, "1.律师必须遵守职业道德和执业纪律；"
              "2.律师应当勤勉尽职，在本合同约定范围内，依法维护甲方权益；"
              "3.律师应当及时向甲方报告事务的进展情况；"
              "4.律师不得超越甲方授权行事，如确有需要，应当由甲方另行出具委托书；"
              "5.乙方及律师负有保密义务。",
         indent=True, space_after=12)

    h2(doc, "五、甲方的义务")
    para(doc, "1.与乙方律师诚实合作，如实提供与本事务有关的资料、证据，"
              "如实陈述与本事务有关的情况；"
              "2.与本事务有关的情况和事实发生变化，应及时告知乙方律师；"
              "3.按照约定支付律师费和其它费用。",
         indent=True, space_after=12)

    h2(doc, "六、律师费及其支付")
    para(doc, "双方商定按下列第{{收费方式序号}}种方式计算收费。", indent=True)
    para(doc, "1.计件方式：律师代理费总额为人民币{{律师费金额}}元。"
              "支付方式：{{勾选_一次性支付}}由甲方于本合同签订之日一次性支付；"
              "{{勾选_分期支付}}由甲方按下列期限分期支付：{{分期支付安排}}。")
    para(doc, "2.风险代理方式：双方另行签订《风险代理合同》作为本合同附件，"
              "具体约定以该合同为准。（示范母版仅展示计件版，风险代理版为同族变体，"
              "仅本条内容不同——见 demo-manifest.json 说明）",
         space_after=12)

    h2(doc, "七、其他费用及其支付")
    para(doc, "律师在办理本项法律事务中所发生的以下费用不包含在上述律师费内，"
              "应由甲方另行承担：①代理直接费用（异地交通、住宿、通讯、文印等）；"
              "②代支间接费用（诉讼费、仲裁费、鉴定费、公证费、查档费等）。",
         indent=True, space_after=12)

    h2(doc, "八、委托事务的完成与合同的有效期限")
    para(doc, "属于诉讼/仲裁代理的，委托法律事务以判决、裁定、调解、案外和解、"
              "撤诉、终止诉讼/仲裁/执行等方式结案，或者甲方原因单方撤销委托解除合同的，"
              "均视为乙方完成委托法律事务。本合同有效期限，自签订之日起至委托法律事务"
              "完成或者一方解除合同时止。",
         indent=True, space_after=12)

    h2(doc, "九、合同的解除")
    para(doc, "1.经书面通知，甲方有权随时以任何理由单方解除本合同；"
              "2.如甲方未按约定支付律师费和其他费用，乙方有权解除本合同；"
              "3.若乙方发现甲方存在故意隐瞒事实或虚假作证等情形的，有权解除本合同。",
         indent=True, space_after=12)

    h2(doc, "十、违约和赔偿")
    para(doc, "1.甲方未按约定及时足额支付律师费和其他费用的，应当承担迟延履行违约金；"
              "2.乙方及律师在提供法律服务过程中，因违法执业或其他过错给甲方造成损失的，"
              "乙方应当赔偿甲方实际直接损失。",
         indent=True, space_after=12)

    h2(doc, "十一、不保证")
    para(doc, "乙方和律师向甲方提供的分析、判断或咨询意见，均不可理解为乙方或律师"
              "就受托事务的结果作出了成功或胜诉的保证。",
         indent=True, space_after=12)

    h2(doc, "十二、争议的解决")
    para(doc, "甲乙双方就本合同发生争议的，先行协商，如协商不成，可以提请律师协会"
              "调解处理。无法解决的双方均可向{{管辖法院}}提起诉讼。",
         indent=True, space_after=12)

    h2(doc, "十三、生效条件")
    para(doc, "本合同由双方签署后生效。", indent=True, space_after=6)
    para(doc, "十四、本合同空格部分填写的文字与印刷文字具有同等效力。", space_after=6)
    para(doc, "十五、本合同一式二份，双方各执一份，效力相同。", space_after=24)

    para(doc, "委托人（甲方）：{{委托人姓名}}　　　　　受托人（乙方）：浙江示范律师事务所")
    para(doc, "签订日期：{{签订年份}}年{{签订月份}}月{{签订日期}}日")

    path = os.path.join(OUT_DIR, "委托代理合同（计件版·示范母版）.docx")
    doc.save(path)
    return path


# ============================================================
# 母版二：授权委托书 + 律所函（同页双文书·示范母版）
# ============================================================
def build_poa():
    doc = Document()
    for section in doc.sections:
        section.page_width = Pt(595.3)
        section.page_height = Pt(841.9)

    # ---- 上半页：律所函 ----
    para(doc, "浙江示范律师事务所函", size=16, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, line=28, space_after=6)
    para(doc, "浙示范律（{{函件编号年份}}）民代字第{{函件编号序号}}号",
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
    para(doc, "{{致送法院}}：", bold=True)  # 法院抬头加粗（样式铁律）
    para(doc, "你院受理{{原告}}诉{{被告}}{{案由}}一案，现根据{{诉讼地位}}委托，"
              "本所指派{{承办律师}}律师为{{诉讼地位}}的诉讼代理人。",
         indent=True, space_after=6)
    para(doc, "特此函告", indent=True, space_after=24)
    para(doc, "浙江示范律师事务所", align=WD_ALIGN_PARAGRAPH.RIGHT)
    para(doc, "{{函件年份}}年{{函件月份}}月{{函件日期}}日",
         align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=24)

    # ---- 下半页：授权委托书 ----
    title(doc, "授 权 委 托 书")
    para(doc, "委托人：{{委托人姓名}}")
    para(doc, "地址：{{委托人地址}}　　电话：{{委托人电话}}", space_after=6)
    para(doc, "受托人：浙江示范律师事务所　{{承办律师}}律师", space_after=12)

    para(doc, "现委托上列受托人在我与{{对方当事人}}{{案由}}一案中，"
              "作为我方参加诉讼的委托代理人。委托权限如下：",
         indent=True, space_after=6)
    para(doc, "代理权限类型：{{勾选_一般代理}}一般代理　{{勾选_特别授权}}特别授权",
         indent=True, space_after=6)

    para(doc, "特别授权代理（勾选特别授权时适用）：包括代为起诉/应诉、"
              "申请/解除保全、出庭接受和解、调解、代为承认、变更、放弃诉讼请求，"
              "提起反诉，申请撤诉，代为签署有关文书，代为签收法律文书，"
              "代为确认送达地址，提起上诉，转委托权，申请执行、执行和解、"
              "代领执行款等。", indent=True, space_after=6)

    para(doc, "（注：依据《民事诉讼法》第62条，代为承认、放弃、变更诉讼请求，"
              "进行和解，提起反诉或者上诉，必须有委托人的特别授权；"
              "仅写“全权代理”而无具体授权的，视为一般代理。）",
         size=12, indent=True, space_after=12)

    para(doc, "委托代理期限从委托之日起至本案本审终结止。", indent=True, space_after=24)

    para(doc, "委托人：{{委托人姓名}}", align=WD_ALIGN_PARAGRAPH.RIGHT)
    para(doc, "{{委托年份}}年{{委托月份}}月{{委托日期}}日",
         align=WD_ALIGN_PARAGRAPH.RIGHT)

    path = os.path.join(OUT_DIR, "授权委托书+律所函（示范母版）.docx")
    doc.save(path)
    return path


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    p1 = build_contract()
    p2 = build_poa()
    print("已生成：")
    print(" ", p1)
    print(" ", p2)
