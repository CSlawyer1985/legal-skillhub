#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智录运营看板生成器v2：从台账快照JSON生成交互式可视化看板HTML
用法: python3 dashboard_gen.py <input.json> [output.html]
"""
import json, sys, re
from collections import Counter

JS_CODE = r"""<script>
var D=__DATA_JSON__;
var filter='all',sortBy='date',sortDir=-1;
function rk(r){return r.indexOf('高')>=0?'高风险':r.indexOf('中')>=0?'中风险':'低风险'}
function render(){
  var rows=D.filter(function(x){if(filter==='all')return true;
    if(filter==='待补全')return (x.miss&&x.miss.length&&x.status!=='已完结');
    if(filter.indexOf('风险')>=0)return rk(x.risk)===filter;
    return x.status===filter});
  rows.sort(function(a,b){var va=a[sortBy],vb=b[sortBy];
    if(typeof va==='string')return va<vb?-sortDir:va>vb?sortDir:0;
    return(va-vb)*sortDir});
  var h=rows.map(function(x,i){
    var a=x.amount?'¥'+Math.round(x.amount):'—';
    var mb=(x.miss&&x.miss.length&&x.status!=='已完结')?'<span class="missbadge">缺'+x.miss.join('+')+'</span>':'';
    return '<tr class="click" onclick="tg('+i+')"><td>'+x.no+'</td><td>'+x.person+
      '</td><td>'+x.type+'</td><td>'+a+'</td><td>'+x.date+'</td><td>'+x.risk+x.score+
      '</td><td><span class="pill '+x.status+'">'+x.status+'</span>'+mb+'</td></tr>'+
      '<tr><td colspan="7" style="padding:0"><div class="detail" id="d'+i+'">'+
      '<div class="sec"><b>编号：</b>'+x.no+' <b>投诉人：</b>'+x.person+
      ' <b>类型：</b>'+x.type+' <b>金额：</b>'+a+' <b>风险：</b>'+x.risk+x.score+
      '分 <b>状态：</b>'+x.status+' <b>收到：</b>'+x.date+'</div>'+
      (mb?'<div class="sec"><b>数据待补全：</b>缺 '+(x.miss||[]).join('、')+'，建议回填后再答复</div>':'')+
      '<div class="sec"><b>投诉内容：</b>'+x.content+'</div></div></td></tr>';
  }).join('');
  document.getElementById('tbody').innerHTML=h;
}
function tg(i){var d=document.getElementById('d'+i);if(d)d.classList.toggle('show')}
var btns=document.querySelectorAll('#filters button');
for(var b=0;b<btns.length;b++){btns[b].onclick=function(){
  var all=document.querySelectorAll('#filters button');
  for(var j=0;j<all.length;j++)all[j].classList.remove('on');
  this.classList.add('on');filter=this.dataset.f;render()}}
var ths=document.querySelectorAll('th[data-sort]');
for(var t=0;t<ths.length;t++){ths[t].onclick=function(){
  if(sortBy===this.dataset.sort)sortDir=-sortDir;
  else{sortBy=this.dataset.sort;sortDir=-1}render()}}
render();
</script>"""

def generate(data, out_path, metrics=None):
    tickets = []
    for r in data:
        date_raw = r.get('date', '')
        if 'T' in date_raw: date = date_raw[5:10]
        elif len(date_raw) >= 10: date = date_raw[5:10]
        else: date = date_raw
        amount = r.get('amount', 0)
        try: amount = float(amount) if amount else 0
        except: amount = 0
        tickets.append({
            'no': r.get('no', '-'), 'person': r.get('person', '匿名'),
            'type': r.get('type', '其他'), 'amount': amount, 'date': date,
            'status': r.get('status', '-'), 'content': r.get('content', ''),
            'risk': r.get('risk', ''), 'score': r.get('score', 0),
            'miss': r.get('miss', []) or [],
        })
    data_json = json.dumps(tickets, ensure_ascii=False)
    type_dist = Counter(t['type'] for t in tickets)
    max_type = max(type_dist.values()) if type_dist else 1
    amts = [t['amount'] for t in tickets if t['amount'] > 0]
    total_amt = sum(amts)
    done = sum(1 for t in tickets if t['status'] == '已完结')
    pending = len(tickets) - done
    incomplete = sum(1 for t in tickets if t.get('miss') and t['status'] != '已完结')
    themes = {"自动续费/扣费":r"自动续费|自动扣|不知情.*扣|未续费.*扣","AI听记":r"AI听记|听记","千问办公":r"千问办公","退款被拒":r"不能退|不予退|不支持退|拒退|格式条款|不可退|不给退|无退费","客服承诺不兑现":r"承诺|宣传.*不符|无法实现|与实际"}
    theme_dist = {}
    for n,p in themes.items():
        h = sum(1 for t in tickets if re.search(p, t['content']))
        if h: theme_dist[n] = h
    max_theme = max(theme_dist.values()) if theme_dist else 1
    buckets = {"小额<500":sum(1 for a in amts if a<500),"中500-5k":sum(1 for a in amts if 500<=a<5000),"大额≥5k":sum(1 for a in amts if a>=5000)}
    max_bucket = max(buckets.values()) if buckets and max(buckets.values()) > 0 else 1
    date_dist = Counter(t['date'] for t in tickets)
    max_date = max(date_dist.values()) if date_dist else 1
    def bars(dist, mv):
        return ''.join(f'<div class="bar-row"><div class="lbl">{k}</div><div class="track"><div class="fill" style="width:{v/mv*100}%"></div></div><div class="val">{v}</div></div>' for k,v in sorted(dist.items(), key=lambda x:-x[1]))
    metrics_html = ''
    if metrics:
        c = metrics.get('cumulative', {}); rd = metrics.get('resolution_days', {})
        rf = metrics.get('refund', {}); rp = metrics.get('repeat', {}); tr = metrics.get('trend_weekly', [])
        def _kpi(num, lbl, approx=False):
            ap = ' <span class="ap">近似</span>' if approx else ''
            return f'<div class="mk"><div class="n">{num}</div><div class="l">{lbl}{ap}</div></div>'
        def _pct(v):
            return '—' if v is None else f'{v}%'
        cards = ''.join([
            _kpi(_pct(c.get('closure_rate')), '总办结率'),
            _kpi('—' if rd.get('median') is None else f"{rd.get('median')}天", f"办结时长中位(n={rd.get('n',0)})", True),
            _kpi(_pct(rf.get('case_rate_pct')), '退赔率·件数', True),
            _kpi(_pct(rf.get('amount_rate_pct')), '退赔率·金额', True),
            _kpi(_pct(rp.get('rate_pct')), '二次投诉率', True),
        ])
        trend = ''.join(f'<span>{t.get("bucket","").replace("2026-","")} 新<b>{t.get("new",0)}</b>/结{t.get("closed",0)}</span>' for t in tr[-6:])
        metrics_html = (f'<div class="mband"><h2>运营度量 · P1</h2><div class="mgrid">{cards}</div>'
                        f'<div class="mtrend">{trend}</div>'
                        f'<div class="mfoot">办结时长=收到→定稿(跟进末次日期近似)；退赔率/二次投诉率为关键词+跨件近似识别，仅供趋势参考。</div></div>')
    html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>智录·投诉运营看板</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"PingFang SC","Hiragino Sans GB",sans-serif;background:#f5f7fa;color:#2c3e50;padding:20px}}
.wrap{{max-width:1280px;margin:0 auto}}
header{{background:#fff;border-radius:12px;padding:24px 32px;box-shadow:0 1px 3px rgba(0,0,0,.06);display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}}
header h1{{font-size:20px;color:#1f4e79}}header .sub{{font-size:13px;color:#8a9aaa;margin-top:4px}}
header .meta{{font-size:12px;color:#b0bcc8;text-align:right}}
.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:20px}}
.stat{{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.06);text-align:center}}
.stat .num{{font-size:32px;font-weight:700;color:#1f4e79}}.stat .lbl{{font-size:13px;color:#8a9aaa;margin-top:4px}}
.stat.amt .num{{color:#e67e22}}.stat.done .num{{color:#27ae60}}.stat.pending .num{{color:#e74c3c}}.stat.miss .num{{color:#8e44ad}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}}
.card{{background:#fff;border-radius:10px;padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.card h2{{font-size:15px;color:#1f4e79;margin-bottom:14px;padding-left:8px;border-left:3px solid #1f4e79}}
.bar-row{{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:13px}}
.bar-row .lbl{{width:100px;color:#5a6b7d;flex-shrink:0}}.bar-row .track{{flex:1;height:20px;background:#eef2f7;border-radius:4px;overflow:hidden}}
.bar-row .fill{{height:100%;background:linear-gradient(90deg,#3b82f6,#1f4e79);border-radius:4px;min-width:2px}}
.bar-row .val{{width:28px;text-align:right;font-weight:600;color:#1f4e79}}
.insight{{background:#fff8e6;border:1px solid #f5d897;border-radius:8px;padding:14px 18px;margin-bottom:12px;font-size:13px;color:#8a6d1a;line-height:1.8}}
.insight b{{color:#1f4e79}}
.filters{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.filters button{{border:1px solid #ccd6e0;background:#fff;border-radius:6px;padding:5px 14px;font-size:12px;cursor:pointer;color:#5a6b7d}}
.filters button.on{{background:#1f4e79;color:#fff;border-color:#1f4e79}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{background:#f0f4f8;color:#5a6b7d;text-align:left;padding:8px 10px;border-bottom:2px solid #e3e8ee;cursor:pointer;user-select:none}}
th:hover{{color:#1f4e79}}td{{padding:8px 10px;border-bottom:1px solid #eef2f7}}
tr.click{{cursor:pointer}}tr.click:hover{{background:#f0f4f8}}
.pill{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;color:#fff}}
.pill.已完结{{background:#27ae60}}.pill.处理中{{background:#e67e22}}.pill.待处理{{background:#95a5a6}}
.detail{{display:none;background:#f8fafc;border-left:3px solid #1f4e79;margin:4px 0}}
.detail.show{{display:block}}
.detail .sec{{padding:10px 16px;font-size:13px;line-height:1.7}}
.detail .sec b{{color:#1f4e79}}
.missbadge{{display:inline-block;margin-left:6px;padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;color:#fff;background:#c0392b}}
.mband{{background:#fff;border-radius:10px;padding:18px 24px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:20px}}
.mband h2{{font-size:15px;color:#1f4e79;margin-bottom:14px;padding-left:8px;border-left:3px solid #2c7be5}}
.mgrid{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}}
.mk{{text-align:center}}.mk .n{{font-size:26px;font-weight:700;color:#2c7be5}}.mk .l{{font-size:12px;color:#8a9aaa;margin-top:2px}}
.mk .ap{{font-size:10px;color:#c0392b;font-weight:600}}
.mtrend{{margin-top:14px;display:flex;gap:6px;flex-wrap:wrap;font-size:12px;color:#5a6b7d}}
.mtrend span{{background:#eef2f7;border-radius:6px;padding:3px 8px}}.mtrend b{{color:#1f4e79}}
.mfoot{{font-size:11px;color:#b0bcc8;margin-top:10px}}
</style></head><body><div class="wrap">
<header><div><h1>智录·投诉运营看板</h1><div class="sub">市监群转办工单全流程闭环 · 交互式数据看板</div></div>
<div class="meta">数据快照自动刷新(每日16:30)<br>{len(tickets)}件工单</div></header>
<div class="stats">
<div class="stat"><div class="num">{len(tickets)}</div><div class="lbl">总工单</div></div>
<div class="stat done"><div class="num">{done}</div><div class="lbl">已完结</div></div>
<div class="stat pending"><div class="num">{pending}</div><div class="lbl">待处理+处理中</div></div>
<div class="stat miss"><div class="num">{incomplete}</div><div class="lbl">待补全</div></div>
<div class="stat amt"><div class="num">¥{total_amt:,.0f}</div><div class="lbl">涉诉总额</div></div>
</div>
{metrics_html}
<div class="grid">
<div class="card"><h2>投诉类型分布</h2>{bars(type_dist,max_type)}</div>
<div class="card"><h2>产品/功能热点</h2>{bars(theme_dist,max_theme)}</div>
</div>
<div class="grid">
<div class="card"><h2>金额区间分布</h2>{bars(buckets,max_bucket)}</div>
<div class="card"><h2>每日趋势</h2>{''.join(f'<div class="bar-row"><div class="lbl">{d}</div><div class="track"><div class="fill" style="width:{date_dist[d]/max_date*100}%"></div></div><div class="val">{date_dist[d]}</div></div>' for d in sorted(date_dist))}</div>
</div>
<div class="card" style="margin-bottom:20px"><h2>风险洞察</h2>
<div class="insight"><b>① 自动续费/扣款是第一大产品合规风险（{theme_dist.get("自动续费/扣费",0)}件）</b>——《消保法实施条例》要求自动续费须显著提示，建议推动产品侧强化开通页显著提示+扣款前短信预提醒。</div>
<div class="insight"><b>② AI听记是投诉重灾区（{theme_dist.get("AI听记",0)}件）</b>——退款流程混乱+自动续费提示不足。建议统一AI听记退款SOP。</div>
<div class="insight"><b>③ 客服承诺不兑现是最高频主题（{theme_dist.get("客服承诺不兑现",0)}件）</b>——建议核查客服话术库，删除未授权承诺。</div>
<div class="insight"><b>④ 大额件集中在企业服务合同（{buckets["大额≥5k"]}件≥5000）</b>——企业客户不适用《消保法》，需法务前置介入。</div>
<div class="insight"><b>⑤ 待处理件需核实</b>——{pending}件在办，逾期件建议优先处理。</div>
</div>
<div class="card"><h2>工单明细（点击行展开详情，点表头排序）</h2>
<div class="filters" id="filters">
<button class="on" data-f="all">全部</button>
<button data-f="已完结">已完结</button>
<button data-f="处理中">处理中</button>
<button data-f="待处理">待处理</button>
<button data-f="待补全">待补全</button>
<button data-f="高风险">高风险</button>
<button data-f="中风险">中风险</button>
<button data-f="低风险">低风险</button>
</div>
<table><thead><tr><th data-sort="no">编号</th><th data-sort="person">投诉人</th><th data-sort="type">类型</th><th data-sort="amount">金额</th><th data-sort="date">收到</th><th data-sort="score">风险</th><th data-sort="status">状态</th></tr></thead>
<tbody id="tbody"></tbody></table></div>
</div>
<!--JS_MARKER-->
</body></html>'''
    html = html.replace('<!--JS_MARKER-->', JS_CODE.replace('__DATA_JSON__', data_json))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"看板已生成: {out_path} ({len(tickets)}件, 交互式v2)")

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ledger_snapshot.json'
    out = sys.argv[2] if len(sys.argv) > 2 else '/Users/chuer/.qwenworkcn/workspace/msxzj93lzcuofavg/outputs/智录运营看板.html'
    with open(inp, encoding='utf-8') as f:
        data = json.load(f)
    generate(data, out)
