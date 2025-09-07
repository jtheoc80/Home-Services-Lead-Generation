#!/usr/bin/env tsx

/**
 * City of Houston ETL Script
 * 
 * This script fetches permit data from City of Houston sources and processes them for storage.
 * It handles both weekly XLSX files and sold permits data, then upserts to Supabase.
 * 
 * Environment Variables:
 *   HOUSTON_WEEKLY_XLSX_URL - URL for Houston weekly permit XLSX files
 *   HOUSTON_SOLD_PERMITS_URL - URL for Houston sold permits data  
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 *   DAYS - Number of days to look back (default: 7)
 */

import { fetchHoustonWeeklyXlsx } from "./adapters/houstonXlsx";
import { fetchHoustonSoldPermits } from "./adapters/houstonSoldPermits";
import { upsertPermits } from "./lib/supabaseUpsert";
import fs from "node:fs";

async function main() {
  try {
    console.log('🏗️  City of Houston ETL Pipeline');
    console.log('================================');
    
    const days = Number(process.env.DAYS || "7");

    const weeklyUrlRaw = process.env.HOUSTON_WEEKLY_XLSX_URL;
    const soldUrlRaw = process.env.HOUSTON_SOLD_PERMITS_URL;

    if (!weeklyUrlRaw) {
      throw new Error("Missing required environment variable: HOUSTON_WEEKLY_XLSX_URL");
    }
    if (!soldUrlRaw) {
      throw new Error("Missing required environment variable: HOUSTON_SOLD_PERMITS_URL");
    }

    let weeklyUrl: string;
    let soldUrl: string;
    try {
      weeklyUrl = new URL(weeklyUrlRaw).toString();
    } catch (e) {
      throw new Error("Invalid URL in HOUSTON_WEEKLY_XLSX_URL: " + weeklyUrlRaw);
    }
    try {
      soldUrl = new URL(soldUrlRaw).toString();
    } catch (e) {
      throw new Error("Invalid URL in HOUSTON_SOLD_PERMITS_URL: " + soldUrlRaw);
    }

    console.log(`📊 Fetching data for last ${days} days`);
    console.log(`📄 Weekly XLSX URL: ${weeklyUrl}`);
    console.log(`🏪 Sold permits URL: ${soldUrl}`);
    console.log('');

    // Fetch data from both sources
    console.log('⬇️  Fetching weekly permits...');
    const weekly = await fetchHoustonWeeklyXlsx(weeklyUrl, days);
    console.log(`✅ Fetched ${weekly.length} weekly permits`);

    console.log('⬇️  Fetching sold permits...');
    const sold = await fetchHoustonSoldPermits(soldUrl, Math.min(days, 2));
    console.log(`✅ Fetched ${sold.length} sold permits`);

    // De-duplicate on (source_system, permit_id, issue_date)
    console.log('🔄 De-duplicating permits...');
    const seen = new Set<string>();
    const merged = [...weekly, ...sold].filter(p => {
      const k = `${p.source_system}|${p.permit_id}|${p.issue_date.slice(0,10)}`;
      if (seen.has(k)) return false;
      seen.add(k); 
      return true;
    });

    console.log(`📋 Processing ${merged.length} unique permits`);

    let upserted = 0;
    if (merged.length === 0) {
      console.log('⚠️  No permits found for processing');
    } else {
      // Upsert to database
      console.log('💾 Upserting permits to database...');
      const result = await upsertPermits(merged);
      upserted = result.upserted;
      console.log(`✅ Upserted ${upserted} permits`);
    }

    // Write summary for CI
    const summary = {
      source: "city_of_houston",
      fetched_weekly: weekly.length,
      fetched_sold: sold.length,
      merged: merged.length,
      upserted,
      first_issue_date: merged.length > 0 ? merged.map(p => p.issue_date).reduce((a, b) => a < b ? a : b) : undefined,
      last_issue_date: merged.length > 0 ? merged.map(p => p.issue_date).reduce((a, b) => a > b ? a : b) : undefined,
    };

    // Ensure logs directory exists
    fs.mkdirSync("logs", { recursive: true });
    
    // Write JSON summary for monitoring
    fs.writeFileSync("logs/etl-summary.json", JSON.stringify(summary, null, 2));
    
    console.log('');
    console.log('📊 ETL Summary:');
    console.log(JSON.stringify(summary, null, 2));
    console.log('');
    console.log('🎉 City of Houston ETL completed successfully!');

  } catch (error) {
    console.error('');
    console.error('❌ City of Houston ETL failed:', error instanceof Error ? error.message : String(error));
    
    // Write error summary
    const errorSummary = {
      source: "city_of_houston", 
      status: "error",
      error: error instanceof Error ? error.message : String(error),
      timestamp: new Date().toISOString()
    };
    
    try {
      fs.mkdirSync("logs", { recursive: true });
      fs.writeFileSync("logs/etl-summary.json", JSON.stringify(errorSummary, null, 2));
    } catch (writeError) {
      console.error('Failed to write error summary:', writeError);
    }
    
    process.exitCode = 1;
  }
}

// Run if called directly
main().catch(error => {
  console.error('Unhandled error:', error);
  process.exitCode = 1;
});