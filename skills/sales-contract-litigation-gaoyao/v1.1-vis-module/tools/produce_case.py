#!/usr/bin/env python3
"""T2 production runner（合同v1.0=71565b84 + v1.1=56c63ba7）：真实clean input→九DOCX→九PDF→全页PNG。

用法: produce_case.py --run-id <ID> --adapter <financial-lease|sales-contract>
      --donor-profile <文本> --input-root <clean input目录> --expected-bundle <sha256>
      --md-src <该案盲稿md目录> --candidate-root <T1 r1.3根> --out <新空输出目录>
      [--route-signals <signals.json>] [--expected-route <base>]

门（fail-closed，任一非零即停且不产出成功manifest）：
- 输入禁fixture解析（templates/example/T1输出/既往T2输出）→ HOLD-TEXT-E2E
- 输入bundle哈希现场复算==expected（算法=abs-path+NUL+sha256-file+NUL+size+LF/sorted-posix/v1）
- 输出目录必须全新为空；旧产物复用禁止
- converter/soffice/pdftoppm每个子进程退出码检查
- 恰9 DOCX+9 PDF+PNG页数配对；frozen07=0/VIS=0
- 输入/candidate树前后逐字节不变
- r1新增：md-src强制绑定T2/drafts+DRAFT-PROVENANCE逐件哈希；md/DOCX可见层隐私门（身份证/手机号样式）；
  G1.5勾稽门（关键金额见于01/05/06/07、当事人见于01、07九节齐、法院件无横幅）；
  --donor-root强制+donor树前后不变；md-src/input全树禁symlink；pdfinfo经run_sub入册；
  必要英文白名单窄化（仅≤6位全大写缩写+模板BASE集）。
- AS-RUN登记合同要求的全部字段。
"""
import sys, os, json, hashlib, subprocess, shutil
from pathlib import Path

def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bundle_sha(root, names):
    """合同算法：abs-path+NUL+sha256-file+NUL+size+LF / sorted-posix（仅合同清单文件）。"""
    root = Path(root).resolve()
    files = sorted((root/n for n in names), key=lambda p: str(p))
    dd = hashlib.sha256()
    for p in files:
        if not p.is_file(): return None, 0
        b = p.read_bytes()
        dd.update(str(p).encode()+b"\0"+hashlib.sha256(b).hexdigest().encode()+b"\0"+str(len(b)).encode()+b"\n")
    return dd.hexdigest(), len(files)

def tree_sha(root):
    root = Path(root)
    files = sorted((p for p in root.rglob("*") if p.is_file() and not p.is_symlink()), key=lambda p: p.relative_to(root).as_posix())
    dd = hashlib.sha256()
    for p in files:
        b = p.read_bytes()
        dd.update(p.relative_to(root).as_posix().encode()+b"\0"+hashlib.sha256(b).hexdigest().encode()+b"\0"+str(len(b)).encode()+b"\n")
    return dd.hexdigest()

def env_render():
    c = Path.home()/".cache/codex-runtimes/codex-primary-runtime/dependencies"
    s = c/"bin/override/soffice"
    if not s.is_file(): return None, {}
    e = dict(os.environ)
    fc = c/"native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fontconfig"
    e.update({"FONTCONFIG_FILE": str(fc/"fonts.conf"), "FONTCONFIG_PATH": str(fc),
              "PATH": str(c/"bin/override")+":"+e.get("PATH","")})
    return str(s), e

NINE = ["01-民事起诉状","02-证据目录","03-合同审查方案","04-材料缺失清单","05-代理词",
        "06-法律意见书","07-诉讼案件办案方案工作底稿","08-质证预案","09-条件性正式质证意见生成门"]
FIXTURE_MARKERS = ["合成示例","合成演示","本节为合成示例最小内容",
                   "甲融资租赁有限公司诉乙建设工程有限公司","甲机械制造股份有限公司诉丙工程有限公司"]

def main():
    a = sys.argv[1:]
    def arg(name, default=None):
        return a[a.index(name)+1] if name in a else default
    run_id = arg("--run-id"); adapter = arg("--adapter"); donor = arg("--donor-profile")
    input_root = Path(arg("--input-root")).resolve()
    expected_bundle = arg("--expected-bundle")
    md_src = Path(arg("--md-src")).resolve()
    cand = Path(arg("--candidate-root")).resolve()
    out = Path(arg("--out")).resolve()
    route_expected = arg("--expected-route")
    route_signals = arg("--route-signals")
    if not all([run_id, adapter, donor, expected_bundle]):
        print(__doc__); return 2
    subs = []
    logdir_holder = {}
    def run_sub(args2, label, env=None):
        r = subprocess.run([str(x) for x in args2], capture_output=True, text=True, env=env, timeout=900)
        ent = {"label": label, "cmd": [str(x) for x in args2], "exit": r.returncode,
               "stdout_tail": r.stdout[-2000:], "stderr_tail": r.stderr[-1000:],
               "stdout_sha256": hashlib.sha256(r.stdout.encode()).hexdigest(),
               "stderr_sha256": hashlib.sha256(r.stderr.encode()).hexdigest(),
               "stdout_bytes": len(r.stdout.encode()), "stderr_bytes": len(r.stderr.encode())}
        ld = logdir_holder.get("dir")
        if ld:
            i = len(subs)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:40]
            so = ld/f"{i:02d}-{safe}.out"; se = ld/f"{i:02d}-{safe}.err"
            so.write_text(r.stdout, encoding="utf-8"); se.write_text(r.stderr, encoding="utf-8")
            os.chmod(so, 0o444); os.chmod(se, 0o444)
            ent["stdout_log"] = str(so.relative_to(ld.parent)); ent["stderr_log"] = str(se.relative_to(ld.parent))
        subs.append(ent)
        return r.returncode
    gates_log = []
    def gate_ok(name): gates_log.append({"gate": name, "result": "ok"})
    # ① 输入禁fixture解析
    ir = str(input_root)
    for bad in ["templates", "example/盲稿md", "gaotao-adapter-T1-runtime", "gaotao-T2-production", "gaotao-T2-r1-production", "gaotao-T2-r1.1-production", "gaotao-T2-r1.2-production"]:
        if bad in ir:
            print(f"HOLD-TEXT-E2E: 输入解析到禁用来源（{bad}）"); return 3
    if not input_root.is_dir():
        print("HOLD-TEXT-E2E: 输入目录不存在"); return 3
    # ② bundle哈希现场复算（合同清单文件集）
    spec = arg("--bundle-spec")
    names = json.loads(Path(spec).read_text(encoding="utf-8"))["files"] if spec else [p.name for p in input_root.iterdir() if p.is_file()]
    got_bundle, n_in = bundle_sha(input_root, names)
    if got_bundle is None:
        print("HOLD-TEXT-E2E: bundle清单文件缺失"); return 3
    if got_bundle != expected_bundle:
        print(f"HOLD-TEXT-E2E: 输入bundle哈希失配 {got_bundle[:16]}≠{expected_bundle[:16]}"); return 3
    gate_ok("input-bundle-recompute")
    input_tree_pre = tree_sha(input_root)
    for q in cand.rglob("*"):
        if q.is_symlink(): print(f"HOLD-ENTITY: candidate后代symlink:{q.relative_to(cand)}"); return 3
    gate_ok("candidate-symlink-sweep-pre")
    cand_tree_pre = tree_sha(cand)
    # ③ 输出必须全新为空
    if out.exists() and any(out.iterdir()):
        print("HOLD-TEXT-E2E: 输出目录非空（禁旧产物复用）"); return 3
    out.mkdir(parents=True, exist_ok=True)
    (out/"logs").mkdir(exist_ok=True)
    logdir_holder["dir"] = out/"logs"
    # ④ 路由编译（FL）
    route_result = None
    if route_signals:
        rc = run_sub([sys.executable, "-B", cand/"adapters/financial-lease/tools/route_compile.py", route_signals], "route_compile")
        if rc != 0: print("HOLD-TEXT-E2E: 路由编译失败"); return 3
        route_result = json.loads(subs[-1]["stdout_tail"].strip().splitlines()[-1])
        if route_expected and route_result.get("base_route") != route_expected:
            print(f"HOLD-TEXT-E2E: 路由{route_result.get('base_route')}≠期望{route_expected}"); return 3
        gate_ok("route-compile")
    # ⑤ 盲稿md齐备且非fixture
    mds = sorted(md_src.glob("0*.md"))
    if [m.stem for m in mds] != NINE:
        print(f"HOLD-TEXT-E2E: 盲稿九件不齐: {[m.stem for m in mds]}"); return 3
    for m in mds:
        t = m.read_text(encoding="utf-8", errors="ignore")
        for mk in FIXTURE_MARKERS:
            if mk in t: print(f"HOLD-TEXT-E2E: {m.name}含fixture标记『{mk}』"); return 3
    gate_ok("fixture-marker-scan")
    # ⑤b md-src绑定：必须位于T2根drafts下且与PROVENANCE哈希逐件一致；全链禁symlink
    t2root = Path(__file__).resolve().parent.parent
    if not str(md_src).startswith(str(t2root/"drafts")):
        print("HOLD-TEXT-E2E: md-src必须位于T2根drafts下"); return 3
    for q in list(md_src.rglob("*")) + list(input_root.rglob("*")):
        if q.is_symlink(): print(f"HOLD-TEXT-E2E: symlink禁用:{q}"); return 3
    provp = md_src/"DRAFT-PROVENANCE.json"
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_provenance_t2.py",
                  md_src, input_root, cand/"adapters"/adapter, expected_bundle], "gate:validate_provenance")
    if rc != 0: print(f"HOLD-PROVENANCE: provenance validator exit={rc}"); return 3
    prov = json.loads(provp.read_text(encoding="utf-8"))
    gate_ok("provenance-v2-binding-subprocess")
    # ⑤c 隐私门（md层，独立子进程）
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_privacy_t2.py", "--phase", "md", "--md-src", md_src], "gate:validate_privacy_md")
    if rc != 0: print(f"HOLD-PRIVACY: privacy(md) validator exit={rc}"); return 3
    gate_ok("privacy-md-subprocess")
    # ⑤d donor绑定（修订合同65b3da22：expected_donors登记表+t0树算法，自由文本不得替代）
    # donor注册表：树哈希/计数取自spec文件（sha入册供复核==合同expected_donors）；
    # 根路径白名单硬编码——spec不可能把donor指向合同外路径
    ALLOWED_DONOR_ROOTS = {
      "financial-lease-direct-geo-v1.0.1": "<local-source-redacted>",
      "financial-lease-subscription-v1.0": "<local-source-redacted>",
      "sales-contract-litigation-v1.0.1": "<local-source-redacted>",
    }
    donors_spec_p = Path(arg("--donors-spec", str(Path(__file__).resolve().parent/"expected-donors.json")))
    if not donors_spec_p.is_file(): print("HOLD-DONOR-BINDING: donors注册表缺失"); return 3
    _dreg = json.loads(donors_spec_p.read_text(encoding="utf-8"))
    EXPECTED_DONORS = {k: {"root": v["root"], "tree": v["tree"], "count": v["count"]}
                       for k, v in _dreg.get("donors", {}).items()}
    for k, v in EXPECTED_DONORS.items():
        if ALLOWED_DONOR_ROOTS.get(k) != v["root"]:
            print(f"HOLD-DONOR-BINDING: donors注册表root越出合同白名单:{k}"); return 3
    def t0_tree(root):
        root = Path(root); ent = []
        for q in root.rglob("*"):
            if q.is_symlink():
                return None, -1  # donor后代symlink拒绝
            if q.is_file():
                ent.append((q.relative_to(root).as_posix(), q))
        ent.sort()  # 按相对posix路径排序（合同算法实测口径）
        lines = [f"{fsha(q)}\t{q.stat().st_size}\tfile\t{rel}" for rel, q in ent]
        return hashlib.sha256(("\n".join(lines)+"\n").encode()).hexdigest(), len(ent)
    donor_id = arg("--donor-id")
    if donor_id not in EXPECTED_DONORS:
        print(f"HOLD-DONOR-BINDING: --donor-id必须为合同登记donor之一，得到{donor_id}"); return 3
    dspec = EXPECTED_DONORS[donor_id]
    donor_root = Path(dspec["root"])
    if not donor_root.is_dir(): print("HOLD-DONOR-BINDING: donor根不存在"); return 3
    donor_tree_pre, donor_n = t0_tree(donor_root)
    if donor_tree_pre is None: print("HOLD-DONOR-BINDING: donor树含symlink"); return 3
    if donor_tree_pre != dspec["tree"] or donor_n != dspec["count"]:
        print(f"HOLD-DONOR-BINDING: donor树失配:{donor_id} {donor_tree_pre[:16]}≠{dspec['tree'][:16]} n={donor_n}"); return 3
    gate_ok("donor-contract-binding-pre")
    # ⑥ 转换（converter子进程+退出码）
    docx_dir = out/"docx"; docx_dir.mkdir()
    conv = Path(__file__).resolve().parent/"md_to_docx_r1.py"  # r1副本：全表禁拆+续页表头
    rc = run_sub([sys.executable, "-B", conv, md_src, docx_dir], "converter")
    if rc != 0: print(f"HOLD-TEXT-E2E: converter exit={rc}"); return 3
    docx = sorted(docx_dir.glob("0*.docx"))
    if len(docx) != 9: print(f"HOLD-TEXT-E2E: DOCX={len(docx)}≠9"); return 3
    # ⑥b 版式门（candidate原门）+中文门（T2版：输入派生必要英文白名单，合同『无必要英文』口径）
    rc = run_sub([sys.executable, "-B", cand/"adapters"/adapter/"tools/validate_layout.py", docx_dir], "gate:validate_layout")
    if rc != 0: print(f"HOLD-TEXT-E2E: layout exit={rc}"); return 3
    gate_ok("layout-ooxml")
    # r1.1显式窄白名单：tools/necessary-english-<case>.json，逐token复核确在clean input实体中
    allow_spec_p = Path(__file__).resolve().parent/f"necessary-english-{prov['case_id']}.json"
    if not allow_spec_p.is_file(): print("HOLD-TEXT-E2E: 显式必要英文白名单缺失"); return 3
    _aspec = json.loads(allow_spec_p.read_text(encoding="utf-8"))
    _input_body = ""
    for fp in sorted(input_root.rglob("*")):
        if fp.is_file() and fp.suffix.lower() in (".json", ".md", ".txt"):
            _input_body += fp.read_text(encoding="utf-8", errors="ignore")
    tokens = set()
    for row in _aspec["tokens"]:
        if row["token"] not in _input_body:
            print(f"HOLD-TEXT-E2E: 白名单token『{row['token']}』未见于clean input实体"); return 3
        tokens.add(row["token"])
    allow_p = out/"necessary-english-allowlist.json"
    allow_p.write_text(json.dumps(sorted(tokens), ensure_ascii=False), encoding="utf-8")
    gate_ok("explicit-narrow-english-allowlist")
    t2gate = Path(__file__).resolve().parent/"validate_chinese_t2.py"
    rc = run_sub([sys.executable, "-B", t2gate, docx_dir, "--allow", allow_p], "gate:validate_chinese_t2")
    if rc != 0: print(f"HOLD-TEXT-E2E: chinese_t2 exit={rc}"); return 3
    gate_ok("chinese-visible-text")
    # ⑥c 产物必须区别于模板与T1 fixture
    tpl_hashes = {fsha(p) for p in (cand/"adapters"/adapter/"templates/markdown").glob("0*.md")}
    t1_hashes = {fsha(p) for p in (cand/"adapters"/adapter/"e2e/docx").glob("0*.docx")}
    for dx in docx:
        if fsha(dx) in t1_hashes: print(f"HOLD-TEXT-E2E: {dx.name}与T1 fixture字节重合"); return 3
    for m in mds:
        if fsha(m) in tpl_hashes: print(f"HOLD-TEXT-E2E: {m.name}与模板字节重合"); return 3
    gate_ok("template-t1-byte-distinction")
    # ⑦ PDF（soffice退出码+计数）
    soffice, renv = env_render()
    if not soffice: print("HOLD-TEXT-E2E: 渲染链缺失"); return 3
    pdf_dir = out/"pdf"; pdf_dir.mkdir()
    rc = run_sub([soffice, "--headless", "--convert-to", "pdf", "--outdir", pdf_dir] + list(docx), "soffice", env=renv)
    if rc != 0: print(f"HOLD-TEXT-E2E: soffice exit={rc}"); return 3
    pdfs = sorted(pdf_dir.glob("0*.pdf"))
    if len(pdfs) != 9: print(f"HOLD-TEXT-E2E: PDF={len(pdfs)}≠9"); return 3
    # ⑧ PNG逐页（pdftoppm退出码+配对）
    pv = out/"preview"; pv.mkdir()
    pairing = []
    for pdf in pdfs:
        rc = run_sub(["pdftoppm", "-png", "-r", "110", pdf, pv/(pdf.stem+"-页")], f"pdftoppm:{pdf.stem}", env=renv)
        if rc != 0: print(f"HOLD-TEXT-E2E: pdftoppm exit={rc} {pdf.stem}"); return 3
        rc = run_sub(["pdfinfo", pdf], f"pdfinfo:{pdf.stem}", env=renv)
        if rc != 0: print(f"HOLD-TEXT-E2E: pdfinfo exit={rc}"); return 3
        info = subs[-1]["stdout_tail"]
        pages = int(next(l for l in info.splitlines() if l.startswith("Pages:")).split()[-1])
        pngs = sorted(pv.glob(f"{pdf.stem}-页-*.png"))
        if len(pngs) != pages: print(f"HOLD-TEXT-E2E: {pdf.stem} 页数{pages}≠PNG{len(pngs)}"); return 3
        if any(p.stat().st_size < 8192 for p in pngs): print(f"HOLD-TEXT-E2E: {pdf.stem}疑似空白页"); return 3
        pairing.append({"doc": pdf.stem, "docx_sha256": fsha(docx_dir/(pdf.stem+".docx")),
                        "pdf_sha256": fsha(pdf), "pages": pages,
                        "png_sha256": [fsha(p) for p in pngs]})
    # ⑧b 隐私门（artifacts相，独立子进程：DOCX全XML+.rels+可见机器词+PDF文本层）
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_privacy_t2.py", "--phase", "artifacts",
                  "--docx-dir", docx_dir, "--pdf-dir", pdf_dir], "gate:validate_privacy_artifacts")
    if rc != 0: print(f"HOLD-PRIVACY: privacy(artifacts) validator exit={rc}"); return 3
    gate_ok("privacy-artifacts-subprocess")
    # ⑧b2 表格版式（独立子进程）
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_layout_extra_t2.py", docx_dir], "gate:validate_layout_extra")
    if rc != 0: print(f"HOLD-LAYOUT: layout-extra validator exit={rc}"); return 3
    gate_ok("table-layout-subprocess")
    # ⑧b3 跨文书一致性/语义边界（独立子进程）
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_consistency_t2.py", docx_dir, provp], "gate:validate_consistency")
    if rc != 0: print(f"HOLD-DRAFTING: consistency validator exit={rc}"); return 3
    gate_ok("consistency-subprocess")
    # ⑧c G1.5起草合同勾稽（独立子进程）
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_g15_t2.py", docx_dir, provp], "gate:validate_g15")
    if rc != 0: print(f"HOLD-DRAFTING: g15 validator exit={rc}"); return 3
    gate_ok("g15-subprocess")
    # ⑨ frozen07=0/VIS=0
    bad = list(out.rglob("*.svg")) + list(out.rglob("view-spec.json")) + [p for p in out.rglob("*frozen*") if p.is_dir()]
    if bad: print(f"HOLD-TEXT-E2E: 禁产物存在{bad[:2]}"); return 3
    # ⑩ 输入/candidate前后不变
    if tree_sha(input_root) != input_tree_pre: print("HOLD-TEXT-E2E: 输入树漂移"); return 3
    for q in cand.rglob("*"):
        if q.is_symlink(): print(f"HOLD-ENTITY: candidate后代symlink(post):{q.relative_to(cand)}"); return 3
    gate_ok("candidate-symlink-sweep-post")
    cand_tree_post = tree_sha(cand)
    if cand_tree_post != cand_tree_pre: print("HOLD-TEXT-E2E: candidate树漂移"); return 3
    input_tree_post = tree_sha(input_root)
    if input_tree_post != input_tree_pre: print("HOLD-TEXT-E2E: 输入树漂移"); return 3
    for q in out.rglob("*"):
        if q.is_symlink(): print(f"HOLD-TEXT-E2E: 输出树含symlink:{q}"); return 3
    gate_ok("symlink-sweep-output")
    donor_tree_post, _dn2 = t0_tree(donor_root)
    if donor_tree_post != donor_tree_pre:
        print("HOLD-DONOR-BINDING: donor树漂移"); return 3
    gate_ok("donor-contract-binding-post"); gate_ok("input-candidate-tree-unchanged")
    # 收尾sidecar全域隐私复扫（独立子进程；排除尚未生成的RUN-AS-RUN.json）
    rc = run_sub([sys.executable, "-B", Path(__file__).resolve().parent/"validate_privacy_t2.py", "--phase", "sidecar",
                  "--out-root", out], "gate:validate_privacy_sidecar")
    if rc != 0: print(f"HOLD-PRIVACY: privacy(sidecar) validator exit={rc}"); return 3
    gate_ok("privacy-sidecar-subprocess")
    import re as _re9
    _PII9 = _re9.compile(r"(?<![\dA-Za-z])\d{17}[\dXx](?![\dA-Za-z])|(?<![\dA-Za-z])1[3-9]\d{9}(?![\dA-Za-z])")
    # 输出精确普通文件manifest
    out_manifest = [{"relpath": q.relative_to(out).as_posix(), "sha256": fsha(q), "size": q.stat().st_size}
                    for q in sorted(out.rglob("*")) if q.is_file()]
    input_manifest = [{"relpath": q.relative_to(input_root).as_posix(), "sha256": fsha(q), "size": q.stat().st_size}
                      for q in sorted(input_root.rglob("*")) if q.is_file()]
    # AS-RUN（success manifest：仅全部门通过后生成）
    asrun = {"run_id": run_id, "adapter": adapter, "donor_profile": donor,
             "contract": "65b3da223842e9a00e51779c7a049d962a3233316bc4e71ed6c43336d3ff865c",
             "clean_input_root": str(input_root), "input_bundle_sha256": got_bundle,
             "input_file_count": n_in,
             "input_tree_before": input_tree_pre, "input_tree_after": input_tree_post,
             "input_regular_file_manifest": input_manifest,
             "candidate_root": str(cand),
             "candidate_tree_before": cand_tree_pre, "candidate_tree_after": cand_tree_post,
             "case_md_src": str(md_src),
             "md_hashes": {m.name: fsha(m) for m in mds},
             "draft_provenance": {"path": str(provp), "sha256": fsha(provp),
                "schema": prov.get("schema"), "case_id": prov["case_id"]},
             "route": route_result, "expected_route": route_expected,
             "donor_binding": {"donor_id": donor_id, "donor_root": str(donor_root),
                "donors_spec_sha256": fsha(donors_spec_p),
                "expected_tree_sha256": dspec["tree"], "tree_before_sha256": donor_tree_pre,
                "tree_after_sha256": donor_tree_post, "regular_file_count": donor_n,
                "unchanged": donor_tree_post == donor_tree_pre},
             "validator_results": gates_log,
             "runner_sha256": fsha(__file__),
             "converter_sha256": fsha(conv),
             "chinese_gate": {"tool": "validate_chinese_t2.py",
                "sha256": fsha(Path(__file__).resolve().parent/"validate_chinese_t2.py"),
                "allowlist_spec": str(allow_spec_p), "allowlist_spec_sha256": fsha(allow_spec_p),
                "rationale": "合同必要英文白名单=显式且窄：仅盲稿实际使用且经复核确在clean input实体中的标识符token；禁全输入动态派生"},
             "output_root": str(out),
             "output_regular_file_manifest": out_manifest,
             "output_manifest_excluded_relpaths": ["RUN-AS-RUN.json"],
             "output_manifest_policy": "manifest覆盖除自引用RUN-AS-RUN.json外的全部最终普通文件（logs含全部validator子进程stdout/stderr）",
             "docx": {d.name: fsha(d) for d in docx},
             "pairing_manifest": pairing,
             "subprocess_records": subs,
             "frozen_07_count": 0, "vis_artifact_count": 0,
             "success_manifest": True,
             "result": "VALID"}
    body = json.dumps(asrun, ensure_ascii=False, indent=1)+"\n"
    if _PII9.search(body):
        print("HOLD-PRIVACY: AS-RUN内容含身份/电话样式"); return 3
    (out/"RUN-AS-RUN.json").write_text(body, encoding="utf-8")
    print(f"RUN-VALID[{run_id}]: 9docx/9pdf/{sum(p['pages'] for p in pairing)}png 子进程{len(subs)}条 门{len(gates_log)}项")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"HOLD-TEXT-E2E: 未预期异常fail-closed: {type(e).__name__}: {e}")
        sys.exit(3)
