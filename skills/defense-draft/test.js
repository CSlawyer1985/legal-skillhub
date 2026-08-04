#!/usr/bin/env node
/**
 * Defense Drafter - Test Suite
 */

const { generateDefense, formatDefense } = require('./scripts/defense-drafter.js');

const TEST_CASES = [
  {
    name: 'Empty input',
    input: null,
    expectError: true
  },
  {
    name: 'Missing defendant name',
    input: { caption: {} },
    expectError: true
  },
  {
    name: 'Basic answer',
    input: {
      defendant: { name: 'John Doe' },
      allegations: [{ response: 'DENY' }]
    },
    expectSuccess: true
  },
  {
    name: 'With affirmative defenses',
    input: {
      defendant: { name: 'Jane Smith' },
      allegations: [{ response: 'DENY' }],
      defenses: ['statute-of-limitations', 'payment']
    },
    expectSuccess: true,
    expectDefenses: 2
  },
  {
    name: 'With counterclaim',
    input: {
      defendant: { name: 'Bob Wilson' },
      allegations: [{ response: 'DENY' }],
      defenses: ['waiver'],
      counterclaims: [{ type: 'breach-of-contract' }]
    },
    expectSuccess: true,
    expectCounterclaims: 1
  }
];

function runTests() {
  console.log('=== Defense Drafter Test Suite ===\n');
  
  let passed = 0;
  let failed = 0;

  for (const testCase of TEST_CASES) {
    process.stdout.write('Test: ' + testCase.name + ' ... ');
    
    try {
      const result = generateDefense(testCase.input);
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
          if (testCase.expectDefenses && result.framework.affirmativeDefenses.length !== testCase.expectDefenses) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectDefenses + ' defenses, got ' + result.framework.affirmativeDefenses.length;
          }
          if (testCase.expectCounterclaims && (!result.framework.counterclaims || result.framework.counterclaims.length !== testCase.expectCounterclaims)) {
            testPassed = false;
            failReason = 'Expected ' + testCase.expectCounterclaims + ' counterclaims';
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
