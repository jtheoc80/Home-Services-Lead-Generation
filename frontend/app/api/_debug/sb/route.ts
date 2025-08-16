import { NextResponse } from 'next/server'
import { createServiceClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET() {
  try {
    const sb = createServiceClient()
    const { count: leads } = await sb.from('leads').select('*', { count: 'exact', head: true })
    const { count: permits } = await sb.from('permits').select('*', { count: 'exact', head: true })
    return NextResponse.json({
      ok: true,
      url: process.env.NEXT_PUBLIC_SUPABASE_URL,
      leads, permits,
    })
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 500 })
  }
}