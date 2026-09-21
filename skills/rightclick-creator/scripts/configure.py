#!/usr/bin/env python3
"""
右键神器 配置工具
供 AI（WorkBuddy / Claude）调用，写入 API Key 配置
"""

import json
import argparse
from pathlib import Path

CONFIG_DIR = Path.home() / ".rightclick-creator" / "config"

TOOL_CONFIGS = {
    "infographic": {
        "file": "infographic.json",
        "schema": {"deepseek_api_key": "", "qwen_api_key": ""},
        "description": "生成信息图（DeepSeek / 通义千问）",
    },
    "md-clean": {
        "file": "md_cleaner.json",
        "schema": {"api_key": "", "model": "auto", "base_url": "dashscope.aliyuncs.com"},
        "description": "MD整理（通义千问）",
    },
}


def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config(tool_id: str) -> dict:
    """加载指定工具的配置"""
    ensure_config_dir()
    config_path = CONFIG_DIR / TOOL_CONFIGS[tool_id]["file"]
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return TOOL_CONFIGS[tool_id]["schema"].copy()


def save_config(tool_id: str, config: dict):
    """保存指定工具的配置"""
    ensure_config_dir()
    config_path = CONFIG_DIR / TOOL_CONFIGS[tool_id]["file"]
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def set_key(tool_id: str, key_name: str, key_value: str):
    """设置单个 API Key"""
    if tool_id not in TOOL_CONFIGS:
        print(f"错误：未知工具 '{tool_id}'")
        print(f"可用工具: {', '.join(TOOL_CONFIGS.keys())}")
        return False

    config = load_config(tool_id)
    config[key_name] = key_value
    save_config(tool_id, config)
    print(f"✅ 已保存 {TOOL_CONFIGS[tool_id]['description']} 的 {key_name}")
    return True


def set_json(tool_id: str, json_str: str):
    """通过 JSON 字符串批量设置配置"""
    if tool_id not in TOOL_CONFIGS:
        print(f"错误：未知工具 '{tool_id}'")
        print(f"可用工具: {', '.join(TOOL_CONFIGS.keys())}")
        return False

    try:
        updates = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"错误：无效的 JSON 字符串: {e}")
        return False

    config = load_config(tool_id)
    config.update(updates)
    save_config(tool_id, config)
    print(f"✅ 已更新 {TOOL_CONFIGS[tool_id]['description']} 配置")
    for k, v in updates.items():
        masked = v[:8] + "..." + v[-4:] if len(v) > 16 else "***"
        print(f"   {k}: {masked}")
    return True


def show_status():
    """显示所有工具的配置状态"""
    ensure_config_dir()
    print("=" * 50)
    print("rightclick-creator API Key 配置状态")
    print("=" * 50)

    for tool_id, meta in TOOL_CONFIGS.items():
        config_path = CONFIG_DIR / meta["file"]
        print(f"\n📦 {meta['description']}")
        print(f"   配置文件: {config_path}")

        if not config_path.exists():
            print(f"   状态: ❌ 未配置")
            continue

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"   状态: ⚠️ 读取失败 ({e})")
            continue

        has_any_key = False
        for k, v in config.items():
            if "key" in k.lower() and v:
                masked = v[:8] + "..." + v[-4:] if len(v) > 16 else "***"
                print(f"   ✅ {k}: {masked}")
                has_any_key = True

        if not has_any_key:
            print(f"   状态: ⚠️ 配置文件存在但 API Key 未设置")

    print(f"\n配置目录: {CONFIG_DIR}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="rightclick-creator 配置工具 - 供 AI 调用写入 API Key"
    )
    parser.add_argument("tool", nargs="?", help="工具 ID (infographic | md-clean)")
    parser.add_argument("--set-key", metavar="NAME=VALUE", help="设置单个 key，如 deepseek_api_key=sk-xxx")
    parser.add_argument("--json", metavar="JSON", help="通过 JSON 字符串批量设置，如 '{\"api_key\":\"sk-xxx\"}'")
    parser.add_argument("--status", action="store_true", help="显示所有工具的配置状态")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if not args.tool:
        parser.print_help()
        print(f"\n可用工具:")
        for tid, meta in TOOL_CONFIGS.items():
            print(f"  {tid:12s} - {meta['description']}")
        return

    if args.set_key:
        if "=" not in args.set_key:
            print("错误：--set-key 格式为 NAME=VALUE")
            return
        key_name, key_value = args.set_key.split("=", 1)
        set_key(args.tool, key_name, key_value)
    elif args.json:
        set_json(args.tool, args.json)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
