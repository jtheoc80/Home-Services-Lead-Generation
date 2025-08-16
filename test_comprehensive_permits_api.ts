#!/usr/bin/env tsx

/**
 * Comprehensive test for the new permits/permits/ingest API
 * Tests all the functionality specified in the problem statement
 */

import { createClient } from '@supabase/supabase-js';

// Test environment variables (use same as the original test)
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('Missing required environment variables:');
  console.error('- NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL');
  console.error('- SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function testUpsertPermitWithP() {
  console.log('🧪 Testing upsert_permit function with parameter p...');
  
  // Test data matching the new Normalized interface
  const testPermit = {
    source: 'test_p',
    source_record_id: 'test_p_001',
    permit_number: 'TEST-P-2025-001',
    issued_date: '2025-01-15T10:00:00Z',
    permit_type: 'Building',
    work_description: 'Test permit for parameter p',
    address: '123 Test P St',
    city: 'Test City',
    county: 'Test County',
    zipcode: '12345',
    latitude: 30.2672,
    longitude: -97.7431,
    valuation: 50000,
    applicant_name: 'Test P Applicant',
    contractor_name: 'Test P Contractor',
    status: 'Issued'
  };
  
  try {
    // Test insert with parameter 'p'
    console.log('  Testing insert with parameter p...');
    const { data: insertData, error: insertError } = await supabase.rpc('upsert_permit', {
      p: testPermit
    });
    
    if (insertError) {
      console.error('  ❌ Insert with p failed:', insertError.message);
      return false;
    }
    
    console.log('  ✅ Insert with p successful:', insertData);
    
    // Test update with parameter 'p'
    console.log('  Testing update with parameter p...');
    const updatedPermit = {
      ...testPermit,
      valuation: 75000,
      status: 'Final Inspection'
    };
    
    const { data: updateData, error: updateError } = await supabase.rpc('upsert_permit', {
      p: updatedPermit
    });
    
    if (updateError) {
      console.error('  ❌ Update with p failed:', updateError.message);
      return false;
    }
    
    console.log('  ✅ Update with p successful:', updateData);
    
    // Clean up test data
    await supabase
      .from('permits')
      .delete()
      .eq('source', 'test_p')
      .eq('source_record_id', 'test_p_001');
    
    return true;
  } catch (error) {
    console.error('  ❌ Test failed:', error);
    return false;
  }
}

async function testNewAPI() {
  console.log('🌐 Testing new /api/permits/permits/ingest endpoint...');
  
  const baseUrl = 'http://localhost:3000/api/permits/permits/ingest';
  
  try {
    // Test 1: Austin dry run (default source)
    console.log('  Test 1: Austin dry run (default source)...');
    const austinResponse = await fetch(`${baseUrl}?dry=1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!austinResponse.ok) {
      console.error('  ❌ Austin dry run failed:', austinResponse.status);
      return false;
    }
    
    const austinData = await austinResponse.json();
    console.log('  ✅ Austin dry run successful:', {
      ok: austinData.ok,
      source: austinData.source,
      fetched: austinData.fetched,
      dry: austinData.dry,
      beforeCount: austinData.beforeCount,
      afterCount: austinData.afterCount,
      sample: austinData.sample?.length || 0
    });
    
    // Test 2: Dallas dry run
    console.log('  Test 2: Dallas dry run...');
    const dallasResponse = await fetch(`${baseUrl}?source=dallas&dry=1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!dallasResponse.ok) {
      console.error('  ❌ Dallas dry run failed:', dallasResponse.status);
      return false;
    }
    
    const dallasData = await dallasResponse.json();
    console.log('  ✅ Dallas dry run successful:', {
      ok: dallasData.ok,
      source: dallasData.source,
      fetched: dallasData.fetched,
      dry: dallasData.dry,
      beforeCount: dallasData.beforeCount,
      afterCount: dallasData.afterCount,
      sample: dallasData.sample?.length || 0
    });
    
    // Test 3: Invalid source
    console.log('  Test 3: Invalid source...');
    const invalidResponse = await fetch(`${baseUrl}?source=invalid`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (invalidResponse.status !== 400) {
      console.error('  ❌ Invalid source test failed: Expected 400 status');
      return false;
    }
    
    const invalidData = await invalidResponse.json();
    console.log('  ✅ Invalid source test passed:', invalidData.error);
    
    // Test 4: Response structure validation
    console.log('  Test 4: Response structure validation...');
    if (!austinData.hasOwnProperty('ok') || 
        !austinData.hasOwnProperty('source') ||
        !austinData.hasOwnProperty('fetched') ||
        !austinData.hasOwnProperty('dry') ||
        !austinData.hasOwnProperty('upserts') ||
        !austinData.hasOwnProperty('beforeCount') ||
        !austinData.hasOwnProperty('afterCount') ||
        !austinData.hasOwnProperty('sample') ||
        !austinData.hasOwnProperty('errors')) {
      console.error('  ❌ Response structure validation failed: Missing required fields');
      return false;
    }
    
    console.log('  ✅ Response structure validation passed');
    
    return true;
  } catch (error) {
    console.error('  ❌ API test failed:', error);
    return false;
  }
}

async function testSourceMapping() {
  console.log('🗺️  Testing SOURCE_KEY mapping...');
  
  const baseUrl = 'http://localhost:3000/api/permits/permits/ingest';
  
  try {
    // Test Austin mapping
    const austinResponse = await fetch(`${baseUrl}?source=austin&dry=1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    const austinData = await austinResponse.json();
    if (austinData.source !== 'austin_socrata') {
      console.error('  ❌ Austin mapping failed. Expected: austin_socrata, Got:', austinData.source);
      return false;
    }
    
    // Test Dallas mapping
    const dallasResponse = await fetch(`${baseUrl}?source=dallas&dry=1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    const dallasData = await dallasResponse.json();
    if (dallasData.source !== 'dallas_socrata') {
      console.error('  ❌ Dallas mapping failed. Expected: dallas_socrata, Got:', dallasData.source);
      return false;
    }
    
    console.log('  ✅ SOURCE_KEY mapping works correctly');
    return true;
  } catch (error) {
    console.error('  ❌ Source mapping test failed:', error);
    return false;
  }
}

async function main() {
  console.log('🚀 Starting Comprehensive Permits/Permits/Ingest API Tests\n');
  
  const tests = [
    { name: 'Upsert Function (parameter p)', fn: testUpsertPermitWithP },
    { name: 'API Endpoint', fn: testNewAPI },
    { name: 'Source Mapping', fn: testSourceMapping },
  ];
  
  let passed = 0;
  let failed = 0;
  
  for (const test of tests) {
    console.log(`\n--- ${test.name} ---`);
    try {
      const result = await test.fn();
      if (result) {
        passed++;
        console.log(`✅ ${test.name} passed\n`);
      } else {
        failed++;
        console.log(`❌ ${test.name} failed\n`);
      }
    } catch (error) {
      failed++;
      console.log(`❌ ${test.name} failed with error:`, error);
    }
  }
  
  console.log('\n📊 Test Results:');
  console.log(`  ✅ Passed: ${passed}`);
  console.log(`  ❌ Failed: ${failed}`);
  console.log(`  📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);
  
  if (failed > 0) {
    console.log('\n⚠️  Some tests failed. This might be expected if:');
    console.log('  - The development server is not running');
    console.log('  - The upsert_permit function with parameter p is not deployed');
    console.log('  - Environment variables are not configured');
    console.log('  - External APIs (Austin/Dallas) are not accessible');
  } else {
    console.log('\n🎉 All tests passed! The implementation is working correctly.');
  }
}

if (require.main === module) {
  main().catch(console.error);
}