#!/usr/bin/env python3
"""AMT门validator：工作底稿主张/欠付行不得含合同总价，且必须出现请求口径余额（合同总价≠欠款余额G9）。
用法: amount_consistency_check.py <fixture目录>   exit 0=PASS, 3=FAIL。"""
import sys, json
from pathlib import Path
def main():
    d = Path(sys.argv[1])
    cfg = json.loads((d/"fields.json").read_text(encoding="utf-8"))
    wp = (d/"workpaper.md").read_text(encoding="utf-8")
    bad = claim_ok = 0
    for line in wp.splitlines():
        if "主张" in line or "欠付" in line:
            if cfg["contract_total"] in line: bad += 1
            if cfg["claim_balance"] in line: claim_ok += 1
    if bad or not claim_ok:
        print(f"HOLD-AMT: 主张口径失配(total冒充={bad},请求口径出现={claim_ok})"); return 3
    print("VALID: 主张口径一致（合同总价未冒充欠款余额）"); return 0
if __name__ == "__main__": sys.exit(main())
