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
 *   tsx scripts/e2e_supabase_delta.ts
 * 
 * Environment Variables:
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 */

import { createClient } from '@supabase/supabase-js';
import { spawn } from 'child_process';
import { randomUUID } from 'crypto';

interface TestResult {
  success: boolean;
  message: string;
  initialCount: number;
  finalCount: number;
  deltaCount: number;
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

async function runHarrisScraperWithSupabase(): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log('🚀 Running Harris scraper with --since=3d...');
    
    // Use the TypeScript Harris scraper which writes directly to Supabase
    const child = spawn('tsx', ['scripts/harrisCounty/issuedPermits.ts', '--since', '3d'], {
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

async function runTest(): Promise<TestResult> {
  console.log('🏠 E2E Supabase Delta Test for Harris County Permits');
  console.log('='.repeat(60));
  
  // Validate environment
  const { supabaseUrl, supabaseKey } = validateEnvironment();
  
  console.log(`📊 Supabase URL: ${supabaseUrl}`);
  console.log('');
  
  // Initialize Supabase client
  const supabase = createClient(supabaseUrl, supabaseKey);
  
  try {
    // Step 1: Get initial count
    console.log('📈 Step 1: Reading initial count from permits_raw_harris...');
    const initialCount = await getPermitsCount(supabase);
    console.log(`   Initial count: ${initialCount}`);
    
    // Step 2: Run Harris scraper with Supabase sink
    console.log('\n🔄 Step 2: Running Harris scraper for --since=3d...');
    await runHarrisScraperWithSupabase();
    
    // Step 3: Get final count
    console.log('\n📊 Step 3: Reading final count from permits_raw_harris...');
    const finalCount = await getPermitsCount(supabase);
    console.log(`   Final count: ${finalCount}`);
    
    // Step 4: Calculate delta and assert
    const deltaCount = finalCount - initialCount;
    console.log(`   Delta: +${deltaCount}`);
    
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
    const result = await runTest();
    
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    console.log('\n' + '='.repeat(60));
    console.log('📋 TEST RESULTS');
    console.log('='.repeat(60));
    console.log(result.message);
    console.log(`⏱️  Duration: ${duration}s`);
    console.log(`📊 Summary: ${result.initialCount} → ${result.finalCount} (${result.deltaCount >= 0 ? '+' : ''}${result.deltaCount})`);
    
    if (result.success) {
      console.log('\n🎉 E2E test completed successfully!');
      process.exit(0);
    } else {
      console.log('\n💥 E2E test failed!');
      console.log('');
      console.log('🔍 Possible causes:');
      console.log('   • No new permits available in the last 3 days');
      console.log('   • Harris County API is down or rate-limited');
      console.log('   • Supabase connection issues');
      console.log('   • Scraper configuration problems');
      console.log('   • Table permissions or RLS policies blocking writes');
      console.log('');
      console.log('🛠️  Troubleshooting:');
      console.log('   • Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables');
      console.log('   • Verify permits_raw_harris table exists and is accessible');
      console.log('   • Try running the Harris scraper manually with: tsx scripts/harrisCounty/issuedPermits.ts --since 3d');
      console.log('   • Check Supabase logs for any errors');
      
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