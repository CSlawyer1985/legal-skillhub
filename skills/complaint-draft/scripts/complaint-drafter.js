#!/usr/bin/env node
/**
 * Complaint Drafter
 * 
 * Generates civil complaint document frameworks.
 * This is a drafting assistance tool and does not constitute legal advice.
 */

const CLAIM_TYPES = {
  'breach-of-contract': {
    name: 'Breach of Contract',
    elements: [
      'Valid contract existed',
      'Plaintiff performed or was ready to perform',
      'Defendant breached the contract',
      'Damages resulted from the breach'
    ],
    damages: ['Contract price', 'Consequential damages', 'Incidental damages']
  },
  'negligence': {
    name: 'Negligence',
    elements: [
      'Defendant owed a duty of care',
      'Defendant breached that duty',
      'Breach was the cause of injury',
      'Plaintiff suffered damages'
    ],
    damages: ['Medical expenses', 'Lost wages', 'Pain and suffering', 'Property damage']
  },
  'unjust-enrichment': {
    name: 'Unjust Enrichment',
    elements: [
      'Plaintiff conferred a benefit on Defendant',
      'Defendant knew of the benefit',
      'It would be inequitable for Defendant to retain the benefit'
    ],
    damages: ['Value of benefit conferred', 'Restitution']
  },
  'fraud': {
    name: 'Fraud/Misrepresentation',
    elements: [
      'Defendant made a false representation',
      'Defendant knew it was false or acted recklessly',
      'Defendant intended to induce reliance',
      'Plaintiff relied on the representation',
      'Plaintiff suffered damages'
    ],
    damages: ['Actual damages', 'Punitive damages (in some cases)']
  },
  'conversion': {
    name: 'Conversion',
    elements: [
      'Plaintiff owned or possessed property',
      'Defendant intentionally interfered with property rights',
      'Plaintiff is entitled to damages'
    ],
    damages: ['Value of property', 'Damages for deprivation']
  },
  'debt': {
    name: 'Money Owed/Debt',
    elements: [
      'Debt exists',
      'Defendant owes the money',
      'Payment has been demanded but not made'
    ],
    damages: ['Principal amount', 'Interest', 'Collection costs']
  }
};

/**
 * Generate complaint framework
 * @param {Object} caseInfo - Case information
 * @returns {Object} Complaint framework
 */
function generateComplaint(caseInfo) {
  if (!caseInfo || typeof caseInfo !== 'object') {
    return {
      error: 'Invalid input: case information is required',
      framework: null
    };
  }

  const {
    plaintiff = {},
    defendant = {},
    facts = [],
    claims = [],
    damages = {},
    relief = [],
    court = {}
  } = caseInfo;

  // Validate minimum required info
  if (!plaintiff.name || !defendant.name) {
    return {
      error: 'Plaintiff and defendant names are required',
      framework: null
    };
  }

  const framework = {
    caption: generateCaption(plaintiff, defendant, court),
    parties: generateParties(plaintiff, defendant),
    jurisdiction: generateJurisdiction(court),
    venue: generateVenue(court),
    facts: generateFacts(facts),
    claims: generateClaims(claims, damages),
    prayer: generatePrayer(relief, damages),
    signature: generateSignature(plaintiff),
    disclaimer: 'This is a document framework for discussion purposes only. It does not constitute legal advice. Consult qualified counsel before filing any legal action.'
  };

  return {
    framework,
    checklist: generateChecklist(claims),
    nextSteps: [
      'Consult with an attorney to review the framework',
      'Verify proper court and venue',
      'Gather supporting evidence and documents',
      'Calculate damages accurately',
      'Check statute of limitations',
      'Prepare filing fee',
      'Ensure proper service of process'
    ]
  };
}

function generateCaption(plaintiff, defendant, court) {
  return {
    court: court.name || '[COURT NAME]',
    caseNumber: court.caseNumber || '[CASE NUMBER (if assigned)]',
    plaintiff: plaintiff.name,
    defendant: defendant.name
  };
}

function generateParties(plaintiff, defendant) {
  return [
    {
      role: 'Plaintiff',
      name: plaintiff.name,
      description: plaintiff.description || '[DESCRIBE PLAINTIFF]',
      address: plaintiff.address || '[ADDRESS]'
    },
    {
      role: 'Defendant',
      name: defendant.name,
      description: defendant.description || '[DESCRIBE DEFENDANT]',
      address: defendant.address || '[ADDRESS (if known)]'
    }
  ];
}

function generateJurisdiction(court) {
  return {
    basis: court.jurisdiction || '[EXPLAIN JURISDICTION BASIS]',
    note: 'This Court has jurisdiction over this matter because...'
  };
}

function generateVenue(court) {
  return {
    basis: court.venue || '[EXPLAIN VENUE BASIS]',
    note: 'Venue is proper in this Court because...'
  };
}

function generateFacts(facts) {
  if (!facts || facts.length === 0) {
    return [
      '[Date/Time]: [Describe first key event]',
      '[Date/Time]: [Describe second key event]',
      '[Continue chronological narrative]'
    ];
  }
  return facts.map((fact, index) => ({
    paragraph: index + 1,
    content: fact
  }));
}

function generateClaims(claims, damages) {
  if (!claims || claims.length === 0) {
    return [{
      count: 1,
      type: '[CLAIM TYPE]',
      elements: ['[List claim elements]'],
      note: 'Please specify the type of claim(s) you wish to bring'
    }];
  }

  return claims.map((claim, index) => {
    const claimType = CLAIM_TYPES[claim.type] || { name: claim.type, elements: [] };
    return {
      count: index + 1,
      type: claimType.name,
      elements: claimType.elements,
      allegations: claim.allegations || ['[Describe specific allegations]'],
      damages: claim.damages || damages[claim.type] || '[SPECIFY DAMAGES]'
    };
  });
}

function generatePrayer(relief, damages) {
  const defaultRelief = [
    'Enter judgment in favor of Plaintiff',
    'Award damages of $[AMOUNT]',
    'Award costs of suit',
    'Grant other relief as the Court deems just'
  ];

  return relief.length > 0 ? relief : defaultRelief;
}

function generateSignature(plaintiff) {
  return {
    name: plaintiff.name,
    date: '[DATE]',
    note: 'If represented by counsel, attorney signature block required'
  };
}

function generateChecklist(claims) {
  const baseChecklist = [
    'Verify correct court and venue',
    'Confirm statute of limitations has not expired',
    'Gather all supporting evidence',
    'Calculate damages accurately',
    'Prepare filing fee',
    'Arrange for proper service of process'
  ];

  if (claims && claims.some(c => c.type === 'fraud')) {
    baseChecklist.push('Pleading fraud with particularity (Fed. R. Civ. P. 9(b))');
  }

  return baseChecklist;
}

/**
 * Format complaint framework for display
 * @param {Object} result - Complaint result
 * @returns {string} Formatted output
 */
function formatComplaint(result) {
  if (result.error) {
    return 'Error: ' + result.error;
  }

  const f = result.framework;
  let output = '=== CIVIL COMPLAINT FRAMEWORK ===\n\n';

  // Caption
  output += '--- CAPTION ---\n';
  output += 'IN THE ' + f.caption.court + '\n';
  output += 'Case No.: ' + f.caption.caseNumber + '\n\n';
  output += f.caption.plaintiff + ', Plaintiff,\n';
  output += 'v.\n';
  output += f.caption.defendant + ', Defendant.\n\n';

  // Parties
  output += '--- PARTIES ---\n';
  f.parties.forEach(p => {
    output += p.role + ': ' + p.name + '\n';
    output += '  Description: ' + p.description + '\n';
    output += '  Address: ' + p.address + '\n\n';
  });

  // Jurisdiction & Venue
  output += '--- JURISDICTION ---\n';
  output += f.jurisdiction.note + '\n';
  output += f.jurisdiction.basis + '\n\n';

  output += '--- VENUE ---\n';
  output += f.venue.note + '\n';
  output += f.venue.basis + '\n\n';

  // Facts
  output += '--- FACTUAL ALLEGATIONS ---\n';
  if (Array.isArray(f.facts)) {
    f.facts.forEach((fact, index) => {
      if (typeof fact === 'object') {
        output += fact.paragraph + '. ' + fact.content + '\n';
      } else {
        output += (index + 1) + '. ' + fact + '\n';
      }
    });
  }
  output += '\n';

  // Claims
  output += '--- CAUSES OF ACTION ---\n';
  f.claims.forEach(claim => {
    output += 'COUNT ' + claim.count + ': ' + claim.type + '\n';
    output += 'Elements:\n';
    claim.elements.forEach(e => output += '  - ' + e + '\n');
    if (claim.allegations) {
      output += 'Allegations:\n';
      claim.allegations.forEach(a => output += '  - ' + a + '\n');
    }
    output += 'Damages: ' + (claim.damages || '[SPECIFY]') + '\n\n';
  });

  // Prayer
  output += '--- PRAYER FOR RELIEF ---\n';
  output += 'WHEREFORE, Plaintiff requests:\n';
  f.prayer.forEach((item, index) => {
    output += '  ' + String.fromCharCode(97 + index) + '. ' + item + '\n';
  });
  output += '\n';

  // Signature
  output += '--- SIGNATURE ---\n';
  output += 'DATED: ' + f.signature.date + '\n';
  output += 'Respectfully submitted,\n\n';
  output += '_____________________\n';
  output += f.signature.name + '\n';
  output += f.signature.note + '\n\n';

  // Checklist
  output += '--- BEFORE FILING CHECKLIST ---\n';
  result.checklist.forEach(item => {
    output += '[ ] ' + item + '\n';
  });
  output += '\n';

  // Next steps
  output += '--- NEXT STEPS ---\n';
  result.nextSteps.forEach((step, index) => {
    output += (index + 1) + '. ' + step + '\n';
  });
  output += '\n';

  // Disclaimer
  output += '=== DISCLAIMER ===\n';
  output += f.disclaimer + '\n';

  return output;
}

// Export for use as module
module.exports = { generateComplaint, formatComplaint, CLAIM_TYPES };

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log('Usage: node complaint-drafter.js --example');
    console.log('   or: node complaint-drafter.js --test');
    process.exit(0);
  }

  if (args[0] === '--test') {
    const test = require('../test.js');
    test.runTests();
    process.exit(0);
  }

  if (args[0] === '--example') {
    // Generate example complaint
    const exampleCase = {
      plaintiff: {
        name: 'John Doe',
        description: 'Individual residing in California',
        address: '123 Main St, Los Angeles, CA 90001'
      },
      defendant: {
        name: 'ABC Corporation',
        description: 'California corporation',
        address: '456 Business Ave, Los Angeles, CA 90002'
      },
      facts: [
        'On January 1, 2024, parties entered into a service agreement',
        'Plaintiff performed services as agreed',
        'Defendant failed to pay invoice dated February 1, 2024',
        'Amount owed is $10,000'
      ],
      claims: [
        { type: 'breach-of-contract', allegations: ['Failed to pay for services'] }
      ],
      damages: { 'breach-of-contract': '$10,000 plus interest' },
      court: {
        name: 'SUPERIOR COURT OF CALIFORNIA, COUNTY OF LOS ANGELES',
        jurisdiction: 'State court jurisdiction',
        venue: 'Defendant resides in Los Angeles County'
      }
    };
    
    const result = generateComplaint(exampleCase);
    console.log(formatComplaint(result));
    process.exit(0);
  }

  console.log('Use --example to see a sample complaint framework');
  console.log('Use --test to run tests');
}
