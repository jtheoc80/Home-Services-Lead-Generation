#!/usr/bin/env tsx
/**
 * Direct Lead Insertion - bypasses RPC function
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Fetch Austin permits
async function fetchAustinPermits(): Promise<any[]> {
  console.log('📡 Fetching permits from Austin Open Data...');
  
  try {
    const response = await fetch(
      'https://data.austintexas.gov/resource/3syk-w9eu.json?$limit=10&$order=issue_date DESC',
      { timeout: 15000 } as any
    );

    if (!response.ok) {
      console.log(`   ⚠️  Austin API returned ${response.status}`);
      return [];
    }

    const data = await response.json();
    console.log(`   ✅ Fetched ${data.length} Austin permits\n`);
    
    return data.map((p: any) => ({
      external_permit_id: p.permit_number || `AUS-${Date.now()}-${Math.random()}`,
      name: p.contractor_name || p.applicant_name || 'Unknown Contractor',
      address: p.address || p.project_address,
      zipcode: p.zip_code || p.zipcode,
      county: 'Travis',
      trade: normalizeTradeType(p.work_type || p.description),
      value: parseValue(p.const_cost || p.valuation),
      lead_score: 0,
      score_label: 'Cold',
      status: 'new',
      source: 'austin_open_data'
    }));
  } catch (error: any) {
    console.log(`   ❌ Austin API error: ${error.message}\n`);
    return [];
  }
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

async function main() {
  console.log('🚀 Direct Lead Insertion\n');
  console.log('━'.repeat(60) + '\n');

  const permits = await fetchAustinPermits();

  if (permits.length === 0) {
    console.log('❌ No permits fetched');
    return;
  }

  console.log(`📥 Inserting ${permits.length} leads directly...\n`);

  const leadsToInsert = permits.map(p => {
    const score = calculateLeadScore(p.value);
    return {
      ...p,
      lead_score: score,
      score_label: getScoreLabel(score)
    };
  });

  const { data, error } = await supabase
    .from('leads')
    .insert(leadsToInsert)
    .select();

  if (error) {
    console.error('❌ Insert error:', error.message);
    console.log('\n💡 Error details:', error);
  } else {
    console.log(`✅ Successfully inserted ${data?.length || 0} leads!\n`);
    
    if (data && data.length > 0) {
      data.forEach((lead: any) => {
        console.log(`  • ${lead.name} - ${lead.county} - ${lead.trade} - ${lead.score_label}`);
      });
    }
  }

  console.log('\n' + '━'.repeat(60));
  console.log('\n🎉 Ingestion complete!');
  console.log('📱 Check http://localhost:5000 to see your leads');
}

main().catch(console.error);
