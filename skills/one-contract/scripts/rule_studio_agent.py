#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 AI Agent 用的 Rule Studio 快捷入口。

**为什么单独有这个脚本**：`open_rule_studio.py` 是给人用的，会打开浏览器；
Agent 通常需要后台启动、等待就绪并以 API 方式调用。本脚本将这些步骤
封装为三条命令，会话凭据由同源 bootstrap 临时取得，不进入 URL、命令行或状态文件。

它复用 `open_rule_studio.py` 的本地服务，不引入第二套规则解析逻辑。

用法
----
    python scripts/rule_studio_agent.py start [--idle-seconds 1800]
        启动服务（不打开浏览器），等就绪后打印 URL 与 PID。
        **token 不打印、不落盘**——需要时由 `api` 子命令在内存中换取。

    python scripts/rule_studio_agent.py api <PATH> [--method GET] [--data '<json>']
        对运行中的实例调用 API。脚本内部完成 bootstrap，自动携带 token、
        CSRF 与同源信息，**会话凭据不经过调用方**。

    python scripts/rule_studio_agent.py status
    python scripts/rule_studio_agent.py stop

合规
----
- 运行状态以 0600 权限写在系统临时目录（仅 url、pid 与日志路径），**不含会话凭据**——
  遵循 architecture-contract §13「token 不放入持久配置或普通日志」；
- 停止服务走本地认证 API；状态过期时不按旧 PID 发信号，避免 PID 复用误伤；
- 不修改任何既有文件；不联网。

退出码：0 成功；1 失败；2 用法错误。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

_HERE = pathlib.Path(__file__).resolve().parent
_LAUNCHER = _HERE / "open_rule_studio.py"
_STATE = pathlib.Path(tempfile.gettempdir()) / "one-contract-rule-studio-agent.json"


def _load_state():
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _save_state(d):
    _STATE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(_STATE, 0o600)
    except OSError:
        pass


def _http(url, *, method="GET", token=None, csrf=None, origin=None,
          data=None, timeout=10):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "::1"):
        raise ValueError("Rule Studio Agent 只允许访问本机回环 HTTP 地址。")
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if csrf:
        req.add_header("X-CSRF-Token", csrf)
    if origin:
        req.add_header("Origin", origin)
    body = None
    if data is not None:
        body = data.encode("utf-8")
        req.add_header("Content-Type", "application/json")
    # 本地 API 不应经过系统 HTTP(S) 代理。某些企业环境没有把
    # 127.0.0.1 写入 NO_PROXY，urllib 会将请求错送到代理并超时。
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, data=body, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def _baseline(url, timeout=1.5):
    """就绪探针——判断服务是否已可用。

    **不能用 `/api/v1/health`**：它需要会话凭据，无 token 时返回 401，
    拿它做探针会永远判定"未就绪"。会话 bootstrap 端点才是无凭据可用的，
    且"能 bootstrap"本身就等价于服务就绪。
    """
    try:
        _, d = _http(f"{url}api/v1/session/bootstrap", timeout=timeout)
        return bool(d.get("success"))
    except Exception:
        return False


def cmd_start(args) -> int:
    st = _load_state()
    if st and _baseline(st.get("url", "")):
        print(f"已在运行：{st['url']}  (pid {st.get('pid')})")
        print(f"如需重启，先执行：{sys.argv[0]} stop")
        return 0

    log = pathlib.Path(tempfile.gettempdir()) / "one-contract-rule-studio-agent.log"
    with open(log, "wb") as fh:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(_LAUNCHER), "--no-browser",
             "--idle-timeout-seconds", str(args.idle_seconds)],
            stdout=fh, stderr=subprocess.STDOUT,
            start_new_session=True,          # 让服务不随本脚本退出而被杀
            cwd=str(_HERE.parent),
        )

    url = None
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            print(f"启动失败，退出码 {proc.returncode}。日志：{log}", file=sys.stderr)
            try:
                print(log.read_text(encoding="utf-8")[-800:], file=sys.stderr)
            except OSError:
                pass
            return 1
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{") and '"url"' in line:
                try:
                    url = json.loads(line)["url"]
                except ValueError:
                    pass
        if url and _baseline(url):
            break
        time.sleep(0.4)

    if not url:
        print(f"超时未就绪。日志：{log}", file=sys.stderr)
        return 1
    if not _baseline(url, timeout=3):
        print(f"服务已启动但健康检查未通过：{url}", file=sys.stderr)
        return 1

    _save_state({"url": url, "pid": proc.pid, "log": str(log)})
    print(f"已启动：{url}")
    print(f"  PID      : {proc.pid}")
    print(f"  日志     : {log}")
    print(f"  空闲自动退出: {args.idle_seconds} 秒")
    print()
    print("调 API（token 由脚本内部换取，不出现在命令行与输出里）：")
    print(f"  python {sys.argv[0]} api /api/v1/rules/tree")
    print()
    print("浏览器访问：直接把上面的 URL 贴进去即可——页面会自行完成会话初始化。")
    return 0


def cmd_api(args) -> int:
    st = _load_state()
    if not st:
        print("没有运行中的实例。先执行 start。", file=sys.stderr)
        return 1
    url = st["url"].rstrip("/")

    # bootstrap：无凭据端点换会话凭据（契约的设计路径）。token 只存活在本进程内。
    try:
        _, b = _http(f"{url}/api/v1/session/bootstrap")
    except Exception as exc:
        print(f"会话初始化失败：{exc}。服务可能已退出，试 status 或重新 start。", file=sys.stderr)
        return 1
    token = (b.get("result") or {}).get("token")
    csrf = (b.get("result") or {}).get("csrf_token")
    origin = (b.get("result") or {}).get("origin")
    if not token or not csrf or not origin:
        print(f"会话初始化未返回完整凭据：{b}", file=sys.stderr)
        return 1

    path = args.path if args.path.startswith("/") else "/" + args.path
    try:
        status, payload = _http(
            f"{url}{path}", method=args.method, token=token,
            csrf=csrf, origin=origin,
            data=args.data, timeout=args.timeout,
        )
    except urllib.error.HTTPError as exc:
        print(json.dumps({"http_status": exc.code,
                          "body": exc.read().decode("utf-8", "replace")},
                         ensure_ascii=False, indent=2))
        return 1
    except Exception as exc:
        print(f"请求失败：{exc}", file=sys.stderr)
        return 1

    print(json.dumps({"http_status": status, "body": payload},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_status(_args) -> int:
    st = _load_state()
    if not st:
        print("未记录运行中的实例。")
        return 0
    alive = _baseline(st.get("url", ""), timeout=3)
    print(json.dumps({"url": st.get("url"), "pid": st.get("pid"),
                      "healthy": alive, "log": st.get("log")},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_stop(_args) -> int:
    st = _load_state()
    if not st:
        print("未记录运行中的实例。")
        return 0
    url = str(st.get("url") or "").rstrip("/")
    stopped = False
    if url and _baseline(url + "/", timeout=3):
        try:
            _, bootstrap = _http(f"{url}/api/v1/session/bootstrap")
            credentials = bootstrap.get("result") or {}
            _http(
                f"{url}/api/v1/service/stop",
                method="POST",
                token=credentials.get("token"),
                csrf=credentials.get("csrf_token"),
                origin=credentials.get("origin"),
                data="{}",
                timeout=5,
            )
            stopped = True
        except Exception:
            # 服务可能在返回响应前完成关闭。只要端口已经不可达，就视为成功。
            stopped = not _baseline(url + "/", timeout=1)
        if stopped:
            print(f"已通过本地服务安全停止：{st.get('url')}")
        else:
            print("停止请求未生效；未向记录的 PID 发送信号，以免误伤其他进程。", file=sys.stderr)
            return 1
    else:
        print("服务已不可达；仅清理过期状态，不向记录的 PID 发送信号。")
    try:
        _STATE.unlink()
    except OSError:
        pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rule Studio 的 Agent 快捷入口")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start", help="启动并等待就绪")
    p.add_argument("--timeout", type=float, default=30.0, help="等待就绪的秒数")
    p.add_argument("--idle-seconds", type=int, default=1800, help="空闲自动退出秒数")
    p.set_defaults(fn=cmd_start)

    p = sub.add_parser("api", help="调用 API（内部换取 token）")
    p.add_argument("path")
    p.add_argument(
        "--method", default="GET",
        choices=("GET", "POST", "PUT", "PATCH", "DELETE"),
    )
    p.add_argument("--data", default=None, help="JSON 字符串")
    p.add_argument("--timeout", type=float, default=20.0)
    p.set_defaults(fn=cmd_api)

    sub.add_parser("status", help="查看状态").set_defaults(fn=cmd_status)
    sub.add_parser("stop", help="停止本脚本启动的实例").set_defaults(fn=cmd_stop)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
