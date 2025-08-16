// Force dynamic rendering and Node runtime for permit self-test API
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { getSupabaseClient } from '@/lib/supabaseServer';

/**
 * Permits Self-Test Route
 * 
 * Inserts a sentinel row with service role and returns before/after counts
 * for diagnostic purposes. This helps verify that the upsert_permit function
 * is working correctly and the database connection is functional.
 */
export async function POST() {
  try {
    // Use service role key for elevated permissions
    const supabase = getSupabaseClient({ useServiceRole: true });
    
    // Get count before insert
    const { count: beforeCount, error: countBeforeError } = await supabase
      .from('permits')
      .select('id', { count: 'exact', head: true });
    
    if (countBeforeError) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Failed to get before count',
          details: countBeforeError.message 
        },
        { status: 500 }
      );
    }

    // Create sentinel permit data for testing
    const timestamp = new Date().toISOString();
    const sentinelPermit = {
      source: 'selftest',
      source_record_id: `selftest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      permit_number: `TEST-${Date.now()}`,
      issued_date: timestamp,
      permit_type: 'Self-Test',
      permit_class: 'Diagnostic',
      work_description: 'Self-test sentinel record for API diagnostics',
      address: '123 Test Street',
      city: 'Test City',
      county: 'Test County',
      zipcode: '12345',
      latitude: 30.2672,
      longitude: -97.7431,
      valuation: 1.00,
      square_feet: 1,
      applicant_name: 'Self-Test System',
      contractor_name: 'API Diagnostics',
      owner_name: 'Test Owner',
      status: 'Self-Test Inserted'
    };

    // Use upsert_permit RPC function to insert the sentinel record
    const { data: upsertData, error: upsertError } = await supabase.rpc('upsert_permit', {
      permit_data: sentinelPermit
    });

    if (upsertError) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Failed to upsert sentinel permit',
          details: upsertError.message,
          sentinelData: sentinelPermit
        },
        { status: 500 }
      );
    }

    // Get count after insert
    const { count: afterCount, error: countAfterError } = await supabase
      .from('permits')
      .select('id', { count: 'exact', head: true });
    
    if (countAfterError) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Failed to get after count',
          details: countAfterError.message 
        },
        { status: 500 }
      );
    }

    // Verify the inserted record exists
    const { data: verifyData, error: verifyError } = await supabase
      .from('permits')
      .select('id, created_at, updated_at, source, source_record_id, permit_number, status')
      .eq('source', 'selftest')
      .eq('source_record_id', sentinelPermit.source_record_id)
      .single();

    if (verifyError && verifyError.code !== 'PGRST116') { // PGRST116 is "not found"
      return NextResponse.json(
        { 
          success: false, 
          error: 'Failed to verify inserted record',
          details: verifyError.message 
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Self-test completed successfully',
      diagnostics: {
        rpc_function: 'upsert_permit',
        sentinel_permit: sentinelPermit,
        upsert_result: upsertData,
        counts: {
          before: beforeCount || 0,
          after: afterCount || 0,
          difference: (afterCount || 0) - (beforeCount || 0)
        },
        verification: {
          record_found: !!verifyData,
          record_details: verifyData || null
        },
        timestamp: new Date().toISOString(),
        environment: {
          runtime: 'nodejs',
          service_role_used: true,
          test_mode: process.env.LEADS_TEST_MODE === "true"
        }
      }
    });

  } catch (error) {
    console.error('Permits self-test error:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'Internal server error during self-test',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}

// GET endpoint for information about the self-test
export async function GET() {
  return NextResponse.json({
    message: 'TX Permits Self-Test API',
    version: '1.0.0',
    description: 'Inserts a sentinel permit record and returns diagnostic information',
    usage: {
      POST: 'Run self-test by inserting a sentinel record and returning before/after counts'
    },
    features: [
      'Uses service role for elevated permissions',
      'Tests upsert_permit RPC function',
      'Returns before/after record counts',
      'Verifies record insertion',
      'Provides detailed diagnostics'
    ],
    runtime: 'nodejs',
    caching: 'force-dynamic'
  });
}