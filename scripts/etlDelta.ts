#!/usr/bin/env tsx

/**
 * ETL Delta Smoke Test Script
 * 
 * Tests the Harris County ETL pipeline by:
 * 1. Reading current count from permits_raw_harris
 * 2. Fetching permits from last 7 days and upserting
 * 3. Verifying that new rows were added
 * 4. Exiting with appropriate status code
 */

import { fetchHarrisIssuedPermits } from './harrisPermitsFetcher';
import { supabaseUpsert, createSupabaseClient } from './supabaseUpsert';

interface CountResult {
  count: number;
}

/**
 * Get current count from permits_raw_harris table
 */
async function getCurrentCount(): Promise<number> {
  const supabase = createSupabaseClient();
  
  const { data, error, count } = await supabase
    .from('permits_raw_harris')
    .select('*', { count: 'exact', head: true });
  
  if (error) {
    throw new Error(`Failed to get current count from permits_raw_harris: ${error.message}`);
  }
  
  return count || 0;
}

/**
 * Main ETL Delta test function
 */
async function main(): Promise<void> {
  try {
    console.log('🚀 Starting Harris County ETL Delta Test');
    console.log('=====================================');
    
    // Calculate timestamp for 7 days ago
    const sevenDaysAgo = Date.now() - (7 * 24 * 3600 * 1000);
    const sevenDaysAgoDate = new Date(sevenDaysAgo);
    
    console.log(`📅 Fetching permits since: ${sevenDaysAgoDate.toISOString()}`);
    console.log('');
    
    // Step 1: Get current count
    console.log('📊 Step 1: Getting current count from permits_raw_harris...');
    const oldCount = await getCurrentCount();
    console.log(`Current count: ${oldCount}`);
    console.log('');
    
    // Step 2: Fetch new permits
    console.log('🔍 Step 2: Fetching Harris County permits...');
    const permits = await fetchHarrisIssuedPermits(sevenDaysAgo);
    console.log(`Fetched ${permits.length} permits from Harris County`);
    console.log('');
    
    // Step 3: Upsert permits
    console.log('💾 Step 3: Upserting permits to permits_raw_harris...');
    await supabaseUpsert('permits_raw_harris', permits, 'event_id');
    console.log('');
    
    // Step 4: Get new count and verify delta
    console.log('📈 Step 4: Verifying delta...');
    const newCount = await getCurrentCount();
    const delta = newCount - oldCount;
    
    console.log(`Old count: ${oldCount}`);
    console.log(`New count: ${newCount}`);
    console.log(`Delta: ${delta}`);
    console.log('');
    
    // Step 5: Assert and report results
    if (delta > 0) {
      console.log('✅ SUCCESS: ETL Delta test passed');
      console.log(`📈 Inserted/Updated: ${delta} rows`);
      console.log('');
      
      // Log summary for monitoring
      const summary = {
        timestamp: new Date().toISOString(),
        test: 'etl-delta',
        status: 'success',
        oldCount,
        newCount,
        delta,
        permitsFetched: permits.length,
        sinceDate: sevenDaysAgoDate.toISOString()
      };
      
      console.log('📋 Summary:', JSON.stringify(summary, null, 2));
      process.exit(0);
      
    } else {
      console.log('❌ FAILURE: ETL Delta test failed');
      console.log(`📉 No new rows were inserted/updated (delta: ${delta})`);
      console.log('');
      
      // Log failure summary for monitoring
      const summary = {
        timestamp: new Date().toISOString(),
        test: 'etl-delta',
        status: 'failure',
        oldCount,
        newCount,
        delta,
        permitsFetched: permits.length,
        sinceDate: sevenDaysAgoDate.toISOString(),
        error: 'No new rows inserted/updated'
      };
      
      console.log('📋 Summary:', JSON.stringify(summary, null, 2));
      process.exit(1);
    }
    
  } catch (error: any) {
    console.error('❌ ETL Delta test failed with error:', error.message);
    console.error('');
    
    // Log error summary for monitoring
    const summary = {
      timestamp: new Date().toISOString(),
      test: 'etl-delta',
      status: 'error',
      error: error.message,
      sinceDate: new Date(Date.now() - (7 * 24 * 3600 * 1000)).toISOString()
    };
    
    console.log('📋 Summary:', JSON.stringify(summary, null, 2));
    process.exit(1);
  }
}

// Only run main if this script is executed directly (ESM compatible check)
if (process.argv[1] && process.argv[1].endsWith('etlDelta.ts') || process.argv[1].endsWith('etlDelta.js')) {
  main();
}