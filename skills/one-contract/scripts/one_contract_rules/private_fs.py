#!/usr/bin/env python3
"""私密目录与文件的权限收口。

契约来源：safety-and-acceptance.md SEC-013（客户目录 0700、文件 0600）；
architecture-contract.md §8.2（显示名等属私有数据，不进入公开包或普通日志）；
§8.5 / §10（快照与审计的落盘）。

**为什么单独成模块**：权限不能靠"每个写入点记得写 chmod"。
`client_repository` 与 `proposal_repository` 各自做了一份收口，而
`publisher`（active-manifest.json、snapshots/*/manifest.json、rules.json）
与 `audit`（audit/events.jsonl）各有自己的写入路径、都没有收口，
于是这些文件以 0644 落盘、目录以 0755 落盘——客户规则正文与审计记录
同机其他用户可读（W7-SEC013 的成因）。把收口收敛到一处，新写入点
只要走这里的函数就不会再漏。

模式常量与 `client_repository` / `proposal_repository` 保持一致；
本模块只负责"权限与原子落盘"，不承担任何业务语义。
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "DIR_MODE",
    "FILE_MODE",
    "atomic_write_json",
    "secure_append_line",
    "secure_dir",
    "secure_path",
]

#: 私密目录/文件权限：同机其他用户不可读、不可进入
DIR_MODE = 0o700
FILE_MODE = 0o600


def secure_dir(path: Path) -> None:
    """创建目录（如需）并把权限收为 0700。"""
    Path(path).mkdir(parents=True, exist_ok=True)
    os.chmod(path, DIR_MODE)


def secure_path(path: Path) -> None:
    """把**已存在**的路径权限收口：目录 0700、文件 0600。

    用于收口由其它工具或早期版本以宽松权限创建的既有数据，
    不改动内容。不存在则静默跳过（收口不是创建）。
    """
    path = Path(path)
    if path.is_dir():
        os.chmod(path, DIR_MODE)
    elif path.is_file():
        os.chmod(path, FILE_MODE)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """原子写 JSON：同目录临时文件 → flush+fsync → 收权限 → rename。

    先收临时文件权限再 rename，避免出现"已就位但权限过宽"的窗口。
    JSON 格式（``ensure_ascii=False, indent=2, sort_keys=True`` + 尾换行）
    与仓库其余写入点一致，不改变内容与哈希。
    """
    path = Path(path)
    secure_dir(path.parent)
    tmp = path.parent / f".tmp-{path.name}.{uuid.uuid4().hex[:8]}"
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(tmp, FILE_MODE)
    os.replace(tmp, path)


def secure_append_line(path: Path, line: str) -> None:
    """向文本文件追加一行（JSONL 用），目录与文件权限均收口。

    追加是"就地"写，无法像原子写那样先收临时文件权限；
    因此在写入后立即收口，且每次追加都重设一次——
    这同时会修正早期版本留下的宽松权限文件。
    """
    path = Path(path)
    secure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, FILE_MODE)
