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



/**
 * E2E Supabase Delta Test
 * 
 * Tests data changes (deltas) in Supabase database to validate ETL pipeline results.
 * This script verifies that recent data ingestion is working properly by:
 * 1. Checking for recent records in permits table
 * 2. Validating data integrity and schema compliance
 * 3. Testing query performance on key indexes
 * 4. Verifying data freshness against expected thresholds
 * 
 * Environment Variables:
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Service role key for database access
 * 
 * Usage: tsx scripts/e2e_supabase_delta.ts [--threshold-hours=24]
 * Exit codes: 0 = success, 1 = test failed, 2 = error
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { program } from 'commander';

interface DeltaTestConfig {
  thresholdHours: number;
  supabaseUrl: string;
  supabaseKey: string;
}

interface TestResult {
  test: string;
  passed: boolean;
  message: string;
  data?: any;
}

interface PermitsStats {
  total_count: number;
  recent_count: number;
  latest_record_date: string | null;
  oldest_record_date: string | null;
}

/**
 * Validate required environment variables
 */

function validateEnvironment(): { supabaseUrl: string; supabaseKey: string } {
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  if (!supabaseUrl) {
    console.error('❌ Missing required environment variable: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');

    process.exit(1);

    process.exit(2);

  }
  
  if (!supabaseKey) {
    console.error('❌ Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');

    process.exit(1);

    process.exit(2);

  }
  
  return { supabaseUrl, supabaseKey };
}

async function getPermitsCount(supabase: SupabaseClient): Promise<number> {
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
    const localTsxPath = path.join(process.cwd(), 'node_modules', '.bin', 'tsx');
    const tsxCmd = fs.existsSync(localTsxPath) ? localTsxPath : 'tsx';
    const child = spawn(tsxCmd, ['scripts/harrisCounty/issuedPermits.ts', '--since', since], {
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

/**
 * Test database connectivity
 */
async function testConnectivity(supabase: SupabaseClient): Promise<TestResult> {
  try {
    const { data, error } = await supabase
      .from('permits_raw_harris')
      .select('event_id', { count: 'exact', head: true })
      .limit(1);
    
    if (error) {
      return {
        test: 'Database Connectivity',
        passed: false,
        message: `Failed to connect to Supabase: ${error.message}`,
        data: { error: error.code }
      };
    }
    
    return {
      test: 'Database Connectivity',
      passed: true,
      message: 'Successfully connected to Supabase database',
      data: { table: 'permits_raw_harris' }
    };
    
  } catch (error: any) {
    return {
      test: 'Database Connectivity',
      passed: false,
      message: `Connection error: ${error.message}`,
      data: { error: error.name }
    };
  }
}

/**
 * Get permits statistics for the delta analysis
 */
async function getPermitsStats(supabase: SupabaseClient, thresholdHours: number): Promise<PermitsStats> {
  const thresholdDate = new Date();
  thresholdDate.setHours(thresholdDate.getHours() - thresholdHours);
  
  // Get total count
  const { count: totalCount, error: totalError } = await supabase
    .from('permits_raw_harris')
    .select('*', { count: 'exact', head: true });
  
  if (totalError) {
    throw new Error(`Failed to get total count: ${totalError.message}`);
  }
  
  // Get recent count
  const { count: recentCount, error: recentError } = await supabase
    .from('permits_raw_harris')
    .select('*', { count: 'exact', head: true })
    .gte('created_at', thresholdDate.toISOString());
  
  if (recentError) {
    throw new Error(`Failed to get recent count: ${recentError.message}`);
  }
  
  // Get date range
  const { data: dateRange, error: dateError } = await supabase
    .from('permits_raw_harris')
    .select('created_at')
    .order('created_at', { ascending: false })
    .limit(1);
  
  const { data: oldestDate, error: oldestError } = await supabase
    .from('permits_raw_harris')
    .select('created_at')
    .order('created_at', { ascending: true })
    .limit(1);
  
  if (dateError || oldestError) {
    throw new Error(`Failed to get date range: ${dateError?.message || oldestError?.message}`);
  }
  
  return {
    total_count: totalCount || 0,
    recent_count: recentCount || 0,
    latest_record_date: dateRange?.[0]?.created_at || null,
    oldest_record_date: oldestDate?.[0]?.created_at || null
  };
}

/**
 * Test data freshness
 */
async function testDataFreshness(supabase: SupabaseClient, thresholdHours: number): Promise<TestResult> {
  try {
    const stats = await getPermitsStats(supabase, thresholdHours);
    
    const isDataFresh = stats.recent_count > 0;
    const latestAge = stats.latest_record_date 
      ? (Date.now() - new Date(stats.latest_record_date).getTime()) / (1000 * 60 * 60)
      : null;
    
    return {
      test: 'Data Freshness',
      passed: isDataFresh,
      message: isDataFresh 
        ? `Found ${stats.recent_count} records within ${thresholdHours} hours (latest: ${latestAge?.toFixed(1)}h ago)`
        : `No records found within ${thresholdHours} hours. Latest record: ${latestAge ? `${latestAge.toFixed(1)}h ago` : 'none'}`,
      data: {
        recent_count: stats.recent_count,
        threshold_hours: thresholdHours,
        latest_age_hours: latestAge
      }
    };
    
  } catch (error: any) {
    return {
      test: 'Data Freshness',
      passed: false,
      message: `Error checking data freshness: ${error.message}`,
      data: { error: error.name }
    };
  }
}

/**
 * Test data integrity
 */
async function testDataIntegrity(supabase: SupabaseClient): Promise<TestResult> {
  try {
    // Check for required fields and data quality
    const { data: sampleRecords, error } = await supabase
      .from('permits_raw_harris')
      .select('event_id, permit_number, issue_date, full_address, created_at')
      .order('created_at', { ascending: false })
      .limit(10);
    
    if (error) {
      return {
        test: 'Data Integrity',
        passed: false,
        message: `Failed to fetch sample records: ${error.message}`,
        data: { error: error.code }
      };
    }
    
    if (!sampleRecords || sampleRecords.length === 0) {
      return {
        test: 'Data Integrity',
        passed: false,
        message: 'No records found in permits table',
        data: { sample_count: 0 }
      };
    }
    
    // Check data quality metrics
    const validEventIds = sampleRecords.filter(r => r.event_id && r.event_id.trim().length > 0);
    const validDates = sampleRecords.filter(r => r.issue_date && !isNaN(Date.parse(r.issue_date)));
    const hasAddresses = sampleRecords.filter(r => r.full_address && r.full_address.trim().length > 0);
    
    const qualityScore = (validEventIds.length + validDates.length + hasAddresses.length) / (sampleRecords.length * 3);
    const qualityPercentage = Math.round(qualityScore * 100);
    
    const isPassing = qualityScore >= 0.7; // At least 70% data quality
    
    return {
      test: 'Data Integrity',
      passed: isPassing,
      message: `Data quality: ${qualityPercentage}% (${validEventIds.length}/${sampleRecords.length} valid IDs, ${validDates.length}/${sampleRecords.length} valid dates, ${hasAddresses.length}/${sampleRecords.length} with addresses)`,
      data: {
        sample_count: sampleRecords.length,
        quality_score: qualityPercentage,
        valid_event_ids: validEventIds.length,
        valid_dates: validDates.length,
        has_addresses: hasAddresses.length
      }
    };
    
  } catch (error: any) {
    return {
      test: 'Data Integrity',
      passed: false,
      message: `Error checking data integrity: ${error.message}`,
      data: { error: error.name }
    };
  }
}

/**
 * Test query performance on key indexes
 */
async function testQueryPerformance(supabase: SupabaseClient): Promise<TestResult> {
  try {
    const startTime = Date.now();
    
    // Test indexed query performance
    const { data, error } = await supabase
      .from('permits_raw_harris')
      .select('event_id, issue_date, app_type')
      .gte('issue_date', '2024-01-01')
      .order('issue_date', { ascending: false })
      .limit(100);
    
    const queryTime = Date.now() - startTime;
    
    if (error) {
      return {
        test: 'Query Performance',
        passed: false,
        message: `Query failed: ${error.message}`,
        data: { error: error.code, query_time_ms: queryTime }
      };
    }
    
    const isPerformant = queryTime < 5000; // Should complete within 5 seconds
    
    return {
      test: 'Query Performance',
      passed: isPerformant,
      message: `Query completed in ${queryTime}ms (${data?.length || 0} records)`,
      data: {
        query_time_ms: queryTime,
        records_returned: data?.length || 0,
        performance_threshold_ms: 5000
      }
    };
    
  } catch (error: any) {
    return {
      test: 'Query Performance',
      passed: false,
      message: `Error testing query performance: ${error.message}`,
      data: { error: error.name }
    };
  }
}

/**
 * Test schema compliance
 */
async function testSchemaCompliance(supabase: SupabaseClient): Promise<TestResult> {
  try {
    // Check if all expected columns exist by running a query
    const { data, error } = await supabase
      .from('permits_raw_harris')
      .select('event_id, permit_number, permit_name, app_type, issue_date, project_number, full_address, street_number, street_name, status, raw, created_at, updated_at')
      .limit(1);
    
    if (error) {
      return {
        test: 'Schema Compliance',
        passed: false,
        message: `Schema validation failed: ${error.message}`,
        data: { error: error.code }
      };
    }
    
    return {
      test: 'Schema Compliance',
      passed: true,
      message: 'All expected columns present and accessible',
      data: { columns_checked: 13 }
    };
    
  } catch (error: any) {
    return {
      test: 'Schema Compliance',
      passed: false,
      message: `Error checking schema compliance: ${error.message}`,
      data: { error: error.name }
    };
  }
}

/**
 * Run all delta tests
 */
async function runDeltaTests(config: DeltaTestConfig): Promise<TestResult[]> {
  console.log('🔗 Initializing Supabase client...');
  const supabase = createClient(config.supabaseUrl, config.supabaseKey);
  
  console.log('🧪 Running Supabase delta tests...\n');
  
  const tests: Array<() => Promise<TestResult>> = [
    () => testConnectivity(supabase),
    () => testDataFreshness(supabase, config.thresholdHours),
    () => testDataIntegrity(supabase),
    () => testQueryPerformance(supabase),
    () => testSchemaCompliance(supabase)
  ];
  
  const results: TestResult[] = [];
  
  for (const test of tests) {
    const result = await test();
    results.push(result);
    
    const status = result.passed ? '✅' : '❌';
    console.log(`${status} ${result.test}: ${result.message}`);
  }
  
  return results;
}

/**
 * Main execution function
 */
async function main(): Promise<void> {
  const options = program.opts();
  const thresholdHours = parseInt(options.thresholdHours) || 24;
  
  console.log('🔍 E2E Supabase Delta Test');
  console.log('==========================');
  console.log(`⏰ Started at: ${new Date().toISOString()}`);
  console.log(`🕐 Data freshness threshold: ${thresholdHours} hours`);
  console.log('');
  
  try {
    // Validate environment
    const { supabaseUrl, supabaseKey } = validateEnvironment();
    
    const config: DeltaTestConfig = {
      thresholdHours,
      supabaseUrl,
      supabaseKey
    };
    
    // Run tests
    const startTime = Date.now();
    const results = await runDeltaTests(config);
    const duration = Date.now() - startTime;
    
    // Summary
    const passed = results.filter(r => r.passed).length;
    const total = results.length;
    const allPassed = passed === total;
    
    console.log('\n📊 Test Summary');
    console.log('===============');
    console.log(`⌚ Duration: ${duration}ms`);
    console.log(`✅ Passed: ${passed}/${total}`);
    console.log(`❌ Failed: ${total - passed}/${total}`);
    
    if (allPassed) {
      console.log('\n🎉 All Supabase delta tests PASSED!');
      console.log('✅ ETL pipeline data integrity verified');
      process.exit(0);
    } else {
      console.log('\n💥 Some Supabase delta tests FAILED!');
      console.log('❌ ETL pipeline may have data issues');
      
      // Print failed test details
      const failed = results.filter(r => !r.passed);
      failed.forEach(result => {
        console.log(`\n🔍 ${result.test} Details:`);
        console.log(`   Message: ${result.message}`);
        if (result.data) {
          console.log(`   Data: ${JSON.stringify(result.data, null, 2)}`);
        }
      });

      
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

    console.error('\n💥 Unexpected error during delta testing:');
    console.error(`   ${error.message}`);
    console.error(`   Stack: ${error.stack}`);
    process.exit(2);
  }
}

// CLI setup
program
  .name('e2e_supabase_delta')
  .description('E2E test for Supabase data delta validation')
  .option('--threshold-hours <hours>', 'Hours threshold for data freshness check', '24')
  .action(main);

// Error handlers
process.on('unhandledRejection', (reason, promise) => {
  console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(2);
});

process.on('uncaughtException', (error) => {
  console.error('💥 Uncaught Exception:', error);
  process.exit(2);
});

// Parse CLI arguments and run
program.parse();

