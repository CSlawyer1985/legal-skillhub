#!/usr/bin/env python3
"""
检查清单生成器 (Checklist Generator)

输入：投标文件路径
输出：格式检查清单Markdown文件，包含内容检查、格式检查、一致性检查三大类

用法：
    python checklist_generator.py bid_document.docx [--output checklist.md]
    python checklist_generator.py bid_document.pdf [--output checklist.md]
"""

import json
import argparse
import re
from datetime import datetime
from pathlib import Path


# 检查项定义
CONTENT_CHECKS = [
    {"id": "C01", "category": "内容检查", "item": "项目名称、招标编号、报价是否正确", "method": "人工核对"},
    {"id": "C02", "category": "内容检查", "item": "授权书是否签署并加盖公章", "method": "逐页检查签章"},
    {"id": "C03", "category": "内容检查", "item": "所有资格证明文件在有效期内", "method": "核对证件有效期"},
    {"id": "C04", "category": "内容检查", "item": "技术方案逐条响应招标要求", "method": "对照响应矩阵"},
    {"id": "C05", "category": "内容检查", "item": "报价明细表计算正确，总价与投标函一致", "method": "双人交叉核对"},
    {"id": "C06", "category": "内容检查", "item": "所有表格填写完整并签章", "method": "逐表检查"},
    {"id": "C07", "category": "内容检查", "item": "目录页码与实际页码对应", "method": "逐一验证"},
    {"id": "C08", "category": "内容检查", "item": "投标函与报价表中的货币单位一致", "method": "人工核对"},
    {"id": "C09", "category": "内容检查", "item": "技术偏离表无遗漏、无错误", "method": "对照招标参数逐条"},
    {"id": "C10", "category": "内容检查", "item": "商务条款全部响应", "method": "对照招标商务条款"},
    {"id": "C11", "category": "内容检查", "item": "业绩材料完整有效（每个案例四要素）", "method": "逐一核查"},
    {"id": "C12", "category": "内容检查", "item": "无模糊表述（'可能''大概''也许'等）", "method": "全文搜索关键词"},
    {"id": "C13", "category": "内容检查", "item": "技术参数带单位且与招标原文一致", "method": "抽查比对"},
    {"id": "C14", "category": "内容检查", "item": "实质性条款（★号）完全满足", "method": "逐条确认"},
    {"id": "C15", "category": "内容检查", "item": "页码连续、无跳页", "method": "逐页浏览"},
]

FORMAT_CHECKS = [
    {"id": "F01", "category": "格式检查", "item": "正文小四宋体、目录四号宋体", "method": "检查字体设置"},
    {"id": "F02", "category": "格式检查", "item": "1.5倍行距、段落首行缩进两字符", "method": "检查段落设置"},
    {"id": "F03", "category": "格式检查", "item": "页面A4尺寸（210mm×297mm）", "method": "检查页面设置"},
    {"id": "F04", "category": "格式检查", "item": "文件命名符合招标要求", "method": "逐字核对文件名"},
    {"id": "F05", "category": "格式检查", "item": "文件格式符合要求（PDF/DOCX）", "method": "检查文件属性"},
    {"id": "F06", "category": "格式检查", "item": "电子签章完整有效（CA认证）", "method": "检查签章面板"},
    {"id": "F07", "category": "格式检查", "item": "PDF为双层格式（可搜索文字）", "method": "Ctrl+F搜索测试"},
    {"id": "F08", "category": "格式检查", "item": "文件大小在平台限制内", "method": "检查文件属性"},
    {"id": "F09", "category": "格式检查", "item": "无密码保护", "method": "尝试无密码打开"},
    {"id": "F10", "category": "格式检查", "item": "图表清晰、图例规范", "method": "放大逐一查看"},
]

CONSISTENCY_CHECKS = [
    {"id": "S01", "category": "一致性检查", "item": "报价总价 = 各分项报价之和", "method": "Excel公式复核"},
    {"id": "S02", "category": "一致性检查", "item": "投标函报价 = 报价一览表报价", "method": "交叉对比"},
    {"id": "S03", "category": "一致性检查", "item": "报价大小写一致", "method": "逐字核对"},
    {"id": "S04", "category": "一致性检查", "item": "货币单位全文统一", "method": "全文搜索"},
    {"id": "S05", "category": "一致性检查", "item": "投标函签字人 = 授权书被授权人", "method": "比对姓名"},
    {"id": "S06", "category": "一致性检查", "item": "项目经理名字全文一致", "method": "全文搜索"},
    {"id": "S07", "category": "一致性检查", "item": "人员名单与简历一一对应", "method": "逐人核对"},
    {"id": "S08", "category": "一致性检查", "item": "签署日期在投标截止日期之前", "method": "日期比对"},
    {"id": "S09", "category": "一致性检查", "item": "授权书有效期覆盖投标有效期", "method": "日期计算"},
    {"id": "S10", "category": "一致性检查", "item": "证书有效期覆盖整个投标有效期", "method": "逐证核对日期"},
    {"id": "S11", "category": "一致性检查", "item": "项目名称全文统一", "method": "全文搜索"},
    {"id": "S12", "category": "一致性检查", "item": "招标编号全文统一", "method": "全文搜索"},
    {"id": "S13", "category": "一致性检查", "item": "投标人名称与公章一致", "method": "逐处比对"},
    {"id": "S14", "category": "一致性检查", "item": "专业术语使用一致", "method": "全文搜索"},
    {"id": "S15", "category": "一致性检查", "item": "联系方式（电话/邮箱）全文统一", "method": "全文搜索"},
]


def export_checklist(all_checks: list, output_path: str):
    """导出检查清单为Markdown文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 投标文件格式检查清单\n\n")
        f.write(f"检查日期：{datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 说明
        f.write("> 在提交投标文件前，请按照此清单逐项核对。每项检查完成后勾选对应复选框。\n\n")

        current_category = ""

        for check in all_checks:
            if check["category"] != current_category:
                current_category = check["category"]
                cat_emoji = {
                    "内容检查": "📄",
                    "格式检查": "📐",
                    "一致性检查": "🔄",
                }.get(current_category, "📋")
                f.write(f"## {cat_emoji} {current_category}\n\n")
                f.write("| 序号 | 检查项 | 检查方法 | 状态 | 备注 |\n")
                f.write("|------|--------|---------|------|------|\n")

            f.write(
                f"| {check['id']} | {check['item']} | {check['method']} | ☐ 待检查 | |\n"
            )

        f.write(f"\n---\n\n")
        f.write(f"## 检查统计\n\n")

        categories = {}
        for c in all_checks:
            cat = c["category"]
            categories[cat] = categories.get(cat, 0) + 1

        f.write("| 检查类别 | 检查项数 |\n")
        f.write("|---------|--------|\n")
        for cat, count in categories.items():
            f.write(f"| {cat} | {count} |\n")
        f.write(f"| **合计** | **{len(all_checks)}** |\n")


def main():
    parser = argparse.ArgumentParser(
        description="检查清单生成器 - 生成投标文件格式检查清单"
    )
    parser.add_argument(
        "document",
        nargs="?",
        help="投标文件路径（用于记录检查对象）"
    )
    parser.add_argument(
        "--output", "-o",
        default="format_checklist_output.md",
        help="输出文件路径（默认: format_checklist_output.md）"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="同时输出JSON格式"
    )

    args = parser.parse_args()

    all_checks = CONTENT_CHECKS + FORMAT_CHECKS + CONSISTENCY_CHECKS

    # 如果指定了文档路径，在输出中记录
    doc_info = ""
    if args.document:
        doc_info = f"检查对象：{args.document}\n\n"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# 投标文件格式检查清单\n\n")
        if doc_info:
            f.write(doc_info)
        f.write(f"检查日期：{datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("> 在提交投标文件前，请按照此清单逐项核对。每项检查完成后勾选对应复选框。\n\n")
        f.write("> 状态标记：✅ 通过 | ❌ 不通过 | ⚠️ 需改进 | N/A 不适用\n\n")

        current_category = ""
        for check in all_checks:
            if check["category"] != current_category:
                current_category = check["category"]
                cat_emoji = {
                    "内容检查": "📄",
                    "格式检查": "📐",
                    "一致性检查": "🔄",
                }.get(current_category, "📋")
                f.write(f"## {cat_emoji} {current_category}\n\n")
                f.write("| 序号 | 检查项 | 检查方法 | 状态 | 备注 |\n")
                f.write("|------|--------|---------|------|------|\n")
            f.write(
                f"| {check['id']} | {check['item']} | {check['method']} | ☐ 待检查 | |\n"
            )

        # 统计
        f.write(f"\n---\n\n## 检查统计\n\n")
        categories = {}
        for c in all_checks:
            cat = c["category"]
            categories[cat] = categories.get(cat, 0) + 1
        f.write("| 检查类别 | 检查项数 |\n")
        f.write("|---------|--------|\n")
        for cat, count in categories.items():
            f.write(f"| {cat} | {count} |\n")
        f.write(f"| **合计** | **{len(all_checks)}** |\n")
        f.write(f"\n---\n\n## 审核签字\n\n")
        f.write("| 审核角色 | 签字 | 日期 |\n")
        f.write("|---------|-----|------|\n")
        f.write("| 编制人 | | |\n")
        f.write("| 技术负责人 | | |\n")
        f.write("| 商务负责人 | | |\n")
        f.write("| 授权代表 | | |\n")

    print(f"✅ 检查清单已导出至: {args.output}")

    if args.json:
        json_path = args.output.replace(".md", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_checks, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON格式已导出至: {json_path}")


if __name__ == "__main__":
    main()
