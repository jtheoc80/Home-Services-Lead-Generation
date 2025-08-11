import { NextResponse } from 'next/server';

/**
 * TEMPORARY ENDPOINT FOR TESTING SUPABASE ENVIRONMENT VARIABLES
 * 
 * !!! SECURITY WARNING !!!
 * This endpoint exposes partial information about environment variables.
 * DELETE THIS FILE AFTER TESTING IS COMPLETE.
 * 
 * Returns:
 * - url: boolean indicating if NEXT_PUBLIC_SUPABASE_URL is set
 * - anon: masked NEXT_PUBLIC_SUPABASE_ANON_KEY (only showing last 4 characters)
 */
export async function GET() {
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    // Check if URL exists and convert to boolean
    const urlExists = !!supabaseUrl;

    // Mask the anon key to show only last 4 characters
    let maskedAnonKey = '';
    if (supabaseAnonKey && supabaseAnonKey.length > 4) {
      const lastFour = supabaseAnonKey.slice(-4);
      const maskLength = supabaseAnonKey.length - 4;
      maskedAnonKey = '*'.repeat(maskLength) + lastFour;
    } else if (supabaseAnonKey) {
      // If key is 4 characters or less, mask all but show it exists
      maskedAnonKey = '*'.repeat(supabaseAnonKey.length);
    } else {
      maskedAnonKey = 'NOT_SET';
    }

    return NextResponse.json(
      {
        url: urlExists,
        anon: maskedAnonKey
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
  } catch (error) {
    console.error('Error in supa-env-check:', error);
    
    return NextResponse.json(
      {
        error: 'Internal server error'
      },
      { status: 500 }
    );
  }
}