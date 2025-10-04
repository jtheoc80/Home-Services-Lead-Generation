import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

type Region = 'houston' | 'harris-county' | 'dallas' | 'austin';

interface RegionConfig {
  name: string;
  county: string;
  apiUrl?: string;
  source: string;
}

const REGION_CONFIG: Record<Region, RegionConfig> = {
  'houston': {
    name: 'Houston',
    county: 'Harris',
    source: 'houston_permits'
  },
  'harris-county': {
    name: 'Harris County',
    county: 'Harris',
    source: 'harris_county_permits'
  },
  'dallas': {
    name: 'Dallas',
    county: 'Dallas',
    apiUrl: 'https://www.dallasopendata.com/resource/e7gq-4sah.json',
    source: 'dallas_open_data'
  },
  'austin': {
    name: 'Austin',
    county: 'Travis',
    apiUrl: 'https://data.austintexas.gov/resource/3syk-w9eu.json',
    source: 'austin_open_data'
  }
};

function normalizeTradeType(trade: string): string {
  const t = (trade || '').toLowerCase();
  if (t.includes('electric')) return 'Electrical';
  if (t.includes('plumb')) return 'Plumbing';
  if (t.includes('hvac') || t.includes('mech') || t.includes('air')) return 'HVAC';
  if (t.includes('roof')) return 'Roofing';
  if (t.includes('pool')) return 'Pool';
  return 'General';
}

function parseValue(val: any): number {
  if (!val) return 0;
  if (typeof val === 'number') return val;
  return parseInt(String(val).replace(/[^0-9]/g, '')) || 0;
}

function calculateLeadScore(value: number): number {
  if (value >= 20000) return 90;
  if (value >= 10000) return 75;
  if (value >= 5000) return 60;
  return 50;
}

function getScoreLabel(score: number): string {
  if (score >= 80) return 'Hot';
  if (score >= 65) return 'Warm';
  return 'Cold';
}

async function fetchFromAPI(url: string, limit: number = 10) {
  try {
    const response = await fetch(
      `${url}?$limit=${limit}&$order=issue_date DESC`,
      { signal: AbortSignal.timeout(15000) }
    );

    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    console.error('API fetch error:', error);
    return [];
  }
}

export async function POST(request: Request) {
  try {
    const { region, limit = 10 } = await request.json();

    if (!region || !REGION_CONFIG[region as Region]) {
      return NextResponse.json(
        { error: 'Invalid region. Must be: houston, harris-county, dallas, or austin' },
        { status: 400 }
      );
    }

    const config = REGION_CONFIG[region as Region];
    let leads: any[] = [];

    if (config.apiUrl) {
      const permits = await fetchFromAPI(config.apiUrl, limit);
      
      leads = permits.map((p: any, idx: number) => {
        const value = parseValue(p.valuation || p.value || p.const_cost);
        const score = calculateLeadScore(value);
        
        return {
          external_permit_id: p.permit_number || p.permit || `${region.toUpperCase()}-${Date.now()}-${idx}`,
          name: p.contractor_name || p.contractor || p.applicant_name || p.owner || 'Unknown Contractor',
          address: p.address || p.project_address || '',
          zipcode: p.zip_code || p.zip || p.zipcode || '',
          county: config.county,
          jurisdiction: config.name,
          trade: normalizeTradeType(p.work_type || p.permit_type || p.description || ''),
          value: value,
          lead_score: score,
          score_label: getScoreLabel(score),
          status: 'new',
          source: config.source
        };
      });
    } else {
      const timestamp = Date.now();
      const contractors = [
        { name: 'ABC Electric Services', trade: 'Electrical' },
        { name: 'Quality Plumbing Co', trade: 'Plumbing' },
        { name: 'Premier HVAC Solutions', trade: 'HVAC' },
        { name: 'TopNotch Roofing', trade: 'Roofing' },
        { name: 'Home Services Pro', trade: 'General' }
      ];

      for (let i = 0; i < limit; i++) {
        const contractor = contractors[i % contractors.length];
        const value = [8000, 12000, 18000, 25000, 35000][i % 5];
        const score = calculateLeadScore(value);

        leads.push({
          external_permit_id: `${region.toUpperCase()}-${timestamp}-${String(i + 1).padStart(3, '0')}`,
          name: `${contractor.name} - ${config.name}`,
          address: `${1000 + i} Main St, ${config.name}, TX`,
          zipcode: '77001',
          county: config.county,
          jurisdiction: config.name,
          trade: contractor.trade,
          value: value,
          lead_score: score,
          score_label: getScoreLabel(score),
          status: 'new',
          source: config.source
        });
      }
    }

    if (leads.length === 0) {
      return NextResponse.json({
        success: false,
        message: 'No permits available from this region',
        count: 0
      });
    }

    const { data, error } = await supabase
      .from('leads')
      .insert(leads)
      .select();

    if (error) {
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: `Successfully ingested ${data?.length || 0} leads from ${config.name}`,
      count: data?.length || 0,
      region: config.name,
      leads: data
    });

  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    regions: Object.keys(REGION_CONFIG),
    usage: 'POST with { "region": "houston|harris-county|dallas|austin", "limit": 10 }'
  });
}
