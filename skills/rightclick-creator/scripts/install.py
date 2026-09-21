#!/usr/bin/env python3
"""
右键神器 · 多工具右键安装器
=====================================
将多个 macOS 右键工具批量安装到 ~/Library/Services/

用法：
  python3 install.py --tools word整理 MD转Word docx2pdf
  python3 install.py --all
  python3 install.py --list          # 列出可用工具
  python3 install.py --uninstall 工具名  # 卸载指定工具

遵循 macOS 右键工具天条：
  ✅ cp -R 复制种子，绝不从零创建 workflow
  ✅ plistlib 修改 COMMAND_STRING，绝不用 sed/echo/cat
  ✅ 同步时间戳保留元数据
  ✅ pbs -flush + killall Finder 刷新服务
"""

import sys
import os
import shutil
import subprocess
import plistlib
import json
import platform
import argparse
import socket
from pathlib import Path
from typing import List, Dict, Optional


# ── 路径常量 ───────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent.resolve()
CATALOG_PATH = SKILL_DIR / "references" / "tools_catalog.json"
SEED_PATH = SKILL_DIR / "assets" / "种子.workflow"
SERVICES_DIR = Path.home() / "Library" / "Services"
INSTALL_BASE = Path.home() / ".rightclick-creator"
TOOLS_DIR = INSTALL_BASE / "tools"
LOGS_DIR = INSTALL_BASE / "logs"


# ── 工具函数 ───────────────────────────────────────────────
def log(msg: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{msg}")


def abort(msg: str):
    print(f"\n❌ {msg}")
    sys.exit(1)


def load_catalog() -> dict:
    """加载工具目录"""
    if not CATALOG_PATH.exists():
        abort(f"工具目录不存在：{CATALOG_PATH}")
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_seed_workflow(catalog: dict) -> Path:
    """获取种子 workflow 路径"""
    if not SEED_PATH.exists():
        abort(f"种子 workflow 不存在：{SEED_PATH}\n")
    return SEED_PATH


# pip 包名 → import 名映射（两者不一致的情况）
PIP_IMPORT_MAP = {
    "Pillow": "PIL",
    "python-docx": "docx",
    "python-pptx": "pptx",
    "pyyaml": "yaml",
    "beautifulsoup4": "bs4",
    "scikit-learn": "sklearn",
    "opencv-python": "cv2",
    "pytesseract": "pytesseract",
}


def check_python_pkg(pkg: str) -> bool:
    """检查 Python 包是否已安装"""
    import_name = PIP_IMPORT_MAP.get(pkg, pkg)
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def detect_proxy() -> Optional[str]:
    """检测用户是否在使用代理，返回代理 URL 或 None"""
    # 1. 检查环境变量
    for env_var in ["https_proxy", "http_proxy", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"]:
        val = os.environ.get(env_var)
        if val:
            return val

    # 2. 探测常见代理工具端口
    common_proxies = [
        ("127.0.0.1", 7890),   # Clash / ClashX / Clash Verge
        ("127.0.0.1", 7891),   # Clash SOCKS5
        ("127.0.0.1", 6152),   # Surge HTTP
        ("127.0.0.1", 6153),   # Surge SOCKS5
        ("127.0.0.1", 1087),   # V2RayU HTTP
        ("127.0.0.1", 1080),   # Shadowsocks / V2Ray SOCKS5
        ("127.0.0.1", 1086),   # ShadowsocksX-NG
        ("127.0.0.1", 7897),   # Clash Verge Rev
    ]
    for host, port in common_proxies:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return f"http://{host}:{port}"
        except (OSError, socket.timeout):
            continue
    return None


def check_command(cmd: str) -> bool:
    """检查系统命令是否可用"""
    return shutil.which(cmd) is not None


# ── 预检 ──────────────────────────────────────────────────
def preflight(selected_tools: List[dict]) -> bool:
    """运行安装前预检"""
    print("\n" + "=" * 50)
    print("  rightclick-creator · 安装前预检")
    print("=" * 50)

    errors = []
    warnings = []

    # macOS 检查
    if platform.system() != "Darwin":
        abort("本工具仅支持 macOS。")

    # Python 版本
    if sys.version_info < (3, 8):
        errors.append("Python 3.8+ 是必需的。")
    else:
        log(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}", 1)

    # 系统命令白名单（这些是 brew 包名，不是 Python 包）
    # pandoc/libreoffice 无需自动安装（大且可选），poppler/tesseract/tesseract-lang 可自动装
    SYSTEM_COMMANDS = {"pandoc", "libreoffice", "poppler", "tesseract", "tesseract-lang"}
    # 标准库白名单
    STDLIB_PKGS = {"re", "os", "sys", "json", "shutil", "pathlib", "plistlib", "subprocess",
                   "tempfile", "typing", "argparse", "datetime", "base64", "textwrap",
                   "html", "urllib", "hashlib", "enum", "collections", "itertools",
                   "math", "random", "string", "csv", "zipfile", "xml", "warnings"}

    # 收集依赖
    py_deps = set()
    sys_cmds = set()
    for tool in selected_tools:
        for dep in tool.get("dependencies", []):
            dep_root = dep.split(".")[0]
            if dep_root in STDLIB_PKGS:
                continue
            if dep in SYSTEM_COMMANDS:
                sys_cmds.add(dep)
            else:
                py_deps.add(dep)

    # 检查 docx2pdf 是否需要 LibreOffice
    has_docx2pdf = any(t["id"] == "docx2pdf" for t in selected_tools)
    if has_docx2pdf:
        libreoffice_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice.bin",
            str(Path.home() / "Applications" / "LibreOffice.app" / "Contents" / "MacOS" / "soffice"),
        ]
        if not any(Path(p).exists() for p in libreoffice_paths):
            warnings.append("LibreOffice 未找到，docx2pdf 将无法工作。请运行：brew install --cask libreoffice")
        else:
            log("✅ LibreOffice 已找到", 1)

    # 检查并自动安装系统命令依赖（via brew）
    # brew 包名 → 实际检测命令名的映射（两者不一致时）
    BREW_CMD_MAP = {"poppler": "pdftoppm"}
    # 可自动安装的 brew 包（pandoc/libreoffice 太大，只警告）
    BREW_AUTO_INSTALL = {"poppler", "tesseract", "tesseract-lang"}
    # tesseract-lang 特殊检测：检查中文语言数据是否可用
    def _check_tesseract_lang() -> bool:
        try:
            r = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=5)
            return "chi_sim" in r.stdout
        except Exception:
            return False

    missing_brew = []
    for cmd in sys_cmds:
        if cmd == "tesseract-lang":
            if _check_tesseract_lang():
                log("✅ tesseract-lang (中文) 已安装", 1)
            else:
                missing_brew.append(cmd)
        else:
            check_cmd = BREW_CMD_MAP.get(cmd, cmd)
            if check_command(check_cmd):
                log(f"✅ {cmd} 已找到", 1)
            else:
                missing_brew.append(cmd)

    if missing_brew:
        auto = [p for p in missing_brew if p in BREW_AUTO_INSTALL]
        manual = [p for p in missing_brew if p not in BREW_AUTO_INSTALL]
        if auto and check_command("brew"):
            log(f"📦 自动安装缺失的 brew 包：{', '.join(auto)}", 1)
            result = subprocess.run(
                ["brew", "install", *auto],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                log("✅ brew 包安装成功", 1)
            else:
                log(f"⚠️  自动安装失败，请手动运行：brew install {' '.join(auto)}", 1)
                if result.stderr:
                    log(f"   错误信息：{result.stderr[:200]}", 1)
        elif auto:
            # brew 本身没装，只能提示
            for p in auto:
                warnings.append(f"{p} 未找到且 Homebrew 不可用，请先安装 Homebrew 后运行：brew install {p}")
        if manual:
            for p in manual:
                install_hint = "brew install --cask libreoffice" if p == "libreoffice" else f"brew install {p}"
                warnings.append(f"{p} 未找到，依赖它的工具将无法工作。请运行：{install_hint}")

    # 检查并自动安装 Python 依赖
    missing_deps = []
    for dep in py_deps:
        if check_python_pkg(dep):
            log(f"✅ {dep} 已安装", 1)
        else:
            missing_deps.append(dep)

    if missing_deps:
        log(f"📦 自动安装缺失的 Python 包：{', '.join(missing_deps)}", 1)

        # 检测代理：有代理直接走官方源，没代理fallback国内镜像
        proxy = detect_proxy()
        installed = False

        if proxy:
            log(f"   检测到代理：{proxy}，优先使用官方源...", 2)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--proxy", proxy, *missing_deps],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                log("✅ Python 包安装成功（官方源 + 代理）", 1)
                installed = True
            else:
                log("   代理安装失败，尝试国内镜像...", 2)

        if not installed:
            # 无代理或代理失败：尝试国内镜像
            mirrors = [
                "https://pypi.tuna.tsinghua.edu.cn/simple",
                "https://mirrors.aliyun.com/pypi/simple/",
                "https://mirrors.cloud.tencent.com/pypi/simple/",
            ]
            for mirror in mirrors:
                log(f"   尝试镜像：{mirror}", 2)
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-i", mirror, "--trusted-host", mirror.split("/")[2], *missing_deps],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    log(f"✅ Python 包安装成功（{mirror.split('/')[2]}）", 1)
                    installed = True
                    break

        if not installed:
            # 最后 fallback：直连官方源（可能已配置系统代理）
            log("   尝试官方源...", 2)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing_deps],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                log("✅ Python 包安装成功（官方源）", 1)
                installed = True

        if not installed:
            # 安装失败，降级为提示（不阻断整个安装）
            log(f"⚠️  自动安装失败，请手动运行：pip3 install {' '.join(missing_deps)}", 1)
            if result.stderr:
                log(f"   错误信息：{result.stderr[:200]}", 1)

    # 检查 Node.js 依赖（天眼查等文本服务）
    has_nodejs = any(t.get("script_type") == "nodejs" for t in selected_tools)
    if has_nodejs:
        if check_command("node"):
            log("✅ Node.js 已找到", 1)
        else:
            errors.append("Node.js 未找到。天眼查工具需要 Node.js，请运行：brew install node")
        if check_command("npm"):
            log("✅ npm 已找到", 1)
        else:
            errors.append("npm 未找到。请运行：brew install node")

    # 种子 workflow 检查
    catalog = load_catalog()
    seed = get_seed_workflow(catalog)
    log(f"✅ 种子 workflow：{seed.name}", 1)

    # 检查需要 API Key 的工具配置
    api_key_tools = {
        "infographic": {
            "name": "生成信息图",
            "config_file": "infographic.json",
            "keys": ["deepseek_api_key", "qwen_api_key"]
        },
        "md-clean": {
            "name": "MD整理",
            "config_file": "md_cleaner.json",
            "keys": ["deepseek_api_key", "api_key"]
        }
    }

    config_dir = Path.home() / ".rightclick-creator" / "config"
    for tool_id, tool_info in api_key_tools.items():
        if any(t["id"] == tool_id for t in selected_tools):
            config_file = config_dir / tool_info["config_file"]
            if not config_file.exists():
                log(f"⚠️  {tool_info['name']}：请通过 AI 对话配置 API Key", 1)
            else:
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    has_key = any(config.get(k) and config.get(k) != f"your-{k}-here"
                                  for k in tool_info["keys"])
                    if has_key:
                        log(f"✅ {tool_info['name']} API Key 已配置", 1)
                    else:
                        log(f"⚠️  {tool_info['name']}：请通过 AI 对话配置 API Key", 1)
                except Exception:
                    log(f"⚠️  {tool_info['name']}：配置文件异常，请通过 AI 对话重新配置", 1)

    # 报告
    print()
    if warnings:
        for w in warnings:
            log(f"⚠️  {w}", 1)
    if errors:
        for e in errors:
            log(f"❌ {e}", 1)
        abort("预检失败，请按上述提示修复后重新运行。")

    log("✅ 预检通过", 1)
    return True


# ── 安装单个工具 ──────────────────────────────────────────
def install_tool(tool: dict, seed: Path) -> bool:
    """安装单个右键工具"""
    name = tool["name"]
    tool_id = tool["id"]
    print(f"\n  📦 安装：{name}")

    # Step 1: 安装脚本（Python 或 Node.js）
    script_dir = tool.get("script_dir")
    script_files = tool.get("script_files", [])
    script_type = tool.get("script_type", "python")
    if script_files and script_dir:
        target_dir = TOOLS_DIR / script_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        src_dir = SKILL_DIR / "scripts" / "tools" / script_dir
        for sf in script_files:
            src = src_dir / sf
            dst = target_dir / sf
            if src.exists():
                shutil.copy2(str(src), str(dst))
                os.chmod(str(dst), 0o755)
                log(f"✅ 脚本：{sf}", 2)
            else:
                log(f"❌ 脚本缺失：{src}", 2)
                return False

        # Node.js 项目：运行 npm install
        if script_type == "nodejs" and (target_dir / "package.json").exists():
            log("📦 安装 Node.js 依赖（首次可能较慢）...", 2)
            result = subprocess.run(
                ["npm", "install", "--production"],
                cwd=str(target_dir),
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                log("✅ npm 依赖安装完成", 2)
            else:
                log(f"⚠️ npm install 失败：{result.stderr[:200]}", 2)
                log("   请手动运行：cd ~/.rightclick-creator/tools/tianyancha && npm install", 2)

    # Step 2: 确保日志目录
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 3: 复制种子 workflow
    workflow_dest = SERVICES_DIR / f"{name}.workflow"
    if workflow_dest.exists():
        shutil.rmtree(str(workflow_dest))
        log("♻️  已移除旧版", 2)

    result = subprocess.run(
        ["cp", "-R", str(seed), str(workflow_dest)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log(f"❌ cp -R 失败：{result.stderr}", 2)
        return False
    log("✅ workflow 已复制", 2)

    # Step 4: 修改 COMMAND_STRING
    wflow_path = workflow_dest / "Contents" / "document.wflow"
    try:
        with open(wflow_path, 'rb') as f:
            data = plistlib.load(f)
    except Exception as e:
        log(f"❌ 解析 plist 失败：{e}", 2)
        return False

    # 获取 shell 脚本并做路径替换
    shell_script = tool.get("shell_script", "")
    path_mappings = tool.get("path_mappings", {})

    for old_path, new_path in path_mappings.items():
        shell_script = shell_script.replace(old_path, new_path)

    # 文本服务：修改 workflow 元数据
    is_text_service = tool.get("input_type") == "text"
    if is_text_service:
        meta = data.get('workflowMetaData', {})
        meta['inputTypeIdentifier'] = 'com.apple.Automator.text'
        meta['outputTypeIdentifier'] = 'com.apple.Automator.nothing'
        meta['serviceInputTypeIdentifier'] = 'com.apple.Automator.text'
        meta['serviceOutputTypeIdentifier'] = 'com.apple.Automator.nothing'
        meta['serviceProcessesInput'] = False
        data['workflowMetaData'] = meta
        log("✅ workflow 元数据已改为文本服务", 2)

    # 写入 plist
    actions = data.get('actions', [])
    if actions:
        action = actions[0].get('action', {})
        params = action.get('ActionParameters', {})
        if 'COMMAND_STRING' in params:
            params['COMMAND_STRING'] = shell_script
            log("✅ COMMAND_STRING 已更新", 2)
        else:
            log("⚠️  未找到 COMMAND_STRING 字段", 2)
            return False
    else:
        log("❌ workflow 中没有 actions", 2)
        return False

    try:
        with open(wflow_path, 'wb') as f:
            plistlib.dump(data, f, fmt=plistlib.FMT_XML)
    except Exception as e:
        log(f"❌ 写入 plist 失败：{e}", 2)
        return False

    # Step 5: 修改 Info.plist（菜单名称、文件/文本类型）
    info_path = workflow_dest / "Contents" / "Info.plist"
    try:
        with open(info_path, 'rb') as f:
            info_data = plistlib.load(f)
        ns_services = info_data.get('NSServices', [])
        if ns_services:
            ns_services[0]['NSMenuItem']['default'] = name
            if is_text_service:
                # 文本服务：删除文件类型相关字段，添加文本类型
                if 'NSSendFileTypes' in ns_services[0]:
                    del ns_services[0]['NSSendFileTypes']
                if 'NSRequiredContext' in ns_services[0]:
                    del ns_services[0]['NSRequiredContext']
                ns_services[0]['NSSendTypes'] = ['public.utf8-plain-text']
                log("✅ Info.plist 已更新为文本服务", 2)
            else:
                file_types = tool.get('file_types')
                if file_types:
                    ns_services[0]['NSSendFileTypes'] = file_types
                log("✅ Info.plist 已更新", 2)
        with open(info_path, 'wb') as f:
            plistlib.dump(info_data, f, fmt=plistlib.FMT_XML)
    except Exception as e:
        log(f"⚠️  修改 Info.plist 失败（非关键）：{e}", 2)

    # Step 6: 同步时间戳
    now_str = subprocess.run(
        ["date", "+%Y%m%d%H%M.%S"],
        capture_output=True, text=True
    ).stdout.strip()

    for dirpath, dirnames, filenames in os.walk(str(workflow_dest)):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            subprocess.run(
                ["touch", "-t", now_str, fpath],
                capture_output=True,
            )
    log("✅ 时间戳已同步", 2)

    return True


# ── 刷新服务 ──────────────────────────────────────────────
def refresh_services():
    """刷新 Services 缓存"""
    print("\n  🔄 刷新 Services 缓存...")
    subprocess.run(
        ["/System/Library/CoreServices/pbs", "-flush"],
        capture_output=True,
    )
    log("✅ pbs 缓存已刷新", 1)
    subprocess.run(
        ["killall", "Finder"],
        capture_output=True,
    )
    log("✅ Finder 已重启（约 3-5 秒后可用）", 1)


# ── 验证 ──────────────────────────────────────────────────
def verify_install(tools: List[dict]) -> bool:
    """验证安装结果"""
    print("\n  🔍 验证安装结果...")
    ok = True
    for tool in tools:
        name = tool["name"]
        workflow = SERVICES_DIR / f"{name}.workflow"
        if workflow.exists():
            log(f"✅ {name}", 1)
        else:
            log(f"❌ {name} — workflow 未找到", 1)
            ok = False
    return ok


# ── 卸载 ──────────────────────────────────────────────────
def uninstall_tool(name: str) -> bool:
    """卸载单个右键工具"""
    workflow = SERVICES_DIR / f"{name}.workflow"
    if not workflow.exists():
        log(f"⚠️  {name} 未安装", 1)
        return False
    shutil.rmtree(str(workflow))
    log(f"✅ 已卸载：{name}", 1)
    return True


# ── 列出工具 ──────────────────────────────────────────────
def list_tools(catalog: dict):
    """列出所有可用工具"""
    print("\n  📋 可用工具列表：\n")
    print(f"  {'ID':<20} {'名称':<12} {'分类':<10}  描述")
    print("  " + "-" * 70)
    for tool in catalog["tools"]:
        print(f"  {tool['id']:<20} {tool['name']:<12} {tool['category']:<10}  {tool['description']}")
    print()


# ── 主入口 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="rightclick-creator — 批量安装 macOS 右键工具"
    )
    parser.add_argument("--tools", nargs="+", help="指定要安装的工具名称（空格分隔）")
    parser.add_argument("--all", action="store_true", help="安装所有可用工具")
    parser.add_argument("--list", action="store_true", help="列出所有可用工具")
    parser.add_argument("--uninstall", help="卸载指定名称的右键工具")
    parser.add_argument("--no-refresh", action="store_true", help="不刷新 pbs 缓存（测试用）")

    args = parser.parse_args()

    catalog = load_catalog()

    # 列出工具
    if args.list:
        list_tools(catalog)
        return

    # 卸载
    if args.uninstall:
        print(f"\n🗑️  卸载：{args.uninstall}")
        if uninstall_tool(args.uninstall):
            refresh_services()
            print(f"\n✅ {args.uninstall} 已卸载")
        return

    # 确定要安装的工具
    all_tools = {t["name"]: t for t in catalog["tools"]}
    all_ids = {t["id"]: t for t in catalog["tools"]}

    if args.all:
        selected = list(catalog["tools"])
    elif args.tools:
        selected = []
        for name in args.tools:
            tool = all_tools.get(name) or all_ids.get(name)
            if tool:
                selected.append(tool)
            else:
                print(f"⚠️  未知工具：{name}")
                print(f"   可用工具：{', '.join(all_tools.keys())}")
                return
    else:
        parser.print_help()
        return

    if not selected:
        print("⚠️  未选择任何工具")
        return

    # 预检
    preflight(selected)

    # 安装
    print(f"\n{'='*50}")
    print(f"  开始安装 {len(selected)} 个右键工具")
    print(f"{'='*50}")

    seed = get_seed_workflow(catalog)
    success_count = 0
    failed_tools = []

    for tool in selected:
        if install_tool(tool, seed):
            success_count += 1
        else:
            failed_tools.append(tool["name"])

    # 刷新服务（只做一次）
    if not args.no_refresh:
        refresh_services()

    # 验证
    print(f"\n{'='*50}")
    print(f"  安装完成：{success_count}/{len(selected)}")
    print(f"{'='*50}")

    if failed_tools:
        print(f"\n❌ 失败：{', '.join(failed_tools)}")

    if success_count > 0:
        print("\n📌 验证方法：")
        print("   1. 等待 Finder 重启（约 3-5 秒）")
        print("   2. 在 Finder 中选中对应类型的文件")
        print("   3. 右键 → 快速操作 → 查看已安装的工具")
        print("\n📌 如遇问题，查看日志：")
        print(f"   cat {LOGS_DIR}/*.log")

    if failed_tools:
        sys.exit(1)


if __name__ == "__main__":
    main()
