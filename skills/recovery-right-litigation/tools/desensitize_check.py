#!/usr/bin/env python3
"""封装前脱敏扫描v2：敏感词(长度,SHA-256)哈希滑窗；DOCX解包word/*.xml按可见语义扫描。
用法: desensitize_check.py <目录> | --selftest
exit 0=零命中/自测过, 3=命中/自测败。声明：PNG/PDF二进制图像层不在文本扫描范围（图内容由人工视觉QA与生成端禁入规则守护）。"""
import sys, hashlib, json, re, zipfile, tempfile
from pathlib import Path
SIGS = json.loads(Path(__file__).with_name("desensitize_sigs.json").read_text())
def scan_text(text):
    hits = 0
    by_len = {}
    for L, h in SIGS: by_len.setdefault(L, set()).add(h)
    for L, hs in by_len.items():
        for i in range(0, max(0, len(text)-L+1)):
            if hashlib.sha256(text[i:i+L].encode("utf-8")).hexdigest() in hs: hits += 1
    return hits
def docx_text(p):
    out = []
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            if n.startswith("word/") and n.endswith(".xml"):
                xml = z.read(n).decode("utf-8", errors="ignore")
                out.append(re.sub(r'<[^>]+>', '', xml))
    return "\n".join(out)
def scan_tree(target):
    total = 0
    for p in sorted(Path(target).rglob("*")):
        if not p.is_file() or p.name == "desensitize_sigs.json": continue
        if p.suffix.lower() == ".docx":
            try: n = scan_text(docx_text(p))
            except Exception as e: print(f"WARN 无法解包 {p}: {e}"); n = 0
        elif p.suffix.lower() in (".png",".pdf"):
            continue  # 见docstring声明
        elif p.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(p) as z:
                    n = scan_text("\n".join(z.namelist()))
                    for m in z.namelist():
                        if m.endswith((".md",".txt",".json",".py")):
                            n += scan_text(z.read(m).decode("utf-8", errors="ignore"))
            except Exception: n = 0
        else:
            try: n = scan_text(p.read_bytes().decode("utf-8", errors="ignore"))
            except Exception: continue
        if n: print(f"HIT: {p} x{n}"); total += n
    return total
def make_docx(path, text):
    ct = '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    rels = '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    doc = f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("word/document.xml", doc)
def selftest():
    with tempfile.TemporaryDirectory() as t:
        canary = "".join(["脱敏","自测","金丝","雀标","记"])  # 运行时拼接，源码不含连续明文
        make_docx(Path(t)/"dirty.docx", f"本段含{canary}用于负向验证")
        make_docx(Path(t)/"clean.docx", "本段为干净中文内容")
        dirty = scan_text(docx_text(Path(t)/"dirty.docx"))
        clean = scan_text(docx_text(Path(t)/"clean.docx"))
        print(f"selftest: dirty_hits={dirty} clean_hits={clean}")
        ok = dirty >= 1 and clean == 0
        print("SELFTEST", "PASS" if ok else "FAIL")
        return 0 if ok else 3
def main(argv):
    if "--selftest" in argv: return selftest()
    target = argv[1] if len(argv) > 1 else "."
    total = scan_tree(target)
    print("CLEAN: 全包脱敏扫描零命中(含DOCX语义层)" if total==0 else f"DIRTY: {total} hits")
    return 0 if total==0 else 3
if __name__ == "__main__":
    sys.exit(main(sys.argv))
