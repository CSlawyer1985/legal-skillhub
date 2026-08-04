#!/usr/bin/env node
/**
 * Defense Drafter
 * 
 * Generates civil answer and defense document frameworks.
 * This is a drafting assistance tool and does not constitute legal advice.
 */

const AFFIRMATIVE_DEFENSES = {
  'statute-of-limitations': {
    name: 'Statute of Limitations',
    description: 'Claim filed after the legal deadline',
    text: 'Plaintiff\'s claims are barred by the applicable statute of limitations.'
  },
  'statute-of-frauds': {
    name: 'Statute of Frauds',
    description: 'Contract not in writing as required',
    text: 'The alleged agreement is unenforceable because it falls within the Statute of Frauds and lacks the required signed writing.'
  },
  'failure-of-consideration': {
    name: 'Failure of Consideration',
    description: 'Promised consideration was not provided',
    text: 'Plaintiff failed to provide the consideration promised, thereby relieving Defendant of any obligation to perform.'
  },
  'waiver': {
    name: 'Waiver',
    description: 'Plaintiff waived its rights',
    text: 'Plaintiff waived any right to enforce the alleged agreement through its conduct.'
  },
  'payment': {
    name: 'Payment',
    description: 'Already paid what is owed',
    text: 'Defendant paid the amounts alleged to be due.'
  },
  'accord-and-satisfaction': {
    name: 'Accord and Satisfaction',
    description: 'Parties settled the dispute',
    text: 'The parties reached an accord and satisfaction of the alleged debt.'
  },
  'unclean-hands': {
    name: 'Unclean Hands',
    description: 'Plaintiff acted improperly',
    text: 'Plaintiff comes to court with unclean hands and is not entitled to equitable relief.'
  },
  'laches': {
    name: 'Laches',
    description: 'Plaintiff unreasonably delayed',
    text: 'Plaintiff unreasonably delayed bringing this action to Defendant\'s prejudice.'
  },
  'impossibility': {
    name: 'Impossibility',
    description: 'Performance became impossible',
    text: 'Performance became impossible due to circumstances beyond Defendant\'s control.'
  },
  'mutual-mistake': {
    name: 'Mutual Mistake',
    description: 'Both parties mistaken about material fact',
    text: 'Both parties were mistaken about a material fact at the time of contracting.'
  }
};

/**
 * Generate defense framework
 * @param {Object} caseInfo - Case information
 * @returns {Object} Defense framework
 */
function generateDefense(caseInfo) {
  if (!caseInfo || typeof caseInfo !== 'object') {
    return {
      error: 'Invalid input: case information is required',
      framework: null
    };
  }

  const {
    caption = {},
    defendant = {},
    allegations = [],
    defenses = [],
    counterclaims = [],
    court = {}
  } = caseInfo;

  // Validate minimum required info
  if (!defendant.name) {
    return {
      error: 'Defendant name is required',
      framework: null
    };
  }

  const framework = {
    caption: generateCaption(caption),
    introduction: generateIntroduction(defendant),
    responses: generateResponses(allegations),
    affirmativeDefenses: generateAffirmativeDefenses(defenses),
    counterclaims: counterclaims.length > 0 ? generateCounterclaims(counterclaims) : null,
    prayer: generatePrayer(counterclaims.length > 0),
    signature: generateSignature(defendant),
    disclaimer: 'This is a document framework for discussion purposes only. It does not constitute legal advice. Consult qualified counsel immediately upon being served with a lawsuit.'
  };

  return {
    framework,
    deadlineWarning: 'CRITICAL: Deadlines for responding to lawsuits are strict. Failure to respond timely can result in default judgment.',
    checklist: generateChecklist(),
    nextSteps: [
      'Consult with an attorney immediately',
      'Verify response deadline (typically 20-30 days from service)',
      'Gather all relevant documents',
      'Identify potential witnesses',
      'Preserve evidence',
      'Notify insurance carrier if applicable',
      'File response before deadline',
      'Serve plaintiff or plaintiff\'s attorney'
    ]
  };
}

function generateCaption(caption) {
  return {
    court: caption.court || '[COURT NAME]',
    caseNumber: caption.caseNumber || '[CASE NUMBER]',
    plaintiff: caption.plaintiff || '[PLAINTIFF NAME]',
    defendant: caption.defendant || '[DEFENDANT NAME]'
  };
}

function generateIntroduction(defendant) {
  return {
    name: defendant.name,
    representation: defendant.hasAttorney ? 'represented by counsel' : 'pro se',
    text: 'Defendant ' + defendant.name + ', ' + (defendant.hasAttorney ? 'represented by counsel' : 'pro se') + ', responds to Plaintiff\'s Complaint as follows:'
  };
}

function generateResponses(allegations) {
  if (!allegations || allegations.length === 0) {
    return [
      {
        paragraph: '[X]',
        response: '[ADMIT/DENY/LACK KNOWLEDGE]',
        explanation: '[Explain if needed]'
      }
    ];
  }

  return allegations.map((allegation, index) => ({
    paragraph: index + 1,
    response: allegation.response || 'DENY',
    explanation: allegation.explanation || ''
  }));
}

function generateAffirmativeDefenses(defenses) {
  if (!defenses || defenses.length === 0) {
    return [
      {
        number: 1,
        name: '[AFFIRMATIVE DEFENSE NAME]',
        text: '[Explain the defense and why it applies]'
      }
    ];
  }

  return defenses.map((defenseKey, index) => {
    const defense = AFFIRMATIVE_DEFENSES[defenseKey] || {
      name: defenseKey,
      text: '[Explain this defense]'
    };
    return {
      number: index + 1,
      name: defense.name,
      text: defense.text
    };
  });
}

function generateCounterclaims(counterclaims) {
  return counterclaims.map((claim, index) => ({
    count: index + 1,
    type: claim.type || '[CLAIM TYPE]',
    facts: claim.facts || ['[Facts supporting counterclaim]'],
    relief: claim.relief || '[Relief sought]'
  }));
}

function generatePrayer(hasCounterclaims) {
  const basePrayer = [
    'Dismiss Plaintiff\'s Complaint with prejudice',
    'Award Defendant costs and attorney fees',
    'Grant other relief as the Court deems just'
  ];

  if (hasCounterclaims) {
    basePrayer.splice(1, 0, 'Enter judgment on Defendant\'s Counterclaim');
  }

  return basePrayer;
}

function generateSignature(defendant) {
  return {
    name: defendant.name,
    date: '[DATE]',
    address: defendant.address || '[ADDRESS]',
    phone: defendant.phone || '[PHONE]',
    email: defendant.email || '[EMAIL]'
  };
}

function generateChecklist() {
  return [
    'Deadline calculated from service date',
    'All complaint paragraphs addressed',
    'Affirmative defenses identified',
    'Counterclaims included (if applicable)',
    'Signature block complete',
    'Filing fee prepared',
    'Copies for all parties',
    'Proof of service prepared'
  ];
}

/**
 * Format defense framework for display
 * @param {Object} result - Defense result
 * @returns {string} Formatted output
 */
function formatDefense(result) {
  if (result.error) {
    return 'Error: ' + result.error;
  }

  const f = result.framework;
  let output = '=== ANSWER AND DEFENSES FRAMEWORK ===\n\n';

  // Warning
  output += '⚠️  ' + result.deadlineWarning + '\n\n';

  // Caption
  output += '--- CAPTION ---\n';
  output += 'IN THE ' + f.caption.court + '\n';
  output += 'Case No.: ' + f.caption.caseNumber + '\n\n';
  output += f.caption.plaintiff + ', Plaintiff,\n';
  output += 'v.\n';
  output += f.caption.defendant + ', Defendant.\n\n';

  // Title
  output += 'ANSWER AND AFFIRMATIVE DEFENSES\n\n';

  // Introduction
  output += '--- INTRODUCTION ---\n';
  output += f.introduction.text + '\n\n';

  // Responses
  output += '--- RESPONSES TO ALLEGATIONS ---\n';
  f.responses.forEach(r => {
    output += 'Paragraph ' + r.paragraph + ': ' + r.response + '\n';
    if (r.explanation) {
      output += '  Note: ' + r.explanation + '\n';
    }
  });
  output += '\n';

  // General Denial
  output += '--- GENERAL DENIAL ---\n';
  output += 'Defendant denies each and every allegation not specifically admitted,\n';
  output += 'and puts Plaintiff to strict proof thereof.\n\n';

  // Affirmative Defenses
  output += '--- AFFIRMATIVE DEFENSES ---\n';
  f.affirmativeDefenses.forEach(d => {
    output += d.number + '. ' + d.name + '\n';
    output += '   ' + d.text + '\n\n';
  });

  // Counterclaims
  if (f.counterclaims) {
    output += '--- COUNTERCLAIMS ---\n';
    f.counterclaims.forEach(c => {
      output += 'COUNT ' + c.count + ': ' + c.type + '\n';
      c.facts.forEach(fact => {
        output += '  - ' + fact + '\n';
      });
      output += 'Relief: ' + c.relief + '\n\n';
    });
  }

  // Prayer
  output += '--- PRAYER FOR RELIEF ---\n';
  output += 'WHEREFORE, Defendant requests:\n';
  f.prayer.forEach((item, index) => {
    output += '  ' + String.fromCharCode(97 + index) + '. ' + item + '\n';
  });
  output += '\n';

  // Signature
  output += '--- SIGNATURE ---\n';
  output += 'DATED: ' + f.signature.date + '\n\n';
  output += 'Respectfully submitted,\n\n';
  output += '_____________________\n';
  output += f.signature.name + '\n';
  output += f.signature.address + '\n';
  output += f.signature.phone + '\n';
  output += f.signature.email + '\n\n';

  // Checklist
  output += '--- FILING CHECKLIST ---\n';
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
module.exports = { generateDefense, formatDefense, AFFIRMATIVE_DEFENSES };

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log('Usage: node defense-drafter.js --example');
    console.log('   or: node defense-drafter.js --test');
    process.exit(0);
  }

  if (args[0] === '--test') {
    const test = require('../test.js');
    test.runTests();
    process.exit(0);
  }

  if (args[0] === '--example') {
    const exampleCase = {
      caption: {
        court: 'SUPERIOR COURT OF CALIFORNIA',
        caseNumber: 'BC123456',
        plaintiff: 'ABC Corporation',
        defendant: 'John Doe'
      },
      defendant: {
        name: 'John Doe',
        hasAttorney: false,
        address: '123 Main St, Los Angeles, CA 90001'
      },
      allegations: [
        { response: 'DENY' },
        { response: 'LACK KNOWLEDGE' },
        { response: 'DENY' }
      ],
      defenses: ['statute-of-limitations', 'failure-of-consideration'],
      counterclaims: []
    };
    
    const result = generateDefense(exampleCase);
    console.log(formatDefense(result));
    process.exit(0);
  }

  console.log('Use --example to see a sample defense framework');
  console.log('Use --test to run tests');
}
