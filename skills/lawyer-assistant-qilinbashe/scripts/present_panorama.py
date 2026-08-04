#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""present_panorama.py — 律师助手全景图一键发布与自愈（v4.3.0 新增）

功能：
  1. 从脚本位置推导技能包根目录（scripts/ 的上级），无需记忆绝对路径；
  2. 先调用 render_panorama.render() 生成最新 assets/律师助手节点树状图.html
     （版本号 / 技能文件数 / 总文件数 / 时间轴「今天」实时注入）；
  3. 将发布件原子写入 --to 指定目录（默认当前工作目录 os.getcwd()），
     文件名固定为「律师助手节点树状图.html」；
  4. 发布目标必须在 .workbuddy 等隐藏目录之外（预览服务器对其返回 403），
     检测到隐藏目录段即报错退出，禁止继续 present_files；
  5. --check-present：自检发布件是否存在、是否过期（对比 VERSION/SKILLS/FILES/TODAY）、
     是否位于隐藏目录内，异常时自动重新发布（自愈）；
  6. 发布 / 自检失败时，打印 agents/00-律师助手全景图.md 内的纯文本节点树
     （<details> 块）降级路径，提示模型直接输出文本目录——不要求用户手动复制任何文件。

用法：
  python scripts/present_panorama.py                  # 生成并发布到当前目录
  python scripts/present_panorama.py --to ./outputs   # 发布到指定目录
  python scripts/present_panorama.py --check-present  # 自检发布件，异常自动重发

原则：用户永远不需要手动复制文件；渲染 → 发布 → 展示全自动，失败自动落到纯文本降级。
"""

import argparse
import os
import re
import sys
import tempfile
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)  # scripts/ 的上级 = 技能包根目录
ASSET_NAME = "律师助手节点树状图.html"
ASSET_SRC = os.path.join(PKG_ROOT, "assets", ASSET_NAME)
AGENT_PANORAMA = os.path.join(PKG_ROOT, "agents", "00-律师助手全景图.md")


def log(msg):
    print("[present_panorama] %s" % msg)


def err(msg):
    print("[present_panorama][ERROR] %s" % msg, file=sys.stderr)


def is_hidden_dir(path):
    """判断路径中是否含有隐藏目录段（.workbuddy / .codebuddy 等，预览服务器返回 403）。"""
    parts = re.split(r"[\\/]+", os.path.abspath(path))
    for p in parts:
        if p.startswith(".") and p not in (".", ".."):
            return True
    return False


def load_render():
    """加载 render_panorama 模块（复用渲染 / 计数 / 常量提取函数）。"""
    sys.path.insert(0, HERE)
    import render_panorama
    return render_panorama


def render_latest():
    """渲染最新源图，返回 (disp_ver, skills, files, today)。"""
    rp = load_render()
    src = rp.DEFAULT_SRC
    out = os.path.join(src, "assets", ASSET_NAME)
    disp_ver, skills, files, today, n_stage, n_node = rp.render(src, out)
    log("已渲染最新源图：版本=%s 技能文件=%d 总文件数=%d 今天=%s"
        % (disp_ver, skills, files, today))
    return disp_ver, skills, files, today


def atomic_write(dst, content):
    """临时文件 + os.replace 原子写入，避免生成一半的 HTML 被预览。"""
    d = os.path.dirname(dst) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".panorama_tmp_", suffix=".html", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, dst)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def publish(to_dir):
    """渲染最新源图并发布到 to_dir（必须位于隐藏目录之外），返回发布件绝对路径。"""
    if is_hidden_dir(to_dir):
        err("发布目标位于隐藏目录内（预览服务器将返回 403）：%s" % to_dir)
        err("请换用 .workbuddy 之外的目录（如当前工作区根目录或 ./outputs/）。")
        print_plain_tree_fallback()
        sys.exit(1)

    render_latest()
    if not os.path.isfile(ASSET_SRC):
        err("源图生成失败：%s" % ASSET_SRC)
        print_plain_tree_fallback()
        sys.exit(1)

    with open(ASSET_SRC, encoding="utf-8") as f:
        content = f.read()

    dst = os.path.join(os.path.abspath(to_dir), ASSET_NAME)
    atomic_write(dst, content)
    log("已发布到工作区（.workbuddy 之外）：%s" % dst)
    log("接下来请执行：present_files → %s" % dst)
    return dst


def extract_const(html, name):
    m = re.search(r"const\s+%s\s*=\s*\"?([^\";\n]+?)\"?;" % re.escape(name), html)
    return m.group(1).strip() if m else None


def check_present(to_dir):
    """自检发布件：存在性 / 时效性（VERSION/SKILLS/FILES/TODAY）/ 位置；异常自动重发。"""
    dst = os.path.join(os.path.abspath(to_dir), ASSET_NAME)
    problems = []
    if not os.path.isfile(dst):
        problems.append("发布件不存在")
    else:
        if is_hidden_dir(dst):
            problems.append("发布件位于隐藏目录内（403 风险）")
        rp = load_render()
        live_ver = rp.read_version(rp.DEFAULT_SRC)
        live_skills = str(rp.count_agents(rp.DEFAULT_SRC))
        live_files = str(rp.count_files(rp.DEFAULT_SRC))
        live_today = datetime.now().strftime("%m-%d")
        html = open(dst, encoding="utf-8").read()
        g_ver = (extract_const(html, "VERSION") or "").lstrip("v")
        g_skills = extract_const(html, "SKILLS")
        g_files = extract_const(html, "FILES")
        g_today = extract_const(html, "TODAY")
        if g_ver != live_ver:
            problems.append("版本号过期（图=%s 包=%s）" % (g_ver or "?", live_ver))
        if g_skills != live_skills:
            problems.append("技能文件数过期（图=%s 包=%s）" % (g_skills or "?", live_skills))
        if g_files != live_files:
            problems.append("总文件数过期（图=%s 包=%s）" % (g_files or "?", live_files))
        if g_today != live_today:
            problems.append("时间轴「今天」过期（图=%s 实际=%s）" % (g_today or "?", live_today))

    if not problems:
        log("自检通过：发布件存在、位于可访问目录、四项统计与技能包一致 → %s" % dst)
        return 0

    for p in problems:
        err("自检发现：%s" % p)
    log("自动重新发布（自愈）……")
    try:
        publish(to_dir)
        log("自愈完成：已重新发布 → %s" % dst)
        return 0
    except SystemExit:
        raise
    except Exception as e:
        err("自动重发失败：%s" % e)
        print_plain_tree_fallback()
        return 1


def print_plain_tree_fallback():
    """打印 00-律师助手全景图.md 内的纯文本节点树（<details> 块），供模型直接输出。"""
    log("【降级路径】以下纯文本节点树可直接输出给用户（零文件操作）：")
    try:
        with open(AGENT_PANORAMA, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"<details>.*?</details>", text, re.S)
        if m:
            print("\n" + m.group(0).strip() + "\n")
            return
    except OSError as e:
        err("读取纯文本节点树失败：%s" % e)
    print("（请直接引用 agents/00-律师助手全景图.md 内的「全流程节点图」折叠块输出给用户）")


def main():
    ap = argparse.ArgumentParser(description="律师助手全景图一键发布与自愈")
    ap.add_argument("--to", default=None, help="发布目标目录（默认当前工作目录）")
    ap.add_argument("--check-present", action="store_true",
                    help="自检发布件（存在/时效/位置），异常自动重发")
    args = ap.parse_args()

    to_dir = args.to or os.getcwd()

    if args.check_present:
        sys.exit(check_present(to_dir))

    try:
        publish(to_dir)
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        err("发布失败：%s" % e)
        print_plain_tree_fallback()
        sys.exit(1)


if __name__ == "__main__":
    main()
