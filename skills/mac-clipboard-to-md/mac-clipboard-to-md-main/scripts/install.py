#!/usr/bin/env python3
"""
mac-clipboard-to-md 安装器
通过 plistlib 构造 .workflow 包，安装到 ~/Library/Services/
"""
from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
import uuid

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.expanduser("~/Library/Services")

TOOLS = {
    "work-record": {
        "template": os.path.join(SKILL_DIR, "work-record.applescript"),
        "service_name": "保存到 Work Record",
        "placeholder_path": "/Users/你的用户名/Documents/Work record.md",
        "description": "静默追加到 Work record.md",
    },
    "brain-dump": {
        "template": os.path.join(SKILL_DIR, "brain-dump.applescript"),
        "service_name": "Brain Dump",
        "placeholder_path": "/Users/你的用户名/Documents/brain dump/",
        "description": "交互式保存到 brain dump/ 文件夹",
    },
}


def gen_uuid() -> str:
    return str(uuid.uuid4()).upper()


def read_template(tool_name: str, user_path: str) -> str:
    """读取 Applescript 模板，替换占位路径为用户实际路径"""
    info = TOOLS[tool_name]
    with open(info["template"], "r", encoding="utf-8") as f:
        source = f.read()

    if info["placeholder_path"] not in source:
        print(f"  ⚠ 未找到占位路径 '{info['placeholder_path']}'，尝试直接替换")
        # 尝试匹配任何以 /Users/ 开头的路径
        import re
        source = re.sub(
            r'("/Users/[^"]*")',
            f'"{user_path}"',
            source,
        )
    else:
        source = source.replace(info["placeholder_path"], user_path)

    return source


def build_workflow(tool_name: str, apple_script_source: str) -> dict:
    """构建 document.wflow 的 plist 结构"""
    input_uuid = gen_uuid()
    output_uuid = gen_uuid()
    action_uuid = gen_uuid()
    arg_uuid = gen_uuid()

    action = {
        "action": {
            "AMAccepts": {
                "Container": "List",
                "Optional": True,
                "Types": ["com.apple.applescript.object"],
            },
            "AMActionVersion": "1.0.2",
            "AMApplication": ["自动操作"],
            "AMParameterProperties": {"source": {}},
            "AMProvides": {
                "Container": "List",
                "Types": ["com.apple.applescript.object"],
            },
            "ActionBundlePath": "/System/Library/Automator/Run AppleScript.action",
            "ActionName": "运行AppleScript",
            "ActionParameters": {
                "source": apple_script_source,
            },
            "BundleIdentifier": "com.apple.Automator.RunScript",
            "CFBundleVersion": "1.0.2",
            "CanShowSelectedItemsWhenRun": False,
            "CanShowWhenRun": True,
            "Category": ["AMCategoryUtilities"],
            "Class Name": "RunScriptAction",
            "InputUUID": input_uuid,
            "Keywords": ["运行"],
            "OutputUUID": output_uuid,
            "UUID": action_uuid,
            "UnlocalizedApplications": ["Automator"],
            "arguments": {
                "0": {
                    "default value": 'on run {input, parameters}\n\t\n\t(* Your script goes here *)\n\t\n\treturn input\nend run',
                    "name": "source",
                    "required": "0",
                    "type": "0",
                    "uuid": arg_uuid,
                },
            },
            "isViewVisible": 1,
            "location": "713.500000:1112.000000",
            "nibPath": "/System/Library/Automator/Run AppleScript.action/Contents/Resources/Base.lproj/main.nib",
        },
        "isViewVisible": 1,
    }

    workflow = {
        "AMApplicationBuild": "528",
        "AMApplicationVersion": "2.10",
        "AMDocumentVersion": "2",
        "actions": [action],
        "connectors": {},
        "workflowMetaData": {
            "applicationBundleIDsByPath": {},
            "applicationPaths": [],
            "inputTypeIdentifier": "com.apple.Automator.nothing",
            "outputTypeIdentifier": "com.apple.Automator.nothing",
            "presentationMode": 11,
            "processesInput": False,
            "serviceInputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": False,
            "systemImageName": "NSActionTemplate",
            "useAutomaticInputType": False,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }

    return workflow


def build_info_plist(service_name: str) -> dict:
    """构建 Info.plist"""
    return {
        "NSServices": [
            {
                "NSBackgroundColorName": "background",
                "NSIconName": "NSActionTemplate",
                "NSMenuItem": {
                    "default": service_name,
                },
                "NSMessage": "runWorkflowAsService",
            },
        ],
    }


def install(tool_name: str, user_path: str) -> bool:
    """安装单个工具的 workflow"""
    if tool_name not in TOOLS:
        print(f"  ✗ 未知工具: {tool_name}")
        return False

    info = TOOLS[tool_name]
    service_name = info["service_name"]
    workflow_dir = os.path.join(SERVICES_DIR, f"{service_name}.workflow")

    # 1. 读取并修改模板
    print(f"  📄 读取模板: {os.path.basename(info['template'])}")
    source = read_template(tool_name, user_path)

    # 2. 清理已有的 workflow
    if os.path.exists(workflow_dir):
        print(f"  🗑  移除已有 workflow: {service_name}.workflow")
        shutil.rmtree(workflow_dir)

    # 3. 构建 plist
    workflow_plist = build_workflow(tool_name, source)
    info_plist = build_info_plist(service_name)

    # 4. 写入 .workflow 包
    os.makedirs(os.path.join(workflow_dir, "Contents"), exist_ok=True)

    wflow_path = os.path.join(workflow_dir, "Contents", "document.wflow")
    with open(wflow_path, "wb") as f:
        plistlib.dump(workflow_plist, f)
    print(f"  ✅ 写入 document.wflow")

    info_path = os.path.join(workflow_dir, "Contents", "Info.plist")
    with open(info_path, "wb") as f:
        plistlib.dump(info_plist, f)
    print(f"  ✅ 写入 Info.plist")

    return True


def refresh_services():
    """刷新 services 缓存并重启 Finder"""
    print("  🔄 刷新 Services 缓存...")
    subprocess.run(["/System/Library/CoreServices/pbs", "-flush"], capture_output=True)
    print("  🔄 重启 Finder...")
    subprocess.run(["killall", "Finder"], capture_output=True)
    print("  ✅ Finder 已重启，右键菜单已刷新")


def list_tools():
    """列出可用工具"""
    print("可用工具：")
    for name, info in TOOLS.items():
        print(f"  {name:15s} → {info['description']}")
        print(f"  {'':15s}   服务名: {info['service_name']}")
        print()


def interactive_install():
    """交互模式：无参数时通过终端问答引导安装"""
    print("\n📋 可用工具：")
    for name, info in TOOLS.items():
        print(f"  {name:15s} → {info['description']}")

    choice = input("\n你想安装哪个？（work-record / brain-dump / all）: ").strip().lower()

    tools_to_install = []
    if choice == "all":
        tools_to_install = list(TOOLS.keys())
    elif choice in TOOLS:
        tools_to_install = [choice]
    else:
        print("✗ 无效选择")
        sys.exit(1)

    install_plan = {}
    for name in tools_to_install:
        default_path = TOOLS[name]["placeholder_path"]
        user_path = input(f"\n{name} 的保存路径（直接回车用默认 {default_path}）: ").strip()
        if not user_path:
            user_path = default_path
        install_plan[name] = user_path

    success = True
    for name, path in install_plan.items():
        print(f"\n📦 安装 {name}...")
        if not install(name, path):
            success = False

    if success:
        refresh_services()
        print(f"\n✅ 安装完成！请在「系统设置 → 键盘 → 键盘快捷键 → 服务」中设置快捷键")


def main():
    parser = argparse.ArgumentParser(description="mac-clipboard-to-md 安装器")
    parser.add_argument("--tool", choices=list(TOOLS.keys()) + ["all"],
                        help="要安装的工具名（all = 全部安装）")
    parser.add_argument("--path", help="保存路径（work-record 用文件路径，brain-dump 用目录路径）")
    parser.add_argument("--work-record-path", help="work-record 的保存文件路径")
    parser.add_argument("--brain-dump-path", help="brain-dump 的保存文件夹路径")
    parser.add_argument("--list", action="store_true", help="列出可用工具")

    args = parser.parse_args()

    if args.list:
        list_tools()
        return

    if not args.tool and not args.list:
        interactive_install()
        return

    # 收集要安装的工具和路径
    install_plan = {}

    if args.tool == "all":
        for name in TOOLS:
            path = args.path
            if name == "work-record" and args.work_record_path:
                path = args.work_record_path
            elif name == "brain-dump" and args.brain_dump_path:
                path = args.brain_dump_path
            if not path:
                print(f"  ✗ {name}: 未指定路径，跳过")
                continue
            install_plan[name] = path
    else:
        path = args.path
        if args.tool == "work-record" and args.work_record_path:
            path = args.work_record_path
        elif args.tool == "brain-dump" and args.brain_dump_path:
            path = args.brain_dump_path
        if not path:
            print(f"  ✗ 请通过 --path 指定保存路径")
            sys.exit(1)
        install_plan[args.tool] = path

    # 执行安装
    success = True
    for name, path in install_plan.items():
        print(f"\n📦 安装 {name}...")
        if not install(name, path):
            success = False

    if success:
        refresh_services()
        print(f"\n✅ 安装完成！")
        for name in install_plan:
            info = TOOLS[name]
            print(f"   → {info['service_name']} 已安装到 ~/Library/Services/")
        print(f"\n📌 必须设置快捷键才能使用：")
        print(f"   「系统设置 → 键盘 → 键盘快捷键 → 服务」")
        print(f"   找到对应名称，点击右侧空白区域按下快捷键")
    else:
        print(f"\n⚠ 部分工具安装失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
