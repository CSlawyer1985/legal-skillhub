# -*- coding: utf-8 -*-
"""以桌面源目录为准，完整重建 legal-skills.zip（排除 dotfile/二进制/平台元数据），
并解包到临时目录做对照校验（危险路径 / 关键节点在位 / 计数 / 版本）。"""
import os, zipfile, time, shutil, sys, tempfile
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 提交稿唯一位置铁律：桌面/legal-skills.zip
# SRC=桌面/法律专家/legal-skills → dirname(dirname(SRC))=桌面 → 桌面/legal-skills.zip
OUT = os.path.join(os.path.dirname(os.path.dirname(SRC)), "legal-skills.zip")
TMP = os.path.join(tempfile.gettempdir(), "legal_skills_verify")

EX_DIR = {".git", "__pycache__", ".codebuddy-plugin", ".workbuddy-plugin", "node_modules", ".idea", ".vscode"}
EX_FILE = {".DS_Store", "Thumbs.db", "desktop.ini", "_icon.jpg", "_meta.json", "_skillhub_meta.json", "fix2.py", "fix_submit_blockers.py", ".gitattributes", ".gitignore"}

# 1. 收集文件
paths = []
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in EX_DIR]
    for fn in files:
        if fn in EX_FILE:
            continue
        full = os.path.join(root, fn)
        rel = os.path.relpath(full, SRC)
        paths.append((full, rel))
paths.sort(key=lambda x: x[1])
print("[build] 收集文件数:", len(paths))

# 2. 写入临时 zip
tmp = OUT + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for full, rel in paths:
        z.write(full, rel)

# 3. 带重试替换正式 zip
last = None
for i in range(10):
    try:
        os.replace(tmp, OUT)
        last = None
        break
    except (PermissionError, OSError) as e:
        last = e
        time.sleep(1)
if last:
    print("[build][X] 替换失败:", last); sys.exit(1)
print("[build] 已重建:", OUT, "大小:", os.path.getsize(OUT), "字节")

# 4. 解包校验
if os.path.exists(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP)
with zipfile.ZipFile(OUT) as z:
    z.extractall(TMP)
    names = z.namelist()

bad = [n for n in names if n.startswith(".workbuddy-plugin/") or n.startswith(".codebuddy-plugin/")
       or n.endswith("_icon.jpg") or n.endswith("_meta.json") or n.endswith("_skillhub_meta.json")]
print("[check] 危险路径(应为空):", bad if bad else "✅ 无")

agents_dir = os.path.join(TMP, "agents")
ags = [f for f in os.listdir(agents_dir) if f.endswith(".md")]
print("[check] zip内 agents md 数:", len(ags), "(含00导航节点，与源一致)")
print("[check] 含 22A?", any("22A" in f for f in ags), "| 含 22B?", any("22B" in f for f in ags))
print("[check] 含 数据安全与合规说明.md?", os.path.exists(os.path.join(TMP, "数据安全与合规说明.md")))
print("[check] 含 恒锦石材样例?", os.path.exists(os.path.join(TMP, "references/样例/恒锦石材仲裁攻防推演.md")))

# plugin.json 不应在 zip 内
in_zip_plugin = [n for n in names if n.endswith("plugin.json")]
print("[check] zip内 plugin.json(应无):", in_zip_plugin if in_zip_plugin else "✅ 已排除")

sk = open(os.path.join(TMP, "SKILL.md"), encoding="utf-8").read()
# 动态推导版本（不再硬编码 4.3.0）
_my = open(os.path.join(TMP, "manifest.yaml"), encoding="utf-8").read()
import re as _re
_mv = _re.search(r'version:\s*[\'"]?([\d.]+)', _my)
_real_ver = _mv.group(1) if _mv else "4.4.1"
print("[check] SKILL.md 版本%s:" % _real_ver, ("version: %s" % _real_ver) in sk, "| 动态计数%d:" % len(ags), ("%d个技能文件" % len(ags)) in sk)

# 总文件数对照源排除后
src_count = len(paths)
zip_count = len(names)
print("[check] 源排除后文件数:", src_count, "| zip内文件数:", zip_count, "| 一致:", src_count == zip_count)

# 清理临时
shutil.rmtree(TMP, ignore_errors=True)
print("\n[OK] 重建+解包校验完成")
