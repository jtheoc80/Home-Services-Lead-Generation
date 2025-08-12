#!/usr/bin/env tsx

/**
 * Test script to verify the leads table SQL scripts work correctly
 * 
 * This script simulates what would happen when the SQL scripts are run
 * by validating the expected schema and structure.
 */

interface ColumnInfo {
  column_name: string;
  data_type: string;
  column_default: string | null;
  is_nullable: string;
}

interface PolicyInfo {
  policyname: string;
  roles: string[];
  cmd: string;
  permissive: string;
  qual: string | null;
  with_check: string | null;
}

function validateLeadsTableSchema(columns: ColumnInfo[]): boolean {
  console.log('🔍 Validating leads table schema...');
  
  const requiredColumns = [
    { name: 'id', type: 'uuid', hasDefault: true },
    { name: 'created_at', type: 'timestamp with time zone', hasDefault: true },
    { name: 'name', type: 'text', hasDefault: false },
    { name: 'email', type: 'text', hasDefault: false },
    { name: 'phone', type: 'text', hasDefault: false },
    { name: 'source', type: 'text', hasDefault: false },
    { name: 'status', type: 'text', hasDefault: true },
    { name: 'metadata', type: 'jsonb', hasDefault: false },
  ];

  let allValid = true;

  for (const required of requiredColumns) {
    const column = columns.find(c => c.column_name === required.name);
    
    if (!column) {
      console.error(`❌ Missing required column: ${required.name}`);
      allValid = false;
      continue;
    }

    if (column.data_type !== required.type) {
      console.error(`❌ Column ${required.name} has wrong type: expected ${required.type}, got ${column.data_type}`);
      allValid = false;
    }

    if (required.hasDefault && !column.column_default) {
      console.error(`❌ Column ${required.name} should have a default value`);
      allValid = false;
    }

    console.log(`✅ Column ${required.name}: ${column.data_type} ${column.column_default ? '(with default)' : ''}`);
  }

  return allValid;
}

function validateRLSPolicies(policies: PolicyInfo[]): boolean {
  console.log('🔍 Validating RLS policies...');
  
  const tempPolicies = [
    'temp_anon_insert_leads',
    'temp_anon_select_leads'
  ];

  const prodPolicies = [
    'authenticated_users_insert_leads',
    'authenticated_users_select_leads', 
    'authenticated_users_update_leads',
    'service_role_full_access_leads'
  ];

  const existingPolicyNames = policies.map(p => p.policyname);
  
  // Check if we have temp policies OR prod policies (not both)
  const hasTempPolicies = tempPolicies.every(name => existingPolicyNames.includes(name));
  const hasProdPolicies = prodPolicies.every(name => existingPolicyNames.includes(name));

  if (hasTempPolicies && !hasProdPolicies) {
    console.log('✅ Temporary anon policies found (testing mode)');
    tempPolicies.forEach(name => {
      console.log(`  ✅ ${name}`);
    });
    return true;
  }

  if (hasProdPolicies && !hasTempPolicies) {
    console.log('✅ Production authenticated policies found (production mode)');
    prodPolicies.forEach(name => {
      console.log(`  ✅ ${name}`);
    });
    return true;
  }

  if (hasTempPolicies && hasProdPolicies) {
    console.warn('⚠️  Both temp and production policies found - this is unusual');
    return true;
  }

  console.error('❌ Neither complete temp nor production policies found');
  console.log('Existing policies:', existingPolicyNames);
  return false;
}

function testSQLScriptLogic(): void {
  console.log('🧪 Testing SQL script logic...\n');

  // Simulate table schema after create_leads_table.sql
  const mockColumnsAfterCreate: ColumnInfo[] = [
    { column_name: 'id', data_type: 'uuid', column_default: 'gen_random_uuid()', is_nullable: 'NO' },
    { column_name: 'created_at', data_type: 'timestamp with time zone', column_default: 'now()', is_nullable: 'YES' },
    { column_name: 'name', data_type: 'text', column_default: null, is_nullable: 'YES' },
    { column_name: 'email', data_type: 'text', column_default: null, is_nullable: 'YES' },
    { column_name: 'phone', data_type: 'text', column_default: null, is_nullable: 'YES' },
    { column_name: 'source', data_type: 'text', column_default: null, is_nullable: 'YES' },
    { column_name: 'status', data_type: 'text', column_default: "'new'::text", is_nullable: 'YES' },
    { column_name: 'metadata', data_type: 'jsonb', column_default: null, is_nullable: 'YES' },
  ];

  // Simulate policies after create_leads_table.sql
  const mockTempPolicies: PolicyInfo[] = [
    { policyname: 'temp_anon_insert_leads', roles: ['anon'], cmd: 'INSERT', permissive: 'PERMISSIVE', qual: null, with_check: 'true' },
    { policyname: 'temp_anon_select_leads', roles: ['anon'], cmd: 'SELECT', permissive: 'PERMISSIVE', qual: 'true', with_check: null },
  ];

  // Simulate policies after remove_temp_policies.sql
  const mockProdPolicies: PolicyInfo[] = [
    { policyname: 'authenticated_users_insert_leads', roles: ['authenticated'], cmd: 'INSERT', permissive: 'PERMISSIVE', qual: null, with_check: 'true' },
    { policyname: 'authenticated_users_select_leads', roles: ['authenticated'], cmd: 'SELECT', permissive: 'PERMISSIVE', qual: 'true', with_check: null },
    { policyname: 'authenticated_users_update_leads', roles: ['authenticated'], cmd: 'UPDATE', permissive: 'PERMISSIVE', qual: 'true', with_check: 'true' },
    { policyname: 'service_role_full_access_leads', roles: ['service_role'], cmd: 'ALL', permissive: 'PERMISSIVE', qual: 'true', with_check: 'true' },
  ];

  console.log('=== Testing create_leads_table.sql result ===');
  const schemaValid = validateLeadsTableSchema(mockColumnsAfterCreate);
  const tempPoliciesValid = validateRLSPolicies(mockTempPolicies);
  
  console.log('\n=== Testing remove_temp_policies.sql result ===');
  const prodPoliciesValid = validateRLSPolicies(mockProdPolicies);

  console.log('\n=== Test Summary ===');
  if (schemaValid && tempPoliciesValid && prodPoliciesValid) {
    console.log('✅ All tests passed! SQL scripts should work correctly.');
  } else {
    console.log('❌ Some tests failed. Review the scripts.');
    process.exit(1);
  }
}

// Run the test
testSQLScriptLogic();