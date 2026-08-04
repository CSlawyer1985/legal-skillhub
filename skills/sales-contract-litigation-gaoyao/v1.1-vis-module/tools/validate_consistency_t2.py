#!/usr/bin/env python3
"""独立跨文书一致性校验子进程（语义边界探针，按case_id）。
用法: validate_consistency_t2.py <docx_dir> <prov_path>  exit 0/3"""
import sys, json, re, zipfile
from pathlib import Path
PROBES = {
 "CASE-01": [["序列号","发动机号"],["现行法源"],["在先程序"],["重复起诉"],["撤诉"],["仲裁"]],
 "CASE-02": [["转让协议"],["转让通知"],["原出租人"],["他案"],
             ["历史台账","旧口径"],["对抗"],["户籍","身份证明"],["送达凭证"]],
 "CASE-003": [["序列号"],["不等于法院"],["冲抵"],["时效"],["授权"],["管辖"]],
}
def main():
    docx_dir, prov = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    joined = ""
    for dx in sorted(docx_dir.glob("0*.docx")):
        with zipfile.ZipFile(dx) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        joined += "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
    cid = prov["case_id"]
    if cid not in PROBES: print(f"HOLD-DRAFTING: 未登记探针的case_id:{cid}"); return 3
    for probe in PROBES[cid]:
        if not any(alt in joined for alt in probe):
            print(f"HOLD-DRAFTING: 语义边界缺失[{cid}]: {'/'.join(probe)}"); return 3
    print(f"VALID: 语义边界探针[{cid}] {len(PROBES[cid])}组全命中"); return 0
if __name__ == "__main__": sys.exit(main())
