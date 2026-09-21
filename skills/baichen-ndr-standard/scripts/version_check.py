#!/usr/bin/env python3
"""共享标准版本校验——业务技能加载时自动检测依赖版本是否匹配"""
import os, sys, yaml

def check_shared_version(skill_dir: str, shared_name: str, expected_version: str) -> bool:
    """检查共享标准版本"""
    shared_path = os.path.join("/sandbox/workspace/skills", shared_name, "SKILL.md")
    if not os.path.isfile(shared_path):
        print(f"⚠ 共享标准 {shared_name} 未安装，请先安装")
        return False
    with open(shared_path) as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3:
        print(f"⚠ {shared_name} SKILL.md 格式异常")
        return False
    fm = yaml.safe_load(parts[1])
    actual = fm.get("version", "未知")
    if actual != expected_version:
        print(f"⚠ 版本不匹配: 期望 {expected_version}, 实际 {actual}")
        print(f"  建议: 技能安装器 重新安装 {shared_name}")
        return False
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: version_check.py <共享标准名> <期望版本>")
        sys.exit(1)
    ok = check_shared_version("", sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
