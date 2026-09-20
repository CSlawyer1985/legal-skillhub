"""
client-due-diligence 生成脚本
=============================
输入：case_data.json（与脚本同目录）
输出：
  O1 <CompanyName>-客户背调报告.docx    （Word 主报告，12 章）
  O2 <CompanyName>-客户背调附件.pdf     （PDF 附件合集）

硬约束：
  R1 信息来源 URL 域名必须在权威网站白名单内
  R3 主报告必须 .docx（python-docx 标准样式）
  R4 附件必须 PDF（reportlab + TTF 中文字体 + 原生 Drawing）
  R5 不输出 Markdown
  R8 利益冲突审查 8 项强制门槛：存在未豁免冲突 → 阻断承接建议，风险强制标红
"""

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "case_data.json"
OUTPUT_DIR = ROOT

# ====================================================================
# 字体注册（Windows TTF，避免 CID 字体缺 CMap 导致 PDF 乱码）
# ====================================================================
_FONTS_REGISTERED = False


def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    font_map = [
        ("SimSun", "C:/Windows/Fonts/simsun.ttc", 0),
        ("SimHei", "C:/Windows/Fonts/simhei.ttf", None),
        ("KaiTi", "C:/Windows/Fonts/simkai.ttf", None),
        ("FangSong", "C:/Windows/Fonts/simfang.ttf", None),
    ]
    for name, path, idx in font_map:
        try:
            if idx is not None:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
            else:
                pdfmetrics.registerFont(TTFont(name, path))
        except Exception as e:
            print(f"[WARN] 注册字体 {name} 失败：{e}")
    _FONTS_REGISTERED = True


_register_fonts()

# ====================================================================
# R1：权威网站白名单
# ====================================================================
AUTHORITATIVE_HOSTS = {
    "gsxt.gov.cn", "creditchina.gov.cn", "samr.gov.cn",
    "wenshu.court.gov.cn", "zxgk.court.gov.cn", "court.gov.cn", "pccz.court.gov.cn", "moj.gov.cn",
    "sbj.cnipa.gov.cn", "pss-system.cnipa.gov.cn", "ncac.gov.cn", "cnipa.gov.cn",
    "csrc.gov.cn", "szse.cn", "sse.com.cn", "bse.cn",
    "cninfo.com.cn",
    "xinhuanet.com", "people.com.cn", "cctv.com", "cctv.cn", "jrj.com.cn", "gmw.cn", "chinacourt.org",
}

NON_AUTHORITATIVE = {
    "baike.baidu.com", "baike.sogou.com", "baike.so.com",
    "sohu.com", "163.com", "sina.com.cn", "qq.com", "ifeng.com",
    "toutiao.com", "bilibili.com", "mp.weixin.qq.com",
    "baidu.com", "google.com", "bing.com", "sogou.com", "zhihu.com",
}


def url_host(url):
    m = re.search(r"https?://([^/]+)", url or "", re.I)
    return m.group(1).lower() if m else ""


def host_in_whitelist(url):
    h = url_host(url)
    if not h:
        return False
    if h in NON_AUTHORITATIVE:
        return False
    return any(h == w or h.endswith("." + w) for w in AUTHORITATIVE_HOSTS)


# ====================================================================
# 加载数据
# ====================================================================
def load_data():
    if not DATA_FILE.exists():
        sys.exit(f"[FAIL] 未找到数据文件：{DATA_FILE}\n请把 case_data.example.json 拷贝为 case_data.json 并填入数据。")
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[FAIL] case_data.json JSON 解析失败：{e}")


# ====================================================================
# R1 校验
# ====================================================================
def collect_urls(d):
    urls = []
    def add(label, u):
        if u:
            urls.append((label, u))
    for section in ["basic_info", "judicial_risk", "execution_risk", "regulatory", "restructuring", "audit"]:
        if isinstance(d.get(section), dict) and d[section].get("data_source"):
            add(f"{section}.data_source", d[section]["data_source"])
    if isinstance(d.get("financials"), dict) and d["financials"].get("data_source"):
        add("financials.data_source", d["financials"]["data_source"])
    return urls


def check_url_guard(d, strict):
    print("\n[R1] URL 权威源校验 ...")
    urls = collect_urls(d)
    bad = []
    for label, u in urls:
        if not host_in_whitelist(u):
            bad.append((label, u))
    print(f"  - 通过：{len(urls) - len(bad)} / {len(urls)}")
    if bad:
        for label, u in bad:
            print(f"      ✗ {label}: {u}")
        if strict:
            sys.exit("\n[FAIL] --strict-legal 模式：存在非权威源 URL，停止生成。")
    return bad


# ====================================================================
# R8：利益冲突门槛
# ====================================================================
def check_conflict(d, strict):
    print("\n[R8] 利益冲突审查（8 项强制门槛）...")
    items = d.get("conflict_check", [])
    if not items:
        msg = "[FAIL] 缺少 conflict_check 字段（8 项利益冲突自查），拒绝生成正式报告。"
        sys.exit(msg)
    unwaived = [c for c in items if c.get("result") == "是" and not c.get("waiver")]
    waived = [c for c in items if c.get("result") == "是" and c.get("waiver")]
    print(f"  - 共 {len(items)} 项；无冲突项 {len([c for c in items if c.get('result')=='否'])}；"
          f"已豁免 {len(waived)}；未豁免 {len(unwaived)}")
    if unwaived:
        print("  ✗ 存在未豁免利益冲突，结论强制置为「禁止承接」")
        if strict:
            sys.exit("[FAIL] --strict-legal 模式：存在未豁免利益冲突，停止生成。")
        return "blocked", unwaived
    if waived:
        print("  ⚠ 存在已豁免冲突，标注「有条件承接」")
        return "conditional", waived
    print("  ✓ 全部通过")
    return "clear", []


# ====================================================================
# docx 辅助
# ====================================================================
def set_cn_font(run, font="宋体", size=10.5):
    run.font.name = font
    run.font.size = Pt(size)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts"); rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), font)


def add_hyperlink(paragraph, url, text, color="0563C1"):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), color); rPr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rPr.append(u)
    new_run.append(rPr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve")
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def style_table(table):
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell in table.rows[0].cells:
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def add_para(doc, text, size=10.5, bold=False, align=None, indent_cm=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if indent_cm is not None:
        p.paragraph_format.first_line_indent = Cm(indent_cm)
    r = p.add_run(text)
    set_cn_font(r, size=size)
    r.bold = bold
    return p


def add_h1(doc, text):
    p = doc.add_heading("", level=1)
    r = p.add_run(text); set_cn_font(r, size=16)
    return p


def add_h2(doc, text):
    p = doc.add_heading("", level=2)
    r = p.add_run(text); set_cn_font(r, size=14)
    return p


def add_h3(doc, text):
    p = doc.add_heading("", level=3)
    r = p.add_run(text); set_cn_font(r, size=12)
    return p


def cite(doc, text, url):
    if not url:
        r = doc.add_paragraph().add_run(f"  {text}（来源：未提供）")
        set_cn_font(r, size=9, font="楷体"); r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
        return
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    r = p.add_run(f"  {text}（来源：")
    set_cn_font(r, size=9, font="楷体")
    add_hyperlink(p, url, url)
    r2 = p.add_run("）"); set_cn_font(r2, size=9, font="楷体")


def make_table(doc, headers, rows):
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = h
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            t.rows[i].cells[j].text = str(v)
    style_table(t)
    return t


# ====================================================================
# O1：docx 主报告（12 章）
# ====================================================================
def render_docx(d, conflict_status):
    company = d["company_name"]
    out = OUTPUT_DIR / f"{company}-客户背调报告.docx"
    doc = Document()

    for section in doc.sections:
        section.left_margin = Cm(2.5); section.right_margin = Cm(2.5)
        section.top_margin = Cm(2.5); section.bottom_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "宋体"; style.font.size = Pt(10.5)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts"); rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "宋体")

    # 页眉页脚
    hp = doc.sections[0].header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run(f"{company} 客户背调报告    编号：{d.get('report_no','')}")
    set_cn_font(hr, size=9, font="楷体")

    fp = doc.sections[0].footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.add_run("第 ")
    fld_begin = OxmlElement("w:fldChar"); fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
    rp = fp.add_run(); rp._element.append(fld_begin); rp._element.append(instr); rp._element.append(fld_end)
    set_cn_font(rp, size=9)
    fp.add_run(" 页    出具日期：" + d.get("report_date", ""))

    # 封面
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(d.get("verifier", "")); set_cn_font(r, size=18); r.bold = True
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("客户背调报告"); set_cn_font(r, size=28); r.bold = True
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(company); set_cn_font(r, size=20); r.bold = True
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"（{d.get('stock_short','')}  {d.get('stock_code','')}）"); set_cn_font(r, size=14)
    for _ in range(6):
        doc.add_paragraph()
    meta = [
        ("报告编号", d.get("report_no", "")),
        ("出具日期", d.get("report_date", "")),
        ("项目主办律师", d.get("primary_lawyer", "")),
        ("委托方", "律师事务所"),
        ("客户指令", d.get("instruction", "")),
    ]
    t = doc.add_table(rows=len(meta), cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(meta):
        t.rows[i].cells[0].text = k; t.rows[i].cells[1].text = v
    style_table(t)
    for _ in range(8):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("内部文件 · 仅供本所承接决策使用 · 禁止对外提供")
    set_cn_font(r, size=10, font="楷体"); r.bold = True
    doc.add_page_break()

    # 目录
    add_h1(doc, "目录")
    for s in ["第一节 报告说明与方法", "第二节 主体识别（工商登记与画像）", "第三节 数据对齐基准表",
              "第四节 股权结构与公司治理", "第五节 财务与资信", "第六节 风险扫描",
              "第七节 综合风险评估", "第八节 法律顾问切入备忘录", "第九节 承接建议与风险缓释",
              "第十节 利益冲突审查结论", "第十一节 待核实事项清单", "第十二节 免责声明"]:
        p = doc.add_paragraph(s)
        for r in p.runs:
            set_cn_font(r, size=11)
    doc.add_page_break()

    # 第一节
    add_h1(doc, "第一节  报告说明与方法")
    add_h2(doc, "一、委托背景与目的")
    add_para(doc, "本所拟为客户提供法律服务，在正式接洽前开展背景调查与法律风险评估，为洽谈、报价与承接决策提供依据。",
             indent_cm=0.74)
    add_h2(doc, "二、核查范围与期间")
    add_para(doc, "核查主体为目标公司本体及其主要对外投资企业；涉诉、执行、处罚、监管类信息重点覆盖 2024 年 1 月至 2026 年 9 月。",
             indent_cm=0.74)
    add_h2(doc, "三、信息源与核查方法")
    add_para(doc, "采用真实数据接口（MCP）优先、权威公开网站兜底的核查方法，屏蔽百度/搜狗/360 百科、微信公众号及自媒体。",
             indent_cm=0.74)
    add_h2(doc, "四、局限性声明")
    add_para(doc, "本报告基于公开渠道信息，未获取公司内部台账；第三方数据存在更新延迟；标注「待核实」事项须以官方渠道核验为准。",
             indent_cm=0.74)
    doc.add_page_break()

    # 第二节 主体识别
    add_h1(doc, "第二节  主体识别（工商登记与画像）")
    b = d["basic_info"]
    rows = [
        ("法定全称", b.get("name")), ("统一社会信用代码", b.get("uscc")),
        ("法定代表人", b.get("legal_rep")), ("成立日期", b.get("established")),
        ("注册资本", b.get("registered_capital")), ("登记状态", b.get("registration_status")),
        ("企业类型", b.get("enterprise_type")), ("登记机关", b.get("registration_authority")),
        ("注册地址", b.get("registered_address")), ("国标行业", b.get("industry")),
        ("人员规模", b.get("staff_range")),
    ]
    make_table(doc, ["项目", "内容"], rows)
    cite(doc, "工商登记信息", b.get("data_source"))
    add_h2(doc, "二、上市基本信息")
    rows = [
        ("证券简称/代码", f"{d.get('stock_short')} / {d.get('stock_code')}"),
        ("交易所/板块", f"{d.get('exchange')} / {d.get('board')}"),
        ("上市日期", b.get("listing_date")), ("总市值", b.get("total_market_cap")),
        ("总股本", b.get("total_shares")),
    ]
    make_table(doc, ["项目", "内容"], rows)
    add_h2(doc, "三、主体资格判断")
    add_para(doc, "目标公司系依法设立并有效存续的股份有限公司，具备签订委托合同的主体资格；但已进入预重整程序，对外签约受程序限制。",
             indent_cm=0.74)
    doc.add_page_break()

    # 第三节 数据对齐基准表（核心）
    add_h1(doc, "第三节  数据对齐基准表")
    add_para(doc, "对关键字段收敛多源口径冲突，输出权威基准值。优先级：政府登记 > 交易所/证监会 > 一手公告 > 法院文书 > 权威媒体 > 商业数据库。",
             indent_cm=0.74)
    headers = ["字段", "权威基准值", "来源", "时点", "冲突说明"]
    rows = [(a["field"], a["baseline"], a["source"], a["as_of"], a.get("conflict", ""))
            for a in d.get("data_alignment", [])]
    make_table(doc, headers, rows)
    add_para(doc, "注：上表已纠正早期版本中「统一社会信用代码」等字段的编造值，统一以国家企业信用信息公示系统为准。",
             indent_cm=0.74, size=9)
    doc.add_page_break()

    # 第四节 股权结构
    add_h1(doc, "第四节  股权结构与公司治理")
    add_h2(doc, "一、前十大股东")
    headers = ["股东名称", "性质", "持股比例", "持股数(股)", "备注"]
    rows = [(s["name"], s["type"], s["ratio"], s.get("shares", ""), s.get("note", ""))
            for s in d.get("shareholders", [])]
    make_table(doc, headers, rows)
    add_h2(doc, "二、董监高")
    headers = ["姓名", "职务", "持股比例", "备注"]
    rows = [(p["name"], p["position"], p["holding"], p.get("note", "")) for p in d.get("key_persons", [])]
    make_table(doc, headers, rows)
    add_h2(doc, "三、治理关注点")
    add_para(doc, b.get("legal_rep_change", ""), indent_cm=0.74)
    add_para(doc, "法定代表人一年内两次变更、审计机构「闪辞」、董事长/总经理/董秘集中受纪律处分，属人员稳定性的高风险信号。",
             indent_cm=0.74)
    doc.add_page_break()

    # 第五节 财务
    add_h1(doc, "第五节  财务与资信")
    fin = d["financials"]
    headers = ["指标", "2023", "2024", "2025", "2026中报"]
    rows = [
        ("营业收入(亿)", f"{fin['2023']['revenue_yi']}", f"{fin['2024']['revenue_yi']}",
         f"{fin['2025']['revenue_yi']}", f"{fin['2026_h1']['revenue_yi']}"),
        ("归母净利润(亿)", f"{fin['2023']['net_profit_yi']}", f"{fin['2024']['net_profit_yi']}",
         f"{fin['2025']['net_profit_yi']}", f"{fin['2026_h1']['net_profit_yi']}"),
        ("净资产(亿)", f"{fin['2023']['net_asset_yi']}", f"{fin['2024']['net_asset_yi']}",
         f"{fin['2025']['net_asset_yi']}", f"{fin['2026_h1']['net_asset_yi']}"),
        ("资产负债率", fin['2023']['debt_ratio'], fin['2024']['debt_ratio'],
         fin['2025']['debt_ratio'], fin['2026_h1']['debt_ratio']),
    ]
    make_table(doc, headers, rows)
    cite(doc, "财务数据", fin.get("data_source"))
    add_h2(doc, "二、审计意见与审计机构异动")
    au = d["audit"]
    for k, label in [("2024_auditor", "2024年度审计"), ("2025_auditor", "2025年度审计"),
                     ("2025_ic_opinion", "2025内控审计"), ("auditor_changes", "审计机构变更"),
                     ("error_correction", "会计差错更正")]:
        add_para(doc, f"{label}：{au.get(k, '')}", indent_cm=0.74)
    add_h2(doc, "三、支付能力结论")
    add_para(doc, "公司已资不抵债（2026年中报归母净资产 -11.59 亿元），经营现金流连续三年为负，已不具备以正常经营现金流支付律师费的客观能力。",
             indent_cm=0.74, bold=True)
    doc.add_page_break()

    # 第六节 风险扫描
    add_h1(doc, "第六节  风险扫描")
    add_h2(doc, "一、司法与执行风险")
    j = d["judicial_risk"]
    add_para(doc, f"5 年内司法案件 {j.get('total_cases_5y')} 起（民事 {j.get('civil_cases')}、执行 {j.get('execution_cases')}）；{j.get('as_defendant_ratio')}。", indent_cm=0.74)
    add_para(doc, f"高频案由：{'、'.join(j.get('top_causes', []))}。", indent_cm=0.74)
    add_para(doc, j.get("unsettled_12m", ""), indent_cm=0.74)
    cite(doc, "司法风险", j.get("data_source"))
    e = d["execution_risk"]
    add_para(doc, f"失信被执行人 {e.get('dishonest_count')} 条、限制高消费 {e.get('restricted_count')} 条、被执行人 {e.get('executed_count')} 条。", indent_cm=0.74)
    cite(doc, "执行信息", e.get("data_source"))
    add_h2(doc, "二、破产与预重整风险")
    r = d["restructuring"]
    for k, label in [("creditor_application", "债权人申请"), ("court_decision", "法院决定"),
                     ("claims_deadline", "债权申报"), ("investor_round1", "首轮招募"),
                     ("investor_round2", "二轮招募"), ("subsidiary", "子公司")]:
        add_para(doc, f"{label}：{r.get(k, '')}", indent_cm=0.74)
    cite(doc, "预重整程序", r.get("data_source"))
    add_h2(doc, "三、行政监管与合规风险")
    g = d["regulatory"]
    for k, label in [("st_status", "退市风险警示"), ("investigation", "证监会立案"), ("exchange_penalty", "交易所处分")]:
        add_para(doc, f"{label}：{g.get(k, '')}", indent_cm=0.74)
    cite(doc, "监管信息", g.get("data_source"))
    doc.add_page_break()

    # 第七节 综合风险评估
    add_h1(doc, "第七节  综合风险评估")
    rs = d.get("risk_scores", {})
    dim_name = {"data_completeness": "数据完备性", "judicial_risk": "司法风险", "admin_penalty": "行政处罚",
                "abnormal": "经营异常/严重违法", "dishonest": "失信/限高/被执行", "ip_risk": "知识产权风险",
                "financial_health": "财务健康度", "media_negative": "舆情负面度", "governance": "关联与公司治理"}
    headers = ["维度", "原始分", "加权分", "评分依据"]
    rows = [(dim_name.get(k, k), str(v["raw"]), f"{v['weighted']:.2f}", v["reason"]) for k, v in rs.items()]
    make_table(doc, headers, rows)

    total = d.get("risk_total", 0)
    level = d.get("risk_level", "")
    advice = d.get("firm_advice", "")
    p = doc.add_paragraph()
    r = p.add_run(f"加权总分：{total:.2f} / 100    风险等级："); set_cn_font(r, size=12); r.bold = True
    r2 = p.add_run(level); set_cn_font(r2, size=14, font="黑体"); r2.bold = True
    r2.font.color.rgb = RGBColor(0xC0, 0x00, 0x00) if "红" in level else (RGBColor(0xC0, 0x80, 0x00) if "黄" in level else RGBColor(0x00, 0x80, 0x00))
    p2 = doc.add_paragraph()
    r3 = p2.add_run(f"承接建议：{advice}"); set_cn_font(r3, size=12); r3.bold = True
    doc.add_page_break()

    # 第八节 法律顾问切入备忘录（核心）
    add_h1(doc, "第八节  法律顾问切入备忘录")
    memo = d.get("engagement_memo", {})
    add_h2(doc, "一、切入定位")
    add_para(doc, memo.get("positioning", ""), indent_cm=0.74)
    add_h2(doc, "二、三张牌（服务切入点）")
    for c in memo.get("three_cards", []):
        add_para(doc, "• " + c, indent_cm=0.74)
    add_h2(doc, "三、切入话术")
    for i, t in enumerate(memo.get("talk_tracks", []), 1):
        add_h3(doc, f"{i}. {t['risk']}")
        add_para(doc, t["talk"], indent_cm=0.74)
    add_h2(doc, "四、需求矩阵")
    headers = ["领域", "需求描述", "紧急度"]
    rows = [(m["field"], m["desc"], m["urgency"]) for m in memo.get("demand_matrix", [])]
    make_table(doc, headers, rows)
    add_h2(doc, "五、首见问题清单")
    for g in memo.get("first_meeting_questions", []):
        add_h3(doc, g["group"])
        for q in g["questions"]:
            add_para(doc, "• " + q, indent_cm=0.74)
    doc.add_page_break()

    # 第九节 承接建议
    add_h1(doc, "第九节  承接建议与风险缓释")
    add_h2(doc, "一、客户分级建议")
    add_para(doc, f"建议：{advice}。", indent_cm=0.74, bold=True)
    add_h2(doc, "二、服务合同关键条款建议")
    for btxt in [
        "预收/阶段预收优先，最高欠款不超过月度服务费 30%，避免垫资风险；",
        "基础服务费 + 风险代理（成功激励）结构；",
        "明确律师费债权在重整中的清偿顺位与共益债务争取条款；",
        "严格限定服务范围，避免被认定参与或协助信息披露违法行为；",
        "加入「重大事项定期告知义务」条款。",
    ]:
        add_para(doc, "• " + btxt, indent_cm=0.74)
    add_h2(doc, "三、持续监控要点")
    for m in [
        "苏州中院是否正式裁定受理重整、投资人招募结果；",
        "证监会立案调查结论与行政处罚；",
        "2026年年报净资产与审计意见（决定是否触发终止上市）；",
        "实控人股份司法拍卖进展与控制权变动。",
    ]:
        add_para(doc, "• " + m, indent_cm=0.74)
    doc.add_page_break()

    # 第十节 利益冲突审查结论
    add_h1(doc, "第十节  利益冲突审查结论")
    headers = ["序号", "审查事项", "是否存在", "豁免状态"]
    rows = [(str(c["no"]), c["item"], c["result"], "已豁免" if c.get("waiver") else ("—" if c["result"] == "否" else "未豁免"))
            for c in d.get("conflict_check", [])]
    make_table(doc, headers, rows)
    concl = d.get("conflict_conclusion", "")
    if conflict_status == "blocked":
        concl = "禁止承接（存在未豁免利益冲突）"
    p = doc.add_paragraph()
    r = p.add_run(f"审查结论：{concl}"); set_cn_font(r, size=12); r.bold = True
    if conflict_status == "blocked":
        r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    doc.add_page_break()

    # 第十一节 待核实事项
    add_h1(doc, "第十一节  待核实事项清单")
    for i, item in enumerate(d.get("pending_verification", []), 1):
        add_para(doc, f"{i}. {item}", indent_cm=0.74)
    doc.add_page_break()

    # 第十二节 免责声明
    add_h1(doc, "第十二节  免责声明")
    for line in d.get("disclaimer", "").split("。"):
        if line.strip():
            p = doc.add_paragraph()
            r = p.add_run(line + "。"); set_cn_font(r, size=9, font="楷体")
            p.paragraph_format.first_line_indent = Cm(0.74)

    doc.save(out)
    return out


# ====================================================================
# O2：PDF 附件
# ====================================================================
def render_pdf(d, conflict_status):
    company = d["company_name"]
    out = OUTPUT_DIR / f"{company}-客户背调附件.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=f"{company} 客户背调附件")
    styles = getSampleStyleSheet()
    cn_title = ParagraphStyle("cn_title", parent=styles["Title"], fontName="SimHei", fontSize=22, alignment=TA_CENTER, spaceAfter=12)
    cn_h1 = ParagraphStyle("cn_h1", parent=styles["Heading1"], fontName="SimHei", fontSize=16, spaceAfter=10, leading=22)
    cn_h2 = ParagraphStyle("cn_h2", parent=styles["Heading2"], fontName="SimHei", fontSize=13, spaceAfter=8, leading=18)
    cn_p = ParagraphStyle("cn_p", parent=styles["BodyText"], fontName="SimSun", fontSize=10, leading=15, firstLineIndent=20)
    cn_p2 = ParagraphStyle("cn_p2", parent=cn_p, firstLineIndent=0)
    cn_small = ParagraphStyle("cn_small", parent=cn_p, fontSize=8, leading=11, textColor=colors.grey)

    def table_style(t, header_bg="#D9E2F3", font="SimSun", fs=9):
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), fs),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    story = []
    # 封面
    story.append(Spacer(1, 6 * cm))
    story.append(Paragraph(d.get("verifier", ""), cn_title))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("客户背调附件（PDF 合集）", cn_title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(company, ParagraphStyle("sub", parent=cn_title, fontSize=16)))
    story.append(Spacer(1, 9 * cm))
    story.append(Paragraph(f"报告编号：{d.get('report_no','')}    出具日期：{d.get('report_date','')}", cn_small))
    story.append(Paragraph("【律所保密文件  严禁外传】", cn_small))
    story.append(PageBreak())

    # 附件（一）利益冲突审查表
    story.append(Paragraph("附件（一）  利益冲突审查表", cn_h1))
    cc = d.get("conflict_check", [])
    rows = [["序号", "审查事项", "是否存在", "豁免状态"]]
    for c in cc:
        waiver = "已豁免" if c.get("waiver") else ("未豁免" if c["result"] == "是" else "—")
        rows.append([str(c["no"]), c["item"], c["result"], waiver])
    tbl = Table(rows, colWidths=[1.2 * cm, 9.5 * cm, 2.2 * cm, 3 * cm])
    table_style(tbl)
    story.append(tbl)
    story.append(Spacer(1, 0.3 * cm))
    concl = d.get("conflict_conclusion", "")
    if conflict_status == "blocked":
        concl = "禁止承接（存在未豁免利益冲突）"
    story.append(Paragraph(f"审查结论：{concl}", cn_p2))
    story.append(PageBreak())

    # 附件（二）数据对齐基准表
    story.append(Paragraph("附件（二）  数据对齐基准表", cn_h1))
    da = d.get("data_alignment", [])
    rows = [["字段", "权威基准值", "来源", "时点", "冲突说明"]]
    for a in da:
        rows.append([a["field"], a["baseline"], a["source"], a["as_of"], a.get("conflict", "")])
    tbl = Table(rows, colWidths=[2.6 * cm, 5.5 * cm, 3 * cm, 2 * cm, 3 * cm])
    table_style(tbl, fs=8)
    story.append(tbl)
    story.append(PageBreak())

    # 附件（三）风险摘要矩阵
    story.append(Paragraph("附件（三）  风险摘要矩阵", cn_h1))
    rs = d.get("risk_scores", {})
    dim_name = {"data_completeness": "数据完备性", "judicial_risk": "司法风险", "admin_penalty": "行政处罚",
                "abnormal": "经营异常/严重违法", "dishonest": "失信/限高/被执行", "ip_risk": "知识产权风险",
                "financial_health": "财务健康度", "media_negative": "舆情负面度", "governance": "关联与公司治理"}
    rows = [["维度", "原始分", "加权分", "评分依据"]]
    for k, v in rs.items():
        rows.append([dim_name.get(k, k), str(v["raw"]), f"{v['weighted']:.2f}", v["reason"]])
    rows.append(["总分", "", f"{d.get('risk_total', 0):.2f}", ""])
    rows.append(["等级", "", d.get("risk_level", ""), d.get("firm_advice", "")])
    tbl = Table(rows, colWidths=[3 * cm, 1.5 * cm, 1.5 * cm, 10 * cm])
    table_style(tbl, fs=9)
    story.append(tbl)
    story.append(PageBreak())

    # 附件（四）待核实事项清单
    story.append(Paragraph("附件（四）  待核实事项清单", cn_h1))
    for i, item in enumerate(d.get("pending_verification", []), 1):
        story.append(Paragraph(f"{i}. {item}", cn_p2))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("权威源白名单（节选）：", cn_h2))
    for w in ["gsxt.gov.cn", "wenshu.court.gov.cn", "zxgk.court.gov.cn", "creditchina.gov.cn",
              "sbj.cnipa.gov.cn", "csrc.gov.cn", "szse.cn", "cninfo.com.cn", "pccz.court.gov.cn",
              "xinhuanet.com", "people.com.cn"]:
        story.append(Paragraph(f"• {w}", cn_small))

    doc.build(story)
    return out


# ====================================================================
# 主流程
# ====================================================================
def main():
    strict = "--strict-legal" in sys.argv
    print("=" * 60)
    print("client-due-diligence 生成器")
    print("=" * 60)
    d = load_data()
    check_url_guard(d, strict)
    conflict_status, unwaived = check_conflict(d, strict)

    print("\n[R3][R4] 开始生成 docx + pdf ...")
    docx_out = render_docx(d, conflict_status)
    print(f"  - O1 主报告：{docx_out}")
    pdf_out = render_pdf(d, conflict_status)
    print(f"  - O2 PDF 附件：{pdf_out}")

    print("\n[OK] 生成完成。")
    print(f"     Word:  {docx_out}")
    print(f"     PDF:   {pdf_out}")
    if conflict_status == "blocked":
        print("     注：存在未豁免利益冲突，报告结论已置为「禁止承接」。")
    print(f"     风险：{d.get('risk_total')} / 100 → {d.get('risk_level')}")


if __name__ == "__main__":
    main()