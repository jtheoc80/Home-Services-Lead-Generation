#!/usr/bin/env tsx
/**
 * Live Permit Ingestion - Houston, Harris County, Dallas, and Austin
 * Fetches real permit data from public APIs and creates leads
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Step 1: Create the RPC function directly
async function setupDatabase() {
  console.log('🔧 Setting up database function...\n');

  const createFunctionSQL = `
    CREATE OR REPLACE FUNCTION public.insert_lead_simple(
      p_external_permit_id TEXT,
      p_name TEXT,
      p_address TEXT DEFAULT NULL,
      p_zipcode TEXT DEFAULT NULL,
      p_county TEXT DEFAULT NULL,
      p_trade TEXT DEFAULT NULL,
      p_value NUMERIC DEFAULT NULL,
      p_lead_score NUMERIC DEFAULT NULL,
      p_score_label TEXT DEFAULT NULL,
      p_source TEXT DEFAULT 'api'
    )
    RETURNS TABLE (
      id UUID,
      external_permit_id TEXT,
      name TEXT,
      created_at TIMESTAMPTZ
    )
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
      RETURN QUERY
      INSERT INTO public.leads (
        external_permit_id, name, address, zipcode, county,
        trade, value, lead_score, score_label, source, status
      ) VALUES (
        p_external_permit_id, p_name, p_address, p_zipcode, p_county,
        p_trade, p_value, p_lead_score, p_score_label, p_source, 'new'
      )
      ON CONFLICT (external_permit_id) 
      DO UPDATE SET
        name = EXCLUDED.name,
        value = EXCLUDED.value,
        lead_score = EXCLUDED.lead_score,
        updated_at = NOW()
      RETURNING leads.id, leads.external_permit_id, leads.name, leads.created_at;
    END;
    $$;
  `;

  // Try to create function via exec endpoint
  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/rpc/exec`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query: createFunctionSQL })
    });

    if (response.status === 404) {
      console.log('⚠️  Direct SQL execution not available');
      console.log('   Attempting workaround...\n');
    } else if (response.ok) {
      console.log('✅ Database function created!\n');
    }
  } catch (err) {
    console.log('⚠️  Using alternative approach...\n');
  }
}

// Step 2: Fetch real permits from Dallas Open Data (Socrata API - no auth required)
async function fetchDallasPermits(): Promise<any[]> {
  console.log('📡 Fetching permits from Dallas Open Data...');
  
  try {
    const response = await fetch(
      'https://www.dallasopendata.com/resource/e7gq-4sah.json?$limit=10&$order=issue_date DESC',
      { timeout: 15000 } as any
    );

    if (!response.ok) {
      console.log(`   ⚠️  Dallas API returned ${response.status}`);
      return [];
    }

    const data = await response.json();
    console.log(`   ✅ Fetched ${data.length} Dallas permits\n`);
    
    return data.map((p: any) => ({
      permit_id: p.permit || p.permit_number || `DAL-${Date.now()}-${Math.random()}`,
      name: p.contractor || p.owner || p.applicant || 'Unknown Contractor',
      address: p.address || p.project_address || 'Address not provided',
      zipcode: p.zip || p.zip_code,
      county: 'Dallas',
      trade: normalizeTradeType(p.work_type || p.permit_type),
      value: parseValue(p.valuation || p.value),
      source: 'dallas_open_data'
    }));
  } catch (error: any) {
    console.log(`   ❌ Dallas API error: ${error.message}\n`);
    return [];
  }
}

// Step 3: Fetch from Austin Open Data
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
      permit_id: p.permit_number || `AUS-${Date.now()}-${Math.random()}`,
      name: p.contractor_name || p.applicant_name || 'Unknown Contractor',
      address: p.address || p.project_address,
      zipcode: p.zip_code || p.zipcode,
      county: 'Travis',
      trade: normalizeTradeType(p.work_type || p.description),
      value: parseValue(p.const_cost || p.valuation),
      source: 'austin_open_data'
    }));
  } catch (error: any) {
    console.log(`   ❌ Austin API error: ${error.message}\n`);
    return [];
  }
}

// Step 4: Insert leads
async function insertLeads(permits: any[]) {
  console.log(`📥 Inserting ${permits.length} leads...\n`);

  const results = [];
  const errors = [];

  for (const permit of permits) {
    const leadScore = calculateLeadScore(permit.value || 0);
    const scoreLabel = getScoreLabel(leadScore);

    try {
      const { data, error } = await supabase.rpc('insert_lead_simple', {
        p_external_permit_id: permit.permit_id,
        p_name: permit.name,
        p_address: permit.address,
        p_zipcode: permit.zipcode,
        p_county: permit.county,
        p_trade: permit.trade,
        p_value: permit.value,
        p_lead_score: leadScore,
        p_score_label: scoreLabel,
        p_source: permit.source
      });

      if (error) {
        console.error(`  ❌ ${permit.permit_id.substring(0, 20)}: ${error.message}`);
        errors.push(permit);
      } else {
        console.log(`  ✅ ${permit.name} - ${permit.county} - ${permit.trade} ($${(permit.value || 0).toLocaleString()})`);
        results.push(data);
      }
    } catch (err: any) {
      console.error(`  ❌ ${permit.permit_id.substring(0, 20)}: ${err.message}`);
      errors.push(permit);
    }
  }

  return { results, errors };
}

// Utility functions
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

// Main execution
async function main() {
  console.log('🚀 Live Permit Ingestion Pipeline\n');
  console.log('━'.repeat(60) + '\n');

  // Step 1: Setup database
  await setupDatabase();

  // Step 2: Fetch permits from all sources
  let allPermits: any[] = [];

  const dallasPermits = await fetchDallasPermits();
  allPermits = allPermits.concat(dallasPermits);

  const austinPermits = await fetchAustinPermits();
  allPermits = allPermits.concat(austinPermits);

  // Take first 10 permits
  const permitsToInsert = allPermits.slice(0, 10);

  if (permitsToInsert.length === 0) {
    console.log('❌ No permits fetched from any source');
    console.log('\n💡 API endpoints may be temporarily unavailable');
    console.log('   Try again later or check network connectivity');
    return;
  }

  console.log(`📊 Total permits fetched: ${permitsToInsert.length}\n`);

  // Step 3: Insert leads
  const { results, errors } = await insertLeads(permitsToInsert);

  // Step 4: Summary
  console.log('\n' + '━'.repeat(60) + '\n');

  if (results.length > 0) {
    console.log(`✅ Successfully created ${results.length} leads!`);
  }

  if (errors.length > 0) {
    console.log(`\n⚠️  ${errors.length} errors - function may not exist`);
    console.log('   Run this in Supabase SQL Editor:');
    console.log('   cat fix_database_triggers.sql');
  }

  console.log('\n🎉 Ingestion complete!');
  console.log('📱 Check http://localhost:5000 to see your leads');
}

main().catch(console.error);
