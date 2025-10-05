import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

export async function GET() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);

    const [leadsResult, countyStats] = await Promise.all([
      supabase
        .from('leads')
        .select('county, status, lead_score', { count: 'exact' }),
      supabase
        .from('leads')
        .select('county')
        .in('county', ['Harris', 'Dallas', 'Travis'])
    ]);

    console.log('Supabase leadsResult:', { count: leadsResult.count, dataLength: leadsResult.data?.length, error: leadsResult.error });
    console.log('Supabase countyStats:', { dataLength: countyStats.data?.length, error: countyStats.error });

    if (leadsResult.error) throw leadsResult.error;

    const totalLeads = leadsResult.count || 0;
    const allLeads = leadsResult.data || [];
    
    const qualifiedLeads = allLeads.filter(
      lead => lead.lead_score && lead.lead_score >= 60
    ).length;

    const activeCounties = new Set(countyStats.data?.map(l => l.county)).size;
    
    const successRate = totalLeads > 0 
      ? Math.round((qualifiedLeads / totalLeads) * 100) 
      : 0;

    const countyBreakdown = countyStats.data?.reduce((acc, lead) => {
      acc[lead.county] = (acc[lead.county] || 0) + 1;
      return acc;
    }, {} as Record<string, number>) || {};

    return NextResponse.json({
      activeCounties,
      totalLeads,
      qualifiedLeads,
      successRate,
      countyBreakdown
    });
  } catch (error) {
    console.error('Stats API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
