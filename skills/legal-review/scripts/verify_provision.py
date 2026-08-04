#!/usr/bin/env python3
"""Verify a legal provision citation by law name + article number."""
import argparse
import json
import sys

from util import get_api_key, api_post


def parse_args():
    parser = argparse.ArgumentParser(description="核验法条引用")
    parser.add_argument("--law", required=True, help="法规名称，如：中华人民共和国民法典")
    parser.add_argument("--article", required=True, help="条号，如：第一千零七十六条")
    parser.add_argument("--generated-text", help="AI 生成的原文，传入后可自动比对")
    parser.add_argument("--refer-date", help="参考日期，格式 YYYY-MM-DD")
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = get_api_key()

    payload = {"fgmc": args.law, "ftnum": args.article}
    if args.refer_date:
        payload["refer_date"] = args.refer_date

    result = api_post("rh_ft_detail", payload, api_key)
    data = result.get("data")

    if data and data.get("ft_num"):
        authoritative_text = data.get("content", "").strip()
        output = {
            "status": "correct",
            "type": "法条",
            "citation": f"《{args.law}》{args.article}",
            "data": {
                "law_name": data.get("fgmc", ""),
                "article": data.get("ft_num", ""),
                "title": data.get("ftmc", ""),
                "content": authoritative_text,
                "validity": data.get("sxx", ""),
                "effect_level": data.get("xljb_1", ""),
                "issue_date": data.get("fbrq", ""),
                "effective_date": data.get("ssrq", ""),
            },
            "generated": {
                "law": args.law,
                "article": args.article,
                "text": args.generated_text,
            },
        }

        # 自动比对原文
        if args.generated_text:
            gen_clean = args.generated_text.strip().replace("\n", "").replace(" ", "").replace("　", "")
            auth_clean = authoritative_text.replace("\n", "").replace(" ", "").replace("　", "")
            if gen_clean == auth_clean:
                output["match"] = "exact"
            elif gen_clean in auth_clean:
                # AI 的引用是权威原文的摘录，内容正确
                output["match"] = "exact"
            elif auth_clean in gen_clean:
                # AI 包含了完整原文，但可能有多余文字
                output["match"] = "exact"
            else:
                output["match"] = "different"
                output["status"] = "incorrect"
                output["discrepancy"] = "生成文本与权威原文不符"

        print(json.dumps(output, ensure_ascii=False))
        return

    if result.get("code") == 0:
        output = {
            "status": "error",
            "type": "法条",
            "citation": f"《{args.law}》{args.article}",
            "message": result.get("message", "请求失败"),
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)
        return

    output = {
        "status": "not_found",
        "type": "法条",
        "citation": f"《{args.law}》{args.article}",
        "message": "未查询到相关内容",
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
