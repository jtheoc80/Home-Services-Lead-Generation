import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { z } from 'zod';
import { randomUUID } from 'crypto';
import { Lead, LeadInsert, IngestLogInsert } from '../../../../types/supabase';

// Zod schema for lead validation
const leadSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email is required'),
  phone: z.string().min(1, 'Phone is required'),
  source: z.string().min(1, 'Source is required')
});

// Get Supabase client based on test mode
function getSupabaseClient() {
  const isTestMode = process.env.LEADS_TEST_MODE === "true";
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  
  if (!supabaseUrl) {
    throw new Error('NEXT_PUBLIC_SUPABASE_URL is required');
  }
  
  // Use service role key in test mode, otherwise use anon key
  if (isTestMode) {
    const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!serviceKey) {
      throw new Error('SUPABASE_SERVICE_ROLE_KEY is required when LEADS_TEST_MODE=true');
    }
    return createClient(supabaseUrl, serviceKey);
  } else {
    const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!anonKey) {
      throw new Error('NEXT_PUBLIC_SUPABASE_ANON_KEY is required');
    }
    return createClient(supabaseUrl, anonKey);
  }
}

// Log to ingest_logs table
async function logIngest(trace_id: string, stage: string, ok: boolean, details?: any) {
  try {
    const supabase = getSupabaseClient();
    const logEntry: IngestLogInsert = {
      trace_id,
      stage,
      ok,
      details
    };
    
    await supabase.from('ingest_logs').insert([logEntry]);
  } catch (err) {
    console.error('Failed to insert ingest log:', err);
  }
}

export async function POST(req: Request) {
  // Only allow in test mode
  if (process.env.LEADS_TEST_MODE !== "true") {
    return NextResponse.json({
      ok: false,
      error: 'This endpoint is only available when LEADS_TEST_MODE=true'
    }, { status: 403 });
  }

  const trace_id = randomUUID();
  const received_at = new Date().toISOString();
  
  try {
    // Parse and validate request body
    const body = await req.json();
    
    // Log request received
    await logIngest(trace_id, 'request_received', true, {
      message: 'Request received',
      received_at
    });
    
    // Validate with zod schema
    const validationResult = leadSchema.safeParse(body);
    
    if (!validationResult.success) {
      // Log validation failure
      await logIngest(trace_id, 'validate', false, {
        error: 'Validation failed',
        issues: validationResult.error.issues,
        received_at
      });
      
      return NextResponse.json({
        ok: false,
        trace_id,
        error: `Validation failed: ${validationResult.error.issues.map(i => i.message).join(', ')}`
      }, { status: 400 });
    }
    
    // Log successful validation
    await logIngest(trace_id, 'validate', true, {
      message: 'Validation successful',
      received_at
    });
    
    const validatedData = validationResult.data;
    
    // Create typed payload for lead insertion
    const leadPayload: LeadInsert = {
      source: validatedData.source,
      name: validatedData.name,
      phone: validatedData.phone,
      email: validatedData.email
    };
    
    // Get Supabase client (will use service role in test mode)
    const supabase = getSupabaseClient();
    
    // Insert lead into database
    const { data, error } = await supabase
      .from('leads')
      .insert([leadPayload])
      .select('*')
      .single();
    
    if (error) {
      // Log database insertion failure
      await logIngest(trace_id, 'db_insert', false, {
        error: error.message,
        code: error.code,
        received_at
      });
      
      return NextResponse.json({
        ok: false,
        trace_id,
        error: `Database insertion failed: ${error.message}`
      }, { status: 500 });
    }
    
    // Log successful database insertion
    await logIngest(trace_id, 'db_insert', true, {
      message: 'Lead inserted successfully',
      lead_id: data.id,
      received_at
    });
    
    return NextResponse.json({
      ok: true,
      trace_id
    }, { status: 201 });
    
  } catch (error) {
    // Log unexpected error
    await logIngest(trace_id, 'processing', false, {
      error: 'Unexpected error during processing',
      details: error instanceof Error ? error.message : 'Unknown error',
      received_at
    });
    
    return NextResponse.json({
      ok: false,
      trace_id,
      error: 'Internal server error'
    }, { status: 500 });
  }
}