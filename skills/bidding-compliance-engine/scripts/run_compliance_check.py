#!/usr/bin/env python3
"""
招标文件合规审查系统 - 端到端入口脚本
一键执行全流程：文本提取 → 结构化解析 → 规则扫描 → 报告生成
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def run_cmd(cmd, step_name):
    """执行命令并打印进度"""
    print(f"\n{'='*60}")
    print(f"▶ 步骤: {step_name}")
    print(f"  命令: {cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"  [STDERR] {result.stderr[:500]}")
    if result.returncode != 0:
        print(f"  ❌ 步骤失败: {step_name}")
        return False
    print(f"  ✅ 步骤完成: {step_name}")
    return True


def main():
    parser = argparse.ArgumentParser(description='招标文件合规审查 - 端到端执行')
    parser.add_argument('--file_path', required=True, help='招标文件路径')
    parser.add_argument('--project_id', required=True, help='项目ID')
    parser.add_argument('--output_root', default='./output', help='输出根目录')
    parser.add_argument('--enable_ocr', default='true', help='是否启用OCR')
    args = parser.parse_args()

    # 项目目录结构
    project_dir = os.path.join(args.output_root, args.project_id)
    artifacts_dir = os.path.join(project_dir, "artifacts")
    audit_dir = os.path.join(project_dir, "audit")
    output_dir = os.path.join(project_dir, "output")

    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(audit_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Skill根目录（本脚本所在目录的上级）
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(skill_root, "scripts")
    rules_dir = os.path.join(skill_root, "references", "rules")
    assets_dir = os.path.join(skill_root, "assets")

    print(f"🚀 招标文件合规审查系统 v2.0")
    print(f"   项目ID: {args.project_id}")
    print(f"   文件路径: {args.file_path}")
    print(f"   输出目录: {project_dir}")
    print(f"   开始时间: {datetime.now().isoformat()}")

    # 扫描步骤定义（按审查表顺序：公平竞争→合法合规性→合同→反垄断/专项）
    scan_steps = [
        # 第一部分：公平竞争审查
        ("fair_competition_rules.yml", "fair_competition", "公平竞争审查"),
        ("disqualify_rules.yml", "disqualify_check", "废标条款审查"),
        ("qualification_rules.yml", "qualification_check", "资格条件审查"),
        ("technical_rules.yml", "technical_spec_match", "技术参数合规"),
        # 第二部分：合法合规性审查
        ("bidding_procedure_rules.yml", "bidding_procedure", "招标程序与评标合规"),
        # 合同与程序合规
        ("contract_rules.yml", "contract_terms_risk", "合同条款风险"),
        ("contract_compliance_rules.yml", "contract_compliance", "合同与程序合规"),
        # 反垄断与专项
        ("antitrust_rules.yml", "antitrust_special", "反垄断与专项审查"),
    ]
    total_steps = 2 + len(scan_steps) + 1  # 文本提取+结构化解析 + 8步扫描 + 报告生成

    # Step 1: 文本提取
    if not run_cmd(
        f'python3 {scripts_dir}/extract_text.py '
        f'--file_path "{args.file_path}" '
        f'--project_id {args.project_id} '
        f'--enable_ocr {args.enable_ocr} '
        f'--output_dir {artifacts_dir}',
        f"1/{total_steps} 文本提取 (tender-intake)"
    ):
        return 1

    # Step 2: 结构化解析
    raw_text = os.path.join(artifacts_dir, "raw_text.txt")
    tender_json = os.path.join(artifacts_dir, "tender.json")

    if not run_cmd(
        f'python3 {scripts_dir}/parse_structure.py '
        f'--raw_text_path {raw_text} '
        f'--project_id {args.project_id} '
        f'--output_dir {artifacts_dir}',
        f"2/{total_steps} 结构化解析 (tender-structure-parse)"
    ):
        return 1

    # 初始化issue清单
    issue_list = os.path.join(artifacts_dir, "issue_list.json")
    with open(issue_list, 'w', encoding='utf-8') as f:
        json.dump({"project_id": args.project_id, "issues": [], "issue_count": 0}, f, ensure_ascii=False, indent=2)

    # Step 3-10: 八维合规扫描
    for i, (rules_file, scan_type, step_name) in enumerate(scan_steps, start=3):
        log_name = scan_type + ".log"
        if not run_cmd(
            f'python3 {scripts_dir}/run_rules_engine.py '
            f'--tender_json {tender_json} '
            f'--rules {rules_dir}/{rules_file} '
            f'--issue_list {issue_list} '
            f'--output {issue_list} '
            f'--log {audit_dir}/{log_name} '
            f'--scan_type {scan_type} '
            f'--project_id {args.project_id}',
            f"{i}/{total_steps} {step_name} ({scan_type})"
        ):
            return 1

    # Step 11: 报告生成
    if not run_cmd(
        f'python3 {scripts_dir}/render_report.py '
        f'--project_id {args.project_id} '
        f'--tender_json {tender_json} '
        f'--issue_list {issue_list} '
        f'--template {assets_dir}/compliance_report.md '
        f'--output {output_dir}/compliance_report.md',
        f"{total_steps}/{total_steps} 报告生成 (report-generator)"
    ):
        return 1

    # 读取最终结果
    meta_path = f"{output_dir}/compliance_report_meta.json"
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print(f"\n{'='*60}")
        print(f"🎉 审查完成！")
        print(f"   审查结论: {meta.get('conclusion', 'unknown')}")
        print(f"   问题总数: {meta.get('summary', {}).get('total_issues', 0)}")
        print(f"   高风险: {meta.get('summary', {}).get('high_count', 0)}")
        print(f"   中风险: {meta.get('summary', {}).get('medium_count', 0)}")
        print(f"   低风险: {meta.get('summary', {}).get('low_count', 0)}")
        print(f"   报告路径: {meta.get('report_path', '')}")
        print(f"   结束时间: {datetime.now().isoformat()}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
