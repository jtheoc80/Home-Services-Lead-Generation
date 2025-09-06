#!/usr/bin/env tsx

/**
 * Demo script to show the ArcGIS URL validation in action
 */

// Extract the functions from etlDelta.ts for demonstration
function isArcGIS(url: string): boolean {
  return /(FeatureServer|MapServer)\/\d+$/i.test(url);
}

async function checkPermitCount(baseUrl: string, sinceMs: number): Promise<number> {
  if (!isArcGIS(baseUrl)) {
    // Not ArcGIS → we can't use /query?returnCountOnly; skip the remote count check
    console.warn(`Skipping ArcGIS count check for non-ArcGIS URL: ${baseUrl}`);
    return -1; // sentinel meaning "unknown"
  }
  
  // This would normally make an HTTP request, but we'll simulate it
  console.log(`✅ Would query ArcGIS endpoint: ${baseUrl}/query`);
  console.log(`   Query: where=ISSUEDDATE >= ${sinceMs}&returnCountOnly=true&f=json`);
  return 42; // Mock successful response
}

async function runDemo(): Promise<void> {
  console.log('🚀 ArcGIS URL Validation Demo\n');
  console.log('This demonstrates the updated checkPermitCount function that only');
  console.log('uses the /query endpoint for ArcGIS URLs.\n');
  
  const testUrls = [
    {
      name: 'Harris County ArcGIS FeatureServer',
      url: 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0',
      type: 'ArcGIS'
    },
    {
      name: 'Arlington ArcGIS MapServer',
      url: 'https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1',
      type: 'ArcGIS'
    },
    {
      name: 'Austin Socrata API',
      url: 'https://data.austintexas.gov/resource/3syk-w9eu.json',
      type: 'Socrata'
    },
    {
      name: 'Dallas Open Data API',
      url: 'https://www.dallasopendata.com/api/views/abcd-1234/rows.json',
      type: 'Custom API'
    },
    {
      name: 'Generic REST API',
      url: 'https://api.example.com/v1/permits',
      type: 'Generic'
    }
  ];

  const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);

  for (const test of testUrls) {
    console.log(`📋 Testing: ${test.name} (${test.type})`);
    console.log(`   URL: ${test.url}`);
    
    const isArcGISEndpoint = isArcGIS(test.url);
    console.log(`   Is ArcGIS: ${isArcGISEndpoint}`);
    
    try {
      const count = await checkPermitCount(test.url, sevenDaysAgo);
      
      if (count === -1) {
        console.log(`   Result: ⚠️  Skipped (non-ArcGIS endpoint)`);
      } else {
        console.log(`   Result: ✅ Would query ArcGIS (mock count: ${count})`);
      }
    } catch (error) {
      console.log(`   Result: ❌ Error: ${error instanceof Error ? error.message : String(error)}`);
    }
    
    console.log('');
  }

  console.log('🎯 Summary:');
  console.log('   • ArcGIS endpoints (FeatureServer/MapServer + layer number):');
  console.log('     → /query endpoint IS used');
  console.log('     → Returns actual permit count or 0');
  console.log('');
  console.log('   • Non-ArcGIS endpoints (Socrata, custom APIs):');
  console.log('     → /query endpoint is NOT used');
  console.log('     → Returns -1 (sentinel for "unknown")');
  console.log('     → Warning message is logged');
  console.log('');
  console.log('✨ This ensures that /query is only used on appropriate ArcGIS endpoints!');
}

// Run demo if this script is executed directly
if (process.argv[1] && process.argv[1].endsWith('demo_arcgis_validation.ts')) {
  runDemo().catch(error => {
    console.error('Demo error:', error);
    process.exit(1);
  });
}

export { runDemo };