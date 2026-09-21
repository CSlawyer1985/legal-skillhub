#!/usr/bin/env python3
"""客户规则的审计日志。

契约来源：architecture-contract.md §8（数据模型）、§10（发布事务顺序）；
safety-and-acceptance.md LIFE-011（审计字段）、DATA-007（发布与审计崩溃窗口）。

要点：
- 追加写 JSONL，每条一次 fsync，保证崩溃前已落盘；
- 发布事务依赖 PREPARED / COMMITTED 两个事件，manifest 是 commit 的可恢复事实；
- 日志只写 ID、快照、错误码与最小诊断信息，**不写完整客户规则正文**（§7 本地服务安全）。
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from . import private_fs

__all__ = [
    "EVENT_KINDS",
    "append_event",
    "audit_log_path",
    "list_events",
    "new_event_id",
]

#: 允许的事件种类。新增种类必须在此登记，避免审计里出现自由文本。
EVENT_KINDS = (
    "profile_created",
    "profile_updated",
    "profile_deactivated",
    "draft_saved",
    "draft_created",
    "draft_deleted",
    "submitted",
    "lawyer_approved",
    "regression_recorded",
    "deprecation_drafted",
    "PREPARED",
    "COMMITTED",
    "RECOVERED_COMMIT",
    "ABORTED",
    "ROLLED_BACK",
)


class AuditError(Exception):
    """审计写入或读取失败。发布流程必须因此中止。"""


def new_event_id() -> str:
    return f"ev_{uuid.uuid4().hex[:16]}"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit_log_path(profile_dir: Path) -> Path:
    return Path(profile_dir) / "audit" / "events.jsonl"


def append_event(
    profile_dir: Path,
    *,
    event_kind: str,
    actor: str,
    result: str = "ok",
    detail: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """追加一条审计事件并 fsync。返回写入的事件。"""
    if event_kind not in EVENT_KINDS:
        raise AuditError(f"未登记的审计事件类型: {event_kind!r}")

    event: Dict[str, Any] = {
        "event_id": new_event_id(),
        "event_kind": event_kind,
        "actor": actor,
        "recorded_at": _now(),
        "result": result,
    }
    if detail:
        # 只保存结构化标识与哈希，调用方不得传入规则正文
        event.update({k: v for k, v in detail.items() if v is not None})

    # 权限收口走 private_fs：审计记录含发布/回滚/审批轨迹，属私有数据，
    # 此前目录 0755、文件 0644（W7-SEC013）。每次追加都重设权限，
    # 顺带修正早期版本留下的宽松权限文件。
    path = audit_log_path(profile_dir)
    private_fs.secure_append_line(
        path, json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
    )
    return event


def list_events(profile_dir: Path) -> List[Dict[str, Any]]:
    """按写入顺序读取全部事件。损坏行直接报错，不静默跳过。"""
    path = audit_log_path(profile_dir)
    if not path.is_file():
        return []
    events: List[Dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AuditError(f"审计日志第 {line_no} 行损坏，拒绝继续。") from exc
    return events


def has_event(profile_dir: Path, event_kind: str, **match: Any) -> bool:
    for event in list_events(profile_dir):
        if event.get("event_kind") != event_kind:
            continue
        if all(event.get(k) == v for k, v in match.items()):
            return True
    return False
