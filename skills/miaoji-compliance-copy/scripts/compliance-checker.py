#!/usr/bin/env python3
"""
Amazon Compliance Checker
Scans listing text for prohibited words, over-marketing language, and policy violations.
Generates replacement suggestions and compliance score.

Usage:
    python compliance-checker.py --title "Best Wireless Earbuds #1 Premium Quality" \
        --bullets "1. Guaranteed 100% satisfaction|2. Free shipping worldwide|3. FDA approved|4. Top rated|5. Cheap price"
    python compliance-checker.py --input '{"title":"...","bullets":["..."]}'
"""

import argparse
import json
import sys
from datetime import datetime


# ── Prohibited Word Lists ────────────────────────────────────────

PROHIBITED_ABSOLUTE = {
    "en": [
        "best", "#1", "number one", "no.1", "top rated", "best seller",
        "amazon choice", "amazon's choice", "amazing", "incredible",
        "guaranteed", "guarantee", "100%", "perfect", "ultimate",
        "cheap", "cheapest", "lowest price", "free shipping",
        "number 1", "first", "leading", "premium quality",
    ],
    "cn": [
        "最好", "第一", "顶级", "最佳", "最强", "最便宜",
        "保证", "100%", "免费送货", "包邮", "最优惠",
        "冠军", "领先", "首选", "独家", "绝无仅有",
    ],
}

PROHIBITED_MEDICAL = {
    "en": [
        "cure", "treat", "heal", "prevent", "diagnose", "therapy",
        "prescription", "clinical", "fda approved", "medical grade",
        "therapeutic", "remedy", "healing",
    ],
    "cn": [
        "治疗", "治愈", "预防", "诊断", "处方", "临床",
        "FDA认证", "医疗级", "疗效", "药效",
    ],
}

PROHIBITED_COMPARATIVE = {
    "en": [
        "better than", "superior to", "compared to competitors",
        "unlike other", "more effective than", "outperforms",
    ],
    "cn": [
        "比...更好", "优于", "超越同类", "比竞品",
    ],
}

REPLACEMENT_SUGGESTIONS = {
    "best": {"suggestion": "high-quality / reliable", "reason": "Absolute claim not allowed"},
    "#1": {"suggestion": "popular / well-regarded", "reason": "Cannot claim ranking"},
    "guaranteed": {"suggestion": "designed to / crafted for", "reason": "Cannot guarantee outcomes"},
    "100%": {"suggestion": "highly / thoroughly", "reason": "Absolute percentage not allowed"},
    "cheap": {"suggestion": "affordable / value-priced", "reason": "'Cheap' implies low quality"},
    "free shipping": {"suggestion": "Remove from listing text (set in shipping settings)", "reason": "Shipping claims go in shipping settings, not listing"},
    "cure": {"suggestion": "support / assist with", "reason": "Medical claims require FDA approval"},
    "treat": {"suggestion": "help with / provide comfort for", "reason": "Medical claims require FDA approval"},
    "fda approved": {"suggestion": "Only use if you have actual FDA clearance documentation", "reason": "False FDA claims lead to listing removal"},
    "better than": {"suggestion": "Compared to standard options / An upgrade from", "reason": "Comparative claims need substantiation"},
    "best seller": {"suggestion": "popular choice / customer favorite", "reason": "Cannot claim badge status"},
    "amazing": {"suggestion": "impressive / notable", "reason": "Over-marketing language"},
    "perfect": {"suggestion": "excellent / well-suited", "reason": "Absolute claim"},
    "ultimate": {"suggestion": "advanced / comprehensive", "reason": "Absolute claim"},
}


def scan_text(text: str, word_list: list, category: str) -> list:
    """Scan text for prohibited words, return matches."""
    text_lower = text.lower()
    matches = []
    for word in word_list:
        if word.lower() in text_lower:
            replacement = REPLACEMENT_SUGGESTIONS.get(word.lower(), {})
            matches.append({
                "word": word,
                "category": category,
                "suggestion": replacement.get("suggestion", "Remove or rephrase"),
                "reason": replacement.get("reason", "Policy violation"),
            })
    return matches


def check_compliance(title: str, bullets: list, lang: str = "en") -> dict:
    """Run full compliance check on listing text."""
    all_text = title + " " + " ".join(bullets)
    all_matches = []

    # Scan each category
    for word_list, category in [
        (PROHIBITED_ABSOLUTE.get(lang, PROHIBITED_ABSOLUTE["en"]), "absolute_claim"),
        (PROHIBITED_MEDICAL.get(lang, PROHIBITED_MEDICAL["en"]), "medical_claim"),
        (PROHIBITED_COMPARATIVE.get(lang, PROHIBITED_COMPARATIVE["en"]), "comparative_claim"),
    ]:
        all_matches.extend(scan_text(all_text, word_list, category))

    # Deduplicate
    seen = set()
    unique_matches = []
    for m in all_matches:
        key = (m["word"], m["category"])
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    # Calculate score
    total_issues = len(unique_matches)
    if total_issues == 0:
        score = 100
    elif total_issues <= 2:
        score = 80
    elif total_issues <= 5:
        score = 60
    else:
        score = max(20, 100 - total_issues * 10)

    # Severity breakdown
    critical = [m for m in unique_matches if m["category"] == "medical_claim"]
    major = [m for m in unique_matches if m["category"] == "absolute_claim"]
    minor = [m for m in unique_matches if m["category"] == "comparative_claim"]

    level = "red" if score < 60 else ("yellow" if score < 85 else "green")

    return {
        "score": score,
        "level": level,
        "total_issues": total_issues,
        "critical_count": len(critical),
        "major_count": len(major),
        "minor_count": len(minor),
        "matches": unique_matches,
        "location_breakdown": {
            "title_issues": len(scan_text(title, PROHIBITED_ABSOLUTE.get(lang, []) + PROHIBITED_MEDICAL.get(lang, []), "any")),
            "bullet_issues": sum(len(scan_text(b, PROHIBITED_ABSOLUTE.get(lang, []) + PROHIBITED_MEDICAL.get(lang, []), "any")) for b in bullets),
        },
    }


def generate_rufus_keywords(title: str, bullets: list, category: str) -> dict:
    """Analyze Rufus search keyword coverage."""
    all_text = (title + " " + " ".join(bullets)).lower()

    scenario_keywords = {
        "use_case": ["for outdoor", "for indoor", "for travel", "for home", "for office", "for gym", "for kids", "for seniors", "for pets", "for camping", "for hiking", "for running", "for cooking", "for cleaning", "for work"],
        "audience": ["for men", "for women", "for beginners", "for professional", "for students", "for elderly"],
        "situation": ["waterproof", "lightweight", "portable", "compact", "durable", "rechargeable", "wireless", "adjustable", "foldable", "noise-cancelling"],
        "compatibility": ["compatible with", "fits", "works with", "suitable for", "designed for", "made for"],
    }

    found = {}
    missing = {}
    for group, keywords in scenario_keywords.items():
        found[group] = [k for k in keywords if k in all_text]
        missing[group] = [k for k in keywords if k not in all_text]

    coverage = sum(len(v) for v in found.values())
    total = sum(len(v) for v in scenario_keywords.values())
    coverage_pct = round(coverage / total * 100, 1) if total > 0 else 0

    return {
        "coverage_percent": coverage_pct,
        "found_keywords": found,
        "missing_keywords": {k: v[:5] for k, v in missing.items() if v},  # Top 5 missing per group
        "rufus_score": min(100, round(coverage_pct * 2)),  # Weighted: 50% coverage = 100 score
    }


def analyze(params: dict) -> dict:
    """Run full compliance + Rufus analysis."""
    title = params.get("title", "")
    bullets_raw = params.get("bullets", [])
    if isinstance(bullets_raw, str):
        bullets = [b.strip() for b in bullets_raw.split("|") if b.strip()]
    else:
        bullets = bullets_raw
    category = params.get("category", "")
    lang = params.get("lang", "en")

    compliance = check_compliance(title, bullets, lang)
    rufus = generate_rufus_keywords(title, bullets, category)

    return {
        "title": title[:80],
        "category": category,
        "compliance": compliance,
        "rufus": rufus,
        "overall_score": round((compliance["score"] * 0.6 + rufus["rufus_score"] * 0.4)),
        "timestamp": datetime.now().isoformat(),
    }


def format_report(result: dict) -> str:
    """Format analysis result as readable report."""
    comp = result["compliance"]
    rufus = result["rufus"]
    level_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

    lines = []
    lines.append("🔍 合规检查报告")
    lines.append("━" * 40)
    lines.append(f"产品：{result['title']}")
    lines.append(f"品类：{result['category']}")
    lines.append(f"综合评分：{result['overall_score']}/100")
    lines.append("")

    # Compliance
    emoji = level_emoji.get(comp["level"], "⚪")
    lines.append(f"📋 合规度：{emoji} {comp['score']}/100")
    lines.append(f"  违规总数：{comp['total_issues']}")
    lines.append(f"  严重（医疗声称）：{comp['critical_count']}")
    lines.append(f"  主要（绝对化用语）：{comp['major_count']}")
    lines.append(f"  次要（对比声称）：{comp['minor_count']}")
    lines.append(f"  标题问题：{comp['location_breakdown']['title_issues']}")
    lines.append(f"  五点问题：{comp['location_breakdown']['bullet_issues']}")

    if comp["matches"]:
        lines.append("")
        lines.append("⚠️ 违规词详情：")
        for m in comp["matches"]:
            sev = {"medical_claim": "🔴", "absolute_claim": "🟡", "comparative_claim": "ℹ️"}.get(m["category"], "⚪")
            lines.append(f"  {sev} 「{m['word']}」→ 建议替换：{m['suggestion']}")
            lines.append(f"     原因：{m['reason']}")

    # Rufus
    lines.append("")
    lines.append(f"🎯 Rufus场景词覆盖：{rufus['coverage_percent']}%")
    lines.append(f"  Rufus适配评分：{rufus['rufus_score']}/100")
    for group, keywords in rufus["found_keywords"].items():
        if keywords:
            lines.append(f"  ✅ {group}：{', '.join(keywords[:3])}")
    for group, keywords in rufus["missing_keywords"].items():
        if keywords:
            lines.append(f"  ❌ {group}缺失：{', '.join(keywords[:3])}")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Amazon Compliance Checker")
    parser.add_argument("--title", required=True, help="Listing title")
    parser.add_argument("--bullets", required=True, help="Bullet points separated by |")
    parser.add_argument("--category", default="", help="Product category")
    parser.add_argument("--lang", default="en", choices=["en", "cn"], help="Language")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--input", type=str, help="JSON string with all parameters")

    args = parser.parse_args()

    if args.input:
        params = json.loads(args.input)
    else:
        params = {
            "title": args.title,
            "bullets": args.bullets,
            "category": args.category,
            "lang": args.lang,
        }

    result = analyze(params)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))


if __name__ == "__main__":
    main()
