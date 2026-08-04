#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 法律助手 —— 中文合同审查报告 PDF 生成器
使用 ReportLab 生成符合中文法律语境的合同审查报告。
"""

import sys
import os
import json
import math
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, mm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Circle, Rect, String, Line, Wedge
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("错误：缺少 reportlab 依赖，请先安装：pip3 install reportlab")
    sys.exit(1)


# ---------------------------------------------------------------------------
# 中文字体注册
# ---------------------------------------------------------------------------
def register_chinese_fonts():
    """
    注册中文字体。
    优先尝试加载 Windows 系统自带的字体（微软雅黑/宋体），解决部分阅读器乱码或不显示问题。
    失败则回退到 ReportLab 自带的 CID 字体。
    """
    try:
        font_path_msyh = "C:/Windows/Fonts/msyh.ttc"
        font_path_simsun = "C:/Windows/Fonts/simsun.ttc"
        
        if os.path.exists(font_path_msyh):
            pdfmetrics.registerFont(TTFont("STSong-Light", font_path_msyh, subfontIndex=0))
            pdfmetrics.registerFont(TTFont("Helvetica-Bold", font_path_msyh, subfontIndex=0))
            pdfmetrics.registerFont(TTFont("Helvetica", font_path_msyh, subfontIndex=0))
        elif os.path.exists(font_path_simsun):
            pdfmetrics.registerFont(TTFont("STSong-Light", font_path_simsun, subfontIndex=0))
            pdfmetrics.registerFont(TTFont("Helvetica-Bold", font_path_simsun, subfontIndex=0))
            pdfmetrics.registerFont(TTFont("Helvetica", font_path_simsun, subfontIndex=0))
        else:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception as e:
        print(f"警告：系统字体注册失败（{e}），回退到 CID 字体")
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        except Exception as ex:
            print(f"错误：CID中文字体注册失败：{ex}")
            sys.exit(1)


# ---------------------------------------------------------------------------
# 颜色配置
# ---------------------------------------------------------------------------
COLORS = {
    "primary": HexColor("#1a365d"),       # 深蓝
    "secondary": HexColor("#2d5f8a"),     # 中蓝
    "accent": HexColor("#3182ce"),        # 亮蓝
    "success": HexColor("#38a169"),       # 绿色
    "warning": HexColor("#d69e2e"),       # 黄色
    "danger": HexColor("#e53e3e"),        # 红色
    "light_bg": HexColor("#f7fafc"),      # 浅灰背景
    "dark_text": HexColor("#1a202c"),     # 深色文字
    "gray_text": HexColor("#718096"),     # 灰色文字
    "white": white,
    "black": black,
    "light_border": HexColor("#e2e8f0"),  # 浅边框
    "high_risk_bg": HexColor("#fff5f5"),  # 高风险背景
    "med_risk_bg": HexColor("#fffff0"),   # 中风险背景
    "low_risk_bg": HexColor("#f0fff4"),   # 低风险背景
}


# ---------------------------------------------------------------------------
# 文本工具
# ---------------------------------------------------------------------------
def safe_text(value, default="未提供"):
    """安全转字符串，避免 None 和非字符串值造成显示异常。"""
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def format_cn_date(dt=None, with_time=False):
    """格式化中文日期。"""
    dt = dt or datetime.now()
    if with_time:
        return dt.strftime("%Y年%m月%d日 %H:%M")
    return dt.strftime("%Y年%m月%d日")


def get_grade_label(score):
    """
    若输入 JSON 未提供 grade_label，则根据分数自动生成中文评级说明。
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "未评级"

    if score >= 90:
        return "风险较低，可推进签署"
    if score >= 75:
        return "整体可控，建议修改后签署"
    if score >= 60:
        return "存在一定风险，建议重点谈判"
    if score >= 40:
        return "风险较高，建议谨慎处理"
    return "风险重大，建议暂缓签署"


def get_grade(score):
    """
    若输入 JSON 未提供 grade，则根据分数自动生成等级。
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "N/A"

    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "E"


def risk_text(risk):
    mapping = {
        "high": "重大风险",
        "medium": "一般风险",
        "low": "低风险",
        "重大风险": "重大风险",
        "一般风险": "一般风险",
        "低风险": "低风险",
    }
    return mapping.get(str(risk).strip().lower(), safe_text(risk, "未标注风险"))


def risk_color(risk):
    key = str(risk).strip().lower()
    if key in ("high", "重大风险"):
        return COLORS["danger"]
    if key in ("medium", "一般风险"):
        return COLORS["warning"]
    if key in ("low", "低风险"):
        return COLORS["success"]
    return COLORS["gray_text"]


def escape_xml(text):
    """
    Paragraph 支持简单 HTML/XML 标记，这里做基本转义。
    """
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


# ---------------------------------------------------------------------------
# 评分仪表盘
# ---------------------------------------------------------------------------
def create_score_gauge(score, size=200):
    """创建半圆形评分仪表盘。"""
    d = Drawing(size, size * 0.68)
    cx, cy = size / 2, size * 0.56
    radius = size * 0.4

    try:
        score = max(0, min(100, float(score)))
    except (TypeError, ValueError):
        score = 0

    segments = [
        (0, 36, COLORS["danger"]),
        (36, 72, HexColor("#ed8936")),
        (72, 108, COLORS["warning"]),
        (108, 144, HexColor("#68d391")),
        (144, 180, COLORS["success"]),
    ]

    for start, end, color in segments:
        w = Wedge(
            cx, cy, radius, 180 + start, 180 + end,
            fillColor=color, strokeColor=white, strokeWidth=2
        )
        d.add(w)

    inner = Circle(cx, cy, radius * 0.65, fillColor=white, strokeColor=None)
    d.add(inner)

    score_text = String(
        cx, cy - 6, str(int(score)),
        fontSize=34, fillColor=COLORS["primary"],
        textAnchor="middle", fontName="Helvetica-Bold"
    )
    d.add(score_text)

    label = String(
        cx, cy - 24, "/ 100",
        fontSize=11, fillColor=COLORS["gray_text"],
        textAnchor="middle", fontName="Helvetica"
    )
    d.add(label)

    angle_deg = 180 + (score / 100) * 180
    angle_rad = math.radians(angle_deg)
    needle_len = radius * 0.55
    nx = cx + needle_len * math.cos(angle_rad)
    ny = cy + needle_len * math.sin(angle_rad)
    needle = Line(cx, cy, nx, ny, strokeColor=COLORS["primary"], strokeWidth=2.5)
    d.add(needle)

    center_dot = Circle(cx, cy, 5, fillColor=COLORS["primary"], strokeColor=None)
    d.add(center_dot)

    return d


# ---------------------------------------------------------------------------
# 风险分布图
# ---------------------------------------------------------------------------
def create_risk_bar_chart(high, medium, low, width=420, height=110):
    """创建水平堆叠风险分布图。"""
    d = Drawing(width, height)

    try:
        high = int(high or 0)
        medium = int(medium or 0)
        low = int(low or 0)
    except (TypeError, ValueError):
        high, medium, low = 0, 0, 0

    total = high + medium + low
    if total == 0:
        d.add(String(
            width / 2, height / 2, "暂无风险统计数据",
            fontSize=11, fillColor=COLORS["gray_text"],
            textAnchor="middle", fontName="Helvetica"
        ))
        return d

    bar_width = width * 0.72
    bar_height = 26
    x_start = width * 0.14
    y = height * 0.42

    high_w = (high / total) * bar_width
    med_w = (medium / total) * bar_width
    low_w = (low / total) * bar_width

    if high_w > 0:
        d.add(Rect(x_start, y, high_w, bar_height, fillColor=COLORS["danger"], strokeColor=None))
    if med_w > 0:
        d.add(Rect(x_start + high_w, y, med_w, bar_height, fillColor=COLORS["warning"], strokeColor=None))
    if low_w > 0:
        d.add(Rect(x_start + high_w + med_w, y, low_w, bar_height, fillColor=COLORS["success"], strokeColor=None))

    labels = [
        (f"重大风险：{high}", COLORS["danger"], x_start),
        (f"一般风险：{medium}", COLORS["warning"], x_start + bar_width * 0.34),
        (f"低风险：{low}", COLORS["success"], x_start + bar_width * 0.68),
    ]
    for text, color, x in labels:
        d.add(String(x, y - 16, text, fontSize=9, fillColor=color, fontName="Helvetica-Bold"))

    return d


# ---------------------------------------------------------------------------
# 样式定义
# ---------------------------------------------------------------------------
def get_styles():
    styles = getSampleStyleSheet()
    cn_font = "STSong-Light"

    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontName=cn_font,
        fontSize=26,
        textColor=COLORS["primary"],
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=32
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontName=cn_font,
        fontSize=12,
        textColor=COLORS["gray_text"],
        alignment=TA_CENTER,
        spaceAfter=18,
        leading=18
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName=cn_font,
        fontSize=15,
        textColor=COLORS["primary"],
        spaceBefore=18,
        spaceAfter=10,
        leading=22
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        fontName=cn_font,
        fontSize=11.5,
        textColor=COLORS["secondary"],
        spaceBefore=10,
        spaceAfter=5,
        leading=18
    ))
    styles.add(ParagraphStyle(
        name="BodyTextCN",
        fontName=cn_font,
        fontSize=10,
        textColor=COLORS["dark_text"],
        spaceBefore=4,
        spaceAfter=4,
        leading=16,
        alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name="Disclaimer",
        fontName=cn_font,
        fontSize=8.5,
        textColor=COLORS["gray_text"],
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10,
        leading=14
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontName=cn_font,
        fontSize=8,
        textColor=COLORS["gray_text"],
        alignment=TA_CENTER,
        leading=12
    ))

    return styles


# ---------------------------------------------------------------------------
# PDF 构建
# ---------------------------------------------------------------------------
def build_pdf(data, output_path):
    """根据结构化数据生成中文合同审查 PDF。"""
    register_chinese_fonts()
    styles = get_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    story = []

    score = data.get("score", 0)
    grade = safe_text(data.get("grade"), get_grade(score))
    grade_label = safe_text(data.get("grade_label"), get_grade_label(score))

    # ── 封面 ──
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph("合同审查报告", styles["CoverTitle"]))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(f"生成日期：{format_cn_date()}", styles["CoverSubtitle"]))
    story.append(Spacer(1, 12 * mm))

    gauge = create_score_gauge(score)
    story.append(gauge)
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph(
        f"综合评分：{escape_xml(grade)}（{escape_xml(grade_label)}）",
        styles["CoverSubtitle"]
    ))

    story.append(Spacer(1, 16 * mm))
    story.append(Paragraph(
        "【声明】本报告基于人工智能技术自动生成，仅供合同审查参考，不构成正式法律意见。"
        "在签署合同、作出重大商业决策或处理争议事项前，建议结合具体业务背景并咨询专业律师。",
        styles["Disclaimer"]
    ))

    story.append(PageBreak())

    # ── 一、合同基本信息 ──
    story.append(Paragraph("一、合同基本信息", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))

    details = data.get("details", {})
    detail_rows = [
        ["合同类型", safe_text(details.get("type"))],
        ["合同主体", safe_text(details.get("parties"))],
        ["生效日期", safe_text(details.get("effective_date"))],
        ["合同期限", safe_text(details.get("term"))],
        ["合同金额", safe_text(details.get("total_value"))],
        ["适用法律", safe_text(details.get("governing_law"))],
    ]

    detail_table = Table(detail_rows, colWidths=[35 * mm, 120 * mm])
    detail_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), COLORS["primary"]),
        ("TEXTCOLOR", (1, 0), (1, -1), COLORS["dark_text"]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, COLORS["light_border"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 10))

    # ── 二、审查结论 ──
    story.append(Paragraph("二、审查结论", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))
    story.append(Paragraph(
        escape_xml(safe_text(data.get("executive_summary"), "暂无审查结论。")),
        styles["BodyTextCN"]
    ))
    story.append(Spacer(1, 10))

    # ── 三、风险概览 ──
    story.append(Paragraph("三、风险概览", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))

    risks = data.get("risks", {"high": 0, "medium": 0, "low": 0})
    high = risks.get("high", 0)
    medium = risks.get("medium", 0)
    low = risks.get("low", 0)

    risk_chart = create_risk_bar_chart(high, medium, low)
    story.append(risk_chart)
    story.append(Spacer(1, 12))

    risk_rows = [
        ["风险等级", "数量", "涉及条款"],
        ["重大风险", str(high or 0), safe_text(risks.get("high_clauses"), "无")],
        ["一般风险", str(medium or 0), safe_text(risks.get("medium_clauses"), "无")],
        ["低风险", str(low or 0), safe_text(risks.get("low_clauses"), "无")],
    ]
    risk_table = Table(risk_rows, colWidths=[30 * mm, 20 * mm, 110 * mm])
    risk_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLORS["white"]),
        ("BACKGROUND", (0, 1), (-1, 1), COLORS["high_risk_bg"]),
        ("TEXTCOLOR", (0, 1), (0, 1), COLORS["danger"]),
        ("BACKGROUND", (0, 2), (-1, 2), COLORS["med_risk_bg"]),
        ("TEXTCOLOR", (0, 2), (0, 2), COLORS["warning"]),
        ("BACKGROUND", (0, 3), (-1, 3), COLORS["low_risk_bg"]),
        ("TEXTCOLOR", (0, 3), (0, 3), COLORS["success"]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, COLORS["light_border"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 12))

    # ── 四、条款逐条审查意见 ──
    clauses = data.get("clauses", [])
    if clauses:
        story.append(PageBreak())
        story.append(Paragraph("四、条款逐条审查意见", styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))

        for clause in clauses:
            risk = clause.get("risk", "low")
            cn_risk = risk_text(risk)
            color = risk_color(risk)

            clause_name = safe_text(clause.get("name"), "未命名条款")
            section = safe_text(clause.get("section"), "未标明")
            summary = safe_text(clause.get("summary"), "")
            risk_explanation = safe_text(clause.get("risk_explanation"), "")
            recommendation = safe_text(clause.get("recommendation"), "")

            clause_block = []

            clause_block.append(Paragraph(
                f'<font color="{color.hexval()}">【{escape_xml(cn_risk)}】</font>'
                f'<b>{escape_xml(clause_name)}</b>（第{escape_xml(section)}条）',
                styles["SubHeader"]
            ))

            if summary:
                clause_block.append(Paragraph(
                    f'<b>条款内容：</b>{escape_xml(summary)}',
                    styles["BodyTextCN"]
                ))

            if risk_explanation:
                clause_block.append(Paragraph(
                    f'<b>风险分析：</b>{escape_xml(risk_explanation)}',
                    styles["BodyTextCN"]
                ))

            if recommendation:
                clause_block.append(Paragraph(
                    f'<b>修改建议：</b>{escape_xml(recommendation)}',
                    styles["BodyTextCN"]
                ))

            clause_block.append(Spacer(1, 8))
            story.append(KeepTogether(clause_block))

    # ── 五、重点谈判事项 ──
    priorities = data.get("negotiation_priorities", [])
    if priorities:
        story.append(Paragraph("五、重点谈判事项", styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))
        for i, priority in enumerate(priorities, 1):
            story.append(Paragraph(
                f"<b>{i}.</b> {escape_xml(safe_text(priority, ''))}",
                styles["BodyTextCN"]
            ))
        story.append(Spacer(1, 10))

    # ── 六、缺失条款及建议补充 ──
    missing = data.get("missing_protections", [])
    if missing:
        story.append(Paragraph("六、缺失条款及建议补充", styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))
        for item in missing:
            story.append(Paragraph(
                f"• {escape_xml(safe_text(item, ''))}",
                styles["BodyTextCN"]
            ))
        story.append(Spacer(1, 10))

    # ── 七、后续处理建议 ──
    steps = data.get("next_steps", [])
    if steps:
        story.append(Paragraph("七、后续处理建议", styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLORS["light_border"]))
        for i, step in enumerate(steps, 1):
            story.append(Paragraph(
                f"<b>{i}.</b> {escape_xml(safe_text(step, ''))}",
                styles["BodyTextCN"]
            ))
        story.append(Spacer(1, 10))

    # ── 页脚声明 ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLORS["light_border"]))
    story.append(Paragraph(
        "本报告由 AI 合同审查系统自动生成，仅供内部审阅与参考，不构成正式法律意见。",
        styles["Disclaimer"]
    ))
    story.append(Paragraph(
        f"生成时间：{format_cn_date(with_time=True)}",
        styles["Footer"]
    ))

    doc.build(story)
    return output_path


# ---------------------------------------------------------------------------
# 主程序入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    register_chinese_fonts()

    if len(sys.argv) < 2:
        print("用法：python3 generate_legal_pdf.py <json数据文件> [输出PDF路径]")
        print("  <json数据文件>：包含报告数据的 JSON 文件路径")
        print("  [输出PDF路径]：可选，默认输出为 合同审查报告.pdf")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "合同审查报告.pdf"

    if not os.path.exists(json_path):
        print(f"错误：JSON 文件不存在：{json_path}")
        sys.exit(1)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(json_path, "r", encoding="gbk") as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误：读取 JSON 失败：{e}")
        sys.exit(1)

    try:
        result = build_pdf(data, output_path)
        print(f"PDF 生成成功：{result}")
    except Exception as e:
        print(f"错误：生成 PDF 失败：{e}")
        sys.exit(1)