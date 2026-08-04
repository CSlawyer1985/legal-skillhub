#!/usr/bin/env python3
"""
跨境魔方全球企业库股东列表查询
根据公司ID获取公司的股东信息。
"""
import argparse
import sys
from common import make_request, print_json_output, cover_fee_info


def get_shareholder_list(pid: str) -> dict:
    """
    根据公司ID获取股东列表。

    Args:
        pid: 公司ID

    Returns:
        包含股东列表的API响应
    """
    response = make_request('/agent/search/depth_company/company/shareholder/list', {'pid': pid})
    return response


def main():
    parser = argparse.ArgumentParser(
        description='从跨境魔方开放平台获取全球企业库公司股东列表'
    )
    parser.add_argument(
        '--pid',
        required=True,
        help='公司ID（如 US_12345）'
    )

    args = parser.parse_args()

    # 获取股东列表
    response = get_shareholder_list(args.pid)

    # 从响应中提取数据
    if response.get('code') in (0, 200):
        data = response.get('data', {})
        print_json_output({"data": data, "fee": cover_fee_info(response.get('fee', {}))})
    else:
        print(f"错误：{response.get('msg', '未知错误')}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
