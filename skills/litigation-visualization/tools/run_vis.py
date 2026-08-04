#!/usr/bin/env python3
"""诉讼可视化唯一公开runner（07-only硬门）。
用法: run_vis.py --enable-vis --case-id <ID> --frozen07-dir <目录> --text-pass-receipt <路径> --out <包外输出目录>
门（任一命中exit3零产物）：未显式--enable-vis｜TEXT-PASS收据缺失/非PASS/跨案｜冻结07缺失/哈希不符/跨案｜A01-A09锚集不全或失配。
唯一语义输入=同案冻结07文本＋A01-A09锚集；不读case-views.json或任何其他案件态。"""
import sys
sys.dont_write_bytecode = True  # 公开runner卫生门：普通python3调用亦不得向包树写回pyc缓存
import os, json, hashlib, subprocess, importlib.util
from pathlib import Path
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hold(m): print(f"HOLD-VIS: {m}"); return 3
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def main():
    a = sys.argv[1:]
    def arg(n): return a[a.index(n)+1] if n in a else None
    if "--enable-vis" not in a: return hold("VIS默认关闭：未显式--enable-vis（关闭态零产物）")
    case_id, f7d, tpr, out = arg("--case-id"), arg("--frozen07-dir"), arg("--text-pass-receipt"), arg("--out")
    if not all((case_id, f7d, tpr, out)): print(__doc__); return 2
    root = Path(__file__).resolve().parent.parent
    out = Path(out).resolve()
    if str(out).startswith(str(root)): return hold("--out须在包外")
    # TEXT PASS绑定
    tp = Path(tpr)
    if not tp.is_file(): return hold("TEXT-PASS收据缺失")
    tj = json.loads(tp.read_text(encoding="utf-8"))
    if tj.get("result") != "PASS": return hold("TEXT未过")
    if tj.get("case_id") != case_id: return hold(f"TEXT收据跨案:{tj.get('case_id')}≠{case_id}")
    # 冻结07门
    f7d = Path(f7d)
    mp = f7d/"FROZEN-07-MANIFEST.json"
    if not mp.is_file(): return hold("冻结07 manifest缺失")
    man = json.loads(mp.read_text(encoding="utf-8"))
    if man.get("case_id") != case_id: return hold(f"冻结07跨案:{man.get('case_id')}≠{case_id}")
    md = f7d/man["md_relpath"]
    if not md.is_file(): return hold("冻结07缺失")
    if fsha(md) != man["md_sha256"]: return hold("冻结07哈希不符")
    # 07-only构建（唯一语义输入=07文本）
    eng = root/"viz-engine"
    build_t4 = load("build_t4", eng/"mother-build_t4.py")
    render_t4 = load("render_t4", eng/"mother-render_t4.py")
    text = md.read_text(encoding="utf-8")
    cv, err = build_t4.build_case_views(text, case_id)
    if err: return hold(f"07解析失败:{err}")
    used = set()
    for _vn, _vd in cv["views"].items():
        for _k, _items in _vd.items():
            if _k == "anchor_ids" or not isinstance(_items, list): continue
            for _it in _items:
                if isinstance(_it, dict): used |= set(_it.get("anchor_ids", []))
    if used != {f"A{i:02d}" for i in range(1, 10)}:
        return hold(f"A01-A09锚集不全或失配（实得{len(used)}项）")
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for vname, fn in (("01-主体关系图", render_t4.render_01), ("02-关键事件时间线", render_t4.render_02),
                      ("03-要件证据矩阵", render_t4.render_03), ("04-阶段计划与风险", render_t4.render_04)):
        svg = fn(cv, f"{case_id}·{vname[3:]}")
        sp = out/f"{vname}.svg"; sp.write_text(svg, encoding="utf-8")
        pp = out/f"{vname}.png"
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", f"--screenshot={pp}",
             "--window-size=1600,900", "--hide-scrollbars", f"file://{sp}"], capture_output=True, timeout=120)
        if r.returncode != 0 or not pp.is_file(): return hold(f"{vname}PNG渲染失败")
        n += 1
    print(f"VALID: {case_id} 4SVG+4PNG（07-only·九锚精确集）"); return 0
if __name__ == "__main__": sys.exit(main())
