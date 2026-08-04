#!/usr/bin/env python3
"""独立provenance校验子进程（合同draft provenance门）。
用法: validate_provenance_t2.py <md_src> <input_root> <adapter_dir> <expected_bundle>
exit 0=VALID / 3=HOLD"""
import sys, json, hashlib, re
from pathlib import Path
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
NINE = ["01","02","03","04","05","06","07","08","09"]
def main():
    md_src, input_root, adapter_dir, expected_bundle = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    provp = md_src/"DRAFT-PROVENANCE.json"
    if not provp.is_file(): print("HOLD-PROVENANCE: DRAFT-PROVENANCE缺失"); return 3
    prov = json.loads(provp.read_text(encoding="utf-8"))
    for req in ("case_id","input_bundle_sha256","drafting_contract_sha256","nine_document_registry_sha256","documents"):
        if req not in prov: print(f"HOLD-PROVENANCE: 缺必填字段{req}"); return 3
    if prov["input_bundle_sha256"] != expected_bundle:
        print("HOLD-PROVENANCE: provenance登记输入bundle与本run期望不一致"); return 3
    if prov["drafting_contract_sha256"] != fsha(adapter_dir/"DRAFTING-CONTRACT.md"):
        print("HOLD-PROVENANCE: drafting_contract_sha256与adapter实体不符"); return 3
    if prov["nine_document_registry_sha256"] != fsha(adapter_dir/"adapter.json"):
        print("HOLD-PROVENANCE: nine_document_registry_sha256与adapter实体不符"); return 3
    docs = prov["documents"]
    if sorted(d["document_id"] for d in docs) != NINE:
        print("HOLD-PROVENANCE: documents登记必须恰为九件"); return 3
    for d in docs:
        for fld in ("document_id","md_relpath","md_sha256","source_refs","unresolved_items"):
            if fld not in d: print(f"HOLD-PROVENANCE: 文书{d.get('document_id')}缺字段{fld}"); return 3
        fp = md_src/d["md_relpath"]
        if not fp.is_file() or fsha(fp) != d["md_sha256"]:
            print(f"HOLD-PROVENANCE: 哈希失配:{d['md_relpath']}"); return 3
        if not d["source_refs"]: print(f"HOLD-PROVENANCE: 文书{d['document_id']}无source_refs"); return 3
        for sr in d["source_refs"]:
            for fld in ("input_relpath","input_file_sha256","locator","purpose"):
                if fld not in sr: print(f"HOLD-PROVENANCE: source_ref缺{fld}"); return 3
            sf = input_root/sr["input_relpath"]
            if not sf.is_file() or fsha(sf) != sr["input_file_sha256"]:
                print(f"HOLD-PROVENANCE: source_ref输入实体失配:{sr['input_relpath']}"); return 3
    pii = re.compile(r"(?<![\dA-Za-z])\d{17}[\dXx](?![\dA-Za-z])|(?<![\dA-Za-z])1[3-9]\d{9}(?![\dA-Za-z])")
    if pii.search(provp.read_text(encoding="utf-8")):
        print("HOLD-PRIVACY: provenance sidecar含明文身份/电话样式"); return 3
    print(f"VALID: provenance v2 九件×source_refs全核 case_id={prov['case_id']}")
    return 0
if __name__ == "__main__": sys.exit(main())
