import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Browser-side Supabase client with safe initialization
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Create client only if environment variables are available
export const supabase = supabaseUrl && supabaseAnonKey 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

/**
 * Get Supabase client with better error handling
 * Returns the client or throws descriptive error for debugging
 */
export function getSupabaseClient(): SupabaseClient {
  if (!supabase) {
    const missing = [];
    if (!supabaseUrl) missing.push('NEXT_PUBLIC_SUPABASE_URL');
    if (!supabaseAnonKey) missing.push('NEXT_PUBLIC_SUPABASE_ANON_KEY');
    
    throw new Error(
      `Supabase configuration missing: ${missing.join(', ')}. ` +
      'Please check your .env.local file and ensure these environment variables are set.'
    );
  }
  return supabase;
}

/**
 * Check if Supabase is properly configured
 */
export function isSupabaseConfigured(): boolean {
  return !!(supabaseUrl && supabaseAnonKey);
}