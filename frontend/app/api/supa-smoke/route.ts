import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

/**
 * Smoke test API endpoint for Supabase integration
 * 
 * Inserts a test record into the leads table and returns the total count.
 * Uses service role key for elevated permissions.
 */
async function smokeTest() {
  try {
    // Step 1: Validate environment variables
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl) {
      return NextResponse.json(
        { 
          ok: false, 
          step: 'env-validation', 
          error: 'Missing NEXT_PUBLIC_SUPABASE_URL environment variable' 
        },
        { status: 500 }
      );
    }

    if (!supabaseServiceRoleKey) {
      return NextResponse.json(
        { 
          ok: false, 
          step: 'env-validation', 
          error: 'Missing SUPABASE_SERVICE_ROLE_KEY environment variable' 
        },
        { status: 500 }
      );
    }

    // Step 2: Create Supabase client with service role key
    const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

    // Step 3: Insert smoke test record
    const smokeRecord = {
      name: "Smoke",
      email: "smoke@test.com",
      source: "api"
    };

    const { error: insertError } = await supabase
      .from('leads')
      .insert([smokeRecord]);

    if (insertError) {
      return NextResponse.json(
        { 
          ok: false, 
          step: 'insert-record', 
          error: insertError.message 
        },
        { status: 500 }
      );
    }

    // Step 4: Get total count of leads
    const { count, error: countError } = await supabase
      .from('leads')
      .select('id', { count: 'exact', head: true });

    if (countError) {
      return NextResponse.json(
        { 
          ok: false, 
          step: 'count-records', 
          error: countError.message 
        },
        { status: 500 }
      );
    }

    // Step 5: Return success response
    return NextResponse.json({
      ok: true,
      total: count || 0
    });

  } catch (error) {
    return NextResponse.json(
      { 
        ok: false, 
        step: 'general-error', 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      },
      { status: 500 }
    );
  }
}

// Export both GET and POST for flexibility
export async function GET() {
  return smokeTest();
}

export async function POST() {
  return smokeTest();
}