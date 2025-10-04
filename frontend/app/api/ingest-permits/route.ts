import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

export async function POST(request: Request) {
  try {
    const { permits } = await request.json();

    if (!permits || !Array.isArray(permits)) {
      return NextResponse.json(
        { error: 'Invalid request: permits array required' },
        { status: 400 }
      );
    }

    const results = [];
    const errors = [];

    for (const permit of permits) {
      try {
        // Transform permit data to lead format
        const lead = {
          external_permit_id: permit.permit_id || `PERMIT-${Date.now()}-${Math.random()}`,
          name: permit.contractor_name || permit.applicant_name || permit.owner_name || 'Unknown',
          address: permit.address,
          zipcode: permit.zipcode || permit.zip,
          county: permit.county || 'Unknown',
          status: 'new',
          trade: normalizeTradeType(permit.trade || permit.work_class || permit.permit_type),
          value: permit.value || permit.valuation || 0,
          lead_score: calculateLeadScore(permit.value || permit.valuation || 0),
          score_label: getScoreLabel(calculateLeadScore(permit.value || permit.valuation || 0)),
          source: permit.source || 'api_ingest',
          metadata: {
            original_permit_data: permit,
            ingested_at: new Date().toISOString()
          }
        };

        // Insert lead directly, bypassing problematic triggers
        const { data, error } = await supabase
          .from('leads')
          .insert(lead)
          .select()
          .single();

        if (error) {
          errors.push({ permit_id: permit.permit_id, error: error.message });
        } else {
          results.push(data);
        }
      } catch (err: any) {
        errors.push({ permit_id: permit.permit_id, error: err.message });
      }
    }

    return NextResponse.json({
      success: true,
      inserted: results.length,
      errors: errors.length,
      results,
      errors
    });

  } catch (error: any) {
    console.error('Ingest error:', error);
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}

export async function GET() {
  // GET endpoint to fetch sample permits from a mock source
  const samplePermits = [
    {
      permit_id: `SAMPLE-${Date.now()}-001`,
      contractor_name: 'ABC Electric Co',
      address: '123 Main St, Houston, TX 77002',
      zipcode: '77002',
      county: 'Harris',
      trade: 'Electrical',
      value: 15000,
      source: 'sample_data'
    },
    {
      permit_id: `SAMPLE-${Date.now()}-002`,
      contractor_name: 'Quality Plumbing',
      address: '456 Oak Ave, Houston, TX 77004',
      zipcode: '77004',
      county: 'Harris',
      trade: 'Plumbing',
      value: 8500,
      source: 'sample_data'
    },
    {
      permit_id: `SAMPLE-${Date.now()}-003`,
      contractor_name: 'Cool Air HVAC',
      address: '789 Pine St, Houston, TX 77019',
      zipcode: '77019',
      county: 'Harris',
      trade: 'HVAC',
      value: 12000,
      source: 'sample_data'
    }
  ];

  return NextResponse.json({
    message: 'POST to this endpoint with permit data to ingest',
    example: {
      permits: samplePermits
    }
  });
}

function normalizeTradeType(trade: string): string {
  const t = trade?.toLowerCase() || '';
  if (t.includes('electric')) return 'Electrical';
  if (t.includes('plumb')) return 'Plumbing';
  if (t.includes('hvac') || t.includes('mech')) return 'HVAC';
  if (t.includes('roof')) return 'Roofing';
  return 'General';
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
