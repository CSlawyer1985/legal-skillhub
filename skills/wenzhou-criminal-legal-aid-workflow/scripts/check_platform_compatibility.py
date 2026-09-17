#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


PLATFORMS = {
    "codex": {
        "display_name": "Codex Desktop / CLI",
        "tier": "完整验证",
        "install": "将完整目录放入或链接到用户/项目 skills 目录，并确认新会话可发现该 Skill。",
        "notes": ["保留 agents/openai.yaml。", "适合真实案件的本地扫描、生成和批量归档。"],
    },
    "workbuddy": {
        "display_name": "WorkBuddy",
        "tier": "推荐入口",
        "install": "导入完整 Skill 目录或 ZIP；必须保留 scripts、references 和 assets。",
        "notes": ["确认运行壳允许访问案件目录并执行本地 Python。", "仅能读取说明而不能执行脚本时，按指导模式降级。"],
    },
    "claude": {
        "display_name": "Claude Code",
        "tier": "标准兼容",
        "install": "安装到 ~/.claude/skills/wenzhou-criminal-legal-aid-workflow/，或作为项目 Skill 安装。",
        "notes": ["可自动触发，也可显式调用 /wenzhou-criminal-legal-aid-workflow。", "首次真实案件运行前应完成一轮本地样例测试。"],
    },
    "gemini": {
        "display_name": "Gemini CLI",
        "tier": "标准兼容",
        "install": "使用 gemini skills install/link 安装完整目录，并用 /skills list 确认发现。",
        "notes": ["Skill 激活和 shell 执行可能需要用户确认。", "首次真实案件运行前应完成一轮本地样例测试。"],
    },
    "opencode": {
        "display_name": "OpenCode",
        "tier": "需轻量适配",
        "install": "目录名使用 wenzhou-criminal-legal-aid-workflow，并放入 .opencode/skills 或兼容 skills 目录。",
        "notes": ["确认 skill、read、bash 和外部案件目录权限。", "目录名应与 SKILL.md 的 name 保持一致。"],
    },
    "web": {
        "display_name": "纯网页聊天平台",
        "tier": "仅限脱敏演示",
        "install": "仅使用脱敏示例和公开模板演示，不上传真实案件材料。",
        "notes": ["通常不能稳定访问本地案件目录或调用本地 OCR 工具。", "不作为真实受援人材料的推荐运行环境。"],
    },
}


def executable_status(name: str) -> dict[str, object]:
    path = shutil.which(name)
    return {"available": bool(path), "path": path or ""}


def build_report(skill_root: Path, platform: str) -> dict[str, object]:
    required_files = [
        "SKILL.md",
        "scripts/generate_criminal_legal_aid_set.py",
        "scripts/extract_case_timeline.py",
        "references/charge-law-library.json",
        "assets/template-packs/wenzhou/manifest.json",
    ]
    files = {item: (skill_root / item).is_file() for item in required_files}
    python_ok = sys.version_info >= (3, 9)
    docx_ok = importlib.util.find_spec("docx") is not None
    core_ok = python_ok and docx_ok and all(files.values())
    ocr_tools = {name: executable_status(name) for name in ("pdftotext", "pdftoppm", "pdfinfo", "tesseract")}
    ocr_ready = all(value["available"] for value in ocr_tools.values())
    selected = PLATFORMS[platform]
    return {
        "platform": platform,
        "display_name": selected["display_name"],
        "compatibility_tier": selected["tier"],
        "core_generation_ready": core_ok,
        "local_ocr_toolchain_ready": ocr_ready,
        "python": {"version": sys.version.split()[0], "meets_3_9": python_ok},
        "python_docx": docx_ok,
        "required_files": files,
        "local_tools": ocr_tools,
        "install_guidance": selected["install"],
        "platform_notes": selected["notes"],
        "manual_checks": [
            "Agent能够读取Skill目录内的references与assets。",
            "Agent获得案件目录的最小必要读写权限。",
            "真实案件材料不上传到公共Skill包或未经确认的云端服务。",
            "所有OCR日期和生成文书均经承办律师复核。",
        ],
    }


def print_text(report: dict[str, object]) -> None:
    print(f"平台：{report['display_name']}（{report['compatibility_tier']}）")
    print(f"核心文书生成：{'可用' if report['core_generation_ready'] else '未通过'}")
    print(f"本地扫描件OCR工具链：{'可用' if report['local_ocr_toolchain_ready'] else '未完全就绪'}")
    print(f"安装建议：{report['install_guidance']}")
    print("平台注意事项：")
    for item in report["platform_notes"]:
        print(f"- {item}")
    print("仍需人工确认：")
    for item in report["manual_checks"]:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查本Skill在不同Agent平台上的本地运行条件。")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), default="codex")
    parser.add_argument("--json", action="store_true", help="输出机器可读JSON。")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    report = build_report(skill_root, args.platform)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0 if report["core_generation_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
