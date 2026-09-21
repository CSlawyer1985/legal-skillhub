#!/usr/bin/env python3
"""本地 HTTP API —— Rules Core 的适配器。

契约来源：architecture-contract.md §3（Core API）、§4（HTTP 映射）、§13（本地服务）。

约束：
- **本模块不实现任何规则语义**，只做参数解析、调用 Core、封装 envelope；
- **不存在公共 active 写路由**（RS-HC-001 / VIS-007）；
- adapter 收到 public target 时返回 `PUBLIC_ASSET_READ_ONLY`；
- GET 一律不改变状态（SEC-015）。
"""
from __future__ import annotations

import json
import urllib.parse
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from one_contract_rules import (
    client_repository, errors, paths, proposal_repository, public_repository, resolver,
)
from one_contract_rules import registry
from one_contract_rules import validator as rule_validator

from . import security

__all__ = ["ROUTES", "Request", "Response", "dispatch"]

API_VERSION = "v1"


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: Mapping[str, str]
    body: Optional[Mapping[str, Any]]


@dataclass(frozen=True)
class Response:
    status: int
    payload: Mapping[str, Any]


class ApiError(Exception):
    """API 层错误，携带冻结的错误码与字段路径。"""

    def __init__(self, status: int, code: str, field_path: Optional[str] = None,
                 detail: Optional[str] = None) -> None:
        super().__init__(detail or code)
        self.status = status
        self.code = code
        self.field_path = field_path
        self.detail = detail


# --------------------------------------------------------------------------- #
# 路由表
# --------------------------------------------------------------------------- #
#: 路由清单。`policy` 为 `public_read` / `client_read` / `client_write`。
#: **任何写路由都不得指向公共规则路径**（RS-HC-001）。
ROUTES: Tuple[Dict[str, Any], ...] = (
    {"method": "GET", "path": "/api/v1/health", "handler": "health", "policy": "none"},
    # Bootstrap：同源页面首次加载时换取内存会话凭据。
    # token **不进入 query、localStorage、日志或导出包**（§13）；
    # 该端点只回传凭据本身，不涉及任何私有客户数据。
    {"method": "GET", "path": "/api/v1/session/bootstrap", "handler": "session_bootstrap",
     "policy": "bootstrap"},
    {"method": "GET", "path": "/api/v1/rules/tree", "handler": "rules_tree", "policy": "public_read"},
    {"method": "GET", "path": "/api/v1/rules/search", "handler": "rules_search", "policy": "public_read"},
    {"method": "GET", "path": "/api/v1/rules/{rule_id}", "handler": "rule_detail", "policy": "public_read"},
    {"method": "GET", "path": "/api/v1/rules/{rule_id}/neighbors", "handler": "rule_neighbors", "policy": "public_read"},
    {"method": "GET", "path": "/api/v1/catalog/contract-types", "handler": "contract_types", "policy": "public_read"},
    {"method": "POST", "path": "/api/v1/resolutions/preview", "handler": "resolution_preview", "policy": "public_read"},
    {"method": "GET", "path": "/api/v1/clients", "handler": "clients_list", "policy": "client_read"},
    {"method": "POST", "path": "/api/v1/clients", "handler": "clients_create", "policy": "client_write"},
    {"method": "GET", "path": "/api/v1/clients/{client_id}", "handler": "client_detail", "policy": "client_read"},
    {"method": "GET", "path": "/api/v1/clients/{client_id}/drafts", "handler": "drafts_list", "policy": "client_read"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/drafts", "handler": "draft_save", "policy": "client_write"},
    # 读单条草稿全文：列表接口只回摘要，编辑器需要完整字段才能载入修改。
    {"method": "GET", "path": "/api/v1/clients/{client_id}/drafts/{rule_id}", "handler": "draft_detail", "policy": "client_read"},
    {"method": "GET", "path": "/api/v1/clients/{client_id}/snapshots", "handler": "snapshots_list", "policy": "client_read"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/publish", "handler": "client_publish", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/rollback", "handler": "client_rollback", "policy": "client_write"},
    {"method": "GET", "path": "/api/v1/clients/{client_id}/audit", "handler": "client_audit", "policy": "client_read"},
    # ---- 客户规则生命周期（CR-001/005/006 与「律师 UAT」九步要求全程可在面板完成）----
    # 底层 repository 早有这些能力，此前只有 drafts/publish/rollback 暴露到 API，
    # 于是「新建规则→提交→审批→回归→发布→回滚」在界面上无法走通（UAT 九步的第 3~5、8~9 步）。
    {"method": "POST", "path": "/api/v1/clients/{client_id}/client-rules", "handler": "rule_create", "policy": "client_write"},
    # 基线快照：不含任何客户规则。UAT 第 9 步「回滚并确认结果恢复」需要一个更早的快照
    # 作为回滚目标，否则只能回滚到自身（无变化，验不出恢复）。
    {"method": "POST", "path": "/api/v1/clients/{client_id}/publish-baseline", "handler": "client_publish_baseline", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/drafts/{rule_id}/delete", "handler": "draft_delete", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/client-rules/{rule_id}/submit", "handler": "rule_submit", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/client-rules/{rule_id}/approval", "handler": "rule_approve", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/client-rules/{rule_id}/regression", "handler": "rule_regression", "policy": "client_write"},
    # CR-006：已发布规则不得物理删除，**只能以新快照停用**——此前只有「禁止」的一半，
    # 没有停用入口，用户想退掉一条已发布规则会走进死路。
    {"method": "POST", "path": "/api/v1/clients/{client_id}/client-rules/{rule_id}/deprecate", "handler": "rule_deprecate", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/clients/{client_id}/deactivate", "handler": "client_deactivate", "policy": "client_write"},
    {"method": "POST", "path": "/api/v1/service/stop", "handler": "service_stop", "policy": "client_write"},
    # ---- W5：公共提案（独立工作区；不写公共资产，不进 runtime）----
    {"method": "GET", "path": "/api/v1/public-proposals", "handler": "proposals_list",
     "policy": "public_read"},
    {"method": "POST", "path": "/api/v1/public-proposals", "handler": "proposal_create",
     "policy": "proposal_write"},
    {"method": "GET", "path": "/api/v1/public-proposals/{proposal_id}", "handler": "proposal_detail",
     "policy": "public_read"},
    {"method": "GET", "path": "/api/v1/public-proposals/{proposal_id}/diff", "handler": "proposal_diff",
     "policy": "public_read"},
    {"method": "POST", "path": "/api/v1/public-proposals/{proposal_id}/transition",
     "handler": "proposal_transition", "policy": "proposal_write"},
    {"method": "POST", "path": "/api/v1/public-proposals/{proposal_id}/export",
     "handler": "proposal_export", "policy": "proposal_write"},
)

_STATIC_PREFIXES = ("/", "/app.js", "/styles.css")


def _match(method: str, path: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
    """按路由表匹配。返回 (route, path_params)。

    **路径参数必须百分号解码**：调用方按 RFC 3986 对节点 ID 做 `encodeURIComponent`，
    而节点 ID 可以含 `/`（第一层的全局文档节点就是 `references/review-doctrine.md`）。
    不解码时该 ID 会以 `references%2Freview-doctrine.md` 原样进入查找，
    于 `/rules/{rule_id}` 上返回 404，界面则保留上一个节点的内容并把它标成本节点的详情。
    """
    for route in ROUTES:
        if route["method"] != method.upper():
            continue
        template = route["path"]
        if "{" not in template:
            if template == path:
                return route, {}
            continue
        # 逐段匹配，段数必须一致
        template_parts = template.strip("/").split("/")
        parts = path.strip("/").split("/")
        if len(template_parts) != len(parts):
            continue
        params: Dict[str, str] = {}
        for expected, actual in zip(template_parts, parts):
            if expected.startswith("{") and expected.endswith("}"):
                params[expected[1:-1]] = urllib.parse.unquote(actual)
            elif expected != actual:
                break
        else:
            return route, params
    return None, {}


# --------------------------------------------------------------------------- #
# 分发
# --------------------------------------------------------------------------- #

def dispatch(
    request: Request,
    *,
    services: Mapping[str, Any],
    context: Optional[security.SecurityContext] = None,
) -> Response:
    """执行一次请求。`services` 提供 public_repository / client_repository / resolver 等。"""
    request_id = uuid.uuid4().hex

    route, params = _match(request.method, request.path)
    if route is None:
        # 不存在的路径：405 用于已知资源上的非法方法，其余 404
        known_path = any(
            r["path"].replace("{rule_id}", "").replace("{client_id}", "") in request.path
            for r in ROUTES
        )
        return _envelope(request_id, False, None,
                         ApiError(405 if known_path else 404, "INVALID_SCHEMA",
                                  detail="请求的路径或方法不存在。"))

    try:
        handler = _HANDLERS[route["handler"]]
        result = handler(request, params, services)
        return _envelope(request_id, True, result, None)
    except ApiError as exc:
        return _envelope(request_id, False, None, exc)
    except public_repository.PublicResolutionError as exc:
        return _envelope(request_id, False, None,
                         ApiError(400, "HUMAN_CONFIRMATION_REQUIRED", detail=str(exc)[:400]))
    except resolver.ResolverError as exc:
        # Core 抛出的合成失败携带冻结错误码，此处照用，不另编一个
        # （同一情形三处报同一个码：W7R3-SNAPSHOT-CORRUPT-CODES）。
        _CODES_409 = {"SNAPSHOT_INTEGRITY_FAILED", "ACTIVE_SNAPSHOT_CONFLICT"}
        status = 409 if getattr(exc, "code", "") in _CODES_409 else 400
        return _envelope(request_id, False, None,
                         ApiError(status, getattr(exc, "code", "HUMAN_CONFIRMATION_REQUIRED"),
                                  detail=str(exc)[:400]))
    # ---- 领域异常 → 正确的 HTTP 状态 + 冻结错误码 ----
    # 不逐个处理器补 except：那会让新处理器重复踩坑（非法 profile ID 曾返回 500）。
    except paths.PathContractError as exc:
        return _envelope(request_id, False, None,
                         ApiError(400, "PATH_OUTSIDE_DATA_ROOT", detail=str(exc)[:300]))
    except client_repository.ProfileNotFound as exc:
        return _envelope(request_id, False, None,
                         ApiError(404, "CLIENT_PROFILE_NOT_FOUND", detail=str(exc)[:300]))
    except client_repository.InvalidIdentifier as exc:
        return _envelope(request_id, False, None,
                         ApiError(400, "INVALID_SCHEMA", detail=str(exc)[:300]))
    except client_repository.RevisionConflict as exc:
        return _envelope(request_id, False, None,
                         ApiError(409, "DRAFT_REVISION_CONFLICT", detail=str(exc)[:300]))
    except client_repository.SnapshotIntegrityError as exc:
        return _envelope(request_id, False, None,
                         ApiError(409, "SNAPSHOT_INTEGRITY_FAILED", detail=str(exc)[:300]))
    except client_repository.ClientStoreError as exc:
        return _envelope(request_id, False, None,
                         ApiError(400, "INVALID_SCHEMA", detail=str(exc)[:300]))
    except Exception as exc:  # 兜底：不回显堆栈与绝对路径
        return _envelope(request_id, False, None,
                         ApiError(500, "INVALID_SCHEMA", detail=type(exc).__name__))


def _validate_envelope(payload: Mapping[str, Any]) -> None:
    """每个 HTTP 响应都必须过 `api-envelope-v1`（冻结契约）。

    这是所有响应的**唯一收口**，接在这里可覆盖全部路由——包括将来新增的。
    此前该 DTO 在产品代码中零引用（W7R2-DTO-ENFORCEMENT 的一部分）。
    失败时抛 ValueError 由测试暴露：响应信封不合契约属实现缺陷，不是运行期故障，
    不应静默返回一个"看起来正常"的响应。
    """
    validator = registry.make_validator("one-contract/api-envelope-v1.schema.json")
    first = next(iter(sorted(validator.iter_errors(payload),
                              key=lambda e: list(e.path))), None)
    if first is not None:
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise ValueError(f"响应信封不符合 api-envelope-v1: {path}: {first.message}")


def _envelope(
    request_id: str, success: bool, result: Any, error: Optional[ApiError]
) -> Response:
    if success:
        payload: Dict[str, Any] = {
            "api_version": API_VERSION,
            "request_id": request_id,
            "success": True,
            "result": result,
            "error": None,
        }
        _validate_envelope(payload)
        return Response(200, payload)

    assert error is not None
    payload = {
        "api_version": API_VERSION,
        "request_id": request_id,
        "success": False,
        "result": None,
        "error": errors.error_payload(error.code, field_path=error.field_path,
                                      details={"detail": error.detail} if error.detail else None),
    }
    _validate_envelope(payload)
    return Response(error.status, payload)


# --------------------------------------------------------------------------- #
# 处理器
# --------------------------------------------------------------------------- #

def _public(services: Mapping[str, Any]) -> public_repository.PublicRepository:
    return services["public_repository"]


def _node_dict(node: Any) -> Dict[str, Any]:
    return {
        "node_id": node.node_id,
        "node_kind": node.node_kind,
        "layer": node.layer,
        "title": node.title,
        "version": node.version,
        "approval_status": node.approval_status,
        "activation_status": node.activation_status,
        "body_visibility": node.body_visibility,
        "body": None,
        "domain_codes": list(node.domain_codes),
        "type_ids": list(node.type_ids),
        "roles": list(node.roles),
        "scene_tags": list(node.scene_tags),
        "source_refs": list(node.source_refs),
        "summary": node.summary,
        "updated_at": node.updated_at,
        "content_hash": node.content_hash,
    }


def handle_health(request, params, services):
    return {"status": "ok", "api_version": API_VERSION}


def handle_session_bootstrap(request, params, services):
    """回传当前会话凭据与 CSRF 值。仅同源页面可读（Host/Origin 已在校验层通过）。"""
    context = services.get("security_context")
    if context is None:
        raise ApiError(503, "UNAUTHORIZED_LOCAL_REQUEST", detail="会话上下文不可用。")
    return {"token": context.token, "csrf_token": context.csrf_token,
            "origin": context.origin}


#: 列表接口最大页大小（§4：列表接口须定义分页、稳定排序与最大 page size）。
MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50


def _page_args(request) -> Tuple[int, int]:
    try:
        limit = int(request.query.get("limit", DEFAULT_PAGE_SIZE))
    except ValueError:
        limit = DEFAULT_PAGE_SIZE
    try:
        offset = int(request.query.get("offset", 0))
    except ValueError:
        offset = 0
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    offset = max(0, offset)
    return limit, offset


def handle_rules_tree(request, params, services):
    layer = request.query.get("layer") or None
    type_id = request.query.get("type_id") or None
    projection_mode = request.query.get("projection_mode") or "maintenance"
    limit, offset = _page_args(request)
    try:
        nodes = _public(services).list_rule_tree(
            layer=layer, type_id=type_id, projection_mode=projection_mode
        )
    except public_repository.PublicResolutionError as exc:
        code = "UNKNOWN_FACT_OR_TARGET" if "未知类型" in str(exc) else "INVALID_SCHEMA"
        raise ApiError(400, code, field_path="type_id" if "未知类型" in str(exc) else None,
                       detail=str(exc)[:300]) from exc
    total = len(nodes)
    page = nodes[offset:offset + limit]
    return {"nodes": [_node_dict(n) for n in page], "total": total,
            "offset": offset, "limit": limit, "truncated": offset + len(page) < total}


def handle_rules_search(request, params, services):
    query = request.query.get("q") or ""
    if not query.strip():
        raise ApiError(400, "INVALID_SCHEMA", field_path="q", detail="搜索词不得为空。")
    limit, offset = _page_args(request)
    nodes = _public(services).search_rules(query)
    total = len(nodes)
    page = nodes[offset:offset + limit]
    return {"nodes": [_node_dict(n) for n in page], "total": total,
            "offset": offset, "limit": limit, "truncated": offset + len(page) < total}


def handle_contract_types(request, params, services):
    """供非技术界面使用的合同类型中文选项，仅返回当前已启用类型。"""
    return {"contract_types": _public(services).list_runtime_contract_types()}


def handle_rule_detail(request, params, services):
    node = _public(services).get_rule(params["rule_id"])
    if node is None:
        raise ApiError(404, "UNKNOWN_FACT_OR_TARGET", field_path="rule_id",
                       detail="未找到该规则。")
    return _node_dict(node)


def handle_rule_neighbors(request, params, services):
    repo = _public(services)
    # 「节点不存在」与「节点存在但没有关系边」必须可区分：`get_rule_neighbors`
    # 两者都返回 []，若直接据此回答，界面会把「查不到这个节点」显示成
    # 「该节点没有对外关系边」——把未知当成明确的假。故先按与 `rule_detail`
    # 相同口径确认节点存在，不存在则与详情一致地报 404。
    if repo.get_rule(params["rule_id"]) is None:
        raise ApiError(404, "UNKNOWN_FACT_OR_TARGET", field_path="rule_id",
                       detail="未找到该规则。")
    edges = repo.get_rule_neighbors(params["rule_id"])
    return {"edges": [
        {"edge_id": e.edge_id, "from_id": e.from_id, "to_id": e.to_id,
         "edge_kind": e.edge_kind, "scope": dict(e.scope or {}),
         "source": e.source, "status": e.status}
        for e in edges
    ]}


def handle_resolution_preview(request, params, services):
    body = request.body or {}
    context = body.get("context")
    if not isinstance(context, Mapping):
        raise ApiError(400, "INVALID_SCHEMA", field_path="context",
                       detail="缺少 resolution context。")
    engine: resolver.Resolver = services["resolver"]
    result = engine.resolve_effective_rules(context)
    payload = result.to_dict()
    payload["client_overlay_active"] = getattr(result, "client_overlay_active", False)
    return payload


def handle_clients_list(request, params, services):
    repo = services["client_repository"]
    root = repo.clients_root
    profiles: List[Dict[str, Any]] = []
    if root.is_dir():
        for child in sorted(root.iterdir()):
            profile_file = child / "profile.json"
            if profile_file.is_file():
                profile = json.loads(profile_file.read_text(encoding="utf-8"))
                profiles.append({
                    "client_profile_id": profile["client_profile_id"],
                    "display_name": profile["display_name"],
                    "status": profile["status"],
                    "revision": profile.get("revision"),
                })
    return {"clients": profiles}


def handle_clients_create(request, params, services):
    body = request.body or {}
    profile_id = body.get("client_profile_id")
    display_name = body.get("display_name")
    if not profile_id or not display_name:
        raise ApiError(400, "INVALID_SCHEMA", field_path="client_profile_id",
                       detail="需要 client_profile_id 与 display_name。")
    created = services["client_repository"].create_client_profile(
        client_profile_id=profile_id, display_name=display_name, actor="local_operator"
    )
    return {"client_profile_id": created["client_profile_id"],
            "display_name": created["display_name"], "status": created["status"]}


def handle_client_detail(request, params, services):
    profile = services["client_repository"].get_client_profile(params["client_id"])
    return {k: profile[k] for k in
            ("client_profile_id", "display_name", "status", "revision")}


def handle_drafts_list(request, params, services):
    drafts = services["client_repository"].list_drafts(params["client_id"])
    return {"drafts": [
        {"client_rule_id": d["client_rule_id"], "version": d["version"],
         "approval_status": d["approval_status"], "activation_status": d["activation_status"],
         "revision": d["revision"], "title": d["title"]}
        for d in drafts
    ]}


def handle_draft_detail(request, params, services):
    """读单条草稿全文（编辑器载入用）。列表接口只回摘要字段，不足以还原规则。"""
    draft = services["client_repository"].get_draft(params["client_id"], params["rule_id"])
    if draft is None:
        raise ApiError(404, "UNKNOWN_FACT_OR_TARGET", field_path="rule_id",
                       detail="未找到该规则草稿。")
    return {"draft": draft}


def handle_draft_save(request, params, services):
    body = request.body or {}
    draft = body.get("draft")
    if not isinstance(draft, Mapping):
        raise ApiError(400, "INVALID_SCHEMA", field_path="draft", detail="缺少 draft。")

    # 先做结构校验：契约要求校验失败时定位到具体字段（CR-002）。
    # 归属一致性（CR-008）等业务检查放在其后，避免遮蔽字段级定位。
    try:
        rule_validator.validate_client_rule(draft)
        rule_validator.validate_rule_business(draft)
    except rule_validator.ValidationError as exc:
        raise ApiError(400, "INVALID_SCHEMA", field_path=exc.field_path,
                       detail=exc.message) from exc

    repo = services["client_repository"]
    try:
        saved = repo.save_draft(
            params["client_id"], draft,
            expected_revision=int(body.get("expected_revision", 0)),
            actor="local_operator",
        )
    except rule_validator.ValidationError as exc:
        raise _rule_validation_error(exc, draft) from exc
    except client_repository.RevisionConflict as exc:
        raise ApiError(409, "DRAFT_REVISION_CONFLICT", field_path="expected_revision",
                       detail=str(exc)[:300]) from exc
    except client_repository.ClientStoreError as exc:
        # 不能一律说成「结构不符合契约、请按字段路径修正」——CR-004 的拒绝（版本已发布）
        # 属于版本规则，用户**没有任何字段可改**，而 field_path 还是 null。
        # 这是同一缺陷型的第三例（publish、rollback 已修，save 未修）。
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": saved["client_rule_id"], "revision": saved["revision"],
            "approval_status": saved["approval_status"]}


# --------------------------------------------------------------------------- #
# 客户规则生命周期（新建 / 删除草稿 / 提交 / 审批 / 回归 / 停用档案）
#
# 这些能力在 repository 层早已存在，此前只有 drafts / publish / rollback 暴露到 API，
# 导致契约「律师 UAT」九步里的第 3~5、8~9 步（新建规则、审批、回归、硬边界、回滚）
# 在浏览器里根本无法走通——普通用户只能建档案、看只读草稿列表。
# --------------------------------------------------------------------------- #

def _actor(body: Mapping[str, Any]) -> str:
    """操作者标识。本地 MVP 的身份是**自述留痕**（ADR-024），故这里原样记录调用方给的值，
    缺省为 `local_operator`。不校验、不认证，界面亦已声明其性质。"""
    value = str(body.get("actor") or "").strip() or "local_operator"
    return value[:64]


def _require_evidence_id(raw: Any) -> str:
    """在调用前做**字段级**校验，使 CR-002「校验阻止提交并定位字段」对审批/回归同样成立。
    复用 repository 的冻结正则，不复制第二份。"""
    value = "" if raw is None else str(raw)
    if not client_repository.EVIDENCE_ID_PATTERN.match(value):
        raise ApiError(400, "INVALID_SCHEMA", field_path="evidence_id",
                       detail="证据编号需以 ev_ 开头、总长 11–99，且只含小写字母数字与 _-。")
    return value


def _rule_lifecycle_error(exc: Exception) -> ApiError:
    """规则生命周期操作的领域异常 → **已登记**的冻结错误码。

    错误码是冻结词表（`one_contract_rules.errors.ERROR_CATALOG`），**不得自创**：
    未登记的码会在 `_envelope` 组装响应时抛 `UnknownErrorCode`，异常逃出 `dispatch`，
    结果不是一条可读的错误响应而是**直接断开连接**（本轮实测踩到）。
    故此处只映射到既有的码：

    - 实体不存在            → `UNKNOWN_FACT_OR_TARGET`（404，与 `/rules/{id}` 一致）
    - 重复 ID / 版本         → `DUPLICATE_ACTIVE_RULE_VERSION`（409）
    - 其余状态或前置不满足   → `INVALID_STATE_TRANSITION`（409）

    以消息子串判定是**权宜**：干净做法是 repository 抛带码的类型化异常，那属接口变更，
    本轮不做，也不新增错误码。判定顺序有意为之——「已存在」不含「不存在」，不会互相吃掉。
    """
    text = str(exc)
    if "不存在" in text:
        return ApiError(404, "UNKNOWN_FACT_OR_TARGET", detail=text[:300])
    if "已存在" in text or "重复" in text or "提升版本号" in text:
        # 「版本已发布，必须提升版本号」（CR-004）本质是版本冲突，
        # 冻结目录里 `DUPLICATE_ACTIVE_RULE_VERSION` 正为此而设。
        return ApiError(409, "DUPLICATE_ACTIVE_RULE_VERSION", detail=text[:300])
    if "目标客户" in text and "不一致" in text:
        # CR-008：规则归属与目标客户不一致——冻结目录里 `CLIENT_SCOPE_VIOLATION` 正为此而设。
        # 落到通用 INVALID_STATE_TRANSITION 会给出「按草稿→提交→…顺序推进」的补救建议，
        # 与「跨客户写入被拒」这件事毫不相干。
        return ApiError(409, "CLIENT_SCOPE_VIOLATION", detail=text[:300])
    if "快照不完整" in text or "快照文件损坏" in text or "快照完整性" in text:
        # 回滚/发布的目标快照缺失或损坏——用 `SNAPSHOT_INTEGRITY_FAILED`（已登记）。
        # 若落到通用的 INVALID_STATE_TRANSITION，其 remediation 会讲「按草稿→提交→…的顺序推进」，
        # 与「目标快照不存在」这件事实对不上，等于换了个说法继续误导。
        return ApiError(409, "SNAPSHOT_INTEGRITY_FAILED", detail=text[:300])
    return ApiError(409, "INVALID_STATE_TRANSITION", detail=text[:300])


def _rule_validation_error(exc: Exception, payload: Mapping[str, Any]) -> ApiError:
    """结构校验失败 → 400（带字段定位）。

    若失败落在 `scope`，优先用业务校验器那句**可读**的说明——JSON Schema 的原始消息
    （`['EC-02'] is expected to be empty`）是英文且指向实现细节，律师读不懂，
    而真正清楚的那句因为 schema 先失败永远执行不到。
    """
    field_path = getattr(exc, "field_path", None)
    message = getattr(exc, "message", str(exc))
    if field_path and str(field_path).startswith("scope"):
        readable = rule_validator.describe_scope_problem(payload.get("scope"))
        if readable is not None:
            message = readable.message
            field_path = readable.field_path or field_path
    return ApiError(400, "INVALID_SCHEMA", field_path=field_path, detail=str(message)[:300])


def handle_rule_create(request, params, services):
    """CR-001：新建客户规则草稿。唯一稳定 ID，初始 candidate，运行时不生效。"""
    body = request.body or {}
    rule = body.get("rule")
    if not isinstance(rule, Mapping):
        raise ApiError(400, "INVALID_SCHEMA", field_path="rule", detail="缺少 rule。")
    # 新建规则的 revision 恒为起点 1、创建/更新时间即当下——三者都由操作本身决定，
    # 由 API 补齐（调用方给了就沿用其 created_at，便于导入既有记录）。
    rule = dict(rule)
    rule.setdefault("revision", 1)
    stamped = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rule.setdefault("created_at", stamped)
    rule.setdefault("updated_at", stamped)
    rule.setdefault("created_by", _actor(body))
    rule.setdefault("updated_by", _actor(body))
    # 不在此处重复校验：repository 的 `_validate_rule_for_save` 会做同一套校验并抛带
    # `field_path` 的 ValidationError（下面接住并转成字段级 400，满足 CR-002）。
    # 之前在这里先校验一次，反而把「仓库会补 content_sha256」这一步挡在了前面。
    try:
        created = services["client_repository"].create_new_rule(
            params["client_id"], rule, actor=_actor(body))
    except rule_validator.ValidationError as exc:
        raise _rule_validation_error(exc, rule) from exc
    except client_repository.ClientStoreError as exc:
        # CR-007：重复 ID 拒绝覆盖（repository 已保证不覆盖）
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": created["client_rule_id"], "revision": created["revision"],
            "approval_status": created["approval_status"],
            "activation_status": created["activation_status"]}


def handle_draft_delete(request, params, services):
    """CR-005：删除**从未发布**的草稿，需二次确认并留最小审计。
    CR-006 / ADR-018：已发布规则禁止物理删除（由 repository 拒绝）。"""
    body = request.body or {}
    if body.get("confirmation") is not True:
        raise ApiError(400, "INVALID_SCHEMA", field_path="confirmation",
                       detail="删除草稿需要二次确认（CR-005）。")
    try:
        services["client_repository"].delete_draft(
            params["client_id"], params["rule_id"], confirmation=True, actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": params["rule_id"], "deleted": True}


def handle_rule_submit(request, params, services):
    """提交规则进入审批流（提交本身不改变审批状态）。"""
    body = request.body or {}
    try:
        out = services["client_repository"].submit_rule(
            params["client_id"], params["rule_id"], actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": out["client_rule_id"], "revision": out.get("revision"),
            "approval_status": out.get("approval_status")}


def handle_rule_approve(request, params, services):
    """记录律师批准。LIFE-003：缺批准不得进入回归与发布。"""
    body = request.body or {}
    evidence_id = _require_evidence_id(body.get("evidence_id"))
    try:
        out = services["client_repository"].record_lawyer_approval(
            params["client_id"], params["rule_id"], evidence_id=evidence_id, actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": out["client_rule_id"], "revision": out.get("revision"),
            "approval_status": out.get("approval_status"),
            "evidence_id": evidence_id}


def handle_rule_regression(request, params, services):
    """记录回归结果。未通过（passed=false）时只记审计、不推进状态。"""
    body = request.body or {}
    evidence_id = _require_evidence_id(body.get("evidence_id"))
    if not isinstance(body.get("passed"), bool):
        raise ApiError(400, "INVALID_SCHEMA", field_path="passed",
                       detail="回归结果必须是布尔值 passed。")
    try:
        out = services["client_repository"].record_regression_result(
            params["client_id"], params["rule_id"],
            evidence_id=evidence_id, passed=bool(body["passed"]), actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": out.get("client_rule_id", params["rule_id"]),
            "revision": out.get("revision"),
            "approval_status": out.get("approval_status"),
            "passed": bool(body["passed"])}


def handle_rule_deprecate(request, params, services):
    """停用一条已发布规则（CR-006 / ADR-018）。

    只把草稿标为 deprecated；**需要再发布一次快照才真正停止生效**（届时新快照不再收录它）。
    响应里回传 `requires_publish`，避免调用方误以为停用已经生效。
    """
    body = request.body or {}
    try:
        out = services["client_repository"].deprecate_rule(
            params["client_id"], params["rule_id"], actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"client_rule_id": out["client_rule_id"], "revision": out.get("revision"),
            "approval_status": out.get("approval_status"),
            "requires_publish": True,
            "note": "已标记停用；需再发布一次快照才会真正停止生效。"}


def handle_client_publish_baseline(request, params, services):
    """发布**基线快照**（不含任何客户规则）。

    用途：给客户一个「无客户规则」的已发布状态作为回滚目标。契约「律师 UAT」第 9 步是
    「回滚并确认结果恢复」——若档案从未发布过快照，就没有可回滚的目标，该步无法成立。
    发布后客户覆盖为空、解析结果与纯公共一致（RES-024）。
    """
    body = request.body or {}
    if body.get("confirmation") is not True:
        raise ApiError(400, "INVALID_SCHEMA", field_path="confirmation",
                       detail="发布基线快照需要二次确认。")
    try:
        snapshot = services["client_repository"].publish_empty_snapshot(
            params["client_id"], actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"snapshot_id": snapshot["snapshot_id"],
            "published_at": snapshot.get("published_at")}


def handle_client_deactivate(request, params, services):
    """停用客户档案。停用后该档案不参与解析（resolve 入口按档案状态拒绝）。"""
    body = request.body or {}
    try:
        out = services["client_repository"].deactivate_client_profile(
            params["client_id"], actor=_actor(body))
    except client_repository.ClientStoreError as exc:
        raise _rule_lifecycle_error(exc) from exc
    return {"client_profile_id": out.get("client_profile_id", params["client_id"]),
            "status": out.get("status")}


def handle_snapshots_list(request, params, services):
    repo = services["client_repository"]
    profile_id = params["client_id"]
    snapshots_dir = repo.clients_root / profile_id / "snapshots"
    entries: List[Dict[str, Any]] = []
    if snapshots_dir.is_dir():
        for child in snapshots_dir.iterdir():
            if child.name.startswith("."):
                continue
            manifest = child / "manifest.json"
            if manifest.is_file():
                data = json.loads(manifest.read_text(encoding="utf-8"))
                entries.append({
                    "snapshot_id": data["snapshot_id"],
                    "published_at": data["published_at"],
                    "published_by": data["published_by"],
                    # 权威的「上一个快照」链接：快照清单里记着链条，比按时间戳推断可靠
                    # （同一秒内两次发布的时间戳相同，无法据此排序）。
                    "previous_snapshot_id": data.get("previous_snapshot_id"),
                })
    # 按发布时间排序，**不能按目录名**——目录名是 `cs_<uuid16>`，那是随机的。
    # 排序仅供展示：找「上一个快照」应当用下面返回的 previous_snapshot_id，不要靠位次。
    entries.sort(key=lambda e: (e["published_at"], e["snapshot_id"]))
    active = repo.load_active_snapshot(profile_id)
    active_id = active["snapshot_id"] if active else None
    previous_of_active = next(
        (e["previous_snapshot_id"] for e in entries if e["snapshot_id"] == active_id), None)
    return {"snapshots": entries,
            "active_snapshot_id": active_id,
            "previous_snapshot_id": previous_of_active}


def handle_client_publish(request, params, services):
    body = request.body or {}
    if body.get("confirmation") is not True:
        raise ApiError(400, "INVALID_SCHEMA", field_path="confirmation",
                       detail="发布需要二次确认。")
    # 必须**携带**该字段（首次发布传 null），使比较交换是调用方的显式声明。
    # 原判断 `not X and X != None` 恒为假——那道守卫从未生效过。
    if "expected_active_snapshot" not in body:
        raise ApiError(400, "INVALID_SCHEMA", field_path="expected_active_snapshot",
                       detail="发布必须携带 expected_active_snapshot（首次发布传 null）。")
    repo = services["client_repository"]
    public = _public(services)
    try:
        snapshot = repo.publish_snapshot(
            params["client_id"],
            expected_active_snapshot=body.get("expected_active_snapshot"),
            confirmation=True, actor="local_operator",
            public_snapshot_id=public.public_snapshot_id,
            public_asset_fingerprint=public.public_asset_fingerprint,
            resolver_semantics_version=public.resolver_semantics_version,
            enforce_single_active_version=True,
        )
    except client_repository.ClientStoreError as exc:
        # 不能把所有 ClientStoreError 都说成「生效快照已被改变」——那是一次**假提示**：
        # 实测「没有可发布的规则」也被映射成该码，用户会去追一个并不存在的快照冲突。
        # 发布器在真正的比较交换失败时，消息里自带该码名（ACTIVE_SNAPSHOT_CONFLICT），
        # 据此区分；其余一律走通用的生命周期映射（含具体原因）。
        text = str(exc)
        if "ACTIVE_SNAPSHOT_CONFLICT" in text:
            raise ApiError(409, "ACTIVE_SNAPSHOT_CONFLICT", detail=text[:300]) from exc
        raise _rule_lifecycle_error(exc) from exc
    # `skipped_drafts` 由 repository 计算：混合发布时（部分已批准、部分仍是 candidate）
    # 发布应当成功，但**必须如实回报哪些草稿没有被包含**——否则用户看到「发布成功」
    # 却不知道少了一条（不在生效集合、不在 excluded_rules、无冲突、无人工确认）。
    return {"snapshot_id": snapshot["snapshot_id"],
            "published_at": snapshot["published_at"],
            "skipped_drafts": snapshot.get("skipped_drafts") or []}


def handle_client_rollback(request, params, services):
    body = request.body or {}
    repo = services["client_repository"]
    try:
        target = repo.rollback_snapshot(
            params["client_id"],
            target_snapshot=body.get("target_snapshot", ""),
            expected_active_snapshot=body.get("expected_active_snapshot"),
            actor="local_operator",
        )
    except client_repository.ClientStoreError as exc:
        # 与 publish 同一处缺陷型，此前未同步：所有 ClientStoreError 都被说成
        # 「发布期间生效快照已被改变」。实测传一个不存在的目标快照也报这个，
        # 用户会照提示去"重新读取当前生效快照"，而真实原因是「目标不存在/快照不完整」。
        text = str(exc)
        if "ACTIVE_SNAPSHOT_CONFLICT" in text:
            raise ApiError(409, "ACTIVE_SNAPSHOT_CONFLICT", detail=text[:300]) from exc
        raise _rule_lifecycle_error(exc) from exc
    return {"snapshot_id": target["snapshot_id"]}


def handle_client_audit(request, params, services):
    events = services["client_repository"].list_audit_events(params["client_id"])
    # 只回传最小诊断字段，不回传规则正文
    return {"events": [
        {"event_id": e.get("event_id"), "event_kind": e.get("event_kind"),
         "actor": e.get("actor"), "recorded_at": e.get("recorded_at"),
         "result": e.get("result")}
        for e in events
    ]}


def _proposals(services: Mapping[str, Any]):
    repo = services.get("proposal_repository")
    if repo is None:
        raise ApiError(503, "INVALID_SCHEMA", detail="提案仓库不可用。")
    return repo


def handle_proposals_list(request, params, services):
    proposals = _proposals(services).list_proposals(
        status=request.query.get("status") or None,
        layer=request.query.get("layer") or None,
    )
    return {"proposals": [
        {"proposal_id": p["proposal_id"], "operation": p["operation"], "layer": p["layer"],
         "target_rule_id": p.get("target_rule_id"), "title": p["title"],
         "status": p["status"], "created_at": p["created_at"],
         "effective": False}
        for p in proposals
    ]}


def handle_proposal_create(request, params, services):
    body = request.body or {}
    required = ("operation", "layer", "title", "rationale")
    for field in required:
        if not body.get(field):
            raise ApiError(400, "INVALID_SCHEMA", field_path=field,
                           detail=f"缺少 {field}。")
    try:
        return _proposals(services).create_proposal(
            operation=body["operation"], layer=body["layer"],
            target_rule_id=body.get("target_rule_id"),
            title=body["title"], rationale=body["rationale"],
            source_refs=body.get("source_refs") or [],
            proposed_rule=body.get("proposed_rule"),
            actor="local_operator",
        )
    except proposal_repository.ProposalError as exc:
        raise ApiError(400, "INVALID_SCHEMA", detail=str(exc)[:300]) from exc


def handle_proposal_detail(request, params, services):
    try:
        return _proposals(services).get_proposal(params["proposal_id"])
    except proposal_repository.ProposalError as exc:
        raise ApiError(404, "UNKNOWN_FACT_OR_TARGET", field_path="proposal_id",
                       detail=str(exc)[:200]) from exc


def handle_proposal_diff(request, params, services):
    repo = _proposals(services)
    try:
        proposal = repo.get_proposal(params["proposal_id"])
        return repo.proposal_diff(
            operation=proposal["operation"], layer=proposal["layer"],
            target_rule_id=proposal.get("target_rule_id"),
            proposed_rule=proposal.get("proposed_rule"),
        )
    except proposal_repository.ProposalError as exc:
        raise ApiError(400, "INVALID_SCHEMA", detail=str(exc)[:300]) from exc


def handle_proposal_transition(request, params, services):
    body = request.body or {}
    to_status = body.get("to_status")
    if not to_status:
        raise ApiError(400, "INVALID_SCHEMA", field_path="to_status", detail="缺少目标状态。")
    try:
        return _proposals(services).transition(
            params["proposal_id"], to_status=to_status, actor="local_operator"
        )
    except proposal_repository.ProposalError as exc:
        # 非法状态迁移（含跳过审批的尝试）一律拒绝
        raise ApiError(409, "INVALID_STATE_TRANSITION", detail=str(exc)[:300]) from exc


def handle_proposal_export(request, params, services):
    try:
        return _proposals(services).export_governance_bundle(params["proposal_id"])
    except proposal_repository.ProposalError as exc:
        raise ApiError(400, "INVALID_SCHEMA", detail=str(exc)[:300]) from exc


def handle_service_stop(request, params, services):
    stop = services.get("stop_callback")
    if callable(stop):
        stop()
    return {"stopping": True}


_HANDLERS: Dict[str, Callable[..., Any]] = {
    "health": handle_health,
    "session_bootstrap": handle_session_bootstrap,
    "rules_tree": handle_rules_tree,
    "rules_search": handle_rules_search,
    "contract_types": handle_contract_types,
    "rule_detail": handle_rule_detail,
    "rule_neighbors": handle_rule_neighbors,
    "resolution_preview": handle_resolution_preview,
    "clients_list": handle_clients_list,
    "clients_create": handle_clients_create,
    "client_detail": handle_client_detail,
    "drafts_list": handle_drafts_list,
    "draft_detail": handle_draft_detail,
    "draft_save": handle_draft_save,
    "snapshots_list": handle_snapshots_list,
    "client_publish": handle_client_publish,
    "client_rollback": handle_client_rollback,
    "client_audit": handle_client_audit,
    "rule_create": handle_rule_create,
    "client_publish_baseline": handle_client_publish_baseline,
    "draft_delete": handle_draft_delete,
    "rule_submit": handle_rule_submit,
    "rule_approve": handle_rule_approve,
    "rule_regression": handle_rule_regression,
    "rule_deprecate": handle_rule_deprecate,
    "client_deactivate": handle_client_deactivate,
    "service_stop": handle_service_stop,
    "proposals_list": handle_proposals_list,
    "proposal_create": handle_proposal_create,
    "proposal_detail": handle_proposal_detail,
    "proposal_diff": handle_proposal_diff,
    "proposal_transition": handle_proposal_transition,
    "proposal_export": handle_proposal_export,
}
