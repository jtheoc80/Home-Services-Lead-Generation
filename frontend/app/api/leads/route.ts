import { NextResponse } from 'next/server';
import { getSupabaseClient } from '../../../lib/supabaseServer';
import { Lead, LeadInsert } from '../../../types/supabase';

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
    }, { status: 500 });
  }
}