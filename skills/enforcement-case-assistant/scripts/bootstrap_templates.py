#!/usr/bin/env python3
"""执行案件助手：模板还原脚本（首次使用必跑）。

上传市场版本不含二进制文件，19 份 docx/doc 模板以 base64 文本存放在
assets/templates_b64/ 下。本脚本将其解码还原为 assets/templates/ 下的
真实 .docx/.doc 文件。已还原则自动跳过。

用法：python3 scripts/bootstrap_templates.py
"""
import base64
import glob
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "assets", "templates_b64")
DST = os.path.join(BASE, "assets", "templates")

os.makedirs(DST, exist_ok=True)
files = sorted(glob.glob(os.path.join(SRC, "*.b64.txt")))
if not files:
    sys.exit("错误：未找到 assets/templates_b64/*.b64.txt")

restored, skipped = 0, 0
for f in files:
    base = os.path.basename(f)[: -len(".b64.txt")]
    # 命名规则：xxx_docx.b64.txt -> xxx.docx；xxx_doc.b64.txt -> xxx.doc
    if base.endswith("_docx"):
        name = base[: -len("_docx")] + ".docx"
    elif base.endswith("_doc"):
        name = base[: -len("_doc")] + ".doc"
    else:
        name = base
    out = os.path.join(DST, name)
    if os.path.exists(out):
        skipped += 1
        continue
    with open(f, encoding="utf-8") as fp:
        data = base64.b64decode(fp.read())
    with open(out, "wb") as fp:
        fp.write(data)
    restored += 1
    print(f"[ok] 还原: {name} ({len(data)} 字节)")

print(f"\n完成：还原 {restored} 个，跳过已存在 {skipped} 个。模板位于 assets/templates/，可正常使用。")
