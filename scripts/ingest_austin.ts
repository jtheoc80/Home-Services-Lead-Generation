#!/usr/bin/env tsx
/**
 * Austin Permit Ingestion
 * Fetches permits from Austin Open Data API and creates leads
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface AustinPermit {
  permit_number?: string;
  contractor_name?: string;
  applicant_name?: string;
  owner_name?: string;
  address?: string;
  project_address?: string;
  zip_code?: string;
  zipcode?: string;
  work_type?: string;
  description?: string;
  const_cost?: string | number;
  valuation?: string | number;
  issue_date?: string;
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

async function fetchAustinPermits(limit: number = 10): Promise<AustinPermit[]> {
  try {
    const response = await fetch(
      `https://data.austintexas.gov/resource/3syk-w9eu.json?$limit=${limit}&$order=issue_date DESC`,
      { signal: AbortSignal.timeout(15000) }
    );

    if (!response.ok) {
      console.log(`Austin API returned ${response.status}`);
      return [];
    }

    return await response.json();
  } catch (error: any) {
    console.error('Austin API error:', error.message);
    return [];
  }
}

export async function ingestAustinLeads(limit: number = 10) {
  console.log(`📡 Fetching ${limit} Austin permits...`);
  
  const permits = await fetchAustinPermits(limit);
  
  if (permits.length === 0) {
    console.log('⚠️  No Austin permits fetched');
    return { success: false, count: 0, errors: ['No permits from Austin API'] };
  }

  console.log(`✅ Fetched ${permits.length} Austin permits\n`);

  const leads = permits.map((p, idx) => {
    const value = parseValue(p.const_cost || p.valuation);
    const score = calculateLeadScore(value);
    
    return {
      external_permit_id: p.permit_number || `AUS-${Date.now()}-${idx}`,
      name: p.contractor_name || p.applicant_name || p.owner_name || 'Unknown Contractor',
      address: p.address || p.project_address || '',
      zipcode: p.zip_code || p.zipcode || '',
      county: 'Travis',
      trade: normalizeTradeType(p.work_type || p.description || ''),
      value: value,
      lead_score: score,
      score_label: getScoreLabel(score),
      status: 'new',
      source: 'austin_open_data'
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

  console.log(`✅ Inserted ${data?.length || 0} Austin leads`);
  return { success: true, count: data?.length || 0, leads: data };
}

if (require.main === module) {
  ingestAustinLeads(10)
    .then(result => {
      console.log('\n🎉 Austin ingestion complete!');
      console.log(`📊 ${result.count} leads created`);
    })
    .catch(console.error);
}
