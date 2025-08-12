#!/usr/bin/env tsx

/**
 * Bot Control Compatibility Layer
 * 
 * This file provides backward compatibility for legacy bot commands.
 * All commands have been consolidated under botctl with new naming.
 * 
 * @deprecated These legacy command mappings will be removed in 60 days.
 * Please migrate to the new botctl commands.
 */

import { execSync } from 'child_process';
import { program } from 'commander';

// Color utilities for consistent output
const colors = {
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
};

/**
 * Execute a command and forward its output
 */
function executeCommand(command: string, legacyName: string, newName: string) {
  console.log(colors.yellow(`⚠️  DEPRECATION WARNING: '${legacyName}' is deprecated`));
  console.log(colors.gray(`    Use '${newName}' instead. Legacy support ends in 60 days.`));
  console.log(colors.blue(`🔄 Forwarding to: ${command}\n`));
  
  try {
    execSync(command, { 
      stdio: 'inherit',
      cwd: process.cwd() 
    });
  } catch (error: any) {
    console.error(colors.red(`❌ Command failed: ${command}`));
    process.exit(error.status || 1);
  }
}

// Legacy command mappings
const COMMAND_MAPPINGS = {
  // Environment/Security Auditing Commands
  'audit:qb': {
    legacy: ['env-auditor', 'audit-env', 'env:audit'],
    command: 'npm run security:audit && npm run security:check',
    description: 'Environment and security audit (legacy: Env Auditor)'
  },
  
  // E2E Testing Commands  
  'e2e:jt': {
    legacy: ['e2e-smoke', 'smoke-e2e', 'e2e:smoke'],
    command: 'npm run e2e:smoke',
    description: 'End-to-end smoke tests (legacy: E2E Smoke)'
  },
  
  // Database Setup Commands
  'db:wire': {
    legacy: ['db-setup', 'setup-db', 'db:setup', 'schema:setup'],
    command: 'npm run schema:drift',
    description: 'Database setup and schema validation (legacy: DB setup)'
  }
};

// Set up CLI commands
program
  .name('botctl-compat')
  .description('Bot Control Compatibility Layer (DEPRECATED)')
  .version('1.0.0');

// Add individual command mappings
Object.entries(COMMAND_MAPPINGS).forEach(([newCmd, config]) => {
  config.legacy.forEach(legacyCmd => {
    program
      .command(legacyCmd)
      .description(`${config.description} → ${newCmd}`)
      .action(() => {
        executeCommand(config.command, legacyCmd, newCmd);
      });
  });
});

// Add the new command names as well (forwards to npm scripts)
Object.entries(COMMAND_MAPPINGS).forEach(([newCmd, config]) => {
  program
    .command(newCmd)
    .description(config.description)
    .action(() => {
      console.log(colors.green(`✅ Running new command: ${newCmd}`));
      console.log(colors.blue(`🔄 Executing: ${config.command}\n`));
      
      try {
        execSync(config.command, { 
          stdio: 'inherit',
          cwd: process.cwd() 
        });
      } catch (error: any) {
        console.error(colors.red(`❌ Command failed: ${config.command}`));
        process.exit(error.status || 1);
      }
    });
});

// Help command showing migration guide
program
  .command('migrate-help')
  .description('Show migration guide for legacy commands')
  .action(() => {
    console.log(colors.blue('\n📘 Bot Control Migration Guide\n'));
    console.log('Legacy commands have been consolidated under botctl with new names:\n');
    
    Object.entries(COMMAND_MAPPINGS).forEach(([newCmd, config]) => {
      console.log(colors.green(`  ${newCmd}`));
      console.log(colors.gray(`    Description: ${config.description}`));
      console.log(colors.gray(`    Legacy names: ${config.legacy.join(', ')}`));
      console.log(colors.gray(`    Command: ${config.command}\n`));
    });
    
    console.log(colors.yellow('⚠️  Timeline:'));
    console.log(colors.gray('   • Legacy commands work via shims (current)'));
    console.log(colors.gray('   • Removal in 60 days'));
    console.log(colors.gray('   • Update your scripts and CI/CD pipelines\n'));
  });

// Export the mappings for use in shim scripts
export { COMMAND_MAPPINGS, executeCommand, colors };

// CLI entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  program.parse();
}