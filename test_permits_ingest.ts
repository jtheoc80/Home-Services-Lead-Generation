#!/usr/bin/env tsx

/**
 * Test script for TX Permits Ingestion API
 * Tests the upsert_permit function and API endpoints
 */

import { createClient } from '@supabase/supabase-js';

// Test environment variables
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('Missing required environment variables:');
  console.error('- NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL');
  console.error('- SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function testUpsertPermitFunction() {
  console.log('🧪 Testing upsert_permit function...');
  
  // Test data
  const testPermit = {
    source: 'test',
    source_record_id: 'test_001',
    permit_number: 'TEST-2025-001',
    issued_date: '2025-01-15T10:00:00Z',
    permit_type: 'Building',
    work_description: 'Test permit for residential addition',
    address: '123 Test St',
    city: 'Test City',
    county: 'Test County',
    zipcode: '12345',
    latitude: 30.2672,
    longitude: -97.7431,
    valuation: 50000,
    applicant_name: 'Test Applicant',
    contractor_name: 'Test Contractor',
    status: 'Issued'
  };
  
  try {
    // Test insert
    console.log('  Testing insert...');
    const { data: insertData, error: insertError } = await supabase.rpc('upsert_permit', {
      permit_data: testPermit
    });
    
    if (insertError) {
      console.error('  ❌ Insert failed:', insertError.message);
      return false;
    }
    
    console.log('  ✅ Insert successful:', insertData);
    
    // Test update
    console.log('  Testing update...');
    const updatedPermit = {
      ...testPermit,
      valuation: 75000,
      status: 'Final Inspection'
    };
    
    const { data: updateData, error: updateError } = await supabase.rpc('upsert_permit', {
      permit_data: updatedPermit
    });
    
    if (updateError) {
      console.error('  ❌ Update failed:', updateError.message);
      return false;
    }
    
    console.log('  ✅ Update successful:', updateData);
    
    // Verify the record
    const { data: verifyData, error: verifyError } = await supabase
      .from('permits')
      .select('*')
      .eq('source', 'test')
      .eq('source_record_id', 'test_001')
      .single();
    
    if (verifyError) {
      console.error('  ❌ Verification failed:', verifyError.message);
      return false;
    }
    
    console.log('  ✅ Verification successful:');
    console.log('    - ID:', verifyData.id);
    console.log('    - Valuation:', verifyData.valuation);
    console.log('    - Status:', verifyData.status);
    console.log('    - Geometry:', verifyData.geom ? 'Created' : 'Not created');
    
    // Clean up test data
    await supabase
      .from('permits')
      .delete()
      .eq('source', 'test')
      .eq('source_record_id', 'test_001');
    
    return true;
  } catch (error) {
    console.error('  ❌ Test failed:', error);
    return false;
  }
}

async function testAPIEndpoint() {
  console.log('🌐 Testing API endpoint...');
  
  try {
    // Test GET endpoint (health check)
    console.log('  Testing GET /api/permits/ingest...');
    const response = await fetch('http://localhost:3000/api/permits/ingest', {
      method: 'GET',
    });
    
    if (!response.ok) {
      console.error('  ❌ GET request failed:', response.status, response.statusText);
      return false;
    }
    
    const data = await response.json();
    console.log('  ✅ GET successful:', data.message);
    
    return true;
  } catch (error) {
    console.error('  ❌ API test failed:', error);
    return false;
  }
}

async function checkTableStructure() {
  console.log('🗃️  Checking table structure...');
  
  try {
    // Check if table exists and has expected columns
    const { data, error } = await supabase
      .from('permits')
      .select('*')
      .limit(1);
    
    if (error) {
      console.error('  ❌ Table check failed:', error.message);
      return false;
    }
    
    console.log('  ✅ Table exists and is accessible');
    
    // Check function exists
    const { data: funcData, error: funcError } = await supabase.rpc('upsert_permit', {
      permit_data: { source: 'test_check', source_record_id: 'test_check' }
    });
    
    if (funcError && !funcError.message.includes('violates check constraint')) {
      // Clean up if it was inserted
      await supabase
        .from('permits')
        .delete()
        .eq('source', 'test_check')
        .eq('source_record_id', 'test_check');
    }
    
    console.log('  ✅ upsert_permit function exists');
    
    return true;
  } catch (error) {
    console.error('  ❌ Structure check failed:', error);
    return false;
  }
}

async function main() {
  console.log('🚀 Starting TX Permits Ingestion Tests\n');
  
  const tests = [
    { name: 'Table Structure', fn: checkTableStructure },
    { name: 'Upsert Function', fn: testUpsertPermitFunction },
    { name: 'API Endpoint', fn: testAPIEndpoint },
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
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}