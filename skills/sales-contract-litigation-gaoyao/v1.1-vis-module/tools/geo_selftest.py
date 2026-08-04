#!/usr/bin/env python3
"""GEO边界可执行自测：三开关全false+边界文件在册。exit 0/3"""
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent.parent
lp = json.loads((root/"LICENSE-PROVENANCE.json").read_text(encoding="utf-8"))
geo = lp.get("geo", {})
bad = [k for k in ("activation", "public_projection", "release") if geo.get(k)]
if bad: print(f"HOLD-GEO: 开关非false:{bad}"); sys.exit(3)
need = ["PRIVACY.md", "LICENSE", "PACKAGE-MANIFEST.json", "LICENSE-PROVENANCE.json"]
if (root/"GEO.md").is_file() or (root/"GEO-V1.1.md").is_file(): pass
else: print("HOLD-GEO: 缺GEO文件"); sys.exit(3)
for f in need:
    if not (root/f).is_file(): print(f"HOLD-GEO: 缺{f}"); sys.exit(3)
print("VALID: GEO三开关false+边界文件齐"); sys.exit(0)
