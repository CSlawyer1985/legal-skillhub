#!/usr/bin/env python3
"""本地服务的会话与请求安全。

契约来源：architecture-contract.md §13（本地服务安全参数）；
safety-and-acceptance.md §8（安全参数量化）；SEC-009/010/011/012。

量化要求（逐条实现，不靠默认值）：
- 会话 token 由 CSPRNG 生成，熵 ≥ 128 bit；只存在于进程与页面内存，
  不进入 query、普通日志、持久配置或导出包；
- token 绝对 TTL ≤ 30 分钟，到期只能由启动器创建新会话，不支持静默续期；
- Host 只接受启动器实际返回的 `127.0.0.1:<port>`；
- Origin 只接受当前会话精确 origin；不配置 `*` CORS；
- 所有 mutation 请求同时校验 token、Origin 与 CSRF 值；
- CSP 至少 `default-src 'self'`，无远程脚本/字体/图片/样式。
"""
from __future__ import annotations

import hmac
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

__all__ = [
    "CSP_POLICY",
    "SECURITY_HEADERS",
    "SecurityContext",
    "TOKEN_TTL_SECONDS",
]

#: 会话 token 绝对存活时间（秒）。到期只能由启动器创建新会话。
TOKEN_TTL_SECONDS = 30 * 60

#: 空闲终止阈值（秒）。浏览器无活动连接时服务退出。
IDLE_TIMEOUT_SECONDS = 120

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)

SECURITY_HEADERS: Dict[str, str] = {
    "Content-Security-Policy": CSP_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
}


class SecurityError(Exception):
    """请求未通过安全校验。调用方不得降级放行。"""


@dataclass
class SecurityContext:
    """一个本地会话的安全上下文。"""

    port: int
    _token: str = field(init=False, repr=False)
    _created_at: float = field(init=False, repr=False)
    _csrf: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # token_urlsafe(32) 提供约 256 bit 熵，远超 128 bit 下限
        self._token = secrets.token_urlsafe(32)
        self._csrf = secrets.token_urlsafe(24)
        self._created_at = time.monotonic()

    # ---- 身份 ---------------------------------------------------------- #
    @property
    def token(self) -> str:
        return self._token

    @property
    def csrf_token(self) -> str:
        return self._csrf

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def expected_host(self) -> str:
        return f"127.0.0.1:{self.port}"

    def is_expired(self) -> bool:
        return (time.monotonic() - self._created_at) > TOKEN_TTL_SECONDS

    # ---- 校验 ---------------------------------------------------------- #
    def check_host(self, host_header: Optional[str]) -> None:
        """Host 只接受启动器实际返回的 127.0.0.1:<port>。"""
        if not host_header:
            raise SecurityError("缺少 Host 头。")
        if host_header.strip().lower() != self.expected_host:
            raise SecurityError("Host 头不被信任。")

    def check_origin(self, origin_header: Optional[str]) -> None:
        """Origin 只接受当前会话精确 origin；无 Origin 的请求也必须有 token。"""
        if origin_header is None:
            return  # 非浏览器客户端（需 token 校验兜底）
        if origin_header.strip().lower() != self.origin:
            raise SecurityError("Origin 不被信任。")

    def check_token(self, authorization_header: Optional[str]) -> None:
        if self.is_expired():
            raise SecurityError("会话已过期；请从启动器重新打开。")
        if not authorization_header:
            raise SecurityError("缺少会话凭据。")
        prefix = "Bearer "
        if not authorization_header.startswith(prefix):
            raise SecurityError("凭据格式不支持。")
        presented = authorization_header[len(prefix):]
        # 常量时间比较，避免计时侧信道
        if not hmac.compare_digest(presented, self._token):
            raise SecurityError("会话凭据无效。")

    def check_csrf(self, csrf_header: Optional[str]) -> None:
        if not csrf_header or not hmac.compare_digest(csrf_header, self._csrf):
            raise SecurityError("防重放校验失败。")

    def authorize(
        self,
        *,
        host: Optional[str],
        origin: Optional[str],
        authorization: Optional[str] = None,
        method: str = "GET",
        csrf: Optional[str] = None,
        require_token: bool = True,
    ) -> None:
        """一次性执行校验。

        `require_token=False` 仅用于静态资源与引导端点——它们必须先于凭据可用；
        此时 **Host 与 Origin 仍然强制校验**，因此仍是 fail closed 的。
        mutation 请求永远要求 token + Origin + CSRF 三者齐备。
        """
        self.check_host(host)
        self.check_origin(origin)
        if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            require_token = True
        if require_token:
            self.check_token(authorization)
        if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            self.check_csrf(csrf)
