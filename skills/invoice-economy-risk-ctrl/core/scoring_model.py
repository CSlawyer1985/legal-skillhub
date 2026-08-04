"""发票经济风控 · 评分与建议模型

负责：加权计算综合风险得分、确定风险等级（P0~P3）、生成整改建议，
并可选择调用云端财税知识库（MCP）为命中指标补强政策依据。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.indicators import MAX_WEIGHT  # noqa: E402

# 命中指标的严重程度系数
_SEVERITY = {"high": 1.0, "medium": 0.7, "low": 0.4}


def _severity_of(result):
    """根据指标权重与命中情况推导严重程度"""
    w = result.get("weight", 0)
    if w >= 8:
        return "high"
    if w >= 6:
        return "medium"
    return "low"


def evaluate(results, context=None, mcp_enrich=False, mcp_limit=3):
    """评估计算结果，输出综合报告数据

    :param results: RiskEngine.calculate 的输出
    :param context: 企业上下文（用于 MCP 补强时传入行业）
    :param mcp_enrich: 是否调用云端知识库补强政策依据
    :param mcp_limit: 最多为多少条命中指标补强（避免过多网络调用）
    :return: dict 报告结构
    """
    context = context or {}
    hits = [r for r in results if r.get("hit")]

    penalty = 0.0
    for r in hits:
        sev = _severity_of(r)
        penalty += r.get("weight", 0) * _SEVERITY[sev]

    risk_score = round(100 * penalty / MAX_WEIGHT) if MAX_WEIGHT else 0
    risk_score = max(0, min(100, risk_score))

    level, label, action = _level_of(risk_score)

    # 建议：按严重程度+权重排序，取前若干条
    ordered = sorted(hits, key=lambda r: (_SEVERITY[_severity_of(r)], r.get("weight", 0)), reverse=True)
    suggestions = []
    for r in ordered:
        suggestions.append({
            "id": r["id"], "name": r["name"], "severity": _severity_of(r),
            "advice": r.get("advice"), "detail": r.get("detail"),
        })

    report = {
        "risk_score": risk_score,
        "level": level,
        "level_label": label,
        "action": action,
        "hit_count": len(hits),
        "total_indicators": len(results),
        "suggestions": suggestions,
        "results": results,
    }

    if mcp_enrich and hits:
        _enrich_with_mcp(report, context, limit=mcp_limit)

    return report


def _level_of(score):
    if score >= 65:
        return "P3", "高危", "🚨 暂停异常开票，立即全面自查并联系专业税务师"
    if score >= 40:
        return "P2", "中风险", "⚡ 限期补充业务资料，核实业务真实性"
    if score >= 20:
        return "P1", "轻度风险", "⚠️ 关注指标变化，必要时咨询税务师"
    return "P0", "安全", "✅ 当前指标未见明显异常，保持合规经营"


def _enrich_with_mcp(report, context, limit=3):
    """为命中的前 N 条指标，调用云端知识库补强政策依据"""
    try:
        from config.mcp_client import invoice_risk_advice
    except Exception:
        return
    industry = context.get("industry")
    enriched = []
    for s in report["suggestions"][:limit]:
        try:
            adv = invoice_risk_advice(s["name"], s.get("advice") or "", industry=industry)
        except Exception:
            adv = {"source": "local", "note": "MCP 调用失败"}
        s["mcp_advice"] = adv  # 挂回建议项，供报告渲染政策依据
        enriched.append({"id": s["id"], "name": s["name"], "advice": adv})
    report["mcp_enrichment"] = enriched
    report["mcp_mode"] = enriched[0]["advice"].get("source") if enriched else "none"
