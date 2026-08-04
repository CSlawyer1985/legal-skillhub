#!/usr/bin/env python3
"""Query the 企业商标信息查询 without exposing the API key."""

import argparse
import hashlib
import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ENDPOINT = "https://openapi.chinaz.net/v1/1036/trademark"
API_KEY_ENV = "CHINAZ_TRADEMARK_API_KEY"


def emit(payload: dict, exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def normalize_searchKey(value: str) -> str:
    """企业名称、企业统代、企业注册号"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("searchKey 不能为空")
    return candidate


def normalize_searchType(value: str) -> str:
    """查询类型：0所有 1企业名称 2统代 3注册号"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("searchType 不能为空")
    return candidate


def normalize_pageNo(value: str) -> str:
    """页码，从1开始"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("pageNo 不能为空")
    return candidate


def normalize_range(value: str) -> str:
    """每页条数，1-300"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("range 不能为空")
    return candidate


def compute_sign() -> str:
    """Compute sign = md5('634xz' + YYYYMMDD)."""
    date_str = datetime.now().strftime("%Y%m%d")
    raw = f"634xz{date_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def parse_json(body: bytes):
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="查询 企业商标信息查询")
    parser.add_argument("--searchKey", required=True, help="企业名称、企业统代、企业注册号")
    parser.add_argument("--searchType", required=False, help="查询类型：0所有 1企业名称 2统代 3注册号")
    parser.add_argument("--pageNo", required=True, help="页码，从1开始")
    parser.add_argument("--range", required=True, help="每页条数，1-300")
    parser.add_argument("--timeout", type=float, default=30, help="请求超时秒数，默认 30")
    args = parser.parse_args()

    try:
        searchKey = normalize_searchKey(args.searchKey)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)
    except AttributeError:
        pass
    try:
        searchType = normalize_searchType(args.searchType)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)
    except AttributeError:
        pass
    try:
        pageNo = normalize_pageNo(args.pageNo)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)
    except AttributeError:
        pass
    try:
        range = normalize_range(args.range)
    except ValueError as error:
        emit({"error": "invalid_input", "message": str(error)}, 2)
    except AttributeError:
        pass

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

    sign = compute_sign()

    form_data = urlencode({
        "searchKey": searchKey,
        "searchType": searchType,
        "pageNo": pageNo,
        "range": range,
        "sign": sign,
        "APIKey": api_key,
        "ChinazVer": "1.0",
    }).encode("utf-8")

    request = Request(
        API_ENDPOINT,
        data=form_data,
        headers={"Accept": "application/json", "User-Agent": "company-trademark-skill/1.0", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
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
