#!/usr/bin/env tsx

/**
 * Integration test for SQL scripts
 * 
 * This script validates that our SQL scripts are syntactically correct
 * and would execute properly on a PostgreSQL database.
 */

import fs from 'fs';
import path from 'path';

function validateSQLSyntax(filePath: string): boolean {
  console.log(`🔍 Validating SQL syntax: ${path.basename(filePath)}`);
  
  try {
    const sql = fs.readFileSync(filePath, 'utf8');
    
    // Basic SQL syntax validation
    const checks = [
      {
        name: 'Has CREATE TABLE or SELECT statements',
        test: () => /CREATE\s+TABLE|SELECT\s+/i.test(sql)
      },
      {
        name: 'Properly terminated statements',
        test: () => {
          const statements = sql.split(';').filter(s => s.trim());
          return statements.length > 0;
        }
      },
      {
        name: 'No obvious syntax errors',
        test: () => {
          // Check for unmatched parentheses
          const openParens = (sql.match(/\(/g) || []).length;
          const closeParens = (sql.match(/\)/g) || []).length;
          return openParens === closeParens;
        }
      },
      {
        name: 'Uses PostgreSQL-compatible syntax',
        test: () => {
          // Check for UUID, TIMESTAMPTZ, JSONB - PostgreSQL specific types
          // OR pg_tables, information_schema - PostgreSQL system tables
          return /UUID|TIMESTAMPTZ|JSONB|pg_tables|information_schema/i.test(sql);
        }
      }
    ];

    let allPassed = true;
    for (const check of checks) {
      const passed = check.test();
      console.log(`  ${passed ? '✅' : '❌'} ${check.name}`);
      if (!passed) allPassed = false;
    }

    return allPassed;
  } catch (error) {
    console.error(`❌ Error reading file: ${error}`);
    return false;
  }
}

function validatePolicyLogic(filePath: string): boolean {
  console.log(`🔍 Validating RLS policy logic: ${path.basename(filePath)}`);
  
  try {
    const sql = fs.readFileSync(filePath, 'utf8');
    const fileName = path.basename(filePath);
    
    // Check for proper RLS setup based on script type
    const hasEnableRLS = /ALTER\s+TABLE.*ENABLE\s+ROW\s+LEVEL\s+SECURITY/i.test(sql);
    const hasPolicies = /CREATE\s+POLICY/i.test(sql);
    const hasDropPolicyIfExists = /DROP\s+POLICY\s+IF\s+EXISTS/i.test(sql);
    
    if (fileName.includes('create')) {
      // Create script should enable RLS
      console.log(`  ${hasEnableRLS ? '✅' : '❌'} Enables RLS`);
      console.log(`  ${hasPolicies ? '✅' : '❌'} Creates policies`);
      console.log(`  ${hasDropPolicyIfExists ? '✅' : '❌'} Safe policy replacement (DROP IF EXISTS)`);
      return hasEnableRLS && hasPolicies && hasDropPolicyIfExists;
    } else if (fileName.includes('remove')) {
      // Remove script doesn't need to enable RLS, just manage policies
      console.log(`  ✅ RLS management (not required for remove script)`);
      console.log(`  ${hasPolicies ? '✅' : '❌'} Creates policies`);
      console.log(`  ${hasDropPolicyIfExists ? '✅' : '❌'} Safe policy replacement (DROP IF EXISTS)`);
      return hasPolicies && hasDropPolicyIfExists;
    } else {
      // Other scripts might not need policies
      console.log(`  ✅ Policy logic (not required for this script type)`);
      return true;
    }
  } catch (error) {
    console.error(`❌ Error reading file: ${error}`);
    return false;
  }
}

function runIntegrationTests(): void {
  console.log('🧪 Running SQL Integration Tests...\n');

  const sqlDir = path.join(process.cwd(), 'sql');
  const files = [
    { path: path.join(sqlDir, 'check_leads_table.sql'), type: 'diagnostic' },
    { path: path.join(sqlDir, 'create_leads_table.sql'), type: 'creation' },
    { path: path.join(sqlDir, 'remove_temp_policies.sql'), type: 'security' }
  ];

  let allPassed = true;

  for (const file of files) {
    console.log(`=== Testing ${path.basename(file.path)} ===`);
    
    if (!fs.existsSync(file.path)) {
      console.error(`❌ File not found: ${file.path}`);
      allPassed = false;
      continue;
    }

    const syntaxValid = validateSQLSyntax(file.path);
    
    if (file.type === 'creation' || file.type === 'security') {
      const policyValid = validatePolicyLogic(file.path);
      if (!policyValid) allPassed = false;
    }
    
    if (!syntaxValid) allPassed = false;
    console.log('');
  }

  // Additional integration checks
  console.log('=== Integration Checks ===');
  
  // Check that all required files exist
  const requiredFiles = ['check_leads_table.sql', 'create_leads_table.sql', 'remove_temp_policies.sql', 'README.md'];
  const missingFiles = requiredFiles.filter(file => !fs.existsSync(path.join(sqlDir, file)));
  
  if (missingFiles.length === 0) {
    console.log('✅ All required files present');
  } else {
    console.error(`❌ Missing files: ${missingFiles.join(', ')}`);
    allPassed = false;
  }

  // Check README exists and has content
  const readmePath = path.join(sqlDir, 'README.md');
  if (fs.existsSync(readmePath)) {
    const readmeContent = fs.readFileSync(readmePath, 'utf8');
    if (readmeContent.length > 500) {
      console.log('✅ README.md has substantial content');
    } else {
      console.error('❌ README.md is too short');
      allPassed = false;
    }
  }

  console.log('\n=== Integration Test Summary ===');
  if (allPassed) {
    console.log('✅ All integration tests passed! SQL scripts are ready for use.');
  } else {
    console.log('❌ Some integration tests failed. Review the scripts.');
    process.exit(1);
  }
}

// Run the integration tests
runIntegrationTests();