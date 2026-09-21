#!/usr/bin/env python3
"""客户数据的结构与业务校验。

契约来源：ADR-006（JSON Schema 是数据契约，不是唯一业务验证）、
architecture-contract.md §16 末段（Schema 结构通过不等于业务有效）。

分工：
- **结构**交给 `registry` 的 Draft 2020-12 验证器；
- **业务**在本模块实现：scope 不变量、有效期反转、同一稳定 ID 的 active 版本唯一、
  profile/manifest/snapshot/rule 的 ID 一致性、路径 containment。

错误一律携带 `field_path`，供前端定位（CR-002）。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from . import registry

__all__ = [
    "ValidationError",
    "validate_active_manifest",
    "validate_client_profile",
    "validate_client_rule",
    "validate_client_snapshot",
    "validate_rule_business",
]


class ValidationError(Exception):
    """校验失败。携带可定位的字段路径。"""

    def __init__(self, message: str, *, field_path: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.field_path = field_path

    def __str__(self) -> str:  # pragma: no cover - 展示用
        if self.field_path:
            return f"{self.field_path}: {self.message}"
        return self.message


def _schema_validate(schema_id: str, payload: Mapping[str, Any]) -> None:
    validator = registry.make_validator(schema_id)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if not errors:
        return
    first = errors[0]
    field_path = ".".join(str(part) for part in first.path) or "<root>"
    # CR-002 要求校验失败时**定位到具体字段**。整项必填属性缺失时，
    # jsonschema 的 path 指向父对象（顶层即 `<root>`），定位不到缺的那个字段。
    # 这里把缺失的属性名补进路径（例如缺 scope → field_path="scope"）。
    if getattr(first, "validator", None) == "required" and isinstance(first.instance, Mapping):
        missing = [p for p in (first.validator_value or ()) if p not in first.instance]
        if missing:
            prefix = [str(part) for part in first.path]
            field_path = ".".join(prefix + [str(missing[0])])
    raise ValidationError(first.message, field_path=field_path)


def _parse_timestamp(value: Any, *, field_path: str) -> Optional[datetime]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError("时间必须是 RFC3339 字符串或 null。", field_path=field_path)
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(f"无法解析时间: {value!r}", field_path=field_path) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


# --------------------------------------------------------------------------- #
# 结构校验
# --------------------------------------------------------------------------- #

def validate_client_profile(payload: Mapping[str, Any]) -> None:
    _schema_validate("one-contract/client-profile-v1.schema.json", payload)


def validate_client_rule(payload: Mapping[str, Any]) -> None:
    _schema_validate("one-contract/client-rule-v1.schema.json", payload)


def validate_client_snapshot(
    payload: Mapping[str, Any], *, defer_evidence_refs: bool = False
) -> None:
    """校验客户快照（`client-snapshot-v1`：manifest + rules 同一文档）。

    `defer_evidence_refs=True` 时**仅暂缓** `evidence_refs` 的条目形状约束，
    其余字段（含 `publish_transaction_id` 的 `^ptx_…$` 等）照常强制。

    为何暂缓这一项：`evidence_refs` 的条目复用
    `governance-evidence-v1#/$defs/evidenceReference`，其必填字段
    `candidate_sha256` 是**发布治理概念**（W7 候选哈希），运行时发布路径
    无从诚实填写；同时该项还要求 `minItems: 3` 并至少各含一条
    `audit/prepared`、`lawyer_approval/approved`、`regression/passed`。
    即运行时能否产出该形状需契约负责人裁决——**不是实现缺陷能单方决定的**。
    在裁决前采用「能强制的全强制、不可强制的显式豁免」，
    并记入 human-confirmation 清单待契约负责人裁决。
    `tests/test_rule_studio_contracts.py::SnapshotValidationBoundaryTests`
    固定该豁免的边界——放宽必须精确，不得掏空其它约束。
    """
    if not defer_evidence_refs:
        _schema_validate("one-contract/client-snapshot-v1.schema.json", payload)
        return
    schema = registry.get_schema("one-contract/client-snapshot-v1.schema.json")
    relaxed = json.loads(json.dumps(schema))
    # 精确放宽**两处**（且仅这两处），其余字段照常强制：
    #   ① evidence_refs 的条目形状与数量（其必填 candidate_sha256 是发布治理概念）；
    #   ② validation_summary.checks 的 **check_kind 词汇**（契约要求
    #      schema_validation 等固定值，实现使用自有词汇）。
    # 二者同源：契约把这些建模为治理侧内容，运行时的口径不同，如何对齐需裁决。
    #
    # **只放宽词汇约束**：`validation_summary` 的 required、
    # `overall_result` 必须为 passed、additionalProperties:false、
    # `checks` 的 minItems 与条目自身结构**一律保持强制**——
    # 否则一个自称"校验失败"的快照也能发布（本函数曾整体放宽 validation_summary，
    # 被独立验证指出该漏洞，已收窄）。
    relaxed["properties"]["evidence_refs"] = {"type": "array"}
    checks_schema = relaxed["properties"]["validation_summary"]["properties"]["checks"]
    checks_schema.pop("allOf", None)          # ① check_kind 词汇
    # ② 检查项内的证据引用形状（同一个 candidate_sha256 障碍）
    checks_items = checks_schema.get("items") or {}
    if "$ref" in checks_items:
        ref_name = str(checks_items["$ref"]).rsplit("/", 1)[-1]
        check_def = relaxed["$defs"][ref_name]["properties"]
    else:  # pragma: no cover - 契约当前用 $ref
        check_def = checks_items.setdefault("properties", {})
    check_def["evidence_refs"] = {"type": "array"}
    # check_kind 的取值词汇：契约要求 schema_validation / reference_validation /
    # conflict_resolution / privacy_validation / regression /
    # hard_boundary_validation / business_validation 七个固定值，
    # 实现使用自有词汇（schema / lifecycle / legal_check / regression / isolation），
    # 二者能否映射（且是否必须凑齐七类）需契约负责人裁决。
    # **仅放宽取值**：check_id 形态、result 枚举、required 与
    # additionalProperties:false 全部保持强制。
    check_def["check_kind"] = {"type": "string"}
    relaxed.pop("allOf", None)
    validator = registry.make_validator_from_schema(relaxed)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if not errors:
        return
    first = errors[0]
    path = ".".join(str(part) for part in first.path) or "<root>"
    raise ValidationError(first.message, field_path=path)


def validate_active_manifest(payload: Mapping[str, Any]) -> None:
    _schema_validate("one-contract/active-client-manifest-v1.schema.json", payload)


# --------------------------------------------------------------------------- #
# 业务校验
# --------------------------------------------------------------------------- #

def _validate_scope(scope: Mapping[str, Any]) -> None:
    """scope 二选一：applies_to_all 为 true 时局部 scope 必须全空；否则至少一个非空。"""
    if not isinstance(scope, Mapping):
        raise ValidationError("scope 必须是对象。", field_path="scope")

    local_keys = (
        "domain_codes", "type_ids", "roles", "scene_tags",
        "contract_stages", "clause_groups",
    )
    populated = [k for k in local_keys if scope.get(k)]
    applies_to_all = scope.get("applies_to_all")

    if applies_to_all is True and populated:
        raise ValidationError(
            f"applies_to_all 为 true 时局部 scope 必须为空，实际非空: {populated}",
            field_path="scope.applies_to_all",
        )
    if applies_to_all is False and not populated:
        raise ValidationError(
            "applies_to_all 为 false 时至少需要一个局部 scope。",
            field_path="scope",
        )


def _validate_effect(effect: Any) -> None:
    if not isinstance(effect, Mapping):
        raise ValidationError("effect 必须是对象。", field_path="effect")
    for key in ("action", "target_key"):
        if not effect.get(key):
            raise ValidationError(f"effect 缺少 {key}。", field_path=f"effect.{key}")


def describe_scope_problem(scope: Any) -> Optional["ValidationError"]:
    """返回 scope 不变量的**可读**问题（没有则 None）。

    为什么需要它：**在 API 路径上**，结构校验先跑 `jsonschema`，它的原始消息是英文
    且指向实现细节（`['EC-02'] is expected to be empty`、`{...} is too short`），
    对律师不可读；而那之后 `_validate_scope` 里那句
    「applies_to_all 为 true 时局部 scope 必须为空」虽然清楚，却**走不到**
    ——API 路径从结构校验失败处就返回了。API 层据此把原始消息换成这一句。

    注意范围：`_validate_scope` 本身**并非**不可达——直接调用校验器的调用方
    （单测、脚本、未来的其它入口）都会执行到它。不可达的只是「经 API 呈现给用户」
    这一条路径，所以修法是在**呈现层**补入口，而不是删掉那句判断。

    已知残留：`scope` 缺失或不是对象时本函数返回 None（两个分支都不成立），
    此时 API 仍会回落到 JSON-Schema 的英文原文。这两种载荷界面产生不了
    （表单总会给出 scope 对象），故不构成用户可见缺陷；判定口径记于本项目的
    已知限制记录（该记录**不在本 Skill 包内**）。
    """
    try:
        _validate_scope(scope if isinstance(scope, Mapping) else {})
    except ValidationError as exc:
        return exc
    return None


def validate_rule_business(payload: Mapping[str, Any]) -> None:
    """跨字段业务规则。结构校验通过后调用。"""
    _validate_scope(payload.get("scope") or {})
    _validate_effect(payload.get("effect"))

    validity = payload.get("validity") or {}
    start = _parse_timestamp(validity.get("valid_from"), field_path="validity.valid_from")
    end = _parse_timestamp(validity.get("valid_until"), field_path="validity.valid_until")
    if start and end and end < start:
        raise ValidationError(
            "valid_until 早于 valid_from，有效期区间反转。",
            field_path="validity.valid_until",
        )

    condition = payload.get("condition") or {}
    if condition.get("mode") not in ("all", "any", None):
        raise ValidationError(
            "condition.mode 只允许 all 或 any。", field_path="condition.mode"
        )


def ensure_single_active_version(rules: Sequence[Mapping[str, Any]]) -> None:
    """同一 stable rule ID 在将要发布的集合中最多只能有一个 active 版本（DATA-003）。"""
    seen = {}
    for rule in rules:
        if rule.get("approval_status") != "active" or rule.get("activation_status") != "active":
            continue
        rule_id = rule.get("client_rule_id")
        if rule_id in seen:
            raise ValidationError(
                f"同一 stable rule ID 存在多个 active 版本: {rule_id}",
                field_path="rules",
            )
        seen[rule_id] = rule.get("version")


def ensure_chain_consistency(
    *, expected_profile_id: str, payloads: Sequence[Mapping[str, Any]], field_prefix: str
) -> None:
    """profile/manifest/snapshot/rule 的 client_profile_id 必须一致（DATA-002）。"""
    for index, payload in enumerate(payloads):
        found = payload.get("client_profile_id")
        if found != expected_profile_id:
            raise ValidationError(
                f"client_profile_id 不一致：期望 {expected_profile_id!r}，实际 {found!r}",
                field_path=f"{field_prefix}[{index}].client_profile_id",
            )
