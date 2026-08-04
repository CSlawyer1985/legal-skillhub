---
name: compliance-audit-assistant
description: Security and compliance auditing tool for AI agents. Scans code for vulnerabilities, checks GDPR/CCPA compliance, generates risk reports with remediation guidance.
metadata: {"primaryCategory": "Security","categories": ["Security","Agents","Development"],"tags": ["security","compliance","audit","gdpr","privacy","vulnerability-scan","ai-agent","safety"]}
---

# AI Agent Compliance Assistant

A comprehensive security and compliance auditing tool designed specifically for AI agents in the OpenClaw/ClawHub ecosystem.

## What It Does

### 🔍 Security Scanning
- **Code Injection Detection**: Identifies dangerous `eval()`, `exec()`, `compile()` usage
- **Command Injection Detection**: Finds `os.system()`, `subprocess.Popen()` calls
- **Unsafe Deserialization**: Detects `pickle.loads()`, `yaml.load()` patterns
- **Hardcoded Secrets**: Flags passwords, API keys embedded in source code
- **Risk Scoring**: Calculates 0-100 risk score based on severity and count

### 📋 Compliance Checking
- **GDPR Compliance**: Data protection, consent verification, cross-border transfer checks
- **CCPA Compliance**: California consumer privacy regulation alignment
- **Data Minimization**: Ensures only necessary personal data is collected
- **Privacy by Design**: Evaluates privacy-first architecture patterns

### 📊 Report Generation
- **HTML Reports**: Rich interactive vulnerability reports
- **JSON Output**: Machine-readable results for CI/CD integration
- **Summary View**: Quick executive summary with key metrics
- **Remediation Guidance**: Specific fix recommendations for each finding

## When to Use This Skill

Use this skill when you need to:
- Audit an AI agent or skill before deployment
- Check code for security vulnerabilities
- Verify compliance with data protection regulations
- Generate audit reports for stakeholders
- Integrate security scanning into your development pipeline

## How It Works

1. **Input**: Provide agent/skill code (Python, JavaScript, TypeScript)
2. **Analysis**: Multi-pattern scanning engine checks for known vulnerability types
3. **Scoring**: Risk score calculated based on severity weights
4. **Output**: Detailed report with findings and remediation steps

## Example Usage

### Basic Scan
```
Scan this Python code for security issues:

import os
import pickle

def process_user_input():
    cmd = input("Enter command: ")
    os.system(cmd)
    
data = pickle.loads(user_data)
return eval(expression)
```

### Expected Output
```
Risk Score: 65/100 (WARNING)

Vulnerabilities Found:
1. CRITICAL - Command Injection (Line 5)
   Issue: os.system() with user input
   Fix: Use subprocess.run() with explicit arguments list

2. HIGH - Unsafe Deserialization (Line 8)
   Issue: pickle.loads() on untrusted data
   Fix: Use JSON or safe serialization format

3. CRITICAL - Code Injection (Line 10)
   Issue: eval() with dynamic expression
   Fix: Use ast.literal_eval() for safe evaluation
```

## Supported Languages

- Python 3.x
- JavaScript (ES6+)
- TypeScript

## Integration

### CLI Usage
```bash
# Scan a file
clawhub run @epstion518/compliance-audit-assistant --file agent.py

# Scan inline code
clawhub run @epstion518/compliance-audit-assistant --code "import os; os.system('ls')"

# JSON output for pipelines
clawhub run @epstion518/compliance-audit-assistant --file agent.py --format json
```

### API Usage
```python
from compliance_audit import SecurityScanner

scanner = SecurityScanner()
result = scanner.scan_code(your_agent_code)

print(f"Risk Score: {result['risk_score']}")
for vuln in result['vulnerabilities']:
    print(f"{vuln['severity']}: {vuln['description']}")
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| language | string | auto | Target programming language |
| strict_mode | boolean | false | Enable stricter checking rules |
| exclude_patterns | array | [] | Regex patterns to exclude |
| output_format | string | text | Output: text, json, html |

## Limitations

- Static analysis only (does not execute code)
- Pattern-based detection may produce false positives
- Compliance rules are generalized (not legal advice)
- Does not replace professional security audits

## Version History

- **1.0.0** (2026-06-30): Initial release with core security scanning and GDPR compliance checks

## License

MIT-0 (No Attribution Required)

## Author

@epstion518 - Agent Compliance Org

## Support

For issues, feature requests, or questions:
- GitHub Issues: [repository URL]
- Discord: OpenClaw community
