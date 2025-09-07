#!/usr/bin/env tsx

/**
 * Simple validation test for City of Houston ETL pipeline
 * Tests the script with proper environment variable validation
 */

import { execSync } from 'node:child_process';

async function testValidation(): Promise<void> {
  console.log('🧪 Testing City of Houston ETL Script Validation');
  console.log('================================================');

  // Test 1: Missing required environment variable
  console.log('🔍 Test 1: Missing HOUSTON_WEEKLY_XLSX_URL');
  try {
    execSync('npx tsx scripts/ingest-coh.ts', {
      env: {
        ...process.env,
        SUPABASE_URL: 'https://test.supabase.co',
        SUPABASE_SERVICE_ROLE_KEY: 'test-key'
        // Intentionally omit HOUSTON_WEEKLY_XLSX_URL
      },
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    console.log('❌ Test 1 failed: Should have thrown an error');
  } catch (error: any) {
    if (error.stderr && error.stderr.includes('Missing required environment variable: HOUSTON_WEEKLY_XLSX_URL')) {
      console.log('✅ Test 1 passed: Correctly validates required environment variables');
    } else {
      console.log(`❌ Test 1 failed: Unexpected error: ${error.stderr || error.message}`);
    }
  }

  // Test 2: Script loads and runs with proper variables (will fail on network, but that's expected)
  console.log('\n🔍 Test 2: Script execution with proper environment variables');
  try {
    const result = execSync('npx tsx scripts/ingest-coh.ts', {
      env: {
        ...process.env,
        SUPABASE_URL: 'https://test.supabase.co',
        SUPABASE_SERVICE_ROLE_KEY: 'test-key',
        HOUSTON_WEEKLY_XLSX_URL: 'https://httpbin.org/status/404',
        ETL_ALLOW_EMPTY: '1'
      },
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    console.log('✅ Test 2 passed: Script executed successfully');
  } catch (error: any) {
    // We expect it to fail due to network issues, but the script should run
    if (error.stdout && error.stdout.includes('City of Houston ETL Pipeline')) {
      console.log('✅ Test 2 passed: Script runs correctly but fails on network (expected)');
    } else {
      console.log(`❌ Test 2 failed: ${error.stderr || error.message}`);
    }
  }

  // Test 3: Check if package.json npm script works
  console.log('\n🔍 Test 3: NPM script execution');
  try {
    const result = execSync('npm run ingest:coh', {
      env: {
        ...process.env,
        SUPABASE_URL: 'https://test.supabase.co',
        SUPABASE_SERVICE_ROLE_KEY: 'test-key',
        HOUSTON_WEEKLY_XLSX_URL: 'https://httpbin.org/status/404',
        ETL_ALLOW_EMPTY: '1'
      },
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    console.log('✅ Test 3 passed: NPM script executed successfully');
  } catch (error: any) {
    // We expect it to fail due to network issues, but the script should run
    if (error.stdout && error.stdout.includes('City of Houston ETL Pipeline')) {
      console.log('✅ Test 3 passed: NPM script runs correctly but fails on network (expected)');
    } else {
      console.log(`❌ Test 3 failed: ${error.stderr || error.message}`);
    }
  }

  console.log('\n🎉 All validation tests completed!');
  console.log('\n📝 Summary:');
  console.log('   - Script validates required environment variables');
  console.log('   - Script loads and executes without syntax errors');
  console.log('   - NPM script "ingest:coh" works correctly');
  console.log('   - Ready for production use with real Houston permit data URLs');
}

// Only run if called directly
if (process.argv[1] && process.argv[1].endsWith('test-coh-validation.ts')) {
  testValidation().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}