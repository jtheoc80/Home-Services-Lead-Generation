#!/usr/bin/env tsx

/**
 * Test script for the new nested permits ingest API
 * Tests the /api/permits/permits/ingest endpoint with query parameters
 */

async function testNewIngestAPI() {
  console.log('🧪 Testing new permits/permits/ingest API...');
  
  const baseUrl = 'http://localhost:3000/api/permits/permits/ingest';
  
  try {
    // Test 1: Dry run with Austin source
    console.log('  Test 1: Dry run with Austin source...');
    const austinDryResponse = await fetch(`${baseUrl}?source=austin&dry=1`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!austinDryResponse.ok) {
      console.error('  ❌ Austin dry run failed:', austinDryResponse.status, austinDryResponse.statusText);
      return false;
    }
    
    const austinDryData = await austinDryResponse.json();
    console.log('  ✅ Austin dry run successful:', {
      ok: austinDryData.ok,
      source: austinDryData.source,
      fetched: austinDryData.fetched,
      dry: austinDryData.dry,
      upserts: austinDryData.upserts
    });
    
    // Test 2: Dry run with Dallas source
    console.log('  Test 2: Dry run with Dallas source...');
    const dallasDryResponse = await fetch(`${baseUrl}?source=dallas&dry=1`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!dallasDryResponse.ok) {
      console.error('  ❌ Dallas dry run failed:', dallasDryResponse.status, dallasDryResponse.statusText);
      return false;
    }
    
    const dallasDryData = await dallasDryResponse.json();
    console.log('  ✅ Dallas dry run successful:', {
      ok: dallasDryData.ok,
      source: dallasDryData.source,
      fetched: dallasDryData.fetched,
      dry: dallasDryData.dry,
      upserts: dallasDryData.upserts
    });
    
    // Test 3: Test invalid source
    console.log('  Test 3: Invalid source test...');
    const invalidResponse = await fetch(`${baseUrl}?source=invalid`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (invalidResponse.status !== 400) {
      console.error('  ❌ Invalid source test failed: Expected 400 status');
      return false;
    }
    
    const invalidData = await invalidResponse.json();
    console.log('  ✅ Invalid source test successful:', {
      ok: invalidData.ok,
      error: invalidData.error
    });
    
    return true;
  } catch (error) {
    console.error('  ❌ API test failed:', error);
    return false;
  }
}

async function main() {
  console.log('🚀 Starting New Permits Ingest API Tests\n');
  
  const result = await testNewIngestAPI();
  
  if (result) {
    console.log('\n✅ All tests passed!');
  } else {
    console.log('\n❌ Some tests failed');
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}