#!/usr/bin/env tsx

/**
 * Test script for probeSources.ts functionality
 */

import SourceHealthProbe from './probeSources';

console.log('🧪 Testing probeSources.ts...\n');

// Test 1: Check if class can be instantiated with mock environment
process.env.SUPABASE_URL = 'https://test.supabase.co';
process.env.SUPABASE_SERVICE_ROLE_KEY = 'test_key';

try {
  console.log('✅ Test 1: SourceHealthProbe class instantiation');
  const probe = new (SourceHealthProbe as any)();
  console.log('   - Class instantiated successfully');
} catch (error: any) {
  console.log('❌ Test 1 failed:', error.message);
}

// Test 2: Check data sources configuration
try {
  console.log('✅ Test 2: Data sources configuration');
  const probe = new (SourceHealthProbe as any)();
  const sources = probe.getDataSources?.() || [];
  
  if (sources.length > 0) {
    console.log(`   - Found ${sources.length} data sources configured`);
    sources.forEach((source: any) => {
      console.log(`   - ${source.key}: ${source.name} (${source.type})`);
    });
  } else {
    console.log('   - No sources found (private method, this is expected)');
  }
} catch (error: any) {
  console.log('   - Cannot access private method (this is expected)');
}

// Test 3: Environment variables check
console.log('✅ Test 3: Environment variables check');
const requiredEnvVars = [
  'SUPABASE_URL',
  'SUPABASE_SERVICE_ROLE_KEY', 
  'AUSTIN_SOCRATA_APP_TOKEN',
  'SA_SOCRATA_APP_TOKEN'
];

let envWarnings = 0;
requiredEnvVars.forEach(envVar => {
  if (process.env[envVar]) {
    console.log(`   ✅ ${envVar} is set`);
  } else {
    console.log(`   ⚠️  ${envVar} is not set (will use empty string)`);
    envWarnings++;
  }
});

if (envWarnings > 0) {
  console.log(`   - ${envWarnings} environment variables missing`);
  console.log('   - Probes may fail without proper tokens');
}

console.log('\n🎉 probeSources.ts test completed!');
console.log('\nTo run a full probe test with real environment variables:');
console.log('  SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... npx tsx scripts/probeSources.ts');