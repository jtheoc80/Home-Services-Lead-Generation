import { NextResponse } from 'next/server'
import { createServiceClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET() {
  try {
    const supabase = createServiceClient()
    const { data, error } = await supabase
      .from('leads')
      .select('id,name,county,status')
      .limit(5)
    
    if (error) {
      return NextResponse.json({ 
        ok: false, 
        error: error.message 
      }, { status: 500 })
    }
    
    return NextResponse.json({ 
      ok: true, 
      rows: data 
    })
  } catch (error: any) {
    return NextResponse.json({ 
      ok: false, 
      error: error.message || 'Unknown error'
    }, { status: 500 })
  }
}