#!/usr/bin/env python3
"""
审查报告生成器
汇总所有审查结果，渲染Markdown报告
"""
import argparse
import json
import os
import sys
from datetime import datetime
from collections import Counter

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("ERROR: Jinja2 not installed. Run: pip install jinja2", file=sys.stderr)
    sys.exit(1)


def load_tender_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_issue_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_conclusion(issues):
    """根据问题等级判定审查结论"""
    severities = [i.get("severity", "low") for i in issues]
    if "high" in severities:
        return "fail"
    elif "medium" in severities:
        return "conditional_pass"
    else:
        return "pass"


def compute_summary(issues):
    """计算统计摘要"""
    counter = Counter(i.get("severity", "low") for i in issues)
    category_counter = Counter(i.get("category", "unknown") for i in issues)
    return {
        "total_issues": len(issues),
        "high_count": counter.get("high", 0),
        "medium_count": counter.get("medium", 0),
        "low_count": counter.get("low", 0),
        "category_distribution": dict(category_counter)
    }


def main():
    parser = argparse.ArgumentParser(description='审查报告生成器')
    parser.add_argument('--project_id', required=True, help='项目ID')
    parser.add_argument('--tender_json', required=True, help='招标文件JSON路径')
    parser.add_argument('--issue_list', required=True, help='问题清单JSON路径')
    parser.add_argument('--template', required=True, help='报告模板路径')
    parser.add_argument('--output', required=True, help='输出报告路径')
    args = parser.parse_args()

    # 加载数据
    tender_data = load_tender_json(args.tender_json)
    issue_data = load_issue_list(args.issue_list)
    issues = issue_data.get("issues", [])

    # 计算结论和摘要
    conclusion = compute_conclusion(issues)
    summary = compute_summary(issues)

    # 准备模板上下文
    context = {
        "project_id": args.project_id,
        "review_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "conclusion": conclusion,
        "summary": summary,
        "issues": issues,
        "tender_data": tender_data
    }

    # 渲染模板
    template_dir = os.path.dirname(args.template)
    template_name = os.path.basename(args.template)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    report = template.render(**context)

    # 输出报告
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    # 输出元信息
    result = {
        "project_id": args.project_id,
        "report_path": args.output,
        "conclusion": conclusion,
        "summary": summary
    }

    meta_path = args.output.replace('.md', '_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"报告生成完成: {args.output}")
    print(f"审查结论: {conclusion}")
    print(f"问题总数: {summary['total_issues']} (高:{summary['high_count']} 中:{summary['medium_count']} 低:{summary['low_count']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
