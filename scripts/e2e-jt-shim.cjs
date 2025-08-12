#!/usr/bin/env node

/**
 * Shim for npm run e2e:jt
 * 
 * This shim imports the new botctl e2e-jt module and calls it directly.
 * This provides a safe migration path from old commands to new botctl commands.
 */

const path = require('path');

// Import the new botctl module
const e2eJt = require('./botctl/commands/e2e-jt.cjs');

async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    
    let env = 'local';
    const envIndex = args.indexOf('--env');
    if (envIndex !== -1 && args[envIndex + 1]) {
      env = args[envIndex + 1];
    }
    
    let reporter = 'json';
    const reporterIndex = args.indexOf('--reporter');
    if (reporterIndex !== -1 && args[reporterIndex + 1]) {
      reporter = args[reporterIndex + 1];
    }
    
    const options = {
      env,
      headless: !args.includes('--headed'),
      reporter,
      verbose: args.includes('--verbose')
    };

    console.log('🔄 Running JT E2E tests via botctl...');
    
    // Call the new botctl command
    const result = await e2eJt.execute(options);
    
    console.log('✅ JT E2E tests completed successfully');
    process.exit(0);
  } catch (error) {
    console.error('❌ JT E2E tests failed:', error.message);
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