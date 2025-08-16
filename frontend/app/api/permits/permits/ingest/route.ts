import { NextResponse } from 'next/server'
import { createServiceClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'          // important when using service role
export const dynamic = 'force-dynamic'
export const revalidate = 0

// map the external key to the internal "source" string you store
const SOURCE_KEY: Record<string, string> = {
  austin: 'austin_socrata',
  dallas: 'dallas_socrata',
  houston: 'houston_csv',
  san_antonio: 'san_antonio_socrata',
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

interface HoustonPermitRecord {
  permit_number?: string;
  permit_no?: string;
  issue_date?: string;
  issued_date?: string;
  description?: string;
  work_description?: string;
  address?: string;
  project_address?: string;
  applicant_name?: string;
  contractor_name?: string;
  valuation?: string | number;
  estimated_cost?: string | number;
  status?: string;
  permit_type?: string;
  type?: string;
  [key: string]: unknown;
}

interface SanAntonioPermitRecord {
  permit_number?: string;
  permit_no?: string;
  issue_date?: string;
  issued_date?: string;
  description?: string;
  work_description?: string;
  address?: string;
  project_address?: string;
  applicant_name?: string;
  contractor_name?: string;
  valuation?: string | number;
  estimated_cost?: string | number;
  status?: string;
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

async function fetchHouston(): Promise<Normalized[]> {
  // Houston CSV endpoint
  const url = 'https://www.houstontx.gov/planning/DevelopReview/permits_issued.csv';
  
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'text/csv',
        'User-Agent': 'LeadLedgerPro/1.0',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Houston API error: ${response.status} ${response.statusText}`);
    }
    
    const csvText = await response.text();
    
    // Parse CSV data (basic CSV parsing)
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    
    const rawData: HoustonPermitRecord[] = [];
    for (let i = 1; i < lines.length && i < 101; i++) { // Limit to 100 records
      if (lines[i].trim()) {
        const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
        const record: HoustonPermitRecord = {};
        headers.forEach((header, index) => {
          record[header as keyof HoustonPermitRecord] = values[index] || undefined;
        });
        rawData.push(record);
      }
    }
    
    console.log(`Houston permits fetched: ${rawData.length} records`);
    
    // Normalize the data
    return rawData.map(record => {
      // Helper function to get the first available field value
      const getField = (...fieldNames: (keyof HoustonPermitRecord)[]): string | number | undefined => {
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

      // Get permit identifier
      const permitId = getField('permit_number', 'permit_no') as string | undefined;
      
      return {
        source: 'houston_csv',
        source_record_id: permitId || `houston_${Date.now()}_${Math.random()}`,
        permit_number: permitId,
        issued_date: getField('issued_date', 'issue_date') as string | undefined,
        permit_type: getField('permit_type', 'type') as string | undefined,
        work_description: getField('work_description', 'description') as string | undefined,
        address: getField('project_address', 'address') as string | undefined,
        city: 'Houston',
        county: 'Harris',
        applicant_name: getField('applicant_name') as string | undefined,
        contractor_name: getField('contractor_name') as string | undefined,
        valuation: parseNumeric(getField('estimated_cost', 'valuation')),
        status: getField('status') as string | undefined,
      };
    });
  } catch (error) {
    console.error('Error fetching Houston permits:', error);
    return [];
  }
}

async function fetchSanAntonio(): Promise<Normalized[]> {
  // San Antonio Socrata API endpoint
  const baseUrl = 'https://data.sanantonio.gov/resource/city-permits.json';
  const url = `${baseUrl}?$limit=100`;
  
  try {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'User-Agent': 'LeadLedgerPro/1.0',
    };
    
    // Add app token if available for higher rate limits
    const sanAntonioAppToken = process.env.SAN_ANTONIO_APP_TOKEN;
    if (sanAntonioAppToken) {
      headers['X-App-Token'] = sanAntonioAppToken;
    }
    
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error(`San Antonio API error: ${response.status} ${response.statusText}`);
    }
    
    const rawData = await response.json() as SanAntonioPermitRecord[];
    console.log(`San Antonio permits fetched: ${rawData.length} records`);
    
    // Normalize the data
    return rawData.map(record => {
      // Helper function to get the first available field value
      const getField = (...fieldNames: (keyof SanAntonioPermitRecord)[]): string | number | undefined => {
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

      // Get permit identifier
      const permitId = getField('permit_number', 'permit_no') as string | undefined;
      
      return {
        source: 'san_antonio_socrata',
        source_record_id: permitId || `san_antonio_${Date.now()}_${Math.random()}`,
        permit_number: permitId,
        issued_date: getField('issued_date', 'issue_date') as string | undefined,
        permit_type: getField('permit_type', 'type') as string | undefined,
        work_description: getField('work_description', 'description') as string | undefined,
        address: getField('project_address', 'address') as string | undefined,
        city: 'San Antonio',
        county: 'Bexar',
        applicant_name: getField('applicant_name') as string | undefined,
        contractor_name: getField('contractor_name') as string | undefined,
        valuation: parseNumeric(getField('estimated_cost', 'valuation')),
        status: getField('status') as string | undefined,
      };
    });
  } catch (error) {
    console.error('Error fetching San Antonio permits:', error);
    return [];
  }
}

const FETCHERS = { 
  austin: fetchAustin, 
  dallas: fetchDallas, 
  houston: fetchHouston, 
  san_antonio: fetchSanAntonio 
}

export async function POST(req: Request) {
  // Check for x-cron-secret header first
  const secret = req.headers.get('x-cron-secret')
  if (secret !== process.env.CRON_SECRET) {
    return new Response('Forbidden', { status: 403 })
  }

  const url = new URL(req.url)
  const key = url.searchParams.get('source') || 'austin'
  const dry = url.searchParams.get('dry') === '1'
  const fetcher = FETCHERS[key as keyof typeof FETCHERS]

  if (!fetcher) {
    return NextResponse.json({ ok: false, error: `Unknown source: ${key}` }, { status: 400 })
  }

  try {
    // Create Supabase service role client
    const supabaseAdmin = createServiceClient()
    
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