#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法海风控 - 案件详情查询脚本（正式环境 · VIP版本）

用法:
  python3 fahai_details.py --auth-code "授权码" --entry-id "xxx" --dimension cpws [选项]

必填参数:
  --auth-code    法海风控授权码（未提供时提示联系010-62502608开通）
  --entry-id     从列表查询结果中获取的 entryId
  --dimension    维度代码（如 cpws, zxgg, sswdjg 等）

可选参数:
  --detail-api   接口路径类型: export（默认，涉诉及所有高精版）或 entry（非涉诉标准版）
  --pretty       输出人类可读格式（默认输出 JSON）

示例:
  python3 fahai_details.py --auth-code "qXIwoa43RfoBdJWHkwOm" --entry-id "xxx" --dimension cpws
  python3 fahai_details.py --auth-code "qXIwoa43RfoBdJWHkwOm" --entry-id "xxx" --dimension zxgg --pretty
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


def query_detail(auth_code: str, entry_id: str, dimension: str,
                 detail_api: str) -> dict:
    """调用详情查询接口"""
    rt, sign = build_sign(auth_code)

    url = f"{BASE_URL}/{VERSION}/{detail_api}/{dimension}"
    params = {
        "authCode": auth_code,
        "rt": rt,
        "sign": sign,
        "id": entry_id,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def print_pretty(result: dict, dimension: str):
    """人类可读格式输出"""
    if result.get("code") != "s":
        print(f"查询失败: {result.get('msg', '')}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    total = result.get("totalCount", 0)
    search_seconds = result.get("searchSeconds", "")
    print(f"查询成功 | 获取详细记录: {total} 条 | 耗时: {search_seconds} 秒")

    # 详情数据通常在以维度命名的 key 中
    detail_list = result.get(dimension, [])
    if not detail_list:
        for key in result.keys():
            if isinstance(result[key], list) and key != "allList":
                detail_list = result[key]
                break
    if not detail_list:
        print("未找到详情数据，原始响应如下：")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n详情内容 ({len(detail_list)} 条):")
    for idx, item in enumerate(detail_list, 1):
        print(f"\n--- 第 {idx} 条 ---")
        for field, value in item.items():
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            elif isinstance(value, list):
                value = f"[列表，包含 {len(value)} 项]"
            elif isinstance(value, dict):
                value = f"[字典，包含 {len(value)} 个字段]"
            print(f"  {field}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="法海风控 - 案件详情查询（正式环境·VIP）"
    )
    parser.add_argument("--auth-code", required=False, default="",
                        help="法海风控授权码（未提供时提示开通联系方式）")
    parser.add_argument("--entry-id", required=True,
                        help="从列表查询结果中获取的 entryId")
    parser.add_argument("--dimension", required=True,
                        help="维度代码（如 cpws, zxgg 等）")
    parser.add_argument("--detail-api", default="export",
                        choices=["export", "entry"],
                        help="接口路径类型: export（默认）或 entry")
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
        result = query_detail(
            auth_code=args.auth_code,
            entry_id=args.entry_id,
            dimension=args.dimension,
            detail_api=args.detail_api,
        )

        if args.pretty:
            print_pretty(result, args.dimension)
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
