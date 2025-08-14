#!/usr/bin/env node

/**
 * Test script for the leads/recent API endpoint
 * Tests both backend proxy and Supabase fallback functionality
 */

console.log('🧪 Testing leads/recent API endpoint...');

async function testApiEndpoint() {
  const baseUrl = process.env.TEST_BASE_URL || 'http://localhost:3000';
  const apiUrl = `${baseUrl}/api/leads/recent`;
  
  try {
    console.log(`📡 Testing API endpoint: ${apiUrl}`);
    
    const response = await fetch(apiUrl);
    const data = await response.json();
    
    console.log(`📊 Response Status: ${response.status}`);
    console.log(`📋 Response Body:`, JSON.stringify(data, null, 2));
    
    // Verify expected response format
    if (response.ok) {
      if (data && typeof data === 'object' && Array.isArray(data.leads)) {
        console.log('✅ API endpoint returned expected format: { leads: [] }');
        console.log(`📈 Leads count: ${data.leads.length}`);
        return true;
      } else {
        console.log('❌ API endpoint did not return expected format');
        return false;
      }
    } else {
      console.log(`❌ API endpoint returned error: ${response.status}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ API test failed: ${error.message}`);
    return false;
  }
}

async function main() {
  const success = await testApiEndpoint();
  
  if (success) {
    console.log('🎉 All tests passed!');
    process.exit(0);
  } else {
    console.log('💥 Tests failed!');
    process.exit(1);
  }
}

// Only run if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { testApiEndpoint };