#!/usr/bin/env python3
"""
元典开放平台（chineselaw.com）API 客户端

设计目标：
    - 为本 skill 接入的所有元典接口提供统一封装（鉴权、请求、错误、落盘）
    - 子命令式 CLI，便于后续追加新接口
    - 不引入任何第三方依赖（仅使用 Python 标准库），避免破坏 skill 的可移植性

凭证管理：
    优先级：--api-key 命令行参数 > 环境变量 CHINESELAW_API_KEY
    *绝不* 将 key 写入任何项目文件或日志

当前已实现的子命令：
    company-detail    根据企业 id 或统一社会信用代码获取企业详情（10 积分/次）
    company-info      根据企业名称 / 股票简称查询企业详情（10 积分/次，返回最多 50 条）

用法示例：
    export CHINESELAW_API_KEY=xxxx

    # 已知 USCC 时：精准查询单条详情
    python3 chineselaw_client.py company-detail --uscc 91110108MA0074PN30 \\
        --output /path/to/project/raw/chineselaw/

    # 仅知名称时：按名称/股票简称检索候选列表
    python3 chineselaw_client.py company-info --name "北京华宇元典信息服务有限公司" \\
        --num 5 --output /path/to/project/raw/chineselaw/

注意：
    1. 文档 §2 与 §5 给出的 URL 不一致；本脚本采用 §2 的正式 URL：
       https://open.chineselaw.com/open/rh_company_detail
       若实际调用 404，请改用 §5 的备用 URL（见 BACKUP_URL 注释）。
    2. 接口计费 10 积分/次，默认调用前需用户确认（--yes 跳过）。
    3. 返回字段为全中文 key；本客户端只负责"取回 + 落盘"，
       不做字段规范化（规范化由 skill 在 draft 模式中由 LLM 完成）。
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

API_BASE = "https://open.chineselaw.com"
COMPANY_DETAIL_PATH = "/open/rh_company_detail"
COMPANY_INFO_PATH = "/open/rh_company_info"
# 备用 URL（文档 §5 示例使用）：
# BACKUP_DETAIL_URL = "https://open.chineselaw.com/legal-insight/service/app/dify/company/companyDetail"
# BACKUP_INFO_URL   = "https://open.chineselaw.com/legal-insight/service/app/dify/company/companyInfo"

DEFAULT_TIMEOUT = 30


class ChineselawError(Exception):
    """元典 API 调用异常"""


def _resolve_api_key(cli_key: str | None) -> str:
    key = cli_key or os.environ.get("CHINESELAW_API_KEY")
    if not key:
        raise ChineselawError(
            "未找到 API Key。请设置环境变量 CHINESELAW_API_KEY，"
            "或使用 --api-key 参数显式传入。"
        )
    return key


def _http_get(url: str, headers: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        raise ChineselawError(f"网络请求失败：{e}") from e
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ChineselawError(f"响应非 JSON：{raw[:200]}") from e


def _confirm_charge(credits: int, skip: bool) -> None:
    if skip:
        return
    ans = input(f"⚠️  本次调用将消耗 {credits} 积分，是否继续？[y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        print("已取消。")
        sys.exit(0)


# ---------------------------------------------------------------------------
# 子命令：company-detail
# ---------------------------------------------------------------------------

def cmd_company_detail(args: argparse.Namespace) -> None:
    if not args.id and not args.uscc:
        raise ChineselawError("必须提供 --id 或 --uscc 之一。")

    api_key = _resolve_api_key(args.api_key)
    _confirm_charge(credits=10, skip=args.yes)

    # 文档明确：id 优先于 tyshxydm
    params = {}
    if args.id:
        params["id"] = args.id
    if args.uscc:
        params["tyshxydm"] = args.uscc

    url = f"{API_BASE}{COMPANY_DETAIL_PATH}?{urllib.parse.urlencode(params)}"
    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key,
    }

    print(f"→ GET {COMPANY_DETAIL_PATH}  params={params}")
    payload = _http_get(url, headers)

    status = payload.get("status")
    code = payload.get("code")
    message = payload.get("message", "")

    if status == "success" and code in (200, 201):
        print(f"✅ 调用成功：{message}")
    elif status == "notFound" or code == 404:
        print(f"⚠️  未找到企业：{message}")
    else:
        print(f"❌ 调用失败：status={status} code={code} message={message}")

    # 无论成败都落盘，便于排查
    out_dir = Path(args.output) if args.output else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    key_part = args.uscc or args.id
    fname = f"company-detail-{key_part}-{ts}.json"
    fpath = out_dir / fname
    fpath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📄 已保存：{fpath}")

    # 简要摘要打印（仅成功时）
    data = payload.get("data") or {}
    if data:
        print("\n--- 摘要 ---")
        for k in ("企业名称", "法定代表人", "统一社会信用代码", "注册资本",
                 "成立日期", "经营状态", "登记机关", "注册地址"):
            v = data.get(k)
            if v:
                print(f"{k}: {v}")


# ---------------------------------------------------------------------------
# 子命令：company-info（按名称/股票简称检索）
# ---------------------------------------------------------------------------

def cmd_company_info(args: argparse.Namespace) -> None:
    if not args.name or not args.name.strip():
        raise ChineselawError("必须提供 --name。")

    # num 文档规则：<0 或 >50 → 后端置为 10；否则使用传入值。客户端这里仅做透传。
    api_key = _resolve_api_key(args.api_key)
    _confirm_charge(credits=10, skip=args.yes)

    params = {"name": args.name}
    if args.num is not None:
        params["num"] = str(args.num)

    url = f"{API_BASE}{COMPANY_INFO_PATH}?{urllib.parse.urlencode(params)}"
    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key,
    }

    print(f"→ GET {COMPANY_INFO_PATH}  params={params}")
    payload = _http_get(url, headers)

    status = payload.get("status")
    code = payload.get("code")
    message = payload.get("message", "")
    data = payload.get("data") or []

    if status == "success" and code in (200, 201):
        print(f"✅ 调用成功：{message}（命中 {len(data)} 条）")
    elif status == "notFound" or code == 404:
        print(f"⚠️  未找到企业：{message}")
    else:
        print(f"❌ 调用失败：status={status} code={code} message={message}")

    # 落盘
    out_dir = Path(args.output) if args.output else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    safe_name = "".join(c for c in args.name if c.isalnum() or c in ("-", "_"))[:40] or "query"
    fname = f"company-info-{safe_name}-{ts}.json"
    fpath = out_dir / fname
    fpath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📄 已保存：{fpath}")

    # 候选摘要（关键字段对比，辅助律师判断重名）
    if data:
        print(f"\n--- 候选企业列表（共 {len(data)} 条）---")
        for i, item in enumerate(data, 1):
            print(f"\n[{i}] {item.get('企业名称', '<无名称>')}")
            for k in ("统一社会信用代码", "法定代表人", "成立日期",
                     "经营状态", "注册地址", "企业类型", "注册资本"):
                v = item.get(k)
                if v:
                    print(f"    {k}: {v}")
        if len(data) == 1:
            print("\n💡 唯一命中：可直接将上述 USCC 用于后续 detail 查询或写入项目信息。")
        else:
            print(f"\n💡 多条命中：请人工确认目标企业后，记录其 USCC 并用于后续步骤。")




def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chineselaw_client",
        description="元典开放平台 API 客户端（用于 legal-due-diligence skill）",
    )
    p.add_argument("--api-key", help="覆盖环境变量 CHINESELAW_API_KEY")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser(
        "company-detail",
        help="根据企业 id 或 USCC 获取企业详情（10 积分/次）",
    )
    sp.add_argument("--id", help="企业 ID（ES 文档 _id）")
    sp.add_argument("--uscc", help="统一社会信用代码")
    sp.add_argument("--output", help="原始 JSON 落盘目录（默认当前目录）")
    sp.add_argument("--yes", "-y", action="store_true",
                    help="跳过 10 积分扣费确认")
    sp.set_defaults(func=cmd_company_detail)

    sp2 = sub.add_parser(
        "company-info",
        help="根据企业名称/股票简称检索候选企业详情（10 积分/次，返回最多 50 条）",
    )
    sp2.add_argument("--name", required=True, help="企业名称、曾用名或股票简称")
    sp2.add_argument("--num", type=int, default=None,
                     help="期望返回条数（1-50，默认 2；超出范围后端会置为 10）")
    sp2.add_argument("--output", help="原始 JSON 落盘目录（默认当前目录）")
    sp2.add_argument("--yes", "-y", action="store_true",
                     help="跳过 10 积分扣费确认")
    sp2.set_defaults(func=cmd_company_info)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ChineselawError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
