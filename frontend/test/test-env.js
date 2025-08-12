#!/usr/bin/env node

/**
 * Test script to validate environment variable handling
 */

// Mock environment for testing
process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co';
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'test-anon-key';
process.env.NEXT_PUBLIC_API_BASE = 'http://localhost:8000';

console.log('🧪 Testing environment validation...');

try {
  // Test with valid environment
  const { env, validateClientEnv } = require('../lib/env.ts');
  console.log('✅ Environment validation passed');
  console.log('📋 Parsed environment variables:');
  console.log('  - SUPABASE_URL:', env.NEXT_PUBLIC_SUPABASE_URL);
  console.log('  - API_BASE:', env.NEXT_PUBLIC_API_BASE);
  console.log('  - LAUNCH_SCOPE:', env.NEXT_PUBLIC_LAUNCH_SCOPE);
  console.log('  - FEATURE_CSV_EXPORT:', env.NEXT_PUBLIC_FEATURE_CSV_EXPORT);
  
  // Test client validation
  validateClientEnv();
  console.log('✅ Client environment validation passed');
  
} catch (error) {
  console.error('❌ Environment validation failed:', error.message);
  process.exit(1);
}

console.log('\n🎉 All environment validation tests passed!');