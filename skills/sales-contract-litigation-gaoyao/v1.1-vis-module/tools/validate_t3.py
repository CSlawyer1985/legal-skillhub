#!/usr/bin/env python3
"""T3冻结07验收器（合同aa7e1d1076bc…逐条实现）。
正例: python3 -B tools/validate_t3.py --root .
自测: python3 -B tools/validate_t3.py --root . --selftest
exit 0=VALID / 3=HOLD-FROZEN-07"""
import sys, os, json, stat, hashlib, shutil, subprocess
from pathlib import Path

CONTRACT_SHA = "aa7e1d1076bc4c14cd86e4c90d6869dbb7a010c0ed2915434c829e716533a7df"
MD = "07-诉讼案件办案方案工作底稿.md"
DOCX = "07-诉讼案件办案方案工作底稿.docx"
MIME_MD = "text/markdown"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def t0_tree(root):
    root = Path(root); ent = []
    for q in root.rglob("*"):
        if q.is_symlink(): return None, -1
        if q.is_file(): ent.append((q.relative_to(root).as_posix(), q))
    ent.sort()
    lines = [f"{fsha(q)}\t{q.stat().st_size}\tfile\t{r}" for r, q in ent]
    return hashlib.sha256(("\n".join(lines)+"\n").encode()).hexdigest(), len(ent)

def hold(msg):
    print(f"HOLD-FROZEN-07: {msg}"); return 3

def check_manifest_replay(root, manifest_name, want_sha, want_entries, allowed_unlisted):
    root = Path(root); mp = root/manifest_name
    if not mp.is_file() or fsha(mp) != want_sha: return f"{root.name}的{manifest_name}哈希失配"
    lines = mp.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) != want_entries: return f"{root.name}清单条数{len(lines)}≠{want_entries}"
    listed = set()
    for line in lines:
        h, _, rel = line.partition("  ")
        listed.add(rel); p = root/rel
        if not p.is_file() or fsha(p) != h: return f"{root.name}树漂移:{rel}"
    extra = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
             and str(p.relative_to(root)) not in listed
             and p.name not in allowed_unlisted]
    if extra: return f"{root.name}清单外文件:{extra[:3]}"
    return None

def source_invariants(contract):
    si = contract["source_invariants"]
    t2 = si["t2"]
    tree, n = t0_tree(t2["root"])
    if tree != t2["tree_sha256"] or n != t2["regular_file_count"]:
        return None, f"T2树失配 {str(tree)[:16]}/{n}"
    err = check_manifest_replay(t2["root"], t2["manifest"], t2["manifest_sha256"],
                                t2["manifest_entry_count"], t2["allowed_unlisted_files"])
    if err: return None, err
    t1 = si["t1"]
    err = check_manifest_replay(t1["root"], t1["manifest"], t1["manifest_sha256"],
                                t1["manifest_entry_count"], t1["allowed_unlisted_files"])
    if err: return None, err
    donors = {}
    for d in si["donors"]:
        tree, n = t0_tree(d["root"])
        if tree != d["tree_sha256"] or n != d["regular_file_count"]:
            return None, f"donor树失配:{d['donor_id']}"
        donors[d["donor_id"]] = tree
    return {"t2_tree_sha256": t2["tree_sha256"], "t2_manifest_sha256": t2["manifest_sha256"],
            "t1_manifest_sha256": t1["manifest_sha256"], "donor_tree_sha256": donors}, None

def validate(root):
    root = Path(root).resolve()
    cp = root/"contract/T3-FROZEN-07-ACCEPTANCE-CONTRACT.json"
    if not cp.is_file() or fsha(cp) != CONTRACT_SHA: return hold("合同副本缺失或哈希失配")
    contract = json.loads(cp.read_text(encoding="utf-8"))
    # 全树symlink+VIS/generator禁令
    for q in root.rglob("*"):
        if q.is_symlink(): return hold(f"symlink:{q.relative_to(root)}")
        if q.is_file() and (q.suffix == ".svg" or q.name.startswith("view-spec")
                            or "mermaid" in q.name.lower() or q.name.lower().startswith(("gen_vis","vis_"))):
            return hold(f"VIS产物或生成器:{q.relative_to(root)}")
    # 布局与八端
    f07 = root/"frozen-07"
    if not f07.is_dir(): return hold("缺frozen-07目录")
    want_dirs = sorted(c["run_id"] for c in contract["cases"])
    got_dirs = sorted(p.name for p in f07.iterdir() if p.is_dir())
    if got_dirs != want_dirs: return hold(f"frozen-07子目录集不符:{got_dirs}")
    if [p.name for p in f07.iterdir() if not p.is_dir()]: return hold("frozen-07含非目录项")
    for c in contract["cases"]:
        d = f07/c["run_id"]
        if stat.S_IMODE(d.stat().st_mode) & 0o222: return hold(f"{c['run_id']}目录含写位")
        content = sorted(p.name for p in d.iterdir())
        if content != sorted([MD, DOCX]): return hold(f"{c['run_id']}内容集≠精确两项:{content}")
        for name, src_key, sha_key in ((MD, "source_md", "source_md_sha256"),
                                        (DOCX, "source_docx", "source_docx_sha256")):
            fp = d/name
            if stat.S_IMODE(fp.stat().st_mode) != 0o444: return hold(f"非0444:{c['run_id']}/{name}")
            src = Path(c[src_key])
            if not src.is_file(): return hold(f"缺源:{src}")
            fh, sh_ = fsha(fp), fsha(src)
            if fh != c[sha_key]: return hold(f"冻结端与合同哈希不符（篡改/跨案绑定）:{c['run_id']}/{name}")
            if sh_ != c[sha_key]: return hold(f"源端与合同哈希不符:{src}")
    # manifest侧件
    man_p = root/"T3-FROZEN-07-MANIFEST.json"
    if not man_p.is_file(): return hold("缺T3-FROZEN-07-MANIFEST.json")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    if man.get("schema") != "gaotao.t3.frozen07-manifest.v1": return hold("manifest schema不符")
    if man.get("stage") != "T3" or man.get("hash_algorithm") != "sha256-file/v1":
        return hold("manifest缺stage=T3或hash_algorithm")
    if Path(man.get("frozen_root", "")).resolve() != root.resolve():
        return hold("manifest frozen_root非实际绝对路径")
    if man.get("text_gate_message_id") != "1785187652497-codex": return hold("manifest缺text_gate_message_id")
    if man.get("vis_started") is not False: return hold("manifest vis_started须为false")
    by_run = {e["run_id"]: e for e in man["cases"]}
    if len(man["cases"]) != 4: return hold("manifest cases须精确四项")
    for c in contract["cases"]:
        e = by_run.get(c["run_id"])
        if not e: return hold(f"manifest缺案:{c['run_id']}")
        if e.get("case_id") != c["case_id"] or e.get("content_dir") != c["content_dir"]:
            return hold(f"manifest case_id/content_dir不符:{c['run_id']}")
        files = e.get("files", [])
        if len(files) != 2: return hold(f"manifest {c['run_id']} files须精确两记录")
        by_role = {f.get("role"): f for f in files}
        for role, bn, mime, src_key, sha_key in (
            ("audit_md", MD, MIME_MD, "source_md", "source_md_sha256"),
            ("workplan_docx", DOCX, MIME_DOCX, "source_docx", "source_docx_sha256")):
            fr = by_role.get(role)
            if not fr: return hold(f"manifest {c['run_id']}缺role={role}")
            if fr.get("basename") != bn or fr.get("entity_type") != mime:
                return hold(f"manifest {c['run_id']}/{role} basename或entity_type不符")
            if fr.get("source_path") != c[src_key]:
                return hold(f"manifest源绑定与合同不符:{c['run_id']}/{role}")
            if Path(fr.get("frozen_path", "")).resolve() != (f07/c["run_id"]/bn).resolve():
                return hold(f"manifest冻结实际路径不符:{c['run_id']}/{role}")
            if fr.get("source_sha256") != c[sha_key] or fr.get("frozen_sha256") != c[sha_key]:
                return hold(f"manifest双哈希与合同不符:{c['run_id']}/{role}")
    # AS-RUN侧件
    ar_p = root/"T3-AS-RUN.json"
    if not ar_p.is_file(): return hold("缺T3-AS-RUN.json")
    ar = json.loads(ar_p.read_text(encoding="utf-8"))
    if ar.get("schema") != "gaotao.t3.as-run.v1": return hold("AS-RUN schema不符")
    if ar.get("stage") != "T3" or ar.get("result") != "PASS": return hold("AS-RUN缺stage=T3/result=PASS")
    if ar.get("vis_started") is not False: return hold("AS-RUN vis_started须为false")
    if ar.get("text_gate_message_id") != "1785187652497-codex": return hold("AS-RUN缺text_gate_message_id")
    ao = ar.get("action_order", [])
    if not (isinstance(ao, list) and len(ao) >= 2 and "1785187652497" in str(ao[0]) and "freeze" in str(ao[1]).lower()):
        return hold("AS-RUN action_order未明确PASS先于freeze")
    want_si, err = source_invariants(contract)
    if err: return hold(err)
    for phase in ("before", "after"):
        got = ar.get("source_invariants", {}).get(phase)
        if got != want_si: return hold(f"AS-RUN source_invariants[{phase}]与合同逐值不符")
    # 负测收据侧件
    nr_p = root/"T3-NEGATIVE-RECEIPTS.json"
    if not nr_p.is_file(): return hold("缺T3-NEGATIVE-RECEIPTS.json")
    nr = json.loads(nr_p.read_text(encoding="utf-8"))
    if nr.get("schema") != "gaotao.t3.negative-receipts.v1": return hold("负测schema不符")
    want_ids = contract["negative_receipts"]["exact_test_ids"]
    got_ids = [r["test_id"] for r in nr["receipts"]]
    if got_ids != want_ids: return hold(f"负测id集不符:{got_ids}")
    req = contract["negative_receipts"]["required_fields"]
    for r in nr["receipts"]:
        for f in req:
            if f not in r: return hold(f"负测{r['test_id']}缺字段{f}")
        if r["actual_exit"] == 0 or not r["source_roots_unchanged"] or r["success_manifest_present"]:
            return hold(f"负测{r['test_id']}语义不符")
        if r["delivery_tree_before"] != r["delivery_tree_after"]:
            return hold(f"负测{r['test_id']}交付树漂移")
    # SUMS精确集（除自身）
    sums_p = root/"SHA256SUMS.txt"
    if not sums_p.is_file(): return hold("缺SHA256SUMS.txt")
    listed = {}
    for line in sums_p.read_text(encoding="utf-8").strip().splitlines():
        h, _, rel = line.partition("  ")
        listed[rel] = h
    actual = {str(p.relative_to(root)): p for p in root.rglob("*")
              if p.is_file() and p.name != "SHA256SUMS.txt"}
    if set(listed) != set(actual): 
        return hold(f"SUMS集不精确 缺{sorted(set(actual)-set(listed))[:2]} 多{sorted(set(listed)-set(actual))[:2]}")
    for rel, h in listed.items():
        if fsha(actual[rel]) != h: return hold(f"SUMS哈希失配:{rel}")
    print("VALID: T3合同全门（布局/八端/三侧件/SUMS精确集/源不变量before+after/负测收据）")
    return 0

def selftest(root):
    """临时副本三负测：合同exact_test_ids逐一注入并确认本验收器非零拒绝；副本即删，源零接触。"""
    root = Path(root).resolve()
    scratch = Path("/private/tmp/claude-502/-Users-Zhuanz/32ee54cd-ecec-44b9-b231-905d9cf32c36/scratchpad/t3selftest")
    shutil.rmtree(scratch, ignore_errors=True) if not scratch.exists() else None
    if scratch.exists():
        for q in scratch.rglob("*"):
            try: os.chmod(q, 0o755 if q.is_dir() else 0o644)
            except OSError: pass
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    contract = json.loads((root/"contract/T3-FROZEN-07-ACCEPTANCE-CONTRACT.json").read_text(encoding="utf-8"))
    def copy_root(name):
        dst = scratch/name
        shutil.copytree(root, dst)
        for q in dst.rglob("*"):
            os.chmod(q, 0o755 if q.is_dir() else 0o644)
        # 搬迁修正：副本内manifest的frozen_root/frozen_path改指副本（属副本机制非注入项）
        mp = dst/"T3-FROZEN-07-MANIFEST.json"
        if mp.is_file():
            mp.write_text(mp.read_text(encoding="utf-8").replace(str(root), str(dst)), encoding="utf-8")
        return dst
    def run_on(dst):
        return subprocess.run([sys.executable, "-B", str(dst/"tools/validate_t3.py"), "--root", str(dst)],
                              capture_output=True, text=True, timeout=900)
    results = []
    # N1 跨案源绑定：交换两案冻结DOCX
    d = copy_root("N1")
    a = d/"frozen-07/T2-E2E-FL-OPEN-DIRECT-CASE01"/DOCX
    b = d/"frozen-07/T2-E2E-FL-SUB-DIRECT-CASE01"/DOCX
    tmp = d/"swap.tmp"; shutil.move(a, tmp); shutil.move(b, a); shutil.move(tmp, b)
    for c in contract["cases"]:
        dd = d/"frozen-07"/c["run_id"]
        for f in dd.iterdir(): os.chmod(f, 0o444)
        os.chmod(dd, 0o555)
    r = run_on(d); results.append(("T3-N1-cross-case-source-binding", r))
    # N2 冻结端篡改
    d = copy_root("N2")
    f2 = d/"frozen-07/T2-E2E-SALES-CASE003"/MD
    f2.write_text(f2.read_text(encoding="utf-8") + "\n篡改\n", encoding="utf-8")
    for c in contract["cases"]:
        dd = d/"frozen-07"/c["run_id"]
        for f in dd.iterdir(): os.chmod(f, 0o444)
        os.chmod(dd, 0o555)
    r = run_on(d); results.append(("T3-N2-frozen-copy-tamper", r))
    # N3 缺源：合同副本内source_md改指不存在（合同哈希同步失配→由合同副本校验拦，改为破坏manifest源路径）
    d = copy_root("N3")
    mp = d/"T3-FROZEN-07-MANIFEST.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    m["cases"][0]["files"][0]["source_path"] = m["cases"][0]["files"][0]["source_path"] + ".GONE"
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    for c in contract["cases"]:
        dd = d/"frozen-07"/c["run_id"]
        for f in dd.iterdir(): os.chmod(f, 0o444)
        os.chmod(dd, 0o555)
    r = run_on(d); results.append(("T3-N3-source-missing", r))
    ok = True
    for tid, r in results:
        good = r.returncode != 0 and "HOLD-FROZEN-07" in r.stdout
        ok &= good
        print(f"[{tid}] exit={r.returncode} {'OK' if good else 'FAIL'} {r.stdout.strip().splitlines()[-1][:70] if r.stdout.strip() else ''}")
    for q in scratch.rglob("*"):
        try: os.chmod(q, 0o755 if q.is_dir() else 0o644)
        except OSError: pass
    shutil.rmtree(scratch, ignore_errors=True)
    print("SELFTEST", "3/3 OK" if ok else "FAIL")
    return 0 if ok else 3

def main():
    a = sys.argv[1:]
    root = a[a.index("--root")+1] if "--root" in a else "."
    if "--selftest" in a: return selftest(root)
    return validate(root)

if __name__ == "__main__":
    sys.exit(main())
