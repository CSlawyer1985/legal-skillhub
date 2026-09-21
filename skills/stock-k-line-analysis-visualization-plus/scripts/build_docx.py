"""将股票技术分析结果合并为一份完整 DOCX 报告并保存到用户桌面。

用法:
  python build_docx.py --workspace <工作区绝对路径> --code <代码> --name <名称> [--desktop <桌面绝对路径>]

输出:
  <桌面>/<名称>（<代码>）日K线技术分析报告.docx

报告结构（单一文件、含页码）:
  1. 封面标题 + 数据区间说明
  2. 核心指标速览表（8项，红涨绿跌着色）
  3. 技术形态分析（趋势/均线/MACD/布林/RSI/量能/支撑阻力/综合判断，共8节，结论与指标联动）
  4. 文字分析摘要（逐段综合结论）
  5. 风险提示（灰色小字，含免责声明）
  6. 分析图表（内嵌 matplotlib 静态 PNG 两张）
  7. 页码（底部居中）

依赖: python-docx (已在 managed venv 中安装)
"""
import os
import sys
import json
import argparse
import numpy as np
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday as intraday_mod
import signal_score as signal_mod


UP_RED = RGBColor(0xE2, 0x3B, 0x3B)   # 红涨
DOWN_GREEN = RGBColor(0x1A, 0xA3, 0x4A)  # 绿跌
DARK = RGBColor(0x1A, 0x22, 0x38)
GREY = RGBColor(0x88, 0x88, 0x88)


def load_metrics(workspace, code):
    kline_path = os.path.join(workspace, f"{code}_kline.json")
    with open(kline_path, encoding="utf-8") as f:
        data = json.load(f)
    klines = data["data"]["klines"]
    rows = []
    for k in klines:
        p = k.split(",")
        dt = p[0]
        o, c, h, l = float(p[1]), float(p[2]), float(p[3]), float(p[4])
        vol = float(p[5])
        rows.append((dt, o, c, h, l, vol))
    dates = [r[0] for r in rows]
    closes = np.array([r[2] for r in rows])
    highs = np.array([r[3] for r in rows])
    lows = np.array([r[4] for r in rows])
    vols = np.array([r[5] for r in rows])
    n = len(closes)

    def ma(arr, w):
        return np.round(np.convolve(arr, np.ones(w) / w, mode="valid"), 2)

    ma5 = ma(closes, 5); ma10 = ma(closes, 10); ma20 = ma(closes, 20); ma60 = ma(closes, 60)

    def ema(arr, span):
        out = np.empty_like(arr, dtype=float)
        out[0] = arr[0]; k = 2 / (span + 1)
        for i in range(1, len(arr)):
            out[i] = arr[i] * k + out[i - 1] * (1 - k)
        return out

    ema12 = ema(closes, 12); ema26 = ema(closes, 26)
    dif = np.round(ema12 - ema26, 2); dea = np.round(ema(dif, 9), 2)
    macd = np.round((dif - dea) * 2, 2)

    def rsi(arr, period=14):
        delta = np.diff(arr)
        up = np.where(delta > 0, delta, 0.0); down = np.where(delta < 0, -delta, 0.0)
        upma = np.convolve(up, np.ones(period) / period, mode="valid")
        downma = np.convolve(down, np.ones(period) / period, mode="valid")
        rs = upma / (downma + 1e-9); r = 100 - 100 / (1 + rs)
        out = np.full(len(arr), np.nan); out[period:] = r
        return np.round(out, 2)

    rsi14 = rsi(closes, 14)
    std = np.array([np.std(closes[i - 20:i]) for i in range(20, n + 1)])
    upper = np.round(ma20 + 2 * std, 2); lower = np.round(ma20 - 2 * std, 2)

    last = closes[-1]; first = closes[0]
    period_ret = round((last / first - 1) * 100, 2)
    max_idx = int(np.argmax(highs)); min_idx = int(np.argmax(-lows))
    max_p = highs[max_idx]; min_p = lows[min_idx]
    recent20_high = highs[-20:].max(); recent20_low = lows[-20:].min(); recent20_amp = round((recent20_high / recent20_low - 1) * 100, 2)
    avg_vol = vols.mean(); recent_vol = np.mean(vols[-5:]); vol_ratio = round(recent_vol / avg_vol, 2)
    retrace = round((last / max_p - 1) * 100, 2)

    bull = bool(ma5[-1] > ma10[-1] > ma20[-1] > ma60[-1])
    golden = bool(dif[-1] > dea[-1])
    prev_close = float(closes[-2]) if n >= 2 else float(closes[-1])

    # 日内分时数据（最新交易日）
    intraday_mod.fetch_intraday(intraday_mod.secid_of(code), code, workspace)
    idata = intraday_mod.load_intraday(workspace, code)

    metrics = dict(
        dates=dates, n=n, last=last, first=first, period_ret=period_ret,
        max_p=max_p, min_p=min_p, max_dt=dates[max_idx], min_dt=dates[min_idx],
        recent20_high=recent20_high, recent20_low=recent20_low, recent20_amp=recent20_amp,
        ma5=ma5[-1], ma10=ma10[-1], ma20=ma20[-1], ma60=ma60[-1], bull=bull,
        dif=dif[-1], dea=dea[-1], macd=macd[-1], golden=golden,
        rsi14=rsi14[-1], upper=upper[-1], mid=ma20[-1], lower=lower[-1],
        vol_ratio=vol_ratio, retrace=retrace, prev_close=prev_close,
        intraday=idata,
    )
    # 操作建议概率（模型测算，非投资建议）
    metrics["signal"] = signal_mod.compute(metrics)
    return metrics


def add_page_number(section):
    """为文档节添加居中的页码域（底部）。"""
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1); run._r.append(instrText); run._r.append(fldChar2)


def set_cjk_font(run, font="宋体", size=None):
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts'); rpr.append(rfonts)
    rfonts.set(qn('w:eastAsia'), font)
    if size is not None:
        run.font.size = Pt(size)


def build_docx(workspace, code, name, metrics, desktop):
    doc = Document()
    # 基础字体
    style = doc.styles['Normal']
    style.font.name = '宋体'
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 标题
    h = doc.add_heading(level=0)
    run = h.add_run(f"{name}（{code}）日K线AI技术分析报告")
    set_cjk_font(run, "黑体", 18)
    run.font.color.rgb = DARK

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sr = sub.add_run(f"数据区间：{metrics['dates'][0]} ~ {metrics['dates'][-1]}（共{metrics['n']}个交易日，前复权）｜ 数据来源：东方财富")
    set_cjk_font(sr, "宋体", 10)
    sr.font.color.rgb = GREY

    # ===== 1. 核心指标速览表 =====
    doc.add_heading("一、核心指标速览", level=1)
    cards = [
        ("最新收盘", f"{metrics['last']:.2f}"),
        ("区间涨跌幅", f"{metrics['period_ret']:+.2f}%"),
        ("较高点回撤", f"{metrics['retrace']:.2f}%"),
        ("区间最高", f"{metrics['max_p']:.2f} ({metrics['max_dt']})"),
        ("区间最低", f"{metrics['min_p']:.2f} ({metrics['min_dt']})"),
        ("近20日振幅", f"{metrics['recent20_amp']:.2f}%"),
        ("量比(近5日/均量)", f"{metrics['vol_ratio']}"),
        ("最新RSI(14)", f"{metrics['rsi14']:.2f}"),
    ]
    t = doc.add_table(rows=2, cols=4)
    t.style = 'Light Grid Accent 1'
    for i, (k, v) in enumerate(cards):
        r, c = divmod(i, 4)
        cell_k = t.cell(r, c).paragraphs[0]
        rk = cell_k.add_run(k); set_cjk_font(rk, "宋体", 9); rk.font.color.rgb = GREY
        cell_v = t.cell(r, c).add_paragraph()
        rv = cell_v.add_run(v); set_cjk_font(rv, "宋体", 11); rv.bold = True
        # 涨跌着色
        if k == "区间涨跌幅":
            rv.font.color.rgb = UP_RED if metrics['period_ret'] >= 0 else DOWN_GREEN
        if k == "较高点回撤":
            rv.font.color.rgb = DOWN_GREEN

    # 段落辅助函数（提前定义，供后续各章节复用）
    def para(text, bold=False, color=None, size=11):
        p = doc.add_paragraph()
        r = p.add_run(text); set_cjk_font(r, "宋体", size); r.bold = bold
        if color is not None:
            r.font.color.rgb = color
        return p

    # ===== 1.5 操作建议概率（模型测算，非投资建议） =====
    sig = metrics.get("signal", {})
    if sig:
        doc.add_heading("一·五、AI技术分析（模型测算）", level=1)
        dom_action, dom_color = signal_mod.dominant(
            sig["prob_buy"], sig["prob_sell"], sig["prob_hold"])

        # 三色圆点 + 百分比概览（一行）
        p_dots = doc.add_paragraph()
        p_dots.alignment = WD_ALIGN_PARAGRAPH.LEFT
        # 买入 红点
        r_b = p_dots.add_run("● ")
        r_b.font.size = Pt(14); r_b.font.color.rgb = RGBColor(0xE2, 0x3B, 0x3B)
        r_bt = p_dots.add_run(f"可能涨概率 {sig['prob_buy']:.1f}%    ")
        set_cjk_font(r_bt, "宋体", 11); r_bt.bold = True
        # 持有 黄点
        r_h = p_dots.add_run("● ")
        r_h.font.size = Pt(14); r_h.font.color.rgb = RGBColor(0xE6, 0xA8, 0x00)
        r_ht = p_dots.add_run(f"可能平概率 {sig['prob_hold']:.1f}%    ")
        set_cjk_font(r_ht, "宋体", 11); r_ht.bold = True
        # 卖出 绿点
        r_s = p_dots.add_run("● ")
        r_s.font.size = Pt(14); r_s.font.color.rgb = RGBColor(0x1A, 0xA3, 0x4A)
        r_st = p_dots.add_run(f"可能跌概率 {sig['prob_sell']:.1f}%")
        set_cjk_font(r_st, "宋体", 11); r_st.bold = True

        # 主导判断说明（涨/平/跌语义映射）
        _ACTION_CN = {"买入": "上涨", "持有": "持平", "卖出": "下跌"}
        dom_cn = _ACTION_CN.get(dom_action, dom_action)
        para(f"综合技术评分 T = {sig['T']:+.4f}（∈[-1,1]，越正越偏多）。基于当前技术面，"
             f"模型测算「{dom_cn}」概率相对占优（{max(sig['prob_buy'], sig['prob_sell'], sig['prob_hold']):.1f}%），"
             f"但三者概率仅反映历史技术指标的量化倾向，并非确定性结论。", color=DARK)

        # 因子明细表（可复核）
        para("因子加权明细（score∈[-1,1]，正=偏多；contrib=权重×score）：", size=10, color=GREY)
        ft = doc.add_table(rows=1, cols=4)
        ft.style = 'Light Grid Accent 1'
        hdr = ft.rows[0].cells
        for ci, htext in enumerate(["技术因子", "权重", "因子分", "贡献"]):
            hr = hdr[ci].paragraphs[0].add_run(htext)
            set_cjk_font(hr, "宋体", 9); hr.bold = True; hr.font.color.rgb = GREY
        for (fname, fw, fscore, fcontrib) in sig["factors"]:
            row = ft.add_row().cells
            c0 = row[0].paragraphs[0].add_run(fname); set_cjk_font(c0, "宋体", 9)
            c1 = row[1].paragraphs[0].add_run(f"{fw:.2f}"); set_cjk_font(c1, "宋体", 9)
            c2 = row[2].paragraphs[0].add_run(f"{fscore:+.2f}"); set_cjk_font(c2, "宋体", 9)
            c3 = row[3].paragraphs[0].add_run(f"{fcontrib:+.3f}"); set_cjk_font(c3, "宋体", 9)
        para("⚠ 本模块为历史技术指标的数学映射示意，所有权重与映射均为人为设定，"
             "结果不构成任何可能涨/可能平/可能跌的操作建议，仅供技术面强弱量化参考。", size=10, color=GREY)

    # ===== 2. 技术形态分析（8节） =====
    doc.add_heading("二、技术形态分析", level=1)

    # 趋势
    para("1. 趋势与区间表现", bold=True)
    para(f"样本区间自 {metrics['dates'][0]} 的 {metrics['first']:.2f} 至 {metrics['dates'][-1]} 的 {metrics['last']:.2f}，"
         f"区间涨跌幅 {metrics['period_ret']:+.2f}%；区间最高 {metrics['max_p']:.2f}（{metrics['max_dt']}），"
         f"最低 {metrics['min_p']:.2f}（{metrics['min_dt']}），较高点回撤 {metrics['retrace']:.2f}%。")

    # 均线
    para("2. 均线排列", bold=True)
    arrange = "多头排列（MA5>MA10>MA20>MA60）" if metrics['bull'] else "空头/纠缠排列（非标准多头）"
    para(f"最新 MA5={metrics['ma5']:.2f} / MA10={metrics['ma10']:.2f} / MA20={metrics['ma20']:.2f} / MA60={metrics['ma60']:.2f}，"
         f"当前为{arrange}。MA60 构成中期趋势参考。")

    # MACD
    para("3. MACD(12,26,9)", bold=True)
    macd_state = "金叉（DIF 在 DEA 上方），动能偏多" if metrics['golden'] else "死叉（DIF 在 DEA 下方），动能偏空"
    bar_color = "红柱" if metrics['macd'] >= 0 else "绿柱"
    para(f"最新 DIF={metrics['dif']:.2f}，DEA={metrics['dea']:.2f}，MACD柱={metrics['macd']:.2f}（{bar_color}），"
         f"当前为{macd_state}。")

    # 布林
    para("4. 布林带(20,2)", bold=True)
    if metrics['last'] >= metrics['mid']:
        boll_pos = "价格位于中轨上方，偏强"
    elif metrics['last'] >= metrics['lower']:
        boll_pos = "价格已跌破中轨、向下轨靠近，偏弱"
    else:
        boll_pos = "价格跌破下轨，处于超卖区"
    para(f"上轨 {metrics['upper']:.2f} / 中轨 {metrics['mid']:.2f} / 下轨 {metrics['lower']:.2f}；{boll_pos}。")

    # RSI
    para("5. RSI(14)强弱", bold=True)
    if metrics['rsi14'] >= 70:
        rsi_state = "进入超买区，注意回调"
    elif metrics['rsi14'] <= 30:
        rsi_state = "进入超卖区，存在反弹可能"
    else:
        rsi_state = "中性区间，多空均衡"
    para(f"最新 RSI(14)={metrics['rsi14']:.2f}，{rsi_state}。")

    # 量能
    para("6. 量能", bold=True)
    para(f"量比（近5日均量/全样本均量）={metrics['vol_ratio']}，"
         f"{'量能温和放大' if metrics['vol_ratio']>1 else '量能相对萎缩'}。")

    # 日内分时
    idata = metrics.get("intraday")
    para("6.5 日内分时（最新交易日）", bold=True)
    if idata:
        intraday_state = "现价位于均价上方，盘中偏强" if idata["last_price"] >= idata["pre_close"] else "现价位于均价下方，盘中偏弱"
        para(f"最新交易日 {idata['trade_date']}：开盘 {idata['prices'][0]:.2f}，收盘 {idata['last_price']:.2f}，"
             f"日内最高 {idata['day_high']:.2f} / 最低 {idata['day_low']:.2f}，较昨收 {idata['chg_pct']:+.2f}%；{intraday_state}。")
    else:
        para("当日分时数据暂未获取（可能为非交易日或接口无数据）。")

    # 关键支撑阻力
    para("7. 关键支撑与阻力", bold=True)
    para(f"关键支撑：布林下轨 {metrics['lower']:.2f} 与前低 {metrics['min_p']:.2f} 附近；"
         f"关键阻力：MA20（{metrics['ma20']:.2f}）与 MA60（{metrics['ma60']:.2f}）重合区。")

    # 综合判断
    para("8. 综合判断", bold=True)
    trend_word = "偏多" if (metrics['bull'] and metrics['golden']) else ("偏空" if (not metrics['bull'] and not metrics['golden']) else "震荡")
    para(f"综合均线、MACD、布林与 RSI，当前技术面整体{trend_word}。"
         f"建议结合价格对关键支撑/阻力的突破情况，以及成交量配合程度，判断后续方向。")

    # ===== 3. 文字分析摘要（逐段综合结论） =====
    doc.add_heading("三、文字分析摘要（综合结论）", level=1)
    para(f"1. 趋势：样本区间先跌后急涨。区间最高 {metrics['max_p']:.2f}（{metrics['max_dt']}）后持续下行至区间最低 "
         f"{metrics['min_p']:.2f}（{metrics['min_dt']}），随后出现强劲反弹至最新收盘 {metrics['last']:.2f}，"
         f"近20日振幅高达 {metrics['recent20_amp']:.2f}%，显示短期波动剧烈、资金博弈激烈。")
    para(f"2. 均线：MA5({metrics['ma5']:.2f}) / MA10({metrics['ma10']:.2f}) / MA20({metrics['ma20']:.2f}) / "
         f"MA60({metrics['ma60']:.2f})，{'多头排列' if metrics['bull'] else '非标准多头排列'}；"
         f"最新价 {metrics['last']:.2f} 已大幅快速脱离均线系统，短期乖离率偏大。")
    para(f"3. MACD：DIF{'上穿' if metrics['golden'] else '下穿'}DEA{'形成金叉' if metrics['golden'] else '形成死叉'}，"
         f"MACD柱 {metrics['macd']:.2f}（{'红柱' if metrics['macd']>=0 else '绿柱'}），"
         f"{'短线动能偏多' if metrics['golden'] else '短线动能偏空'}。")
    boll_out = "已冲出布林上轨，属强势外轨运行，但通常预示短线超买" if metrics['last'] > metrics['upper'] else (
        "已跌破下轨，处于超卖区" if metrics['last'] < metrics['lower'] else "位于布林带内运行")
    para(f"4. 布林带：上轨 {metrics['upper']:.2f} / 中轨 {metrics['mid']:.2f} / 下轨 {metrics['lower']:.2f}；"
         f"最新价 {boll_out}。")
    rsi_word = "已进入超买区（>70），需注意回调风险" if metrics['rsi14'] >= 70 else (
        "已进入超卖区（<30），存在反弹可能" if metrics['rsi14'] <= 30 else "处于中性区间，多空均衡")
    para(f"5. RSI(14)={metrics['rsi14']:.2f}：{rsi_word}。")
    para(f"6. 量能：量比 {metrics['vol_ratio']}，{'反弹伴随明显放量，量价配合尚可，但高位放量亦需警惕分歧' if metrics['vol_ratio']>1 else '量能相对萎缩'}。")
    para(f"7. 支撑/阻力：关键支撑—布林中轨 {metrics['mid']:.2f} 及前低 {metrics['min_p']:.2f}；"
         f"关键阻力—MA60（{metrics['ma60']:.2f}）已突破，上方无明显密集成交区，下一心理位为区间前高 {metrics['max_p']:.2f}。")
    trend_word2 = "偏多" if (metrics['bull'] and metrics['golden']) else ("偏空" if (not metrics['bull'] and not metrics['golden']) else "震荡")
    para(f"综合判断：当前处于急跌后的{'强势反弹段' if metrics['golden'] and not metrics['bull'] else trend_word2}——"
         f"MACD{'金叉' if metrics['golden'] else '死叉'}、量能{'放大' if metrics['vol_ratio']>1 else '萎缩'}、"
         f"价格{'突破布林上轨' if metrics['last']>metrics['upper'] else '位于布林带内'}，"
         f"短线动能{'偏多' if metrics['golden'] else '偏空'}；"
         f"但 RSI {'已进入超买区' if metrics['rsi14']>=70 else ('已进入超卖区' if metrics['rsi14']<=30 else '中性')}、"
         f"价格对均线系统乖离{'过大' if not metrics['bull'] else '适中'}，"
         f"{'短线追高风险上升，存在回踩布林中轨（约'+format(metrics['mid'],'.2f')+'）的技术需求' if metrics['rsi14']>=70 else '需观察后续方向确认'}。"
         f"中线趋势尚未确认反转（均线仍{'非多头排列' if not metrics['bull'] else '多头排列'}，区间仍"
         f"{'为负收益' if metrics['period_ret']<0 else '为正收益'}）。", bold=False)

    # ===== 4. 风险提示 =====
    doc.add_heading("四、风险提示", level=1)
    rp = doc.add_paragraph()
    rr = rp.add_run("本分析仅基于历史价格与技术指标，不构成任何投资建议。技术分析存在滞后性，前期涨跌不预示未来表现；"
                   "超买反弹亦可能随时回落。高波动标的尤需结合基本面、行业环境与宏观因素综合判断，并严格控制仓位与止损。")
    set_cjk_font(rr, "宋体", 10)
    rr.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ===== 5. 图表 =====
    doc.add_heading("五、分析图表", level=1)
    png_main = os.path.join(workspace, f"{code}_analysis.png")
    png_rsi = os.path.join(workspace, f"{code}_rsi.png")
    png_intraday = os.path.join(workspace, f"{code}_intraday.png")
    if os.path.exists(png_main):
        doc.add_paragraph("图1：K线 + 均线 + 布林带 + 成交量 + MACD（matplotlib 静态图）")
        doc.add_picture(png_main, width=Inches(6.3))
    if os.path.exists(png_rsi):
        doc.add_paragraph("图2：RSI(14) 走势")
        doc.add_picture(png_rsi, width=Inches(6.3))
    if os.path.exists(png_intraday):
        doc.add_paragraph("图3：日内分时图（最新交易日，现价 / 均价 / 昨收基准）")
        doc.add_picture(png_intraday, width=Inches(6.3))

    # 页码
    add_page_number(doc.sections[0])

    # 保存到桌面
    out = os.path.join(desktop, f"{name}（{code}）日K线AI技术分析报告.docx")
    doc.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, help="工作区绝对路径")
    ap.add_argument("--code", required=True, help="A股代码，如 300308")
    ap.add_argument("--name", required=True, help="股票名称，如 中际旭创")
    ap.add_argument("--desktop", default=os.path.expanduser("~/Desktop"), help="桌面绝对路径，默认 ~/Desktop")
    args = ap.parse_args()

    metrics = load_metrics(args.workspace, args.code)
    out = build_docx(args.workspace, args.code, args.name, metrics, args.desktop)
    print("DOCX报告已生成:", out)


if __name__ == "__main__":
    main()
