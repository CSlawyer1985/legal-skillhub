#!/usr/bin/env python3
"""Verify a regulation citation by name."""
import argparse
import json
import sys

from util import get_api_key, api_post


def parse_args():
    parser = argparse.ArgumentParser(description="核验法规引用")
    parser.add_argument("--name", required=True, help="法规名称，如：中华人民共和国民法典")
    parser.add_argument("--refer-date", help="参考日期，格式 YYYY-MM-DD，用于确定当时生效的版本")
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = get_api_key()

    payload = {"fgmc": args.name}
    if args.refer_date:
        payload["refer_date"] = args.refer_date

    result = api_post("rh_fg_detail", payload, api_key)
    data = result.get("data")

    if data:
        output = {
            "status": "correct",
            "type": "法规",
            "citation": args.name,
            "data": {
                "name": data.get("fgmc", ""),
                "validity": data.get("sxx", ""),
                "effect_level": data.get("xljb_1", ""),
                "issue_date": data.get("fbrq", ""),
                "effective_date": data.get("ssrq", ""),
                "issuing_body": data.get("fbbm", ""),
                "document_number": data.get("fwzh", ""),
            },
            "generated": {"name": args.name},
        }
        if args.refer_date:
            output["data"]["refer_date"] = args.refer_date
        print(json.dumps(output, ensure_ascii=False))
        return

    if result.get("code") == 0:
        output = {
            "status": "error",
            "type": "法规",
            "citation": args.name,
            "message": result.get("message", "请求失败"),
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)
        return

    output = {
        "status": "not_found",
        "type": "法规",
        "citation": args.name,
        "message": "未查询到相关内容",
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
