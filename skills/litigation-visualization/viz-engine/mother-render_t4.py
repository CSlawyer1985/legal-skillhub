#!/usr/bin/env python3
"""T4-r1.1渲染器：全文换行+动态行高，可见文本零截断零省略号零Markdown语法。
用法: render_t4.py --root .   exit 0/3"""
import sys, json, html, subprocess, re
from pathlib import Path
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1600, 900
FONT = "PingFang SC, Songti SC, sans-serif"
def esc(s): return html.escape(str(s), quote=True)
def hold(m): print(f"HOLD-VIS: {m}"); return 3

def vw(ch):  # 视觉宽度：CJK=1，其他=0.55
    return 1.0 if ord(ch) > 0x2E7F else 0.55

def wrap(s, maxw):
    """按视觉宽度换行，零截断。"""
    lines, cur, w = [], "", 0.0
    for ch in str(s):
        cw = vw(ch)
        if w + cw > maxw and cur:
            lines.append(cur); cur, w = ch, cw
        else:
            cur += ch; w += cw
    if cur: lines.append(cur)
    return lines or [""]

def tspans(x, y, lines, size, fill, lh=None, weight=None, anchor=None):
    lh = lh or size + 6
    wa = f' font-weight="{weight}"' if weight else ""
    aa = f' text-anchor="{anchor}"' if anchor else ""
    out = ""
    for i, l in enumerate(lines):
        out += f'<text x="{x}" y="{y + i*lh}" font-family="{FONT}" font-size="{size}"{wa}{aa} fill="{fill}">{esc(l)}</text>'
    return out, y + len(lines)*lh

def svg_head(title, subtitle):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect width="{W}" height="{H}" fill="#fbfaf7"/>'
        f'<text x="40" y="52" font-family="{FONT}" font-size="30" font-weight="bold" fill="#1a1a1a">{esc(title)}</text>'
        f'<text x="40" y="84" font-family="{FONT}" font-size="16" fill="#666">{esc(subtitle)}</text>'
        f'<text x="{W-40}" y="52" text-anchor="end" font-family="{FONT}" font-size="14" fill="#999">内部研究草稿·历史盲评·禁止外发</text>')

def box_list(s, items, x, y0, boxw, size, fillc, strokec, textc, aid_c, maxw):
    y = y0
    for it in items:
        lines = wrap(it["text"], maxw)
        bh = len(lines)*(size+6) + 18
        s += f'<rect x="{x}" y="{y}" width="{boxw}" height="{bh}" rx="8" fill="{fillc}" stroke="{strokec}"/>'
        ts, _ = tspans(x+16, y+size+10, lines, size, textc)
        s += ts
        pass  # 锚标签仅存审计侧件，不入可见层
        y += bh + 12
    return s, y

def render_01(cv, title):
    v = cv["views"]["01-主体关系图"]
    s = svg_head(title, "数据源：第一节 主体与角色＋第二节 合同与交易链")
    s += f'<text x="60" y="122" font-family="{FONT}" font-size="19" font-weight="bold" fill="#333">主体与角色</text>'
    s, _ = box_list(s, v["parties"], 60, 140, 680, 15, "#eef3fb", "#4a76b8", "#1a3a6b", "#8aa", 40)
    s += f'<text x="790" y="122" font-family="{FONT}" font-size="19" font-weight="bold" fill="#333">合同与交易链</text>'
    s, _ = box_list(s, v["chain"], 790, 140, 750, 15, "#f6efe2", "#b8944a", "#5b451a", "#b8944a", 45)
    return s + "</svg>"

def render_02(cv, title):
    v = cv["views"]["02-关键事件时间线"]
    s = svg_head(title, "数据源：第二至五节含日期事实行；无日期节以数据行摘要入图")
    evs = v["events"]
    ms = v.get("undated_milestones", [])
    ym = 330
    x0, x1 = 90, W-90
    if evs:
        s += f'<line x1="{x0}" y1="{ym}" x2="{x1}" y2="{ym}" stroke="#4a76b8" stroke-width="3"/>'
        n = len(evs)
        for i, e in enumerate(evs):
            x = x0 + (x1-x0)*(i/max(n-1,1))
            lx = min(max(x, 250), W-250)
            up = i % 2 == 0
            lines = wrap(e["text"], 30)
            block_h = 18 + len(lines)*17 + 14
            ty = (ym - 40 - block_h) if up else (ym + 46)
            s += (f'<circle cx="{x:.0f}" cy="{ym}" r="7" fill="#4a76b8"/>'
                  f'<line x1="{x:.0f}" y1="{ym}" x2="{x:.0f}" y2="{ty+block_h if up else ty-6}" stroke="#9bb" stroke-dasharray="3,3"/>')
            ts, ny = tspans(lx, ty+14, [e["date"]], 14, "#1a3a6b", weight="bold", anchor="middle")
            s += ts
            ts, ny = tspans(lx, ny+2, lines, 13, "#444", lh=17, anchor="middle")
            s += ts
            pass  # 锚标签不入可见层
    my = 620
    if ms:
        s += f'<text x="90" y="{my-28}" font-family="{FONT}" font-size="16" font-weight="bold" fill="#555">未系日期事实（数据行全文）</text>'
        for m in ms:
            lines = wrap("◇ " + m["text"], 92)
            ts, my = tspans(90, my, lines, 14, "#555", lh=22)
            s += ts
            my += 8
    return s + "</svg>"

def render_03(cv, title):
    v = cv["views"]["03-要件证据矩阵"]
    s = svg_head(title, "数据源：第六节 要件-事实-证据矩阵＋第四节 款项与余额＋第七节 证据索引")
    y = 126
    s += f'<text x="60" y="{y}" font-family="{FONT}" font-size="17" font-weight="bold" fill="#333">要件矩阵</text>'
    y += 12
    colw = [170, 300, 190, 330, 420]
    cw_chars = [11, 21, 13, 23, 30]
    for r in v["matrix"]:
        cells = r["cells"]
        wrapped = [wrap(cells[j] if j < len(cells) else "", cw_chars[j]) for j in range(5)]
        rh = max(len(wl) for wl in wrapped)*17 + 12
        pend = any(k in "".join(cells) for k in ("待","暂缓","未核","缺","双口径"))
        x = 60
        for j in range(5):
            s += f'<rect x="{x}" y="{y}" width="{colw[j]}" height="{rh}" fill="{"#fdf3ee" if pend else "#eef7ee"}" stroke="#bbb"/>'
            ts, _ = tspans(x+7, y+16, wrapped[j], 12, "#333", lh=17)
            s += ts
            x += colw[j]
        y += rh
    y += 26
    s += f'<text x="60" y="{y}" font-family="{FONT}" font-size="17" font-weight="bold" fill="#333">款项与余额</text>'
    y += 12
    aw = [180, 240, 520, 470]
    aw_chars = [12, 17, 38, 34]
    for r in v["amounts"]:
        cells = r["cells"]
        wrapped = [wrap(cells[j] if j < len(cells) else "", aw_chars[j]) for j in range(4)]
        rh = max(len(wl) for wl in wrapped)*17 + 12
        x = 60
        for j in range(4):
            s += f'<rect x="{x}" y="{y}" width="{aw[j]}" height="{rh}" fill="#eef3fb" stroke="#bbb"/>'
            ts, _ = tspans(x+7, y+16, wrapped[j], 12, "#1a3a6b", lh=17)
            s += ts
            x += aw[j]
        y += rh
    y += 26
    s += f'<text x="60" y="{y}" font-family="{FONT}" font-size="17" font-weight="bold" fill="#333">证据索引</text>'
    y += 20
    for e in v["evidence_index"]:
        lines = wrap("· " + e["text"], 100)
        ts, y = tspans(60, y, lines, 13, "#444", lh=20)
        s += ts
        y += 6
    return s + "</svg>"

def render_04(cv, title):
    v = cv["views"]["04-阶段计划与风险"]
    s = svg_head(title, "数据源：第八节 诉讼阶段计划＋第九节 风险与暂停事项")
    s += f'<text x="60" y="122" font-family="{FONT}" font-size="18" font-weight="bold" fill="#333">阶段计划</text>'
    stage_items = [{"text": "　".join(c for c in r["cells"] if c), "anchor_ids": r["anchor_ids"]} for r in v["stages"]]
    s, _ = box_list(s, stage_items, 60, 140, 700, 14, "#eef3fb", "#4a76b8", "#1a3a6b", "#8aa", 45)
    s += f'<text x="810" y="122" font-family="{FONT}" font-size="18" font-weight="bold" fill="#7a2b1a">风险与暂停事项——待核/暂停口径原样保留</text>'
    risk_items = [{"text": "　".join(c for c in r["cells"] if c), "anchor_ids": r["anchor_ids"]} for r in v["risks"]]
    s, _ = box_list(s, risk_items, 810, 140, 730, 13, "#fdf3ee", "#c47a5a", "#7a2b1a", "#c47a5a", 51)
    return s + "</svg>"

RENDER = {"01-主体关系图": render_01, "02-关键事件时间线": render_02,
          "03-要件证据矩阵": render_03, "04-阶段计划与风险": render_04}

def main():
    a = sys.argv[1:]
    root = Path(a[a.index("--root")+1] if "--root" in a else ".").resolve()
    n_svg = n_png = 0
    for cd in sorted((root/"cases").iterdir()):
        if not cd.is_dir(): continue
        cv = json.loads((cd/"case-views.json").read_text(encoding="utf-8"))
        spec = json.loads((cd/"view-spec.json").read_text(encoding="utf-8"))
        for vwc in spec["views"]:
            name = vwc["name"]
            svg = RENDER[name](cv, f"{cv['case_id']}｜{name}")
            if "…" in svg or re.search(r">[^<]*\|[^<]*<", svg):
                print(f"HOLD-VIS: 渲染层残留省略号或竖线语法:{cd.name}/{name}"); return 3
            svg_p = cd/vwc["svg"]; svg_p.write_text(svg, encoding="utf-8"); n_svg += 1
            png_p = cd/vwc["png"]
            r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--force-device-scale-factor=1",
                f"--screenshot={png_p}", f"--window-size={vwc['width']},{vwc['height']}",
                "--hide-scrollbars", f"file://{svg_p}"], capture_output=True, text=True, timeout=120)
            if r.returncode != 0 or not png_p.is_file():
                print(f"HOLD-VIS: PNG渲染失败:{png_p.name}"); return 3
            n_png += 1
        print(f"RENDER[{cd.name}]: 4svg+4png")
    if n_svg != 16 or n_png != 16: print(f"HOLD-VIS: 计数{n_svg}/{n_png}≠16"); return 3
    print(f"RENDERED: {n_svg} SVG + {n_png} PNG")
    return 0
if __name__ == "__main__": sys.exit(main())
