#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仲裁费用估算工具
功能: 基于ICC/DIAC/SIAC等仲裁机构规则，估算仲裁总费用
输入: 争议金额、仲裁机构、案件复杂度、证人数量等
输出: 详细费用估算报告（仲裁费、律师费、专家费、其他费用）

版本: v1.0.0 (2026-06-29)
理论依据: 
- ICC Arbitration Rules (2021)
- DIAC Rules (2022)
- SIAC Rules (2016)
"""

import sys
import json
import argparse
from datetime import datetime

# 设置UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)


def estimate_arbitration_cost(input_data):
    """
    估算仲裁费用
    
    Args:
        input_data: 输入数据字典，包含：
            - dispute_amount: 争议金额（美元）
            - arbitration_institution: 仲裁机构（ICC/DIAC/SIAC/LCIA）
            - case_complexity: 案件复杂度（low/medium/high）
            - witness_count: 证人数量
            - expert_count: 专家证人数量
            - hearing_days: 听证天数
            - language: 仲裁语言（English/Chinese/Bilingual）
    
    Returns:
        dict: 费用估算结果
    """
    
    dispute_amount = input_data.get('dispute_amount', 0)
    institution = input_data.get('arbitration_institution', 'ICC')
    complexity = input_data.get('case_complexity', 'medium')
    witness_count = input_data.get('witness_count', 3)
    expert_count = input_data.get('expert_count', 2)
    hearing_days = input_data.get('hearing_days', 5)
    language = input_data.get('language', 'English')
    
    # 初始化费用估算
    cost_estimate = {
        'arbitration_fees': 0,      # 仲裁费（机构管理费 + 仲裁员费）
        'legal_fees': 0,             # 律师费
        'expert_fees': 0,            # 专家费
        'witness_fees': 0,           # 证人费
        'translation_fees': 0,       # 翻译费（如适用）
        'hearing_fees': 0,           # 听证费用（场地、设备、转录）
        'other_fees': 0,             # 其他费用
        'total': 0                   # 总费用
    }
    
    # 1. 仲裁费（机构管理费 + 仲裁员费）
    cost_estimate['arbitration_fees'] = calculate_arbitration_fees(dispute_amount, institution)
    
    # 2. 律师费（基于争议金额和复杂度）
    cost_estimate['legal_fees'] = calculate_legal_fees(dispute_amount, complexity, institution)
    
    # 3. 专家费（基于专家数量和听证天数）
    cost_estimate['expert_fees'] = calculate_expert_fees(expert_count, hearing_days, complexity)
    
    # 4. 证人费（基于证人数量和听证天数）
    cost_estimate['witness_fees'] = calculate_witness_fees(witness_count, hearing_days)
    
    # 5. 翻译费（如适用）
    if language == 'Bilingual':
        cost_estimate['translation_fees'] = calculate_translation_fees(dispute_amount, hearing_days)
    
    # 6. 听证费用
    cost_estimate['hearing_fees'] = calculate_hearing_fees(hearing_days, complexity)
    
    # 7. 其他费用
    cost_estimate['other_fees'] = calculate_other_fees(dispute_amount, complexity)
    
    # 计算总费用
    cost_estimate['total'] = sum([
        cost_estimate['arbitration_fees'],
        cost_estimate['legal_fees'],
        cost_estimate['expert_fees'],
        cost_estimate['witness_fees'],
        cost_estimate['translation_fees'],
        cost_estimate['hearing_fees'],
        cost_estimate['other_fees']
    ])
    
    return cost_estimate


def calculate_arbitration_fees(dispute_amount, institution):
    """
    计算仲裁费（机构管理费 + 仲裁员费）
    
    基于各仲裁机构的最新费用表（2023-2026）
    """
    
    if institution == 'ICC':
        # ICC仲裁费（2021规则）
        # 包括：管理费（ICC administrative expenses）+ 仲裁员费（arbitrators' fees）
        
        # 管理费（简化计算）
        if dispute_amount <= 100000:
            admin_fees = dispute_amount * 0.05
        elif dispute_amount <= 1000000:
            admin_fees = 5000 + (dispute_amount - 100000) * 0.03
        elif dispute_amount <= 10000000:
            admin_fees = 32000 + (dispute_amount - 1000000) * 0.015
        else:
            admin_fees = 167000 + (dispute_amount - 10000000) * 0.008
        
        # 仲裁员费（简化计算，假设3名仲裁员）
        if dispute_amount <= 100000:
            arbitrator_fees = dispute_amount * 0.08
        elif dispute_amount <= 1000000:
            arbitrator_fees = 8000 + (dispute_amount - 100000) * 0.05
        elif dispute_amount <= 10000000:
            arbitrator_fees = 53000 + (dispute_amount - 1000000) * 0.025
        else:
            arbitrator_fees = 278000 + (dispute_amount - 10000000) * 0.012
        
        return admin_fees + arbitrator_fees
    
    elif institution == 'DIAC':
        # DIAC仲裁费（2022规则）
        # 通常比ICC低20-30%
        icc_fees = calculate_arbitration_fees(dispute_amount, 'ICC')
        return icc_fees * 0.75
    
    elif institution == 'SIAC':
        # SIAC仲裁费（2016规则）
        # 通常比ICC低10-20%
        icc_fees = calculate_arbitration_fees(dispute_amount, 'ICC')
        return icc_fees * 0.85
    
    elif institution == 'LCIA':
        # LCIA仲裁费
        # 通常比ICC高5-10%
        icc_fees = calculate_arbitration_fees(dispute_amount, 'ICC')
        return icc_fees * 1.05
    
    else:
        # 默认ICC
        return calculate_arbitration_fees(dispute_amount, 'ICC')


def calculate_legal_fees(dispute_amount, complexity, institution):
    """
    计算律师费
    
    基于市场费率（2023-2026）：
    - 初级律师：$300-500/小时
    - 中级律师：$500-800/小时
    - 高级律师：$800-1500/小时
    - 合伙人：$1500-3000/小时
    """
    
    # 估计律师工作时间（小时）
    if complexity == 'low':
        hours = dispute_amount / 100000 * 50  # 简单案件
    elif complexity == 'medium':
        hours = dispute_amount / 100000 * 100  # 中等复杂
    else:
        hours = dispute_amount / 100000 * 200  # 高度复杂
    
    # 平均小时费率（考虑团队组合）
    avg_hourly_rate = 800  # USD/hour
    
    # 计算律师费
    legal_fees = hours * avg_hourly_rate
    
    # 如果是双语仲裁，增加20%（翻译和沟通成本）
    if institution in ['DIAC', 'SIAC'] and dispute_amount > 5000000:
        legal_fees *= 1.2
    
    return legal_fees


def calculate_expert_fees(expert_count, hearing_days, complexity):
    """
    计算专家费
    
    基于市场费率（2023-2026）：
    - 进度计划专家：$300-500/小时
    - quantum专家：$400-600/小时
    - 技术专家：$500-800/小时
    """
    
    # 每个专家估计工作时间（小时）
    if complexity == 'low':
        hours_per_expert = 100
    elif complexity == 'medium':
        hours_per_expert = 200
    else:
        hours_per_expert = 400
    
    # 平均小时费率
    avg_hourly_rate = 450  # USD/hour
    
    # 计算专家费
    expert_fees = expert_count * hours_per_expert * avg_hourly_rate
    
    return expert_fees


def calculate_witness_fees(witness_count, hearing_days):
    """
    计算证人费
    
    包括：
    - 证人准备（律师时间）
    - 听证出席（证人时间）
    - 差旅费（如适用）
    """
    
    # 每个证人准备时间（小时）
    preparation_hours = 20
    
    # 每个证人听证出席时间（小时）
    hearing_hours = hearing_days * 8
    
    # 平均证人费率（假设证人为公司员工）
    witness_rate = 150  # USD/hour
    
    # 律师准备证人时间（小时）
    lawyer_preparation_hours = witness_count * 10
    lawyer_rate = 800  # USD/hour
    
    # 计算证人费
    witness_fees = (
        witness_count * (preparation_hours + hearing_hours) * witness_rate +
        lawyer_preparation_hours * lawyer_rate
    )
    
    return witness_fees


def calculate_translation_fees(dispute_amount, hearing_days):
    """
    计算翻译费
    
    包括：
    - 文件翻译（USD 0.10-0.15/词汇）
    - 听证翻译（USD 500-800/天）
    """
    
    # 估计文件词汇量
    word_count = dispute_amount / 1000 * 1000  # 简化计算
    
    # 翻译费率
    translation_rate = 0.12  # USD/词
    
    # 文件翻译费
    document_translation = word_count * translation_rate
    
    # 听证翻译费（假设需要2名翻译）
    hearing_translation = hearing_days * 2 * 600  # USD/day
    
    return document_translation + hearing_translation


def calculate_hearing_fees(hearing_days, complexity):
    """
    计算听证费用
    
    包括：
    - 听证场地租赁
    - 设备租赁（投影、录音、转录）
    - 午餐和茶歇
    """
    
    # 每天听证费用
    if complexity == 'low':
        daily_hearing_cost = 5000  # USD/day
    elif complexity == 'medium':
        daily_hearing_cost = 10000  # USD/day
    else:
        daily_hearing_cost = 20000  # USD/day
    
    return hearing_days * daily_hearing_cost


def calculate_other_fees(dispute_amount, complexity):
    """
    计算其他费用
    
    包括：
    - 差旅费（仲裁员、律师、专家、证人）
    - 文档管理（电子发现）
    - 银行手续费
    - 通讯费
    """
    
    # 简化计算：争议金额的1-2%
    if complexity == 'low':
        other_fees = dispute_amount * 0.01
    elif complexity == 'medium':
        other_fees = dispute_amount * 0.015
    else:
        other_fees = dispute_amount * 0.02
    
    return other_fees


def generate_cost_report(input_data, cost_estimate):
    """
    生成费用估算报告
    """
    
    report = []
    report.append("=" * 80)
    report.append("仲裁费用估算报告")
    report.append("=" * 80)
    report.append("")
    
    report.append("【输入信息】")
    report.append(f"  争议金额: ${input_data.get('dispute_amount', 0):,.2f}")
    report.append(f"  仲裁机构: {input_data.get('arbitration_institution', 'ICC')}")
    report.append(f"  案件复杂度: {input_data.get('case_complexity', 'medium')}")
    report.append(f"  证人数量: {input_data.get('witness_count', 3)}")
    report.append(f"  专家证人数量: {input_data.get('expert_count', 2)}")
    report.append(f"  听证天数: {input_data.get('hearing_days', 5)}")
    report.append(f"  仲裁语言: {input_data.get('language', 'English')}")
    report.append("")
    
    report.append("【费用估算】")
    report.append(f"  1. 仲裁费（机构+仲裁员）: ${cost_estimate['arbitration_fees']:,.2f}")
    report.append(f"  2. 律师费: ${cost_estimate['legal_fees']:,.2f}")
    report.append(f"  3. 专家费: ${cost_estimate['expert_fees']:,.2f}")
    report.append(f"  4. 证人费: ${cost_estimate['witness_fees']:,.2f}")
    report.append(f"  5. 翻译费: ${cost_estimate['translation_fees']:,.2f}")
    report.append(f"  6. 听证费用: ${cost_estimate['hearing_fees']:,.2f}")
    report.append(f"  7. 其他费用: ${cost_estimate['other_fees']:,.2f}")
    report.append("")
    
    report.append("【总计】")
    report.append(f"  总费用估算: ${cost_estimate['total']:,.2f}")
    report.append(f"  占争议金额比例: {cost_estimate['total']/input_data.get('dispute_amount', 1)*100:.1f}%")
    report.append("")
    
    report.append("【费用分配估算（如败诉）】")
    report.append("  根据ICC实践，通常'loser pays'原则")
    report.append("  但如果部分胜诉，可能按比例分配")
    report.append(f"  最大风险: ${cost_estimate['total']:,.2f}（如果全败）")
    report.append(f"  最小风险: ${cost_estimate['total']*0.3:,.2f}（如果部分胜诉）")
    report.append("")
    
    report.append("【费用节省建议】")
    if input_data.get('language') == 'Bilingual':
        report.append("  1. 考虑单方语言仲裁（节省翻译费）")
    if input_data.get('hearing_days', 5) > 5:
        report.append("  2. 尝试和解（减少听证天数）")
    if input_data.get('expert_count', 2) > 2:
        report.append("  3. 减少专家证人数量（只保留关键专家）")
    report.append("")
    
    report.append("=" * 80)
    report.append("报告生成完成")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """
    主函数
    """
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='仲裁费用估算工具 - ZFCC仲裁准备系列'
    )
    parser.add_argument('--input', type=str, help='输入JSON文件')
    parser.add_argument('--output', type=str, help='输出报告文件')
    parser.add_argument('--dispute_amount', type=float, help='争议金额（美元）')
    parser.add_argument('--institution', type=str, default='ICC', help='仲裁机构（ICC/DIAC/SIAC/LCIA）')
    parser.add_argument('--complexity', type=str, default='medium', help='案件复杂度（low/medium/high）')
    
    args = parser.parse_args()
    
    # 加载输入数据
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    else:
        # 使用命令行参数或默认值
        input_data = {
            'dispute_amount': args.dispute_amount or 10000000,
            'arbitration_institution': args.institution,
            'case_complexity': args.complexity,
            'witness_count': 3,
            'expert_count': 2,
            'hearing_days': 5,
            'language': 'English'
        }
    
    # 估算费用
    cost_estimate = estimate_arbitration_cost(input_data)
    
    # 生成报告
    report = generate_cost_report(input_data, cost_estimate)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        print(report)
    
    # 返回JSON结果（供其他脚本使用）
    result = {
        'input': input_data,
        'cost_estimate': cost_estimate
    }
    
    print("\nJSON结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
