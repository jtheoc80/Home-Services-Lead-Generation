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
 * Usage: tsx scripts/etlDelta.ts
 * 
 * Environment Variables:
 *   HC_ISSUED_PERMITS_URL - Harris County FeatureServer URL
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 */

import { createClient } from '@supabase/supabase-js';
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
  issue_date: string | null; // Note: Using issue_date to match table schema, not issue_date_iso
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

function getSevenDaysAgo(): Date {
  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
  return sevenDaysAgo;
}

async function checkPermitCount(baseUrl: string, since: Date): Promise<number> {
  const sinceTimestamp = since.getTime();
  
  const queryParams = new URLSearchParams({
    where: `ISSUEDDATE > ${sinceTimestamp}`,
    returnCountOnly: 'true',
    f: 'json'
  });
  
  const url = `${baseUrl}/query?${queryParams}`;
  
  console.log(`Checking permit count for last 7 days from: ${since.toISOString()}`);
  console.log(`Count query URL: ${url}`);
  
  try {
    const response = await axios.get(url, {
      timeout: 30000,
      headers: {
        'User-Agent': 'Home-Services-Lead-Generation-ETL-Delta/1.0'
      }
    });
    
    if (response.status !== 200) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = response.data as { count: number };
    
    if (typeof data.count !== 'number') {
      throw new Error('Invalid response format: count field missing or not a number');
    }
    
    console.log(`Found ${data.count} permits in the last 7 days`);
    return data.count;
    
  } catch (error) {
    console.error(`Error checking permit count:`, error);
    throw new Error(`Failed to check permit count: ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function fetchPermits(baseUrl: string, since: Date): Promise<PermitRecord[]> {
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
      
      const url = `${baseUrl}/query?${queryParams}`;
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
      
      if (!data.features || !Array.isArray(data.features)) {
        throw new Error('Invalid response format from ArcGIS server');
      }
      
      // Process features
      for (const feature of data.features) {
        const attrs = feature.attributes;
        
        // Map ArcGIS attributes to our schema
        const permit: PermitRecord = {
          event_id: attrs.EVENTID || attrs.OBJECTID || null,
          permit_number: attrs.PERMITNUMBER || null,
          permit_name: attrs.PERMITNAME || attrs.PROJECTNAME || null,
          app_type: attrs.APPTYPE || null,
          issue_date: attrs.ISSUEDDATE ? new Date(attrs.ISSUEDDATE).toISOString() : null,
          full_address: attrs.FULLADDRESS || null,
          status: attrs.STATUS || null,
          project_number: attrs.PROJECTNUMBER || null,
          raw: attrs
        };
        
        // Skip records without event_id
        if (permit.event_id) {
          permits.push(permit);
        }
      }
      
      console.log(`Fetched ${data.features.length} permits in this batch (${permits.length} valid permits so far)`);
      
      // Check if we should continue pagination
      if (data.features.length < PAGE_SIZE && !data.exceededTransferLimit) {
        hasMore = false;
      } else {
        offset += PAGE_SIZE;
      }
      
      // Safety check to prevent infinite loops
      if (offset > 100000) {
      if (offset > MAX_OFFSET_LIMIT) {
        console.warn(`Reached maximum offset limit (${MAX_OFFSET_LIMIT}), stopping pagination`);
        hasMore = false;
      }
      
    } catch (error) {
      console.error(`Error fetching permits at offset ${offset}:`, error);
      throw new Error(`Failed to fetch permits: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  return permits;
}

async function upsertPermits(supabase: SupabaseClient, permits: PermitRecord[]): Promise<{ inserted: number; updated: number }> {
  if (permits.length === 0) {
    console.log('No permits to upsert');
    return { inserted: 0, updated: 0 };
  }
  
  console.log(`Upserting ${permits.length} permits to Supabase in batches of ${UPSERT_BATCH_SIZE}...`);
  
  let totalUpserted = 0;
  let insertedCount = 0;
  let updatedCount = 0;
  
  for (let i = 0; i < permits.length; i += UPSERT_BATCH_SIZE) {
    const batch = permits.slice(i, i + UPSERT_BATCH_SIZE);
    
    try {
      // For tracking inserts vs updates, we'll check existing records first
      const existingIds = batch.map(p => p.event_id);
      const { data: existing, error: selectError } = await supabase
        .from('permits_raw_harris')
        .select('event_id')
        .in('event_id', existingIds);
      
      if (selectError) {
        throw selectError;
      }
      
      const existingIdSet = new Set((existing || []).map((row: any) => row.event_id));
      const batchInserts = batch.filter(p => !existingIdSet.has(p.event_id)).length;
      const batchUpdates = batch.length - batchInserts;
      
      const { error } = await supabase
        .from('permits_raw_harris')
        .upsert(batch, { 
          onConflict: 'event_id',
          ignoreDuplicates: false 
        });
      
      if (error) {
        throw error;
      }
      
      totalUpserted += batch.length;
      insertedCount += batchInserts;
      updatedCount += batchUpdates;
      
      console.log(`Upserted batch ${Math.floor(i / UPSERT_BATCH_SIZE) + 1}/${Math.ceil(permits.length / UPSERT_BATCH_SIZE)} ` +
                  `(${totalUpserted}/${permits.length} total, +${batchInserts} new, ~${batchUpdates} updated)`);
      
    } catch (error) {
      console.error(`Error upserting batch starting at index ${i}:`, error);
      throw new Error(`Failed to upsert permits: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  console.log(`Successfully upserted ${totalUpserted} permits (${insertedCount} inserted, ${updatedCount} updated)`);
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

async function main(): Promise<void> {
  try {
    console.log('ETL Delta Script for Harris County Permits');
    console.log('==========================================');
    
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
    const permitCount = await checkPermitCount(hcUrl, sevenDaysAgo);
    
    if (permitCount === 0) {
      const sinceTimestamp = sevenDaysAgo.getTime();
      const fullUrl = `${hcUrl}/query?where=ISSUEDDATE > ${sinceTimestamp}&returnCountOnly=true&f=json`;
      console.log(`No permits found for the last 7 days (since ${sevenDaysAgo.toISOString()})`);
      console.log(`Full URL: ${fullUrl}`);
      process.exit(0);
    }
    
    // Fetch permits from ArcGIS
    const permits = await fetchPermits(hcUrl, sevenDaysAgo);
    
    if (permits.length === 0) {
      console.log('No valid permits found to process');
      process.exit(0);
    }
    
    console.log(`Found ${permits.length} valid permits to process`);
    
    // Upsert permits to Supabase
    const { inserted, updated } = await upsertPermits(supabase, permits);
    
    console.log('');
    console.log('✅ ETL Delta completed successfully');
    console.log(`📊 Summary: ${inserted} inserted, ${updated} updated, ${inserted + updated} total processed`);
    
  } catch (error) {
    console.error('');
    console.error('❌ ETL Delta failed:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run the main function
main();