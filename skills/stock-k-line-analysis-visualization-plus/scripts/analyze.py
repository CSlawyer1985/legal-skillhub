import json
import os
import sys
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday as intraday_mod

parser = argparse.ArgumentParser()
parser.add_argument("--workspace", default=os.getcwd(), help="工作区绝对路径")
parser.add_argument("--code", default="", help="A股代码，如 300308")
parser.add_argument("--name", default="", help="股票名称")
args, _ = parser.parse_known_args()
WS = args.workspace
CODE = args.code
NAME = args.name if args.name else CODE

with open(os.path.join(WS, f"{CODE}_kline.json"), encoding="utf-8") as f:
    data = json.load(f)

klines = data["data"]["klines"]
rows = []
for k in klines:
    p = k.split(",")
    dt = datetime.strptime(p[0], "%Y-%m-%d")
    o, c, h, l = float(p[1]), float(p[2]), float(p[3]), float(p[4])
    vol = float(p[5])
    amount = float(p[6])
    chg = float(p[8])  # 涨跌幅 %
    rows.append((dt, o, c, h, l, vol, amount, chg))

dates = np.array([r[0] for r in rows])
opens = np.array([r[1] for r in rows])
closes = np.array([r[2] for r in rows])
highs = np.array([r[3] for r in rows])
lows = np.array([r[4] for r in rows])
vols = np.array([r[5] for r in rows])
chgs = np.array([r[7] for r in rows])

n = len(closes)

def ma(arr, w):
    return np.convolve(arr, np.ones(w)/w, mode="valid")

# MA
ma5 = ma(closes, 5)
ma10 = ma(closes, 10)
ma20 = ma(closes, 20)
ma60 = ma(closes, 60)

# MACD
def ema(arr, span):
    out = np.empty_like(arr, dtype=float)
    out[0] = arr[0]
    k = 2/(span+1)
    for i in range(1, len(arr)):
        out[i] = arr[i]*k + out[i-1]*(1-k)
    return out

ema12 = ema(closes, 12)
ema26 = ema(closes, 26)
dif = ema12 - ema26
dea = ema(dif, 9)
macd = (dif - dea) * 2

# RSI14
def rsi(arr, period=14):
    delta = np.diff(arr)
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    up_ma = np.convolve(up, np.ones(period)/period, mode="valid")
    down_ma = np.convolve(down, np.ones(period)/period, mode="valid")
    rs = up_ma / (down_ma + 1e-9)
    r = 100 - 100/(1+rs)
    out = np.full(len(arr), np.nan)
    out[period:] = r
    return out

rsi14 = rsi(closes, 14)

# Bollinger Bands (20,2)
mid = ma20
std = np.array([np.std(closes[i-20:i]) for i in range(20, n+1)])
upper = mid + 2*std
lower = mid - 2*std

# 统计
last = closes[-1]
first = closes[0]
period_ret = (last/first - 1)*100
max_idx = np.argmax(highs)
min_idx = np.argmax(-lows)
max_p = highs[max_idx]; min_p = lows[min_idx]
# 近期振幅
recent20_high = highs[-20:].max(); recent20_low = lows[-20:].min(); recent20_amp = (recent20_high/recent20_low-1)*100
# 量能
avg_vol = vols.mean(); recent_vol = vols[-5:].mean(); vol_ratio = recent_vol/avg_vol

print(f"=== {NAME}({CODE}) 技术指标统计 ===")
print(f"样本区间: {dates[0].date()} ~ {dates[-1].date()}  共{n}个交易日")
print(f"最新收盘: {last:.2f}  区间首日收盘: {first:.2f}")
print(f"区间涨跌幅: {period_ret:+.2f}%")
print(f"区间最高: {max_p:.2f} ({dates[max_idx].date()})  区间最低: {min_p:.2f} ({dates[min_idx].date()})")
print(f"近20日最高: {recent20_high:.2f}  最低: {recent20_low:.2f}  振幅: {recent20_amp:.2f}%")
print(f"最新MA5/10/20/60: {ma5[-1]:.2f}/{ma10[-1]:.2f}/{ma20[-1]:.2f}/{ma60[-1]:.2f}")
print(f"MA多头排列(5>10>20>60)? {ma5[-1]>ma10[-1]>ma20[-1]>ma60[-1]}")
print(f"最新MACD DIF/DEA/柱: {dif[-1]:.2f}/{dea[-1]:.2f}/{macd[-1]:.2f}  金叉? {dif[-1]>dea[-1]}")
print(f"最新RSI14: {rsi14[-1]:.2f}")
print(f"布林上/中/下轨: {upper[-1]:.2f}/{mid[-1]:.2f}/{lower[-1]:.2f}")
print(f"量比(近5日/全样本均量): {vol_ratio:.2f}")

# ===== 绘图 =====
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 红涨绿跌（中国习惯）
fig = plt.figure(figsize=(15, 12))
# K线 + MA
ax1 = plt.subplot2grid((4,1),(0,0), rowspan=2)
for i in range(n):
    color = "red" if closes[i] >= opens[i] else "green"
    ax1.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, lw=0.6)
    ax1.plot([dates[i], dates[i]], [opens[i], closes[i]], color=color, lw=3.0)
# MA lines
ax1.plot(dates[4:], ma5, color="#FF8C00", lw=1.0, label="MA5")
ax1.plot(dates[9:], ma10, color="#1E90FF", lw=1.0, label="MA10")
ax1.plot(dates[19:], ma20, color="#9370DB", lw=1.0, label="MA20")
ax1.plot(dates[59:], ma60, color="#2F4F4F", lw=1.0, label="MA60")
ax1.plot(dates[19:], upper, color="gray", lw=0.6, ls="--")
ax1.plot(dates[19:], lower, color="gray", lw=0.6, ls="--")
ax1.set_title(f"{NAME}({CODE}) 日K线 + 均线 + 布林带", fontsize=14, fontweight="bold")
ax1.legend(loc="upper left", fontsize=8)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax1.grid(True, alpha=0.3)

# 成交量
ax2 = plt.subplot2grid((4,1),(2,0), rowspan=1)
for i in range(n):
    color = "red" if closes[i] >= opens[i] else "green"
    ax2.bar(dates[i], vols[i]/1e4, color=color, width=0.8)
ax2.set_title("成交量(万手)", fontsize=11)
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax2.grid(True, alpha=0.3)

# MACD
ax3 = plt.subplot2grid((4,1),(3,0), rowspan=1)
ax3.plot(dates, dif, color="red", lw=1.0, label="DIF")
ax3.plot(dates, dea, color="blue", lw=1.0, label="DEA")
ax3.bar(dates, macd, color=np.where(macd>=0, "red", "green"), width=0.8)
ax3.axhline(0, color="black", lw=0.5)
ax3.set_title("MACD(12,26,9)", fontsize=11)
ax3.legend(loc="upper left", fontsize=8)
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax3.grid(True, alpha=0.3)

plt.tight_layout()
out = os.path.join(WS, f"{CODE}_analysis.png")
plt.savefig(out, dpi=130, bbox_inches="tight")
print("图表已保存:", out)

# RSI单独图也画一张合并进主图上方？这里额外存RSI
fig2, axr = plt.subplots(figsize=(15,3))
axr.plot(dates, rsi14, color="purple", lw=1.2)
axr.axhline(70, color="red", ls="--", lw=0.8)
axr.axhline(30, color="green", ls="--", lw=0.8)
axr.set_title("RSI(14)", fontsize=11)
axr.set_ylim(0,100)
axr.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
axr.grid(True, alpha=0.3)
rsi_out = os.path.join(WS, f"{CODE}_rsi.png")
plt.savefig(rsi_out, dpi=130, bbox_inches="tight")
print("RSI图已保存:", rsi_out)

# ===== 日内分时图 =====
intraday_mod.fetch_intraday(intraday_mod.secid_of(CODE), CODE, WS)
idata = intraday_mod.load_intraday(WS, CODE)
if idata:
    ix = np.arange(len(idata["times"]))
    pre = idata["pre_close"]
    prices = np.array(idata["prices"])
    avgs = np.array(idata["avg_prices"])
    up = idata["last_price"] >= pre
    line_color = "#e23b3b" if up else "#1aa34a"
    fig3, (axi, axv) = plt.subplots(2, 1, figsize=(15, 6), gridspec_kw={"height_ratios": [3, 1]})
    # 价格线 + 均价线 + 昨收基准线
    axi.plot(ix, prices, color=line_color, lw=1.2, label="现价")
    axi.plot(ix, avgs, color="#1E90FF", lw=1.0, label="均价")
    axi.axhline(pre, color="gray", lw=0.8, ls="--", label=f"昨收 {pre:.2f}")
    # 填充：涨红跌绿
    axi.fill_between(ix, pre, prices, where=(prices >= pre), color="#e23b3b", alpha=0.15)
    axi.fill_between(ix, pre, prices, where=(prices < pre), color="#1aa34a", alpha=0.15)
    axi.set_title(f"{NAME}({CODE}) 日内分时图  {idata['trade_date']}  收 {idata['last_price']:.2f} ({idata['chg_pct']:+.2f}%)", fontsize=13, fontweight="bold")
    # x 轴仅显示关键时点
    tick_pos = [0, 60, 120, 180, len(ix)-1]
    tick_pos = [p for p in tick_pos if 0 <= p < len(ix)]
    axi.set_xticks(tick_pos)
    axi.set_xticklabels([idata["times"][p][11:] for p in tick_pos], fontsize=9)
    axi.legend(loc="upper left", fontsize=8)
    axi.grid(True, alpha=0.3)
    # 成交量副图
    vols = np.array(idata["vols"]) / 1e4
    bar_colors = [line_color if prices[i] >= avgs[i] else "#1aa34a" for i in range(len(prices))]
    axv.bar(ix, vols, color=bar_colors, width=1.0)
    axv.set_xticks(tick_pos)
    axv.set_xticklabels([idata["times"][p][11:] for p in tick_pos], fontsize=9)
    axv.set_title("分时成交量(万手)", fontsize=10)
    axv.grid(True, alpha=0.3)
    plt.tight_layout()
    intraday_out = os.path.join(WS, f"{CODE}_intraday.png")
    plt.savefig(intraday_out, dpi=130, bbox_inches="tight")
    print("分时图已保存:", intraday_out)
else:
    print("分时数据缺失，跳过分时图生成")
