#!/usr/bin/env node
/**
 * Complaint Drafter - Test Suite
 */

const { generateComplaint, formatComplaint } = require('./scripts/complaint-drafter.js');

const TEST_CASES = [
  {
    name: 'Empty input',
    input: null,
    expectError: true
  },
  {
    name: 'Missing parties',
    input: { facts: ['Something happened'] },
    expectError: true
  },
  {
    name: 'Basic breach of contract',
    input: {
      plaintiff: { name: 'John Doe' },
      defendant: { name: 'ABC Corp' },
      claims: [{ type: 'breach-of-contract' }]
    },
    expectSuccess: true,
    expectClaims: 1
  },
  {
    name: 'Multiple claims',
    input: {
      plaintiff: { name: 'Jane Smith' },
      defendant: { name: 'XYZ Inc' },
      claims: [
        { type: 'breach-of-contract' },
        { type: 'negligence' }
      ]
    },
    expectSuccess: true,
    expectClaims: 2
  },
  {
    name: 'With facts',
    input: {
      plaintiff: { name: 'Bob Wilson' },
      defendant: { name: 'Acme LLC' },
      facts: ['Event 1', 'Event 2', 'Event 3']
    },
    expectSuccess: true,
    expectFacts: 3
  }
];

function runTests() {
  console.log('=== Complaint Drafter Test Suite ===\n');
  
  let passed = 0;
  let failed = 0;

  for (const testCase of TEST_CASES) {
    process.stdout.write('Test: ' + testCase.name + ' ... ');
    
    try {
      const result = generateComplaint(testCase.input);
      let testPassed = true;
      let failReason = '';

      if (testCase.expectError) {
        if (!result.error) {
          testPassed = false;
          failReason = 'Expected error but got none';
        }
      } else if (testCase.expectSuccess) {
        if (result.error) {
          testPassed = false;
          failReason = 'Unexpected error: ' + result.error;
        } else {
          if (testCase.expectClaims && result.framework.claims.length !== testCase.expectClaims) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectClaims + ' claims, got ' + result.framework.claims.length;
          }
          if (testCase.expectFacts && result.framework.facts.length !== testCase.expectFacts) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectFacts + ' facts, got ' + result.framework.facts.length;
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
