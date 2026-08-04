#!/usr/bin/env python3
"""
Equity Structure Report Generator — v3.0 (hardened).

DESIGN RULES (zero-tolerance, enforced by validation):
  1. HTML assembly uses list.append() + ''.join() — NO f-strings with {} in HTML context.
  2. SVG: all user-provided text runs through svg_escape() before insertion.
  3. Image paths: ALWAYS absolute (os.path.join(out_dir, png_name)).
  4. Post-generation validation: HTML checked for {var} leaks, SVG checked for XML validity.
  5. WeasyPrint font_config: always FontConfiguration().

Usage as module:
  from generate_equity_report import EquityReport
  report = EquityReport(data_dict, output_dir)
  report.generate_all()

Or standalone:
  python generate_equity_report.py data.json output_dir/
"""

import json
import os
import re
import subprocess
import sys
from datetime import date
from xml.etree import ElementTree as ET

# ── Constants ──
CSS = r"""<style>
  @page { margin: 15mm 15mm 20mm 15mm; size: A4;
    @top-center { content: element(header); font-size: 9px; color: #888;
      border-bottom: 1px solid #e0ddd5; padding-bottom: 4px; width: 180mm; }
    @bottom-center { content: counter(page); font-size: 9px; color: #888; padding-top: 8px; }
  }
  @page cover { margin: 0; @top-center { content: none; } @bottom-center { content: none; } }
  @page toc { margin: 15mm; @top-center { content: none; } @bottom-center { content: none; } }
  body { font-family: "Source Han Sans SC","PingFang SC","Microsoft YaHei",sans-serif; background: #F7F4ED; color: #3a3430; line-height: 1.7; font-size: 13px; }
  .cover { width: 210mm; height: 297mm; margin: 0 auto; background: linear-gradient(160deg,#2C3E50,#1a2a38,#243342); position: relative; overflow: hidden; page: cover; page-break-after: always; }
  .cover-content { position: relative; z-index: 1; padding: 70px 70px 50px; color: #fff; display: flex; flex-direction: column; height: 297mm; }
  .cover-badge { display: inline-block; background: rgba(212,165,116,0.25); border: 1px solid rgba(212,165,116,0.4); padding: 6px 18px; border-radius: 20px; font-size: 11px; letter-spacing: 2px; margin-bottom: 30px; }
  .cover-title { font-size: 28px; font-weight: 700; line-height: 1.4; margin-bottom: 10px; }
  .cover-subtitle { font-size: 14px; color: #a0b0c0; margin-bottom: 40px; letter-spacing: 1px; }
  .cover-info { flex: 1; }
  .cover-info-item { display: flex; margin-bottom: 10px; font-size: 12px; }
  .cover-info-label { color: #8899aa; min-width: 90px; }
  .cover-info-value { color: #d0d8e0; }
  .cover-footer { margin-top: auto; padding: 16px 0 30px 0; border-top: 1px solid rgba(255,255,255,0.10); font-size: 10px; color: #667; }
  .toc-page { width: 180mm; margin: 0 auto; padding: 25px 30px 45px; background: #fff; page: toc; page-break-after: always; }
  .toc-title { font-size: 22px; font-weight: 700; color: #2C3E50; margin-bottom: 25px; padding-bottom: 12px; border-bottom: 2px solid #D4A574; }
  .toc-entry { margin: 6px 0; font-size: 13px; }
  .toc-entry a { text-decoration: none; color: #3a3430; display: flex; align-items: baseline; width: 100%; }
  .toc-entry a::after { content: target-counter(attr(href), page); min-width: 28px; text-align: right; font-size: 12px; }
  .toc-dots { flex: 1; border-bottom: 1px dotted #c0c8d0; margin: 0 8px; min-width: 20px; align-self: flex-end; margin-bottom: 4px; }
  .toc-l2 { padding-left: 20px; font-size: 12px; color: #555; }
  .page, .page-last { width: 180mm; margin: 0 auto; padding: 15px 0 45px; background: #fff; page-break-before: always; }
  .page-inner, .page-last-inner { padding: 0 30px; }
  .page-header { position: running(header); display: flex; justify-content: space-between; width: 180mm; padding: 4px 0 8px; font-size: 9px; color: #888; }
  .sec-title { border-bottom: 2px solid #D4A574; padding-bottom: 10px; margin-bottom: 25px; font-size: 20px; color: #2C3E50; font-weight: 700; }
  .sub-title { font-size: 16px; color: #2C3E50; font-weight: 600; margin: 25px 0 15px 0; }
  table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 12px; page-break-inside: avoid; }
  th { background: #2C3E50; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; font-size: 11px; }
  td { padding: 9px 12px; border-bottom: 1px solid #eee; }
  tr:nth-child(even) td { background: #faf8f4; }
  .name-col { white-space: nowrap; text-align: left; }
  .ai-box { background: #F0F7FF; border-left: 4px solid #4A90D9; padding: 16px 20px; margin: 20px 0; border-radius: 0 6px 6px 0; font-size: 12px; page-break-inside: avoid; }
  .ai-box .ai-title { font-weight: 700; color: #2C5F8A; margin-bottom: 8px; font-size: 13px; }
  .ai-box p, .ai-box li { margin: 6px 0; }
  .ai-box ul { margin: 4px 0; padding-left: 20px; }
  .metric-grid { display: flex; flex-wrap: wrap; gap: 12px; margin: 15px 0; }
  .metric-card { flex: 1; min-width: 140px; background: #faf8f4; border: 1px solid #e0ddd5; border-radius: 8px; padding: 14px 16px; }
  .metric-label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
  .metric-value { font-size: 18px; font-weight: 700; color: #2C3E50; }
  .metric-sub { font-size: 10px; color: #999; margin-top: 2px; }
  .control-bar { display: flex; margin: 12px 0; page-break-inside: avoid; }
  .control-seg { height: 28px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #fff; font-weight: 600; white-space: nowrap; }
  .highlight-box { background: #FFF8E1; border-left: 4px solid #FFC107; padding: 12px 16px; margin: 15px 0; font-size: 12px; }
  img { max-width: 100%; }
</style>"""

PAGE_HEADER_HTML = """
<div class="page-header">
  <span>{name} · 股权结构深度分析报告</span>
  <span>水滴信用</span>
</div>
"""

TOC_HTML = """
<div class="toc-page" id="toc">
  <div class="toc-title">目 录</div>
  <div class="toc-entry"><a href="#ch1"><span>第一章 · 执行摘要</span><span class="toc-dots"></span></a></div>
  <div class="toc-entry"><a href="#ch2"><span>第二章 · 股权结构与实际控制人</span><span class="toc-dots"></span></a></div>
  <div class="toc-entry"><a href="#ch3"><span>第三章 · 关联企业全景</span><span class="toc-dots"></span></a></div>
  <div class="toc-entry"><a href="#ch4"><span>第四章 · 控制力分档与投资矩阵</span><span class="toc-dots"></span></a></div>
  <div class="toc-entry"><a href="#ch5"><span>第五章 · 关键发现与风险提示</span><span class="toc-dots"></span></a></div>
</div>
"""


# ── Helpers ──
def svg_escape(text):
    """Escape text for safe inclusion in SVG <text> elements."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def html_escape(text):
    """Escape text for safe inclusion in HTML body."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def categorize(investments):
    """Split investment list into control tiers."""
    full_ctrl = [i for i in investments if i.get('ratio') is not None and i['ratio'] == 1.0]
    strong_ctrl = [i for i in investments if i.get('ratio') is not None and 0.87 <= i['ratio'] <= 0.99]
    mid_ctrl = [i for i in investments if i.get('ratio') is not None and 0.50 <= i['ratio'] < 0.87]
    weak_ctrl = [i for i in investments if i.get('ratio') is not None and 0.25 <= i['ratio'] < 0.50]
    inv = [i for i in investments if i.get('ratio') is None or i['ratio'] < 0.25]
    return full_ctrl, strong_ctrl, mid_ctrl, weak_ctrl, inv


def validate_html(html_content):
    """Check for f-string-style variable leaks AND image tag presence."""
    # Remove CSS (which has valid {} for CSS rules)
    html_no_css = re.sub(r'<style>.*?</style>', '', html_content, flags=re.DOTALL)
    leaks = re.findall(r'\{[a-z_]+[\(}\)]', html_no_css)
    if leaks:
        raise ValueError("Variable leak detected in HTML: " + ", ".join(leaks))
    # Verify image tag is present — this is the most common omission
    if '<img ' not in html_no_css and '<img>' not in html_no_css:
        raise ValueError("HTML is missing <img> tag for equity architecture diagram. "
                         "Ensure img_abs_path is set in data and build_chapter2() renders it.")
    return True


def validate_svg(svg_path):
    """Check SVG is valid XML."""
    try:
        ET.parse(svg_path)
        return True
    except ET.ParseError as e:
        raise ValueError("SVG XML parse error: " + str(e))


def tbl_row(*cells, name_cols=None):
    """Build a <tr> with optional .name-col classes."""
    if name_cols is None:
        name_cols = set()
    parts = ["    <tr>"]
    for i, cell in enumerate(cells):
        cls = ' class="name-col"' if i in name_cols else ""
        parts.append("<td" + cls + ">" + svg_escape(str(cell)) + "</td>")
    parts.append("</tr>\n")
    return "".join(parts)


def inv_table_rows(inv_list):
    """Build table rows for an investment list."""
    rows = []
    for inv in inv_list:
        rows.append(tbl_row(
            inv['name'], inv.get('legal_person', ''),
            inv.get('capital', ''), inv.get('ratio_display', ''),
            inv.get('status', ''), inv.get('sector', ''),
            name_cols={0}
        ))
    return "".join(rows)


# ── SVG Generator ──
def build_svg(data, out_dir):
    """Build and save SVG equity structure diagram. Returns (svg_path, png_path)."""
    subj = data['subject']
    name = svg_escape(subj.get('company_name', ''))
    head = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">' + CSS + '</head><body>\n'
    head += PAGE_HEADER_HTML.format(name=name)

    head += '<div class="page" id="ch1"><div class="page-inner">\n'
    head += '<div class="sec-title">第一章 · 执行摘要</div>\n'

    # Metric grid row 1
    head += '<div class="metric-grid">\n'
    for label, value, sub in [
        ("企业全称", subj.get('company_name', ''), ""),
        ("注册资本", subj.get('capital_display', subj.get('capital', '')), subj.get('capital_note', '')),
        ("企业类型", subj.get('type_short', ''), subj.get('type_full', subj.get('company_type', ''))),
        ("成立日期", (subj.get('establish_date', '') or '')[:10], subj.get('years_note', '')),
    ]:
        head += '<div class="metric-card"><div class="metric-label">' + label + '</div>'
        head += '<div class="metric-value" style="font-size:14px;">' + str(value) + '</div>'
        if sub:
            head += '<div class="metric-sub">' + str(sub) + '</div>'
        head += '</div>\n'
    head += '</div>\n'

    # Metric grid row 2
    inv_list = data.get('investments', [])
    full_ctrl, strong_ctrl, mid_ctrl, weak_ctrl, equity_inv = categorize(inv_list)
    n_total = len(inv_list)
    n_full = len(full_ctrl)
    n_ctrl = len(strong_ctrl) + len(mid_ctrl) + len(weak_ctrl)
    n_equity = len(equity_inv)

    listed = data.get('listed_parent', {})
    stock_code = data.get('stock_code', data.get('listed_parent', {}).get('code', '—'))
    ctrl_info = data.get('controller', {})

    head += '<div class="metric-grid">\n'
    for label, value, sub in [
        ("唯一股东/实控人", data.get('sole_shareholder', ctrl_info.get('controller_name', '')), data.get('shareholder_note', '')),
        ("实际控制人", ctrl_info.get('controller_name', ''), "受益 " + ctrl_info.get('benefit_ratio', '') + " · 表决权 " + ctrl_info.get('voting_right', '')),
        ("对外投资", str(n_total) + " 家", "全资" + str(n_full) + "家 · 参控股" + str(n_ctrl) + "家 · 产业链" + str(n_equity) + "家"),
        ("上市公司母公司", stock_code, listed.get('employeesNum', '') + " 人" if listed.get('employeesNum') else ""),
    ]:
        head += '<div class="metric-card"><div class="metric-label">' + label + '</div>'
        head += '<div class="metric-value" style="font-size:13px;">' + str(value) + '</div>'
        if sub:
            head += '<div class="metric-sub">' + str(sub) + '</div>'
        head += '</div>\n'
    head += '</div>\n'

    # Summary text
    summary = data.get('summary_text', '')
    head += '<p><strong>核心结论：</strong>' + summary + '</p>\n'
    head += '<div class="ai-box"><div class="ai-title">【AI 深度解读 · 整体判断】</div>\n'
    head += data.get('ai_summary_html', '<p>数据来源：水滴信用 MCP 平台实时查询。</p>')
    head += '</div>\n</div></div>\n'

    return head


def build_chapter2(data):
    """Chapter 2: Equity Structure."""
    subj = data['subject']
    ctrl = data.get('controller', {})
    bo = data.get('beneficial_owner', {})
    chain_html = data.get('chain_table_html', '')
    img_abs_path = data.get('img_abs_path', '')
    ctrl_assessment = data.get('control_assessment_html', '')

    html = []
    html.append('<div class="page" id="ch2"><div class="page-inner">\n')
    html.append('<div class="sec-title">第二章 · 股权结构与实际控制人</div>\n')

    # 2.1 Basic info
    html.append('<h3 class="sub-title">2.1 企业基本信息</h3>\n')
    html.append('<table>\n')
    html.append('<tr><th style="width:25%;">项目</th><th>内容</th></tr>\n')
    fields = [
        ("企业全称", subj.get('company_name', ''), True),
        ("统一社会信用代码", subj.get('credit_no', ''), False),
        ("企业类型", subj.get('company_type', ''), False),
        ("法定代表人", subj.get('legal_person', ''), True),
        ("注册资本", subj.get('capital', ''), False),
        ("成立日期", (subj.get('establish_date', '') or '')[:10], False),
        ("登记机关", subj.get('authority', ''), False),
        ("经营状态", subj.get('company_status', '正常'), False),
        ("注册地址", subj.get('company_address', ''), False),
    ]
    for label, val, is_name in fields:
        cls = ' class="name-col"' if is_name else ''
        html.append('<tr><td>' + label + '</td><td' + cls + '>' + str(val) + '</td></tr>\n')
    html.append('</table>\n')

    # 2.2 Chain table
    html.append('<h3 class="sub-title">2.2 控股架构穿透</h3>\n')
    html.append(chain_html)

    # 2.3 Controller
    html.append('<h3 class="sub-title">2.3 实际控制人</h3>\n')
    html.append('<table>\n')
    html.append('<tr><th style="width:25%;">项目</th><th>内容</th></tr>\n')
    ctrl_rows = [
        ("实控人姓名", ctrl.get('controller_name', '')),
        ("实控人类型", ctrl.get('controller_type', '')),
        ("受益比例", ctrl.get('benefit_ratio', '')),
        ("表决权比例", ctrl.get('voting_right', '')),
    ]
    for label, val in ctrl_rows:
        cls = ' class="name-col"' if '姓名' in label else ''
        html.append('<tr><td>' + label + '</td><td' + cls + '>' + str(val) + '</td></tr>\n')
    for p in ctrl.get('paths', []):
        html.append('<tr><td>控制路径</td><td>' + str(p) + '</td></tr>\n')
    html.append('<tr><td>任职情况</td><td>' + ctrl.get('position', '') + '</td></tr>\n')
    html.append('</table>\n')

    # 2.4 Architecture diagram (ALWAYS include — validate_html will catch if missing)
    if not img_abs_path:
        print("  WARNING: img_abs_path is empty — architecture diagram will be missing!")
    html.append('<h3 class="sub-title">2.4 架构全景图</h3>\n')
    html.append('<img src="' + (img_abs_path or 'MISSING_IMAGE_PATH') + '" style="width:100%;max-width:680px;display:block;margin:20px auto;" alt="股权架构图"/>\n')

    html.append('<h3 class="sub-title">2.5 控制力评估</h3>\n')
    html.append(ctrl_assessment)

    html.append('<div class="ai-box"><div class="ai-title">【AI 深度解读 · 股权架构分析】</div>\n')
    html.append(data.get('ai_ch2_html', '<p>数据来源：MCP 工具实时查询。</p>'))
    html.append('</div>\n</div></div>\n')
    return "".join(html)


def build_chapter3(inv_list):
    """Chapter 3: Affiliated Enterprises."""
    full_ctrl, strong_ctrl, mid_ctrl, weak_ctrl, equity_inv = categorize(inv_list)
    n_total = len(inv_list)
    n_full = len(full_ctrl)
    n_strong = len(strong_ctrl)
    n_mid = len(mid_ctrl)
    n_weak = len(weak_ctrl)
    n_equity = len(equity_inv)
    n_dead = len([i for i in inv_list if i.get('status') in ('注销', '吊销')])

    dead_pct = round(n_dead / n_total * 100) if n_total > 0 else 0
    ctrl_pct = round((n_full + n_strong) / n_total * 100) if n_total > 0 else 0
    eq_pct = round(n_equity / n_total * 100) if n_total > 0 else 0

    html = []
    html.append('<div class="page" id="ch3"><div class="page-inner">\n')
    html.append('<div class="sec-title">第三章 · 关联企业全景</div>\n')
    html.append('<h3 class="sub-title">3.1 对外投资总览</h3>\n')
    html.append('<p>共对外投资 <strong>' + str(n_total) + ' 家企业</strong>：</p>\n')

    # Control bar
    bar_segs = [
        ("#2E7D32", "全资 " + str(n_full) + "家", n_full),
        ("#43A047", "绝对 " + str(n_strong) + "家", n_strong),
        ("#FF9800", "实质 " + str(n_mid) + "家", n_mid),
        ("#FFC107", "强参股 " + str(n_weak) + "家", n_weak),
        ("#9E9E9E", "参股 " + str(n_equity) + "家", n_equity),
    ]
    bar_segs = [(c, t, cnt) for c, t, cnt in bar_segs if cnt > 0]
    total_cnt = sum(cnt for _, _, cnt in bar_segs)
    html.append('<div class="control-bar">\n')
    for color, text, cnt in bar_segs:
        pct = max(int(cnt / total_cnt * 100), 6) if total_cnt > 0 else 20
        html.append('<div class="control-seg" style="background:' + color + ';width:' + str(pct) + '%;">' + text + '</div>\n')
    html.append('</div>\n')

    # Full + strong control
    html.append('<h3 class="sub-title">3.2 全资及高度控股子公司</h3>\n')
    html.append('<table><tr><th>企业名称</th><th>法定代表人</th><th>注册资本</th><th>持股</th><th>状态</th><th>领域</th></tr>\n')
    html.append(inv_table_rows(full_ctrl + strong_ctrl + mid_ctrl))
    html.append('</table>\n')

    # Weak control
    if weak_ctrl:
        html.append('<h3 class="sub-title">3.3 重要参股（25%-50%）</h3>\n')
        html.append('<table><tr><th>企业名称</th><th>法定代表人</th><th>注册资本</th><th>持股</th><th>状态</th><th>领域</th></tr>\n')
        html.append(inv_table_rows(weak_ctrl))
        html.append('</table>\n')

    # Equity investments
    html.append('<h3 class="sub-title">3.4 产业链参股（&lt;25%）</h3>\n')
    html.append('<table><tr><th>企业名称</th><th>法定代表人</th><th>注册资本</th><th>持股</th><th>状态</th><th>领域</th></tr>\n')
    html.append(inv_table_rows(equity_inv))
    html.append('</table>\n')

    # Dead list
    dead_list = [i for i in inv_list if i.get('status') in ('注销', '吊销')]
    if dead_list:
        html.append('<h3 class="sub-title">3.5 注销/吊销企业（' + str(len(dead_list)) + ' 家）</h3>\n')
        html.append('<table><tr><th>企业名称</th><th>注册资本</th><th>原持股</th><th>状态</th></tr>\n')
        for inv in dead_list:
            html.append(tbl_row(inv['name'], inv.get('capital', ''), inv.get('ratio_display', ''), inv['status'], name_cols={0}))
        html.append('</table>\n')

    html.append('<div class="ai-box"><div class="ai-title">【AI 深度解读 · 投资组合分析】</div>\n')
    html.append('<p><strong>事实：</strong>' + str(n_total) + ' 家对外投资中，全资/绝对控股 ' + str(n_full + n_strong) + ' 家（' + str(ctrl_pct) + '%）、参股 ' + str(n_equity) + ' 家（' + str(eq_pct) + '%）。已注销/吊销 ' + str(n_dead) + ' 家（' + str(dead_pct) + '%）。</p>')
    html.append('<p><strong>推论：</strong>投资组合呈现核心控股+广泛参股格局。</p>')
    html.append('</div>\n</div></div>\n')
    return "".join(html)


def build_chapter4(inv_list):
    """Chapter 4: Control Tier Analysis."""
    full_ctrl, strong_ctrl, mid_ctrl, weak_ctrl, equity_inv = categorize(inv_list)
    n_full = len(full_ctrl)
    n_strong = len(strong_ctrl)
    n_mid = len(mid_ctrl)
    n_weak = len(weak_ctrl)
    n_equity = len(equity_inv)

    html = []
    html.append('<div class="page" id="ch4"><div class="page-inner">\n')
    html.append('<div class="sec-title">第四章 · 控制力分档与投资矩阵</div>\n')

    html.append('<h3 class="sub-title">4.1 控制力六档分级</h3>\n')
    html.append('<table>\n')
    html.append('<tr><th>持股区间</th><th>档级名称</th><th>企业数量</th><th>代表企业</th></tr>\n')
    tiers = [
        ("100%", "全资控制", "#2E7D32", str(n_full)),
        ("90%–99%", "绝对控制", "#43A047", str(n_strong)),
        ("50%–89%", "实质控制", "#FF9800", str(n_mid)),
        ("25%–49%", "强参股", "#FFC107", str(n_weak)),
        ("< 25%", "产业链参股", "#9E9E9E", str(n_equity)),
    ]
    for interval, name, color, cnt in tiers:
        if int(cnt) > 0 or interval == "< 25%":
            html.append('<tr><td>' + interval + '</td><td style="color:' + color + ';font-weight:700;">' + name + '</td><td>' + cnt + '</td><td class="name-col">—</td></tr>\n')
    html.append('</table>\n')

    # Top investments
    html.append('<h3 class="sub-title">4.2 投资行业分布</h3>\n')
    html.append('<table><tr><th>行业领域</th><th>涉及企业数</th><th>代表企业</th></tr>\n')
    sectors = data.get('sectors', [])
    if not sectors:
        sectors = [("综合", str(len(inv_list)), "详见第三章")]
    for name, cnt, example in sectors:
        html.append('<tr><td>' + name + '</td><td>' + cnt + '</td><td class="name-col">' + example + '</td></tr>\n')
    html.append('</table>\n')

    html.append('<div class="ai-box"><div class="ai-title">【AI 深度解读 · 控制力与投资策略】</div>\n')
    html.append('<p><strong>事实：</strong>全资控股 ' + str(n_full) + ' 家，参股 ' + str(n_equity + n_weak) + ' 家持股低于 50%。</p>')
    html.append('</div>\n</div></div>\n')
    return "".join(html)


def build_chapter5(inv_list):
    """Chapter 5: Key Findings & Risks."""
    n_total = len(inv_list)
    n_dead = len([i for i in inv_list if i.get('status') in ('注销', '吊销')])
    dead_pct = round(n_dead / n_total * 100) if n_total > 0 else 0

    html = []
    html.append('<div class="page-last" id="ch5"><div class="page-last-inner">\n')
    html.append('<div class="sec-title">第五章 · 关键发现与风险提示</div>\n')

    html.append('<h3 class="sub-title">5.1 控制权稳定性评估</h3>\n')
    html.append('<div class="highlight-box">')
    html.append(data.get('risk_control_text', '<strong>风险评估：</strong>详见报告全文。'))
    html.append('</div>\n')

    html.append('<h3 class="sub-title">5.2 多层架构透明度风险</h3>\n')
    html.append(data.get('risk_transparency_html', '<p>详见报告全文。</p>'))

    html.append('<h3 class="sub-title">5.3 投资组合减值风险</h3>\n')
    html.append('<p>' + str(n_total) + ' 家对外投资中，' + str(n_dead) + ' 家已注销/吊销（' + str(dead_pct) + '%）。</p>')

    html.append('<h3 class="sub-title">5.4 积极因素</h3>\n<ul>\n')
    positives = data.get('positive_factors', [])
    for pf in positives:
        html.append('<li><strong>' + pf[0] + '：</strong>' + pf[1] + '</li>\n')
    html.append('</ul>\n')

    html.append('<div class="ai-box"><div class="ai-title">【AI 深度解读 · 风险综合评估】</div>\n')
    html.append(data.get('ai_risk_html', '<p>风险等级：详见报告全文。</p>'))
    html.append('</div>\n')

    html.append('<p style="text-align:center;color:#aaa;font-size:11px;margin-top:40px;">— 报告完 —</p>\n')
    html.append('<p style="text-align:center;color:#aaa;font-size:9px;">凭安智能 · 水滴信用团队 | 数据截止：' + str(date.today()) + ' | 仅供内部参考</p>\n')
    html.append('</div></div>\n')
    return "".join(html)


# ── Main Report Class ──
class EquityReport:
    def __init__(self, data, output_dir):
        self.data = data
        self.out_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.subj = data['subject']
        self.company_short = self.subj['company_name'][:30].replace(' ', '').replace('（', '_').replace('）', '')

    def generate_svg(self):
        """Build SVG diagram. Returns (svg_path, png_path)."""
        svg_content = self._build_svg_content()
        svg_path = os.path.join(self.out_dir, self.company_short + "_股权架构图.svg")
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        # Validate
        try:
            validate_svg(svg_path)
        except ValueError as e:
            # Try common fix: replace unescaped &
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', content)
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(content)
            validate_svg(svg_path)

        # Convert to PNG
        png_path = os.path.join(self.out_dir, self.company_short + "_股权架构图_hd.png")
        r = subprocess.run(
            ['rsvg-convert', '--width=1200', '--height=864', svg_path, '-o', png_path],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print("WARNING: rsvg-convert failed:", r.stderr[:200])
            png_path = None
        else:
            print("  PNG:", png_path, f"({os.path.getsize(png_path)//1024}KB)")

        return svg_path, png_path

    def _build_svg_content(self):
        """Internal: construct SVG XML string."""
        subj = self.data['subject']
        inv_list = self.data.get('investments', [])
        full_ctrl, strong_ctrl, mid_ctrl, weak_ctrl, equity_inv = categorize(inv_list)

        name = svg_escape(subj.get('company_name', ''))
        ctrl_name = svg_escape(self.data.get('controller', {}).get('controller_name', ''))
        stock_code = svg_escape(self.data.get('stock_code', ''))
        listed = self.data.get('listed_parent', {})

        # Build SVG layers from data
        layers = self.data.get('svg_layers', [])
        if not layers:
            # Default simple layout
            svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" font-family="Source Han Sans SC, PingFang SC, Microsoft YaHei, sans-serif">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f8f6f1"/><stop offset="100%" stop-color="#efebe0"/></linearGradient>
    <linearGradient id="person" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#D4A574"/><stop offset="100%" stop-color="#c09060"/></linearGradient>
    <linearGradient id="platform" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#87A878"/><stop offset="100%" stop-color="#6d9168"/></linearGradient>
    <linearGradient id="listed" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#2C3E50"/><stop offset="100%" stop-color="#1a2a38"/></linearGradient>
    <filter id="shadow"><feDropShadow dx="2" dy="3" stdDeviation="4" flood-opacity="0.25"/></filter>
  </defs>
  <rect width="1000" height="600" fill="url(#bg)"/>
  <text x="500" y="32" text-anchor="middle" font-size="18" font-weight="700" fill="#2C3E50">''' + name + ''' · 股权架构图</text>
  <text x="500" y="54" text-anchor="middle" font-size="11" fill="#888">Equity Structure Map · ''' + str(date.today()) + '''</text>
  <text x="500" y="300" text-anchor="middle" font-size="14" fill="#999">架构图 —— 请提供 svg_layers 数据以生成详细图表</text>
</svg>'''
            return svg

        # Build from layers
        parts = ['<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 720" font-family="Source Han Sans SC, PingFang SC, Microsoft YaHei, sans-serif">\n']
        parts.append('  <defs>\n    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f8f6f1"/><stop offset="100%" stop-color="#efebe0"/></linearGradient>\n    <linearGradient id="person" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#D4A574"/><stop offset="100%" stop-color="#c09060"/></linearGradient>\n    <linearGradient id="platform" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#87A878"/><stop offset="100%" stop-color="#6d9168"/></linearGradient>\n    <linearGradient id="listed" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#2C3E50"/><stop offset="100%" stop-color="#1a2a38"/></linearGradient>\n    <filter id="shadow"><feDropShadow dx="2" dy="3" stdDeviation="4" flood-opacity="0.25"/></filter>\n  </defs>\n  <rect width="1000" height="720" fill="url(#bg)"/>\n')
        parts.append('  <text x="500" y="32" text-anchor="middle" font-size="18" font-weight="700" fill="#2C3E50">' + name + ' · 股权架构图</text>\n')
        parts.append('  <text x="500" y="54" text-anchor="middle" font-size="11" fill="#888">Equity Structure Map · ' + str(date.today()) + '</text>\n')

        for layer in layers:
            layer_type = layer.get('type', '')
            if layer_type == 'title':
                parts.append('  <text x="' + str(layer.get('x', 500)) + '" y="' + str(layer.get('y', 80)) + '" text-anchor="middle" font-size="' + str(layer.get('font_size', 12)) + '" fill="#999">' + svg_escape(layer.get('text', '')) + '</text>\n')
            elif layer_type == 'node':
                rx = str(layer.get('rx', 8))
                fill = layer.get('fill', 'url(#platform)')
                filter_attr = ' filter="url(#shadow)"' if layer.get('shadow', True) else ''
                parts.append('  <rect x="' + str(layer.get('x', 100)) + '" y="' + str(layer.get('y', 100)) + '" width="' + str(layer.get('w', 300)) + '" height="' + str(layer.get('h', 50)) + '" rx="' + rx + '" fill="' + fill + '"' + filter_attr + '/>\n')
                for text_line in layer.get('text_lines', []):
                    parts.append('  <text x="' + str(text_line.get('x', 500)) + '" y="' + str(text_line.get('y', 120)) + '" text-anchor="middle" font-size="' + str(text_line.get('font_size', 13)) + '" font-weight="' + str(text_line.get('weight', 700)) + '" fill="' + str(text_line.get('color', '#fff')) + '">' + svg_escape(text_line.get('text', '')) + '</text>\n')
            elif layer_type == 'line':
                dash = ' stroke-dasharray="' + layer.get('dash', '6,3') + '"' if layer.get('dashed') else ''
                parts.append('  <line x1="' + str(layer.get('x1', 0)) + '" y1="' + str(layer.get('y1', 0)) + '" x2="' + str(layer.get('x2', 0)) + '" y2="' + str(layer.get('y2', 0)) + '" stroke="' + layer.get('stroke', '#2C3E50') + '" stroke-width="' + str(layer.get('sw', 2)) + '"' + dash + '/>\n')
                if layer.get('label'):
                    parts.append('  <text x="' + str(layer.get('lx', 0)) + '" y="' + str(layer.get('ly', 0)) + '" font-size="' + str(layer.get('lfs', 9)) + '" fill="' + layer.get('lc', '#2C3E50') + '" font-weight="600" text-anchor="middle">' + svg_escape(layer['label']) + '</text>\n')
            elif layer_type == 'legend':
                parts.append('  <rect x="20" y="690" width="960" height="20" rx="4" fill="#faf8f4" stroke="#e0ddd5"/>\n')
                lx = 35
                for item in layer.get('items', []):
                    parts.append('  <rect x="' + str(lx) + '" y="695" width="10" height="10" rx="2" fill="' + item.get('color', '#999') + '"/>\n')
                    parts.append('  <text x="' + str(lx + 15) + '" y="705" font-size="8" fill="#555">' + svg_escape(item.get('text', '')) + '</text>\n')
                    lx += 80

        parts.append('</svg>\n')
        return "".join(parts)

    def generate_html(self, png_abs_path):
        """Build full HTML report. Returns html_path."""
        self.data['img_abs_path'] = png_abs_path

        parts = []
        parts.append('<!DOCTYPE html>\n<html lang="zh-CN">\n<head><meta charset="UTF-8">')
        parts.append(CSS)
        parts.append('</head>\n<body>\n')

        name = self.subj.get('company_name', '')
        parts.append(PAGE_HEADER_HTML.format(name=name))

        # Cover
        stock_code = self.data.get('stock_code', '—')
        today = str(date.today())
        parts.append('<div class="cover"><div class="cover-content">\n')
        parts.append('<div class="cover-badge">EQUITY STRUCTURE ANALYSIS</div>\n')
        parts.append('<div class="cover-title">' + name + '<br>股权结构与关联企业深度分析报告</div>\n')
        parts.append('<div class="cover-subtitle">Equity Structure &amp; Affiliated Enterprise Analysis Report</div>\n')
        parts.append('<div class="cover-info">\n')
        parts.append('<div class="cover-info-item"><span class="cover-info-label">股票代码</span><span class="cover-info-value">' + stock_code + '</span></div>\n')
        parts.append('<div class="cover-info-item"><span class="cover-info-label">分析日期</span><span class="cover-info-value">' + today + '</span></div>\n')
        parts.append('<div class="cover-info-item"><span class="cover-info-label">数据来源</span><span class="cover-info-value">水滴信用 MCP 数据平台 · 实时查询</span></div>\n')
        parts.append('<div class="cover-info-item"><span class="cover-info-label">分析机构</span><span class="cover-info-value">凭安智能 · 水滴信用团队</span></div>\n')
        parts.append('</div>\n')
        parts.append('<div class="cover-footer"><strong>免责声明：</strong>本报告基于水滴信用 MCP 数据平台实时查询的公开工商信息编制。AI 深度解读观点为分析性推论，不构成法律或投资建议。</div>\n')
        parts.append('</div></div>\n')

        # TOC
        parts.append(TOC_HTML)

        # Chapters
        parts.append(build_chapter1(self.data))
        parts.append(build_chapter2(self.data))
        parts.append(build_chapter3(self.data.get('investments', [])))
        parts.append(build_chapter4(self.data.get('investments', [])))
        parts.append(build_chapter5(self.data.get('investments', [])))

        parts.append('</body></html>')
        full_html = "".join(parts)

        # Validate
        validate_html(full_html)

        html_path = os.path.join(self.out_dir, self.company_short + "_股权报告.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print("  HTML:", html_path, f"({len(full_html)} bytes) — validated, no leaks")
        return html_path

    def generate_pdf(self, html_path):
        """Convert HTML to PDF with embedded fonts."""
        pdf_path = os.path.join(self.out_dir, self.company_short + "_股权结构分析报告.pdf")
        from weasyprint import HTML as WHTML
        from weasyprint.text.fonts import FontConfiguration
        WHTML(filename=html_path).write_pdf(pdf_path, font_config=FontConfiguration())
        size_kb = os.path.getsize(pdf_path) // 1024
        print("  PDF:", pdf_path, f"({size_kb}KB)")
        return pdf_path

    def generate_all(self):
        """Full pipeline: SVG -> PNG -> HTML -> PDF."""
        print("Generating report for:", self.subj.get('company_name', ''))
        svg_path, png_path = self.generate_svg()
        if not png_path:
            raise RuntimeError("PNG generation failed — cannot embed architecture diagram in PDF")
        png_abs = os.path.abspath(png_path)
        html_path = self.generate_html(png_abs)
        pdf_path = self.generate_pdf(html_path)
        print("Done:", pdf_path)
        return pdf_path


def build_chapter1(data):
    """Chapter 1: Executive Summary."""
    subj = data['subject']
    inv_list = data.get('investments', [])
    full_ctrl, strong_ctrl, mid_ctrl, weak_ctrl, equity_inv = categorize(inv_list)
    listed = data.get('listed_parent', {})
    ctrl = data.get('controller', {})
    stock_code = data.get('stock_code', '—')

    n_total = len(inv_list)
    n_full = len(full_ctrl)
    n_ctrl = len(strong_ctrl) + len(mid_ctrl) + len(weak_ctrl)
    n_equity = len(equity_inv)

    parts = []
    parts.append('<div class="page" id="ch1"><div class="page-inner">\n')
    parts.append('<div class="sec-title">第一章 · 执行摘要</div>\n')

    # Metric grid row 1
    parts.append('<div class="metric-grid">\n')
    metrics_r1 = [
        ("企业全称", subj.get('company_name', ''), "", "14px"),
        ("注册资本", subj.get('capital_display', subj.get('capital', '')), subj.get('capital_note', ''), "18px"),
        ("企业类型", subj.get('type_short', '法人独资' if '法人独资' in subj.get('company_type', '') else ''), subj.get('company_type', ''), "15px"),
        ("成立日期", (subj.get('establish_date', '') or '')[:10], subj.get('years_note', ''), "15px"),
    ]
    for label, value, sub, fs in metrics_r1:
        parts.append('<div class="metric-card"><div class="metric-label">' + label + '</div>')
        parts.append('<div class="metric-value" style="font-size:' + fs + ';">' + str(value) + '</div>')
        if sub:
            parts.append('<div class="metric-sub">' + str(sub) + '</div>')
        parts.append('</div>\n')
    parts.append('</div>\n')

    # Metric grid row 2
    parts.append('<div class="metric-grid">\n')
    metrics_r2 = [
        ("唯一股东/实控人", data.get('sole_shareholder', ctrl.get('controller_name', '')), data.get('shareholder_note', '')),
        ("实际控制人", ctrl.get('controller_name', ''), "受益 " + ctrl.get('benefit_ratio', '') + " · 表决权 " + ctrl.get('voting_right', '')),
        ("对外投资", str(n_total) + " 家", "全资" + str(n_full) + "家 · 参控股" + str(n_ctrl) + "家 · 产业链" + str(n_equity) + "家"),
        ("上市公司母公司", stock_code, "注册 " + listed.get('registeredCapital', '') + " · " + listed.get('employeesNum', '') + " 人" if listed.get('employeesNum') else ""),
    ]
    for label, value, sub in metrics_r2:
        parts.append('<div class="metric-card"><div class="metric-label">' + label + '</div>')
        parts.append('<div class="metric-value" style="font-size:13px;">' + str(value) + '</div>')
        if sub:
            parts.append('<div class="metric-sub">' + str(sub) + '</div>')
        parts.append('</div>\n')
    parts.append('</div>\n')

    parts.append('<p><strong>核心结论：</strong>' + data.get('summary_text', '') + '</p>\n')
    parts.append('<div class="ai-box"><div class="ai-title">【AI 深度解读 · 整体判断】</div>\n')
    parts.append(data.get('ai_summary_html', ''))
    parts.append('</div>\n</div></div>\n')
    return "".join(parts)


# ── Standalone CLI ──
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python generate_equity_report.py data.json output_dir/")
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)
    report = EquityReport(data, sys.argv[2])
    report.generate_all()
