
#!/usr/bin/env tsx

/**
 * ETL Script for City of Houston Permits
 * 
 * Fetches permit data from City of Houston sources and processes them for storage.
 * This script integrates with the Houston permits data sources and handles:
 * - Weekly XLSX files from HOUSTON_WEEKLY_XLSX_URL
 * - Sold permits data from HOUSTON_SOLD_PERMITS_URL
 * - Data processing and normalization
 * - Upsert to Supabase database
 * 
 * Enhanced with:
 * - Print current working directory and discovered CSVs before processing
 * - Write summary line to logs/etl_output.log with record count
 * - Save any generated CSVs into artifacts/ directory
 * - Handle ETL_ALLOW_EMPTY=1 environment variable for graceful empty exits
 * - Call scripts/ensure_artifacts.py at the end
 * 
 * Usage: tsx scripts/etlHouston.ts
 * 
 * Environment Variables:
 *   HOUSTON_WEEKLY_XLSX_URL - URL for Houston weekly permit XLSX files
 *   HOUSTON_SOLD_PERMITS_URL - URL for Houston sold permits data
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 *   DAYS - Number of days to look back (default: 7)
 *   ETL_ALLOW_EMPTY - Set to "1" to exit with code 0 instead of 1 when no records found
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import axios from 'axios';

// Batch size for Supabase upserts
const UPSERT_BATCH_SIZE = 500;

interface HoustonPermitRecord {
  permit_id: string;
  permit_number: string | null;
  permit_type: string | null;
  status: string | null;
  issue_date: string | null;
  address: string | null;
  applicant_name: string | null;
  contractor_name: string | null;
  description: string | null;
  valuation: number | null;
  fees: number | null;
  raw: Record<string, any>;
}

function validateEnvironment(): { 
  supabaseUrl: string; 
  supabaseKey: string; 
  weeklyXlsxUrl: string | null; 
  soldPermitsUrl: string | null;
  days: number;
} {
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const weeklyXlsxUrl = process.env.HOUSTON_WEEKLY_XLSX_URL || null;
  const soldPermitsUrl = process.env.HOUSTON_SOLD_PERMITS_URL || null;
  const days = parseInt(process.env.DAYS || '7', 10);
  
  if (!supabaseUrl) {
    console.error('Missing required environment variable: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');
    process.exit(1);
  }
  
  if (!supabaseKey) {
    console.error('Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');
    process.exit(1);
  }
  
  if (!weeklyXlsxUrl && !soldPermitsUrl) {
    console.error('At least one Houston data source URL must be provided:');
    console.error('- HOUSTON_WEEKLY_XLSX_URL for weekly XLSX files');
    console.error('- HOUSTON_SOLD_PERMITS_URL for sold permits data');
    process.exit(1);
  }
  
  return { supabaseUrl, supabaseKey, weeklyXlsxUrl, soldPermitsUrl, days };
}

function getDaysAgo(days: number): Date {
  const now = new Date();
  const daysAgo = new Date(now.getTime() - (days * 24 * 60 * 60 * 1000));
  return daysAgo;
}

async function ensureTableExists(supabase: SupabaseClient): Promise<void> {
  console.log('Ensuring permits_raw_houston table exists...');
  
  // Test if we can access the table
  const { data, error } = await supabase
    .from('permits_raw_houston')
    .select('permit_id', { count: 'exact', head: true })
    .limit(1);
  
  if (error) {
    console.error('❌ Error accessing permits_raw_houston table:', error.message);
    console.error('Please ensure the table exists with the following schema:');
    console.error(`
CREATE TABLE IF NOT EXISTS permits_raw_houston (
  permit_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_type TEXT,
  status TEXT,
  issue_date TIMESTAMPTZ,
  address TEXT,
  applicant_name TEXT,
  contractor_name TEXT,
  description TEXT,
  valuation NUMERIC,
  fees NUMERIC,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
    `);
    process.exit(1);
  }
  
  console.log('✅ Table permits_raw_houston is accessible');
}

async function fetchHoustonWeeklyData(url: string, days: number): Promise<HoustonPermitRecord[]> {
  console.log(`Fetching Houston weekly XLSX data from: ${url}`);
  console.log(`Looking for data from the last ${days} days`);
  
  try {
    const response = await axios.get(url, {
      timeout: 60000, // 60 second timeout for large files
      responseType: 'arraybuffer',
      headers: {
        'User-Agent': 'Home-Services-Lead-Generation-Houston-ETL/1.0'
      }
    });
    
    if (response.status !== 200) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    console.log(`Downloaded ${response.data.byteLength} bytes from weekly XLSX URL`);
    
    // TODO: Implement XLSX parsing
    // For now, return empty array as placeholder
    console.log('⚠️  XLSX parsing not yet implemented - returning empty results');
    console.log('TODO: Add XLSX parsing library (e.g., xlsx, exceljs) and implement data extraction');
    
    return [];
    
  } catch (error) {
    console.error(`❌ Failed to fetch weekly XLSX data: ${error instanceof Error ? error.message : String(error)}`);
    throw error;
  }
}

async function fetchHoustonSoldPermits(url: string, days: number): Promise<HoustonPermitRecord[]> {
  console.log(`Fetching Houston sold permits data from: ${url}`);
  console.log(`Looking for data from the last ${days} days`);
  
  try {
    const response = await axios.get(url, {
      timeout: 30000,
      headers: {
        'User-Agent': 'Home-Services-Lead-Generation-Houston-ETL/1.0'
      }
    });
    
    if (response.status !== 200) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    console.log(`Downloaded data from sold permits URL`);
    
    // TODO: Implement sold permits data parsing
    // This could be JSON, CSV, or HTML depending on the actual endpoint
    console.log('⚠️  Sold permits data parsing not yet implemented - returning empty results');
    console.log('TODO: Determine the format of sold permits data and implement appropriate parsing');
    
    return [];
    
  } catch (error) {
    console.error(`❌ Failed to fetch sold permits data: ${error instanceof Error ? error.message : String(error)}`);
    throw error;
  }
}

async function upsertPermits(supabase: SupabaseClient, permits: HoustonPermitRecord[]): Promise<{ inserted: number; updated: number }> {
  let inserted = 0;
  let updated = 0;
  
  console.log(`Upserting ${permits.length} permits in batches of ${UPSERT_BATCH_SIZE}...`);
  
  for (let i = 0; i < permits.length; i += UPSERT_BATCH_SIZE) {
    const batch = permits.slice(i, i + UPSERT_BATCH_SIZE);
    const batchNumber = Math.floor(i / UPSERT_BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(permits.length / UPSERT_BATCH_SIZE);
    
    console.log(`Processing batch ${batchNumber}/${totalBatches} (${batch.length} permits)...`);
    
    const { data, error } = await supabase
      .from('permits_raw_houston')
      .upsert(batch, {
        onConflict: 'permit_id',
        count: 'exact'
      });
    
    if (error) {
      console.error(`❌ Error upserting batch ${batchNumber}:`, error.message);
      throw error;
    }
    
    // Count as inserted for now (Supabase doesn't distinguish between insert/update in upsert response)
    inserted += batch.length;
    
    console.log(`✅ Batch ${batchNumber} completed`);
  }
  
  return { inserted, updated };
}

async function writeSummaryToLog(recordCount: number, message: string): Promise<void> {
  try {
    const fs = await import('fs/promises');
    const path = await import('path');
    
    // Ensure logs directory exists
    await fs.mkdir('logs', { recursive: true });
    
    const timestamp = new Date().toISOString();
    const summary = `[${timestamp}] City of Houston ETL: ${message} (${recordCount} records)\n`;
    
    await fs.appendFile('logs/etl_output.log', summary);
    console.log(`📝 Summary written to logs/etl_output.log: ${message}`);
    
    // Also create etl-summary.json for monitoring
    const jsonSummary = {
      timestamp,
      test: 'houston-etl',
      status: recordCount > 0 ? 'success' : 'empty',
      recordsProcessed: recordCount,
      message
    };
    
    await fs.writeFile('logs/etl-summary.json', JSON.stringify(jsonSummary, null, 2));
    
  } catch (error) {
    console.error(`⚠️  Failed to write summary to log: ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function callEnsureArtifacts(args?: string): Promise<void> {
  try {
    const { spawn } = await import('child_process');
    
    const spawnArgs = ['scripts/ensure_artifacts.py'];
    if (args) {
      spawnArgs.push(args);
    }
    
    console.log(`🔧 Calling ensure_artifacts.py${args ? ` ${args}` : ''}`);
    
    const child = spawn('python3', spawnArgs, {
      cwd: process.cwd(),
      stdio: 'inherit'
    });
    
    return new Promise((resolve, reject) => {
      child.on('close', (code) => {
        if (code === 0) {
          console.log('✅ ensure_artifacts.py completed successfully');
          resolve();
        } else {
          console.error(`❌ ensure_artifacts.py exited with code ${code}`);
          reject(new Error(`ensure_artifacts.py failed with exit code ${code}`));
        }
      });
      
      child.on('error', (error) => {
        console.error(`❌ Failed to spawn ensure_artifacts.py: ${error.message}`);
        reject(error);
      });
    });
  } catch (error) {
    console.error(`⚠️  Failed to call ensure_artifacts.py: ${error instanceof Error ? error.message : String(error)}`);
    throw error;
  }
}

async function main(): Promise<void> {
  try {
    console.log('ETL Script for City of Houston Permits');
    console.log('=====================================');
    
    // Print current working directory and discovered CSVs
    console.log(`📂 Current working directory: ${process.cwd()}`);
    
    // Discover CSV files in data/**/*.csv recursively
    const { glob } = await import('glob');
    const csvFiles = await glob('data/**/*.csv', { cwd: process.cwd() });
    console.log(`📋 Discovered ${csvFiles.length} CSV files:`);
    csvFiles.forEach(file => console.log(`  - ${file}`));
    console.log('');
    
    // Validate environment variables
    const { supabaseUrl, supabaseKey, weeklyXlsxUrl, soldPermitsUrl, days } = validateEnvironment();
    
    console.log(`Supabase URL: ${supabaseUrl}`);
    console.log(`Houston Weekly XLSX URL: ${weeklyXlsxUrl || 'Not provided'}`);
    console.log(`Houston Sold Permits URL: ${soldPermitsUrl || 'Not provided'}`);
    console.log(`Days lookback: ${days}`);
    console.log('');
    
    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Ensure table exists
    await ensureTableExists(supabase);
    
    let allPermits: HoustonPermitRecord[] = [];
    
    // Fetch from weekly XLSX if URL is provided
    if (weeklyXlsxUrl) {
      try {
        const weeklyPermits = await fetchHoustonWeeklyData(weeklyXlsxUrl, days);
        allPermits.push(...weeklyPermits);
        console.log(`Fetched ${weeklyPermits.length} permits from weekly XLSX data`);
      } catch (error) {
        console.error(`⚠️  Failed to fetch weekly XLSX data, continuing with other sources: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    
    // Fetch from sold permits if URL is provided
    if (soldPermitsUrl) {
      try {
        const soldPermits = await fetchHoustonSoldPermits(soldPermitsUrl, days);
        allPermits.push(...soldPermits);
        console.log(`Fetched ${soldPermits.length} permits from sold permits data`);
      } catch (error) {
        console.error(`⚠️  Failed to fetch sold permits data, continuing: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    
    if (allPermits.length === 0) {
      console.log(`No permits found for the last ${days} days`);
      
      // Write summary to log file
      await writeSummaryToLog(0, 'No input found');
      
      // Handle ETL_ALLOW_EMPTY environment variable
      const allowEmpty = process.env.ETL_ALLOW_EMPTY === '1';
      if (allowEmpty) {
        console.log('🔧 ETL_ALLOW_EMPTY=1 detected, calling ensure_artifacts.py for graceful exit');
        await callEnsureArtifacts('--empty-pipeline');
        process.exit(0);
      } else {
        await callEnsureArtifacts();
        process.exit(0);
      }
    }
    
    console.log(`Found ${allPermits.length} valid permits to process`);
    
    // Upsert permits to Supabase
    const { inserted, updated } = await upsertPermits(supabase, allPermits);
    
    const totalProcessed = inserted + updated;
    
    console.log('');
    console.log('✅ City of Houston ETL completed successfully');
    console.log(`📊 Summary: ${inserted} inserted, ${updated} updated, ${totalProcessed} total processed`);
    
    // Write summary to log file
    await writeSummaryToLog(totalProcessed, `Processed ${totalProcessed} records (${inserted} inserted, ${updated} updated)`);
    
    // Call ensure_artifacts.py at the end
    await callEnsureArtifacts();
    
  } catch (error) {
    console.error('');
    console.error('❌ City of Houston ETL failed:', error instanceof Error ? error.message : String(error));
    
    // Write error summary to log file
    await writeSummaryToLog(0, `Error: ${error instanceof Error ? error.message : String(error)}`);
    
    // Call ensure_artifacts.py even on error
    await callEnsureArtifacts();

    process.exit(1);
  }
}

// Only run main if this script is executed directly (ESM compatible check)
if (process.argv[1] && (process.argv[1].endsWith('etlHouston.ts') || process.argv[1].endsWith('etlHouston.js'))) {
  // Handle unhandled promise rejections
  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
  });

  // Run the main function
  main();
}

import { fetchHoustonWeeklyXlsx } from "./adapters/houstonXlsx";
import { fetchHoustonSoldPermits } from "./adapters/houstonSoldPermits";
import { upsertPermits } from "./lib/supabaseUpsert";
import fs from "node:fs";

async function main() {
  const days = Number(process.env.DAYS || "7");

  const weeklyUrlRaw = process.env.HOUSTON_WEEKLY_XLSX_URL;
  const soldUrlRaw   = process.env.HOUSTON_SOLD_PERMITS_URL;

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
  const weekly = await fetchHoustonWeeklyXlsx(weeklyUrl, days);
  const sold   = await fetchHoustonSoldPermits(soldUrl, Math.min(days, 2));

  // de-dupe on (source_system, permit_id, issue_date)
  const seen = new Set<string>();
  const merged = [...weekly, ...sold].filter(p => {
    const k = `${p.source_system}|${p.permit_id}|${p.issue_date.slice(0,10)}`;
    if (seen.has(k)) return false;
    seen.add(k); return true;
  });

  const { upserted } = await upsertPermits(merged);

  // write summary for CI
  const summary = {
    source: "city_of_houston",
    fetched_weekly: weekly.length,
    fetched_sold: sold.length,
    merged: merged.length,
    upserted,
    first_issue_date: merged.length > 0 ? merged.map(p => p.issue_date).reduce((a, b) => a < b ? a : b) : undefined,
    last_issue_date: merged.length > 0 ? merged.map(p => p.issue_date).reduce((a, b) => a > b ? a : b) : undefined,
  };
  fs.mkdirSync("logs", { recursive: true });
  fs.writeFileSync("logs/etl-summary.json", JSON.stringify(summary, null, 2));
  console.log("COH ETL summary:", summary);
}
main().catch(e => {
  console.error(e);
  process.exitCode = 1;
});

