#!/usr/bin/env python3
"""一轮审查的规则解析入口（One-Contract 集成层）。

契约来源：architecture-contract.md §7（解析算法）、§14（兼容与降级边界）、
§3（resolve_effective_rules）；ADR-010（审查任务固定快照）、
ADR-028（降级仅适用于未请求客户规则的公共审查）、INT-001/002/009/010。

两种模式的边界（**本模块最重要的语义**）：

- `client_profile_id is None`：纯公共审查。Rule Studio 不可用时**可以**继续，
  只附一条面板不可用提示，公共选择结果不变（INT-001）。
- `client_profile_id 已给出`：客户模式。snapshot 缺失、损坏、指纹不兼容时
  **fail closed** —— 不加载任何客户规则，返回明确错误码与修复指引，
  **绝不静默退回公共规则**（INT-002 / ADR-028）。此时同时给出公共结果，
  以便用户看清"如改选仅公共规则会得到什么"，但状态必须显式标记为 blocked。

快照固定：一轮审查开始时原子读取并固定公共与客户快照；中途发布只影响下一轮
（ADR-010）。provenance 记录实际使用的快照 ID、规则 ID 与结果哈希（INT-004/009）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

_SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from one_contract_rules import client_repository, models, paths, public_repository, resolver

__all__ = [
    "attach_provenance",
    "resolve",
    "should_auto_activate_client",
    "suggest_client_profile",
]

_API_VERSION = "v1"

#: 客户模式失败时的稳定错误码（与冻结错误码目录一致）
_FAILURE_CODES = {
    "profile_missing": "CLIENT_PROFILE_NOT_FOUND",
    #: 档案存在但非 active：非 active 资产试图生效（DATA-005）。
    #: 与 Core（resolver）保持同一错误码，避免同一情形两条路径报不同码。
    "profile_inactive": "CANDIDATE_NOT_EXECUTABLE",
    "snapshot_missing": "SNAPSHOT_INTEGRITY_FAILED",
    "snapshot_corrupt": "SNAPSHOT_INTEGRITY_FAILED",
    "fingerprint_mismatch": "PUBLIC_SNAPSHOT_MISMATCH",
}

_REMEDIATION = (
    "修复或重新发布该客户快照；或由用户明确改选『仅公共规则』后重跑。"
    "系统不会自行退回公共规则。"
)


def _conflict(code: str, detail: str, **extra: Any) -> Dict[str, Any]:
    payload = {"code": code, "detail": detail, "requires_explicit_choice": True}
    payload.update(extra)
    return payload


def resolve(
    context: Mapping[str, Any],
    *,
    data_root: Path,
    rule_studio_available: bool = True,
    #: 默认 True：已选客户但未显式给快照时，原子读取并固定当时的 active 快照
    #: （INT-010 的规范行为）。此前默认 False 且产品调用方无一处传 True，
    #: 导致该场景默认走 blocked 而非固定快照（W7 独立验证发现的 R0 缺陷）。
    #: 传 False 仅用于"必须显式指定快照"的严格模式。
    allow_implicit_active_snapshot: bool = True,
) -> Dict[str, Any]:
    """解析一轮审查的生效规则。

    返回 `status` 为 `ok` 或 `blocked`。`blocked` 表示**客户模式未成立**，
    调用方不得据此产出"按客户口径审查"的结论。
    """
    root = Path(data_root).expanduser().resolve()
    public = public_repository.PublicRepository()
    clients = client_repository.ClientRepository(data_root=root)
    engine = resolver.Resolver(public_repository=public, client_repository=clients)

    ctx = dict(context)
    profile_id = ctx.get("client_profile_id")
    snapshot_id = ctx.get("client_policy_snapshot_id")
    notices: List[str] = []

    if not rule_studio_available:
        if profile_id is None:
            # 纯公共审查：面板不可用不阻断（INT-001）
            notices.append("panel_unavailable_notice: Rule Studio 面板不可用；已按纯公共规则继续。")
        else:
            notices.append("panel_unavailable_notice: Rule Studio 面板不可用。")

    if profile_id is None:
        result = engine.resolve_effective_rules(ctx)
        payload = result.to_dict()
        payload["client_overlay_active"] = getattr(result, "client_overlay_active", False)
        return {
            "status": "ok",
            "api_version": _API_VERSION,
            "notices": notices,
            "effective_rule_set": payload,
            "provenance": _provenance(public, payload, ctx, client_snapshot=None),
        }

    # ---- 客户模式：先做快照固定与完整性检查，失败即 fail closed ---- #
    failure = _load_client_snapshot(
        clients,
        profile_id=profile_id,
        snapshot_id=snapshot_id,
        expected_fingerprint=public.public_asset_fingerprint,
        allow_implicit_active=allow_implicit_active_snapshot,
    )
    if failure is not None:
        kind, detail = failure
        # 对外只用冻结错误码目录里的码；原始 failure kind 仅作内部诊断字段。
        # （此前直接把 kind 当 code 发出，`_FAILURE_CODES` 从未被使用，
        #  导致同一情形下 Core 与集成入口报出不同且非契约的错误码。）
        code = _FAILURE_CODES.get(kind, "SNAPSHOT_INTEGRITY_FAILED")
        # 仍解析公共部分，便于用户判断"改选仅公共规则"的结果
        public_only = engine.resolve_effective_rules({**ctx, "client_profile_id": None,
                                                     "client_policy_snapshot_id": None})
        payload = public_only.to_dict()
        payload["client_overlay_active"] = False
        payload["client_profile_id"] = profile_id
        payload["client_policy_snapshot_id"] = None
        payload["rule_conflicts"] = list(payload.get("rule_conflicts") or []) + [
            _conflict(code, detail, client_profile_id=profile_id, failure_kind=kind)
        ]
        payload["human_confirmation_required"] = True
        return {
            "status": "blocked",
            "api_version": _API_VERSION,
            "notices": notices + [
                f"client_mode_blocked: {detail} {_REMEDIATION}",
            ],
            "effective_rule_set": payload,
            "provenance": _provenance(public, payload, ctx, client_snapshot=None),
        }

    snapshot = _resolved_snapshot
    ctx["client_policy_snapshot_id"] = snapshot["snapshot_id"]
    result = engine.resolve_effective_rules(ctx)
    payload = result.to_dict()
    payload["client_overlay_active"] = getattr(result, "client_overlay_active", False)
    return {
        "status": "ok",
        "api_version": _API_VERSION,
        "notices": notices,
        "effective_rule_set": payload,
        "provenance": _provenance(public, payload, ctx, client_snapshot=snapshot),
    }


#: `_load_client_snapshot` 成功时把快照放在这里，供 `resolve` 取用。
#: 用模块级变量而非返回值重载，是为了让失败路径的返回值保持单一含义（失败原因）。
_resolved_snapshot: Optional[Mapping[str, Any]] = None


def _load_client_snapshot(
    clients: Any,
    *,
    profile_id: str,
    snapshot_id: Optional[str],
    expected_fingerprint: str,
    allow_implicit_active: bool,
) -> Optional[tuple]:
    """加载并校验客户快照。返回 None 表示成功（快照存于 `_resolved_snapshot`）。"""
    global _resolved_snapshot
    _resolved_snapshot = None

    try:
        profile = clients.get_client_profile(profile_id)
    except Exception as exc:
        return ("profile_missing", f"客户档案不存在：{str(exc)[:120]}")

    # DATA-005：非 active 档案不得进入客户模式（Core 侧同样阻断）。
    # 这是"客户模式未成立"，必须 fail closed，不得静默退回纯公共结果。
    if profile.get("status") != "active":
        return ("profile_inactive",
                f"客户档案 {profile_id} 状态为 {profile.get('status')!r}，不可用于审查；"
                "请先恢复为 active。")

    if snapshot_id is None and not allow_implicit_active:
        # INT-010 的严格模式：未显式给快照时不自动猜，交由调用方显式选择
        return ("snapshot_missing", "未显式指定客户快照，且未允许自动固定当前 active 快照。")

    try:
        active = clients.load_active_snapshot(profile_id)
    except Exception as exc:
        return ("snapshot_corrupt", f"active manifest 损坏或不可读：{str(exc)[:120]}")

    target_id = snapshot_id or (active["snapshot_id"] if active else None)
    if not target_id:
        return ("snapshot_missing", "该客户尚无已发布的 active 快照。")

    try:
        snapshot = clients.load_snapshot(profile_id, target_id)
    except Exception as exc:
        return ("snapshot_corrupt", f"快照完整性校验失败：{str(exc)[:120]}")

    bound = snapshot.get("public_asset_fingerprint")
    if bound != expected_fingerprint:
        return ("fingerprint_mismatch",
                f"客户快照绑定的公共指纹 {bound!r} 与当前公共版本不一致。")

    _resolved_snapshot = snapshot
    return None


def _provenance(
    public: Any,
    payload: Mapping[str, Any],
    ctx: Mapping[str, Any],
    *,
    client_snapshot: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    """本轮审查的可复现溯源信息（INT-004 / INT-009 / RES-026）。"""
    return {
        "public_snapshot_id": public.public_snapshot_id,
        "public_asset_fingerprint": public.public_asset_fingerprint,
        "resolver_semantics_version": public.resolver_semantics_version,
        "client_profile_id": payload.get("client_profile_id"),
        "client_policy_snapshot_id": payload.get("client_policy_snapshot_id"),
        "client_policy_snapshot_sha256": (
            client_snapshot.get("content_sha256") if client_snapshot else None
        ),
        "coverage_level": payload.get("coverage_level"),
        "effective_rule_ids": [r.get("rule_id") for r in payload.get("effective_rules", [])],
        "excluded_rule_ids": [r.get("rule_id") for r in payload.get("excluded_rules", [])],
        "rule_conflicts": list(payload.get("rule_conflicts") or ()),
        "human_confirmation_required": bool(payload.get("human_confirmation_required")),
        "result_hash": payload.get("result_hash"),
        "context_hash": payload.get("context_hash"),
        "pinned_at": "review_start",
    }


# --------------------------------------------------------------------------- #
# review plan 扩展（保持旧 plan 兼容）
# --------------------------------------------------------------------------- #

def attach_provenance(plan: Mapping[str, Any], result: Mapping[str, Any]) -> Dict[str, Any]:
    """把本轮 provenance 附加到 review plan，**不改变旧字段语义**。"""
    extended = dict(plan)
    meta = dict(extended.get("meta") or {})
    prov = dict(result.get("provenance") or {})
    meta["resolution_provenance"] = prov
    meta["client_selection"] = {
        "client_profile_id": prov.get("client_profile_id"),
        "client_policy_snapshot_id": prov.get("client_policy_snapshot_id"),
        "mode": "explicit" if prov.get("client_profile_id") else "none",
    }
    extended["meta"] = meta
    return extended


# --------------------------------------------------------------------------- #
# 客户档案建议（SEC-006：名称只能建议，绝不自动激活）
# --------------------------------------------------------------------------- #

def suggest_client_profile(*, counterparty_name: str, data_root: Path) -> Optional[str]:
    """按主体名称给出**建议**的档案 ID。找不到或名称不足时返回 None。

    本函数只读取档案显示名做匹配，**不产生任何激活副作用**。
    """
    if not counterparty_name or not counterparty_name.strip():
        return None
    root = Path(data_root).expanduser().resolve() / "clients"
    if not root.is_dir():
        return None
    needle = counterparty_name.strip()
    for child in sorted(root.iterdir()):
        profile_file = child / "profile.json"
        if not profile_file.is_file():
            continue
        try:
            profile = json.loads(profile_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        names = [profile.get("display_name")] + list(profile.get("aliases") or ())
        if any(n and n == needle for n in names):
            return str(profile.get("client_profile_id"))
    return None


def should_auto_activate_client(suggestion: Optional[str]) -> bool:
    """永远返回 False —— 名称匹配只是建议（SEC-006 / ADR-008）。"""
    return False


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="解析一轮审查的生效规则（公共 + 可选客户 overlay）。"
    )
    parser.add_argument("--context", required=True,
                        help="resolution context 的 JSON 文件路径")
    parser.add_argument("--data-dir", default=None,
                        help="外部 data root；缺省读取 ONE_CONTRACT_DATA_DIR")
    parser.add_argument("--no-studio", action="store_true",
                        help="模拟 Rule Studio 面板不可用")
    args = parser.parse_args(argv)

    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    data_root = paths.resolve_data_root(args.data_dir)
    result = resolve(context, data_root=data_root,
                     rule_studio_available=not args.no_studio)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
