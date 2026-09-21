#!/usr/bin/env python3
"""公共规则的提案式维护（proposal store）。

契约来源：ADR-003（公共修改采用 proposal）、ADR-002（公共 active 只读）、
architecture-contract.md §4（proposal 路由与错误码）、RS-HC-001；
public-rule-proposal-v1.schema.json（冻结契约）。

硬边界（本模块的核心价值就在这些"不做"上）：
- **绝不原地修改公共 active 资产**：proposal 是独立工作区的独立文件；
- **绝不进入 runtime**：resolver 与 PublicRepository 都不引用本模块；
- **没有跳过审批直接激活的 API**：不存在 activate/apply/publish/promote 方法；
- 即使 proposal 走到 `accepted`，也只是一种记录状态，公共资产仍然零改动
  ——正式晋级属知识治理流程（2.9.x），不在本包。
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import models, paths, registry

__all__ = [
    "NEXT_STATUS",
    "PROPOSAL_STATUSES",
    "ProposalError",
    "ProposalRepository",
]

#: 提案状态机。只允许逐级向前或转 rejected（终态）。
PROPOSAL_STATUSES: Tuple[str, ...] = (
    "candidate", "lawyer_approved", "regression_passed", "accepted", "rejected", "deprecated",
)

NEXT_STATUS: Mapping[str, Tuple[str, ...]] = {
    "candidate": ("lawyer_approved", "rejected"),
    "lawyer_approved": ("regression_passed", "rejected"),
    "regression_passed": ("accepted", "rejected"),
    "accepted": (),
    "rejected": (),
    "deprecated": (),
}

_DIR_MODE = 0o700
_FILE_MODE = 0o600

#: 晋级链路各阶段需跑的回归项（PROP-006 要求导出含测试清单）。
_REGRESSION_CHECKLIST: Tuple[Mapping[str, str], ...] = (
    {"check_id": "public_hash", "description": "公共资产前后 SHA-256 必须一致"},
    {"check_id": "selector_equivalence", "description": "与 2.8.1 选择器结果逐条等价"},
    {"check_id": "resolver_golden", "description": "解析 golden 用例全通过"},
    {"check_id": "hard_boundary", "description": "硬边界用例未被绕过"},
    {"check_id": "export_privacy", "description": "公开包隐私扫描零命中"},
)


class ProposalError(Exception):
    """提案操作失败。调用方不得降级为部分写入。"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _with_hash(payload: Mapping[str, Any]) -> Dict[str, Any]:
    body = {k: v for k, v in payload.items() if k != "content_sha256"}
    body["content_sha256"] = models.content_hash(body)
    return body


def _secure_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, _DIR_MODE)
    tmp = path.parent / f".tmp-{path.name}.{uuid.uuid4().hex[:8]}"
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(tmp, _FILE_MODE)
    os.replace(tmp, path)


@dataclass
class ProposalRepository:
    """外部 data root 上的提案仓库。

    注意：本类**故意不提供**任何 activate / apply / publish / promote 方法。
    晋级到公共资产属知识治理流程，不在 Rule Studio 内。
    """

    data_root: Path
    public_repository: Any

    def __post_init__(self) -> None:
        self.data_root = Path(self.data_root).expanduser().resolve()
        self.root = self.data_root / "public-proposals"
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, _DIR_MODE)

    # ------------------------------------------------------------------ #
    # 创建
    # ------------------------------------------------------------------ #
    def create_proposal(
        self,
        *,
        operation: str,
        layer: str,
        target_rule_id: Optional[str],
        title: str,
        rationale: str,
        source_refs: Sequence[str],
        proposed_rule: Optional[Mapping[str, Any]],
        actor: str,
    ) -> Dict[str, Any]:
        if operation not in ("create", "supersede", "deprecate"):
            raise ProposalError(f"未支持的提案操作: {operation!r}")
        if layer not in ("global", "domain", "type"):
            raise ProposalError(f"未支持的层级: {layer!r}")
        if not title or not rationale:
            raise ProposalError("提案必须包含 title 与 rationale。")

        # create 不得指向既有规则；其余操作必须指向既有 active 规则
        if operation == "create":
            if target_rule_id:
                raise ProposalError("create 提案不得携带 target_rule_id。")
        else:
            if not target_rule_id:
                raise ProposalError(f"{operation} 提案必须指定 target_rule_id。")
            if self.public_repository.get_rule(target_rule_id) is None:
                raise ProposalError(
                    f"目标规则不存在于公共知识: {target_rule_id!r}；"
                    "不得对不存在的规则提出修改。"
                )

        proposal = {
            "schema_version": "1.0",
            "proposal_id": f"pr_{uuid.uuid4().hex[:12]}",
            "operation": operation,
            "layer": layer,
            "target_rule_id": target_rule_id,
            "base_public_fingerprint": self.public_repository.public_asset_fingerprint,
            "title": title,
            "rationale": rationale,
            "source_refs": list(source_refs),
            "proposed_rule": dict(proposed_rule) if proposed_rule is not None else None,
            "impact": {
                # 契约要求四个必填字段；human_review_required 恒为 true
                # ——公共规则晋级必须经人工复核，不得自动化。
                "affected_rule_ids": [target_rule_id] if target_rule_id else [],
                "affected_type_ids": self._affected_type_ids(target_rule_id),
                "required_regression_ids": [c["check_id"] for c in _REGRESSION_CHECKLIST],
                "human_review_required": True,
                "impact_note": f"{operation} 提案；运行时不生效，须经知识治理流程晋级。",
            },
            "status": "candidate",
            "created_at": _now(),
            "created_by": actor,
            "content_sha256": "sha256:" + "0" * 64,
        }
        stored = _with_hash(proposal)
        self._validate(stored)
        self._write(stored)
        self._audit(stored["proposal_id"], "proposal_created", actor,
                    detail={"operation": operation, "layer": layer})
        return stored

    def _affected_type_ids(self, target_rule_id: Optional[str]) -> List[str]:
        """受影响的具体类型。委派给公共索引，不在本模块推导规则语义。"""
        if not target_rule_id:
            return []
        node = self.public_repository.get_rule(target_rule_id)
        if node is None:
            return []
        return sorted(set(node.type_ids))

    def _validate(self, proposal: Mapping[str, Any]) -> None:
        validator = registry.make_validator(
            "one-contract/public-rule-proposal-v1.schema.json"
        )
        errors = sorted(validator.iter_errors(proposal), key=lambda e: list(e.path))
        if errors:
            first = errors[0]
            raise ProposalError(
                f"提案不符合公共契约: {'.'.join(str(p) for p in first.path)}: {first.message}"
            )

    # ------------------------------------------------------------------ #
    # 读写
    # ------------------------------------------------------------------ #
    def _proposal_path(self, proposal_id: str) -> Path:
        try:
            return paths.contained_path(self.root, f"{proposal_id}.json")
        except paths.PathContractError as exc:
            raise ProposalError(str(exc)) from exc

    def _write(self, proposal: Mapping[str, Any]) -> None:
        _secure_write(self._proposal_path(str(proposal["proposal_id"])), proposal)

    def get_proposal(self, proposal_id: str) -> Dict[str, Any]:
        path = self._proposal_path(proposal_id)
        if not path.is_file():
            raise ProposalError(f"提案不存在: {proposal_id}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ProposalError(f"提案文件损坏: {proposal_id}") from exc

    def list_proposals(
        self, *, status: Optional[str] = None, layer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for path in sorted(self.root.glob("pr_*.json")):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if status and item.get("status") != status:
                continue
            if layer and item.get("layer") != layer:
                continue
            out.append(item)
        return out

    # ------------------------------------------------------------------ #
    # 状态机
    # ------------------------------------------------------------------ #
    def transition(self, proposal_id: str, *, to_status: str, actor: str,
                   note: Optional[str] = None) -> Dict[str, Any]:
        proposal = self.get_proposal(proposal_id)
        current = proposal.get("status")
        if to_status not in PROPOSAL_STATUSES:
            raise ProposalError(f"未登记的提案状态: {to_status!r}")
        allowed = NEXT_STATUS.get(current, ())
        if to_status not in allowed:
            raise ProposalError(
                f"非法状态迁移：{current!r} → {to_status!r}；"
                f"允许的目标状态: {list(allowed) or '无（终态）'}。"
            )
        updated = dict(proposal)
        updated["status"] = to_status
        stored = _with_hash(updated)
        self._validate(stored)
        self._write(stored)
        self._audit(proposal_id, "proposal_transitioned", actor,
                    detail={"from": current, "to": to_status, "note": note})
        return stored

    # ------------------------------------------------------------------ #
    # 差异
    # ------------------------------------------------------------------ #
    def proposal_diff(
        self,
        *,
        operation: str,
        layer: str,
        target_rule_id: Optional[str],
        proposed_rule: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        current = None
        if target_rule_id:
            node = self.public_repository.get_rule(target_rule_id)
            if node is None:
                raise ProposalError(f"目标规则不存在: {target_rule_id!r}")
            current = {
                "node_id": node.node_id,
                "node_kind": node.node_kind,
                "layer": node.layer,
                "title": node.title,
                "version": node.version,
                "approval_status": node.approval_status,
                "activation_status": node.activation_status,
                "content_hash": node.content_hash,
            }
        else:
            current = None

        proposed = dict(proposed_rule) if proposed_rule is not None else None

        changed: List[str] = []
        if proposed and current:
            for key, value in proposed.items():
                if current.get(key) != value:
                    changed.append(key)
        elif proposed and not current:
            changed = sorted(proposed.keys())

        return {
            "operation": operation,
            "layer": layer,
            "target_rule_id": target_rule_id,
            "current": current,
            "proposed": proposed,
            "changed_fields": sorted(changed),
            "removes_current": operation == "deprecate",
            "effective": False,
        }

    # ------------------------------------------------------------------ #
    # 治理导出
    # ------------------------------------------------------------------ #
    def export_governance_bundle(self, proposal_id: str) -> Dict[str, Any]:
        proposal = self.get_proposal(proposal_id)
        diff = self.proposal_diff(
            operation=str(proposal["operation"]),
            layer=str(proposal["layer"]),
            target_rule_id=proposal.get("target_rule_id"),
            proposed_rule=proposal.get("proposed_rule"),
        )
        bundle = {
            "schema_version": "1.0",
            "proposal": proposal,
            "diff": diff,
            "source_refs": list(proposal.get("source_refs") or ()),
            "rationale": proposal.get("rationale"),
            "impact": dict(proposal.get("impact") or {}),
            "regression_checklist": [dict(c) for c in _REGRESSION_CHECKLIST],
            "status": proposal.get("status"),
            # 导出包始终声明未生效，避免被误当作已发布规则
            "effective": False,
            "exported_at": _now(),
            "exported_by": proposal.get("created_by"),
            "bundle_sha256": "sha256:" + "0" * 64,
        }
        bundle["bundle_sha256"] = models.content_hash(
            bundle, exclude=("bundle_sha256", "exported_at")
        )
        return bundle

    # ------------------------------------------------------------------ #
    # 审计
    # ------------------------------------------------------------------ #
    def _audit_path(self, proposal_id: str) -> Path:
        return paths.contained_path(self.root, proposal_id, "events.jsonl")

    def _audit(self, proposal_id: str, event_kind: str, actor: str,
               detail: Optional[Mapping[str, Any]] = None) -> None:
        path = self._audit_path(proposal_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent, _DIR_MODE)
        event = {
            "event_id": f"ev_{uuid.uuid4().hex[:12]}",
            "proposal_id": proposal_id,
            "event_kind": event_kind,
            "actor": actor,
            "recorded_at": _now(),
            "result": "ok",
        }
        if detail:
            event.update({k: v for k, v in detail.items() if v is not None})
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def list_audit_events(self, proposal_id: str) -> List[Dict[str, Any]]:
        path = self._audit_path(proposal_id)
        if not path.is_file():
            return []
        return [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
