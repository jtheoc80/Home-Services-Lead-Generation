#!/usr/bin/env tsx
/**
 * Create sample permits that will automatically generate leads via database trigger
 * This is the correct way to populate the leads table in this system
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function main() {
  console.log('🚀 Creating sample permits (which auto-generate leads)...\n');

  const timestamp = Date.now();
  const samplePermits = [
    {
      source_system: 'demo_data',
      source_record_id: `DEMO-${timestamp}-001`,
      permit_id: `DEMO-${timestamp}-001`,
      permit_number: `DEMO-${timestamp}-001`,
      jurisdiction: 'tx-harris',
      county: 'Harris',
      address: '123 Main St, Houston, TX 77002',
      city: 'Houston',
      zipcode: '77002',
      status: 'Issued',
      work_description: 'Electrical panel upgrade',
      work_class: 'Electrical',
      trade: 'Electrical',
      applicant: 'ABC Electric Co',
      contractor_name: 'ABC Electric Co',
      value: 15000,
      issued_date: new Date().toISOString()
    },
    {
      source_system: 'demo_data',
      source_record_id: `DEMO-${timestamp}-002`,
      permit_id: `DEMO-${timestamp}-002`,
      permit_number: `DEMO-${timestamp}-002`,
      jurisdiction: 'tx-harris',
      county: 'Harris',
      address: '456 Oak Ave, Houston, TX 77004',
      city: 'Houston',
      zipcode: '77004',
      status: 'Issued',
      work_description: 'Water heater replacement',
      work_class: 'Plumbing',
      trade: 'Plumbing',
      applicant: 'Quality Plumbing Services',
      contractor_name: 'Quality Plumbing Services',
      value: 8500,
      issued_date: new Date().toISOString()
    },
    {
      source_system: 'demo_data',
      source_record_id: `DEMO-${timestamp}-003`,
      permit_id: `DEMO-${timestamp}-003`,
      permit_number: `DEMO-${timestamp}-003`,
      jurisdiction: 'tx-harris',
      county: 'Harris',
      address: '789 Pine St, Houston, TX 77019',
      city: 'Houston',
      zipcode: '77019',
      status: 'Issued',
      work_description: 'HVAC system installation',
      work_class: 'HVAC',
      trade: 'HVAC',
      applicant: 'Cool Air HVAC',
      contractor_name: 'Cool Air HVAC',
      value: 12000,
      issued_date: new Date().toISOString()
    },
    {
      source_system: 'demo_data',
      source_record_id: `DEMO-${timestamp}-004`,
      permit_id: `DEMO-${timestamp}-004`,
      permit_number: `DEMO-${timestamp}-004`,
      jurisdiction: 'tx-harris',
      county: 'Harris',
      address: '321 Elm Dr, Houston, TX 77025',
      city: 'Houston',
      zipcode: '77025',
      status: 'Issued',
      work_description: 'Roof replacement',
      work_class: 'Roofing',
      trade: 'Roofing',
      applicant: 'Top Notch Roofing',
      contractor_name: 'Top Notch Roofing',
      value: 25000,
      issued_date: new Date().toISOString()
    },
    {
      source_system: 'demo_data',
      source_record_id: `DEMO-${timestamp}-005`,
      permit_id: `DEMO-${timestamp}-005`,
      permit_number: `DEMO-${timestamp}-005`,
      jurisdiction: 'tx-harris',
      county: 'Harris',
      address: '654 Maple Ln, Houston, TX 77077',
      city: 'Houston',
      zipcode: '77077',
      status: 'Issued',
      work_description: 'Kitchen remodel',
      work_class: 'General',
      trade: 'General',
      applicant: 'Home Improvement Pro',
      contractor_name: 'Home Improvement Pro',
      value: 45000,
      issued_date: new Date().toISOString()
    }
  ];

  console.log(`📥 Inserting ${samplePermits.length} permits...\n`);

  const { data: permits, error: permitError } = await supabase
    .from('permits')
    .insert(samplePermits)
    .select();

  if (permitError) {
    console.error('❌ Error inserting permits:', permitError.message);
    process.exit(1);
  }

  console.log(`✅ Successfully created ${permits?.length || 0} permits!\n`);

  // Wait a moment for triggers to fire
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Check if leads were auto-created
  console.log('🔍 Checking for auto-generated leads...\n');

  const { data: leads, error: leadsError } = await supabase
    .from('leads')
    .select('*')
    .eq('source', 'demo_data')
    .order('created_at', { ascending: false })
    .limit(10);

  if (leadsError) {
    console.error('❌ Error querying leads:', leadsError.message);
  } else {
    console.log(`✅ Found ${leads?.length || 0} leads created from permits:\n`);
    leads?.forEach((lead: any) => {
      console.log(`  📌 ${lead.name} - ${lead.trade} - ${lead.county} County (Value: $${lead.value?.toLocaleString() || 0})`);
    });
  }

  console.log('\n🎉 Permits and leads are now available in your Supabase dashboard and frontend!');
  console.log(`\n📊 Total leads in database: ${leads?.length || 0}`);
}

main().catch(console.error);
