#!/usr/bin/env python3
"""Query the 企业股权质押 without exposing the API key."""

import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ENDPOINT = "https://openapi.chinaz.net/v1/1057/dsj_ep"
API_KEY_ENV = "CHINAZ_EQUITY_PLEDGE_API_KEY"


def emit(payload: dict, exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def normalize_keyword(value: str) -> str:
    """企业id/企业名称/统一社会信用代码/注册号"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("keyword 不能为空")
    return candidate


def normalize_pageNum(value: str) -> str:
    """当前页"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("pageNum 不能为空")
    return candidate


def normalize_pageSize(value: str) -> str:
    """每页条数，默认10，最多20"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("pageSize 不能为空")
    return candidate


def parse_json(body: bytes):
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="查询 企业股权质押")
    parser.add_argument("--keyword", required=True, help="企业id/企业名称/统一社会信用代码/注册号")
    parser.add_argument("--pageNum", required=False, help="当前页")
    parser.add_argument("--pageSize", required=False, help="每页条数，默认10，最多20")
    parser.add_argument("--timeout", type=float, default=30, help="请求超时秒数，默认 30")
    args = parser.parse_args()

    try:
        keyword = normalize_keyword(args.keyword)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)
    try:
        pageNum = normalize_pageNum(args.pageNum)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)
    try:
        pageSize = normalize_pageSize(args.pageSize)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)

    if args.timeout <= 0:
        emit({"error": "invalid_input", "message": "timeout 必须大于 0"}, 2)

    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        emit(
            {
                "error": "missing_api_key",
                "message": f"请设置环境变量 {API_KEY_ENV} 后重试。",
            },
            2,
        )

    query = urlencode(
        {
        "keyword": keyword,
        "pageNum": pageNum,
        "pageSize": pageSize,
        "APIKey": api_key,
        "ChinazVer": "1.0",
        }
    )
    request = Request(
        f"{API_ENDPOINT}?{query}",
        headers={"Accept": "application/json", "User-Agent": "equity-pledge-skill/1.0"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=args.timeout) as response:
            emit(parse_json(response.read()), 0)
    except HTTPError as error:
        emit(
            {
                "error": "http_error",
                "http_status": error.code,
                "response": parse_json(error.read()),
            },
            1,
        )
    except URLError as error:
        emit({"error": "network_error", "message": str(error.reason)}, 1)
    except TimeoutError:
        emit({"error": "timeout", "message": "请求超时，请稍后重试。"}, 1)


if __name__ == "__main__":
    main()
