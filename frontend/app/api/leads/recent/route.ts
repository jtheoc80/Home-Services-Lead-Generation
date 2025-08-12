import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { randomUUID } from 'crypto';
import { Lead } from '../../../../../types/supabase';

function client() {
  const isTestMode = process.env.LEADS_TEST_MODE === "true";
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  
  // Use service role key in test mode, otherwise use anon key
  const supabaseKey = isTestMode 
    ? process.env.SUPABASE_SERVICE_ROLE_KEY!
    : process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
    
  return createClient(supabaseUrl, supabaseKey);
}

/**
 * GET /api/leads/recent
 * Returns the most recent 10 leads ordered by created_at desc
 * Uses server-side Supabase client (service role in test mode, anon otherwise)
 */
export async function GET() {
  try {
    const supabase = client();
    
    const { data, error } = await supabase
      .from('leads')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) {
      console.error('Error fetching recent leads:', error);
      return NextResponse.json(
        { 
          error: error.message,
          trace_id: randomUUID() 
        }, 
        { status: 400 }
      );
    }

    return NextResponse.json({ 
      data: data as Lead[],
      count: data?.length || 0,
      trace_id: randomUUID()
    });

  } catch (error) {
    console.error('Unexpected error in recent leads endpoint:', error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Internal server error',
        trace_id: randomUUID()
      }, 
      { status: 500 }
    );
  }
}