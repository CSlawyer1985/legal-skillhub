#!/usr/bin/env python3
"""客户档案、规则草稿、生命周期与发布的存储层。

契约来源：architecture-contract.md §8（客户数据模型）、§9（数据根与路径安全）、
§10（并发与原子性）、§11（错误码）；RS-HC-003/004/005；ADR-005/007/018/023。

数据布局（全部在 `data_root` 之外无写入）：
    <data-root>/clients/<profile-id>/
        profile.json
        drafts/<rule-id>.json
        snapshots/<snapshot-id>/{manifest.json,rules.json}
        active-manifest.json
        audit/events.jsonl

硬边界：
- 客户数据**绝不**写入 Skill 目录（RS-HC-003）；
- 保存草稿不隐式发布（RS-HC-004）；
- 已发布规则不做物理删除，只能以新快照停用或 deprecated（ADR-018 / CR-006）；
- 路径一律经 `contained_path` 校验，拒绝点段、绝对路径与符号链接越界。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import audit, models, paths, publisher, validator

__all__ = [
    "ACTIVE_PROFILE_STATUSES",
    "ClientRepository",
    "ClientStoreError",
    "RevisionConflict",
    "SnapshotIntegrityError",
]

#: 允许继续操作的 profile 状态
ACTIVE_PROFILE_STATUSES = ("active",)

#: 允许发布的规则状态（必须已完成律师批准与回归）
PUBLISHABLE_APPROVAL_STATES = ("regression_passed", "active")

_DIR_MODE = 0o700
_FILE_MODE = 0o600


class ClientStoreError(Exception):
    """客户存储操作失败。调用方不得降级为部分写入。"""


class RevisionConflict(ClientStoreError):
    """expected_revision 不匹配（DRAFT_REVISION_CONFLICT）。"""


class ProfileNotFound(ClientStoreError):
    """客户档案不存在。HTTP 层据此映射 404 CLIENT_PROFILE_NOT_FOUND。"""


class InvalidIdentifier(ClientStoreError):
    """标识符形态非法（点段、绝对路径、大小写或长度不符契约）。

    与「不存在」区分开：前者是调用方输入非法（400），后者是资源缺失（404）。
    """


class SnapshotIntegrityError(ClientStoreError):
    """快照完整性校验失败（SNAPSHOT_INTEGRITY_FAILED）。"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


#: 证据 ID 形态由 `governance-evidence-v1` 冻结（其 evidenceReference.evidence_id）。
#: 在**记录时**即校验：非法 ID 会让规则永远无法发布，早报比等到发布才报好
#: （此前只由快照 schema 在发布时兜住，而那个校验此前根本没接线）。
_EVIDENCE_ID_RE = re.compile(r"^ev_[a-z0-9][a-z0-9_-]{7,95}$")
#: 公开别名：API 层需要在调用前做**字段级**校验（CR-002 要求校验失败时定位到具体字段），
#: 但不得复制这份正则——冻结格式只有这一处来源。
EVIDENCE_ID_PATTERN = _EVIDENCE_ID_RE


def _require_valid_evidence_id(evidence_id: str) -> str:
    if not isinstance(evidence_id, str) or not _EVIDENCE_ID_RE.match(evidence_id):
        raise ClientStoreError(
            f"证据 ID 不符合冻结契约（应为 ev_ 开头、总长 11–99 的小写标识）："
            f"{evidence_id!r}"
        )
    return evidence_id


def _secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, _DIR_MODE)


def _secure_write(path: Path, payload: Mapping[str, Any]) -> None:
    _secure_dir(path.parent)
    tmp = path.parent / f".tmp-{path.name}.{uuid.uuid4().hex[:8]}"
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(tmp, _FILE_MODE)
    os.replace(tmp, path)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ClientStoreError(f"文件不存在: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ClientStoreError(f"文件损坏: {path.name}") from exc


def _with_hash(rule: Mapping[str, Any]) -> Dict[str, Any]:
    body = {k: v for k, v in rule.items() if k != "content_sha256"}
    body["content_sha256"] = models.content_hash(body)
    return body


class ClientRepository:
    """外置 data root 上的客户数据仓库。"""

    def __init__(self, *, data_root: Path) -> None:
        self.data_root = Path(data_root).expanduser().resolve()
        self.clients_root = self.data_root / "clients"
        _secure_dir(self.clients_root)

    # ------------------------------------------------------------------ #
    # 路径
    # ------------------------------------------------------------------ #
    def _resolve_profile_dir(self, profile_id: str) -> Path:
        if not paths.is_safe_profile_id(profile_id):
            raise ClientStoreError(
                f"不安全的 profile ID: {profile_id!r}；只允许小写字母数字与 _-，且必须以字母数字开头。"
            )
        try:
            target = paths.contained_path(self.clients_root, profile_id)
        except paths.PathContractError as exc:
            raise ClientStoreError(str(exc)) from exc
        # 二次校验：resolve 后必须仍在 clients 根内（覆盖符号链接越界）
        if target.exists():
            real = target.resolve()
            if real != self.clients_root and self.clients_root not in real.parents:
                raise ClientStoreError("profile 目录越出 data root，拒绝访问。")
        return target

    def _require_profile_dir(self, profile_id: str) -> Path:
        profile_dir = self._resolve_profile_dir(profile_id)
        if not (profile_dir / "profile.json").is_file():
            # SEC-005：不存在即 fail closed，不退回最近客户
            raise ProfileNotFound(f"客户档案不存在: {profile_id}")
        return profile_dir

    def _require_active_profile_dir(self, profile_id: str) -> Path:
        profile_dir = self._require_profile_dir(profile_id)
        profile = _read_json(profile_dir / "profile.json")
        if profile.get("status") not in ACTIVE_PROFILE_STATUSES:
            raise ClientStoreError(
                f"客户档案状态为 {profile.get('status')!r}，不可写入（DATA-005）。"
            )
        return profile_dir

    # ------------------------------------------------------------------ #
    # Profile
    # ------------------------------------------------------------------ #
    def create_client_profile(
        self, *, client_profile_id: str, display_name: str, actor: str
    ) -> Dict[str, Any]:
        profile_dir = self._resolve_profile_dir(client_profile_id)
        if (profile_dir / "profile.json").is_file():
            raise ClientStoreError(f"客户档案已存在: {client_profile_id}")

        now = _now()
        profile = {
            "schema_version": "1.0",
            "client_profile_id": client_profile_id,
            "display_name": display_name,
            "selection_policy": "explicit",
            "status": "active",
            "revision": 1,
            "created_at": now,
            "updated_at": now,
            "created_by": actor,
            "updated_by": actor,
            "content_sha256": "sha256:" + "0" * 64,
        }
        try:
            validator.validate_client_profile(_with_hash(profile))
        except validator.ValidationError as exc:
            raise InvalidIdentifier(f"档案不符合契约: {exc}") from exc

        _secure_dir(profile_dir)
        _secure_write(profile_dir / "profile.json", _with_hash(profile))
        publisher.empty_active_manifest(client_profile_id)  # 仅供自检
        publisher._atomic_write_json(
            profile_dir / publisher.ACTIVE_MANIFEST_NAME,
            publisher.empty_active_manifest(client_profile_id),
        )
        audit.append_event(profile_dir, event_kind="profile_created", actor=actor,
                           detail={"client_profile_id": client_profile_id})
        return _read_json(profile_dir / "profile.json")

    def get_client_profile(self, profile_id: str) -> Dict[str, Any]:
        profile_dir = self._require_profile_dir(profile_id)
        return _read_json(profile_dir / "profile.json")

    def deactivate_client_profile(self, profile_id: str, *, actor: str) -> Dict[str, Any]:
        profile_dir = self._require_profile_dir(profile_id)
        profile = _read_json(profile_dir / "profile.json")
        profile["status"] = "inactive"
        profile["revision"] = int(profile.get("revision", 1)) + 1
        profile["updated_at"] = _now()
        profile["updated_by"] = actor
        _secure_write(profile_dir / "profile.json", _with_hash(profile))
        audit.append_event(profile_dir, event_kind="profile_deactivated", actor=actor,
                           detail={"client_profile_id": profile_id})
        return _read_json(profile_dir / "profile.json")

    # ------------------------------------------------------------------ #
    # 草稿
    # ------------------------------------------------------------------ #
    def _draft_path(self, profile_dir: Path, rule_id: str) -> Path:
        try:
            return paths.contained_path(profile_dir, "drafts", f"{rule_id}.json")
        except paths.PathContractError as exc:
            raise ClientStoreError(str(exc)) from exc

    def _load_draft_or_none(self, profile_dir: Path, rule_id: str) -> Optional[Dict[str, Any]]:
        path = self._draft_path(profile_dir, rule_id)
        return _read_json(path) if path.is_file() else None

    def get_draft(self, profile_id: str, rule_id: str) -> Optional[Dict[str, Any]]:
        profile_dir = self._require_profile_dir(profile_id)
        return self._load_draft_or_none(profile_dir, rule_id)

    def list_drafts(self, profile_id: str) -> List[Dict[str, Any]]:
        profile_dir = self._require_profile_dir(profile_id)
        drafts_dir = profile_dir / "drafts"
        if not drafts_dir.is_dir():
            return []
        return [
            _read_json(p) for p in sorted(drafts_dir.glob("*.json"))
            if not p.name.startswith(".tmp-")
        ]

    def _validate_rule_for_save(self, profile_id: str, rule: Mapping[str, Any]) -> Dict[str, Any]:
        if rule.get("client_profile_id") != profile_id:
            raise ClientStoreError(
                f"规则归属 {rule.get('client_profile_id')!r} 与目标客户 {profile_id!r} 不一致（CR-008）。"
            )
        try:
            validator.validate_client_rule(rule)
            validator.validate_rule_business(rule)
        except validator.ValidationError:
            raise
        return dict(rule)

    def create_new_rule(
        self, profile_id: str, rule: Mapping[str, Any], *, actor: str
    ) -> Dict[str, Any]:
        """新建规则。已存在同 ID 时拒绝，不覆盖（CR-007）。"""
        profile_dir = self._require_active_profile_dir(profile_id)
        rule_id = str(rule.get("client_rule_id") or "")
        if not rule_id:
            raise ClientStoreError("规则缺少 client_rule_id。")
        if self._load_draft_or_none(profile_dir, rule_id) is not None:
            raise ClientStoreError(f"规则 ID 已存在，拒绝覆盖: {rule_id}")

        # 内容哈希由仓库计算，调用方无需提供：schema 把它列为必需字段，但值只可能由
        # 本层算出——强迫调用方先编一个占位哈希再被覆写，是没有意义的契约摩擦。
        # （`_with_hash` 会把传入值覆盖为真实哈希，故此处先补位再校验。）
        prepared = self._validate_rule_for_save(profile_id, _with_hash(dict(rule)))
        prepared["revision"] = 1
        stored = _with_hash(prepared)
        _secure_write(self._draft_path(profile_dir, rule_id), stored)
        audit.append_event(profile_dir, event_kind="draft_created", actor=actor,
                           detail={"client_rule_id": rule_id, "rule_version": stored.get("version"),
                                     "content_sha256": stored["content_sha256"]})
        return stored

    def save_draft(
        self,
        profile_id: str,
        rule: Mapping[str, Any],
        *,
        expected_revision: int,
        actor: str,
    ) -> Dict[str, Any]:
        """保存草稿。草稿不存在时按新建处理。保存**不**触发发布（RS-HC-004）。"""
        profile_dir = self._require_active_profile_dir(profile_id)
        rule_id = str(rule.get("client_rule_id") or "")
        if not rule_id:
            raise ClientStoreError("规则缺少 client_rule_id。")

        existing = self._load_draft_or_none(profile_dir, rule_id)

        # CR-009：先做并发比较交换——调用方视图过期时不得继续。
        current_revision = int(existing.get("revision", 0)) if existing else 0
        if current_revision != expected_revision:
            raise RevisionConflict(
                f"草稿已被其他操作修改：期望 revision={expected_revision}，"
                f"当前 revision={current_revision}（DRAFT_REVISION_CONFLICT）。"
            )

        # CR-004：已发布规则**不得就地改写**。
        #
        # 原实现把这段挂在 `existing.approval_status == "active"` 之下，而**发布并不会把草稿
        # 置为 active**（active 是快照里那份规则的属性，草稿仍是 regression_passed）——
        # 于是该分支在真实流程里从不触发：实测同一版本号 1.0.0 可被就地改写、标题已变而版本未变。
        # 判定条件改为「该版本号是否已出现在生效快照里」，与草稿状态无关。
        published_versions = self._active_version_set(profile_dir, rule_id)
        incoming_version = str(rule.get("version") or "")
        if published_versions and incoming_version in published_versions:
            raise ClientStoreError(
                f"版本 {incoming_version!r} 已发布，修改已发布规则必须提升版本号（CR-004）："
                "已发布的版本不得就地改写（旧 active 与其哈希必须保持不变）。"
            )

        prepared = self._validate_rule_for_save(profile_id, _with_hash(dict(rule)))
        is_new_version = bool(published_versions) and existing is not None
        if is_new_version:
            # 该规则发布过：本次保存即**新版本草稿**。审批与回归必须**重新走**——
            # LIFE-003/004 要求「缺审批或法律核验不得进入后续状态」；把上一版本的批准
            # 继承到新版本，等于让未经审阅的内容直接可发布。
            # （原实现只在那个不触发的分支里做这件事，等于没做。）
            prepared["approval_status"] = "candidate"
            prepared["activation_status"] = "inactive"
            review = dict(prepared.get("review") or {})
            review.update({
                "lawyer_approval_evidence_id": None, "lawyer_approved_by": None,
                "lawyer_approved_at": None, "legal_check_status": "not_checked",
                "legal_checked_at": None, "regression_evidence_ids": [],
            })
            prepared["review"] = review

        prepared["revision"] = current_revision + 1 if existing else 1
        prepared["updated_at"] = _now()
        prepared["updated_by"] = actor
        stored = _with_hash(prepared)
        _secure_write(self._draft_path(profile_dir, rule_id), stored)
        audit.append_event(profile_dir, event_kind="draft_saved", actor=actor,
                           detail={"client_rule_id": rule_id,
                                     "new_version": is_new_version,
                                     "rule_version": stored.get("version"),
                                     "content_sha256": stored["content_sha256"]})
        return stored

    def delete_draft(
        self, profile_id: str, rule_id: str, *, confirmation: bool, actor: str
    ) -> None:
        profile_dir = self._require_profile_dir(profile_id)
        draft = self._load_draft_or_none(profile_dir, rule_id)
        if draft is None:
            raise ClientStoreError(f"草稿不存在: {rule_id}")
        if not confirmation:
            raise ClientStoreError("删除草稿需要二次确认（CR-005）。")
        if draft.get("approval_status") == "active" or self._is_published(profile_dir, rule_id):
            # CR-006 / ADR-018：已发布规则禁止物理删除
            raise ClientStoreError(
                "已发布规则不得物理删除；请以新快照停用或标记 deprecated（CR-006 / ADR-018）。"
            )
        path = self._draft_path(profile_dir, rule_id)
        path.unlink()
        audit.append_event(profile_dir, event_kind="draft_deleted", actor=actor,
                           detail={"client_rule_id": rule_id, "rule_version": draft.get("version")})

    def _active_version_set(self, profile_dir: Path, rule_id: str) -> set:
        versions = set()
        pub = publisher.Publisher(profile_dir)
        manifest = pub.read_manifest()
        for snapshot_id in {manifest.get("active_snapshot_id"),
                            manifest.get("previous_snapshot_id")}:
            if not snapshot_id:
                continue
            try:
                doc = pub.load_snapshot(snapshot_id)
            except Exception:
                continue
            for rule in doc["rules_doc"].get("rules", []):
                if rule.get("client_rule_id") == rule_id:
                    versions.add(rule.get("version"))
        return versions

    def _is_published(self, profile_dir: Path, rule_id: str) -> bool:
        return bool(self._active_version_set(profile_dir, rule_id))

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #
    def _transition(
        self,
        profile_dir: Path,
        rule_id: str,
        *,
        allowed_from: Sequence[str],
        to_state: str,
        actor: str,
        event_kind: str,
        mutate: Optional[Any] = None,
    ) -> Dict[str, Any]:
        draft = self._load_draft_or_none(profile_dir, rule_id)
        if draft is None:
            raise ClientStoreError(f"规则不存在: {rule_id}")
        current = draft.get("approval_status")
        if current not in allowed_from:
            raise ClientStoreError(
                f"非法状态迁移：{current!r} → {to_state!r}（当前状态不允许该跳转，"
                f"允许来源: {list(allowed_from)}）。"
            )
        updated = dict(draft)
        updated["approval_status"] = to_state
        updated["revision"] = int(draft.get("revision", 1)) + 1
        updated["updated_at"] = _now()
        updated["updated_by"] = actor
        if mutate is not None:
            mutate(updated)
        stored = _with_hash(updated)
        _secure_write(self._draft_path(profile_dir, rule_id), stored)
        audit.append_event(profile_dir, event_kind=event_kind, actor=actor,
                           detail={"client_rule_id": rule_id, "to_state": to_state,
                                     "rule_version": stored.get("version")})
        return stored

    def deprecate_rule(self, profile_id: str, rule_id: str, *, actor: str) -> Dict[str, Any]:
        """停用一条已发布规则（CR-006 / ADR-018）。

        CR-006 写的是「禁止物理删除，**只能新快照停用或 deprecated**」——此前只实现了前半句：
        删除会被拒绝，但**没有任何路径去停用**，用户想退掉一条已发布规则会走进死路。

        本方法只把草稿标为 `deprecated`，**不改任何物理记录**；由于 `publish_snapshot`
        只收录 `PUBLISHABLE_APPROVAL_STATES`（regression_passed / active），
        下一次发布的新快照自然不再包含它——这就是「以新快照停用」。
        在重新发布之前，旧快照仍是当前生效版本，规则也仍然生效。
        """
        profile_dir = self._require_active_profile_dir(profile_id)
        return self._transition(
            profile_dir, rule_id,
            allowed_from=("regression_passed", "active"),
            to_state="deprecated",
            actor=actor, event_kind="deprecation_drafted",
        )

    def submit_rule(self, profile_id: str, rule_id: str, *, actor: str) -> Dict[str, Any]:
        """提交规则进入审批流。提交本身不改变审批状态，只记录事件并递增 revision。"""
        profile_dir = self._require_active_profile_dir(profile_id)
        return self._transition(
            profile_dir, rule_id,
            allowed_from=("candidate", "draft"), to_state="candidate",
            actor=actor, event_kind="submitted",
        )

    def record_lawyer_approval(
        self, profile_id: str, rule_id: str, *, evidence_id: str, actor: str
    ) -> Dict[str, Any]:
        _require_valid_evidence_id(evidence_id)
        profile_dir = self._require_active_profile_dir(profile_id)

        def _mutate(rule: Dict[str, Any]) -> None:
            review = dict(rule.get("review") or {})
            review.update({
                "lawyer_approval_evidence_id": evidence_id,
                "lawyer_approved_by": actor,
                "lawyer_approved_at": _now(),
                "legal_check_status": "checked",
                "legal_checked_at": _now(),
            })
            rule["review"] = review

        return self._transition(
            profile_dir, rule_id,
            allowed_from=("candidate",), to_state="lawyer_approved",
            actor=actor, event_kind="lawyer_approved", mutate=_mutate,
        )

    def record_regression_result(
        self, profile_id: str, rule_id: str, *,
        evidence_id: str, passed: bool, actor: str,
    ) -> Dict[str, Any]:
        _require_valid_evidence_id(evidence_id)
        profile_dir = self._require_active_profile_dir(profile_id)
        draft = self._load_draft_or_none(profile_dir, rule_id)
        if draft is None:
            raise ClientStoreError(f"规则不存在: {rule_id}")
        review = draft.get("review") or {}
        if not review.get("lawyer_approval_evidence_id"):
            # LIFE-003：缺审批不得进入后续状态
            raise ClientStoreError("缺少律师批准证据，不得记录回归结果（LIFE-003）。")
        if draft.get("approval_status") != "lawyer_approved":
            raise ClientStoreError(
                f"当前状态 {draft.get('approval_status')!r} 不允许记录回归结果。"
            )
        if not passed:
            audit.append_event(profile_dir, event_kind="regression_recorded", actor=actor,
                               result="failed",
                               detail={"client_rule_id": rule_id, "evidence_id": evidence_id,
                                         "rule_version": draft.get("version")})
            raise ClientStoreError("回归未通过，不允许发布（LIFE-004）。")

        def _mutate(rule: Dict[str, Any]) -> None:
            rev = dict(rule.get("review") or {})
            rev["regression_evidence_ids"] = list(rev.get("regression_evidence_ids") or []) + [evidence_id]
            rule["review"] = rev

        return self._transition(
            profile_dir, rule_id,
            allowed_from=("lawyer_approved",), to_state="regression_passed",
            actor=actor, event_kind="regression_recorded", mutate=_mutate,
        )

    # ------------------------------------------------------------------ #
    # 发布 / 回滚 / 读取
    # ------------------------------------------------------------------ #
    def publish_snapshot(
        self, profile_id: str, *,
        expected_active_snapshot: Optional[str],
        confirmation: bool,
        actor: str,
        enforce_single_active_version: bool = False,
        public_snapshot_id: str = "public_sha256_" + "0" * 64,
        public_asset_fingerprint: str = "sha256:" + "0" * 64,
        resolver_semantics_version: str = "0.1.0",
    ) -> Dict[str, Any]:
        if not confirmation:
            raise ClientStoreError("发布需要显式二次确认（RS-HC-004）。")
        profile_dir = self._require_active_profile_dir(profile_id)
        pub = publisher.Publisher(profile_dir)

        drafts = self.list_drafts(profile_id)
        rules = []
        for draft in drafts:
            if draft.get("approval_status") not in PUBLISHABLE_APPROVAL_STATES:
                continue
            rule = dict(draft)
            rule["approval_status"] = "active"
            rule["activation_status"] = "active"
            rules.append(_with_hash(rule))

        if not rules:
            # 「没有可发布的规则」有两种截然不同的情形，原先一律拒绝，于是把第二种误伤了：
            #
            #   (a) 规则都被**停用**了（或本就没有规则）——这是合法的「以空快照停用」。
            #       CR-006 明确要求「禁止物理删除，**只能新快照停用**」；若这里也拒绝，
            #       **最后一条已发布规则将永远无法停用**——契约要求的能力被守卫堵死。
            #   (b) 有规则但都还没走完审批/回归——用户多半以为它们会被发布，
            #       这时必须拒绝并**指名**是哪些，否则会出现「按了发布却什么都没发布」的静默结果
            #       （LIFE-002 / LIFE-004 的本意）。
            pending = [d for d in drafts
                       if d.get("approval_status") not in PUBLISHABLE_APPROVAL_STATES
                       and d.get("approval_status") != "deprecated"]
            if pending:
                raise ClientStoreError(
                    "以下规则尚未完成律师批准与回归，不能发布（LIFE-002 / LIFE-004）："
                    + "、".join(str(d.get("client_rule_id")) for d in pending)
                )

        # 部分发布时，**如实回报哪些草稿没有被包含**。
        # 此前只在「一条可发布的都没有」时提示；混合情形（1 条已批准 + 1 条仍 candidate）
        # 会静默丢弃后者——不在生效集合、不在 excluded_rules、无冲突、无人工确认，
        # 用户看到的是「发布成功」却不知道少了一条。发布本身应当成功（发布已就绪的规则
        # 是正当流程），但结果不得静默。
        skipped = [
            {"client_rule_id": d.get("client_rule_id"),
             "approval_status": d.get("approval_status"),
             "reason": "尚未完成律师批准与回归" if d.get("approval_status") != "deprecated"
                       else "已停用"}
            for d in drafts
            if d.get("approval_status") not in PUBLISHABLE_APPROVAL_STATES
        ]

        if enforce_single_active_version:
            try:
                validator.ensure_single_active_version(rules)
            except validator.ValidationError as exc:
                raise ClientStoreError(str(exc)) from exc

        evidence_refs = [
            {"relative_path": f"clients/{profile_id}/drafts/{r['client_rule_id']}.json",
             "sha256": r["content_sha256"].removeprefix("sha256:"),
             "media_type": "application/json"}
            for r in rules
        ]

        try:
            snapshot = pub.publish(
                client_profile_id=profile_id,
                rules=rules,
                evidence_refs=evidence_refs,
                public_snapshot_id=public_snapshot_id,
                public_asset_fingerprint=public_asset_fingerprint,
                resolver_semantics_version=resolver_semantics_version,
                expected_active_snapshot=expected_active_snapshot,
                actor=actor,
            )
        except publisher.PublishError as exc:
            raise ClientStoreError(str(exc)) from exc

        # 把未包含的草稿随结果一并回报（见上文：混合发布不得静默丢弃）
        snapshot["skipped_drafts"] = skipped
        return snapshot

    def publish_empty_snapshot(self, profile_id: str, *, actor: str) -> Dict[str, Any]:
        """发布一个空快照（用于演示与基线）。"""
        profile_dir = self._require_active_profile_dir(profile_id)
        pub = publisher.Publisher(profile_dir)
        try:
            return pub.publish(
                client_profile_id=profile_id,
                rules=[],
                evidence_refs=[],
                public_snapshot_id="public_sha256_" + "0" * 64,
                public_asset_fingerprint="sha256:" + "0" * 64,
                resolver_semantics_version="0.1.0",
                expected_active_snapshot=pub.read_manifest().get("active_snapshot_id"),
                actor=actor,
            )
        except publisher.PublishError as exc:
            raise ClientStoreError(str(exc)) from exc

    def load_active_snapshot(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """返回当前生效快照的 manifest；未发布时返回 None。"""
        profile_dir = self._require_profile_dir(profile_id)
        pub = publisher.Publisher(profile_dir)
        manifest = pub.read_manifest()
        snapshot_id = manifest.get("active_snapshot_id")
        if not snapshot_id:
            return None
        try:
            return pub.load_snapshot(snapshot_id)["manifest"]
        except publisher.PublishError as exc:
            raise SnapshotIntegrityError(str(exc)) from exc

    def load_snapshot(self, profile_id: str, snapshot_id: str) -> Dict[str, Any]:
        profile_dir = self._require_profile_dir(profile_id)
        pub = publisher.Publisher(profile_dir)
        try:
            doc = pub.load_snapshot(snapshot_id)
        except publisher.PublishError as exc:
            raise SnapshotIntegrityError(str(exc)) from exc
        return doc["manifest"]

    def rollback_snapshot(
        self, profile_id: str, *,
        target_snapshot: str, expected_active_snapshot: Optional[str], actor: str,
    ) -> Dict[str, Any]:
        profile_dir = self._require_profile_dir(profile_id)
        pub = publisher.Publisher(profile_dir)
        try:
            return pub.rollback(
                target_snapshot=target_snapshot,
                expected_active_snapshot=expected_active_snapshot,
                actor=actor,
            )
        except publisher.PublishError as exc:
            raise ClientStoreError(str(exc)) from exc

    def recover_pending_commits(self, profile_id: str) -> bool:
        profile_dir = self._require_profile_dir(profile_id)
        return publisher.Publisher(profile_dir).recover_pending_commits()

    def list_audit_events(self, profile_id: str) -> List[Dict[str, Any]]:
        profile_dir = self._require_profile_dir(profile_id)
        return audit.list_events(profile_dir)
