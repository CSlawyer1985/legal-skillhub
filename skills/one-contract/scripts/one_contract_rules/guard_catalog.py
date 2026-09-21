#!/usr/bin/env python3
"""只读 guard catalog 与确定性硬边界判定。

契约来源：ADR-020（硬边界只做确定性 guard，不声称自动理解任意自然语言）、
architecture-contract.md §7.5（冲突分类与机器可判范围）、
RS-HC-007（冲突不得静默择一）。

边界声明（必须显式）：
- 本模块**只**处理受控 fact key、operator、effect target 与显式关系；
- 无法确定的法律语义一律返回 `human_confirmation_required`，
  不猜测、不静默择一、不折中；
- guard 定义来自公共 `rule-vocabulary`，本模块不新造边界。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from . import models

__all__ = [
    "DependencyVerdict",
    "GuardCatalog",
    "GuardVerdict",
    "build_guard_catalog",
    "check_dependencies",
    "detect_conflicts",
    "evaluate_hard_guards",
    "is_rule_executable",
]


@dataclass(frozen=True)
class GuardVerdict:
    blocked: bool = False
    human_confirmation_required: bool = False
    conflicts: Tuple[Mapping[str, Any], ...] = ()
    blocked_rule_ids: Tuple[str, ...] = ()
    unknown_targets: Tuple[str, ...] = ()

    def merged(self, other: "GuardVerdict") -> "GuardVerdict":
        return GuardVerdict(
            blocked=self.blocked or other.blocked,
            human_confirmation_required=(
                self.human_confirmation_required or other.human_confirmation_required
            ),
            conflicts=self.conflicts + other.conflicts,
            blocked_rule_ids=tuple(dict.fromkeys(self.blocked_rule_ids + other.blocked_rule_ids)),
            unknown_targets=tuple(dict.fromkeys(self.unknown_targets + other.unknown_targets)),
        )


@dataclass(frozen=True)
class DependencyVerdict:
    satisfied: bool
    missing: Tuple[str, ...] = ()


@dataclass(frozen=True)
class GuardCatalog:
    """公共 guard 与受控 target 的只读快照。"""

    guards: Tuple[Mapping[str, Any], ...] = ()
    effect_targets: Tuple[Mapping[str, Any], ...] = ()
    fact_keys: Tuple[Mapping[str, Any], ...] = ()
    operators: Tuple[Mapping[str, Any], ...] = ()
    # guard 的业务适用范围从其 boundary_rule_id 指向的公共规则读取。
    # 它不属于 rule-vocabulary 的语义正文，避免为了展示层修复而复制或改写公共资产。
    guard_scopes: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    @property
    def known_target_keys(self) -> Set[str]:
        return {t.get("target_key") for t in self.effect_targets if t.get("target_key")}

    @property
    def known_fact_keys(self) -> Set[str]:
        return {f.get("fact_key") for f in self.fact_keys if f.get("fact_key")}


def build_guard_catalog(
    public_repository: Any, *, vocabulary: Optional[Mapping[str, Any]] = None
) -> GuardCatalog:
    """构造 guard catalog。

    默认使用本模块内的 `_DEFAULT_GUARDS`（结构受 `rule-vocabulary-v1` 约束）。
    *vocabulary* 可注入替代词汇，供测试夹具使用。

    **不静默降级为空 catalog**——那会让所有硬边界失效，属于最危险的失败模式。
    """
    from . import registry

    # 结构自检：词汇表必须仍符合冻结契约，否则硬边界判定不可信
    try:
        validator = registry.make_validator("one-contract/rule-vocabulary-v1.schema.json")
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"无法加载 rule-vocabulary 契约，硬边界判定不可用: {exc}") from exc

    def scopes_for(guards: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
        scopes: Dict[str, Mapping[str, Any]] = {}
        getter = getattr(public_repository, "get_rule", None)
        if not callable(getter):
            return scopes
        for guard in guards:
            guard_id = guard.get("guard_id")
            boundary_id = guard.get("boundary_rule_id")
            node = getter(boundary_id) if boundary_id else None
            if not guard_id or node is None:
                continue
            scopes[str(guard_id)] = {
                "domain_codes": tuple(getattr(node, "domain_codes", ()) or ()),
                "type_ids": tuple(getattr(node, "type_ids", ()) or ()),
                "roles": tuple(getattr(node, "roles", ()) or ()),
                "scene_tags": tuple(getattr(node, "scene_tags", ()) or ()),
            }
        return scopes

    if vocabulary is not None:
        payload = dict(vocabulary)
        errors = list(validator.iter_errors(payload))
        if errors:
            raise ValueError(
                f"注入的词汇表不符合 rule-vocabulary-v1: {errors[0].message[:120]}"
            )
        guards = tuple(payload.get("guards", ()))
        return GuardCatalog(
            guards=guards,
            effect_targets=tuple(payload.get("effect_targets", ())),
            fact_keys=tuple(payload.get("fact_keys", ())),
            operators=tuple(payload.get("operators", ())),
            guard_scopes=scopes_for(guards),
        )

    return GuardCatalog(
        guards=_DEFAULT_GUARDS,
        effect_targets=_DEFAULT_EFFECT_TARGETS,
        fact_keys=_DEFAULT_FACT_KEYS,
        operators=(),
        guard_scopes=scopes_for(_DEFAULT_GUARDS),
    )


#: 随包默认的受控 fact key。
_DEFAULT_FACT_KEYS: Tuple[Mapping[str, Any], ...] = (
    {
        "fact_key": "presale.permit.validity",
        "description": "预售许可是否经核验有效。缺失表示材料未提供；显式 null 表示已知该事实目前未知；两者都不得当作 false。",
        "value_type": "string",
        "nullable": True,
        "sensitive": False,
        "allowed_operators": ("equals", "not_equals", "in", "not_in", "exists",),
        "enum_values": ("confirmed_valid", "confirmed_absent", "unverified",),
    },
    {
        "fact_key": "our.role",
        "description": "我方在本交易中的角色。",
        "value_type": "string",
        "nullable": False,
        "sensitive": False,
        "allowed_operators": ("equals", "not_equals", "in", "not_in",),
        "enum_values": ("buyer", "supplier", "any",),
    },
    {
        "fact_key": "reservation.deposit.ratio",
        "description": "预留尾款比例（百分数）。",
        "value_type": "number",
        "nullable": True,
        "sensitive": False,
        "allowed_operators": ("equals", "not_equals", "gte", "lte", "exists",),
    },
)


#: 随包默认的硬边界 guard。
#: 当前唯一 guard 对应真实模块 `mod-commercial-housing-sale-eligibility-permit`
#: 的 `directed_block_policy`（预售许可未核验时收窄可输出范围）。
#: 结构受 rule-vocabulary-v1 契约约束，`build_guard_catalog` 会做自检。
_DEFAULT_GUARDS: Tuple[Mapping[str, Any], ...] = (
    {
        "guard_id": "guard_presale_permit_unverified",
        "title": "预售许可未核验时定向阻断许可依赖的输出",
        "guard_kind": "global_hard_boundary",
        "boundary_rule_id": "mod-commercial-housing-sale-eligibility-permit",
        "condition_mode": "all",
        "when": (
            {
                "fact_key": "presale.permit.validity",
                "operator": "in",
                "value": ("confirmed_absent", "unverified",),
            },
        ),
        "blocked_effects": (
            {
                "target_key": "output.draft_finalization",
                "actions": ("set_output",),
                "source_normative_classes": ("client_preferred", "client_advisory", "type_rule", "domain_rule", "global_soft_rule",),
            },
        ),
        "outcome": "block",
        "reason_code": "HARD_BOUNDARY_CONFLICT",
    },
)


#: 受控 effect target 的兜底集合。仅用于词汇表尚未提供 guard 时的 target 合法性判定；
#: 任何**边界**判定都不依赖它（边界只能来自 vocabulary 的 guards）。
_DEFAULT_EFFECT_TARGETS: Tuple[Mapping[str, Any], ...] = (
    {
        "target_key": "output.draft_finalization",
        "description": "是否允许自动定稿依赖某前置条件的交易条款。",
        "value_type": "boolean",
        "allowed_actions": ["require", "forbid", "set_output"],
        "allowed_normative_classes": ["global_hard_boundary", "client_mandatory"],
        "client_writable": False,
    },
    {
        "target_key": "output.reservation_ratio",
        "description": "建议保留的尾款比例。",
        "value_type": "number",
        "allowed_actions": ["require", "prefer", "set_output"],
        "allowed_normative_classes": [
            "client_mandatory", "client_preferred", "type_rule", "global_soft_rule",
        ],
        "client_writable": True,
    },
)


def is_rule_executable(rule: Mapping[str, Any]) -> bool:
    """审批轴与执行轴必须**同时**为 active（RS-HC-002 / RES-025）。"""
    return (
        rule.get("approval_status") == "active"
        and rule.get("activation_status") == "active"
    )


def _normative_class_of(rule: Mapping[str, Any]) -> str:
    level = rule.get("normative_level")
    if rule.get("rule_kind") == "output_style":
        return "client_advisory"
    return models.CLIENT_NORMATIVE_LEVEL_TO_CLASS.get(level, "client_advisory")


#: 条件求值的三态结果。**「未确定」必须与「条件为假」分开**——
#: 合并二者会让硬边界在材料未提供时静默失效（见 `_condition_holds` 说明）。
_CONDITION_UNKNOWN: Any = object()


#: 受控 value_type → 类型判定。bool 是 int 的子类，须先排除。
_TYPE_CHECKS: Mapping[str, Any] = {
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


def _declaration_problem(declaration: Mapping[str, Any], value: Any) -> Optional[str]:
    """按 `factKey` 声明判定取值是否违规。返回人类可读原因，合法则 None。

    校验 `nullable`、`value_type`、`enum_values`——这三项此前**全无执行点**，
    于是枚举外取值与类型不符被当作正常值，使硬边界失效（W7R3-FACT-OUT-OF-ENUM）。
    """
    if value is None:
        if declaration.get("nullable") is False:
            return (f"fact 声明 nullable=false，但收到 null："
                    f"{declaration.get('fact_key')}")
        return None  # null 本身由求值层当作「未确定」，不在此判违规

    value_type = declaration.get("value_type")
    check = _TYPE_CHECKS.get(str(value_type))
    if check is not None and not check(value):
        return (f"fact 声明 value_type={value_type}，实际为 "
                f"{type(value).__name__}：{declaration.get('fact_key')}")

    enum_values = declaration.get("enum_values")
    if enum_values and value not in tuple(enum_values):
        return (f"fact 取值不在声明枚举内：{declaration.get('fact_key')}={value!r}，"
                f"允许值 {sorted(enum_values)}")
    return None


def _operator_declaration_problem(
    catalog: "GuardCatalog", when: Sequence[Mapping[str, Any]]
) -> Optional[str]:
    """校验每个子句的 operator 是否在该 fact 的 `allowed_operators` 内。

    `allowed_operators` 此前无执行点。违规意味着词汇表自身的编写错误
    （用未声明的操作符判定该事实），按未确定转人工，不猜测其语义。
    """
    declarations = {
        str(f.get("fact_key")): f for f in catalog.fact_keys if f.get("fact_key")
    }
    for clause in when:
        key = str(clause.get("fact_key"))
        declaration = declarations.get(key)
        if declaration is None:
            return f"子句引用了未登记的 fact 键：{key}"
        allowed = tuple(declaration.get("allowed_operators") or ())
        if allowed and clause.get("operator") not in allowed:
            return (f"operator {clause.get('operator')!r} 不在 fact {key} 的 "
                    f"allowed_operators {sorted(allowed)} 内")
    return None


def validate_facts(
    catalog: "GuardCatalog", facts: Mapping[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """按键声明校验 fact 取值。

    返回 `(净化后的 facts, 问题清单)`。**违反声明的键会被移除**，
    使条件求值把它们当作「未确定」——未识别的取值不得被当作有利值
    （与「缺失/null 不得当作 false」同源，见 ADR-020 与 RS-HC-007）。
    """
    declarations = {
        str(f.get("fact_key")): f for f in catalog.fact_keys if f.get("fact_key")
    }
    clean: Dict[str, Any] = {}
    issues: List[Dict[str, Any]] = []
    for key, value in facts.items():
        declaration = declarations.get(str(key))
        if declaration is None:
            issues.append({
                "code": "UNKNOWN_FACT_OR_TARGET",
                "fact_key": str(key),
                "detail": f"fact 键未在词汇表登记：{key}；请先登记该键或其取值口径。",
            })
            continue
        problem = _declaration_problem(declaration, value)
        if problem:
            issues.append({
                "code": "INVALID_CONDITION_TYPE",
                "fact_key": str(key),
                "detail": problem + "；未识别的取值不得作为有利值，故按未确定处理。",
            })
            continue
        clean[str(key)] = value
    return clean, issues


def _evaluate_clause(clause: Mapping[str, Any], facts: Mapping[str, Any]) -> Any:
    """求值单个 guard 子句，返回 True / False / `_CONDITION_UNKNOWN`。

    事实缺失或显式 null 一律视为**未确定**，而不是「条件不成立」。
    理由（第二轮独立验证发现的 R0 缺陷）：

    - 本模块唯一随包 guard 的立法目的是「预售许可**未核验**时定向阻断」，
      而「材料未提供」在语义上正是未核验——把它当作「不触发」等于
      把未知当作最宽松值，硬边界形同虚设；
    - fact key 自身的随包声明明确写着「缺失表示材料未提供；显式 null 表示
      已知该事实目前未知；两者都不得当作 false」；
    - ADR-020 要求无法确定的一律转人工，不猜测、不静默择一。
    """
    fact_key = clause.get("fact_key")
    operator = clause.get("operator")
    expected = clause.get("value")
    if fact_key not in facts or facts[fact_key] is None:
        return _CONDITION_UNKNOWN
    actual = facts[fact_key]
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "in":
        if not isinstance(expected, (list, tuple)):
            return False
        return actual in expected
    if operator == "not_in":
        if not isinstance(expected, (list, tuple)):
            return True
        return actual not in expected
    if operator == "exists":
        return True
    # 未登记 operator：不确定即转人工
    raise ValueError(f"未登记的 operator: {operator!r}")


def _condition_holds(
    when: Sequence[Mapping[str, Any]],
    facts: Mapping[str, Any],
    *,
    mode: str = "all",
) -> Any:
    """按 `condition_mode` 组合子句，返回 True / False / `_CONDITION_UNKNOWN`。

    `rule-vocabulary-v1` 把 `condition_mode` 列为**必填**（enum all/any），
    `when` 允许最多 50 个子句，故必须真的读取该字段。组合规则用 Kleene 三值逻辑
    （标准语义，无歧义）：

    - ``all``：任一子句**确定假** ⇒ 假；无假但有未确定 ⇒ 未确定；否则真。
    - ``any``：任一子句**确定真** ⇒ 真；无真但有未确定 ⇒ 未确定；否则假。

    此前的实现把 `when` 无条件按 AND 处理，导致两个方向的错误：
    ``any`` 模式失败开放（该拦不拦）；``all`` 模式在「有子句未知、另有子句确定假」时
    过度阻断，且结论依赖子句顺序（第三轮独立验证发现）。

    未确定由调用方按 fail-closed（触发 guard → 阻断 + 转人工）处理。
    """
    results = [_evaluate_clause(clause, facts) for clause in when]
    if mode == "all":
        if any(r is False for r in results):
            return False
        if any(r is _CONDITION_UNKNOWN for r in results):
            return _CONDITION_UNKNOWN
        return True
    if mode == "any":
        if any(r is True for r in results):
            return True
        if any(r is _CONDITION_UNKNOWN for r in results):
            return _CONDITION_UNKNOWN
        return False
    # 词汇表 schema 已限定 enum；走到这里说明词汇被绕过，按未确定转人工
    raise ValueError(f"未登记的 condition_mode: {mode!r}")


def _guard_applies(
    catalog: GuardCatalog,
    guard: Mapping[str, Any],
    context: Optional[Mapping[str, Any]],
) -> bool:
    """判断硬边界是否属于本次合同场景。

    hard boundary 的强制性是“在其适用范围内不可覆盖”，并不意味着房地产许可
    可以跨领域约束设备采购。适用范围直接取 boundary rule 的公共元数据，避免在
    guard 词汇表中复制第二份 type/domain 真源。直接调用且未提供 context 时保留旧
    行为，便于对 guard 本身做独立真值测试；Resolver 的生产路径总会传入完整 context。
    """
    if context is None:
        return True
    scope = catalog.guard_scopes.get(str(guard.get("guard_id")))
    if not scope:
        # 无法取得边界规则的范围时不擅自放行，保持 fail closed。
        return True

    scoped_types = set(scope.get("type_ids") or ())
    context_types = {
        context.get("primary_type_id"),
        *(context.get("secondary_type_ids") or ()),
    } - {None, ""}
    if scoped_types and context_types and scoped_types.isdisjoint(context_types):
        return False

    scoped_domains = set(scope.get("domain_codes") or ())
    context_domains = {
        context.get("confirmed_domain_code"),
        context.get("primary_domain_code"),
        *(context.get("secondary_domain_codes") or ()),
    } - {None, ""}
    if scoped_domains and context_domains and scoped_domains.isdisjoint(context_domains):
        return False

    scoped_roles = set(scope.get("roles") or ()) - {"any"}
    role = context.get("our_role")
    if scoped_roles and role and role not in scoped_roles:
        return False

    scoped_scenes = set(scope.get("scene_tags") or ())
    context_scenes = set(context.get("scene_tags") or ())
    if scoped_scenes and context_scenes and scoped_scenes.isdisjoint(context_scenes):
        return False
    return True


def evaluate_hard_guards(
    catalog: GuardCatalog,
    *,
    rules: Sequence[Mapping[str, Any]] = (),
    facts: Mapping[str, Any] = (),
    target_keys: Optional[Set[str]] = None,
    context: Optional[Mapping[str, Any]] = None,
) -> GuardVerdict:
    """判定待执行规则是否触发硬边界或需要人工确认。"""
    for rule in rules:
        if not isinstance(rule, Mapping):
            raise TypeError("规则必须是映射类型。")

    # 先按键声明校验 fact 取值：违规取值会被移除，使其在条件求值中
    # 表现为「未确定」→ 硬边界 fail closed（W7R3-FACT-OUT-OF-ENUM）。
    facts, fact_issues = validate_facts(catalog, facts)

    targets = set(target_keys or ())
    for rule in rules:
        effect = rule.get("effect") or {}
        if isinstance(effect, Mapping) and effect.get("target_key"):
            targets.add(effect["target_key"])

    # 未知 target 不得假设安全
    unknown = tuple(sorted(t for t in targets if t not in catalog.known_target_keys))
    if unknown:
        return GuardVerdict(
            human_confirmation_required=True,
            unknown_targets=unknown,
            conflicts=tuple(
                {"code": "UNKNOWN_FACT_OR_TARGET", "target_key": t} for t in unknown
            ),
        )

    verdicts: List[GuardVerdict] = []
    for guard in catalog.guards:
        if not _guard_applies(catalog, guard, context):
            continue
        when = guard.get("when") or ()
        # 子句的 operator 必须在该 fact 的 allowed_operators 内。
        # 该声明此前同样没有执行点；违规属词汇表编写错误 → 按未确定转人工。
        operator_problem = _operator_declaration_problem(catalog, when)
        if operator_problem:
            verdicts.append(GuardVerdict(
                human_confirmation_required=True,
                conflicts=({"code": "INVALID_CONDITION_TYPE",
                            "guard_id": guard.get("guard_id"),
                            "detail": operator_problem},),
            ))
            continue

        fact_state = "matched"
        try:
            holds = _condition_holds(when, facts,
                                     mode=guard.get("condition_mode", "all"))
        except ValueError:
            verdicts.append(GuardVerdict(
                human_confirmation_required=True,
                conflicts=({"code": "UNKNOWN_FACT_OR_TARGET",
                            "guard_id": guard.get("guard_id")},),
            ))
            continue
        if holds is _CONDITION_UNKNOWN:
            # fail closed：未知按「未核验」处理，触发 guard。
            # 但必须与「已确认违规」在载荷上可区分——前者要补材料，
            # 后者是实体判断，律师的处理动作不同。
            fact_state = "unknown"
        elif not holds:
            continue

        blocked_ids: List[str] = []
        for blocked in guard.get("blocked_effects") or ():
            target_key = blocked.get("target_key")
            if target_key not in targets:
                continue
            for rule in rules:
                if (rule.get("effect") or {}).get("target_key") != target_key:
                    continue
                # 硬边界命中即阻断，**不按来源性质筛选**：
                # ADR-009 要求硬边界不可被任何普通偏好（含客户强制政策）覆盖。
                # `source_normative_classes` 在词汇表中保留为语义文档，
                # 不作为放行依据——否则 `client_mandatory` 可绕过硬边界。
                blocked_ids.append(
                    str(rule.get("client_rule_id") or rule.get("rule_id"))
                )

        if blocked_ids:
            verdicts.append(GuardVerdict(
                blocked=True,
                human_confirmation_required=True,
                blocked_rule_ids=tuple(dict.fromkeys(blocked_ids)),
                # 必须包成列表再 tuple：tuple({...}) 会得到**键名元组**，
                # 下游 dict(c) 抛 ValueError，使硬边界路径整体不可达
                # （W7 独立验证发现的 R0 缺陷）。
                conflicts=tuple([
                    {
                        "code": guard.get("reason_code", "HARD_BOUNDARY_CONFLICT"),
                        "guard_id": guard.get("guard_id"),
                        "boundary_rule_id": guard.get("boundary_rule_id"),
                        "blocked_rule_ids": list(dict.fromkeys(blocked_ids)),
                        #: matched=已确认命中条件；unknown=事实缺失或未知而 failel closed
                        "fact_state": fact_state,
                        "fact_keys": sorted(
                            str(c.get("fact_key")) for c in when if c.get("fact_key")
                        ),
                        "detail": (
                            "触发条件的事实未提供或未知，已按 fail closed 阻断并转人工："
                            "请补充该事实的核验结果后重跑。"
                            if fact_state == "unknown" else
                            "规则触及不可覆盖的全局硬边界，未执行并转人工确认。"
                        ),
                    }
                ]),
            ))

    # fact 键声明的违规（未登记 / 枚举外 / 类型不符 / 不可空却给 null）
    # 一律报冲突并要求人工确认——不得静默忽略。
    if fact_issues:
        verdicts.append(GuardVerdict(
            human_confirmation_required=True,
            conflicts=tuple(fact_issues),
        ))

    result = GuardVerdict()
    for verdict in verdicts:
        result = result.merged(verdict)
    return result


def check_dependencies(
    rules: Sequence[Mapping[str, Any]], available_rule_ids: Set[str]
) -> DependencyVerdict:
    """依赖缺失即不得孤立应用（RES-019）。"""
    missing: List[str] = []
    known = set(available_rule_ids) | {
        str(r.get("client_rule_id")) for r in rules if r.get("client_rule_id")
    }
    for rule in rules:
        for dependency in rule.get("depends_on") or ():
            if dependency not in known:
                missing.append(str(dependency))
    return DependencyVerdict(satisfied=not missing, missing=tuple(dict.fromkeys(missing)))


def detect_conflicts(rules: Sequence[Mapping[str, Any]]) -> Tuple[Mapping[str, Any], ...]:
    """显式冲突与同 target 的互斥动作。**不自行择一**（RES-020）。"""
    by_id = {str(r.get("client_rule_id")): r for r in rules if r.get("client_rule_id")}
    found: List[Mapping[str, Any]] = []

    for rule in rules:
        rule_id = str(rule.get("client_rule_id"))
        for other_id in rule.get("conflicts_with") or ():
            if other_id in by_id:
                pair = tuple(sorted((rule_id, str(other_id))))
                if not any(c.get("pair") == pair for c in found):
                    found.append({
                        "code": "HUMAN_CONFIRMATION_REQUIRED",
                        "kind": "explicit_conflict",
                        "pair": pair,
                        "target_key": (rule.get("effect") or {}).get("target_key"),
                    })

    by_target: Dict[str, List[Mapping[str, Any]]] = {}
    for rule in rules:
        effect = rule.get("effect") or {}
        if not isinstance(effect, Mapping) or not effect.get("target_key"):
            continue
        by_target.setdefault(effect["target_key"], []).append(rule)

    for target_key, group in sorted(by_target.items()):
        if len(group) < 2:
            continue
        values = {
            json_key((r.get("effect") or {}).get("value")) for r in group
        }
        if len(values) > 1:
            found.append({
                "code": "HUMAN_CONFIRMATION_REQUIRED",
                "kind": "value_divergence",
                "target_key": target_key,
                "rule_ids": sorted(str(r.get("client_rule_id")) for r in group),
            })
    return tuple(found)


def json_key(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True)
