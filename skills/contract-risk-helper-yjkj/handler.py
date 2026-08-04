#!/usr/bin/env python3
"""
Contract Risk Helper - handler.py
Read-only local analysis. No network, no exec, no credential access.
"""

import re


RISK_PATTERNS = [
    # Critical - Liability
    {
        "category": "Liability",
        "severity": "critical",
        "pattern": re.compile(r"unlimited liability|liability for all damages|no limit on liability", re.I),
        "description": "Unlimited liability clause — no financial cap on exposure",
        "suggestion": "Negotiate a liability cap (e.g., 12 months of fees or contract value)"
    },
    {
        "category": "Liability",
        "severity": "critical",
        "pattern": re.compile(r"indemnify.*any and all claims|hold harmless.*any and all", re.I),
        "description": "Broad indemnification obligation — one-sided with no carve-outs",
        "suggestion": "Limit indemnification to direct damages caused by the indemnifying party's actions"
    },
    # Critical - Termination
    {
        "category": "Termination",
        "severity": "critical",
        "pattern": re.compile(r"may not be terminated|termination only for cause|no right to terminate", re.I),
        "description": "No termination for convenience — no exit without breach",
        "suggestion": "Add termination for convenience with reasonable notice (30-90 days)"
    },
    {
        "category": "Termination",
        "severity": "critical",
        "pattern": re.compile(r"automatically renew|auto-renew|automatic renewal|successive one-year", re.I),
        "description": "Automatic renewal without active renewal decision",
        "suggestion": "Ensure 30-60 day notice requirement before renewal; add opt-out clause"
    },
    {
        "category": "Dispute",
        "severity": "critical",
        "pattern": re.compile(r"venue shall be|jurisdiction shall be|exclusive jurisdiction", re.I),
        "description": "Exclusive venue/jurisdiction clause — verify fairness",
        "suggestion": "Negotiate neutral venue or your home jurisdiction"
    },
    # Warning - Payment
    {
        "category": "Payment",
        "severity": "warning",
        "pattern": re.compile(r"payment.*(?:due|within).*\d+\s*days|net\s*[6-9]\d", re.I),
        "description": "Extended payment terms (60+ days)",
        "suggestion": "Negotiate standard net 30 terms or request early payment discount"
    },
    {
        "category": "Payment",
        "severity": "warning",
        "pattern": re.compile(r"no.*late.*payment.*penalty|no.*penalty.*late", re.I),
        "description": "No penalty for late payment",
        "suggestion": "Add late fee clause (e.g., 1.5% per month on overdue amounts)"
    },
    # Warning - IP
    {
        "category": "Intellectual Property",
        "severity": "warning",
        "pattern": re.compile(r"work[-\s]?made[-\s]?for[-\s]?hire|work[-\s]?for[-\s]?hire|work for hire", re.I),
        "description": "Work-for-hire clause — may transfer all background IP",
        "suggestion": "Limit to specific project deliverables; carve out pre-existing IP"
    },
    {
        "category": "Intellectual Property",
        "severity": "warning",
        "pattern": re.compile(r"assigns? all rights|all inventions|all intellectual property", re.I),
        "description": "Broad IP assignment — no limitation to project scope",
        "suggestion": "Limit assignment to inventions conceived specifically during this project"
    },
    # Warning - Termination details
    {
        "category": "Termination",
        "severity": "warning",
        "pattern": re.compile(r"notice.*180 days|notice.*six months|termination fee.*total|early termination.*all fees", re.I),
        "description": "Excessive termination notice period or prohibitive exit fee",
        "suggestion": "Reduce notice to 30-60 days; negotiate reasonable prorated termination fee"
    },
    # Warning - Confidentiality
    {
        "category": "Confidentiality",
        "severity": "warning",
        "pattern": re.compile(r"perpetual confidentiality|perpetuity|indefinite.*confidential|survive forever", re.I),
        "description": "Indefinite confidentiality obligation — never expires",
        "suggestion": "Limit confidentiality term to 3-5 years after contract termination"
    },
    {
        "category": "Confidentiality",
        "severity": "warning",
        "pattern": re.compile(r"return.*confidential|destroy.*confidential", re.I),
        "description": "No obligation to return or destroy confidential information",
        "suggestion": "Add clause requiring return or certified destruction upon termination"
    },
    # Warning - Dispute
    {
        "category": "Dispute",
        "severity": "warning",
        "pattern": re.compile(r"prevailing party.*attorney.*fee|attorney.*fee.*prevailing", re.I),
        "description": "One-sided attorney fee provision",
        "suggestion": "Make mutual — each party bears its own costs, or prevailing party recovers fees"
    },
    # Advisory
    {
        "category": "Payment",
        "severity": "advisory",
        "pattern": re.compile(r"payment upon completion|upon completion.*payment", re.I),
        "description": "Unclear payment trigger — no milestone definition",
        "suggestion": "Define specific milestones or deliverables that trigger payment obligations"
    },
    {
        "category": "Service",
        "severity": "advisory",
        "pattern": re.compile(r"sole discretion|reasonably determined|solely at.*discretion", re.I),
        "description": "Vague scope — allows unilateral expansion",
        "suggestion": "Define specific deliverables with measurable acceptance criteria"
    },
    {
        "category": "Service",
        "severity": "advisory",
        "pattern": re.compile(r"no service level|no uptime|without.*guarantee", re.I),
        "description": "No service level or performance guarantee",
        "suggestion": "Add SLA with remedies (credits or termination right) for missed targets"
    },
]


def scan(text: str) -> list:
    """Scan contract text for risk patterns. Pure read-only."""
    if not text or not isinstance(text, str) or not text.strip():
        return []

    results = []
    for item in RISK_PATTERNS:
        match = item["pattern"].search(text)
        if match:
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].strip()
            results.append({
                "category": item["category"],
                "severity": item["severity"],
                "matched": match.group(),
                "context": context[:120],
                "description": item["description"],
                "suggestion": item["suggestion"]
            })
    return results


def format_results(results: list) -> str:
    """Format scan results as readable text."""
    if not results:
        return ("✅ 未发现已知风险模式。\n\n"
                "（此扫描仅针对常见已知风险模式，不能替代专业法律审查）\n")

    by_severity = {"critical": [], "warning": [], "advisory": []}
    for r in results:
        by_severity[r["severity"]].append(r)

    emojis = {"critical": "🔴", "warning": "🟡", "advisory": "🟢"}
    labels = {"critical": "严重", "warning": "警告", "advisory": "提醒"}

    output = f"## 合同风险扫描结果\n\n共发现 **{len(results)}** 个风险项\n\n"

    for severity in ("critical", "warning", "advisory"):
        items = by_severity[severity]
        if items:
            output += f"### {emojis[severity]} {labels[severity]} ({len(items)})\n\n"
            for item in items:
                output += f"- **[{item['category']}]** {item['description']}\n"
                output += f"  → {item['suggestion']}\n\n"

    output += ("---\n\n"
               "**⚠️ 以上仅为常见风险模式识别，不构成法律建议。\n"
               "建议委托专业律师进行完整审查。**\n")
    return output


def handle(skill_input: dict) -> dict:
    """
    Main handler.
    skill_input: {"contract_text": "...", "language": "zh"}
    """
    contract_text = skill_input.get("contract_text", "")
    if not contract_text or not contract_text.strip():
        return {"ok": False, "error": "未提供合同文本，请提供需要扫描的合同内容。"}

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
    test_text = (
        "This agreement automatically renews for successive one-year terms unless terminated. "
        "Party A shall have unlimited liability for all damages arising from this agreement. "
        "Payment is due within 90 days of invoice. All work product shall be work-made-for-hire. "
        "The venue shall be determined solely by Party B."
    )

    print("=== Contract Risk Helper Self-Test ===\n")
    results = scan(test_text)
    print(format_results(results))

    resp = handle({"contract_text": test_text})
    print(f"Stats: {resp['stats']}")

    print("\n--- empty text test ---")
    resp2 = handle({"contract_text": ""})
    print(resp2)

    print("\n--- no-risk text test ---")
    resp3 = handle({"contract_text": "This is a simple agreement between two parties."})
    print(format_results(scan("This is a simple agreement between two parties.")))
