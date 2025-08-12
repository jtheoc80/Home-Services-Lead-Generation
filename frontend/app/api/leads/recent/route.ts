import { NextResponse } from 'next/server';
import { getSupabaseClient } from '../../../../lib/supabaseServer';
import { Lead } from '../../../../types/supabase';

/**
 * GET /api/leads/recent
 * Returns the most recent 10 leads ordered by created_at desc
 * Uses server-side Supabase client (service role in test mode, anon otherwise)
 */
export async function GET() {
  try {
    const supabase = getSupabaseClient();
    
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
          trace_id: crypto.randomUUID() 
        }, 
        { status: 400 }
      );
    }

    return NextResponse.json({ 
      data: data as Lead[],
      count: data?.length || 0,
      trace_id: crypto.randomUUID()
    });

  } catch (error) {
    console.error('Unexpected error in recent leads endpoint:', error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Internal server error',
        trace_id: crypto.randomUUID()
      }, 
      { status: 500 }
    );
  }
}