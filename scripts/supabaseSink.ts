
#!/usr/bin/env tsx

/**
 * Supabase sink for upserting permit data in batches.
 * 
 * TypeScript version of permit_leads/sinks/supabase_sink.py
 * Provides idempotent batch upserts to Supabase with configurable
 * conflict resolution and comprehensive logging.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

export interface UpsertResult {
  success: number;
  failed: number;
}

export class SupabaseSink {
  private client: SupabaseClient;
  private upsertTable: string;
  private conflictCol: string;
  private chunkSize: number;

  /**
   * Initialize Supabase sink.
   * 
   * @param upsertTable - Target table name for upserts
   * @param conflictCol - Column name for conflict resolution (default: event_id)
   * @param chunkSize - Number of records per batch (default: 500)
   */
  constructor(upsertTable: string, conflictCol: string = 'event_id', chunkSize: number = 500) {
    this.upsertTable = upsertTable;
    this.conflictCol = conflictCol;
    this.chunkSize = chunkSize;

    // Read configuration from environment
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error(
        'Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY'
      );
    }

    this.client = createClient(supabaseUrl, supabaseServiceKey);
  }

  /**
   * Upsert a batch of records to Supabase
   */
  async upsertBatch(records: Record<string, any>[]): Promise<UpsertResult> {
    if (!records || records.length === 0) {
      console.log('No records to upsert');
      return { success: 0, failed: 0 };
    }

    try {
      // Serialize records to handle dates and other types
      const serializedRecords = this._serializeRecords(records);
      
      console.log(`Upserting batch of ${serializedRecords.length} records to ${this.upsertTable}`);

      const { data, error } = await this.client
        .from(this.upsertTable)
        .upsert(serializedRecords, {
          onConflict: this.conflictCol,
          ignoreDuplicates: false
        });

      if (error) {
        const errorMsg = `Failed to upsert batch: ${error.message}`;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      const successCount = records.length;
      console.log(`Successfully upserted ${successCount} records to ${this.upsertTable}`);

      return { success: successCount, failed: 0 };

    } catch (error) {
      console.error(`Failed to upsert batch of ${records.length} records: ${error}`);
      return { success: 0, failed: records.length };
    }
  }

  /**
   * Upsert records in chunks
   */
  async upsertRecords(records: Record<string, any>[]): Promise<UpsertResult> {
    if (!records || records.length === 0) {
      console.log('No records to upsert');
      return { success: 0, failed: 0 };
    }

    let totalSuccess = 0;
    let totalFailed = 0;

    console.log(`Processing ${records.length} records in chunks of ${this.chunkSize}`);

    // Process records in chunks
    for (let i = 0; i < records.length; i += this.chunkSize) {
      const chunk = records.slice(i, i + this.chunkSize);
      const chunkNumber = Math.floor(i / this.chunkSize) + 1;
      const totalChunks = Math.ceil(records.length / this.chunkSize);

      try {
        console.log(`Processing chunk ${chunkNumber}/${totalChunks} (${chunk.length} records)`);
        
        const result = await this.upsertBatch(chunk);
        totalSuccess += result.success;
        totalFailed += result.failed;

        console.log(`✅ Chunk ${chunkNumber}/${totalChunks}: ${result.success} success, ${result.failed} failed`);

      } catch (error) {
        console.error(`❌ Chunk ${chunkNumber}/${totalChunks} failed: ${error}`);
        totalFailed += chunk.length;
      }
    }

    console.log(`Final results: ${totalSuccess} success, ${totalFailed} failed out of ${records.length} total`);
    return { success: totalSuccess, failed: totalFailed };
  }

  /**
   * Serialize records to handle dates and other types
   */
  private _serializeRecords(records: Record<string, any>[]): Record<string, any>[] {
    return records.map(record => {
      const serialized: Record<string, any> = {};
      
      for (const [key, value] of Object.entries(record)) {
        if (value instanceof Date) {
          serialized[key] = value.toISOString();
        } else if (value === null || value === undefined) {
          serialized[key] = null;
        } else {
          serialized[key] = value;
        }
      }
      
      return serialized;
    });
  }

  /**
   * Perform a health check on the Supabase connection
   */
  async healthCheck(): Promise<boolean> {
    try {
      // Simple query to test connection
      const { data, error } = await this.client
        .from(this.upsertTable)
        .select('*')
        .limit(1);

      if (error) {
        console.warn('Supabase connection health check failed:', error.message);
        return false;
      }

      console.log('Supabase connection health check passed');
      return true;

    } catch (error) {
      console.error(`Supabase health check failed: ${error}`);
      return false;
    }
  }
}

/**
 * Helper function to create a SupabaseSink instance
 */
export function createSupabaseSink(
  upsertTable: string, 
  conflictCol: string = 'event_id', 
  chunkSize: number = 500
): SupabaseSink {
  return new SupabaseSink(upsertTable, conflictCol, chunkSize);
}


// Wrapper module for Supabase permit upserting
export { upsertPermits } from "./lib/supabaseUpsert";


export type Permit = {
  source_system: "city_of_houston";
  permit_id: string;
  issue_date: string;  // ISO
  trade: string;

import { createClient } from "@supabase/supabase-js";

export type Permit = {
  source_system: string;   // e.g. "city_of_houston"
  permit_id: string;
  issue_date: string;      // ISO (or 'YYYY-MM-DD')
  trade?: string;

  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;

};

};

const url = process.env.SUPABASE_URL;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!url) {
  throw new Error("Missing required environment variable: SUPABASE_URL");
}
if (!key) {
  throw new Error("Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY");
}
const sb = createClient(url, key, { auth: { persistSession: false } });

export async function upsertPermits(rows: Permit[], chunk = 500) {
  let upserted = 0;
  for (let i = 0; i < rows.length; i += chunk) {
    const batch = rows.slice(i, i + chunk);
    const { error, count } = await sb
      .from("permits")
      .upsert(batch, { onConflict: "source_system,permit_id", ignoreDuplicates: false, count: "estimated" });
    if (error) throw error;
    upserted += count ?? batch.length; // supabase-js may not return count—fallback
  }
  return upserted;
}


