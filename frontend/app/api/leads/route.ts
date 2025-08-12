import { NextResponse } from 'next/server';

import { getSupabaseClient } from '../../../lib/supabaseServer';
import { Lead, LeadInsert } from '../../../types/supabase';

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

function client() {
  const isTestMode = process.env.LEADS_TEST_MODE === "true";
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  
  // Use service role key in test mode, otherwise use anon key
  const supabaseKey = isTestMode 
    ? process.env.SUPABASE_SERVICE_ROLE_KEY!
    : process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
    
  return createClient(supabaseUrl, supabaseKey);
}

async function logIngest(supabase: SupabaseClient, trace_id: string, stage: string, ok: boolean, details?: any) {
  const logEntry: IngestLogInsert = {
    trace_id,
    stage,
    ok,
    details
  };
  
  try {
    await supabase.from('ingest_logs').insert([logEntry]);
  } catch (err) {
    console.error('Failed to insert ingest log:', err);
  }
}


export async function GET() {
  try {
    const supabase = getSupabaseClient();
    const { data, error } = await supabase
      .from('leads')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50);
    
    if (error) {
      return NextResponse.json({ 
        error: error.message,
        trace_id: crypto.randomUUID()
      }, { status: 400 });
    }
    
    return NextResponse.json({ 
      data: data as Lead[],
      trace_id: crypto.randomUUID()
    });
  } catch (error) {
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Internal server error',
      trace_id: crypto.randomUUID()
    }, { status: 500 });
  }
}

export async function POST(req: Request) {

  try {
    const body = await req.json();

    // Create typed payload for lead insertion
    const leadPayload: LeadInsert = {
      source: body.source ?? 'web',
      name: body.name ?? null,
      phone: body.phone ?? null,
      email: body.email ?? null,
      address: body.address ?? null,
      city: body.city ?? null,
      state: body.state ?? null,
      zip: body.zip ?? null
    };

    const supabase = getSupabaseClient();

  const trace_id = randomUUID();
  const received_at = new Date().toISOString();
  const supabase = client();
  
  try {
    // Parse and validate request body
    const body = await req.json();
    
    // Validate with zod schema
    const validationResult = leadSchema.safeParse(body);
    
    if (!validationResult.success) {
      // Log validation failure
      await logIngest(supabase, trace_id, 'validate', false, {
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
    await logIngest(supabase, trace_id, 'validate', true, {
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
    
    // Insert lead into database

    const { data, error } = await supabase
      .from('leads')
      .insert([leadPayload])
      .select('*')
      .single();
    
    if (error) {

      return NextResponse.json({ 
        error: error.message,
        trace_id: crypto.randomUUID()
      }, { status: 400 });
    }
    
    return NextResponse.json({ 
      data: data as Lead,
      trace_id: crypto.randomUUID()
    }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Internal server error',
      trace_id: crypto.randomUUID()

      // Log database insertion failure
      await logIngest(supabase, trace_id, 'db_insert', false, {
        error: error.message,
        received_at
      });
      
      return NextResponse.json({
        ok: false,
        trace_id,
        error: `Database insertion failed: ${error.message}`
      }, { status: 500 });
    }
    
    // Log successful database insertion
    await logIngest(supabase, trace_id, 'db_insert', true, {
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
    await logIngest(supabase, trace_id, 'processing', false, {
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