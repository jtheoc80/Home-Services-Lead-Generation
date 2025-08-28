import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseInstance: SupabaseClient | null = null;

// Startup environment check - runs immediately when module is imported
function validateSupabaseEnvironment(): { supabaseUrl: string; supabaseAnonKey: string } | null {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  const missing = [];
  if (!supabaseUrl) missing.push('NEXT_PUBLIC_SUPABASE_URL');
  if (!supabaseAnonKey) missing.push('NEXT_PUBLIC_SUPABASE_ANON_KEY');
  
  if (missing.length > 0) {
    const errorMessage = 
      `Missing Supabase configuration: ${missing.join(', ')}. ` +
      'Please check your .env.local file and ensure these environment variables are set.';
    
    // Check if we're in production mode
    const isProduction = process.env.NEXT_PUBLIC_ENVIRONMENT === 'production';
    
    if (isProduction) {
      // In production, warn but don't crash the app
      console.warn('⚠️ Supabase Configuration Warning:', errorMessage);
      console.warn('Some features may not work correctly.');
      return null;
    } else {
      // In development, fail fast with clear error
      throw new Error(errorMessage);
    }
  }
  
  // TypeScript knows these are strings now because of the checks above
  return { supabaseUrl: supabaseUrl!, supabaseAnonKey: supabaseAnonKey! };
}

// Validate environment on module load
const envConfig = validateSupabaseEnvironment();

// "browser client" only – safe to use with anon key
export const supabase = envConfig 
  ? createClient(envConfig.supabaseUrl, envConfig.supabaseAnonKey)
  : null;

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

  // If the exported supabase client exists, use it
  if (supabase) {
    supabaseInstance = supabase;
    return supabaseInstance;
  }

  // Environment validation already ran at module load time
  // If we reach here, it means we're in production mode with missing env vars
  throw new Error(
    'Supabase client not available. Environment variables were missing at startup. ' +
    'Please ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set.'
  );
}