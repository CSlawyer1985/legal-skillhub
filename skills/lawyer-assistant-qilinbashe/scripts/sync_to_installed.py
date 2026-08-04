# -*- coding: utf-8 -*-
"""把桌面权威源同步到 ~/.workbuddy 已安装源，保持双源一致（增量覆盖，保留目标多余文件）。"""
import os, shutil

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.expanduser("~/.workbuddy/skills/qilinbashe__skillhub")
EX_DIR = {".git", "__pycache__"}
EX_FILE = {".DS_Store", "Thumbs.db", "desktop.ini"}

n = 0
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in EX_DIR]
    for fn in files:
        if fn in EX_FILE:
            continue
        full = os.path.join(root, fn)
        rel = os.path.relpath(full, SRC)
        tgt = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        shutil.copy2(full, tgt)
        n += 1
print("已同步文件数:", n)

# 验证关键项
ck = [
    ("plugin", os.path.join(DST, ".workbuddy-plugin", "plugin.json")),
]
for name, p in ck:
    print("  DST 含 %s:" % name, os.path.exists(p))

sk = open(os.path.join(DST, "SKILL.md"), encoding="utf-8").read()
print("  DST SKILL.md v4.4.1:", "version: 4.4.1" in sk, "| 计数107:", "107个技能文件" in sk)
print("SYNC TO INSTALLED DONE")
