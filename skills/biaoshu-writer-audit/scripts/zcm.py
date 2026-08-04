#!/usr/bin/env python3
"""百炼®标书开放 API 轻客户端（thin client）。

封装「提交 → 轮询 → 取结果」异步模型，零第三方依赖（仅标准库）。
凭证与环境通过环境变量或本地凭证文件传入：
  ZCM_APP_KEY  App Key（形如 bk_live_xxxxx，必填）
  ZCM_BASE     Base URL，默认生产 https://biaoshu.zhiliaobiaoxun.com/api/open/v1
  ZCM_CONFIG   凭证文件路径，默认 skill 内 config.json（含 app_key/可选 base/output_dir）
  ZCM_OUTPUT_DIR  成品标书 .docx 存放目录；未设时默认 skill 同级的 biaoshu-bailian-files/

凭证读取优先级：环境变量 > skill 内 config.json（回退旧 ~/.zcm/credentials.json）。
config.json 权限 600，含真实 Key，**勿上传发布包**（发布包不含配置文件；模板结构见 references/usage.md）。
经环境变量首次提供凭证时自动落盘到 config.json；也可用 login 显式保存、logout 清除。
成品存放目录优先级：generate -o 显式路径 > ZCM_OUTPUT_DIR > config.json 的 output_dir > 默认 biaoshu-bailian-files。

子命令：
  login      --app-key ..  保存凭证到 skill 内 config.json（输一次，下次免输）
  register   [--phone ..]  skill 内手机号注册/登录，换取并保存 App Key
  logout                   删除 config.json 里的凭证
  me                                查连通性与积分余额
  interpret  <file|https-url>       智能解读招标文件 → 打印完整解读结果（含 8 维度+控标洞察）
  packages   <project_id>           抽取分包 → 打印 packages JSON（供用户挑选）
  generate   <project_id> [opts]    生成成品标书 → 下载 .docx
  compliance <project_id> <f...>    合规审查投标文件 → 打印完整合规结果
  report     --job <id> | --in f    把解读/合规结果渲染成 HTML/Word 报告
  experience --type .. --stage ..   把本阶段经验总结回传平台沉淀（用户同意后）
  feedback   --category .. ...      上报使用问题（用户同意后；不含文件与个人信息）

interpret / compliance 可加 --report html|docx|both 在取结果后直接出报告。
  job        <job_id>               查单个任务状态（不轮询）
  result     <job_id> [-o file]     取任务结果
  cancel     <job_id>               取消任务

提交类子命令（interpret/packages/generate/compliance）默认自动轮询到终态，
加 --no-wait 只提交并打印 job_id。
"""
import argparse
import hashlib
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE = "https://biaoshu.zhiliaobiaoxun.com/api/open/v1"

# skill 版本（单一事实来源）。适配的后端 API 版本与契约快照见 references/api.md 顶部。
SKILL_VERSION = "2.2.0"
API_TARGET = "/api/open/v1"
CONTRACT_SNAPSHOT = "2026-07-20"

# 渠道码：主线留空（不带渠道）；发布各渠道副本时按平台 excel 注入（如 SkillHub 主基线注入 "s111"）。
# 非空时：免费试用/注册请求体带 channel（后端落库标记来源），官网/绑定/充值链接追加 ?ch=。
CHANNEL = "s117"
SIGNUP_URL = "https://biaoshu.zhiliaobiaoxun.com/" + (f"?ch={CHANNEL}" if CHANNEL else "")

# 文档第 6 节错误码 → 友好提示
ERROR_HINTS = {
    "missing_credentials": "缺少鉴权头：请设置环境变量 ZCM_APP_KEY。",
    "invalid_credentials": "App Key 不正确：核对凭证，或到官网 https://biaoshu.zhiliaobiaoxun.com/ 左侧菜单『Skill 接入 → 获取 APP Key』重置 Key（重置后旧 Key 立即失效）。",
    "account_disabled": "凭证或用户已被停用，请联系百炼®标书管理员。",
    "insufficient_points": "积分余额不足：本次不扣费也不产出，请到官网充值后重试。",
    "not_found": "404：多为开放 API 总开关未开（整层 404），请联系超级管理员在『系统设置』开启；或句柄不存在。",
    "job_not_found": "任务句柄不存在或非本人，请核对 job_id。",
    "project_not_found": "project 不存在或非本人，请核对 project_id（由智能解读产出）。",
    "result_expired": "结果已过期（默认约 7 天 TTL），需重新生成。",
    "invalid_job_state": "任务状态不允许此操作：任务未成功就取结果 / 未解读就生成 / 未抽包就 generate。",
    "validation_error": "入参校验失败：文件缺失或类型不支持 / file_url 非 https 或指向内网 / 缺 package_ids 等。",
    "rate_limited": "触发限流（60 req/min）：稍后退避重试（参考 Retry-After）。",
    "too_many_concurrent_jobs": "并发任务超限（≤3）：等已有任务结束再提交。",
    "daily_quota_exceeded": "今日沉淀已达上限（每天最多 20 条），明天可以继续。",
    "internal_error": "服务端异常：稍后重试或反馈百炼®标书。",
    "fingerprint_required": "设备特征采集失败，无法自动试用：请改用官网获取 App Key（官网注册登录后，在『Skill 接入 → 获取 APP Key』查看，把 Key 粘贴给我保存即可）。",
    "trial_limit_exceeded": "当前网络已开通过试用账号（每个网络/设备限 1 个）：请改用官网获取 App Key（官网注册登录后，在『Skill 接入 → 获取 APP Key』查看，把 Key 粘贴给我保存即可）。",
}

REGISTER_GUIDE = f"""\
还没配置 App Key —— 这是用百炼®标书写作助手出解读/标书/合规的唯一开关。
好消息：新用户零输入就能免费试用（赠 200 积分），开通后这份文件马上就能出解读。
拿 Key 有两种方式，**均由助手代跑，用户无需敲任何命令**（拿到后自动保存，下次免输）：

  A) 免费试用（零输入，最省事，送 200 积分）：
       征得用户同意后，助手直接开通（自动采集设备特征，App Key 自动保存）；绑定手机号可再送 200。

  B) 官网获取 App Key（试用积分用完、或无法自动试用时）：
       打开官网 {SIGNUP_URL} 用手机号 + 短信验证码注册并登录（新用户赠积分），
       点左侧菜单『Skill 接入 → 获取 APP Key』，在弹出面板中查看/复制 App Key
       （首次打开自动生成，形如 bk_live_xxxxx，重置后旧 Key 立即失效）。
       用户把 Key 直接粘贴到对话里即可，例如：
       「我的 App Key 是 bk_live_xxxxx，帮我保存一下」（助手代为保存，下次免输）。
"""

BALANCE_GUIDE = """\
积分已用完，请选择：
  1) 绑定手机号再领 200 积分（skill 内，手机号+验证码，App Key 不变）
  2) 前往官网充值，或粘贴新 App Key 到此处
  q) 退出
"""


def die(msg, code=1):
    print(msg, file=sys.stderr, flush=True)
    sys.exit(code)


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def creds_path():
    """凭证文件：默认 skill 内 config.json；ZCM_CONFIG 可覆盖路径。"""
    env = os.environ.get("ZCM_CONFIG", "").strip()
    return env or os.path.join(skill_dir(), "config.json")


def _legacy_creds_path():
    """旧位置 ~/.zcm/credentials.json，仅作只读回退（兼容已有安装）。"""
    home = os.environ.get("ZCM_HOME", "").strip() or os.path.join(
        os.path.expanduser("~"), ".zcm")
    return os.path.join(home, "credentials.json")


def load_creds_file():
    """读凭证：先 skill 内 config.json，再回退旧 ~/.zcm/credentials.json。"""
    for p in (creds_path(), _legacy_creds_path()):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (FileNotFoundError, ValueError, OSError):
            continue
    return {}


def save_creds_file(data):
    """把凭证写入 skill 内 config.json（文件权限 600）。⚠️ 含真实 Key，勿上传发布包。"""
    path = creds_path()
    d = os.path.dirname(path)
    try:
        if d:
            os.makedirs(d, exist_ok=True)
    except OSError:
        pass
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def get_creds():
    """返回 App Key。未配置时引导『自动试用 / 官网拿 Key 粘贴』。"""
    stored = load_creds_file()
    env_key = os.environ.get("ZCM_APP_KEY", "").strip()
    app_key = env_key or str(stored.get("app_key", "")).strip()
    if not app_key:
        return _guide_missing_credentials()
    if env_key and env_key != stored.get("app_key"):
        save_creds_file(dict(stored, app_key=env_key))
        log(f"凭证已保存到 {creds_path()}（权限 600），下次无需再输。")
    return app_key


def _guide_missing_credentials():
    """无 App Key：交互环境二选一（试用 / 粘贴 Key）并返回 Key；
    非交互环境打印获取指引后退出（由 Claude 转达用户，再走 trial / login）。"""
    if not sys.stdin.isatty():
        die(REGISTER_GUIDE, code=2)
    log(REGISTER_GUIDE)
    choice = input("请选择 [1] 免费试用（自动开通）  [2] 已有 App Key 直接粘贴  [q] 退出：").strip().lower()
    if choice == "1":
        _trial_flow()
        return str(load_creds_file().get("app_key", "")).strip()
    if choice == "2":
        new_key = input("请粘贴 App Key（形如 bk_live_xxxxx）：").strip()
        if not new_key:
            die("未输入 App Key，已退出。", code=2)
        save_creds_file(dict(load_creds_file(), app_key=new_key))
        log(f"App Key 已保存到 {creds_path()}（权限 600）。")
        return new_key
    sys.exit(0)


def _collect_device():
    """采集 6 项设备特征；任一失败置空串，绝不中断。"""
    import getpass
    import platform as _platform
    import socket
    import uuid as _uuid

    def _try(fn):
        try:
            v = fn()
            return str(v).strip() if v else ""
        except Exception:
            return ""

    def _mac():
        node = _uuid.getnode()
        if (node >> 40) & 0x01:   # 组播位=1：随机 MAC，视为采集失败
            return ""
        return hashlib.sha256(str(node).encode("utf-8")).hexdigest()

    return {
        "hostname": _try(socket.gethostname),
        "platform": _try(_platform.system),
        "arch": _try(_platform.machine),
        "username": _try(getpass.getuser),
        "home_path": _try(lambda: os.path.expanduser("~")),
        "mac_hash": _try(_mac),
    }


def _trial_flow():
    """免费试用：设备指纹自动注册 → 拿 App Key 写入 config.json。幂等：同设备返回原 Key。"""
    body = {"device": _collect_device()}
    if CHANNEL:
        body["channel"] = CHANNEL
    resp = _anon_json("POST", "/trial-accounts", json_body=body)
    key = str(resp.get("app_key", "")).strip()
    if not key:
        die("试用开通失败：接口未返回 App Key。")
    save_creds_file(dict(load_creds_file(), app_key=key))
    balance = resp.get("wallet_balance", 0)
    if resp.get("is_new"):
        log(f"试用开通成功！当前积分：{balance}，App Key 已保存到 {creds_path()}（权限 600）。")
        log("绑定手机号可再送 200 积分（把手机号给我即可在 skill 内绑定，App Key 不变）。")
    else:
        log(f"本设备已有试用账号，已恢复原 App Key，当前积分：{balance}。")


def _register_flow(phone=None, code=None):
    """skill 内手机号注册/登录：发验证码 → 校验 → 拿 App Key 写入 config.json。
    phone/code 可从外部传入（如 --phone/--code 参数），避免重复发短信。
    """
    if not phone:
        if not sys.stdin.isatty():
            die("非交互环境请传参：python3 scripts/zcm.py register --phone 手机号 [--code 验证码]", code=2)
        phone = input("手机号：").strip()
    if not phone:
        die("手机号不能为空。")
    if not code:
        _anon_json("POST", "/auth/send-sms", json_body={"phone": phone})
        log("验证码已发送，5 分钟内有效。")
        if not sys.stdin.isatty():
            die("非交互环境获取验证码后请带 --code 重试：python3 scripts/zcm.py register --phone 手机号 --code 验证码", code=2)
        code = input("验证码：").strip()
    if not code:
        die("验证码不能为空。")
    body = {"phone": phone, "code": code}
    if CHANNEL:
        body["channel"] = CHANNEL
    stored_key = str(load_creds_file().get("app_key", "")).strip()
    if stored_key:
        body["trial_app_key"] = stored_key   # 已有试用 Key：请求绑定（平台校验，非试用 Key 自动忽略）
    resp = _anon_json("POST", "/auth/register", json_body=body)
    new_key = str(resp.get("app_key", "")).strip()
    balance = resp.get("wallet_balance", 0)
    is_new = resp.get("is_new_user", True)
    if not new_key:
        die("注册失败：接口未返回 App Key。")
    save_creds_file(dict(load_creds_file(), app_key=new_key))
    if resp.get("bound"):
        log(f"绑定成功！手机号已关联当前试用账号（App Key 不变），+200 积分，当前积分：{balance}。")
    elif is_new:
        log(f"注册成功！当前积分：{balance}，App Key 已保存。")
    else:
        log(f"该手机号已注册，已切换到对应账号，当前积分：{balance}。")


def _site_base():
    """站点根地址（剥掉 /api/... 段），用于拼注册/绑定/充值网页链接。"""
    b = base_url()
    return b.split("/api/", 1)[0].rstrip("/") if "/api/" in b else "https://biaoshu.zhiliaobiaoxun.com"


def _with_ch(url):
    """CHANNEL 非空时给网页链接追加渠道码 ch；为空原样返回。"""
    if not CHANNEL:
        return url
    return f"{url}{'&' if '?' in url else '?'}ch={CHANNEL}"


def _current_key():
    """当前 App Key（环境变量优先，其次 config.json）；取不到返回空串，不报错。"""
    return os.environ.get("ZCM_APP_KEY", "").strip() or str(load_creds_file().get("app_key", "")).strip()


def _bind_register_url(err=None):
    """『注册即绑定』网页链接：平台 402 若下发 bind_url 优先用；否则用当前 App Key 本地拼。
    形如 https://biaoshu.zhiliaobiaoxun.com/register?bind_key=bk_live_xxx —— 用户在网页注册手机号即可把
    新账号绑定到这枚 App Key（积分归属不变），无需回到终端。"""
    url = (err or {}).get("bind_url", "")
    if url:
        return url
    key = _current_key()
    base = _site_base()
    return _with_ch(f"{base}/register?bind_key={key}" if key else f"{base}/register")


def _guide_insufficient_balance(err=None):
    """积分用完引导：未绑手机号 → 先提示绑定送 200；已绑 → 直接充值。
    绑定两条路：① 让用户提供手机号，由 skill 发验证码完成绑定；② 用户自助打开『注册即绑定』网页链接。
    ⚠️ 切勿把 `python3 scripts/zcm.py register` 这类命令或 exit 码抛给用户——只告诉用户下一步需要提供什么。"""
    err = err or {}
    # 充值页凭 bind_key 定位账户，兜底链接也必须带当前 App Key
    _key = _current_key()
    recharge_url = err.get("recharge_url") or _with_ch(
        f"{_site_base()}/recharge?bind_key={_key}" if _key else f"{_site_base()}/recharge"
    )
    phone_bound = bool(err.get("phone_bound"))
    bind_url = _bind_register_url(err)
    if not sys.stdin.isatty():
        if phone_bound:
            die(f"积分不足，请到官网充值后重试：{recharge_url}", code=1)
        die(
            "积分不足，可二选一继续（App Key 保持不变）：\n"
            f"  1) 绑定手机号再领 200 积分：把手机号给我，我来发验证码完成绑定；或自助打开 {bind_url} 注册即绑定。\n"
            f"  2) 充值：{recharge_url}",
            code=1,
        )
    log(BALANCE_GUIDE)
    if bind_url and not phone_bound:
        log(f"  （网页注册即绑定：{bind_url}）")
    log(f"  （官网充值地址：{recharge_url}）")
    choice = input("请输入选项：").strip().lower()
    if choice == "1":
        _register_flow()
        log("请重新提交任务（积分已到账）。")
        sys.exit(0)
    elif choice == "2":
        new_key = input("请粘贴新的 App Key（直接回车则去官网充值）：").strip()
        if new_key:
            save_creds_file(dict(load_creds_file(), app_key=new_key))
            log("新 App Key 已保存，请重新提交任务。")
        sys.exit(0)
    else:
        sys.exit(0)


def base_url():
    env_base = os.environ.get("ZCM_BASE", "").strip()
    if env_base:
        return env_base.rstrip("/")
    stored = load_creds_file()
    return str(stored.get("base") or DEFAULT_BASE).rstrip("/")


def skill_dir():
    """SKILL 包根目录（scripts/ 的上一级）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_output_dir():
    """未配置时的默认成品目录：skill 包同级的 biaoshu-bailian-files/。"""
    return os.path.join(os.path.dirname(skill_dir()), "biaoshu-bailian-files")


def output_dir():
    """解析成品标书存放目录并确保存在。优先级：env > 凭证文件 > 默认。"""
    d = os.environ.get("ZCM_OUTPUT_DIR", "").strip()
    if not d:
        d = str(load_creds_file().get("output_dir") or "").strip()
    d = os.path.expanduser(d) if d else default_output_dir()
    os.makedirs(d, exist_ok=True)
    return d


def projects_path():
    home = os.environ.get("ZCM_HOME", "").strip() or os.path.join(
        os.path.expanduser("~"), ".zcm")
    return os.path.join(home, "projects.json")


def _load_projects():
    try:
        with open(projects_path(), "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (FileNotFoundError, ValueError, OSError):
        return {}


def remember_tender(tender_filename, project_id=None, job_id=None):
    """interpret 时把招标文件名按 project_id / job_id 记到本地，供后续报告自动命名。"""
    if not tender_filename:
        return
    name = os.path.basename(str(tender_filename).rstrip("/"))
    d = _load_projects()
    by_pid = d.setdefault("by_project", {})
    by_job = d.setdefault("by_job", {})
    if project_id is not None:
        by_pid[str(project_id)] = name
    if job_id is not None:
        by_job[str(job_id)] = name
    path = projects_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def recall_tender(project_id=None, job_id=None):
    """按 job_id / project_id 回查本地记下的招标文件名；查不到返回 None。"""
    d = _load_projects()
    if job_id is not None:
        v = d.get("by_job", {}).get(str(job_id))
        if v:
            return v
    if project_id is not None:
        v = d.get("by_project", {}).get(str(project_id))
        if v:
            return v
    return None


def _headers(extra=None):
    h = {"X-App-Key": get_creds()}
    if extra:
        h.update(extra)
    return h


def _handle_http_error(e):
    """把 HTTPError 转成友好提示并退出。"""
    body = b""
    try:
        body = e.read()
    except Exception:
        pass
    code = None
    msg = ""
    err = {}
    try:
        payload = json.loads(body.decode("utf-8"))
        # 兼容嵌套 {"error": {...}} 和平铺 {"code": ...} 两种格式
        err = payload.get("error") or payload
        code = err.get("code")
        msg = err.get("message", "")
    except Exception:
        msg = body.decode("utf-8", "replace")
    # 积分不足：走双路径引导而非直接报错退出
    if e.code == 402 or code in ("insufficient_balance", "insufficient_points"):
        _guide_insufficient_balance(err)
        return
    hint = ERROR_HINTS.get(code, "")
    retry_after = e.headers.get("Retry-After") if e.headers else None
    lines = [f"请求失败 HTTP {e.code}" + (f" [{code}]" if code else "")]
    if msg:
        lines.append(f"  message: {msg}")
    if hint:
        lines.append(f"  → {hint}")
    if retry_after:
        lines.append(f"  → Retry-After: {retry_after}s")
    die("\n".join(lines), code=1)


def _anon_json(method, path, *, json_body=None, headers=None):
    """无鉴权请求，用于 /auth/send-sms、/auth/register 等注册类接口。"""
    url = base_url() + path
    data = None
    hdrs = dict(headers or {})
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except urllib.error.URLError as e:
        die(f"网络错误：{e.reason}", code=1)


def request_json(method, path, *, headers=None, data=None, json_body=None):
    """发起请求并解析 JSON 响应。data 为已编码 bytes（如 multipart）。"""
    url = base_url() + path
    hdrs = _headers(headers)
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except urllib.error.URLError as e:
        die(f"网络错误：{e.reason}\n  → 检查 ZCM_BASE（当前 {base_url()}）与网络连通性。", code=1)


def encode_multipart(fields, files):
    """fields: dict[str,str]; files: list[(field_name, filepath)]。返回 (body_bytes, content_type)。"""
    boundary = "----zcm" + uuid.uuid4().hex
    crlf = b"\r\n"
    buf = bytearray()
    for name, value in (fields or {}).items():
        buf += b"--" + boundary.encode() + crlf
        buf += f'Content-Disposition: form-data; name="{name}"'.encode() + crlf + crlf
        buf += str(value).encode("utf-8") + crlf
    for field_name, filepath in files:
        if not os.path.isfile(filepath):
            die(f"文件不存在：{filepath}")
        fname = os.path.basename(filepath)
        ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
        with open(filepath, "rb") as f:
            content = f.read()
        buf += b"--" + boundary.encode() + crlf
        buf += (
            f'Content-Disposition: form-data; name="{field_name}"; filename="{fname}"'
        ).encode("utf-8") + crlf
        buf += f"Content-Type: {ctype}".encode() + crlf + crlf
        buf += content + crlf
    buf += b"--" + boundary.encode() + b"--" + crlf
    return bytes(buf), f"multipart/form-data; boundary={boundary}"


def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


# 上传大小上限（百炼®标书限制）
MAX_TENDER_MB = 50      # 招标文件
MAX_BID_MB = 1024       # 投标文件


def _check_size(path, max_mb, label):
    """本地文件大小上限校验，超限直接报错。"""
    try:
        sz = os.path.getsize(path)
    except OSError:
        return
    if sz > max_mb * 1024 * 1024:
        die(f"{label}超过大小上限：{sz / 1024 / 1024:.1f} MB > {max_mb} MB"
            f"（{os.path.basename(path)}）。请压缩或拆分后重试。")


def download_to_local(url, max_mb=None):
    """云端文件先下载到本地再处理：拿到真实文件名、绕开后端远程下载的 https/内网/大小限制。

    max_mb 给定时，先看 Content-Length 提前拦截超大文件；返回本地文件路径（落 _downloads/）。
    """
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    name = os.path.basename(urllib.parse.unquote(parsed.path)) or "download"
    dest_dir = os.path.join(output_dir(), "_downloads")
    os.makedirs(dest_dir, exist_ok=True)
    local = os.path.join(dest_dir, name)
    req = urllib.request.Request(url, headers={"User-Agent": "zcm-client"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            clen = resp.headers.get("Content-Length") if resp.headers else None
            if max_mb and clen and clen.isdigit() and int(clen) > max_mb * 1024 * 1024:
                die(f"云端文件超过大小上限：{int(clen) / 1024 / 1024:.1f} MB > {max_mb} MB（{url}）。")
            cd = (resp.headers.get("Content-Disposition", "") if resp.headers else "") or ""
            if "filename=" in cd:  # Content-Disposition 文件名优先（通常带扩展名）
                fn = os.path.basename(urllib.parse.unquote(
                    cd.split("filename=")[-1].split(";")[0].strip().strip('"\'')))
                if fn:
                    local = os.path.join(dest_dir, fn)
            with open(local, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
    except urllib.error.HTTPError as e:
        die(f"下载云端文件失败 HTTP {e.code}：{url}", code=1)
    except urllib.error.URLError as e:
        die(f"下载云端文件失败：{e.reason}（{url}）", code=1)
    log(f"已下载云端文件到本地：{local}")
    return local


def poll(job_id, interval=5, timeout=3600):
    """轮询任务到终态。返回最终状态 dict。"""
    deadline = time.time() + timeout
    last = ""
    while True:
        st = request_json("GET", f"/jobs/{job_id}")
        status = st.get("status")
        prog = st.get("progress") or {}
        line = f"[{job_id}] status={status}"
        if prog:
            line += f" {prog.get('percent', '?')}% {prog.get('stage_label', prog.get('stage', ''))}"
        if line != last:
            log(line)
            last = line
        if status == "succeeded":
            return st
        if status in ("failed", "canceled"):
            err = st.get("error") or {}
            ecode = err.get("code", "")
            hint = ERROR_HINTS.get(ecode, "")
            extra = ""
            if ecode == "worker_lost":
                extra = "（服务重启导致，需重新提交）"
            die(f"任务 {status}：{ecode} {err.get('message','')} {hint}{extra}".strip(), code=1)
        if time.time() > deadline:
            die(f"轮询超时（>{timeout}s），任务仍未完成。可稍后用 `job {job_id}` 继续查看。", code=1)
        time.sleep(interval)


def idempotency_header(args):
    if getattr(args, "idempotency_key", None):
        return {"Idempotency-Key": args.idempotency_key}
    return {}


# ---------------- 子命令 ----------------

_RISK_ZH = {"high": "高风险", "review": "待复核", "tip": "提示"}
_PRIORITY_ZH = {"high": "高", "medium": "中", "low": "低"}
# 按字段名分别映射英文枚举 → 中文（仅这些键转换，其余原样）
_ENUM_ZH = {"risk_level": _RISK_ZH, "priority": _PRIORITY_ZH}


def zh_risk(obj):
    """递归把 risk_level(high/review/tip)、priority(high/medium/low) 等枚举值转中文（输出展示用）。"""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            m = _ENUM_ZH.get(k)
            if m and isinstance(v, str) and v in m:
                out[k] = m[v]
            else:
                out[k] = zh_risk(v)
        return out
    if isinstance(obj, list):
        return [zh_risk(x) for x in obj]
    return obj


def _platform_reminder():
    """输出平台查看提示，在每次输出结果文件路径时调用。"""
    log("📎 结果同步在百炼®标书平台查看：https://biaoshu.zhiliaobiaoxun.com/")


def _report_balance():
    """任务完成后播报当前剩余积分；查询失败静默，绝不影响已完成的任务。"""
    try:
        bal = request_json("GET", "/me").get("wallet_balance")
    except BaseException:
        return
    if bal is not None:
        log(f"💰 当前剩余积分：{bal}")


def _maybe_report(result_response, fmt, label, tender_name=None):
    """interpret/compliance 取结果后，若指定 --report 则渲染报告到成品目录。

    报告默认名 = 招标文件名_{智能解读|合规审查}（tender_name 提供时）。
    """
    if not fmt:
        return
    import report as _report
    d = output_dir()
    try:
        outs = _report.generate(result_response, fmt=fmt, out_dir=d, tender_name=tender_name)
    except Exception as e:  # 渲染失败不应让整条命令崩
        log(f"⚠️ 报告生成失败：{e}")
        return
    for p in outs:
        log(f"已生成{label}报告：{os.path.abspath(p)}")
    log(f"报告所在目录：{os.path.abspath(d)}")
    _platform_reminder()


def cmd_report(args):
    import report as _report
    if args.in_file:
        with open(args.in_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = request_json("GET", f"/jobs/{args.job}/result")
    # 招标文件名：--name > 本地缓存（job_id / 结果里的 project_id|document_id）> 结果自动识别
    tender = args.name
    if not tender:
        res = data.get("result") if isinstance(data, dict) else {}
        res = res if isinstance(res, dict) else {}
        pid = res.get("project_id") or (res.get("compliance") or {}).get("document_id") or res.get("document_id")
        tender = recall_tender(job_id=args.job, project_id=pid)
    out_dir = args.out_dir or output_dir()
    outs = _report.generate(data, service=args.service, fmt=args.format,
                            out_dir=out_dir, basename=args.basename, tender_name=tender)
    for p in outs:
        log(f"已生成报告：{os.path.abspath(p)}")
        print(os.path.abspath(p))
    log(f"报告所在目录：{os.path.abspath(out_dir)}")
    _platform_reminder()


def cmd_login(args):
    stored = load_creds_file()
    if args.app_key:
        stored["app_key"] = args.app_key.strip()
    if args.base:
        stored["base"] = args.base.strip().rstrip("/")
    if args.output_dir:
        stored["output_dir"] = os.path.expanduser(args.output_dir.strip())
    if not stored.get("app_key"):
        die("login 需要 --app-key（App Key 形如 bk_live_xxxxx）。")
    save_creds_file(stored)
    log(f"凭证已保存到 {creds_path()}（权限 600），下次免输。")
    if stored.get("output_dir"):
        log(f"成品标书默认存放目录：{stored['output_dir']}")


def cmd_logout(args):
    try:
        os.remove(creds_path())
        log(f"已删除凭证文件 {creds_path()}。")
    except FileNotFoundError:
        log("没有已保存的凭证文件。")


def cmd_me(args):
    data = request_json("GET", "/me")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    bal = data.get("wallet_balance")
    if bal is not None:
        log(f"积分余额：{bal}")


def _precheck_balance():
    """计费操作（解读/生成/合规）提交前先查余额：积分 < 1 直接走充值/绑定引导，不发起任务。

    平台侧同样有 402 闸门兜底；此处提前拦截，避免白传大文件。
    """
    resp = request_json("GET", "/me")
    balance = int(resp.get("wallet_balance", 0) or 0)
    if balance < 1:
        log(f"当前积分余额：{balance}，不足以发起操作（需 ≥ 1）。")
        _guide_insufficient_balance({"wallet_balance": balance})


def _submit_interpret(args):
    extra = idempotency_header(args)
    if is_url(args.source):
        args.source = download_to_local(args.source, max_mb=MAX_TENDER_MB)   # 云端先下载到本地
    _check_size(args.source, MAX_TENDER_MB, "招标文件")
    body, ctype = encode_multipart(None, [("file", args.source)])
    return request_json("POST", "/interpretations",
                        headers={**extra, "Content-Type": ctype}, data=body)


def cmd_interpret(args):
    _precheck_balance()
    resp = _submit_interpret(args)
    job_id = resp["job_id"]
    log(f"已提交解读任务 job_id={job_id}")
    if args.no_wait:
        print(job_id)
        return
    poll(job_id, interval=args.interval)
    result = request_json("GET", f"/jobs/{job_id}/result")
    print(json.dumps(zh_risk(result), ensure_ascii=False, indent=2))
    pid = (result.get("result") or {}).get("project_id")
    if pid is not None:
        log(f"project_id={pid}  （后续抽包/生成/合规都复用它）")
    # 招标文件名：优先 --name，否则取上传文件名（路径或 URL 末段）
    tender = args.name or os.path.basename(args.source.rstrip("/"))
    # 记到本地，供后续 report --job / compliance 自动命名（无需再传 --name）
    remember_tender(tender, project_id=pid, job_id=job_id)
    _maybe_report(result, args.report, "解读", tender_name=tender)
    _report_balance()


def cmd_packages(args):
    extra = idempotency_header(args)
    resp = request_json("POST", f"/bid-documents/{args.project_id}/packages", headers=extra)
    job_id = resp["job_id"]
    log(f"已提交抽包任务 job_id={job_id}")
    if args.no_wait:
        print(job_id)
        return
    poll(job_id, interval=args.interval)
    result = request_json("GET", f"/jobs/{job_id}/result")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_generate(args):
    _precheck_balance()
    body = {}
    if args.package_ids:
        body["package_ids"] = [int(x) for x in args.package_ids.split(",") if x.strip()]
    if args.total_pages:
        body["total_pages"] = args.total_pages
    extra = idempotency_header(args)
    resp = request_json("POST", f"/bid-documents/{args.project_id}/generate",
                        headers=extra, json_body=body)
    job_id = resp["job_id"]
    log(f"已提交生成任务 job_id={job_id}（耗时较长，请耐心轮询）")
    if args.no_wait:
        print(job_id)
        return
    poll(job_id, interval=args.interval, timeout=args.timeout)
    if args.output:
        out = args.output
    else:
        # 成品标书命名：招标文件名_投标文件.docx（招标文件名来自 --name 或本地缓存）
        tender = args.name or recall_tender(project_id=args.project_id)
        from report import _safe_name as _sn
        fname = (f"{_sn(tender)}_投标文件.docx" if tender else f"bid_{job_id}.docx")
        out = os.path.join(output_dir(), fname)
        log(f"未指定 -o，成品存入默认目录：{output_dir()}"
            f"（可用 -o 路径、或 login --output-dir / 环境变量 ZCM_OUTPUT_DIR 改）")
    download_result(job_id, out)
    abs_out = os.path.abspath(out)
    log(f"已下载成品标书：{abs_out}")
    log(f"标书所在目录：{os.path.dirname(abs_out)}")
    print(abs_out)
    _platform_reminder()
    _report_balance()


def cmd_compliance(args):
    _precheck_balance()
    extra = idempotency_header(args)
    # 云端投标文件先逐个下载到本地，再统一按本地文件多文件上传
    paths = [download_to_local(s, max_mb=MAX_BID_MB) if is_url(s) else s for s in args.files]
    for p in paths:
        _check_size(p, MAX_BID_MB, "投标文件")
    body, ctype = encode_multipart(
        {"is_blind_bid": str(args.blind).lower(),
         "is_electronic_bid": str(args.electronic).lower()},
        [("bid_files", p) for p in paths])
    resp = request_json("POST", f"/projects/{args.project_id}/compliance-reviews",
                        headers={**extra, "Content-Type": ctype}, data=body)
    job_id = resp["job_id"]
    log(f"已提交合规审查任务 job_id={job_id}")
    if args.no_wait:
        print(job_id)
        return
    poll(job_id, interval=args.interval)
    result = request_json("GET", f"/jobs/{job_id}/result")
    print(json.dumps(zh_risk(result), ensure_ascii=False, indent=2))
    # 招标文件名：--name 优先，否则按 project_id 回查本地（interpret 时记下的）
    tender = args.name or recall_tender(project_id=args.project_id)
    _maybe_report(result, args.report, "合规", tender_name=tender)
    _report_balance()


def cmd_job(args):
    data = request_json("GET", f"/jobs/{args.job_id}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def download_result(job_id, out_path):
    """流式下载结果（标书制作返回 .docx 二进制）。"""
    url = base_url() + f"/jobs/{job_id}/result"
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req) as resp, open(out_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except urllib.error.URLError as e:
        die(f"网络错误：{e.reason}", code=1)


def cmd_result(args):
    if args.output:
        download_result(args.job_id, args.output)
        log(f"已保存：{args.output}")
        print(args.output)
        _platform_reminder()
    else:
        data = request_json("GET", f"/jobs/{args.job_id}/result")
        print(json.dumps(zh_risk(data), ensure_ascii=False, indent=2))


def cmd_register(args):
    """skill 内手机号注册/登录，换取 App Key 并保存到 config.json。"""
    _register_flow(phone=getattr(args, "phone", None),
                   code=getattr(args, "code", None))


def cmd_trial(args):
    """免费试用：设备特征自动开通账号（送 200 积分），换取并保存 App Key。"""
    _trial_flow()


def cmd_cancel(args):
    data = request_json("POST", f"/jobs/{args.job_id}/cancel")
    print(json.dumps(data, ensure_ascii=False, indent=2))


# 经验/反馈单条内容上限（与平台一致）
MAX_EXPERIENCE_CHARS = 10 * 1024


def cmd_experience(args):
    """经验沉淀：把助手总结（用户已过目并同意）回传平台，只存不用。"""
    if args.content_file:
        try:
            with open(args.content_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except OSError as e:
            die(f"读取内容文件失败：{e}")
    else:
        content = (args.content or "").strip()
    if not content:
        die("需要 --content 文本或 --content-file 文件路径。")
    if len(content) > MAX_EXPERIENCE_CHARS:
        die(f"内容过长（{len(content)} 字符 > {MAX_EXPERIENCE_CHARS}），请精简后重试。")
    body = {"type": args.type, "stage": args.stage,
            "title": args.title, "content": content}
    if args.project_id:
        body["project_id"] = args.project_id
    resp = request_json("POST", "/experience/submit", json_body=body)
    total = resp.get("total_count")
    if total is not None:
        log(f"经验已沉淀到百炼®标书平台，累计 {total} 条。")
    else:
        log("经验已沉淀到百炼®标书平台。")
    print(json.dumps(resp, ensure_ascii=False))


def cmd_feedback(args):
    """问题上报：结构化上报使用问题（用户已过目并同意），自动附带版本与渠道。"""
    body = {
        "category": args.category,
        "scene": args.scene,
        "phenomenon": args.phenomenon,
        "expectation": (args.expectation or ""),
        "skill_version": SKILL_VERSION,
        "channel": CHANNEL,
    }
    resp = request_json("POST", "/feedback/submit", json_body=body)
    log("问题已上报，感谢反馈（不含文件内容与个人信息）。")
    print(json.dumps(resp, ensure_ascii=False))


def cmd_progress_stream(args):
    """流式进度到 stdout，每行一条状态变更，供 Monitor 工具实时订阅。
    成功退出 0，失败/取消/超时退出 1。
    """
    deadline = time.time() + args.timeout
    last = ""
    last_pct = None
    last_stage = ""
    while True:
        try:
            st = request_json("GET", f"/jobs/{args.job_id}")
        except (Exception, SystemExit):
            # 网络抖动/连接重置/服务重启时跳过本次，不崩溃
            time.sleep(1)
            continue
        status = st.get("status")
        prog = st.get("progress") or {}
        pct = prog.get("percent")
        label = prog.get("stage_label") or prog.get("stage", "")
        elapsed = prog.get("elapsed_seconds")
        remaining = prog.get("estimated_remaining_seconds")
        pct_display = pct if pct is not None else "?"
        time_parts = []
        if elapsed is not None:
            time_parts.append(f"已用 {elapsed}s")
        if remaining is not None:
            time_parts.append(f"剩余 {remaining}s")
        time_str = f"  ({' / '.join(time_parts)})" if time_parts else ""
        # stage_key 不含 time_str，避免时间每秒变化误触发输出
        stage_key = f"{label}（{status}）"
        stage_changed = stage_key != last_stage
        pct_stepped = (last_pct is None or pct is None or
                       abs(pct - last_pct) >= args.step or stage_changed)
        line = f"[{pct_display}%] {label}（{status}）{time_str}"
        if line != last and pct_stepped:
            print(line, flush=True)
            last = line
            last_stage = stage_key
            if pct is not None:
                last_pct = pct
        if status == "succeeded":
            print("[完成]", flush=True)
            return
        if status in ("failed", "canceled"):
            err = st.get("error") or {}
            ecode = err.get("code", "")
            hint = ERROR_HINTS.get(ecode, "")
            print(f"[失败] {ecode} {err.get('message', '')} {hint}".strip(), flush=True)
            sys.exit(1)
        if time.time() > deadline:
            print(f"[超时] 任务超过 {args.timeout}s 未完成", flush=True)
            sys.exit(1)
        time.sleep(args.interval)


def build_parser():
    p = argparse.ArgumentParser(description="百炼®标书开放 API 轻客户端")
    p.add_argument("--version", action="version",
                   version=f"biaoshu-bailian {SKILL_VERSION}　·　适配 {API_TARGET}　·　契约快照 {CONTRACT_SNAPSHOT}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp, wait=False):
        sp.add_argument("--interval", type=int, default=5, help="轮询间隔秒（默认 5）")
        if wait:
            sp.add_argument("--no-wait", action="store_true", help="只提交，打印 job_id 不轮询")
            sp.add_argument("--idempotency-key", help="幂等键 UUID，重试防重复扣费")

    sp = sub.add_parser("login", help="保存凭证到 config.json")
    sp.add_argument("--app-key", help="App Key，形如 bk_live_xxxxx（必填）")
    sp.add_argument("--base", help="可选：Base URL")
    sp.add_argument("--output-dir", help="可选：成品标书 .docx 默认存放目录")
    sp.set_defaults(func=cmd_login)

    sp = sub.add_parser("logout", help="删除已保存的凭证文件")
    sp.set_defaults(func=cmd_logout)

    sp = sub.add_parser("register", help="skill 内手机号注册/登录，换取并保存 App Key")
    sp.add_argument("--phone", help="手机号（可选，不填则交互输入）")
    sp.add_argument("--code", help="验证码（已有验证码时传入，跳过重发短信）")
    sp.set_defaults(func=cmd_register)

    sp = sub.add_parser("trial", help="免费试用：设备特征自动开通账号（送 200 积分），换取并保存 App Key")
    sp.set_defaults(func=cmd_trial)

    sp = sub.add_parser("me", help="查连通性与积分余额")
    sp.set_defaults(func=cmd_me)

    sp = sub.add_parser("interpret", help="智能解读招标文件 → 完整解读结果")
    sp.add_argument("source", help="本地文件(.pdf/.doc/.docx) 或 https URL")
    sp.add_argument("--report", choices=["html", "docx", "both"], help="取结果后直接生成解读报告")
    sp.add_argument("--name", help="招标文件名（报告默认命名用；不填取上传文件名）")
    add_common(sp, wait=True)
    sp.set_defaults(func=cmd_interpret)

    sp = sub.add_parser("packages", help="抽取分包供挑选")
    sp.add_argument("project_id")
    add_common(sp, wait=True)
    sp.set_defaults(func=cmd_packages)

    sp = sub.add_parser("generate", help="生成成品标书 .docx")
    sp.add_argument("project_id")
    sp.add_argument("--package-ids", help="逗号分隔的选中分包 ID，如 11,12（多包必填）")
    sp.add_argument("--total-pages", type=int, help="期望总页数（可选）")
    sp.add_argument("-o", "--output", help="输出 .docx 路径（默认 招标文件名_投标文件.docx）")
    sp.add_argument("--name", help="招标文件名（成品默认命名 招标文件名_投标文件）")
    sp.add_argument("--timeout", type=int, default=3600, help="轮询超时秒（默认 3600）")
    add_common(sp, wait=True)
    sp.set_defaults(func=cmd_generate)

    sp = sub.add_parser("compliance", help="合规审查投标文件(.doc/.docx)")
    sp.add_argument("project_id")
    sp.add_argument("files", nargs="+", help="一个或多个本地 .doc/.docx，或多个 https URL")
    sp.add_argument("--blind", action="store_true", help="暗标")
    sp.add_argument("--electronic", action="store_true", help="电子标")
    sp.add_argument("--report", choices=["html", "docx", "both"], help="取结果后直接生成合规报告")
    sp.add_argument("--name", help="招标文件名（合规报告默认命名 招标文件名_合规审查）")
    add_common(sp, wait=True)
    sp.set_defaults(func=cmd_compliance)

    sp = sub.add_parser("report", help="把解读/合规结果渲染成 HTML/Word 报告")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--job", help="任务 job_id（自动取 /result 再渲染）")
    g.add_argument("--in", dest="in_file", help="本地结果 JSON 文件（/result 响应或 result 体）")
    sp.add_argument("--service", choices=["interpretation", "compliance"], help="不指定则自动识别")
    sp.add_argument("--format", choices=["html", "docx", "both"], default="html",
                    help="默认 html；用户明确要 Word 才用 docx 或 both")
    sp.add_argument("-o", "--out-dir", help="输出目录（默认成品目录 biaoshu-bailian-files/）")
    sp.add_argument("--name", help="招标文件名（报告默认命名 招标文件名_{智能解读|合规审查}）")
    sp.add_argument("--basename", help="完整文件名（不含扩展名），优先级最高")
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("job", help="查任务状态（不轮询）")
    sp.add_argument("job_id")
    sp.set_defaults(func=cmd_job)

    sp = sub.add_parser("result", help="取任务结果")
    sp.add_argument("job_id")
    sp.add_argument("-o", "--output", help="保存到文件（标书制作返回 .docx 时必填）")
    sp.set_defaults(func=cmd_result)

    sp = sub.add_parser("cancel", help="取消任务")
    sp.add_argument("job_id")
    sp.set_defaults(func=cmd_cancel)

    sp = sub.add_parser("experience", help="把本阶段经验总结回传平台沉淀（用户同意后）")
    sp.add_argument("--type", required=True,
                    choices=["material", "preference", "correction"],
                    help="material=内容素材 preference=写作偏好 correction=纠错经验")
    sp.add_argument("--stage", required=True,
                    choices=["interpret", "write", "compliance"],
                    help="interpret=解读调整 write=改稿 compliance=合规整改")
    sp.add_argument("--title", required=True, help="条目标题")
    sp.add_argument("--content", help="总结文本（短文本直接传）")
    sp.add_argument("--content-file", help="总结文本文件路径（长文本用，避开命令行长度限制）")
    sp.add_argument("--project-id", help="可选：关联项目 ID（溯源用）")
    sp.set_defaults(func=cmd_experience)

    sp = sub.add_parser("feedback", help="上报使用问题（用户同意后；不含文件内容与个人信息）")
    sp.add_argument("--category", required=True,
                    choices=["misguide", "correction", "error", "suggestion"],
                    help="misguide=流程跑偏 correction=用户纠正 error=报错 suggestion=建议")
    sp.add_argument("--scene", required=True, help="场景，如 智能解读/生成标书/合规审查")
    sp.add_argument("--phenomenon", required=True, help="现象描述（勿含文件内容/个人信息）")
    sp.add_argument("--expectation", help="期望行为（可选）")
    sp.set_defaults(func=cmd_feedback)

    sp = sub.add_parser("progress-stream",
                        help="流式进度到 stdout，供 Monitor 实时订阅（配合 --no-wait 两阶段用）")
    sp.add_argument("job_id")
    sp.add_argument("--interval", type=float, default=0.015, help="轮询间隔秒（默认 0.015 即 15ms）")
    sp.add_argument("--step", type=int, default=5, help="百分比变化步进阈值，达到才输出（默认 5）")
    sp.add_argument("--timeout", type=int, default=3600, help="超时秒（默认 3600）")
    sp.set_defaults(func=cmd_progress_stream)

    return p


def _cmp_semver(a, b):
    """比较 MAJOR.MINOR.PATCH：a<b→-1，a==b→0，a>b→1；非法输入抛 ValueError。"""
    def _parse(v):
        parts = str(v).strip().split(".")
        if len(parts) != 3:
            raise ValueError("非法版本号: %r" % (v,))
        return tuple(int(x) for x in parts)
    ta, tb = _parse(a), _parse(b)
    return (ta > tb) - (ta < tb)


def _fetch_latest_version(timeout=2.0):
    """带 App Key GET /skill/version（带 channel）；返回 (latest, notice) 或 None（无 Key/任何失败）。"""
    try:
        app_key = os.environ.get("ZCM_APP_KEY", "").strip() or str(
            load_creds_file().get("app_key", "")).strip()
        if not app_key:
            return None
        url = base_url() + "/skill/version"
        if CHANNEL:
            url += "?channel=" + CHANNEL
        req = urllib.request.Request(
            url, headers={"User-Agent": "zcm-client", "X-App-Key": app_key}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        data = json.loads(raw.decode("utf-8")) if raw else {}
        latest = data.get("latest")
        if not latest:
            return None
        return str(latest), data.get("notice")
    except Exception:
        return None


def _maybe_check_update():
    """每天首次运行匿名查一次最新版本；本地落后则提示。任何失败静默、绝不阻断命令。"""
    try:
        if not os.path.exists(creds_path()):
            return  # 未配置凭证：onboarding 阶段跳过，重点是引导拿 Key
        creds = load_creds_file()
        today = time.strftime("%Y-%m-%d")
        if creds.get("last_version_check") == today:
            return  # 今天已查过
        creds["last_version_check"] = today  # 无论成败都记，避免当天反复打网络
        try:
            save_creds_file(creds)
        except Exception:
            pass
        got = _fetch_latest_version()
        if not got:
            return
        latest, notice = got
        try:
            if _cmp_semver(latest, SKILL_VERSION) <= 0:
                return  # 本地不落后
        except ValueError:
            return
        log("📢 「百炼®标书」检测到新版本 v%s（当前 v%s）。是否需要更新到最新版？（用户同意后，我会为你拉取并安装最新版本的本 skill。）"
            % (latest, SKILL_VERSION))
        if notice:
            log("   说明：%s" % (notice,))
    except Exception:
        return


def main():
    args = build_parser().parse_args()
    _maybe_check_update()
    args.func(args)


if __name__ == "__main__":
    main()
