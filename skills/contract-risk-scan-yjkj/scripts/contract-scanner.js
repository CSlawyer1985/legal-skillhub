#!/usr/bin/env node
/**
 * Contract Risk Scanner
 * 
 * Scans contract text for common risk patterns and returns identified risks.
 * This is a preliminary tool and does not constitute legal advice.
 */

const RISK_PATTERNS = [
  // Critical - Liability
  {
    category: 'Liability',
    severity: 'critical',
    pattern: /unlimited liability|liability for all damages|no limit on liability/i,
    description: 'Unlimited liability clause detected',
    suggestion: 'Negotiate a liability cap (e.g., 12 months of fees or contract value)'
  },
  {
    category: 'Indemnification',
    severity: 'critical',
    pattern: /indemnify.*any and all claims|hold harmless.*any and all/i,
    description: 'Broad indemnification obligation detected',
    suggestion: 'Limit indemnification to direct damages caused by your actions'
  },
  
  // Critical - Termination
  {
    category: 'Termination',
    severity: 'critical',
    pattern: /may not be terminated.*except|termination.*only for cause|no right to terminate/i,
    description: 'No termination for convenience clause',
    suggestion: 'Add termination for convenience with reasonable notice (30-90 days)'
  },
  {
    category: 'Termination',
    severity: 'critical',
    pattern: /automatically renew|auto-renew|automatic renewal/i,
    description: 'Automatic renewal clause detected',
    suggestion: 'Ensure notice requirement exists (30-60 days before renewal)'
  },
  
  // Critical - Venue
  {
    category: 'Dispute Resolution',
    severity: 'critical',
    pattern: /venue shall be|jurisdiction shall be|exclusive jurisdiction/i,
    description: 'Exclusive venue/jurisdiction clause - verify fairness',
    suggestion: 'Negotiate neutral venue or your home jurisdiction'
  },
  
  // Warning - Payment
  {
    category: 'Payment',
    severity: 'warning',
    pattern: /net\s*6[0-9]|payment within\s*6[0-9]|payment within\s*9[0-9]/i,
    description: 'Extended payment terms (60+ days) detected',
    suggestion: 'Negotiate standard net 30 terms'
  },
  {
    category: 'Termination',
    severity: 'warning',
    pattern: /notice.*180 days|notice.*six months|termination fee/i,
    description: 'Long termination notice or termination fee detected',
    suggestion: 'Reduce notice to 30-60 days or negotiate reasonable termination fee'
  },
  
  // Warning - IP
  {
    category: 'Intellectual Property',
    severity: 'warning',
    pattern: /work[-\s]made[-\s]for[-\s]hire|work for hire/i,
    description: 'Work-for-hire clause detected',
    suggestion: 'Ensure limitation to specific deliverables; exclude background IP'
  },
  {
    category: 'Intellectual Property',
    severity: 'warning',
    pattern: /assigns all rights|all inventions|all intellectual property/i,
    description: 'Broad IP assignment detected',
    suggestion: 'Limit to inventions conceived during specific project work only'
  },
  
  // Warning - Confidentiality
  {
    category: 'Confidentiality',
    severity: 'warning',
    pattern: /indefinitely|perpetual confidentiality|unlimited period/i,
    description: 'Indefinite confidentiality obligation detected',
    suggestion: 'Set reasonable term (3-5 years) with trade secret exception'
  },
  {
    category: 'Confidentiality',
    severity: 'warning',
    pattern: /all information.*confidential|everything disclosed/i,
    description: 'Overly broad confidentiality definition',
    suggestion: 'Define specific categories and marking requirements'
  },
  
  // Warning - Dispute
  {
    category: 'Dispute Resolution',
    severity: 'warning',
    pattern: /prevailing party.*attorney|attorney fees.*shall be awarded/i,
    description: 'Attorney fee provision detected - verify mutuality',
    suggestion: 'Ensure attorney fee provision is mutual'
  },
  
  // Advisory
  {
    category: 'General',
    severity: 'advisory',
    pattern: /upon completion|when completed/i,
    description: 'Vague completion-based payment trigger',
    suggestion: 'Define specific milestones or deliverables triggering payment'
  },
  {
    category: 'General',
    severity: 'advisory',
    pattern: /may not be assigned|assignment.*prior consent/i,
    description: 'Assignment restriction detected',
    suggestion: 'Allow assignment to affiliates or in M&A transactions'
  }
];

/**
 * Scan contract text for risk patterns
 * @param {string} contractText - The contract text to scan
 * @returns {Object} Scan results with identified risks
 */
function scanContract(contractText) {
  if (!contractText || typeof contractText !== 'string') {
    return {
      error: 'Invalid input: contract text is required',
      risks: [],
      summary: { critical: 0, warning: 0, advisory: 0, total: 0 }
    };
  }

  const text = contractText.toLowerCase();
  const risks = [];
  const foundPatterns = new Set();

  for (const rule of RISK_PATTERNS) {
    // Skip if we've already found this pattern category
    const patternKey = rule.category + '-' + rule.pattern.toString();
    if (foundPatterns.has(patternKey)) continue;

    if (rule.pattern.test(text)) {
      foundPatterns.add(patternKey);
      
      // Find context around match
      const match = text.match(rule.pattern);
      let context = '';
      if (match && match.index !== undefined) {
        const start = Math.max(0, match.index - 50);
        const end = Math.min(text.length, match.index + match[0].length + 50);
        context = contractText.substring(start, end).replace(/\s+/g, ' ').trim();
      }

      risks.push({
        category: rule.category,
        severity: rule.severity,
        description: rule.description,
        suggestion: rule.suggestion,
        context: context ? '...' + context + '...' : undefined
      });
    }
  }

  // Sort by severity
  const severityOrder = { critical: 0, warning: 1, advisory: 2 };
  risks.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  const summary = {
    critical: risks.filter(r => r.severity === 'critical').length,
    warning: risks.filter(r => r.severity === 'warning').length,
    advisory: risks.filter(r => r.severity === 'advisory').length,
    total: risks.length
  };

  return {
    risks,
    summary,
    disclaimer: 'This scan provides preliminary risk identification only and does not constitute legal advice. Always consult a qualified attorney for important contract decisions.'
  };
}

/**
 * Format scan results for display
 * @param {Object} results - Scan results from scanContract
 * @returns {string} Formatted output
 */
function formatResults(results) {
  if (results.error) {
    return 'Error: ' + results.error;
  }

  const severityEmoji = {
    critical: '🔴',
    warning: '🟡',
    advisory: '🟢'
  };

  let output = '=== CONTRACT RISK SCAN RESULTS ===\n\n';
  output += 'Summary: ' + results.summary.critical + ' Critical, ' + results.summary.warning + ' Warning, ' + results.summary.advisory + ' Advisory\n';
  output += 'Total Risks Identified: ' + results.summary.total + '\n\n';

  if (results.risks.length === 0) {
    output += 'No common risk patterns detected.\n';
    output += 'Note: This does not mean the contract is risk-free.\n';
  } else {
    results.risks.forEach((risk, index) => {
      output += (index + 1) + '. ' + severityEmoji[risk.severity] + ' [' + risk.category + '] ' + risk.description + '\n';
      output += '   Suggestion: ' + risk.suggestion + '\n';
      if (risk.context) {
        output += '   Context: ' + risk.context + '\n';
      }
      output += '\n';
    });
  }

  output += '\n=== DISCLAIMER ===\n';
  output += results.disclaimer + '\n';

  return output;
}

// Export for use as module
module.exports = { scanContract, formatResults, RISK_PATTERNS };

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log('Usage: node contract-scanner.js <contract-file.txt>');
    console.log('   or: echo "contract text" | node contract-scanner.js');
    console.log('   or: node contract-scanner.js --test');
    process.exit(0);
  }

  if (args[0] === '--test') {
    // Run built-in tests
    console.log('Running tests...');
    const test = require('./test.js');
    test.runTests();
    process.exit(0);
  }

  const fs = require('fs');
  const filePath = args[0];
  
  if (!fs.existsSync(filePath)) {
    console.error('Error: File not found: ' + filePath);
    process.exit(1);
  }

  const contractText = fs.readFileSync(filePath, 'utf-8');
  const results = scanContract(contractText);
  console.log(formatResults(results));
}
