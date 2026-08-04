#!/usr/bin/env python3
"""
合规检查报告生成脚本
功能：汇总检查结果，生成Markdown格式的合规评审报告
输入：检查结果JSON文件
输出：Markdown格式合规评审报告

用法：
    python report_generator.py --input check_results.json --output report.md
    python report_generator.py --interactive  # 交互式输入检查结果
"""

import argparse
import json
import os
import sys
from datetime import datetime


def generate_report(app_info, check_results, apk_analysis=None):
    """生成合规评审报告Markdown"""

    now = datetime.now().strftime("%Y年%m月%d日")

    # 统计各模块合规状态
    module_stats = {}
    total_items = 0
    compliant_items = 0
    warning_items = 0
    non_compliant_items = 0

    for result in check_results:
        module = result.get("module", "未分类")
        status = result.get("status", "unknown")

        if module not in module_stats:
            module_stats[module] = {"total": 0, "compliant": 0, "warning": 0, "non_compliant": 0}

        module_stats[module]["total"] += 1
        total_items += 1

        if status == "compliant":
            module_stats[module]["compliant"] += 1
            compliant_items += 1
        elif status == "warning":
            module_stats[module]["warning"] += 1
            warning_items += 1
        elif status == "non_compliant":
            module_stats[module]["non_compliant"] += 1
            non_compliant_items += 1

    compliance_rate = round(compliant_items / total_items * 100, 1) if total_items > 0 else 0

    # 构建报告
    report = f"""# APP个人信息保护合规评审报告

**报告生成日期：** {now}

---

## 一、执行摘要

### APP基本信息

| 项目 | 内容 |
|------|------|
| APP名称 | {app_info.get('app_name', '未提供')} |
| 包名 | {app_info.get('package_name', '未提供')} |
| 版本号 | {app_info.get('version', '未提供')} |
| 平台 | {app_info.get('platform', 'Android')} |
| 审查日期 | {now} |
| 审查范围 | 个人信息保护合规（11大模块） |

### 总体合规情况

| 指标 | 数值 |
|------|------|
| 检查项总数 | {total_items} |
| ✅ 合规项 | {compliant_items} |
| ⚠️ 需关注项 | {warning_items} |
| ❌ 不合规项 | {non_compliant_items} |
| **合规率** | **{compliance_rate}%** |

### 重大风险项概述

"""

    # 列出高风险不合规项
    high_risk_items = [r for r in check_results if r.get("status") == "non_compliant" and r.get("risk_level") == "high"]
    if high_risk_items:
        report += "以下为高风险不合规项，须在上线前优先修复：\n\n"
        for i, item in enumerate(high_risk_items, 1):
            report += f"{i}. **{item.get('item_id', '')} {item.get('item_name', '')}**\n"
            report += f"   - 事实发现：{item.get('finding', '')}\n"
            report += f"   - 法规依据：{item.get('legal_basis', '')}\n\n"
    else:
        report += "未发现高风险不合规项。\n\n"

    # 模块合规总览表
    report += "## 二、合规总览表\n\n"
    report += "| 模块 | 检查项数 | ✅合规 | ⚠️需关注 | ❌不合规 | 状态 |\n"
    report += "|------|----------|--------|----------|----------|------|\n"

    module_names = {
        "M1": "隐私政策合规",
        "M2": "知情同意",
        "M3": "最小必要",
        "M4": "权限管理",
        "M5": "SDK与第三方",
        "M6": "敏感个人信息",
        "M7": "用户权利",
        "M8": "广告合规",
        "M9": "数据安全",
        "M10": "特殊场景",
        "M11": "分发平台责任",
    }

    for module_code in ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11"]:
        stats = module_stats.get(module_code, {"total": 0, "compliant": 0, "warning": 0, "non_compliant": 0})
        name = module_names.get(module_code, module_code)

        if stats["non_compliant"] > 0:
            status = "❌ 不合规"
        elif stats["warning"] > 0:
            status = "⚠️ 需关注"
        elif stats["total"] > 0:
            status = "✅ 合规"
        else:
            status = "— 未检查"

        report += f"| {module_code} {name} | {stats['total']} | {stats['compliant']} | {stats['warning']} | {stats['non_compliant']} | {status} |\n"

    # 逐项检查结果
    report += "\n## 三、逐项检查结果\n\n"

    current_module = ""
    for result in check_results:
        module = result.get("module", "")
        if module != current_module:
            current_module = module
            report += f"\n### {module} {module_names.get(module, '')}\n\n"

        item_id = result.get("item_id", "")
        item_name = result.get("item_name", "")
        status = result.get("status", "")
        risk = result.get("risk_level", "")

        status_emoji = {"compliant": "✅", "warning": "⚠️", "non_compliant": "❌"}.get(status, "❓")
        risk_label = {"high": "🔴高风险", "medium": "🟡中风险", "low": "🟢低风险"}.get(risk, "")

        report += f"#### {item_id} {item_name}\n\n"
        report += f"**状态：** {status_emoji} {status} | **风险等级：** {risk_label}\n\n"

        if result.get("check_content"):
            report += f"**检查内容：** {result['check_content']}\n\n"
        if result.get("finding"):
            report += f"**事实发现：** {result['finding']}\n\n"
        if result.get("legal_basis"):
            report += f"**法规依据：** {result['legal_basis']}\n\n"
        if result.get("recommendation"):
            report += f"**整改建议：** {result['recommendation']}\n\n"
        if result.get("method"):
            report += f"**审查方法：** {result['method']}\n\n"

        report += "---\n\n"

    # 一致性核验发现
    report += "## 四、一致性核验发现\n\n"
    report += "以下为文本声明与技术事实（APK技术取证）不一致的发现：\n\n"

    cross_findings = [r for r in check_results if r.get("method", "").startswith("[交叉]")]
    if cross_findings:
        report += "| 编号 | 检查项 | 发现 | 风险等级 |\n"
        report += "|------|--------|------|----------|\n"
        for i, f in enumerate(cross_findings, 1):
            if f.get("status") != "compliant":
                risk_label = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(f.get("risk_level", ""), "")
                report += f"| {i} | {f.get('item_id', '')} {f.get('item_name', '')} | {f.get('finding', '')} | {risk_label} |\n"
    else:
        report += "未发现文本材料与技术事实不一致的情况。\n"

    # APK分析摘要（如有）
    if apk_analysis:
        report += "\n## 五、APK静态分析摘要\n\n"
        report += f"**文件大小：** {apk_analysis.get('file_size', 0) / 1024 / 1024:.2f} MB\n\n"

        perms = apk_analysis.get("permissions", {})
        report += f"**声明权限总数：** {perms.get('total_count', 0)}\n"
        report += f"**敏感权限数：** {perms.get('sensitive_count', 0)}\n\n"

        if perms.get("sensitive_permissions"):
            report += "**敏感权限清单：**\n\n"
            for p in perms["sensitive_permissions"]:
                report += f"- {p['name']}（{p['description']}）\n"

        sdks = apk_analysis.get("sdks", {})
        report += f"\n**识别到的第三方SDK（{sdks.get('total_count', 0)}个）：**\n\n"
        for sdk in sdks.get("identified_sdks", []):
            report += f"- {sdk}\n"

        pp = apk_analysis.get("privacy_policy", {})
        if pp.get("found_links"):
            report += "\n**内嵌隐私政策链接：**\n\n"
            for link in pp["found_links"]:
                report += f"- {link}\n"

    # 整改优先级清单
    report += "\n## 六、整改优先级清单\n\n"

    priorities = {"P0": [], "P1": [], "P2": [], "P3": []}

    for r in check_results:
        if r.get("status") == "non_compliant":
            risk = r.get("risk_level", "medium")
            if risk == "high":
                priorities["P0"].append(r)
            else:
                priorities["P1"].append(r)
        elif r.get("status") == "warning":
            risk = r.get("risk_level", "low")
            if risk == "medium":
                priorities["P2"].append(r)
            else:
                priorities["P3"].append(r)

    priority_desc = {
        "P0": "P0 紧急（上线前必须修复）",
        "P1": "P1 高优（限期修复）",
        "P2": "P2 中优（版本迭代修复）",
        "P3": "P3 低优（长期优化）",
    }

    for p in ["P0", "P1", "P2", "P3"]:
        if priorities[p]:
            report += f"### {priority_desc[p]}\n\n"
            for i, item in enumerate(priorities[p], 1):
                report += f"{i}. **{item.get('item_id', '')} {item.get('item_name', '')}**\n"
                report += f"   - 整改建议：{item.get('recommendation', '参见详细检查结果')}\n\n"

    # 法规依据索引
    report += "## 七、法规依据索引\n\n"
    report += "本报告引用的法律法规汇总：\n\n"
    report += "| 序号 | 法规名称 | 引用条款 | 适用检查项 |\n"
    report += "|------|----------|----------|------------|\n"

    legal_refs = {}
    for r in check_results:
        basis = r.get("legal_basis", "")
        if basis:
            legal_refs[basis] = legal_refs.get(basis, [])
            legal_refs[basis].append(r.get("item_id", ""))

    for i, (basis, items) in enumerate(legal_refs.items(), 1):
        report += f"| {i} | {basis} | — | {', '.join(items[:5])}{'...' if len(items) > 5 else ''} |\n"

    # 免责声明
    report += """
## 免责声明

本报告基于静态分析和文本审查，不构成正式法律意见。报告中涉及的APK静态分析结果反映"声明层面"的技术事实，不等同于运行时实际行为。运行时真实调用行为需通过动态测试进一步确认。涉及重大合规决策或面临监管调查时，应咨询专业律师。

---

*本报告由APP个人信息保护合规检查技能（app-compliance-review）生成*
"""

    return report


def interactive_input():
    """交互式输入检查结果"""
    print("=" * 60)
    print("APP合规检查报告生成器 - 交互模式")
    print("=" * 60)

    app_info = {}
    app_info["app_name"] = input("APP名称: ").strip() or "未提供"
    app_info["package_name"] = input("包名: ").strip() or "未提供"
    app_info["version"] = input("版本号: ").strip() or "未提供"
    app_info["platform"] = input("平台(Android/iOS) [Android]: ").strip() or "Android"

    check_results = []
    modules = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11"]

    print("\n请逐项输入检查结果（留空跳过）：")
    for module in modules:
        print(f"\n--- {module} ---")
        while True:
            item_id = input(f"检查项编号（如{module}-1，留空结束本模块）: ").strip()
            if not item_id:
                break
            item_name = input("检查项名称: ").strip()
            status = input("状态(compliant/warning/non_compliant): ").strip().lower()
            risk = input("风险等级(high/medium/low): ").strip().lower()
            finding = input("事实发现: ").strip()
            legal_basis = input("法规依据: ").strip()
            recommendation = input("整改建议: ").strip()

            check_results.append({
                "module": module,
                "item_id": item_id,
                "item_name": item_name,
                "status": status,
                "risk_level": risk,
                "finding": finding,
                "legal_basis": legal_basis,
                "recommendation": recommendation,
                "method": "[文本]",
            })

    return app_info, check_results


def main():
    parser = argparse.ArgumentParser(description="合规检查报告生成器 - APP合规检查")
    parser.add_argument("--input", "-i", help="检查结果JSON文件路径")
    parser.add_argument("--apk-analysis", help="APK分析JSON报告路径（可选）")
    parser.add_argument("--output", "-o", help="输出Markdown报告文件路径")
    parser.add_argument("--interactive", action="store_true", help="交互式输入检查结果")

    args = parser.parse_args()

    if args.interactive:
        app_info, check_results = interactive_input()
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        app_info = data.get("app_info", {})
        check_results = data.get("check_results", [])
    else:
        print("请指定 --input 或 --interactive 参数", file=sys.stderr)
        sys.exit(1)

    apk_analysis = None
    if args.apk_analysis:
        with open(args.apk_analysis, "r", encoding="utf-8") as f:
            apk_analysis = json.load(f)

    report = generate_report(app_info, check_results, apk_analysis)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ 报告已生成: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
