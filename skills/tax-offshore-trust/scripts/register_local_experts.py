#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register_local_experts.py  ·  双市场分发包自动注册本地专家钩子（骨架 v1）

功能：把 experts_build/ 下的专家/团队包复制到本机 WorkBuddy「我的专家」市场，
      并写入 marketplace.json 注册条目。复用 WD register_expert.py 的写入契约：
        - 目标：<WORKBUDDY_CONFIG_DIR|~/.workbuddy>/plugins/marketplaces/my-experts/
        - manifest：<marketplace_dir>/.codebuddy-plugin/marketplace.json
                     {name, description, plugins:[{name, source, description}]}
        - source = ./plugins/<expert_dir.name>
        - 幂等：已注册则跳过/更新；先备份后写；提供 --unregister
安全边界：仅写本机 ~/.workbuddy，无外呼、不采集指纹、不共享 key。

触发方式（双轨，见方案 §5.2）：
  A. 单包内嵌：分发包 zip 内置本脚本，装包后引导/自动运行
  B. 总装包：财税专家团队总装包.zip 内含全部专家 + 本脚本，一次装齐

仅落库/本机注册，不触碰云端发布。
"""

import sys
import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
EXPERTS_SRC = ROOT / "experts_build"  # agents/ + teams/
MARKER_SOURCE = ".from-tax-matrix"     # 来源标记，便于批量卸载


def get_marketplace_base():
    config = os.environ.get("WORKBUDDY_CONFIG_DIR", "").strip()
    if not config:
        config = str(Path.home() / ".workbuddy")
    return Path(config) / "plugins" / "marketplaces" / "my-experts"


def find_plugin_json(d: Path):
    for meta in [".codebuddy-plugin", ".workbuddy-plugin"]:
        c = d / meta / "plugin.json"
        if c.exists():
            return c
    return None


def validate(d: Path):
    """轻量完整性校验（对齐 WD validate_expert_completeness 关键项）。"""
    errors = []
    pj = find_plugin_json(d)
    if not pj:
        return ["缺 plugin.json（须位于 .codebuddy-plugin/ 或 .workbuddy-plugin/）"]
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
    except Exception as e:
        return ["plugin.json 非法 JSON: %s" % e]
    for f in ["name", "description", "expertType"]:
        if not data.get(f) or "[TODO" in str(data.get(f, "")):
            errors.append("字段 %s 缺失或含 [TODO]" % f)
    dn = data.get("displayName", {})
    if isinstance(dn, dict):
        if not dn.get("zh") and not dn.get("en"):
            errors.append("displayName 空")
    ad = d / "agents"
    if not ad.exists() or not list(ad.glob("*.md")):
        errors.append("agents/ 缺 .md")
    return errors


def register_one(d: Path, marketplace_dir: Path, dry_run=False):
    pj = find_plugin_json(d)
    data = json.loads(pj.read_text(encoding="utf-8"))
    name = data.get("name", d.name)
    desc = data.get("description", "")
    target = marketplace_dir / "plugins" / d.name

    # 幂等：已存在则跳过
    if target.exists() and not dry_run:
        print("⏭️  已注册，跳过：%s" % name)
        return "skip"

    if dry_run:
        print("🔍 [dry-run] 将注册：%s → %s" % (name, target))
        return "dry"

    # 复制专家包
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(d, target)
    # 来源标记
    (target / MARKER_SOURCE).write_text(datetime.now().isoformat(), encoding="utf-8")

    # 写 marketplace.json（先备后写）
    manifest_path = marketplace_dir / ".codebuddy-plugin" / "marketplace.json"
    if manifest_path.exists():
        shutil.copy2(manifest_path, str(manifest_path) + ".bak")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"name": "my-experts", "description": "my-experts marketplace (auto-generated)", "plugins": []}

    source = "./plugins/%s" % d.name
    plugins = manifest.setdefault("plugins", [])
    for p in plugins:
        if p.get("source") == source or p.get("name") == name:
            p.update({"name": name, "source": source, "description": desc})
            break
    else:
        plugins.append({"name": name, "source": source, "description": desc})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ 已注册：%s" % name)
    return "ok"


def unregister_all(marketplace_dir: Path):
    manifest_path = marketplace_dir / ".codebuddy-plugin" / "marketplace.json"
    if not manifest_path.exists():
        print("ℹ️  无 marketplace.json，无需卸载")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    kept = []
    removed = []
    plugins_dir = marketplace_dir / "plugins"
    for p in manifest.get("plugins", []):
        src = p.get("source", "")
        name = p.get("name", "")
        # 仅移除来自本矩阵（名称前缀 expert- / expert-pod-）的
        if name.startswith("expert-") and src.startswith("./plugins/"):
            tgt = plugins_dir / src.replace("./plugins/", "")
            if tgt.exists():
                shutil.rmtree(tgt)
            removed.append(name)
        else:
            kept.append(p)
    shutil.copy2(manifest_path, str(manifest_path) + ".bak")
    manifest["plugins"] = kept
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("🗑️  已卸载 %d 个本矩阵专家：%s" % (len(removed), ", ".join(removed) if removed else "无"))


def main():
    ap = argparse.ArgumentParser(description="自动注册本地专家/团队到 WorkBuddy 我的专家")
    ap.add_argument("--src", default=str(EXPERTS_SRC), help="专家包源目录（默认 experts_build）")
    ap.add_argument("--marketplace-dir", default=None, help="自定义 marketplace 根目录")
    ap.add_argument("--dry-run", action="store_true", help="仅预览不写入")
    ap.add_argument("--unregister", action="store_true", help="卸载本矩阵注册的全部专家")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    if not src.exists():
        print("❌ 源目录不存在：%s" % src)
        sys.exit(1)

    base = Path(args.marketplace_dir).resolve() if args.marketplace_dir else get_marketplace_base()
    plugins_dir = base / "plugins"

    if args.unregister:
        unregister_all(base)
        return

    print("📋 目标市场：%s" % base)
    print("📦 源目录：%s" % src)
    if args.dry_run:
        print("🔍 DRY-RUN 模式（不写入本机）\n")

    count = 0
    for sub in ["agents", "teams"]:
        d = src / sub
        if not d.exists():
            continue
        for pkg in sorted(d.iterdir()):
            if not pkg.is_dir():
                continue
            errs = validate(pkg)
            if errs:
                print("❌ 跳过 %s（不完整）：%s" % (pkg.name, "; ".join(errs)))
                continue
            r = register_one(pkg, base, dry_run=args.dry_run)
            if r in ("ok", "dry"):
                count += 1
    print("\n🎉 注册完成：本次处理 %d 个专家包（已注册/预览）" % count)
    if not args.dry_run:
        print("   专家已出现在 WorkBuddy「专家中心 → 我的专家」，可一句话唤醒或卡片点击调用。")


if __name__ == "__main__":
    main()
