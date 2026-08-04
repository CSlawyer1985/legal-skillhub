#!/usr/bin/env python3
"""
输入材料完整性校验脚本
功能：检查APP合规检查所需的输入材料是否齐备
输出：缺失材料清单 + 完整度评分

用法：
    python material_validator.py --materials-dir /path/to/materials/
    python material_validator.py --materials-dir /path/to/materials/ --output validation_report.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 必需材料定义
REQUIRED_MATERIALS = [
    {
        "id": "apk",
        "name": "APP安装包（APK）",
        "extensions": [".apk", ".ipa"],
        "description": "最新正式发布版本的APK安装包（未加固）",
        "critical": True,
    },
    {
        "id": "privacy_policy",
        "name": "最新版隐私政策",
        "extensions": [".md", ".txt", ".docx", ".doc", ".pdf", ".html"],
        "description": "APP当前线上使用的最新版隐私政策完整文本",
        "critical": True,
    },
    {
        "id": "user_agreement",
        "name": "用户协议/服务协议",
        "extensions": [".md", ".txt", ".docx", ".doc", ".pdf", ".html"],
        "description": "APP当前线上使用的最新版用户协议",
        "critical": True,
    },
    {
        "id": "sdk_list",
        "name": "SDK清单",
        "extensions": [".xlsx", ".xls", ".csv", ".md"],
        "description": "含SDK名称、公司、功能、收集信息、目的、场景的清单",
        "critical": True,
    },
    {
        "id": "permission_list",
        "name": "权限使用清单",
        "extensions": [".xlsx", ".xls", ".csv", ".md"],
        "description": "含权限名称、使用场景、目的的清单",
        "critical": True,
    },
    {
        "id": "business_functions",
        "name": "业务功能清单",
        "extensions": [".xlsx", ".xls", ".csv", ".md", ".docx", ".doc"],
        "description": "基本功能与附加功能划分清单",
        "critical": True,
    },
    {
        "id": "collected_info_list",
        "name": "已收集个人信息清单（双清单之一）",
        "extensions": [".xlsx", ".xls", ".csv", ".md"],
        "description": "已收集个人信息清单（信息种类、字段、目的、场景）",
        "critical": True,
    },
    {
        "id": "shared_info_list",
        "name": "与第三方共享个人信息清单（双清单之一）",
        "extensions": [".xlsx", ".xls", ".csv", ".md"],
        "description": "与第三方共享的个人信息清单",
        "critical": True,
    },
]

# 可选材料定义
OPTIONAL_MATERIALS = [
    {"id": "personalized_recommendation", "name": "个性化推荐/算法推送设置说明"},
    {"id": "account_cancellation", "name": "账号注销流程说明"},
    {"id": "complaint_channels", "name": "投诉举报渠道说明"},
    {"id": "elderly_adaptation", "name": "适老化改造说明"},
    {"id": "child_protection", "name": "儿童个人信息保护规则"},
    {"id": "data_export", "name": "数据出境情况说明"},
    {"id": "pia_report", "name": "个人信息保护影响评估报告/PIA报告"},
    {"id": "security_assessment", "name": "安全评估报告/等保证明"},
    {"id": "auto_renewal", "name": "自动续费/会员订阅机制说明"},
]

# 文件名关键词匹配（用于自动识别材料类型）
FILE_KEYWORDS = {
    "apk": ["app", "apk", "application", "release"],
    "privacy_policy": ["隐私政策", "隐私权政策", "个人信息保护政策", "privacy", "policy", "隐私"],
    "user_agreement": ["用户协议", "服务协议", "user_agreement", "terms", "服务条款"],
    "sdk_list": ["sdk", "SDK", "第三方", "sdk清单", "sdk列表"],
    "permission_list": ["权限", "permission", "权限清单", "权限列表"],
    "business_functions": ["业务功能", "功能清单", "功能列表", "business", "function"],
    "collected_info_list": ["已收集", "收集清单", "个人信息清单", "collected"],
    "shared_info_list": ["共享", "第三方共享", "shared", "共享清单"],
    "personalized_recommendation": ["个性化", "算法", "推荐", "推送", "recommendation"],
    "account_cancellation": ["注销", "cancellation", "账号注销"],
    "complaint_channels": ["投诉", "举报", "complaint", "客服"],
    "elderly_adaptation": ["适老", "无障碍", "elderly", "关怀"],
    "child_protection": ["儿童", "未成年", "child", "minor"],
    "data_export": ["出境", "跨境", "export", "cross_border"],
    "pia_report": ["pia", "影响评估", "impact_assessment", "安全评估"],
    "security_assessment": ["等保", "安全评估", "security", "assessment"],
    "auto_renewal": ["续费", "会员", "订阅", "renewal", "subscription"],
}


def scan_materials(materials_dir):
    """扫描材料目录，识别已提供的材料"""
    found_materials = {}
    if not os.path.exists(materials_dir):
        return found_materials

    all_files = []
    for root, dirs, files in os.walk(materials_dir):
        for f in files:
            if not f.startswith(".") and not f.startswith("_"):
                all_files.append(os.path.join(root, f))

    # 对每个文件尝试匹配材料类型
    for file_path in all_files:
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_path)[1].lower()

        for mat_id, keywords in FILE_KEYWORDS.items():
            if mat_id in found_materials:
                continue
            for kw in keywords:
                if kw.lower() in file_name:
                    found_materials[mat_id] = file_path
                    break

    return found_materials


def validate_materials(materials_dir):
    """校验材料完整性"""
    found = scan_materials(materials_dir)

    result = {
        "materials_dir": materials_dir,
        "found_materials": found,
        "missing_required": [],
        "missing_optional": [],
        "provided_optional": [],
        "completeness_score": 0,
        "total_required": len(REQUIRED_MATERIALS),
        "total_found_required": 0,
    }

    # 检查必需材料
    for mat in REQUIRED_MATERIALS:
        if mat["id"] in found:
            result["total_found_required"] += 1
        else:
            result["missing_required"].append({
                "id": mat["id"],
                "name": mat["name"],
                "description": mat["description"],
                "expected_extensions": mat["extensions"],
            })

    # 检查可选材料
    for mat in OPTIONAL_MATERIALS:
        if mat["id"] in found:
            result["provided_optional"].append(mat["name"])
        else:
            result["missing_optional"].append(mat["name"])

    # 计算完整度评分
    required_score = (result["total_found_required"] / result["total_required"]) * 80
    optional_score = (len(result["provided_optional"]) / len(OPTIONAL_MATERIALS)) * 20
    result["completeness_score"] = round(required_score + optional_score, 1)

    return result


def print_report(result):
    """打印校验报告"""
    print("\n" + "=" * 60)
    print("📋 输入材料完整性校验报告")
    print("=" * 60)
    print(f"材料目录: {result['materials_dir']}")
    print(f"完整度评分: {result['completeness_score']}/100")
    print(f"必需材料: {result['total_found_required']}/{result['total_required']} 已提供")

    print("\n✅ 已提供的必需材料:")
    for mat_id, path in result["found_materials"].items():
        mat_name = next((m["name"] for m in REQUIRED_MATERIALS if m["id"] == mat_id), mat_id)
        print(f"  ✅ {mat_name}")
        print(f"     → {path}")

    if result["missing_required"]:
        print("\n❌ 缺失的必需材料（须补充）:")
        for mat in result["missing_required"]:
            print(f"  ❌ {mat['name']}")
            print(f"     说明: {mat['description']}")
            print(f"     格式: {', '.join(mat['expected_extensions'])}")

    if result["missing_optional"]:
        print("\n⚠️ 未提供的可选材料（影响审查完整度）:")
        for name in result["missing_optional"]:
            print(f"  ⚠️ {name}")

    print("\n" + "=" * 60)

    if result["missing_required"]:
        print("\n📌 下一步操作:")
        print("  请将上述缺失的必需材料补充至材料目录，")
        print("  然后重新运行校验。")
        print("  可选材料缺失不影响审查启动，但会降低审查完整度。")
    else:
        print("\n🎉 所有必需材料已齐备，可以启动合规审查！")


def main():
    parser = argparse.ArgumentParser(description="输入材料完整性校验 - APP合规检查")
    parser.add_argument("--materials-dir", required=True, help="材料目录路径")
    parser.add_argument("--output", "-o", help="输出JSON报告文件路径")

    args = parser.parse_args()

    result = validate_materials(args.materials_dir)
    print_report(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 详细报告已保存到: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
