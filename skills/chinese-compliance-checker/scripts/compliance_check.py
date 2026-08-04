#!/usr/bin/env python3
"""
Global Compliance Quick Checker
Quick scan of product profile against key regulations.

Usage:
  python compliance_check.py --product "SaaS App" --markets EU,US,JP --data "personal,payment,behavioral" --ai yes --ugc yes --children no
"""

import argparse
import json
import sys


# Regulation applicability rules
REGULATIONS = {
    "EU": {
        "GDPR": {
            "triggers": ["personal"],
            "always": True,
            "risk": "critical",
            "max_penalty": "€20M or 4% global revenue",
            "key_requirements": [
                "Lawful basis for processing",
                "Privacy policy in local language",
                "Data Protection Officer (DPO)",
                "Data Protection Impact Assessment (DPIA)",
                "72-hour breach notification",
                "Right to erasure / portability",
                "Standard Contractual Clauses for cross-border transfer",
                "Cookie consent banner"
            ]
        },
        "DSA": {
            "triggers": ["ugc"],
            "always": False,
            "risk": "high",
            "max_penalty": "6% global revenue",
            "key_requirements": [
                "Illegal content reporting mechanism",
                "Transparency reporting",
                "Risk assessment for systemic risks",
                "24-hour content takedown capability"
            ]
        },
        "AI Act": {
            "triggers": ["ai"],
            "always": False,
            "risk": "high",
            "max_penalty": "€35M or 7% revenue",
            "key_requirements": [
                "AI risk classification",
                "Transparency obligations",
                "Human oversight mechanisms",
                "Bias testing documentation"
            ]
        },
        "PSD2": {
            "triggers": ["payment"],
            "always": False,
            "risk": "critical",
            "max_penalty": "Operating license required",
            "key_requirements": [
                "Payment institution license",
                "Strong Customer Authentication (SCA)",
                "Fund segregation"
            ]
        }
    },
    "US": {
        "CCPA": {
            "triggers": ["personal"],
            "always": True,
            "risk": "high",
            "max_penalty": "$7,500 per intentional violation",
            "key_requirements": [
                "Do Not Sell link",
                "Right to delete",
                "Privacy policy update",
                "Opt-out of data sharing",
                "Consumer data inventory"
            ]
        },
        "COPPA": {
            "triggers": ["children"],
            "always": False,
            "risk": "critical",
            "max_penalty": "$50,120 per violation",
            "key_requirements": [
                "Parental consent before data collection",
                "Data minimization",
                "Retention limits",
                "Age verification gate"
            ]
        },
        "State AI Laws": {
            "triggers": ["ai"],
            "always": False,
            "risk": "medium",
            "max_penalty": "Varies by state",
            "key_requirements": [
                "AI impact assessment (CO, IL)",
                "Transparency in AI decisions",
                "Bias testing (TX)"
            ]
        }
    },
    "JP": {
        "APPI": {
            "triggers": ["personal"],
            "always": True,
            "risk": "high",
            "max_penalty": "¥100M",
            "key_requirements": [
                "Purpose specification",
                "Consent for sensitive data",
                "Cross-border transfer assessment",
                "Privacy policy in Japanese"
            ]
        },
        "Payment Services Act": {
            "triggers": ["payment"],
            "always": False,
            "risk": "critical",
            "max_penalty": "Criminal penalties",
            "key_requirements": [
                "Payment services registration",
                "Fund segregation",
                "Client asset management"
            ]
        }
    },
    "SG": {
        "PDPA": {
            "triggers": ["personal"],
            "always": True,
            "risk": "high",
            "max_penalty": "S$1M",
            "key_requirements": [
                "Consent for collection/use/disclosure",
                "DPIA for high-risk processing",
                "Cross-border transfer assessment",
                "Data breach notification"
            ]
        }
    },
    "VN": {
        "Cybersecurity Law": {
            "triggers": ["personal"],
            "always": True,
            "risk": "critical",
            "max_penalty": "Business suspension",
            "key_requirements": [
                "Data localization for certain services",
                "24-hour illegal content removal",
                "Local representative office",
                "User identity verification"
            ]
        }
    },
    "SA": {
        "PDPL": {
            "triggers": ["personal"],
            "always": True,
            "risk": "high",
            "max_penalty": "SAR 5M",
            "key_requirements": [
                "Consent for processing",
                "Data localization for certain sectors",
                "Breach notification within 72h",
                "Arabic language interface"
            ]
        }
    }
}

# Data categories and their risk levels
DATA_RISKS = {
    "personal": "medium",
    "payment": "critical",
    "location": "high",
    "health": "critical",
    "children": "critical",
    "biometric": "critical",
    "behavioral": "high",
    "financial": "critical",
    "communication": "medium"
}


def run_check(product_type: str, markets: list, data_types: list, has_ai: bool, has_ugc: bool, has_children: bool) -> dict:
    """Run compliance check against product profile."""
    
    # Normalize data types
    all_data = set(data_types)
    if has_ai:
        all_data.add("ai")
    if has_ugc:
        all_data.add("ugc")
    if has_children:
        all_data.add("children")
    
    report = {
        "product_type": product_type,
        "target_markets": markets,
        "data_categories": list(all_data),
        "applicable_regulations": [],
        "critical_issues": [],
        "high_issues": [],
        "medium_issues": [],
        "overall_risk": "green"
    }
    
    for market in markets:
        market_regs = REGULATIONS.get(market, {})
        for reg_name, reg_info in market_regs.items():
            applies = reg_info.get("always", False)
            if not applies:
                for trigger in reg_info.get("triggers", []):
                    if trigger in all_data:
                        applies = True
                        break
            
            if applies:
                entry = {
                    "market": market,
                    "regulation": reg_name,
                    "risk_level": reg_info["risk"],
                    "max_penalty": reg_info["max_penalty"],
                    "requirements": reg_info["key_requirements"],
                    "requirements_count": len(reg_info["key_requirements"])
                }
                report["applicable_regulations"].append(entry)
                
                if reg_info["risk"] == "critical":
                    report["critical_issues"].append(f"{market} - {reg_name}")
                    report["overall_risk"] = "red"
                elif reg_info["risk"] == "high" and report["overall_risk"] != "red":
                    report["overall_risk"] = "yellow"
                    report["high_issues"].append(f"{market} - {reg_name}")
    
    # Data risk assessment
    report["data_risk_assessment"] = {}
    for dt in data_types:
        risk = DATA_RISKS.get(dt, "low")
        report["data_risk_assessment"][dt] = risk
        if risk == "critical":
            report["critical_issues"].append(f"Data category: {dt} (critical risk)")
    
    # China outbound data transfer check
    if "personal" in data_types or "payment" in data_types:
        report["china_outbound_transfer"] = {
            "required": True,
            "mechanisms": [
                "CAC Security Assessment (for CIIOs or 1M+ users)",
                "Standard Contract (for general personal info)",
                "PIPC Certification (alternative path)"
            ],
            "note": "Must complete Data Outbound Transfer Impact Assessment (数据出境影响评估)"
        }
    
    # Summary
    total_reqs = sum(r["requirements_count"] for r in report["applicable_regulations"])
    report["summary"] = {
        "total_regulations": len(report["applicable_regulations"]),
        "total_requirements": total_reqs,
        "critical_count": len(report["critical_issues"]),
        "high_count": len(report["high_issues"]),
        "estimated_remediation_weeks": max(2, total_reqs // 5),
        "estimated_cost_range": "$10K-$50K" if total_reqs < 20 else "$50K-$100K+"
    }
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Global Compliance Quick Checker")
    parser.add_argument("--product", required=True, help="Product type (e.g., 'SaaS App', 'Mobile App')")
    parser.add_argument("--markets", required=True, help="Comma-separated markets (EU,US,JP,SG,VN,SA)")
    parser.add_argument("--data", required=True, help="Comma-separated data types (personal,payment,location,health,children,biometric,behavioral,financial,communication)")
    parser.add_argument("--ai", default="no", help="Has AI/ML features (yes/no)")
    parser.add_argument("--ugc", default="no", help="Has user-generated content (yes/no)")
    parser.add_argument("--children", default="no", help="May have child users (yes/no)")
    
    args = parser.parse_args()
    
    markets = [m.strip().upper() for m in args.markets.split(",")]
    data_types = [d.strip().lower() for d in args.data.split(",")]
    has_ai = args.ai.lower() in ("yes", "true", "1")
    has_ugc = args.ugc.lower() in ("yes", "true", "1")
    has_children = args.children.lower() in ("yes", "true", "1")
    
    report = run_check(args.product, markets, data_types, has_ai, has_ugc, has_children)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
