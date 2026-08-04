#!/usr/bin/env python3
"""
工业招投标技术方案合规审查引擎
核心功能: 条款提取 → 标准匹配 → 逐条对标 → 合规判定 → 综合评分

使用方式:
  python compliance_checker.py --input tech_proposal.docx --type EQUIP --output result.json
  python compliance_checker.py --input tech_proposal.pdf --type ENG
  python compliance_checker.py --input clause_list.json --type SVC
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# 合规判定常量
PASS = "PASS"           # 完全合规
PASS_STAR = "PASS*"     # 基本合规
UNCERTAIN = "UNCERTAIN"  # 不确定
FAIL = "FAIL"           # 不合规
MISSING = "MISSING"     # 缺项
NA = "N/A"              # 不适用

COMPLIANCE_SCORE_MAP = {
    PASS: 1.0,
    PASS_STAR: 0.8,
    UNCERTAIN: 0.5,
    FAIL: 0.2,
    MISSING: 0.0,
    NA: -1
}

SEVERITY_MAP = {
    "P0": "critical",
    "P1": "warning",
    "P2": "warning",
    "P3": "info"
}

# 9维体系权重
DIMENSION_WEIGHT = {
    "技术参数": 0.20,
    "安全规范": 0.15,
    "环保要求": 0.10,
    "能效标准": 0.10,
    "质量管理": 0.10,
    "验收标准": 0.10,
    "强制条款": 0.15,
    "资质人员": 0.05,
    "知识产权": 0.05
}

DIMENSION_NAMES = list(DIMENSION_WEIGHT.keys())

# ★否决项关键词
MANDATORY_KEYWORDS = [
    "★", "*", "必须满足", "不得低于", "实质性要求",
    "废标", "否决", "无效标", "资格后审不通过",
    "不允许偏离", "不接受替代"
]


def load_clauses(input_path: str) -> list:
    """
    从结构化JSON加载条款列表。
    预期格式: [{"id": "CL-001", "content": "...", "category": "技术参数", ...}, ...]
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "clauses" in data:
        return data["clauses"]
    return []


def classify_clause_type(clause: dict) -> str:
    """判断条款类型: 实质性条款(★) / 一般条款 / 参考性条款"""
    content = clause.get("content", "")
    combined = f"{clause.get('section', '')} {content}"

    for kw in MANDATORY_KEYWORDS:
        if kw in combined:
            return "实质性条款"
    return clause.get("clause_type", "一般条款")


def classify_risk(clause: dict, compliance: str) -> str:
    """评估不合规风险等级"""
    clause_type = clause.get("clause_type", classify_clause_type(clause))

    if clause_type == "实质性条款" and compliance in (FAIL, MISSING):
        return "废标"
    if compliance == FAIL:
        return "扣分"
    if compliance == MISSING:
        return "扣分"
    if compliance == UNCERTAIN:
        return "需确认"
    return "无影响"


def match_standard(clause: dict, standards_map: dict) -> list:
    """
    根据条款内容匹配适用标准。
    简化版：基于关键词匹配
    """
    content = clause.get("content", "")
    matched = []

    keyword_standard_map = {
        "电机": ["GB 18613-2020 电动机能效限定值及能效等级"],
        "变压器": ["GB 20052-2020 电力变压器能效限定值及能效等级"],
        "压缩机": ["GB/T 13279-2015 一般用固定的往复活塞空气压缩机"],
        "空压机": ["GB/T 13279-2015 一般用固定的往复活塞空气压缩机"],
        "泵": ["GB/T 5656-2008 离心泵技术条件", "GB/T 3216-2016 回转动力泵 水力性能验收试验"],
        "容器": ["GB 150.1-2011 压力容器"],
        "压力容器": ["GB 150.1-2011 压力容器"],
        "换热器": ["GB/T 151-2014 热交换器"],
        "焊接": ["GB 50236-2011 现场设备、工业管道焊接工程施工规范"],
        "管道": ["GB 50235-2010 工业金属管道工程施工规范"],
        "电气": ["GB 7251.1-2013 低压成套开关设备和控制设备"],
        "开关柜": ["GB 7251.1-2013 低压成套开关设备和控制设备"],
        "消防": ["GB 50720-2011 建设工程施工现场消防安全技术规范", "GB 50016 建筑设计防火规范"],
        "噪声": ["GB 12523-2011 建筑施工场界环境噪声排放标准"],
        "安全阀": ["GB/T 12241-2021 安全阀 一般要求"],
        "能效": ["GB 18613-2020 电动机能效限定值及能效等级"],
        "排放": ["GB 8978-1996 污水综合排放标准", "GB 16297-1996 大气污染物综合排放标准"],
        "废水": ["GB 8978-1996 污水综合排放标准"],
        "废气": ["GB 16297-1996 大气污染物综合排放标准"],
        "固废": ["GB 18599-2020 一般工业固体废物贮存和填埋污染控制标准"],
        "质量": ["GB/T 19001-2016/ISO 9001:2015 质量管理体系"],
        "安全": ["AQ/T 9006-2010 企业安全生产标准化基本规范", "GB/T 45001-2020 职业健康安全管理体系"],
        "环境": ["GB/T 24001-2016/ISO 14001:2015 环境管理体系"],
        "安装": ["GB 50231-2009 机械设备安装工程施工及验收通用规范"],
        "验收": ["GB 50300-2013 建筑工程施工质量验收统一标准"],
        "特种设备": ["《特种设备安全法》", "TSG系列安全技术规范"],
        "知识产权": ["《专利法》", "《著作权法》"],
        "数据安全": ["GB/T 37988-2019 信息安全技术 数据安全能力成熟度模型"],
        "信息安全": ["GB/T 22080-2016/ISO/IEC 27001:2013 信息安全管理体系"],
    }

    for keyword, standards in keyword_standard_map.items():
        if keyword in content:
            matched.extend(standards)

    # 去重
    matched = list(set(matched))
    return matched[:5]  # 最多返回5条


def analyze_compliance(clause: dict, standards: list) -> dict:
    """
    核心审查逻辑: 分析条款与标准的合规性。
    注: 此为规则引擎版本，实际完整版需结合LLM语义分析。
    """
    content = clause.get("content", "")

    # 检查是否包含"满足"/"符合"/"达到"等肯定词
    positive_indicators = ["满足", "符合", "达到", "不低于", "≥", "优于", "通过"]
    negative_indicators = ["不满足", "不符合", "低于", "≤", "未达到", "缺失", "无"]

    has_positive = any(ind in content for ind in positive_indicators)
    has_negative = any(ind in content for ind in negative_indicators)

    # 基本判定逻辑
    if has_negative:
        compliance = FAIL
        score = COMPLIANCE_SCORE_MAP[FAIL]
        finding = f"条款存在否定表述，疑似不满足要求。" if not standards else \
                  f"条款内容与适用标准存在不一致，建议逐项核对。"
    elif has_positive:
        compliance = PASS
        score = COMPLIANCE_SCORE_MAP[PASS]
        finding = f"条款明确声明满足要求。" if not standards else \
                  f"条款内容与适用标准初步判断一致，建议人工复核确认。"
    else:
        if clause.get("clause_type") == "实质性条款":
            compliance = UNCERTAIN
            score = COMPLIANCE_SCORE_MAP[UNCERTAIN]
            finding = "该条款为实质性要求，但AI无法自动判定合规性，需人工审查。"
        else:
            compliance = PASS
            score = COMPLIANCE_SCORE_MAP[PASS]
            finding = "未检测到明显不合规信号，建议人工复核。"

    std_quote = ""
    if standards:
        std_quote = f"相关标准: {'; '.join(standards[:3])}"

    return {
        "compliance": compliance,
        "compliance_score": score,
        "finding": finding,
        "standard_quote": std_quote,
        "severity": SEVERITY_MAP.get(classify_risk(clause, compliance), "info")
    }


def compute_dimension_scores(reviews: list) -> dict:
    """计算9维合规评分"""
    dim_stats = {dim: {"total": 0, "score_sum": 0, "na": 0} for dim in DIMENSION_NAMES}

    for review in reviews:
        dim = review.get("category", "技术参数")
        if dim not in dim_stats:
            dim_stats[dim] = {"total": 0, "score_sum": 0, "na": 0}

        score = review.get("compliance_score", -1)
        if score == -1:
            dim_stats[dim]["na"] += 1
            continue

        dim_stats[dim]["total"] += 1
        dim_stats[dim]["score_sum"] += score

    dim_scores = {}
    for dim in DIMENSION_NAMES:
        stats = dim_stats[dim]
        valid_count = stats["total"]
        if valid_count > 0:
            dim_scores[dim] = round(stats["score_sum"] / valid_count * 100, 1)
        else:
            dim_scores[dim] = 100.0  # 无条款默认为满分

    # 综合合规率
    total_score = 0
    total_weight = 0
    for dim in DIMENSION_NAMES:
        w = DIMENSION_WEIGHT.get(dim, 0)
        total_score += dim_scores.get(dim, 100) * w
        total_weight += w

    if total_weight > 0:
        overall = round(total_score / total_weight, 1)
    else:
        overall = 100.0

    return {
        "overall_rate": overall,
        "dimension_rates": dim_scores,
        "dimension_weights": DIMENSION_WEIGHT
    }


def classify_overall_grade(rate: float) -> tuple:
    """综合合规等级判定"""
    if rate >= 95:
        return "优秀", "green"
    elif rate >= 85:
        return "良好", "yellow"
    elif rate >= 75:
        return "待改进", "orange"
    elif rate >= 60:
        return "不合格", "red"
    else:
        return "严重不合规", "black"


def compute_statistics(reviews: list) -> dict:
    """统计各判定等级数量"""
    stats = {PASS: 0, PASS_STAR: 0, UNCERTAIN: 0, FAIL: 0, MISSING: 0, NA: 0}
    for review in reviews:
        c = review.get("compliance", NA)
        if c in stats:
            stats[c] += 1
    return stats


def generate_gap_analysis(reviews: list) -> list:
    """生成差距分析清单（不合规项整改建议）"""
    gaps = []
    priority_map = {
        "废标": "P0",
        "扣分": "P1",
        "需确认": "P2",
        "无影响": "P3"
    }

    for i, review in enumerate(reviews):
        compliance = review.get("compliance", "")
        if compliance in (FAIL, MISSING, UNCERTAIN):
            clause = review.get("clause", {})
            risk = classify_risk(clause, compliance)
            gap = {
                "gap_id": f"GAP-{i+1:03d}",
                "review_id": review.get("review_id", f"REV-{i+1:03d}"),
                "clause_id": clause.get("id", f"CL-{i+1:03d}"),
                "clause_content": clause.get("content", ""),
                "category": clause.get("category", "技术参数"),
                "compliance": compliance,
                "risk": risk,
                "priority": priority_map.get(risk, "P2"),
                "finding": review.get("finding", ""),
                "standard_quote": review.get("standard_quote", ""),
                "remediation": generate_remediation(compliance, clause),
                "impact": risk
            }
            gaps.append(gap)

    # 按优先级排序 P0 > P1 > P2 > P3
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    gaps.sort(key=lambda x: priority_order.get(x["priority"], 99))
    return gaps


def generate_remediation(compliance: str, clause: dict) -> dict:
    """生成整改建议"""
    content = clause.get("content", "")
    if compliance == FAIL:
        return {
            "action": f"建议重新审核\"{content[:30]}...\"是否符合标准和招标要求，必要时修改技术方案。",
            "estimated_effort": "中等",
            "reference": "参见审查记录中的适用标准原文"
        }
    elif compliance == MISSING:
        return {
            "action": f"方案中缺少\"{content[:30]}...\"相关内容，必须补充完整。",
            "estimated_effort": "视补充内容而定",
            "reference": "参见招标文件要求"
        }
    elif compliance == UNCERTAIN:
        return {
            "action": f"建议人工审查\"{content[:30]}...\"的合规性，必要时咨询专业技术人员。",
            "estimated_effort": "低（确认即可）",
            "reference": "参见审查记录"
        }
    return {
        "action": "无需整改",
        "estimated_effort": "无",
        "reference": ""
    }


def build_mandatory_report(reviews: list) -> list:
    """构建★否决项专项报告"""
    mandatory = []
    for i, review in enumerate(reviews):
        clause = review.get("clause", {})
        if clause.get("clause_type") == "实质性条款":
            mandatory.append({
                "id": f"M-{i+1:03d}",
                "clause_id": clause.get("id", ""),
                "section": clause.get("section", ""),
                "content": clause.get("content", ""),
                "source_page": clause.get("source_page", ""),
                "compliance": review.get("compliance", ""),
                "finding": review.get("finding", ""),
                "risk": classify_risk(clause, review.get("compliance", FAIL))
            })
    return mandatory


def check_abandonment_risk(gaps: list) -> dict:
    """废标风险评估"""
    p0_gaps = [g for g in gaps if g.get("priority") == "P0"]
    fail_gaps = [g for g in gaps if g.get("compliance") == FAIL]
    missing_gaps = [g for g in gaps if g.get("compliance") == MISSING]

    has_risk = len(p0_gaps) > 0

    if len(p0_gaps) > 0:
        return {
            "has_abandonment_risk": True,
            "risk_level": "high",
            "p0_count": len(p0_gaps),
            "fail_count": len(fail_gaps),
            "missing_count": len(missing_gaps),
            "summary": f"存在 {len(p0_gaps)} 项★否决项不合规，投标存在废标风险。必须全部整改后方可提交。"
        }
    elif len(fail_gaps) > 0:
        return {
            "has_abandonment_risk": False,
            "risk_level": "medium",
            "p0_count": 0,
            "fail_count": len(fail_gaps),
            "missing_count": len(missing_gaps),
            "summary": f"存在 {len(fail_gaps)} 项不合规条款，可能扣分但不构成废标条件。"
        }
    else:
        return {
            "has_abandonment_risk": False,
            "risk_level": "low",
            "p0_count": 0,
            "fail_count": 0,
            "missing_count": len(missing_gaps),
            "summary": "未检测到废标风险。建议继续完善方案细节。"
        }


def run_compliance_check(
    input_path: str,
    project_type: str = "EQUIP",
    project_name: str = "工业项目"
) -> dict:
    """
    执行完整合规审查管线

    Args:
        input_path: 条款JSON文件路径
        project_type: 项目类型 (EQUIP/ENG/SVC)
        project_name: 项目名称

    Returns:
        完整审查结果字典
    """

    # 1. 加载条款
    clauses = load_clauses(input_path)
    if not clauses:
        return {"error": "No clauses found in input file.", "clauses_loaded": 0}

    # 2. 准备标准映射
    standards_map = {}  # 简化版

    # 3. 逐条审查
    reviews = []
    for i, clause in enumerate(clauses):
        # 补充条款类型
        clause["clause_type"] = clause.get("clause_type") or classify_clause_type(clause)

        # 匹配标准
        standards = match_standard(clause, standards_map)

        # 合规分析
        result = analyze_compliance(clause, standards)

        review = {
            "review_id": f"REV-{i+1:03d}",
            "clause_id": clause.get("id", f"CL-{i+1:03d}"),
            "clause": clause,
            "category": clause.get("category", "技术参数"),
            "applicable_standards": standards,
            "compliance": result["compliance"],
            "compliance_score": result["compliance_score"],
            "finding": result["finding"],
            "standard_quote": result["standard_quote"],
            "remediation": None if result["compliance"] == PASS else \
                          generate_remediation(result["compliance"], clause),
            "severity": result["severity"]
        }
        reviews.append(review)

    # 4. 计算评分
    scores = compute_dimension_scores(reviews)
    grade, grade_color = classify_overall_grade(scores["overall_rate"])

    # 5. 统计
    stats = compute_statistics(reviews)

    # 6. 差距分析
    gaps = generate_gap_analysis(reviews)

    # 7. ★否决项报告
    mandatory = build_mandatory_report(reviews)

    # 8. 废标风险评估
    abandonment = check_abandonment_risk(gaps)

    # 9. 组装结果
    return {
        "project_info": {
            "name": project_name,
            "type": project_type,
            "review_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_clauses": len(clauses),
            "standards_applied": len(set(
                std for r in reviews for std in r.get("applicable_standards", [])
            ))
        },
        "compliance_overview": {
            "overall_rate": scores["overall_rate"],
            "grade": grade,
            "grade_color": grade_color,
            "dimension_rates": scores["dimension_rates"],
            "dimension_weights": scores["dimension_weights"],
            "statistics": stats
        },
        "reviews": reviews,
        "gaps": gaps,
        "mandatory_report": mandatory,
        "abandonment_risk": abandonment
    }


def main():
    parser = argparse.ArgumentParser(
        description="工业招投标技术方案合规审查引擎"
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="条款JSON输入文件路径"
    )
    parser.add_argument(
        "--type", "-t", default="EQUIP",
        choices=["EQUIP", "ENG", "SVC"],
        help="项目类型: EQUIP(设备采购) / ENG(工程施工) / SVC(技术服务)"
    )
    parser.add_argument(
        "--name", "-n", default="工业项目",
        help="项目名称"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="输出JSON文件路径（可选，默认输出到stdout）"
    )

    args = parser.parse_args()

    result = run_compliance_check(args.input, args.type, args.name)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding='utf-8')
        print(f"审查结果已保存到: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
