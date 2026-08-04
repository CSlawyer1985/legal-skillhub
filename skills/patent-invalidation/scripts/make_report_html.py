#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_report_html.py — 专利无效检索「执行过程报告」HTML 生成器（数据驱动）

【设计目标】
本技能在每次无效检索/分析中，都必须产出一份**结构固定、图文并茂**的 HTML 报告，
方便用户跨轮次、跨案例对照查看执行过程（检索 → 对比文件 → 特征比对 → 理由策略 → 附图比对）。

报告采用「固定 7 章结构」：
  一、目标专利信息
  二、检索过程记录
  三、对比文件分析与筛选
  四、技术方案特征比对（G7）
  五、无效理由策略与论证
  六、附图比对（被无效专利 vs 对比文件）
  七、执行过程日志

无论输入数据多寡，7 章标题 / 锚点(id) / 目录顺序**永远不变**；缺失数据以占位符渲染，
从而「每次都生成相同结构的文件」。

【用法】
  python make_report_html.py --data report_data.json --out invalidation_report_CNxxxx.html
  # --out 缺省时自动生成 invalidation_report_<目标专利号>.html（与 --data 同目录）

【数据契约】
report_data.json 字段说明见 references/无效检索分析报告_HTML生成规范.md
所有字符串字段默认按纯文本转义；若字段以 "_html" 结尾，则按原始 HTML 透传（作者自负）。
"""
import argparse
import html
import json
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 固定 CSS（与技能视觉规范一致；每次生成完全相同）
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
  :root {
    --bg: #f8f9fa; --card: #ffffff; --text: #1a1a2e; --muted: #6c757d;
    --primary: #1b4965; --accent: #e74c3c; --green: #27ae60;
    --orange: #e67e22; --blue: #2980b9; --purple: #8e44ad;
    --border: #dee2e6; --code-bg: #f1f3f5; --shadow: 0 2px 12px rgba(0,0,0,.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, "Microsoft YaHei", "Segoe UI", sans-serif; background: var(--bg); color: var(--text); line-height:1.7; padding:20px; }
  .container { max-width:1100px; margin:0 auto; }
  h1 { font-size:22px; color:var(--primary); border-bottom:3px solid var(--primary); padding-bottom:10px; margin-bottom:24px; }
  h2 { font-size:18px; color:var(--primary); border-left:4px solid var(--accent); padding-left:12px; margin:32px 0 16px; }
  h3 { font-size:15px; color:#333; margin:18px 0 10px; }
  .card { background:var(--card); border-radius:10px; box-shadow:var(--shadow); padding:24px; margin-bottom:20px; }
  .meta-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:10px 20px; }
  .meta-item { display:flex; gap:8px; }
  .meta-label { font-weight:700; color:var(--primary); white-space:nowrap; min-width:90px; }
  .meta-value { color:#444; word-break:break-all; }
  table { width:100%; border-collapse:collapse; margin:14px 0; font-size:13.5px; }
  th, td { border:1px solid var(--border); padding:8px 10px; text-align:left; vertical-align:top; }
  th { background:var(--primary); color:#fff; font-weight:600; }
  tr:nth-child(even) td { background:#f7fafc; }
  .tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11.5px; font-weight:600; color:#fff; }
  .tag-red { background:var(--accent); } .tag-green { background:var(--green); }
  .tag-orange { background:var(--orange); } .tag-blue { background:var(--blue); }
  .tag-purple { background:var(--purple); } .tag-gray { background:#95a5a6; }
  .same { background:#c8e6c9 !important; color:#1b5e20; font-weight:600; }
  .diff { background:#ffcdd2 !important; color:#b71c1c; font-weight:600; }
  .partial { background:#fff9c4 !important; color:#f57f17; font-weight:600; }
  pre { background:var(--code-bg); border-radius:6px; padding:14px; overflow-x:auto; font-size:12px; line-height:1.5; border:1px solid var(--border); white-space:pre-wrap; }
  code { font-family:"Cascadia Code","Consolas",monospace; font-size:12px; }
  .fig-container { text-align:center; margin:20px 0; }
  .fig-container img { max-width:100%; border:1px solid var(--border); border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,.1); }
  .fig-caption { font-size:12.5px; color:var(--muted); margin-top:6px; font-style:italic; }
  .compare-wrap { display:flex; flex-wrap:wrap; gap:16px; align-items:flex-start; margin:16px 0; }
  .compare-col { flex:1 1 320px; min-width:280px; }
  .compare-col .fig-container { margin:0; }
  .vs-badge { display:block; text-align:center; font-weight:700; color:var(--accent); margin:8px 0; font-style:normal; }
  .pa-card { border:1px solid var(--border); border-radius:8px; padding:10px; margin:8px 0; }
  .timeline { border-left:3px solid var(--primary); padding-left:20px; margin:16px 0; }
  .timeline-item { position:relative; margin-bottom:16px; }
  .timeline-item::before { content:''; position:absolute; left:-26px; top:5px; width:10px; height:10px; border-radius:50%; background:var(--accent); }
  .strength-bar { display:inline-block; width:120px; height:18px; border-radius:9px; background:#e0e0e0; vertical-align:middle; position:relative; overflow:hidden; }
  .strength-fill { height:100%; border-radius:9px; }
  .claim-box { background:#eef4ff; border-left:4px solid var(--blue); padding:12px 16px; margin:12px 0; font-size:13px; }
  .warn { background:#fff3cd; border:1px solid #ffc107; border-radius:6px; padding:10px 14px; margin:12px 0; font-size:13px; }
  .info { background:#d1ecf1; border:1px solid #17a2b8; border-radius:6px; padding:10px 14px; margin:12px 0; font-size:13px; }
  .toc { background:#fff; border:1px solid var(--border); border-radius:8px; padding:18px 24px; margin-bottom:20px; }
  .toc a { color:var(--blue); text-decoration:none; display:block; padding:3px 0; }
  .toc a:hover { text-decoration:underline; color:var(--accent); }
  .footer { text-align:center; color:var(--muted); font-size:12px; margin-top:30px; padding-top:16px; border-top:1px solid var(--border); }
  @media print { body { padding:0; background:#fff; } .card { box-shadow:none; border:1px solid #ddd; } }
  .fig-src { display:inline-block; font-size:11px; font-weight:600; padding:1px 8px; border-radius:10px; margin:2px 0 6px; }
  .fig-src-official { background:#e8f5e9; color:#1b5e20; border:1px solid #27ae60; }
  .fig-src-upload { background:#e3f2fd; color:#0d47a1; border:1px solid #2980b9; }
  .fig-src-svg { background:#fff3cd; color:#b45309; border:1px solid #e67e22; }
  .fig-src-neutral { background:#eceff1; color:#455a64; border:1px solid #95a5a6; }
"""


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────
def esc(v):
    """纯文本转义（默认对所有字符串字段使用）。"""
    if v is None:
        return ""
    return html.escape(str(v), quote=True)


def g(d, *keys, default=""):
    """深层安全取字段。"""
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur if cur is not None else default


def txt(v):
    """字符串字段：转义。若字段本身已是 HTML 字符串（调用方显式传入），请直接用 raw()。"""
    return esc(v)


def raw(v):
    """透传原始 HTML（仅在对数据来源有把握时使用）。"""
    return "" if v is None else str(v)


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def placeholder(label="待补充"):
    return f'<span style="color:#b71c1c;font-style:italic;">（{esc(label)}）</span>'


def rank_tag(relevance, cls=None):
    """相关度标签渲染。relevance 形如 '★★★★'；cls 可显式指定 tag 颜色类。"""
    if not relevance:
        return placeholder("相关度待填")
    if cls:
        return f'<span class="tag {cls}">{esc(relevance)}</span>'
    # 按星数推断颜色
    star = str(relevance).count("★")
    klass = {4: "tag-red", 3: "tag-orange", 2: "tag-blue", 1: "tag-gray"}.get(star, "tag-gray")
    return f'<span class="tag {klass}">{esc(relevance)}</span>'


def conclusion_cell(conclusion):
    """特征比对结论单元格：same/partial/diff → 对应 CSS 类。"""
    c = str(conclusion).strip().lower()
    if c.startswith("same") or c == "相同" or c == "✅" or c == "✔":
        return '<td class="same">✅ 相同</td>'
    if c.startswith("partial") or c == "基本相同" or c == "部分相同" or c.startswith("⚠"):
        return '<td class="partial">⚠️ 基本相同</td>'
    return '<td class="diff">❌ 不同</td>'


def fig_badge(obj):
    """附图来源溯源徽标：official(官方) / user_upload(用户上传) / svg_reconstruction(SVG重构)。
    字段缺省则不渲染（向后兼容既有案例）。"""
    if not isinstance(obj, dict):
        return ""
    s = (obj.get("source") or "").strip().lower()
    if not s:
        return ""
    mapping = {
        "official": ("官方附图", "fig-src-official"),
        "user_upload": ("用户上传", "fig-src-upload"),
        "upload": ("用户上传", "fig-src-upload"),
        "svg_reconstruction": ("SVG重构(非官方)", "fig-src-svg"),
        "svg": ("SVG重构(非官方)", "fig-src-svg"),
    }
    label, cls = mapping.get(s, ("附图", "fig-src-neutral"))
    return f'<div class="fig-src {cls}">{esc(label)}</div>'


# ─────────────────────────────────────────────────────────────────────────────
# 各章节渲染（结构固定）
# ─────────────────────────────────────────────────────────────────────────────
def build_cover(meta):
    title = g(meta, "title") or placeholder("专利名称")
    tno = g(meta, "target_patent_no") or placeholder("目标专利号")
    pno = g(meta, "publication_no") or ""
    pno_disp = f"（{esc(pno)}）" if pno else ""
    report_date = g(meta, "report_date") or datetime.now().strftime("%Y年%m月%d日")
    ipc_main = g(meta, "ipc_main") or placeholder("IPC主分类")
    ptype = g(meta, "patent_type") or "发明"
    status = g(meta, "status") or placeholder("法律状态")
    return f"""
<div class="card">
<h1>📋 无效宣告检索分析报告</h1>
<div style="display:flex; justify-content:space-between; align-items:center;">
  <div><strong>目标专利：</strong>{esc(tno)}{esc(pno_disp)}<br>
       <strong>专利名称：</strong>{esc(title)}<br>
       <strong>报告日期：</strong>{esc(report_date)}</div>
  <div style="text-align:right;"><span class="tag tag-blue">{esc(ipc_main)}</span>&nbsp;<span class="tag tag-green">{esc(ptype)}</span><br>
       <strong>状态：</strong>{esc(status)}</div>
</div>
</div>"""


def build_toc():
    items = [
        ("一、目标专利信息", "sec1"),
        ("二、检索过程记录", "sec2"),
        ("三、对比文件分析与筛选", "sec3"),
        ("四、技术方案特征比对（G7）", "sec4"),
        ("五、无效理由策略与论证", "sec5"),
        ("六、附图比对（被无效专利 vs 对比文件）", "sec6"),
        ("七、执行过程日志", "sec7"),
    ]
    links = "\n".join(f'<a href="#{i}">{esc(t)}</a>' for t, i in items)
    return f"""
<div class="toc">
<strong>📑 目录</strong><br>
{links}
</div>"""


def build_sec1(meta, claims):
    if not meta and not claims:
        meta = {}
        claims = {}
    md = meta or {}
    cl = claims or {}
    def item(label, val):
        v = g(md, label) or g(md, label.replace(" ", "_"))
        return f'<div class="meta-item"><span class="meta-label">{esc(label)}:</span><span class="meta-value">{esc(v) if v else placeholder(label)}</span></div>'
    fields = ["公开号", "申请号", "名称", "申请人", "发明人", "申请日", "公开日", "授权日", "IPC主分类", "IPC分类"]
    grid = "".join(item(f, None) for f in fields)
    claim_count = g(cl, "claim_count") or placeholder("N")
    indep = g(cl, "independent_claim") or placeholder("独立权利要求内容")
    # 支持从属权利要求以列表或字符串给出
    dep = g(cl, "dependent_claims")
    if isinstance(dep, list):
        dep_html = "<br>".join(f"权{esc(x.get('no','?'))}→{esc(x.get('text',''))}" for x in dep)
    else:
        dep_html = esc(dep) if dep else placeholder("从属权利要求内容")
    return f"""
<h2 id="sec1">一、目标专利信息</h2>
<div class="card">
<div class="meta-grid">{grid}</div>

<h3>权利要求书摘要（共{esc(claim_count)}项）</h3>
<div class="claim-box">
<strong>独立权利要求1 — 核心技术方案：</strong><br>
{esc(indep).replace(chr(10), "<br>") if indep else placeholder("独立权利要求内容")}
<br>
<strong>从属权利要求：</strong> {dep_html}
</div>
</div>"""


def build_sec2(search):
    s = search or {}
    tool = g(s, "tool") or "PatSeek API（patseek.cn）"
    deadline = g(s, "deadline") or placeholder("时间死线")
    strategy = g(s, "strategy") or placeholder("检索策略")
    info = f"""<div class="info">
<strong>检索工具：</strong>{esc(tool)}<br>
<strong>时间死线：</strong>所有对比文件公开日须早于 {esc(deadline)}<br>
<strong>检索策略：</strong>{esc(strategy)}</div>"""

    # 2.1 布尔检索
    b = g(s, "bool_search", default={}) or {}
    bquery = g(b, "query") or placeholder("检索式")
    bcount = g(b, "result_count") or "0"
    bhits = as_list(g(b, "hits", default=[]))
    if bhits:
        blines = "\n".join(
            f"--- 第 {esc(h.get('rank', i+1))} 条 --- {esc(h.get('pubno',''))} | {esc(h.get('title',''))} | {esc(h.get('applicant',''))} | {esc(h.get('date',''))}"
            for i, h in enumerate(bhits)
        )
    else:
        blines = placeholder("布尔检索命中（在 bool_search.hits 中填写）")
    sec21 = f"""<h3>2.1 布尔检索（主检索）— IPC 限领域 + 核心关键词</h3>
<pre><code># 检索式：{esc(bquery)}
# 结果：共 {esc(bcount)} 条命中

{blines}</code></pre>"""

    # 2.2 补充定向检索
    supp = as_list(g(s, "supplementary", default=[]))
    if supp:
        sec22_lines = []
        for i, sp in enumerate(supp):
            q = g(sp, "query", default=placeholder("检索式"))
            c = g(sp, "count", default="?")
            kh = as_list(g(sp, "key_hits", default=[]))
            kh_txt = "\n".join(f"#   {esc(x)}" for x in kh) if kh else ""
            sec22_lines.append(f"# 检索式 {chr(65)+str(i)}：{esc(q)} → {esc(c)}条\n{kh_txt}")
        sec22 = "<h3>2.2 补充定向检索（旋转冷藏柜 / 圆柱体 / 导轨风扇 等）</h3>\n<pre><code>" + "\n\n".join(sec22_lines) + "</code></pre>"
    else:
        sec22 = f"<h3>2.2 补充定向检索</h3>\n<pre><code>{placeholder('补充定向检索式与命中（在 supplementary 中填写）')}</code></pre>"

    # 2.3 语义检索
    sem = g(s, "semantic", default={}) or {}
    squery = g(sem, "query") or placeholder("语义查询文本")
    scount = g(sem, "result_count") or "0"
    shits = as_list(g(sem, "top_hits", default=[]))
    if shits:
        sheader = "  排名  公开号           相似度  名称                          申请日      判定"
        slines = "\n".join(
            f"  {esc(x.get('rank','')):>3}  {esc(x.get('pubno','')):<16} {esc(x.get('similarity','')):<6} {esc(x.get('title','')):<28} {esc(x.get('date','')):<10} {esc(x.get('verdict',''))}"
            for x in shits
        )
        sec23 = f"""<h3>2.3 语义检索</h3>
<pre><code># 查询文本：{esc(squery)}
# 结果：{esc(scount)}条语义相似文献
# Top hits（按相似度排序）：

{sheader}
{slines}</code></pre>"""
    else:
        sec23 = f"""<h3>2.3 语义检索</h3>
<pre><code># 查询文本：{esc(squery)}
# 结果：{esc(scount)}条语义相似文献
{placeholder('语义 Top 命中（在 semantic.top_hits 中填写）')}</code></pre>"""

    # 2.4 预期/重复
    ad = g(s, "anticipation_dup", default={}) or {}
    anti = g(ad, "anticipation") or placeholder("预期检索结论")
    dup = g(ad, "duplicate") or placeholder("重复检索结论")
    sec24 = f"""<h3>2.4 预期/重复检索</h3>
<pre><code># 预期检索（同申请人）：{esc(anti)}
# 重复检索（相同主题）：{esc(dup)}</code></pre>"""

    # 2.5 时间线
    tl = as_list(g(s, "timeline", default=[]))
    if tl:
        tl_html = "".join(f'<div class="timeline-item">{esc(x)}</div>' for x in tl)
    else:
        tl_html = placeholder("检索过程时间线（在 timeline 中填写）")
    sec25 = f"""<h3>2.5 检索过程时间线</h3>
<div class="timeline">{tl_html}</div>"""

    return f"""
<h2 id="sec2">二、检索过程记录</h2>
<div class="card">
{info}
{sec21}
{sec22}
{sec23}
{sec24}
{sec25}
</div>"""


def build_sec3(prior_art):
    pa = as_list(prior_art)
    if not pa:
        return """
<h2 id="sec3">三、对比文件分析与筛选</h2>
<div class="card"><p>经多轮检索与筛选，以下为最具价值的对比文件候选（均满足时间死线要求）：</p>
<p style="color:#b71c1c;font-style:italic;">（待补充：在 prior_art 中填写对比文件列表）</p></div>"""
    # 概览表
    rows = []
    for p in pa:
        code = g(p, "code") or "?"
        pubno = g(p, "pubno") or placeholder("公开号")
        title = g(p, "title") or placeholder("名称")
        applicant = g(p, "applicant") or placeholder("申请人")
        pubdate = g(p, "pubdate") or placeholder("公开日")
        ipc = g(p, "ipc") or ""
        rel = g(p, "relevance") or ""
        relcls = g(p, "relevance_class")
        role = g(p, "role") or placeholder("推荐角色")
        rows.append(f"""<tr>
<td><strong>{esc(code)}</strong></td>
<td>{esc(pubno)}</td>
<td>{esc(title)}</td>
<td>{esc(applicant)}</td>
<td>{esc(pubdate)}</td>
<td>{esc(ipc)}</td>
<td>{rank_tag(rel, relcls)}</td>
<td>{esc(role)}</td>
</tr>""")
    overview = f"""<table>
<thead><tr><th>编号</th><th>公开号</th><th>名称</th><th>申请人</th><th>公开日</th><th>IPC</th><th>相关度</th><th>推荐角色</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>"""
    # 逐篇详析
    details = []
    for p in pa:
        code = g(p, "code") or "?"
        pubno = g(p, "pubno") or "?"
        title = g(p, "title") or ""
        core = g(p, "core_structure") or placeholder("核心结构")
        corr = g(p, "correspondence") or placeholder("与权利要求对应")
        dist = g(p, "distinctions") or placeholder("区别特征")
        det = f"""<h3>{esc(code)} 详细分析 — {esc(pubno)}「{esc(title)}」</h3>
<table>
<tr><th width="90">项目</th><th>内容</th></tr>
<tr><td>核心结构</td><td>{esc(core).replace(chr(10), "<br>")}</td></tr>
<tr><td>与权项对应</td><td>{esc(corr).replace(chr(10), "<br>")}</td></tr>
<tr><td>区别特征</td><td>{esc(dist).replace(chr(10), "<br>")}</td></tr>
</table>"""
        details.append(det)
    return f"""
<h2 id="sec3">三、对比文件分析与筛选</h2>
<div class="card">
<p>经多轮检索与筛选，以下为最具价值的对比文件候选（均满足时间死线要求）：</p>
{overview}
{''.join(details)}
</div>"""


def build_sec4(fc):
    fc = fc or {}
    against = g(fc, "against") or placeholder("对比文件")
    rows = as_list(g(fc, "rows", default=[]))
    if not rows:
        table = placeholder("特征比对行（在 feature_compare.rows 中填写）")
    else:
        trs = []
        for r in rows:
            rid = g(r, "id") or ""
            cf = g(r, "claim_feature") or placeholder("权利要求特征")
            cmp = g(r, "compare_feature") or placeholder("对比文件对应技术")
            concl = g(r, "conclusion") or "diff"
            remark = g(r, "remark") or ""
            trs.append(f"""<tr>
<td>{esc(rid)}</td>
<td><strong>{esc(cf)}</strong></td>
<td>{esc(cmp).replace(chr(10), "<br>")}</td>
{conclusion_cell(concl)}
<td>{esc(remark).replace(chr(10), "<br>")}</td>
</tr>""")
        table = f"""<table>
<thead><tr><th>序号</th><th>权利要求特征</th><th>{esc(against)}对应技术</th><th>比对结论</th><th>备注</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table>"""
    summary = g(fc, "summary") or placeholder("G7比对小结")
    # 三步法
    ts = as_list(g(fc, "three_step", default=[]))
    if ts:
        trows = []
        for t in ts:
            step = g(t, "step") or placeholder("步骤")
            content = g(t, "content") or placeholder("分析内容")
            concl = g(t, "conclusion") or ""
            trows.append(f"""<tr>
<td><strong>{esc(step)}</strong></td>
<td>{esc(content).replace(chr(10), "<br>")}</td>
<td>{esc(concl)}</td>
</tr>""")
        threestep = f"""<h3>区别特征的显而易见性分析（三步法）</h3>
<table>
<thead><tr><th>步骤</th><th>分析内容</th><th>结论</th></tr></thead>
<tbody>{''.join(trows)}</tbody></table>"""
    else:
        threestep = ""
    return f"""
<h2 id="sec4">四、技术方案特征比对（G7色标对照）</h2>
<div class="card">
<p>以下表格将<strong>权利要求1</strong>的全部必要技术特征逐一拆解，与<strong>{esc(against)}</strong>进行逐特征比对：</p>
{table}
<div class="info"><strong>G7比对小结：</strong><br>{esc(summary).replace(chr(10), "<br>")}</div>
{threestep}
</div>"""


def build_sec5(strategy):
    st = strategy or {}
    main = g(st, "main", default={}) or {}
    # 主攻
    m_title = g(main, "title") or "主攻路线：法第22条第3款 — 创造性（不具备创造性）"
    m_legal = g(main, "legal_basis") or placeholder("法律依据")
    m_target = g(main, "target") or placeholder("攻击对象")
    m_combo = g(main, "combination") or placeholder("对比文件组合")
    m_core = g(main, "core_argument") or placeholder("核心论点")
    m_strength = g(main, "strength") or placeholder("强度评估")
    m_pct = g(main, "strength_pct", default=0) or 0
    m_color = g(main, "strength_color") or "orange"
    m_note = g(main, "note") or ""
    main_html = f"""<h3>5.1 {esc(m_title)}</h3>
<table>
<thead><tr><th width="140">要素</th><th>内容</th></tr></thead>
<tbody>
<tr><td><strong>法律依据</strong></td><td>{esc(m_legal).replace(chr(10), "<br>")}</td></tr>
<tr><td><strong>攻击对象</strong></td><td>{esc(m_target)}</td></tr>
<tr><td><strong>对比文件组合</strong></td><td>{esc(m_combo).replace(chr(10), "<br>")}</td></tr>
<tr><td><strong>核心论点</strong></td><td>{esc(m_core).replace(chr(10), "<br>")}</td></tr>
<tr><td><strong>强度评估</strong></td><td>
<span class="strength-bar"><span class="strength-fill" style="width:{esc(m_pct)}%;background:var(--{esc(m_color)});"></span></span> <strong>{esc(m_strength)}</strong>
{m_note and ('<br><small>' + esc(m_note).replace(chr(10), "<br>") + '</small>') or ''}
</td></tr>
</tbody></table>"""
    # 辅助
    aux = as_list(g(st, "aux", default=[]))
    aux_html = []
    for i, a in enumerate(aux, start=2):
        a_title = g(a, "title") or f"辅助路线{i-1}"
        a_target = g(a, "target") or placeholder("攻击对象")
        a_ref = g(a, "reference") or placeholder("对比文件")
        a_arg = g(a, "argument") or placeholder("论点")
        a_str = g(a, "strength") or placeholder("强度")
        a_pct = g(a, "strength_pct", default=0) or 0
        a_color = g(a, "strength_color") or "green"
        aux_html.append(f"""<h3>5.{i} {esc(a_title)}</h3>
<table>
<thead><tr><th width="140">要素</th><th>内容</th></tr></thead>
<tbody>
<tr><td><strong>攻击对象</strong></td><td>{esc(a_target)}</td></tr>
<tr><td><strong>对比文件</strong></td><td>{esc(a_ref).replace(chr(10), "<br>")}</td></tr>
<tr><td><strong>论点</strong></td><td>{esc(a_arg).replace(chr(10), "<br>")}</td></tr>
<tr><td><strong>强度评估</strong></td><td><span class="strength-bar"><span class="strength-fill" style="width:{esc(a_pct)}%;background:var(--{esc(a_color)});"></span></span> <strong>{esc(a_str)}</strong></td></tr>
</tbody></table>""")
    # 总览
    ov = as_list(g(st, "overview", default=[]))
    if ov:
        orows = "".join(
            f"""<tr><td>{esc(x.get('priority',''))}</td><td>{esc(x.get('reason',''))}</td><td>{esc(x.get('legal',''))}</td><td>{esc(x.get('scope',''))}</td><td>{esc(x.get('strength',''))}</td><td>{esc(x.get('advice',''))}</td></tr>"""
            for x in ov
        )
        ov_html = f"""<h3>5.{len(aux)+2 if aux else 4} 策略总览</h3>
<table>
<thead><tr><th>优先级</th><th>无效理由</th><th>法律依据</th><th>攻击范围</th><th>强度</th><th>建议</th></tr></thead>
<tbody>{orows}</tbody></table>"""
    else:
        ov_html = ""
    return f"""
<h2 id="sec5">五、无效理由策略与论证</h2>
<div class="card">
{main_html}
{''.join(aux_html)}
{ov_html}
</div>"""


def build_sec6(fig):
    fig = fig or {}
    intro = g(fig, "intro") or "本节将<strong>被无效专利</strong>的关键附图与各<strong>对比文件</strong>的对应附图并排比对，从图形结构层面直观展示相同点与区别点。"
    groups = as_list(g(fig, "groups", default=[]))
    group_html = []
    for i, grp in enumerate(groups, start=1):
        gtitle = g(grp, "title") or f"6.{i} 比对组"
        tf = as_list(g(grp, "target_figs", default=[]))
        pf = as_list(g(grp, "prior_figs", default=[]))
        tcols = "".join(
            f"""<div class="fig-container">
      {fig_badge(x)}<img src="{esc(x.get('src',''))}" alt="{esc(x.get('alt', x.get('src','')))}">
      <div class="fig-caption">{esc(x.get('caption','')).replace(chr(10), "<br>")}</div>
    </div>"""
            for x in tf
        )
        pcols = "".join(
            f"""<div class="pa-card">
      <div class="fig-container" style="margin:0;">
      {fig_badge(x)}<img src="{esc(x.get('src',''))}" alt="{esc(x.get('alt', x.get('src','')))}">
      <div class="fig-caption">{esc(x.get('caption','')).replace(chr(10), "<br>")}</div>
      </div>
    </div>"""
            for x in pf
        )
        concl = g(grp, "conclusion_html") or g(grp, "conclusion") or placeholder("图形比对结论")
        group_html.append(f"""<h3>{esc(gtitle)}</h3>
<div class="compare-wrap">
  <div class="compare-col">{tcols}</div>
  <div class="compare-col">{pcols}</div>
</div>
<div class="info">{esc(concl).replace(chr(10), "<br>") if not str(concl).startswith('<') else raw(concl)}</div>""")
    # 总表
    st = g(fig, "summary_table", default={}) or {}
    stcols = as_list(g(st, "columns", default=["比对维度", "被无效专利", "对比文件", "图形结论"]))
    strows = as_list(g(st, "rows", default=[]))
    if strows:
        srows = "".join(
            "<tr>" + "".join(f"<td>{raw(c) if str(c).startswith('<') else esc(c)}</td>" for c in r) + "</tr>"
            for r in strows
        )
        summary_table = f"""<h3>6.{len(groups)+1 if groups else 2} 附图比对总表</h3>
<table>
<thead><tr>{''.join(f'<th>{esc(c)}</th>' for c in stcols)}</tr></thead>
<tbody>{srows}</tbody></table>"""
    else:
        summary_table = f"""<h3>6.{len(groups)+1 if groups else 2} 附图比对总表</h3>
{placeholder('附图比对总表（在 summary_table 中填写）')}"""
    note = g(fig, "note")
    note_html = f'<div class="warn">{esc(note).replace(chr(10), "<br>")}</div>' if note else ""
    # 被无效专利其余附图
    te = g(fig, "target_extra_figs", default={}) or {}
    te_title = g(te, "title") or "被无效专利其余附图"
    te_figs = as_list(g(te, "figs", default=[]))
    if te_figs:
        te_cards = "".join(
            f"""<div class="fig-container" style="margin:0;flex:1 1 300px;">
    {fig_badge(x)}<img src="{esc(x.get('src',''))}" alt="{esc(x.get('alt', x.get('src','')))}">
    <div class="fig-caption">{esc(x.get('caption','')).replace(chr(10), "<br>")}</div>
  </div>"""
            for x in te_figs
        )
        extra_html = f"""<h3>6.{len(groups)+2 if groups else 3} {esc(te_title)}</h3>
<p style="font-size:13px;color:#666;">以下为被无效专利中未在上述比对组出现的附图，供理解完整技术方案参考：</p>
<div style="display:flex;gap:12px;flex-wrap:wrap;">{te_cards}</div>"""
    else:
        extra_html = ""
    return f"""
<h2 id="sec6">六、附图比对（被无效专利 vs 对比文件）</h2>
<div class="card">
<p>{raw(intro) if str(intro).startswith('<') else esc(intro).replace(chr(10), '<br>')}</p>
{''.join(group_html)}
{summary_table}
{note_html}
{extra_html}
</div>"""


def build_sec7(log):
    log = log or {}
    env = g(log, "env") or placeholder("执行环境信息")
    recs = as_list(g(log, "records", default=[]))
    recs_html = "\n".join(esc(r) for r in recs) if recs else placeholder("关键操作记录")
    outf = g(log, "output_files") or placeholder("输出文件清单")
    pending = as_list(g(log, "pending", default=[]))
    pending_html = "\n".join(f"{i+1}. {esc(p)}" for i, p in enumerate(pending)) if pending else placeholder("无")
    return f"""
<h2 id="sec7">七、执行过程日志</h2>
<div class="card">
<pre><code>=== 执行环境 ===
{esc(env)}

=== 关键操作记录 ===
{recs_html}

=== 输出文件 ===
{esc(outf)}

=== 待后续完善事项 ===
{pending_html}</code></pre>
</div>"""


def build_footer(meta):
    skill_ver = g(meta, "skill_version") or "patent-invalidation-skill v1.1.0"
    gen_time = g(meta, "generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M CST")
    return f"""
<div class="footer">
<p>本报告由 {esc(skill_ver)} + PatSeek API 自动生成 | 生成时间: {esc(gen_time)}</p>
<p>⚠️ 本报告仅供研究参考，不构成正式法律意见。实际无效宣告请求应由具备资质的专利代理师/律师起草。</p>
</div>"""


def generate(data, out_path):
    meta = g(data, "meta", default={}) or {}
    claims = g(data, "claims_summary", default={}) or {}
    search = g(data, "search", default={}) or {}
    prior_art = g(data, "prior_art", default=[]) or []
    fc = g(data, "feature_compare", default={}) or {}
    strategy = g(data, "strategy", default={}) or {}
    fig = g(data, "figure_compare", default={}) or {}
    log = g(data, "execution_log", default={}) or {}

    title_full = f"{esc(g(meta,'target_patent_no',''))} {esc(g(meta,'title',''))}".strip()
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>无效宣告检索分析报告 — {title_full}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
{build_cover(meta)}
{build_toc()}
{build_sec1(meta, claims)}
{build_sec2(search)}
{build_sec3(prior_art)}
{build_sec4(fc)}
{build_sec5(strategy)}
{build_sec6(fig)}
{build_sec7(log)}
{build_footer(meta)}
</div><!-- end container -->
</body>
</html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="专利无效检索执行过程报告 HTML 生成器（固定7章结构）")
    ap.add_argument("--data", required=True, help="report_data.json 路径（数据契约见 references/无效检索分析报告_HTML生成规范.md）")
    ap.add_argument("--out", default=None, help="输出 HTML 路径；缺省为 invalidation_report_<目标专利号>.html（与 --data 同目录）")
    args = ap.parse_args()

    if not os.path.isfile(args.data):
        sys.exit(f"[错误] 找不到数据文件: {args.data}")
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    tno = g(data, "meta", "target_patent_no", default="PATENT")
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.data)),
                                   f"invalidation_report_{tno}.html")
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    generate(data, out)

    # 自检：确保 7 章锚点齐全
    with open(out, "r", encoding="utf-8") as f:
        html_txt = f.read()
    secs = [f'id="sec{i}"' for i in range(1, 8)]
    missing = [s for s in secs if s not in html_txt]
    if missing:
        print(f"[警告] 输出缺少章节锚点: {missing}")
    print(f"[完成] 报告已生成: {out}")
    print(f"[自检] 7章结构锚点: {'全部存在 ✓' if not missing else '缺失 ' + str(missing)}")


if __name__ == "__main__":
    main()
