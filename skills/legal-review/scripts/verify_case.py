#!/usr/bin/env python3
"""Verify a judicial case citation by case number."""
import argparse
import json
import sys

from util import get_api_key, api_get


def parse_args():
    parser = argparse.ArgumentParser(description="核验案例引用")
    parser.add_argument("--ah", required=True, help="案号，如：（2021）京01刑终263号")
    parser.add_argument("--type", default="ptal", choices=["ptal", "qwal"],
                        help="案例类型：ptal（普通案例）/ qwal（权威案例），默认 ptal")
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = get_api_key()

    params = {"ah": args.ah, "type": args.type}
    result = api_get("rh_case_details", params, api_key)

    case_list = result.get("data")
    if case_list and len(case_list) > 0:
        case = case_list[0]
        case_type_label = "权威案例" if args.type == "qwal" else "普通案例"
        output = {
            "status": "correct",
            "type": "案例",
            "case_type": case_type_label,
            "citation": args.ah,
            "data": {
                "case_number": case.get("ah", ""),
                "title": case.get("title", ""),
                "court": case.get("jbdw", ""),
                "case_category": case.get("ajlb", ""),
                "trial_procedure": case.get("spcx", ""),
                "judgment_date": case.get("cprq", ""),
                "document_type": case.get("wszl", ""),
                "cause_of_action": case.get("ay", ""),
                "region_province": case.get("xzqh_p", ""),
                "content": case.get("content", ""),
            },
            "generated": {"case_number": args.ah},
        }
        print(json.dumps(output, ensure_ascii=False))
        return

    if result.get("code") == 0:
        output = {
            "status": "error",
            "type": "案例",
            "citation": args.ah,
            "message": result.get("message", "请求失败"),
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)
        return

    output = {
        "status": "not_found",
        "type": "案例",
        "citation": args.ah,
        "message": "未查询到相关内容",
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
