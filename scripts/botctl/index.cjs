#!/usr/bin/env node

/**
 * Botctl - Bot Control Command Interface
 * 
 * A unified command interface for common bot and automation tasks.
 * This modular design allows individual commands to be imported and called directly.
 */

const { Command } = require('commander');
const path = require('path');

// Import command modules
const auditQb = require('./commands/audit-qb.cjs');
const dbWire = require('./commands/db-wire.cjs');
const e2eJt = require('./commands/e2e-jt.cjs');

const program = new Command();

program
  .name('botctl')
  .description('Bot Control - Unified command interface for automation tasks')
  .version('1.0.0');

// Register commands
program
  .command('audit:qb')
  .description('Run QuickBooks audit operations')
  .option('--verbose', 'Enable verbose output')
  .option('--dry-run', 'Run in dry-run mode without making changes')
  .action(async (options) => {
    try {
      await auditQb.execute(options);
    } catch (error) {
      console.error('❌ audit:qb failed:', error.message);
      process.exit(1);
    }
  });

program
  .command('db:wire')
  .description('Execute database wiring operations')
  .option('--target <target>', 'Specific target to wire (default: all)')
  .option('--check', 'Check wiring status without making changes')
  .action(async (options) => {
    try {
      await dbWire.execute(options);
    } catch (error) {
      console.error('❌ db:wire failed:', error.message);
      process.exit(1);
    }
  });

program
  .command('e2e:jt')
  .description('Run JT-specific end-to-end tests')
  .option('--env <environment>', 'Target environment (local, staging, production)', 'local')
  .option('--headless', 'Run tests in headless mode', true)
  .option('--reporter <reporter>', 'Test reporter (json, junit, html)', 'json')
  .action(async (options) => {
    try {
      await e2eJt.execute(options);
    } catch (error) {
      console.error('❌ e2e:jt failed:', error.message);
      process.exit(1);
    }
  });

// Export for programmatic use
module.exports = {
  auditQb,
  dbWire,
  e2eJt,
  program
};

// CLI execution
if (require.main === module) {
  program.parse();
}