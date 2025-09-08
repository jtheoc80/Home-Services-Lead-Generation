#!/usr/bin/env tsx

/**
 * Test script to validate the new Houston ETL on-demand workflow configuration
 */

import { readFileSync } from 'fs';
import { join } from 'path';

console.log('🧪 Testing Houston ETL On-Demand Workflow Configuration');
console.log('========================================================');

try {
  // Test 1: Verify workflow file exists and is valid YAML
  console.log('🔍 Test 1: Workflow file validation');
  const workflowPath = join(process.cwd(), '.github/workflows/etl-houston-ondemand.yml');
  const workflowContent = readFileSync(workflowPath, 'utf8');
  
  // Basic YAML validation
  const yaml = await import('yaml');
  const parsed = yaml.parse(workflowContent);
  
  if (!parsed.name || !parsed.on || !parsed.jobs) {
    throw new Error('Invalid workflow structure');
  }
  
  console.log('✅ Test 1 passed: Workflow file is valid YAML with proper structure');

  // Test 2: Verify workflow has required components
  console.log('🔍 Test 2: Workflow components validation');
  
  const job = parsed.jobs.houston;
  if (!job) {
    throw new Error('Houston job not found in workflow');
  }
  
  if (!job['runs-on'] || !job['runs-on'].includes('self-hosted')) {
    throw new Error('Workflow should use self-hosted runner');
  }
  
  if (!job.concurrency || job.concurrency.group !== 'etl-houston') {
    throw new Error('Workflow should have etl-houston concurrency group');
  }
  
  console.log('✅ Test 2 passed: Workflow has required job configuration');

  // Test 3: Verify environment variables mapping
  console.log('🔍 Test 3: Environment variables validation');
  
  const etlStep = job.steps.find((step: any) => step.name === 'Run Houston ETL');
  if (!etlStep) {
    throw new Error('Run Houston ETL step not found');
  }
  
  const requiredEnvVars = [
    'SUPABASE_URL',
    'SUPABASE_SERVICE_ROLE_KEY',
    'HOUSTON_WEEKLY_XLSX_URL',
    'HOUSTON_SOLD_PERMITS_URL'
  ];
  
  for (const envVar of requiredEnvVars) {
    if (!etlStep.env[envVar]) {
      throw new Error(`Missing environment variable: ${envVar}`);
    }
  }
  
  console.log('✅ Test 3 passed: All required environment variables are configured');

  // Test 4: Verify script command
  console.log('🔍 Test 4: Script command validation');
  
  if (!etlStep.run.includes('npx tsx scripts/ingest-coh.ts')) {
    throw new Error('Workflow should run the Houston ETL script');
  }
  
  console.log('✅ Test 4 passed: Workflow runs the correct Houston ETL script');

  // Test 5: Verify workflow input configuration
  console.log('🔍 Test 5: Workflow inputs validation');
  
  const inputs = parsed.on.workflow_dispatch?.inputs;
  if (!inputs || !inputs.days) {
    throw new Error('Workflow should have days input parameter');
  }
  
  if (inputs.days.default !== '14') {
    throw new Error('Days input should default to 14');
  }
  
  console.log('✅ Test 5 passed: Workflow has proper input configuration');

  console.log('');
  console.log('🎉 All workflow configuration tests passed!');
  console.log('');
  console.log('📝 Summary:');
  console.log('   - Workflow YAML is syntactically valid');
  console.log('   - Uses self-hosted runner with scraping capabilities');
  console.log('   - Has proper concurrency control (etl-houston group)');
  console.log('   - All required environment variables are mapped');
  console.log('   - Runs the correct Houston ETL script');
  console.log('   - Has configurable days input (default: 14)');
  console.log('');
  console.log('✅ The Houston ETL on-demand workflow is ready for use!');

} catch (error) {
  console.error('❌ Test failed:', error instanceof Error ? error.message : String(error));
  process.exit(1);
}