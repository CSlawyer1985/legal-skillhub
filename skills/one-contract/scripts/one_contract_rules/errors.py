#!/usr/bin/env python3
"""错误码目录。

契约来源：architecture-contract.md §11。

要求：
- 码名匹配 API envelope 的 `^[A-Z][A-Z0-9_]{2,99}$`；
- 每个码提供对律师可读的 message 与可执行的 remediation；
- 不得回显堆栈、完整私有规则或本机绝对路径；
- 未知码 fail closed（抛 UnknownErrorCode），不做兜底透传。
"""
from __future__ import annotations

import re
from typing import Dict, Mapping, Optional

__all__ = [
    "CODE_PATTERN",
    "ERROR_CATALOG",
    "UnknownErrorCode",
    "describe",
    "error_payload",
    "is_known_code",
]

CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,99}$")


class UnknownErrorCode(Exception):
    """请求了未注册的错误码。"""


ERROR_CATALOG: Dict[str, Dict[str, str]] = {
    "INVALID_SCHEMA": {
        "message": "提交的内容结构不符合契约。",
        "remediation": "按提示的字段路径修正后重新提交；不要手工绕过结构校验。",
    },
    "INVALID_STATE_TRANSITION": {
        "message": "该状态跳转不被允许。",
        "remediation": "按草稿→提交→律师批准→回归通过→发布的顺序推进，补齐缺失的前置证据。",
    },
    "PUBLIC_ASSET_READ_ONLY": {
        "message": "公共规则资产为只读，不能原地修改。",
        "remediation": "改用“提出修改”生成公共提案；提案与正式生效资产相互隔离。",
    },
    "CLIENT_PROFILE_NOT_SELECTED": {
        "message": "本轮未选择顾问单位档案。",
        "remediation": "如需按客户口径审查，请显式选择客户档案；否则请确认按纯公共规则继续。",
    },
    "CLIENT_PROFILE_NOT_FOUND": {
        "message": "指定的顾问单位档案不存在。",
        "remediation": "核对档案标识，或先创建该客户档案。系统不会自动回退到其他客户。",
    },
    "CLIENT_SCOPE_VIOLATION": {
        "message": "请求跨越了客户边界。",
        "remediation": "确认操作对象与当前所选客户一致；不同客户的数据严格隔离。",
    },
    "PATH_OUTSIDE_DATA_ROOT": {
        "message": "目标路径超出允许的数据目录范围。",
        "remediation": "改用数据目录内的相对路径；绝对路径、上级目录与符号链接越界都会被拒绝。",
    },
    "DRAFT_REVISION_CONFLICT": {
        "message": "草稿已被其他操作修改，当前版本不是最新。",
        "remediation": "重新载入最新草稿，确认差异后再提交；不要覆盖他人修改。",
    },
    "ACTIVE_SNAPSHOT_CONFLICT": {
        "message": "发布期间生效快照已被改变。",
        "remediation": "重新读取当前生效快照，确认后再发布；系统不会用旧假设覆盖新状态。",
    },
    "SNAPSHOT_INTEGRITY_FAILED": {
        "message": "快照内容损坏或哈希不匹配，已停止加载。",
        "remediation": "从已有合法快照恢复，或重新发布该客户快照；不得跳过完整性校验继续。",
    },
    "PUBLIC_SNAPSHOT_MISMATCH": {
        "message": "客户快照绑定的公共规则版本与当前公共版本不一致。",
        "remediation": "客户数据已保留但叠加已暂停；请重新校验并发布绑定新公共版本的客户快照。",
    },
    "CANDIDATE_NOT_EXECUTABLE": {
        "message": "该资产尚未正式生效，不能进入审查结果。",
        "remediation": "完成律师批准与回归验证并发布后再使用；维护视图可查看其未生效状态。",
    },
    "HARD_BOUNDARY_CONFLICT": {
        "message": "该规则与不可覆盖的边界冲突。",
        "remediation": "不得以优先级或数值覆盖；请人工复核并调整规则表述或适用范围。",
    },
    "DEPENDENCY_UNSATISFIED": {
        "message": "该规则依赖的前置规则缺失或不可用。",
        "remediation": "补齐依赖规则后重新校验；依赖不满足时该规则不会单独生效。",
    },
    "INVALID_CONDITION_TYPE": {
        "message": "条件中的事实值与操作符类型不匹配。",
        "remediation": "核对事实字段类型与比较方式；系统不做隐式类型转换。",
    },
    "UNKNOWN_FACT_OR_TARGET": {
        "message": "引用了未登记的事实字段或作用目标。",
        "remediation": "改用已登记的事实字段与作用目标；新字段需先进入受控目录。",
    },
    "DUPLICATE_ACTIVE_RULE_VERSION": {
        "message": "同一规则标识存在多个生效版本。",
        "remediation": "保留一个生效版本并停用其余版本后重新发布；发布会被拒绝直到冲突解除。",
    },
    "PROFILE_SNAPSHOT_MISMATCH": {
        "message": "档案、发布清单、快照或规则之间的客户标识不一致。",
        "remediation": "核对客户标识链；跨客户引用一律拒绝，不会自动纠正。",
    },
    "HUMAN_CONFIRMATION_REQUIRED": {
        "message": "该事项需要人工判断，系统未自动决定。",
        "remediation": "请律师或授权用户确认后再继续；系统不会在冲突中静默择一。",
    },
    "UNAUTHORIZED_LOCAL_REQUEST": {
        "message": "本地请求未通过安全校验。",
        "remediation": "请从启动器打开的页面重新操作；会话可能已过期或来源不被信任。",
    },
}


def is_known_code(code: object) -> bool:
    return isinstance(code, str) and code in ERROR_CATALOG


def describe(code: str) -> Mapping[str, str]:
    """返回该码的 message 与 remediation。未知码 fail closed。"""
    if not is_known_code(code):
        raise UnknownErrorCode(
            f"未注册的错误码: {code!r}。请先在 errors.ERROR_CATALOG 中登记再加使用。"
        )
    return ERROR_CATALOG[code]


def error_payload(
    code: str,
    field_path: Optional[str] = None,
    details: Optional[Mapping[str, object]] = None,
) -> Dict[str, object]:
    """构造 API envelope 的 error 对象。

    文案固定来自目录，调用方不得注入本机绝对路径或私有规则正文。
    """
    spec = describe(code)
    payload: Dict[str, object] = {
        "code": code,
        "message": spec["message"],
        "field_path": field_path,
        "remediation": spec["remediation"],
    }
    if details:
        payload["details"] = dict(details)
    return payload
