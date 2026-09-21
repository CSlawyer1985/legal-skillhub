"""操作建议概率（买入/持有/卖出）技术评分模块。

模型说明（透明、可复核）：
  本模块基于已有技术指标，构造 7 个技术因子，每个因子给出一个
  归一化倾向分 score_i ∈ [-1, 1]（正=偏多/买入，负=偏空/卖出），
  按显式权重 W_i 加权求和得到综合技术分 T ∈ [-1, 1]：

      T = Σ (W_i * score_i)

  再将 T 映射为三类概率（softmax 形式，三者之和=100%）：

      buy_raw  = exp(k * T)
      sell_raw = exp(-k * T)
      hold_raw = 1.0
      p_buy / p_sell / p_hold = 归一化 * 100%

  其中 k 为分化系数（默认 4.0）：T 越偏正，买入概率越高；越偏负，
  卖出概率越高；T 接近 0 时持有概率占主导。

重要声明：
  **本模型仅为历史技术指标的数学映射示意，不构成任何投资建议。**
  权重与映射为人为设定，结果不预示未来，仅作技术面强弱的量化参考。
"""
import math

# ===== 因子权重（显式、可调、合计=1.0） =====
W_MA = 0.24        # 均线排列（多头/空头）
W_MACD = 0.24      # MACD 金叉/死叉
W_RSI = 0.14       # RSI 超买/超卖
W_BOLL = 0.14      # 布林带位置（贴近下轨偏多 / 上轨偏空）
W_POS = 0.10       # 当前价在样本区间的百分位（低位偏多）
W_VOL = 0.06       # 量能配合（放量上涨偏多 / 下跌放量偏空）
W_TREND = 0.08     # 中期趋势方向（区间涨跌幅正负）

K = 4.0  # 分化系数

# 圆点颜色（与红涨绿跌一致：买入红、持有黄、卖出绿）
DOT_BUY = "#E23B3B"    # 红
DOT_HOLD = "#E6A800"   # 黄（深黄，保证白底可见）
DOT_SELL = "#1AA34A"   # 绿


def _clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def compute(metrics):
    """根据 metrics 计算买入/持有/卖出概率。

    metrics 需包含：
      bull (bool), golden (bool), rsi14 (float),
      last, lower, mid, upper (布林), min_p, max_p,
      vol_ratio, period_ret, prev_close (前一日收盘)
    返回 dict：prob_buy, prob_sell, prob_hold, T, factors(list of (name, weight, score, contrib))
    """
    factors = []

    # 1. 均线排列
    s_ma = 1.0 if metrics["bull"] else (-1.0 if not metrics["bull"] else 0.0)
    # bull 为 True 即多头排列；否则视为空头/纠缠，给 -1
    s_ma = 1.0 if metrics["bull"] else -1.0
    factors.append(("均线排列(MA5/10/20/60)", W_MA, s_ma))

    # 2. MACD
    s_macd = 1.0 if metrics["golden"] else -1.0
    factors.append(("MACD金叉/死叉", W_MACD, s_macd))

    # 3. RSI（<50 偏多反弹，>50 偏空；超卖/超买强化）
    rsi = metrics["rsi14"]
    s_rsi = _clamp((50.0 - rsi) / 20.0)  # rsi=30→+1, 50→0, 70→-1
    factors.append(("RSI(14)强弱", W_RSI, s_rsi))

    # 4. 布林位置（pos=0 下轨, 1 上轨；越低越偏多）
    mid = metrics["mid"]; lower = metrics["lower"]; upper = metrics["upper"]
    span = (upper - lower) or 1.0
    pos = _clamp((metrics["last"] - lower) / span, 0.0, 1.0)
    s_boll = _clamp((0.5 - pos) * 2.0)  # pos=0→+1, 0.5→0, 1→-1
    factors.append(("布林带位置", W_BOLL, s_boll))

    # 5. 区间百分位（低位偏多）
    min_p = metrics["min_p"]; max_p = metrics["max_p"]
    rng = (max_p - min_p) or 1.0
    pct = _clamp((metrics["last"] - min_p) / rng, 0.0, 1.0)
    s_pos = _clamp((0.5 - pct) * 2.0)
    factors.append(("区间百分位(低→偏多)", W_POS, s_pos))

    # 6. 量能配合（当日涨跌 × 量比）
    prev = metrics.get("prev_close") or metrics["last"]
    day_up = metrics["last"] >= prev
    vr = metrics["vol_ratio"]
    if day_up and vr > 1.0:
        s_vol = 1.0
    elif (not day_up) and vr > 1.0:
        s_vol = -1.0
    else:
        s_vol = 0.0
    factors.append(("量能配合(量比×涨跌)", W_VOL, s_vol))

    # 7. 中期趋势方向（区间涨跌幅）
    s_trend = 1.0 if metrics["period_ret"] >= 0 else -1.0
    factors.append(("中期趋势(区间涨跌)", W_TREND, s_trend))

    # 加权求和
    T = sum(w * s for (_n, w, s) in factors)
    T = _clamp(T)

    # softmax 映射
    buy_raw = math.exp(K * T)
    sell_raw = math.exp(-K * T)
    hold_raw = 1.0
    total = buy_raw + sell_raw + hold_raw
    p_buy = round(buy_raw / total * 100, 1)
    p_sell = round(sell_raw / total * 100, 1)
    p_hold = round(hold_raw / total * 100, 1)
    # 修正四舍五入误差，保证和为100
    diff = round(100.0 - (p_buy + p_sell + p_hold), 1)
    # 把差额补到最大项
    mx = max(p_buy, p_sell, p_hold)
    if mx == p_buy: p_buy += diff
    elif mx == p_sell: p_sell += diff
    else: p_hold += diff

    factor_detail = [(n, w, round(s, 3), round(w * s, 3)) for (n, w, s) in factors]

    return dict(
        prob_buy=p_buy, prob_sell=p_sell, prob_hold=p_hold,
        T=round(T, 4), factors=factor_detail,
    )


def dominant(prob_buy, prob_sell, prob_hold):
    """返回 (主导动作, 颜色) 用于概览圆点。"""
    mx = max(prob_buy, prob_sell, prob_hold)
    if mx == prob_buy:
        return ("买入", DOT_BUY)
    if mx == prob_sell:
        return ("卖出", DOT_SELL)
    return ("持有", DOT_HOLD)
