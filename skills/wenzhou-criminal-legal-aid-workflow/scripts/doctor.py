#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


def command_version(command: str, args: list[str]) -> str:
    executable = shutil.which(command)
    if not executable:
        return "未安装"
    result = subprocess.run([executable, *args], capture_output=True, text=True, errors="replace", check=False)
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else executable


def has_tesseract_chinese() -> bool:
    executable = shutil.which("tesseract")
    if not executable:
        return False
    result = subprocess.run([executable, "--list-langs"], capture_output=True, text=True, errors="replace", check=False)
    return result.returncode == 0 and "chi_sim" in {line.strip() for line in result.stdout.splitlines()}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查刑事法律援助Skill的生成与本地OCR环境。")
    parser.add_argument("--template-pack-dir", type=Path, help="需要检查的外部地区模板包")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    pack_dir = args.template_pack_dir.resolve() if args.template_pack_dir else skill_root / "assets" / "template-packs" / "wenzhou"

    required_errors: list[str] = []
    print("=== 核心生成环境 ===")
    print(f"[{'通过' if sys.version_info >= (3, 9) else '失败'}] Python：{sys.version.split()[0]}（要求3.9以上）")
    if sys.version_info < (3, 9):
        required_errors.append("Python版本过低")
    has_docx = importlib.util.find_spec("docx") is not None
    print(f"[{'通过' if has_docx else '失败'}] python-docx：{'已安装' if has_docx else '未安装'}")
    if not has_docx:
        required_errors.append("缺少python-docx；运行 pip install -r requirements.txt")
    manifest = pack_dir / "manifest.json"
    print(f"[{'通过' if manifest.is_file() else '失败'}] 模板包：{pack_dir}")
    if not manifest.is_file():
        required_errors.append("模板包缺少manifest.json")
    charge_library = skill_root / "references" / "charge-law-library.json"
    print(f"[{'通过' if charge_library.is_file() else '失败'}] 常见罪名基础说明库：{charge_library}")
    if not charge_library.is_file():
        required_errors.append("缺少常见罪名基础说明库")

    print("\n=== 本地材料扫描/OCR环境 ===")
    print(f"[{'可用' if shutil.which('pdftotext') else '缺失'}] pdftotext：{command_version('pdftotext', ['-v'])}")
    print(f"[{'可用' if shutil.which('pdftoppm') else '缺失'}] pdftoppm：{command_version('pdftoppm', ['-v'])}")
    print(f"[{'可用' if shutil.which('tesseract') else '缺失'}] tesseract：{command_version('tesseract', ['--version'])}")
    print(f"[{'可用' if has_tesseract_chinese() else '缺失'}] Tesseract简体中文模型 chi_sim")
    if not shutil.which("pdftotext"):
        print("处理建议：安装 Poppler 后才能提取PDF文字层。macOS可运行 brew install poppler。")
    if not shutil.which("pdftoppm") or not shutil.which("tesseract") or not has_tesseract_chinese():
        print("处理建议：扫描PDF/图片需 Poppler、Tesseract 和 chi_sim；缺少时仍可读取MD、TXT、DOCX及有文字层PDF。")

    print("\n=== 字体提示 ===")
    print("生成器会把温州文书属性写为：正文仿宋_GB2312四号、主标题黑体三号、正文固定行距28.5磅。")
    print("如当前电脑没有相应字体，Word可能发生字体替换；请在正式导出PDF前人工检查。Skill不捆绑第三方字体文件。")

    if required_errors:
        print("\n核心环境未通过：")
        for error in required_errors:
            print(f"- {error}")
        return 2
    print("\n核心生成环境通过。OCR项为可选能力，缺失时按上方提示补充。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
