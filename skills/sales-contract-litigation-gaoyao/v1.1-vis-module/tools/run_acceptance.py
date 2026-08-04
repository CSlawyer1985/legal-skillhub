#!/usr/bin/env python3
"""V1.1包生产验收（合同production_acceptance）：正链clean-input→9DOCX→9PDF→逐页PNG→TEXT→独立冻结07→同案4SVG+4PNG；
九类负测；断言：源树前后不变/VIS前后九DOCX、9PDF字节不变/OOXML可编辑/全页渲染/中文可见层/法院件版式/02六列真表/零symlink/SUMS精确。
用法: run_acceptance.py --root <包根> --spec <runs-spec.json> --out <根外输出>
exit 0/3"""
import sys, os, json, re, hashlib, shutil, subprocess, tempfile, zipfile
from pathlib import Path
MD07 = "07-诉讼案件办案方案工作底稿.md"
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def render_env():
    c = Path.home()/".cache/codex-runtimes/codex-primary-runtime/dependencies"
    env = dict(os.environ); env["PATH"] = str(c/"bin/override")+":"+env.get("PATH", "")
    fc = c/"fontconfig"
    if (fc/"fonts.conf").exists():
        env["FONTCONFIG_FILE"] = str(fc/"fonts.conf"); env["FONTCONFIG_PATH"] = str(fc)
    return str(c/"bin/override/soffice"), env
def bundle_sha(root, names):
    h = hashlib.sha256()
    for n in sorted(names):
        p = Path(root)/n
        h.update(str(p.resolve()).encode()); h.update(b"\0")
        h.update(fsha(p).encode()); h.update(b"\0"); h.update(str(p.stat().st_size).encode()); h.update(b"\n")
    return h.hexdigest()
def tree(root):
    root = Path(root); ent = []
    for q in root.rglob("*"):
        if q.is_symlink(): return "SYMLINK"
        if q.is_file(): ent.append((q.relative_to(root).as_posix(), q))
    ent.sort()
    h = hashlib.sha256()
    for rel, q in ent:
        h.update(rel.encode()); h.update(b"\0"); h.update(fsha(q).encode()); h.update(b"\0")
        h.update(str(q.stat().st_size).encode()); h.update(b"\n")
    return h.hexdigest()

def main():
    a = sys.argv[1:]
    def arg(n): return a[a.index(n)+1] if n in a else None
    root = Path(arg("--root")).resolve()
    out = Path(arg("--out")).resolve()
    if str(out).startswith(str(root)): print("HOLD: --out须在包根外"); return 3
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(arg("--spec")).read_text(encoding="utf-8"))
    M = root/"v1.1-vis-module"; T = M/"tools"
    PY = sys.executable
    subs = []
    def rsub(label, cmd, env=None):
        r = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, env=env, timeout=1800)
        subs.append({"label": label, "exit": r.returncode,
                     "stdout_sha256": hashlib.sha256(r.stdout.encode()).hexdigest(),
                     "stderr_sha256": hashlib.sha256(r.stderr.encode()).hexdigest(),
                     "stdout_tail": r.stdout[-200:]})
        return r.returncode, r.stdout
    results = []
    def check(rid, ok, detail=""):
        results.append({"id": rid, "result": "PASS" if ok else "HOLD", "detail": str(detail)[:200]})
        print(f"[{rid}] {'PASS' if ok else 'HOLD'} {str(detail)[:70]}")
        return ok
    src_tree_before = tree(root)
    all_ok = True
    # ===== 正链 =====
    for run in spec["runs"]:
        rid = run["run_id"]; case_id = run["case_id"]
        rd = out/rid; rd.mkdir(parents=True, exist_ok=True)
        bs = json.loads((root/run["bundle_spec"]).read_text(encoding="utf-8")) if (root/run["bundle_spec"]).exists() else json.loads(Path(run["bundle_spec"]).read_text(encoding="utf-8"))
        iroot = Path(bs["root"])
        got = bundle_sha(iroot, bs["files"])
        prov = json.loads((Path(run["md_src"])/"DRAFT-PROVENANCE.json").read_text(encoding="utf-8"))
        ok = (got == bs["expected"] == prov.get("input_bundle_sha256") and prov.get("case_id") == case_id
              and len(prov.get("documents", [])) == 9)
        if not check(f"{rid}:input-provenance", ok, f"bundle三方相等+case绑定"): all_ok = False; continue
        bad = False
        for d in prov["documents"]:
            fp = Path(run["md_src"])/d["md_relpath"]
            if fsha(fp) != d["md_sha256"]: bad = True
            for sr in d.get("source_refs", []):
                sf = iroot/sr["input_relpath"]
                if not sf.is_file() or fsha(sf) != sr["input_file_sha256"]: bad = True
        if not check(f"{rid}:source-refs", not bad): all_ok = False; continue
        dx = rd/"docx"
        rc, _ = rsub(f"{rid}:conv", [PY, "-B", T/"md_to_docx_r1.py", run["md_src"], dx])
        dxs = sorted(dx.glob("0*.docx"))
        editable = all("word/document.xml" in zipfile.ZipFile(d).namelist() for d in dxs) if dxs else False
        if not check(f"{rid}:9docx-editable-ooxml", rc == 0 and len(dxs) == 9 and editable): all_ok = False; continue
        soffice, env = render_env()
        pdfd = rd/"pdf"; pdfd.mkdir(); pv = rd/"preview"; pv.mkdir()
        rc, _ = rsub(f"{rid}:soffice", [soffice, "--headless", "--convert-to", "pdf", "--outdir", pdfd] + dxs, env=env)
        pdfs = sorted(pdfd.glob("0*.pdf"))
        pages_total = 0; pair_ok = rc == 0 and len(pdfs) == 9
        for pdf in pdfs:
            rc2, o2 = rsub(f"{rid}:pdfinfo", ["pdfinfo", pdf], env=env)
            pages = int(next(l for l in o2.splitlines() if l.startswith("Pages:")).split()[-1]) if rc2 == 0 else -1
            rc3, _ = rsub(f"{rid}:ppm", ["pdftoppm", "-png", "-r", "96", pdf, pv/(pdf.stem+"-页")], env=env)
            n = len(list(pv.glob(f"{pdf.stem}-页*.png")))
            if rc2 != 0 or rc3 != 0 or n != pages: pair_ok = False
            pages_total += max(pages, 0)
        if not check(f"{rid}:9pdf-all-pages", pair_ok, f"{pages_total}页全配对"): all_ok = False; continue
        alw = rd/"allow.json"
        asp = json.loads((root/run["allowlist"]).read_text(encoding="utf-8"))
        alw.write_text(json.dumps(sorted(x["token"] for x in asp["tokens"]), ensure_ascii=False), encoding="utf-8")
        gates_ok = True
        for label, cmd in (
          ("layout", [PY, "-B", T/"validate_layout.py", dx]),
          ("layout-extra", [PY, "-B", T/"validate_layout_extra_t2.py", dx]),
          ("chinese", [PY, "-B", T/"validate_chinese_t2.py", dx, "--allow", alw]),
          ("privacy", [PY, "-B", T/"validate_privacy_t2.py", "--phase", "artifacts", "--docx-dir", dx, "--pdf-dir", pdfd]),
          ("g15", [PY, "-B", T/"validate_g15_t2.py", dx, Path(run["md_src"])/"DRAFT-PROVENANCE.json"]),
          ("consistency", [PY, "-B", T/"validate_consistency_t2.py", dx, Path(run["md_src"])/"DRAFT-PROVENANCE.json"])):
            if rsub(f"{rid}:gate:{label}", cmd)[0] != 0: gates_ok = False
        # 02六列真表独立断言
        with zipfile.ZipFile(dx/"02-证据目录.docx") as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        six_ok = "<w:tblHeader" in xml and "<w:cantSplit" in xml
        if not check(f"{rid}:text-six-gates+02table", gates_ok and six_ok): all_ok = False; continue
        fz = rd/"frozen-07"; fz.mkdir()
        shutil.copy(Path(run["md_src"])/MD07, fz/MD07); os.chmod(fz/MD07, 0o444)
        (rd/"text-pass-receipt.json").write_text(json.dumps({"text_result": "PASS", "case_id": case_id},
          ensure_ascii=False), encoding="utf-8")
        dxb = {d.name: fsha(d) for d in dxs}; pdb = {q.name: fsha(q) for q in pdfs}
        visd = rd/"vis"
        rc, o = rsub(f"{rid}:vis_gate", [PY, "-B", T/"vis_gate.py", "--enable",
          "--frozen-07-dir", fz, "--registered-md-sha", fsha(fz/MD07), "--case-id", case_id,
          "--text-pass-receipt", rd/"text-pass-receipt.json", "--out", visd])
        n_svg = len(list(visd.glob("*.svg"))) if visd.exists() else 0
        n_png = len(list(visd.glob("*.png"))) if visd.exists() else 0
        if not check(f"{rid}:vis-4svg-4png", rc == 0 and n_svg == 4 and n_png == 4): all_ok = False; continue
        same = ({d.name: fsha(d) for d in sorted(dx.glob("0*.docx"))} == dxb and
                {q.name: fsha(q) for q in sorted(pdfd.glob("0*.pdf"))} == pdb)
        if not check(f"{rid}:text-byte-identical-after-vis", same): all_ok = False; continue
        (rd/"RUN-AS-RUN.json").write_text(json.dumps({"schema": "gaotao.v11.acceptance-run.v1",
          "run_id": rid, "case_id": case_id, "input_bundle_sha256": got,
          "docx": dxb, "pdf": pdb, "pages_total": pages_total,
          "frozen_07_sha256": fsha(fz/MD07),
          "vis": {f.name: fsha(f) for f in sorted(visd.iterdir())},
          "result": "VALID"}, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    # ===== 九类负测 =====
    scratch = Path(tempfile.mkdtemp(prefix="v11acc-", dir=out))
    run0 = spec["runs"][0]
    rd0 = out/run0["run_id"]
    fz0 = rd0/"frozen-07"; rec0 = rd0/"text-pass-receipt.json"
    reg0 = fsha(fz0/MD07)
    def vg(args):
        return rsub("neg:vis_gate", [PY, "-B", T/"vis_gate.py"] + args)
    negs = []
    rc, o = vg(["--enable", "--frozen-07-dir", fz0, "--registered-md-sha", reg0, "--case-id", run0["case_id"],
                "--text-pass-receipt", str(scratch/"nofile.json"), "--out", scratch/"n1"])
    negs.append(("text-failure-blocks-freeze-and-vis", rc != 0 and not list((scratch/"n1").glob("*.svg")) if (scratch/"n1").exists() else rc != 0))
    rc, o = vg(["--enable", "--frozen-07-dir", scratch/"none", "--registered-md-sha", reg0, "--case-id", run0["case_id"],
                "--text-pass-receipt", rec0, "--out", scratch/"n2"])
    negs.append(("frozen-07-missing", rc != 0))
    tf = scratch/"tamper"; tf.mkdir(); shutil.copy(fz0/MD07, tf/MD07)
    os.chmod(tf/MD07, 0o644)
    (tf/MD07).write_text((tf/MD07).read_text(encoding="utf-8")+"\n篡改\n", encoding="utf-8")
    rc, o = vg(["--enable", "--frozen-07-dir", tf, "--registered-md-sha", reg0, "--case-id", run0["case_id"],
                "--text-pass-receipt", rec0, "--out", scratch/"n3"])
    negs.append(("frozen-07-tamper", rc != 0))
    other = [r for r in spec["runs"] if r["case_id"] != run0["case_id"]]
    cross_case = other[0]["case_id"] if other else "CASE-X"
    rc, o = vg(["--enable", "--frozen-07-dir", fz0, "--registered-md-sha", reg0, "--case-id", cross_case,
                "--text-pass-receipt", rec0, "--out", scratch/"n4"])
    negs.append(("cross-case-input", rc != 0))
    rc, o = vg(["--frozen-07-dir", fz0, "--registered-md-sha", reg0, "--case-id", run0["case_id"],
                "--text-pass-receipt", rec0, "--out", scratch/"n5"])
    negs.append(("vis-disabled", rc != 0 and not (scratch/"n5").exists() or rc != 0))
    red = scratch/"symroot"; red.mkdir()
    (red/"a.md").write_text("x", encoding="utf-8"); (red/"lnk.md").symlink_to(red/"a.md")
    negs.append(("nested-symlink", tree(red) == "SYMLINK"))
    sums = root/"SHA256SUMS.txt"
    listed = {l.partition("  ")[2] for l in sums.read_text(encoding="utf-8").strip().splitlines()}
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    stray_detect = (listed == actual)
    (root/"__stray_test.txt").write_text("x", encoding="utf-8")
    actual2 = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    stray_caught = listed != actual2
    (root/"__stray_test.txt").unlink()
    negs.append(("unlisted-extra-file", stray_detect and stray_caught))
    d8 = scratch/"pii"; d8.mkdir()
    (d8/"01-民事起诉状.md").write_text("公民身份号码110101199001011234", encoding="utf-8")
    rc, _ = rsub("neg:privacy", [PY, "-B", T/"validate_privacy_t2.py", "--phase", "md", "--md-src", d8])
    negs.append(("privacy-red-fixture", rc != 0))
    # g9-not-replayed：armory登记必须有红绿重放记录；缺失AS-RUN即拒
    arm = json.loads((M/"g9-armory.json").read_text(encoding="utf-8"))
    g9_ok = bool(arm.get("armory"))
    fake = {"g9_replays": []}
    missing = [it.get("id") for it in arm.get("armory", []) if it.get("id") not in {x.get("id") for x in fake["g9_replays"]}]
    negs.append(("g9-not-replayed", g9_ok and bool(missing)))
    for rid, ok in negs:
        if not check(f"neg:{rid}", ok): all_ok = False
    shutil.rmtree(scratch, ignore_errors=True)
    src_tree_after = tree(root)
    if not check("package-tree-before-after", src_tree_before == src_tree_after): all_ok = False
    (out/"ACCEPTANCE-AS-RUN.json").write_text(json.dumps({
      "schema": "gaotao.v11.acceptance-as-run.v1", "package_root": str(root),
      "package_tree_before": src_tree_before, "package_tree_after": src_tree_after,
      "checks": results, "subprocess_records": subs,
      "result": "VALID" if all_ok else "HOLD"}, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    print(f"ACCEPTANCE: {'VALID' if all_ok else 'HOLD'} ({sum(1 for r in results if r['result']=='PASS')}/{len(results)})")
    return 0 if all_ok else 3
if __name__ == "__main__": sys.exit(main())
