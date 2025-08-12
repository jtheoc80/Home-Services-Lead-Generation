#!/usr/bin/env tsx

/**
 * @deprecated Use 'botctl audit:qb' instead. This shim will be removed in 60 days.
 * Legacy Env Auditor script - forwards to new audit:qb command
 */

import { execSync } from 'child_process';

const colors = {
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
};

console.log('🔄 Legacy script: env-auditor.ts');
console.log(colors.yellow(`⚠️  DEPRECATION WARNING: 'env-auditor' is deprecated`));
console.log(colors.gray(`    Use 'botctl audit:qb' instead. Legacy support ends in 60 days.`));
console.log(colors.blue(`🔄 Forwarding to: npm run security:audit && npm run security:check\n`));

try {
  execSync('npm run security:audit && npm run security:check', { 
    stdio: 'inherit',
    cwd: process.cwd() 
  });
} catch (error: any) {
  console.error(`❌ Command failed`);
  process.exit(error.status || 1);
}