#!/usr/bin/env python3
"""
AI法律数据库检索 - 类案分析引擎
对检索到的案例进行聚类分析、裁判观点提炼和相似度评估
"""

import json
import re
from collections import Counter
from typing import List, Dict, Any


def analyze_similar_cases(cases: List[Dict], query: str = "") -> Dict[str, Any]:
    """
    对案例列表进行类案分析

    Args:
        cases: 案例列表，每个案例包含 case_num, court, date, summary, result 等字段
        query: 原始检索词

    Returns:
        分析结果字典，包含 cluster_results, consensus, divergence, statistics
    """
    if not cases:
        return {
            "cluster_results": [],
            "consensus": "暂无数据",
            "divergence": "暂无数据",
            "statistics": {},
        }

    # 1. 按法院层级聚类
    court_clusters = _cluster_by_court(cases)

    # 2. 按裁判结果聚类
    result_clusters = _cluster_by_result(cases)

    # 3. 按时间分布
    timeline = _cluster_by_timeline(cases)

    # 4. 提取共识观点
    consensus = _extract_consensus(cases)

    # 5. 提取分歧
    divergence = _extract_divergence(cases)

    # 6. 统计
    statistics = {
        "total": len(cases),
        "court_distribution": {k: len(v) for k, v in court_clusters.items()},
        "result_distribution": dict(Counter(c.get("result", "未知") for c in cases)),
        "year_distribution": dict(sorted(timeline.items())),
    }

    return {
        "cluster_results": {
            "by_court": court_clusters,
            "by_result": result_clusters,
            "by_timeline": timeline,
        },
        "consensus": consensus,
        "divergence": divergence,
        "statistics": statistics,
    }


def _cluster_by_court(cases: List[Dict]) -> Dict[str, List[Dict]]:
    """按法院层级和地域聚类"""
    clusters = {}
    for case in cases:
        court = case.get("court", "未知法院")
        # 提取法院层级：最高人民法院、高级、中级、基层
        if "最高" in court:
            level = "最高人民法院"
        elif "高级" in court:
            level = "高级人民法院"
        elif "中级" in court or "中院" in court:
            level = "中级人民法院"
        else:
            level = "基层人民法院"

        if level not in clusters:
            clusters[level] = []
        clusters[level].append(case)

    return clusters


def _cluster_by_result(cases: List[Dict]) -> Dict[str, List[Dict]]:
    """按裁判结果聚类"""
    clusters = {}
    for case in cases:
        result = case.get("result", "未知")
        # 标准化结果分类
        if any(kw in str(result) for kw in ["支持", "胜诉", "维持", "确认", "成立"]):
            cat = "支持/胜诉"
        elif any(kw in str(result) for kw in ["驳回", "不予支持", "撤销", "不予认定", "不认定"]):
            cat = "驳回/不支持"
        elif any(kw in str(result) for kw in ["调解", "和解"]):
            cat = "调解/和解"
        else:
            cat = "其他"

        if cat not in clusters:
            clusters[cat] = []
        clusters[cat].append(case)

    return clusters


def _cluster_by_timeline(cases: List[Dict]) -> Dict[str, int]:
    """按年份归类"""
    years = Counter()
    for case in cases:
        date = case.get("date", "") or case.get("judgment_date", "")
        if date and len(date) >= 4:
            year = date[:4]
            years[year] += 1
    return dict(years)


def _extract_consensus(cases: List[Dict]) -> str:
    """提取类案中的共识观点"""
    results = [str(c.get("result", "")) for c in cases]
    opinions = [str(c.get("opinion", "")) for c in cases]

    # 统计结果倾向
    positive = sum(1 for r in results if any(kw in r for kw in ["支持", "胜诉", "维持", "确认", "成立"]))
    negative = sum(1 for r in results if any(kw in r for kw in ["驳回", "不予", "撤销", "不认定"]))
    total = len(results)

    if total == 0:
        return "暂无足够案例形成共识"

    parts = []
    if positive > total * 0.6:
        parts.append(f"多数法院（{positive}/{total}）持支持态度")
    elif negative > total * 0.6:
        parts.append(f"多数法院（{negative}/{total}）持驳回态度")
    else:
        parts.append(f"法院观点存在分歧（支持{positive}件/驳回{negative}件）")

    # 提取常见关键词
    if opinions:
        all_text = " ".join(opinions)
        keywords = ["实质重于形式", "从属性", "公平原则", "诚实信用", "比例原则", "利益平衡"]
        found_kw = [kw for kw in keywords if kw in all_text]
        if found_kw:
            parts.append(f"常见裁判逻辑涉及：{'、'.join(found_kw)}")

    return "；".join(parts)


def _extract_divergence(cases: List[Dict]) -> str:
    """提取裁判分歧点"""
    courts = [c.get("court", "") for c in cases]
    results = [str(c.get("result", "")) for c in cases]

    # 检查是否存在结果分歧
    positive_courts = [
        courts[i]
        for i in range(len(courts))
        if any(kw in results[i] for kw in ["支持", "胜诉", "确认", "成立"])
    ]
    negative_courts = [
        courts[i]
        for i in range(len(courts))
        if any(kw in results[i] for kw in ["驳回", "不予", "不认定", "撤销"])
    ]

    parts = []
    if positive_courts and negative_courts:
        parts.append(f"存在裁判分歧：{len(positive_courts)}家法院支持 vs {len(negative_courts)}家法院驳回")
        if len(positive_courts) <= 3:
            parts.append(f"支持方：{'、'.join(positive_courts[:3])}")
        if len(negative_courts) <= 3:
            parts.append(f"反对方：{'、'.join(negative_courts[:3])}")

    # 地域分歧
    regions_pos = set(re.findall(r"(北京|上海|广州|深圳|杭州|成都|武汉|南京)", " ".join(positive_courts)))
    regions_neg = set(re.findall(r"(北京|上海|广州|深圳|杭州|成都|武汉|南京)", " ".join(negative_courts)))
    diff = regions_pos - regions_neg
    if diff:
        parts.append(f"地域差异：{'、'.join(diff)}地区法院更倾向支持")

    if not parts:
        return "当前类案中未发现显著裁判分歧"

    return "；".join(parts)


def generate_comparison_table(cases: List[Dict]) -> List[Dict]:
    """生成标准化的类案对比表"""
    table = []
    for case in cases:
        table.append(
            {
                "case_num": case.get("case_num", ""),
                "court": case.get("court", ""),
                "date": case.get("date", ""),
                "dispute_focus": case.get("dispute_focus", case.get("title", "")),
                "opinion": case.get("opinion", case.get("summary", "")[:100]),
                "result": case.get("result", ""),
            }
        )
    return table


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="类案分析引擎")
    parser.add_argument("--input", "-i", help="输入案例JSON文件")
    parser.add_argument("--query", "-q", default="", help="检索词")
    parser.add_argument("--output", "-o", help="输出JSON文件")

    args = parser.parse_args()

    if args.input:
        cases = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        cases = json.loads(sys.stdin.read())

    result = analyze_similar_cases(cases, args.query)

    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"分析结果已保存: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
