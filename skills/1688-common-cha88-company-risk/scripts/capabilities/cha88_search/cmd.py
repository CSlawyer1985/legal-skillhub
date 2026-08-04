#!/usr/bin/env python3
"""88查企业搜索 CLI 入口"""

COMMAND_NAME = "cha88_search"
COMMAND_DESC = "企业搜索"

import os
import sys
import argparse

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..')))

from _auth import get_ak_from_env
from _output import print_output, print_error
from capabilities.cha88_search.service import company_search


def _build_markdown(result: dict, keyword: str, page_no: int, page_size: int) -> str:
    """将搜索结果格式化为 markdown"""
    companies = result.get("data", []) or []

    if not companies:
        return f"未找到与「{keyword}」相关的企业信息。"

    total = result.get("total", len(companies))
    total_page = result.get("totalPage", 1)

    lines = [
        f"# 企业查询结果：{keyword}",
        f"共找到 **{total}** 家企业，第 **{page_no}/{total_page}** 页（每页 {page_size} 条）\n",
    ]

    for idx, company in enumerate(companies, 1):
        ent_name = (company.get("ent_name") or "").replace("<em>", "**").replace("</em>", "**")
        legal_name = company.get("legal_name", "-")
        ent_status = company.get("ent_status", "-")
        reg_cap = company.get("reg_cap", "-")
        currency_type = company.get("currencyType", "")
        if currency_type and reg_cap != "-":
            reg_cap = f"{reg_cap}（{currency_type}）"
        social_credit_code = company.get("social_credit_code", "-")
        es_date = company.get("es_date", "-")
        ent_type = company.get("ent_type", "-")
        address = company.get("address", "-")
        ability_label = company.get("ability_label_outside", "-")
        if ability_label and ability_label.startswith("ZM$"):
            ability_label = ability_label[3:]
        ability_label = ability_label.replace(";", "、") if ability_label else "-"

        lines.append(f"---\n")
        lines.append(f"## {idx}. {ent_name}\n")
        lines.append(f"| 项目 | 内容 |")
        lines.append(f"|------|------|")
        lines.append(f"| **法人代表** | {legal_name} |")
        lines.append(f"| **企业状态** | {ent_status} |")
        lines.append(f"| **注册资本** | {reg_cap} |")
        lines.append(f"| **统一社会信用代码** | `{social_credit_code}` |")
        lines.append(f"| **成立日期** | {es_date} |")
        lines.append(f"| **企业类型** | {ent_type} |")
        lines.append(f"| **注册地址** | {address} |")
        lines.append(f"| **能力标签** | {ability_label} |")
        lines.append("")

    return "\n".join(lines)


def main():
    ak_id, _ = get_ak_from_env()
    if not ak_id:
        print_output(False,
                     "AK 未配置。\n\n运行: `cli.py configure YOUR_AK`",
                     {"data": {}})
        return

    parser = argparse.ArgumentParser(description="88查企业搜索")
    parser.add_argument("--keyword", "-k", required=True, help="公司名称关键词")
    parser.add_argument("--pageNo", "-n", type=int, default=1, help="页码（默认 1）")
    parser.add_argument("--pageSize", "-s", type=int, default=10, help="每页数量（默认 10）")
    args = parser.parse_args()

    try:
        result = company_search(args.keyword, args.pageNo, args.pageSize)
        markdown = _build_markdown(result, args.keyword, args.pageNo, args.pageSize)
        print_output(True, markdown, {"data": result})
    except Exception as e:
        print_error(e, {"data": {}})


if __name__ == "__main__":
    main()
