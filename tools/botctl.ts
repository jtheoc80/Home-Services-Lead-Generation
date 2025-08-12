#!/usr/bin/env tsx

/**
 * Bot Control CLI
 * 
 * Main CLI tool that registers subcommands and delegates to the three bots:
 * - db:wire → dbWire.main()
 * - e2e:jt → jtSmoke.main()
 * - audit:qb → qbAuditor.main()
 */

import { program } from 'commander';
import { main as dbWireMain } from './bots/dbWire.ts';
import { main as jtSmokeMain } from './bots/jtSmoke.ts';
import { main as qbAuditorMain } from './bots/qbAuditor.ts';

/**
 * Setup and configure the CLI commands
 */
function setupCommands() {
  program
    .name('botctl')
    .description('Bot Control CLI - Orchestrates database, E2E testing, and audit bots')
    .version('1.0.0');

  // db:wire command
  program
    .command('db:wire')
    .description('Run database wiring bot - performs connectivity and health checks')
    .action(async () => {
      console.log('🤖 Launching DB Wire Bot...');
      try {
        await dbWireMain(['node', 'db-wire']);
        process.exit(0);
      } catch (error) {
        console.error('❌ DB Wire Bot failed:', error);
        process.exit(1);
      }
    });

  // e2e:jt command  
  program
    .command('e2e:jt')
    .description('Run E2E testing bot - performs smoke tests on lead ingestion pipeline')
    .requiredOption('--baseUrl <url>', 'Base URL of the application (e.g., https://your-app.vercel.app)')
    .option('--timeout <ms>', 'Request timeout in milliseconds', '30000')
    .action(async (options) => {
      console.log('🤖 Launching JT Smoke Bot...');
      try {
        const args = ['node', 'jt-smoke', '--baseUrl', options.baseUrl];
        if (options.timeout) {
          args.push('--timeout', options.timeout);
        }
        await jtSmokeMain(args);
        process.exit(0);
      } catch (error) {
        console.error('❌ JT Smoke Bot failed:', error);
        process.exit(1);
      }
    });

  // audit:qb command
  program
    .command('audit:qb')
    .description('Run QB auditing bot - compares local and live database schemas')
    .option('--output-dir <dir>', 'Directory to write migration files', '.')
    .action(async (options) => {
      console.log('🤖 Launching QB Auditor Bot...');
      try {
        const args = ['node', 'qb-auditor'];
        if (options.outputDir && options.outputDir !== '.') {
          args.push('--output-dir', options.outputDir);
        }
        await qbAuditorMain(args);
        process.exit(0);
      } catch (error) {
        console.error('❌ QB Auditor Bot failed:', error);
        process.exit(1);
      }
    });

  // List all available bots
  program
    .command('list')
    .description('List all available bots and their descriptions')
    .action(() => {
      console.log('🤖 Available Bots:');
      console.log('==================');
      console.log('');
      console.log('📊 db:wire     - Database Wiring Bot');
      console.log('   └─ Performs database connectivity and health checks');
      console.log('   └─ Tests table access, read/write operations');
      console.log('   └─ Environment: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY');
      console.log('');
      console.log('🧪 e2e:jt      - E2E Testing Bot (JT Smoke)');
      console.log('   └─ Tests complete lead ingestion pipeline');
      console.log('   └─ Validates POST /api/leads and GET /api/leads/recent');
      console.log('   └─ Requires: --baseUrl parameter');
      console.log('');
      console.log('🔍 audit:qb    - Schema Auditing Bot (QB Auditor)');
      console.log('   └─ Compares local models.sql with live database schema');
      console.log('   └─ Generates migration SQL for schema drift');
      console.log('   └─ Environment: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY');
      console.log('');
      console.log('Usage Examples:');
      console.log('  botctl db:wire');
      console.log('  botctl e2e:jt --baseUrl https://your-app.vercel.app');
      console.log('  botctl audit:qb');
      console.log('  botctl list');
    });

  // Health check command - runs all bots in check mode
  program
    .command('health')
    .description('Run health checks across all bots (where applicable)')
    .option('--baseUrl <url>', 'Base URL for E2E testing (optional)')
    .action(async (options) => {
      console.log('🏥 Running Bot Health Checks...');
      console.log('===============================');
      
      let overallHealth = true;
      const results: { bot: string; status: 'PASS' | 'FAIL' | 'SKIP'; error?: string }[] = [];

      // 1. DB Wire Health Check
      console.log('\n1️⃣ Running DB Wire health check...');
      try {
        await dbWireMain(['node', 'db-wire']);
        results.push({ bot: 'db:wire', status: 'PASS' });
        console.log('✅ DB Wire: HEALTHY');
      } catch (error) {
        results.push({ bot: 'db:wire', status: 'FAIL', error: String(error) });
        console.log('❌ DB Wire: UNHEALTHY');
        overallHealth = false;
      }

      // 2. QB Auditor Health Check
      console.log('\n2️⃣ Running QB Auditor schema check...');
      try {
        await qbAuditorMain(['node', 'qb-auditor']);
        results.push({ bot: 'audit:qb', status: 'PASS' });
        console.log('✅ QB Auditor: NO DRIFT');
      } catch (error) {
        // QB Auditor exits with 1 for schema drift, 2 for actual errors
        const errorStr = String(error);
        if (errorStr.includes('exit code 1')) {
          results.push({ bot: 'audit:qb', status: 'FAIL', error: 'Schema drift detected' });
          console.log('⚠️ QB Auditor: SCHEMA DRIFT DETECTED');
        } else {
          results.push({ bot: 'audit:qb', status: 'FAIL', error: errorStr });
          console.log('❌ QB Auditor: ERROR');
          overallHealth = false;
        }
      }

      // 3. E2E Testing (if baseUrl provided)
      if (options.baseUrl) {
        console.log('\n3️⃣ Running E2E smoke test...');
        try {
          await jtSmokeMain(['node', 'jt-smoke', '--baseUrl', options.baseUrl]);
          results.push({ bot: 'e2e:jt', status: 'PASS' });
          console.log('✅ JT Smoke: PASSED');
        } catch (error) {
          results.push({ bot: 'e2e:jt', status: 'FAIL', error: String(error) });
          console.log('❌ JT Smoke: FAILED');
          overallHealth = false;
        }
      } else {
        results.push({ bot: 'e2e:jt', status: 'SKIP', error: 'No baseUrl provided' });
        console.log('\n3️⃣ Skipping E2E test (no --baseUrl provided)');
      }

      // Summary
      console.log('\n📋 Health Check Summary:');
      console.log('========================');
      results.forEach(result => {
        const icon = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '⏭️';
        console.log(`${icon} ${result.bot}: ${result.status}${result.error ? ` (${result.error})` : ''}`);
      });

      console.log(`\n🏥 Overall Health: ${overallHealth ? '✅ HEALTHY' : '❌ NEEDS ATTENTION'}`);
      
      process.exit(overallHealth ? 0 : 1);
    });
}

/**
 * Main CLI entry point
 */
async function main() {
  try {
    setupCommands();
    
    // Handle unhandled errors
    process.on('unhandledRejection', (reason, promise) => {
      console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
      process.exit(1);
    });

    process.on('uncaughtException', (error) => {
      console.error('💥 Uncaught Exception:', error);
      process.exit(1);
    });

    // Parse CLI arguments
    await program.parseAsync(process.argv);
    
  } catch (error) {
    console.error('❌ BotCtl failed:', error);
    process.exit(1);
  }
}

// Only run if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { main };