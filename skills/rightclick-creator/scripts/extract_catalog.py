#!/usr/bin/env python3
"""
extract_catalog.py — 一次性工具
==============================
从 ~/Library/Services/ 现有 workflow 批量提取 COMMAND_STRING，
生成 references/tools_catalog.json 初稿。

用法：
  python3 extract_catalog.py

输出：
  references/tools_catalog.json（覆盖已有文件）

注意：
  此工具仅用于初始化或更新 catalog。
  生成后需要手动补充 description、dependencies、path_mappings 等字段。
"""

import plistlib
import json
import sys
from pathlib import Path


SERVICES_DIR = Path.home() / "Library" / "Services"
OUTPUT_PATH = Path(__file__).parent.parent / "references" / "tools_catalog.json"


def extract_tool(name: str) -> dict:
    """从单个 workflow 提取信息"""
    wf = SERVICES_DIR / f"{name}.workflow"
    wflow = wf / "Contents" / "document.wflow"
    info = wf / "Contents" / "Info.plist"

    entry = {"name": name}

    # 提取 COMMAND_STRING
    with open(wflow, 'rb') as f:
        data = plistlib.load(f)
    actions = data.get('actions', [])
    for aw in actions:
        action = aw.get('action', {})
        params = action.get('ActionParameters', {})
        if 'COMMAND_STRING' in params:
            entry['shell_script'] = params['COMMAND_STRING']
            break

    # 提取 Info.plist
    try:
        with open(info, 'rb') as f:
            info_data = plistlib.load(f)
        ns_services = info_data.get('NSServices', [])
        if ns_services:
            s = ns_services[0]
            entry['menu_name'] = s.get('NSMenuItem', {}).get('default', name)
            entry['file_types'] = s.get('NSSendFileTypes', ['public.item'])
    except Exception:
        entry['file_types'] = ['public.item']

    return entry


def main():
    # 目标工具列表
    targets = [
        "word整理", "Word表格横排", "Excel格式整理", "docx2pdf",
        "MD转Word", "生成信息图", "PDF转MD", "MD整理"
    ]

    catalog = {
        "version": "1.0",
        "seed_workflow": "docx2pdf",
        "install_base_dir": "~/.rightclick-creator",
        "tools": []
    }

    print("🔍 扫描现有 workflow...\n")
    for name in targets:
        wf = SERVICES_DIR / f"{name}.workflow"
        if not wf.exists():
            print(f"❌ {name}: workflow 不存在")
            continue
        try:
            tool = extract_tool(name)
            # 添加占位字段
            tool["id"] = name.lower().replace(" ", "-").replace("转", "2").replace("整理", "clean").replace("生成", "gen")
            tool["category"] = "待分类"
            tool["description"] = "待补充"
            tool["dependencies"] = []
            tool["script_files"] = []
            tool["script_dir"] = None
            tool["path_mappings"] = {}
            catalog["tools"].append(tool)
            print(f"✅ {name}: 提取 {len(tool.get('shell_script', ''))} 字符")
        except Exception as e:
            print(f"❌ {name}: {e}")

    # 写入
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Catalog 已保存到：{OUTPUT_PATH}")
    print(f"   共 {len(catalog['tools'])} 个工具")
    print("\n⚠️  提醒：请手动补充以下字段：")
    print("   - id（唯一标识）")
    print("   - category（分类）")
    print("   - description（描述）")
    print("   - dependencies（依赖）")
    print("   - script_files / script_dir（Python脚本）")
    print("   - path_mappings（路径替换规则）")


if __name__ == "__main__":
    main()
