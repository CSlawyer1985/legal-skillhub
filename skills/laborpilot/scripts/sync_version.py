#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同步并校验 LaborPilot 整包版本号。

VERSION 是唯一版本源。同步范围包括 README 版本徽章、根 SKILL、全部
子 Skill、Codex Plugin 清单、知识构建统计清单和领域评测数据；校验时还要求
CHANGELOG 的最新版本与 VERSION 一致。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
README_BADGE_PATTERN = re.compile(
    r"(\[!\[Version\]\(https://img\.shields\.io/badge/version-v)"
    r"(.+?)"
    r"(-brightgreen\.svg\)\]\(\./CHANGELOG\.md\))"
)


def validate_semver(version: str) -> str:
    """校验并返回规范化的 SemVer 字符串。"""
    normalized = str(version).strip()
    if not SEMVER_PATTERN.fullmatch(normalized):
        raise ValueError(f"版本号不符合 SemVer：{version}")
    return normalized


def skill_files(root: Path) -> list[Path]:
    """返回整包内所有需要统一版本的 Skill 文件。"""
    files = [root / "SKILL.md"]
    files.extend(sorted((root / "skills").glob("*/SKILL.md")))
    return files


def _readme_version(path: Path) -> tuple[str, str]:
    """读取 README 中唯一的版本徽章。"""
    text = path.read_text(encoding="utf-8")
    matches = list(README_BADGE_PATTERN.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"README 必须包含且仅包含一个标准版本徽章：{path}")
    return text, matches[0].group(2)


def _frontmatter_version(path: Path) -> tuple[list[str], int, str]:
    """读取 Skill frontmatter 中唯一的 version 字段。"""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"缺少 YAML frontmatter：{path}")

    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing is None:
        raise ValueError(f"YAML frontmatter 未闭合：{path}")

    matches = []
    for index in range(1, closing):
        match = re.fullmatch(
            r"version:\s*[\"']?([^\"']+?)[\"']?\s*",
            lines[index].rstrip("\r\n"),
        )
        if match:
            matches.append((index, match.group(1).strip()))
    if len(matches) != 1:
        raise ValueError(f"frontmatter 必须包含且仅包含一个 version 字段：{path}")
    index, version = matches[0]
    return lines, index, version


def read_version(root: Path = ROOT) -> str:
    """读取唯一版本源。"""
    return validate_semver((root / "VERSION").read_text(encoding="utf-8"))


def set_version(root: Path, version: str) -> list[Path]:
    """将版本号同步到 VERSION、README、Plugin、统计、评测和全部 Skill。"""
    normalized = validate_semver(version)
    changed: list[Path] = []

    # 写入前先读取并校验全部目标，避免中途失败留下半同步状态。
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    knowledge_stats_path = root / "data" / "knowledge-build-stats.json"
    knowledge_stats = json.loads(knowledge_stats_path.read_text(encoding="utf-8"))
    evals_path = root / "evals" / "evals.json"
    evals = json.loads(evals_path.read_text(encoding="utf-8"))
    readme_path = root / "README.md"
    readme_text, readme_version = _readme_version(readme_path)
    skill_states = [
        (path, *_frontmatter_version(path))
        for path in skill_files(root)
    ]

    version_file = root / "VERSION"
    desired_version_text = f"{normalized}\n"
    if not version_file.exists() or version_file.read_text(encoding="utf-8") != desired_version_text:
        version_file.write_text(desired_version_text, encoding="utf-8")
        changed.append(version_file)

    if manifest.get("version") != normalized:
        manifest["version"] = normalized
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed.append(manifest_path)

    if knowledge_stats.get("package_version") != normalized:
        knowledge_stats["package_version"] = normalized
        knowledge_stats_path.write_text(
            json.dumps(knowledge_stats, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed.append(knowledge_stats_path)

    if evals.get("package_version") != normalized:
        evals["package_version"] = normalized
        evals_path.write_text(
            json.dumps(evals, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed.append(evals_path)

    if readme_version != normalized:
        readme_text = README_BADGE_PATTERN.sub(
            lambda match: f"{match.group(1)}{normalized}{match.group(3)}",
            readme_text,
            count=1,
        )
        readme_path.write_text(readme_text, encoding="utf-8")
        changed.append(readme_path)

    for path, lines, index, current in skill_states:
        if current == normalized:
            continue
        newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
        if not lines[index].endswith(("\n", "\r")):
            newline = ""
        lines[index] = f'version: "{normalized}"{newline}'
        path.write_text("".join(lines), encoding="utf-8")
        changed.append(path)

    return changed


def consistency_issues(root: Path = ROOT) -> list[str]:
    """返回版本不一致问题；无问题时返回空列表。"""
    issues: list[str] = []
    try:
        version = read_version(root)
    except (OSError, ValueError) as exc:
        return [str(exc)]

    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("version") != version:
            issues.append(
                f"{manifest_path.relative_to(root)}：{manifest.get('version')!r}，应为 {version!r}"
            )
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"无法读取 {manifest_path.relative_to(root)}：{exc}")

    knowledge_stats_path = root / "data" / "knowledge-build-stats.json"
    try:
        knowledge_stats = json.loads(knowledge_stats_path.read_text(encoding="utf-8"))
        if knowledge_stats.get("package_version") != version:
            issues.append(
                f"{knowledge_stats_path.relative_to(root)}："
                f"{knowledge_stats.get('package_version')!r}，应为 {version!r}"
            )
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"无法读取 {knowledge_stats_path.relative_to(root)}：{exc}")

    evals_path = root / "evals" / "evals.json"
    try:
        evals = json.loads(evals_path.read_text(encoding="utf-8"))
        if evals.get("package_version") != version:
            issues.append(
                f"{evals_path.relative_to(root)}："
                f"{evals.get('package_version')!r}，应为 {version!r}"
            )
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"无法读取 {evals_path.relative_to(root)}：{exc}")

    readme_path = root / "README.md"
    try:
        _, current = _readme_version(readme_path)
        if current != version:
            issues.append(f"README.md：{current!r}，应为 {version!r}")
    except (OSError, ValueError) as exc:
        issues.append(str(exc))

    for path in skill_files(root):
        try:
            _, _, current = _frontmatter_version(path)
            if current != version:
                issues.append(f"{path.relative_to(root)}：{current!r}，应为 {version!r}")
        except (OSError, ValueError) as exc:
            issues.append(str(exc))

    changelog_path = root / "CHANGELOG.md"
    try:
        changelog = changelog_path.read_text(encoding="utf-8")
        entries = re.findall(r"(?m)^## \[([^]]+)](?:\s+-\s+\d{4}-\d{2}-\d{2})?\s*$", changelog)
        if not entries:
            issues.append("CHANGELOG.md：未找到版本条目")
        elif entries[0] != version:
            issues.append(f"CHANGELOG.md：最新版本为 {entries[0]!r}，应为 {version!r}")
    except OSError as exc:
        issues.append(f"无法读取 CHANGELOG.md：{exc}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="同步并校验 LaborPilot 整包版本号")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--set", metavar="VERSION", help="同步设置新的 SemVer 版本号")
    group.add_argument("--check", action="store_true", help="仅校验版本一致性（默认）")
    args = parser.parse_args()

    if args.set:
        try:
            changed = set_version(ROOT, args.set)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"版本同步失败：{exc}", file=sys.stderr)
            return 1
        if changed:
            print("已同步版本字段：")
            for path in changed:
                print(f"- {path.relative_to(ROOT)}")
        else:
            print("版本字段已经一致，无需修改。")

    issues = consistency_issues(ROOT)
    if issues:
        print("版本一致性校验失败：", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        if args.set:
            print("请同步更新 CHANGELOG.md 后重新运行 --check。", file=sys.stderr)
        return 1

    print(f"版本一致性校验通过：{read_version(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
