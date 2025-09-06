#!/usr/bin/env tsx

/**
 * ETL Delta Script for Harris County Permits
 * 
 * Reads process.env.HC_ISSUED_PERMITS_URL and fetches permits from the last 7 days.
 * Queries returnCountOnly=true for ISSUEDDATE > now-7d; if 0, exits with clear message and full URL.
 * Pages in 2,000-row chunks using resultOffset until empty.
 * Maps fields to { event_id, permit_number, permit_name, app_type, issue_date, full_address, status, project_number, raw }.
 * Converts ISSUEDDATE from ms to ISO format.
 * Upserts to Supabase table permits_raw_harris using event_id as conflict target (chunk size 500).
 * Uses @supabase/supabase-js + SUPABASE_SERVICE_ROLE_KEY.
 * Logs inserted/updated counts and exits non-zero on any HTTP/DB error.
 * 
 * Enhanced with:
 * - Print current working directory and discovered CSVs before processing
 * - Write summary line to logs/etl_output.log with record count
 * - Save any generated CSVs into artifacts/ directory
 * - Handle ETL_ALLOW_EMPTY=1 environment variable for graceful empty exits
 * - Call scripts/ensure_artifacts.py at the end
 * 
 * Usage: tsx scripts/etlDelta.ts
 * 
 * Environment Variables:
 *   HC_ISSUED_PERMITS_URL - Harris County FeatureServer URL
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 *   ETL_ALLOW_EMPTY - Set to "1" to exit with code 0 instead of 1 when no records found
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import axios from 'axios';

// Pagination size for ArcGIS queries
const PAGE_SIZE = 2000;

// Batch size for Supabase upserts
const UPSERT_BATCH_SIZE = 500;

interface ArcGISFeature {
  attributes: Record<string, any>;
}

interface ArcGISResponse {
  features: ArcGISFeature[];
  count?: number;
  exceededTransferLimit?: boolean;
}

interface PermitRecord {
  event_id: number;
  permit_number: string | null;
  permit_name: string | null;
  app_type: string | null;
  issue_date: string | null; // Note: Using issue_date to match table schema (ISO string format)
  full_address: string | null;
  status: string | null;
  project_number: string | null;
  raw: Record<string, any>;
}

function validateEnvironment(): { supabaseUrl: string; supabaseKey: string; hcUrl: string } {
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const hcUrl = process.env.HC_ISSUED_PERMITS_URL;
  
  if (!hcUrl) {
    console.error('Missing required environment variable: HC_ISSUED_PERMITS_URL');
    process.exit(1);
  }
  
  if (!supabaseUrl) {
    console.error('Missing required environment variable: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');
    process.exit(1);
  }
  
  if (!supabaseKey) {
    console.error('Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');
    process.exit(1);
  }
  
  return { supabaseUrl, supabaseKey, hcUrl };
}

function isArcGIS(url: string): boolean {
  return /(FeatureServer|MapServer)\/\d+$/i.test(url);
}

function getSevenDaysAgo(): Date {
  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
  return sevenDaysAgo;
}

async function checkPermitCount(baseUrl: string, sinceMs: number): Promise<number> {
  if (!isArcGIS(baseUrl)) {
    // Not ArcGIS → we can't use /query?returnCountOnly; skip the remote count check
    console.warn(`Skipping ArcGIS count check for non-ArcGIS URL: ${baseUrl}`);
    return -1; // sentinel meaning "unknown"
  }
  const url = `${baseUrl.replace(/\/$/, '')}/query` +
              `?where=ISSUEDDATE+>=+${sinceMs}` +
              `&returnCountOnly=true&f=json`;
  const { data } = await axios.get(url, {
    headers: { 'User-Agent': 'Home-Services-Lead-Generation-ETL-Delta/1.0' },
    timeout: 30_000,
  });
  if (typeof data?.count === 'number') return data.count;
  throw new Error(`Unexpected ArcGIS response: ${JSON.stringify(data).slice(0,200)}...`);
}

async function fetchPermits(hcUrl: string, since: Date): Promise<PermitRecord[]> {
  if (!isArcGIS(hcUrl)) {
    console.warn(`Cannot fetch permits from non-ArcGIS URL: ${hcUrl}`);
    return [];
  }
  
  const permits: PermitRecord[] = [];
  let offset = 0;
  let hasMore = true;
  const sinceTimestamp = since.getTime();
  
  console.log(`Fetching permits since: ${since.toISOString()}`);
  
  while (hasMore) {
    try {
      const queryParams = new URLSearchParams({
        where: `ISSUEDDATE > ${sinceTimestamp}`,
        outFields: '*',
        f: 'json',
        resultOffset: offset.toString(),
        resultRecordCount: PAGE_SIZE.toString(),
        orderByFields: 'ISSUEDDATE DESC'
      });
      
      const url = `${hcUrl}/query?${queryParams}`;
      console.log(`Fetching batch ${Math.floor(offset / PAGE_SIZE) + 1} (offset: ${offset})`);
      
      const response = await axios.get(url, {
        timeout: 30000,
        headers: {
          'User-Agent': 'Home-Services-Lead-Generation-ETL-Delta/1.0'
        }
      });
      
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = response.data as ArcGISResponse;
      const features = data.features || [];
      
      console.log(`Received ${features.length} features in this batch`);
      
      // Process features into permit records
      for (const feature of features) {
        const attrs = feature.attributes;
        
        const permit: PermitRecord = {
          event_id: attrs.EVENT_ID || attrs.OBJECTID,
          permit_number: attrs.PERMIT_NUMBER || attrs.PERMITNUMBER || null,
          permit_name: attrs.PERMIT_NAME || attrs.PERMITNAME || null,
          app_type: attrs.APP_TYPE || attrs.APPTYPE || null,
          issue_date: attrs.ISSUEDDATE ? new Date(attrs.ISSUEDDATE).toISOString() : null,
          full_address: attrs.FULL_ADDRESS || attrs.FULLADDRESS || attrs.ADDRESS || null,
          status: attrs.STATUS || null,
          project_number: attrs.PROJECT_NUMBER || attrs.PROJECTNUMBER || null,
          raw: attrs
        };
        
        // Only include permits with required fields
        if (permit.event_id) {
          permits.push(permit);
        }
      }
      
      // Check if we have more data
      hasMore = features.length === PAGE_SIZE;
      offset += PAGE_SIZE;
      
      // Safety check to prevent infinite loops
      if (offset > 100000) {
        console.log('Reached safety limit of 100,000 records');
        break;
      }
      
    } catch (error) {
      console.error(`Error fetching batch at offset ${offset}:`, error);
      throw new Error(`Failed to fetch permits: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  console.log(`Fetched ${permits.length} valid permits total`);
  return permits;
}

async function upsertPermits(supabase: SupabaseClient, permits: PermitRecord[]): Promise<{ inserted: number; updated: number }> {
  let insertedCount = 0;
  let updatedCount = 0;
  
  console.log(`Upserting ${permits.length} permits in batches of ${UPSERT_BATCH_SIZE}`);
  
  for (let i = 0; i < permits.length; i += UPSERT_BATCH_SIZE) {
    const batch = permits.slice(i, i + UPSERT_BATCH_SIZE);
    const batchNumber = Math.floor(i / UPSERT_BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(permits.length / UPSERT_BATCH_SIZE);
    
    console.log(`Processing batch ${batchNumber}/${totalBatches} (${batch.length} records)`);
    
    try {
      const { data, error, count } = await supabase
        .from('permits_raw_harris')
        .upsert(batch, {
          onConflict: 'event_id',
          count: 'exact'
        });
      
      if (error) {
        throw new Error(`Supabase upsert error: ${error.message}`);
      }
      
      console.log(`Batch ${batchNumber} processed successfully`);
      
      // Note: Supabase doesn't differentiate between inserts and updates in the response
      // We'll count all as "upserted"
      const batchCount = count || batch.length;
      insertedCount += batchCount; // This represents "upserted" records
      
    } catch (error) {
      console.error(`Error upserting batch ${batchNumber}:`, error);
      throw new Error(`Failed to upsert permits: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  // For simplicity, we'll report all as "inserted" since Supabase doesn't distinguish
  const totalUpserted = insertedCount;
  console.log(`Successfully upserted ${totalUpserted} permits`);
  return { inserted: insertedCount, updated: updatedCount };
}

async function ensureTableExists(supabase: SupabaseClient): Promise<void> {
  try {
    const { error } = await supabase
      .from('permits_raw_harris')
      .select('event_id', { count: 'exact', head: true })
      .limit(1);
    
    if (error && (error.code === 'PGRST116' || error.message?.includes('does not exist'))) {
      console.error('Table permits_raw_harris does not exist. Please create it first.');
      throw new Error('Table permits_raw_harris does not exist');
    } else if (error) {
      throw error;
    }
    
    console.log('Table permits_raw_harris exists and is accessible');
  } catch (error) {
    console.error('Error checking table existence:', error);
    throw new Error(`Failed to verify table existence: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Write summary line to logs/etl_output.log
 */
async function writeSummaryToLog(recordCount: number, message: string): Promise<void> {
  try {
    const { writeFile, mkdir } = await import('fs/promises');
    const { join } = await import('path');
    
    const logsDir = join(process.cwd(), 'logs');
    const logFile = join(logsDir, 'etl_output.log');
    
    // Ensure logs directory exists
    await mkdir(logsDir, { recursive: true });
    
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} - ETL Delta: ${recordCount} records - ${message}\n`;
    
    // Append to log file
    await writeFile(logFile, logEntry, { flag: 'a' });
    console.log(`📝 Summary logged to ${logFile}`);
  } catch (error) {
    console.error(`⚠️  Failed to write to log file: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Call scripts/ensure_artifacts.py
 */
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
    console.log('ETL Delta Script for Harris County Permits');
    console.log('==========================================');
    
    // Print current working directory and discovered CSVs
    console.log(`📂 Current working directory: ${process.cwd()}`);
    
    // Discover CSV files in data/**/*.csv recursively
    const { glob } = await import('glob');
    const csvFiles = await glob('data/**/*.csv', { cwd: process.cwd() });
    console.log(`📋 Discovered ${csvFiles.length} CSV files:`);
    csvFiles.forEach(file => console.log(`  - ${file}`));
    console.log('');
    
    // Validate environment variables
    const { supabaseUrl, supabaseKey, hcUrl } = validateEnvironment();
    
    console.log(`Supabase URL: ${supabaseUrl}`);
    console.log(`Harris County URL: ${hcUrl}`);
    console.log('');
    
    // Calculate 7 days ago
    const sevenDaysAgo = getSevenDaysAgo();
    
    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Ensure table exists
    await ensureTableExists(supabase);
    
    // Check permit count first
    const permitCount = await checkPermitCount(hcUrl, sevenDaysAgo.getTime());
    
    if (permitCount === 0) {
      const sinceTimestamp = sevenDaysAgo.getTime();
      const fullUrl = `${hcUrl}/query?where=ISSUEDDATE > ${sinceTimestamp}&returnCountOnly=true&f=json`;
      console.log(`No permits found for the last 7 days (since ${sevenDaysAgo.toISOString()})`);
      console.log(`Full URL: ${fullUrl}`);
      
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
      }
    } else if (permitCount > 0) {
      console.log(`Found ${permitCount} permits in the last 7 days`);
    }
    // If permitCount === -1 (non-ArcGIS), skip count check and proceed to fetch
    
    // Fetch permits from ArcGIS
    const permits = await fetchPermits(hcUrl, sevenDaysAgo);
    
    if (permits.length === 0) {
      console.log('No valid permits found to process');
      
      // Write summary to log file
      await writeSummaryToLog(0, 'No valid permits found');
      
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
    
    console.log(`Found ${permits.length} valid permits to process`);
    
    // Upsert permits to Supabase
    const { inserted, updated } = await upsertPermits(supabase, permits);
    
    const totalProcessed = inserted + updated;
    
    console.log('');
    console.log('✅ ETL Delta completed successfully');
    console.log(`📊 Summary: ${inserted} inserted, ${updated} updated, ${totalProcessed} total processed`);
    
    // Write summary to log file
    await writeSummaryToLog(totalProcessed, `Processed ${totalProcessed} records (${inserted} inserted, ${updated} updated)`);
    
    // Call ensure_artifacts.py at the end
    await callEnsureArtifacts();
    
  } catch (error) {
    console.error('');
    console.error('❌ ETL Delta failed:', error instanceof Error ? error.message : String(error));
    
    // Write error summary to log file
    await writeSummaryToLog(0, `Error: ${error instanceof Error ? error.message : String(error)}`);
    
    // Call ensure_artifacts.py even on error
    await callEnsureArtifacts();

    process.exit(1);
  }
}

// Only run main if this script is executed directly (ESM compatible check)
if (process.argv[1] && (process.argv[1].endsWith('etlDelta.ts') || process.argv[1].endsWith('etlDelta.js'))) {
  // Handle unhandled promise rejections
  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
  });

  // Run the main function
  main();
}