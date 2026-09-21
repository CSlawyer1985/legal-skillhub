#!/usr/bin/env python3
"""公共＋客户规则合成。

契约来源：architecture-contract.md §7（解析算法）、§6（EffectiveRuleSet）、
§8.5（哈希）、§14（兼容与降级边界）；ADR-009（优先级按性质）、
ADR-010（审查任务固定快照）、ADR-020（硬边界只做确定性 guard）、
ADR-022（公共升级默认暂停客户 overlay）、ADR-028（降级边界）。

硬边界：
- **未选择客户**时结果必须与纯公共选择器一致（RES-024 / INT-008）；
- 一旦**明确选择客户**，snapshot 缺失、损坏或 public fingerprint 不兼容时
  **必须 fail closed**，不得静默退回公共规则（DATA-006 / ADR-028）；
- 冲突不得静默择一，一律输出冲突集合并要求人工确认（RS-HC-007）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from . import guard_catalog, models, validator

__all__ = [
    "Resolver",
    "ResolverError",
]

#: 优先级排序：按性质，不按数值（ADR-009）
_CLASS_ORDER = tuple(models.NORMATIVE_CLASSES)
_LAYER_ORDER = ("global", "domain", "type", "client", "case_instruction")


class ResolverError(Exception):
    """合成无法给出可信结果。调用方不得降级为部分结果。

    携带 `code`（冻结错误码目录中的值），使 Core、集成入口与 HTTP 三处
    对同一情形报**同一个码**——此前同一「active manifest 损坏」在
    三处分别是无码异常 / SNAPSHOT_INTEGRITY_FAILED / HUMAN_CONFIRMATION_REQUIRED
    （W7R3-SNAPSHOT-CORRUPT-CODES）。
    """

    def __init__(self, message: str, *, code: str = "SNAPSHOT_INTEGRITY_FAILED") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class _Candidate:
    rule_id: str
    version: str
    source_layer: str
    source_snapshot: str
    normative_class: str
    content_hash: str
    payload: Mapping[str, Any]
    matched_scope: Mapping[str, Any]
    inclusion_reason: str
    overridden_rule_ids: Tuple[str, ...] = ()
    dependencies: Tuple[str, ...] = ()


class Resolver:
    """在 PublicRepository 与 ClientRepository 之上实现 active 客户 overlay。"""

    def __init__(self, *, public_repository: Any, client_repository: Any) -> None:
        self._public = public_repository
        self._clients = client_repository

    # ------------------------------------------------------------------ #
    # 主入口
    # ------------------------------------------------------------------ #
    def resolve_effective_rules(
        self,
        context: Mapping[str, Any],
        *,
        public_fingerprint_override: Optional[str] = None,
    ) -> models.EffectiveRuleSet:
        ctx = dict(context)
        profile_id = ctx.get("client_profile_id")
        snapshot_id = ctx.get("client_policy_snapshot_id")

        public_result = self._public.resolve_public_rules(
            primary_type_id=ctx["primary_type_id"],
            secondary_type_ids=list(ctx.get("secondary_type_ids") or ()),
            our_role=ctx["our_role"],
            scene_tags=list(ctx.get("scene_tags") or ()),
            classification_status=ctx.get("classification_status", "high"),
            confirmed_domain_code=ctx.get("confirmed_domain_code", ""),
        )

        candidates: List[_Candidate] = [
            _Candidate(
                rule_id=r.rule_id, version=r.version, source_layer=r.source_layer,
                source_snapshot=r.source_snapshot, normative_class=r.normative_class,
                content_hash=r.content_hash, payload=dict(r.rule_payload or {}),
                matched_scope=dict(r.matched_scope), inclusion_reason=r.inclusion_reason,
                overridden_rule_ids=tuple(r.overridden_rule_ids),
                dependencies=tuple(r.dependencies),
            )
            for r in public_result.effective_rules
        ]
        excluded: List[Dict[str, Any]] = [dict(e) for e in public_result.excluded_rules]
        conflicts: List[Dict[str, Any]] = [dict(c) for c in public_result.rule_conflicts]
        human = public_result.human_confirmation_required
        overlay_active = False

        # ---- 客户 overlay ------------------------------------------------ #
        if profile_id is not None:
            fingerprint_expected = public_fingerprint_override or self._public.public_asset_fingerprint
            snapshot, overlay_active, overlay_conflicts, overlay_human = self._load_client_overlay(
                profile_id=profile_id,
                snapshot_id=snapshot_id,
                expected_fingerprint=fingerprint_expected,
            )
            conflicts.extend(overlay_conflicts)
            human = human or overlay_human

            if overlay_active and snapshot is not None:
                client_candidates, client_excluded, client_human, client_conflicts = (
                    self._build_client_candidates(ctx, snapshot)
                )
                candidates.extend(client_candidates)
                excluded.extend(client_excluded)
                conflicts.extend(client_conflicts)
                human = human or client_human

                # 本案授权：作用于**全量**候选（只影响被点名的规则），
                # 不得因此丢弃公共层候选。
                candidates, auth_conflicts, auth_human = self._apply_authorizations(
                    ctx, candidates
                )
                conflicts.extend(auth_conflicts)
                human = human or auth_human

        # ---- 硬边界（确定性 guard）-------------------------------------- #
        guard_verdict = guard_catalog.evaluate_hard_guards(
            guard_catalog.build_guard_catalog(self._public),
            rules=[c.payload for c in candidates if c.source_layer == "client"],
            facts=ctx.get("facts") or {},
            target_keys={
                (c.payload.get("effect") or {}).get("target_key")
                for c in candidates
                if isinstance(c.payload.get("effect"), Mapping)
                and (c.payload.get("effect") or {}).get("target_key")
            },
            context=ctx,
        )
        blocked = set(guard_verdict.blocked_rule_ids)
        if blocked:
            candidates = [c for c in candidates if c.rule_id not in blocked]
            for rule_id in sorted(blocked):
                excluded.append({
                    "rule_id": rule_id,
                    "reason": "hard_boundary_conflict: 触及全局硬边界，未执行并转人工",
                })
        conflicts.extend(dict(c) for c in guard_verdict.conflicts)
        human = human or guard_verdict.human_confirmation_required

        # ---- 依赖与冲突 -------------------------------------------------- #
        available_ids = {c.rule_id for c in candidates}
        dependency = guard_catalog.check_dependencies(
            [c.payload for c in candidates if c.source_layer == "client"],
            available_rule_ids=available_ids,
        )
        if not dependency.satisfied:
            dropped = [
                c for c in candidates
                if c.source_layer == "client"
                and any(d in dependency.missing for d in c.dependencies)
            ]
            keep = {c.rule_id for c in candidates} - {c.rule_id for c in dropped}
            candidates = [c for c in candidates if c.rule_id in keep]
            for c in dropped:
                excluded.append({
                    "rule_id": c.rule_id,
                    "reason": f"dependencies_missing: {sorted(set(c.dependencies) & set(dependency.missing))}",
                })

        client_rule_payloads = [c.payload for c in candidates if c.source_layer == "client"]
        detected = guard_catalog.detect_conflicts(client_rule_payloads)
        if detected:
            conflicts.extend(dict(c) for c in detected)
            human = True

        # ---- 组装 -------------------------------------------------------- #
        # 结果中**不含客户层规则**时，必须保持公共快照自身的发射顺序，
        # 即 2.8.1 的 global → domain → principles → modules 目录序（RES-024 / INT-008）。
        # §7.6 的性质排序是"建议"，用于客户 overlay 混层时表达优先级；
        # 对纯公共结果套用它会让全局政策文档掉到末尾、模块被改成 rule_id
        # 字母序，与 2.8.1 不等价（W7 独立验证发现的 R0 缺陷）。
        # 中间各步（授权、硬边界、依赖剔除）均保序，故此处保留即为目录序。
        has_client_layer = any(c.source_layer == "client" for c in candidates)
        if has_client_layer:
            candidates.sort(key=self._sort_key)
        effective = [
            models.EffectiveRule(
                rule_id=c.rule_id, version=c.version, source_layer=c.source_layer,
                source_snapshot=c.source_snapshot, matched_scope=dict(c.matched_scope),
                inclusion_reason=c.inclusion_reason, normative_class=c.normative_class,
                content_hash=c.content_hash, overridden_rule_ids=c.overridden_rule_ids,
                dependencies=c.dependencies,
                payload_schema_id=c.payload.get("_payload_schema_id")
                or "one-contract/rule-graph-v1.schema.json",
                rule_payload=dict(c.payload),
            )
            for c in candidates
        ]
        trace = [
            models.ResolutionTraceItem(
                rule_id=c.rule_id, version=c.version, source_layer=c.source_layer,
                source_snapshot=c.source_snapshot, matched_scope=dict(c.matched_scope),
                decision="included", content_hash=c.content_hash,
                overridden_rule_ids=c.overridden_rule_ids, dependencies=c.dependencies,
            )
            for c in candidates
        ]

        # 记录**实际使用的**客户快照 ID，而不是调用方传入的原始值：
        # 未显式给快照时本方法会从 active manifest 隐式固定一个（INT-010），
        # 若此处回填原始入参，结果会变成"客户规则已生效但快照 ID 为 null"，
        # 溯源（RES-026 / INT-004 / INT-009）随之失效（生产者侧 HTTP 冒烟发现）。
        resolved_snapshot_id = None
        if overlay_active:
            resolved_snapshot_id = (snapshot or {}).get("snapshot_id") or snapshot_id

        result = models.EffectiveRuleSet(
            schema_version="1.0",
            public_snapshot_id=self._public.public_snapshot_id,
            context_hash=models.content_hash(
                {k: v for k, v in ctx.items() if k != "client_policy_snapshot_id"}
            ),
            client_profile_id=profile_id,
            client_policy_snapshot_id=resolved_snapshot_id,
            effective_rules=effective,
            excluded_rules=excluded,
            rule_conflicts=conflicts,
            coverage_level=public_result.coverage_level,
            coverage_notice=public_result.coverage_notice,
            resolution_trace=trace,
            human_confirmation_required=human,
        )
        result.client_overlay_active = overlay_active  # type: ignore[attr-defined]
        return result.with_hash()

    # ------------------------------------------------------------------ #
    # 客户 overlay
    # ------------------------------------------------------------------ #
    def _load_client_overlay(
        self,
        *,
        profile_id: str,
        snapshot_id: Optional[str],
        expected_fingerprint: str,
    ) -> Tuple[Optional[Mapping[str, Any]], bool, List[Dict[str, Any]], bool]:
        """返回 (snapshot, overlay_active, conflicts, human_confirmation_required)。"""
        try:
            profile = self._clients.get_client_profile(profile_id)
        except Exception as exc:
            return None, False, [{
                "code": "CLIENT_PROFILE_NOT_FOUND",
                "client_profile_id": profile_id,
                "detail": str(exc)[:200],
            }], True

        # DATA-005：非 active 的客户档案不得进入合成。
        # 写路径（client_repository）已有校验，但读/合成路径此前没有，
        # 导致 inactive 客户的规则仍会生效（W7 独立验证发现的 R0 缺陷）。
        # 错误码用冻结目录的 CANDIDATE_NOT_EXECUTABLE（非 active 资产试图生效），
        # 而不是 CLIENT_PROFILE_NOT_FOUND——档案确实存在，只是不可执行。
        if profile.get("status") != "active":
            return None, False, [{
                "code": "CANDIDATE_NOT_EXECUTABLE",
                "client_profile_id": profile_id,
                "profile_status": profile.get("status"),
                "detail": f"客户档案状态为 {profile.get('status')!r}，不参与合成；"
                          "请先恢复为 active，或明确改选仅公共规则。",
            }], True

        try:
            active = self._clients.load_active_snapshot(profile_id)
        except Exception as exc:
            # active manifest 损坏 → fail closed，**不回退**草稿或最新文件（RES-023）。
            # 这是不可恢复的存储损坏，直接抛出而不是返回“空 overlay”，
            # 否则调用方可能误以为“该客户没有规则”而继续出审查结论。
            raise ResolverError(
                f"客户 {profile_id} 的 active manifest 损坏，拒绝加载：{str(exc)[:180]}"
            ) from exc

        if active is None:
            return None, False, [{
                "code": "SNAPSHOT_INTEGRITY_FAILED",
                "client_profile_id": profile_id,
                "detail": "该客户尚无已发布的 active 快照；不使用最近历史快照（INT-010）。",
            }], True

        target_id = snapshot_id or active["snapshot_id"]
        try:
            snapshot = self._clients.load_snapshot(profile_id, target_id)
        except Exception as exc:
            return None, False, [{
                "code": "SNAPSHOT_INTEGRITY_FAILED",
                "client_profile_id": profile_id,
                "snapshot_id": target_id,
                "detail": str(exc)[:200],
            }], True

        bound = snapshot.get("public_asset_fingerprint")
        if bound != expected_fingerprint:
            # 公共升级 → 暂停 overlay，客户数据保留（DATA-006 / ADR-022）
            return None, False, [{
                "code": "PUBLIC_SNAPSHOT_MISMATCH",
                "client_profile_id": profile_id,
                "snapshot_id": target_id,
                "snapshot_public_fingerprint": bound,
                "current_public_fingerprint": expected_fingerprint,
                "detail": "客户快照绑定的公共指纹与当前公共版本不一致；"
                          "客户数据已保留但 overlay 已暂停。",
            }], True

        return snapshot, True, [], False

    def _build_client_candidates(
        self, ctx: Mapping[str, Any], snapshot: Mapping[str, Any]
    ) -> Tuple[List[_Candidate], List[Dict[str, Any]], bool, List[Dict[str, Any]]]:
        try:
            rules = self._clients_snapshot_rules(snapshot)
        except Exception as exc:
            return [], [{"rule_id": "<snapshot>", "reason": f"snapshot_rules_unreadable: {exc}"}], True, []

        candidates: List[_Candidate] = []
        excluded: List[Dict[str, Any]] = []
        undetermined: List[Dict[str, Any]] = []
        human = False
        now = self._parse_time(ctx.get("now")) or datetime.now(timezone.utc)

        for rule in rules:
            rule_id = str(rule.get("client_rule_id"))
            if not guard_catalog.is_rule_executable(rule):
                excluded.append({
                    "rule_id": rule_id,
                    "reason": "not_executable: 审批轴与执行轴必须同为 active（RES-025）",
                })
                continue

            validity = rule.get("validity") or {}
            start = self._parse_time(validity.get("valid_from"))
            end = self._parse_time(validity.get("valid_until"))
            if start and now < start:
                excluded.append({"rule_id": rule_id, "reason": "not_yet_valid: 尚未生效"})
                continue
            if end and now > end:
                excluded.append({"rule_id": rule_id, "reason": "expired: 已过期"})
                continue

            mismatch_reason, undetermined_reason = self._scope_mismatch(rule, ctx)
            if mismatch_reason:
                excluded.append({"rule_id": rule_id, "reason": mismatch_reason})
                continue
            if undetermined_reason:
                # 缺维度 ⇒ 未确定：排除但**必须显式转人工**，不得静默丢弃
                # （第三轮独立验证确认的 R0）。
                human = True
                excluded.append({"rule_id": rule_id, "reason": undetermined_reason})
                undetermined.append({
                    "code": "HUMAN_CONFIRMATION_REQUIRED",
                    "kind": "scope_undetermined",
                    "rule_ids": [rule_id],
                    "detail": undetermined_reason,
                })
                continue

            payload = dict(rule)
            candidates.append(_Candidate(
                rule_id=rule_id,
                version=str(rule.get("version") or "0.0.0"),
                source_layer="client",
                source_snapshot=str(snapshot.get("snapshot_id")),
                normative_class=models.normative_class_for_client_level(
                    str(rule.get("normative_level") or "advisory")
                ),
                content_hash=str(rule.get("content_sha256") or ""),
                payload=payload,
                matched_scope=dict(rule.get("scope") or {}),
                inclusion_reason="客户 active 规则且 scope 匹配本案上下文",
                dependencies=tuple(rule.get("depends_on") or ()),
            ))

        return candidates, excluded, human, undetermined

    def _clients_snapshot_rules(self, snapshot: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        """读取已发布快照内的规则集合。

        经 `publisher.Publisher.load_snapshot` 读取：它会**复核内容哈希**，
        篡改过的快照会抛错而不是被静默使用（LIFE-008）。W3A 未对外暴露
        snapshot→rules 的读取方法，且 W3A 模块不在本包白名单内，故在此复用
        publisher 的完整性校验路径，不新增对客户存储的旁路。
        """
        from . import paths, publisher

        profile_dir = paths.contained_path(
            self._clients.clients_root, snapshot["client_profile_id"]
        )
        doc = publisher.Publisher(profile_dir).load_snapshot(snapshot["snapshot_id"])
        return tuple(doc["rules_doc"].get("rules", ()))

    def _scope_mismatch(
        self, rule: Mapping[str, Any], ctx: Mapping[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        """返回 `(mismatch_reason, undetermined_reason)`，二者互斥。

        **「上下文未提供该维度」不得当作「取值不匹配」。** 原实现用
        `if allowed and value not in allowed`，缺维度时 `value` 为 `None`，
        `None not in allowed` 成立 → 规则被静默丢弃，且无冲突、无转人工，
        结果看起来像一份干净的纯公共结果（第三轮独立验证确认的 R0）。

        缺维度按**未确定**处理（ADR 提案 Q3(b)）：既不静默应用，也不静默丢弃，
        而是排除并显式要求人工确认；确定的取值不匹配才是安静的合法排除。
        """
        scope = rule.get("scope") or {}
        if scope.get("applies_to_all"):
            return None, None

        undetermined: List[str] = []
        checks = (
            ("domain_codes", ctx.get("primary_domain_code"), "domain"),
            ("type_ids", ctx.get("primary_type_id"), "type"),
            ("roles", ctx.get("our_role"), "role"),
            ("contract_stages", ctx.get("contract_stage"), "stage"),
        )
        for key, value, label in checks:
            allowed = scope.get(key) or ()
            if not allowed:
                continue
            if value is None:
                undetermined.append(f"{label}（规则限定 {sorted(allowed)}）")
                continue
            if value not in allowed:
                return (f"scope_mismatch[{label}]: 规则限定 {sorted(allowed)}，本案为 {value!r}",
                        None)

        allowed_scenes = set(scope.get("scene_tags") or ())
        scenes = set(ctx.get("scene_tags") or ())
        if allowed_scenes:
            if not scenes:
                undetermined.append(f"scene（规则限定 {sorted(allowed_scenes)}）")
            elif not (allowed_scenes & scenes):
                return (f"scope_mismatch[scene]: 规则限定 {sorted(allowed_scenes)}，本案场景无交集",
                        None)

        if undetermined:
            return None, (
                "scope_undetermined: 上下文未提供 " + "、".join(undetermined)
                + "；未确定不得当作不匹配，故本规则不执行并转人工确认"
            )
        return None, None

    # ------------------------------------------------------------------ #
    # 本案授权
    # ------------------------------------------------------------------ #
    def _apply_authorizations(
        self, ctx: Mapping[str, Any], candidates: List[_Candidate]
    ) -> Tuple[List[_Candidate], List[Dict[str, Any]], bool]:
        """本案授权例外。

        有有效授权：被点名规则**保留在结果中但标记为被覆盖**，并记录授权人、
        时间、理由与被覆盖规则 ID（RES-018）。不 Physical 删除候选，
        以便 trace 与审计都能看到"它被覆盖了"这一事实。

        无有效授权：**不静默覆盖**，原样返回并要求人工确认（RES-017）。
        """
        authorizations = list(ctx.get("case_authorizations") or ())
        instruction = ctx.get("case_instruction") or {}
        target_ids = set(instruction.get("overrides_rule_ids") or ())

        # 未声明任何本案指令或授权 → 无豁免，原样返回
        if not target_ids and not authorizations:
            return candidates, [], False

        # 提供了授权声明但未点名具体规则时，以授权声明的规则集合为准。
        # 这是保守语义：授权声明本身就是"请求豁免"的表示，必须被校验，
        # 不能因为缺少 case_instruction 就静默忽略（过期授权尤其如此）。
        if not target_ids:
            for auth in authorizations:
                target_ids |= set(auth.get("overrides_rule_ids") or ())
            if not target_ids:
                return candidates, [], False

        conflicts: List[Dict[str, Any]] = []
        now = self._parse_time(ctx.get("now")) or datetime.now(timezone.utc)

        # 授权必须**属于本案客户**（`case-authorization-v1` 把 client_profile_id
        # 列为必填；SEC-003 要求两客户严格隔离）。原实现只读 overrides_rule_ids
        # 等少数字段、从不校验归属——实测「归属 A 的授权」可覆盖 B 的规则，
        # 跨客户隔离在授权路径上是破的。缺归属或归属不符一律 fail closed。
        expected_profile = ctx.get("client_profile_id")
        scope_rejected: List[Mapping[str, Any]] = []
        valid_auth = None
        for auth in authorizations:
            expires = self._parse_time(auth.get("expires_at"))
            if expires and now > expires:
                continue
            if not target_ids.issubset(set(auth.get("overrides_rule_ids") or ())):
                continue
            if expected_profile is None or auth.get("client_profile_id") != expected_profile:
                scope_rejected.append(auth)
                continue
            valid_auth = auth
            break

        if valid_auth is None:
            if scope_rejected:
                conflicts.append({
                    "code": "HUMAN_CONFIRMATION_REQUIRED",
                    "kind": "authorization_scope_mismatch",
                    "overridden_rule_ids": sorted(target_ids),
                    "client_profile_id": expected_profile,
                    "authorization_profile_ids": sorted(
                        str(a.get("client_profile_id")) for a in scope_rejected),
                    "detail": "提供的授权不属于本案客户（或未声明归属），"
                              "不得用于覆盖本案规则；请改用本客户的授权，"
                              "或由律师另行确认。不静默生效。",
                })
                return candidates, conflicts, True
            conflicts.append({
                "code": "HUMAN_CONFIRMATION_REQUIRED",
                "kind": "authorization_missing",
                "overridden_rule_ids": sorted(target_ids),
                "detail": "本案指令要求突破客户强制政策，但缺少有效授权；不静默覆盖。",
            })
            return candidates, conflicts, True

        out: List[_Candidate] = []
        for candidate in candidates:
            if candidate.rule_id in target_ids:
                conflicts.append({
                    "code": "HUMAN_CONFIRMATION_REQUIRED",
                    "kind": "case_authorized_override",
                    "overridden_rule_ids": [candidate.rule_id],
                    # 必须记录**是哪一份授权**：此前只记授权人/时间/理由，
                    # 审计无法引用具体的授权记录（`case-authorization-v1`
                    # 的 authorization_id 与 evidence_refs 均未被读取）。
                    "authorization_id": valid_auth.get("authorization_id"),
                    "authorized_by": valid_auth.get("authorized_by"),
                    "authorized_at": valid_auth.get("authorized_at"),
                    "reason": valid_auth.get("reason"),
                    "authentication_level": valid_auth.get("authentication_level"),
                    "evidence_refs": list(valid_auth.get("evidence_refs") or ()),
                })
                out.append(_Candidate(
                    rule_id=candidate.rule_id, version=candidate.version,
                    source_layer=candidate.source_layer,
                    source_snapshot=candidate.source_snapshot,
                    normative_class=candidate.normative_class,
                    content_hash=candidate.content_hash, payload=candidate.payload,
                    matched_scope=candidate.matched_scope,
                    inclusion_reason=f"被本案授权例外覆盖（授权人 {valid_auth.get('authorized_by')}）",
                    overridden_rule_ids=tuple(
                        dict.fromkeys(candidate.overridden_rule_ids + (candidate.rule_id,))
                    ),
                    dependencies=candidate.dependencies,
                ))
                continue
            out.append(candidate)
        return out, conflicts, False

    # ------------------------------------------------------------------ #
    # 工具
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_time(value: Any) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _sort_key(c: _Candidate) -> Tuple[int, int, int, str, str]:
        """稳定排序：性质 → 来源专指度 → 显式优先级 → 稳定 ID → 版本。

        禁止依赖文件系统遍历顺序、JSON 对象顺序或写入时间（§7.6）。
        """
        class_rank = _CLASS_ORDER.index(c.normative_class) if c.normative_class in _CLASS_ORDER else 99
        layer_rank = _LAYER_ORDER.index(c.source_layer) if c.source_layer in _LAYER_ORDER else 99
        priority = int(c.payload.get("priority_within_class") or 0)
        # 来源越具体排名越靠前：client > type > domain > global
        specificity = -_LAYER_ORDER.index(c.source_layer) if c.source_layer in _LAYER_ORDER else 0
        return (class_rank, specificity, priority, c.rule_id, c.version)
