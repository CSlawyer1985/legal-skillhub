#!/usr/bin/env python3
"""
Trademark info skill for OpenClaw.
基于极速数据商标信息 API：
https://www.jisuapi.com/api/trademark/
"""

import sys
import json
import os
import requests


BASE_URL = "https://api.jisuapi.com/trademark"


def _call_trademark_api(path: str, appkey: str, params: dict):
    all_params = {"appkey": appkey}
    all_params.update(params)
    url = f"{BASE_URL}/{path}"

    try:
        resp = requests.get(url, params=all_params, timeout=10)
    except Exception as e:
        return {"error": "request_failed", "message": str(e)}

    if resp.status_code != 200:
        return {
            "error": "http_error",
            "status_code": resp.status_code,
            "body": resp.text,
        }

    try:
        data = resp.json()
    except Exception:
        return {"error": "invalid_json", "body": resp.text}

    if data.get("status") != 0:
        return {
            "error": "api_error",
            "code": data.get("status"),
            "message": data.get("msg"),
        }

    return data.get("result", {})


def search_trademark(appkey: str, req: dict):
    """
    调用 /trademark/search 接口，根据关键词搜索商标。

    请求 JSON 示例：
    {
        "keyword": "手机",
        "pagenum": 1,
        "pagesize": 10,
        "ismatch": 0,
        "type": 1,
        "classid": "0"
    }
    """
    keyword = req.get("keyword")
    if not keyword:
        return {"error": "missing_param", "message": "keyword is required"}

    params: dict = {
        "keyword": keyword,
        "pagenum": req.get("pagenum", 1),
        "pagesize": req.get("pagesize", 10),
    }

    # 可选参数
    if "ismatch" in req:
        params["ismatch"] = req["ismatch"]
    if "type" in req:
        params["type"] = req["type"]
    if "classid" in req:
        params["classid"] = req["classid"]

    return _call_trademark_api("search", appkey, params)


def detail_trademark(appkey: str, req: dict):
    """
    调用 /trademark/detail 接口，根据申请/注册号 + 国际分类查询商标详情。

    请求 JSON 示例：
    {
        "regno": "4952050",
        "classid": "42"
    }
    """
    regno = req.get("regno")
    classid = req.get("classid")
    if not regno:
        return {"error": "missing_param", "message": "regno is required"}
    if not classid:
        return {"error": "missing_param", "message": "classid is required"}

    params = {
        "regno": regno,
        "classid": classid,
    }

    return _call_trademark_api("detail", appkey, params)


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  trademark.py search '{\"keyword\":\"手机\",\"pagenum\":1,\"pagesize\":10}'  # 商标搜索\n"
            "  trademark.py detail '{\"regno\":\"4952050\",\"classid\":\"42\"}'          # 商标详情",
            file=sys.stderr,
        )
        sys.exit(1)

    appkey = os.getenv("JISU_API_KEY")

    if not appkey:
        print("Error: JISU_API_KEY must be set in environment.", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd in ("search", "detail"):
        if len(sys.argv) < 3:
            print(f"Error: JSON body is required for '{cmd}' subcommand.", file=sys.stderr)
            sys.exit(1)
        raw = sys.argv[2]
        try:
            req = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}", file=sys.stderr)
            sys.exit(1)

        if cmd == "search":
            result = search_trademark(appkey, req)
        else:
            result = detail_trademark(appkey, req)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"Error: unknown command '{cmd}'", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()

