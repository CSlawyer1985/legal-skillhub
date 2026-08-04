#!/usr/bin/env python3
"""GEO可执行自测（复用母包geo-query-set协议）：①GEO/llms入口引用全可达；
②llms-full覆盖SKILL+common+LAYOUT-SPEC；③query-set逐条：entry存在且含must_include、不含must_not_include。
exit 0=PASS, 3=FAIL。"""
import sys, json, re
from pathlib import Path
def main(root):
    root = Path(root).resolve(); fails = []
    for f in ["GEO.md","llms.txt","llms-full.txt","geo/query-set.json"]:
        if not (root/f).is_file(): fails.append(f"缺失:{f}")
    if fails:
        for f in fails: print("FAIL:", f)
        return 3
    # ①入口可达
    for f in ["GEO.md","llms.txt"]:
        t = (root/f).read_text(encoding="utf-8")
        for ref in set(re.findall(r'`((?:common|templates|tools)/[^`（)]*?\.(?:md|py))`?', t) + re.findall(r'((?:common|templates|tools)/[^\s，。`）)]+\.(?:md|py))', t)):
            if not (root/ref).is_file(): fails.append(f"{f}断链:{ref}")
    # ②llms-full覆盖
    full = (root/"llms-full.txt").read_text(encoding="utf-8")
    for src in ["SKILL.md","LAYOUT-SPEC.md"] + [f"common/{p.name}" for p in (root/"common").glob("*.md")]:
        head = (root/src).read_text(encoding="utf-8").strip().split("\n")
        h1 = next((l for l in head if l.startswith("# ")), None)
        if h1 and h1 not in full: fails.append(f"llms-full未覆盖:{src}")
    # ③query-set
    qs = json.loads((root/"geo/query-set.json").read_text(encoding="utf-8"))
    for q in qs["queries"]:
        ep = root/q["entry"]
        if not ep.is_file(): fails.append(f"{q['id']}: entry缺失{q['entry']}"); continue
        t = ep.read_text(encoding="utf-8")
        for kw in q["must_include"]:
            if kw not in t: fails.append(f"{q['id']}: {q['entry']}缺关键词『{kw}』")
        for kw in q["must_not_include"]:
            if kw in t: fails.append(f"{q['id']}: {q['entry']}含禁词『{kw}』")
    if fails:
        for f in fails[:20]: print("FAIL:", f)
        print(f"INVALID: {len(fails)}"); return 3
    print(f"VALID: GEO入口可达+llms-full覆盖+query-set {len(qs['queries'])}条全过"); return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "."))
