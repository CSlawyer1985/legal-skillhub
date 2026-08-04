#!/usr/bin/env python3
"""88查公司风险查询 CLI 入口"""

COMMAND_NAME = "companyRisk"
COMMAND_DESC = "公司风险查询"

import os
import sys
import json
import argparse

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..')))

from _auth import get_ak_from_env
from _output import print_output, print_error
from capabilities.companyRisk.service import company_risk


# 风险等级排序（用于汇总展示）
_LEVEL_ORDER = ["高风险", "中风险", "低风险", "提示"]


def _format_timestamp(ts) -> str:
    """毫秒时间戳 → YYYY-MM-DD"""
    if not ts:
        return "-"
    try:
        from datetime import datetime
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return "-"


def _parse_content(content: str) -> dict:
    """contentChinese 字段是 JSON 字符串，解析为 dict"""
    if not content or not isinstance(content, str):
        return {}
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {}


def _format_content_dict(content_dict: dict) -> str:
    """把内容 dict 渲染为单元格内的 key: value 摘要"""
    if not content_dict:
        return "-"
    parts = []
    for k, v in content_dict.items():
        if v is None or v == "":
            continue
        v_str = str(v).replace("|", "／").replace("\n", " ").strip()
        parts.append(f"**{k}**：{v_str}")
    return "<br/>".join(parts) if parts else "-"


def _build_markdown(result: dict, key: str) -> str:
    """将风险查询结果格式化为 markdown"""
    total = result.get("total", 0)
    risk_map = result.get("riskMap") or {}
    page_no = result.get("pageNo", 1)
    page_size = result.get("pageSize", 10)

    lines = [
        "# 企业风险查询结果",
        f"**查询关键字：** `{key}`",
        f"**总记录数：** {total} 条　**当前页：** {page_no}　**每页：** {page_size}\n",
    ]

    if total == 0 or not risk_map:
        lines.append("✅ 未发现风险记录。")
        return "\n".join(lines)

    # 1) 概览：按主类型 + 风险等级聚合
    lines.append("## 风险概览\n")
    lines.append("| 风险大类 | 记录数 | 风险等级分布 |")
    lines.append("|---------|-------|------------|")
    for main_type, records in risk_map.items():
        count = len(records)
        level_count = {}
        for r in records:
            lvl = r.get("level") or "未标注"
            level_count[lvl] = level_count.get(lvl, 0) + 1
        # 按等级顺序拼接
        ordered_levels = sorted(
            level_count.items(),
            key=lambda kv: _LEVEL_ORDER.index(kv[0]) if kv[0] in _LEVEL_ORDER else 99,
        )
        level_str = "、".join(f"{lvl} {n}" for lvl, n in ordered_levels) or "-"
        lines.append(f"| {main_type} | {count} | {level_str} |")
    lines.append("")

    # 2) 各风险大类明细
    for main_type, records in risk_map.items():
        if not records:
            continue
        lines.append(f"## {main_type}（{len(records)} 条）\n")
        lines.append("| # | 风险等级 | 子类型 | 时间 | 企业名称 | 详情 |")
        lines.append("|---|---------|-------|------|---------|------|")
        for idx, r in enumerate(records, 1):
            level = r.get("level") or "-"
            sub_type = r.get("subType") or "-"
            time_str = r.get("time") or _format_timestamp(r.get("timeStamp"))
            if isinstance(time_str, str) and " " in time_str:
                time_str = time_str.split(" ")[0]
            company_name = r.get("companyName") or "-"
            content = _format_content_dict(_parse_content(r.get("contentChinese")))
            lines.append(
                f"| {idx} | {level} | {sub_type} | {time_str} | {company_name} | {content} |"
            )
        lines.append("")

    return "\n".join(lines)


def main():
    ak_id, _ = get_ak_from_env()
    if not ak_id:
        print_output(
            False,
            "AK 未配置。\n\n运行: `cli.py configure YOUR_AK`",
            {"data": {}},
        )
        return

    parser = argparse.ArgumentParser(description="88查公司风险查询")
    parser.add_argument("--socialCreditCode", "-s", default="",
                        help="统一社会信用代码（与 --companyId 二选一）")
    parser.add_argument("--companyId", "-c", default="",
                        help="企业 ID（与 --socialCreditCode 二选一）")
    parser.add_argument("--page", "-p", type=int, default=1, help="页码（默认 1）")
    parser.add_argument("--pageSize", "-n", type=int, default=10, help="每页数量（默认 10）")
    args = parser.parse_args()

    if not args.socialCreditCode and not args.companyId:
        print_output(
            False,
            "❌ 参数缺失：必须提供 --socialCreditCode 或 --companyId 至少一个。",
            {"data": {}},
        )
        return

    key = args.socialCreditCode or args.companyId

    try:
        result = company_risk(
            social_credit_code=args.socialCreditCode,
            company_id=args.companyId,
            page=args.page,
            page_size=args.pageSize,
        )
        markdown = _build_markdown(result, key)
        print_output(True, markdown, {"data": result})
    except Exception as e:
        print_error(e, {"data": {}})


if __name__ == "__main__":
    main()
