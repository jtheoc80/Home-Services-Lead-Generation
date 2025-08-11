#!/usr/bin/env tsx

/**
 * Harris County Permit Data Smoke Test
 * 
 * Fetches the top 5 most recent permit features from Harris County ArcGIS FeatureServer
 * and prints PERMITNUMBER, PERMITNAME, FULLADDRESS, ISSUEDDATE.
 * 
 * Usage: tsx scripts/harrisCounty/smoke.ts
 * Exit codes: 0 = success, 1 = error
 */

interface PermitFeature {
  attributes: {
    PERMITNUMBER?: string;
    PERMITNAME?: string;
    PROJECTNAME?: string; // Fallback in case PERMITNAME doesn't exist
    FULLADDRESS?: string;
    ISSUEDDATE?: number; // Epoch timestamp
  };
}

interface ArcGISResponse {
  features: PermitFeature[];
  error?: {
    code: number;
    message: string;
  };
}

const HARRIS_COUNTY_API = "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query";

async function fetchPermitData(): Promise<PermitFeature[]> {
  const params = new URLSearchParams({
    where: "1=1",
    orderByFields: "ISSUEDDATE DESC",
    resultRecordCount: "5",
    f: "json",
    outFields: "PERMITNUMBER,PERMITNAME,PROJECTNAME,FULLADDRESS,ISSUEDDATE"
  });

  const url = `${HARRIS_COUNTY_API}?${params.toString()}`;
  
  console.log(`Fetching data from: ${url}`);
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data: ArcGISResponse = await response.json();
    
    if (data.error) {
      throw new Error(`ArcGIS API Error ${data.error.code}: ${data.error.message}`);
    }
    
    if (!data.features || data.features.length === 0) {
      throw new Error("No permit features returned from API");
    }
    
    return data.features;
    
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Network error: Unable to connect to Harris County API. ${error.message}`);
    }
    throw error;
  }
}

function formatDate(epochTimestamp: number | undefined): string {
  if (!epochTimestamp) return "N/A";
  
  try {
    const date = new Date(epochTimestamp);
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  } catch {
    return "Invalid Date";
  }
}

function printPermitData(features: PermitFeature[]): void {
  console.log("\n=== Top 5 Most Recent Harris County Permits ===");
  console.log("PERMITNUMBER\t\tPERMITNAME\t\t\t\tFULLADDRESS\t\t\t\tISSUEDDATE");
  console.log("─".repeat(120));
  
  features.forEach((feature, index) => {
    const attrs = feature.attributes;
    
    const permitNumber = attrs.PERMITNUMBER || "N/A";
    const permitName = attrs.PERMITNAME || attrs.PROJECTNAME || "N/A";
    const fullAddress = attrs.FULLADDRESS || "N/A";
    const issuedDate = formatDate(attrs.ISSUEDDATE);
    
    // Truncate long strings for display
    const truncatedName = permitName.length > 30 ? permitName.substring(0, 27) + "..." : permitName;
    const truncatedAddress = fullAddress.length > 40 ? fullAddress.substring(0, 37) + "..." : fullAddress;
    
    console.log(`${permitNumber.padEnd(15)}\t${truncatedName.padEnd(30)}\t${truncatedAddress.padEnd(40)}\t${issuedDate}`);
  });
  
  console.log("─".repeat(120));
  console.log(`Total records: ${features.length}`);
}

async function main(): Promise<void> {
  try {
    console.log("Harris County Permit Data Smoke Test");
    console.log("=====================================");
    
    const features = await fetchPermitData();
    printPermitData(features);
    
    console.log("\n✅ Smoke test completed successfully");
    process.exit(0);
    
  } catch (error) {
    console.error("\n❌ Smoke test failed:");
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// Run the script
main();