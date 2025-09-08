#!/usr/bin/env tsx

/**
 * Validation script for Houston ETL and Lead Generation SQL functions
 * 
 * This script validates that the required SQL functions and tables exist
 * and can be called correctly.
 */

import fs from 'node:fs';

async function validateSupabaseSetup(): Promise<void> {
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    console.log('⚠️  Supabase environment variables not set. Skipping validation.');
    console.log('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to test against your database.');
    return;
  }
  
  console.log('🔍 Validating Supabase setup...');
  
  try {
    // Test 1: Check if upsert_leads_from_permits_limit function exists
    console.log('\n📋 Test 1: Checking if upsert_leads_from_permits_limit function exists...');
    
    const response = await fetch(`${supabaseUrl}/rest/v1/rpc/upsert_leads_from_permits_limit`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ p_limit: 0, p_days: 1 }) // Test with 0 limit
    });
    
    if (response.ok) {
      console.log('✅ upsert_leads_from_permits_limit function exists and is callable');
    } else {
      const errorText = await response.text();
      console.log(`❌ Function test failed: ${response.status} - ${errorText}`);
    }
    
    // Test 2: Check if permits table exists and has data
    console.log('\n📋 Test 2: Checking permits table...');
    
    const permitsResponse = await fetch(`${supabaseUrl}/rest/v1/permits?select=count&limit=1`, {
      method: 'HEAD',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Prefer': 'count=exact'
      }
    });
    
    if (permitsResponse.ok) {
      const count = permitsResponse.headers.get('content-range')?.split('/')[1] || '0';
      console.log(`✅ Permits table exists with ${count} records`);
    } else {
      console.log(`❌ Permits table check failed: ${permitsResponse.status}`);
    }
    
    // Test 3: Check if leads table exists
    console.log('\n📋 Test 3: Checking leads table...');
    
    const leadsResponse = await fetch(`${supabaseUrl}/rest/v1/leads?select=count&limit=1`, {
      method: 'HEAD',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Prefer': 'count=exact'
      }
    });
    
    if (leadsResponse.ok) {
      const count = leadsResponse.headers.get('content-range')?.split('/')[1] || '0';
      console.log(`✅ Leads table exists with ${count} records`);
    } else {
      console.log(`❌ Leads table check failed: ${leadsResponse.status}`);
    }
    
    // Test 4: Check if etl_runs table exists
    console.log('\n📋 Test 4: Checking etl_runs table...');
    
    const etlResponse = await fetch(`${supabaseUrl}/rest/v1/etl_runs?select=count&limit=1`, {
      method: 'HEAD',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Prefer': 'count=exact'
      }
    });
    
    if (etlResponse.ok) {
      const count = etlResponse.headers.get('content-range')?.split('/')[1] || '0';
      console.log(`✅ ETL runs table exists with ${count} records`);
    } else {
      console.log(`❌ ETL runs table check failed: ${etlResponse.status}`);
    }
    
    console.log('\n✅ Supabase validation completed');
    
  } catch (error) {
    console.error(`❌ Validation failed: ${error}`);
  }
}

async function validateMigrationFiles(): Promise<void> {
  console.log('\n🔍 Validating migration files...');
  
  const requiredFiles = [
    'supabase/migrations/20250121000000_add_upsert_leads_from_permits_limit.sql',
    'sql/etl_runs_table.sql',
    'sql/houston-etl-mint-leads.sql'
  ];
  
  for (const file of requiredFiles) {
    if (fs.existsSync(file)) {
      console.log(`✅ Found: ${file}`);
    } else {
      console.log(`❌ Missing: ${file}`);
    }
  }
}

async function validateScripts(): Promise<void> {
  console.log('\n🔍 Validating scripts...');
  
  const requiredFiles = [
    'scripts/run-houston-etl-and-mint-leads.ts',
    'scripts/run-houston-etl.sh',
    'scripts/ingest-coh.ts'
  ];
  
  for (const file of requiredFiles) {
    if (fs.existsSync(file)) {
      console.log(`✅ Found: ${file}`);
      
      // Check if shell script is executable
      if (file.endsWith('.sh')) {
        try {
          const stats = fs.statSync(file);
          const isExecutable = !!(stats.mode & parseInt('111', 8));
          if (isExecutable) {
            console.log(`   ✅ ${file} is executable`);
          } else {
            console.log(`   ⚠️  ${file} is not executable (run chmod +x ${file})`);
          }
        } catch (error) {
          console.log(`   ❌ Could not check permissions for ${file}`);
        }
      }
    } else {
      console.log(`❌ Missing: ${file}`);
    }
  }
}

async function main(): Promise<void> {
  console.log('🚀 Houston ETL and Lead Generation Validation');
  console.log('=============================================');
  
  await validateMigrationFiles();
  await validateScripts();
  await validateSupabaseSetup();
  
  console.log('\n📋 Next Steps:');
  console.log('1. If Supabase validation failed, ensure your database has the latest migrations');
  console.log('2. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables');
  console.log('3. Run: npm run houston:etl-and-mint:dry-run');
  console.log('4. For production: npm run houston:etl-and-mint');
  
  console.log('\n🎉 Validation completed!');
}

// Execute main function
if (process.argv[1] && (process.argv[1].endsWith('validate-houston-etl.ts') || process.argv[1].endsWith('validate-houston-etl.js'))) {
  main().catch(error => {
    console.error('Validation failed:', error);
    process.exit(1);
  });
}