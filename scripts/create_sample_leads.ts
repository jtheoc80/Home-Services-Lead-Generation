#!/usr/bin/env tsx
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function createSampleLeads() {
  console.log('🚀 Creating sample leads in Supabase...\n');

  const sampleLeads = [
    {
      permit_id: `DEMO-${Date.now()}-001`,
      service: 'Electrical',
      address: '123 Main St, Houston, TX 77002',
      city: 'Houston',
      state: 'TX',
      zip: '77002',
      county: 'Harris',
      name: 'ABC Electric Co',
      phone: '281-555-0100',
      value: 15000,
      source: 'demo_data',
      lead_score: 85,
      score_label: 'high',
      status: 'new'
    },
    {
      permit_id: `DEMO-${Date.now()}-002`,
      service: 'Plumbing',
      address: '456 Oak Ave, Houston, TX 77004',
      city: 'Houston',
      state: 'TX',
      zip: '77004',
      county: 'Harris',
      name: 'Quality Plumbing Services',
      phone: '713-555-0200',
      value: 8500,
      source: 'demo_data',
      lead_score: 72,
      score_label: 'medium',
      status: 'new'
    },
    {
      permit_id: `DEMO-${Date.now()}-003`,
      service: 'HVAC',
      address: '789 Pine St, Houston, TX 77019',
      city: 'Houston',
      state: 'TX',
      zip: '77019',
      county: 'Harris',
      name: 'Cool Air HVAC',
      phone: '832-555-0300',
      value: 12000,
      source: 'demo_data',
      lead_score: 78,
      score_label: 'medium',
      status: 'new'
    },
    {
      permit_id: `DEMO-${Date.now()}-004`,
      service: 'Roofing',
      address: '321 Elm Dr, Houston, TX 77025',
      city: 'Houston',
      state: 'TX',
      zip: '77025',
      county: 'Harris',
      name: 'Top Notch Roofing',
      phone: '281-555-0400',
      value: 25000,
      source: 'demo_data',
      lead_score: 90,
      score_label: 'high',
      status: 'new'
    },
    {
      permit_id: `DEMO-${Date.now()}-005`,
      service: 'General',
      address: '654 Maple Ln, Houston, TX 77077',
      city: 'Houston',
      state: 'TX',
      zip: '77077',
      county: 'Harris',
      name: 'Home Improvement Pro',
      phone: '713-555-0500',
      value: 45000,
      source: 'demo_data',
      lead_score: 88,
      score_label: 'high',
      status: 'new'
    }
  ];

  const { data, error } = await supabase
    .from('leads')
    .insert(sampleLeads)
    .select();

  if (error) {
    console.error('❌ Error inserting leads:', error);
    process.exit(1);
  }

  console.log(`✅ Successfully created ${data?.length || 0} sample leads!\n`);
  console.log('📊 Sample leads created:');
  data?.forEach((lead: any) => {
    console.log(`  - ${lead.service} permit at ${lead.address} (Score: ${lead.lead_score}, ${lead.score_label})`);
  });
  
  console.log('\n🎉 Leads are now available in your frontend dashboard!');
}

createSampleLeads();
