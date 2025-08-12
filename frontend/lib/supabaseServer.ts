import { createClient, SupabaseClient } from '@supabase/supabase-js';

/**
 * Get server-side Supabase client instance
 * In test mode (LEADS_TEST_MODE==="true"), uses service role key
 * Otherwise uses anonymous key
 * @param options Configuration options
 * @param options.useServiceRole Force service role usage (overrides test mode check)
 * @returns Supabase client instance
 * @throws Error if required environment variables are missing
 */
export function getSupabaseClient({ useServiceRole = false }: { useServiceRole?: boolean } = {}): SupabaseClient {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  
  if (!supabaseUrl) {
    throw new Error(
      'Missing Supabase URL. Please ensure NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL is set in your environment variables.'
    );
  }

  // Determine if we should use service role
  const isTestMode = process.env.LEADS_TEST_MODE === "true";
  const shouldUseServiceRole = useServiceRole || isTestMode;

  if (shouldUseServiceRole) {
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    if (!serviceRoleKey) {
      throw new Error(
        'Missing Supabase Service Role Key. Please ensure SUPABASE_SERVICE_ROLE_KEY is set in your environment variables. This is required when LEADS_TEST_MODE=true or useServiceRole=true.'
      );
    }

    return createClient(supabaseUrl, serviceRoleKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    });
  } else {
    const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;
    
    if (!anonKey) {
      throw new Error(
        'Missing Supabase Anonymous Key. Please ensure NEXT_PUBLIC_SUPABASE_ANON_KEY or SUPABASE_ANON_KEY is set in your environment variables.'
      );
    }

    return createClient(supabaseUrl, anonKey);
  }
}