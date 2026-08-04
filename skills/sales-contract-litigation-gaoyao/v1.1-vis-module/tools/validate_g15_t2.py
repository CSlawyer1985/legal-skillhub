#!/usr/bin/env python3
"""独立G1.5起草合同校验子进程（关键金额入法院件/当事人入01/07九节/法院件无横幅）。
用法: validate_g15_t2.py <docx_dir> <prov_path>  exit 0/3"""
import sys, json, re, zipfile
from pathlib import Path
def vis_text(dx):
    with zipfile.ZipFile(dx) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
def amt_forms(amt):
    plain = amt.replace(",", ""); forms = [plain]
    try:
        ws = ("%f" % (float(plain)/10000.0)).rstrip("0").rstrip(".")
        forms.append(ws + "万")
    except ValueError: pass
    return forms
def main():
    docx_dir, prov = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    texts = {dx.stem[:2]: vis_text(dx) for dx in sorted(docx_dir.glob("0*.docx"))}
    for amt in prov.get("key_amounts", []):
        for dno in prov.get("court_docs_amount_docs", []):
            body = texts.get(dno, "").replace(",", "")
            if not any(f in body for f in amt_forms(amt)):
                print(f"HOLD-DRAFTING: 关键金额{amt}未见于{dno}号文书"); return 3
    for pty in prov.get("key_parties", []):
        if pty not in texts.get("01", ""):
            print(f"HOLD-DRAFTING: 当事人{pty}未见于01号文书"); return 3
    for sec in ["第一节","第二节","第三节","第四节","第五节","第六节","第七节","第八节","第九节"]:
        if sec not in texts.get("07", ""): print(f"HOLD-DRAFTING: 07缺{sec}"); return 3
    for dno in ("01","02","05","06"):
        if "内部研究草稿" in texts.get(dno, ""): print(f"HOLD-DRAFTING: 法院件{dno}含内部横幅"); return 3
    print("VALID: G1.5勾稽（金额/当事人/07九节/法院件无横幅）全过"); return 0
if __name__ == "__main__": sys.exit(main())
