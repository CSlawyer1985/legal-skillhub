#!/usr/bin/env python3
"""公共知识的目录索引。

契约来源：architecture-contract.md §3（list_rule_tree / get_rule / search_rules）、
safety-and-acceptance.md §4.1（2.8.1 回归锚点）。

原则：
- 只读。本模块不提供任何写方法。
- 统计一律由当前目录内容计算，前端不得硬编码数量。
- 索引按 skill_root 缓存，同一次审查内复用同一内存投影。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from . import paths

__all__ = [
    "ASSET_FILES",
    "CatalogIndex",
    "CatalogIndexError",
    "build_catalog_index",
]

#: 参与索引的资产文件（相对 assets/knowledge_v2）
ASSET_FILES: Tuple[str, ...] = (
    "asset_manifest.json",
    "taxonomy_v2.json",
    "domain_principle_catalog.json",
    "principle_catalog.json",
    "module_catalog.json",
    "module_group_catalog.json",
    "trigger_catalog.json",
    "source_catalog.json",
    "experience_catalog.json",
    "template_catalog.json",
)

_ASSET_SUBDIR = "assets/knowledge_v2"


class CatalogIndexError(Exception):
    """资产缺失或结构不符。调用方不得降级为部分索引。"""


@dataclass(frozen=True)
class CatalogIndex:
    """公共知识资产的只读内存索引。"""

    manifest: Mapping[str, Any]
    taxonomy: Mapping[str, Any]
    domain_principles: Tuple[Mapping[str, Any], ...]
    type_principles: Tuple[Mapping[str, Any], ...]
    modules: Tuple[Mapping[str, Any], ...]
    module_groups: Tuple[Mapping[str, Any], ...]
    triggers: Tuple[Mapping[str, Any], ...]
    sources: Tuple[Mapping[str, Any], ...]
    experience_cards: Tuple[Mapping[str, Any], ...]
    templates: Tuple[Mapping[str, Any], ...]

    # ---- 统计（由目录内容计算，非硬编码）--------------------------------- #
    @property
    def domain_principle_count(self) -> int:
        return len(self.domain_principles)

    @property
    def type_count(self) -> int:
        return len(self.taxonomy.get("catalog_types", ()))

    @property
    def module_count(self) -> int:
        return len(self.modules)

    @property
    def module_group_count(self) -> int:
        return len(self.module_groups)

    @property
    def trigger_count(self) -> int:
        return len(self.triggers)

    @property
    def active_type_count(self) -> int:
        return len(self.manifest.get("active_type_ids", ()))

    @property
    def active_module_count(self) -> int:
        return len(self.manifest.get("active_module_ids", ()))

    @property
    def active_domain_principle_count(self) -> int:
        return len(self.manifest.get("active_domain_doctrine_ids", ()))

    @property
    def active_type_principle_count(self) -> int:
        return len(self.manifest.get("active_doctrine_ids", ()))

    # ---- 词表（用于 fail closed 校验）------------------------------------ #
    @property
    def valid_roles(self) -> frozenset:
        roles = {"any"}
        for collection in (self.modules, self.type_principles):
            for item in collection:
                roles.update(item.get("roles", ()) or ())
        return frozenset(roles)

    @property
    def valid_scene_tags(self) -> frozenset:
        scenes = set()
        for collection in (self.modules, self.type_principles):
            for item in collection:
                scenes.update(item.get("scene_tags", ()) or ())
        return frozenset(scenes)

    @property
    def type_to_domain(self) -> Mapping[str, str]:
        mapping: Dict[str, str] = {}
        for item in self.taxonomy.get("catalog_types", ()):
            if item.get("type_id") and item.get("domain_code"):
                mapping[item["type_id"]] = item["domain_code"]
        for item in self.taxonomy.get("domain_fallbacks", ()):
            if item.get("type_id") and item.get("domain_code"):
                mapping[item["type_id"]] = item["domain_code"]
        return mapping

    # ---- 查询（只读）------------------------------------------------------ #
    def collections(self) -> Tuple[Tuple[Mapping[str, Any], ...], ...]:
        """全部资产集合（每个元素是一个 catalog 的资产元组）。"""
        return (
            self.domain_principles, self.type_principles, self.modules,
            self.module_groups, self.triggers, self.sources,
            self.experience_cards, self.templates,
        )

    def all_nodes(self) -> Tuple[Mapping[str, Any], ...]:
        """把全部 catalog 的资产摊平为单层元组。"""
        return tuple(
            item for collection in self.collections() for item in collection
        )

    _ID_KEYS: Tuple[str, ...] = (
        "domain_doctrine_id", "doctrine_id", "module_id", "module_group_id",
        "trigger_id", "source_id", "experience_id", "template_id",
    )

    def lookup(self, stable_id: str) -> Optional[Mapping[str, Any]]:
        """按稳定 ID 查单条资产。找不到返回 None，不抛错（由调用方决定语义）。"""
        for item in self.all_nodes():
            for key in self._ID_KEYS:
                if item.get(key) == stable_id:
                    return item
        return None

    def known_ids(self) -> frozenset:
        ids = set()
        for item in self.all_nodes():
            for key in self._ID_KEYS:
                if item.get(key):
                    ids.add(item[key])
        return frozenset(ids)


_CACHE: Dict[str, CatalogIndex] = {}


def _load_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise CatalogIndexError(f"资产文件缺失: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogIndexError(f"资产文件不是合法 JSON: {path.name}") from exc


def _assets_of(document: Mapping[str, Any], name: str) -> Tuple[Mapping[str, Any], ...]:
    if "assets" not in document:
        raise CatalogIndexError(f"{name} 缺少 assets 数组")
    return tuple(document["assets"])


def build_catalog_index(*, skill_root: Optional[Path] = None) -> CatalogIndex:
    """构建目录索引。纯读，不写盘、不联网。"""
    root = Path(skill_root) if skill_root is not None else paths.skill_root()
    cache_key = str(root)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    asset_root = root / _ASSET_SUBDIR
    if not asset_root.is_dir():
        raise CatalogIndexError(f"资产目录缺失: {_ASSET_SUBDIR}")

    docs = {name: _load_json(asset_root / name) for name in ASSET_FILES}

    index = CatalogIndex(
        manifest=docs["asset_manifest.json"],
        taxonomy=docs["taxonomy_v2.json"],
        domain_principles=_assets_of(docs["domain_principle_catalog.json"], "domain_principle_catalog"),
        type_principles=_assets_of(docs["principle_catalog.json"], "principle_catalog"),
        modules=_assets_of(docs["module_catalog.json"], "module_catalog"),
        module_groups=_assets_of(docs["module_group_catalog.json"], "module_group_catalog"),
        triggers=_assets_of(docs["trigger_catalog.json"], "trigger_catalog"),
        sources=_assets_of(docs["source_catalog.json"], "source_catalog"),
        experience_cards=_assets_of(docs["experience_catalog.json"], "experience_catalog"),
        templates=_assets_of(docs["template_catalog.json"], "template_catalog"),
    )
    _CACHE[cache_key] = index
    return index
