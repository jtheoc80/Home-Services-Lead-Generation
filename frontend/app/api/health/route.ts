import { NextRequest, NextResponse } from 'next/server';

/**
 * Frontend Health Check API Route
 * 
 * Provides health status for the frontend, including webhook configuration
 */
export async function GET(request: NextRequest) {
  try {
    const webhookStripe = !!process.env.STRIPE_WEBHOOK_SECRET;
    const supabaseConfigured = !!(process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY);
    const backendWebhookConfigured = !!(process.env.INTERNAL_BACKEND_WEBHOOK_URL && process.env.INTERNAL_WEBHOOK_TOKEN);
    
    return NextResponse.json({
      status: 'ok',
      webhooksStripe: webhookStripe,
      supabaseConfigured: supabaseConfigured,
      backendWebhookConfigured: backendWebhookConfigured,
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    });
    
  } catch (error) {
    console.error('Health check error:', error);
    return NextResponse.json(
      { 
        status: 'error', 
        error: 'Health check failed',
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    );
  }
}