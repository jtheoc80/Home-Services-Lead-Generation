import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'          // important when using service role
export const dynamic = 'force-dynamic'
export const revalidate = 0

// Create the Supabase admin client inside the request handler to avoid build-time errors
function createSupabaseAdmin() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  
  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error('Missing required Supabase environment variables');
  }
  
  return createClient(supabaseUrl, serviceRoleKey);
}

// map the external key to the internal "source" string you store
const SOURCE_KEY: Record<string, string> = {
  austin: 'austin_socrata',
  dallas: 'dallas_socrata',
}

// Types for normalized permit data
interface Normalized {
  source: string;
  source_record_id: string;
  permit_number?: string;
  issued_date?: string;
  application_date?: string;
  permit_type?: string;
  permit_class?: string;
  work_description?: string;
  address?: string;
  city?: string;
  county?: string;
  zipcode?: string;
  latitude?: number;
  longitude?: number;
  valuation?: number;
  square_feet?: number;
  applicant_name?: string;
  contractor_name?: string;
  owner_name?: string;
  status?: string;
}

// Types for raw permit data sources
interface AustinPermitRecord {
  permit_num?: string;
  issued_date?: string;
  description?: string;
  project_address?: string;
  applicant_name?: string;
  contractor_name?: string;
  declared_value?: string;
  status_current?: string;
  permit_type?: string;
  [key: string]: unknown;
}

interface DallasPermitRecord {
  permit_number?: string;
  permit_no?: string;
  record_id?: string;
  issue_date?: string;
  issued_date?: string;
  issuance_date?: string;
  work_description?: string;
  description?: string;
  project_description?: string;
  project_address?: string;
  address?: string;
  full_address?: string;
  applicant_name?: string;
  applicant?: string;
  contractor_name?: string;
  contractor?: string;
  estimated_cost?: string | number;
  valuation?: string | number;
  project_value?: string | number;
  status?: string;
  permit_status?: string;
  current_status?: string;
  permit_type?: string;
  type?: string;
  [key: string]: unknown;
}

// Fetcher functions for each data source
async function fetchAustin(): Promise<Normalized[]> {
  // Austin Socrata API endpoint  
  const url = 'https://data.austintexas.gov/resource/3syk-w9eu.json?$limit=100';
  
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'LeadLedgerPro/1.0',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Austin API error: ${response.status} ${response.statusText}`);
    }
    
    const rawData = await response.json() as AustinPermitRecord[];
    
    // Normalize the data
    return rawData.map(record => ({
      source: 'austin_socrata',
      source_record_id: record.permit_num || `austin_${Date.now()}_${Math.random()}`,
      permit_number: record.permit_num,
      issued_date: record.issued_date,
      permit_type: record.permit_type,
      work_description: record.description,
      address: record.project_address,
      city: 'Austin',
      county: 'Travis',
      applicant_name: record.applicant_name,
      contractor_name: record.contractor_name,
      valuation: record.declared_value ? parseFloat(record.declared_value.toString()) : undefined,
      status: record.status_current,
    }));
  } catch (error) {
    console.error('Error fetching Austin permits:', error);
    return [];
  }
}

async function fetchDallas(): Promise<Normalized[]> {
  // Dallas OpenData API (Socrata) - Dataset ID: e7gq-4sah
  const baseUrl = 'https://www.dallasopendata.com/resource/e7gq-4sah.json';
  const url = `${baseUrl}?$limit=1000`; // Fetch up to 1000 records
  
  try {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'User-Agent': 'LeadLedgerPro/1.0',
    };
    
    // Add app token if available for higher rate limits
    const dallasAppToken = process.env.DALLAS_APP_TOKEN;
    if (dallasAppToken) {
      headers['X-App-Token'] = dallasAppToken;
    }
    
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error(`Dallas API error: ${response.status} ${response.statusText}`);
    }
    
    const rawData = await response.json() as DallasPermitRecord[];
    console.log(`Dallas permits fetched: ${rawData.length} records`);
    
    // Normalize the data
    return rawData.map(record => {
      // Helper function to get the first available field value
      const getField = (...fieldNames: (keyof DallasPermitRecord)[]): string | number | undefined => {
        for (const fieldName of fieldNames) {
          const value = record[fieldName];
          if (value !== undefined && value !== null && value !== '') {
            return value as string | number;
          }
        }
        return undefined;
      };

      // Helper function to parse numeric values safely
      const parseNumeric = (value: string | number | undefined): number | undefined => {
        if (value === undefined || value === null) return undefined;
        const numValue = typeof value === 'number' ? value : parseFloat(value.toString());
        return isNaN(numValue) ? undefined : numValue;
      };

      // Get permit identifier (try multiple field names)
      const permitId = getField('permit_number', 'permit_no', 'record_id') as string | undefined;
      
      return {
        source: 'dallas_socrata',
        source_record_id: permitId || `dallas_${Date.now()}_${Math.random()}`,
        permit_number: permitId,
        issued_date: getField('issued_date', 'issue_date', 'issuance_date') as string | undefined,
        permit_type: getField('permit_type', 'type') as string | undefined,
        work_description: getField('work_description', 'description', 'project_description') as string | undefined,
        address: getField('project_address', 'address', 'full_address') as string | undefined,
        city: 'Dallas',
        county: 'Dallas',
        applicant_name: getField('applicant_name', 'applicant') as string | undefined,
        contractor_name: getField('contractor_name', 'contractor') as string | undefined,
        valuation: parseNumeric(getField('estimated_cost', 'valuation', 'project_value')),
        status: getField('status', 'permit_status', 'current_status') as string | undefined,
      };
    });
  } catch (error) {
    console.error('Error fetching Dallas permits:', error);
    return [];
  }
}

const FETCHERS = { austin: fetchAustin, dallas: fetchDallas }

export async function POST(req: Request) {
  const url = new URL(req.url)
  const key = url.searchParams.get('source') || 'austin'
  const dry = url.searchParams.get('dry') === '1'
  const fetcher = FETCHERS[key as keyof typeof FETCHERS]

  if (!fetcher) {
    return NextResponse.json({ ok: false, error: `Unknown source: ${key}` }, { status: 400 })
  }

  try {
    // Create Supabase admin client
    const supabaseAdmin = createSupabaseAdmin()
    
    // 1) fetch from city source
    const rows = await fetcher()
    const source = SOURCE_KEY[key] || key
    const sample = rows.slice(0, 3)

    // 2) count before
    const { count: beforeCount, error: countBeforeErr } = await supabaseAdmin
      .from('permits')
      .select('*', { count: 'exact', head: true })
      .eq('source', source)
    if (countBeforeErr) throw countBeforeErr

    let upserts = 0
    const errors: string[] = []

    // 3) optional write
    if (!dry) {
      for (const row of rows) {
        // Use 'p' parameter as specified in the problem statement
        const { error } = await supabaseAdmin.rpc('upsert_permit', { p: row as any })
        if (error) errors.push(error.message)
        else upserts++
      }
    }

    // 4) count after
    const { count: afterCount, error: countAfterErr } = await supabaseAdmin
      .from('permits')
      .select('*', { count: 'exact', head: true })
      .eq('source', source)
    if (countAfterErr) throw countAfterErr

    return NextResponse.json({
      ok: true,
      source,
      fetched: rows.length,
      dry,
      upserts,
      beforeCount,
      afterCount,
      sample,
      errors: errors.slice(0, 5), // first 5 errors if any
    })
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 500 })
  }
}