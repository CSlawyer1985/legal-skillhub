#!/usr/bin/env python3
"""
KAI·民商事诉讼大师技能包版本管理脚本
版本：2.0.0

功能：
1. 查看当前版本号
2. 递增版本号（major/minor/patch）
3. 自动同步所有文件中的版本号（SKILL.md、README.md、CHANGELOG.md、build-lite.py、build-expert.py、build-all.py、含 version 的子技能）
4. 添加变更日志条目

使用方式：
  python scripts/version_manager.py --current
  python scripts/version_manager.py --bump minor --desc "新增法院短信处理子技能"
  python scripts/version_manager.py --bump patch --desc "修复版本号同步问题"
  python scripts/version_manager.py --sync          # 强制同步所有文件版本号到当前版本

说明：
  - 版本号以 SKILL.md 中 `version: X.X.X` 为准
  - `name` / `name_zh` / 主标题中的版本号会自动同步
  - build-lite.py / build-expert.py / build-all.py 中的 Pro/Lite/专家 版本号会同步更新
  - 子技能文件中若包含 `version: X.X.X` 也会同步（不强制所有子技能都有 version 字段）
  - `--sync` 模式会强制将所有关键字段中的版本号统一为当前 `version:` 字段值，用于修复历史不一致
  - 版本更新后，请运行 `python scripts/build-all.py` 同步 Lite 版和 民商事诉讼专家 版
"""

import re
import argparse
from datetime import datetime
from pathlib import Path

# 常量定义
SKILL_DIR = Path(__file__).parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
README_MD = SKILL_DIR / "README.md"
CHANGELOG_MD = SKILL_DIR / "CHANGELOG.md"
BUILD_LITE_PY = SKILL_DIR / "build-lite.py"
META_JSON = SKILL_DIR / "_skillhub_meta.json"
SUB_SKILLS_DIR = SKILL_DIR / "sub-skills"


def get_current_version():
    """从 SKILL.md 读取当前版本号"""
    content = SKILL_MD.read_text(encoding="utf-8")
    version_match = re.search(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)", content, re.MULTILINE)
    if not version_match:
        raise ValueError("未在 SKILL.md 中找到 version 字段")
    return version_match.group(1)


def bump_version(current_version, bump_type):
    """递增版本号"""
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"未知的 bump_type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def replace_version_in_text(content, old_version, new_version):
    """在文本中统一替换版本号，覆盖常见格式"""
    patterns = [
        # YAML frontmatter: version: X.X.X
        (rf"^(version:\s*){re.escape(old_version)}", rf"\g<1>{new_version}"),
        # name: KAI·民商事诉讼大师·Pro版 vX.X.X
        (rf"(name:\s*KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v){re.escape(old_version)}", rf"\g<1>{new_version}"),
        # name_zh: KAI·民商事诉讼大师·Pro版 vX.X.X
        (rf"(name_zh:\s*KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v){re.escape(old_version)}", rf"\g<1>{new_version}"),
        # # KAI·民商事诉讼大师·Pro版 vX.X.X
        (rf"^(# KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v){re.escape(old_version)}", rf"\g<1>{new_version}"),
        # # Kai·民商事诉讼律师助手·Pro版 vX.X.X
        (rf"^(# Kai·民商事诉讼律师助手·(?:Pro|Lite)版\s+v){re.escape(old_version)}", rf"\g<1>{new_version}"),
        # - **版本**：vX.X.X
        (rf"(- \*\*版本\*\*：\s*v){re.escape(old_version)}", rf"\g<1>{new_version}"),
        # version: "X.X.X"（JSON 风格）
        (rf"(\"version\":\s*\"){re.escape(old_version)}(\")", rf"\g<1>{new_version}\g<2>"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def sync_all_versions(target_version):
    """
    强制同步：将所有已知版本字段中的任意 vX.X.X 统一更新为 target_version。
    用于修复历史版本号不一致（如 README 标题、主标题、子技能 frontmatter 等）。
    """
    generic_patterns = [
        # name: KAI·民商事诉讼大师·Pro版 v任意版本
        (rf"(name:\s*KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v)\d+\.\d+\.\d+", rf"\g<1>{target_version}"),
        # name_zh: KAI·民商事诉讼大师·Pro版 v任意版本
        (rf"(name_zh:\s*KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v)\d+\.\d+\.\d+", rf"\g<1>{target_version}"),
        # # KAI·民商事诉讼大师·Pro版 v任意版本
        (rf"^(# KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v)\d+\.\d+\.\d+", rf"\g<1>{target_version}"),
        # # Kai·民商事诉讼律师助手·Pro版 v任意版本
        (rf"^(# Kai·民商事诉讼律师助手·(?:Pro|Lite)版\s+v)\d+\.\d+\.\d+", rf"\g<1>{target_version}"),
        # - **版本**：v任意版本
        (rf"(- \*\*版本\*\*：\s*v)\d+\.\d+\.\d+", rf"\g<1>{target_version}"),
        # YAML version: 任意版本
        (rf"^(version:\s*)\d+\.\d+\.\d+", rf"\g<1>{target_version}"),
        # JSON 风格 "version": "任意版本"
        (rf"(\"version\":\s*\")\d+\.\d+\.\d+(\")", rf"\g<1>{target_version}\g<2>"),
        # _skillhub_meta.json 中的 name 字段
        (rf'(\"name\":\s*\"KAI·民商事诉讼大师·(?:Pro|Lite)版\s+v)\d+\.\d+\.\d+(\")', rf"\g<1>{target_version}\g<2>"),
    ]

    files_to_check = [
        ("SKILL.md", SKILL_MD),
        ("README.md", README_MD),
        ("build-lite.py", BUILD_LITE_PY),
        ("_skillhub_meta.json", META_JSON),
    ]

    # 子技能
    if SUB_SKILLS_DIR.exists():
        for file_path in sorted(SUB_SKILLS_DIR.glob("*_SKILL.md")):
            files_to_check.append((f"sub-skills/{file_path.name}", file_path))

    changed_files = []
    for label, file_path in files_to_check:
        if not file_path.exists():
            continue
        content = file_path.read_text(encoding="utf-8")
        new_content = content
        for pattern, replacement in generic_patterns:
            new_content = re.sub(pattern, replacement, new_content, flags=re.MULTILINE)

        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            changed_files.append(label)

    return changed_files


def update_skill_md(old_version, new_version):
    """更新 SKILL.md 中的版本信息"""
    content = SKILL_MD.read_text(encoding="utf-8")
    content = replace_version_in_text(content, old_version, new_version)
    SKILL_MD.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 SKILL.md：v{old_version} -> v{new_version}")


def update_readme_md(old_version, new_version):
    """更新 README.md 中的版本信息"""
    if not README_MD.exists():
        print("⚠️ README.md 不存在，跳过")
        return
    content = README_MD.read_text(encoding="utf-8")
    content = replace_version_in_text(content, old_version, new_version)
    README_MD.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 README.md：v{old_version} -> v{new_version}")


def update_build_lite_py(old_version, new_version):
    """更新 build-lite.py 中的版本号"""
    if not BUILD_LITE_PY.exists():
        print("⚠️ build-lite.py 不存在，跳过")
        return
    content = BUILD_LITE_PY.read_text(encoding="utf-8")
    content = replace_version_in_text(content, old_version, new_version)
    BUILD_LITE_PY.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 build-lite.py：v{old_version} -> v{new_version}")


def update_sub_skills(old_version, new_version):
    """更新包含 version 字段的子技能 frontmatter"""
    if not SUB_SKILLS_DIR.exists():
        print("⚠️ sub-skills 目录不存在，跳过")
        return

    updated = []
    for file_path in SUB_SKILLS_DIR.glob("*_SKILL.md"):
        content = file_path.read_text(encoding="utf-8")
        # 只处理包含 version 字段的子技能
        if re.search(r"^version:\s*" + re.escape(old_version), content, re.MULTILINE):
            content = replace_version_in_text(content, old_version, new_version)
            file_path.write_text(content, encoding="utf-8")
            updated.append(file_path.name)

    if updated:
        print(f"✅ 已更新 {len(updated)} 个子技能：{', '.join(updated)}")
    else:
        print("ℹ️ 没有需要更新的子技能（未找到含 version 字段或版本已一致）")


def update_changelog_md(new_version, description, bump_type):
    """在 CHANGELOG.md 开头添加新版本条目"""
    if not CHANGELOG_MD.exists():
        print("⚠️ CHANGELOG.md 不存在，跳过")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    if bump_type == "major":
        type_label = "🚨 重大更新"
    elif bump_type == "minor":
        type_label = "✨ 功能更新"
    else:
        type_label = "🔧 修复优化"

    new_entry = f"""## v{new_version}（{today}）

### {type_label}

**来源**：{description}

**核心更新**：

1. **更新内容1**：请在此处填写具体更新内容
2. **更新内容2**：请在此处填写具体更新内容
3. **更新内容3**：请在此处填写具体更新内容

**影响范围**：请在此处描述本次更新影响的模块或功能。

---

"""

    existing_content = CHANGELOG_MD.read_text(encoding="utf-8")

    if existing_content.startswith("# 修订记录"):
        lines = existing_content.split("\n")
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith("## v"):
                insert_index = i
                break

        if insert_index > 0:
            new_content = "\n".join(lines[:insert_index]) + "\n\n" + new_entry + "\n".join(lines[insert_index:])
        else:
            new_content = existing_content + "\n\n" + new_entry
    else:
        new_content = new_entry + existing_content

    CHANGELOG_MD.write_text(new_content, encoding="utf-8")
    print(f"✅ 已在 CHANGELOG.md 中添加 v{new_version} 条目")


def main():
    parser = argparse.ArgumentParser(description="KAI·民商事诉讼大师技能包版本管理")
    parser.add_argument("--current", action="store_true", help="显示当前版本号")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], help="递增版本号类型")
    parser.add_argument("--desc", type=str, help="更新描述（用于变更日志）")
    parser.add_argument("--sync", action="store_true", help="强制同步所有关键字段版本号到当前 version 字段值（不递增）")
    parser.add_argument("--yes", "-y", action="store_true", help="跳过确认直接执行")

    args = parser.parse_args()

    try:
        current_version = get_current_version()

        if args.current:
            print(f"当前版本：v{current_version}")
            return

        if args.sync:
            print(f"准备强制同步所有版本号到：v{current_version}")
            if not args.yes:
                confirm = input("确认同步？(y/N): ")
                if confirm.lower() != "y":
                    print("操作已取消")
                    return

            changed_files = sync_all_versions(current_version)
            if changed_files:
                print(f"✅ 已同步 {len(changed_files)} 个文件：")
                for label in changed_files:
                    print(f"  - {label}")
            else:
                print("ℹ️ 所有文件版本号已一致，无需同步")

            print(f"\n当前版本：v{current_version}")
            print("提示：运行 `python scripts/build-all.py` 可同时同步 Lite 版和 民商事诉讼专家 版版本号。")
            return

        if args.bump:
            if not args.desc:
                print("❌ 请使用 --desc 参数提供更新描述")
                return

            new_version = bump_version(current_version, args.bump)
            print(f"准备更新版本号：v{current_version} -> v{new_version}")
            print(f"更新类型：{args.bump}")
            print(f"更新描述：{args.desc}")

            if not args.yes:
                confirm = input("确认更新？(y/N): ")
                if confirm.lower() != "y":
                    print("操作已取消")
                    return

            update_skill_md(current_version, new_version)
            update_readme_md(current_version, new_version)
            update_build_lite_py(current_version, new_version)
            update_sub_skills(current_version, new_version)
            update_changelog_md(new_version, args.desc, args.bump)

            # 兜底同步：确保 _skillhub_meta.json 等所有关键文件版本号一致
            sync_all_versions(new_version)

            print("\n🎉 版本更新完成！")
            print(f"当前版本：v{new_version}")
            print("请检查以下文件：")
            print(f"  - {SKILL_MD}")
            print(f"  - {README_MD}")
            print(f"  - {BUILD_LITE_PY}")
            print(f"  - {CHANGELOG_MD}")
            print("\n提示：请手动编辑 CHANGELOG.md，完善具体的更新内容。")
            print("提示：运行 `python scripts/build-all.py` 可同时同步 Lite 版和 民商事诉讼专家 版版本号。")

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
