#!/usr/bin/env python3
"""T2用户可见层中文门（r1.2版）：扫描DOCX可见文本部件的乱码/井号/机读引注/路径/英文token。
英文token白名单只来自--allow显式文件（逐案tools/necessary-english-*.json经runner复核生成），无任何内置集。
用法: validate_chinese_t2.py <docx目录> --allow <allow.json>
exit 0=VALID, 3=INVALID。"""
import sys, re, json, zipfile
from pathlib import Path

def parts_text(docx):
    out = {}
    with zipfile.ZipFile(docx) as z:
        for n in z.namelist():
            if n.startswith("word/") and n.endswith(".xml") and ("document" in n or "header" in n or "footer" in n):
                xml = z.read(n).decode("utf-8", errors="replace")
                out[n] = "".join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml))
    return out

def main():
    target = Path(sys.argv[1])
    allow = set()
    if "--allow" in sys.argv:
        allow = set(json.loads(Path(sys.argv[sys.argv.index("--allow")+1]).read_text(encoding="utf-8")))
    fails = []
    for dx in sorted(target.rglob("0*.docx")):
        for part, t in parts_text(dx).items():
            tag = f"{dx.name}[{part.split('/')[-1]}]"
            if "�" in t: fails.append(f"{tag}: U+FFFD乱码")
            if "#" in t: fails.append(f"{tag}: 含#")
            if ".md#" in t: fails.append(f"{tag}: 机读引注")
            if re.search(r'<local-source-redacted>', t): fails.append(f"{tag}: 路径")
            latin = {w for w in re.findall(r'[A-Za-z]{2,}', t) if w not in allow}
            if latin: fails.append(f"{tag}: 非白名单英文{sorted(latin)[:6]}")
    if fails:
        for f in fails[:20]: print("FAIL:", f)
        print(f"INVALID: {len(fails)}"); return 3
    print("VALID: T2中文门（白名单仅显式--allow文件）"); return 0

if __name__ == "__main__":
    sys.exit(main())
