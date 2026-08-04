#!/usr/bin/env python3
"""独立隐私/脱敏校验子进程（合同privacy/desensitization门，分相）。
用法: validate_privacy_t2.py --phase md --md-src D
      validate_privacy_t2.py --phase artifacts --docx-dir D --pdf-dir D
      validate_privacy_t2.py --phase sidecar --out-root D
exit 0=VALID / 3=HOLD"""
import sys, re, zipfile
from pathlib import Path
PII = re.compile(r"(?<![\dA-Za-z])\d{17}[\dXx](?![\dA-Za-z])|(?<![\dA-Za-z])1[3-9]\d{9}(?![\dA-Za-z])")
MACHINE_TERMS = ("HOLD","SSOT","DRAFT","AS-RUN","PASS","FAIL")
def arg(name):
    a = sys.argv[1:]
    return a[a.index(name)+1] if name in a else None
def main():
    phase = arg("--phase")
    if phase == "md":
        for m in sorted(Path(arg("--md-src")).glob("0*.md")):
            if PII.findall(m.read_text(encoding="utf-8", errors="ignore")):
                print(f"HOLD-PRIVACY: {m.name}含身份证/手机号样式"); return 3
        print("VALID: md层隐私扫描零命中"); return 0
    if phase == "artifacts":
        docx_dir, pdf_dir = Path(arg("--docx-dir")), Path(arg("--pdf-dir"))
        for dx in sorted(docx_dir.glob("0*.docx")):
            with zipfile.ZipFile(dx) as z:
                for member in z.namelist():
                    if member.endswith((".xml", ".rels")):
                        if PII.search(z.read(member).decode("utf-8", errors="ignore")):
                            print(f"HOLD-PRIVACY: {dx.name}[{member}]含身份证/手机号样式"); return 3
                xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            vis = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
            for term in MACHINE_TERMS:
                if term in vis:
                    print(f"HOLD-DRAFTING: {dx.name}可见正文含机器治理词『{term}』"); return 3
        import pypdf
        for pdf in sorted(pdf_dir.glob("0*.pdf")):
            try:
                ptxt = "".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(pdf)).pages)
            except Exception as ex:
                print(f"HOLD-PRIVACY: PDF文本层不可读:{pdf.name}:{ex}"); return 3
            if PII.search(ptxt):
                print(f"HOLD-PRIVACY: {pdf.name} PDF文本层含身份证/手机号样式"); return 3
        print("VALID: DOCX全XML部件+.rels+可见机器词+PDF文本层零命中"); return 0
    if phase == "sidecar":
        out = Path(arg("--out-root"))
        for q in sorted(out.rglob("*")):
            if q.name == "RUN-AS-RUN.json": continue  # 自引排除（runner另对AS-RUN内容体扫）
            if q.is_file() and q.suffix.lower() in (".json", ".txt", ".md", ".out", ".err", ".xml"):
                if PII.search(q.read_text(encoding="utf-8", errors="ignore")):
                    print(f"HOLD-PRIVACY: 输出sidecar含身份/电话样式:{q.name}"); return 3
        print("VALID: 输出sidecar全域（含logs/allowlist）零命中"); return 0
    print("HOLD-PRIVACY: 未知phase"); return 3
if __name__ == "__main__": sys.exit(main())
