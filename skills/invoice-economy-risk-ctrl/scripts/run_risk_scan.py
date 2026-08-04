"""
发票经济风控扫描器 v3.0.0 (Skill 版)
基于 15 项风控指标的企业发票风险智能扫描 —— 支持问卷式扫描、文件上传分析、演示模式，
并可一键调用云端「财税知识库 MCP 服务」为命中指标补强政策依据与整改建议。

依赖：Python 3.8+ 标准库；MCP 补强需联网（自动复用 tax-policy-knowledge-mcp 的注册凭证）。

用法：
  python run_risk_scan.py --demo                演示模式（模拟一家制造业企业）
  python run_risk_scan.py --questionnaire       问卷式扫描
  python run_risk_scan.py --analyze "文件"       上传 CSV/JSON 分析
  python run_risk_scan.py --analyze "文件" --mcp 上传分析并调用云端知识库补强政策
  python run_risk_scan.py --status              查看扫描历史

作者：Joyxj2devs Team
"""
# Copyright (c) 2026 Joyxj2devs Team. All rights reserved.
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

# Windows 控制台默认 GBK，重配置为 UTF-8 以正确输出 emoji / 中文
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore
except Exception:
    pass

from core.risk_engine import RiskEngine  # noqa: E402
from core.scoring_model import evaluate  # noqa: E402

DATA_DIR = SKILL_ROOT / "scripts" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = DATA_DIR / "scan_log.jsonl"

RISK_ENGINE = RiskEngine()


# ============= 演示数据 =============
def _demo_data():
    invoices = [
        {"id": "I001", "amount": 99999.99, "item": "电子设备", "type": "销项", "is_red": False, "tax_rate": 13, "buyer": "B1", "seller": "SELF", "date": "2026-03-02"},
        {"id": "I002", "amount": 99500.00, "item": "电子设备", "type": "销项", "is_red": False, "tax_rate": 13, "buyer": "B2", "seller": "SELF", "date": "2026-03-05"},
        {"id": "I003", "amount": 5200.00, "item": "配件", "type": "销项", "is_red": False, "tax_rate": 13, "buyer": "B3", "seller": "SELF", "date": "2026-03-08"},
        {"id": "I004", "amount": 12000.00, "item": "退货", "type": "销项", "is_red": True, "tax_rate": 13, "buyer": "B4", "seller": "SELF", "date": "2026-03-10"},
        {"id": "I005", "amount": 80000.00, "item": "原材料", "type": "进项", "is_red": False, "tax_rate": 13, "buyer": "SELF", "seller": "S1", "date": "2026-03-01"},
        {"id": "I006", "amount": 75000.00, "item": "原材料", "type": "进项", "is_red": False, "tax_rate": 13, "buyer": "SELF", "seller": "S2", "date": "2026-03-03"},
    ]
    context = {
        "industry": "制造业",
        "sales": 500000,
        "tax": 3000,
        "is_private_account": True,
        "related_party_ratio": 40,
        "profit": -50000,
        "loss_years": 0,
        "entity_age_months": 8,
        "transaction_count": 6,
        "no_invoice_cost": 200000,
        "total_cost": 450000,
    }
    return invoices, context


# ============= 问卷 =============
QUESTIONNAIRE = [
    {"key": "industry", "q": "企业所属行业？（制造业/商贸/软件信息技术服务/建筑业/房地产业/交通运输业/餐饮）", "opts": None},
    {"key": "sales", "q": "年销售额（元，数字即可）？", "opts": None},
    {"key": "tax", "q": "上年度已缴增值税（元）？", "opts": None},
    {"key": "is_private_account", "q": "是否存在用个人银行账户收取经营款项？（A 是 / B 否）", "opts": ["A", "B"]},
    {"key": "related_party_ratio", "q": "关联交易金额占全部交易比例约多少（%，数字即可，无则填0）？", "opts": None},
    {"key": "loss_years", "q": "连续亏损年数（数字，无则填0）？", "opts": None},
    {"key": "entity_age_months", "q": "企业成立月数（数字）？", "opts": None},
    {"key": "transaction_count", "q": "近一年开票/收票交易笔数（数字）？", "opts": None},
]


def _ask(question, opts):
    while True:
        ans = input(f"  {question}\n  输入: ").strip()
        if opts is None:
            return ans
        if ans in opts:
            return ans
        print("  [ERROR] 输入无效，请重输")


def _questionnaire_context():
    ctx = {}
    print("\n[SCAN] 开始发票经济风险问卷扫描（回答以下问题）\n")
    for item in QUESTIONNAIRE:
        ans = _ask(item["q"], item["opts"])
        if item["key"] == "is_private_account":
            ctx[item["key"]] = (ans == "A")
        elif item["key"] in ("sales", "tax", "related_party_ratio", "loss_years", "entity_age_months", "transaction_count"):
            try:
                ctx[item["key"]] = float(ans)
            except ValueError:
                ctx[item["key"]] = 0
        else:
            ctx[item["key"]] = ans
    return [], ctx


# ============= 报告 =============
def generate_report(report, mcp=False):
    lines = []
    lines.append("")
    lines.append("=" * 54)
    lines.append("📊 发票经济风险扫描报告")
    lines.append("=" * 54)
    lines.append(f"⏱ 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"综合得分: {report['risk_score']} 分")
    lines.append(f"风险等级: 【{report['level']}_{report['level_label']}】")
    lines.append(f"命中风险点数: {report['hit_count']} 个 (共 {report['total_indicators']} 项指标)")
    lines.append("-" * 54)
    icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}
    for s in report["suggestions"]:
        lines.append(f"{icon.get(s['severity'], '•')} 指标 {s['id']}: {s['name']}（{s['severity']}）")
        lines.append(f"    {s['detail']}")
        if s.get("advice"):
            lines.append(f"    建议: {s['advice']}")
        # MCP 补强
        if mcp and "mcp_advice" in s:
            ma = s["mcp_advice"]
            src = ma.get("source")
            if src == "mcp" and ma.get("policy_basis"):
                lines.append(f"    📚 政策依据: {str(ma['policy_basis'])[:160]}")
    lines.append("-" * 54)
    lines.append(f"💡 处置建议: {report['action']}")
    if mcp:
        mode = report.get("mcp_mode", "none")
        lines.append(f"🔗 知识库补强来源: {'云端财税知识库 MCP' if mode == 'mcp' else '本地规则库（远程不可用）'}")
    lines.append("=" * 54)
    lines.append("⚠️ 免责声明: 本报告基于 15 项指标与通用规则生成，仅供参考，")
    lines.append("   不能替代专业税务师意见。如需正式依据请咨询专业机构或拨打 12366。")
    lines.append("=" * 54)
    return "\n".join(lines)


def _save_log(report, mode):
    try:
        entry = {
            "ts": datetime.now().isoformat(), "mode": mode,
            "risk_score": report["risk_score"], "level": report["level"],
            "hit_count": report["hit_count"],
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load_history():
    if not LOG_FILE.exists():
        return []
    try:
        return [json.loads(l) for l in LOG_FILE.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    except Exception:
        return []


# ============= 入口 =============
def main():
    args = sys.argv[1:]
    mcp = "--mcp" in args
    if not args or args[0] == "--help":
        print("""
==============================================================
        发票经济风控扫描器 v3.0.0
==============================================================
  Usage:
    python run_risk_scan.py --demo                演示模式
    python run_risk_scan.py --questionnaire       问卷式扫描
    python run_risk_scan.py --analyze "文件"       上传 CSV/JSON 分析
    python run_risk_scan.py --analyze "文件" --mcp 分析+云端知识库补强
    python run_risk_scan.py --status              查看扫描历史
    python run_risk_scan.py --help                帮助
==============================================================
        """)
        return

    mode = args[0]
    if mode == "--demo":
        invoices, context = _demo_data()
        results = RISK_ENGINE.calculate(invoices, context)
        report = evaluate(results, context, mcp_enrich=mcp)
        print(generate_report(report, mcp))
        _save_log(report, "demo")

    elif mode == "--questionnaire":
        invoices, context = _questionnaire_context()
        results = RISK_ENGINE.calculate(invoices, context)
        report = evaluate(results, context, mcp_enrich=mcp)
        print(generate_report(report, mcp))
        _save_log(report, "questionnaire")

    elif mode == "--analyze":
        if len(args) < 2:
            print("[ERROR] 用法: python run_risk_scan.py --analyze <文件路径>")
            return
        path = args[1]
        raw = RISK_ENGINE.load_invoices(path)
        invoices = [RiskEngine.normalize_invoice(r) for r in raw] if isinstance(raw, list) else []
        context = raw.get("context", {}) if isinstance(raw, dict) else {}
        results = RISK_ENGINE.calculate(invoices, context)
        report = evaluate(results, context, mcp_enrich=mcp)
        print(generate_report(report, mcp))
        _save_log(report, "analyze")

    elif mode == "--status":
        hist = _load_history()
        if not hist:
            print("\n[EMPTY] 暂无扫描历史")
            return
        print(f"\n[LIST] 扫描历史（共 {len(hist)} 次）:")
        print("-" * 54)
        for h in hist[-10:]:
            ts = h.get("ts", "")[:19]
            flag = {"P3": "🔴", "P2": "🟠", "P1": "🟡", "P0": "🟢"}.get(h.get("level"), "•")
            print(f"  {flag} {ts} | {h.get('mode'):12s} | 得分 {h.get('risk_score')} | 命中 {h.get('hit_count')}")
        print("-" * 54)

    else:
        print(f"[ERROR] 未知命令: {mode}")


if __name__ == "__main__":
    main()
