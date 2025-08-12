#!/usr/bin/env node

/**
 * Shim for npm run audit:qb
 * 
 * This shim imports the new botctl audit-qb module and calls it directly.
 * This provides a safe migration path from old commands to new botctl commands.
 */

const path = require('path');

// Import the new botctl module
const auditQb = require('./botctl/commands/audit-qb.cjs');

async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const options = {
      verbose: args.includes('--verbose'),
      dryRun: args.includes('--dry-run')
    };

    console.log('🔄 Running QuickBooks audit via botctl...');
    
    // Call the new botctl command
    const result = await auditQb.execute(options);
    
    console.log('✅ QuickBooks audit completed successfully');
    process.exit(0);
  } catch (error) {
    console.error('❌ QuickBooks audit failed:', error.message);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = main;