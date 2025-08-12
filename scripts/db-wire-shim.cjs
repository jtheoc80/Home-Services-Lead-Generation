#!/usr/bin/env node

/**
 * Shim for npm run db:wire
 * 
 * This shim imports the new botctl db-wire module and calls it directly.
 * This provides a safe migration path from old commands to new botctl commands.
 */

const path = require('path');

// Import the new botctl module
const dbWire = require('./botctl/commands/db-wire.cjs');

async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    
    let target = 'all';
    const targetIndex = args.indexOf('--target');
    if (targetIndex !== -1 && args[targetIndex + 1]) {
      target = args[targetIndex + 1];
    }
    
    const options = {
      target,
      check: args.includes('--check'),
      verbose: args.includes('--verbose')
    };

    console.log('🔄 Running database wiring via botctl...');
    
    // Call the new botctl command
    const result = await dbWire.execute(options);
    
    console.log('✅ Database wiring completed successfully');
    process.exit(0);
  } catch (error) {
    console.error('❌ Database wiring failed:', error.message);
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