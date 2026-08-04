#!/usr/bin/env python3
"""
Tax Compliance 7-Step Closed Loop Tool
Version: v1.0.0 | Updated: 2026-07-04

[Design Principles]
- This tool provides standardized process guidance, NOT KB caching
- KB files managed by MCP server, online query only
- This tool provides offline process guidance when MCP unavailable

[Usage]
- MCP available -> Call server API for professional answers
- MCP unavailable -> Use this tool for offline process guidance
"""

from typing import Optional, List, Dict

STEP_NAMES = [
    "Step 1: Risk Identification",
    "Step 2: Initial Assessment",
    "Step 3: Self-check Checklist",
    "Step 4: Evidence Preparation",
    "Step 5: Policy Confirmation",
    "Step 6: Tax Calculation",
    "Step 7: Filing & Execution"
]

STEP_DESCRIPTIONS = [
    "Use risk_check or tax_policy_ask to identify risk points",
    "Evaluate risk level against risk indicator matrix",
    "Use practical-guide.md for tax-type self-check",
    "Organize invoices/contracts/fund flows/logistics docs",
    "Use tax_policy_ask to confirm specific policy terms",
    "Use tax_calculate to compute tax amount",
    "File on time + periodic review"
]

STEP_CHECKLIST = [
    ["Are invoice/fund/contract/logistics flows consistent?"],
    ["Any high-risk keywords (虚开/买票/走账/空壳)?"],
    ["A类(invoice)/B类(revenue)/C类(cost) self-check?"],
    ["Are contracts, invoices, fund flows, logistics complete?"],
    ["Policy terms, conditions, deadlines confirmed?"],
    ["VAT/CIT/PIT/small taxes calculated separately?"],
    ["Filing deadline? Advance payment needed? Quarterly or monthly?"],
]

HIGH_RISK_KEYWORDS = [
    "虚开", "买票", "走票", "变票", "走账不走货",
    "空壳公司", "私人账户", "阴阳合同",
    "洗钱", "代持", "资金拆分", "恶意注销",
    "跨境", "隐瞒收入", "失控发票"
]

MEDIUM_RISK_KEYWORDS = [
    "税负率异常", "成本倒挂", "白条入账",
    "无票费用", "关联交易", "长期挂账"
]

# 结构化情形兜底识别（离线场景）：命中即提示"关联专项情形，须用 risk_check 立体评估"，
# 避免关键词 0 命中时误报 "LOW / 无风险"。仅做情形归类，不展开风险点。
SCENARIO_GUARD = {
    "减资/撤资/退股": ["减资", "撤资", "退股", "减少注册资本", "公司回购", "回购股权", "退伙", "股东退出"],
    "股权转让": ["股权转让", "转股权", "卖股权", "股权过户", "转让股权", "股权退出"],
    "清算/注销": ["清算", "注销", "清税", "解散", "终止经营"],
    "转增股本": ["转增", "未分配利润转增", "盈余公积转增", "资本公积转增", "送股"],
    "对赌/估值调整": ["对赌", "估值调整", "业绩承诺", "补偿条款"],
    "股权代持": ["代持", "名义股东", "隐名股东", "代持还原"],
    "家族/持股平台架构": ["家族", "持股平台", "家族信托", "股权架构", "有限合伙持股"],
    "跨境重组": ["跨境重组", "走出去", "境外架构", "红筹", "间接转让"],
    "破产重整/债务重组": ["破产重整", "债务重组", "破产清算", "债转股", "债务豁免"],
    "促销红包/扫码返现": ["扫码红包", "返现", "促销红包", "扫码返现", "消费者红包", "二维码红包", "现金红包", "冲减收入", "业务宣传费", "促销费用"],
    "全生命周期/全税种综合审查": ["全生命周期", "全税种", "全周期", "全环节", "全流程", "税务健康", "税务体检", "全面自查", "一体化", "涉税风险管理指引"],
}


def print_header():
    print("=" * 60)
    print("Tax Compliance 7-Step Closed Loop Tool v1.0.0")
    print("=" * 60)
    print()


def print_step(step_idx: int):
    print(f"\n{'=' * 60}")
    print(f"Step {step_idx + 1}/7: {STEP_NAMES[step_idx]}")
    print(f"{'=' * 60}")
    print(f"Description: {STEP_DESCRIPTIONS[step_idx]}")
    if step_idx < len(STEP_CHECKLIST):
        print("\nSelf-check Points:")
        for i, item in enumerate(STEP_CHECKLIST[step_idx], 1):
            print(f"  [{i}] {item}")


def quick_risk_check(scenario: str) -> Dict:
    """Quick risk self-check (offline available)"""
    scenario_lower = scenario.lower()
    matched_high = [kw for kw in HIGH_RISK_KEYWORDS if kw in scenario]
    matched_medium = [kw for kw in MEDIUM_RISK_KEYWORDS if kw in scenario]

    if matched_high:
        return {
            "level": "CRITICAL",
            "message": f"High-risk keywords: {', '.join(matched_high)}",
            "action": "Stop immediately, consult professionals"
        }
    elif matched_medium:
        return {
            "level": "MEDIUM",
            "message": f"Medium-risk keywords: {', '.join(matched_medium)}",
            "action": "Self-check, confirm business authenticity"
        }

    # 结构化情形兜底：关键词 0 命中也可能关联专项资本交易情形，提示用 risk_check 立体评估
    matched_scenarios = [name for name, aliases in SCENARIO_GUARD.items()
                         if any(a in scenario for a in aliases)]
    if matched_scenarios:
        return {
            "level": "SCENARIO",
            "message": f"关联结构化情形: {', '.join(matched_scenarios)}（关键词引擎未命中，但可能涉及专项结构化风险，含资本交易 / 促销返现 / 全生命周期审查等）",
            "action": "恢复服务后用 risk_check 做双引擎立体评估，勿仅凭'无关键词'认定无风险"
        }

    return {
        "level": "LOW",
        "message": "No obvious risk keywords detected",
        "action": "Proceed with caution, use risk_check for confirmation"
    }


def print_full_workflow():
    """Print complete 7-step workflow"""
    print_header()
    print("Tax Compliance 7-Step Closed Loop:\n")
    for i, (name, desc) in enumerate(zip(STEP_NAMES, STEP_DESCRIPTIONS), 1):
        print(f"  {name}")
        print(f"    -> {desc}\n")

    print("\n" + "=" * 60)
    print("High-Risk Keywords (Triggers CRITICAL risk):")
    print("=" * 60)
    for kw in HIGH_RISK_KEYWORDS:
        print(f"  [!] {kw}")
    print()


def print_offline_usage():
    """Print offline usage guide"""
    print("\n" + "=" * 60)
    print("Offline Usage Guide")
    print("=" * 60)
    print("""
This tool provides standardized process guidance.
KB files are managed by MCP server:

[MCP Available]
  -> Call tax_policy_ask for professional policy answers
  -> Call risk_check for accurate risk assessment
  -> Call tax_calculate for tax computation

[MCP Unavailable]
  -> Use this tool's 7-step workflow for self-check
  -> Use quick_risk_check() for offline risk assessment
  -> See anti-patterns.md to avoid common mistakes

[After Service Recovery]
  -> Use kb_list to view all KB topics
    """)


def run_interactive():
    """Run interactive mode"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_full_workflow()
        print_offline_usage()
        return

    print_header()
    print("Select operation:")
    print("  [1] View complete 7-step workflow")
    print("  [2] Quick risk self-check")
    print("  [3] Offline usage guide")
    print("  [q] Quit")
    print()

    while True:
        try:
            choice = input("Select (1/2/3/q): ").strip()
            if choice == "1":
                print_full_workflow()
            elif choice == "2":
                scenario = input("\nEnter scenario: ").strip()
                if scenario:
                    result = quick_risk_check(scenario)
                    icon = "[!]" if result["level"] == "CRITICAL" else \
                           "[?]" if result["level"] == "MEDIUM" else "[OK]"
                    print(f"\n{icon} Risk Level: {result['level']}")
                    print(f"   {result['message']}")
                    print(f"   Action: {result['action']}")
            elif choice == "3":
                print_offline_usage()
            elif choice.lower() == "q":
                print("Goodbye!")
                break
            else:
                print("Invalid choice")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run_interactive()
