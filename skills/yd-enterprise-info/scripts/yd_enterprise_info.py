#!/usr/bin/env python3
"""
yd-enterprise-info — 元典开放平台企业信息查询 CLI
版本：v26.4.29.1545

设计目标：
  - 封装元典开放平台「企业信息」全部22个接口
  - 分页接口默认自动翻页，合并为一个 JSON 文件，彻底消除列表数量限制
  - 不引入任何第三方依赖（仅 Python 标准库）
  - 凭证仅从环境变量或 --api-key 参数读取，禁止落盘

凭证：
  优先级：--api-key 命令行参数 > 环境变量 CHINESELAW_API_KEY

用法示例：
  export CHINESELAW_API_KEY=xxxx

  # 按名称检索候选企业
  python3 yd_enterprise_info.py search-company --name "华宇元典" --top-k 5

  # 按 USCC 拉取基本信息（含股东/核心成员/分支机构）
  python3 yd_enterprise_info.py base-info --tyshxydm 91110108MA0074PN30 --output ./raw/

  # 分页接口：自动翻页拉全（默认）
  python3 yd_enterprise_info.py brand --tyshxydm 91110108MA0074PN30 --output ./raw/

  # 分页接口：只拉前 2 页
  python3 yd_enterprise_info.py brand --tyshxydm 91110108MA0074PN30 --max-pages 2 --output ./raw/

  # 分页接口：指定单页
  python3 yd_enterprise_info.py brand --tyshxydm 91110108MA0074PN30 --page 3 --output ./raw/

  # 显式打印完整 JSON 数据（默认只打印摘要）
  python3 yd_enterprise_info.py litigation-stat --tyshxydm 91110108MA0074PN30 --print-data

  # 批量执行（尽调第 9 章所有接口）
  for cmd in litigation-stat litigation-doc court-announcement court-hearing executed dishonest admin-penalty serious-violation equity-frozen; do
    python3 yd_enterprise_info.py $cmd --tyshxydm XXXX --output ./raw/ --yes
  done

注意：
  - 分页接口默认 --max-pages 20，避免积分爆炸；设 0 表示不限制
  - 每次调用前会打印预估积分消耗并要求确认，--yes 跳过
  - 落盘文件名格式：<subcommand>_<identifier>_<YYYYMMDDHHMM>.json
  - 合并后文件根节点追加 _meta 字段（fetched_pages, total, subcommand, identifier, fetched_at）
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

API_BASE = "https://open.chineselaw.com"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_PAGES = 20

# ──────────────────────────────────────────────────────────────────────
# 接口注册表
# ──────────────────────────────────────────────────────────────────────

SUBCOMMANDS = {
    # ── 检索类 ──────────────────────────────────────────────
    "search-company": {
        "endpoint": "/open/rh_enterpriseSearch",
        "desc": "按企业名称检索候选企业列表（精准命中优先）",
        "paginated": False,
        "id_required": False,
    },
    # ── 基本信息 ─────────────────────────────────────────────
    "base-info": {
        "endpoint": "/open/rh_enterpriseBaseInfo",
        "desc": "企业扁平详情（基本信息+股东+核心成员+分支机构）",
        "paginated": False,
        "id_required": True,
    },
    # ── 分页类 ──────────────────────────────────────────────
    "change": {
        "endpoint": "/open/rh_enterpriseChangeInfo",
        "desc": "企业变更记录列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "brand": {
        "endpoint": "/open/rh_enterpriseBrand",
        "desc": "企业商标信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "soft-right": {
        "endpoint": "/open/rh_enterpriseSoftRight",
        "desc": "企业软件著作权信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "patent": {
        "endpoint": "/open/rh_enterprisePatent",
        "desc": "企业专利信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "copyright-work": {
        "endpoint": "/open/rh_enterpriseWorksRight",
        "desc": "企业作品著作权信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "website": {
        "endpoint": "/open/rh_enterpriseIcp",
        "desc": "企业网站备案信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "outbound-invest": {
        "endpoint": "/open/rh_enterpriseOutInvest",
        "desc": "企业对外投资信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "outbound-guarantee": {
        "endpoint": "/open/rh_enterpriseGuaranty",
        "desc": "企业对外担保信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "equity-pledge": {
        "endpoint": "/open/rh_enterprisePledge",
        "desc": "企业股权出质信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "equity-frozen": {
        "endpoint": "/open/rh_enterpriseFrozenEquity",
        "desc": "企业股权冻结信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "abnormal": {
        "endpoint": "/open/rh_enterpriseAbnormalOperation",
        "desc": "企业经营异常记录列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "serious-violation": {
        "endpoint": "/open/rh_enterpriseSeriousIllegal",
        "desc": "企业严重违法记录列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "tax-arrears": {
        "endpoint": "/open/rh_enterpriseCorporateTax",
        "desc": "企业欠税公告记录列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "admin-penalty": {
        "endpoint": "/open/rh_enterprisePunishment",
        "desc": "企业行政处罚信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "executed": {
        "endpoint": "/open/rh_enterpriseExecutedPerson",
        "desc": "企业被执行人信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "dishonest": {
        "endpoint": "/open/rh_enterpriseExecutions",
        "desc": "企业失信被执行人信息列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "litigation-doc": {
        "endpoint": "/open/rh_enterpriseWritList",
        "desc": "企业涉诉文书列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "litigation-stat": {
        "endpoint": "/open/rh_enterpriseWritAgg",
        "desc": "企业涉诉信息多维度统计（非分页，含案件类别/案由/文书种类等）",
        "paginated": False,
        "id_required": True,
    },
    "court-announcement": {
        "endpoint": "/open/rh_enterpriseCourtNotice",
        "desc": "企业法院公告列表（分页）",
        "paginated": True,
        "id_required": True,
    },
    "court-hearing": {
        "endpoint": "/open/rh_enterpriseCourtSessionNotice",
        "desc": "企业开庭公告列表（分页）",
        "paginated": True,
        "id_required": True,
    },
}


# ──────────────────────────────────────────────────────────────────────
# 公共工具
# ──────────────────────────────────────────────────────────────────────

class EnterpriseInfoError(Exception):
    """元典 API 调用异常"""


def get_api_key(cli_key: str | None) -> str:
    key = cli_key or os.environ.get("CHINESELAW_API_KEY", "")
    if not key:
        raise EnterpriseInfoError(
            "未找到 API Key。请设置环境变量 CHINESELAW_API_KEY=xxxx，"
            "或通过 --api-key 参数传入。"
        )
    return key


def build_url(endpoint: str, params: dict) -> str:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return f"{API_BASE}{endpoint}?{qs}" if qs else f"{API_BASE}{endpoint}"


def do_request(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"X-API-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise EnterpriseInfoError(f"HTTP {e.code} {e.reason}：{url}") from e
    except urllib.error.URLError as e:
        raise EnterpriseInfoError(f"网络错误：{e.reason}") from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise EnterpriseInfoError(f"响应 JSON 解析失败：{e}") from e

    code = data.get("code")
    status = data.get("status", "")
    if code != 200 or status not in ("success",):
        msg = data.get("message", body[:200])
        raise EnterpriseInfoError(f"接口返回异常 code={code} status={status}：{msg}")

    return data


def make_output_path(output_dir: str, subcommand: str, identifier: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d%H%M")
    safe_id = identifier.replace("/", "_").replace("\\", "_")[:40]
    filename = f"{subcommand}_{safe_id}_{ts}.json"
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out / filename


def save_json(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def confirm_call(subcommand: str, yes: bool) -> None:
    if yes:
        return
    print(f"[yd-enterprise-info] 即将调用「{subcommand}」接口（计费约 10 积分/次）。")
    ans = input("确认继续？[y/N] ").strip().lower()
    if ans not in ("y", "yes"):
        print("已取消。")
        sys.exit(0)


# ──────────────────────────────────────────────────────────────────────
# 核心逻辑
# ──────────────────────────────────────────────────────────────────────

def fetch_single(endpoint: str, params: dict, api_key: str) -> dict:
    """请求单次（非分页）接口，返回 data 字段内容。"""
    url = build_url(endpoint, params)
    resp = do_request(url, api_key)
    return resp["data"]


def fetch_paginated(
    endpoint: str,
    base_params: dict,
    api_key: str,
    page: int | None,
    max_pages: int,
) -> dict:
    """
    自动翻页拉取分页接口。
    - page=N：只拉第 N 页，直接返回该页 data
    - page=None：循环拉直到 hasMore=False 或到达 max_pages 限制
    返回合并后的 data dict，list 字段为所有页数据拼接，附 _meta。
    """
    if page is not None:
        params = {**base_params, "pageNo": page}
        url = build_url(endpoint, params)
        resp = do_request(url, api_key)
        return resp["data"]

    all_items: list = []
    fetched_pages = 0
    total = None
    page_no = 1
    last_data: dict = {}

    while True:
        params = {**base_params, "pageNo": page_no}
        url = build_url(endpoint, params)
        resp = do_request(url, api_key)
        data = resp["data"]
        last_data = data

        items = data.get("list", [])
        all_items.extend(items)
        fetched_pages += 1

        if total is None:
            total = data.get("total")

        has_more = data.get("hasMore", False)
        print(
            f"  页 {page_no}：获取 {len(items)} 条，累计 {len(all_items)} 条"
            + (f"（共 {total}）" if total is not None else ""),
            file=sys.stderr,
        )

        if not has_more:
            break
        if max_pages > 0 and fetched_pages >= max_pages:
            print(
                f"  已达到 --max-pages {max_pages} 上限，停止翻页（剩余未取）。",
                file=sys.stderr,
            )
            break
        page_no += 1
        time.sleep(0.3)  # 礼貌性延迟，避免过快请求

    result = {k: v for k, v in last_data.items() if k != "list"}
    result["list"] = all_items
    result["_meta"] = {
        "fetched_pages": fetched_pages,
        "fetched_items": len(all_items),
        "total": total,
        "max_pages_limit": max_pages if max_pages > 0 else "unlimited",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }
    return result


def run_subcommand(args: argparse.Namespace) -> None:
    subcommand = args.subcommand
    spec = SUBCOMMANDS[subcommand]
    api_key = get_api_key(getattr(args, "api_key", None))

    # 构建基础参数
    if subcommand == "search-company":
        params: dict = {"name": args.name}
        if args.top_k:
            params["top_k"] = args.top_k
    else:
        if not args.id and not args.tyshxydm:
            print("错误：--id 或 --tyshxydm 至少提供一个。", file=sys.stderr)
            sys.exit(1)
        params = {}
        if args.id:
            params["id"] = args.id
        if args.tyshxydm:
            params["tyshxydm"] = args.tyshxydm

    identifier = (
        args.tyshxydm or args.id
        if subcommand != "search-company"
        else args.name
    )

    confirm_call(subcommand, args.yes)

    print(f"[yd-enterprise-info] 调用「{subcommand}」…", file=sys.stderr)

    if spec["paginated"]:
        page = getattr(args, "page", None)
        max_pages = getattr(args, "max_pages", DEFAULT_MAX_PAGES)
        data = fetch_paginated(spec["endpoint"], params, api_key, page, max_pages)
    else:
        data = fetch_single(spec["endpoint"], params, api_key)

    # 输出/落盘
    output_dir = getattr(args, "output", None)
    if output_dir:
        out_path = make_output_path(output_dir, subcommand, identifier)
        save_json(out_path, data)
        summary = {
            "file": str(out_path),
            "subcommand": subcommand,
            "identifier": identifier,
        }
        if spec["paginated"] and "_meta" in data:
            meta = data["_meta"]
            summary["total"] = meta.get("total")
            summary["fetched_items"] = meta.get("fetched_items")
            summary["fetched_pages"] = meta.get("fetched_pages")
        elif "total" in data:
            summary["total"] = data["total"]
        print(json.dumps(summary, ensure_ascii=False))
    else:
        # 无 --output：打印数据（自动相当于 --print-data）
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if args.print_data:
        print(json.dumps(data, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────────────────────────────
# CLI 解析
# ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yd_enterprise_info.py",
        description="元典开放平台企业信息查询工具 v26.4.29.1545",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            [f"  {k:25s} {v['desc']}" for k, v in SUBCOMMANDS.items()]
        ),
    )
    parser.add_argument("--api-key", metavar="KEY", help="API Key（优先级高于环境变量）")

    sub = parser.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")
    sub.required = True

    # 公共参数组（id/tyshxydm）
    def add_id_args(p: argparse.ArgumentParser) -> None:
        g = p.add_mutually_exclusive_group()
        g.add_argument("--id", metavar="ID", help="企业 ID")
        g.add_argument("--tyshxydm", metavar="USCC", help="统一社会信用代码")
        p.add_argument("--output", metavar="DIR", help="JSON 落盘目录（省略则直接打印）")
        p.add_argument("--print-data", action="store_true", help="落盘同时打印完整 JSON")
        p.add_argument("--yes", "-y", action="store_true", help="跳过积分确认提示")

    def add_paginate_args(p: argparse.ArgumentParser) -> None:
        pg = p.add_mutually_exclusive_group()
        pg.add_argument("--page", type=int, metavar="N", help="只拉第 N 页（不自动翻页）")
        pg.add_argument(
            "--max-pages",
            type=int,
            default=DEFAULT_MAX_PAGES,
            metavar="N",
            help=f"自动翻页最大页数（默认 {DEFAULT_MAX_PAGES}，0 表示不限制）",
        )

    # ── search-company ──
    p = sub.add_parser("search-company", help=SUBCOMMANDS["search-company"]["desc"])
    p.add_argument("--name", required=True, metavar="NAME", help="企业名称关键词")
    p.add_argument("--top-k", type=int, metavar="N", help="返回条数（1-50，默认10）")
    p.add_argument("--output", metavar="DIR", help="JSON 落盘目录")
    p.add_argument("--print-data", action="store_true", help="落盘同时打印完整 JSON")
    p.add_argument("--yes", "-y", action="store_true", help="跳过积分确认提示")

    # ── base-info ──
    p = sub.add_parser("base-info", help=SUBCOMMANDS["base-info"]["desc"])
    add_id_args(p)

    # ── 分页接口 ──
    for cmd in [
        "change", "brand", "soft-right", "patent", "copyright-work", "website",
        "outbound-invest", "outbound-guarantee", "equity-pledge", "equity-frozen",
        "abnormal", "serious-violation", "tax-arrears", "admin-penalty",
        "executed", "dishonest", "litigation-doc", "court-announcement", "court-hearing",
    ]:
        p = sub.add_parser(cmd, help=SUBCOMMANDS[cmd]["desc"])
        add_id_args(p)
        add_paginate_args(p)

    # ── litigation-stat（无分页）──
    p = sub.add_parser("litigation-stat", help=SUBCOMMANDS["litigation-stat"]["desc"])
    add_id_args(p)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_subcommand(args)
    except EnterpriseInfoError as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[中断]", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
