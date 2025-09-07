#!/usr/bin/env tsx

/**
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
import { execSync } from "node:child_process";

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

async function buildLeadsFromPermits(): Promise<void> {
  try {
    console.log('🎯 Building leads from fresh permits...');
    
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    const missingVars = [];
    if (!supabaseUrl) missingVars.push('SUPABASE_URL');
    if (!supabaseKey) missingVars.push('SUPABASE_SERVICE_ROLE_KEY');
    if (missingVars.length > 0) {
      throw new Error(`Missing required environment variable${missingVars.length > 1 ? 's' : ''}: ${missingVars.join(', ')}`);
    }
    
    const response = await fetch(`${supabaseUrl}/rest/v1/rpc/upsert_leads_from_permits`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ p_days: 14 })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`RPC call failed: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    const result = await response.json();
    console.log(`✅ Leads generation completed:`, result);
    
    if (Array.isArray(result) && result.length > 0) {
      const stats = result[0];
      console.log(`   📈 Inserted: ${stats.inserted_count || 0} leads`);
      console.log(`   🔄 Updated: ${stats.updated_count || 0} leads`);
      console.log(`   📊 Total processed: ${stats.total_processed || 0} permits`);
    }
    
  } catch (error) {
    console.error('❌ Failed to build leads from permits:', error instanceof Error ? error.message : String(error));
    // Don't throw - we want ETL to continue even if lead generation fails
  }
}

/**
 * Main ingestion function
 */
async function main(): Promise<void> {
  const startTime = Date.now();
  
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
    const weeklyPermits = await fetchHoustonWeeklyXlsx(weeklyUrl, days);
    console.log(`✅ Fetched ${weeklyPermits.length} weekly permits`);

    // Optionally fetch sold permits if URL is provided
    let soldPermits: any[] = [];
    const soldUrl = process.env.HOUSTON_SOLD_PERMITS_URL;
    if (soldUrl) {
      try {
        console.log('⬇️  Fetching sold permits...');
        soldPermits = await fetchHoustonSoldPermits(soldUrl, days);
        console.log(`✅ Fetched ${soldPermits.length} sold permits`);
      } catch (error) {
        console.warn(`⚠️  Failed to fetch sold permits: ${error}`);
        // Continue with just weekly permits
      }
    }

    // Merge permits (weekly + sold)
    const allPermits = [...weeklyPermits, ...soldPermits];
    console.log(`📋 Total permits to process: ${allPermits.length}`);

    if (allPermits.length === 0) {
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

    // Upsert to database
    console.log('💾 Upserting permits to database...');
    const upsertResult = await upsertPermits(allPermits);
    const upserted = typeof upsertResult === 'number' ? upsertResult : upsertResult.upserted;
    console.log(`✅ Upserted ${upserted} permits`);

    // Build leads from fresh permits
    await buildLeadsFromPermits();

    // Compute first/last issue dates
    const issueDates = allPermits.map(p => p.issue_date).filter(Boolean).sort();
    const first_issue_date = issueDates.length > 0 ? issueDates[0] : undefined;
    const last_issue_date = issueDates.length > 0 ? issueDates[issueDates.length - 1] : undefined;

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Log ETL run to etl_runs table
    console.log('📝 Logging ETL run...');
    await logEtlRun({
      source_system: "city_of_houston",
      fetched: allPermits.length,
      parsed: allPermits.length,
      upserted: upserted,
      errors: 0,
      first_issue_date: first_issue_date ? first_issue_date.slice(0, 10) : undefined,
      last_issue_date: last_issue_date ? last_issue_date.slice(0, 10) : undefined,
      status: 'success',
      duration_ms: duration
    });

    // Write summary for CI
    const summary = {
      source: "city_of_houston",
      fetched_weekly: weeklyPermits.length,
      fetched_sold: soldPermits.length,
      total_fetched: allPermits.length,
      upserted,
      first_issue_date,
      last_issue_date,
      status: "success",
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

    // Call ensure_artifacts.py even on error
    try {
      await callEnsureArtifacts();
    } catch (artifactError) {
      console.error('Failed to call ensure_artifacts.py:', artifactError);
    }

    process.exitCode = 1;
  }
}

// Only run main if this script is executed directly (ESM compatible check)
if (process.argv[1] && (process.argv[1].endsWith('ingest-coh.ts') || process.argv[1].endsWith('ingest-coh.js'))) {
  main().catch(error => {
    console.error('Unhandled error in main:', error);
    process.exit(1);
  });
}