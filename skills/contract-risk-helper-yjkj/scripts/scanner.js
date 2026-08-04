#!/usr/bin/env node
/**
 * Contract Risk Scanner - Local Pattern Matching
 * Read-only: no network, no exec, no credential access
 */

const path = require('path');
const fs = require('fs');

const RISK_PATTERNS = [
  // Critical - Liability
  {
    category: 'Liability',
    severity: 'critical',
    pattern: /unlimited liability|liability for all damages|no limit on liability/i,
    description: 'Unlimited liability clause detected — no financial cap on exposure',
    suggestion: 'Negotiate a liability cap (e.g., 12 months of fees or contract value)'
  },
  {
    category: 'Liability',
    severity: 'critical',
    pattern: /indemnify.*any and all claims|hold harmless.*any and all/i,
    description: 'Broad indemnification obligation — one-sided with no carve-outs',
    suggestion: 'Limit indemnification to direct damages caused by the indemnifying party\'s actions'
  },

  // Critical - Termination
  {
    category: 'Termination',
    severity: 'critical',
    pattern: /may not be terminated|termination only for cause|no right to terminate/i,
    description: 'No termination for convenience — no exit without breach',
    suggestion: 'Add termination for convenience with reasonable notice (30-90 days)'
  },
  {
    category: 'Termination',
    severity: 'critical',
    pattern: /automatically renew|auto-renew|automatic renewal|successive one-year/i,
    description: 'Automatic renewal without active decision',
    suggestion: 'Ensure 30-60 day notice requirement before renewal; add opt-out clause'
  },
  {
    category: 'Termination',
    severity: 'critical',
    pattern: /venue shall be|jurisdiction shall be|exclusive jurisdiction/i,
    description: 'Exclusive venue/jurisdiction clause — verify it is fair',
    suggestion: 'Negotiate neutral venue or your home jurisdiction'
  },

  // Warning - Payment
  {
    category: 'Payment',
    severity: 'warning',
    pattern: /net\s*6[0-9]|payment within\s*6[0-9]|payment within\s*9[0-9]/i,
    description: 'Extended payment terms (60+ days)',
    suggestion: 'Negotiate standard net 30 terms or request early payment discount'
  },
  {
    category: 'Payment',
    severity: 'warning',
    pattern: /no.*late.*payment.*penalty|no.*penalty.*late/i,
    description: 'No penalty for late payment',
    suggestion: 'Add late fee clause (e.g., 1.5% per month on overdue amounts)'
  },

  // Warning - IP
  {
    category: 'Intellectual Property',
    severity: 'warning',
    pattern: /work[-\s]made[-\s]for[-\s]hire|work for hire/i,
    description: 'Work-for-hire clause — may transfer all background IP',
    suggestion: 'Limit to specific project deliverables; carve out pre-existing IP'
  },
  {
    category: 'Intellectual Property',
    severity: 'warning',
    pattern: /assigns? all rights|all inventions|all intellectual property/i,
    description: 'Broad IP assignment — no limitation to project scope',
    suggestion: 'Limit assignment to inventions conceived specifically during this project'
  },

  // Warning - Termination details
  {
    category: 'Termination',
    severity: 'warning',
    pattern: /notice.*180 days|notice.*six months|termination fee.*total|early termination.*all fees/i,
    description: 'Excessive termination notice period or prohibitive exit fee',
    suggestion: 'Reduce notice to 30-60 days; negotiate reasonable prorated termination fee'
  },

  // Warning - Confidentiality
  {
    category: 'Confidentiality',
    severity: 'warning',
    pattern: /perpetual confidentiality|indefinite.*confidential|survive forever/i,
    description: 'Indefinite confidentiality obligation — never expires',
    suggestion: 'Limit confidentiality term to 3-5 years after contract termination'
  },
  {
    category: 'Confidentiality',
    severity: 'warning',
    pattern: /return.*confidential|destroy.*confidential/i,
    description: 'No obligation to return or destroy confidential information',
    suggestion: 'Add clause requiring return or certified destruction upon termination'
  },

  // Warning - Dispute
  {
    category: 'Dispute',
    severity: 'warning',
    pattern: /prevailing party.*attorney.*fee|attorney.*fee.*prevailing/i,
    description: 'One-sided attorney fee provision',
    suggestion: 'Make mutual — each party bears its own costs, or prevailing party recovers fees'
  },

  // Advisory
  {
    category: 'Payment',
    severity: 'advisory',
    pattern: /payment upon completion|upon completion.*payment/i,
    description: 'Unclear payment trigger — no milestone definition',
    suggestion: 'Define specific milestones or deliverables that trigger payment obligations'
  },
  {
    category: 'Service',
    severity: 'advisory',
    pattern: /sole discretion|reasonably determined|solely at.*discretion/i,
    description: 'Vague scope — allows unilateral expansion',
    suggestion: 'Define specific deliverables with measurable acceptance criteria'
  },
  {
    category: 'Service',
    severity: 'advisory',
    pattern: /no service level|no uptime|without.*guarantee/i,
    description: 'No service level or performance guarantee',
    suggestion: 'Add SLA with remedies (credits or termination right) for missed targets'
  }
];

/**
 * Scan contract text for risk patterns
 * @param {string} text - Contract text
 * @returns {Array} Array of found risks
 */
function scan(text) {
  if (!text || typeof text !== 'string' || text.trim().length === 0) {
    return [];
  }

  const results = [];
  const seenCategories = new Set();

  for (const item of RISK_PATTERNS) {
    const match = text.match(item.pattern);
    if (match) {
      // Find the sentence containing the match for context
      const sentenceMatch = text.slice(Math.max(0, match.index - 100), match.index + match[0].length + 100);
      const sentence = sentenceMatch.split(/[.。\n]/).find(s => new RegExp(item.pattern).test(s.trim())) || match[0];

      results.push({
        category: item.category,
        severity: item.severity,
        matched: match[0],
        context: sentence.trim().slice(0, 150),
        description: item.description,
        suggestion: item.suggestion
      });
    }
  }

  return results;
}

/**
 * Format scan results for display
 */
function formatResults(results) {
  if (!results || results.length === 0) {
    return '✅ 未发现已知风险模式。\n\n（此扫描仅针对常见已知风险模式，不能替代专业法律审查）';
  }

  const bySeverity = { critical: [], warning: [], advisory: [] };
  for (const r of results) {
    bySeverity[r.severity].push(r);
  }

  let output = `## 合同风险扫描结果\n\n共发现 **${results.length}** 个风险项\n\n`;

  const emojis = { critical: '🔴', warning: '🟡', advisory: '🟢' };
  const labels = { critical: '严重', warning: '警告', advisory: '提醒' };

  for (const severity of ['critical', 'warning', 'advisory']) {
    const items = bySeverity[severity];
    if (items.length > 0) {
      output += `### ${emojis[severity]} ${labels[severity]} (${items.length})\n\n`;
      for (const item of items) {
        output += `- **[${item.category}]** ${item.description}\n`;
        output += `  → ${item.suggestion}\n\n`;
      }
    }
  }

  output += '---\n\n**⚠️ 以上仅为常见风险模式识别，不构成法律建议。建议委托专业律师进行完整审查。**\n';
  return output;
}

// Export for handler.py
module.exports = { scan, formatResults };

// Self-test when run directly
if (require.main === module) {
  const testText = `This agreement automatically renews for successive one-year terms unless terminated.
  Party A shall have unlimited liability for all damages arising from this agreement.
  Payment is due within 90 days of invoice. All work product shall be work-made-for-hire.`;

  console.log('=== Contract Risk Scanner Self-Test ===\n');
  const results = scan(testText);
  console.log(formatResults(results));
}
