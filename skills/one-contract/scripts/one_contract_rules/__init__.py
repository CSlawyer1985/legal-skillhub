#!/usr/bin/env python3
"""One-Contract Rules Core —— Rule Studio 的规则内核。

设计边界（architecture-contract.md §1）：
- 本包不导入 HTTP server、浏览器或 MCP；
- 每个入口显式接收或持有已验证的 skill_root 与 data_root；
- public repository 不提供写方法；
- 未来 MCP adapter 与 HTTP adapter 平级调用同一套 Core。

W1 冻结范围：paths、errors、registry、models 与 schemas/。
后续工作包在此骨架上实现 public_repository(W2)、client_repository(W3A)、
resolver(W3B)、API/UI(W4)、proposal(W5) 与集成(W6)。
"""
from __future__ import annotations

from . import (
    audit,
    catalog_index,
    client_repository,
    errors,
    fingerprint,
    graph_service,
    guard_catalog,
    models,
    paths,
    projection,
    proposal_repository,
    public_repository,
    publisher,
    registry,
    resolver,
    validator,
)

__all__ = [
    "audit",
    "catalog_index",
    "client_repository",
    "errors",
    "fingerprint",
    "graph_service",
    "guard_catalog",
    "models",
    "paths",
    "projection",
    "proposal_repository",
    "public_repository",
    "publisher",
    "registry",
    "resolver",
    "validator",
]
