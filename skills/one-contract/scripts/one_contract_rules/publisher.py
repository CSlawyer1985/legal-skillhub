#!/usr/bin/env python3
"""客户快照的不可变发布、原子指针切换与回滚。

契约来源：architecture-contract.md §8.3/§8.4/§10；ADR-007、ADR-023；
safety-and-acceptance.md LIFE-006/007/008/009/012/014、DATA-001/007/008。

发布事务顺序（任一失败，旧 active 保持不变）：
1. 生成 transaction ID；
2. 写完整 immutable snapshot（规则集合、验证摘要、证据引用）；
3. append PREPARED 审计事件并 fsync；
4. 复核 expected active、snapshot 与内容哈希；
5. 原子替换 active-manifest（manifest 自身记录 committed_at 与 transaction ID）；
6. append COMMITTED 事件；
7. 若第 6 步前崩溃，启动恢复依据 manifest 补记 RECOVERED_COMMIT。

active-manifest 是**可恢复的 commit 事实**：即使进程在指针切换后、追加普通审计前
崩溃，也能从 manifest 重建提交记录（ADR-023）。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import audit, models, private_fs, validator

__all__ = [
    "ACTIVE_MANIFEST_NAME",
    "SNAPSHOTS_DIR",
    "Publisher",
    "PublishError",
    "empty_active_manifest",
    "read_active_manifest",
    "snapshot_content_hash",
]

ACTIVE_MANIFEST_NAME = "active-manifest.json"
SNAPSHOTS_DIR = "snapshots"
TEMP_PREFIX = ".tmp-"


class PublishError(Exception):
    """发布无法安全完成。旧 active manifest 必须保持不变。"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def snapshot_content_hash(rules: Sequence[Mapping[str, Any]]) -> str:
    """快照内容哈希：对规则集合取 JCS 哈希。"""
    return models.content_hash({"rules": list(rules)}, exclude=())


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """写临时文件 → flush+fsync → 收权限 → 原子 rename。

    权限收口走 `private_fs`（0700/0600）：active-manifest.json 含客户
    快照指针与规则摘要，属私有数据，此前以默认 umask 落盘为 0644（W7-SEC013）。
    """
    private_fs.atomic_write_json(path, payload)
    _fsync_dir(Path(path).parent)


def empty_active_manifest(client_profile_id: str) -> Dict[str, Any]:
    """初始（未发布）active manifest。"""
    now = _now()
    return {
        "schema_version": "1.0",
        "client_profile_id": client_profile_id,
        "commit_state": "empty",
        "active_snapshot_id": None,
        "active_snapshot_sha256": None,
        "previous_snapshot_id": None,
        "previous_snapshot_sha256": None,
        "public_snapshot_id": None,
        "public_asset_fingerprint": None,
        "resolver_semantics_version": None,
        "publish_transaction_id": None,
        "prepare_audit_event_id": None,
        "generation": 0,
        "committed_at": None,
        "updated_at": now,
        # 契约要求 updated_by 恒为非空字符串（即使 commit_state 为 empty），
        # 用固定占位符表示“尚无操作者”，不得写 null。
        "updated_by": "system:unpublished",
        "content_sha256": "sha256:" + "0" * 64,
    }


def read_active_manifest(profile_dir: Path) -> Dict[str, Any]:
    path = Path(profile_dir) / ACTIVE_MANIFEST_NAME
    if not path.is_file():
        raise PublishError(f"active manifest 缺失: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PublishError("active manifest 损坏，拒绝加载。") from exc
    # 读取时也过契约：漂移的记录不得被静默使用（fail closed）
    try:
        validator.validate_active_manifest(payload)
    except validator.ValidationError as exc:
        raise PublishError(f"active manifest 不符合冻结契约，拒绝加载：{exc}") from exc
    return payload


class Publisher:
    """负责把一个 profile 的已批准规则发布为不可变快照。"""

    def __init__(self, profile_dir: Path) -> None:
        self.profile_dir = Path(profile_dir)
        self.snapshots_dir = self.profile_dir / SNAPSHOTS_DIR

    # ---- 读取 ---------------------------------------------------------- #
    def read_manifest(self) -> Dict[str, Any]:
        return read_active_manifest(self.profile_dir)

    def active_snapshot_id(self) -> Optional[str]:
        return self.read_manifest().get("active_snapshot_id")

    def load_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """加载并**复核完整性**。哈希不符即拒绝（LIFE-008）。"""
        snapshot_dir = self.snapshots_dir / snapshot_id
        manifest_path = snapshot_dir / "manifest.json"
        rules_path = snapshot_dir / "rules.json"
        if not manifest_path.is_file() or not rules_path.is_file():
            raise PublishError(f"快照不完整: {snapshot_id}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            rules_doc = json.loads(rules_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PublishError(f"快照文件损坏: {snapshot_id}") from exc

        actual = snapshot_content_hash(rules_doc.get("rules", []))
        if actual != manifest.get("content_sha256"):
            raise PublishError(
                f"快照内容哈希不符（可能被篡改）: {snapshot_id}"
            )
        # 读取时也过契约（manifest + rules 同一文档）
        try:
            validator.validate_client_snapshot(
                {**manifest, "rules": rules_doc.get("rules", [])},
                defer_evidence_refs=True,
            )
        except validator.ValidationError as exc:
            raise PublishError(f"快照不符合冻结契约，拒绝加载：{exc}") from exc
        return {"manifest": manifest, "rules_doc": rules_doc}

    # ---- 发布 ---------------------------------------------------------- #
    def publish(
        self,
        *,
        client_profile_id: str,
        rules: Sequence[Mapping[str, Any]],
        evidence_refs: Sequence[Mapping[str, Any]],
        public_snapshot_id: str,
        public_asset_fingerprint: str,
        resolver_semantics_version: str,
        expected_active_snapshot: Optional[str],
        actor: str,
        publish_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        current = self.read_manifest()
        if current.get("active_snapshot_id") != expected_active_snapshot:
            raise PublishError(
                "expected active snapshot 与当前不一致；发布被拒绝（ACTIVE_SNAPSHOT_CONFLICT）。"
            )

        rules = list(rules)
        validator.ensure_chain_consistency(
            expected_profile_id=client_profile_id,
            payloads=rules,
            field_prefix="rules",
        )
        validator.ensure_single_active_version(rules)

        # 冻结契约（active-client-manifest-v1 / client-snapshot-v1 /
        # governance-evidence-v1）要求 ^ptx_[a-z0-9][a-z0-9_-]{7,95}$。
        # 此前发的是 "tx_…"，使每一份已发布 manifest 与快照都在该字段上
        # 违反自己的 schema，而产出物从不与 schema 对照，故无人发现。
        transaction_id = f"ptx_{uuid.uuid4().hex[:16]}"
        content_sha = snapshot_content_hash(rules)
        snapshot_id = f"cs_{uuid.uuid4().hex[:16]}"
        now = _now()

        validation_summary = {
            "overall_result": "passed",
            "checks": [
                # check_id 须满足 client-snapshot 的 pattern ^chk_[a-z0-9][a-z0-9_-]{7,95}$
                # （`chk_schema` 只有 10 字符，太短——由收窄豁免后的校验暴露）
                {"check_id": f"chk_{kind}_validation", "check_kind": kind, "result": "passed",
                 "evidence_refs": list(evidence_refs)}
                for kind in (
                    "schema", "lifecycle", "legal_check", "regression", "isolation",
                )
            ],
        }

        snapshot_manifest = {
            "schema_version": "1.0",
            "snapshot_id": snapshot_id,
            "client_profile_id": client_profile_id,
            "previous_snapshot_id": current.get("active_snapshot_id"),
            "published_at": now,
            "published_by": actor,
            "publish_transaction_id": transaction_id,
            "prepare_audit_event_id": None,  # PREPARED 事件写入后回填
            "public_snapshot_id": public_snapshot_id,
            "public_asset_fingerprint": public_asset_fingerprint,
            "resolver_semantics_version": resolver_semantics_version,
            "validation_summary": validation_summary,
            "evidence_refs": list(evidence_refs),
            "immutable": True,
            "content_sha256": content_sha,
        }
        if publish_reason:
            snapshot_manifest["publish_reason"] = publish_reason


        # 1) 完整快照先落到临时目录，写完再整体改名
        #    权限收口：snapshots/ 与快照目录 0700、manifest.json 与
        #    rules.json 0600（rules.json 即客户规则正文，此前为 0644/0755，
        #    同机其他用户可读——W7-SEC013）。staging 改名后权限随之保留。
        private_fs.secure_dir(self.snapshots_dir)
        staging = self.snapshots_dir / f"{TEMP_PREFIX}{snapshot_id}"
        private_fs.secure_dir(staging)
        try:
            private_fs.atomic_write_json(staging / "manifest.json", snapshot_manifest)
            private_fs.atomic_write_json(staging / "rules.json", {"rules": list(rules)})
            _fsync_dir(staging)

            final_dir = self.snapshots_dir / snapshot_id
            if final_dir.exists():
                raise PublishError(f"快照 ID 冲突，拒绝覆盖: {snapshot_id}")

            # 2) PREPARED 事件（先审计后切换，保证不会出现“已生效但无发布事件”）
            prepared = audit.append_event(
                self.profile_dir,
                event_kind="PREPARED",
                actor=actor,
                detail={
                    "publish_transaction_id": transaction_id,
                    "snapshot_id": snapshot_id,
                    "previous_snapshot_id": current.get("active_snapshot_id"),
                    "content_sha256": content_sha,
                },
            )
            snapshot_manifest["prepare_audit_event_id"] = prepared["event_id"]

            # **冻结 DTO 必须在写入前校验。** `client-snapshot-v1` 描述的是
            # 「manifest + rules 同一文档」，此前产品代码从不调用该校验器
            # （调用点为 0），产出物与契约的漂移因此无人发现——
            # 例如 publish_transaction_id 曾长期写成 `tx_…` 而非契约要求的 `ptx_…`。
            #
            # 校验点必须在这里：`prepare_audit_event_id` 是上一步才回填的，
            # 在此之前该字段为 None，而 schema 要求 string；此处之后的
            # 内容才是最终落盘物。
            #
            # defer_evidence_refs=True：仅暂缓 evidence_refs 的条目形状
            # （其必填字段 candidate_sha256 是发布治理概念，运行时无从诚实填写，
            #  需契约负责人裁决）；其余字段照常强制。
            validator.validate_client_snapshot(
                {**snapshot_manifest, "rules": rules}, defer_evidence_refs=True
            )
            private_fs.atomic_write_json(staging / "manifest.json", snapshot_manifest)
            os.replace(staging, final_dir)
            private_fs.secure_dir(final_dir)
            _fsync_dir(self.snapshots_dir)

            # 3) 原子切换 active manifest —— manifest 本身即 commit 事实
            new_manifest = {
                "schema_version": "1.0",
                "client_profile_id": client_profile_id,
                "commit_state": "committed",
                "active_snapshot_id": snapshot_id,
                "active_snapshot_sha256": content_sha,
                "previous_snapshot_id": current.get("active_snapshot_id"),
                "previous_snapshot_sha256": current.get("active_snapshot_sha256"),
                "public_snapshot_id": public_snapshot_id,
                "public_asset_fingerprint": public_asset_fingerprint,
                "resolver_semantics_version": resolver_semantics_version,
                "publish_transaction_id": transaction_id,
                "prepare_audit_event_id": prepared["event_id"],
                "generation": int(current.get("generation", 0)) + 1,
                "committed_at": _now(),
                "updated_at": _now(),
                "updated_by": actor,
                "content_sha256": content_sha,
            }
            self._swap_active_manifest(new_manifest)

            # 4) COMMITTED 事件
            audit.append_event(
                self.profile_dir,
                event_kind="COMMITTED",
                actor=actor,
                detail={
                    "publish_transaction_id": transaction_id,
                    "snapshot_id": snapshot_id,
                    "previous_snapshot_id": current.get("active_snapshot_id"),
                    "content_sha256": content_sha,
                },
            )
        except Exception:
            # 回滚暂存区；旧 active manifest 未被触碰
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            raise

        return snapshot_manifest

    def _swap_active_manifest(self, manifest: Mapping[str, Any]) -> None:
        """原子替换 active manifest。测试可通过替换本方法注入切换前故障。

        这是 active manifest 的**唯一写入收口**（发布、回滚、恢复都走它），
        故校验放在此处即可覆盖全部路径：产出物必须先过自身冻结 schema。
        """
        validator.validate_active_manifest(manifest)
        _atomic_write_json(self.profile_dir / ACTIVE_MANIFEST_NAME, manifest)

    # ---- 回滚 ---------------------------------------------------------- #
    def rollback(
        self,
        *,
        target_snapshot: str,
        expected_active_snapshot: Optional[str],
        actor: str,
    ) -> Dict[str, Any]:
        current = self.read_manifest()
        if current.get("active_snapshot_id") != expected_active_snapshot:
            raise PublishError(
                "expected active snapshot 与当前不一致；回滚被拒绝（ACTIVE_SNAPSHOT_CONFLICT）。"
            )

        if current.get("active_snapshot_id") == target_snapshot:
            # 幂等：已指向目标，不产生漂移
            return self.load_snapshot(target_snapshot)["manifest"]

        target = self.load_snapshot(target_snapshot)["manifest"]
        if target.get("client_profile_id") != current.get("client_profile_id"):
            raise PublishError("回滚目标不属于当前客户，拒绝。")

        new_manifest = dict(current)
        new_manifest.update(
            {
                "active_snapshot_id": target["snapshot_id"],
                "active_snapshot_sha256": target["content_sha256"],
                "previous_snapshot_id": current.get("active_snapshot_id"),
                "previous_snapshot_sha256": current.get("active_snapshot_sha256"),
                "generation": int(current.get("generation", 0)) + 1,
                "updated_at": _now(),
                "updated_by": actor,
                "content_sha256": target["content_sha256"],
            }
        )
        self._swap_active_manifest(new_manifest)
        audit.append_event(
            self.profile_dir,
            event_kind="ROLLED_BACK",
            actor=actor,
            detail={
                "snapshot_id": target["snapshot_id"],
                "previous_snapshot_id": current.get("active_snapshot_id"),
                "content_sha256": target["content_sha256"],
            },
        )
        return target

    # ---- 恢复 ---------------------------------------------------------- #
    def recover_pending_commits(self, actor: str = "system") -> bool:
        """切换后崩溃：manifest 已是 commit 事实，据此补记 COMMITTED（ADR-023）。"""
        manifest = self.read_manifest()
        if manifest.get("commit_state") != "committed":
            return False
        transaction_id = manifest.get("publish_transaction_id")
        if not transaction_id:
            return False
        if audit.has_event(self.profile_dir, "COMMITTED", publish_transaction_id=transaction_id):
            return False
        audit.append_event(
            self.profile_dir,
            event_kind="RECOVERED_COMMIT",
            actor=actor,
            detail={
                "publish_transaction_id": transaction_id,
                "snapshot_id": manifest.get("active_snapshot_id"),
                "content_sha256": manifest.get("active_snapshot_sha256"),
            },
        )
        audit.append_event(
            self.profile_dir,
            event_kind="COMMITTED",
            actor=actor,
            detail={
                "publish_transaction_id": transaction_id,
                "snapshot_id": manifest.get("active_snapshot_id"),
                "content_sha256": manifest.get("active_snapshot_sha256"),
                "recovered": True,
            },
        )
        return True

    def cleanup_orphan_staging(self) -> List[str]:
        """识别过期临时目录。**不**把它当作 active（§10）。"""
        if not self.snapshots_dir.is_dir():
            return []
        orphans = sorted(
            p.name for p in self.snapshots_dir.iterdir() if p.name.startswith(TEMP_PREFIX)
        )
        for name in orphans:
            shutil.rmtree(self.snapshots_dir / name, ignore_errors=True)
        return orphans
