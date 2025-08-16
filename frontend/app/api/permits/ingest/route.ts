// Force dynamic rendering and Node runtime for permit ingestion API
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseClient } from '@/lib/supabaseServer';

// Types for permit data sources
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
  // Possible field variations from Dallas Socrata API
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
    source: 'dallas',
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
}

// Fetcher functions for each data source
async function fetchAustinPermits(): Promise<AustinPermitRecord[]> {
  // TODO: Replace with actual Austin Socrata API endpoint
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
  // Dallas OpenData API (Socrata) - Dataset ID: e7gq-4sah
  const baseUrl = 'https://www.dallasopendata.com/resource/e7gq-4sah.json';
  const limit = 1000; // Fetch up to 1000 records per request
  const url = `${baseUrl}?$limit=${limit}`;
  
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
    
    const data = await response.json() as DallasPermitRecord[];
    console.log(`Dallas permits fetched: ${data.length} records from ${url}`);
    return data;
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
    
    // Support both query parameters and JSON body for source
    const { searchParams } = new URL(request.url);
    let source = searchParams.get('source');
    
    // If no query parameter, try to get from JSON body (backward compatibility)
    if (!source) {
      try {
        const body = await request.json();
        source = body.source;
      } catch (error) {
        // If no JSON body and no query param, return error
        if (!source) {
          return NextResponse.json(
            { error: 'Source parameter required either as query parameter (?source=austin) or in JSON body' },
            { status: 400 }
          );
        }
      }
    }
    
    // Validate cron secret if provided
    const cronSecret = request.headers.get('x-cron-secret');
    const expectedCronSecret = process.env.CRON_SECRET;
    
    if (cronSecret) {
      if (!expectedCronSecret) {
        return NextResponse.json(
          { error: 'Server misconfiguration: CRON_SECRET environment variable not set' },
          { status: 500 }
        );
      }
      if (cronSecret !== expectedCronSecret) {
        return NextResponse.json(
          { error: 'Invalid cron secret' },
          { status: 401 }
        );
      }
    }
    
    let permits: NormalizedPermit[] = [];
    let sourceData: unknown[] = [];
    
    // Fetch data based on source
    switch (source) {
      case 'austin':
        sourceData = await fetchAustinPermits();
        permits = sourceData.map(record => mapAustinPermit(record as AustinPermitRecord));
        break;
        
      case 'houston':
        sourceData = await fetchHoustonPermits();
        permits = sourceData.map(record => mapHoustonPermit(record as HoustonPermitRecord));
        break;
        
      case 'dallas':
        sourceData = await fetchDallasPermits();
        permits = sourceData.map(record => mapDallasPermit(record as DallasPermitRecord));
        break;
        
      case 'all':
        // Fetch from all sources
        const [austinData, houstonData, dallasData] = await Promise.all([
          fetchAustinPermits(),
          fetchHoustonPermits(),
          fetchDallasPermits()
        ]);
        
        permits = [
          ...austinData.map(record => mapAustinPermit(record as AustinPermitRecord)),
          ...houstonData.map(record => mapHoustonPermit(record as HoustonPermitRecord)),
          ...dallasData.map(record => mapDallasPermit(record as DallasPermitRecord))
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
    const processedSamples: unknown[] = [];
    const upsertResults: unknown[] = [];
    
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
          const resultId = data[0].id;
          
          upsertResults.push({
            source_record_id: permit.source_record_id,
            action,
            id: resultId
          });
          
          if (action === 'inserted') {
            insertedCount++;
          } else if (action === 'updated') {
            updatedCount++;
          }
          
          // Keep samples for diagnostic purposes (first 3 of each type)
          if (processedSamples.length < 3) {
            processedSamples.push({
              original_data: sourceData[permits.indexOf(permit)],
              normalized_permit: permit,
              upsert_result: { action, id: resultId }
            });
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
      summary: {
        fetched: sourceData.length,
        processed: permits.length,
        inserted: insertedCount,
        updated: updatedCount,
        errors: errors.length
      },
      diagnostics: {
        samples: processedSamples,
        upsert_results: upsertResults.slice(0, 10), // Limit to first 10 for readability
        error_details: errors.length > 0 ? errors : undefined,
        runtime_info: {
          runtime: 'nodejs',
          service_role_used: true,
          timestamp: new Date().toISOString()
        }
      },
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
    },
    features: [
      'Service role authentication',
      'Normalized upserts via upsert_permit RPC',
      'Detailed diagnostics with samples',
      'Before/after processing counts',
      'Error tracking and reporting'
    ],
    runtime: 'nodejs',
    caching: 'force-dynamic'
  });
}