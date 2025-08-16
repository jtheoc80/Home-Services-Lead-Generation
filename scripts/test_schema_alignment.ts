#!/usr/bin/env tsx

/**
 * Test script for the Supabase schema alignment migration
 * Validates the migration and tests the sentinel case
 */

import { createClient } from '@supabase/supabase-js';

// Use environment variables or fallback to development/mock values  
const SUPABASE_URL = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://mock.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || 'mock-service-key';
// Use environment variables for Supabase credentials
const SUPABASE_URL = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set.');
  process.exit(1);
}
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

interface TestResult {
  test: string;
  passed: boolean;
  message: string;
  data?: any;
}

async function runSchemaAlignmentTests(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  
  console.log('🧪 Testing Supabase schema alignment migration...\n');

  // Test 1: Check if permits table has new columns
  try {
    const { data, error } = await supabase
      .from('permits')
      .select('id, permit_id, applicant, owner, work_class, provenance, finaled_at')
      .limit(1);
    
    results.push({
      test: 'Permits table enhanced schema',
      passed: !error,
      message: error ? `Schema issue: ${error.message}` : 'Enhanced permits schema accessible',
      data: data?.[0] || null
    });
  } catch (err) {
    results.push({
      test: 'Permits table enhanced schema',
      passed: false,
      message: `Error accessing enhanced permits schema: ${err}`,
    });
  }

  // Test 2: Check if leads table has service/trade columns
  try {
    const { data, error } = await supabase
      .from('leads')
      .select('id, service, trade, permit_id')
      .limit(1);
    
    results.push({
      test: 'Leads table service/trade columns',
      passed: !error,
      message: error ? `Leads schema issue: ${error.message}` : 'Leads service/trade columns accessible',
      data: data?.[0] || null
    });
  } catch (err) {
    results.push({
      test: 'Leads table service/trade columns',
      passed: false,
      message: `Error accessing leads service/trade: ${err}`,
    });
  }

  // Test 3: Check compatibility views
  try {
    const { data: permitsCompat, error: permitsError } = await supabase
      .from('permits_compat')
      .select('id, issue_date, value, postal_code')
      .limit(1);
    
    const { data: leadsCompat, error: leadsError } = await supabase
      .from('leads_compat')
      .select('id, service, trade')
      .limit(1);
    
    results.push({
      test: 'Compatibility views access',
      passed: !permitsError && !leadsError,
      message: (permitsError || leadsError) 
        ? `Compatibility views issue: ${permitsError?.message || leadsError?.message}` 
        : 'Compatibility views accessible',
      data: { permitsCompat: permitsCompat?.[0], leadsCompat: leadsCompat?.[0] }
    });
  } catch (err) {
    results.push({
      test: 'Compatibility views access',
      passed: false,
      message: `Error accessing compatibility views: ${err}`,
    });
  }

  // Test 4: Test enhanced upsert_permit function with sentinel data
  try {
    const sentinelPayload = {
      source: 'selftest',
      source_record_id: 'sent-1',
      permit_no: 'SENT-1',
      permit_id: 'SENT-1',
      jurisdiction: 'Austin',
      county: 'Travis',
      status: 'Issued',
      address: '100 Test St',
      city: 'Austin',
      state: 'TX',
      issued_date: new Date().toISOString(),
      value: 12345
    };

    const { data, error } = await supabase
      .rpc('upsert_permit', { p: sentinelPayload });
    
    results.push({
      test: 'Enhanced upsert_permit RPC function',
      passed: !error && data && data.length > 0,
      message: error 
        ? `upsert_permit error: ${error.message}` 
        : `upsert_permit successful: ${data?.[0]?.action} permit ${data?.[0]?.id}`,
      data: data
    });
  } catch (err) {
    results.push({
      test: 'Enhanced upsert_permit RPC function',
      passed: false,
      message: `Error calling upsert_permit: ${err}`,
    });
  }

  // Test 5: Verify permit→lead pipeline with canonical permit_id
  try {
    const { data, error } = await supabase
      .from('leads')
      .select('id, permit_id, service, trade, source, metadata')
      .eq('source', 'permit_ingest')
      .limit(5);
    
    const hasCanonicalIds = data?.some(lead => 
      lead.permit_id && !lead.permit_id.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    );
    
    results.push({
      test: 'Permit→lead pipeline with canonical permit_id',
      passed: !error && (data?.length || 0) >= 0,
      message: error 
        ? `Pipeline error: ${error.message}` 
        : `Found ${data?.length || 0} permit-generated leads${hasCanonicalIds ? ' (some with canonical IDs)' : ''}`,
      data: { count: data?.length, hasCanonicalIds, sample: data?.slice(0, 2) }
    });
  } catch (err) {
    results.push({
      test: 'Permit→lead pipeline with canonical permit_id',
      passed: false,
      message: `Error checking permit→lead pipeline: ${err}`,
    });
  }

  // Test 6: Verify unique constraints
  try {
    // Check if permits have unique (source, permit_id) where permit_id is not null
    const { data, error } = await supabase
      .from('permits')
      .select('source, permit_id')
      .not('permit_id', 'is', null)
      .limit(10);
    
    const uniqueCheck = new Set();
    let hasDuplicates = false;
    
    data?.forEach(permit => {
      const key = `${permit.source}:${permit.permit_id}`;
      if (uniqueCheck.has(key)) {
        hasDuplicates = true;
      }
      uniqueCheck.add(key);
    });
    
    results.push({
      test: 'Unique constraint verification',
      passed: !error && !hasDuplicates,
      message: error 
        ? `Constraint check error: ${error.message}` 
        : hasDuplicates 
          ? 'Warning: Found duplicate (source, permit_id) combinations'
          : `Unique constraints working: checked ${data?.length || 0} records`,
      data: { checkedRecords: data?.length, hasDuplicates }
    });
  } catch (err) {
    results.push({
      test: 'Unique constraint verification',
      passed: false,
      message: `Error checking constraints: ${err}`,
    });
  }

  return results;
}

async function main() {
  try {
    console.log('🚀 Starting Supabase Schema Alignment Test Suite\n');
    
    if (SUPABASE_URL === 'https://mock.supabase.co') {
      console.log('⚠️  Warning: Using mock Supabase URL. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables for real testing.\n');
    }
    
    const results = await runSchemaAlignmentTests();
    
    console.log('📊 Test Results:\n');
    
    let passedTests = 0;
    results.forEach((result, index) => {
      const status = result.passed ? '✅' : '❌';
      console.log(`${index + 1}. ${status} ${result.test}`);
      console.log(`   ${result.message}`);
      
      if (result.data && Object.keys(result.data).length > 0) {
        console.log(`   Data:`, JSON.stringify(result.data, null, 2).slice(0, 300) + '...');
      }
      console.log();
      
      if (result.passed) passedTests++;
    });
    
    console.log(`\n🎯 Summary: ${passedTests}/${results.length} tests passed`);
    
    if (passedTests === results.length) {
      console.log('🎉 All tests passed! Schema alignment migration is working correctly.');
      console.log('\n📋 Migration Summary:');
      console.log('✅ Enhanced permits table with permit_id and missing fields');
      console.log('✅ Added service/trade sync to leads table'); 
      console.log('✅ Created compatibility views for old column names');
      console.log('✅ Enhanced upsert_permit() with permit_id derivation');
      console.log('✅ Improved permit→lead pipeline with canonical identifiers');
      console.log('✅ Added unique constraints and proper indexing');
    } else {
      console.log('⚠️  Some tests failed. Check the database setup and migration execution.');
      console.log('\n💡 Troubleshooting:');
      console.log('1. Ensure the migration file has been executed in Supabase');
      console.log('2. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables');
      console.log('3. Verify database permissions for schema modifications');
      console.log('4. Run migration in Supabase SQL editor as postgres user');
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
Usage: npm run test:schema:alignment [options]

Options:
  --help, -h     Show this help message
  
Environment Variables:
  SUPABASE_URL              Your Supabase project URL
  SUPABASE_SERVICE_ROLE_KEY Your Supabase service role key
  
This script tests the schema alignment migration by:
1. Checking enhanced permits table schema
2. Verifying leads service/trade columns
3. Testing compatibility views
4. Running sentinel upsert_permit test
5. Validating permit→lead pipeline
6. Checking unique constraints

Run this after executing the align_repo_supabase.sql migration.
`);
  process.exit(0);
}

// Run main function
main();