#!/usr/bin/env python3
"""Rules Core 的 DTO 与规范化工具。

契约来源：architecture-contract.md §5（RuleNode/RuleEdge）、§6（EffectiveRuleSet）、
§7.1（Resolution Context 与 fact 语义）、§8.5（哈希规范）。

本模块**只做结构表达与规范化**，不做业务判断：
- 不读盘、不联网、不依赖工作目录；
- 跨引用、状态机与硬边界由业务 validator 负责（§16 末段）；
- operator 语义的真值表由 W3B 的 resolver 消费，此处只冻结 op 名与合法性。

哈希采用 RFC 8785/JCS 口径的规范化，见 canonical_json 与 content_hash。
"""
from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "CANONICALIZATION",
    "CLIENT_NORMATIVE_LEVEL_TO_CLASS",
    "FACT_KEY_PATTERN",
    "NORMATIVE_CLASSES",
    "OPERATORS",
    "RULE_NODE_KINDS",
    "BODY_VISIBILITIES",
    "EDGE_KINDS",
    "SOURCE_LAYERS",
    "ModelContractError",
    "normative_class_for_client_level",
    "EffectiveRule",
    "EffectiveRuleSet",
    "ResolutionTraceItem",
    "RuleEdge",
    "RuleNode",
    "canonical_json",
    "content_hash",
    "normalize_operator",
    "validate_condition_semantics",
]

CANONICALIZATION = "RFC8785/JCS"

#: body_visibility 枚举（architecture-contract.md §5）
BODY_VISIBILITIES: Tuple[str, ...] = (
    "full_active",
    "metadata_only_candidate",
    "document_node",
    "private_client",
    "unavailable",
)

#: edge_kind 枚举（architecture-contract.md §5）
EDGE_KINDS: Tuple[str, ...] = (
    "contains",
    "inherits",
    "deepens",
    "depends_on",
    "conflicts_with",
    "shared_by",
    "sourced_from",
    "client_overlays",
)

#: 解析优先级性质分类（§7.5）。
#: 取值来自 effective-rule-set / rule-vocabulary 的 normativeClass 枚举，
#: schema 是唯一机器真源；此处仅为 Python 侧一致性常量。
NORMATIVE_CLASSES: Tuple[str, ...] = (
    "global_hard_boundary",
    "case_authorized_exception",
    "client_mandatory",
    "client_preferred",
    "client_advisory",
    "type_rule",
    "domain_rule",
    "global_soft_rule",
)

#: 来源层（§6 / §7.5）。
#: 注意 case_instruction 独立于 client：本案授权指令不是客户长期政策。
SOURCE_LAYERS: Tuple[str, ...] = (
    "global",
    "domain",
    "type",
    "client",
    "case_instruction",
)

#: client-rule.normative_level（三值）到 NORMATIVE_CLASSES 的确定性映射。
#: 客户规则自身只声明 mandatory/preferred/advisory，全限定类名由此派生。
CLIENT_NORMATIVE_LEVEL_TO_CLASS: Dict[str, str] = {
    "mandatory": "client_mandatory",
    "preferred": "client_preferred",
    "advisory": "client_advisory",
}

#: 节点种类
RULE_NODE_KINDS: Tuple[str, ...] = (
    "global_document",
    "domain_principle",
    "type_principle",
    "clause_module",
    "module_group",
    "trigger",
    "experience_card",
    "knowledge_source",
    "template",
    "client_rule",
)

#: 条件操作符真值表（§7.1）。语义由 W3B 实现，此处冻结名称集合。
OPERATORS: Tuple[str, ...] = (
    "equals",
    "not_equals",
    "in",
    "not_in",
    "exists",
    "contains",
    "gte",
    "lte",
)

#: fact key 命名：小写字母数字与下划线/点号分段。
FACT_KEY_PATTERN = r"^[a-z][a-z0-9_]*(?:[.][a-z][a-z0-9_]*)*$"


class ModelContractError(Exception):
    """DTO 违反结构契约。调用方不得降级为跳过。"""


# --------------------------------------------------------------------------- #
# 规范化与哈希
# --------------------------------------------------------------------------- #

def _normalize_strings(value: Any) -> Any:
    """进入模型前把字符串统一为 Unicode NFC（§8.5）。"""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize_strings(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_strings(v) for k, v in value.items()}
    return value


def _reject_non_finite(value: Any, path: str = "$") -> None:
    """拒绝 NaN、Infinity 与无法按 JCS 表达的数值（§8.5）。"""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ModelContractError(
                f"{path} 含 NaN/Infinity；JCS 无法表达，契约拒绝该值。"
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_non_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_non_finite(item, f"{path}[{index}]")


def _utf16_key(text: str) -> bytes:
    """RFC 8785 要求成员名按 UTF-16 码元序排序，不是按 Unicode 码点排序。

    两者在补充平面（emoji、部分生僻汉字）上会分叉：
    U+1F600 的 UTF-16 代理对以 D83D 开头，排在 U+FFFD 之前，
    但按码点比较则 U+FFFD < U+1F600。用大端编码即可得到码元序。
    """
    return text.encode("utf-16-be")


_ESCAPES = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\f": "\\f",
            "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _serialize_string(text: str) -> str:
    """字符串序列化：与 ECMAScript JSON.stringify 一致。

    仅 < U+0020 的控制字符需要转义；U+2028/U+2029 与 U+007F 保持原样，
    非 ASCII 字符不转义。已实测 Python json.dumps 在这些点上与 ES 一致，
    此处显式实现以确保行为不随 Python 版本漂移。
    """
    out = ['"']
    for char in text:
        escape = _ESCAPES.get(char)
        if escape is not None:
            out.append(escape)
        elif ord(char) < 0x20:
            out.append("\\u%04x" % ord(char))
        else:
            out.append(char)
    out.append('"')
    return "".join(out)


def _serialize_number(value: int | float) -> str:
    """数字序列化：采用 ECMAScript Number::toString 口径（RFC 8785 §3.2.2.3）。

    关键差异（Python 默认 json.dumps 不符合）：
    - 整数值的浮点数不带小数点：1.0 → 1，100.0 → 100；
    - -0.0 序列化为 0；
    - 指数记法不补零：1e-07 → 1e-7。

    非有限值在进入本函数前已由 _reject_non_finite 拒绝。
    """
    if isinstance(value, bool):  # bool 是 int 子类，绝不能走数值分支
        raise ModelContractError("布尔值不得作为数值序列化。")
    if isinstance(value, int):
        return str(value)
    if value == 0.0:
        return "0"  # 覆盖 -0.0
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    text = repr(value)
    # Python 指数记法补零（1e-07），ES 不补零（1e-7）
    if "e" in text or "E" in text:
        mantissa, _, exponent = text.partition("e" if "e" in text else "E")
        sign = ""
        if exponent.startswith(("+", "-")):
            sign, exponent = exponent[0], exponent[1:]
        text = f"{mantissa}e{sign}{int(exponent)}"
    return text


def _serialize(node: Any) -> str:
    if node is None:
        return "null"
    if node is True:
        return "true"
    if node is False:
        return "false"
    if isinstance(node, str):
        return _serialize_string(node)
    if isinstance(node, (int, float)):
        return _serialize_number(node)
    if isinstance(node, (list, tuple)):
        return "[" + ",".join(_serialize(item) for item in node) + "]"
    if isinstance(node, Mapping):
        parts = []
        for key in sorted(node.keys(), key=_utf16_key):
            if not isinstance(key, str):
                raise ModelContractError("JCS 要求成员名必须是字符串。")
            parts.append(_serialize_string(key) + ":" + _serialize(node[key]))
        return "{" + ",".join(parts) + "}"
    raise ModelContractError(f"类型 {type(node).__name__} 无法按 JCS 序列化。")


def canonical_json(payload: Mapping[str, Any], *, exclude: Sequence[str] = ()) -> str:
    """按 RFC 8785/JCS 口径产出规范化 JSON 文本。

    实现要点（均针对 Python 默认 json.dumps 的不合规之处修正）：
    - 成员名按 **UTF-16 码元序**排序，而非码点序（补充平面字符会分叉）；
    - 数字采用 ECMAScript Number::toString：1.0 → 1、-0.0 → 0、1e-07 → 1e-7；
    - 字符串转义与 ES 一致；
    - 先做 Unicode NFC 规范化，再拒绝 NaN/Infinity 与不可表达类型；
    - *exclude* 中的顶层字段在计算前剔除（用于排除自身哈希字段）。

    注意：RFC 8785 的完整数字口径覆盖 1e-7 至 1e21 的指数边界与超出
    IEEE-754 双精度整数的处理。本实现覆盖 Python/JS 两侧常见取值域，
    边界差异需在 golden vectors 中逐项核对（见 CON-007 未完事项）。
    """
    if not isinstance(payload, Mapping):
        raise ModelContractError("canonical_json 需要映射类型作为输入。")

    body = {k: v for k, v in payload.items() if k not in set(exclude)}
    normalized = _normalize_strings(body)
    _reject_non_finite(normalized)
    try:
        return _serialize(normalized)
    except (TypeError, ValueError) as exc:
        raise ModelContractError(f"输入无法按 JCS 规范化: {exc}") from exc


def content_hash(payload: Mapping[str, Any], *, exclude: Sequence[str] = ()) -> str:
    """返回 `sha256:<hex>` 形式的内容哈希。

    默认排除自身哈希字段，避免自引用（§8.5）。
    """
    default_exclude = ("content_sha256", "result_hash")
    merged = tuple(dict.fromkeys(tuple(default_exclude) + tuple(exclude)))
    digest = hashlib.sha256(canonical_json(payload, exclude=merged).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


# --------------------------------------------------------------------------- #
# 条件语义校验（结构层，不执行）
# --------------------------------------------------------------------------- #

def normative_class_for_client_level(level: str) -> str:
    """把 client-rule 的 normative_level 映射成全限定 normative_class。

    映射是确定性的（mandatory|preferred|advisory → client_*），
    不接受未登记的级别——避免客户端自造优先级。
    """
    try:
        return CLIENT_NORMATIVE_LEVEL_TO_CLASS[level]
    except KeyError:
        raise ModelContractError(
            f"未登记的客户规则优先级别: {level!r}；"
            f"可用: {', '.join(sorted(CLIENT_NORMATIVE_LEVEL_TO_CLASS))}。"
        ) from None


def normalize_operator(operator: str) -> str:
    if operator not in OPERATORS:
        raise ModelContractError(
            f"未注册的操作符: {operator!r}；可用: {', '.join(OPERATORS)}。"
        )
    return operator


def validate_condition_semantics(operator: str, fact_value: Any, rule_value: Any) -> None:
    """按 §7.1 做类型匹配检查。不做隐式转换，不执行脚本。

    类型不匹配抛出 ModelContractError——对应错误码 INVALID_CONDITION_TYPE。
    """
    normalize_operator(operator)

    if operator == "exists":
        # 只判断 fact key 是否存在，不携带 value
        return

    if operator in ("equals", "not_equals"):
        if type(fact_value) is not type(rule_value):  # noqa: E721 - 需精确类型
            raise ModelContractError(
                f"操作符 {operator} 要求同 JSON 类型精确比较，"
                f"实际为 {type(fact_value).__name__} 与 {type(rule_value).__name__}。"
            )
        return

    if operator in ("in", "not_in"):
        if not isinstance(rule_value, list):
            raise ModelContractError(f"操作符 {operator} 的规则值必须是数组。")
        if isinstance(fact_value, list):
            raise ModelContractError(f"操作符 {operator} 的被测事实必须是单值。")
        return

    if operator == "contains":
        if isinstance(fact_value, str) and isinstance(rule_value, str):
            return
        if isinstance(fact_value, list) and rule_value is not None:
            for item in fact_value:
                if type(item) is type(rule_value):  # noqa: E721
                    return
            raise ModelContractError(
                "contains 用于数组时，规则值必须与数组中至少一个元素同类型。"
            )
        raise ModelContractError(
            "contains 只允许字符串包含字符串，或数组包含同类型标量。"
        )

    if operator in ("gte", "lte"):
        for label, value in (("fact", fact_value), ("rule", rule_value)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ModelContractError(
                    f"操作符 {operator} 的 {label} 值必须是有限 JSON number，不接受字符串或布尔。"
                )
        _reject_non_finite(fact_value, "$.fact")
        _reject_non_finite(rule_value, "$.rule")
        return


# --------------------------------------------------------------------------- #
# DTO
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class RuleNode:
    """规则节点（architecture-contract.md §5）。字段与契约逐项对应。"""

    node_id: str
    node_kind: str
    layer: str
    title: str
    version: str
    approval_status: str
    activation_status: str
    body_visibility: str
    domain_codes: Tuple[str, ...] = ()
    type_ids: Tuple[str, ...] = ()
    roles: Tuple[str, ...] = ()
    scene_tags: Tuple[str, ...] = ()
    source_refs: Tuple[str, ...] = ()
    updated_at: Optional[str] = None
    summary: Optional[str] = None
    content_hash: Optional[str] = None

    def __post_init__(self) -> None:
        if self.node_kind not in RULE_NODE_KINDS:
            raise ModelContractError(f"未注册的 node_kind: {self.node_kind!r}")
        if self.body_visibility not in BODY_VISIBILITIES:
            raise ModelContractError(f"未注册的 body_visibility: {self.body_visibility!r}")
        if self.layer not in SOURCE_LAYERS:
            raise ModelContractError(f"未注册的 layer: {self.layer!r}")

    @property
    def is_runtime_eligible(self) -> bool:
        """只有审批与执行双轴同为 active 才可进入运行时。"""
        return self.approval_status == "active" and self.activation_status == "active"

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        for key in ("domain_codes", "type_ids", "roles", "scene_tags", "source_refs"):
            out[key] = list(out[key])
        return out

    def with_hash(self) -> "RuleNode":
        payload = self.to_dict()
        return RuleNode(**{**payload, "content_hash": content_hash(payload)})


@dataclass(frozen=True)
class RuleEdge:
    """关系边（architecture-contract.md §5）。"""

    edge_id: str
    from_id: str
    to_id: str
    edge_kind: str
    scope: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None

    def __post_init__(self) -> None:
        if self.edge_kind not in EDGE_KINDS:
            raise ModelContractError(f"未注册的 edge_kind: {self.edge_kind!r}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EffectiveRule:
    """一条生效规则及其来源载荷（architecture-contract.md §6）。

    契约要求每条 effective rule 携带**最小安全规则载荷**或固定快照内的
    content ref，不得只有 ID 而无法执行（CON-004）。
    """

    rule_id: str
    version: str
    source_layer: str
    source_snapshot: str
    matched_scope: Mapping[str, Any]
    inclusion_reason: str
    normative_class: str
    content_hash: str
    overridden_rule_ids: Tuple[str, ...] = ()
    dependencies: Tuple[str, ...] = ()
    payload_schema_id: Optional[str] = None
    rule_payload: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.source_layer not in SOURCE_LAYERS:
            raise ModelContractError(f"未注册的 source_layer: {self.source_layer!r}")
        if self.normative_class not in NORMATIVE_CLASSES:
            raise ModelContractError(
                f"未注册的 normative_class: {self.normative_class!r}"
            )
        if self.rule_payload is None and not self.payload_schema_id:
            raise ModelContractError(
                "生效规则必须携带 rule_payload，或指明可在固定快照内解析的 payload_schema_id。"
            )

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        out["overridden_rule_ids"] = list(self.overridden_rule_ids)
        out["dependencies"] = list(self.dependencies)
        return out


@dataclass(frozen=True)
class ResolutionTraceItem:
    """解析轨迹的一项，支持从固定输入重放（CON-005）。"""

    rule_id: str
    version: str
    source_layer: str
    source_snapshot: str
    matched_scope: Mapping[str, Any]
    decision: str
    content_hash: str
    overridden_rule_ids: Tuple[str, ...] = ()
    dependencies: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source_layer not in SOURCE_LAYERS:
            raise ModelContractError(f"未注册的 source_layer: {self.source_layer!r}")
        if self.decision not in ("included", "excluded"):
            raise ModelContractError(
                f"decision 必须是 included 或 excluded，实际为 {self.decision!r}"
            )

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        out["overridden_rule_ids"] = list(self.overridden_rule_ids)
        out["dependencies"] = list(self.dependencies)
        return out


@dataclass
class EffectiveRuleSet:
    """合成结果（architecture-contract.md §6 的最低输出结构）。"""

    schema_version: str
    public_snapshot_id: str
    context_hash: str
    client_profile_id: Optional[str] = None
    client_policy_snapshot_id: Optional[str] = None
    effective_rules: List[EffectiveRule] = field(default_factory=list)
    excluded_rules: List[Mapping[str, Any]] = field(default_factory=list)
    rule_conflicts: List[Mapping[str, Any]] = field(default_factory=list)
    coverage_level: str = "global_only"
    coverage_notice: str = ""
    resolution_trace: List[ResolutionTraceItem] = field(default_factory=list)
    human_confirmation_required: bool = False
    result_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "public_snapshot_id": self.public_snapshot_id,
            "client_profile_id": self.client_profile_id,
            "client_policy_snapshot_id": self.client_policy_snapshot_id,
            "context_hash": self.context_hash,
            "effective_rules": [r.to_dict() for r in self.effective_rules],
            "excluded_rules": [dict(x) for x in self.excluded_rules],
            "rule_conflicts": [dict(x) for x in self.rule_conflicts],
            "coverage_level": self.coverage_level,
            "coverage_notice": self.coverage_notice,
            "resolution_trace": [t.to_dict() for t in self.resolution_trace],
            "human_confirmation_required": self.human_confirmation_required,
            "result_hash": self.result_hash,
        }

    def with_hash(self) -> "EffectiveRuleSet":
        """写入 result_hash（排除自身字段后计算）。"""
        self.result_hash = content_hash(self.to_dict())
        return self

    @property
    def is_client_scoped(self) -> bool:
        """是否显式绑定了客户快照。用于 fail closed 判断（ADR-028）。"""
        return self.client_profile_id is not None and self.client_policy_snapshot_id is not None
