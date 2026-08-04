#!/usr/bin/env python3
"""Query the 企业软件著作权查询 without exposing the API key."""

import argparse
import hashlib
import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ENDPOINT = "https://openapi.chinaz.net/v1/1036/copyrightsoftware"
API_KEY_ENV = "CHINAZ_COPYRIGHT_SOFTWARE_API_KEY"


def emit(payload: dict, exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def normalize_entName(value: str) -> str:
    """企业名称"""
    candidate = value.strip()
    if not candidate:
        raise ValueError("entName 不能为空")
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
    parser = argparse.ArgumentParser(description="查询 企业软件著作权查询")
    parser.add_argument("--entName", required=True, help="企业名称")
    parser.add_argument("--pageNo", required=True, help="页码，从1开始")
    parser.add_argument("--range", required=True, help="每页条数，1-300")
    parser.add_argument("--timeout", type=float, default=30, help="请求超时秒数，默认 30")
    args = parser.parse_args()

    try:
        entName = normalize_entName(args.entName)
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
        "entName": entName,
        "pageNo": pageNo,
        "range": range,
        "sign": sign,
        "APIKey": api_key,
        "ChinazVer": "2.0",
    }).encode("utf-8")

    request = Request(
        API_ENDPOINT,
        data=form_data,
        headers={"Accept": "application/json", "User-Agent": "company-copyright-software-skill/1.0", "Content-Type": "application/x-www-form-urlencoded"},
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
