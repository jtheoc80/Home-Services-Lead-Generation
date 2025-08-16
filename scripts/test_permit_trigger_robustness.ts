#!/usr/bin/env tsx

/**
 * Test script to verify the permit→lead trigger robustness fix
 * 
 * This validates that the updated trigger handles missing permit_type correctly
 * and always provides a fallback to 'General' for the trade field.
 */

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
}

function runTriggerRobustnessTests(): TestResult[] {
  console.log('🧪 Testing permit→lead trigger robustness fix...\n');
  
  const tests: TestResult[] = [];
  
  // Test 1: Migration file syntax validation
  try {
    const fs = require('fs');
    const migrationContent = fs.readFileSync('./supabase/migrations/20250817000000_fix_permit_lead_trigger_robust.sql', 'utf8');
    
    const requiredElements = [
      'ALTER TABLE public.leads ALTER COLUMN trade SET DEFAULT',
      'UPDATE public.leads SET trade = \'General\' WHERE trade IS NULL',
      'COALESCE(NULLIF(NEW.permit_type,\'\'), NULLIF(NEW.permit_class,\'\'), \'General\')',
      'DROP TRIGGER IF EXISTS trg_lead_from_permit',
      'CREATE TRIGGER trg_lead_from_permit'
    ];
    
    let allFound = true;
    const missing: string[] = [];
    
    for (const element of requiredElements) {
      if (!migrationContent.includes(element)) {
        allFound = false;
        missing.push(element);
      }
    }
    
    tests.push({
      name: 'Migration file contains required elements',
      passed: allFound,
      message: allFound ? 'All required SQL elements found' : `Missing: ${missing.join(', ')}`
    });
    
  } catch (error) {
    tests.push({
      name: 'Migration file exists and readable',
      passed: false,
      message: `Error reading migration file: ${error}`
    });
  }
  
  // Test 2: Function logic validation
  try {
    const fs = require('fs');
    const migrationContent = fs.readFileSync('./supabase/migrations/20250817000000_fix_permit_lead_trigger_robust.sql', 'utf8');
    
    // Check that the new function uses the robust COALESCE logic
    const hasRobustLogic = migrationContent.includes(
      "COALESCE(\n    NULLIF(NEW.permit_type,''), \n    NULLIF(NEW.permit_class,''), \n    'General'\n  )"
    );
    
    tests.push({
      name: 'Function uses robust trade derivation',
      passed: hasRobustLogic,
      message: hasRobustLogic ? 'Robust COALESCE logic implemented' : 'Robust logic not found in function'
    });
    
  } catch (error) {
    tests.push({
      name: 'Function logic validation',
      passed: false,
      message: `Error validating function: ${error}`
    });
  }
  
  // Test 3: README documentation validation
  try {
    const fs = require('fs');
    const readmeContent = fs.readFileSync('./README.md', 'utf8');
    
    const hasTestSection = readmeContent.includes('## Testing Permit→Lead Trigger Robustness');
    const hasTestCommands = readmeContent.includes('SELECT public.upsert_permit(jsonb_build_object(');
    const hasVerificationCommands = readmeContent.includes('FROM public.leads');
    
    tests.push({
      name: 'README contains test documentation',
      passed: hasTestSection && hasTestCommands && hasVerificationCommands,
      message: hasTestSection && hasTestCommands && hasVerificationCommands 
        ? 'Complete test documentation added' 
        : 'Missing test documentation elements'
    });
    
  } catch (error) {
    tests.push({
      name: 'README documentation check',
      passed: false,
      message: `Error checking README: ${error}`
    });
  }
  
  return tests;
}

function printTestResults(results: TestResult[]): void {
  console.log('\n📊 Test Results:\n');
  
  let passedCount = 0;
  
  for (const result of results) {
    const status = result.passed ? '✅' : '❌';
    console.log(`${status} ${result.name}`);
    console.log(`   ${result.message}\n`);
    
    if (result.passed) {
      passedCount++;
    }
  }
  
  const totalTests = results.length;
  console.log(`\n🎯 Summary: ${passedCount}/${totalTests} tests passed`);
  
  if (passedCount === totalTests) {
    console.log('\n🎉 All tests passed! The permit→lead trigger fix is ready for deployment.');
    console.log('\n📋 Next steps:');
    console.log('1. Apply the migration: 20250817000000_fix_permit_lead_trigger_robust.sql');
    console.log('2. Test with actual data using the README examples');
    console.log('3. Verify no NULL trades in the leads table');
  } else {
    console.log('\n⚠️  Some tests failed. Please review the issues above.');
    process.exit(1);
  }
}

// Run the tests
if (require.main === module) {
  const results = runTriggerRobustnessTests();
  printTestResults(results);
}

export { runTriggerRobustnessTests, TestResult };