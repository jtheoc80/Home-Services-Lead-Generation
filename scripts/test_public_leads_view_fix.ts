#!/usr/bin/env tsx

/**
 * Test script to validate the public_leads view fix migration
 * 
 * This script validates the SQL syntax and structure of the view fix migration.
 */

import { readFileSync } from 'fs';
import { join } from 'path';

function validateMigrationSyntax(): boolean {
  console.log('🔍 Validating public_leads view fix migration...');
  
  try {
    const migrationPath = join(process.cwd(), 'supabase/migrations/0003_fix_public_leads_view.sql');
    const migrationContent = readFileSync(migrationPath, 'utf8');
    
    console.log('✅ Migration file exists and readable');
    
    // Check for required SQL constructs
    const requiredPatterns = [
      /DROP VIEW IF EXISTS public\.public_leads/i,
      /CREATE VIEW public\.public_leads AS/i,
      /SELECT.*source.*external_permit_id.*trade.*address.*zipcode.*status.*created_at.*updated_at/is,
      /FROM public\.leads/i,
      /GRANT SELECT ON public\.public_leads TO/i,
    ];
    
    let validationPassed = true;
    
    requiredPatterns.forEach((pattern, index) => {
      if (pattern.test(migrationContent)) {
        console.log(`✅ Required pattern ${index + 1} found`);
      } else {
        console.log(`❌ Required pattern ${index + 1} missing`);
        validationPassed = false;
      }
    });
    
    // Check for proper column mapping
    if (migrationContent.includes('zip AS zipcode')) {
      console.log('✅ Proper column mapping (zip -> zipcode) found');
    } else {
      console.log('❌ Column mapping issue - zip column should be mapped to zipcode');
      validationPassed = false;
    }
    
    // Check for comments and documentation
    if (migrationContent.includes('COMMENT ON VIEW')) {
      console.log('✅ Documentation comment found');
    }
    
    return validationPassed;
    
  } catch (error) {
    console.error('❌ Error reading migration file:', error);
    return false;
  }
}

function main() {
  console.log('🧪 Testing public_leads view fix migration...\n');
  
  const isValid = validateMigrationSyntax();
  
  console.log('\n=== Test Summary ===');
  if (isValid) {
    console.log('✅ Migration validation passed! Ready for deployment.');
    process.exit(0);
  } else {
    console.log('❌ Migration validation failed! Please fix the issues above.');
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}