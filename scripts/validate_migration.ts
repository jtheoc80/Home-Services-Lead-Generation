#!/usr/bin/env tsx

/**
 * SQL Migration Validation Script
 * Performs basic syntax and structure validation on the migration file
 */

import { readFileSync } from 'fs';
import { join } from 'path';

interface ValidationResult {
  check: string;
  passed: boolean;
  message: string;
  details?: string[];
}

function validateMigrationFile(): ValidationResult[] {
  const results: ValidationResult[] = [];
  const migrationPath = join(process.cwd(), 'supabase/migrations/align_repo_supabase.sql');
  
  try {
    const sqlContent = readFileSync(migrationPath, 'utf-8');
    
    // Basic file structure validation
    results.push({
      check: 'Migration file exists and readable',
      passed: true,
      message: `Found migration file: ${migrationPath.split('/').pop()}`,
    });
    
    // Content length validation
    const lineCount = sqlContent.split('\n').length;
    results.push({
      check: 'File content validation',
      passed: lineCount > 100,
      message: `Migration file contains ${lineCount} lines, ${sqlContent.length} characters`,
    });
    
    // Check for required SQL constructs
    const requiredConstructs = [
      { name: 'Extension enablement', pattern: /CREATE EXTENSION IF NOT EXISTS/gi },
      { name: 'Table alterations', pattern: /ALTER TABLE.*ADD COLUMN/gi },
      { name: 'Index creation', pattern: /CREATE.*INDEX/gi },
      { name: 'View creation', pattern: /CREATE.*VIEW/gi },
      { name: 'Function creation', pattern: /CREATE OR REPLACE FUNCTION/gi },
      { name: 'Trigger creation', pattern: /CREATE TRIGGER/gi },
      { name: 'DO blocks', pattern: /DO \$\$/gi },
      { name: 'JSONB operations', pattern: /jsonb_build_object/gi },
    ];
    
    const foundConstructs: string[] = [];
    const missingConstructs: string[] = [];
    
    requiredConstructs.forEach(construct => {
      const matches = sqlContent.match(construct.pattern);
      if (matches && matches.length > 0) {
        foundConstructs.push(`${construct.name} (${matches.length})`);
      } else {
        missingConstructs.push(construct.name);
      }
    });
    
    results.push({
      check: 'Required SQL constructs',
      passed: missingConstructs.length === 0,
      message: missingConstructs.length === 0 
        ? 'All required SQL constructs found'
        : `Missing constructs: ${missingConstructs.join(', ')}`,
      details: foundConstructs
    });
    
    // Check for balanced parentheses and blocks
    const parenBalance = checkBalancedParentheses(sqlContent);
    results.push({
      check: 'Balanced parentheses',
      passed: parenBalance.balanced,
      message: parenBalance.balanced ? 'All parentheses properly balanced' : `Unbalanced parentheses: ${parenBalance.message}`,
    });
    
    // Check for potential SQL injection or dangerous patterns
    const dangerousPatterns = [
      { name: 'DROP DATABASE', pattern: /DROP\s+DATABASE/gi },
      { name: 'TRUNCATE without conditions', pattern: /TRUNCATE\s+(?!.*WHERE)/gi },
      { name: 'DELETE without WHERE', pattern: /DELETE\s+FROM\s+\w+\s*(?!.*WHERE)/gi },
    ];
    
    const foundDangerous: string[] = [];
    dangerousPatterns.forEach(pattern => {
      const matches = sqlContent.match(pattern.pattern);
      if (matches && matches.length > 0) {
        foundDangerous.push(`${pattern.name} (${matches.length})`);
      }
    });
    
    results.push({
      check: 'Safety validation',
      passed: foundDangerous.length === 0,
      message: foundDangerous.length === 0 
        ? 'No dangerous SQL patterns detected'
        : `WARNING: Found potentially dangerous patterns: ${foundDangerous.join(', ')}`,
    });
    
    // Check for PostgreSQL-specific syntax
    const pgPatterns = [
      { name: 'UUID functions', pattern: /gen_random_uuid\(\)/gi },
      { name: 'TIMESTAMPTZ usage', pattern: /TIMESTAMPTZ/gi },
      { name: 'JSONB operations', pattern: /JSONB/gi },
      { name: 'PostGIS geometry', pattern: /GEOMETRY\(POINT/gi },
      { name: 'PostgreSQL functions', pattern: /\$\$ LANGUAGE plpgsql/gi },
    ];
    
    const foundPgFeatures: string[] = [];
    pgPatterns.forEach(pattern => {
      const matches = sqlContent.match(pattern.pattern);
      if (matches && matches.length > 0) {
        foundPgFeatures.push(`${pattern.name} (${matches.length})`);
      }
    });
    
    results.push({
      check: 'PostgreSQL compatibility',
      passed: foundPgFeatures.length > 0,
      message: `Found ${foundPgFeatures.length} PostgreSQL-specific features`,
      details: foundPgFeatures
    });
    
    // Check for proper schema targeting
    const schemaReferences = sqlContent.match(/public\./gi);
    const schemaCount = schemaReferences ? schemaReferences.length : 0;
    
    results.push({
      check: 'Schema targeting',
      passed: schemaCount > 5,
      message: `Found ${schemaCount} references to 'public.' schema`,
    });
    
    // Check migration phases
    const phases = [
      'PHASE 1: Enhance permits table schema',
      'PHASE 2: Add unique constraints and indexes',
      'PHASE 3: Enhance leads table schema',
      'PHASE 4: Create compatibility views',
      'PHASE 5: Update upsert_permit RPC function',
      'PHASE 6: Refresh permit→lead pipeline',
      'PHASE 7: Backfill and validation',
      'PHASE 8: Final verification'
    ];
    
    const foundPhases = phases.filter(phase => sqlContent.includes(phase));
    
    results.push({
      check: 'Migration phases structure',
      passed: foundPhases.length === phases.length,
      message: `Found ${foundPhases.length}/${phases.length} migration phases`,
      details: foundPhases
    });
    
  } catch (error) {
    results.push({
      check: 'Migration file access',
      passed: false,
      message: `Error reading migration file: ${error}`,
    });
  }
  
  return results;
}

function checkBalancedParentheses(sql: string): { balanced: boolean; message: string } {
  let balance = 0;
  let dollarBlockBalance = 0;
  let inQuotes = false;
  let quoteChar = '';
  
  for (let i = 0; i < sql.length; i++) {
    const char = sql[i];
    const prevChar = i > 0 ? sql[i-1] : '';
    
    // Handle quotes
    if ((char === '"' || char === "'") && prevChar !== '\\') {
      if (!inQuotes) {
        inQuotes = true;
        quoteChar = char;
      } else if (char === quoteChar) {
        inQuotes = false;
        quoteChar = '';
      }
    }
    
    if (!inQuotes) {
      // Handle dollar-quoted blocks ($$...$$)
      if (char === '$' && sql[i+1] === '$') {
        dollarBlockBalance = dollarBlockBalance === 0 ? 1 : 0;
        i++; // Skip next $
        continue;
      }
      
      if (dollarBlockBalance === 0) {
        if (char === '(') balance++;
        if (char === ')') balance--;
      }
    }
  }
  
  return {
    balanced: balance === 0 && dollarBlockBalance === 0,
    message: balance !== 0 ? `Parentheses: ${balance}` : dollarBlockBalance !== 0 ? 'Dollar blocks unbalanced' : 'OK'
  };
}

async function main() {
  console.log('🔍 Validating Supabase Schema Alignment Migration\n');
  
  const results = validateMigrationFile();
  
  console.log('📊 Validation Results:\n');
  
  let passedChecks = 0;
  results.forEach((result, index) => {
    const status = result.passed ? '✅' : '❌';
    console.log(`${index + 1}. ${status} ${result.check}`);
    console.log(`   ${result.message}`);
    
    if (result.details && result.details.length > 0) {
      console.log(`   Details: ${result.details.join(', ')}`);
    }
    console.log();
    
    if (result.passed) passedChecks++;
  });
  
  console.log(`\n🎯 Summary: ${passedChecks}/${results.length} validation checks passed`);
  
  if (passedChecks === results.length) {
    console.log('🎉 Migration file validation successful!');
    console.log('\n📋 Ready for deployment:');
    console.log('1. Execute migration in Supabase SQL editor as postgres user');
    console.log('2. Run test suite: npm run test:schema:alignment');
    console.log('3. Verify with sentinel test case');
  } else {
    console.log('⚠️  Some validation checks failed. Review the migration file.');
    process.exit(1);
  }
}

// Add command line argument parsing
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Usage: npm run validate:migration [options]

Options:
  --help, -h     Show this help message
  
This script validates the Supabase schema alignment migration file by:
1. Checking file accessibility and basic structure
2. Validating required SQL constructs are present
3. Checking for balanced parentheses and blocks
4. Scanning for dangerous SQL patterns
5. Verifying PostgreSQL-specific syntax
6. Confirming proper schema targeting
7. Validating migration phases structure

Run this before executing the migration in Supabase.
`);
  process.exit(0);
}

// Run main function
main().catch(console.error);