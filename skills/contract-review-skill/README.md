# Contract Review Skill

An OpenClaw skill for AI-powered contract analysis and review. Identifies risky clauses, missing provisions, and compliance issues in legal documents.

## Features

- 📄 **Contract Analysis**: Parses and analyzes various contract formats (text, markdown, PDF via external tools)
- ⚠️ **Risk Clause Detection**: Identifies high-risk clauses such as unilateral modification, automatic renewal, excessive liability, etc.
- ✅ **Required Clause Checking**: Verifies presence of essential clauses like confidentiality, IP, termination, dispute resolution
- 🏢 **Industry-Specific Rules**: Customizable checks for different industries (tech, healthcare, finance, construction, etc.)
- 📊 **Risk Scoring**: Provides overall contract risk score with detailed breakdown
- 📝 **Remediation Suggestions**: Offers specific language improvements and negotiation points
- 📋 **Report Generation**: Creates structured reports in JSON and human-readable formats

## Installation

```bash
clawhub install contract-review-skill
```

## Usage

### Basic Contract Review

```bash
# Review a contract text file
contract-review-skill ./contract.txt

# Review a markdown contract
contract-review-skill ./agreement.md
```

### With Custom Options

```bash
# Specify industry focus
contract-review-skill ./contract.txt --industry tech

# Output JSON format for integration
contract-review-skill ./contract.txt --format json
```

## Output Example

```
============================================================
CONTRACT REVIEW REPORT
============================================================
Contract: service_agreement.txt
Overall Risk Score: 68/100 (MEDIUM-HIGH)
Risk Distribution:
  - High Risk: 3 clauses
  - Medium Risk: 5 clauses  
  - Low Risk: 8 clauses
  - Compliant: 12 clauses

Top Risk Findings:
  [HIGH] Unilateral Modification Clause
    Location: Section 8.2 (Page 4)
    Issue: Party A may modify terms without Party B's consent
    Suggestion: Require mutual agreement for any modifications
    Reference: Contract Law Principle of Mutuality

  [HIGH] Automatic Renewal without Notice
    Location: Section 12.1 (Page 6)  
    Issue: Contract renews annually without prior notice requirement
    Suggestion: Add 30-60 day notice period for non-renewal
    Reference: Consumer Protection Regulations

  [MEDIUM] Missing Confidentiality Clause
    Location: Not found in contract
    Issue: No explicit confidentiality obligations defined
    Suggestion: Add standard NDA clause covering proprietary information
    Reference: Standard Business Practice

Recommendations:
  1. Address all HIGH risk items before signing
  2. Consider negotiating MEDIUM risk clauses based on leverage
  3. Have legal counsel review final revised version
============================================================
```

## Configuration

The skill can be customized by:

1. **Modifying Pattern Files**: Update JSON files in `legal_patterns/` directory
2. **Adding Industry Templates**: Create new industry-specific rule sets
3. **Adjusting Risk Weights**: Modify scoring algorithm in `review_engine.py`

## Requirements

- Python 3.7+
- No external dependencies for core functionality (uses standard library)
- Optional: `pypdf` or `pdfplumber` for PDF contract support (install via pip if needed)

## Security Notes

- This skill processes contract text locally - no data leaves your machine
- For highly sensitive contracts, consider running in air-gapped environment
- The skill does not provide legal advice - consult qualified attorney for binding decisions

## License

MIT

## Author

laosi (did:soul:laosi)