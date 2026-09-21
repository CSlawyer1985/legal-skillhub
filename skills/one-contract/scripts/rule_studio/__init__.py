#!/usr/bin/env python3
"""Rule Studio 本地 HTTP adapter 与静态前端。

契约边界（architecture-contract.md §1）：
- 本包**只做适配**：参数解析、调用 Rules Core、封装 API envelope；
- **不实现任何规则语义**，前端也不复制优先级；
- 不提供公共 active 写路由（RS-HC-001）；
- 仅监听 loopback 与随机端口，静态资源全部本地（无 CDN/遥测）。

未来 MCP adapter 与此包平级，二者都只调用 `one_contract_rules`。
"""
from __future__ import annotations

from . import api, security, server

__all__ = ["api", "security", "server"]
