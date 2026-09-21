#!/usr/bin/env python3
"""离线 Schema registry。

契约来源：architecture-contract.md §8.5 末段、§16；CON-001。

要求：
- Schema loader 只从随包的本地白名单注册表解析引用，禁止远程抓取；
- 断网时必须能完成全部解析（不得访问 `$id` 对应网络地址）；
- 未知 `$id` fail closed；
- 产品代码只加载本目录版本，不回读开发交接包（ADR-027）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from . import paths

__all__ = [
    "PRODUCT_ID_PREFIX",
    "SchemaRegistryError",
    "build_registry",
    "get_schema",
    "list_schema_ids",
    "make_validator",
    "load_schema_from_uri",
]

PRODUCT_ID_PREFIX = "one-contract/"

_CACHE: Dict[str, object] = {}


class SchemaRegistryError(Exception):
    """Schema 无法解析或不存在。不得降级为跳过校验。"""


def _iter_schema_files():
    directory = paths.schema_dir()
    if not directory.is_dir():
        raise SchemaRegistryError("产品 Schema 目录不存在；无法构建 registry。")
    return sorted(directory.glob("*.json"))


def _load_local_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaRegistryError(f"Schema 文件不是合法 JSON: {path.name}") from exc


def build_registry() -> Registry:
    """构建只含本地 schema 的 Registry。结果按目录内容缓存。"""
    cached = _CACHE.get("registry")
    if cached is not None:
        return cached  # type: ignore[return-value]

    registry = Registry()
    for path in _iter_schema_files():
        document = _load_local_file(path)
        schema_id = document.get("$id")
        if not isinstance(schema_id, str) or not schema_id.startswith(PRODUCT_ID_PREFIX):
            raise SchemaRegistryError(
                f"Schema {path.name} 的 $id 缺失或未使用 {PRODUCT_ID_PREFIX} 命名空间。"
            )
        registry = registry.with_resource(
            schema_id, Resource.from_contents(document, default_specification=DRAFT202012)
        )
    _CACHE["registry"] = registry
    return registry


def list_schema_ids(reg: Registry | None = None) -> List[str]:
    """列出已注册的 schema `$id`。"""
    out: List[str] = []
    for path in _iter_schema_files():
        document = _load_local_file(path)
        schema_id = document.get("$id")
        if isinstance(schema_id, str):
            out.append(schema_id)
    return sorted(out)


def get_schema(schema_id: str) -> dict:
    """按 `$id` 取回 schema。未知 ID fail closed。"""
    for path in _iter_schema_files():
        document = _load_local_file(path)
        if document.get("$id") == schema_id:
            return document
    raise SchemaRegistryError(
        f"未注册的 Schema ID: {schema_id!r}。只允许加载产品 schemas 目录中的白名单条目。"
    )


def make_validator(schema_id: str) -> Draft202012Validator:
    """为指定 schema 构造离线验证器（含日期等格式校验）。"""
    return make_validator_from_schema(get_schema(schema_id))


def make_validator_from_schema(schema: dict) -> Draft202012Validator:
    """用**给定的 schema 文档**构造离线验证器，`$ref` 仍从本地白名单解析。

    用途：个别约束因契约尚未裁决而需显式豁免时（见
    `validator.validate_client_snapshot(defer_evidence_refs=True)`），
    需要对 schema 的一个副本求值——但绝不能因此失去离线 `$ref` 解析能力，
    否则校验会退化成"看起来在校验"。
    """
    return Draft202012Validator(
        schema, registry=build_registry(), format_checker=FormatChecker()
    )


def load_schema_from_uri(uri: str) -> dict:
    """按 URI 加载 schema。

    只接受 `one-contract/<name>` 形式的本地标识。
    任何 http(s) 或其他远程 URI 一律拒绝——离线是硬约束，不是优化项。
    """
    if uri.startswith("http://") or uri.startswith("https://"):
        raise SchemaRegistryError(
            "拒绝远程 Schema 抓取；请使用本地 one-contract/ 命名空间标识。"
        )
    return get_schema(uri)
