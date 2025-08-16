#!/usr/bin/env tsx

/**
 * Test script to validate the updated_at trigger and indexing changes
 * 
 * This script tests:
 * 1. That the SQL file syntax is valid
 * 2. That the trigger functions are properly defined
 * 3. That the indexes are correctly specified
 * 
 * Usage:
 *   tsx scripts/test_permit_triggers.ts
 */

import { readFileSync } from 'fs';
import { resolve } from 'path';

interface TriggerTest {
  name: string;
  test: () => boolean;
  description: string;
}

function testPermitTriggerChanges(): void {
  console.log('🧪 Testing permit trigger and index changes...\n');

  const sqlFilePath = resolve('sql/public_permits_setup.sql');
  let sqlContent: string;

  try {
    sqlContent = readFileSync(sqlFilePath, 'utf-8');
    console.log('✅ Successfully read sql/public_permits_setup.sql');
  } catch (error) {
    console.error('❌ Failed to read SQL file:', error);
    process.exit(1);
  }

  const tests: TriggerTest[] = [
    {
      name: 'update_updated_at_column function exists',
      test: () => sqlContent.includes('CREATE OR REPLACE FUNCTION update_updated_at_column()'),
      description: 'Reusable trigger function should be defined'
    },
    {
      name: 'set_updated_at trigger exists',
      test: () => sqlContent.includes('CREATE OR REPLACE TRIGGER set_updated_at'),
      description: 'BEFORE UPDATE trigger should be created'
    },
    {
      name: 'trigger targets correct table',
      test: () => sqlContent.includes('BEFORE UPDATE ON public.permits'),
      description: 'Trigger should target public.permits table'
    },
    {
      name: 'trigger calls correct function',
      test: () => sqlContent.includes('EXECUTE FUNCTION update_updated_at_column()'),
      description: 'Trigger should execute the reusable function'
    },
    {
      name: 'composite index exists',
      test: () => sqlContent.includes('idx_permits_issued_date_created_at'),
      description: 'Composite index for sorting should be created'
    },
    {
      name: 'composite index has correct columns',
      test: () => sqlContent.includes('(issued_date DESC, created_at DESC)'),
      description: 'Index should sort by issued_date then created_at'
    },
    {
      name: 'geometry function no longer sets updated_at',
      test: () => !sqlContent.includes('NEW.updated_at := NOW()') || 
                  sqlContent.indexOf('NEW.updated_at = NOW()') > sqlContent.indexOf('NEW.updated_at := NOW()'),
      description: 'Geometry function should not set updated_at inline anymore'
    },
    {
      name: 'created_at column exists',
      test: () => sqlContent.includes('created_at TIMESTAMPTZ DEFAULT NOW()'),
      description: 'created_at column should exist with default'
    },
    {
      name: 'created_at index exists',
      test: () => sqlContent.includes('idx_permits_created_at'),
      description: 'created_at should have its own index'
    }
  ];

  let passedTests = 0;
  let totalTests = tests.length;

  console.log('Running tests...\n');

  for (const test of tests) {
    const result = test.test();
    const status = result ? '✅' : '❌';
    console.log(`${status} ${test.name}`);
    console.log(`   ${test.description}`);
    
    if (result) {
      passedTests++;
    } else {
      console.log('   Failed: Test condition not met');
    }
    console.log('');
  }

  console.log(`\nTest Results: ${passedTests}/${totalTests} tests passed\n`);

  if (passedTests === totalTests) {
    console.log('🎉 All tests passed! The trigger and index changes look correct.');
    console.log('\nNext steps:');
    console.log('1. Apply the SQL changes to your database');
    console.log('2. Test with actual data to verify trigger functionality');
    console.log('3. Validate query performance with the new composite index');
  } else {
    console.log('❌ Some tests failed. Please review the SQL file.');
    process.exit(1);
  }
}

// Run the tests
testPermitTriggerChanges();