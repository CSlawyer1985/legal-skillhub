#!/usr/bin/env python3
"""
CCPA选择退出机制检查工具
检查企业的选择退出机制是否符合CCPA要求
"""

import json
import argparse
import sys
from typing import Dict, List, Any, Optional


def check_opt_out_mechanism(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查选择退出机制
    
    Args:
        config: 配置信息
        
    Returns:
        检查结果
    """
    results = {
        "do_not_sell_link": {
            "description": "请勿销售链接检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        },
        "global_signal_support": {
            "description": "全局信号支持检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        },
        "agent_authorization": {
            "description": "代理授权检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        },
        "compliance_monitoring": {
            "description": "合规监控检查",
            "status": "pending",
            "checks": [],
            "recommendations": []
        }
    }
    
    # 检查"请勿销售"链接
    if config.get("has_do_not_sell_link", False):
        results["do_not_sell_link"]["checks"].append("✅ 有'请勿销售我的个人信息'链接")
        if config.get("link_location", "") == "homepage":
            results["do_not_sell_link"]["checks"].append("✅ 链接位于网站首页")
        else:
            results["do_not_sell_link"]["checks"].append("❌ 链接位置不正确")
            results["do_not_sell_link"]["recommendations"].append("将链接移动到网站首页")
    else:
        results["do_not_sell_link"]["checks"].append("❌ 缺少'请勿销售'链接")
        results["do_not_sell_link"]["recommendations"].append("在网站首页添加'请勿销售我的个人信息'链接")
    
    # 检查全局信号支持
    if config.get("supports_global_opt_out", False):
        results["global_signal_support"]["checks"].append("✅ 支持全局选择退出信号")
        if config.get("respects_global_signal", False):
            results["global_signal_support"]["checks"].append("✅ 尊重全局选择退出信号")
        else:
            results["global_signal_support"]["checks"].append("❌ 未充分尊重全局信号")
            results["global_signal_support"]["recommendations"].append("确保全局选择退出信号被充分尊重")
    else:
        results["global_signal_support"]["checks"].append("❌ 不支持全局选择退出")
        results["global_signal_support"]["recommendations"].append("实现全局选择退出信号支持")
    
    # 检查代理授权
    if config.get("accepts_authorized_agents", False):
        results["agent_authorization"]["checks"].append("✅ 接受授权代理请求")
        if config.get("verification_mechanism", "simple") in ["secure", "advanced"]:
            results["agent_authorization"]["checks"].append("✅ 有安全的验证机制")
        else:
            results["authorization"]["checks"].append("❌ 验证机制不足")
            results["agent_authorization"]["recommendations"].append("增强代理授权验证机制")
    else:
        results["agent_authorization"]["checks"].append("❌ 未接受授权代理请求")
        results["agent_authorization"]["recommendations"].append("建立授权代理请求处理流程")
    
    # 检查合规监控
    compliance_monitoring = config.get("compliance_monitoring", {})
    if compliance_monitoring.get("has_compliance_monitoring", False):
        results["compliance_monitoring"]["checks"].append("✅ 有合规监控机制")
        
        if compliance_monitoring.get("monitoring_frequency", "monthly") in ["weekly", "daily"]:
            results["compliance_monitoring"]["checks"].append("✅ 监控频率合理")
        else:
            results["compliance_monitoring"]["checks"].append("❌ 监控频率不足")
            results["compliance_monitoring"]["recommendations"].append("增加合规监控频率")
        
        if compliance_monitoring.get("has_reporting_system", False):
            results["compliance_monitoring"]["checks"].append("✅ 有合规报告系统")
        else:
            results["compliance_monitoring"]["checks"].append("❌ 缺少合规报告系统")
            results["compliance_monitoring"]["recommendations"].append("建立合规报告系统")
    else:
        results["compliance_monitoring"]["checks"].append("❌ 缺乏合规监控机制")
        results["compliance_monitoring"]["recommendations"].append("建立全面的合规监控机制")
    
    # 更新状态
    for test in results.values():
        has_errors = any("❌" in check for check in test["checks"])
        test["status"] = "passed" if not has_errors else "failed"
    
    return results


def generate_check_report(results: Dict[str, Any], output_format: str = "json") -> str:
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
        report_lines = ["CCPA选择退出机制检查报告", "=" * 40]
        
        for test_name, test_data in results.items():
            report_lines.append(f"\n{test_data['description']}: {test_data['status']}")
            report_lines.append("-" * 30)
            
            for check in test_data["checks"]:
                report_lines.append(f"  {check}")
            
            if test_data["recommendations"]:
                report_lines.append("\n  建议:")
                for rec in test_data["recommendations"]:
                    report_lines.append(f"  • {rec}")
        
        return "\n".join(report_lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CCPA选择退出机制检查工具")
    parser.add_argument("--type", choices=["sale", "sharing", "marketing", "all"],
                       default="all", help="检查的选择退出类型")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    
    args = parser.parse_args()
    
    # 默认配置
    default_config = {
        "company_name": "示例公司",
        "has_do_not_sell_link": True,
        "link_location": "homepage",
        "supports_global_opt_out": True,
        "respects_global_signal": True,
        "accepts_authorized_agents": True,
        "verification_mechanism": "secure",
        "compliance_monitoring": {
            "has_compliance_monitoring": True,
            "monitoring_frequency": "weekly",
            "has_reporting_system": True
        }
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
    print(f"🔍 检查CCPA选择退出机制...")
    print(f"   公司: {config.get('company_name', '未指定')}")
    
    results = check_opt_out_mechanism(config)
    
    # 过滤结果（如果指定了特定类型）
    if args.type != "all":
        filtered_results = {}
        type_mapping = {
            "sale": "do_not_sell_link",
            "sharing": "sharing_restrictions",
            "marketing": "marketing_opt_out"
        }
        if args.type in type_mapping:
            key = type_mapping[args.type]
            filtered_results[key] = results[key]
        results = filtered_results
    
    # 生成报告
    report = generate_check_report(results, args.format)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到: {args.output}")
    else:
        print(report)
    
    # 总结
    passed = sum(1 for test in results.values() if test["status"] == "passed")
    total = len(results)
    print(f"\n📊 总结: {passed}/{total} 项检查通过")


if __name__ == "__main__":
    main()