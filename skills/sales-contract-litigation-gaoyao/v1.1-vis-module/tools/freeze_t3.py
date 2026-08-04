#!/usr/bin/env python3
"""T3-r1冻结执行器（1785188700484口径）：fresh自T2-r1.2源复制，manifest细化schema+AS-RUN action_order。"""
import sys, os, json, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_t3 import fsha, source_invariants, MD, DOCX, MIME_MD, MIME_DOCX, CONTRACT_SHA
ROOT = Path(__file__).resolve().parent.parent
def main():
    cp = ROOT/"contract/T3-FROZEN-07-ACCEPTANCE-CONTRACT.json"
    assert fsha(cp) == CONTRACT_SHA
    contract = json.loads(cp.read_text(encoding="utf-8"))
    si_before, err = source_invariants(contract)
    if err: print(f"HOLD-FROZEN-07: 冻结前不变量失败:{err}"); return 3
    f07 = ROOT/"frozen-07"; f07.mkdir(exist_ok=True)
    cases = []
    for c in contract["cases"]:
        d = f07/c["run_id"]
        if d.is_dir(): os.chmod(d, 0o755)
        d.mkdir(exist_ok=True)
        files = []
        for role, name, src_key, sha_key, mime in (
            ("audit_md", MD, "source_md", "source_md_sha256", MIME_MD),
            ("workplan_docx", DOCX, "source_docx", "source_docx_sha256", MIME_DOCX)):
            src = Path(c[src_key])
            if fsha(src) != c[sha_key]: print(f"HOLD-FROZEN-07: 源与合同哈希不符:{src}"); return 3
            dst = d/name
            if not (dst.is_file() and fsha(dst) == c[sha_key]):
                if dst.exists(): os.chmod(dst, 0o644)
                shutil.copyfile(src, dst)
            if fsha(dst) != c[sha_key]: print(f"HOLD-FROZEN-07: 冻结端漂移:{dst}"); return 3
            os.chmod(dst, 0o444)
            files.append({"role": role, "basename": name, "entity_type": mime,
                          "source_path": c[src_key], "frozen_path": str(dst),
                          "source_sha256": c[sha_key], "frozen_sha256": fsha(dst)})
        os.chmod(d, 0o555)
        cases.append({"run_id": c["run_id"], "case_id": c["case_id"],
                      "content_dir": c["content_dir"], "files": files})
    si_after, err = source_invariants(contract)
    if err: print(f"HOLD-FROZEN-07: 冻结后不变量失败:{err}"); return 3
    (ROOT/"T3-FROZEN-07-MANIFEST.json").write_text(json.dumps(
      {"schema": "gaotao.t3.frozen07-manifest.v1", "stage": "T3",
       "hash_algorithm": "sha256-file/v1", "frozen_root": str(ROOT),
       "text_gate_message_id": "1785187652497-codex", "vis_started": False,
       "contract_sha256": CONTRACT_SHA, "cases": cases}, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    (ROOT/"T3-AS-RUN.json").write_text(json.dumps(
      {"schema": "gaotao.t3.as-run.v1", "stage": "T3", "result": "PASS",
       "vis_started": False, "date": "2026-07-27",
       "t3_root": str(ROOT), "contract_sha256": CONTRACT_SHA,
       "text_gate_message_id": "1785187652497-codex",
       "action_order": [
         "1: T2-r1.2双席PASS（1785187652497-codex + 1785187222152-hermes）",
         "2: freeze执行（本根fresh自T2-r1.2源复制，未从任何预合同T3根复制产物）"],
       "source_invariants": {"before": si_before, "after": si_after},
       "freeze_tool_sha256": fsha(Path(__file__)),
       "validator_sha256": fsha(Path(__file__).resolve().parent/"validate_t3.py"),
       "authorization_note": "root终审/安装/晋升/外发/法院提交未授权；VIS未启动"},
      ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    print(f"FROZEN: 4案×2端; invariants before==after: {si_before == si_after}")
    return 0
if __name__ == "__main__": sys.exit(main())
