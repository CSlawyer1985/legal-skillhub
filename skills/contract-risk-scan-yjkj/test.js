#!/usr/bin/env node
/**
 * Contract Risk Scanner - Test Suite
 */

const { scanContract, formatResults } = require('./scripts/contract-scanner.js');

const TEST_CASES = [
  {
    name: 'Empty input',
    input: '',
    expectError: true
  },
  {
    name: 'No risks detected',
    input: 'This is a simple agreement between two parties for services.',
    expectRisks: 0
  },
  {
    name: 'Critical - Unlimited liability',
    input: 'Party A shall have unlimited liability for all damages arising from this agreement.',
    expectRisks: 1,
    expectCritical: 1
  },
  {
    name: 'Critical - Auto renewal',
    input: 'This agreement shall automatically renew for successive one-year terms unless terminated.',
    expectRisks: 1,
    expectCritical: 1
  },
  {
    name: 'Warning - Work for hire',
    input: 'All work product shall be considered work-made-for-hire and owned by Company.',
    expectRisks: 1,
    expectWarning: 1
  },
  {
    name: 'Multiple risks',
    input: `This Service Agreement automatically renews annually. 
            Contractor assigns all rights to all inventions. 
            Payment terms are net 60 days.`,
    expectRisks: 3,
    expectCritical: 1,
    expectWarning: 2
  }
];

function runTests() {
  console.log('=== Contract Risk Scanner Test Suite ===\n');
  
  let passed = 0;
  let failed = 0;

  for (const testCase of TEST_CASES) {
    process.stdout.write('Test: ' + testCase.name + ' ... ');
    
    try {
      const result = scanContract(testCase.input);
      let testPassed = true;
      let failReason = '';

      if (testCase.expectError) {
        if (!result.error) {
          testPassed = false;
          failReason = 'Expected error but got none';
        }
      } else {
        if (result.error) {
          testPassed = false;
          failReason = 'Unexpected error: ' + result.error;
        } else {
          if (testCase.expectRisks !== undefined && result.summary.total !== testCase.expectRisks) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectRisks + ' risks, got ' + result.summary.total;
          }
          if (testCase.expectCritical !== undefined && result.summary.critical !== testCase.expectCritical) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectCritical + ' critical, got ' + result.summary.critical;
          }
          if (testCase.expectWarning !== undefined && result.summary.warning !== testCase.expectWarning) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectWarning + ' warning, got ' + result.summary.warning;
          }
        }
      }

      if (testPassed) {
        console.log('✓ PASS');
        passed++;
      } else {
        console.log('✗ FAIL: ' + failReason);
        failed++;
      }
    } catch (err) {
      console.log('✗ ERROR: ' + err.message);
      failed++;
    }
  }

  console.log('\n=== Test Summary ===');
  console.log('Passed: ' + passed + '/' + TEST_CASES.length);
  console.log('Failed: ' + failed + '/' + TEST_CASES.length);
  
  if (failed === 0) {
    console.log('\n✓ All tests passed!');
    process.exit(0);
  } else {
    console.log('\n✗ Some tests failed');
    process.exit(1);
  }
}

// Run tests if called directly
if (require.main === module) {
  runTests();
}

module.exports = { runTests, TEST_CASES };
