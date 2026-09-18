#!/usr/bin/env python3
"""法律 Skill 工具链共享的安全、解析与证据辅助函数。

仅依赖 Python 标准库；该模块不执行输入材料中的任何内容。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path


PLACEHOLDER_MARKERS = ("【填写", "【替换", "replace-with", "示例仅供")


def contains_placeholder(text: str) -> bool:
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def safe_relative_path(value: object) -> bool:
    """只接受普通相对路径，并拒绝 POSIX/Windows 两类目录逃逸。"""
    if not isinstance(value, str) or not value.strip():
        return False
    raw = value.replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw) or raw.startswith("//"):
        return False
    parts = [part for part in raw.split("/") if part not in ("",)]
    if any(part in {".", ".."} for part in parts):
        return False
    return bool(parts)


def resolve_regular_file(root: Path, relative: object, label: str) -> Path:
    """解析包内普通文件，拒绝软链接、越界和非普通文件。"""
    if not safe_relative_path(relative):
        raise ValueError(f"{label} 必须为包内安全相对路径")
    root = root.absolute()
    candidate = root.joinpath(*str(relative).replace("\\", "/").split("/"))
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} 必须位于包内：{relative}") from exc
    current = root
    for part in candidate.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} 不得经过软链接：{relative}")
    if not candidate.is_file():
        raise ValueError(f"{label} 不存在或不是普通文件：{relative}")
    return candidate


def load_json_file(path: Path, label: str, *, max_bytes: int = 2_000_000) -> object:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"{label} 超过允许大小 {max_bytes} 字节")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} 无法读取或解析：{exc}") from exc


def valid_review_date(value: object, *, today: date | None = None) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return False
    return parsed <= (today or date.today())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_frontmatter(text: str) -> tuple[str, str]:
    """解析本项目使用的 frontmatter 子集，保证畸形输入返回 ValueError。"""
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md 缺少有效 YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("SKILL.md 的 YAML frontmatter 未闭合")
    body = text[4:end]
    lines = body.splitlines()
    name: str | None = None
    description_parts: list[str] = []
    collecting_description = False
    for line in lines:
        if re.match(r"^name:\s*", line):
            if name is not None:
                raise ValueError("frontmatter 的 name 重复")
            name = line.split(":", 1)[1].strip().strip("\"'")
            collecting_description = False
        elif re.match(r"^description:\s*", line):
            if description_parts:
                raise ValueError("frontmatter 的 description 重复")
            first = line.split(":", 1)[1].strip()
            if first in ("", "|"):
                collecting_description = True
            else:
                description_parts.append(first.strip("|\t "))
                collecting_description = True
        elif collecting_description and line.startswith("  "):
            description_parts.append(line.strip())
        elif collecting_description and line.strip():
            collecting_description = False
    description = " ".join(part for part in description_parts if part).strip(" |\t")
    if not name or not description:
        raise ValueError("frontmatter 必须包含非空 name 和 description")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise ValueError("name 必须为不超过 64 字符的小写字母、数字和单连字符组合")
    if len(description) > 1024:
        raise ValueError("description 超过官方 1024 字符限制")
    return name, description
