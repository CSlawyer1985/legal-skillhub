#!/usr/bin/env python3
"""
Contract Review Skill - CLI Wrapper for OpenClaw Skill Chain
Provides easy-to-use interface for the contract reviewing functionality
"""

import json
import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print('{"error": "Usage: contract-review-skill <path_to_contract> [--industry <industry>] [--format <json|text>]"}')
        sys.exit(1)
    
    target_path = sys.argv[1]
    industry = None
    output_format = "text"  # default
    
    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--industry" and i + 1 < len(sys.argv):
            industry = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--format" and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Read contract content
    try:
        contract_text = Path(target_path).read_text(encoding='utf-8')
    except Exception as e:
        print(json.dumps({"error": f"Failed to read contract file: {str(e)}"}, ensure_ascii=False))
        sys.exit(1)
    
    # Import and run the review engine
    sys.path.insert(0, str(Path(__file__).parent))
    from review_engine import ContractReviewEngine
    
    engine = ContractReviewEngine(Path(__file__).parent / "legal_patterns")
    result = engine.review_contract(contract_text, industry)
    
    # Output as requested format
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Format as human-readable report
        print(format_report(result, Path(target_path).name))

def format_report(report: dict, contract_name: str) -> str:
    """Format review results as human-readable report."""
    findings = report.get("findings", [])
    risk_score = report.get("risk_score", 0)
    summary = report.get("summary", {})
    
    # Determine risk level label (lower score means higher risk)
    if risk_score >= 80:
        risk_label = "LOW"
    elif risk_score >= 60:
        risk_label = "MEDIUM"
    elif risk_score >= 40:
        risk_label = "HIGH"
    else:
        risk_label = "CRITICAL"
    
    # Count by risk level
    by_level = summary.get("by_risk_level", {"critical": 0, "high": 0, "medium": 0, "low": 0})
    critical_count = by_level.get("critical", 0)
    high_count = by_level.get("high", 0)
    medium_count = by_level.get("medium", 0)
    low_count = by_level.get("low", 0)
    
    lines = [
        "=" * 60,
        "CONTRACT REVIEW REPORT",
        "=" * 60,
        f"Contract: {contract_name}",
        f"Overall Risk Score: {risk_score}/100 ({risk_label})",
        "Risk Distribution:",
        f"  - Critical: {critical_count} clauses",
        f"  - High: {high_count} clauses",
        f"  - Medium: {medium_count} clauses",
        f"  - Low: {low_count} clauses",
        ""
    ]
    
    if findings:
        lines.append("Top Risk Findings:")
        # Sort findings by risk level (critical first)
        risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(findings, key=lambda f: risk_order.get(f["risk_level"], 4))
        
        for finding in sorted_findings[:5]:  # Show top 5
            risk_level = finding['risk_level']
            if hasattr(risk_level, 'value'):
                risk_level_str = risk_level.value.upper()
            else:
                risk_level_str = str(risk_level).upper()
            lines.append(f"  [{risk_level_str}] {finding['title']}")
            lines.append(f"    Location: {finding['location']}")
            lines.append(f"    Issue: {finding['description']}")
            lines.append(f"    Suggestion: {finding['suggestion']}")
            if finding.get("reference"):
                lines.append(f"    Reference: {finding['reference']}")
            lines.append("")
        
        if len(findings) > 5:
            lines.append(f"  ... and {len(findings) - 5} more findings")
            lines.append("")
    
    lines.append("Recommendations:")
    if critical_count > 0:
        lines.append("  1. [CRITICAL] Address all critical risk items immediately - do not sign without legal review")
    if high_count > 0:
        lines.append("  2. [HIGH] Address high risk items before signing or seek legal counsel")
    if medium_count > 0:
        lines.append("  3. [MEDIUM] Consider negotiating medium risk clauses based on your leverage position")
    if low_count > 0:
        lines.append("  4. [LOW] Minor items - standard business practice")
    
    if critical_count == 0 and high_count == 0 and medium_count == 0:
        lines.append("  [LOW] No significant risks identified - contract appears reasonably balanced")
    
    lines.extend([
        "",
        "=" * 60
    ])
    
    return "\n".join(lines)

if __name__ == "__main__":
    main()