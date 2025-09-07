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
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 *   DAYS - Number of days to look back (default: 7)
 *   ETL_ALLOW_EMPTY - Set to "1" to exit gracefully when no records found
 */

import { fetchHoustonWeeklyPermits, HoustonPermit } from './houstonWeekly.js';
import { SupabaseSink } from './supabaseSink.js';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';

interface IngestSummary {
  source: string;
  fetched: number;
  processed: number;
  upserted: number;
  failed: number;
  timestamp: string;
  duration_ms: number;
}

/**
 * Validate required environment variables
 */
function validateEnvironment(): {
  weeklyUrl: string;
  supabaseUrl: string;
  supabaseKey: string;
  days: number;
  allowEmpty: boolean;
} {
  const weeklyUrl = process.env.HOUSTON_WEEKLY_XLSX_URL;
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const days = parseInt(process.env.DAYS || '7', 10);
  const allowEmpty = process.env.ETL_ALLOW_EMPTY === '1';

  if (!weeklyUrl) {
    throw new Error('Missing required environment variable: HOUSTON_WEEKLY_XLSX_URL');
  }

  if (!supabaseUrl) {
    throw new Error('Missing required environment variable: SUPABASE_URL');
  }

  if (!supabaseKey) {
    throw new Error('Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');
  }

  if (isNaN(days) || days < 1) {
    throw new Error('DAYS environment variable must be a positive integer');
  }

  return { weeklyUrl, supabaseUrl, supabaseKey, days, allowEmpty };
}

/**
 * Create logs directory if it doesn't exist
 */
async function ensureLogsDirectory(): Promise<void> {
  const logsDir = path.join(process.cwd(), 'logs');
  try {
    await fs.mkdir(logsDir, { recursive: true });
  } catch (error) {
    console.warn(`Failed to create logs directory: ${error}`);
  }
}

/**
 * Create artifacts directory if it doesn't exist
 */
async function ensureArtifactsDirectory(): Promise<void> {
  const artifactsDir = path.join(process.cwd(), 'artifacts');
  try {
    await fs.mkdir(artifactsDir, { recursive: true });
  } catch (error) {
    console.warn(`Failed to create artifacts directory: ${error}`);
  }
}

/**
 * Write summary to log file
 */
async function writeSummaryToLog(summary: IngestSummary): Promise<void> {
  try {
    const logPath = path.join(process.cwd(), 'logs', 'etl_output.log');
    const logLine = `[${summary.timestamp}] City of Houston ETL: ${summary.upserted} records processed in ${summary.duration_ms}ms\n`;
    await fs.appendFile(logPath, logLine);
    console.log(`Summary written to: ${logPath}`);
  } catch (error) {
    console.warn(`Failed to write summary to log: ${error}`);
  }
}

/**
 * Write JSON summary for CI/CD pipeline
 */
async function writeJsonSummary(summary: IngestSummary): Promise<void> {
  try {
    const summaryPath = path.join(process.cwd(), 'logs', 'etl-summary.json');
    await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2));
    console.log(`JSON summary written to: ${summaryPath}`);
  } catch (error) {
    console.warn(`Failed to write JSON summary: ${error}`);
  }
}

/**
 * Call scripts/ensure_artifacts.py
 */
async function callEnsureArtifacts(args?: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const spawnArgs = ['scripts/ensure_artifacts.py'];
    if (args) {
      spawnArgs.push(args);
    }

    console.log(`🔧 Calling ensure_artifacts.py${args ? ` ${args}` : ''}`);

    const child = spawn('python3', spawnArgs, {
      cwd: process.cwd(),
      stdio: 'inherit'
    });

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
}

/**
 * Convert Houston permits to database format
 */
function convertPermitsToDbFormat(permits: HoustonPermit[]): Record<string, any>[] {
  return permits.map(permit => ({
    // Use a composite ID for uniqueness
    event_id: `${permit.source_system}_${permit.permit_id}_${permit.issue_date.slice(0, 10)}`,
    permit_id: permit.permit_id,
    source_system: permit.source_system,
    issue_date: permit.issue_date,
    trade: permit.trade,
    address: permit.address || null,
    zipcode: permit.zipcode || null,
    valuation: permit.valuation,
    contractor: permit.contractor,
    raw_data: permit.raw,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }));
}

/**
 * Main ingestion function
 */
async function main(): Promise<void> {
  const startTime = Date.now();
  
  try {
    console.log('🏠 City of Houston Permits Ingestion Script');
    console.log('==========================================');
    console.log(`📂 Current working directory: ${process.cwd()}`);
    console.log('');

    // Validate environment
    const { weeklyUrl, days, allowEmpty } = validateEnvironment();
    
    console.log(`📊 Configuration:`);
    console.log(`  - Weekly URL: ${weeklyUrl.substring(0, 50)}...`);
    console.log(`  - Days to fetch: ${days}`);
    console.log(`  - Allow empty: ${allowEmpty}`);
    console.log('');

    // Create necessary directories
    await ensureLogsDirectory();
    await ensureArtifactsDirectory();

    // Fetch permits from Houston
    console.log('📥 Fetching Houston weekly permits...');
    const permits = await fetchHoustonWeeklyPermits(weeklyUrl, days);
    
    if (permits.length === 0) {
      const message = `No permits found for the last ${days} days`;
      console.log(`⚠️  ${message}`);
      
      if (allowEmpty) {
        console.log('🔧 ETL_ALLOW_EMPTY=1 detected, calling ensure_artifacts.py for graceful exit');
        await callEnsureArtifacts('--empty-pipeline');
        
        const summary: IngestSummary = {
          source: 'city_of_houston',
          fetched: 0,
          processed: 0,
          upserted: 0,
          failed: 0,
          timestamp: new Date().toISOString(),
          duration_ms: Date.now() - startTime
        };
        
        await writeSummaryToLog(summary);
        await writeJsonSummary(summary);
        
        process.exit(0);
      } else {
        await callEnsureArtifacts();
        process.exit(0);
      }
    }

    console.log(`Found ${permits.length} valid permits to process`);

    // Convert permits to database format
    const dbRecords = convertPermitsToDbFormat(permits);
    console.log(`Converted ${dbRecords.length} permits to database format`);

    // Upsert to Supabase
    console.log('💾 Upserting permits to Supabase...');
    const sink = new SupabaseSink('permits_raw', 'event_id', 500);
    
    // Health check first
    const isHealthy = await sink.healthCheck();
    if (!isHealthy) {
      throw new Error('Supabase health check failed');
    }

    const result = await sink.upsertRecords(dbRecords);
    
    const endTime = Date.now();
    const duration = endTime - startTime;

    console.log('');
    console.log('✅ City of Houston ETL completed successfully');
    console.log(`📊 Summary: ${result.success} upserted, ${result.failed} failed, ${duration}ms duration`);

    // Write summaries
    const summary: IngestSummary = {
      source: 'city_of_houston',
      fetched: permits.length,
      processed: dbRecords.length,
      upserted: result.success,
      failed: result.failed,
      timestamp: new Date().toISOString(),
      duration_ms: duration
    };

    await writeSummaryToLog(summary);
    await writeJsonSummary(summary);

    // Call ensure_artifacts.py at the end
    await callEnsureArtifacts();

  } catch (error) {
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    console.error('');
    console.error('❌ City of Houston ETL failed:', error instanceof Error ? error.message : String(error));

    // Write error summary
    const errorSummary: IngestSummary = {
      source: 'city_of_houston',
      fetched: 0,
      processed: 0,
      upserted: 0,
      failed: 1,
      timestamp: new Date().toISOString(),
      duration_ms: duration
    };

    await writeSummaryToLog(errorSummary);
    await writeJsonSummary(errorSummary);

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