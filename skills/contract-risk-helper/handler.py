#!/usr/bin/env python3
"""
Contract Risk Helper - handler.py
Read-only local analysis. No network, no exec, no credential access.
Scans both Chinese (中文) and English contract text for common risk clauses.
"""

import re

RISK_PATTERNS = [
    # ========== Critical - Liability ==========
    {
        "category": "Liability",
        "severity": "critical",
        "pattern": re.compile(r"unlimited liability|liability for all damages|no limit on liability|"
                             r"无限责任|无限赔偿|全部赔偿责任|一切损失.*赔偿|赔偿.*一切损失|"
                             r"承担.*全部.*责任|所有.*损失.*负责", re.I),
        "description": "无限责任条款 — 无赔偿金额上限",
        "description_en": "Unlimited liability clause — no financial cap on exposure",
        "suggestion": "协商增加赔偿上限（如 12 个月服务费或合同总额的 1-2 倍）",
        "suggestion_en": "Negotiate a liability cap (e.g., 12 months of fees or contract value)"
    },
    {
        "category": "Liability",
        "severity": "critical",
        "pattern": re.compile(r"indemnify.*any and all claims|hold harmless.*any and all|"
                             r"赔偿.*任何.*所有.*索赔|补偿.*一切.*损失|"
                             r"保证.*不受.*任何.*损失", re.I),
        "description": "宽泛的赔偿/保证条款 — 单方承担，无例外排除",
        "description_en": "Broad indemnification obligation — one-sided with no carve-outs",
        "suggestion": "限制赔偿范围为直接损失，增加例外条款（如第三方故意行为除外）",
        "suggestion_en": "Limit indemnification to direct damages caused by the indemnifying party's actions"
    },

    # ========== Critical - Termination ==========
    {
        "category": "Termination",
        "severity": "critical",
        "pattern": re.compile(r"may not be terminated|termination only for cause|no right to terminate|"
                             r"不得.*终止|不得.*解除|不能.*单方.*解除|"
                             r"除.*违约.*不得.*终止|除.*重大.*不得.*解除|"
                             r"不可撤销|不可解除", re.I),
        "description": "无任意终止权 — 无法在无违约情况下退出合同",
        "description_en": "No termination for convenience — no exit without breach",
        "suggestion": "增加任意终止权条款，给予合理通知期（30-90 天）",
        "suggestion_en": "Add termination for convenience with reasonable notice (30-90 days)"
    },
    {
        "category": "Termination",
        "severity": "critical",
        "pattern": re.compile(r"automatically renew|auto-renew|automatic renewal|successive one-year|"
                             r"自动续签|自动续约|自动延长|自动顺延|"
                             r"到期.*自动.*续|届满.*自动.*延长|"
                             r"如无.*异议.*自动", re.I),
        "description": "自动续约条款 — 合同在无主动决策下自动延长",
        "description_en": "Automatic renewal without active renewal decision",
        "suggestion": "增加续约前 30-60 天书面确认要求，添加不续约退出条款",
        "suggestion_en": "Ensure 30-60 day notice requirement before renewal; add opt-out clause"
    },

    # ========== Critical - Dispute ==========
    {
        "category": "Dispute",
        "severity": "critical",
        "pattern": re.compile(r"venue shall be|jurisdiction shall be|exclusive jurisdiction|"
                             r"管辖.*法院.*为|争议.*由.*法院.*管辖|"
                             r"提交.*法院.*解决|由.*所在地.*法院.*管辖|"
                             r"诉讼.*地点.*为|仲裁.*地点.*为|仲裁.*机构.*为", re.I),
        "description": "指定管辖/仲裁地条款 — 可能对己方不利",
        "description_en": "Exclusive venue/jurisdiction clause — verify fairness",
        "suggestion": "协商选择中立地点或己方所在地法院/仲裁机构",
        "suggestion_en": "Negotiate neutral venue or your home jurisdiction"
    },
    # Additional: unfair arbitration clause
    {
        "category": "Dispute",
        "severity": "critical",
        "pattern": re.compile(r"arbitration.*final.*binding.*no.*appeal|"
                             r"仲裁裁决.*终局.*不得.*上诉|"
                             r"一裁终局|仲裁.*最终.*有约束力", re.I),
        "description": "一裁终局且不可上诉 — 放弃司法救济途径",
        "description_en": "Final binding arbitration with no appeal right",
        "suggestion": "确认是否接受放弃上诉权，重大争议建议保留司法审查途径",
        "suggestion_en": "Consider whether to waive appeal rights; retain judicial review for major disputes"
    },

    # ========== Warning - Payment ==========
    {
        "category": "Payment",
        "severity": "warning",
        "pattern": re.compile(r"payment.*(?:due|within).*\d+\s*days|net\s*[6-9]\d|"
                             r"付款.*期限.*\d+.*天|到货.*\d+.*天.*付款|"
                             r"收货.*\d+.*天.*内.*支付|"
                             r"发票.*开具.*后.*\d+.*天|付款周期.*\d+.*天", re.I),
        "description": "延长付款期限（60+ 天）— 影响现金流",
        "description_en": "Extended payment terms (60+ days) — cash flow impact",
        "suggestion": "协商缩短至 30 天标准账期，或要求预付部分款项",
        "suggestion_en": "Negotiate standard net 30 terms or request early payment discount"
    },
    {
        "category": "Payment",
        "severity": "warning",
        "pattern": re.compile(r"no.*late.*payment.*penalty|no.*penalty.*late|"
                             r"未.*约定.*逾期.*罚则|无.*逾期.*利息|"
                             r"未约定.*违约金|无.*迟延.*责任", re.I),
        "description": "无逾期付款罚则 — 缺乏按时付款的约束力",
        "description_en": "No penalty for late payment — no incentive for timely payment",
        "suggestion": "增加逾期付款违约金条款（如每日万分之五或月息 1.5%）",
        "suggestion_en": "Add late fee clause (e.g., 1.5% per month on overdue amounts)"
    },
    # Additional: non-refundable
    {
        "category": "Payment",
        "severity": "warning",
        "pattern": re.compile(r"non[-\s]?refundable|no refund|"
                             r"不.*退还|不予.*退还|不予.*退款|"
                             r"已付款项.*不退|预付款.*不退|定金.*不退", re.I),
        "description": "不退款条款 — 已付款项在任何情况下均不退还",
        "description_en": "Non-refundable payment clause — no refund under any circumstances",
        "suggestion": "协商增加退款条件（如对方违约、未交付等情况）",
        "suggestion_en": "Add refund conditions (e.g., breach by counterparty, non-delivery)"
    },

    # ========== Warning - IP ==========
    {
        "category": "Intellectual Property",
        "severity": "warning",
        "pattern": re.compile(r"work[-\s]?made[-\s]?for[-\s]?hire|work[-\s]?for[-\s]?hire|work for hire|"
                             r"职务作品|工作成果.*归.*所有|职务.*成果.*归|"
                             r"在.*期间.*完成.*成果.*归|"
                             r"所有.*知识产权.*归属|知识产权.*归.*所有|知识产权.*均归", re.I),
        "description": "职务作品/知识产权归属条款 — 可能包含背景 IP",
        "description_en": "Work-for-hire clause — may transfer all background IP",
        "suggestion": "限定为「本项目范围内产生的成果」，明确排除背景知识产权",
        "suggestion_en": "Limit to specific project deliverables; carve out pre-existing IP"
    },
    {
        "category": "Intellectual Property",
        "severity": "warning",
        "pattern": re.compile(r"assigns? all rights|all inventions|all intellectual property|"
                             r"转让.*全部.*权利|全部.*知识产权.*转让|"
                             r"所有.*发明.*归|所有.*专利.*归|"
                             r"一切.*技术.*成果.*归", re.I),
        "description": "宽泛的知识产权转让 — 超出项目范围",
        "description_en": "Broad IP assignment — beyond project scope",
        "suggestion": "限定转让范围为「本项目直接产生的发明创造」",
        "suggestion_en": "Limit assignment to inventions conceived specifically during this project"
    },

    # ========== Warning - Confidentiality ==========
    {
        "category": "Confidentiality",
        "severity": "warning",
        "pattern": re.compile(r"perpetual confidentiality|perpetuity|indefinite.*confidential|survive forever|"
                             r"永久.*保密|无限期.*保密|保密.*永久|"
                             r"终身.*保密|保密义务.*无限|"
                             r"保密.*没有.*期限|保密.*不因.*终止", re.I),
        "description": "永久保密义务 — 无期限限制，执行成本高",
        "description_en": "Indefinite confidentiality obligation — never expires",
        "suggestion": "保密期限限制为合同终止后 3-5 年",
        "suggestion_en": "Limit confidentiality term to 3-5 years after contract termination"
    },
    {
        "category": "Confidentiality",
        "severity": "warning",
        "pattern": re.compile(r"all information.*confidential|any information.*confidential|"
                             r"所有信息.*视为.*保密|全部.*信息.*保密|"
                             r"任何.*信息.*均.*视为.*保密|"
                             r"一切.*资料.*保密|任何.*知悉.*保密", re.I),
        "description": "保密信息定义过宽 — 无例外条款（如已公开信息）",
        "description_en": "Overly broad definition of confidential information",
        "suggestion": "增加例外条款：已公开信息、独立开发、第三方合法获取等",
        "suggestion_en": "Add explicit carve-outs (public info, independently developed, etc.)"
    },
    # Additional: missing return clause
    {
        "category": "Confidentiality",
        "severity": "warning",
        "pattern": re.compile(r"return.*confidential|destroy.*confidential|"
                             r"返还.*保密|销毁.*保密|交还.*资料|"
                             r"归还.*全部.*材料|返还.*全部.*文件", re.I),
        "description": "已存在保密资料返还/销毁条款 — 正常。但如果合同不含此条款则为缺失，需人工判断。",
        "description_en": "Return/destroy clause present — normal. If absent, flag manually.",
        "suggestion": "",  # This is an info-only pattern
        "suggestion_en": ""
    },

    # ========== Warning - Termination Details ==========
    {
        "category": "Termination",
        "severity": "warning",
        "pattern": re.compile(r"notice.*(?:180|one hundred eighty|six months)|termination fee.*total|early termination.*all fees|"
                             r"通知.*180.*天|通知.*六个月|提前.*半年.*通知|"
                             r"违约金.*合同总额|终止.*支付.*全部|"
                             r"提前.*终止.*支付.*全部.*费用|"
                             r"解约.*赔偿.*全部|提前.*解约.*支付.*剩余", re.I),
        "description": "过长通知期或高额提前终止费 — 退出成本过高",
        "description_en": "Excessive termination notice period or prohibitive exit fee",
        "suggestion": "协商缩短通知期至 30-60 天，终止费应按比例计算",
        "suggestion_en": "Reduce notice to 30-60 days; negotiate reasonable prorated termination fee"
    },

    # ========== Warning - Dispute ==========
    {
        "category": "Dispute",
        "severity": "warning",
        "pattern": re.compile(r"prevailing party.*attorney.*fee|attorney.*fee.*prevailing|"
                             r"胜诉方.*律师费|律师费.*由.*败诉|"
                             r"律师费.*胜诉.*承担|诉讼费.*败诉.*承担", re.I),
        "description": "单方律师费条款 — 注意是否对等",
        "description_en": "Attorney fee provision — check if mutual",
        "suggestion": "修改为双方各自承担或双向条款",
        "suggestion_en": "Make mutual — each party bears its own costs, or prevailing party recovers fees"
    },

    # ========== Advisory - Payment ==========
    {
        "category": "Payment",
        "severity": "advisory",
        "pattern": re.compile(r"payment upon completion|upon completion.*payment|"
                             r"完成.*后.*付款|验收.*后.*支付|"
                             r"交付.*后.*结算|完工.*后.*付款", re.I),
        "description": "付款节点不明确 — 缺少里程碑/验收标准定义",
        "description_en": "Unclear payment trigger — no milestone definition",
        "suggestion": "明确具体的交付成果和验收标准作为付款触发条件",
        "suggestion_en": "Define specific milestones or deliverables that trigger payment obligations"
    },

    # ========== Advisory - Service/Scope ==========
    {
        "category": "Service",
        "severity": "advisory",
        "pattern": re.compile(r"sole discretion|reasonably determined|solely at.*discretion|"
                             r"有权.*随时|由.*单方.*决定|由.*自行.*判断|"
                             r"甲方.*有权.*调整|乙方.*需.*配合.*任何|"
                             r"根据.*需要.*随时|单方面.*变更|无需.*另行.*通知", re.I),
        "description": "范围模糊/单方可变更 — 可能被单方面扩大义务",
        "description_en": "Vague scope — allows unilateral expansion of obligations",
        "suggestion": "明确具体交付物和验收标准，限制单方变更需双方书面确认",
        "suggestion_en": "Define specific deliverables with measurable acceptance criteria"
    },
    {
        "category": "Service",
        "severity": "advisory",
        "pattern": re.compile(r"no service level|no uptime|without.*guarantee|"
                             r"无.*服务.*标准|无.*服务.*等级|"
                             r"不保证.*可用|无.*质量.*保证|"
                             r"不.*承诺.*服务.*质量|"
                             r"尽力.*提供|尽.*最大.*努力", re.I),
        "description": "无服务水平承诺 — 缺少服务质量保障",
        "description_en": "No service level agreement — no quality guarantee",
        "suggestion": "增加 SLA 条款，明确服务标准和未达标的补救措施（如减免费用或解约权）",
        "suggestion_en": "Add SLA with remedies (credits or termination right) for missed targets"
    },
    # Additional: penalty clause
    {
        "category": "Service",
        "severity": "advisory",
        "pattern": re.compile(r"penalty.*per.*day|liquidated damages.*per.*day|"
                             r"每日.*违约金|按日.*计算.*违约金|"
                             r"每.*逾期.*一日.*支付|每日.*万分之", re.I),
        "description": "违约金/罚则条款 — 已存在，需评估是否合理",
        "description_en": "Penalty/liquidated damages clause present — evaluate reasonableness",
        "suggestion": "确认违约金比例是否合理（通常每日万分之五以内）",
        "suggestion_en": "Confirm penalty rate is reasonable (typically under 0.05% per day)"
    },
]


def scan(text: str) -> list:
    """Scan contract text for risk patterns. Pure read-only."""
    if not text or not isinstance(text, str) or not text.strip():
        return []

    results = []
    seen = set()  # deduplicate similar matches
    for item in RISK_PATTERNS:
        match = item["pattern"].search(text)
        if match:
            key = (item["category"], item["severity"], item.get("description_en", item["description"]))
            if key in seen:
                continue
            seen.add(key)

            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            context = text[start:end].strip()

            # Skip patterns that are purely informational (empty suggestion)
            if not item.get("suggestion") and not item.get("suggestion_en"):
                continue

            results.append({
                "category": item["category"],
                "severity": item["severity"],
                "matched": match.group(),
                "context": context[:150],
                "description": item["description"],
                "suggestion": item["suggestion"]
            })
    return results


def format_results(results: list) -> str:
    """Format scan results as readable bilingual text."""
    if not results:
        return ("✅ 未发现已知风险模式。\n\n"
                "（此扫描仅针对常见已知风险模式，不能替代专业法律审查）\n"
                "✅ No known risk patterns detected.\n\n"
                "(This scan covers common patterns only; not a substitute for professional legal review)\n")

    by_severity = {"critical": [], "warning": [], "advisory": []}
    for r in results:
        by_severity[r["severity"]].append(r)

    emojis = {"critical": "🔴", "warning": "🟡", "advisory": "🟢"}
    labels = {"critical": "严重 Critical", "warning": "警告 Warning", "advisory": "提醒 Advisory"}

    output = f"## 合同风险扫描结果 Contract Risk Scan\n\n共发现 **{len(results)}** 个风险项 | Found **{len(results)}** risk items\n\n"

    for severity in ("critical", "warning", "advisory"):
        items = by_severity[severity]
        if items:
            output += f"### {emojis[severity]} {labels[severity]} ({len(items)})\n\n"
            for item in items:
                output += f"- **[{item['category']}]** {item['description']}\n"
                output += f"  → 💡 {item['suggestion']}\n\n"

    output += ("---\n\n"
               "**⚠️ 以上仅为常见风险模式识别，不构成法律建议。建议委托专业律师进行完整审查。**\n"
               "**⚠️ Preliminary pattern-based scan only. Not legal advice. Consult a qualified attorney.**\n")
    return output


def handle(skill_input: dict) -> dict:
    """
    Main handler.
    skill_input: {"contract_text": "...", "language": "zh|en"}
    """
    contract_text = skill_input.get("contract_text", "")
    if not contract_text or not contract_text.strip():
        return {"ok": False, "error": "未提供合同文本，请提供需要扫描的合同内容。 | No contract text provided."}

    results = scan(contract_text)
    output = format_results(results)

    stats = {
        "total": len(results),
        "critical": len([r for r in results if r["severity"] == "critical"]),
        "warning": len([r for r in results if r["severity"] == "warning"]),
        "advisory": len([r for r in results if r["severity"] == "advisory"]),
    }

    return {"ok": True, "result": output, "stats": stats}


if __name__ == "__main__":
    # Self-test
    test_text_en = (
        "This agreement automatically renews for successive one-year terms unless terminated. "
        "Party A shall have unlimited liability for all damages arising from this agreement. "
        "Payment is due within 90 days of invoice. All work product shall be work-made-for-hire. "
        "The venue shall be determined solely by Party B."
    )
    test_text_zh = (
        "甲乙双方签订本合同，期限三年。合同到期后自动续签一年，除非任一方提前 180 天书面通知。"
        "乙方在工作期间完成的所有工作成果、发明创造和知识产权均归甲方所有。"
        "乙方对工作中可能给甲方造成的任何损失承担无限赔偿责任。"
        "付款期限为到货后 90 天内。争议由甲方所在地人民法院管辖。"
        "双方在合同终止后仍负有永久保密义务。"
    )

    print("=== Contract Risk Helper Self-Test ===\n")
    print("--- English text ---")
    print(format_results(scan(test_text_en)))
    resp = handle({"contract_text": test_text_en})
    print(f"Stats: {resp['stats']}")

    print("\n--- Chinese text ---")
    print(format_results(scan(test_text_zh)))
    resp_zh = handle({"contract_text": test_text_zh})
    print(f"Stats: {resp_zh['stats']}")

    print("\n--- empty text test ---")
    print(handle({"contract_text": ""}))

    print("\n--- no-risk text test ---")
    print(format_results(scan("This is a simple agreement between two parties.")))
