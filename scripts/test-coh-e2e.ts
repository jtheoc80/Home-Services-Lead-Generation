#!/usr/bin/env tsx

/**
 * Test script to verify the City of Houston ETL pipeline works end-to-end
 * Creates a mock XLSX file and tests the full pipeline
 */

import * as XLSX from 'xlsx';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

async function createMockXlsxFile(): Promise<string> {
  // Create mock permit data
  const mockData = [
    {
      'Permit Number': 'COH-2024-001',
      'Issue Date': '2024-01-01',
      'Work Type': 'Electrical',
      'Address': '123 Main St',
      'ZIP Code': '77001',
      'Valuation': '5000',
      'Contractor': 'ABC Electric Co'
    },
    {
      'Permit Number': 'COH-2024-002', 
      'Issue Date': '2024-01-02',
      'Work Type': 'Plumbing',
      'Address': '456 Oak Ave',
      'ZIP Code': '77002',
      'Valuation': '3000',
      'Contractor': 'XYZ Plumbing'
    }
  ];

  // Create workbook and worksheet
  const workbook = XLSX.utils.book_new();
  const worksheet = XLSX.utils.json_to_sheet(mockData);
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Permits');

  // Write to temp file
  const tempFile = path.join(process.cwd(), 'tmp', 'mock-houston-permits.xlsx');
  fs.mkdirSync(path.dirname(tempFile), { recursive: true });
  XLSX.writeFile(workbook, tempFile);
  
  console.log(`✅ Created mock XLSX file: ${tempFile}`);
  return tempFile;
}

async function runTest(): Promise<void> {
  console.log('🧪 Testing City of Houston ETL Pipeline End-to-End');
  console.log('==================================================');

  try {
    // Create mock XLSX file
    const xlsxFile = await createMockXlsxFile();

    // Set up environment variables for test
    const testEnv = {
      ...process.env,
      SUPABASE_URL: 'https://test.supabase.co',
      SUPABASE_SERVICE_ROLE_KEY: 'test-key',
      HOUSTON_WEEKLY_XLSX_URL: `file://${xlsxFile}`,
      ETL_ALLOW_EMPTY: '1',
      DAYS: '365' // Look back a full year to catch our mock data
    };

    console.log('🏃 Running ETL script with mock data...');
    
    // Run the ETL script
    const result = execSync('npx tsx scripts/ingest-coh.ts', {
      env: testEnv,
      encoding: 'utf8',
      cwd: process.cwd()
    });

    console.log('📊 ETL Script Output:');
    console.log(result);

    // Clean up
    fs.unlinkSync(xlsxFile);
    console.log('🧹 Cleaned up mock file');

    console.log('✅ End-to-end test completed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

// Only run if called directly
if (process.argv[1] && process.argv[1].endsWith('test-coh-e2e.ts')) {
  runTest().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}