import { NextResponse } from 'next/server';

import { createClient } from '@supabase/supabase-js';
import { Lead } from '../../../../../types/supabase';
import pino from 'pino';
import { v4 as uuidv4 } from 'uuid';

// Create logger for JSON structured logs (Vercel/Railway compatible)
const logger = pino({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  formatters: {
    level: (label) => {
      return { level: label };
    },
  },
});

function client() {
  const testMode = process.env.LEADS_TEST_MODE === 'true';
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  
  // In test mode, use service role to bypass RLS
  if (testMode && process.env.SUPABASE_SERVICE_ROLE_KEY) {
    return createClient(supabaseUrl, process.env.SUPABASE_SERVICE_ROLE_KEY);
  }
  
  // Normal mode: use anon key (subject to RLS policies)
  return createClient(supabaseUrl, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
}

export async function GET(req: Request) {
  const startTime = Date.now();
  const trace_id = uuidv4();
  const path = new URL(req.url).pathname;
  
  logger.info({ trace_id, path, method: 'GET' }, 'Starting GET /api/leads/recent');

  try {
    const supabase = client();
    
    // Get leads from the last 24 hours, ordered by created_at descending
    const { data, error } = await supabase
      .from('leads')
      .select('*')
      .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
      .order('created_at', { ascending: false })
      .limit(100);
    
    const duration_ms = Date.now() - startTime;
    
    if (error) {
      logger.error({ 
        trace_id, 
        path, 
        error: error.message, 
        supabase_error_code: error.code,
        duration_ms,
        status: 400 
      }, 'Supabase error in GET /api/leads/recent');
      
      return NextResponse.json({ error: error.message, trace_id }, { status: 400 });
    }
    
    logger.info({ 
      trace_id, 
      path, 
      count: data?.length || 0,
      duration_ms,
      status: 200 
    }, 'Successfully retrieved recent leads');
    
    return NextResponse.json({ 
      data: data as Lead[], 
      trace_id,
      count: data?.length || 0,
      timespan: '24h'
    });
    
  } catch (error: any) {
    const duration_ms = Date.now() - startTime;
    
    logger.error({ 
      trace_id, 
      path, 
      error: error.message,
      duration_ms,
      status: 500 
    }, 'Unexpected error in GET /api/leads/recent');
    
    return NextResponse.json({ 
      error: 'Internal server error', 
      trace_id 
    }, { status: 500 });

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