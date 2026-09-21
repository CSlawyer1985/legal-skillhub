#!/usr/bin/env python3
"""本地 HTTP adapter（Python 标准库，无框架、无 Node）。

契约来源：architecture-contract.md §13（本地服务）；ADR-012（不依赖 Node）。

- 只监听 127.0.0.1，端口由操作系统随机分配；
- 每次启动生成短时高熵会话 token；
- 校验 Host、Origin 与写请求的 CSRF 值；
- 静态资源全部本地；安全响应头统一由 `security.SECURITY_HEADERS` 提供；
- 提供显式停止与空闲超时。
"""
from __future__ import annotations

import json
import mimetypes
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from one_contract_rules import (
    client_repository, proposal_repository, public_repository, resolver,
)

from . import api, security

__all__ = ["RuleStudioServer"]

STATIC_DIR = Path(__file__).resolve().parent / "static"

#: 静态资源后缀 → MIME。不使用 mimetypes 的默认值，避免引入系统差异。
_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json; charset=utf-8",
}


class _Handler(BaseHTTPRequestHandler):
    server_version = "OneContractRuleStudio/1.0"
    protocol_version = "HTTP/1.1"

    # ---- 基础设施 ------------------------------------------------------ #
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        """默认日志会打印完整请求行（可能含 token）。此处关闭普通日志。"""
        return

    @property
    def studio(self) -> "RuleStudioServer":
        return self.server.studio  # type: ignore[attr-defined]

    def _send(self, status: int, body: bytes, content_type: str,
              extra: Optional[Mapping[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in security.SECURITY_HEADERS.items():
            self.send_header(key, value)
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _read_body(self) -> Optional[Mapping[str, Any]]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return None
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return parsed if isinstance(parsed, Mapping) else None

    # ---- 校验 ---------------------------------------------------------- #
    #: 无需会话凭据的路径：静态资源与引导端点。
    #: 理由：页面必须先能加载、才能取得凭据，否则形成鸡生蛋。
    #: 这两类路径**仍强制校验 Host 与 Origin**——足以阻断 DNS rebinding
    #: 与跨站请求；且它们不返回任何私有客户数据（仅凭据本身与静态文件）。
    _TOKEN_EXEMPT = ("/", "/index.html", "/app.js", "/styles.css",
                     "/api/v1/session/bootstrap")

    def _authorize(self, method: str, path: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        ctx = self.studio.security_context
        exempt = path in self._TOKEN_EXEMPT
        try:
            if exempt:
                ctx.authorize(host=self.headers.get("Host"),
                              origin=self.headers.get("Origin"),
                              authorization=None, csrf=None, require_token=False)
            else:
                ctx.authorize(
                    method=method,
                    host=self.headers.get("Host"),
                    origin=self.headers.get("Origin"),
                    authorization=self.headers.get("Authorization"),
                    csrf=self.headers.get("X-CSRF-Token"),
                )
        except security.SecurityError as exc:
            code = 403 if "Host" in str(exc) or "Origin" in str(exc) else 401
            return code, {
                "api_version": api.API_VERSION,
                "request_id": os.urandom(8).hex(),
                "success": False,
                "result": None,
                "error": {"code": "UNAUTHORIZED_LOCAL_REQUEST", "message": str(exc),
                          "field_path": None, "remediation": "请从启动器打开的页面重新操作。"},
            }
        return None

    # ---- 静态资源 ------------------------------------------------------ #
    def _serve_static(self, path: str) -> bool:
        relative = path.lstrip("/") or "index.html"
        candidate = (STATIC_DIR / unquote(relative)).resolve()
        # 路径穿越防护：解析后必须仍在 static 目录内
        if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
            self._json(403, {"api_version": api.API_VERSION, "request_id": os.urandom(8).hex(),
                             "success": False, "result": None,
                             "error": {"code": "PATH_OUTSIDE_DATA_ROOT",
                                       "message": "路径越界，请求已拒绝。",
                                       "field_path": None, "remediation": None}})
            return True
        if not candidate.is_file():
            return False
        content_type = _MIME.get(candidate.suffix, "application/octet-stream")
        self._send(200, candidate.read_bytes(), content_type)
        return True

    # ---- HTTP 方法 ----------------------------------------------------- #
    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._handle("PUT")

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle("DELETE")

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        self.studio.touch()

        denied = self._authorize(method, path)
        if denied is not None:
            status, payload = denied
            self._json(status, payload)
            return

        if not path.startswith("/api/"):
            if self._serve_static(path):
                return
            self._json(404, {"api_version": api.API_VERSION, "request_id": os.urandom(8).hex(),
                             "success": False, "result": None,
                             "error": {"code": "INVALID_SCHEMA", "message": "资源不存在。",
                                       "field_path": None, "remediation": None}})
            return

        request = api.Request(
            method=method,
            path=path,
            query={k: v[0] for k, v in parse_qs(parsed.query).items()},
            body=self._read_body(),
        )
        response = api.dispatch(request, services=self.studio.services)
        self._json(response.status, response.payload)


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address) -> None:
        """客户端提前断连（ConnectionReset/BrokenPipe）属正常关闭，不打印噪声。

        其他异常仍交给默认处理，避免掩盖真实缺陷。
        """
        import sys as _sys

        exc = _sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


class RuleStudioServer:
    """本地 Rule Studio 服务实例。"""

    def __init__(
        self,
        *,
        data_root: Path,
        open_browser: bool = False,
        idle_timeout_seconds: Optional[float] = None,
    ) -> None:
        self.data_root = Path(data_root).expanduser().resolve()
        self.data_root.mkdir(parents=True, exist_ok=True)
        self._open_browser = open_browser
        self._httpd: Optional[_Server] = None
        self._thread: Optional[threading.Thread] = None
        self._last_activity = time.monotonic()
        self._stopping = threading.Event()
        #: 空闲超时秒数。None 取契约默认值；<=0 表示禁用看门狗（仅测试用）。
        self.idle_timeout_seconds = (
            security.IDLE_TIMEOUT_SECONDS if idle_timeout_seconds is None
            else float(idle_timeout_seconds)
        )
        self._watchdog: Optional[threading.Thread] = None
        #: 退出原因：None=仍在运行；idle_timeout / explicit_stop
        self.exit_reason: Optional[str] = None

        self._public = public_repository.PublicRepository()
        self._clients = client_repository.ClientRepository(data_root=self.data_root)
        self._resolver = resolver.Resolver(
            public_repository=self._public, client_repository=self._clients
        )
        # W5：公共提案仓库。走独立工作区，**不触碰公共资产、不进 runtime**。
        self._proposals = proposal_repository.ProposalRepository(
            data_root=self.data_root, public_repository=self._public
        )
        self.security_context: Optional[security.SecurityContext] = None

    # ---- 生命周期 ------------------------------------------------------ #
    def start(self) -> None:
        if self._httpd is not None:
            return
        # 端口 0 = 由操作系统随机分配；绑定 loopback，不监听 0.0.0.0
        self._httpd = _Server(("127.0.0.1", 0), _Handler)
        self._httpd.studio = self  # type: ignore[attr-defined]
        host, port = self._httpd.server_address[0], self._httpd.server_address[1]
        self.security_context = security.SecurityContext(port=port)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self._start_idle_watchdog()

    # ---- 空闲看门狗 ---------------------------------------------------- #
    def _start_idle_watchdog(self) -> None:
        """空闲超时后自动退出（PLAT-008：直接关页 → 空闲超时后退出）。

        契约依据：architecture-contract.md §4（本地服务为短生命周期）、
        safety-and-acceptance.md PLAT-008；并且 `machine_result()` 已声明
        `exit_mode=idle_timeout_or_explicit_stop`——声明必须与行为一致，
        否则机器可读状态在说谎（W7-PLAT-008 的成因：该参数此前收下不用、
        没有任何看门狗线程）。

        看门狗是 daemon 线程，不阻塞解释器退出；轮询间隔随超时缩放
        （短超时用于测试时也能及时响应）。
        """
        timeout = self.idle_timeout_seconds
        if not timeout or timeout <= 0:
            return
        interval = min(1.0, max(0.1, timeout / 10.0))

        def _watch() -> None:
            while not self._stopping.wait(interval):
                if self.idle_seconds >= timeout:
                    self.exit_reason = "idle_timeout"
                    self.stop()
                    return

        self._watchdog = threading.Thread(
            target=_watch, name="rule-studio-idle-watchdog", daemon=True
        )
        self._watchdog.start()

    @property
    def is_running(self) -> bool:
        """服务是否仍在监听（供启动器决定主循环是否继续）。"""
        return self._httpd is not None and not self._stopping.is_set()

    def stop(self) -> None:
        if self._stopping.is_set():
            return  # 幂等：看门狗与调用方可能同时触发
        if self.exit_reason is None:
            self.exit_reason = "explicit_stop"
        self._stopping.set()
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        # 会话随进程结束失效（token 只存在内存）
        self.security_context = None

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    @property
    def idle_seconds(self) -> float:
        return time.monotonic() - self._last_activity

    # ---- 身份 ---------------------------------------------------------- #
    @property
    def address(self) -> Tuple[str, int]:
        if self._httpd is None:
            raise RuntimeError("服务尚未启动。")
        return self._httpd.server_address[0], self._httpd.server_address[1]

    @property
    def url(self) -> str:
        host, port = self.address
        return f"http://{host}:{port}/"

    @property
    def url_is_shareable(self) -> bool:
        """无法自动打开浏览器时，返回可复制 URL 与说明。"""
        return True

    @property
    def session_token(self) -> str:
        if self.security_context is None:
            raise RuntimeError("服务尚未启动。")
        return self.security_context.token

    @property
    def services(self) -> Dict[str, Any]:
        return {
            "public_repository": self._public,
            "client_repository": self._clients,
            "resolver": self._resolver,
            "stop_callback": self.stop,
            "proposal_repository": self._proposals,
            "security_context": self.security_context,
        }
