#!/usr/bin/env python3
"""One-Contract Rule Studio 启动器。

契约来源：architecture-contract.md §13（启动器 CLI 与一次性 bootstrap）；
safety-and-acceptance.md PLAT-001/002/003/006/010/011。

行为：
- 一条入口启动本地服务并返回可访问 URL；
- 自动打开浏览器失败时，返回普通的 127.0.0.1 本机地址；页面从同源
  bootstrap 端点取得短时凭据，凭据不进入 URL、请求行或普通日志；
- 机器可读结果与普通输出**不含 bearer token**；
- 依赖缺失给出人类可读提示，不生成半初始化数据；
- 不安装或修改用户级 Skill，不联网。
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

_SCRIPT_ROOT = Path(__file__).resolve().parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

__all__ = [
    "LauncherInstance",
    "dependency_hint",
    "main",
    "preflight",
    "start",
]

_API_VERSION = "v1"

#: **不得在模块导入期引入 `one_contract_rules`。**
#: 该包的 `__init__` 会急切导入整条链，其中 `registry` 需要第三方
#: `jsonschema` / `referencing`；若在这里直接 import，缺依赖时会先抛
#: `ModuleNotFoundError`，`main()` 与 `preflight()` 根本没机会执行，
#: 用户看到的是一段 traceback 而不是可执行提示（W7-PLAT-SMOKE-PLAT_011）。
#: 需要时在函数内部惰性导入。

#: 需要检查的第三方依赖。这里是**兜底名单**；主路径改为试导入真实入口，
#: 以便新增依赖时不会因为漏登记而静默失效（此前名单只有 jsonschema，
#: 漏了实际被 registry 使用的 referencing）。
_REQUIRED_MODULES = ("jsonschema", "referencing")

#: 试导入该模块即可覆盖 Rule Studio 的整条运行时导入链
_ENTRY_MODULE = "rule_studio.server"


def dependency_hint(missing: Mapping[str, Any]) -> str:
    """把缺失依赖转成人类可读、可执行的提示。"""
    names = ", ".join(sorted(missing)) or "（未知）"
    return (
        f"Rule Studio 需要以下 Python 依赖但当前环境未安装：{names}。\n"
        "请在项目环境中执行：pip install -r scripts/requirements-rule-studio-dev.txt\n"
        "（产品运行时不需要 Node；浏览器端为原生静态资源。）"
    )


def preflight() -> Dict[str, Any]:
    """检查依赖是否齐备。返回缺失模块映射（空表示齐备）。

    以**试导入真实入口**为主：这样依赖集合由代码本身决定，
    不依赖人工维护的名单（漏登记会让检查形同虚设）。
    名单作为兜底，覆盖入口尚未触及的模块。
    """
    import importlib

    missing: Dict[str, Any] = {}

    try:
        importlib.import_module(_ENTRY_MODULE)
    except ImportError as exc:
        # ModuleNotFoundError.name 是真正缺的顶层模块名；ImportError 无此属性时退回入口名
        missing[getattr(exc, "name", None) or _ENTRY_MODULE] = exc

    for name in _REQUIRED_MODULES:
        try:
            importlib.import_module(name)
        except ImportError as exc:
            missing[name] = exc
    return missing


class LauncherInstance:
    """已启动的 Rule Studio 实例。"""

    def __init__(self, instance: Any, *, opened_in_browser: bool) -> None:
        self._instance = instance
        self._opened = opened_in_browser

    # ---- 身份 ---------------------------------------------------------- #
    @property
    def url(self) -> str:
        return self._instance.url

    @property
    def address(self):
        return self._instance.address

    @property
    def data_root(self) -> Path:
        return self._instance.data_root

    @property
    def session_token(self) -> str:
        return self._instance.session_token

    @property
    def session_id(self) -> str:
        return self._instance.security_context.csrf_token[:12]

    # ---- 交付 ---------------------------------------------------------- #
    def machine_result(self) -> Dict[str, Any]:
        """单行机器可读结果。**不含 bearer token**。

        `exit_mode` 声明的行为必须真实存在：空闲看门狗由
        `RuleStudioServer._start_idle_watchdog` 实现（PLAT-008）。
        另附 `idle_timeout_seconds`，便于运维方知道实际阈值。
        """
        return {
            "api_version": _API_VERSION,
            "url": self.url,
            "session_id": self.session_id,
            "data_root_selected": True,
            "exit_mode": "idle_timeout_or_explicit_stop",
            "idle_timeout_seconds": self._instance.idle_timeout_seconds,
            "opened_in_browser": self._opened,
        }

    @property
    def is_running(self) -> bool:
        return self._instance.is_running

    @property
    def exit_reason(self) -> Optional[str]:
        return self._instance.exit_reason

    def stop(self) -> None:
        self._instance.stop()


def _open_browser(url: str) -> bool:
    """尝试打开浏览器。失败不抛错——改为交付可复制 URL（PLAT-006）。"""
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False


def start(
    *,
    data_root: Optional[Path] = None,
    open_browser: bool = True,
    idle_timeout_seconds: Optional[int] = None,
) -> LauncherInstance:
    """启动本地服务。依赖缺失时抛出人类可读错误，不产生半初始化数据。"""
    missing = preflight()
    if missing:
        raise RuntimeError(dependency_hint(missing))

    # 惰性导入：见文件头说明（模块导入期不得引入 one_contract_rules）
    from one_contract_rules import paths

    resolved_root = paths.resolve_data_root(data_root)

    from rule_studio import server as studio_server

    instance = studio_server.RuleStudioServer(
        data_root=resolved_root,
        open_browser=open_browser,
        # 透传空闲超时：此前该参数在启动器里被收下却从未使用，
        # 服务永不因空闲退出，而 machine_result() 仍声明会退出（W7-PLAT-008）。
        idle_timeout_seconds=idle_timeout_seconds,
    )
    instance.start()

    opened = _open_browser(instance.url) if open_browser else False
    launcher = LauncherInstance(instance, opened_in_browser=opened)

    if open_browser and not opened:
        print(f"无法自动打开浏览器。请复制以下地址访问：\n{launcher.url}")
    return launcher


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="打开 One-Contract 规则面板（本地、离线）。"
    )
    parser.add_argument("--data-dir", default=None,
                        help="外部数据根；缺省读取 ONE_CONTRACT_DATA_DIR 或平台默认目录")
    parser.add_argument("--no-browser", action="store_true",
                        help="不自动打开浏览器，返回可复制 URL")
    parser.add_argument("--read-only", action="store_true",
                        help="只读模式（本版仍允许客户草稿写入，仅用于提示）")
    parser.add_argument("--idle-timeout-seconds", type=int, default=None,
                        help="空闲超时秒数；关闭页面后自动退出")
    parser.add_argument("--dry-run", action="store_true",
                        help="启动后立即停止并打印机器结果（跨平台代理用）")
    args = parser.parse_args(argv)

    missing = preflight()
    if missing:
        print(dependency_hint(missing), file=sys.stderr)
        return 2

    try:
        launcher = start(
            data_root=Path(args.data_dir) if args.data_dir else None,
            open_browser=not args.no_browser,
            idle_timeout_seconds=args.idle_timeout_seconds,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ImportError as exc:
        # 兜底：任何未被 preflight 覆盖的导入缺失，也给人类可读提示而非 traceback
        print(dependency_hint({getattr(exc, "name", None) or str(exc): exc}),
              file=sys.stderr)
        return 2

    print(json.dumps(launcher.machine_result(), ensure_ascii=False))
    if args.dry_run:
        launcher.stop()
        return 0

    print(f"\nRule Studio 已启动：{launcher.url}")
    print(
        f"空闲 {launcher._instance.idle_timeout_seconds:.0f} 秒后自动退出；"
        "或按 Ctrl+C 立即停止。\n"
    )
    try:
        import time

        # 主循环跟随服务状态：空闲看门狗触发退出后，进程随之结束（PLAT-008）。
        while launcher.is_running:
            time.sleep(0.5)
        print(f"服务已停止（原因：{launcher.exit_reason}）。")
    except KeyboardInterrupt:
        pass
    finally:
        launcher.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
