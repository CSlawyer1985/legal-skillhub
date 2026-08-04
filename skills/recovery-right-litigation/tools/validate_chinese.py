#!/usr/bin/env python3
"""用户可见层全中文机扫v2：扫描DOCX全部word/*.xml部件（正文+页眉页脚），
禁英文治理词/#/机读引注/绝对路径/U+FFFD替代字符。exit 0=PASS, 3=FAIL。"""
import sys, re, zipfile
from pathlib import Path
WHITELIST = re.compile(r'^(HT|JJ|DZ|ZLJ|TC|THB|RZ|A4)?[-\d]*$')
def parts_text(docx):
    out = {}
    with zipfile.ZipFile(docx) as z:
        for n in z.namelist():
            if n.startswith("word/") and n.endswith(".xml") and ("document" in n or "header" in n or "footer" in n):
                xml = z.read(n).decode("utf-8", errors="replace")
                out[n] = "".join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml))
    return out
def main(target):
    fails = []
    for dx in sorted(Path(target).rglob("0*.docx")):
        for part, t in parts_text(dx).items():
            tag = f"{dx.name}[{part.split('/')[-1]}]"
            if "�" in t: fails.append(f"{tag}: 含U+FFFD替代字符（乱码）")
            if "#" in t: fails.append(f"{tag}: 含#×{t.count('#')}")
            if ".md#" in t or "md#" in t: fails.append(f"{tag}: 含机读引注")
            if re.search(r'<local-source-redacted>', t): fails.append(f"{tag}: 含路径")
            latin = {w for w in re.findall(r'[A-Za-z]{2,}', t) if not WHITELIST.match(w)}
            if latin: fails.append(f"{tag}: 英文{sorted(latin)[:6]}")
    if fails:
        for f in fails[:30]: print("FAIL:", f)
        print(f"INVALID: {len(fails)}"); return 3
    print("VALID: 全部DOCX全部可见部件全中文无乱码"); return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "."))
