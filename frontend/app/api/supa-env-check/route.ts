import { NextResponse } from 'next/server';

/**
 * TEMPORARY ENDPOINT FOR TESTING SUPABASE ENVIRONMENT VARIABLES
 * 
 * !!! SECURITY WARNING !!!
 * This endpoint exposes partial information about environment variables.
 * DELETE THIS FILE AFTER TESTING IS COMPLETE.
 * 
 * Returns:
 * - urlSet: boolean indicating if NEXT_PUBLIC_SUPABASE_URL is set
 * - anonKeySuffix: last 4 characters of NEXT_PUBLIC_SUPABASE_ANON_KEY
 * - hasServiceKey: boolean indicating if SUPABASE_SERVICE_ROLE_KEY is set
 */
export async function GET() {
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    // Check if URL exists and convert to boolean
    const urlSet = !!supabaseUrl;

    // Get last 4 characters of anon key (or empty string if not set)
    const anonKeySuffix = supabaseAnonKey && supabaseAnonKey.length >= 4 
      ? supabaseAnonKey.slice(-4) 
      : '';

    // Check if service key exists and convert to boolean
    const hasServiceKey = !!supabaseServiceKey;

    return NextResponse.json(
      {
        urlSet,
        anonKeySuffix,
        hasServiceKey
      },
      { 
        status: 200,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      }
    );
  } catch {
    console.error('Error in supa-env-check occurred.');
    
    return NextResponse.json(
      {
        error: 'Internal server error'
      },
      { status: 500 }
    );
  }
}