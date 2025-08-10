import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseInstance: SupabaseClient | null = null;

/**
 * Get Supabase client instance with safe initialization
 * Returns null on server-side to prevent build-time crashes
 * Throws descriptive error in browser if environment variables are missing
 */
export function getSupabase(): SupabaseClient | null {
  // Return null on server-side to prevent build-time initialization
  if (typeof window === 'undefined') {
    return null;
  }

  // Return existing instance if already created
  if (supabaseInstance) {
    return supabaseInstance;
  }

  // Check for required environment variables
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Missing Supabase configuration. Please ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set in your environment variables.'
    );
  }

  // Create and cache the instance
  supabaseInstance = createClient(supabaseUrl, supabaseAnonKey);
  return supabaseInstance;
}