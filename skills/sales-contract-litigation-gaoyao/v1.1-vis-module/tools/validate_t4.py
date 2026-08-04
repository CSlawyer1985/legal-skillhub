#!/usr/bin/env python3
"""T4验收器（合同8644715d…）。
正例: validate_t4.py --root . --t3-root <T3根>
自测: validate_t4.py --root . --t3-root <T3根> --selftest
exit 0=VALID / 3=HOLD-VIS"""
import sys, os, json, re, struct, hashlib, shutil, subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

CONTRACT_SHA = "8644715d0a145b06ae9387939d9f850d4b8ca1c252eb67076c30fe12665feae2"
MD = "07-诉讼案件办案方案工作底稿.md"
ANCHOR_TITLES = ["第一节　主体与角色","第二节　合同与交易链","第三节　履行与交付链","第四节　款项与余额",
                 "第五节　通知抗辩与期间","第六节　要件-事实-证据矩阵","第七节　证据索引",
                 "第八节　诉讼阶段计划","第九节　风险与暂停事项"]
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hold(m): print(f"HOLD-VIS: {m}"); return 3
def t0_tree(root):
    root = Path(root); ent = []
    for q in root.rglob("*"):
        if q.is_symlink(): return None, -1
        if q.is_file(): ent.append((q.relative_to(root).as_posix(), q))
    ent.sort()
    return hashlib.sha256(("\n".join(f"{fsha(q)}\t{q.stat().st_size}\tfile\t{r}" for r, q in ent)+"\n").encode()).hexdigest(), len(ent)
def png_dims(p):
    b = Path(p).read_bytes()
    if b[:8] != b"\x89PNG\r\n\x1a\n": return None
    w, h = struct.unpack(">II", b[16:24])
    return w, h
def manifest_replay(root, name, want_sha, want_n):
    root = Path(root); mp = root/name
    if not mp.is_file() or fsha(mp) != want_sha: return f"{root.name}/{name}哈希失配"
    lines = mp.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) != want_n: return f"{root.name}清单条数{len(lines)}≠{want_n}"
    for line in lines:
        h, _, rel = line.partition("  ")
        p = root/rel
        if not p.is_file() or fsha(p) != h: return f"{root.name}树漂移:{rel}"
    return None
def recompute_anchors(text):
    idxs = []
    for title in ANCHOR_TITLES:
        m = re.search(rf"^## {re.escape(title)}$", text, re.M)
        if not m: return None
        idxs.append(m.start())
    out = []
    for i in range(9):
        s, e = idxs[i], (idxs[i+1] if i < 8 else len(text))
        out.append({"anchor_id": f"A{i+1:02d}", "char_start": s, "char_end": e,
                    "sha256": hashlib.sha256(text[s:e].encode("utf-8")).hexdigest()})
    return out
def source_state(contract, t3root):
    si = contract["source_invariants"]
    st = {}
    err = manifest_replay(si["t2"]["root"], si["t2"]["manifest"], si["t2"]["manifest_sha256"], si["t2"]["manifest_entry_count"])
    if err: return None, err
    tree, n = t0_tree(si["t2"]["root"])
    if tree != si["t2"]["tree_sha256"] or n != si["t2"]["regular_file_count"]: return None, "T2树失配"
    st["t2_tree_sha256"] = tree
    err = manifest_replay(si["t1"]["root"], si["t1"]["manifest"], si["t1"]["manifest_sha256"], si["t1"]["manifest_entry_count"])
    if err: return None, err
    st["t1_manifest_sha256"] = si["t1"]["manifest_sha256"]
    donors = {}
    for d in si["donors"]:
        tree, n = t0_tree(d["root"])
        if tree != d["tree_sha256"] or n != d["regular_file_count"]: return None, f"donor失配:{d['donor_id']}"
        donors[d["donor_id"]] = tree
    st["donor_tree_sha256"] = donors
    t3tree, _ = t0_tree(t3root)
    st["t3_tree_sha256"] = t3tree
    frozen = {}
    for c in contract["cases"]:
        fmd = Path(t3root)/c["frozen_content_dir"]/MD
        if not fmd.is_file() or fsha(fmd) != c["frozen_md_sha256"]: return None, f"冻结07失配:{c['run_id']}"
        frozen[c["run_id"]] = c["frozen_md_sha256"]
    st["frozen_md_sha256"] = frozen
    return st, None

PII_SVG = re.compile(r"(?<![\dA-Za-z])\d{17}[\dXx](?![\dA-Za-z])|(?<![\dA-Za-z])1[3-9]\d{9}(?![\dA-Za-z])"
                     r"|(?<![\dA-Za-z])\d{16,19}(?![\dA-Za-z])|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def validate(root, t3root):
    root, t3root = Path(root).resolve(), Path(t3root).resolve()
    cp = root/"contract/T4-VIS-ACCEPTANCE-CONTRACT.json"
    if not cp.is_file() or fsha(cp) != CONTRACT_SHA: return hold("T4合同副本缺失或哈希失配")
    contract = json.loads(cp.read_text(encoding="utf-8"))
    for q in root.rglob("*"):
        if q.is_symlink(): return hold(f"symlink:{q.relative_to(root)}")
    vm = contract["semantic_contract"]["view_anchor_map"]
    n_svg = n_png = 0
    for c in contract["cases"]:
        cd = root/c["output_dir"]
        cvp, vsp = cd/"case-views.json", cd/"view-spec.json"
        if not cvp.is_file() or not vsp.is_file(): return hold(f"缺case侧件:{c['run_id']}")
        cv = json.loads(cvp.read_text(encoding="utf-8"))
        vs = json.loads(vsp.read_text(encoding="utf-8"))
        if cv.get("schema") != "gaotao.t4.case-view-data.v1" or vs.get("schema") != "gaotao.t4.case-view-spec.v1":
            return hold(f"case侧件schema不符:{c['run_id']}")
        fmd = t3root/c["frozen_content_dir"]/MD
        if not fmd.is_file(): return hold(f"冻结07缺失:{c['run_id']}")
        if fsha(fmd) != c["frozen_md_sha256"]: return hold(f"冻结07篡改或跨案:{c['run_id']}")
        text = fmd.read_text(encoding="utf-8")
        want = recompute_anchors(text)
        if want is None: return hold(f"锚重算失败:{c['run_id']}")
        got = cv.get("anchors", [])
        if len(got) != 9: return hold(f"锚数≠9:{c['run_id']}")
        for w, g in zip(want, got):
            if not re.fullmatch(r"[0-9a-f]{64}", g.get("sha256", "")): return hold(f"锚hash非64hex:{c['run_id']}/{g.get('anchor_id')}")
            if (g["anchor_id"], g["char_start"], g["char_end"], g["sha256"]) != \
               (w["anchor_id"], w["char_start"], w["char_end"], w["sha256"]):
                return hold(f"锚区间/哈希失配:{c['run_id']}/{w['anchor_id']}")
        used = set()
        for vname, vdata in cv["views"].items():
            allowed = set(vm[vname])
            for key, items in vdata.items():
                if key == "anchor_ids": continue
                if not isinstance(items, list): continue
                for it in items:
                    aids = it.get("anchor_ids", [])
                    if not aids: return hold(f"datum未声明锚:{c['run_id']}/{vname}")
                    if not set(aids) <= allowed: return hold(f"datum锚越出视图映射:{c['run_id']}/{vname}:{aids}")
                    used |= set(aids)
        if used != {f"A{i:02d}" for i in range(1, 10)}:
            return hold(f"九锚未全被视图使用:{c['run_id']}:缺{sorted({f'A{i:02d}' for i in range(1,10)}-used)}")
        for vw in vs["views"]:
            svg_p, png_p = cd/vw["svg"], cd/vw["png"]
            if not svg_p.is_file() or not png_p.is_file(): return hold(f"缺视图文件:{c['run_id']}/{vw['name']}")
            try: ET.fromstring(svg_p.read_text(encoding="utf-8"))
            except ET.ParseError as e: return hold(f"SVG非良构XML:{vw['svg']}:{e}")
            svg_txt = svg_p.read_text(encoding="utf-8")
            m = re.search(r'width="(\d+)" height="(\d+)"', svg_txt)
            sw, sh = int(m.group(1)), int(m.group(2))
            dims = png_dims(png_p)
            if dims is None: return hold(f"PNG头损坏:{vw['png']}")
            if dims != (sw, sh): return hold(f"SVG/PNG尺寸不符:{vw['png']}:{dims}≠{(sw,sh)}")
            if dims[0] < 1200 or dims[1] < 600: return hold(f"PNG尺寸低于1200x600:{vw['png']}")
            if png_p.stat().st_size < 15000: return hold(f"PNG疑似空白:{vw['png']}")
            vis_text = " ".join(re.findall(r">([^<]+)<", svg_txt))
            if re.search(r"<local-source-redacted>", vis_text): return hold(f"SVG可见层含机器路径:{vw['svg']}")
            if PII_SVG.search(vis_text): return hold(f"SVG可见层含敏感样式:{vw['svg']}")
            # r1.1视觉窄修合同363b4fec：可见Markdown表格语法=0/省略号=0/断裂括号=0
            if "…" in vis_text or "..." in vis_text:
                return hold(f"可见层含省略号截断:{vw['svg']}")
            if "|" in vis_text or re.search(r"(?<![-—])---(?![-—])", vis_text):
                return hold(f"可见层含Markdown表格语法:{vw['svg']}")
            for run_txt in re.findall(r">([^<]+)<", svg_txt):
                if run_txt.count("（") != run_txt.count("）") and (run_txt.endswith("（") or run_txt.startswith("）")):
                    return hold(f"可见层疑似断裂切片:{vw['svg']}:{run_txt[:20]}")
            n_svg += 1; n_png += 1
    if n_svg != 16 or n_png != 16: return hold(f"视图计数{n_svg}/{n_png}≠16/16")
    # 风险视图法条未注入可见性
    for c in contract["cases"]:
        cv = json.loads((root/c["output_dir"]/"case-views.json").read_text(encoding="utf-8"))
        joined = json.dumps(cv["views"]["04-阶段计划与风险"], ensure_ascii=False)
        if "法条" not in joined and "法源" not in joined:
            return hold(f"风险视图未保留法条未注入提示:{c['run_id']}")
    # r1.1：CASE-003指定必见事实（合同case003_required_visible_facts）
    REQ003 = {"02-关键事件时间线.svg": ["3,421,701.65","3,271,701.65","双口径","对账核定"],
              "03-要件证据矩阵.svg": ["保证文件（待核）","四项未核·不入本次诉请","内部台账算术（C-003）","付款率59.0012%"]}
    cd003 = root/"cases/T2-E2E-SALES-CASE003"
    for fname, needs in REQ003.items():
        vis3 = " ".join(re.findall(r">([^<]+)<", (cd003/fname).read_text(encoding="utf-8")))
        for need in needs:
            if need not in vis3.replace(" ", ""):
                return hold(f"CASE-003必见事实缺失:{fname}:{need}")
    # 侧件
    man_p, ar_p, nr_p, qa_p = (root/"T4-VIS-MANIFEST.json", root/"T4-AS-RUN.json",
                               root/"T4-NEGATIVE-RECEIPTS.json", root/"T4-VISUAL-QA.json")
    for p, sc in ((man_p, "gaotao.t4.vis-manifest.v1"), (ar_p, "gaotao.t4.as-run.v1"),
                  (nr_p, "gaotao.t4.negative-receipts.v1")):
        if not p.is_file(): return hold(f"缺侧件:{p.name}")
        if json.loads(p.read_text(encoding='utf-8')).get("schema") != sc: return hold(f"{p.name} schema不符")
    if not qa_p.is_file(): return hold("缺T4-VISUAL-QA.json")
    qa = json.loads(qa_p.read_text(encoding="utf-8"))
    if len(qa.get("pages", [])) != 16: return hold("视觉QA未覆盖16 PNG")
    ar = json.loads(ar_p.read_text(encoding="utf-8"))
    if ar.get("t3_joint_pass_before_build", {}).get("codex") != "1785189597617-codex" or \
       ar.get("t3_joint_pass_before_build", {}).get("hermes") != "1785190117898-hermes":
        return hold("AS-RUN未登记T3双席PASS先于build")
    st, err = source_state(contract, t3root)
    if err: return hold(f"源不变量失败:{err}")
    for phase in ("before", "after"):
        if ar.get("source_invariants", {}).get(phase) != st:
            return hold(f"AS-RUN source_invariants[{phase}]与现场不符")
    if len(ar.get("per_case_io", [])) != 4: return hold("AS-RUN缺per_case输入输出哈希")
    nr = json.loads(nr_p.read_text(encoding="utf-8"))
    want_ids = contract["negative_receipts"]["exact_test_ids"]  # 基础合同精确ID（附录cb968900：修订合同N1…N5仅为selftest内部别名）
    if [r["test_id"] for r in nr["receipts"]] != want_ids: return hold("负测id集不符")
    for r in nr["receipts"]:
        for f in contract["negative_receipts"]["required_fields"]:
            if f not in r: return hold(f"负测{r['test_id']}缺字段{f}")
        if r["actual_exit"] == 0 or r["success_manifest_present"] or not r["source_roots_unchanged"]:
            return hold(f"负测{r['test_id']}语义不符")
        if r["output_tree_before"] != r["output_tree_after"]: return hold(f"负测{r['test_id']}输出残留")
    # SUMS精确集
    sums_p = root/"SHA256SUMS.txt"
    if not sums_p.is_file(): return hold("缺SHA256SUMS.txt")
    listed = {}
    for line in sums_p.read_text(encoding="utf-8").strip().splitlines():
        h, _, rel = line.partition("  ")
        listed[rel] = h
    actual = {str(p.relative_to(root)): p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    if set(listed) != set(actual): return hold("SUMS集不精确")
    for rel, h in listed.items():
        if fsha(actual[rel]) != h: return hold(f"SUMS哈希失配:{rel}")
    print("VALID: T4合同全门（锚/映射/16SVG+16PNG/尺寸/非空白/敏感扫描/侧件/不变量/负测/SUMS）")
    return 0

def selftest(root, t3root):
    root, t3root = Path(root).resolve(), Path(t3root).resolve()
    SC = Path("/private/tmp/claude-502/-Users-Zhuanz/32ee54cd-ecec-44b9-b231-905d9cf32c36/scratchpad/t4selftest")
    def clean(p):
        if p.exists():
            for q in p.rglob("*"):
                try: os.chmod(q, 0o755 if q.is_dir() else 0o644)
                except OSError: pass
            shutil.rmtree(p, ignore_errors=True)
    clean(SC); SC.mkdir(parents=True)
    def t3copy(name):
        dst = SC/name
        shutil.copytree(t3root, dst)
        for q in dst.rglob("*"): os.chmod(q, 0o755 if q.is_dir() else 0o644)
        return dst
    def build(t3, extra=None, out=None):
        out = out or SC/"out"
        clean(out); shutil.copytree(root/"contract", out/"contract")
        shutil.copytree(root/"tools", out/"tools")
        cmd = [sys.executable, "-B", str(out/"tools/build_t4.py"), "--root", str(out), "--t3-root", str(t3)]
        if extra != "no-vis": cmd.append("--vis-enabled")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        ok = r.returncode != 0 and "HOLD-VIS" in r.stdout
        clean(out)
        return ok, r
    results = []
    d = t3copy("N1"); ar = d/"T3-AS-RUN.json"
    j = json.loads(ar.read_text(encoding="utf-8")); j["result"] = "REVISE"
    ar.write_text(json.dumps(j, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    ok, _ = build(d); results.append(("N1-TEXT-GATE-FAIL", ok)); clean(d)
    d = t3copy("N2"); os.remove(d/"frozen-07/T2-E2E-SALES-CASE003"/MD)
    ok, _ = build(d); results.append(("N2-MISSING-FROZEN-07", ok)); clean(d)
    d = t3copy("N3"); f = d/"frozen-07/T2-E2E-SALES-CASE003"/MD
    f.write_text(f.read_text(encoding="utf-8") + "\n篡改\n", encoding="utf-8")
    ok, _ = build(d); results.append(("N3-TAMPERED-FROZEN-07", ok)); clean(d)
    d = t3copy("N4")
    a = d/"frozen-07/T2-E2E-FL-OPEN-DIRECT-CASE01"/MD; b = d/"frozen-07/T2-E2E-FL-SUB-DIRECT-CASE01"/MD
    tmp = d/"swap.tmp"; shutil.move(a, tmp); shutil.move(b, a); shutil.move(tmp, b)
    ok, _ = build(d); results.append(("N4-CROSS-CASE-INPUT", ok)); clean(d)
    ok, _ = build(t3root, extra="no-vis"); results.append(("N5-VIS-DISABLED", ok))
    # r1.1新增三条G9红样（合同363b4fec new_g9_regressions）：对临时T4副本注入缺陷→本验收器须非零HOLD-VIS
    def t4copy(name):
        dst = SC/name
        shutil.copytree(root, dst, ignore=shutil.ignore_patterns("*.png"))
        # PNG不复制（体积），改为复制后逐个占位重链？——G9只动SVG/case-views，PNG需在场：全量复制
        shutil.rmtree(dst); shutil.copytree(root, dst)
        for qq in dst.rglob("*"): os.chmod(qq, 0o755 if qq.is_dir() else 0o644)
        return dst
    def run_validator(dst):
        r = subprocess.run([sys.executable, "-B", str(dst/"tools/validate_t4.py"), "--root", str(dst),
                            "--t3-root", str(t3root)], capture_output=True, text=True, timeout=900)
        return r.returncode != 0 and "HOLD-VIS" in r.stdout
    import re as _rg
    d = t4copy("G9A")
    f = d/"cases/T2-E2E-SALES-CASE003/03-要件证据矩阵.svg"
    f.write_text(f.read_text(encoding="utf-8").replace("要件矩阵（A06）", "| 口径 | 算式 | 余额（元） | 状态 |", 1), encoding="utf-8")
    results.append(("G9-VIS-RAW-MARKDOWN-TABLE-AS-FACT", run_validator(d))); clean(d)
    d = t4copy("G9B")
    f = d/"cases/T2-E2E-SALES-CASE003/02-关键事件时间线.svg"
    f.write_text(f.read_text(encoding="utf-8").replace("3,421,701.65", "3,421,7…", 1), encoding="utf-8")
    results.append(("G9-VIS-DECISIVE-TEXT-TRUNCATED", run_validator(d))); clean(d)
    d = t4copy("G9C")
    f = d/"cases/T2-E2E-SALES-CASE003/02-关键事件时间线.svg"
    f.write_text(_rg.sub(r"3,271,701\.65", "", f.read_text(encoding="utf-8")), encoding="utf-8")
    results.append(("G9-VIS-CASE003-A04-FACTS-MISSING", run_validator(d))); clean(d)
    clean(SC)
    allok = all(ok for _, ok in results)
    for tid, ok in results: print(f"[{tid}] {'OK' if ok else 'FAIL'}")
    print("SELFTEST", f"{sum(ok for _, ok in results)}/{len(results)} OK" if allok else "FAIL")
    return 0 if allok else 3

def main():
    a = sys.argv[1:]
    root = a[a.index("--root")+1] if "--root" in a else "."
    t3root = a[a.index("--t3-root")+1] if "--t3-root" in a else ""
    if "--selftest" in a: return selftest(root, t3root)
    return validate(root, t3root)
if __name__ == "__main__": sys.exit(main())
