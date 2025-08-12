#!/usr/bin/env tsx

/**
 * @deprecated Use 'botctl e2e:jt' instead. This shim will be removed in 60 days.
 * Legacy E2E Smoke script - forwards to new e2e:jt command
 */

import { execSync } from 'child_process';

const colors = {
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
};

console.log('🔄 Legacy script: e2e-smoke.ts');
console.log(colors.yellow(`⚠️  DEPRECATION WARNING: 'e2e-smoke' is deprecated`));
console.log(colors.gray(`    Use 'botctl e2e:jt' instead. Legacy support ends in 60 days.`));
console.log(colors.blue(`🔄 Forwarding to: npm run e2e:smoke\n`));

try {
  execSync('npm run e2e:smoke', { 
    stdio: 'inherit',
    cwd: process.cwd() 
  });
} catch (error: any) {
  console.error(`❌ Command failed`);
  process.exit(error.status || 1);
}