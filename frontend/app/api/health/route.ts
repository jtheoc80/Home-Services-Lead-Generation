import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

/**
 * Frontend health check endpoint
 * 
 * Checks:
 * - Frontend status (always "ok" if this runs)
 * - Backend /healthz endpoint connectivity 
 * - Supabase client initialization with NEXT_PUBLIC_* vars
 * 
 * Returns combined health status for monitoring
 */
export async function GET() {
  const results = {
    timestamp: new Date().toISOString(),
    frontend: "ok",
    backend: "down",
    supabase: "down"
  };

  // Check backend health
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    const backendUrl = `${apiBase}/healthz`;
    
    const backendResponse = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Short timeout for health checks
      signal: AbortSignal.timeout(5000)
    });

    if (backendResponse.ok) {
      const backendData = await backendResponse.json();
      // Include backend details in response
      results.backend = backendData.status === 'ok' ? 'ok' : 'down';
    }
  } catch (error) {
    console.error('Backend health check failed:', error);
    results.backend = 'down';
  }

  // Check Supabase client initialization
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
      throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY');
    }

    // Initialize Supabase client to verify env vars work
    const supabase = createClient(supabaseUrl, supabaseAnonKey);
    
    // Simple test - try to call auth endpoint (should not error on client init)
    const { error } = await supabase.auth.getSession();
    
    // If we get here without throwing, Supabase client is working
    results.supabase = 'ok';
  } catch (error) {
    console.error('Supabase health check failed:', error);
    results.supabase = 'down';
  }

  // Determine overall status
  const isHealthy = results.frontend === 'ok' && 
                   results.backend === 'ok' && 
                   results.supabase === 'ok';

  return NextResponse.json(
    results,
    { 
      status: isHealthy ? 200 : 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    }
  );
}