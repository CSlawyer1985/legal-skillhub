#!/usr/bin/env python3
"""V1.1 VIS门（默认关闭；合同child_package_requirements.vis_capability六类fail-closed）。
用法: vis_gate.py --frozen-07-dir <目录> --registered-md-sha <sha> --case-id <id> --out <根外目录> [--enable]
前提：TEXT PASS由包主链承担，本门要求--text-pass-receipt <文件> 登记其结果。
exit 0=生成4SVG+4PNG / 3=HOLD-VIS"""
import sys, os, json, re, hashlib, subprocess
from pathlib import Path
MD07 = "07-诉讼案件办案方案工作底稿.md"
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hold(m): print(f"HOLD-VIS: {m}"); return 3
def main():
    a = sys.argv[1:]
    def arg(n): return a[a.index(n)+1] if n in a else None
    if "--enable" not in a:
        return hold("VIS默认关闭（--enable缺失），拒绝生成任何视图")  # vis-disabled
    rcp = arg("--text-pass-receipt")
    if not rcp or not Path(rcp).is_file():
        return hold("缺TEXT PASS收据")  # text-failed
    rec = json.loads(Path(rcp).read_text(encoding="utf-8"))
    if rec.get("text_result") != "PASS":
        return hold("TEXT未通过，禁止VIS")  # text-failed
    fz = Path(arg("--frozen-07-dir") or "")
    f = fz/MD07
    if not f.is_file(): return hold("冻结07缺失")  # frozen-07-missing
    want = arg("--registered-md-sha") or ""
    if fsha(f) != want: return hold("冻结07哈希失配（篡改）")  # frozen-07-hash-mismatch
    case_id = arg("--case-id") or ""
    if rec.get("case_id") != case_id:
        return hold(f"跨案：收据case_id={rec.get('case_id')}≠{case_id}")  # cross-case
    out = Path(arg("--out") or "").resolve()
    pkg = Path(__file__).resolve().parent.parent.parent
    if str(out).startswith(str(pkg)): return hold("--out必须在包根外（禁写回）")
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_t4, render_t4
    text = f.read_text(encoding="utf-8")
    anchors, err = build_t4.extract_anchors(text)
    if err: return hold(f"锚集不全:{err}")  # anchor-set-incomplete
    cv, err = build_t4.build_case_views(text, case_id)
    if err: return hold(f"case-views失败:{err}")
    n = 0
    for vname, fn in (("01-主体关系图", render_t4.render_01), ("02-关键事件时间线", render_t4.render_02),
                      ("03-要件证据矩阵", render_t4.render_03), ("04-阶段计划与风险", render_t4.render_04)):
        svg = fn(cv, f"{case_id}｜{vname}")
        if "…" in svg or re.search(r">[^<]*\|[^<]*<", svg): return hold(f"{vname}可见层截断/竖线")
        sp = out/f"{vname}.svg"; sp.write_text(svg, encoding="utf-8")
        pp = out/f"{vname}.png"
        r = subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless",
            "--disable-gpu", f"--screenshot={pp}", "--window-size=1600,900", "--hide-scrollbars",
            f"file://{sp}"], capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not pp.is_file() or pp.stat().st_size < 15000:
            return hold(f"{vname}渲染失败/空白")
        n += 1
    (out/"VIS-AS-RUN.json").write_text(json.dumps({"schema": "gaotao.v11.vis-as-run.v1",
      "case_id": case_id, "frozen_md_sha256": want, "svg": 4, "png": 4,
      "write_back": False}, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    print(f"VIS-VALID[{case_id}]: 4SVG+4PNG（根外out，零写回）")
    return 0
if __name__ == "__main__": sys.exit(main())
