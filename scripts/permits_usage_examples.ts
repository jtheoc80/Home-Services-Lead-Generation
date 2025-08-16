#!/usr/bin/env tsx

/**
 * Example usage of the permits view query
 * 
 * This script demonstrates different ways to use the permits query
 * from the problem statement in various contexts.
 */

import { createClient } from '@supabase/supabase-js';

// Types matching the problem statement
interface Permit {
  id: string;
  jurisdiction: string;
  county: string;
  permit_type: string;
  value: number | null;
  status: string;
  issued_date: string;
  address: string;
}

async function demonstratePermitsUsage() {
  console.log('📋 Permits View Usage Examples\n');

  // Setup Supabase client
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Missing Supabase configuration');
    process.exit(1);
  }

  const supabase = createClient(supabaseUrl, supabaseKey);

  // Example 1: Basic query from problem statement
  console.log('1️⃣ Basic Problem Statement Query');
  console.log('=====================================');
  
  try {
    const { data: permits, error } = await supabase
      .from('permits')
      .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
      .order('issued_date', { ascending: false })
      .limit(50);

    if (error) throw error;

    console.log(`✅ Found ${permits?.length || 0} permits`);
    
    if (permits && permits.length > 0) {
      const sample = permits[0] as Permit;
      console.log('📄 Sample permit:');
      console.log(`   ${sample.jurisdiction} | ${sample.permit_type} | $${sample.value?.toLocaleString() || 'N/A'}`);
      console.log(`   ${sample.address}`);
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n');

  // Example 2: Filtered by county
  console.log('2️⃣ Filtered by County');
  console.log('=======================');
  
  try {
    const { data: harrisPermits, error } = await supabase
      .from('permits')
      .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
      .eq('county', 'Harris')
      .order('issued_date', { ascending: false })
      .limit(20);

    if (error) throw error;

    console.log(`✅ Found ${harrisPermits?.length || 0} Harris County permits`);
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n');

  // Example 3: High-value permits
  console.log('3️⃣ High-Value Permits (>$100k)');
  console.log('===============================');
  
  try {
    const { data: highValuePermits, error } = await supabase
      .from('permits')
      .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
      .gt('value', 100000)
      .order('value', { ascending: false })
      .limit(10);

    if (error) throw error;

    console.log(`✅ Found ${highValuePermits?.length || 0} high-value permits`);
    
    if (highValuePermits && highValuePermits.length > 0) {
      highValuePermits.forEach((permit, index) => {
        console.log(`   ${index + 1}. $${permit.value?.toLocaleString()} - ${permit.permit_type} in ${permit.jurisdiction}`);
      });
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n');

  // Example 4: Recent permits by jurisdiction
  console.log('4️⃣ Recent Permits by Jurisdiction');
  console.log('===================================');
  
  try {
    const { data: recentByJurisdiction, error } = await supabase
      .from('permits')
      .select('jurisdiction, county, permit_type, value, issued_date', { count: 'exact' })
      .gte('issued_date', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()) // Last 30 days
      .order('issued_date', { ascending: false });

    if (error) throw error;

    console.log(`✅ Found ${recentByJurisdiction?.length || 0} permits in last 30 days`);
    
    // Group by jurisdiction
    if (recentByJurisdiction && recentByJurisdiction.length > 0) {
      const grouped = recentByJurisdiction.reduce((acc: Record<string, number>, permit) => {
        acc[permit.jurisdiction] = (acc[permit.jurisdiction] || 0) + 1;
        return acc;
      }, {});
      
      Object.entries(grouped).forEach(([jurisdiction, count]) => {
        console.log(`   ${jurisdiction}: ${count} permits`);
      });
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n');

  // Example 5: Summary statistics
  console.log('5️⃣ Summary Statistics');
  console.log('======================');
  
  try {
    const { data: allPermits, error } = await supabase
      .from('permits')
      .select('jurisdiction, county, permit_type, value, status');

    if (error) throw error;

    if (allPermits && allPermits.length > 0) {
      const totalPermits = allPermits.length;
      const uniqueJurisdictions = new Set(allPermits.map(p => p.jurisdiction)).size;
      const uniqueCounties = new Set(allPermits.map(p => p.county)).size;
      const permitsByType = allPermits.reduce((acc: Record<string, number>, permit) => {
        const type = permit.permit_type || 'Unknown';
        acc[type] = (acc[type] || 0) + 1;
        return acc;
      }, {});
      
      const totalValue = allPermits
        .filter(p => p.value)
        .reduce((sum, p) => sum + (p.value || 0), 0);
      
      const avgValue = totalValue / allPermits.filter(p => p.value).length;

      console.log(`📊 Total permits: ${totalPermits.toLocaleString()}`);
      console.log(`🏛️  Jurisdictions: ${uniqueJurisdictions}`);
      console.log(`🗺️  Counties: ${uniqueCounties}`);
      console.log(`💰 Total value: $${totalValue.toLocaleString()}`);
      console.log(`📈 Average value: $${Math.round(avgValue).toLocaleString()}`);
      
      console.log('\n📋 Top permit types:');
      Object.entries(permitsByType)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .forEach(([type, count]) => {
          console.log(`   ${type}: ${count}`);
        });
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n✨ Examples completed successfully!');
}

// Run examples
if (import.meta.url === `file://${process.argv[1]}`) {
  demonstratePermitsUsage()
    .catch(error => {
      console.error('💥 Unexpected error:', error);
      process.exit(1);
    });
}