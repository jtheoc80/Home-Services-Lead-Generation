import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { Lead, LeadInsert } from '../../../../types/supabase';

function client() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

export async function GET() {
  const supabase = client();
  const { data, error } = await supabase
    .from('leads')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(50);
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ data: data as Lead[] });
}

export async function POST(req: Request) {
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

  const supabase = client();
  const { data, error } = await supabase
    .from('leads')
    .insert([leadPayload])
    .select('*')
    .single();
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ data: data as Lead }, { status: 201 });
}