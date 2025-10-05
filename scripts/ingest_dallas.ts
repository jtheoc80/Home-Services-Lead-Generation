#!/usr/bin/env tsx
/**
 * Dallas Permit Ingestion
 * Fetches permits from Dallas Open Data API and creates leads
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface DallasPermit {
  permit?: string;
  permit_number?: string;
  contractor?: string;
  owner?: string;
  applicant?: string;
  address?: string;
  street_address?: string;
  project_address?: string;
  zip?: string;
  zip_code?: string;
  work_type?: string;
  work_description?: string;
  permit_type?: string;
  valuation?: string | number;
  value?: string | number;
  issue_date?: string;
  issued_date?: string;
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

async function fetchDallasPermits(limit: number = 10): Promise<DallasPermit[]> {
  try {
    const response = await fetch(
      `https://www.dallasopendata.com/resource/e7gq-4sah.json?$limit=${limit}&$order=issued_date DESC`,
      { signal: AbortSignal.timeout(15000) }
    );

    if (!response.ok) {
      console.log(`Dallas API returned ${response.status}`);
      return [];
    }

    return await response.json();
  } catch (error: any) {
    console.error('Dallas API error:', error.message);
    return [];
  }
}

export async function ingestDallasLeads(limit: number = 10) {
  console.log(`📡 Fetching ${limit} Dallas permits...`);
  
  const permits = await fetchDallasPermits(limit);
  
  if (permits.length === 0) {
    console.log('⚠️  No Dallas permits fetched');
    return { success: false, count: 0, errors: ['No permits from Dallas API'] };
  }

  console.log(`✅ Fetched ${permits.length} Dallas permits\n`);

  const leads = permits.map((p, idx) => {
    const value = parseValue(p.valuation || p.value);
    const score = calculateLeadScore(value);
    
    const contractorName = p.contractor || null;
    const ownerName = p.owner || p.applicant || null;
    
    let leadType = 'unknown';
    let primaryName = 'Unknown';
    
    if (ownerName && contractorName) {
      leadType = 'owner';
      primaryName = ownerName;
    } else if (ownerName) {
      leadType = 'owner';
      primaryName = ownerName;
    } else if (contractorName) {
      leadType = 'contractor';
      primaryName = contractorName;
    }
    
    return {
      external_permit_id: p.permit_number || p.permit || `DAL-${Date.now()}-${String(idx).padStart(3, '0')}`,
      name: primaryName,
      contractor_name: contractorName,
      owner_name: ownerName,
      lead_type: leadType,
      address: p.street_address || p.address || p.project_address || '',
      zipcode: p.zip_code || p.zip || '',
      county: 'Dallas',
      trade: normalizeTradeType(p.work_description || p.work_type || p.permit_type || ''),
      value: value,
      lead_score: score,
      score_label: getScoreLabel(score),
      status: 'new',
      source: 'dallas_open_data'
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

  console.log(`✅ Inserted ${data?.length || 0} Dallas leads`);
  return { success: true, count: data?.length || 0, leads: data };
}

// Run if executed directly
ingestDallasLeads(10)
  .then(result => {
    console.log('\n🎉 Dallas ingestion complete!');
    console.log(`📊 ${result.count} leads created`);
    process.exit(0);
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
