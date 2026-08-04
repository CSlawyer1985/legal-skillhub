#!/usr/bin/env python3
"""
合规审查规则引擎
通用规则执行脚本，支持多种扫描类型
加载YAML规则文件，对结构化招标JSON执行规则匹配，输出issue清单
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_rules(rules_path):
    """加载YAML规则文件"""
    with open(rules_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('rules', [])


def load_tender_json(tender_json_path):
    """加载结构化招标文件JSON"""
    with open(tender_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_existing_issues(issue_list_path):
    """加载已有issue清单（用于追加）"""
    if os.path.exists(issue_list_path):
        with open(issue_list_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"project_id": "", "issues": [], "issue_count": 0}


def match_pattern(text, pattern):
    """使用正则匹配文本"""
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return False


def check_exclusion(text, exclusion_patterns):
    """检查排除模式"""
    for ep in exclusion_patterns:
        if match_pattern(text, ep):
            return True
    return False


def scan_section(section, rule):
    """对单个section执行单条规则扫描"""
    content = section.get("content", "")
    title = section.get("title", "")
    combined_text = f"{title}\n{content}"

    issues = []

    # 缺席检查（如不可抗力条款缺失）
    if rule.get("is_absence_check"):
        has_keyword = False
        for kw in rule.get("keywords", []):
            if kw in combined_text:
                has_keyword = True
                break
        if not has_keyword:
            # 还需确认是在合同章节范围内
            section_title_lower = title.lower()
            contract_keywords = ["合同", "协议", "条款", "契约"]
            if any(ck in section_title_lower for ck in contract_keywords):
                pass  # 在合同章节中，但无关键词
            else:
                return issues  # 不在合同章节，跳过

            issues.append({
                "rule_id": rule["rule_id"],
                "category": rule["category"],
                "severity": rule["severity"],
                "title": rule["title"],
                "clause_ref": f"{title}",
                "evidence": f"合同条款中未发现'{rule['keywords'][0]}'相关条款",
                "suggestion": rule.get("suggestion", ""),
                "section_id": section.get("section_id", "")
            })
        return issues

    # 正向匹配
    matched = False
    evidence_lines = []

    # 关键词匹配
    for kw in rule.get("keywords", []):
        if kw in combined_text:
            matched = True
            break

    # 正则模式匹配
    for pattern in rule.get("patterns", []):
        if match_pattern(combined_text, pattern):
            matched = True
            # 提取匹配行作为证据
            for line in combined_text.split('\n'):
                if match_pattern(line, pattern):
                    evidence_lines.append(line.strip()[:200])

    if not matched:
        return issues

    # 排除模式检查
    if check_exclusion(combined_text, rule.get("exclusion_patterns", [])):
        return issues  # 匹配了排除模式，不算问题

    # 构造issue
    evidence = evidence_lines[0] if evidence_lines else f"在'{title}'章节中发现'{rule['title']}'相关内容"

    issues.append({
        "rule_id": rule["rule_id"],
        "category": rule["category"],
        "severity": rule["severity"],
        "title": rule["title"],
        "clause_ref": title,
        "evidence": evidence[:500],
        "suggestion": rule.get("suggestion", ""),
        "section_id": section.get("section_id", "")
    })

    return issues


def run_scan(tender_data, rules, scan_type, project_id):
    """执行完整扫描"""
    sections = tender_data.get("sections", [])
    all_issues = []

    for section in sections:
        for rule in rules:
            section_issues = scan_section(section, rule)
            all_issues.extend(section_issues)

    # 去重（同一section同一rule只保留一条）
    seen = set()
    unique_issues = []
    for issue in all_issues:
        key = f"{issue['rule_id']}_{issue['section_id']}"
        if key not in seen:
            seen.add(key)
            # 添加全局issue_id
            issue["issue_id"] = f"ISS-{scan_type[:3].upper()}-{len(unique_issues)+1:03d}"
            unique_issues.append(issue)

    return unique_issues


def main():
    parser = argparse.ArgumentParser(description='合规审查规则引擎')
    parser.add_argument('--tender_json', required=True, help='结构化招标JSON路径')
    parser.add_argument('--rules', required=True, help='YAML规则文件路径')
    parser.add_argument('--output', required=True, help='输出issue_list.json路径')
    parser.add_argument('--log', required=True, help='审计日志路径')
    parser.add_argument('--scan_type', required=True, help='扫描类型')
    parser.add_argument('--issue_list', default=None, help='已有issue清单路径（用于追加）')
    parser.add_argument('--project_id', default='', help='项目ID')
    args = parser.parse_args()

    # 加载数据
    tender_data = load_tender_json(args.tender_json)
    rules = load_rules(args.rules)
    project_id = args.project_id or tender_data.get("project_id", "unknown")

    # 加载已有issues
    existing = load_existing_issues(args.issue_list) if args.issue_list else {"project_id": project_id, "issues": [], "issue_count": 0}
    existing_issues = existing.get("issues", [])

    # 执行扫描
    start_time = datetime.now()
    new_issues = run_scan(tender_data, rules, args.scan_type, project_id)
    end_time = datetime.now()

    # 合并issues
    all_issues = existing_issues + new_issues

    result = {
        "project_id": project_id,
        "scan_type": args.scan_type,
        "issue_count": len(all_issues),
        "issues": all_issues
    }

    # 输出
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 审计日志
    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "scan_type": args.scan_type,
        "project_id": project_id,
        "rules_loaded": len(rules),
        "new_issues_found": len(new_issues),
        "total_issues": len(all_issues),
        "duration_seconds": (end_time - start_time).total_seconds()
    }
    with open(args.log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    print(f"扫描完成: {args.scan_type}")
    print(f"新增问题: {len(new_issues)} 条")
    print(f"累计问题: {len(all_issues)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
