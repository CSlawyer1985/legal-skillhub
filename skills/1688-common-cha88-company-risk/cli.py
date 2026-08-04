#!/usr/bin/env python3
"""
1688-common-cha88-company-risk —— 88查公司风险查询工具 CLI 统一入口

用法：
    python3 cli.py companyRisk --socialCreditCode "统一社会信用代码"
    python3 cli.py companyRisk --companyId "企业ID" --page 1 --pageSize 10

Usage:
    python3 cli.py <command> [options]

Commands（更多参数见项目根目录 SKILL.md）:
    companyRisk    公司风险查询    python3 cli.py companyRisk --socialCreditCode "91441881577945666N"
    configure      配置 AK         python3 cli.py configure YOUR_AK

输出 JSON：{"success": bool, "markdown": str, "data": {...}}
"""

import json
import os
import sys
import importlib

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def _discover_capabilities() -> dict:
    """扫描 capabilities/*/cmd.py，自动注册命令"""
    commands = {}
    caps_dir = os.path.join(SCRIPTS_DIR, "capabilities")

    if not os.path.isdir(caps_dir):
        return commands

    for name in sorted(os.listdir(caps_dir)):
        cmd_path = os.path.join(caps_dir, name, "cmd.py")
        if not os.path.isfile(cmd_path):
            continue
        module_path = f"capabilities.{name}.cmd"
        try:
            mod = importlib.import_module(module_path)
            cmd_name = getattr(mod, 'COMMAND_NAME', name)
            commands[cmd_name] = module_path
        except Exception:
            pass

    return commands


def _usage(commands: dict):
    lines = ["**1688-common-cha88-company-risk 用法**\n", "```"]
    for name in sorted(commands):
        try:
            mod = importlib.import_module(commands[name])
            desc = getattr(mod, 'COMMAND_DESC', '')
            lines.append(f"python3 cli.py {name:<16} {desc}")
        except Exception:
            lines.append(f"python3 cli.py {name}")
    lines.append("```")

    print(json.dumps({
        "success": False,
        "data": {},
        "markdown": "\n".join(lines),
    }, ensure_ascii=False, indent=2))


def main():
    commands = _discover_capabilities()

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        _usage(commands)
        sys.exit(1)

    cmd = sys.argv[1]
    module_path = commands[cmd]

    sys.argv = [f"cli.py {cmd}"] + sys.argv[2:]

    module = importlib.import_module(module_path)
    module.main()

    # 每次命令执行后上报埋点，失败不影响主流程
    try:
        from _tracker import report_skill_usage
        report_skill_usage()
    except Exception:
        pass


if __name__ == "__main__":
    main()
