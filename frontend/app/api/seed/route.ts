import { NextResponse } from 'next/server'
import { createServiceClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function POST() {
  try {
    const supabase = createServiceClient()
    
    // Generate a test lead based on the current timestamp
    const now = new Date()
    const testLead = {
      name: `Test Lead ${now.toISOString().slice(11, 16)}`, // Include time for uniqueness
      email: `test${Date.now()}@example.com`,
      phone: '+1-713-555-' + String(Math.floor(1000 + Math.random() * 9000)),
      address: `${Math.floor(100 + Math.random() * 9900)} Test St`,
      city: 'Houston',
      state: 'TX',
      zip: '77001',
      county: 'Harris',
      service: 'HVAC Installation',
      status: 'new',
      lead_score: Math.floor(60 + Math.random() * 40), // Score between 60-100
      value: Math.floor(10000 + Math.random() * 40000), // Value between $10k-$50k
      source: 'api_seed',
      created_at: now.toISOString()
    }
    
    const { data, error } = await supabase
      .from('leads')
      .insert([testLead])
      .select()
    
    if (error) {
      return NextResponse.json({ 
        ok: false, 
        error: error.message 
      }, { status: 500 })
    }
    
    return NextResponse.json({ 
      ok: true, 
      message: 'Test lead created successfully',
      lead: data?.[0] || testLead
    })
  } catch (error: any) {
    return NextResponse.json({ 
      ok: false, 
      error: error.message || 'Unknown error'
    }, { status: 500 })
  }
}