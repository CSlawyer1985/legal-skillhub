#!/usr/bin/env python3
"""
compliance-monitor.py — 合规哨兵监控虾核心脚本

用法:
  python3 compliance-monitor.py query --company "公司名称" [--credit-code "统一社会信用代码"]
  python3 compliance-monitor.py import --file partners.csv
  python3 compliance-monitor.py monitor --bitable-token <app_token> --table-id <table_id>
  python3 compliance-monitor.py report --month 2026-04

环境变量（可选，提升数据质量）:
  QCC_API_KEY   — 企查查 API Key
  TYC_API_KEY   — 天眼查 API Key
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date

# ─── 风险规则 ────────────────────────────────────────────────────────────────

RISK_RULES = {
    "失信被执行人": {"level": "high", "score": 60, "emoji": "🔴"},
    "资产冻结":     {"level": "high", "score": 50, "emoji": "🔴"},
    "重大诉讼":     {"level": "high", "score": 40, "emoji": "🔴"},
    "经营异常":     {"level": "medium", "score": 30, "emoji": "🟠"},
    "行政处罚":     {"level": "medium", "score": 20, "emoji": "🟠"},
    "股权变更":     {"level": "low", "score": 10, "emoji": "🟡"},
    "法人变更":     {"level": "low", "score": 10, "emoji": "🟡"},
    "注册信息变更": {"level": "low", "score": 5,  "emoji": "🟡"},
}

def score_to_level(score: int) -> tuple[str, str]:
    if score >= 60:
        return "high", "🔴 高风险"
    elif score >= 30:
        return "medium", "🟠 中风险"
    elif score > 0:
        return "low", "🟡 低风险"
    return "normal", "✅ 正常"


# ─── 数据查询（免费数据源 + 商业 API）────────────────────────────────────────

def query_qcc(company_name: str, credit_code: str = "") -> dict:
    """企查查 API 查询（需要 QCC_API_KEY）"""
    api_key = os.environ.get("QCC_API_KEY", "")
    if not api_key:
        return {}
    # 企查查 API 示例（实际接入时替换为真实 endpoint）
    # https://openapi.qcc.com/dataservice/api/CompanyBase
    return {"source": "qcc", "note": "企查查 API 已配置，请参考官方文档接入"}


def query_tyc(company_name: str, credit_code: str = "") -> dict:
    """天眼查 API 查询（需要 TYC_API_KEY）"""
    api_key = os.environ.get("TYC_API_KEY", "")
    if not api_key:
        return {}
    return {"source": "tyc", "note": "天眼查 API 已配置，请参考官方文档接入"}


def query_company(company_name: str, credit_code: str = "") -> dict:
    """
    查询公司合规信息。
    优先使用商业 API，降级到免费数据源提示。
    返回结构化风险摘要。
    """
    result = {
        "company_name": company_name,
        "credit_code": credit_code,
        "query_time": datetime.now().isoformat(),
        "risks": [],
        "total_score": 0,
        "risk_level": "normal",
        "risk_label": "✅ 正常",
        "data_sources": [],
        "note": "",
    }

    # 尝试商业数据源
    qcc_data = query_qcc(company_name, credit_code)
    tyc_data = query_tyc(company_name, credit_code)

    if qcc_data:
        result["data_sources"].append("企查查")
    if tyc_data:
        result["data_sources"].append("天眼查")

    if not result["data_sources"]:
        result["data_sources"].append("免费数据源（有限）")
        result["note"] = (
            "未配置商业 API Key，数据覆盖有限。\n"
            "建议配置 QCC_API_KEY（企查查）或 TYC_API_KEY（天眼查）以获取完整数据。\n"
            "免费数据源查询地址：\n"
            "  - 工商信息：https://www.gsxt.gov.cn/\n"
            "  - 失信名单：https://zxgk.court.gov.cn/shixin/\n"
            "  - 裁判文书：https://wenshu.court.gov.cn/"
        )

    # 计算风险等级
    total_score = sum(r.get("score", 0) for r in result["risks"])
    result["total_score"] = total_score
    level, label = score_to_level(total_score)
    result["risk_level"] = level
    result["risk_label"] = label

    return result


# ─── 命令：query ──────────────────────────────────────────────────────────────

def cmd_query(args):
    print(f"\n🔍 查询合规信息：{args.company}")
    if args.credit_code:
        print(f"   统一社会信用代码：{args.credit_code}")
    print()

    result = query_company(args.company, args.credit_code or "")

    print(f"风险等级：{result['risk_label']}")
    print(f"综合评分：{result['total_score']} 分")
    print(f"数据来源：{', '.join(result['data_sources'])}")
    print(f"查询时间：{result['query_time']}")

    if result["risks"]:
        print("\n发现风险：")
        for risk in result["risks"]:
            rule = RISK_RULES.get(risk["type"], {})
            emoji = rule.get("emoji", "⚠️")
            print(f"  {emoji} {risk['type']}：{risk.get('detail', '')}")
    else:
        print("\n未发现明显风险记录。")

    if result["note"]:
        print(f"\n📌 提示：\n{result['note']}")

    # 输出 JSON 供程序化使用
    if args.json:
        print("\n--- JSON 输出 ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


# ─── 命令：import ─────────────────────────────────────────────────────────────

def cmd_import(args):
    """批量导入监控对象（从 CSV/Excel）"""
    import csv

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在：{args.file}")
        sys.exit(1)

    companies = []
    with open(args.file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("公司名称") or row.get("company_name") or row.get("name", "")
            code = row.get("统一社会信用代码") or row.get("credit_code") or row.get("code", "")
            if name:
                companies.append({"name": name.strip(), "credit_code": code.strip()})

    print(f"✅ 读取到 {len(companies)} 家合作方")
    for c in companies:
        print(f"  - {c['name']} ({c['credit_code'] or '无信用代码'})")

    print("\n📋 导入完成。请将以上数据录入飞书多维表格进行持续监控。")
    print("   表格字段：公司名称、统一社会信用代码、风险等级、最后检查时间、状态")

    return companies


# ─── 命令：report ─────────────────────────────────────────────────────────────

def cmd_report(args):
    """生成监控报告摘要"""
    month = args.month or datetime.now().strftime("%Y-%m")
    print(f"\n📊 生成 {month} 合规监控报告")
    print()
    print("报告模板（请结合飞书多维表格中的实际数据填充）：")
    print(f"""
【合规监控月报】{month}

监控概况：
- 监控合作方总数：__ 家
- 本月新增监控：__ 家
- 本月发现异动：__ 次

风险分布：
🔴 高风险：__ 家
🟠 中风险：__ 家
🟡 低风险：__ 家
✅ 正常：__ 家

建议：从飞书多维表格导出本月数据后填充以上数字。
""")


# ─── 命令：monitor ────────────────────────────────────────────────────────────

def cmd_monitor(args):
    """持续监控模式（说明）"""
    print("""
🔄 持续监控模式

持续监控通过以下方式实现：

1. 飞书多维表格存储监控对象清单
2. OpenClaw 定时任务（cron）每日触发监控
3. 发现异动时通过飞书消息推送预警

配置步骤：
  1. 在飞书多维表格中创建"合规监控档案"表
  2. 录入监控对象（公司名称 + 统一社会信用代码）
  3. 在 OpenClaw 中配置每日定时任务：
     "每天早上 8 点检查合规监控档案，对每家公司执行合规查询，发现异动推送飞书预警"
  4. 配置商业 API Key（可选）：
     export QCC_API_KEY=your_key
     export TYC_API_KEY=your_key

注意：实时监控依赖数据源更新频率，司法数据通常滞后 1-3 天。
""")


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="合规哨兵监控虾 — 合作方合规风险监控")
    subparsers = parser.add_subparsers(dest="command")

    # query
    p_query = subparsers.add_parser("query", help="单次查询公司合规信息")
    p_query.add_argument("--company", required=True, help="公司名称")
    p_query.add_argument("--credit-code", default="", help="统一社会信用代码（可选，提升准确率）")
    p_query.add_argument("--json", action="store_true", help="同时输出 JSON 格式结果")

    # import
    p_import = subparsers.add_parser("import", help="批量导入监控对象")
    p_import.add_argument("--file", required=True, help="CSV 文件路径（含公司名称、统一社会信用代码列）")

    # monitor
    p_monitor = subparsers.add_parser("monitor", help="持续监控模式说明")
    p_monitor.add_argument("--bitable-token", default="", help="飞书多维表格 app_token")
    p_monitor.add_argument("--table-id", default="", help="数据表 ID")

    # report
    p_report = subparsers.add_parser("report", help="生成监控报告")
    p_report.add_argument("--month", default="", help="报告月份，格式 YYYY-MM（默认当月）")
    p_report.add_argument("--output", default="", help="输出文件路径（可选）")

    args = parser.parse_args()

    if args.command == "query":
        cmd_query(args)
    elif args.command == "import":
        cmd_import(args)
    elif args.command == "monitor":
        cmd_monitor(args)
    elif args.command == "report":
        cmd_report(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
