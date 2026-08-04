# render.py —— 诉讼可视化Plus 单一内容源 HTML 渲染器（多样式）
# 同目录 SKILL.md 第七节引用本模块。运行技能时 import 此文件，
# 调用 render_html(chart) 生成图形化 HTML 片段（HTML/CSS）。
# 该函数读取同一份 chart 数据，按 type 解析，输出图形化 HTML 片段，
# 再由调用方经 Write 生成独立 .html 或直接喂 show_widget 预览。
#
# 说明：本 skill 已移除 .docx 导出能力，render.py 仅提供 HTML 渲染器。
# 如需独立 .html 文件，由 render_html 产物经 Write 生成后 present_files。

import xml.sax.saxutils as su

# 7.1 统一马蒂斯色码表（单点定义，渲染器统一取色）
# 与 SKILL.md 7.1 色码表保持一致；马蒂斯基准色（明黄/品红/深青/紫）亦在此集中定义，
# 供时间图纵向分层、关系图节点等按需取用，杜绝渲染器与文档色差。
MATISSE_COLORS = {
    "risk":     "#E83929",   # 风险/缺口 马蒂斯红
    "title":    "#2E5FB0",   # 标题蓝 钴蓝
    "party_a":  "#E6F1FB",   # 出借方/证据 蓝底
    "party_b":  "#E8852E",   # 借款方 橘
    "gap_bg":   "#FCEBEB",   # 缺口底 红底
    "proof":    "#2E9E6B",   # 证明目的 翠绿
    "proof_bg": "#EAF3DE",   # 证明底 绿底
    "amber":    "#BA7517",   # 三性 琥珀
    "amber_bg": "#FAEEDA",   # 三性底 琥珀底
    "text":     "#3A3A3A",   # 文字/连线 深灰
    "text2":    "#5A5A5A",   # 文字/连线 深灰2
    # —— 马蒂斯基准色（SKILL.md 第二节颜色规范引用）——
    "yellow":   "#F2C12E",   # 明黄
    "magenta":  "#C0306A",   # 品红
    "teal":     "#1F8A8A",   # 深青
    "purple":   "#7A4FA3",   # 紫
    "grid":     "#DDDDDD",   # 表格边框/分隔线
    "legend_bg":"#F5F5F5",   # 图例条底色
    "footer_bg":"#FAFAFA",   # 底部来源条底色
}

# 节点 color 键 -> 具体底色（关系图）。party_a/party_b 为主，其余按语义取色。
NODE_FILL = {
    "party_a": MATISSE_COLORS["party_a"],
    "party_b": MATISSE_COLORS["party_b"],
    "proof_bg": MATISSE_COLORS["proof_bg"],
    "amber_bg": MATISSE_COLORS["amber_bg"],
    "gap_bg": MATISSE_COLORS["gap_bg"],
    "yellow": MATISSE_COLORS["yellow"],
    "magenta": MATISSE_COLORS["magenta"],
    "teal": MATISSE_COLORS["teal"],
    "purple": MATISSE_COLORS["purple"],
}


# ----------------------------------------------------------------------------
# 通用工具
# ----------------------------------------------------------------------------
def _esc(s: str) -> str:
    return su.escape(str(s))


def _style(tag: str, props: dict) -> str:
    """拼装 style 属性字符串。"""
    return f'{tag} style="{";".join(f"{k}:{v}" for k, v in props.items())}"'


# ----------------------------------------------------------------------------
# HTML 渲染器（图形化，按 type 分流）—— 矢量图形化预览
# ----------------------------------------------------------------------------
def _pdf_disclaimer_html() -> str:
    """PDF 风险提示区块（强制，详见 SKILL.md 第四节第9步 / 7.5）。

    该区块须出现在每一份渲染 HTML 的末尾，确保经系统 Chrome 原生无头打印
    转 PDF 后（见 scripts/html_to_pdf.sh）真实包含在 PDF 文件内。内容固定为指定
    文本，不得包含任何内部保密信息。
    """
    risk = MATISSE_COLORS["risk"]
    text2 = MATISSE_COLORS["text2"]
    return (
        f'<div class="pdf-disclaimer" style="margin-top:24px;padding-top:14px;'
        f'border-top:1px solid #E0E0E0;font-size:13px;color:{text2};'
        f'font-family:-apple-system,\'PingFang SC\',sans-serif;line-height:1.7;">'
        f'<div style="color:{risk};font-weight:700;margin-bottom:6px;">⚠ 风险提示</div>'
        f'<div>此为 AI 生成，仅供参考。温馨提醒：用户自己可将PDF格式文件通过WPS等软件转换为DOCX格式文件，可以自行编辑、修改。</div>'
        f'</div>'
    )


def render_html(chart: dict) -> str:
    """按 chart['type'] 输出图形化 HTML 片段（时间轴/关系图/树/流程/鱼骨/表）。

    返回值为纯 HTML 字符串，由调用方写入 .html 或传 show_widget 预览。
    支持 type：time / relation / fund / element / attack / process /
    fishbone / data；`matrix` 及未知或缺失 type 均统一回落到 _html_table
    （通用表格，body 用 columns/rows 结构），保证不报错。
    输出末尾统一追加「PDF 风险提示区块」（见 _pdf_disclaimer_html）。
    """
    t = chart.get("type")
    if t == "time":
        body = _html_time(chart)
    elif t == "relation":
        body = _html_relation(chart)
    elif t == "fund":
        body = _html_fund(chart)
    elif t == "element":
        body = _html_tree(chart)
    elif t == "process":
        body = _html_process(chart)
    elif t == "fishbone":
        body = _html_fishbone(chart)
    elif t == "attack":
        body = _html_attack(chart)
    elif t == "data":
        body = _html_data(chart)
    else:
        # 表格类（matrix 及未知/缺失 type）
        body = _html_table(chart)
    return body + "\n" + _pdf_disclaimer_html()


def _title_block_html(chart):
    colors = chart.get("colors", {})
    title_color = colors.get("title", MATISSE_COLORS["title"])
    html = ['<div style="font-family:-apple-system,\'PingFang SC\',sans-serif;max-width:900px;margin:0 auto;">']
    html.append(f'<div style="background-color:{title_color};color:#fff;font-weight:700;padding:10px 14px;border-radius:6px 6px 0 0;font-size:15px;">{_esc(chart.get("title",""))}</div>')
    if chart.get("legend"):
        html.append(f'<div style="background:{MATISSE_COLORS["legend_bg"]};color:{MATISSE_COLORS["text2"]};padding:6px 14px;font-size:12px;border-bottom:1px solid {MATISSE_COLORS["grid"]};">{_esc(chart["legend"])}</div>')
    return html


def _footer_html(chart):
    footer = []
    if chart.get("source"):
        footer.append(f'数据来源：{_esc(chart["source"])}')
    if chart.get("notes"):
        footer.append(f'附注：{_esc(chart["notes"])}')
    if footer:
        return [f'<div style="background:{MATISSE_COLORS["footer_bg"]};color:{MATISSE_COLORS["text2"]};padding:8px 14px;font-size:12px;border:1px solid {MATISSE_COLORS["grid"]};border-top:none;border-radius:0 0 6px 6px;">{"<br>".join(footer)}</div>', "</div>"]
    return ["</div>"]


def _html_time(chart):
    """时间图：支持纵向分层对比（不同主体上下分置，各主体一色），
    与 SKILL.md 模板 A「纵向分层对比」一致。"""
    colors = chart.get("colors", {})
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    party_a = colors.get("party_a", MATISSE_COLORS["party_a"])
    party_b = colors.get("party_b", MATISSE_COLORS["party_b"])
    events = chart.get("body", {}).get("events", [])
    # 收集参与方，按出现顺序纵向分层
    parties = []
    for ev in events:
        p = ev.get("party", "")
        if p and p not in parties:
            parties.append(p)
    if not parties:
        parties = ["方"]
    party_fill = {}
    palette = [party_a, party_b, MATISSE_COLORS["yellow"], MATISSE_COLORS["teal"], MATISSE_COLORS["purple"]]
    for i, p in enumerate(parties):
        party_fill[p] = palette[i % len(palette)]

    html = _title_block_html(chart)
    html.append(f'<div style="padding:14px;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    # 左侧时间列 + 右侧各主体纵向泳道
    lane_w = max(70, 110 - 12 * max(0, len(parties) - 2))
    html.append('<div style="display:flex;gap:8px;">')
    # 时间列
    html.append(f'<div style="width:{lane_w}px;flex-shrink:0;"></div>')
    # 主体泳道表头
    for p in parties:
        html.append(f'<div style="flex:1;text-align:center;font-weight:700;padding:4px;color:{MATISSE_COLORS["text"]};">{_esc(p)}</div>')
    html.append('</div>')
    # 逐事件行
    for ev in events:
        is_risk = ev.get("risk")
        p = ev.get("party", parties[0])
        bg = MATISSE_COLORS["gap_bg"] if is_risk else party_fill.get(p, "#fff")
        txt = _esc(ev.get("text", ""))
        if is_risk:
            txt = f'<span style="color:{risk_color};font-weight:600;">{txt}</span>'
        html.append('<div style="display:flex;gap:8px;align-items:stretch;margin-bottom:8px;">')
        html.append(f'<div style="width:{lane_w}px;flex-shrink:0;color:{MATISSE_COLORS["text2"]};padding-top:6px;">{_esc(ev.get("date",""))}</div>')
        for lp in parties:
            if lp == p:
                html.append(f'<div style="flex:1;background:{bg};border:1px solid {MATISSE_COLORS["grid"]};border-radius:6px;padding:6px 10px;">{txt}</div>')
            else:
                html.append(f'<div style="flex:1;border:1px dashed {MATISSE_COLORS["grid"]};border-radius:6px;"></div>')
        html.append('</div>')
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_relation(chart):
    """关系图：按 level 分行排布节点，并用 SVG 在节点间绘制 from→to 连线与箭头，
    连线标签标注关系性质；与 SKILL.md「关系（连线并标注性质与依据）」一致。"""
    colors = chart.get("colors", {})
    nodes = chart.get("body", {}).get("nodes", [])
    edges = chart.get("body", {}).get("edges", [])
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    max_level = max([n.get("level", 0) for n in nodes], default=0)
    lanes = {}
    for n in nodes:
        lanes.setdefault(n.get("level", 0), []).append(n)
    node_by_id = {n.get("id"): n for n in nodes}

    html = _title_block_html(chart)
    html.append(f'<div style="padding:16px;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    # 计算节点布局坐标（供 SVG 连线）
    lane_height = 90
    node_width = 120
    node_positions = {}
    for lvl in range(max_level + 1):
        row = lanes.get(lvl, [])
        row_w = len(row) * (node_width + 40)
        start_x = max(0, (760 - row_w) // 2) + node_width // 2
        for idx, n in enumerate(row):
            x = start_x + idx * (node_width + 40)
            y = 23 + lvl * lane_height
            node_positions[n.get("id")] = (x, y)

    # 画布 + SVG 连线（置于底层）
    svg = [f'<svg width="100%" height="{23 + (max_level + 1) * lane_height}px" style="position:absolute;left:0;top:0;pointer-events:none;">']
    for e in edges:
        f = node_by_id.get(e.get("from"))
        t = node_by_id.get(e.get("to"))
        if not f or not t:
            continue
        x1, y1 = node_positions.get(e.get("from"), (0, 0))
        x2, y2 = node_positions.get(e.get("to"), (0, 0))
        dash = 'stroke-dasharray="6 4"' if e.get("kind") == "dash" else ""
        col = risk_color if e.get("risk") else MATISSE_COLORS["title"]
        # 末端箭头
        svg.append(f'<defs><marker id="arw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{col}"/></marker></defs>')
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="2" {dash} marker-end="url(#arw)"/>')
        # 连线标签
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 6
        svg.append(f'<text x="{mx}" y="{my}" fill="{col}" font-size="11" text-anchor="middle">{_esc(e.get("label",""))}</text>')
    svg.append('</svg>')

    html.append(f'<div style="position:relative;">{ "".join(svg) }')
    for lvl in range(max_level + 1):
        row = lanes.get(lvl, [])
        html.append(f'<div style="display:flex;gap:40px;justify-content:center;margin-bottom:{lane_height - 50}px;position:relative;z-index:1;">')
        for n in row:
            fill = NODE_FILL.get(n.get("color", ""), MATISSE_COLORS["party_a"])
            shape = n.get("shape", "box")
            radius = "50%" if shape == "ellipse" else "8px"
            html.append(
                f'<div style="background:{fill};border:2px solid {MATISSE_COLORS["title"]};border-radius:{radius};'
                f'padding:10px 16px;font-weight:600;min-width:{node_width-40}px;text-align:center;">{_esc(n.get("label",""))}</div>'
            )
        html.append('</div>')
    html.append('</div></div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_tree(chart):
    html = _title_block_html(chart)
    html.append(f'<div style="padding:14px;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    root = chart.get("body", {}).get("root", "")
    html.append(f'<div style="font-weight:700;color:{MATISSE_COLORS["title"]};margin-bottom:8px;">▣ {_esc(root)}</div>')
    def walk(children, depth):
        for c in children:
            gap = "⚠" if c.get("gap") else "●"
            col = MATISSE_COLORS["risk"] if c.get("gap") else MATISSE_COLORS["proof"]
            html.append(f'<div style="margin-left:{depth*22}px;">{gap} <span style="color:{col};font-weight:600;">{_esc(c.get("label",""))}</span>'
                        f' <span style="color:{MATISSE_COLORS["text2"]};">{_esc(c.get("support",""))}</span></div>')
            if c.get("children"):
                walk(c["children"], depth + 1)
    walk(chart.get("body", {}).get("children", []), 1)
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_process(chart):
    colors = chart.get("colors", {})
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    steps = chart.get("body", {}).get("steps", [])
    html = _title_block_html(chart)
    html.append(f'<div style="padding:14px;font-size:13px;color:{MATISSE_COLORS["text"]};display:flex;flex-wrap:wrap;gap:10px;">')
    for i, s in enumerate(steps):
        is_risk = s.get("risk")
        bg = MATISSE_COLORS["gap_bg"] if is_risk else MATISSE_COLORS["proof_bg"]
        txt = _esc(s.get("action", ""))
        if is_risk:
            txt = f'<span style="color:{risk_color};font-weight:600;">{txt}</span>'
        html.append(
            f'<div style="background:{bg};border:1px solid {MATISSE_COLORS["proof"]};border-radius:8px;padding:10px 12px;min-width:140px;flex:1;">'
            f'<div style="font-weight:700;">{i+1}. {_esc(s.get("stage",""))}</div>'
            f'<div>{txt}</div>'
            f'<div style="color:{MATISSE_COLORS["text2"]};font-size:12px;">⏱ {_esc(s.get("deadline",""))}</div></div>'
        )
        if i < len(steps) - 1:
            html.append('<div style="align-self:center;color:#2E9E6B;font-weight:700;">→</div>')
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_fishbone(chart):
    spine = chart.get("body", {}).get("spine", "")
    bones = chart.get("body", {}).get("bones", [])
    html = _title_block_html(chart)
    html.append(f'<div style="padding:16px;font-size:13px;color:{MATISSE_COLORS["text"]};"><div style="font-weight:700;color:{MATISSE_COLORS["title"]};margin-bottom:10px;">鱼骨主轴：{_esc(spine)}</div>')
    for b in bones:
        html.append(f'<div style="margin-bottom:8px;"><span style="color:{MATISSE_COLORS["party_b"]};font-weight:600;">▸ {_esc(b.get("cause",""))}</span>：{_esc(b.get("detail",""))}</div>')
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_fund(chart):
    """资金/财产流向图：body 使用 rows 结构（与 matrix 同构）：
    cells[0]=付款方, cells[1]=收款方, cells[2]=金额, cells[3]=币种/时间等。
    箭头 + 金额呈现，异常回流用马蒂斯红高亮，与 SKILL.md 模板 D 一致。"""
    colors = chart.get("colors", {})
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    rows = chart.get("body", {}).get("rows", [])
    html = _title_block_html(chart)
    html.append(f'<div style="padding:14px;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    for r in rows:
        is_risk = r.get("risk")
        cells = r.get("cells", [])
        payer = _esc(cells[0]) if len(cells) > 0 else ""
        payee = _esc(cells[1]) if len(cells) > 1 else ""
        amount = _esc(cells[2]) if len(cells) > 2 else ""
        extra = _esc(" ".join(cells[3:])) if len(cells) > 3 else ""
        flow = f'{payer} <span style="color:{MATISSE_COLORS["title"]};font-weight:700;">→</span> {payee}'
        bg = MATISSE_COLORS["gap_bg"] if is_risk else MATISSE_COLORS["proof_bg"]
        if is_risk:
            flow = f'<span style="color:{risk_color};font-weight:600;">{flow}</span>'
        html.append(
            f'<div style="background:{bg};border:1px solid {MATISSE_COLORS["proof"]};border-radius:8px;'
            f'padding:8px 12px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
            f'<div>{flow}</div>'
            f'<div style="color:{MATISSE_COLORS["text2"]};font-weight:600;">金额：{amount} {extra}</div></div>'
        )
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_attack(chart):
    """攻防对抗图：双栏（我方 ↔ 对方），中缝列争议焦点。
    未指定代理方时双栏均衡（见 SKILL.md 第五节）。body 用 columns/rows 同矩阵。"""
    colors = chart.get("colors", {})
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    body = chart.get("body", {})
    columns = body.get("columns", ["我方主张/依据", "争议焦点与待证事项", "对方主张/依据"])
    rows = body.get("rows", [])
    html = _title_block_html(chart)
    html.append(f'<div style="padding:12px;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    html.append('<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-weight:700;margin-bottom:6px;">')
    for c in columns[:3]:
        html.append(f'<div style="background:{MATISSE_COLORS["proof_bg"]};padding:8px;text-align:center;border-radius:6px 6px 0 0;">{_esc(str(c))}</div>')
    html.append('</div>')
    for r in rows:
        cells = r.get("cells", [])
        row_bg = MATISSE_COLORS["gap_bg"] if r.get("risk") else "#fff"
        html.append('<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:6px;">')
        for i, c in enumerate(cells[:3]):
            txt = _esc(str(c)) if c else "&nbsp;"
            if r.get("risk") and c:
                txt = f'<span style="color:{risk_color};font-weight:600;">{txt}</span>'
            html.append(f'<div style="background:{row_bg};border:1px solid {MATISSE_COLORS["grid"]};padding:8px;border-radius:6px;">{txt}</div>')
        html.append('</div>')
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _parse_amount(val_raw: str):
    """解析带单位的中文数值字符串，返回以「元」为基准的浮点数。

    支持写法（可组合）：逗号千分位、¥ 符号、空格、正负号；
    单位万/万元/元、亿/亿元、百分比 %（按百分点数值返回，如 30% -> 30.0）。
    无法解析时回落到 0.0，不抛异常。
    """
    s = str(val_raw).strip()
    if not s:
        return 0.0
    # 百分比单独处理：保留数值本身（30% -> 30.0）
    is_pct = "%" in s
    # 去除常见符号与单位
    cleaned = (s.replace(",", "").replace("¥", "").replace("￥", "")
               .replace("元", "").replace("万", "").replace("亿", "")
               .replace("%", "").replace(" ", "").replace("+", ""))
    neg = cleaned.startswith("-")
    cleaned = cleaned.lstrip("-")
    try:
        num = float(cleaned or 0)
    except Exception:
        return 0.0
    if "亿" in s and "万" not in s:
        num *= 100_000_000
    elif "万" in s:
        num *= 10_000
    if is_pct:
        num = abs(num)  # 百分比按原始百分点展示，不放大
    if neg:
        num = -num
    return num


def _html_data(chart):
    """数据图：横向柱状对比（标的额/利息/份额/赔偿等），关键数据用马蒂斯红高亮。
    body 用 rows 同矩阵，cells[0]=项目, cells[1]=数值（支持带单位字符串，详见 _parse_amount）。"""
    colors = chart.get("colors", {})
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    body = chart.get("body", {})
    rows = body.get("rows", [])
    parsed = []
    for r in rows:
        cells = r.get("cells", [])
        label = _esc(str(cells[0])) if cells else ""
        val_raw = str(cells[1]) if len(cells) > 1 else "0"
        val = _parse_amount(val_raw)
        is_pct = "%" in str(cells[1]) if len(cells) > 1 else False
        parsed.append((label, val_raw, val, is_pct, r.get("risk", False)))
    # 量纲分组：百分比项用 100 为满刻，非百分比项用自身最大值满刻，
    # 避免「亿元 vs 万元 vs 百分比」混用导致柱长失真（量纲压制）。
    pct_vals = [v for (_l, _r, v, is_p, _rk) in parsed if is_p]
    num_vals = [v for (_l, _r, v, is_p, _rk) in parsed if not is_p and v != 0]
    pct_max = max(pct_vals) if pct_vals else 100.0
    num_max = max([abs(v) for v in num_vals]) if num_vals else 1.0
    has_mixed = bool(pct_vals) and bool(num_vals)
    html = _title_block_html(chart)
    if has_mixed:
        html.append(f'<div style="padding:0 14px;color:{MATISSE_COLORS["risk"]};font-size:12px;">⚠ 注：含百分比与金额两类量纲，已分组按比例呈现，不可跨类直接比较数值大小。</div>')
    html.append(f'<div style="padding:14px;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    for label, val_raw, val, is_pct, is_risk in parsed:
        if is_pct:
            pct = int((val / pct_max) * 100) if pct_max else 0
        else:
            pct = int((abs(val) / num_max) * 100) if num_max else 0
        pct = max(0, min(100, pct))
        bar_col = risk_color if is_risk else MATISSE_COLORS["title"]
        txt_col = risk_color if is_risk else MATISSE_COLORS["text"]
        html.append(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
            f'<div style="width:120px;flex-shrink:0;text-align:right;color:{MATISSE_COLORS["text2"]};">{label}</div>'
            f'<div style="flex:1;background:{MATISSE_COLORS["legend_bg"]};border-radius:4px;height:22px;position:relative;">'
            f'<div style="width:{pct}%;background:{bar_col};height:22px;border-radius:4px;"></div></div>'
            f'<div style="width:90px;flex-shrink:0;color:{txt_col};font-weight:600;">{_esc(val_raw)}</div></div>'
        )
    html.append('</div>')
    html += _footer_html(chart)
    return "\n".join(html)


def _html_table(chart):
    colors = chart.get("colors", {})
    risk_color = colors.get("risk", MATISSE_COLORS["risk"])
    body = chart.get("body", {})
    columns = body.get("columns", [])
    rows = body.get("rows", [])
    html = _title_block_html(chart)
    html.append(f'<table style="width:100%;border-collapse:collapse;font-size:13px;color:{MATISSE_COLORS["text"]};">')
    if columns:
        html.append("<thead><tr>")
        for c in columns:
            html.append(f'<th style="border:1px solid {MATISSE_COLORS["grid"]};background:#f0f0f0;padding:8px;text-align:left;font-weight:600;">{_esc(str(c))}</th>')
        html.append("</tr></thead>")
    html.append("<tbody>")
    for r in rows:
        cells = r.get("cells", [])
        row_bg = MATISSE_COLORS["gap_bg"] if r.get("risk") else ""
        html.append("<tr>")
        for i, c in enumerate(cells):
            style = f"border:1px solid {MATISSE_COLORS['grid']};padding:8px;vertical-align:top;"
            if row_bg:
                style += f"background-color:{row_bg};"
            txt = _esc(str(c)) if c else "&nbsp;"
            if r.get("risk") and c:
                txt = f'<span style="color:{risk_color};font-weight:600;">{txt}</span>'
            html.append(f"<td style=\"{style}\">{txt}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")
    html += _footer_html(chart)
    return "\n".join(html)


if __name__ == "__main__":
    demo_chart = {
        "title": "【图一·时间图】借款关系成立于2023-03-10",
        "type": "time",
        "legend": "■事实 □〔分析〕 ⚠风险",
        "body": {"events": [
            {"date": "2023-03-10", "party": "甲", "text": "签订借条出借50万", "risk": False},
            {"date": "2023-09-10", "party": "乙", "text": "应还款未还", "risk": True},
        ]},
        "colors": {"title": MATISSE_COLORS["title"], "risk": MATISSE_COLORS["risk"],
                   "party_a": MATISSE_COLORS["party_a"], "party_b": MATISSE_COLORS["party_b"]},
        "source": "材料：借条/转账凭证", "notes": "利息待核",
    }
    print(render_html(demo_chart))
