#!/usr/bin/env tsx

/**
 * Test script to verify the isArcGIS function works correctly
 * 
 * Tests the function that detects ArcGIS endpoints to ensure /query
 * is only used on appropriate URLs.
 */

// Import the function from etlDelta.ts
import { readFileSync } from 'fs';
import { join } from 'path';

// Since we can't directly import from etlDelta.ts (it's a script), 
// we'll inline the function for testing
function isArcGIS(url: string): boolean {
  return /(FeatureServer|MapServer)\/\d+$/i.test(url);
}

interface TestCase {
  url: string;
  expected: boolean;
  description: string;
}

function runTests(): boolean {
  console.log('🧪 Testing isArcGIS function...\n');
  
  const testCases: TestCase[] = [
    // Positive cases - should return true
    {
      url: 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0',
      expected: true,
      description: 'Harris County FeatureServer endpoint'
    },
    {
      url: 'https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1',
      expected: true,
      description: 'Arlington MapServer endpoint'
    },
    {
      url: 'https://example.com/rest/services/SomeService/FeatureServer/123',
      expected: true,
      description: 'Generic FeatureServer with high layer number'
    },
    {
      url: 'https://example.com/rest/services/SomeService/MapServer/0',
      expected: true,
      description: 'Generic MapServer layer 0'
    },
    {
      url: 'https://example.com/FEATURESERVER/5',
      expected: true,
      description: 'Case insensitive FeatureServer'
    },
    {
      url: 'https://example.com/mapserver/9',
      expected: true,
      description: 'Case insensitive MapServer'
    },
    
    // Negative cases - should return false
    {
      url: 'https://data.austintexas.gov/resource/3syk-w9eu.json',
      expected: false,
      description: 'Socrata endpoint (Austin)'
    },
    {
      url: 'https://www.dallasopendata.com/api/views/abcd-1234/rows.json',
      expected: false,
      description: 'Dallas open data endpoint'
    },
    {
      url: 'https://example.com/api/permits',
      expected: false,
      description: 'Generic API endpoint'
    },
    {
      url: 'https://example.com/rest/services/SomeService/FeatureServer',
      expected: false,
      description: 'FeatureServer without layer number'
    },
    {
      url: 'https://example.com/rest/services/SomeService/MapServer',
      expected: false,
      description: 'MapServer without layer number'
    },
    {
      url: 'https://example.com/rest/services/SomeService/FeatureServer/abc',
      expected: false,
      description: 'FeatureServer with non-numeric layer'
    },
    {
      url: 'https://example.com/rest/services/SomeService/FeatureServer/0/query',
      expected: false,
      description: 'FeatureServer URL that already includes /query'
    },
    {
      url: 'https://example.com/FeatureServerSomething/0',
      expected: false,
      description: 'URL with FeatureServer in middle but not at right position'
    },
    {
      url: '',
      expected: false,
      description: 'Empty URL'
    },
    {
      url: 'not-a-url',
      expected: false,
      description: 'Invalid URL format'
    }
  ];

  let passed = 0;
  let failed = 0;

  for (const testCase of testCases) {
    const result = isArcGIS(testCase.url);
    const success = result === testCase.expected;
    
    if (success) {
      console.log(`✅ ${testCase.description}`);
      console.log(`   URL: ${testCase.url}`);
      console.log(`   Expected: ${testCase.expected}, Got: ${result}\n`);
      passed++;
    } else {
      console.log(`❌ ${testCase.description}`);
      console.log(`   URL: ${testCase.url}`);
      console.log(`   Expected: ${testCase.expected}, Got: ${result}\n`);
      failed++;
    }
  }

  console.log('📊 Test Results:');
  console.log(`   ✅ Passed: ${passed}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📋 Total: ${testCases.length}`);

  if (failed === 0) {
    console.log('\n🎉 All tests passed!');
    return true;
  } else {
    console.log('\n💥 Some tests failed!');
    return false;
  }
}

// Run tests if this script is executed directly
if (process.argv[1] && process.argv[1].endsWith('test_arcgis_detection.ts')) {
  const success = runTests();
  process.exit(success ? 0 : 1);
}

export { isArcGIS, runTests };