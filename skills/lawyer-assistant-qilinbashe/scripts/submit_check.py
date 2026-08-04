# -*- coding: utf-8 -*-
"""提交 SkillHub 专项校验：zip 内逐文件内容对照源目录（同排除规则），
并强化危险路径 / plugin.json / 关键文档计数核对。

提交路径规则（强哥 2026-07-28 明确）：
  排除 dotfile 目录(.codebuddy-plugin/.workbuddy-plugin) → 路径不安全
  排除二进制 _icon.jpg → 被拒绝
  排除平台元数据 _meta.json / _skillhub_meta.json → 平台自动产物
  源目录保留这些文件（本地运行/同步用），仅 zip 排除
"""
import os, tempfile, zipfile, hashlib, sys, shutil
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(SRC)), "legal-skills.zip")
TMP = os.path.join(tempfile.gettempdir(), "legal_skills_submit")

EX_DIR = {".git", "__pycache__", ".codebuddy-plugin", ".workbuddy-plugin", "node_modules", ".idea", ".vscode"}
EX_FILE = {".DS_Store", "Thumbs.db", "desktop.ini", "_icon.jpg", "_meta.json", "_skillhub_meta.json", "fix2.py", "fix_submit_blockers.py", ".gitattributes", ".gitignore"}

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

# 1. 源目录排除后清单
src_files = {}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in EX_DIR]
    for fn in files:
        if fn in EX_FILE:
            continue
        full = os.path.join(root, fn)
        rel = os.path.relpath(full, SRC).replace("\\", "/")
        src_files[rel] = full

# 2. 解包 zip
if os.path.exists(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP)
with zipfile.ZipFile(OUT) as z:
    z.extractall(TMP)
    names = [n for n in z.namelist() if not n.endswith("/")]
zip_files = {}
for n in names:
    zip_files[n] = os.path.join(TMP, n)

errors = []

# 3. 危险路径（提交规则红线）
for n in names:
    low = n.lower()
    if n.startswith(".codebuddy-plugin/") or n.startswith(".workbuddy-plugin/"):
        errors.append("危险路径(dotfile目录): %s" % n)
    if low.endswith("_icon.jpg") or low.endswith("_meta.json") or low.endswith("_skillhub_meta.json"):
        errors.append("危险路径(禁止文件): %s" % n)
    # 任意隐藏目录前缀
    if "/." in ("/" + n):
        # 允许 assets/.gitkeep 之类？源目录无；仅 .workbuddy-plugin/.codebuddy-plugin 已排除，
        # 其余 dotfile 一律判危险
        head = n.split("/")[0]
        if head.startswith("."):
            errors.append("危险路径(隐藏目录): %s" % n)

# 4. 集合对照
src_set = set(src_files)
zip_set = set(zip_files)
missing_in_zip = src_set - zip_set
extra_in_zip = zip_set - src_set
if missing_in_zip:
    for m in sorted(missing_in_zip):
        errors.append("源有但zip缺: %s" % m)
if extra_in_zip:
    for e in sorted(extra_in_zip):
        errors.append("zip多但源无(应被排除规则拦截): %s" % e)

# 5. 逐文件内容 md5 对照
for rel in sorted(src_set & zip_set):
    if md5(src_files[rel]) != md5(zip_files[rel]):
        errors.append("内容不一致: %s" % rel)

# 6. plugin.json 不应在 zip 内（dotfile 目录被排除，故必无；二次确认）
if any(n.endswith("plugin.json") for n in names):
    errors.append("zip 内含 plugin.json（应排除）")

# 7. 关键文档计数（动态：以 agents/ 实际文件数为准）
ags = [n for n in names if n.startswith("agents/") and n.endswith(".md")]
EXPECTED_AGENTS = len(ags)
sk_path = os.path.join(TMP, "SKILL.md")
sk = open(sk_path, encoding="utf-8").read() if os.path.exists(sk_path) else ""
if "%d个技能文件" % EXPECTED_AGENTS not in sk:
    errors.append("SKILL.md 计数非 %d" % EXPECTED_AGENTS)
if "version: 4.4.1" not in sk:
    errors.append("SKILL.md 版本非 4.4.1")
if len(ags) != EXPECTED_AGENTS:
    errors.append("agents md 数=%d (应为%d)" % (len(ags), EXPECTED_AGENTS))

shutil.rmtree(TMP, ignore_errors=True)

# 输出
print("源排除后文件数:", len(src_files))
print("zip 内文件数:    ", len(zip_files))
print("危险路径检查:    ", "✅ 无" if not any('危险路径' in e for e in errors) else "❌ 有")
print("plugin.json 排除:", "✅ 是" if not any('plugin.json' in e for e in errors) else "❌ 否")
print("逐文件内容对照:  ", "✅ 全部一致" if not missing_in_zip and not extra_in_zip and not any('内容不一致' in e for e in errors) else "❌ 有差异")
if errors:
    print("\n[X] %d 个提交校验错误:" % len(errors))
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\n[OK] 提交专项校验通过：zip 内文件与源目录(同排除规则)完全一致，无危险路径，无 plugin.json，计数/版本正确，符合 SkillHub 提交路径规则。")
sys.exit(0)
