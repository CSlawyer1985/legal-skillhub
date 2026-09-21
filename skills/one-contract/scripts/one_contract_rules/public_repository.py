#!/usr/bin/env python3
"""只读公共资产 repository 与纯公共侧解析。

契约来源：architecture-contract.md §1（public repository 没有写方法）、
§3（公共读取 API）、§7（解析流程）、§14（与 2.8.1 选择器兼容）；
safety-and-acceptance.md RES-001~RES-010、VIS-001~VIS-003、VIS-007。

设计要点：
- **本模块不提供任何写方法**，也不存在公共写 API（RS-HC-001 / ADR-002）。
- 过滤语义复用既有选择器的 `applicable()`，避免第二套 active 判定导致结果漂移。
- 本包只做**纯公共**解析：客户 overlay 传 None，属 W3B 范围。
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from . import catalog_index, errors, fingerprint, graph_service, models, paths, projection

__all__ = [
    "GLOBAL_DOCUMENT_TITLES",
    "PublicRepository",
    "PublicResolutionError",
]

GLOBAL_DOCUMENT_TITLES: Mapping[str, str] = {
    "references/review-doctrine.md": "全局审查方法",
    "references/redline-comment-policy.md": "红线与批注策略",
    "references/common-clause-doctrine.md": "通用条款原则",
}

_KNOWN_LAYERS = ("global", "domain", "type")

#: 覆盖等级取值模式。
#: False（默认）= 透传 2.8.1 选择器结果，满足 INT-008「关键 notice 等价」；
#: True          = 使用语义更准确的取值（type_only 等），留待 2.9.x 评审后启用。
#: 切换前必须重新评估 INT-008 与 W7 的集成回归。
_COVERAGE_SEMANTIC_MODE = False

#: 资产种类 → 在 repository 中的集合名
_COLLECTIONS: Sequence[Tuple[str, str]] = (
    ("domain_principle", "domain_principles"),
    ("type_principle", "type_principles"),
    ("clause_module", "modules"),
    ("module_group", "module_groups"),
    ("trigger", "triggers"),
    ("knowledge_source", "sources"),
    ("experience_card", "experience_cards"),
    ("template", "templates"),
)


class PublicResolutionError(Exception):
    """纯公共侧解析无法给出可信结果。调用方不得降级为部分结果。"""


def _load_legacy_selector():
    """加载 2.8.1 既有选择器，复用其 active 判定，确保行为不分叉。"""
    path = paths.skill_root() / "scripts" / "knowledge" / "select_active_assets.py"
    spec = importlib.util.spec_from_file_location("_legacy_select_active_assets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class _Eligibility:
    applicable: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class _EligibilityPublic:
    """过滤结论的对外只读视图（供测试与后续包使用）。"""

    applicable: bool
    reason: Optional[str] = None


class PublicRepository:
    """公共知识资产的只读访问入口。"""

    def __init__(self, *, skill_root: Optional[Path] = None) -> None:
        self._skill_root = Path(skill_root) if skill_root else paths.skill_root()
        self._index = catalog_index.build_catalog_index(skill_root=self._skill_root)
        self._fingerprint = fingerprint.fingerprint_public_assets(skill_root=self._skill_root)
        self._legacy = _load_legacy_selector()
        self._assets_by_kind = self._build_asset_table()
        self._nodes_cache: Optional[Tuple[models.RuleNode, ...]] = None

    # ------------------------------------------------------------------ #
    # 身份
    # ------------------------------------------------------------------ #
    @property
    def public_snapshot_id(self) -> str:
        return self._fingerprint.public_snapshot_id

    @property
    def public_asset_fingerprint(self) -> str:
        return self._fingerprint.public_asset_fingerprint

    @property
    def resolver_semantics_version(self) -> str:
        return self._fingerprint.resolver_semantics_version

    @property
    def index(self) -> catalog_index.CatalogIndex:
        return self._index

    # ------------------------------------------------------------------ #
    # 只读读取
    # ------------------------------------------------------------------ #
    def list_rule_tree(
        self,
        *,
        layer: Optional[str] = None,
        type_id: Optional[str] = None,
        projection_mode: str = "maintenance",
    ) -> List[models.RuleNode]:
        """列出节点。`projection_mode="runtime"` 只暴露 active 正文。"""
        if layer is not None and layer not in _KNOWN_LAYERS:
            raise PublicResolutionError(
                f"未知 layer: {layer!r}；可用: {', '.join(_KNOWN_LAYERS)}。"
            )

        nodes = list(self._all_nodes())

        if layer is not None:
            nodes = [n for n in nodes if n.layer == layer]
        if type_id is not None:
            known = self._index.type_to_domain
            if type_id not in known:
                raise PublicResolutionError(
                    f"未知类型: {type_id!r} 不在 taxonomy 中。"
                )
            nodes = [n for n in nodes if type_id in n.type_ids]

        if projection_mode == "runtime":
            nodes = [
                self._runtime_view(n) for n in nodes
            ]
        return nodes

    def _runtime_view(self, node: models.RuleNode) -> models.RuleNode:
        """运行投影：候选只保留影子元数据，不携带正文。"""
        if node.approval_status == "active" and node.activation_status == "active":
            return node
        if node.node_kind == "global_document":
            return node
        return models.RuleNode(
            node_id=node.node_id,
            node_kind=node.node_kind,
            layer=node.layer,
            title=node.title,
            version=node.version,
            approval_status=node.approval_status,
            activation_status=node.activation_status,
            body_visibility="metadata_only_candidate",
            domain_codes=node.domain_codes,
            type_ids=node.type_ids,
            roles=node.roles,
            scene_tags=node.scene_tags,
            source_refs=node.source_refs,
            updated_at=node.updated_at,
            summary=node.summary,
        ).with_hash()

    def get_rule(self, rule_id: str) -> Optional[models.RuleNode]:
        for node in self._all_nodes():
            if node.node_id == rule_id:
                return node
        return None

    def get_rule_neighbors(
        self,
        rule_id: str,
        *,
        edge_kinds: Optional[Sequence[str]] = None,
        depth: int = 1,
    ) -> List[models.RuleEdge]:
        asset = self._find_asset(rule_id)
        if asset is None:
            return []
        known = self._index.known_ids()
        kinds = set(edge_kinds) if edge_kinds else None
        out: List[models.RuleEdge] = []
        for raw in graph_service.derive_edges(asset, set(known), from_id=rule_id):
            if kinds is not None and raw["edge_kind"] not in kinds:
                continue
            out.append(
                models.RuleEdge(
                    edge_id=raw["edge_id"],
                    from_id=raw["from_id"],
                    to_id=raw["to_id"],
                    edge_kind=raw["edge_kind"],
                    scope=raw["scope"] or None,
                    source=raw["source"],
                    status=raw["status"],
                )
            )
        return out

    def search_rules(self, query: str, *, limit: int = 200) -> List[models.RuleNode]:
        if not isinstance(query, str) or not query.strip():
            raise PublicResolutionError("搜索词不得为空。")
        needle = query.strip().casefold()
        hits = []
        for node in self._all_nodes():
            haystack = f"{node.title} {node.node_id} {node.summary or ''}".casefold()
            if needle in haystack:
                hits.append(node)
        return hits[:limit]

    def list_runtime_contract_types(self) -> List[Dict[str, str]]:
        """返回运行预览可选的已启用合同类型及中文名称。

        这是 taxonomy 的最小只读投影：界面不应要求律师记忆内部 type ID，也不应
        把尚未启用的类型放进可执行下拉框。类型是否启用仍以 manifest 为唯一真源。
        """
        active_ids = set(self._index.manifest.get("active_type_ids", ()))
        domain_names = {
            str(item.get("code")): str(item.get("name"))
            for item in self._index.taxonomy.get("domains", ())
            if item.get("code") and item.get("name")
        }
        choices: List[Dict[str, str]] = []
        for item in self._index.taxonomy.get("catalog_types", ()):
            type_id = item.get("type_id")
            if type_id not in active_ids:
                continue
            domain_code = str(item.get("domain_code") or "")
            choices.append({
                "type_id": str(type_id),
                "type_name": str(item.get("type_name") or type_id),
                "type_code": str(item.get("type_code") or ""),
                "domain_code": domain_code,
                "domain_name": domain_names.get(domain_code, domain_code),
            })
        choices.sort(key=lambda item: (item["domain_code"], item["type_code"], item["type_name"]))
        return choices

    def shadow_domain_metadata(self, domain_code: str) -> Optional[Dict[str, Any]]:
        """候选大类的安全影子元数据。不返回任何候选正文。"""
        card = None
        for asset in self._index.domain_principles:
            if asset.get("domain_code") == domain_code:
                card = asset
                break
        if card is None:
            return None
        coverage = card.get("coverage") or {}
        return {
            "domain_doctrine_id": card.get("domain_doctrine_id"),
            "domain_code": card.get("domain_code"),
            "coverage_status": coverage.get("coverage_status"),
            "supported_type_count": coverage.get("supported_type_count", 0),
            "total_type_count": coverage.get("total_type_count", 0),
            "source_count": len(card.get("source_ids", ())),
            "approval_status": card.get("approval_status"),
            "activation_status": card.get("activation_status"),
            "body_included": False,
        }

    # ------------------------------------------------------------------ #
    # 纯公共侧解析（RES-001~RES-010）
    # ------------------------------------------------------------------ #
    def resolve_public_rules(
        self,
        *,
        primary_type_id: str,
        secondary_type_ids: Sequence[str] = (),
        our_role: str,
        scene_tags: Sequence[str],
        classification_status: str = "high",
        confirmed_domain_code: str = "",
    ) -> models.EffectiveRuleSet:
        """纯公共输入 → 生效规则集合。

        不涉及客户 overlay；`client_profile_id` 恒为 None。
        """
        self._validate_inputs(
            primary_type_id=primary_type_id,
            secondary_type_ids=secondary_type_ids,
            our_role=our_role,
            scene_tags=scene_tags,
            confirmed_domain_code=confirmed_domain_code,
        )

        type_ids = {primary_type_id, *secondary_type_ids}
        scenes = set(scene_tags)
        primary_domain_code = self._index.type_to_domain[primary_type_id]

        effective: List[models.EffectiveRule] = []
        excluded: List[Dict[str, Any]] = []

        # 全局层：三份政策文档始终适用
        for relative_path in fingerprint.GLOBAL_DOCUMENT_PATHS:
            effective.append(
                models.EffectiveRule(
                    rule_id=relative_path,
                    version="n/a",
                    source_layer="global",
                    source_snapshot=self.public_snapshot_id,
                    matched_scope={"scope": "global"},
                    inclusion_reason="全局政策文档始终适用",
                    normative_class="global_soft_rule",
                    content_hash=self._fingerprint.projection_hash,
                    payload_schema_id="one-contract/rule-graph-v1.schema.json",
                    rule_payload={"relative_path": relative_path},
                )
            )

        # 大类层：主大类卡已激活且非 gap 时进入执行集合。
        # 当前生产数据第二层 active 为 0，此分支仅在激活夹具下触发（RES-003 / RES-004）。
        domain_card = None
        for asset in self._index.domain_principles:
            if asset.get("domain_code") == primary_domain_code:
                domain_card = asset
                break
        if domain_card is not None:
            coverage_status = (domain_card.get("coverage") or {}).get("coverage_status")
            if (
                domain_card.get("approval_status") == "active"
                and domain_card.get("activation_status") == "active"
                and coverage_status != "gap"
            ):
                effective.append(
                    self._domain_effective_rule(domain_card, primary_domain_code)
                )
            elif coverage_status == "gap":
                excluded.append({
                    "rule_id": str(domain_card.get("domain_code")),
                    "reason": f"coverage gap: 大类 {primary_domain_code} 覆盖为 gap，其原则卡不执行",
                })

        # 类型层：仅在分类已确认时加载专项正文。
        # 执行范围限定在**已确认主类型**；辅类型资产作为元数据记录但不执行（RES-010）。
        confirmation_required = classification_status in ("medium", "low") or not confirmed_domain_code
        if not confirmation_required:
            primary_only = {primary_type_id}
            for asset_kind, attribute in (
                ("type_principle", "type_principles"),
                ("clause_module", "modules"),
            ):
                for asset in getattr(self._index, attribute):
                    rule_id = self._stable_id_of(asset)
                    asset_types = set(asset.get("type_ids", [asset.get("type_id")])) - {None}

                    if not asset_types.intersection(primary_only):
                        if asset_types.intersection(type_ids):
                            # 命中辅类型：记为元数据，不进入执行集合
                            excluded.append({
                                "rule_id": rule_id,
                                "reason": "secondary_type_metadata_only: 命中辅类型，仅作元数据提示，不执行",
                                "matched_secondary_type_ids": sorted(
                                    asset_types.intersection(type_ids)
                                ),
                            })
                        continue

                    eligibility = self._check_eligibility(
                        asset, type_ids=primary_only, our_role=our_role, scenes=scenes
                    )
                    if eligibility.applicable:
                        effective.append(self._effective_rule(asset, asset_kind, primary_type_id))
                    elif eligibility.reason:
                        excluded.append({"rule_id": rule_id, "reason": eligibility.reason})

        coverage_level, coverage_notice = self._coverage(
            primary_type_id=primary_type_id,
            secondary_type_ids=secondary_type_ids,
            our_role=our_role,
            scene_tags=scene_tags,
            classification_status=classification_status,
            confirmed_domain_code=confirmed_domain_code,
            has_domain_rule=any(r.source_layer == "domain" for r in effective),
            has_type_rules=any(r.source_layer == "type" for r in effective),
            confirmation_required=confirmation_required,
        )

        result = models.EffectiveRuleSet(
            schema_version="1.0",
            public_snapshot_id=self.public_snapshot_id,
            context_hash=models.content_hash(
                {
                    "primary_type_id": primary_type_id,
                    "secondary_type_ids": list(secondary_type_ids),
                    "our_role": our_role,
                    "scene_tags": list(scene_tags),
                    "classification_status": classification_status,
                    "confirmed_domain_code": confirmed_domain_code,
                }
            ),
            effective_rules=effective,
            excluded_rules=excluded,
            coverage_level=coverage_level,
            coverage_notice=coverage_notice,
            human_confirmation_required=confirmation_required,
        )
        return result.with_hash()

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #
    def _is_fixture_root(self) -> bool:
        """是否在使用注入的夹具资产根（非生产根）。"""
        try:
            return self._skill_root.resolve() != paths.skill_root().resolve()
        except OSError:
            return True

    def _validate_inputs(
        self,
        *,
        primary_type_id: str,
        secondary_type_ids: Sequence[str],
        our_role: str,
        scene_tags: Sequence[str],
        confirmed_domain_code: str,
    ) -> None:
        known_types = self._index.type_to_domain
        for type_id in (primary_type_id, *secondary_type_ids):
            if type_id not in known_types:
                raise PublicResolutionError(
                    f"未知类型 {type_id!r}：不在 taxonomy_v2 的 catalog_types/domain_fallbacks 中。"
                )

        if not our_role or our_role not in self._index.valid_roles:
            raise PublicResolutionError(
                f"未知角色 {our_role!r}：角色词表封闭，未知值必须明确失败而非静默返回空集合。"
            )

        unknown_scenes = [s for s in scene_tags if s not in self._index.valid_scene_tags]
        if unknown_scenes:
            raise PublicResolutionError(
                f"未知场景 {unknown_scenes}：场景词表封闭，未知值必须明确失败。"
            )

        expected_domain = known_types[primary_type_id]
        if confirmed_domain_code and confirmed_domain_code != expected_domain:
            raise PublicResolutionError(
                f"已确认大类 {confirmed_domain_code!r} 与 taxonomy 中 {primary_type_id!r} 的"
                f"归属 {expected_domain!r} 冲突；不强制执行错误大类。"
            )

    def _check_eligibility(
        self,
        asset: Mapping[str, Any],
        *,
        type_ids: Set[str],
        our_role: str,
        scenes: Set[str],
    ) -> _Eligibility:
        if self._legacy.applicable(asset, set(type_ids), our_role, set(scenes)):
            return _Eligibility(True)

        # 复用同一 active 判定后，逐条给出可解释的排除原因
        if asset.get("approval_status") != "active" or asset.get("activation_status") != "active":
            return _Eligibility(False, None)  # 非 active 不属"被排除"，属不可用
        asset_types = set(asset.get("type_ids", [asset.get("type_id")])) - {None}
        if not asset_types.intersection(type_ids):
            return _Eligibility(False, "type mismatch: 资产作用类型与控制台主辅类型无交集")
        roles = set(asset.get("roles") or ())
        if roles and our_role not in roles and "any" not in roles:
            return _Eligibility(False, f"role mismatch: 资产限定角色 {sorted(roles)}，本轮为 {our_role!r}")
        required_scenes = set(asset.get("scene_tags") or ())
        if required_scenes and not required_scenes.intersection(scenes):
            return _Eligibility(
                False, f"scene mismatch: 资产限定场景 {sorted(required_scenes)}，本轮场景无交集"
            )
        return _Eligibility(False, None)

    def _effective_rule(
        self, asset: Mapping[str, Any], asset_kind: str, primary_type_id: str
    ) -> models.EffectiveRule:
        rule_id = self._stable_id_of(asset)
        payload = {
            key: value
            for key, value in asset.items()
            if key
            in (
                "type_id", "type_ids", "roles", "scene_tags", "review_objective",
                "clause_group", "requiredness", "failure_mode", "review_checks",
                "name", "title", "trigger_id", "module_id", "doctrine_id",
                "content_status",
            )
        }
        payload["primary_type_id"] = primary_type_id
        payload["asset_kind"] = asset_kind
        return models.EffectiveRule(
            rule_id=rule_id,
            version=str(asset.get("version") or "n/a"),
            source_layer="type",
            source_snapshot=self.public_snapshot_id,
            matched_scope={
                "type_ids": sorted(
                    set(asset.get("type_ids", [asset.get("type_id")])) - {None}
                ),
                "primary_type_id": primary_type_id,
            },
            inclusion_reason="命中 active 类型资产且角色/场景作用域匹配",
            normative_class="type_rule",
            content_hash=models.content_hash(payload, exclude=()),
            payload_schema_id="one-contract/rule-graph-v1.schema.json",
            rule_payload=payload,
        )

    def _domain_effective_rule(
        self, card: Mapping[str, Any], primary_domain_code: str
    ) -> models.EffectiveRule:
        """大类原则卡进入执行集合时的生效规则。"""
        coverage = (card.get("coverage") or {}).get("coverage_status")
        payload = {
            "domain_code": primary_domain_code,
            "domain_name": card.get("domain_name"),
            "coverage_status": coverage,
            "review_sequence": card.get("review_sequence"),
            "review_objectives": card.get("review_objectives"),
            "hard_boundaries": card.get("hard_boundaries"),
            "judgment_coordinates": card.get("judgment_coordinates"),
            "default_tendencies": card.get("default_tendencies"),
            "override_factors": card.get("override_factors"),
        }
        return models.EffectiveRule(
            rule_id=str(card.get("domain_code") or card.get("domain_doctrine_id")),
            version=str(card.get("version") or "n/a"),
            source_layer="domain",
            source_snapshot=self.public_snapshot_id,
            matched_scope={"domain_codes": [primary_domain_code]},
            inclusion_reason="主大类原则卡已激活且覆盖非 gap",
            normative_class="domain_rule",
            content_hash=models.content_hash(payload, exclude=()),
            payload_schema_id="one-contract/rule-graph-v1.schema.json",
            rule_payload=payload,
        )

    def _coverage(
        self,
        *,
        primary_type_id: str,
        secondary_type_ids: Sequence[str],
        our_role: str,
        scene_tags: Sequence[str],
        classification_status: str,
        confirmed_domain_code: str,
        has_domain_rule: bool,
        has_type_rules: bool,
        confirmation_required: bool,
    ) -> Tuple[str, str]:
        """覆盖等级与说明。

        **默认与 2.8.1 选择器逐字一致**（`_COVERAGE_SEMANTIC_MODE = False`）。
        理由：INT-008 是 R0 发布阻断项，要求「未选择客户的完整审查：规则集合、
        顺序及关键 notice 与 2.8.1 基线等价」。任何标签差异都会挡住发布门。

        已知 legacy 的不精确之处（不改变本次决定，仅记录以便后续版本修订）：
        其 coverage 只由**输入**决定，不看实际过滤结果。例如「低置信且大类未
        确认」时即便专项资产全部被排除，仍会返回「已命中active具体类型资产」。
        语义上更准确的取值是 `type_only` / `global_only`（见下方语义分支），
        该改进留待 2.9.x 独立评审。

        **注入自定义 skill_root 时（夹具场景）强制走语义分支**：既有选择器只读
        它自己解析出的生产资产根，无法感知注入的夹具根。此时若透传 legacy，
        会得到与夹具内容不符的结论（夹具激活了大类，legacy 仍报未激活）。
        生产路径（skill_root 为默认值）始终走透传，以满足 INT-008。
        """
        use_semantic = _COVERAGE_SEMANTIC_MODE or self._is_fixture_root()
        if use_semantic:
            if has_domain_rule and has_type_rules:
                return "domain_and_type", "已同时加载 active 大类原则卡和 active 具体类型资产。"
            if has_domain_rule:
                return "domain_only", "已加载 active 大类原则卡；未命中成熟具体类型资产。"
            if has_type_rules:
                return "type_only", "已命中 active 具体类型资产；第二层大类卡尚未激活。"
            if confirmation_required:
                return "global_only", "分类置信度不足或大类未确认；不加载专项正文，已要求人工确认。"
            return "global_only", "暂无成熟专项资产，继续使用全局规则。"

        legacy = self._legacy.select_assets(
            primary_type_id=primary_type_id,
            secondary_type_ids=list(secondary_type_ids),
            our_role=our_role,
            scene_tags=list(scene_tags),
            classification_status=classification_status,
            confirmed_domain_code=confirmed_domain_code,
        )
        return legacy["coverage_level"], legacy["coverage_notice"]

    def check_eligibility_for_test(
        self,
        asset: Mapping[str, Any],
        *,
        type_ids: Set[str],
        our_role: str,
        scenes: Set[str],
    ) -> _EligibilityPublic:
        """供测试直接验证过滤函数。生产路径请使用 `resolve_public_rules`。"""
        verdict = self._check_eligibility(
            asset, type_ids=set(type_ids), our_role=our_role, scenes=set(scenes)
        )
        return _EligibilityPublic(verdict.applicable, verdict.reason)

    def _stable_id_of(self, asset: Mapping[str, Any]) -> str:
        for key in (
            "domain_doctrine_id", "doctrine_id", "module_id", "module_group_id",
            "trigger_id", "source_id", "experience_id", "template_id",
        ):
            if asset.get(key):
                return str(asset[key])
        return "unknown"

    def _find_asset(self, rule_id: str) -> Optional[Mapping[str, Any]]:
        # Rule Studio 的类型原则节点使用 doctrine_id::type_id 唯一定位；
        # 原始目录仍保留可复用 doctrine_id，不修改运行时规则身份。
        for asset_kind, attribute in _COLLECTIONS:
            for asset in getattr(self._index, attribute):
                if projection.asset_node_id(asset, asset_kind=asset_kind) == rule_id:
                    return asset
        found = self._index.lookup(rule_id)
        if found is not None:
            return found
        return None

    def _build_asset_table(self) -> Dict[str, List[Mapping[str, Any]]]:
        table: Dict[str, List[Mapping[str, Any]]] = {}
        for asset_kind, attribute in _COLLECTIONS:
            table[asset_kind] = list(getattr(self._index, attribute))
        return table

    def _all_nodes(self) -> Tuple[models.RuleNode, ...]:
        if self._nodes_cache is not None:
            return self._nodes_cache

        nodes: List[models.RuleNode] = []

        for relative_path, title in GLOBAL_DOCUMENT_TITLES.items():
            nodes.append(
                projection.project_global_document_node(
                    relative_path=relative_path, title=title
                )
            )
        for asset in self._index.domain_principles:
            nodes.append(projection.project_domain_node(asset))
        for asset_kind, attribute in _COLLECTIONS:
            if asset_kind == "domain_principle":
                continue
            for asset in getattr(self._index, attribute):
                nodes.append(projection.project_type_node(asset, asset_kind=asset_kind))

        self._nodes_cache = tuple(nodes)
        return self._nodes_cache
