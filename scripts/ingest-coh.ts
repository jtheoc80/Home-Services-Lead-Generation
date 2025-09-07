#!/usr/bin/env tsx

/**

 * City of Houston ETL Script
 * 
 * This script fetches permit data from City of Houston sources and processes them for storage.
 * It handles both weekly XLSX files and sold permits data, then upserts to Supabase.

 * City of Houston Permits Ingestion Script
 * 
 * Main ETL script for ingesting City of Houston permit data.
 * This script:
 * - Fetches weekly permit data from Houston XLSX source
 * - Processes and normalizes the data
 * - Upserts to Supabase database using the SupabaseSink
 * - Generates summary reports and logs
 * - Handles error cases gracefully
 * 
 * Usage: tsx scripts/ingest-coh.ts

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
import { logEtlRun, logEtlError } from "./lib/logEtlRun";
import fs from "node:fs";

async function main() {
  const startTime = Date.now();
  

 *   ETL_ALLOW_EMPTY - Set to "1" to exit gracefully when no records found
 */

import { fetchHoustonWeeklyPermits, HoustonPermit } from './houstonWeekly.js';
import { SupabaseSink } from './supabaseSink.js';
import fs from 'node:fs';
import { execSync } from 'node:child_process';

async function callEnsureArtifacts(args?: string): Promise<void> {
  try {
    console.log('📂 Calling ensure_artifacts.py...');
    const command = args ? `python scripts/ensure_artifacts.py ${args}` : 'python scripts/ensure_artifacts.py';
    execSync(command, { stdio: 'inherit' });
    console.log('✅ ensure_artifacts.py completed');
  } catch (error) {
    console.error('❌ ensure_artifacts.py failed:', error);
    throw error;
  }
}

/**
 * Convert Houston permits to database format
 */
function convertPermitsToDbFormat(permits: HoustonPermit[]): Record<string, any>[] {
  return permits.map(permit => ({
    source: 'houston',
    source_record_id: permit.permit_id || permit.id || `houston-${permit.permit_number || Date.now()}`,
    permit_number: permit.permit_number,
    issued_date: permit.issue_date ? new Date(permit.issue_date).toISOString() : null,
    application_date: permit.application_date ? new Date(permit.application_date).toISOString() : null,
    expiration_date: permit.expiration_date ? new Date(permit.expiration_date).toISOString() : null,
    permit_type: permit.permit_type,
    permit_class: permit.permit_class,
    work_description: permit.work_description,
    trade: permit.trade || 'General',
    address: permit.address,
    city: permit.city || 'Houston',
    county: permit.county || 'Harris',
    zipcode: permit.zipcode,
    latitude: permit.latitude ? parseFloat(permit.latitude.toString()) : null,
    longitude: permit.longitude ? parseFloat(permit.longitude.toString()) : null,
    valuation: permit.valuation ? parseFloat(permit.valuation.toString()) : null,
    square_feet: permit.square_feet ? parseInt(permit.square_feet.toString()) : null,
    applicant_name: permit.applicant_name,
    contractor_name: permit.contractor_name,
    owner_name: permit.owner_name,
    status: permit.status || 'Unknown',
    raw_data: permit
  }));
}

/**
 * Main ingestion function
 */
async function main(): Promise<void> {

  try {
    console.log('🏗️  City of Houston ETL Pipeline');
    console.log('================================');
    
    const days = Number(process.env.DAYS || "7");
    const allowEmpty = process.env.ETL_ALLOW_EMPTY === "1";
    
    // Validate required environment variables
    const weeklyUrl = process.env.HOUSTON_WEEKLY_XLSX_URL;
    if (!weeklyUrl) {
      throw new Error("Missing required environment variable: HOUSTON_WEEKLY_XLSX_URL");
    }
    
    console.log(`📊 Fetching Houston permits for last ${days} days`);
    console.log(`📄 Weekly XLSX URL: ${weeklyUrl}`);
    console.log('');

    // Fetch permit data
    console.log('⬇️  Fetching weekly permits...');
    const permits = await fetchHoustonWeeklyPermits(weeklyUrl, days);
    console.log(`✅ Fetched ${permits.length} permits`);


    let upserted = 0;
    if (merged.length === 0) {
      console.log('⚠️  No permits found for processing');
    } else {
      // Upsert to database
      console.log('💾 Upserting permits to database...');
      const result = await upsertPermits(merged);
      upserted = typeof result === 'number' ? result : result.upserted;
      console.log(`✅ Upserted ${upserted} permits`);
    }

    // Compute first/last issue dates
    const first_issue_date = merged.length > 0 
      ? merged.map(p => p.issue_date).reduce((a, b) => a < b ? a : b) 
      : undefined;
    const last_issue_date = merged.length > 0 
      ? merged.map(p => p.issue_date).reduce((a, b) => a > b ? a : b) 
      : undefined;

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Log ETL run to etl_runs table
    console.log('📝 Logging ETL run...');
    await logEtlRun({
      source_system: "city_of_houston",
      fetched: weekly.length + sold.length,
      parsed: merged.length,
      upserted: upserted,
      errors: 0,
      first_issue_date: first_issue_date ? first_issue_date.slice(0, 10) : undefined,
      last_issue_date: last_issue_date ? last_issue_date.slice(0, 10) : undefined,
      status: 'success',
      duration_ms: duration
    });

    if (permits.length === 0) {
      const message = '⚠️  No permits found for processing';
      console.log(message);
      
      if (!allowEmpty) {
        throw new Error('No permits found and ETL_ALLOW_EMPTY is not set');
      }
      
      // Write empty summary and exit gracefully
      const summary = {
        source: "city_of_houston",
        fetched: 0,
        upserted: 0,
        status: "completed_empty",
        timestamp: new Date().toISOString()
      };
      
      fs.mkdirSync("logs", { recursive: true });
      fs.writeFileSync("logs/etl-summary.json", JSON.stringify(summary, null, 2));
      
      console.log('✅ ETL completed with empty result set');
      return;
    }

    // Convert to database format
    console.log('🔄 Converting permits to database format...');
    const dbPermits = convertPermitsToDbFormat(permits);
    
    // Initialize Supabase sink and upsert
    console.log('💾 Upserting permits to database...');
    const sink = new SupabaseSink();
    const result = await sink.upsert(dbPermits);
    console.log(`✅ Upserted ${result.upserted} permits`);


    // Write summary for CI
    const summary = {
      source: "city_of_houston",

      fetched_weekly: weekly.length,
      fetched_sold: sold.length,
      merged: merged.length,
      upserted,
      first_issue_date,
      last_issue_date,

      fetched: permits.length,
      upserted: result.upserted,
      first_issue_date: permits.length > 0 ? permits.map(p => p.issue_date).reduce((a, b) => a < b ? a : b) : undefined,
      last_issue_date: permits.length > 0 ? permits.map(p => p.issue_date).reduce((a, b) => a > b ? a : b) : undefined,
      timestamp: new Date().toISOString()

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

    // Call ensure_artifacts.py for post-processing
    try {
      await callEnsureArtifacts();
    } catch (artifactError) {
      console.error('⚠️  ensure_artifacts.py failed (non-critical):', artifactError);
    }

  } catch (error) {
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    console.error('');
    console.error('❌ City of Houston ETL failed:', error instanceof Error ? error.message : String(error));
    
    // Log error ETL run
    try {
      console.log('📝 Logging error ETL run...');
      await logEtlError(
        "city_of_houston",
        error instanceof Error ? error.message : String(error),
        duration
      );
    } catch (logError) {
      console.error('Failed to log ETL error:', logError instanceof Error ? logError.message : String(logError));
    }
    
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



    // Call ensure_artifacts.py even on error
    try {
      await callEnsureArtifacts();
    } catch (artifactError) {
      console.error('Failed to call ensure_artifacts.py:', artifactError);
    }

    process.exit(1);
  }
}


// Only run main if this script is executed directly (ESM compatible check)
if (process.argv[1] && (process.argv[1].endsWith('ingest-coh.ts') || process.argv[1].endsWith('ingest-coh.js'))) {
  main().catch(error => {
    console.error('Unhandled error in main:', error);
    process.exit(1);
  });
}