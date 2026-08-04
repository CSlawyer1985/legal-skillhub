# -*- coding: utf-8 -*-
"""
律师助手 · 双平台 plugin.json 生成脚本（P2-2 落地）

设计：
- `_plugin_base.json` 为两个平台共享的公共权威源（含 skills / teamInfo / author /
  version / name 等除 `platforms` 外的所有字段）。
- 本脚本读 `_plugin_base.json` + 下方 `PLATFORMS` 平台差异，合并生成
  `.codebuddy-plugin/plugin.json` 与 `.workbuddy-plugin/plugin.json`，
  消除手动维护两份 34KB 配置、需保持同步的负担。

维护约定：
- 增删技能 / 改公共字段 → 编辑 `_plugin_base.json`，跑本脚本即同步两平台。
- 改平台差异 → 改下方 `PLATFORMS` 常量。
- 首次运行（_plugin_base.json 不存在）会自动从现有两 plugin.json 抽取公共部分初始化。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, "_plugin_base.json")

# 平台差异：仅 platforms 一个字段不同
PLATFORMS = {
    "codebuddy": ["codebuddy", "skillhub", "windsurf"],
    "workbuddy": ["workbuddy", "skillhub"],
}
TARGETS = {
    "codebuddy": os.path.join(ROOT, ".codebuddy-plugin", "plugin.json"),
    "workbuddy": os.path.join(ROOT, ".workbuddy-plugin", "plugin.json"),
}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, p):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


# 首次初始化：从现有两 plugin.json 抽取公共部分（去 platforms）写入 _plugin_base.json
if not os.path.exists(BASE):
    a = load(TARGETS["codebuddy"])
    b = load(TARGETS["workbuddy"])
    base = {}
    for k in a:
        if k == "platforms":
            continue
        if k in b and b[k] == a[k]:
            base[k] = a[k]
    dump(base, BASE)
    print("[init] 已抽取 _plugin_base.json，含 %d 个公共字段" % len(base))

base = load(BASE)

# 生成两平台 plugin.json，并校验与原始语义完全一致
for plat, path in TARGETS.items():
    merged = dict(base)  # 保持 base 键顺序
    merged["platforms"] = PLATFORMS[plat]
    dump(merged, path)
    orig = load(path)
    assert merged == orig, "生成结果与原始不一致: %s" % plat
    print("[ok] 生成 %s  (platforms=%s)" %
          (os.path.relpath(path, ROOT), PLATFORMS[plat]))

print("P2-2 完成：_plugin_base.json 为公共权威源，两平台 plugin.json 由脚本生成且与原值等价。")
