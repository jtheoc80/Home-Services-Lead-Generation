#!/usr/bin/env tsx

/**
 * Harris County Issued Permits Data Fetcher
 * 
 * Fetches issued permits from Harris County ArcGIS FeatureServer and stores them in Supabase.
 * 
 * Usage:
 *   tsx scripts/harrisCounty/issuedPermits.ts [--since YYYY-MM-DD]
 * 
 * Environment Variables:
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key for database access
 *   HC_ISSUED_PERMITS_URL - Harris County FeatureServer URL (optional, defaults to known URL)
 */

import { createClient } from '@supabase/supabase-js';
import axios from 'axios';

// Default Harris County Issued Permits FeatureServer URL
const DEFAULT_HC_URL = 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0';

// Pagination size for ArcGIS queries
const PAGE_SIZE = 2000;

interface ArcGISFeature {
  attributes: Record<string, any>;
}

interface ArcGISResponse {
  features: ArcGISFeature[];
  exceededTransferLimit?: boolean;
}

interface PermitRecord {
  event_id: string;
  permit_number: string | null;
  permit_name: string | null;
  app_type: string | null;
  issue_date: string | null;
  project_number: string | null;
  full_address: string | null;
  street_number: string | null;
  street_name: string | null;
  status: string | null;
  raw: Record<string, any>;
}

function parseArgs(): { since: Date } {
  const args = process.argv.slice(2);
  let sinceDate = new Date();
  
  // Default to 3 days ago
  sinceDate.setDate(sinceDate.getDate() - 3);
  
  // Parse --since argument
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--since' && i + 1 < args.length) {
      const dateStr = args[i + 1];
      const parsed = new Date(dateStr);
      if (!isNaN(parsed.getTime())) {
        sinceDate = parsed;
      } else {
        console.error(`Invalid date format: ${dateStr}`);
        process.exit(1);
      }
      break;
    }
  }
  
  return { since: sinceDate };
}

function validateEnvironment(): { supabaseUrl: string; supabaseKey: string; hcUrl: string } {
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const hcUrl = process.env.HC_ISSUED_PERMITS_URL || DEFAULT_HC_URL;
  
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

async function fetchPermits(baseUrl: string, since: Date): Promise<PermitRecord[]> {
  const permits: PermitRecord[] = [];
  let offset = 0;
  let hasMore = true;
  
  // Format date for ArcGIS query (epoch milliseconds)
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
          'User-Agent': 'Home-Services-Lead-Generation/1.0'
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
          event_id: attrs.EVENTID?.toString() || attrs.OBJECTID?.toString() || `unknown_${Date.now()}_${Math.random()}`,
          permit_number: attrs.PERMITNUMBER || null,
          permit_name: attrs.PERMITNAME || attrs.PROJECTNAME || null,
          app_type: attrs.APPTYPE || null,
          issue_date: attrs.ISSUEDDATE ? new Date(attrs.ISSUEDDATE).toISOString() : null,
          project_number: attrs.PROJECTNUMBER || null,
          full_address: attrs.FULLADDRESS || null,
          street_number: attrs.STREETNUMBER || null,
          street_name: attrs.STREETNAME || null,
          status: attrs.STATUS || null,
          raw: attrs
        };
        
        permits.push(permit);
      }
      
      console.log(`Fetched ${data.features.length} permits in this batch`);
      
      // Check if we should continue pagination
      if (data.features.length < PAGE_SIZE && !data.exceededTransferLimit) {
        hasMore = false;
      } else {
        offset += PAGE_SIZE;
      }
      
      // Safety check to prevent infinite loops
      if (offset > 100000) {
        console.warn('Reached maximum offset limit (100,000), stopping pagination');
        hasMore = false;
      }
      
    } catch (error) {
      console.error(`Error fetching permits at offset ${offset}:`, error);
      throw error;
    }
  }
  
  return permits;
}

async function upsertPermits(supabase: any, permits: PermitRecord[]): Promise<void> {
  if (permits.length === 0) {
    console.log('No permits to upsert');
    return;
  }
  
  console.log(`Upserting ${permits.length} permits to Supabase...`);
  
  // Upsert in batches to avoid Supabase limits
  const batchSize = 1000;
  let upsertedCount = 0;
  
  for (let i = 0; i < permits.length; i += batchSize) {
    const batch = permits.slice(i, i + batchSize);
    
    try {
      const { error } = await supabase
        .from('permits_raw_harris')
        .upsert(batch, { 
          onConflict: 'event_id',
          ignoreDuplicates: false 
        });
      
      if (error) {
        throw error;
      }
      
      upsertedCount += batch.length;
      console.log(`Upserted batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(permits.length / batchSize)} (${upsertedCount}/${permits.length} total)`);
      
    } catch (error) {
      console.error(`Error upserting batch starting at index ${i}:`, error);
      throw error;
    }
  }
  
  console.log(`Successfully upserted ${upsertedCount} permits`);
}

async function ensureTableExists(supabase: any): Promise<void> {
  // Check if the table exists by trying to query it
  try {
    const { error } = await supabase
      .from('permits_raw_harris')
      .select('event_id', { count: 'exact', head: true })
      .limit(1);
    
    if (error && error.code === 'PGRST116') {
      // Table doesn't exist, provide helpful error
      console.error('Table permits_raw_harris does not exist. Please create it with the following schema:');
      console.error(`
CREATE TABLE permits_raw_harris (
  event_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_name TEXT,
  app_type TEXT,
  issue_date TIMESTAMPTZ,
  project_number TEXT,
  full_address TEXT,
  street_number TEXT,
  street_name TEXT,
  status TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_permits_raw_harris_issue_date ON permits_raw_harris(issue_date);
CREATE INDEX idx_permits_raw_harris_status ON permits_raw_harris(status);
CREATE INDEX idx_permits_raw_harris_app_type ON permits_raw_harris(app_type);
      `);
      process.exit(1);
    } else if (error) {
      throw error;
    }
    
    console.log('Table permits_raw_harris exists and is accessible');
  } catch (error) {
    console.error('Error checking table existence:', error);
    process.exit(1);
  }
}

async function main() {
  try {
    // Parse command line arguments
    const { since } = parseArgs();
    
    // Validate environment variables
    const { supabaseUrl, supabaseKey, hcUrl } = validateEnvironment();
    
    console.log('Harris County Issued Permits Fetcher');
    console.log('====================================');
    console.log(`Supabase URL: ${supabaseUrl}`);
    console.log(`Harris County URL: ${hcUrl}`);
    console.log(`Fetching permits since: ${since.toISOString()}`);
    console.log('');
    
    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Ensure table exists
    await ensureTableExists(supabase);
    
    // Fetch permits from ArcGIS
    const permits = await fetchPermits(hcUrl, since);
    
    if (permits.length === 0) {
      console.log('No new permits found');
      return;
    }
    
    console.log(`Found ${permits.length} permits to process`);
    
    // Upsert permits to Supabase
    await upsertPermits(supabase, permits);
    
    console.log('✅ Successfully completed permit data sync');
    
  } catch (error) {
    console.error('❌ Error occurred:', error);
    process.exit(1);
  }
}

// Run the main function
main();