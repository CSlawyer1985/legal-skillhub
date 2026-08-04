/**
 * Legal Consultation - Test Suite
 */

const { consult } = require('./scripts/legal-consultation.js');

const TEST_CASES = [
  {
    name: 'Empty input',
    input: '',
    expectError: true
  },
  {
    name: 'Contract question',
    input: '合同有问题怎么办',
    expectArea: 'contract'
  },
  {
    name: 'Labor question',
    input: '被辞退了怎么赔偿',
    expectArea: 'labor'
  },
  {
    name: 'Litigation question',
    input: '想起诉对方',
    expectArea: 'litigation'
  },
  {
    name: 'Evidence question',
    input: '怎么整理证据',
    expectArea: 'evidence'
  }
];

function runTests() {
  console.log('=== Legal Consultation Test Suite ===\n');
  
  let passed = 0;
  let failed = 0;

  for (const testCase of TEST_CASES) {
    process.stdout.write('Test: ' + testCase.name + ' ... ');
    
    try {
      const result = consult(testCase.input);
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
        } else if (testCase.expectArea && result.area !== testCase.expectArea) {
          testPassed = false;
          failReason = 'Expected area ' + testCase.expectArea + ', got ' + result.area;
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

if (require.main === module) {
  runTests();
}

module.exports = { runTests, TEST_CASES };