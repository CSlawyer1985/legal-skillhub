#!/usr/bin/env python3
"""路径解析与 containment。

契约来源：architecture-contract.md §9（数据根与路径安全）、§8.5（指纹口径）。

原则：
- Rules Core 显式接收或持有已验证的 skill_root 与 data_root，不依赖当前工作目录；
- 客户数据必须在 skill 目录之外（RS-HC-003）；
- 所有写入路径先 resolve，再校验落在 data root 内；
- 本模块不读取全局 .env，不扫描用户主目录寻找客户数据。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable, Optional, Union

__all__ = [
    "APP_DIR_NAME",
    "ENV_VAR",
    "PathContractError",
    "PROFILE_ID_PATTERN",
    "contained_path",
    "is_safe_profile_id",
    "platform_default_data_root",
    "resolve_data_root",
    "schema_dir",
    "skill_root",
]

ENV_VAR = "ONE_CONTRACT_DATA_DIR"
APP_DIR_NAME = "one-contract"

# 稳定 ID 只允许小写字母、数字、连字符与下划线，且必须以字母数字开头。
PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")

_PACKAGE_DIR = Path(__file__).resolve().parent


class PathContractError(Exception):
    """路径不满足契约。调用方不得捕获后继续写入。"""


def skill_root() -> Path:
    """候选 Skill 根目录（本文件位于 <skill>/scripts/one_contract_rules/）。"""
    return _PACKAGE_DIR.parents[1]


def schema_dir() -> Path:
    """产品契约 Schema 目录。迁入后的版本是唯一运行时真源（ADR-027）。"""
    return _PACKAGE_DIR / "schemas"


def platform_default_data_root() -> Path:
    """操作系统用户级应用数据目录。此处只计算，不创建。"""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_DIR_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_DIR_NAME


def resolve_data_root(explicit: Optional[Union[str, Path]] = None) -> Path:
    """解析数据根。

    顺序：显式参数 > ONE_CONTRACT_DATA_DIR > 平台默认。
    仅计算与校验，不创建目录，不写盘。
    """
    if explicit is not None:
        candidate = Path(explicit)
        source = "explicit"
    elif os.environ.get(ENV_VAR):
        candidate = Path(os.environ[ENV_VAR])
        source = ENV_VAR
    else:
        candidate = platform_default_data_root()
        source = "platform_default"

    if candidate.exists() and not candidate.is_dir():
        raise PathContractError(
            f"data root 指向已存在的非目录（来源: {source}）；请改用目录路径。"
        )
    return candidate.expanduser().resolve()


def is_safe_profile_id(value: object) -> bool:
    """profile ID 只允许安全字符；拒绝绝对路径、点段、分隔符、NUL 与非 ASCII。"""
    if not isinstance(value, str):
        return False
    if "\x00" in value:
        return False
    return bool(PROFILE_ID_PATTERN.match(value))


def _reject_unsafe_segment(segment: str) -> None:
    if "\x00" in segment:
        raise PathContractError("路径片段含 NUL 字节；请求已拒绝。")
    if segment in ("..",):
        raise PathContractError("路径片段含上级目录引用；请求已拒绝。")
    if os.path.isabs(segment) or segment.startswith("~"):
        raise PathContractError("路径片段为绝对路径；请求已拒绝。")
    if os.sep in segment or (os.altsep and os.altsep in segment):
        raise PathContractError("路径片段含路径分隔符；请求已拒绝。")


def contained_path(root: Union[str, Path], *segments: str) -> Path:
    """把 *segments* 拼到 *root* 之下，并保证结果仍在 root 内。

    校验两层：
    1. 静态：逐段拒绝 NUL、`..`、绝对路径与分隔符；
    2. 动态：resolve 后复核是否仍在 root 内（覆盖符号链接越界）。
    越界一律抛 PathContractError，调用方不得降级为静默忽略。
    """
    resolved_root = Path(root).expanduser().resolve()
    for segment in segments:
        if not isinstance(segment, str):
            raise PathContractError("路径片段必须是字符串；请求已拒绝。")
        _reject_unsafe_segment(segment)

    target = resolved_root.joinpath(*segments) if segments else resolved_root

    # 逐级向上找到最近的已存在祖先，用于符号链接越界检查。
    probe = target
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    real_probe = probe.resolve()
    if real_probe != resolved_root and resolved_root not in real_probe.parents:
        raise PathContractError(
            "目标路径经解析后落在 data root 之外（可能为符号链接越界）；请求已拒绝。"
        )

    if target.exists():
        real_target = target.resolve()
        if real_target != resolved_root and resolved_root not in real_target.parents:
            raise PathContractError(
                "目标路径经解析后落在 data root 之外；请求已拒绝。"
            )
    return target


def join_checked(root: Union[str, Path], segments: Iterable[str]) -> Path:
    """contained_path 的可迭代包装。"""
    return contained_path(root, *tuple(segments))
