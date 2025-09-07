#!/usr/bin/env tsx

/**
 * Comprehensive test for Houston Weekly XLSX Adapter
 * Tests actual XLSX processing functionality
 */

import { fetchHoustonWeekly } from './houstonWeekly';
import type { Permit } from './supabaseSink';
import * as XLSX from 'xlsx';
import axios from 'axios';

console.log('🧪 Running comprehensive Houston Weekly XLSX Adapter tests...');

// Mock axios to intercept HTTP requests
const originalGet = axios.get;

async function runTests() {
  try {
    // Test 1: Create realistic test data
    const testData = [
      {
        'Permit Number': 'BP2025000001',
        'Issue Date': new Date('2025-01-15'),
        'Work Type': 'Electrical Installation',
        'Address': '123 Main St, Houston, TX',
        'ZIP': '77001',
        'Valuation': '$75,000',
        'Contractor': 'ABC Electric LLC'
      },
      {
        'Permit ID': 'BP2025000002', 
        'Issue Date': '2025-01-10',
        'Trade Type': 'Plumbing Repair',
        'Project Address': '456 Oak Ave, Houston, TX',
        'Postal Code': '77002',
        'Job Value': '15000.50',
        'Company': 'Houston Plumbers Inc'
      },
      {
        'permit_no': 'BP2025000003',
        'issuedate': '2025-01-05',
        'tradetype': 'Mechanical HVAC',
        'siteaddress': '789 Pine St, Houston, TX',
        'zipcode': '77003',
        'valuation': '32500',
        'contractor': 'Cool Air Systems'
      },
      {
        'Permit Number': 'BP2024000999',
        'Issue Date': '2024-12-01', // Old permit - should be filtered out
        'Work Type': 'Electrical',
        'Address': '999 Old St',
        'ZIP': '77099'
      }
    ];

    // Create workbook and convert to buffer
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(testData);
    XLSX.utils.book_append_sheet(wb, ws, 'Permits');
    const buffer = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });

    // Mock axios.get to return our test data
    axios.get = async () => ({
      data: buffer
    });

    console.log('✅ Test data prepared with', testData.length, 'records');

    // Test 2: Call fetchHoustonWeekly with 7 days lookback
    const permits: Permit[] = await fetchHoustonWeekly('http://test-url.com', 7);

    console.log('✅ fetchHoustonWeekly executed successfully');
    console.log(`   - Returned ${permits.length} permits`);

    // Test 3: Verify filtering (should exclude old permit)
    if (permits.length !== 3) {
      throw new Error(`Expected 3 permits after filtering, got ${permits.length}`);
    }
    console.log('✅ Date filtering works correctly');

    // Test 4: Verify permit structure
    permits.forEach((permit, index) => {
      if (!permit.source_system || permit.source_system !== 'city_of_houston') {
        throw new Error(`Permit ${index} missing or invalid source_system`);
      }
      if (!permit.permit_id || typeof permit.permit_id !== 'string') {
        throw new Error(`Permit ${index} missing or invalid permit_id`);
      }
      if (!permit.issue_date || !permit.issue_date.includes('T')) {
        throw new Error(`Permit ${index} missing or invalid ISO date`);
      }
      if (!permit.trade || typeof permit.trade !== 'string') {
        throw new Error(`Permit ${index} missing or invalid trade`);
      }
    });
    console.log('✅ All permits have required fields and correct types');

    // Test 5: Verify trade normalization
    const trades = permits.map(p => p.trade);
    if (!trades.includes('Electrical')) {
      throw new Error('Expected Electrical trade normalization');
    }
    if (!trades.includes('Plumbing')) {
      throw new Error('Expected Plumbing trade normalization');
    }
    if (!trades.includes('Mechanical')) {
      throw new Error('Expected Mechanical trade normalization');
    }
    console.log('✅ Trade normalization works correctly');

    // Test 6: Verify address handling
    const addressedPermits = permits.filter(p => p.address);
    if (addressedPermits.length !== 3) {
      throw new Error('Expected all test permits to have addresses');
    }
    console.log('✅ Address field handling works correctly');

    // Test 7: Verify valuation parsing
    const valuations = permits.map(p => p.valuation).filter(v => v !== null);
    if (valuations.length !== 3) {
      throw new Error('Expected 3 permits with valuation');
    }
    if (!valuations.includes(75000) || !valuations.includes(15000.5) || !valuations.includes(32500)) {
      throw new Error('Valuation parsing failed');
    }
    console.log('✅ Valuation parsing works correctly');

    console.log('\n🎉 All comprehensive tests passed!');
    console.log('\nProcessed permits:');
    permits.forEach((permit, i) => {
      console.log(`  ${i + 1}. ${permit.permit_id} - ${permit.trade} - $${permit.valuation || 'N/A'}`);
    });

  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  } finally {
    // Restore original axios.get
    axios.get = originalGet;
  }
}

// Add jest mock function if not available
if (typeof jest === 'undefined') {
  (global as any).jest = {
    fn: () => ({
      mockResolvedValue: (value: any) => () => Promise.resolve(value)
    })
  };
}

runTests();