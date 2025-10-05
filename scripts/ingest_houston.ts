#!/usr/bin/env tsx
/**
 * Houston/Harris County Permit Ingestion
 * Creates sample leads based on Houston/Harris County permit patterns
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

const HOUSTON_ADDRESSES = [
  '2450 Richmond Ave, Houston, TX 77098',
  '8900 Westheimer Rd, Houston, TX 77063',
  '5200 Memorial Dr, Houston, TX 77007',
  '1234 Heights Blvd, Houston, TX 77008',
  '7800 Kirby Dr, Houston, TX 77030',
  '3400 Montrose Blvd, Houston, TX 77006',
  '9500 Bellaire Blvd, Houston, TX 77036',
  '6200 Westpark Dr, Houston, TX 77057',
  '4100 Southwest Fwy, Houston, TX 77027',
  '2900 Woodridge Dr, Houston, TX 77087'
];

const CONTRACTORS = [
  { name: 'ABC Electric Services Inc', trade: 'Electrical' },
  { name: 'Quality Plumbing & Repair', trade: 'Plumbing' },
  { name: 'Cool Breeze HVAC Solutions', trade: 'HVAC' },
  { name: 'TopNotch Roofing Contractors', trade: 'Roofing' },
  { name: 'Premier Home Services LLC', trade: 'General' },
  { name: 'Lone Star Electric Co', trade: 'Electrical' },
  { name: 'Texas HVAC & Mechanical', trade: 'HVAC' },
  { name: 'Metro Plumbing Services', trade: 'Plumbing' },
  { name: 'Reliable Roofing & Construction', trade: 'Roofing' },
  { name: 'Houston Electrical Solutions', trade: 'Electrical' }
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

function generateRandomValue(): number {
  const values = [7200, 8900, 12300, 15500, 18500, 19500, 25000, 28000, 32000, 45000];
  return values[Math.floor(Math.random() * values.length)];
}

export async function ingestHoustonLeads(limit: number = 10) {
  console.log(`📡 Generating ${limit} Houston/Harris County leads...`);

  const leads = [];
  const timestamp = Date.now();

  for (let i = 0; i < limit; i++) {
    const contractor = CONTRACTORS[i % CONTRACTORS.length];
    const address = HOUSTON_ADDRESSES[i % HOUSTON_ADDRESSES.length];
    const zipcode = address.match(/\d{5}/)?.[0] || '77002';
    const value = generateRandomValue();
    const score = calculateLeadScore(value);

    leads.push({
      external_permit_id: `HOU-${timestamp}-${String(i + 1).padStart(3, '0')}`,
      name: contractor.name,
      address: address,
      zipcode: zipcode,
      county: 'Harris',
      trade: contractor.trade,
      value: value,
      lead_score: score,
      score_label: getScoreLabel(score),
      status: 'new',
      source: 'houston_permits'
    });
  }

  const { data, error } = await supabase
    .from('leads')
    .insert(leads)
    .select();

  if (error) {
    console.error('❌ Insert error:', error.message);
    return { success: false, count: 0, errors: [error.message] };
  }

  console.log(`✅ Inserted ${data?.length || 0} Houston leads`);
  return { success: true, count: data?.length || 0, leads: data };
}

// Run if executed directly
ingestHoustonLeads(10)
  .then(result => {
    console.log('\n🎉 Houston ingestion complete!');
    console.log(`📊 ${result.count} leads created`);
    process.exit(0);
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
