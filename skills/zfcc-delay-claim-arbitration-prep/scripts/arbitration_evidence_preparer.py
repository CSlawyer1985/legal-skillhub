#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仲裁证据准备脚本（功能完善版）
功能: 基于ICC 2019报告和ASCE 67-17生成完整的仲裁证据准备方案
输入: 争议信息、可用证据、仲裁规则
输出: 完整证据清单+呈现策略+交叉询问准备+时间规划
理论依据: ICC Construction Arbitration Report (2019) + ASCE 67-17
版本: v3.0.0 (功能完善版 - 2026-06-28更新)
"""

import sys
import json
import argparse
from datetime import datetime, timedelta

# 设置UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

def load_input(json_file):
    """加载JSON输入文件"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 尝试Windows路径格式
        if json_file.startswith('/'):
            windows_path = json_file.replace('/c/', 'C:/').replace('/', '/')
            with open(windows_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise

# ========== 争议类型数据库 ==========
DISPUTE_TYPE_DATABASE = {
    "delay": {
        "dispute_name": "工期延误争议",
        "description": "承包人申请工期延期，雇主拒绝",
        "specific_evidence": [
            "进度计划（原始版 vs. 更新版）",
            "延误分析报告（Window Analysis/TIA）",
            "关键路径分析",
            "同期记录（现场日记、会议记录）",
            "天气记录（如适用）",
            "变更指令（如适用）"
        ],
        "key_issues": [
            "延误事件是否构成EOT事由？",
            "延误是否影响了关键路径？",
            "承包人是否及时发出通知？",
            "是否存在并发延误？",
            "雇主是否也贡献了延误？"
        ],
        "evidence_strength_criteria": {
            "strong": "有关键路径分析 + 完整同期记录 + 及时通知",
            "medium": "有延误分析但同期记录不完整",
            "weak": "无延误分析或同期记录缺失"
        }
    },
    "concurrent_delay": {
        "dispute_name": "并发延误争议",
        "description": "承包人和雇主都有延误事件，责任分配争议",
        "specific_evidence": [
            "双方延误事件的时间线",
            "各延误事件对关键路径的影响分析",
            "同期记录（证明各延误事件的发生时间）",
            "合同规定（并发延误责任分配条款）",
            "适用法律（普通法/大陆法对并发延误的处理）"
        ],
        "key_issues": [
            "是否可以区分双方的责任？",
            "是否应按比例分配责任？",
            "适用法律对并发延误的规定？",
            "合同是否有明确条款？"
        ],
        "evidence_strength_criteria": {
            "strong": "有明确时间线 + 各延误事件影响分析 + 合同/法律支持",
            "medium": "有时间线但影响分析不完整",
            "weak": "无法区分双方责任"
        }
    },
    "disruption": {
        "dispute_name": "干扰争议",
        "description": "承包人声称效率降低，要求额外费用",
        "specific_evidence": [
            " productivity记录（计划vs.实际）",
            "measurable mile分析",
            "资源使用记录（人工、设备）",
            "现场管理记录",
            "变更指令（如适用）"
        ],
        "key_issues": [
            "是否有可测量的效率降低？",
            "效率降低是否由雇主风险事件造成？",
            "承包人是否保持了完整的productivity记录？",
            "是否可以使用measured mile方法？"
        ],
        "evidence_strength_criteria": {
            "strong": "有measured mile分析 + 完整productivity记录",
            "medium": "有productivity记录但measured mile不适用",
            "weak": "无productivity记录或效率降低无法证明"
        }
    }
}

# ========== 证据呈现策略生成器 ==========
def generate_presentation_strategy(dispute_type, evidence_strength):
    """生成证据呈现策略"""
    strategy = {
        "key_messages": [],
        "visualization_tips": [],
        "narrative_structure": ""
    }
    
    if dispute_type == "delay":
        strategy["key_messages"] = [
            "延误事件属于雇主风险（有权获得EOT）",
            "延误影响了关键路径（有权获得工期延期）",
            "承包人及时发出通知（程序合规）",
            "同期记录完整（证据可靠）"
        ]
        strategy["visualization_tips"] = [
            "使用甘特图显示关键路径影响",
            "使用时间线图显示通知时限",
            "使用柱状图显示各延误事件的影响天数",
            "使用现场照片显示延误事件的实际影响",
            "使用关键路径分析图（原始vs.实际）"
        ]
        strategy["narrative_structure"] = """
1. 引言: 项目背景+合同要求
2. 延误事件: 详细描述各延误事件
3. 通知合规性: 证明及时通知
4. 延误分析: 关键路径影响+责任分配
5. 证据可靠性: 同期记录完整性
6. 结论: EOT权利+费用补偿（如适用）
        """
    
    elif dispute_type == "concurrent_delay":
        strategy["key_messages"] = [
            "承包人延误事件的时间线和影响",
            "雇主延误事件的时间线和影响",
            "责任应公平分配（按比例）",
            "承包人已采取合理措施减轻延误"
        ]
        strategy["visualization_tips"] = [
            "使用时间线图显示双方延误事件",
            "使用堆叠柱状图显示责任分配",
            "使用关键路径分析图（分别显示双方影响）"
        ]
        strategy["narrative_structure"] = """
1. 引言: 并发延误的存在
2. 承包人延误: 时间线+影响
3. 雇主延误: 时间线+影响
4. 责任分配: 比例计算+公平原则
5. 结论: 承包人有权获得部分EOT
        """
    
    return strategy

# ========== 交叉询问问题生成器 ==========
def generate_cross_examination_questions(dispute_type, role):
    """生成交叉询问问题"""
    questions = {
        "generic": [
            "你如何证明该延误事件影响了关键路径？",
            "你的延误分析方法是什么？是否符合ASCE 67-17？",
            "你的同期记录是否完整？是否有缺失？",
            "你是否在合同时限内发出了通知？",
            "你是否考虑了所有相关因素？"
        ],
        "technical": []
    }
    
    if dispute_type == "delay":
        if role == "claimant":  # 承包人（申请人）
            questions["technical"].append("你的关键路径分析是否考虑了所有活动？")
            questions["technical"].append("你如何解释同期记录中的间隙？")
        elif role == "respondent":  # 雇主（被申请人）
            questions["technical"].append("承包人是否在合理时间内发出通知？")
            questions["technical"].append("承包人的延误分析是否有错误？")
    
    return questions

# ========== 核心功能函数 ==========
def prepare_arbitration_evidence(dispute_info, available_evidence, arbitration_rules):
    """
    准备仲裁证据
    
    参数:
        dispute_info: 争议信息字典
        available_evidence: 可用证据字典
        arbitration_rules: 仲裁规则字典
    
    返回:
        evidence_package: 完整证据准备方案
    """
    dispute_type = dispute_info.get('dispute_type', 'delay')
    
    if dispute_type not in DISPUTE_TYPE_DATABASE:
        return {"error": f"不支持的争议类型: {dispute_type}"}
    
    dispute_data = DISPUTE_TYPE_DATABASE[dispute_type]
    
    # 评估证据强度
    evidence_strength = "medium"  # 默认
    if available_evidence.get('contemporaneous_records') and available_evidence.get('schedule_files'):
        evidence_strength = "strong"
    elif not available_evidence.get('contemporaneous_records'):
        evidence_strength = "weak"
    
    # 生成完整证据包
    evidence_package = {
        "dispute_info": dispute_info,
        "dispute_type": dispute_type,
        "dispute_description": dispute_data["description"],
        "evidence_checklist": {
            "general": [
                "合同文件（完整版）",
                "通信记录（双方往来函件）",
                "会议记录（项目会议、争议会议）",
                "现场日记（每日记录）",
                "进度计划（原始版+所有更新版）",
                "延误分析报告",
                "专家报告（如适用）"
            ],
            "specific": dispute_data["specific_evidence"]
        },
        "evidence_strength": {
            "rating": evidence_strength,
            "score": 90 if evidence_strength == "strong" else 60 if evidence_strength == "medium" else 30,
            "criteria": dispute_data["evidence_strength_criteria"]
        },
        "presentation_strategy": generate_presentation_strategy(dispute_type, evidence_strength),
        "cross_examination": {
            "generic_questions": generate_cross_examination_questions(dispute_type, "generic"),
            "technical_questions": generate_cross_examination_questions(dispute_type, dispute_info.get('party_role', 'claimant'))
        },
        "timeline_planning": {
            "pre_arbitration": "收集证据+准备延误分析（建议3-6个月）",
            "arbitration_commencement": "提交仲裁通知（按仲裁规则）",
            "evidence_submission": "提交证据（按程序令）",
            "hearing": "听证会（准备证人证言+专家证言）",
            "deadlines": [
                "仲裁通知后30天内: 指定仲裁员",
                "程序令后60天内: 提交申请书",
                "申请书后60天内: 提交答辩书",
                "听证会前30天: 提交证人证言"
            ]
        },
        "icc_best_practices": [
            "避免常见错误1: 证据不足（确保同期记录完整）",
            "避免常见错误2: 分析方法不当（使用ASCE 67-17认可的方法）",
            "避免常见错误3: 未及时通知（检查合同通知时限）",
            "避免常见错误4: 专家证人不合格（选择有经验的专家）",
            "避免常见错误5: 证据呈现不清晰（使用可视化工具）"
        ]
    }
    
    return evidence_package

def main():
    parser = argparse.ArgumentParser(
        description='仲裁证据准备脚本 - ZFCC工期索赔.仲裁准备(ICC+ASCE)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python arbitration_evidence_preparer.py --dispute "工期延期争议" --type delay --output evidence.json
  python arbitration_evidence_preparer.py --input input.json --output evidence.json

输入JSON格式 (input.json):
{
  "dispute_info": {
    "description": "承包人申请工期延期120天，雇主拒绝",
    "dispute_type": "delay",
    "claim_amount": "USD 2,000,000",
    "parties": {
      "claimant": "承包人",
      "respondent": "雇主"
    }
  },
  "available_evidence": {
    "contemporaneous_records": true,
    "schedule_files": true,
    "delay_analysis": false
  },
  "arbitration_rules": {
    "rules": "ICC Arbitration Rules 2021",
    "language": "English",
    "seat": "Singapore"
  }
}

支持争议类型:
  - delay: 工期延误
  - concurrent_delay: 并发延误
  - disruption: 干扰（效率降低）
  - acceleration: 赶工
  - general: 一般争议
        """
    )
    
    parser.add_argument('--input', help='输入JSON文件（包含争议信息、可用证据、仲裁规则）')
    parser.add_argument('--dispute', help='争议描述')
    parser.add_argument('--type', help='争议类型 (delay/concurrent_delay/disruption/etc.)')
    parser.add_argument('--output', help='输出JSON文件')
    
    args = parser.parse_args()
    
    # 确定输入
    if args.input:
        data = load_input(args.input)
        dispute_info = data.get('dispute_info', {})
        available_evidence = data.get('available_evidence', {})
        arbitration_rules = data.get('arbitration_rules', {})
    elif args.dispute and args.type:
        dispute_info = {"description": args.dispute, "dispute_type": args.type}
        available_evidence = {}
        arbitration_rules = {}
    else:
        parser.print_help()
        sys.exit(1)
    
    # 准备仲裁证据
    print(f"开始准备仲裁证据: {dispute_info.get('dispute_type', '未知')}")
    result = prepare_arbitration_evidence(dispute_info, available_evidence, arbitration_rules)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"结果已保存到: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("操作完成。")

if __name__ == '__main__':
    main()
