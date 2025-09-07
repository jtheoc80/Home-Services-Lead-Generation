#!/usr/bin/env tsx

/**
 * Test script for ETL run logging functionality
 * 
 * This script tests the logEtlRun and logEtlError functions
 * without requiring the full ETL pipeline to run.
 * 
 * Usage: 
 *   SUPABASE_URL=<url> SUPABASE_SERVICE_ROLE_KEY=<key> npx tsx scripts/test-etl-logging.ts
 */

import { logEtlRun, logEtlError } from './lib/logEtlRun';

async function testSuccessfulRun() {
  console.log('🧪 Testing successful ETL run logging...');
  
  try {
    const result = await logEtlRun({
      source_system: "test_system",
      fetched: 100,
      parsed: 95,
      upserted: 90,
      errors: 0,
      first_issue_date: "2024-01-01",
      last_issue_date: "2024-01-07",
      status: 'success',
      duration_ms: 5000
    });
    
    console.log('✅ Successfully logged ETL run:', {
      id: result.id,
      source_system: result.source_system,
      status: result.status,
      upserted: result.upserted
    });
    
    return result.id;
  } catch (error) {
    console.error('❌ Failed to log successful ETL run:', error instanceof Error ? error.message : String(error));
    throw error;
  }
}

async function testErrorRun() {
  console.log('🧪 Testing error ETL run logging...');
  
  try {
    const result = await logEtlError(
      "test_system",
      "Test error message - connection timeout",
      2500
    );
    
    console.log('✅ Successfully logged error ETL run:', {
      id: result.id,
      source_system: result.source_system,
      status: result.status,
      error_message: result.error_message
    });
    
    return result.id;
  } catch (error) {
    console.error('❌ Failed to log error ETL run:', error instanceof Error ? error.message : String(error));
    throw error;
  }
}

async function testEnvironmentValidation() {
  console.log('🧪 Testing environment variable validation...');
  
  // Save original values
  const originalUrl = process.env.SUPABASE_URL;
  const originalKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  try {
    // Test missing URL
    delete process.env.SUPABASE_URL;
    try {
      await logEtlRun({
        source_system: "test_system",
        fetched: 1,
        parsed: 1,
        upserted: 1,
        errors: 0
      });
      console.error('❌ Should have thrown error for missing SUPABASE_URL');
    } catch (error) {
      if (error instanceof Error && error.message.includes('SUPABASE_URL')) {
        console.log('✅ Correctly caught missing SUPABASE_URL error');
      } else {
        throw error;
      }
    }
    
    // Restore URL, test missing key
    process.env.SUPABASE_URL = originalUrl;
    delete process.env.SUPABASE_SERVICE_ROLE_KEY;
    try {
      await logEtlRun({
        source_system: "test_system",
        fetched: 1,
        parsed: 1,
        upserted: 1,
        errors: 0
      });
      console.error('❌ Should have thrown error for missing SUPABASE_SERVICE_ROLE_KEY');
    } catch (error) {
      if (error instanceof Error && error.message.includes('SUPABASE_SERVICE_ROLE_KEY')) {
        console.log('✅ Correctly caught missing SUPABASE_SERVICE_ROLE_KEY error');
      } else {
        throw error;
      }
    }
    
  } finally {
    // Restore original values
    if (originalUrl) process.env.SUPABASE_URL = originalUrl;
    if (originalKey) process.env.SUPABASE_SERVICE_ROLE_KEY = originalKey;
  }
}

async function main() {
  console.log('🚀 ETL Run Logging Test Suite');
  console.log('==============================');
  
  try {
    // Check environment variables
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
      console.log('⚠️  Missing required environment variables for database testing');
      console.log('   Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to test database integration');
      console.log('   Running environment validation tests only...');
      console.log('');
      
      await testEnvironmentValidation();
      
      console.log('');
      console.log('✅ Environment validation tests passed');
      console.log('🔧 To test database integration, set the required environment variables');
      return;
    }
    
    console.log('🔗 Database connection configured, running full test suite...');
    console.log('');
    
    // Test environment validation
    await testEnvironmentValidation();
    console.log('');
    
    // Test successful run logging
    const successId = await testSuccessfulRun();
    console.log('');
    
    // Test error run logging  
    const errorId = await testErrorRun();
    console.log('');
    
    console.log('🎉 All tests passed successfully!');
    console.log(`   Success run ID: ${successId}`);
    console.log(`   Error run ID: ${errorId}`);
    
  } catch (error) {
    console.error('💥 Test suite failed:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Unhandled error in test suite:', error);
  process.exit(1);
});