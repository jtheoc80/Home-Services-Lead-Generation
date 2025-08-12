#!/usr/bin/env tsx

/**
 * @deprecated Use 'botctl db:wire' instead. This shim will be removed in 60 days.
 * Legacy DB Setup script - forwards to new db:wire command
 */

import { execSync } from 'child_process';

const colors = {
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
};

console.log('🔄 Legacy script: db-setup.ts');
console.log(colors.yellow(`⚠️  DEPRECATION WARNING: 'db-setup' is deprecated`));
console.log(colors.gray(`    Use 'botctl db:wire' instead. Legacy support ends in 60 days.`));
console.log(colors.blue(`🔄 Forwarding to: npm run schema:drift\n`));

try {
  execSync('npm run schema:drift', { 
    stdio: 'inherit',
    cwd: process.cwd() 
  });
} catch (error: any) {
  console.error(`❌ Command failed`);
  process.exit(error.status || 1);
}