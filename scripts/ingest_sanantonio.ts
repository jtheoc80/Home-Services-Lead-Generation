#!/usr/bin/env tsx
/**
 * San Antonio Permit Ingestion
 * Fetches permits from San Antonio Open Data API (CKAN) and creates leads
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface SanAntonioPermit {
  PERMIT_NUMBER?: string;
  PERMIT_NO?: string;
  CONTRACTOR_NAME?: string;
  CONTRACTOR?: string;
  OWNER_NAME?: string;
  OWNER?: string;
  ADDRESS?: string;
  WORK_ADDRESS?: string;
  ZIP?: string;
  ZIP_CODE?: string;
  WORK_TYPE?: string;
  PERMIT_TYPE?: string;
  DESCRIPTION?: string;
  VALUATION?: string | number;
  VALUE?: string | number;
  ISSUE_DATE?: string;
  ISSUED_DATE?: string;
}

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

async function fetchSanAntonioPermits(limit: number = 10): Promise<SanAntonioPermit[]> {
  try {
    // CKAN API endpoint - using the resource ID from the search results
    const resourceId = 'c21106f9-3ef5-4f3a-8604-f992b4db7512';
    const response = await fetch(
      `https://data.sanantonio.gov/api/3/action/datastore_search?resource_id=${resourceId}&limit=${limit}&sort=ISSUE_DATE desc`,
      { signal: AbortSignal.timeout(15000) }
    );

    if (!response.ok) {
      console.log(`San Antonio API returned ${response.status}`);
      return [];
    }

    const json = await response.json();
    
    // CKAN wraps results in a specific structure
    if (json.success && json.result && json.result.records) {
      return json.result.records;
    }

    return [];
  } catch (error: any) {
    console.error('San Antonio API error:', error.message);
    return [];
  }
}

export async function ingestSanAntonioLeads(limit: number = 10) {
  console.log(`📡 Fetching ${limit} San Antonio permits...`);
  
  const permits = await fetchSanAntonioPermits(limit);
  
  if (permits.length === 0) {
    console.log('⚠️  No San Antonio permits fetched');
    return { success: false, count: 0, errors: ['No permits from San Antonio API'] };
  }

  console.log(`✅ Fetched ${permits.length} San Antonio permits`);

  const leads = permits.map((p, idx) => {
    const value = parseValue(p.VALUATION || p.VALUE);
    const score = calculateLeadScore(value);
    
    return {
      external_permit_id: p.PERMIT_NUMBER || p.PERMIT_NO || `SAT-${Date.now()}-${String(idx).padStart(3, '0')}`,
      name: p.CONTRACTOR_NAME || p.CONTRACTOR || p.OWNER_NAME || p.OWNER || 'Unknown Contractor',
      address: p.WORK_ADDRESS || p.ADDRESS || '',
      zipcode: p.ZIP_CODE || p.ZIP || '',
      county: 'Bexar',
      trade: normalizeTradeType(p.WORK_TYPE || p.PERMIT_TYPE || p.DESCRIPTION || ''),
      value: value,
      lead_score: score,
      score_label: getScoreLabel(score),
      status: 'new',
      source: 'sanantonio_open_data'
    };
  });

  const { data, error } = await supabase
    .from('leads')
    .insert(leads)
    .select();

  if (error) {
    console.error('❌ Insert error:', error.message);
    return { success: false, count: 0, errors: [error.message] };
  }

  console.log(`✅ Inserted ${data?.length || 0} San Antonio leads`);
  return { success: true, count: data?.length || 0, leads: data };
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  ingestSanAntonioLeads(10)
    .then(result => {
      console.log('\n🎉 San Antonio ingestion complete!');
      console.log(`📊 ${result.count} leads created`);
      process.exit(0);
    })
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}
