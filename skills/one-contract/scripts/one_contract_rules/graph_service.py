#!/usr/bin/env python3
"""局部规则关系图。

契约来源：architecture-contract.md §5（RuleEdge、edge_kind）、§12.1（当前节点局部图）、
ADR-014（局部图而非全量巨图）、TASKS.md W2「不把共享模块复制成多个规则对象」。

边由资产自身的引用字段派生，不复制共享模块：
- 模块/原则的 `dependencies` → `depends_on`
- 原则的 `linked_module_ids`      → `contains`
- 任一所引 `source_ids`           → `sourced_from`
- 模块组 `member_module_ids`      → `contains`
- 触发器 `required_modules`       → `depends_on`
- 触发器的 `type_id` 归属         → `inherits`

断裂引用标记为 `status="broken"` 并保留在图中，使前端可显示警告，
而不是静默丢弃（VIS-006）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from . import models, projection

__all__ = [
    "RuleGraph",
    "derive_edges",
    "build_local_graph",
]

_SCHEMA_VERSION = "1.0"


class GraphError(Exception):
    """关系图无法生成。"""


@dataclass(frozen=True)
class RuleGraph:
    schema_version: str
    public_snapshot_id: str
    nodes: Tuple[Dict[str, Any], ...]
    edges: Tuple[Dict[str, Any], ...]
    projection_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "public_snapshot_id": self.public_snapshot_id,
            "nodes": [dict(n) for n in self.nodes],
            "edges": [dict(e) for e in self.edges],
            "projection_hash": self.projection_hash,
        }


def _edge(
    from_id: str,
    to_id: str,
    kind: str,
    known_ids: Set[str],
    *,
    scope: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "edge_id": f"{kind}:{from_id}->{to_id}",
        "from_id": from_id,
        "to_id": to_id,
        "edge_kind": kind,
        "scope": dict(scope or {}),
        "source": "knowledge_v2",
        "status": "valid" if to_id in known_ids else "broken",
    }


def derive_edges(
    asset: Mapping[str, Any],
    known_ids: Set[str],
    *,
    from_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """从一个资产的引用字段派生边。不修改资产，不复制共享模块。"""
    node_id = from_id
    if node_id is None:
        for key in (
            "domain_doctrine_id", "doctrine_id", "module_id", "module_group_id",
            "trigger_id", "source_id", "experience_id", "template_id",
        ):
            if asset.get(key):
                node_id = str(asset[key])
                break
    if node_id is None:
        return []

    edges: List[Dict[str, Any]] = []
    for target in asset.get("dependencies") or ():
        edges.append(_edge(node_id, str(target), "depends_on", known_ids))
    for target in asset.get("linked_module_ids") or ():
        edges.append(_edge(node_id, str(target), "contains", known_ids))
    for target in asset.get("member_module_ids") or ():
        edges.append(_edge(node_id, str(target), "contains", known_ids))
    for target in asset.get("required_modules") or ():
        edges.append(_edge(node_id, str(target), "depends_on", known_ids))
    for target in asset.get("derived_module_ids") or ():
        edges.append(_edge(node_id, str(target), "contains", known_ids))
    for target in asset.get("source_ids") or ():
        edges.append(_edge(node_id, str(target), "sourced_from", known_ids))
    if asset.get("source_id"):
        edges.append(_edge(node_id, str(asset["source_id"]), "sourced_from", known_ids))
    if asset.get("type_id"):
        edges.append(_edge(node_id, str(asset["type_id"]), "inherits", known_ids))
    return edges


def _collect_nodes(repository: Any, focus_node_id: Optional[str], depth: int) -> List[models.RuleNode]:
    all_nodes = repository.list_rule_tree()
    if focus_node_id is None:
        return list(all_nodes)

    by_id = {n.node_id: n for n in all_nodes}
    if focus_node_id not in by_id:
        raise GraphError(f"焦点节点不存在: {focus_node_id}")

    selected: Set[str] = {focus_node_id}
    frontier = {focus_node_id}
    for _ in range(max(0, depth)):
        next_frontier: Set[str] = set()
        for node_id in frontier:
            for edge in repository.get_rule_neighbors(node_id):
                for candidate in (edge.from_id, edge.to_id):
                    if candidate not in selected:
                        selected.add(candidate)
                        next_frontier.add(candidate)
        frontier = next_frontier
        if not frontier:
            break
    return [by_id[nid] for nid in sorted(selected) if nid in by_id]


def build_local_graph(
    repository: Any,
    *,
    focus_node_id: Optional[str] = None,
    depth: int = 1,
) -> RuleGraph:
    """构建当前节点附近的局部关系图（ADR-014：不做全量巨图）。"""
    nodes = _collect_nodes(repository, focus_node_id, depth)
    node_dicts = [
        projection.node_to_schema_dict(node, body=None) for node in nodes
    ]

    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    if focus_node_id is not None:
        for edge in repository.get_rule_neighbors(focus_node_id):
            payload = {
                "edge_id": edge.edge_id,
                "from_id": edge.from_id,
                "to_id": edge.to_id,
                "edge_kind": edge.edge_kind,
                "scope": dict(edge.scope or {}),
                "source": edge.source or "knowledge_v2",
                "status": edge.status or "valid",
            }
            if payload["edge_id"] not in seen:
                seen.add(payload["edge_id"])
                edges.append(payload)

    payload = {
        "schema_version": _SCHEMA_VERSION,
        "public_snapshot_id": repository.public_snapshot_id,
        "nodes": node_dicts,
        "edges": edges,
    }
    return RuleGraph(
        schema_version=_SCHEMA_VERSION,
        public_snapshot_id=repository.public_snapshot_id,
        nodes=tuple(node_dicts),
        edges=tuple(edges),
        projection_hash=models.content_hash(payload, exclude=("projection_hash",)),
    )
