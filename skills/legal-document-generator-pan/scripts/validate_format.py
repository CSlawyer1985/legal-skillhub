#!/usr/bin/env python3
"""
Legal Document Format Validator

Validates Chinese legal documents against standard formatting requirements.
"""

import re
from typing import Dict, List, Optional


class LegalDocumentValidator:
    """Validate Chinese legal document format and content"""

    def __init__(self, document_text: str):
        self.text = document_text
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def validate_contract(self) -> bool:
        """Validate contract document structure"""
        issues = []

        # Check for required sections
        if not self._find_header():
            issues.append("Missing document header with title/date")

        if not self._find_parties():
            issues.append("Missing parties section (甲乙方信息)")

        if not self._find_signature_block():
            issues.append("Missing signature block (签署栏)")

        # Check for article numbering
        if not self._find_articles():
            issues.append("No article numbering found (e.g., 第一条, 第二条)")

        self.issues.extend(issues)
        return len(issues) == 0

    def validate_litigation_document(self) -> bool:
        """Validate civil/criminal litigation document"""
        issues = []

        # Check for court name
        if not self._find_court():
            issues.append("Missing court name (法院名称)")

        # Check for plaintiff/defendant
        if not self._find_litigation_parties():
            issues.append("Missing plaintiff or defendant information")

        # Check for claims
        if not self._find_claims():
            issues.append("Missing claims or requests section")

        # Check for factual background
        if not self._find_facts():
            issues.append("Missing factual background section")

        # Check for legal basis
        if not self._find_legal_basis():
            issues.append("Missing legal basis citations")

        self.issues.extend(issues)
        return len(issues) == 0

    def validate_legal_opinion(self) -> bool:
        """Validate legal opinion letter"""
        issues = []

        # Check for recipient
        if not self._find_recipient():
            issues.append("Missing recipient/client information")

        # Check for opinion section
        if not self._find_opinion_statement():
            issues.append("Missing clear opinion statement")

        # Check for legal basis
        if not self._find_legal_basis():
            issues.append("Missing legal citations in opinion")

        self.issues.extend(issues)
        return len(issues) == 0

    def validate_legal_citations(self) -> Dict[str, List[str]]:
        """Extract and validate legal citations"""
        citations = {
            'civil_code': [],
            'criminal_law': [],
            'procedural_law': []
        }

        # Pattern for legal citations
        patterns = {
            '民法典': 'civil_code',
            '刑法': 'criminal_law',
            '刑事诉讼法': 'procedural_law',
            '民事诉讼法': 'procedural_law',
        }

        for term, category in patterns.items():
            matches = re.findall(rf'{term}[第\s]*(\d+)[条、]', self.text)
            citations[category].extend(matches)

        return citations

    def _find_header(self) -> bool:
        """Check for document header"""
        return bool(re.search(r'(合同|协议|起诉状|答辩状|意见书)', self.text[:500]))

    def _find_parties(self) -> bool:
        """Check for parties in contract"""
        return bool(re.search(r'甲方[：:].*乙方[：:]', self.text))

    def _find_signature_block(self) -> bool:
        """Check for signature section"""
        return bool(re.search(r'(甲方.*签字|签署人|盖章)', self.text))

    def _find_articles(self) -> bool:
        """Check for article numbering"""
        return bool(re.search(r'第[一二三四五六七八九十\d]+[条]', self.text))

    def _find_court(self) -> bool:
        """Check for court name"""
        return bool(re.search(r'(人民法院|法院)', self.text))

    def _find_litigation_parties(self) -> bool:
        """Check for plaintiff/defendant"""
        return bool(re.search(r'(原告|被告|申请人|被申请人)', self.text))

    def _find_claims(self) -> bool:
        """Check for claims/requests"""
        return bool(re.search(r'(诉讼请求|请求|诉求)', self.text))

    def _find_facts(self) -> bool:
        """Check for factual background"""
        return bool(re.search(r'(事实与理由|案件事实|事实|案情)', self.text))

    def _find_legal_basis(self) -> bool:
        """Check for legal citations"""
        patterns = [
            r'(民法典|刑法|诉讼法)',
            r'第\d+条',
            r'法律规定',
            r'依据.*法'
        ]
        return any(re.search(p, self.text) for p in patterns)

    def _find_recipient(self) -> bool:
        """Check for opinion letter recipient"""
        return bool(re.search(r'(致|收件人|客户)', self.text))

    def _find_opinion_statement(self) -> bool:
        """Check for opinion statement"""
        return bool(re.search(r'(本律师认为|意见如下|结论|建议)', self.text))

    def get_report(self) -> str:
        """Generate validation report"""
        report = ["=" * 50, "Legal Document Validation Report", "=" * 50]

        if self.issues:
            report.append("\n[Issues Found]")
            for issue in self.issues:
                report.append(f"  ✗ {issue}")
        else:
            report.append("\n✓ No major issues found")

        if self.warnings:
            report.append("\n[Warnings]")
            for warning in self.warnings:
                report.append(f"  ! {warning}")

        # Add citation summary
        citations = self.validate_legal_citations()
        report.append("\n[Legal Citations]")
        for category, articles in citations.items():
            if articles:
                report.append(f"  {category}: {', '.join(articles)}")

        report.append("\n" + "=" * 50)
        return "\n".join(report)


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: validate_format.py <document_file> [--type contract|litigation|opinion]")
        sys.exit(1)

    file_path = sys.argv[1]
    doc_type = sys.argv[2] if len(sys.argv) > 2 else 'contract'

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    validator = LegalDocumentValidator(text)

    if doc_type == 'contract':
        result = validator.validate_contract()
    elif doc_type == 'litigation':
        result = validator.validate_litigation_document()
    elif doc_type == 'opinion':
        result = validator.validate_legal_opinion()
    else:
        print(f"Unknown document type: {doc_type}")
        sys.exit(1)

    print(validator.get_report())
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
