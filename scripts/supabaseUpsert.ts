#!/usr/bin/env tsx

/**
 * Supabase Upsert Utility
 * Provides idempotent upsert functionality with chunking and error handling
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

/**
 * Upserts data into a Supabase table with chunking and error handling
 * 
 * @param table - Table name to upsert into
 * @param rows - Array of rows to upsert
 * @param conflict - Conflict resolution column(s), defaults to 'event_id'
 * @returns Promise that resolves when all batches are successfully upserted
 */
export async function supabaseUpsert(
  table: string, 
  rows: any[], 
  conflict: string = 'event_id'
): Promise<void> {
  if (!rows || rows.length === 0) {
    console.log('No rows to upsert');
    return;
  }

  // Get Supabase credentials from environment
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl) {
    throw new Error('Missing required environment variable: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');
  }

  if (!supabaseKey) {
    throw new Error('Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');
  }

  // Create Supabase client
  const supabase = createClient(supabaseUrl, supabaseKey);

  console.log(`Upserting ${rows.length} rows to table '${table}' in chunks of 500...`);

  // Chunk data into 500-row batches
  const chunkSize = 500;
  let totalUpserted = 0;

  for (let i = 0; i < rows.length; i += chunkSize) {
    const chunk = rows.slice(i, i + chunkSize);
    const chunkNumber = Math.floor(i / chunkSize) + 1;
    const totalChunks = Math.ceil(rows.length / chunkSize);

    try {
      console.log(`Processing chunk ${chunkNumber}/${totalChunks} (${chunk.length} rows)`);

      const { data, error } = await supabase
        .from(table)
        .upsert(chunk, {
          onConflict: conflict,
          ignoreDuplicates: false
        });

      if (error) {
        throw new Error(`Supabase upsert failed for chunk ${chunkNumber}/${totalChunks}: ${error.message}`);
      }

      totalUpserted += chunk.length;
      console.log(`✅ Successfully upserted chunk ${chunkNumber}/${totalChunks} (${totalUpserted}/${rows.length} total)`);

    } catch (error: any) {
      // Throw with detailed Supabase error message
      const errorMessage = error.message || 'Unknown error during upsert';
      throw new Error(`Failed to upsert chunk ${chunkNumber}/${totalChunks} into table '${table}': ${errorMessage}`);
    }
  }

  console.log(`✅ Successfully upserted all ${totalUpserted} rows to table '${table}'`);
}

/**
 * Helper function to initialize Supabase client with validation
 */
export function createSupabaseClient(): SupabaseClient {
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl) {
    throw new Error('Missing required environment variable: SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL');
  }

  if (!supabaseKey) {
    throw new Error('Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY');
  }

  return createClient(supabaseUrl, supabaseKey);
}