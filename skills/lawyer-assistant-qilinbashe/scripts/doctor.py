#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doctor.py — 律师助手开箱即用体检（v4.3.0 新增）

功能：首次使用 / 环境变更后运行一次，统一检查：
  1. 包完整性：agents/*.md、assets/律师助手节点树状图.html、manifest.yaml 是否存在；
  2. 版本一致性：SKILL.md / manifest.yaml / _plugin_base.json / 全景图常量 四处一致；
  3. 全景图发布状态：调用 present_panorama.py --check-present（缺失/过期自动重发）；
  4. 核心依赖：python-docx、openai（缺失即阻断）；
  5. 可选依赖：easyocr、PyMuPDF/pdfplumber、whisper、ffmpeg、python-pptx、
     openpyxl、xlrd、docx2txt、beautifulsoup4、pillow-heif（缺失按需安装，触发对应格式降级）；
  6. 知识库：check_knowledge_base.py 存在性提示；
  7. 多模态自检：multimodal_ingest.py --self-test（可用时执行）；
  8. MCP：探测常用法律知识库 MCP 工具配置（不可用仅提示，不失败）。

退出码约定：
  0 = 核心可用，全景图可发布，首轮可直接使用；
  2 = 核心可用，部分可选依赖缺失，会触发对应格式降级；
  1 = 核心依赖或包结构阻断，需要先安装 / 修复。

用法：
  python scripts/doctor.py            # 全量体检
  python scripts/doctor.py --quick    # 仅核心项（包完整性 + 版本 + 发布状态）
"""

import argparse
import importlib.util
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)  # scripts/ 的上级 = 技能包根目录
ASSET_HTML = os.path.join(PKG_ROOT, "assets", "律师助手节点树状图.html")

# 核心依赖：缺失即阻断（退出码 1）
CORE_DEPS = ["docx", "openai"]
# 可选依赖：缺失触发对应格式降级（退出码 2）
OPT_DEPS = [
    ("easyocr", "图片/扫描件 OCR"),
    ("fitz", "PDF 文字层（PyMuPDF）"),
    ("pdfplumber", "PDF 文字层（备选）"),
    ("whisper", "语音转写"),
    ("ffmpeg", "视频抽音轨 / 音频转码（命令行）"),
    ("pptx", "PPT 解析"),
    ("openpyxl", "Excel 解析"),
    ("xlrd", "旧版 Excel .xls 解析"),
    ("docx2txt", "Word 解析（备选）"),
    ("bs4", "HTML 正文抽取"),
    ("PIL", "图片基础处理"),
]

results = []  # (类别, 名称, 状态: OK|降级|FAIL, 说明)


def record(cat, name, status, note):
    results.append((cat, name, status, note))


def check_file(path, cat, name):
    if os.path.isfile(path):
        record(cat, name, "OK", path)
        return True
    record(cat, name, "FAIL", "缺失: %s" % path)
    return False


def check_version_consistency():
    """版本一致性：SKILL.md / manifest.yaml / _plugin_base.json / 全景图常量。"""
    def read_ver(path, pattern):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    m = re.search(pattern, line)
                    if m:
                        return m.group(1).strip().strip('"').strip("'").lstrip("v")
        except OSError:
            return None
        return None

    v_skill = read_ver(os.path.join(PKG_ROOT, "SKILL.md"), r"^version:\s*\"?([\d.]+)\"?")
    v_manifest = read_ver(os.path.join(PKG_ROOT, "manifest.yaml"), r"^version:\s*\"?([\d.]+)\"?")
    v_plugin = read_ver(os.path.join(PKG_ROOT, "_plugin_base.json"), r'"version"\s*:\s*"([\d.]+)"')
    v_html = None
    if os.path.isfile(ASSET_HTML):
        m = re.search(r"const\s+VERSION\s*=\s*\"?([^\";\n]+?)\"?;", open(ASSET_HTML, encoding="utf-8").read())
        if m:
            v_html = m.group(1).strip().lstrip("v")

    seen = {v for v in [v_skill, v_manifest, v_plugin, v_html] if v}
    if len(seen) <= 1 and v_skill:
        record("版本一致性", "SKILL/manifest/_plugin_base/全景图", "OK",
               "四处一致 v%s" % v_skill)
        return True
    record("版本一致性", "SKILL/manifest/_plugin_base/全景图", "FAIL",
           "不一致: SKILL=%s manifest=%s _plugin_base=%s 全景图=%s"
           % (v_skill, v_manifest, v_plugin, v_html))
    return False


def check_panorama_publish(quick):
    """全景图发布状态：调用 present_panorama.py --check-present（自愈）。

    在独立临时目录中验证发布链路（渲染→发布→自检），避免发布件写入技能包根目录污染包体。
    """
    script = os.path.join(HERE, "present_panorama.py")
    if not os.path.isfile(script):
        record("全景图", "present_panorama.py", "FAIL", "脚本缺失")
        return False
    import subprocess
    import tempfile
    tmp = tempfile.mkdtemp(prefix="legal_doctor_")
    try:
        r = subprocess.run([sys.executable, script, "--check-present", "--to", tmp],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=120, cwd=tmp)
        if r.returncode == 0:
            record("全景图", "一键发布+自检", "OK", "发布链路可用（临时目录验证通过）")
            return True
        record("全景图", "一键发布+自检", "FAIL",
               "自检未通过（rc=%d）：%s" % (r.returncode, (r.stderr or r.stdout)[-300:]))
        return False
    except Exception as e:
        record("全景图", "一键发布+自检", "FAIL", "执行异常: %s" % e)
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_deps():
    """核心 / 可选依赖分级检查。"""
    core_ok = True
    for mod in CORE_DEPS:
        if importlib.util.find_spec(mod):
            record("核心依赖", mod, "OK", "已安装")
        else:
            core_ok = False
            record("核心依赖", mod, "FAIL", "未安装：pip install %s" % mod)
    for mod, desc in OPT_DEPS:
        if mod == "ffmpeg":
            if shutil.which("ffmpeg"):
                record("可选依赖", mod, "OK", "已安装")
            else:
                record("可选依赖", mod, "降级", "未安装（%s 将无法使用，可用其他工具转文字稿）" % desc)
        elif importlib.util.find_spec(mod):
            record("可选依赖", mod, "OK", "已安装")
        else:
            record("可选依赖", mod, "降级", "未安装（%s 将降级）" % desc)
    return core_ok


def check_kb():
    """知识库检查：脚本存在性提示（不实际调用，避免副作用）。"""
    script = os.path.join(HERE, "check_knowledge_base.py")
    if os.path.isfile(script):
        record("知识库", "check_knowledge_base.py", "OK",
               "存在；建议另行运行 python scripts/check_knowledge_base.py 验证数据注入")
        return True
    record("知识库", "check_knowledge_base.py", "降级", "缺失（离线法条仍可用，实时检索将受限）")
    return False


def check_multimodal_selftest():
    """多模态自检：multimodal_ingest.py --self-test（可用时执行）。"""
    script = os.path.join(HERE, "multimodal_ingest.py")
    if not os.path.isfile(script):
        record("多模态", "multimodal_ingest.py", "FAIL", "脚本缺失")
        return False
    import subprocess
    try:
        r = subprocess.run([sys.executable, script, "--self-test"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=180, cwd=PKG_ROOT)
        if r.returncode == 0:
            record("多模态", "--self-test", "OK", "样例解析自检通过")
            return True
        record("多模态", "--self-test", "降级",
               "自检未完全通过（rc=%d），详见输出；缺失格式会走降级提示" % r.returncode)
        return False
    except Exception as e:
        record("多模态", "--self-test", "降级", "执行异常: %s" % e)
        return False


def check_mcp():
    """MCP 探测：仅提示，不失败。"""
    env_hits = [k for k in os.environ if "MCP" in k.upper() or "PKULAW" in k.upper()
                or "YUANDIAN" in k.upper()]
    if env_hits:
        record("MCP", "法律知识库 MCP", "OK", "检测到相关环境变量: %s" % ", ".join(env_hits[:5]))
    else:
        record("MCP", "法律知识库 MCP", "降级",
               "未检测到 MCP 环境变量；若平台未配置北大法宝/华宇元典 MCP，实时法条检索将走离线兜底（不阻断使用）")
    return True


def main():
    ap = argparse.ArgumentParser(description="律师助手开箱即用体检")
    ap.add_argument("--quick", action="store_true", help="仅检查核心项（包完整性+版本+发布状态+核心依赖）")
    args = ap.parse_args()

    print("=" * 60)
    print("律师助手 · 开箱即用体检")
    print("技能包根目录：%s" % PKG_ROOT)
    print("=" * 60)

    # 1. 包完整性
    ok_integrity = True
    ok_integrity &= check_file(os.path.join(PKG_ROOT, "SKILL.md"), "包完整性", "SKILL.md")
    ok_integrity &= check_file(os.path.join(PKG_ROOT, "manifest.yaml"), "包完整性", "manifest.yaml")
    ok_integrity &= check_file(os.path.join(PKG_ROOT, "_plugin_base.json"), "包完整性", "_plugin_base.json")
    agents_dir = os.path.join(PKG_ROOT, "agents")
    n_agents = len([f for f in os.listdir(agents_dir) if f.endswith(".md")]) if os.path.isdir(agents_dir) else 0
    if n_agents >= 100:
        record("包完整性", "agents/*.md", "OK", "共 %d 个技能文件" % n_agents)
    else:
        ok_integrity = False
        record("包完整性", "agents/*.md", "FAIL", "技能文件数异常: %d" % n_agents)
    ok_integrity &= check_file(ASSET_HTML, "包完整性", "assets/律师助手节点树状图.html")

    # 2. 版本一致性
    ok_ver = check_version_consistency()

    # 3. 全景图发布状态
    ok_pub = check_panorama_publish(args.quick)

    # 4. 核心依赖
    ok_core = check_deps()

    if args.quick:
        checks = [ok_integrity, ok_ver, ok_pub, ok_core]
    else:
        # 5-8
        ok_kb = check_kb()
        ok_mm = check_multimodal_selftest()
        ok_mcp = check_mcp()
        checks = [ok_integrity, ok_ver, ok_pub, ok_core, ok_kb, ok_mm, ok_mcp]

    print()
    print("-" * 60)
    print("体检明细：")
    for cat, name, status, note in results:
        icon = {"OK": "✅", "降级": "⚠️", "FAIL": "❌"}.get(status, "·")
        print("  %s [%s] %s · %s — %s" % (icon, cat, name, status, note))

    n_fail = sum(1 for _, _, s, _ in results if s == "FAIL")
    # 只统计「可选依赖」类别的降级项（MCP/知识库未配置属环境提示，不误报为依赖缺失）
    n_opt = sum(1 for cat, _, s, _ in results if cat == "可选依赖" and s == "降级")
    # 环境降级提示（MCP/知识库未配置等，不影响退出码）
    n_env = sum(1 for cat, _, s, _ in results
                if cat in ("MCP", "知识库", "多模态") and s == "降级")

    print("-" * 60)
    if n_fail == 0:
        if n_opt == 0:
            if n_env:
                print("结论：核心可用，依赖齐全，全景图可发布，首轮可直接使用；"
                      "MCP/知识库未配置，实时法条检索走离线兜底，不影响核心使用。（退出码 0）")
            else:
                print("结论：核心可用，依赖齐全，全景图可发布，首轮可直接使用。（退出码 0）")
            sys.exit(0)
        print("结论：核心可用，部分可选依赖缺失（%d 项），对应格式将降级处理。（退出码 2）" % n_opt)
        sys.exit(2)
    print("结论：存在阻断项（%d 项），请先安装依赖 / 修复包结构后再使用。（退出码 1）" % n_fail)
    sys.exit(1)


if __name__ == "__main__":
    main()
