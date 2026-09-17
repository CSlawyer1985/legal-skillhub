# -*- coding: utf-8 -*-
"""委托材料孵化器 · 一步安装脚本

设计要点（2026-08-18 落地，对应测试报告 P1/P2）：
1. 一步解压直达目标目录（~/.workbuddy/skills/委托材料孵化器/），不经过任何中间临时目录，
   避免沙箱回收导致重复安装；
2. 文件名编码自适应：zip 条目带 UTF-8 标志位（bit 11, 0x800）直接按 UTF-8；
   无标志的旧包（Windows 系统压缩 GBK）走 cp437 → gbk 兜底还原；
3. 路径穿越防护：拒绝绝对路径 / ".." 路径，仅允许包内相对路径；
4. 覆盖式安装：只写入 zip 内文件，不删除目标目录中已存在的其他文件（保护用户数据）；
   安装完成后自动读取 SKILL.md 版本号核对。

用法:
    python install_skill.py <skill.zip> [目标目录]
    # 不带参数时：自动查找桌面「委托材料孵化器-Skill包-*.zip」最新包，安装到用户级 skills 目录
"""
import os
import sys
import glob
import zipfile

DEFAULT_DEST = os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "委托材料孵化器")


def decode_name(info: zipfile.ZipInfo) -> str:
    """按 zip 规范还原文件名：bit 11 置位=UTF-8；否则 cp437→gbk 兜底。"""
    name = info.filename
    if info.flag_bits & 0x800:  # UTF-8 标志位
        return name
    # 旧包：Windows 系统压缩以 GBK 写入且未置位，Python 已按 cp437 解码为 str
    try:
        return name.encode("cp437", errors="strict").decode("gbk", errors="strict")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return name  # 无法还原则保留原样


def is_safe_path(name: str) -> bool:
    """路径穿越防护：拒绝绝对路径与 '..' 段。"""
    if name.startswith(("/", "\\")) or (len(name) > 1 and name[1] == ":"):
        return False
    parts = name.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        return False
    return True


def common_top_dir(z: zipfile.ZipFile) -> str:
    """计算 zip 内公共顶层目录（若有且唯一），供解压时剥离，避免多套一层目录。"""
    tops = set()
    for info in z.infolist():
        if info.is_dir():
            continue
        name = decode_name(info)
        parts = name.replace("\\", "/").split("/")
        tops.add(parts[0] if parts else "")
    if len(tops) == 1 and tops != {""}:
        return tops.pop()
    return ""


def extract_zip(zip_path: str, dest: str) -> int:
    count = 0
    with zipfile.ZipFile(zip_path, "r") as z:
        top = common_top_dir(z)
        for info in z.infolist():
            if info.is_dir():
                continue
            name = decode_name(info)
            if top:
                rel = name[len(top):].lstrip("/\\")
                if not rel:
                    continue
                name = rel
            if not is_safe_path(name):
                print(f"[跳过] 不安全的路径: {name}")
                continue
            target = os.path.join(dest, name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())
            count += 1
    return count


def read_version(dest: str) -> str:
    """读取 SKILL.md frontmatter 中的 version 字段。"""
    skill_md = os.path.join(dest, "SKILL.md")
    if not os.path.exists(skill_md):
        return "(未找到 SKILL.md)"
    with open(skill_md, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip()
            if line == "---" and "version:" in line:  # 防异常情况
                continue
    return "(未找到 version 字段)"


def find_latest_zip() -> str | None:
    """桌面查找最新「委托材料孵化器-Skill包-*.zip」。"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    zips = glob.glob(os.path.join(desktop, "委托材料孵化器-Skill包-*.zip"))
    if not zips:
        return None
    return max(zips, key=os.path.getmtime)


def main():
    if len(sys.argv) >= 2:
        zip_path = os.path.abspath(sys.argv[1])
    else:
        zip_path = find_latest_zip()
        if not zip_path:
            print("错误：未指定 zip 路径，且桌面未找到「委托材料孵化器-Skill包-*.zip」")
            sys.exit(1)
    dest = os.path.abspath(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_DEST

    if not os.path.exists(zip_path):
        print(f"错误：zip 不存在: {zip_path}")
        sys.exit(1)

    print(f"源包  : {zip_path}")
    print(f"目标  : {dest}")

    count = extract_zip(zip_path, dest)
    version = read_version(dest)
    print(f"完成  : 解压 {count} 个文件 → {dest}")
    print(f"版本  : {version}")


if __name__ == "__main__":
    main()
