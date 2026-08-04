#!/usr/bin/env python3
# 财税合规助手 - 离线参考工具（Offline Reference Tool）
# Version: v2.0.0 | Updated: 2026-07-20
#
# 设计原则：本工具为纯本地离线参考，不发起任何网络请求、不连接任何本地服务端口。
# 当远程 MCP 服务可用时，请直接使用主技能（SKILL.md）提供的在线能力；
# 本工具仅在完全离线场景下提供税率速查与风险关键词本地对照。

OFFLINE_TAX_RATE_REF = {
    "Small-scale VAT Exemption": "Monthly sales <= 100k exempt (2026)",
    "General Taxpayer Rates": "Goods 13%, Services 6%, Transport 9%",
    "Small Micro CIT": "Under 3M at 25%, effective rate 5%",
    "R&D Super Deduction": "General 100%, Manufacturing 120%",
    "PIT Special Deductions": "7 items, e.g. child ed 2000/month/person",
    "Year-end Bonus": "Separate or combined (by 2027)",
}

OFFLINE_RISK_KEYWORDS = {
    "Invoice Risk": ["虚开", "买票", "变票", "走账", "失控发票", "变名销售"],
    "Fund Risk": ["私人账户", "公转私", "资金异常"],
    "Revenue Risk": ["隐瞒收入", "阴阳合同", "零申报", "未开票收入"],
    "Cost Risk": ["白条入账", "虚增成本", "无票费用"],
    "New Business Risk": ["直播带货", "电商刷单", "跨境低报"],
}

OFFLINE_HELP = '\n'.join([
    'Usage:',
    '  python offline_fallback.py        # 显示离线说明',
    '  python offline_fallback.py --ref  # 税率速查',
    '  python offline_fallback.py --risk # 风险关键词',
    '  python offline_fallback.py --help # 显示本帮助',
    '',
])

OFFLINE_MODE = '\n'.join([
    '',
    '[离线使用说明]',
    '1. 政策查询 -> 使用下方税率速查与风险关键词对照',
    '2. 在线完整能力（政策问答/风险自查/合同审核等）-> 由主技能在联网时提供',
    '3. 恢复联网后，主技能将自动调用云端知识库获取最新政策',
    '',
])


def print_offline_mode():
    print('\n' + '=' * 60)
    print('[INFO] 当前为离线参考模式（未连接远程服务）')
    print('=' * 60)
    print(OFFLINE_MODE)


def print_quick_ref():
    print('\n' + '=' * 60)
    print('Tax Rate Quick Reference (Offline)')
    print('=' * 60)
    for topic, desc in OFFLINE_TAX_RATE_REF.items():
        print('  %s: %s' % (topic, desc))
    print()


def print_risk_keywords():
    print('\n' + '=' * 60)
    print('Risk Keywords (Offline Self-check)')
    print('=' * 60)
    for category, keywords in OFFLINE_RISK_KEYWORDS.items():
        print('\n  [%s]' % category)
        for kw in keywords:
            print('    - %s' % kw)
    print()


def main():
    import sys
    print('=' * 60)
    print('Tax Compliance Assistant - Offline Reference Tool v2.0.0')
    print('=' * 60)
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--ref':
            print_quick_ref()
        elif arg == '--risk':
            print_risk_keywords()
        elif arg == '--help':
            print(OFFLINE_HELP)
        else:
            print('Unknown argument: %s' % arg)
    else:
        print_offline_mode()
        print_quick_ref()
        print_risk_keywords()


if __name__ == '__main__':
    main()
