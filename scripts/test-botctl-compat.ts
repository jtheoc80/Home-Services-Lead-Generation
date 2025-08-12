#!/usr/bin/env tsx

/**
 * Validation script for botctl compatibility layer
 * Tests that all command mappings are working correctly
 */

import { execSync } from 'child_process';

const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
};

function testCommand(cmd: string, description: string): boolean {
  try {
    console.log(`${colors.blue('Testing:')} ${description}`);
    console.log(`${colors.blue('Command:')} ${cmd}`);
    
    const output = execSync(cmd, { 
      encoding: 'utf8',
      stdio: 'pipe'
    });
    
    console.log(colors.green('✅ PASS: Command executed successfully'));
    console.log('');
    return true;
  } catch (error: any) {
    console.log(colors.red('❌ FAIL: Command failed'));
    console.log(`${colors.red('Error:')} ${error.message}`);
    console.log('');
    return false;
  }
}

console.log(colors.blue('🧪 Botctl Compatibility Layer Validation\n'));

const tests = [
  {
    cmd: 'npx tsx tools/bots/index.ts migrate-help',
    description: 'Migration help command'
  },
  {
    cmd: 'npx tsx tools/bots/index.ts e2e-smoke --help',
    description: 'Legacy e2e-smoke command help'
  },
  {
    cmd: 'npx tsx tools/bots/index.ts env-auditor --help', 
    description: 'Legacy env-auditor command help'
  },
  {
    cmd: 'npx tsx tools/bots/index.ts db-setup --help',
    description: 'Legacy db-setup command help'
  },
  {
    cmd: 'npx tsx tools/bots/index.ts audit:qb --help',
    description: 'New audit:qb command help'
  },
  {
    cmd: 'npx tsx tools/bots/index.ts e2e:jt --help',
    description: 'New e2e:jt command help'
  },
  {
    cmd: 'npx tsx tools/bots/index.ts db:wire --help',
    description: 'New db:wire command help'
  }
];

let passed = 0;
let failed = 0;

for (const test of tests) {
  if (testCommand(test.cmd, test.description)) {
    passed++;
  } else {
    failed++;
  }
}

console.log(`${colors.blue('📊 Test Results:')}`);
console.log(`${colors.green('✅ Passed:')} ${passed}`);
console.log(`${colors.red('❌ Failed:')} ${failed}`);

if (failed === 0) {
  console.log(colors.green('\n🎉 All tests passed! Botctl compatibility layer is working correctly.'));
  process.exit(0);
} else {
  console.log(colors.red('\n💥 Some tests failed. Please check the compatibility layer.'));
  process.exit(1);
}