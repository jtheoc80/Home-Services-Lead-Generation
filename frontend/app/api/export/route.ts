import { NextRequest, NextResponse } from 'next/server';
import Papa from 'papaparse';
import { createServerClient } from '@/lib/supabase/server';

export async function GET(request: NextRequest) {
  try {
    const supabase = createServerClient();

    // Get query parameters for filtering
    const searchParams = request.nextUrl.searchParams;
    const countiesParam = searchParams.get('counties');
    const status = searchParams.get('status');
    const dateFrom = searchParams.get('dateFrom');
    const dateTo = searchParams.get('dateTo');

    // Build the query
    let query = supabase
      .from('leads')
      .select('*')
      .order('created_at', { ascending: false });

    // Apply filters
    if (countiesParam) {
      const counties = countiesParam.split(',').map(c => c.trim()).filter(Boolean);
      if (counties.length === 1) {
        query = query.ilike('county', `%${counties[0]}%`);
      } else if (counties.length > 1) {
        const orConditions = counties.map(c => `county.ilike.%${c}%`).join(',');
        query = query.or(orConditions);
      }
    }
    if (status) {
      query = query.eq('status', status);
    }
    if (dateFrom) {
      query = query.gte('created_at', dateFrom);
    }
    if (dateTo) {
      query = query.lte('created_at', dateTo);
    }

    const { data: leads, error } = await query;

    if (error) {
      console.error('Error fetching leads:', error);
      return NextResponse.json(
        { error: 'Failed to fetch leads' },
        { status: 500 }
      );
    }

    if (!leads || leads.length === 0) {
      return NextResponse.json(
        { error: 'No leads found' },
        { status: 404 }
      );
    }

    // Transform data for CSV export
    const csvData = leads.map(lead => ({
      id: lead.id,
      name: lead.name || '',
      owner_name: lead.owner_name || '',
      contractor_name: lead.contractor_name || '',
      lead_type: lead.lead_type || '',
      email: lead.email || '',
      phone: lead.phone || '',
      address: lead.address || '',
      city: lead.city || '',
      state: lead.state || '',
      zip: lead.zip || lead.zipcode || '',
      county: lead.county || '',
      trade: lead.trade || '',
      service: lead.service || '',
      status: lead.status || '',
      source: lead.source || '',
      lead_score: lead.lead_score || '',
      score_label: lead.score_label || '',
      value: lead.value || '',
      external_permit_id: lead.external_permit_id || '',
      county_population: lead.county_population || '',
      created_at: lead.created_at,
      updated_at: lead.updated_at || '',
    }));

    // Convert to CSV
    const csv = Papa.unparse(csvData);

    // Create filename with timestamp
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `leads-export-${timestamp}.csv`;

    // Return CSV file
    return new NextResponse(csv, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'no-cache',
      },
    });

  } catch (error) {
    console.error('Export error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { leadIds } = body;

    if (!leadIds || !Array.isArray(leadIds) || leadIds.length === 0) {
      return NextResponse.json(
        { error: 'Lead IDs are required' },
        { status: 400 }
      );
    }

    const supabase = createServerClient();

    const { data: leads, error } = await supabase
      .from('leads')
      .select('*')
      .in('id', leadIds)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching leads:', error);
      return NextResponse.json(
        { error: 'Failed to fetch leads' },
        { status: 500 }
      );
    }

    if (!leads || leads.length === 0) {
      return NextResponse.json(
        { error: 'No leads found' },
        { status: 404 }
      );
    }

    // Transform data for CSV export
    const csvData = leads.map(lead => ({
      id: lead.id,
      name: lead.name || '',
      owner_name: lead.owner_name || '',
      contractor_name: lead.contractor_name || '',
      lead_type: lead.lead_type || '',
      email: lead.email || '',
      phone: lead.phone || '',
      address: lead.address || '',
      city: lead.city || '',
      state: lead.state || '',
      zip: lead.zip || lead.zipcode || '',
      county: lead.county || '',
      trade: lead.trade || '',
      service: lead.service || '',
      status: lead.status || '',
      source: lead.source || '',
      lead_score: lead.lead_score || '',
      score_label: lead.score_label || '',
      value: lead.value || '',
      external_permit_id: lead.external_permit_id || '',
      county_population: lead.county_population || '',
      created_at: lead.created_at,
      updated_at: lead.updated_at || '',
    }));

    // Convert to CSV
    const csv = Papa.unparse(csvData);

    // Create filename with timestamp
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `selected-leads-export-${timestamp}.csv`;

    // Return CSV file
    return new NextResponse(csv, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'no-cache',
      },
    });

  } catch (error) {
    console.error('Export error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}