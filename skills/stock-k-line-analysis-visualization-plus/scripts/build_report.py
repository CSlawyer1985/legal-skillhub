import json
import base64
import os
import sys
import argparse
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intraday as intraday_mod
import signal_score as signal_mod

# 工作区与标的通过参数传入，避免硬编码路径
parser = argparse.ArgumentParser()
parser.add_argument("--workspace", default=os.getcwd(), help="工作区绝对路径")
parser.add_argument("--code", default="", help="A股代码，如 300308")
parser.add_argument("--name", default="", help="股票名称，如 中际旭创")
args, _ = parser.parse_known_args()
WS = args.workspace
CODE = args.code
NAME = args.name

kline_path = os.path.join(WS, f"{CODE}_kline.json")
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
kdata = [[r[1], r[2], r[4], r[3]] for r in rows]  # open, close, low, high for ECharts
vols = np.array([r[5] for r in rows])
closes = np.array([r[2] for r in rows])
lows = np.array([r[4] for r in rows])
highs = np.array([r[3] for r in rows])
n = len(closes)

def ma(arr, w):
    return np.round(np.convolve(arr, np.ones(w)/w, mode="valid"), 2)

ma5 = ma(closes, 5); ma10 = ma(closes, 10); ma20 = ma(closes, 20); ma60 = ma(closes, 60)
dates5 = dates[4:]; dates10 = dates[9:]; dates20 = dates[19:]; dates60 = dates[59:]

def ema(arr, span):
    out = np.empty_like(arr, dtype=float)
    out[0] = arr[0]; k = 2/(span+1)
    for i in range(1, len(arr)):
        out[i] = arr[i]*k + out[i-1]*(1-k)
    return out
ema12 = ema(closes,12); ema26 = ema(closes,26)
dif = np.round(ema12-ema26,2); dea = np.round(ema(dif,9),2)
macd = np.round((dif-dea)*2,2)

def rsi(arr, period=14):
    delta = np.diff(arr)
    up = np.where(delta>0, delta, 0.0); down = np.where(delta<0, -delta, 0.0)
    upma = np.convolve(up, np.ones(period)/period, mode="valid")
    downma = np.convolve(down, np.ones(period)/period, mode="valid")
    rs = upma/(downma+1e-9); r = 100-100/(1+rs)
    out = np.full(len(arr), np.nan); out[period:]=r
    return np.round(out,2)
rsi14 = rsi(closes,14)

std = np.array([np.std(closes[i-20:i]) for i in range(20,n+1)])
mid = ma20
upper = np.round(mid+2*std,2); lower = np.round(mid-2*std,2)

last = closes[-1]; first = closes[0]
period_ret = round((last/first-1)*100,2)
max_idx = int(np.argmax(highs)); min_idx = int(np.argmax(-lows))
max_p = highs[max_idx]; min_p = lows[min_idx]
recent20_high = highs[-20:].max(); recent20_low = lows[-20:].min(); recent20_amp = round((recent20_high/recent20_low-1)*100,2)
avg_vol = vols.mean(); recent_vol = np.mean(vols[-5:]); vol_ratio = round(recent_vol/avg_vol,2)
retrace = round((last/max_p-1)*100,2)

# 操作建议概率所需变量（与 build_docx 保持一致）
bull = bool(ma5[-1] > ma10[-1] > ma20[-1] > ma60[-1])
golden = bool(dif[-1] > dea[-1])
prev_close = float(closes[-2]) if n >= 2 else float(closes[-1])
sig_metrics = dict(
    bull=bull, golden=golden, rsi14=float(rsi14[-1]),
    last=float(last), lower=float(lower[-1]), mid=float(mid[-1]), upper=float(upper[-1]),
    min_p=float(min_p), max_p=float(max_p), vol_ratio=vol_ratio, period_ret=period_ret,
    prev_close=prev_close,
)
signal_res = signal_mod.compute(sig_metrics)
sig_dom_action, sig_dom_color = signal_mod.dominant(
    signal_res["prob_buy"], signal_res["prob_sell"], signal_res["prob_hold"])
sig_dom_action_cn = {"买入": "上涨", "持有": "持平", "卖出": "下跌"}.get(sig_dom_action, sig_dom_action)

# 编码PNG图片为base64
def img_b64(path):
    with open(path,"rb") as f:
        return base64.b64encode(f.read()).decode()

png_main = img_b64(os.path.join(WS, f"{CODE}_analysis.png"))
png_rsi = img_b64(os.path.join(WS, f"{CODE}_rsi.png"))
png_intraday = None
intraday_times = "[]"; intraday_prices = "[]"; intraday_avg = "[]"
intraday_pre = 0; intraday_chg = 0.0; intraday_last = 0.0
intraday_high = 0.0; intraday_low = 0.0; intraday_date = "N/A"
intraday_mod.fetch_intraday(intraday_mod.secid_of(CODE), CODE, WS)
idata = intraday_mod.load_intraday(WS, CODE)
if idata:
    png_intraday = img_b64(os.path.join(WS, f"{CODE}_intraday.png"))
    intraday_times = json.dumps(idata["times"])
    intraday_prices = json.dumps([round(x, 2) for x in idata["prices"]])
    intraday_avg = json.dumps([round(x, 2) for x in idata["avg_prices"]])
    intraday_pre = round(idata["pre_close"], 2)
    intraday_chg = round(idata["chg_pct"], 2)
    intraday_last = round(idata["last_price"], 2)
    intraday_high = round(idata["day_high"], 2)
    intraday_low = round(idata["day_low"], 2)
    intraday_date = idata["trade_date"]

# 用于 HTML：分时图 JS 块与 resize 调用（无数据时置空）
if idata:
    ichart_resize = "ichart.resize();"
    intraday_script = f"""
var ichart = echarts.init(document.getElementById('intraday'));
var itimes = {intraday_times};
var iprices = {intraday_prices};
var iavg = {intraday_avg};
var ipre = {intraday_pre};
ichart.setOption({{
  tooltip:{{trigger:'axis'}},
  legend:{{data:['现价','均价'], top:0}},
  grid:{{left:60,right:20,top:35,bottom:30}},
  xAxis:{{type:'category', data:itimes, axisLabel:{{fontSize:10, formatter:function(v){{return v.slice(11);}}}}}},
  yAxis:{{scale:true, splitArea:{{show:true}}, axisLabel:{{formatter:'{{value}}'}}}},
  series:[
    {{name:'现价', type:'line', data:iprices, symbol:'none', lineStyle:{{color: iprices[iprices.length-1]>=ipre?'#e23b3b':'#1aa34a', width:1.2}},
      markLine:{{silent:true, symbol:'none', lineStyle:{{color:'#999', type:'dashed'}}, data:[{{yAxis:ipre, name:'昨收'}}]}}}},
    {{name:'均价', type:'line', data:iavg, symbol:'none', lineStyle:{{color:'#1E90FF', width:1}}}}
  ]
}});
"""
else:
    ichart_resize = ""
    intraday_script = ""

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{NAME}({CODE}) K线技术分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
  body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; margin:0; background:#f5f6fa; color:#222; }}
  .header {{ background:#1a2238; color:#fff; padding:18px 28px; }}
  .header h1 {{ margin:0; font-size:22px; }}
  .header p {{ margin:6px 0 0; font-size:13px; color:#aab; }}
  .cards {{ display:flex; flex-wrap:wrap; gap:14px; padding:20px 28px; }}
  .card {{ background:#fff; border-radius:10px; padding:16px 20px; flex:1; min-width:150px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .card .label {{ font-size:12px; color:#888; }}
  .card .value {{ font-size:22px; font-weight:700; margin-top:6px; }}
  .red {{ color:#e23b3b; }} .green {{ color:#1aa34a; }}
  .chart-box {{ background:#fff; margin:0 28px 22px; border-radius:10px; padding:10px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .section-title {{ font-size:16px; font-weight:700; padding:14px 28px 0; color:#1a2238; }}
  .imgs {{ display:flex; flex-wrap:wrap; gap:16px; padding:16px 28px; }}
  .imgs img {{ max-width:100%; border:1px solid #eee; border-radius:8px; }}
  .note {{ padding:10px 28px 40px; font-size:12px; color:#999; line-height:1.7; }}
</style>
</head>
<body>
<div class="header">
  <h1>{NAME} ({CODE}) 日K线技术分析</h1>
  <p>数据区间：{dates[0]} ~ {dates[-1]}（共{n}个交易日，前复权）｜ 数据来源：东方财富</p>
</div>

<div class="cards">
  <div class="card"><div class="label">最新收盘</div><div class="value">{last:.2f}</div></div>
  <div class="card"><div class="label">区间涨跌幅</div><div class="value red">+{period_ret}%</div></div>
  <div class="card"><div class="label">较高点回撤</div><div class="value green">{retrace}%</div></div>
  <div class="card"><div class="label">区间最高</div><div class="value">{max_p:.2f}</div></div>
  <div class="card"><div class="label">区间最低</div><div class="value">{min_p:.2f}</div></div>
  <div class="card"><div class="label">近20日振幅</div><div class="value">{recent20_amp}%</div></div>
  <div class="card"><div class="label">量比(近5日/均量)</div><div class="value">{vol_ratio}</div></div>
  <div class="card"><div class="label">最新RSI(14)</div><div class="value">{rsi14[-1]:.2f}</div></div>
</div>

<div class="section-title">AI技术分析（模型测算 · 非投资建议）</div>
<div class="cards">
  <div class="card" style="border-left:5px solid {signal_mod.DOT_BUY};"><div class="label">● 可能涨概率</div><div class="value red">{signal_res['prob_buy']:.1f}%</div></div>
  <div class="card" style="border-left:5px solid {signal_mod.DOT_HOLD};"><div class="label">● 可能平概率</div><div class="value" style="color:{signal_mod.DOT_HOLD};">{signal_res['prob_hold']:.1f}%</div></div>
  <div class="card" style="border-left:5px solid {signal_mod.DOT_SELL};"><div class="label">● 可能跌概率</div><div class="value green">{signal_res['prob_sell']:.1f}%</div></div>
  <div class="card"><div class="label">综合技术评分 T</div><div class="value">{signal_res['T']:+.4f}</div></div>
</div>
<p class="note">综合技术评分 T={signal_res['T']:+.4f}（∈[-1,1]）。当前模型测算「{sig_dom_action_cn}」概率相对占优（{max(signal_res['prob_buy'], signal_res['prob_sell'], signal_res['prob_hold']):.1f}%）。<b>本模块为历史技术指标的数学映射示意，不构成任何可能涨/可能平/可能跌的操作建议。</b>因子明细：{', '.join(f"{fn} {fc:+.2f}" for (fn, fw, fs, fc) in signal_res['factors'])}。</p>

<div class="section-title">K线 · 均线 · 布林带</div>
<div class="chart-box"><div id="kline" style="height:460px;"></div></div>

<div class="section-title">成交量</div>
<div class="chart-box"><div id="vol" style="height:240px;"></div></div>

<div class="section-title">MACD (12,26,9)</div>
<div class="chart-box"><div id="macd" style="height:260px;"></div></div>

<div class="section-title">RSI (14)</div>
<div class="chart-box"><div id="rsi" style="height:240px;"></div></div>

{('<div class="section-title">日内分时图（'+intraday_date+'）</div><div class="chart-box"><div id="intraday" style="height:360px;"></div></div>') if idata else '<div class="section-title">日内分时图</div><div class="chart-box"><p style="color:#999;padding:20px;">当日分时数据暂未获取（可能为非交易日或接口连接失败）。</p></div>'}

<div class="section-title">静态分析图（matplotlib）</div>
<div class="imgs">
  <img src="data:image/png;base64,{png_main}" alt="K线主图">
  <img src="data:image/png;base64,{png_rsi}" alt="RSI图">
  {f'<img src="data:image/png;base64,{png_intraday}" alt="分时图">' if png_intraday else ''}
</div>

<div class="note">
  分析结论摘要：<br>
  1. 趋势：样本区间自{dates[0]}的{first:.2f}至{dates[-1]}的{last:.2f}，区间涨跌幅{period_ret:+.2f}%；区间最高{max_p:.2f}（{dates[max_idx]}），最低{min_p:.2f}（{dates[min_idx]}），较高点回撤{retrace:.2f}%。<br>
  2. 均线：MA5({ma5[-1]}) / MA10({ma10[-1]}) / MA20({ma20[-1]}) / MA60({ma60[-1]})，当前为{"多头排列（MA5>MA10>MA20>MA60）" if ma5[-1]>ma10[-1]>ma20[-1]>ma60[-1] else "非标准多头排列"}，MA60 构成中期参考。<br>
  3. MACD：DIF({dif[-1]}){"在DEA上方" if dif[-1]>dea[-1] else "在DEA下方"}，{"红柱" if macd[-1]>=0 else "绿柱"}({macd[-1]}){"扩大" if macd[-1]<macd[-2] else "收窄"}，动能{"偏多" if dif[-1]>dea[-1] else "偏空"}。<br>
  4. 布林带：上轨{upper[-1]} / 中轨{mid[-1]} / 下轨{lower[-1]}，价格{"位于中轨上方偏强" if last>=mid[-1] else ("已跌破中轨、向下轨靠近偏弱" if last>=lower[-1] else "跌破下轨、处于超卖区")}。<br>
  5. RSI(14)={rsi14[-1]}，{"超买" if rsi14[-1]>=70 else ("超卖" if rsi14[-1]<=30 else "中性偏弱" if rsi14[-1]<50 else "中性偏强")}，{"注意回调" if rsi14[-1]>=70 else ("存在反弹可能" if rsi14[-1]<=30 else "多空均衡")}。<br>
  6. 量能：量比（近5日均量/全样本均量）={vol_ratio}，{"量能温和放大" if vol_ratio>1 else "量能相对萎缩"}。<br>
  {"7. 日内分时（"+intraday_date+"）：开盘 "+format(idata['prices'][0],'.2f')+"，收盘 "+format(intraday_last,'.2f')+"，日内最高 "+format(intraday_high,'.2f')+" / 最低 "+format(intraday_low,'.2f')+"，较昨收 "+format(intraday_chg,'+.2f')+"%；现价"+(("位于均价上方，盘中偏强" if intraday_last>=intraday_pre else "位于均价下方，盘中偏弱"))+"。<br>" if idata else ""}
  关键支撑：布林下轨{lower[-1]} / 前低{min_p:.2f}附近；关键阻力：MA20({ma20[-1]})与MA60({ma60[-1]})重合区。<br>
  <b>风险提示：</b>本分析仅基于历史价格与技术指标，不构成投资建议。技术分析存在滞后性，前期涨跌不预示未来表现；高波动标的尤需结合基本面、行业环境与宏观因素综合判断，并注意仓位与止损控制。
</div>

<script>
var dates = {json.dumps(dates)};
var kdata = {json.dumps(kdata)};
var upColor='#e23b3b', downColor='#1aa34a';

var kchart = echarts.init(document.getElementById('kline'));
kchart.setOption({{
  tooltip:{{trigger:'axis', axisPointer:{{type:'cross'}}}},
  legend:{{data:['MA5','MA10','MA20','MA60','BOLL上','BOLL下'], top:0}},
  grid:{{left:60,right:20,top:40,bottom:30}},
  xAxis:{{type:'category', data:dates, boundaryGap:true, axisLabel:{{fontSize:10}}}},
  yAxis:{{scale:true, splitArea:{{show:true}}}},
  dataZoom:[{{type:'inside'}},{{type:'slider', bottom:0, height:18}}],
  series:[
    {{name:'K线', type:'candlestick', data:kdata, itemStyle:{{color:upColor, color0:downColor, borderColor:upColor, borderColor0:downColor}}}},
    {{name:'MA5', type:'line', data:{json.dumps([None]*(n-5)+list(ma5))}, smooth:true, symbol:'none', lineStyle:{{color:'#FF8C00',width:1}}}},
    {{name:'MA10', type:'line', data:{json.dumps([None]*(n-10)+list(ma10))}, smooth:true, symbol:'none', lineStyle:{{color:'#1E90FF',width:1}}}},
    {{name:'MA20', type:'line', data:{json.dumps([None]*(n-20)+list(ma20))}, smooth:true, symbol:'none', lineStyle:{{color:'#9370DB',width:1}}}},
    {{name:'MA60', type:'line', data:{json.dumps([None]*(n-60)+list(ma60))}, smooth:true, symbol:'none', lineStyle:{{color:'#2F4F4F',width:1}}}},
    {{name:'BOLL上', type:'line', data:{json.dumps([None]*(n-len(upper))+list(upper))}, smooth:true, symbol:'none', lineStyle:{{color:'#bbb',width:1,type:'dashed'}}}},
    {{name:'BOLL下', type:'line', data:{json.dumps([None]*(n-len(lower))+list(lower))}, smooth:true, symbol:'none', lineStyle:{{color:'#bbb',width:1,type:'dashed'}}}}
  ]
}});

var vchart = echarts.init(document.getElementById('vol'));
vchart.setOption({{
  tooltip:{{trigger:'axis'}},
  grid:{{left:60,right:20,top:20,bottom:30}},
  xAxis:{{type:'category', data:dates, axisLabel:{{fontSize:10}}}},
  yAxis:{{name:'万手', splitArea:{{show:true}}}},
  dataZoom:[{{type:'inside'}}],
  series:[{{type:'bar', data:{json.dumps([round(v/1e4,1) for v in vols])}, itemStyle:{{color:function(p){{return p.dataIndex>0? (kdata[p.dataIndex][1]>=kdata[p.dataIndex][0]?'#e23b3b':'#1aa34a'):'#ccc'}}}}}}]
}});

var mchart = echarts.init(document.getElementById('macd'));
mchart.setOption({{
  tooltip:{{trigger:'axis'}},
  legend:{{data:['DIF','DEA','MACD'], top:0}},
  grid:{{left:60,right:20,top:30,bottom:30}},
  xAxis:{{type:'category', data:dates, axisLabel:{{fontSize:10}}}},
  yAxis:{{splitArea:{{show:true}}}},
  dataZoom:[{{type:'inside'}}],
  series:[
    {{name:'DIF', type:'line', data:{json.dumps(list(dif))}, symbol:'none', lineStyle:{{color:'#e23b3b'}}}},
    {{name:'DEA', type:'line', data:{json.dumps(list(dea))}, symbol:'none', lineStyle:{{color:'#1E90FF'}}}},
    {{name:'MACD', type:'bar', data:{json.dumps(list(macd))}, itemStyle:{{color:function(p){{return p.data>=0?'#e23b3b':'#1aa34a'}}}}}}
  ]
}});

var rchart = echarts.init(document.getElementById('rsi'));
rchart.setOption({{
  tooltip:{{trigger:'axis'}},
  grid:{{left:60,right:20,top:20,bottom:30}},
  xAxis:{{type:'category', data:dates, axisLabel:{{fontSize:10}}}},
  yAxis:{{min:0,max:100, splitLine:{{show:true}}}},
  dataZoom:[{{type:'inside'}}],
  series:[
    {{type:'line', data:{json.dumps([None if np.isnan(x) else float(x) for x in rsi14])}, smooth:true, symbol:'none', lineStyle:{{color:'#9370DB',width:1.5}},
      markLine:{{silent:true, data:[{{yAxis:70,name:'超买'}},{{yAxis:30,name:'超卖'}}], lineStyle:{{color:'#999',type:'dashed'}}}}}}
  ]
}});

window.addEventListener('resize', function(){{ kchart.resize(); vchart.resize(); mchart.resize(); rchart.resize(); {ichart_resize} }});

{intraday_script}
</script>
</body>
</html>"""

html_path = os.path.join(WS, f"{CODE}_report.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML报告已生成:", html_path, len(html), "bytes")

# ===== 同步生成完整 DOCX 报告并保存到用户桌面（最终交付物）=====
script_dir = os.path.dirname(os.path.abspath(__file__))
docx_script = os.path.join(script_dir, "build_docx.py")
py = "/Users/gongjiayong/.workbuddy/binaries/python/envs/default/bin/python"
desktop = os.path.expanduser("~/Desktop")
try:
    subprocess.run(
        [py, docx_script, "--workspace", WS, "--code", CODE, "--name", NAME, "--desktop", desktop],
        check=True,
    )
except subprocess.CalledProcessError as e:
    print("DOCX生成失败（不影响HTML）:", e)
