#!/usr/bin/env python3
"""
Contract Review Engine - Core logic for analyzing contracts and identifying risks, missing clauses, and compliance issues.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ReviewFinding:
    id: str
    title: str
    description: str
    risk_level: RiskLevel
    category: str  # e.g., "Risk Clause", "Missing Clause", "Compliance"
    location: str  # e.g., "Section 5.2", "Line 45"
    suggestion: str
    reference: Optional[str] = None  # e.g., "Civil Code Article 496"

class ContractReviewEngine:
    def __init__(self, patterns_dir: Path):
        self.patterns_dir = patterns_dir
        self.high_risk_patterns = self._load_patterns("high_risk.json")
        self.required_clauses = self._load_patterns("required_clauses.json")
        self.industry_patterns = {}  # Can be extended for industry-specific rules
        
    def _load_patterns(self, filename: str) -> Dict[str, Any]:
        """Load pattern JSON file from patterns directory."""
        file_path = self.patterns_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def review_contract(self, contract_text: str, industry: str = None) -> Dict[str, Any]:
        """
        Main review function.
        Returns a dictionary with review results.
        """
        findings = []
        
        # 1. Check for high-risk clauses
        findings.extend(self._check_high_risk_clauses(contract_text))
        
        # 2. Check for missing required clauses
        findings.extend(self._check_required_clauses(contract_text))
        
        # 3. Industry-specific checks (if industry specified)
        if industry:
            findings.extend(self._check_industry_specific(contract_text, industry))
        
        # 4. Calculate overall risk score
        risk_score = self._calculate_risk_score(findings)
        
        # 5. Generate summary
        summary = self._generate_summary(findings)
        
        findings_list = []
        for f in findings:
            f_dict = asdict(f)
            # Convert Enum to string for JSON serialization
            if isinstance(f_dict['risk_level'], RiskLevel):
                f_dict['risk_level'] = f_dict['risk_level'].value
            findings_list.append(f_dict)
        return {
            "findings": findings_list,
            "risk_score": risk_score,
            "summary": summary,
            "metadata": {
                "total_clauses_checked": len(self.high_risk_patterns) + len(self.required_clauses),
                "industry": industry or "general",
                "engine_version": "1.0.0"
            }
        }
    
    def _check_high_risk_clauses(self, text: str) -> List[ReviewFinding]:
        """Scan for high-risk clause patterns."""
        findings = []
        for pattern_id, pattern_data in self.high_risk_patterns.items():
            pattern = pattern_data.get("pattern", "")
            if not pattern:
                continue
            
            # Simple regex search - in production, might use more sophisticated NLP
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # Approximate location (line number)
                line_number = text[:match.start()].count('\n') + 1
                
                findings.append(ReviewFinding(
                    id=f"HR-{pattern_id}-{len(findings)+1:03d}",
                    title=pattern_data.get("title", "High Risk Clause Detected"),
                    description=pattern_data.get("description", "Potentially problematic clause detected"),
                    risk_level=RiskLevel[pattern_data.get("risk_level", "HIGH").upper()],
                    category="Risk Clause",
                    location=f"Line {line_number}",
                    suggestion=pattern_data.get("suggestion", "Review this clause with legal counsel"),
                    reference=pattern_data.get("reference")
                ))
        return findings
    
    def _check_required_clauses(self, text: str) -> List[ReviewFinding]:
        """Check for presence of required clauses."""
        findings = []
        for clause_id, clause_data in self.required_clauses.items():
            pattern = clause_data.get("pattern", "")
            if not pattern:
                continue
            
            # Check if pattern exists in text
            if not re.search(pattern, text, re.IGNORECASE):
                findings.append(ReviewFinding(
                    id=f"RC-{clause_id}-{len(findings)+1:03d}",
                    title=clause_data.get("title", "Missing Required Clause"),
                    description=clause_data.get("description", "Important clause may be missing"),
                    risk_level=RiskLevel[clause_data.get("risk_level", "MEDIUM").upper()],
                    category="Missing Clause",
                    location="Not found in contract",
                    suggestion=clause_data.get("suggestion", "Consider adding this clause"),
                    reference=clause_data.get("reference")
                ))
        return findings
    
    def _check_industry_specific(self, text: str, industry: str) -> List[ReviewFinding]:
        """Apply industry-specific rules."""
        # This would be extended with industry-specific pattern files
        # For now, return empty list as placeholder
        return []
    
    def _calculate_risk_score(self, findings: List[ReviewFinding]) -> int:
        """Calculate overall risk score (0-100, lower is better)."""
        if not findings:
            return 10  # Low risk if no issues found
        
        # Weight by risk level
        weights = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 15,
            RiskLevel.MEDIUM: 8,
            RiskLevel.LOW: 3
        }
        
        total_penalty = sum(weights[f.risk_level] for f in findings)
        # Cap the penalty at 90 to keep minimum score at 10
        penalty = min(total_penalty, 90)
        return 10 + penalty  # Score range 10-100
    
    def _generate_summary(self, findings: List[ReviewFinding]) -> Dict[str, Any]:
        """Generate summary statistics."""
        counts = {
            "critical": len([f for f in findings if f.risk_level == RiskLevel.CRITICAL]),
            "high": len([f for f in findings if f.risk_level == RiskLevel.HIGH]),
            "medium": len([f for f in findings if f.risk_level == RiskLevel.MEDIUM]),
            "low": len([f for f in findings if f.risk_level == RiskLevel.LOW])
        }
        
        categories = {}
        for f in findings:
            cat = f.category
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "by_risk_level": counts,
            "by_category": categories,
            "total_findings": len(findings)
        }

def main():
    """Simple test function."""
    # This would be replaced by the CLI wrapper
    sample_contract = """
    SERVICE AGREEMENT
    
    This Agreement is made between Party A and Party B.
    
    Section 1: Services
    Party A shall provide services as described in Exhibit A.
    
    Section 2: Payment
    Party B shall pay Party A $1000 per month.
    
    Section 8: Modification
    Either party may amend this agreement at any time by providing written notice to the other party.
    
    Section 12: Term and Termination
    This agreement shall remain in effect until terminated by either party.
    """
    
    engine = ContractReviewEngine(Path("legal_patterns"))
    result = engine.review_contract(sample_contract)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()