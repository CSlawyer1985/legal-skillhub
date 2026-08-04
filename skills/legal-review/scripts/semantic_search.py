#!/usr/bin/env python3
"""Semantic search for laws or cases to support broader fact-checking."""
import argparse
import json
import sys

from util import get_api_key, api_post


def parse_args():
    parser = argparse.ArgumentParser(description="法律语义检索，辅助核验模糊引用")
    parser.add_argument("--type", required=True, choices=["law", "case"],
                        help="检索类型：law（法律法规）/ case（案例）")
    parser.add_argument("--query", required=True, help="检索文本")
    parser.add_argument("--top-k", type=int, default=5, help="返回数量（默认5，最大45）")
    parser.add_argument("--validity", help="时效性过滤（仅 law）：现行有效/失效/已被修改")
    parser.add_argument("--effect-level", help="效力级别过滤（仅 law）")
    parser.add_argument("--case-type", help="案件类别过滤（仅 case）：刑事案件/民事案件/等")
    parser.add_argument("--case-start", help="结案起始日期（仅 case），YYYY-MM-DD")
    parser.add_argument("--case-end", help="结案截止日期（仅 case），YYYY-MM-DD")
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = get_api_key()

    if args.type == "law":
        payload = {"query": args.query, "rewrite_flag": False, "return_num": args.top_k}
        fatiao_filter = {}
        if args.validity:
            fatiao_filter["sxx"] = [args.validity]
        if args.effect_level:
            fatiao_filter["effect1"] = [args.effect_level]
        if fatiao_filter:
            payload["fatiao_filter"] = fatiao_filter
        result = api_post("law_vector_search", payload, api_key)
        key_field = "fatiao"
    else:
        payload = {"query": args.query, "rewrite_flag": False, "return_num": args.top_k}
        wenshu_filter = {}
        if args.case_type:
            wenshu_filter["wenshu_type"] = args.case_type
        if args.case_start:
            wenshu_filter["ja_start"] = args.case_start
        if args.case_end:
            wenshu_filter["ja_end"] = args.case_end
        if wenshu_filter:
            payload["wenshu_filter"] = wenshu_filter
        result = api_post("case_vector_search", payload, api_key)
        key_field = "wenshu"

    if result.get("code") in (200, 201):
        items = result.get("extra", {}).get(key_field, [])
        output = {
            "status": "correct",
            "type": args.type,
            "query": args.query,
            "count": len(items),
            "results": items[:args.top_k],
        }
        print(json.dumps(output, ensure_ascii=False, default=str))
    else:
        output = {
            "status": "error",
            "type": args.type,
            "query": args.query,
            "message": result.get("msg", "检索失败"),
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
