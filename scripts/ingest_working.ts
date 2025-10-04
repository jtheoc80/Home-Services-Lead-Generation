#!/usr/bin/env tsx
/**
 * Working Permit Ingestion Script
 * Uses the insert_lead_simple RPC function to bypass trigger issues
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Sample permit data (representing real permit information)
const samplePermits = [
  {
    permit_id: `PERMIT-${Date.now()}-001`,
    contractor_name: 'ABC Electric Co',
    address: '123 Main St, Houston, TX 77002',
    zipcode: '77002',
    county: 'Harris',
    trade: 'Electrical',
    value: 15000
  },
  {
    permit_id: `PERMIT-${Date.now()}-002`,
    contractor_name: 'Quality Plumbing Services',
    address: '456 Oak Ave, Houston, TX 77004',
    zipcode: '77004',
    county: 'Harris',
    trade: 'Plumbing',
    value: 8500
  },
  {
    permit_id: `PERMIT-${Date.now()}-003`,
    contractor_name: 'Cool Air HVAC',
    address: '789 Pine St, Houston, TX 77019',
    zipcode: '77019',
    county: 'Harris',
    trade: 'HVAC',
    value: 12000
  },
  {
    permit_id: `PERMIT-${Date.now()}-004`,
    contractor_name: 'Top Notch Roofing',
    address: '321 Elm Dr, Houston, TX 77025',
    zipcode: '77025',
    county: 'Harris',
    trade: 'Roofing',
    value: 25000
  },
  {
    permit_id: `PERMIT-${Date.now()}-005`,
    contractor_name: 'Home Improvement Pro',
    address: '654 Maple Ln, Houston, TX 77077',
    zipcode: '77077',
    county: 'Harris',
    trade: 'General',
    value: 45000
  }
];

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
  console.log('🚀 Permit Ingestion Using RPC Function\n');
  console.log('━'.repeat(60) + '\n');

  const results = [];
  const errors = [];

  for (const permit of samplePermits) {
    const leadScore = calculateLeadScore(permit.value);
    const scoreLabel = getScoreLabel(leadScore);

    try {
      const { data, error } = await supabase.rpc('insert_lead_simple', {
        p_external_permit_id: permit.permit_id,
        p_name: permit.contractor_name,
        p_address: permit.address,
        p_zipcode: permit.zipcode,
        p_county: permit.county,
        p_trade: permit.trade,
        p_value: permit.value,
        p_lead_score: leadScore,
        p_score_label: scoreLabel,
        p_source: 'ingestion_script'
      });

      if (error) {
        console.error(`  ❌ ${permit.permit_id}: ${error.message}`);
        errors.push({ permit_id: permit.permit_id, error: error.message });
      } else {
        console.log(`  ✅ ${permit.contractor_name} - ${permit.trade} ($${permit.value.toLocaleString()})`);
        results.push(data);
      }
    } catch (err: any) {
      console.error(`  ❌ ${permit.permit_id}: ${err.message}`);
      errors.push({ permit_id: permit.permit_id, error: err.message });
    }
  }

  console.log('\n' + '━'.repeat(60) + '\n');

  if (results.length > 0) {
    console.log(`✅ Successfully created ${results.length} leads!`);
  }

  if (errors.length > 0) {
    console.log(`\n⚠️  ${errors.length} errors encountered:`);
    console.log('\n💡 If you see "function public.insert_lead_simple does not exist"');
    console.log('   Run the SQL script: fix_database_triggers.sql in your Supabase SQL Editor');
  } else {
    console.log('\n🎉 All permits successfully converted to leads!');
    console.log('📱 Check your frontend at http://localhost:5000 to see the leads');
  }
}

main().catch(console.error);
