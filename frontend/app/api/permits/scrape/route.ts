import { NextResponse } from 'next/server'
import { createServiceClient } from '@/lib/supabase/server'

type Normalized = {
  source: string
  source_record_id: string
  jurisdiction: string
  county?: string
  permit_no?: string
  permit_type?: string
  category?: string
  status?: string
  description?: string
  value?: number
  address?: string
  city?: string
  state?: string
  zipcode?: string
  latitude?: number
  longitude?: number
  applied_date?: string
  issued_date?: string
  scraped_at?: string
}

// --- Example fetchers with real API endpoints ---
async function fetchAustin(): Promise<Normalized[]> {
  // Austin Socrata API - Building permits
  const url = `https://data.austintexas.gov/resource/3syk-w9eu.json?$limit=2000`
  const headers: Record<string, string> = {}
  if (process.env.AUSTIN_SOCRATA_TOKEN) {
    headers['X-App-Token'] = process.env.AUSTIN_SOCRATA_TOKEN
  }
  
  const r = await fetch(url, { headers })
  const rows = await r.json()
  return rows.map((x: any) => ({
    source: 'austin_socrata',
    source_record_id: String(x.permit_number ?? x.objectid ?? x.id),
    jurisdiction: 'Austin',
    county: 'Travis',
    permit_no: x.permit_number,
    permit_type: x.permit_type,
    category: x.category ?? x.work_type,
    status: x.status_current ?? x.status,
    description: x.description ?? x.work_description,
    value: Number(x.total_valuation ?? x.estimated_value ?? x.valuation ?? 0),
    address: x.original_address1 ?? x.address ?? x.street_address,
    city: 'Austin',
    state: 'TX',
    zipcode: x.zip || x.zipcode,
    latitude: Number(x.latitude ?? x.location?.latitude ?? 0) || undefined,
    longitude: Number(x.longitude ?? x.location?.longitude ?? 0) || undefined,
    applied_date: x.applied_date || x.file_date,
    issued_date: x.issued_date || x.issue_date,
    scraped_at: new Date().toISOString(),
  }))
}

async function fetchHouston(): Promise<Normalized[]> {
  // Houston CSV feed
  const url = `https://www.houstontx.gov/planning/DevelopReview/permits_issued.csv`
  const r = await fetch(url)
  const text = await r.text()
  const [header, ...lines] = text.split(/\r?\n/)
  const cols = header.split(',').map(col => col.replace(/"/g, ''))
  
  return lines.filter(Boolean).map(line => {
    // Simple CSV parsing - in production, use a proper CSV parser
    const values = line.split(',').map(val => val.replace(/"/g, ''))
    const get = (k: string) => {
      const index = cols.findIndex(col => col.toLowerCase().includes(k.toLowerCase()))
      return index >= 0 ? values[index] : ''
    }
    
    return {
      source: 'houston_csv',
      source_record_id: String(get('permit') || get('number') || get('id')),
      jurisdiction: 'Houston',
      county: 'Harris',
      permit_no: get('permit') || get('number'),
      permit_type: get('type') || get('permit_type'),
      category: get('category') || get('work_type'),
      status: get('status'),
      description: get('description') || get('work_description'),
      value: Number(get('value') || get('valuation') || get('cost') || 0),
      address: get('address') || get('location'),
      city: 'Houston',
      state: 'TX',
      zipcode: get('zip') || get('zipcode'),
      latitude: Number(get('lat') || get('latitude') || 0) || undefined,
      longitude: Number(get('lon') || get('lng') || get('longitude') || 0) || undefined,
      applied_date: get('applied') || get('application_date'),
      issued_date: get('issued') || get('issue_date'),
      scraped_at: new Date().toISOString(),
    } as Normalized
  })
}

async function fetchDallas(): Promise<Normalized[]> {
  // Dallas Socrata API - Building permits
  const url = `https://www.dallasopendata.com/resource/e7gq-4sah.json?$limit=2000`
  const headers: Record<string, string> = {}
  if (process.env.DALLAS_SOCRATA_TOKEN) {
    headers['X-App-Token'] = process.env.DALLAS_SOCRATA_TOKEN
  }
  
  const r = await fetch(url, { headers })
  const rows = await r.json()
  return rows.map((x: any) => ({
    source: 'dallas_socrata',
    source_record_id: String(x.permit_number ?? x.objectid ?? x.id),
    jurisdiction: 'Dallas',
    county: 'Dallas',
    permit_no: x.permit_number,
    permit_type: x.permit_type,
    category: x.category ?? x.work_type,
    status: x.permit_status ?? x.status,
    description: x.work_description ?? x.description,
    value: Number(x.estimated_cost ?? x.valuation ?? x.value ?? 0),
    address: x.address,
    city: 'Dallas',
    state: 'TX',
    zipcode: x.zip || x.zipcode,
    latitude: Number(x.latitude ?? 0) || undefined,
    longitude: Number(x.longitude ?? 0) || undefined,
    applied_date: x.application_date || x.applied_date,
    issued_date: x.issued_date || x.issue_date,
    scraped_at: new Date().toISOString(),
  }))
}

// Map the `source` query to a fetcher
const FETCHERS: Record<string, () => Promise<Normalized[]>> = {
  austin: fetchAustin,
  houston: fetchHouston,
  dallas: fetchDallas,
}

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function POST(req: Request) {
  // Check for x-cron-secret header first
  const secret = req.headers.get('x-cron-secret')
  if (secret !== process.env.CRON_SECRET) {
    return new Response('Forbidden', { status: 403 })
  }

  try {
    const { searchParams } = new URL(req.url)
    const key = searchParams.get('source') || 'austin'
    const fetcher = FETCHERS[key]
    if (!fetcher) {
      return NextResponse.json({ ok: false, error: `Unknown source: ${key}` }, { status: 400 })
    }

    const rows = await fetcher()
    let upserts = 0
    let errors = 0

    // Get Supabase client with service role
    const supabase = createServiceClient()

    // Preferred: use RPC so we get ON CONFLICT + type casting in SQL
    for (const row of rows) {
      try {
        const { error } = await supabase.rpc('upsert_permit', { p: row as any })
        if (error) {
          console.error('Upsert error:', error)
          errors++
        } else {
          upserts++
        }
      } catch (e) {
        console.error('Unexpected error during upsert:', e)
        errors++
      }
    }

    return NextResponse.json({ 
      ok: true, 
      source: key, 
      fetched: rows.length,
      upserts, 
      errors,
      timestamp: new Date().toISOString()
    })
  } catch (e: any) {
    console.error('Permit scraping error:', e)
    return NextResponse.json({ 
      ok: false, 
      error: String(e),
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}