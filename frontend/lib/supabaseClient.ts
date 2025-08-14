import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseInstance: SupabaseClient | null = null;

// "browser client" only – safe to use with anon key
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

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
      'Missing Supabase configuration. Please ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set as client-side environment variables (prefixed with NEXT_PUBLIC_) in your .env file. These must be available to the browser at build time.'
    );
  }

  // Create and cache the instance
  supabaseInstance = createClient(supabaseUrl, supabaseAnonKey);
  return supabaseInstance;
}