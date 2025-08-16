import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function POST() {
  try {
    const admin = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY! // server-only
    )
    
    const p = {
      source: 'selftest',
      source_record_id: 'sentinel-001',
      jurisdiction: 'Austin',
      county: 'Travis',
      permit_no: 'SENT-001',
      status: 'Issued',
      address: '100 Test St',
      city: 'Austin',
      state: 'TX',
      issued_date: new Date().toISOString(),
    }
    const { error } = await admin.rpc('upsert_permit', { p })
    if (error) return NextResponse.json({ ok: false, error: error.message }, { status: 500 })
    return NextResponse.json({ ok: true })
  } catch (e: unknown) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 500 })
  }
}