#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法海风控 - 企业司法数据列表查询脚本（正式环境 · VIP版本）

用法:
  python3 fahai_query.py --auth-code "授权码" --keyword "企业名称" [选项]

必填参数:
  --auth-code    法海风控授权码（未提供时提示联系010-62502608开通）
  --keyword      搜索关键词（企业名称/统一社会信用代码等）

可选参数:
  --domain       领域代码，默认 sifa（司法）
  --data-type    维度代码，留空则查询该领域所有维度
  --page-no      页码，默认 1
  --range        每页条数，默认 10
  --pretty       输出人类可读格式（默认输出 JSON）

示例:
  python3 fahai_query.py --auth-code "qXIwoa43RfoBdJWHkwOm" --keyword "北京某某科技有限公司"
  python3 fahai_query.py --auth-code "qXIwoa43RfoBdJWHkwOm" --keyword "北京某某科技有限公司" --domain sifa --data-type cpws
"""

import argparse
import hashlib
import json
import sys
import time

import requests

# ==================== 正式环境配置 ====================
BASE_URL = "https://api.fahaicc.com"
VERSION = "vip"
AUTH_CONTACT = "授权码开通可联系我们010-62502608"
# =====================================================


def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def build_sign(auth_code: str) -> tuple:
    """生成时间戳和签名"""
    rt = str(int(time.time() * 1000))
    sign = md5(auth_code + rt)
    return rt, sign


def query_enterprise(auth_code: str, keyword: str, domain: str,
                     data_type: str, page_no: int, range_: int) -> dict:
    """调用企业司法数据列表查询接口"""
    rt, sign = build_sign(auth_code)

    args = {"keyword": keyword, "pageno": page_no, "range": range_}
    if data_type:
        args["dataType"] = data_type

    url = f"{BASE_URL}/{VERSION}/query/{domain}"
    params = {
        "authCode": auth_code,
        "rt": rt,
        "sign": sign,
        "args": json.dumps(args, ensure_ascii=False),
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def print_pretty(result: dict):
    """人类可读格式输出"""
    if result.get("code") != "s":
        print(f"查询失败: {result.get('msg', '')}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    total = result.get("totalCount")
    pn = result.get("pageNo")
    tp = result.get("totalPageNum")
    print(f"查询成功 | 命中总数: {total} | 当前页: {pn}/{tp}")

    for key, value in result.items():
        if key.endswith("Count") and key != "totalCount":
            print(f"  {key.replace('Count', '')}: {value}")

    items = result.get("allList", [])
    if not items:
        print("当前页无数据。")
        return

    print(f"\n当前页条目 ({len(items)} 条):")
    for i, item in enumerate(items, 1):
        print(f"\n--- 第{i}条 ---")
        print(f"  类型: {item.get('dataType')}")
        print(f"  标题: {item.get('title')}")
        print(f"  时间: {item.get('sortTimeString')}")
        print(f"  entryId: {item.get('entryId')}")
        body = item.get("body", "")
        if body:
            print(f"  摘要: {body[:80]}")


def main():
    parser = argparse.ArgumentParser(
        description="法海风控 - 企业司法数据列表查询（正式环境·VIP）"
    )
    parser.add_argument("--auth-code", required=False, default="",
                        help="法海风控授权码（未提供时提示开通联系方式）")
    parser.add_argument("--keyword", required=True,
                        help="搜索关键词（企业名称等）")
    parser.add_argument("--domain", default="sifa",
                        help="领域代码，默认 sifa")
    parser.add_argument("--data-type", default="",
                        help="维度代码，留空则查询该领域所有维度")
    parser.add_argument("--page-no", type=int, default=1,
                        help="页码，默认 1")
    parser.add_argument("--range", type=int, default=10,
                        help="每页条数，默认 10")
    parser.add_argument("--pretty", action="store_true",
                        help="输出人类可读格式（默认输出 JSON）")

    args = parser.parse_args()

    # 授权码校验：未提供则提示开通联系方式并退出
    if not args.auth_code:
        no_auth_result = {
            "code": "auth_required",
            "msg": AUTH_CONTACT
        }
        if args.pretty:
            print(f"⚠️ {AUTH_CONTACT}")
        else:
            print(json.dumps(no_auth_result, ensure_ascii=False))
        sys.exit(0)

    try:
        result = query_enterprise(
            auth_code=args.auth_code,
            keyword=args.keyword,
            domain=args.domain,
            data_type=args.data_type,
            page_no=args.page_no,
            range_=args.range,
        )

        if args.pretty:
            print_pretty(result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except requests.exceptions.HTTPError as e:
        print(json.dumps({"code": "error", "msg": f"HTTP错误: {e}",
                          "status_code": e.response.status_code if e.response else None},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"code": "error", "msg": str(e)},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
