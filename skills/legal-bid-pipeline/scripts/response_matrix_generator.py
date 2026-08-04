#!/usr/bin/env python3
"""
响应矩阵生成器 (Response Matrix Generator)

输入：招标要素JSON文件 + 公司能力库JSON文件（可选）
输出：响应矩阵Excel文件 (.xlsx) + 风险提示清单

用法：
    python response_matrix_generator.py tender_requirements.json [--company company_capabilities.json] [--output response_matrix.xlsx]
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path


def load_json(filepath: str) -> dict:
    """加载JSON文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_clause_type(clause: dict) -> str:
    """
    分类条款类型
    - 强制性 (mandatory): ★号条款、明确"必须满足"、"不可偏离"
    - 推荐性 (recommended): 加分项、建议项、"宜"
    - 隐含性 (implicit): 未明确但行业惯例
    """
    text = clause.get("description", "") + clause.get("requirement", "")
    text_lower = text.lower()

    mandatory_keywords = [
        "必须", "不可偏离", "实质性", "废标", "否决", "★", "☆",
        "应满足", "应符合", "必须满足", "必须具备"
    ]
    recommended_keywords = [
        "建议", "宜", "优先", "鼓励", "推荐", "加分", "更好",
        "最佳", "尽可能"
    ]

    for kw in mandatory_keywords:
        if kw in text:
            return "强制性"

    for kw in recommended_keywords:
        if kw in text:
            return "推荐性"

    return "隐含性"


def assess_risk(clause_type: str, response_status: str, has_support: bool) -> str:
    """
    评估响应风险等级
    - 高: 强制性条款不满足
    - 中: 推荐性条款不满足 或 隐含性无支撑材料
    - 低: 其他
    """
    if clause_type == "强制性" and response_status in ("不满足", "部分满足"):
        return "高（废标风险）"
    if clause_type == "强制性" and not has_support:
        return "中（需补充材料）"
    if clause_type == "推荐性" and response_status == "不满足":
        return "中（可能丢分）"
    if clause_type == "隐含性" and response_status == "不满足":
        return "低"
    return "低"


def generate_matrix(requirements: list, company_caps: dict = None) -> list:
    """
    生成响应矩阵
    每条招标要求映射到公司能力和建议响应章节
    """
    matrix = []
    company_caps = company_caps or {}

    for i, req in enumerate(requirements, 1):
        clause_num = req.get("clause_number", f"未编号_{i}")
        clause_text = req.get("description", req.get("requirement", ""))
        clause_type = classify_clause_type(req)

        # 尝试从公司能力库匹配
        matched_cap = None
        score = 0
        for cap_name, cap_info in company_caps.items():
            # 简单的关键词匹配
            cap_keywords = cap_info.get("keywords", [])
            matched_count = sum(
                1 for kw in cap_keywords if kw in clause_text
            )
            if matched_count > score:
                score = matched_count
                matched_cap = cap_info

        response_status = "满足" if matched_cap and score > 0 else "需评估"
        has_support = matched_cap is not None and score > 0

        # 建议章节
        chapter_map = {
            "资质": "第二章 资格证明文件",
            "业绩": "第五章 业绩与案例",
            "案例": "第五章 业绩与案例",
            "技术": "第三章 技术方案",
            "参数": "第三章 技术方案",
            "实施": "第三章 技术方案-项目实施计划",
            "售后": "第三章 技术方案-售后服务",
            "培训": "第四章 商务方案-培训计划",
            "报价": "第四章 商务方案",
            "付款": "第四章 商务方案-商务条款响应",
            "质保": "第四章 商务方案-售后服务承诺",
            "人员": "第二章 资格证明文件-项目团队",
            "财务": "第二章 资格证明文件-财务状况",
            "安全": "第三章 技术方案-安全与风险管理",
            "保密": "第四章 商务方案-合同条款响应",
            "知识产权": "第四章 商务方案-合同条款响应",
        }

        suggested_chapter = "待定"
        for kw, chapter in chapter_map.items():
            if kw in clause_text:
                suggested_chapter = chapter
                break

        risk = assess_risk(clause_type, response_status, has_support)

        matrix.append({
            "序号": i,
            "条款编号": clause_num,
            "条款原文摘要": clause_text[:150] + ("..." if len(clause_text) > 150 else ""),
            "条款类型": clause_type,
            "响应状态": response_status,
            "建议响应章节": suggested_chapter,
            "匹配能力": matched_cap.get("name", "未匹配") if matched_cap else "需手动匹配",
            "支撑材料": matched_cap.get("evidence", "需补充") if matched_cap else "需补充",
            "风险等级": risk,
        })

    return matrix


def export_to_markdown(matrix: list, output_path: str):
    """导出响应矩阵为Markdown表格"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 响应矩阵 (Compliance Matrix)\n\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 统计
        total = len(matrix)
        mandatory = sum(1 for r in matrix if r["条款类型"] == "强制性")
        high_risk = sum(1 for r in matrix if "高" in r["风险等级"])

        f.write(f"## 统计概览\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 总条款数 | {total} |\n")
        f.write(f"| 强制性条款 | {mandatory} |\n")
        f.write(f"| 推荐性条款 | {sum(1 for r in matrix if r['条款类型'] == '推荐性')} |\n")
        f.write(f"| 隐含性条款 | {sum(1 for r in matrix if r['条款类型'] == '隐含性')} |\n")
        f.write(f"| 高风险项 | {high_risk} |\n\n")

        # 主表格
        f.write(f"## 详细响应矩阵\n\n")
        headers = [
            "序号", "条款编号", "条款原文摘要", "条款类型",
            "响应状态", "建议响应章节", "匹配能力", "支撑材料", "风险等级"
        ]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["------"] * len(headers)) + "|\n")

        for row in matrix:
            values = [str(row.get(h, "")) for h in headers]
            f.write("| " + " | ".join(values) + " |\n")

        # 高风险项清单
        high_risk_items = [r for r in matrix if "高" in r["风险等级"]]
        if high_risk_items:
            f.write(f"\n## ⚠️ 高风险项清单\n\n")
            f.write(f"> 以下条款如不及时处理，可能导致废标或严重失分。\n\n")
            for item in high_risk_items:
                f.write(f"- **条款{item['条款编号']}**：[{item['条款类型']}] {item['条款原文摘要'][:100]}\n")
                f.write(f"  - 当前状态：{item['响应状态']}\n")
                f.write(f"  - 建议：需紧急补充支撑材料或调整方案\n\n")

    print(f"✅ 响应矩阵已导出至: {output_path}")


def create_sample_requirements() -> list:
    """创建示例招标要求JSON"""
    return [
        {"clause_number": "1.1.1", "description": "投标人须具备ISO 9001质量管理体系认证（★实质性条款）"},
        {"clause_number": "1.1.2", "description": "投标人须提供近3年内至少3个同类项目业绩证明"},
        {"clause_number": "1.1.3", "description": "投标人注册资本不低于1000万元人民币"},
        {"clause_number": "2.1.1", "description": "系统须支持7×24小时不间断运行，可用性≥99.9%"},
        {"clause_number": "2.1.2", "description": "支持国密SM4加密算法，通过等保三级测评"},
        {"clause_number": "2.1.3", "description": "单次查询响应时间≤3秒，并发用户数≥500"},
        {"clause_number": "2.2.1", "description": "提供完整的系统架构设计文档和技术方案"},
        {"clause_number": "2.2.2", "description": "建议兼容信创环境（麒麟操作系统+达梦数据库）"},
        {"clause_number": "3.1.1", "description": "交付周期不超过120个自然日"},
        {"clause_number": "3.1.2", "description": "质保期不少于3年，质保期内免费升级"},
        {"clause_number": "3.2.1", "description": "付款方式：合同签订后付30%，验收合格后付65%，质保期满付5%"},
        {"clause_number": "3.2.2", "description": "须提供7×24小时售后技术支持，故障响应时间≤30分钟"},
        {"clause_number": "4.1.1", "description": "项目经理须持有PMP或信息系统项目管理师证书"},
        {"clause_number": "4.1.2", "description": "须提供完整的项目实施方案和培训计划"},
        {"clause_number": "5.1.1", "description": "技术方案评分占60%，商务评分占30%，报价评分占10%"},
    ]


def main():
    parser = argparse.ArgumentParser(
        description="响应矩阵生成器 - 将招标要求转换为条款→响应映射表"
    )
    parser.add_argument(
        "requirements",
        nargs="?",
        help="招标要求JSON文件路径"
    )
    parser.add_argument(
        "--company", "-c",
        help="公司能力库JSON文件路径（可选）"
    )
    parser.add_argument(
        "--output", "-o",
        default="response_matrix.md",
        help="输出文件路径（默认: response_matrix.md）"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="生成示例招标要求JSON文件"
    )

    args = parser.parse_args()

    if args.sample:
        sample = create_sample_requirements()
        sample_path = "sample_requirements.json"
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)
        print(f"✅ 示例招标要求已生成: {sample_path}")
        print(f"   运行命令: python response_matrix_generator.py {sample_path}")
        return

    if not args.requirements:
        print("使用方法:")
        print("  1. 先生成示例文件: python response_matrix_generator.py --sample")
        print("  2. 编辑示例文件，填入实际招标要求")
        print("  3. 运行生成: python response_matrix_generator.py sample_requirements.json")
        print()
        print("  或直接指定您的招标要求JSON文件:")
        print("  python response_matrix_generator.py my_tender.json --company my_company.json -o matrix.md")
        return

    # 加载招标要求
    reqs = load_json(args.requirements)

    # 加载公司能力库（如果提供）
    company_caps = None
    if args.company:
        company_caps = load_json(args.company)

    # 生成响应矩阵
    matrix = generate_matrix(reqs, company_caps)

    # 导出
    export_to_markdown(matrix, args.output)


if __name__ == "__main__":
    main()
