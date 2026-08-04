#!/usr/bin/env python3
"""案内诉讼可视化生成器（GPL-3.0）：单案冻结07 → 九节锚 → 四视图SVG。

用法: gen_case_views.py <冻结07目录> <case-views.json> <输出目录>
生成门(fail-closed)：冻结目录须含SHA256-MANIFEST.txt，逐项复算不匹配即exit(1)不生成。
case-views.json: {case, banner?, parties{nodes,edges}, timeline[], hard[2], matrix[], stages[], risks[]}
渲染PNG可用无头浏览器截图（按SVG尺寸开窗）。
"""
import sys, json, hashlib, re
from pathlib import Path

BANNER = "内部研究草稿 · 基于冻结办案底稿生成 · 法律结论待人工复核 · 禁止外发"
F = "Songti SC, STSong, serif"; FH = "Heiti SC, STHeiti, sans-serif"
C = {"green":"#2e7d32","yellow":"#f9a825","red":"#c62828","gray":"#757575",
     "blue":"#1565c0","ink":"#212121","line":"#9e9e9e","bg":"#ffffff","box":"#f5f5f5"}

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def svg_open(w,h,title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
      f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>',
      '<defs><marker id="arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
      f'<path d="M0,0 L10,4 L0,8 z" fill="{C["ink"]}"/></marker></defs>',
      f'<text x="{w/2}" y="46" font-family="{FH}" font-size="30" font-weight="bold" text-anchor="middle" fill="{C["ink"]}">{esc(title)}</text>',
      f'<text x="{w/2}" y="76" font-family="{F}" font-size="15" text-anchor="middle" fill="{C["gray"]}">{esc(BANNER)}</text>']

def node(x,y,w,h,name,role,color):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{C["box"]}" stroke="{color}" stroke-width="2.5"/>'
      f'<text x="{x+w/2}" y="{y+h/2-8}" font-family="{FH}" font-size="19" font-weight="bold" text-anchor="middle" fill="{C["ink"]}">{esc(name)}</text>'
      f'<text x="{x+w/2}" y="{y+h/2+18}" font-family="{F}" font-size="14" text-anchor="middle" fill="{C["gray"]}">{esc(role)}</text>')

def edge(x1,y1,x2,y2,label,color="#212121",dash="",lx=None,ly=None):
    lx = lx if lx is not None else (x1+x2)/2; ly = ly if ly is not None else (y1+y2)/2-8
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"{d} marker-end="url(#arr)"/>'
      f'<text x="{lx}" y="{ly}" font-family="{F}" font-size="14" text-anchor="middle" fill="{color}">{esc(label)}</text>')

def chip(x,y,text,color):
    w = 14*len(text)+22
    return (f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="13" fill="{color}" opacity="0.15"/>'
      f'<text x="{x+w/2}" y="{y+18}" font-family="{FH}" font-size="14" text-anchor="middle" fill="{color}">{esc(text)}</text>'), w

# ============ 视图1 主体关系 ============
def view_parties(case, d):
    W,H = 1500,860
    s = svg_open(W,H,f"{case}案 · 主体关系图")
    for n in d["nodes"]:
        s.append(node(*n["xy"], n["w"], n["h"], n["name"], n["role"], C[n["color"]]))
    for e in d["edges"]:
        s.append(edge(*e["p"], e["label"], C[e.get("color","ink")], e.get("dash",""), e.get("lx"), e.get("ly")))
    y = H-46
    for t,c in [("原被告","blue"),("非当事人","gray"),("待决策","yellow")]:
        ch,w = chip(60 if t=="原被告" else 0,0,t,C[c]); pass
    s.append(f'<text x="{W-30}" y="{H-24}" font-family="{F}" font-size="13" text-anchor="end" fill="{C["gray"]}">依据：冻结《诉讼案件办案方案工作底稿》第一、二节 · 证件号/账号一律略去</text>')
    s.append("</svg>")
    return "\n".join(s)

# ============ 视图2 时间线 ============
def view_timeline(case, events, hard):
    W = 1500; H = 300 + 130*len(events)
    s = svg_open(W,H,f"{case}案 · 关键事件时间线")
    x0 = 250; s.append(f'<line x1="{x0}" y1="120" x2="{x0}" y2="{H-140}" stroke="{C["line"]}" stroke-width="3"/>')
    y = 150
    for ev in events:
        col = C[ev.get("color","blue")]
        s.append(f'<circle cx="{x0}" cy="{y}" r="9" fill="{col}"/>')
        s.append(f'<text x="{x0-24}" y="{y+6}" font-family="{FH}" font-size="17" font-weight="bold" text-anchor="end" fill="{C["ink"]}">{esc(ev["date"])}</text>')
        s.append(f'<text x="{x0+30}" y="{y-2}" font-family="{FH}" font-size="17" font-weight="bold" fill="{col}">{esc(ev["title"])}</text>')
        s.append(f'<text x="{x0+30}" y="{y+24}" font-family="{F}" font-size="15" fill="{C["ink"]}">{esc(ev["desc"])}</text>')
        y += 130
    s.append(f'<rect x="150" y="{H-120}" width="{W-300}" height="64" rx="10" fill="{C["red"]}" opacity="0.09"/>')
    s.append(f'<text x="{W/2}" y="{H-95}" font-family="{FH}" font-size="18" font-weight="bold" text-anchor="middle" fill="{C["red"]}">{esc(hard[0])}</text>')
    s.append(f'<text x="{W/2}" y="{H-70}" font-family="{F}" font-size="15" text-anchor="middle" fill="{C["ink"]}">{esc(hard[1])}</text>')
    s.append(f'<text x="{W-30}" y="{H-24}" font-family="{F}" font-size="13" text-anchor="end" fill="{C["gray"]}">依据：冻结《诉讼案件办案方案工作底稿》第三、五节</text>')
    s.append("</svg>")
    return "\n".join(s)

# ============ 视图3 要件-证据矩阵 ============
def view_matrix(case, rows):
    W = 1500; rh = 62; H = 210 + rh*len(rows) + 80
    s = svg_open(W,H,f"{case}案 · 请求权要件-证据矩阵")
    cols = [("请求权要件",250),("正面证据",420),("缺口",330),("状态",200)]
    x = 60; y0 = 120
    s.append(f'<rect x="{x}" y="{y0}" width="{sum(c[1] for c in cols)}" height="44" fill="{C["box"]}" stroke="{C["line"]}"/>')
    cx = x
    for name,wd in cols:
        s.append(f'<text x="{cx+14}" y="{y0+29}" font-family="{FH}" font-size="17" font-weight="bold" fill="{C["ink"]}">{esc(name)}</text>')
        cx += wd
    y = y0+44
    for r in rows:
        s.append(f'<rect x="{x}" y="{y}" width="{sum(c[1] for c in cols)}" height="{rh}" fill="none" stroke="{C["line"]}"/>')
        cx = x
        for i,(val,wd) in enumerate(zip(r["cells"], [c[1] for c in cols])):
            if i == 3:
                col = C[r["color"]]
                ch_w = 14*len(val)+22
                s.append(f'<rect x="{cx+14}" y="{y+rh/2-14}" width="{ch_w}" height="28" rx="14" fill="{col}" opacity="0.16"/>')
                s.append(f'<text x="{cx+14+ch_w/2}" y="{y+rh/2+6}" font-family="{FH}" font-size="15" text-anchor="middle" fill="{col}">{esc(val)}</text>')
            else:
                lines = [val[j:j+ (wd//17)] for j in range(0,len(val), max(1,wd//17))][:2]
                for k,ln in enumerate(lines):
                    s.append(f'<text x="{cx+14}" y="{y+26+k*22}" font-family="{F}" font-size="15" fill="{C["ink"]}">{esc(ln)}</text>')
            cx += wd
        y += rh
    lx = 60
    for t,c in [("已核验","green"),("单一来源","yellow"),("存在冲突","red"),("缺失","gray")]:
        ch,w = chip(lx, y+22, t, C[c]); s.append(ch); lx += w+18
    s.append(f'<text x="{W-30}" y="{H-24}" font-family="{F}" font-size="13" text-anchor="end" fill="{C["gray"]}">依据：冻结《诉讼案件办案方案工作底稿》第六节 · 状态为底稿登记口径</text>')
    s.append("</svg>")
    return "\n".join(s)

# ============ 视图4 阶段计划与风险 ============
def view_plan(case, stages, risks):
    W = 1500; H = 300 + max(len(stages),len(risks))*74 + 60
    s = svg_open(W,H,f"{case}案 · 诉讼阶段计划与风险登记")
    s.append(f'<text x="90" y="122" font-family="{FH}" font-size="20" font-weight="bold" fill="{C["blue"]}">阶段计划</text>')
    y = 150
    for i,(name,act,ddl) in enumerate(stages):
        s.append(f'<rect x="70" y="{y}" width="620" height="60" rx="8" fill="{C["box"]}" stroke="{C["blue"]}" stroke-width="1.5"/>')
        s.append(f'<text x="90" y="{y+25}" font-family="{FH}" font-size="16" font-weight="bold" fill="{C["ink"]}">{esc(name)}</text>')
        s.append(f'<text x="90" y="{y+48}" font-family="{F}" font-size="14" fill="{C["ink"]}">{esc(act)}</text>')
        if ddl: s.append(f'<text x="672" y="{y+25}" font-family="{FH}" font-size="14" text-anchor="end" fill="{C["red"]}">{esc(ddl)}</text>')
        if i < len(stages)-1: s.append(f'<line x1="380" y1="{y+60}" x2="380" y2="{y+74}" stroke="{C["blue"]}" stroke-width="2" marker-end="url(#arr)"/>')
        y += 74
    s.append(f'<text x="790" y="122" font-family="{FH}" font-size="20" font-weight="bold" fill="{C["red"]}">风险登记</text>')
    y = 150
    for tag,txt,color in risks:
        col = C[color]
        s.append(f'<rect x="770" y="{y}" width="660" height="60" rx="8" fill="{col}" opacity="0.08"/>')
        s.append(f'<rect x="770" y="{y}" width="6" height="60" rx="3" fill="{col}"/>')
        s.append(f'<text x="792" y="{y+25}" font-family="{FH}" font-size="15" font-weight="bold" fill="{col}">{esc(tag)}</text>')
        s.append(f'<text x="792" y="{y+48}" font-family="{F}" font-size="14" fill="{C["ink"]}">{esc(txt)}</text>')
        y += 74
    s.append(f'<text x="{W-30}" y="{H-24}" font-family="{F}" font-size="13" text-anchor="end" fill="{C["gray"]}">依据：冻结《诉讼案件办案方案工作底稿》第八、九节</text>')
    s.append("</svg>")
    return "\n".join(s)


def verify_manifest(frozen: Path):
    man = frozen/"SHA256-MANIFEST.txt"
    if not man.is_file(): print("GATE-FAIL: manifest missing"); sys.exit(1)
    for ln in man.read_text(encoding="utf-8").strip().split("\n"):
        h, name = ln.split(None, 1)
        p = frozen/name.strip().lstrip("*")
        if not p.is_file(): print(f"GATE-FAIL: {name} missing"); sys.exit(1)
        if hashlib.sha256(p.read_bytes()).hexdigest() != h:
            print(f"GATE-FAIL: {name} hash mismatch"); sys.exit(1)
    print("GATE-PASS: 冻结07清单逐项复算通过")

def parse_anchors(md_text):
    marks = [(m.start(), m.group(1).strip()) for m in re.finditer(r'^## (第.节[　 ]*\S+.*)$', md_text, re.M)]
    out = []
    for i,(pos,title) in enumerate(marks):
        end = marks[i+1][0] if i+1 < len(marks) else len(md_text)
        out.append({"id": f"A{i+1:02d}", "title": title, "char_range": [pos, end],
                    "section_sha256": hashlib.sha256(md_text[pos:end].encode()).hexdigest()[:16]})
    return out

VIEW_ANCHOR_MAP = {"01-主体关系图":["A01","A02"],"02-关键事件时间线":["A03","A05"],
                   "03-要件证据矩阵":["A06"],"04-阶段计划与风险":["A08","A09"]}

def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(2)
    frozen, spec_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    verify_manifest(frozen)
    D = json.loads(spec_path.read_text(encoding="utf-8"))
    case = D["case"]
    if D.get("banner"):
        global BANNER; BANNER = D["banner"]
    mds = list(frozen.glob("*07*.md")) or list(frozen.glob("*.md"))
    if not mds: print("GATE-FAIL: 冻结目录无07 md"); sys.exit(1)
    md_text = mds[0].read_text(encoding="utf-8")
    anchors = parse_anchors(md_text)
    out.mkdir(parents=True, exist_ok=True)
    mtx = view_matrix(case, D["matrix"]).replace("状态为底稿登记口径", "状态为底稿登记口径 · 待复核=待人工法律复核")
    views = {"01-主体关系图": view_parties(case, D["parties"]),
             "02-关键事件时间线": view_timeline(case, D["timeline"], D["hard"]),
             "03-要件证据矩阵": mtx,
             "04-阶段计划与风险": view_plan(case, [tuple(s) for s in D["stages"]], [tuple(r) for r in D["risks"]])}
    spec = {"schema_version":"vis-four-view/2.1","frozen_manifest_verified":True,
            "frozen_md": mds[0].name, "frozen_md_sha256": hashlib.sha256(md_text.encode()).hexdigest(),
            "anchors": anchors, "view_anchor_map": VIEW_ANCHOR_MAP, "views":{}}
    for name, svg in views.items():
        p = out/f"{name}.svg"; p.write_text(svg, encoding="utf-8")
        spec["views"][name] = {"svg_sha256": hashlib.sha256(svg.encode()).hexdigest()[:16],
                               "anchors": VIEW_ANCHOR_MAP[name]}
    (out/"view-spec.json").write_text(json.dumps(spec,ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
    print(f"{case}: anchors={len(anchors)} views=4 -> {out}")

if __name__ == "__main__":
    main()
