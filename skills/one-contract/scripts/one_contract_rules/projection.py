#!/usr/bin/env python3
"""公共知识的三层规范化投影。

契约来源：architecture-contract.md §5（RuleNode）、§12.1（知识地图）、
safety-and-acceptance.md VIS-001~VIS-003、§4.1（2.8.1 回归锚点）。

三层结构与可见性规则：
- 第一层（global）：三份 Markdown 政策文档节点，`document_node`，不逐条拆分；
- 第二层（domain）：EC-01~EC-10，候选一律 `metadata_only_candidate`；
- 第三层（type）：原则卡、条款模块、模块组、触发器、来源、经验卡、模板，
  运行投影只返回 active 正文。

节点种类与 `rule-graph-v1` 的 `node_kind` 枚举存在映射关系。本模块以
**schema 为准**（它是冻结的机器真源），内部语义名保留在 `models.RULE_NODE_KINDS`。
两者不一致属 W1 遗留缺陷，已在 W2 completion 中记为 ADR 提案。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import models

__all__ = [
    "ASSET_KIND_TO_SCHEMA_KIND",
    "DOMAIN_LAYER",
    "GLOBAL_LAYER",
    "TYPE_LAYER",
    "asset_node_id",
    "node_to_schema_dict",
    "project_domain_node",
    "project_global_document_node",
    "project_type_node",
    "schema_kind_for",
]

GLOBAL_LAYER = "global"
DOMAIN_LAYER = "domain"
TYPE_LAYER = "type"

#: 内部资产种类 → rule-graph-v1 的 node_kind 枚举
ASSET_KIND_TO_SCHEMA_KIND: Mapping[str, str] = {
    "domain_principle": "domain_principle",
    "type_principle": "type_principle",
    "clause_module": "module",
    "module_group": "module_group",
    "trigger": "trigger",
    "knowledge_source": "source",
    "experience_card": "module",   # schema 无 experience 枚举，归入 module 语义层
    "template": "module",          # 同上
    "global_document": "global_document",
    "client_rule": "client_rule",
}

_ID_KEYS: Sequence[str] = (
    "domain_doctrine_id", "doctrine_id", "module_id", "module_group_id",
    "trigger_id", "source_id", "experience_id", "template_id",
)


class ProjectionError(Exception):
    """投影无法生成。调用方不得降级为部分节点。"""


def schema_kind_for(asset_kind: str) -> str:
    try:
        return ASSET_KIND_TO_SCHEMA_KIND[asset_kind]
    except KeyError:
        raise ProjectionError(f"未登记的资产种类: {asset_kind!r}") from None


def node_to_schema_dict(
    node: models.RuleNode,
    *,
    body: Any = None,
    body_visibility: Optional[str] = None,
) -> Dict[str, Any]:
    """把 `models.RuleNode` 适配为 `rule-graph-v1` 的 `ruleNode` 结构。

    这是本包唯一的适配点，用于吸收 W1 遗留的模型/schema 差异：

    - `rule-graph-v1` 要求 `body` 字段，`models.RuleNode` 没有该字段；
    - schema 另有 `contract_type` / `module` / `source` 等 node_kind 名，
      与 `models.RULE_NODE_KINDS` 的语义名不同。

    `layer` 直接沿用节点上的值：`models.SOURCE_LAYERS` 的 `global|domain|type`
    与 schema 的 `layer` 枚举一致；`client` / `case_instruction` 不属本包范围。

    差异整体记录在 W2 completion 的 ADR 提案中，不在此处静默修改共享契约。
    """
    if node.layer not in ("global", "domain", "type"):
        raise ProjectionError(
            f"公共投影不应出现 layer={node.layer!r}；客户层由 W3B 负责。"
        )
    return {
        "node_id": node.node_id,
        "node_kind": schema_kind_for(node.node_kind),
        "layer": node.layer,
        "title": node.title,
        "version": node.version,
        "approval_status": node.approval_status,
        "activation_status": node.activation_status,
        "body_visibility": body_visibility or node.body_visibility,
        "body": body,
        "domain_codes": list(node.domain_codes),
        "type_ids": list(node.type_ids),
        "roles": list(node.roles),
        "scene_tags": list(node.scene_tags),
        "source_refs": list(node.source_refs),
        "summary": node.summary,
        "updated_at": node.updated_at,
        "content_hash": node.content_hash,
    }


def _stable_id(asset: Mapping[str, Any]) -> str:
    for key in _ID_KEYS:
        if asset.get(key):
            return str(asset[key])
    raise ProjectionError("资产缺少稳定 ID，无法投影。")


def asset_node_id(asset: Mapping[str, Any], *, asset_kind: str) -> str:
    """返回 Rule Studio 中唯一、稳定的节点 ID。

    类型原则是“可复用原则 × 具体合同类型”的映射记录。同一 `doctrine_id`
    可以服务多个类型，因此不能单独作为可视化节点主键；否则详情、提案与局部图
    只能命中第一条记录。运行时规则仍保留 doctrine_id，本函数只解决维护投影的
    唯一定位问题。
    """
    stable_id = _stable_id(asset)
    if asset_kind == "type_principle":
        type_id = asset.get("type_id")
        if not type_id:
            raise ProjectionError("类型原则缺少 type_id，无法生成唯一节点 ID。")
        return f"{stable_id}::{type_id}"
    return stable_id


def _is_runtime_active(asset: Mapping[str, Any]) -> bool:
    return (
        asset.get("approval_status") == "active"
        and asset.get("activation_status") == "active"
    )


def _activation_status_for_schema(value: Any) -> str:
    """rule-graph-v1 的 activation_status 只允许 active|inactive。"""
    return "active" if value == "active" else "inactive"


def project_global_document_node(*, relative_path: str, title: str) -> models.RuleNode:
    """第一层：政策文档节点。只读呈现，不拆分为正式规则（ADR-013）。"""
    return models.RuleNode(
        node_id=relative_path,
        node_kind="global_document",
        layer=GLOBAL_LAYER,
        title=title,
        version="n/a",
        approval_status="active",
        activation_status="active",
        body_visibility="document_node",
        summary=f"全局政策文档：{title}",
    ).with_hash()


def project_domain_node(asset: Mapping[str, Any]) -> models.RuleNode:
    """第二层：大类原则卡。候选只给影子元数据，不暴露正文。

    node_id 采用 `domain_code`（EC-01..EC-10）：它是知识地图与筛选器的
    稳定入口，也是运维与文档中唯一被使用的第二层标识。
    `domain_doctrine_id` 保留在 `source_refs` 中以便追溯原始资产。
    """
    domain_code = asset.get("domain_code") or ""
    doctrine_id = asset.get("domain_doctrine_id")
    coverage = (asset.get("coverage") or {}).get("coverage_status")
    active = _is_runtime_active(asset)
    source_refs = list(asset.get("source_ids") or ())
    if doctrine_id:
        source_refs.insert(0, str(doctrine_id))
    return models.RuleNode(
        node_id=str(domain_code or doctrine_id or ""),
        node_kind="domain_principle",
        layer=DOMAIN_LAYER,
        title=str(asset.get("domain_name") or domain_code),
        version=str(asset.get("version") or "n/a"),
        approval_status=str(asset.get("approval_status") or "candidate"),
        activation_status=_activation_status_for_schema(asset.get("activation_status")),
        body_visibility="full_active" if active else "metadata_only_candidate",
        domain_codes=(domain_code,) if domain_code else (),
        type_ids=tuple(asset.get("derived_principle_ids") or ()),
        source_refs=tuple(dict.fromkeys(source_refs)),
        summary=f"覆盖等级 {coverage}" if coverage else None,
    ).with_hash()


def project_type_node(asset: Mapping[str, Any], *, asset_kind: str) -> models.RuleNode:
    """第三层：原则卡、模块、模块组、触发器、来源等。"""
    active = _is_runtime_active(asset)
    domain_codes: Tuple[str, ...] = ()
    if asset.get("type_code"):
        domain_codes = (str(asset["type_code"]).split("-")[0] + "-" + str(asset["type_code"]).split("-")[1],)

    title = (
        asset.get("name") or asset.get("title") or asset.get("module_id")
        or asset.get("trigger_id") or asset.get("source_id") or _stable_id(asset)
    )

    source_refs = list(asset.get("source_ids") or ())
    if asset_kind == "type_principle" and asset.get("doctrine_id"):
        source_refs.insert(0, str(asset["doctrine_id"]))
    if asset.get("source_id"):
        source_refs.insert(0, asset["source_id"])

    return models.RuleNode(
        node_id=asset_node_id(asset, asset_kind=asset_kind),
        # 此处保留**语义种类**（models.RULE_NODE_KINDS 的取值），
        # 到 `node_to_schema_dict` 输出时才映射为 rule-graph-v1 的 node_kind 枚举。
        node_kind=asset_kind,
        layer=TYPE_LAYER,
        title=str(title),
        version=str(asset.get("version") or "n/a"),
        approval_status=str(asset.get("approval_status") or "candidate"),
        activation_status=_activation_status_for_schema(asset.get("activation_status")),
        body_visibility="full_active" if active else "metadata_only_candidate",
        domain_codes=domain_codes,
        type_ids=tuple(asset.get("type_ids") or (([asset["type_id"]] if asset.get("type_id") else []))),
        roles=tuple(asset.get("roles") or ()),
        scene_tags=tuple(asset.get("scene_tags") or ()),
        source_refs=tuple(dict.fromkeys(source_refs)),
        summary=str(asset.get("review_objective") or asset.get("description") or "") or None,
    ).with_hash()
