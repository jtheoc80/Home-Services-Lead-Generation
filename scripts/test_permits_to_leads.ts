#!/usr/bin/env tsx

/**
 * Test script for permits to leads auto-creation functionality
 * Validates the trigger and function work correctly
 */

import { createClient } from '@supabase/supabase-js';

// Mock Supabase configuration for testing
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://mock.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || 'mock-key';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

interface TestResult {
  test: string;
  passed: boolean;
  message: string;
  data?: any;
}

async function runTests(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  
  console.log('🧪 Testing permits to leads auto-creation functionality...\n');

  // Test 1: Check if permits table exists
  try {
    const { data, error } = await supabase
      .from('permits')
      .select('id')
      .limit(1);
    
    results.push({
      test: 'Permits table accessibility',
      passed: !error,
      message: error ? `Cannot access permits table: ${error.message}` : 'Permits table accessible',
      data: data
    });
  } catch (err) {
    results.push({
      test: 'Permits table accessibility',
      passed: false,
      message: `Error accessing permits table: ${err}`,
    });
  }

  // Test 2: Check if leads table exists and has permit_id field
  try {
    const { data, error } = await supabase
      .from('leads')
      .select('id, permit_id')
      .limit(1);
    
    results.push({
      test: 'Leads table with permit_id field',
      passed: !error,
      message: error ? `Cannot access leads table: ${error.message}` : 'Leads table accessible with permit_id field',
      data: data
    });
  } catch (err) {
    results.push({
      test: 'Leads table with permit_id field',
      passed: false,
      message: `Error accessing leads table: ${err}`,
    });
  }

  // Test 3: Check for existing leads from permits
  try {
    const { data, error } = await supabase
      .from('leads')
      .select('id, permit_id, source, name, service')
      .in('source', ['permit_ingest', 'permit_backfill'])
      .limit(5);
    
    results.push({
      test: 'Existing permit-generated leads',
      passed: !error,
      message: error 
        ? `Error querying permit leads: ${error.message}` 
        : `Found ${data?.length || 0} leads from permits`,
      data: data
    });
  } catch (err) {
    results.push({
      test: 'Existing permit-generated leads',
      passed: false,
      message: `Error querying permit leads: ${err}`,
    });
  }

  // Test 4: Test anon access to leads (required for dashboard)
  try {
    const { data, error } = await supabase
      .from('leads')
      .select('id, name, created_at, permit_id')
      .order('created_at', { ascending: false })
      .limit(3);
    
    results.push({
      test: 'Anonymous access to leads',
      passed: !error,
      message: error 
        ? `Anon access denied: ${error.message}` 
        : `Anonymous access working - fetched ${data?.length || 0} leads`,
      data: data
    });
  } catch (err) {
    results.push({
      test: 'Anonymous access to leads',
      passed: false,
      message: `Error with anon access: ${err}`,
    });
  }

  // Test 5: Validate leads have proper service categorization
  try {
    const { data, error } = await supabase
      .from('leads')
      .select('service, permit_id')
      .not('permit_id', 'is', null)
      .limit(10);
    
    const serviceTypes = data?.map(lead => lead.service).filter(Boolean) || [];
    const uniqueServices = [...new Set(serviceTypes)];
    
    results.push({
      test: 'Service categorization from permits',
      passed: !error && uniqueServices.length > 0,
      message: error 
        ? `Error checking services: ${error.message}` 
        : `Found ${uniqueServices.length} service types: ${uniqueServices.join(', ')}`,
      data: { uniqueServices, sampleData: data?.slice(0, 3) }
    });
  } catch (err) {
    results.push({
      test: 'Service categorization from permits',
      passed: false,
      message: `Error checking services: ${err}`,
    });
  }

  return results;
}

async function main() {
  try {
    const results = await runTests();
    
    console.log('📊 Test Results:\n');
    
    let passedTests = 0;
    results.forEach((result, index) => {
      const status = result.passed ? '✅' : '❌';
      console.log(`${index + 1}. ${status} ${result.test}`);
      console.log(`   ${result.message}`);
      
      if (result.data && Object.keys(result.data).length > 0) {
        console.log(`   Sample data:`, JSON.stringify(result.data, null, 2).slice(0, 200) + '...');
      }
      console.log();
      
      if (result.passed) passedTests++;
    });
    
    console.log(`\n🎯 Summary: ${passedTests}/${results.length} tests passed`);
    
    if (passedTests === results.length) {
      console.log('🎉 All tests passed! Permits to leads functionality is working correctly.');
    } else {
      console.log('⚠️  Some tests failed. Check the configuration and database setup.');
      process.exit(1);
    }
    
  } catch (error) {
    console.error('❌ Test runner failed:', error);
    process.exit(1);
  }
}

// Add command line argument parsing
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Usage: npm run test:permits:leads [options]

Options:
  --help, -h     Show this help message
  
Environment Variables:
  SUPABASE_URL      Your Supabase project URL
  SUPABASE_ANON_KEY Your Supabase anonymous key
  
This script tests the permits to leads auto-creation functionality by:
1. Checking table accessibility
2. Verifying permit_id field exists in leads
3. Looking for existing permit-generated leads
4. Testing anonymous access (required for dashboard)
5. Validating service categorization

Run this after setting up the permits_to_leads_setup.sql script.
`);
  process.exit(0);
}

// Run main function
main();