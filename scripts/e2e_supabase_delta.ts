#!/usr/bin/env tsx
/**
 * E2E Supabase Delta Test for Harris County Permits
 * 
 * This script:
 * 1. Reads initial count from public.permits_raw_harris via Supabase REST/service role
 * 2. Runs the Harris scraper for --since=3d with Supabase sink enabled
 * 3. Re-reads the count and asserts newCount > oldCount
 * 4. Exits non-zero with readable errors if assertions fail
 * 
 * Usage:
 *   tsx scripts/e2e_supabase_delta.ts [--since=3d] [--dry-run]
 * 
 * Options:
 *   --since=<period>    Time period to scrape (default: 3d). Examples: 1d, 7d, 24h
 *   --dry-run          Only test Supabase connection and count reading, skip scraper
 * 
 * Environment Variables:
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 */

import { createClient } from '@supabase/supabase-js';
import { spawn } from 'child_process';

interface TestResult {
  success: boolean;
  message: string;
  initialCount: number;
  finalCount: number;
  deltaCount: number;
}

interface TestOptions {
  since: string;
  dryRun: boolean;
}

function parseArgs(): TestOptions {
  const args = process.argv.slice(2);
  const options: TestOptions = {
    since: '3d',
    dryRun: false
  };
  
  for (const arg of args) {
    if (arg.startsWith('--since=')) {
      options.since = arg.split('=')[1];
    } else if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Usage: tsx scripts/e2e_supabase_delta.ts [options]

Options:
  --since=<period>    Time period to scrape (default: 3d)
                      Examples: 1d, 7d, 24h, 2024-01-01
  --dry-run          Only test Supabase connection, skip scraper
  --help, -h         Show this help message

Environment Variables:
  SUPABASE_URL               Supabase project URL
  SUPABASE_SERVICE_ROLE_KEY  Supabase service role key

Examples:
  tsx scripts/e2e_supabase_delta.ts
  tsx scripts/e2e_supabase_delta.ts --since=7d
  tsx scripts/e2e_supabase_delta.ts --dry-run
      `);
      process.exit(0);
    }
  }
  
  return options;
}

function validateEnvironment(): { supabaseUrl: string; supabaseKey: string } {
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  if (!supabaseUrl) {
    console.error('❌ Missing required environment variable: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');
    process.exit(1);
  }
  
  if (!supabaseKey) {
    console.error('❌ Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');
    process.exit(1);
  }
  
  return { supabaseUrl, supabaseKey };
}

async function getPermitsCount(supabase: any): Promise<number> {
  try {
    const { count, error } = await supabase
      .from('permits_raw_harris')
      .select('*', { count: 'exact', head: true });
    
    if (error) {
      throw new Error(`Supabase query error: ${error.message}`);
    }
    
    return count || 0;
  } catch (error: any) {
    throw new Error(`Failed to get permits count: ${error.message}`);
  }
}

async function runHarrisScraperWithSupabase(since: string): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log(`🚀 Running Harris scraper with --since=${since}...`);
    
    // Use the TypeScript Harris scraper which writes directly to Supabase
    const child = spawn('tsx', ['scripts/harrisCounty/issuedPermits.ts', '--since', since], {
      stdio: 'inherit',
      cwd: process.cwd()
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        console.log('✅ Harris scraper completed successfully');
        resolve();
      } else {
        reject(new Error(`Harris scraper failed with exit code ${code}`));
      }
    });
    
    child.on('error', (error) => {
      reject(new Error(`Failed to start Harris scraper: ${error.message}`));
    });
  });
}

async function runTest(options: TestOptions): Promise<TestResult> {
  console.log('🏠 E2E Supabase Delta Test for Harris County Permits');
  console.log('='.repeat(60));
  
  // Validate environment
  const { supabaseUrl, supabaseKey } = validateEnvironment();
  
  console.log(`📊 Supabase URL: ${supabaseUrl}`);
  console.log(`⏱️  Since: ${options.since}`);
  console.log(`🧪 Mode: ${options.dryRun ? 'DRY RUN (Supabase test only)' : 'FULL TEST'}`);
  console.log('');
  
  // Initialize Supabase client
  const supabase = createClient(supabaseUrl, supabaseKey);
  
  try {
    // Step 1: Get initial count
    console.log('📈 Step 1: Reading initial count from permits_raw_harris...');
    const initialCount = await getPermitsCount(supabase);
    console.log(`   Initial count: ${initialCount}`);
    
    if (options.dryRun) {
      console.log('\n🧪 DRY RUN: Skipping scraper execution');
      return {
        success: true,
        message: `✅ DRY RUN PASSED: Successfully connected to Supabase and read count (${initialCount})`,
        initialCount,
        finalCount: initialCount,
        deltaCount: 0
      };
    }
    
    // Step 2: Run Harris scraper with Supabase sink
    console.log(`\n🔄 Step 2: Running Harris scraper for --since=${options.since}...`);
    await runHarrisScraperWithSupabase(options.since);
    
    // Wait a moment for data to settle
    console.log('⏳ Waiting 2 seconds for data to settle...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Step 3: Get final count
    console.log('\n📊 Step 3: Reading final count from permits_raw_harris...');
    const finalCount = await getPermitsCount(supabase);
    console.log(`   Final count: ${finalCount}`);
    
    // Step 4: Calculate delta and assert
    const deltaCount = finalCount - initialCount;
    console.log(`   Delta: ${deltaCount >= 0 ? '+' : ''}${deltaCount}`);
    
    // Assertion: newCount > oldCount
    if (finalCount > initialCount) {
      return {
        success: true,
        message: `✅ Test PASSED: Final count (${finalCount}) > Initial count (${initialCount}), Delta: +${deltaCount}`,
        initialCount,
        finalCount,
        deltaCount
      };
    } else {
      return {
        success: false,
        message: `❌ Test FAILED: Final count (${finalCount}) <= Initial count (${initialCount}), Delta: ${deltaCount}`,
        initialCount,
        finalCount,
        deltaCount
      };
    }
    
  } catch (error: any) {
    return {
      success: false,
      message: `❌ Test ERROR: ${error.message}`,
      initialCount: 0,
      finalCount: 0,
      deltaCount: 0
    };
  }
}

async function main() {
  const startTime = Date.now();
  
  try {
    // Parse command line arguments
    const options = parseArgs();
    
    const result = await runTest(options);
    
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    console.log('\n' + '='.repeat(60));
    console.log('📋 TEST RESULTS');
    console.log('='.repeat(60));
    console.log(result.message);
    console.log(`⏱️  Duration: ${duration}s`);
    console.log(`📊 Summary: ${result.initialCount} → ${result.finalCount} (${result.deltaCount >= 0 ? '+' : ''}${result.deltaCount})`);
    
    if (result.success) {
      console.log(`\n🎉 E2E test completed successfully!${options.dryRun ? ' (DRY RUN)' : ''}`);
      process.exit(0);
    } else {
      console.log('\n💥 E2E test failed!');
      console.log('');
      console.log('🔍 Possible causes:');
      console.log(`   • No new permits available in the last ${options.since}`);
      console.log('   • Harris County API is down or rate-limited');
      console.log('   • Supabase connection issues');
      console.log('   • Scraper configuration problems');
      console.log('   • Table permissions or RLS policies blocking writes');
      console.log('');
      console.log('🛠️  Troubleshooting:');
      console.log('   • Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables');
      console.log('   • Verify permits_raw_harris table exists and is accessible');
      console.log(`   • Try running the Harris scraper manually with: tsx scripts/harrisCounty/issuedPermits.ts --since ${options.since}`);
      console.log('   • Check Supabase logs for any errors');
      console.log('   • Try a longer time period with --since=7d or --since=30d');
      console.log('   • Use --dry-run to test just the Supabase connection');
      
      process.exit(1);
    }
    
  } catch (error: any) {
    console.error('\n💥 Fatal error during E2E test:');
    console.error(error.message);
    console.error('\nStack trace:');
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the main function
main();