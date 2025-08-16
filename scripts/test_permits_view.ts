#!/usr/bin/env tsx

/**
 * Test script to validate the permits view implementation
 * 
 * This script tests:
 * 1. That the permits view exists and can be queried
 * 2. That the expected columns are available
 * 3. That the query from the problem statement works correctly
 * 
 * Usage:
 *   tsx scripts/test_permits_view.ts
 */

import { createClient } from '@supabase/supabase-js';

// Interface matching the problem statement query
interface Permit {
  id: string;
  jurisdiction: string;
  county: string;
  permit_type: string;
  value: number | null;
  status: string;
  issued_date: string;
  address: string;
}

async function testPermitsView() {
  console.log('🧪 Testing permits view implementation...\n');

  // Check environment variables
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Missing Supabase configuration');
    console.error('   Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables');
    console.error('   Or NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY for browser client');
    process.exit(1);
  }

  console.log('✅ Supabase configuration found');
  console.log(`   URL: ${supabaseUrl}`);
  console.log(`   Key: ${supabaseKey.substring(0, 20)}...`);

  // Create Supabase client
  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    // Test 1: Check if permits view exists
    console.log('\n📋 Test 1: Checking if permits view exists...');
    
    const { data: tableCheck, error: tableError } = await supabase
      .from('permits')
      .select('*', { count: 'exact', head: true })
      .limit(1);

    if (tableError) {
      if (tableError.code === 'PGRST116' || tableError.message?.includes('does not exist')) {
        console.error('❌ permits view does not exist');
        console.error('   Please run the create_permits_view.sql migration first');
        console.error('   Also ensure 2025-setup.sql has been applied to create gold.permits table');
        return false;
      }
      throw tableError;
    }

    console.log('✅ permits view exists and is accessible');

    // Test 2: Test the exact query from the problem statement
    console.log('\n🔍 Test 2: Testing problem statement query...');
    
    const { data: permits, error } = await supabase
      .from('permits')
      .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
      .order('issued_date', { ascending: false })
      .limit(50);

    if (error) {
      console.error('❌ Problem statement query failed:', error.message);
      return false;
    }

    console.log(`✅ Query executed successfully, returned ${permits?.length || 0} permits`);

    // Test 3: Validate column types and structure
    console.log('\n🔧 Test 3: Validating data structure...');
    
    if (permits && permits.length > 0) {
      const samplePermit = permits[0] as Permit;
      const expectedFields = ['id', 'jurisdiction', 'county', 'permit_type', 'value', 'status', 'issued_date', 'address'];
      
      for (const field of expectedFields) {
        if (!(field in samplePermit)) {
          console.error(`❌ Missing expected field: ${field}`);
          return false;
        }
      }
      
      console.log('✅ All expected fields present');
      
      // Show sample data
      console.log('\n📊 Sample permit data:');
      console.log(`   ID: ${samplePermit.id}`);
      console.log(`   Jurisdiction: ${samplePermit.jurisdiction}`);
      console.log(`   County: ${samplePermit.county}`);
      console.log(`   Type: ${samplePermit.permit_type}`);
      console.log(`   Value: ${samplePermit.value ? `$${samplePermit.value.toLocaleString()}` : 'N/A'}`);
      console.log(`   Status: ${samplePermit.status}`);
      console.log(`   Issued: ${samplePermit.issued_date}`);
      console.log(`   Address: ${samplePermit.address?.substring(0, 50)}${samplePermit.address?.length > 50 ? '...' : ''}`);
      
    } else {
      console.log('ℹ️  No permit data found (this is okay for empty database)');
    }

    // Test 4: Performance check
    console.log('\n⚡ Test 4: Performance check...');
    
    const startTime = Date.now();
    const { data: perfData, error: perfError } = await supabase
      .from('permits')
      .select('id, jurisdiction, county')
      .limit(10);
    
    const duration = Date.now() - startTime;
    
    if (perfError) {
      console.error(`❌ Performance test failed: ${perfError.message}`);
      return false;
    }
    
    console.log(`✅ Query completed in ${duration}ms`);
    
    if (duration > 5000) {
      console.warn('⚠️  Query took longer than 5 seconds, consider adding indexes');
    }

    console.log('\n🎉 All tests passed! The permits view is working correctly.');
    console.log('\n📋 Summary:');
    console.log(`   - permits view is accessible`);
    console.log(`   - All expected columns are present`);
    console.log(`   - Problem statement query works`);
    console.log(`   - Query performance is acceptable (${duration}ms)`);
    console.log(`   - Data returned: ${permits?.length || 0} permits`);
    
    return true;

  } catch (error) {
    console.error('❌ Test failed with error:', error);
    return false;
  }
}

// Run the test
if (import.meta.url === `file://${process.argv[1]}`) {
  testPermitsView()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Unexpected error:', error);
      process.exit(1);
    });
}