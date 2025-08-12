import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import pino from 'pino';

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
  // Always use service role for debug endpoints to access all data
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const startTime = Date.now();
  const traceId = params.id;
  const path = new URL(req.url).pathname;
  
  // Check for debug API key in header
  const debugKey = req.headers.get('X-Debug-Key');
  if (!debugKey || debugKey !== process.env.DEBUG_API_KEY) {
    logger.warn({ 
      trace_id: traceId, 
      path, 
      provided_key: debugKey ? '[REDACTED]' : 'none',
      status: 401 
    }, 'Unauthorized debug endpoint access');
    
    return NextResponse.json({ 
      error: 'Unauthorized. X-Debug-Key header required.' 
    }, { status: 401 });
  }
  
  logger.info({ trace_id: traceId, path, method: 'GET' }, 'Starting debug trace lookup');

  try {
    const supabase = client();
    
    // Get all ingest_logs for this trace_id
    const { data: logs, error: logsError } = await supabase
      .from('ingest_logs')
      .select('*')
      .eq('trace_id', traceId)
      .order('created_at', { ascending: true });
    
    if (logsError) {
      logger.error({ 
        trace_id: traceId, 
        path, 
        error: logsError.message,
        status: 400 
      }, 'Error fetching ingest_logs');
      
      return NextResponse.json({ 
        error: logsError.message,
        trace_id: traceId 
      }, { status: 400 });
    }
    
    // Try to find any leads created during this trace (if applicable)
    const { data: leads, error: leadsError } = await supabase
      .from('leads')
      .select('*')
      .eq('id', traceId); // This might not match, but we try
    
    // If direct ID match doesn't work, look for leads created around the time of this trace
    let relatedLeads = leads;
    if (!leads || leads.length === 0) {
      const firstLogTime = logs && logs.length > 0 ? logs[0].created_at : null;
      if (firstLogTime) {
        // Look for leads created within 1 minute of the trace
        const timeWindow = new Date(new Date(firstLogTime).getTime() - 60000).toISOString();
        const timeWindowEnd = new Date(new Date(firstLogTime).getTime() + 60000).toISOString();
        
        const { data: nearbyLeads } = await supabase
          .from('leads')
          .select('*')
          .gte('created_at', timeWindow)
          .lte('created_at', timeWindowEnd)
          .order('created_at', { ascending: false })
          .limit(10);
        
        relatedLeads = nearbyLeads;
      }
    }
    
    const duration_ms = Date.now() - startTime;
    
    logger.info({ 
      trace_id: traceId, 
      path, 
      logs_count: logs?.length || 0,
      leads_count: relatedLeads?.length || 0,
      duration_ms,
      status: 200 
    }, 'Successfully retrieved trace debug info');
    
    return NextResponse.json({ 
      trace_id: traceId,
      ingest_logs: logs || [],
      related_leads: relatedLeads || [],
      summary: {
        total_logs: logs?.length || 0,
        successful_stages: logs?.filter(log => log.ok).length || 0,
        failed_stages: logs?.filter(log => !log.ok).length || 0,
        stages: logs?.map(log => log.stage) || [],
        duration_ms
      }
    });
    
  } catch (error: any) {
    const duration_ms = Date.now() - startTime;
    
    logger.error({ 
      trace_id: traceId, 
      path, 
      error: error.message,
      duration_ms,
      status: 500 
    }, 'Unexpected error in debug trace lookup');
    
    return NextResponse.json({ 
      error: 'Internal server error', 
      trace_id: traceId 
    }, { status: 500 });
  }
}