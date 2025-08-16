// Force dynamic rendering - no caching for permit ingestion API
export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseClient } from '@/lib/supabaseServer';

// Types for permit data sources
interface AustinPermitRecord {
  permit_num?: string;
  permit_number?: string;
  issued_date?: string;
  issue_date?: string;
  description?: string;
  project_address?: string;
  original_address1?: string;
  applicant_name?: string;
  contractor_name?: string;
  declared_value?: string;
  total_valuation?: string;
  status_current?: string;
  permit_type?: string;
  [key: string]: unknown;
}

interface HoustonPermitRecord {
  OBJECTID?: string | number;
  PERMIT_NUM?: string;
  ISSUE_DATE?: string;
  DESCRIPTION?: string;
  ADDRESS?: string;
  APPLICANT?: string;
  CONTRACTOR?: string;
  VALUATION?: string | number;
  STATUS?: string;
  PERMIT_TYPE?: string;
  X?: number;
  Y?: number;
  [key: string]: unknown;
}

interface DallasPermitRecord {
  permit_number?: string;
  issue_date?: string;
  work_description?: string;
  project_address?: string;
  applicant_name?: string;
  contractor_name?: string;
  estimated_cost?: string;
  status?: string;
  permit_type?: string;
  [key: string]: unknown;
}

interface NormalizedPermit {
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

// Field mapping functions for each source
function mapAustinPermit(record: AustinPermitRecord): NormalizedPermit {
  return {
    source: 'austin',
    source_record_id: record.permit_num || record.permit_number || `austin_${Date.now()}_${Math.random()}`,
    permit_number: record.permit_num || record.permit_number,
    issued_date: record.issued_date || record.issue_date,
    permit_type: record.permit_type,
    work_description: record.description,
    address: record.original_address1 || record.project_address,
    city: 'Austin',
    county: 'Travis',
    applicant_name: record.applicant_name,
    contractor_name: record.contractor_name,
    valuation: record.total_valuation ? parseFloat(record.total_valuation.toString()) : 
               record.declared_value ? parseFloat(record.declared_value.toString()) : undefined,
    status: record.status_current,
  };
}

function mapHoustonPermit(record: HoustonPermitRecord): NormalizedPermit {
  return {
    source: 'houston',
    source_record_id: record.OBJECTID?.toString() || record.PERMIT_NUM || `houston_${Date.now()}_${Math.random()}`,
    permit_number: record.PERMIT_NUM,
    issued_date: record.ISSUE_DATE,
    permit_type: record.PERMIT_TYPE,
    work_description: record.DESCRIPTION,
    address: record.ADDRESS,
    city: 'Houston',
    county: 'Harris',
    applicant_name: record.APPLICANT,
    contractor_name: record.CONTRACTOR,
    valuation: typeof record.VALUATION === 'number' ? record.VALUATION : 
               typeof record.VALUATION === 'string' ? parseFloat(record.VALUATION) : undefined,
    latitude: record.Y,
    longitude: record.X,
    status: record.STATUS,
  };
}

function mapDallasPermit(record: DallasPermitRecord): NormalizedPermit {
  return {
    source: 'dallas',
    source_record_id: record.permit_number || `dallas_${Date.now()}_${Math.random()}`,
    permit_number: record.permit_number,
    issued_date: record.issue_date,
    permit_type: record.permit_type,
    work_description: record.work_description,
    address: record.project_address,
    city: 'Dallas',
    county: 'Dallas',
    applicant_name: record.applicant_name,
    contractor_name: record.contractor_name,
    valuation: record.estimated_cost ? parseFloat(record.estimated_cost.toString()) : undefined,
    status: record.status,
  };
}

// Fetcher functions for each data source
async function fetchAustinPermits(): Promise<AustinPermitRecord[]> {
  // Austin Socrata API with ordering by issue_date and optional app token
  const params = new URLSearchParams({
    '$limit': '1000',
    '$order': 'issue_date DESC'
  });
  
  const url = `https://data.austintexas.gov/resource/3syk-w9eu.json?${params}`;
  
  const headers: HeadersInit = {
    'Accept': 'application/json',
    'User-Agent': 'LeadLedgerPro/1.0',
  };
  
  // Add Austin app token if available for higher rate limits
  const austinAppToken = process.env.AUSTIN_APP_TOKEN;
  if (austinAppToken) {
    headers['X-App-Token'] = austinAppToken;
  }
  
  try {
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error(`Austin API error: ${response.status} ${response.statusText}`);
    }
    
    return await response.json() as AustinPermitRecord[];
  } catch (error) {
    console.error('Error fetching Austin permits:', error);
    return [];
  }
}

async function fetchHoustonPermits(): Promise<HoustonPermitRecord[]> {
  // TODO: Replace with actual Houston ArcGIS API endpoint
  const url = 'https://services.arcgis.com/sample/permits/query?where=1%3D1&outFields=*&f=json&resultRecordCount=100';
  
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'LeadLedgerPro/1.0',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Houston API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.features?.map((f: { attributes: HoustonPermitRecord }) => f.attributes) || [];
  } catch (error) {
    console.error('Error fetching Houston permits:', error);
    return [];
  }
}

async function fetchDallasPermits(): Promise<DallasPermitRecord[]> {
  // TODO: Replace with actual Dallas CSV endpoint
  const url = 'https://www.dallasopendata.com/api/views/permits/rows.csv?accessType=DOWNLOAD';
  
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'text/csv',
        'User-Agent': 'LeadLedgerPro/1.0',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Dallas API error: ${response.status} ${response.statusText}`);
    }
    
    const csvText = await response.text();
    // TODO: Parse CSV data (would need to add CSV parsing logic or use library)
    console.log('Dallas CSV data length:', csvText.length);
    return []; // Return empty array for now until CSV parsing is implemented
  } catch (error) {
    console.error('Error fetching Dallas permits:', error);
    return [];
  }
}

// Main API route handler
export async function POST(request: NextRequest) {
  try {
    // Get Supabase client with service role key
    const supabase = getSupabaseClient({ useServiceRole: true });
    
    const body = await request.json();
    const { source } = body;
    
    let permits: NormalizedPermit[] = [];
    let sourceData: unknown[] = [];
    
    // Fetch data based on source
    switch (source) {
      case 'austin':
        sourceData = await fetchAustinPermits();
        permits = (sourceData as AustinPermitRecord[]).map(mapAustinPermit);
        break;
        
      case 'houston':
        sourceData = await fetchHoustonPermits();
        permits = (sourceData as HoustonPermitRecord[]).map(mapHoustonPermit);
        break;
        
      case 'dallas':
        sourceData = await fetchDallasPermits();
        permits = (sourceData as DallasPermitRecord[]).map(mapDallasPermit);
        break;
        
      case 'all':
        // Fetch from all sources
        const [austinData, houstonData, dallasData] = await Promise.all([
          fetchAustinPermits(),
          fetchHoustonPermits(),
          fetchDallasPermits()
        ]);
        
        permits = [
          ...(austinData as AustinPermitRecord[]).map(mapAustinPermit),
          ...(houstonData as HoustonPermitRecord[]).map(mapHoustonPermit),
          ...(dallasData as DallasPermitRecord[]).map(mapDallasPermit)
        ];
        break;
        
      default:
        return NextResponse.json(
          { error: 'Invalid source. Must be one of: austin, houston, dallas, all' },
          { status: 400 }
        );
    }
    
    // Process permits through upsert function
    let insertedCount = 0;
    let updatedCount = 0;
    const errors: string[] = [];
    
    for (const permit of permits) {
      try {
        const { data, error } = await supabase.rpc('upsert_permit', {
          permit_data: permit
        });
        
        if (error) {
          errors.push(`Error upserting permit ${permit.source_record_id}: ${error.message}`);
          continue;
        }
        
        if (data && data.length > 0) {
          const action = data[0].action;
          if (action === 'inserted') {
            insertedCount++;
          } else if (action === 'updated') {
            updatedCount++;
          }
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        errors.push(`Error processing permit ${permit.source_record_id}: ${errorMessage}`);
      }
    }
    
    return NextResponse.json({
      success: true,
      source,
      fetched: sourceData.length,
      processed: permits.length,
      inserted: insertedCount,
      updated: updatedCount,
      errors: errors.length > 0 ? errors : undefined,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Permit ingestion error:', error);
    
    return NextResponse.json(
      { 
        error: 'Internal server error during permit ingestion',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// GET endpoint for testing/health check
export async function GET() {
  return NextResponse.json({
    message: 'TX Permit Ingestion API',
    version: '1.0.0',
    sources: ['austin', 'houston', 'dallas'],
    endpoints: {
      POST: 'Ingest permits from specified source',
      GET: 'Health check and API info'
    },
    usage: {
      POST: {
        body: {
          source: 'austin | houston | dallas | all'
        }
      }
    }
  });
}