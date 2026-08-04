#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ip-management-compliance 版本漂移闸门 / 同步引擎（移植自 patent-examination-guide）。

设计原则：版本是「数据」而非「文档」。
- 单一真源：每个技能的 frontmatter `version:` 字段。
- 内部映射表（母技能 SKILL.md 中 VERSION_TABLE_START/END 标记之间）由本脚本
  从各子技能 frontmatter 实时派生（sync），不再手写 —— 根除内部漂移。
- 外部依赖只记「能力地板 + 最后核验日期」，不钉精确补丁号（策略 B）。

两种模式：
  check   校验内部一致性（母映射表 vs 各子技能 frontmatter）。
           内部不一致 -> 退出码 1（pre-commit 据此阻断提交）。
           外部漂移   -> 仅告警（退出码 0，不阻断）。
  sync    从 frontmatter 重新生成内部版本映射表（标记区间内的内容）。

鲁棒性：仅用标准库；git 缺失或脚本异常时，check 不阻断正常提交流程。
"""
import os
import re
import sys
import subprocess
from pathlib import Path

# ---- 路径解析（基于脚本自身位置，可移植） ----
SKILL_ROOT = Path(__file__).resolve().parent.parent          # .../ip-management-compliance
SKILLS_DIR = SKILL_ROOT.parent                               # .../skills
PARENT_FILE = SKILL_ROOT / "SKILL.md"
FALLBACK_DATE = "2026-07-16"

MARK_START = "<!-- VERSION_TABLE_START -->"
MARK_END = "<!-- VERSION_TABLE_END -->"

# 母技能 frontmatter 中声明的子技能（稳定列表，单一真源之一）
CHILDREN = [
    "ip-mgmt-framework",
    "ip-mgmt-strategy",
    "ip-mgmt-innovation",
    "ip-mgmt-tools",
    "ip-mgmt-examination",
    "ip-mgmt-risk",
    "ip-mgmt-exploitation",
    "ip-mgmt-audit",
    "ip-mgmt-search",
]


def read_frontmatter_version(path: Path):
    """读取 frontmatter 中的 version: 字段。无则返回 None。"""
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    m = re.search(
        r'^version:\s*["\']?([0-9]+\.[0-9]+(?:\.[0-9]+)?)["\']?',
        text,
        re.MULTILINE,
    )
    return m.group(1) if m else None


def git_date(path: Path) -> str:
    """取文件最后一次提交的日期（YYYY-MM-DD），失败则回退常量。"""
    try:
        rel = str(path.relative_to(SKILLS_DIR))
        out = subprocess.run(
            ["git", "-C", str(SKILLS_DIR), "log", "-1", "--format=%as", "--", rel],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return FALLBACK_DATE


def parse_version_tuple(v: str):
    """'1.13.3' -> (1,13,3)；无法解析返回 None。"""
    if not v:
        return None
    parts = re.findall(r"\d+", v)
    if not parts:
        return None
    return tuple(int(p) for p in parts)


def version_ge(actual: str, floor: str) -> bool:
    """actual >= floor（按数值逐段比较）。"""
    a, b = parse_version_tuple(actual), parse_version_tuple(floor)
    if a is None or b is None:
        return False
    length = max(len(a), len(b))
    a = a + (0,) * (length - len(a))
    b = b + (0,) * (length - len(b))
    return a >= b


def parse_mapping_table(text: str):
    """解析标记区间内版本映射表，返回 [(name, version, date), ...]。"""
    rows = []
    inside = False
    for line in text.splitlines():
        if MARK_START in line:
            inside = True
            continue
        if MARK_END in line:
            inside = False
            continue
        if inside and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            if cells[0].startswith("技能"):  # 表头行
                continue
            # 名称可能带「（母技能）」等括号注解，剥离括号内容
            name = re.sub(r"[（(].*?[）)]", "", cells[0]).strip()
            ver = cells[1].lstrip("vV")
            date = cells[2]
            rows.append((name, ver, date))
    return rows


def extract_section(text: str, heading: str) -> str:
    """提取以 '### <heading>' 开头、到下一个 '### ' 为止的章节文本。"""
    lines = text.splitlines()
    out, in_sec = [], False
    for line in lines:
        if line.strip().startswith("### ") and heading in line:
            in_sec = True
            continue
        if in_sec and line.strip().startswith("### "):
            break
        if in_sec:
            out.append(line)
    return "\n".join(out)


def parse_external_deps(text: str):
    """解析运行时依赖表（限定章节内），返回 [(name, floor), ...]。"""
    section = extract_section(text, "运行时依赖")
    deps = []
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or not cells[0].startswith("`"):
            continue
        name = cells[0].strip("`").strip()
        floor = None
        for c in cells:
            m = re.search(r"[≥>]=?\s*[vV]?(\d+\.\d+(?:\.\d+)?)", c)
            if m:
                floor = m.group(1)
                break
        deps.append((name, floor))
    return deps


def cmd_check() -> int:
    print("[version-gate] 内部版本校验（母映射表 vs 子技能 frontmatter）：")
    if not PARENT_FILE.exists():
        print("  ⚠️ 找不到母技能 SKILL.md，跳过校验。")
        return 0

    text = PARENT_FILE.read_text(encoding="utf-8")
    parent_ver = read_frontmatter_version(PARENT_FILE)
    rows = parse_mapping_table(text)

    errors = 0
    row_by_name = {name: (ver, date) for name, ver, date in rows}

    # 母技能自身
    doc_parent = row_by_name.get("ip-management-compliance")
    if doc_parent:
        if parent_ver and doc_parent[0] == parent_ver:
            print(f"  ✅ ip-management-compliance（母） 文档 {doc_parent[0]} == 实际 {parent_ver}")
        else:
            print(f"  ❌ ip-management-compliance（母） 文档 {doc_parent[0]} != 实际 {parent_ver}")
            errors += 1
    else:
        print("  ⚠️ 映射表中未找到母技能行（标记区间可能缺失）。")
        errors += 1

    # 各子技能
    for child in CHILDREN:
        actual = read_frontmatter_version(SKILLS_DIR / child / "SKILL.md")
        doc = row_by_name.get(child)
        if doc is None:
            print(f"  ❌ {child} 映射表中缺失")
            errors += 1
            continue
        if actual is None:
            print(f"  ⚠️ {child} 无法读取实际版本，跳过（不阻断）")
            continue
        if doc[0] == actual:
            print(f"  ✅ {child} 文档 {doc[0]} == 实际 {actual}")
        else:
            print(f"  ❌ {child} 文档 {doc[0]} != 实际 {actual}")
            errors += 1

    # 外部依赖（仅告警）
    print("[version-gate] 外部依赖校验（能力地板，仅告警）：")
    for name, floor in parse_external_deps(text):
        actual = read_frontmatter_version(SKILLS_DIR / name / "SKILL.md")
        if actual is None:
            print(f"  ⚠️ {name} 无法确定实际版本（无 frontmatter version），跳过")
            continue
        if floor and version_ge(actual, floor):
            print(f"  ✅ {name} 实际 {actual} >= 地板 ≥{floor}")
        elif floor:
            print(f"  ⚠️ {name} 实际 {actual} < 地板 ≥{floor}（已漂移，请复核联动）")
        else:
            print(f"  ⚠️ {name} 实际 {actual}，未声明能力地板")

    if errors:
        print(f"[version-gate] ❌ 内部版本不一致（{errors} 处），提交被阻断。运行 sync 修复。")
        return 1
    print("[version-gate] ✅ 内部一致，放行。")
    return 0


def cmd_sync() -> int:
    if not PARENT_FILE.exists():
        print("⚠️ 找不到母技能 SKILL.md。")
        return 2
    text = PARENT_FILE.read_text(encoding="utf-8")
    parent_ver = read_frontmatter_version(PARENT_FILE) or "?"

    lines = [MARK_START, "### 版本映射", "",
             "| 技能 | 当前版本 | 最后更新 |", "|-----|---------|---------|"]
    lines.append(f"| ip-management-compliance（母技能） | v{parent_ver} | {git_date(PARENT_FILE)} |")
    for child in CHILDREN:
        cf = SKILLS_DIR / child / "SKILL.md"
        v = read_frontmatter_version(cf) or "?"
        lines.append(f"| {child} | v{v} | {git_date(cf)} |")
    lines.append(MARK_END)
    block = "\n".join(lines)

    if MARK_START in text and MARK_END in text:
        pattern = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), re.DOTALL)
        new_text = pattern.sub(block, text)
    else:
        # 标记缺失：在「### 运行时依赖」前插入整块
        new_text = text.replace(
            "### 运行时依赖",
            block + "\n\n### 运行时依赖",
            1,
        )
    PARENT_FILE.write_text(new_text, encoding="utf-8")
    print("[version-gate] 已根据 frontmatter 重新生成版本映射表。")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "sync"):
        print("用法: versions.py {check|sync}")
        return 2
    try:
        if sys.argv[1] == "check":
            return cmd_check()
        return cmd_sync()
    except Exception as e:  # 异常不阻断正常提交流程
        print(f"[version-gate] ⚠️ 脚本异常（{e}），放行。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
