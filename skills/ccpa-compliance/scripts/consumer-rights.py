#!/usr/bin/env python3
"""
CCPA消费者权利检查工具
检查企业是否充分实现CCPA消费者权利
"""

import json
import argparse
import sys
from typing import Dict, List, Any, Optional


def check_consumer_rights_implementation(rights_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查消费者权利实现情况
    
    Args:
        rights_config: 权利配置信息
        
    Returns:
        检查结果
    """
    results = {
        "right_to_know": {
            "description": "知情权检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        },
        "right_to_delete": {
            "description": "删除权检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        },
        "right_to_opt_out": {
            "description": "选择退出权检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        },
        "right_to_non_discrimination": {
            "description": "不受歧视权检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        }
    }
    
    # 检查知情权
    if rights_config.get("has_privacy_notice", False):
        results["right_to_know"]["checks"].append("✅ 有隐私通知")
    else:
        results["right_to_know"]["checks"].append("❌ 缺少隐私通知")
        results["right_to_know"]["recommendations"].append("创建符合CCPA要求的隐私通知")
    
    if rights_config.get("discloses_data_categories", False):
        results["right_to_know"]["checks"].append("✅ 披露数据类别")
    else:
        results["right_to_know"]["checks"].append("❌ 未充分披露数据类别")
        results["right_to_know"]["recommendations"].append("明确披露收集的个人信息类别")
    
    # 检查删除权
    if rights_config.get("has_deletion_request_mechanism", False):
        results["right_to_delete"]["checks"].append("✅ 有删除请求机制")
    else:
        results["right_to_delete"]["checks"].append("❌ 缺少删除请求机制")
        results["right_to_delete"]["recommendations"].append("建立删除请求响应机制")
    
    if rights_config.get("response_time_days", 0) <= 45:
        results["right_to_delete"]["checks"].append(f"✅ 响应时间 {rights_config.get('response_time_days', 0)} 天符合要求")
    else:
        results["right_to_delete"]["checks"].append(f"❌ 响应时间超过45天限制")
        results["right_to_delete"]["recommendations"].append("优化响应流程以符合45天要求")
    
    # 检查选择退出权
    if rights_config.get("has_do_not_sell_link", False):
        results["right_to_opt_out"]["checks"].append("✅ 有'请勿销售'链接")
    else:
        results["right_to_opt_out"]["checks"].append("❌ 缺少'请勿销售'链接")
        results["right_to_opt_out"]["recommendations"].append("在网站首页添加'请勿销售我的个人信息'链接")
    
    if rights_config.get("supports_global_opt_out", False):
        results["right_to_opt_out"]["checks"].append("✅ 支持全局选择退出")
    else:
        results["right_to_opt_out"]["checks"].append("❌ 不支持全局选择退出")
        results["right_to_opt_out"]["recommendations"].append("实现全局选择退出信号支持")
    
    # 检查不受歧视权
    if not rights_config.get("discriminates_for_exercising_rights", False):
        results["right_to_non_discrimination"]["checks"].append("✅ 未因行使权利而歧视")
    else:
        results["right_to_non_discrimination"]["checks"].append("❌ 存在歧视性做法")
        results["right_to_non_discrimination"]["recommendations"].append("停止因消费者行使权利而歧视")
    
    # 更新状态
    for right in results.values():
        has_errors = any("❌" in check for check in right["checks"])
        right["status"] = "passed" if not has_errors else "failed"
    
    return results


def generate_report(results: Dict[str, Any], output_format: str = "json") -> str:
    """
    生成检查报告
    
    Args:
        results: 检查结果
        output_format: 输出格式
        
    Returns:
        报告内容
    """
    if output_format == "json":
        return json.dumps(results, ensure_ascii=False, indent=2)
    else:
        # 文本格式报告
        report_lines = ["CCPA消费者权利检查报告", "=" * 40]
        
        for right_name, right_data in results.items():
            report_lines.append(f"\n{right_data['description']}: {right_data['status']}")
            report_lines.append("-" * 30)
            
            for check in right_data["checks"]:
                report_lines.append(f"  {check}")
            
            if right_data["recommendations"]:
                report_lines.append("\n  建议:")
                for rec in right_data["recommendations"]:
                    report_lines.append(f"  • {rec}")
        
        return "\n".join(report_lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CCPA消费者权利检查工具")
    parser.add_argument("--right", choices=["know", "delete", "opt-out", "non-discrimination", "all"],
                       default="all", help="检查的权利类型")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    
    args = parser.parse_args()
    
    # 默认配置
    default_config = {
        "company_name": "示例公司",
        "has_privacy_notice": True,
        "discloses_data_categories": True,
        "has_deletion_request_mechanism": True,
        "response_time_days": 30,
        "has_do_not_sell_link": True,
        "supports_global_opt_out": True,
        "discriminates_for_exercising_rights": False
    }
    
    # 加载配置（如果提供）
    config = default_config
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"错误: 无法加载配置文件 {args.config}: {e}")
            sys.exit(1)
    
    # 运行检查
    print(f"🔍 检查CCPA消费者权利实现...")
    print(f"   公司: {config.get('company_name', '未指定')}")
    
    results = check_consumer_rights_implementation(config)
    
    # 过滤结果（如果指定了特定权利）
    if args.right != "all":
        filtered_results = {}
        right_mapping = {
            "know": "right_to_know",
            "delete": "right_to_delete", 
            "opt-out": "right_to_opt_out",
            "non-discrimination": "right_to_non_discrimination"
        }
        if args.right in right_mapping:
            key = right_mapping[args.right]
            filtered_results[key] = results[key]
        results = filtered_results
    
    # 生成报告
    report = generate_report(results, args.format)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到: {args.output}")
    else:
        print(report)
    
    # 总结
    passed = sum(1 for r in results.values() if r["status"] == "passed")
    total = len(results)
    print(f"\n📊 总结: {passed}/{total} 项权利检查通过")


if __name__ == "__main__":
    main()